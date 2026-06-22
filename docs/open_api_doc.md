# OpenYZJ API 接口文档（香港 ECS 测试环境）

> 域名：`https://kimpi.cn` | 环境：test | 分支：`feature/proxy-gateway`

---

## 1. 健康检查

### 1.1 主服务健康检查

`GET /health`

```bash
curl https://kimpi.cn/health
```

响应：
```json
{"app":"ok","mongo":"ok","env":"test"}
```

---

## 2. Admin 管理接口

> 所有管理接口需 `Authorization: Bearer <ADMIN_TOKEN>` 鉴权。

### 2.1 机器人管理（robots 集合 CRUD）

#### 创建机器人

`POST /api/admin/robots`

```bash
curl -X POST https://kimpi.cn/api/admin/robots \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "robot_code": "my_bot",
    "name": "测试机器人",
    "appSecret": "<云之家 appSecret>",
    "robotId": "<云之家 robotId>",
    "sid": "<可选: 门店SID>",
    "company_name": "<可选: 公司名>",
    "webhook_push_url": "<可选: 推送地址>",
    "allowed_handlers": ["echo", "mys4s"]
  }'
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| robot_code | string | 是 | 机器人唯一代号，全英文小写 |
| name | string | 是 | 机器人显示名 |
| appSecret | string | 是 | 云之家分配的 appSecret |
| robotId | string | 否 | 云之家分配的 robotId |
| description | string | 否 | 描述 |
| sid | string | 否 | 金斗云门店 SID |
| company_name | string | 否 | 公司名称 |
| webhook_push_url | string | 否 | 独立消息推送地址 |
| allowed_handlers | string[] | 否 | 允许的处理器列表 |

#### 列出全部机器人

`GET /api/admin/robots`

```bash
curl https://kimpi.cn/api/admin/robots \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

#### 查询单个机器人

`GET /api/admin/robots/{robot_code}`

```bash
curl https://kimpi.cn/api/admin/robots/my_bot \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

#### 更新机器人

`PUT /api/admin/robots/{robot_code}`

```bash
curl -X PUT https://kimpi.cn/api/admin/robots/my_bot \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"新名称","sid":"SID001"}'
```

支持局部更新，所有字段均为可选。

#### 删除机器人

`DELETE /api/admin/robots/{robot_code}`

```bash
curl -X DELETE https://kimpi.cn/api/admin/robots/my_bot \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

---

### 2.2 代理调用方管理（proxy_clients 集合 CRUD）

> 此处管理的是**调用方 System A** 在代理网关的注册信息（非金蝶发票云客户端）。
> System A 注册后会获得 `api_key` + `api_secret`，用于调用第 3 节的金蝶发票云代理 API。

#### 创建代理调用方

`POST /api/admin/proxy-clients`

```bash
curl -X POST https://kimpi.cn/api/admin/proxy-clients \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "system-a",
    "api_key": "<自定义 API Key>",
    "api_secret": "<自定义明文密钥>",
    "allowed_endpoints": ["/api/proxy/v1/invoice", "/api/proxy/v1/digital"],
    "rate_limit": 60
  }'
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| client_name | string | 是 | 调用方名称（同时作为 client_id） |
| api_key | string | 是 | 自定义 API Key，唯一 |
| api_secret | string | 是 | 明文密钥，入库自动 Fernet 加密 |
| allowed_endpoints | string[] | 否 | 端点白名单，空=全部允许 |
| rate_limit | int | 否 | 每分钟请求上限，默认 60 |

#### 列出全部代理调用方

`GET /api/admin/proxy-clients`

#### 查询单个代理调用方

`GET /api/admin/proxy-clients/{client_id}`

#### 更新代理调用方

`PUT /api/admin/proxy-clients/{client_id}`

#### 删除代理调用方

`DELETE /api/admin/proxy-clients/{client_id}`

---

## 3. 金蝶发票云代理 API

> **鉴权方式**：所有接口需 HMAC-SHA256 签名鉴权。System A 通过 2.2 节注册代理调用方获得 `api_key` + `api_secret`。
>
> **统一响应格式**：所有接口返回如下结构：
> ```json
> {"code": 0, "data": <业务数据>, "message": "success"}
> ```
> - `code=0` 成功；`code=500` 时查看 `message` 获取错误详情。
>
> **调用环境**：默认调用金蝶发票云**测试环境**。如需生产环境，加 Header `X-Proxy-Env: prod`。

### 3.1 鉴权签名算法

签名公式：
```
Signature = Hex(HMAC-SHA256(api_secret, HTTP方法 + 请求路径 + 时间戳 + Body))
```
> Body 使用原始 HTTP 请求体字节，无需 MD5 摘要，减少一层序列化开销。

**必需 Headers**：

| Header | 类型 | 说明 |
|--------|------|------|
| `X-Proxy-Api-Key` | string | 注册时分配的 API Key |
| `X-Proxy-Timestamp` | string | Unix 时间戳（秒），±5 分钟有效期 |
| `X-Proxy-Signature` | string | HMAC-SHA256 签名结果（十六进制小写） |
| `X-Proxy-Env` | string | **可选**。`test`（默认）或 `prod` |

**签名计算伪代码**：
```
sign_payload = HTTP_METHOD + PATH + TIMESTAMP + BODY  (BODY 为原始 bytes)
signature    = HMAC-SHA256(api_secret, sign_payload).hex()
```

**Python 完整示例**：

```python
import hashlib, hmac, time, requests

api_key = "<your_api_key>"
api_secret = "<your_api_secret>"
base_url = "https://kimpi.cn"

method = "POST"
path = "/api/proxy/v1/invoice/create"
body = '{"requestId":"REQ20260610001","bills": [...], "autoInvoice": true}'
timestamp = str(int(time.time()))

sign_payload = method.encode() + path.encode() + timestamp.encode() + body.encode()
signature = hmac.new(
    api_secret.encode(), sign_payload, hashlib.sha256
).hexdigest()

resp = requests.post(
    f"{base_url}{path}",
    data=body,
    headers={
        "Content-Type": "application/json",
        "X-Proxy-Api-Key": api_key,
        "X-Proxy-Timestamp": timestamp,
        "X-Proxy-Signature": signature,
        # "X-Proxy-Env": "prod",  # 可选
    },
)
print(resp.json())  # {"code":0,"data":{...},"message":"success"}
```

---

### 3.2 开票接口

#### 3.2.1 开票申请单生成及开票

`POST /api/proxy/v1/invoice/create`

提交开票申请单，支持自动开票和自动合并。

**顶层字段**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| requestId | string | 是 | 调用方生成的唯一请求 ID，用于去重和链路追踪 |
| bills | array[object] | 是 | 开票申请单列表 |
| autoInvoice | boolean | 否 | 提交后立即自动开票，默认 `false`。代理层自动将顶层值注入每张单据 |
| autoMerge | boolean | 否 | 是否自动合并申请单，默认 `false`。代理层自动将顶层值注入每张单据 |

---

**`bills[]` 元素字段**：

**单据基本信息**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| billNo | string | 否 | 单据编号，用于幂等校验，长度 ≤50 |
| batch | string | 否 | 批次号，长度 ≤50 |
| invoiceProperty | number | 是 | 开票类型：`0`-蓝票，`1`-红票 |
| invoiceType | string | 是 | 发票种类（见下文编码表） |

**发票种类编码（invoiceType）**：

| 编码 | 含义 |
|------|------|
| `004` | 增值税纸质专用发票 |
| `007` | 增值税纸质普通发票 |
| `026` | 增值税电子普通发票 |
| `028` | 增值税电子专用发票（数电专票） |
| `029` | 数电普通发票（数电普票） |
| `012` | 机动车统一销售发票 |
| `030` | 二手车销售统一发票 |
| `08xdp` | 数电发票（增值税专用发票） |
| `10xdp` | 数电发票（普通发票） |

**购买方信息**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| buyerName | string | 是 | 购买方名称，长度 ≤100 |
| buyerTaxpayerId | string | 专票必填 | 购买方税号，长度 ≤20 |
| buyerProperty | number | 否 | 购买方性质：`0`-企业，`1`-个人 |
| buyerAddressAndTel | string | 否 | 购买方地址和电话（专票建议填），GBK 编码 ≤100 字节 |
| buyerBankAndAccount | string | 否 | 购买方银行和账号（专票建议填），GBK 编码 ≤100 字节 |
| buyerRecipientPhone | string | 否 | 电子发票收票手机号，长度 ≤80 |
| buyerRecipientMail | string | 否 | 电子发票收票邮箱，长度 ≤300 |

**销售方信息**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sellerName | string | 是 | 销方名称，长度 ≤100 |
| sellerTaxpayerId | string | 是 | 销方税号，长度 ≤20 |
| sellerAddressAndTel | string | 否 | 销方地址和电话，长度 ≤100 |
| sellerBankAndAccount | string | 否 | 销方银行和账号，长度 ≤100 |
| drawer | string | 否 | 开票人，长度 ≤10 |
| payee | string | 否 | 收款人，长度 ≤10 |
| reviewer | string | 否 | 复核人，长度 ≤10 |

**税务信息**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| includeTaxFlag | number | 是 | 含税标识：`0`-不含税，`1`-含税 |
| taxedType | number | 否 | 征税方式：`0`-普通征税，`2`-差额征税 |
| deduction | number | 否 | 差额征税差额，征税方式为差额征税时必填，长度 (14,2) |

**其他信息**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| remark | string | 否 | 备注，GBK 编码 ≤230 字节 |
| inventoryMark | string | 否 | 清单标志：`0`-非清单，`1`-清单发票 |
| originalInvoiceCode | string | 红票必填 | 原蓝票发票代码，长度 ≤12 |
| originalInvoiceNumber | string | 红票必填 | 原蓝票发票号码，长度 ≤8 |
| redInfoBillNo | string | 否 | 红字信息表编号，专票红冲必传，长度 ≤16 |

---

**`bills[].billDetail[]` — 发票明细行**：

> 代理层自动将 `items` 字段映射为金蝶要求的 `billDetail`，调用方可使用 `items` 或 `billDetail` 均可。
> 同样，`billSourceId` 会自动映射为金蝶要求的 `detailId`。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| lineProperty | number | 是 | 行性质：`2`-正常商品行，`1`-折扣行（必须紧跟被折扣行） |
| goodsName | string | 是 | 商品名称（不含税分编码简称前缀），GBK ≤92 字节 |
| revenueCode | string | 是 | 税收分类编码，长度 ≤19 |
| amount | number | 是 | 金额（蓝票 >0，红票 <0），长度 (14,2) |
| taxRate | string | 是 | 税率，支持 `0.13` / `13%` / `13` 三种格式，小数位最多 3 位 |
| detailId | string | 是 | 业务系统明细 ID，用于反写回原业务系统，长度 ≤50 |
| taxAmount | number | 否 | 税额（系统会自动计算），长度 (14,2) |
| includeTaxAmount | number | 否 | 价税合计，金额×税率±0.06 校验 |
| quantity | number/string | 否 | 数量，金额不为空时可免填 |
| price | number/string | 否 | 不含税单价，长度 (14,8) |
| includeTaxPrice | string | 否 | 含税单价 |
| specification | string | 否 | 规格型号，GBK 编码 ≤40 字节 |
| units | string | 否 | 计量单位，GBK 编码 ≤22 字节 |
| discountAmount | number | 否 | 折扣金额，折扣行必填，长度 (14,2) |
| discountRate | string | 否 | 折扣率 |
| zeroTaxRateFlag | string | 否 | 零税率标识：`1`-出口退税，`2`-不征税，`3`-普通零税率 |
| privilegeFlag | number | 否 | 是否享受优惠：`0`-不享受，`1`-享受 |
| privilegeContent | string | 否 | 享受优惠内容，长度 ≤50 |

**请求示例**：
```bash
curl -X POST https://kimpi.cn/api/proxy/v1/invoice/create \
  -H "Content-Type: application/json" \
  -H "X-Proxy-Api-Key: <API_KEY>" \
  -H "X-Proxy-Timestamp: <TIMESTAMP>" \
  -H "X-Proxy-Signature: <SIGNATURE>" \
  -d '{
    "requestId": "REQ20260610001",
    "bills": [{
      "billNo": "ORD20260601001",
      "invoiceProperty": 0,
      "invoiceType": "028",
      "includeTaxFlag": 1,
      "buyerName": "XX有限公司",
      "buyerTaxpayerId": "91110000XXXXXXXXXX",
      "sellerName": "销售方公司",
      "sellerTaxpayerId": "91110000YYYYYYYYYY",
      "billDetail": [{
        "lineProperty": 2,
        "goodsName": "技术服务费",
        "revenueCode": "3040201990000000000",
        "amount": 1000.00,
        "taxRate": "0.06",
        "taxAmount": 60.00,
        "detailId": "ITEM_001",
        "quantity": 1,
        "price": 1000.00,
        "specification": "次",
        "units": "次"
      }]
    }],
    "autoInvoice": true
  }'
```

**成功响应**：
```json
{
  "code": 0,
  "data": {
    "applyId": "A202606110001",
    "status": "invoiced"
  },
  "message": "success"
}
```

#### 3.2.2 开票申请单撤回

`POST /api/proxy/v1/invoice/revoke`

撤回已提交但尚未完成开票的申请单。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| requestId | string | 是 | 调用方生成的唯一请求 ID，用于去重和链路追踪 |
| applyId | string | 是 | 要撤回的申请单 ID（由 3.2.1 返回） |

**请求示例**：
```json
{"requestId": "REQ20260610002", "applyId": "A202606110001"}
```

**成功响应**：
```json
{"code": 0, "data": {"applyId": "A202606110001", "status": "revoked"}, "message": "success"}
```

#### 3.2.3 开票申请单发票查询

`GET /api/proxy/v1/invoice/query/{apply_id}?requestId={request_id}&sellerTaxpayerId={seller_taxpayer_id}`

按申请单 ID 查询关联的发票信息。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| apply_id | path | string | 是 | 开票申请单 ID |
| requestId | query | string | 是 | 调用方生成的唯一请求 ID，用于去重和链路追踪 |
| sellerTaxpayerId | query | string | 是 | 销售方纳税人识别号，金蝶 API 必填字段 |

> ⚠️ `requestId` 仅用于网关外层标识，不会编码进金蝶 API `data` 内层。

**请求示例**：
```bash
curl "https://kimpi.cn/api/proxy/v1/invoice/query/A202606110001?requestId=REQ20260610003&sellerTaxpayerId=91110000YYYYYYYYYY" \
  -H "X-Proxy-Api-Key: <API_KEY>" \
  -H "X-Proxy-Timestamp: <TIMESTAMP>" \
  -H "X-Proxy-Signature: <SIGNATURE>"
```

**成功响应**：
```json
{
  "code": 0,
  "data": {
    "applyId": "A202606110001",
    "invoices": [
      {"invoiceNo": "12345678", "invoiceCode": "044001900111", "amount": 1000.00}
    ]
  },
  "message": "success"
}
```

---

### 3.3 机动车发票接口

> 当前代理层对机动车接口采用**透明透传**模式（Pydantic 模型仅设 `extra="allow"`，不做字段级校验）。请求体直接传入金蝶发票云机动车 API 的原生 JSON 结构，代理层不做解析和转换。

#### 3.3.1 机动车信息查询

`POST /api/proxy/v1/vehicle/info`

查询机动车合格证/车辆信息（VIN 码、品牌、型号等），返回的车辆信息是 3.3.2 机动车发票开具的**前置依赖数据**。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| requestId | string | 是 | 调用方生成的唯一请求 ID，用于去重和链路追踪 |
| vehicleCode | string | 是 | 车架号（VIN）或合格证编号 |
| queryType | string | 否 | 查询方式：`byVin`（按车架号）、`byQualifiedNo`（按合格证编号） |

**请求示例**：
```json
{"requestId": "REQ20260610004", "vehicleCode": "LSVAA4185E2123456", "queryType": "byVin"}
```

**成功响应**：
```json
{
  "code": 0,
  "data": {
    "vehicleCode": "LSVAA4185E2123456",
    "brand": "XX品牌",
    "model": "XX型号",
    "engineNo": "ENG123456"
  },
  "message": "success"
}
```

#### 3.3.2 机动车发票开具

`POST /api/proxy/v1/vehicle/invoice`

开具机动车销售统一发票（支持税控机动车、数电机动车、数电纸票机动车）。请求体中的车辆信息字段通常来自 3.3.1 的响应数据。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| requestId | string | 是 | 调用方生成的唯一请求 ID，用于去重和链路追踪 |
| applyId | string | 否 | 开票申请单 ID |
| invoiceType | string | 是 | 发票种类编码，机动车为 `012` |
| vehicleCode | string | 是 | 车架号（VIN） |
| buyerName | string | 是 | 购买方名称 |
| buyerTaxpayerId | string | 否 | 购买方税号（企业必填） |
| buyerAddressAndTel | string | 否 | 购买方地址和电话 |
| buyerBankAndAccount | string | 否 | 购买方银行和账号 |
| sellerName | string | 是 | 销方名称 |
| sellerTaxpayerId | string | 是 | 销方税号 |
| items | array[object] | 是 | 发票明细行，字段同 3.2.1 items[] 结构 |

**请求示例**：
```json
{
  "requestId": "REQ20260610005",
  "invoiceType": "012",
  "vehicleCode": "LSVAA4185E2123456",
  "buyerName": "购方公司",
  "buyerTaxpayerId": "91110000XXXXXXXXXX",
  "sellerName": "销方公司",
  "sellerTaxpayerId": "91110000YYYYYYYYYY",
  "items": [{
    "lineProperty": 2,
    "goodsName": "XX品牌乘用车",
    "revenueCode": "1090101000000000000",
    "amount": 100000.00,
    "taxRate": "0.13",
    "taxAmount": 13000.00
  }]
}
```

**成功响应**：
```json
{
  "code": 0,
  "data": {"invoiceNo": "87654321", "invoiceCode": "044001900111"},
  "message": "success"
}
```

#### 3.3.3 机动车发票红冲

`POST /api/proxy/v1/vehicle/red-flush`

对已开具的机动车发票发起红冲（负数发票冲销），支持数电机动车和税控机动车。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| requestId | string | 是 | 调用方生成的唯一请求 ID，用于去重和链路追踪 |
| originalInvoiceCode | string | 是 | 原蓝票发票代码，长度 ≤12 |
| originalInvoiceNumber | string | 是 | 原蓝票发票号码，长度 ≤8 |
| redReason | string | 否 | 红冲原因 |

> ⚠️ 本接口代码已实现但未经过实际机动车发票测试，使用前需验证。

**请求示例**：
```json
{
  "requestId": "REQ20260610006",
  "originalInvoiceCode": "044001900111",
  "originalInvoiceNumber": "87654321",
  "redReason": "开票信息有误"
}
```

**成功响应**：
```json
{
  "code": 0,
  "data": {"redInvoiceNo": "99999999", "status": "completed"},
  "message": "success"
}
```

---

### 3.4 数电票查询接口

#### 3.4.1 批量查询

`POST /api/proxy/v1/digital/batch-query`

按发票流水号批量查询数电票发票信息。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| requestId | string | 是 | 调用方生成的唯一请求 ID，用于去重和链路追踪 |
| serialNos | array[string] | 是 | 发票流水号列表，每次最多查询 50 条 |

**请求示例**：
```bash
curl -X POST https://kimpi.cn/api/proxy/v1/digital/batch-query \
  -H "Content-Type: application/json" \
  -H "X-Proxy-Api-Key: <API_KEY>" \
  -H "X-Proxy-Timestamp: <TIMESTAMP>" \
  -H "X-Proxy-Signature: <SIGNATURE>" \
  -d '{"requestId": "REQ20260610007", "serialNos": ["SN20260601001", "SN20260601002"]}'
```

**成功响应**：
```json
{
  "code": 0,
  "data": {
    "invoices": [
      {"serialNo": "SN20260601001", "invoiceNo": "12345678", "amount": 1000.00, "status": "已开具"},
      {"serialNo": "SN20260601002", "invoiceNo": "12345679", "amount": 2000.00, "status": "已开具"}
    ]
  },
  "message": "success"
}
```

#### 3.4.2 单张查询

`POST /api/proxy/v1/digital/query`

按发票流水号查询单张数电票发票信息。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| requestId | string | 是 | 调用方生成的唯一请求 ID，用于去重和链路追踪 |
| serialNo | string | 是 | 发票流水号（与 invoiceNum 二选一） |
| sellerTaxpayerId | string | 是 | 销售方纳税人识别号，金蝶 API 必填字段 |

> ⚠️ `requestId` 仅用于网关外层标识，不会编码进金蝶 API `data` 内层。

**请求示例**：
```bash
curl -X POST https://kimpi.cn/api/proxy/v1/digital/query \
  -H "Content-Type: application/json" \
  -H "X-Proxy-Api-Key: <API_KEY>" \
  -H "X-Proxy-Timestamp: <TIMESTAMP>" \
  -H "X-Proxy-Signature: <SIGNATURE>" \
  -d '{"requestId": "REQ20260610008", "serialNo": "SN20260601001", "sellerTaxpayerId": "91440300MA5G9GK78Y"}'
```

**成功响应**：
```json
{
  "code": 0,
  "data": {"serialNo": "SN20260601001", "invoiceNo": "12345678", "amount": 1000.00, "status": "已开具"},
  "message": "success"
}
```

---

### 3.5 回调接口（存根实现）

以下接口当前为**存根实现**（仅记录日志并返回 `{"code":0,"message":"received"}`），待 System A 提供转发地址后增加实际转发逻辑。

| 端点 | 方法 | 说明 | 回调触发场景 |
|------|------|------|------------|
| `/api/proxy/v1/callbacks/apply-return` | POST | 开票申请单回退通知 | 发票云侧主动退回开票申请单时触发 |
| `/api/proxy/v1/callbacks/by-invoice` | POST | 按票回调通知 | 每开一张发票回调一次（拆分 N 张则回调 N 次） |
| `/api/proxy/v1/callbacks/by-apply` | POST | 按单批量回调通知 | 所有发票开具完毕后一次性回调（含成功/失败） |

**回调请求体公共字段**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| interfaceCode | string | 是 | 业务编码：`INVOICE.OPEN`（蓝票回调）、`INVOICE.RED`（红票回调）、`INVOICE.CANCEL`（作废回调） |
| returnCode | string | 是 | 回调代码：`0`-成功，`9999`-失败 |
| returnMsg | string | 是 | 回调信息：成功返回 `success`，失败返回原因 |
| data | object/array | 是 | 回调数据体（按票回调为单对象，按单回调为数组） |

> `data` 字段的具体结构与 3.2.1 响应格式一致，包含发票号码、代码、金额、明细、版式文件 URL 等信息。

---

## 附录 A：调用链路

```
System A → https://kimpi.cn/api/proxy/v1/*  ──Nginx──► proxy:8001 ──httpx──► 金蝶发票云
                                      │                    │
                                  30s timeout           60s read timeout
```

## 附录 B：环境确认

**当前部署的 proxy 默认调用金蝶发票云测试环境**。

证据：
1. `kdcloud_client.py:19` — `_current_env: str = "test"`
2. `main.py:40` — `init_kdcloud_client()` 无参调用，默认 `env="test"`
3. 各端点 `_get_env()` — `return request.headers.get("X-Proxy-Env", "test")`

金蝶 API 调用的实际 base URL：
- 测试环境：`https://baode.test.kdcloud.com`
- 生产环境：`https://baode.kdcloud.com`（需 Header `X-Proxy-Env: prod`）

> ✅ 已确认：ECS `.env` 中金蝶测试环境凭证（APP_ID、APP_SECRET、USER、ACCOUNT_ID）均已配置，proxy 容器可正常调用金蝶发票云测试环境 API。
