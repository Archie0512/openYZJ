"""代理网关独立 FastAPI 应用入口。

与主 OpenYZJ 服务完全解耦：
- 独立容器部署（proxy 服务）
- 共享同一 MongoDB 实例
- 通过 docker-compose backend 网络通信
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.config import settings
from app import mongodb
from app.db_indexes import ensure_indexes
from app.kdcloud_client import init_kdcloud_client, close_kdcloud_client
from app.token_manager import init_token_manager, start_token_refresh_loop
from app.middleware import RateLimitMiddleware, RequestLoggingMiddleware
from app.router import router as proxy_router
from app.admin import router as admin_router, callback_events_router, forwarding_config_router

# 配置日志
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：连接 MongoDB → 初始化金蝶客户端 → 预取 Token → 启动后台刷新。"""
    log.info("代理网关启动中, env=%s", settings.env)
    await mongodb.connect()
    log.info("MongoDB 已就绪")

    # 初始化代理网关专属集合索引（kdcloud_callbacks 等）
    await ensure_indexes(mongodb.get_db())

    # 初始化金蝶发票云 HTTP 客户端（连接池）
    await init_kdcloud_client()
    log.info("金蝶发票云 HTTP 客户端已就绪")

    # 初始化 TokenManager 并预取 token
    await init_token_manager()

    # 启动后台 Token 主动刷新循环
    asyncio.create_task(start_token_refresh_loop())

    log.info("代理网关已就绪（端口 8001）")
    yield

    # 清理
    await close_kdcloud_client()
    await mongodb.close()
    log.info("代理网关关闭完成")


app = FastAPI(
    title="OpenYZJ Proxy Gateway",
    version="1.0.0",
    lifespan=lifespan,
)

# ── 健康检查 ──────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "proxy-gateway"}


@app.get("/health/ready")
async def health_ready(request: Request):
    """就绪检查：验证 MongoDB 可达。"""
    try:
        db = mongodb.get_db()
        await db.command("ping")
        mongo_ok = True
    except Exception:
        mongo_ok = False
    return {
        "status": "ready" if mongo_ok else "degraded",
        "mongo": mongo_ok,
    }

# ── 路由注册 ──────────────────────────────────────────

# 管理接口（复用 Bearer Token 鉴权）
app.include_router(admin_router)
app.include_router(callback_events_router)
app.include_router(forwarding_config_router)

# 代理 API 路由
app.include_router(proxy_router)

# 中间件（仅拦截 /api/proxy/v1/*）
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
