# OpenYZJ Backend

基于 **FastAPI + MongoDB** 的异步 Python 后端，采用**双服务架构**，两个服务相互解耦、独立容器部署，但**共享同一个 MongoDB 实例**：

| 服务 | 目录 | 端口 | 职责 | 应用入口 |
| --- | --- | --- | --- | --- |
| 云之家机器人后台 | [`server/`](server/) | 8000 | 接收云之家机器人 Webhook、消息处理、卡片/出门单生成、robots 管理 | [`server/app/main.py`](server/app/main.py) |
| 金蝶 KDCloud 发票网关 | [`proxy-server/`](proxy-server/) | 8001 | 代理调用金蝶发票云开放接口、接收并转发发票回调、代理调用方与转发运维管理 | [`proxy-server/app/main.py`](proxy-server/app/main.py) |

两个服务均通过根目录下的**同一份 `.env`** 读取配置（`docker-compose.yml` 用 `env_file: .env` 注入），由 `mongo`（MongoDB 7）承载持久化，经 `backend` 桥接网络互通。生产环境由本地服务器 + 1Panel OpenResty 反向代理对外提供 HTTPS。

---

## 目录结构

```
.
├── docker-compose.yml           # 本地/默认编排：mongo + fastapi(8000) + proxy(8001)
├── docker-compose.prod.yml      # 生产编排：内存兜底 + 日志限额 + 更长冷启动窗口
├── .env.example                 # 环境变量模板（两个服务共用）
├── nginx/                       # OpenResty/Nginx 反代站点配置
├── scripts/                     # 运维脚本（回调重放、机器人预置、签名生成等）
├── docs/                        # 接口文档与部署清单
├── README.md
│
├── server/                      # ── 服务一：云之家机器人后台 ──
│   ├── Dockerfile               # gunicorn + 2 workers，监听 8000
│   ├── requirements.txt
│   └── app/
│       ├── main.py              # 应用入口 & lifespan（连库→建索引→PNG 清理循环）
│       ├── config.py            # pydantic-settings 配置
│       ├── api/
│       │   ├── health.py        # GET /health
│       │   ├── yunzhijia.py     # POST /api/yunzhijia/webhook/{robot_code}
│       │   └── admin.py         # /api/admin/robots CRUD（Bearer 鉴权）
│       ├── core/
│       │   ├── admin_auth.py    # Admin Bearer Token 校验
│       │   ├── crypto.py        # Fernet 加密（robot appSecret）
│       │   ├── deps.py          # 依赖注入（get_db / robot 反查等）
│       │   └── security.py      # 云之家签名校验（SHA256/SHA1）
│       ├── db/
│       │   ├── mongodb.py       # MongoDB 连接管理
│       │   └── indexes.py       # 索引初始化
│       ├── models/
│       │   ├── yunzhijia.py     # Webhook 请求/响应模型
│       │   ├── robot.py         # robots 集合模型
│       │   ├── message.py       # 消息模型
│       │   ├── session.py       # 会话模型
│       │   └── command_log.py   # 指令日志模型
│       └── services/
│           ├── message_processor.py  # 消息处理编排
│           ├── command_router.py     # 指令路由
│           ├── card_builder.py       # 云之家卡片构建
│           ├── qrcode_generator.py   # 二维码生成
│           ├── pass_cleanup.py       # 出门单 PNG 过期清理
│           ├── outbound.py           # 主动外呼云之家
│           ├── ai_caller.py          # OpenAI 兼容调用
│           ├── api_caller.py         # 外部 API 调用
│           ├── storage.py            # messages / sessions 落库
│           └── handlers/             # 消息处理器：echo / ai / api / mys4s
│
└── proxy-server/                # ── 服务二：金蝶 KDCloud 发票网关 ──
    ├── Dockerfile               # gunicorn + 4 workers，监听 8001
    ├── requirements.txt
    └── app/
        ├── main.py              # 应用入口 & lifespan（连库→建索引→金蝶客户端→Token 预取+刷新）
        ├── config.py            # pydantic-settings 配置（含 KDCLOUD_*）
        ├── router.py            # 代理 API 主路由，前缀 /api/proxy/v1
        ├── endpoints/
        │   ├── invoicing.py     # /invoice：create / revoke / query
        │   ├── vehicle.py       # /vehicle：info / invoice / red-flush（机动车）
        │   ├── digital.py       # /digital：batch-query / query（数电票）
        │   └── callbacks.py     # /callbacks：apply-return / by-invoice / by-apply
        ├── admin.py             # Admin API：proxy-clients / callback-events / forwarding-config
        ├── admin_auth.py        # Admin Bearer Token 校验（require_admin）
        ├── auth.py              # 调用方鉴权（X-Proxy-* HMAC-SHA256，require_proxy_auth）
        ├── crypto.py            # Fernet 加密（proxy 调用方 api_secret）
        ├── kdcloud_client.py    # 金蝶发票云 HTTP 客户端（连接池）
        ├── token_manager.py     # 金蝶 access_token 预取与后台刷新
        ├── forwarder.py         # 回调出站转发到 System A
        ├── runtime_config.py    # 运行时开关（自动转发，免重启切换）
        ├── middleware.py        # 限流 + 请求日志（仅拦截 /api/proxy/v1/*）
        ├── models.py            # 请求/响应模型
        ├── mongodb.py           # MongoDB 连接管理
        └── db_indexes.py        # 代理专属集合索引（kdcloud_callbacks 等）
```

---

## 服务一：`server/`（云之家机器人后台）

- **应用入口**：[`server/app/main.py`](server/app/main.py) → FastAPI 应用 `OpenYZJ Backend`，监听 **8000**。
- **容器启动命令**（见 [`server/Dockerfile`](server/Dockerfile)）：
  `gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000`
- **生命周期**：启动时连接 MongoDB、初始化索引，并启动后台任务定时清理过期出门单 PNG；关闭时释放连接。

### 主要路由

| 方法 & 路径 | 说明 | 鉴权 |
| --- | --- | --- |
| `GET /health` | 健康检查，返回 `{"app":"ok","mongo":"ok"｜"error","env":"<env>"}` | 无 |
| `POST /api/yunzhijia/webhook/{robot_code}` | 云之家机器人 Webhook；签名校验（SHA256/SHA1），落库经 BackgroundTasks 异步执行 | 云之家签名 |
| `/api/admin/robots`（POST/GET/PUT/DELETE） | robots 集合 CRUD；appSecret 入库自动 Fernet 加密 | `Authorization: Bearer <ADMIN_TOKEN>` |
| `GET /static/passes/*` | 出门单等静态 PNG 资源 | 无 |

### 配置来源

从根目录 `.env`（pydantic-settings，见 [`server/app/config.py`](server/app/config.py)）读取。**必填**：`MONGO_USER`、`MONGO_PASSWORD`、`APP_SECRET_KEY`、`ADMIN_TOKEN`。可选：`OPENAI_*`（未配置时 `ai_caller` 走 stub）、`ENV`、`LOG_LEVEL`；其余（云之家推送地址、金斗云道闸、卡片模板 ID、`base_url`、`passes_dir` 等）在 `config.py` 中已有默认值，按需在 `.env` 覆盖。

---

## 服务二：`proxy-server/`（金蝶 KDCloud 发票网关）

- **应用入口**：[`proxy-server/app/main.py`](proxy-server/app/main.py) → FastAPI 应用 `OpenYZJ Proxy Gateway`，监听 **8001**。
- **容器启动命令**（见 [`proxy-server/Dockerfile`](proxy-server/Dockerfile)）：
  `gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8001`
- **生命周期**：连接 MongoDB → 初始化代理专属索引 → 初始化金蝶发票云 HTTP 客户端（连接池）→ 预取 access_token → 启动后台 Token 主动刷新循环；关闭时释放客户端与连接。

### 代理 API（前缀 `/api/proxy/v1`）

面向调用方（System A）代理调用金蝶发票云开放接口。鉴权由 `require_proxy_auth` 完成：请求需带 `X-Proxy-Api-Key` / `X-Proxy-Timestamp` / `X-Proxy-Signature`（HMAC-SHA256，时间戳 ±5min 容差），调用方凭据存于 `proxy_clients` 集合。

| 分组 | 端点 | 说明 |
| --- | --- | --- |
| `/invoice` | `POST /create`、`POST /revoke`、`GET /query/{apply_id}` | 开票 / 作废 / 查询 |
| `/vehicle` | `POST /info`、`POST /invoice`、`POST /red-flush` | 机动车：查信息 / 开票 / 红冲 |
| `/digital` | `POST /batch-query`、`POST /query` | 数电票批量 / 单张查询 |
| `/callbacks` | `POST /apply-return`、`POST /by-invoice`、`POST /by-apply` | 接收金蝶发票云回调，落库 `kdcloud_callbacks`；`by-invoice` 开票成功时可自动转发 System A |

> 中间件 `RateLimitMiddleware` / `RequestLoggingMiddleware` 仅拦截 `/api/proxy/v1/*`；健康检查与 Admin 路由不受限流影响。

### Admin API（`Authorization: Bearer <ADMIN_TOKEN>`）

由 `require_admin` 统一鉴权，用于运维管理。**仅限内网/反代白名单访问，勿对公网暴露**。

| 路径 | 能力 |
| --- | --- |
| `/api/admin/proxy-clients`（POST/GET/PUT/DELETE） | 代理调用方注册与管理；`api_secret` 入库自动 Fernet 加密，对外视图剥离密钥 |
| `/api/admin/callback-events`（GET 列表 / GET `/{id}` 详情 / POST `/{id}/replay`） | `kdcloud_callbacks` 回调审计只读查询；`replay` 将已落库回调（仅 `by-invoice`、`returnCode=0`）重放转发到 System A |
| `/api/admin/forwarding-config`（GET / PUT） | 查看/切换自动转发开关（存 `proxy_settings`，运行时生效、免重启） |

### 回调转发链路

金蝶发票云 → `POST /api/proxy/v1/callbacks/*` → 落库 `kdcloud_callbacks` → 依据 `forwarding-config` 自动转发开关，将 `by-invoice` 开票成功回调经 `forwarder.py` 出站转发到对应调用方的 `callback_url`（System A）。失败或需补发时可用 Admin `replay` 接口重放。

### 配置来源

从根目录 `.env`（pydantic-settings，见 [`proxy-server/app/config.py`](proxy-server/app/config.py)）读取。除与 `server/` 共享的 `MONGO_*`、`APP_SECRET_KEY`（Fernet 加密调用方密钥）、`ADMIN_TOKEN`、`ENV`、`LOG_LEVEL` 外，还需下列金蝶相关变量：

| 变量 | 说明 |
| --- | --- |
| `KDCLOUD_TEST_BASE_URL` / `KDCLOUD_PROD_BASE_URL` | 金蝶发票云测试 / 生产网关地址 |
| `KDCLOUD_APP_ID` / `KDCLOUD_APP_SECRET` | 金蝶开放平台应用凭据 |
| `KDCLOUD_USER` / `KDCLOUD_ACCOUNT_ID` | 金蝶用户名 / 账套 ID |
| `KDCLOUD_USERTYPE`（默认 `UserName`）/ `KDCLOUD_LANGUAGE`（默认 `en`） | 用户类型 / 语言 |
| `KDCLOUD_TEST_TENANT_ID` / `KDCLOUD_PROD_TENANT_ID` | 按环境隔离的租户标识（`env=prod` 用生产，否则用测试） |
| `KDCLOUD_BUSINESS_SYSTEM_CODE` / `KDCLOUD_AES_KEY` | 金蝶统一网关业务系统编码 / data 字段 AES 加密密钥 |

> ⚠️ 测试与生产的金蝶凭据/租户**完全隔离**，切勿混用。

---

## 本地启动

### 前置条件

- Docker & Docker Compose v2+

### 步骤

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. ⚠️ 编辑 .env，至少修改以下必填项为你自己的值：
#    - MONGO_PASSWORD           MongoDB 管理员密码
#    - APP_SECRET_KEY           Fernet 密钥（server 云之家 appSecret / proxy 调用方 api_secret 加密）
#    - ADMIN_TOKEN              两个服务共用的管理接口 Bearer Token
#    若需启用金蝶网关，另配置 KDCLOUD_* 系列变量（见上文“配置来源”）

# 3. 启动全部服务（mongo + fastapi + proxy）
docker compose up -d

# 4. 验证健康检查
curl http://localhost:8000/health       # server：{"app":"ok","mongo":"ok","env":"dev"}
curl http://localhost:8001/health        # proxy ：{"status":"ok","service":"proxy-gateway"}
curl http://localhost:8001/health/ready  # proxy ：校验 MongoDB 可达
```

## 生产部署

生产环境使用独立编排文件 [`docker-compose.prod.yml`](docker-compose.prod.yml)（MongoDB 内存兜底、容器日志限额、更长冷启动窗口），与 `docker-compose.yml` **互斥使用**（共享同一 `mongo_data` 卷，勿同时运行）：

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

对外流量由本地服务器上的 1Panel OpenResty 反向代理到 8000 / 8001（HTTPS 443，站点配置见 [`nginx/`](nginx/)）。

## 常见命令

```bash
# 查看全部服务日志
docker compose logs -f

# 仅查看某个服务日志
docker compose logs -f fastapi   # 云之家机器人后台
docker compose logs -f proxy     # 金蝶发票网关

# 进入 MongoDB shell
docker compose exec mongo mongosh -u admin -p <你的密码> --authenticationDatabase admin

# 停止服务
docker compose down

# 停止服务并清理数据卷（⚠️ 会删除所有 MongoDB 数据）
docker compose down -v
```

## 运行测试

测试基于 **pytest**，共 **122** 项用例，分布在两个服务：`proxy-server/tests`（92 项）与 `server/tests`（30 项）。两个服务的顶层包同名（都叫 `app`），无法被同一个 pytest 进程同时导入，因此两套件需在各自独立的进程中依次运行。

### 安装测试依赖

pytest 属于开发依赖，未写入服务的 `requirements.txt`（避免进入生产镜像）。首次运行前，在仓库根目录一次性安装两个服务的运行依赖及 pytest：

```bash
pip install -r proxy-server/requirements.txt -r server/requirements.txt pytest
```

### 一条命令运行全部 122 项测试

在**仓库根目录**执行下面这条命令即可运行全部 122 项测试（依次运行两套件，任一失败即返回非零退出码）：

```bash
# Linux / macOS / Git Bash
python -m pytest proxy-server/tests && python -m pytest server/tests
```

```powershell
# Windows PowerShell
python -m pytest proxy-server/tests; if ($LASTEXITCODE -eq 0) { python -m pytest server/tests }
```

预期结果：先输出 `92 passed`，再输出 `30 passed`，合计 122 项全部通过。

> 为什么不是单个 `pytest` 进程？两个服务都以 `app` 作为顶层包名，`import app` 在同一进程内只能解析到其中一个，因此必须分两个进程运行——这也是上面命令由两段组成的原因。

### 单独运行某个服务

两个服务各自内置了 `pytest.ini`（`testpaths` 指向其 `tests/`），进入对应目录直接运行 `pytest` 即可，无需指定路径或猜测测试根目录：

```bash
cd proxy-server && pytest      # 92 项
cd server && pytest            # 30 项
```

## 安全提示

- **绝对不要**将 `.env` 提交到版本控制。
- 所有默认密钥值（`changeme`、`please-change-this-...`）**必须**在生产环境替换为强随机值。
- 生产部署时 `ENV` 应设为 `production`。
- Admin API（`/api/admin/*`）与 MongoDB 端口仅限内网/反代白名单访问，禁止直接对公网暴露。
