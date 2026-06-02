# V2 功能规划压缩总结

## 1. V1 现有架构快照

**请求入口**：云之家 POST → Nginx(:443, proxy_read_timeout=2500ms) → FastAPI(:8000) `POST /api/yunzhijia/webhook/{robot_code}`。验签采用 SHA256+SHA1 双路径策略，appSecret Fernet 加密存储。

**Handler 模式**：`message_processor.handle()` → `command_router.route(content)` 按前缀匹配分发。当前注册 4 个 handler：
- `/ai`, `#ai` → AIHandler（is_async=True，立即返回"思考中…"占位，后台 ai_caller + outbound 推送）
- `/api`, `#api` → ApiHandler（同步调用，2s 内返回）
- `/echo` → EchoHandler（原文回显，调试用）
- 默认兜底 → MYS4SHandler（解析车牌+事由 → 调用金斗云道闸 API 发送通行证）

**数据模型**：MongoDB 4 集合——`messages`(消息记录)、`sessions`(会话状态, TTL 30min)、`command_logs`(指令日志含外部 API 调用明细)、`robots`(机器人配置, 含加密密钥/sid/per-robot推送地址)。

**出站推送**：`outbound.py push_card_message()` 支持 per-robot webhook_push_url 优先、全局 fallback。当前仅传 `{robotId, sessionId, content}` 纯文本 payload。

**管理面**：`/api/admin/robots` Bearer Token 鉴权 CRUD，支持创建/列表/查询/更新/删除机器人配置。

---

## 2. V2 待开发功能清单

### 2.1 消息卡片（Card Message）

**云之家卡片消息格式**（待确认具体API文档）：
- 云之家支持富文本消息（markdown-like）、图文混排卡片、按钮交互卡片
- 消息 type 字段扩展：当前 `type=2` 为纯文本，卡片类型预计为 `type=10` 或独立 card 字段
- 按钮卡片可能支持 callback_url 回调（点击后云之家回调服务端）

**模板系统设计方向**：
| 方案 | 优势 | 劣势 |
|------|------|------|
| Jinja2 模板 | 灵活、支持条件/循环逻辑、前端设计师可直接编辑 | 运行时渲染有开销、模板安全需限制 |
| 结构化 JSON Builder | 类型安全、IDE 补全友好、易于单测验证 | 复杂卡片可读性差、修改需改代码 |

**推荐**：核心用 JSON Builder（Pydantic model 定义 CardPayload），高频变动卡片用 Jinja2 模板覆盖。

**push 通道复用**：
- `outbound.py` 扩展 `push_card_message()` 签名，新增 `card_type: str = "text"` 参数
- `card_type="text"` 走现有纯文本逻辑
- `card_type="rich"/"button"/"image"` 构建对应 card payload 结构
- 新增 `push_rich_card()` 便捷封装，内部调用 `push_card_message(card_type="rich", ...)`

**与现有 Handler 集成点**：
- AIHandler：AI 回复改为卡片推送（markdown 渲染 + "重新生成"按钮）
- MYS4SHandler：通行证结果用图文卡片展示（含二维码图片 URL、车牌、有效期）
- 新增 CardHandler：专门处理按钮回调事件（云之家 POST 回调 → 路由到对应业务逻辑）

### 2.2 应用类功能

**独立应用入口 vs webhook 扩展选型**：

| 维度 | Webhook 扩展 | 独立轻应用 |
|------|-------------|-----------|
| 开发成本 | 低，复用现有路由+handler 体系 | 中，需新增 OAuth + 前端页面 |
| 交互能力 | 受限于对话框，按钮回调可部分弥补 | 完整 H5/小程序交互 |
| 适用场景 | 查询/通知/简单操作 | 表单录入/复杂工作流/仪表盘 |
| 权限粒度 | 机器人级（所有对话者共享配置） | 用户级（可区分角色） |

**推荐**：Phase 1-2 以 Webhook 扩展为主（卡片+按钮回调覆盖 80% 场景），Phase 3 按需引入轻应用。

**权限模型**：
- 当前：机器人级 appSecret + Admin Bearer Token
- V2 扩展：若引入轻应用，需接入云之家 OAuth2.0（authorization_code 流程获取 user access_token）
- 中间态：按钮回调场景可复用 webhook 验签，无需额外 OAuth

**前端适配**：
- 卡片消息阶段：无需前端，云之家原生渲染
- 轻应用阶段：需 H5 页面（Vue3/React SPA），通过云之家 JSAPI 获取用户身份
- 小程序：优先级低，云之家小程序生态不成熟

**与现有 admin API 关系**：
- `robots` 集合扩展字段：`card_templates[]`, `app_config{}`
- Admin API 新增模板管理端点：`/api/admin/robots/{code}/templates`
- 轻应用若独立部署，共享 MongoDB，通过内部 service 层复用业务逻辑

---

## 3. 技术约束与已知限制

| 约束 | 影响 | 应对策略 |
|------|------|---------|
| 3秒响应窗口 | Nginx 2500ms hard timeout，同步 handler 必须在此内完成 | 卡片构建耗时操作走异步占位+后台推送模式 |
| 云之家 API 限流 | 推送频率上限待确认（预估 100次/分/机器人） | 出站层加 rate limiter，批量通知合并推送 |
| ICP 备案要求 | Webhook 地址必须备案域名，测试环境 kimpi.cn(香港) 无法注册正式机器人 | 生产用 ibowdex.cn，测试用 test-robotId 跳过验签 |
| 双环境差异 | 生产 8C8G 国内 / 测试 2C4G 香港，网络延迟不同 | 金斗云等国内 API 调用仅生产环境可用，测试环境 mock |
| 卡片消息格式 | 云之家文档更新频率低，部分字段需实测确认 | 抽象 CardPayload 模型，format 变更只改模型层 |
| MongoDB 单实例 | 无副本集，无事务支持 | 业务层幂等设计，command_log 用 msgId 去重 |

---

## 4. V1 → V2 依赖关系

| V1 现有模块 | V2 变更类型 | 说明 |
|------------|-----------|------|
| `outbound.py` | **扩展** | 新增 card_type 参数、CardPayload 构建逻辑、rich/button/image 推送方法 |
| `command_router.py` | **扩展** | 新增 card_callback 路由（按钮回调事件分发） |
| `message_processor.py` | **微调** | 识别 callback 类型消息，走独立分发路径 |
| `handlers/ai_handler.py` | **扩展** | 推送结果改为卡片格式，附加"重新生成"按钮 |
| `handlers/mys4s_handler.py` | **扩展** | 通行证结果用图文卡片+二维码展示 |
| `models/yunzhijia.py` | **扩展** | 新增 CardPayload / CallbackEvent Pydantic 模型 |
| `api/yunzhijia.py` | **微调** | 识别 callback POST 请求（区分普通消息 vs 按钮回调） |
| `api/admin.py` | **扩展** | 新增模板 CRUD 端点 |
| `models/robot.py` | **扩展** | 增加 card_templates / app_config 字段 |
| — | **新建** `services/card_builder.py` | 卡片 payload 构建器（JSON Builder + Jinja2 渲染） |
| — | **新建** `services/handlers/card_callback_handler.py` | 按钮回调事件处理 |
| — | **新建** `models/card_template.py` | 卡片模板数据模型 |
| — | **新建** `templates/cards/` | Jinja2 卡片模板目录（可选） |

---

## 5. 推荐实施路径

### Phase 1：卡片消息基础能力（1-2 周）
1. 定义 `CardPayload` Pydantic 模型（text/rich/image 三种 type）
2. `outbound.py` 扩展支持 card payload 推送
3. MYS4SHandler 通行证结果改为图文卡片输出
4. AIHandler 回复改为 rich 卡片（markdown + 元信息）
5. 端到端测试：测试环境验证卡片渲染效果

### Phase 2：模板系统 + 按钮交互（2-3 周）
1. `card_builder.py` 实现 JSON Builder + Jinja2 双模式
2. Admin API 新增模板管理（CRUD + 预览）
3. 实现按钮回调处理链路：`yunzhijia.py` 识别回调 → `card_callback_handler.py` 分发
4. AI "重新生成"按钮 → 回调触发重新调用 ai_caller
5. `robots` 集合新增 `card_templates` 字段

### Phase 3：应用类扩展（按需，4-6 周）
1. 评估云之家轻应用接入文档与 OAuth 流程
2. 若需要：新增 `/api/app/` 路由组 + OAuth middleware
3. H5 前端骨架搭建（如需仪表盘/表单场景）
4. 与现有 service 层复用：card_builder / ai_caller / outbound 等模块共享
