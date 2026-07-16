# 出站转发到 System A（callback forwarding v1）设计

> 日期：2026-07-15
> 依赖：回调持久化 v1（`feature/callback-persistence`）
> 状态：已确认，待实现

## 一、目标与范围

在已落库的金蝶回调基础上，支持把回调数据**转换并转发**给 System A（EAS InvoiceCallback 接口），用于联调测试。

**本期做**：
- 报文转换：金蝶回调 → System A 期望格式（内层 7 字段 + base64）
- 手动 replay 端点：按需把某条落库回调转发给 System A，可重复、可指定目标
- 用 `systemSource` 定位 proxy_client，取其 `callback_url`
- 运行时可切换的自动转发开关（存 DB，免重启），默认关
- 修正落库打平逻辑：先 base64 解码 data 再提取 serial_nos/bill_nos
- 联调脚本 + 单元测试

**本期不做**：
- by-apply（5.1.03 按单，多张拆分）转发、apply-return（5.1.01）转发 —— replay 时返回"不支持的端点类型"
- 带重试队列的后台 worker（自动转发失败仅记状态，不自动重试；生产级重试留下期）
- 转发鉴权（System A 侧当前无鉴权）

## 二、System A 接口事实（依据 systemA_InvoiceCallback_接口文档.md）

- 对接金蝶 **5.1.02 按票回调**（一次一张发票）
- URL：测试 `http://baodetest.haverise.com:23822/callback/invoiceCallback`；生产待定
- 方法 POST，`Content-Type: application/json; charset=UTF-8`，无鉴权
- 请求外层：`{ interfaceCode, returnCode, returnMsg?, data }`，`data` = 内层 JSON 的**标准 base64**
- 内层 7 字段：`billNo`(必填) / `invoiceDate` / `invoiceNum` / `totalAmount` / `totalTaxAmount` / `invoicePdfFileUrl` / `drawer`
- 响应：`{ message, code:"200"|"500", success:true|false }`（`code` 是字符串）

## 三、分支与合并策略

- base = `feature/callback-persistence`，切新分支 `feature/callback-forwarding`
- 部署测试：服务器 `git checkout feature/callback-forwarding` + `docker compose ... up -d --build`（该分支已含持久化全部 commit）
- 合并顺序：先 `feature/callback-persistence` → PR 入 `main`；再 `feature/callback-forwarding` rebase 到最新 main → PR 入 main

## 四、数据模型变更

### 4.1 `kdcloud_callbacks` 增字段

```
matched_client_id        str | null      # 落库时按 systemSource 匹配到的 client_id
forward_status           str             # "not_forwarded"(默认) | "sent" | "failed" | "unsupported"
forward_attempts         int             # 默认 0，每次 replay/自动转发 +1
last_forward_at          datetime | null
last_forward_status_code int | null      # System A HTTP 状态码
last_forward_error       str | null
forward_history          [ { at, target_url, ok, status_code, error } ]   # $push + $slice: -10
```

### 4.2 `ProxyClientDoc` 增字段（[models.py](file:///d:/Downloads/.vibeCode/.openYZJ/proxy-server/app/models.py)）

```
callback_url             str = ""        # System A 接收回调的地址
```
- `ProxyClientCreateReq` / `ProxyClientUpdateReq` / `ProxyClientPublic` 同步增加 `callback_url`
- admin client CRUD（[admin.py](file:///d:/Downloads/.vibeCode/.openYZJ/proxy-server/app/admin.py) create/update/_to_public）读写该字段

### 4.3 新集合 `proxy_settings`（运行时配置）

```
{ _id: "forwarding", auto_forward_enabled: false, updated_at: datetime }
```

## 五、配置项（[config.py](file:///d:/Downloads/.vibeCode/.openYZJ/proxy-server/app/config.py) + .env.example）

```python
system_a_forward_timeout: int = 10   # 转发 HTTP 超时（秒），静态项
```
> callback_url 存 client doc（不在 .env）；自动转发开关存 proxy_settings（不在 .env，免重启）。

## 六、报文转换（新建 [app/forwarder.py](file:///d:/Downloads/.vibeCode/.openYZJ/proxy-server/app/forwarder.py)）

### 6.1 字段映射（内层，金蝶字段名与 System A 一致）

| System A 内层 | 金蝶来源 | 必填 |
|---|---|---|
| billNo | data.billNo | 是 |
| invoiceDate | data.invoiceDate | 否 |
| invoiceNum | data.invoiceNum | 否 |
| totalAmount | data.totalAmount | 否 |
| totalTaxAmount | data.totalTaxAmount | 否 |
| invoicePdfFileUrl | data.invoicePdfFileUrl | 否 |
| drawer | data.drawer | 否 |

### 6.2 核心函数

```python
class ForwardConfigError(Exception): ...   # URL 未配置
class ForwardUnsupportedError(Exception): ...  # 非 by-invoice 端点

def _decode_kdcloud_data(parsed: dict) -> dict:
    """取金蝶回调 data 并解码为单张发票 dict。
    data 是 base64 str → base64.b64decode + json.loads；已是 dict → 直接返回；
    是 list（by-apply）→ 抛 ForwardUnsupportedError（本期不支持）。"""

def _build_system_a_payload(parsed: dict) -> dict:
    """组装 System A 外层 payload。
    inner = 从解码后的发票 dict 提取 7 字段（None/缺失则省略，billNo 缺失抛错）
    inner_b64 = base64.b64encode(json.dumps(inner, ensure_ascii=False).encode('utf-8')).decode()
    return { interfaceCode, returnCode, returnMsg, data: inner_b64 }"""

async def forward_to_system_a(doc: dict, target_url: str) -> dict:
    """POST payload 到 target_url（Content-Type: application/json; charset=UTF-8）。
    解析 System A 响应：success==true 或 code=='200' → ok=True。
    返回 { ok, status_code, error, target_url }。用 httpx，超时 settings.system_a_forward_timeout。"""
```

### 6.3 转发结果回写（forwarder 或调用方）

```python
async def record_forward_result(db, event_id, target_url, result) -> None:
    """$set forward_status(sent/failed) / last_forward_* ；$inc forward_attempts ；
    $push forward_history（$slice -10）。"""
```

## 七、systemSource 定位 client

### 7.1 落库时（[callbacks.py](file:///d:/Downloads/.vibeCode/.openYZJ/proxy-server/app/endpoints/callbacks.py) `_build_doc` / `_persist_and_ack`）

- 解码 data 后取 `systemSource`
- 查 `proxy_clients` where `client_name == systemSource` 或 `client_id == systemSource`，取 `client_id` 存入 `matched_client_id`（查不到则 null）

### 7.2 replay 目标 URL 解析优先级

1. 请求体 `target_url`（联调覆盖，最高优先）
2. 请求体 `client_id` → 该 client 的 `callback_url`
3. `doc.matched_client_id` → 该 client 的 `callback_url`
4. 都没有 → HTTP 400 `no target_url resolvable`

## 八、落库打平逻辑修正（[callbacks.py](file:///d:/Downloads/.vibeCode/.openYZJ/proxy-server/app/endpoints/callbacks.py)）

金蝶真实 `data` 是 base64 字符串，故 `_extract_flat_fields` 需先尝试解码：

```
data = parsed.get("data")
if isinstance(data, str):    # base64 → 解码 json
    try: data = json.loads(base64.b64decode(data))
    except: data 保持原样，打平留空
# 之后按 dict / list 提取 serial_nos / bill_nos / batches / systemSource
```
- 兼容明文（dict/list）与 base64（str）两种；解码失败不影响落库（打平留空 + parse_error 不变）
- 同时提取 `systemSource` 供 7.1 匹配

## 九、运行时开关（新建 [app/runtime_config.py](file:///d:/Downloads/.vibeCode/.openYZJ/proxy-server/app/runtime_config.py)）

```python
async def get_auto_forward_enabled(db) -> bool:
    """读 proxy_settings/_id=forwarding；10s 内存缓存避免每条回调查库；缺省 False。"""

async def set_auto_forward_enabled(db, enabled: bool) -> None:
    """upsert proxy_settings，更新 updated_at，清缓存。"""
```

admin 端点（[admin.py](file:///d:/Downloads/.vibeCode/.openYZJ/proxy-server/app/admin.py)）：
```
GET  /api/admin/forwarding-config        → { auto_forward_enabled, updated_at }
PUT  /api/admin/forwarding-config        body { auto_forward_enabled: bool } → 立即生效
```

## 十、replay 端点（[admin.py](file:///d:/Downloads/.vibeCode/.openYZJ/proxy-server/app/admin.py)）

```
POST /api/admin/callback-events/{event_id}/replay
  body（可选）: { "target_url"?: str, "client_id"?: str }
  流程：查 doc（404）→ 校验 endpoint==by-invoice（否则 forward_status=unsupported，返回 422）
        → 解析 target_url（八·7.2，缺失 400）→ forward_to_system_a → record_forward_result
  → 200 { forwarded: bool, status_code, forward_attempts, target_url, error? }
```

## 十一、自动转发 hook（[callbacks.py](file:///d:/Downloads/.vibeCode/.openYZJ/proxy-server/app/endpoints/callbacks.py)）

```python
# _persist_and_ack 落库成功且 endpoint == "by-invoice" 后
if await get_auto_forward_enabled(db):
    asyncio.create_task(_safe_auto_forward(inserted_id))   # fire-and-forget，不阻塞金蝶 ACK
```
- `_safe_auto_forward`：查 doc → 解析目标 URL（matched_client_id 的 callback_url）→ forward → record；异常仅 ERROR 日志
- 默认开关关闭时完全不触发；打开后每条 by-invoice 落库尝试转发一次（失败不自动重试）

## 十二、联调脚本 [scripts/replay_to_system_a.sh](file:///d:/Downloads/.vibeCode/.openYZJ/scripts/replay_to_system_a.sh)

封装：按 serial_no/bill_no 查列表 → 取 `_id` → 调 replay 端点（支持传 target_url）。给联调时一行命令重放。

## 十三、测试（proxy-server/tests/）

- `test_forwarder.py`：字段映射 + base64 编码正确；billNo 缺失抛错；by-apply/data=list 抛 ForwardUnsupportedError；base64 str 与 dict 两种输入兼容；System A 响应 success/code 判定；httpx mock 成功/5xx/超时
- `test_flat_fields_base64.py`：`_extract_flat_fields` 对 base64 字符串 data 正确解码并提取 serial_nos/bill_nos/systemSource
- `test_admin_replay.py`：replay 成功 + doc 状态回写；404；非 by-invoice → 422；URL 缺失 → 400；target_url / client_id 覆盖优先级；鉴权
- `test_admin_forwarding_config.py`：GET 缺省 false；PUT 切换生效；鉴权
- `test_auto_forward_switch.py`：开关 off 不触发；on 且 by-invoice 触发 create_task（mock forwarder）；非 by-invoice 不触发
- `test_client_callback_url.py`：client create/update/get 读写 callback_url

DB/httpx 用 `unittest.mock`（AsyncMock），沿用持久化期的 mock 模式，不引入新依赖。

## 十四、文档

更新 [open_api_doc.md](file:///d:/Downloads/.vibeCode/.openYZJ/docs/open_api_doc.md)：新增"出站转发"章节 —— replay 端点、forwarding-config 端点、转发状态字段、字段映射表、`callback_url` 配置、联调脚本用法。

## 十五、提交拆分

1. `feat(models): ProxyClient 增 callback_url + client CRUD 支持`
2. `fix(callbacks): 打平逻辑兼容 base64 data + 提取 systemSource`
3. `feat(forwarder): 金蝶→System A 报文转换与转发核心`
4. `feat(callbacks): 落库匹配 matched_client_id`
5. `feat(admin): forwarding-config 运行时开关`
6. `feat(admin): callback-events replay 端点`
7. `feat(callbacks): 自动转发 hook（默认关）`
8. `chore(scripts): replay_to_system_a.sh 联调脚本`
9. `docs(open_api_doc): 出站转发章节`

（相邻小项可在实现时合并，保持每个 commit 可独立 review）

## 十六、验证

- 本地：`cd proxy-server && pytest tests/` 全绿
- 联调：配置某 client 的 `callback_url` 指向 System A 测试地址 → 造一条 by-invoice 落库 → `POST /replay` → 观察 System A 返回 `code:"200"` 且 EAS 应收单更新
- 生产开关：`PUT /api/admin/forwarding-config {auto_forward_enabled:true}` 免重启生效

## 十七、假设与风险

- **金蝶 data 为 base64 字符串**：依据用户确认 + System A 文档 data 编码方式。若真实报文 data 为明文 dict，forwarder 与打平逻辑均已兼容
- **systemSource 存在于金蝶回调 data**：依据金蝶文档 5.1.03 data 项含 systemSource；by-invoice(5.1.02) 假设同样存在。若缺失则 matched_client_id 为 null，replay 需显式传 target_url/client_id
- **自动转发无重试**：开关打开后失败仅记 failed，需人工 replay 补发；生产级重试队列为下一期
