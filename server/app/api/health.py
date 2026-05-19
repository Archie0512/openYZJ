"""健康检查接口。"""
from __future__ import annotations

import logging

from fastapi import APIRouter

from app.config import settings
from app.db import mongodb

log = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """健康检查：同时检查应用与 MongoDB 状态。

    返回结构：
        {"app": "ok", "mongo": "ok" | "error", "env": "<env>"}
    """
    mongo_status = "ok"
    try:
        client = mongodb.get_client()
        await client.admin.command("ping")
    except Exception as exc:  # noqa: BLE001 - 健康检查需捕获所有异常
        log.warning("MongoDB 健康检查失败: %s", exc)
        mongo_status = "error"

    return {"app": "ok", "mongo": mongo_status, "env": settings.env}
