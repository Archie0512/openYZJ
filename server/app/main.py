"""FastAPI 应用入口。"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from app.api import health, yunzhijia
from app.api import admin
from app.config import settings
from app.db import mongodb
from app.db.indexes import ensure_indexes

# 配置日志
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时连接 MongoDB 并初始化索引，关闭时释放连接。"""
    log.info("应用启动中, env=%s", settings.env)
    await mongodb.connect()
    await ensure_indexes(mongodb.get_db())
    log.info("MongoDB 已就绪")
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

# 挂载静态文件目录（放在路由注册之后，避免前缀匹配拦截其他路由）
os.makedirs("static/passes", exist_ok=True)
app.mount("/static/passes", StaticFiles(directory="static/passes"), name="passes")
