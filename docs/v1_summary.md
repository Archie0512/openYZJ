# OpenYZJ V1 全链路压缩总结

## 技术栈

| 层次 | 技术 |
|------|------|
| Web框架 | Python 3.12 + FastAPI 0.136 + uvicorn + gunicorn |
| 数据库 | MongoDB 7，PyMongo 4.12+ Async API（已弃用 motor） |
| 部署 | Docker Compose（dev/prod 两套） |
| 配置 | pydantic-settings v2 |
| HTTP客户端 | httpx |
| 加密 | cryptography Fernet（加密 appSecret） |

---

## 目录结构

```
.openYZJ/
├── server/app/
│   ├── main.py              # FastAPI 入口 + lifespan
│   ├── config.py            # Settings（pydantic-settings）
│   ├── api/
│   │   ├── health.py        # GET /health
│   │   ├── yunzhijia.py     # POST /api/yunzhijia/webhook/{robot_code}
│   │   └── admin.py         # Admin CRUD /api/admin/robots（Bearer Token）
│   ├── core/
│   │   ├── security.py      # 双路径签名验证 SHA256 + SHA1
│   │   ├── deps.py          # get_db, get_robot_secret
│   │   ├── crypto.py        # Fernet 加解密
│   │   └── admin_auth.py    # Bearer Token 鉴权
│   ├── db/
│   │   ├── mongodb.py       # AsyncClient 连接管理
│   │   └── indexes.py       # 索引创建（含 TTL）
│   ├── models/              # yunzhijia / message / session / command_log / robot
│   └── services/
│       ├── message_processor.py  # 总调度入口
│       ├── command_router.py     # 前缀路由（/ai /api /echo）
│       ├── storage.py            # 落库（messages + sessions）
│       ├── api_caller.py         # httpx 通用 API 调用
│       ├── ai_caller.py          # OpenAI 兼容协议
│       ├── outbound.py           # 云之家主动推送
│       └── handlers/             # base / echo / api / ai
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── nginx/kimpi.cn.conf
└── scripts/deploy.sh
```

---

## 请求流转路径

```
云之家 POST
  → Nginx(:443) proxy_read_timeout=2500ms
  → FastAPI(:8000) POST /api/yunzhijia/webhook/{robot_code}
      ├─ robot_code == "test-robotId" → 跳过验签，立即返回 200
      └─ 正式请求:
          → get_robot_secret（从 robots 集合读取 Fernet 解密后的 appSecret）
          → verify_sign（先 SHA256，失败再 SHA1，任一通过即合法）
          → BackgroundTasks: storage（messages + sessions upsert）
          → message_processor.handle()
              → command_router.route()
                  /ai   → AIHandler（立即返回"思考中…"，后台 ai_caller + outbound 推送）
                  /api  → ApiHandler（同步调用，2s 内返回）
                  /echo → EchoHandler（原文回显）
                  默认  → 待配置
```

---

## 关键环境变量（.env）

```dotenv
# MongoDB
MONGO_USER=
MONGO_PASSWORD=
MONGO_HOST=
MONGO_PORT=27017
MONGO_DB=openyzj

# 安全
APP_SECRET_KEY=       # Fernet 派生密钥（加密 appSecret 用）
ADMIN_TOKEN=          # Admin API Bearer Token

# AI（OpenAI 兼容）
OPENAI_API_BASE=
OPENAI_API_KEY=
OPENAI_MODEL=

# 云之家
YUNZHIJIA_WEBHOOK_URL=

# 运行
ENV=production        # dev / test / production
LOG_LEVEL=INFO
```

---

## 部署速查

```bash
cd /opt/openyzj
git pull
docker compose up -d --build fastapi   # 仅重建 fastapi
docker compose up -d --build           # 全量重建
docker compose logs fastapi --tail=50  # 查日志
curl -fsS http://127.0.0.1:8000/health # 健康检查
```

---

## 核心设计决策 & 约束

| 项目 | 说明 |
|------|------|
| 3s 响应硬约束 | Nginx `proxy_read_timeout 2500ms`，FastAPI 必须在 2.5s 内响应 |
| 测试机器人 | `robot_code=test-robotId` 跳过验签（云之家内部密钥无法在外部验证） |
| 签名双路径 | 先 SHA256，失败再 SHA1；任一通过即合法，兼容新旧云之家版本 |
| Sessions TTL | 1800s（最后活动后 30 分钟自动过期） |
| AI 异步占位 | 立即返回"思考中…"占位，后台完成后通过 `outbound.py` 主动推送 |
| appSecret 加密 | Fernet 加密存储；旧明文记录在读取时自动迁移为密文 |
| ENV=test 兜底 | 测试环境下 `test-robotId` 可使用固定密钥，无需配置 robot 记录 |
| 域名要求 | 云之家 Webhook 消息接收地址必须为 **ICP 备案域名**，IP 直连无效 |

---

## MongoDB 集合概览

| 集合 | 用途 | 关键字段 |
|------|------|---------|
| `robots` | 机器人配置 | `robot_code`, `app_id`, `app_secret`(加密) |
| `messages` | 消息记录 | `msg_id`, `robot_code`, `sender_id`, `content` |
| `sessions` | 会话状态 | `session_key`, `last_active`(TTL索引) |
| `command_logs` | 指令日志 | `command`, `handler`, `status`, `created_at` |
