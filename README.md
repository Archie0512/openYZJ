# OpenYZJ Backend

云之家机器人 Webhook 后台服务 —— 基于 FastAPI + MongoDB 的异步 Python 应用。

## 目录结构

```
.
├── docker-compose.yml          # Docker 编排配置
├── .env.example                # 环境变量模板
├── .gitignore
├── README.md
└── server/
    ├── Dockerfile              # FastAPI 服务镜像
    ├── requirements.txt        # Python 依赖
    └── app/
        ├── __init__.py
        ├── main.py             # 应用入口 & lifespan
        ├── config.py           # pydantic-settings 配置
        ├── api/
        │   ├── __init__.py
        │   ├── health.py       # 健康检查 GET /health
        │   ├── yunzhijia.py    # 云之家 Webhook（待实现）
        │   └── admin.py        # 管理接口（待实现）
        ├── core/
        │   └── __init__.py     # 安全/依赖注入（待实现）
        ├── db/
        │   ├── __init__.py
        │   ├── mongodb.py      # MongoDB 连接管理
        │   └── indexes.py      # 索引初始化
        ├── models/
        │   └── __init__.py     # 数据模型（待实现）
        └── services/
            └── __init__.py     # 业务逻辑（待实现）
```

## 本地启动

### 前置条件

- Docker & Docker Compose v2+

### 步骤

```bash
# 1. 复制环境变量文件
cp .env.example .env

# 2. ⚠️ 编辑 .env，修改以下必填密钥为你自己的值：
#    - MONGO_PASSWORD（MongoDB 管理员密码）
#    - APP_SECRET_KEY（云之家机器人 appSecret）
#    - ADMIN_TOKEN（管理接口 Bearer Token）

# 3. 启动服务
docker compose up -d

# 4. 验证健康检查
curl http://localhost:8000/health
# 预期返回：{"app":"ok","mongo":"ok","env":"dev"}
```

## 常见命令

```bash
# 查看所有服务日志
docker compose logs -f

# 仅查看 FastAPI 日志
docker compose logs -f fastapi

# 进入 MongoDB shell
docker compose exec mongo mongosh -u admin -p <你的密码> --authenticationDatabase admin

# 停止服务
docker compose down

# 停止服务并清理数据卷（⚠️ 会删除所有 MongoDB 数据）
docker compose down -v
```

## 安全提示

- **绝对不要**将 `.env` 文件提交到版本控制
- 所有默认密钥值（`changeme`、`please-change-this-...`）**必须**在生产环境中替换为强随机值
- 生产部署时 `ENV` 应设为 `production`
