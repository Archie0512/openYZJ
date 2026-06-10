"""代理网关主路由。

组装所有金蝶发票云端点子路由，统一前缀 /api/proxy/v1。
所有端点通过 require_proxy_auth 鉴权。
"""
from __future__ import annotations

from fastapi import APIRouter

from app.endpoints import (
    callbacks,
    digital,
    invoicing,
    vehicle,
)

router = APIRouter(prefix="/api/proxy/v1", tags=["Proxy Gateway"])

# ── 开票（P1-P2）────────────────────────────────────
router.include_router(invoicing.router, prefix="/invoice")

# ── 机动车（P3, P6）─────────────────────────────────
router.include_router(vehicle.router, prefix="/vehicle")

# ── 数电票查询（P4）─────────────────────────────────
router.include_router(digital.router, prefix="/digital")

# ── 回调（P5）──────────────────────────────────────
router.include_router(callbacks.router, prefix="/callbacks")
