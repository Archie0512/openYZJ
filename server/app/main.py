"""FastAPI 应用入口。"""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from app.api import health, yunzhijia
from app.api import admin
from app.api import open_api
from app.config import settings
from app.db import mongodb
from app.db.indexes import ensure_indexes
from app.services.pass_cleanup import cleanup_expired_passes

# 代理网关模块（可选，通过 proxy_api_enabled 控制）
from app.proxy.kdcloud.client import init_kdcloud_client, close_kdcloud_client
from app.proxy.token_manager import init_token_manager, start_token_refresh_loop
from app.proxy.middleware import RateLimitMiddleware, RequestLoggingMiddleware

# 配置日志
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


async def _cleanup_loop():
    """后台定时任务：每 10 分钟清理超过 1 小时的 PNG 文件。"""
    while True:
        await asyncio.sleep(600)  # 10 分钟
        cleanup_expired_passes()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时连接 MongoDB 并初始化索引，关闭时释放连接。"""
    log.info("应用启动中, env=%s", settings.env)
    await mongodb.connect()
    await ensure_indexes(mongodb.get_db())
    log.info("MongoDB 已就绪")
    asyncio.create_task(_cleanup_loop())

    # ── 代理网关初始化 ──
    if settings.proxy_api_enabled:
        await init_kdcloud_client()
        await init_token_manager()
        asyncio.create_task(start_token_refresh_loop())
        log.info("代理网关已就绪")

    yield

    # ── 代理网关清理 ──
    if settings.proxy_api_enabled:
        await close_kdcloud_client()

    await mongodb.close()
    log.info("应用关闭完成")


app = FastAPI(
    title="OpenYZJ Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# 注册路由
app.include_router(health.router)
app.include_router(yunzhijia.router)
app.include_router(admin.router)

# 开放 API 路由（可通过配置开关控制）
if settings.open_api_enabled:
    app.include_router(open_api.router)

# 代理网关路由（可通过配置开关控制）
if settings.proxy_api_enabled:
    from app.proxy.router import router as proxy_router
    app.include_router(proxy_router)
    # 注册代理中间件（仅拦截 /api/proxy/v1/*）
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

# 代理客户端管理接口（复用 admin 鉴权）
from app.proxy.admin import router as proxy_admin_router
app.include_router(proxy_admin_router)

# 挂载静态文件目录（放在路由注册之后，避免前缀匹配拦截其他路由）
os.makedirs(settings.passes_dir, exist_ok=True)
app.mount("/static/passes", StaticFiles(directory=settings.passes_dir), name="passes")

# 挂载 miniapp 轻应用静态文件（仅当目录存在时）
_miniapp_dir = "../miniapp"
if os.path.isdir(_miniapp_dir):
    app.mount("/miniapp", StaticFiles(directory=_miniapp_dir, html=True), name="miniapp")
else:
    log.warning("miniapp 目录不存在，跳过轻应用静态文件挂载（非生产部署可忽略）")
