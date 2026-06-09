# OpenYZJ Backend — V2 项目总结文档

> 最后更新：2026-06-09
> 分支状态：main / staging 已同步

---

## 1. 项目定位

云之家机器人 Webhook 后台服务，面向宝德企业集团内部使用。接收云之家对话消息，按策略路由到不同 Handler 处理，返回文本或消息卡片响应。

---

## 2. 技术栈

| 层面 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python 3.12) |
| 数据库 | MongoDB (motor 异步驱动) |
| 容器化 | Docker + docker-compose |
| 反向代理 | Nginx / OpenResty (1Panel 管理) |
| 二维码 | qrcode[pil] |
| 配置管理 | pydantic-settings v2 (.env) |
| HTTP 客户端 | httpx (异步) |

---

## 3. 核心模块与职责

### 3.1 请求流转路径

```
云之家消息 → Nginx(:443) → FastAPI(:8000)
  POST /api/yunzhijia/webhook/{robot_code}
    → 验签(SHA256+SHA1双路径)
    → _resolve_robot_code() 查机器人配置
    → message_processor.handle()
      → command_router.route(content) 前缀匹配
      → handler.handle() 执行业务逻辑
    → 返回 YunzhijiaResponse (type=2纯文本 / type=25卡片)
```

### 3.2 Handler 策略

| Handler | 触发条件 | 模式 | 说明 |
|---------|---------|------|------|
| AIHandler | `/ai`, `#ai` | is_async=True | 立即返回"思考中"，后台 ai_caller + outbound 推送 |
| ApiHandler | `/api`, `#api` | is_async=False | 同步调用外部 API，2s 内返回 |
| EchoHandler | `/echo` | is_async=False | 原文回显（调试用） |
| MYS4SHandler | 默认兜底 | is_async=False | 解析车牌+事由 → 调金斗云 API → 有牌车返回纯文本，无牌车返回消息卡片 |

**白名单机制**：每个机器人可配置 `allowed_handlers` 字段，未配置时不限制。

### 3.3 消息卡片（无牌车场景）

- **触发**：车牌匹配到"无"前缀（如 `无8G32960`）
- **响应格式**：type=25 卡片消息
- **关键字段**：
  - `content`: "无牌车通行证发送成功"（云之家会同时发一条文本气泡）
  - `forwardControl`: "1"（仅允许内部群组转发）
  - `templateId`: `6a278658e4b0432247a2fa40`
- **卡片数据**：`card_builder.py` 构建 dataContent JSON，包含 appIcon、门店、车牌、时间、事由、二维码URL、备注等
- **二维码**：`qrcode_generator.py` 只生成纯二维码 PNG（~200px），文字信息全由卡片模板展示
- **过期清理**：后台每 10 分钟清理超过 1 小时的 PNG 文件

### 3.4 数据模型

MongoDB 集合：

| 集合 | 用途 |
|------|------|
| `messages` | 消息记录 |
| `sessions` | 会话状态 (TTL 30min) |
| `command_logs` | 指令日志（含外部 API 调用明细） |
| `robots` | 机器人配置（加密密钥/sid/allowed_handlers/推送地址） |

---

## 4. 目录结构

```
.openYZJ/
├── server/
│   ├── app/
│   │   ├── api/
│   │   │   ├── health.py          # 健康检查 /api/health
│   │   │   ├── yunzhijia.py       # Webhook 入口 + 验签
│   │   │   └── admin.py           # 管理接口 CRUD
│   │   ├── core/
│   │   │   ├── crypto.py          # Fernet 加解密
│   │   │   ├── security.py        # 签名验证
│   │   │   ├── admin_auth.py      # Admin Token 鉴权
│   │   │   └── deps.py            # FastAPI 依赖注入
│   │   ├── db/
│   │   │   ├── mongodb.py         # Motor 连接管理
│   │   │   └── indexes.py         # 集合索引定义
│   │   ├── models/
│   │   │   ├── yunzhijia.py       # Webhook 请求/响应模型(含卡片)
│   │   │   ├── robot.py           # 机器人配置模型
│   │   │   ├── message.py         # 消息记录模型
│   │   │   ├── session.py         # 会话模型
│   │   │   └── command_log.py     # 指令日志模型
│   │   ├── services/
│   │   │   ├── handlers/
│   │   │   │   ├── base.py        # BaseHandler 抽象基类
│   │   │   │   ├── mys4s_handler.py  # 金斗云道闸
│   │   │   │   ├── ai_handler.py     # AI 对话
│   │   │   │   ├── api_handler.py    # 通用 API
│   │   │   │   └── echo_handler.py   # 回显调试
│   │   │   ├── message_processor.py  # 消息处理主入口
│   │   │   ├── command_router.py     # 前缀路由
│   │   │   ├── card_builder.py       # 卡片 dataContent 构建
│   │   │   ├── qrcode_generator.py   # 纯二维码 PNG 生成
│   │   │   ├── pass_cleanup.py       # PNG 过期清理
│   │   │   ├── ai_caller.py          # AI API 调用
│   │   │   ├── api_caller.py         # 通用外部 API 调用
│   │   │   ├── outbound.py           # 出站消息推送
│   │   │   └── storage.py            # 持久化操作
│   │   ├── config.py              # pydantic-settings 全局配置
│   │   └── main.py                # FastAPI 入口 + lifespan
│   ├── tests/                     # pytest 单元测试 (30个)
│   ├── Dockerfile
│   └── requirements.txt
├── docs/                          # 项目文档
│   ├── v2_summary.md              # 本文件
│   ├── 消息卡片.md                # 云之家卡片 API 文档
│   ├── 新增业务技术规范1.1.md     # MYS4S 业务规范
│   ├── 云之家机器人对话流程明细.md # 对话流程参考
│   ├── yzjrob_mys.ini            # 机器人-门店映射参考
│   ├── deploy_test_env.md         # 部署指南
│   └── baota_checklist.md         # 宝塔检查清单
├── nginx/                         # Nginx 配置
│   └── kimpi.cn.conf             # 测试环境配置
├── scripts/
│   ├── deploy.sh                  # 部署脚本
│   ├── bt_test.sh                 # 宝塔测试脚本
│   └── gen_test_sign.py           # 签名生成测试工具
├── docker-compose.yml             # 开发/测试编排
├── docker-compose.prod.yml        # 生产编排
├── .env.example                   # 环境变量示例
└── .gitignore
```

---

## 5. 配置项清单

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `MONGO_USER` / `MONGO_PASSWORD` | (必填) | MongoDB 认证 |
| `MONGO_HOST` | `mongo` | MongoDB 地址 |
| `APP_SECRET_KEY` | (必填) | 应用密钥 |
| `ADMIN_TOKEN` | (必填) | 管理接口 Bearer Token |
| `OPENAI_API_BASE` | `https://api.openai.com/v1` | AI 接口地址 |
| `OPENAI_API_KEY` | `""` | AI 密钥 |
| `OPENAI_MODEL` | `gpt-4o-mini` | AI 模型 |
| `YUNZHIJIA_WEBHOOK_URL` | (默认全局推送地址) | 云之家推送 |
| `MYS4S_SECRET_KEY` | (默认值) | 金斗云签名密钥 |
| `MYS4S_API_KEY` | `baode` | 金斗云 API Key |
| `MYS4S_BASE_URL` | `https://mys4s.cn/grey/openapi` | 金斗云 API 地址 |
| `ENV` | `dev` | 运行环境 (dev/prod) |
| `BASE_URL` | `https://ibowdex.cn` | 对外域名 |
| `PASSES_DIR` | `static/passes` | PNG 存储目录 |
| `MYS4S_CARD_TEMPLATE_ID` | `6a278658e4b0432247a2fa40` | 卡片模板 ID |

---

## 6. 部署环境

| 环境 | 分支 | 服务器 | 域名 |
|------|------|--------|------|
| 生产 | main | 国内 8C8G 本地服务器 | ibowdex.cn |
| 测试 | staging | 香港 2C4G ECS | kimpi.cn |

**部署命令**：`docker compose up -d --build fastapi`

---

## 7. 关键技术约束

| 约束 | 影响 | 应对 |
|------|------|------|
| 3秒响应窗口 | Nginx 2500ms timeout | 同步 handler 必须在此内完成；AI 走异步占位+推送 |
| ICP 备案 | Webhook 地址必须备案域名 | 生产 ibowdex.cn；测试 kimpi.cn 跳过验签 |
| 云之家卡片 content 字段 | 对话机器人强制发送 content 文本消息 | 设为有意义的固定文本 |
| MongoDB 单实例 | 无事务支持 | 业务层幂等设计，msgId 去重 |

---

## 8. 车牌正则规则

```python
# 常规/新能源车牌：省份简称 + 字母 + 5~6位字母数字
# 无牌车：无 + 7位数字和英文（不含O/o，避免与0混淆）
_PLATE_RE = re.compile(
    r"(无[A-NP-Za-np-z0-9]{7}"
    r"|[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁][A-Za-z][A-Za-z0-9]{5,6})"
)
```

---

## 9. 后续开发方向

- **Phase 2**：卡片模板系统 + 按钮交互（回调处理链路）
- **Phase 3**：轻应用接入（OAuth 2.0 + H5 前端）
- **待优化**：AI Handler 卡片化输出、出站推送 rate limiter、集成测试覆盖
