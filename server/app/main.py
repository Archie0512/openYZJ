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
    yield
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

# 挂载静态文件目录（放在路由注册之后，避免前缀匹配拦截其他路由）
os.makedirs(settings.passes_dir, exist_ok=True)
app.mount("/static/passes", StaticFiles(directory=settings.passes_dir), name="passes")
