"""运行时配置（存 MongoDB proxy_settings 集合，动态可切换，免重启）。

自动转发开关不放 .env（改 .env 需重启容器），改存 DB + admin API 动态切换。
hot path（每条回调落库）用 get_auto_forward_enabled，带 10s 内存缓存避免频繁查库。
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

from app import mongodb

_SETTINGS_ID = "forwarding"
_CACHE_TTL = 10.0  # 秒

# 内存缓存：value → (enabled, expire_at_monotonic)
_cache: dict[str, tuple[bool, float]] = {}


def _clear_cache() -> None:
    """清空缓存（set 之后调用，或测试用）。"""
    _cache.clear()


async def get_auto_forward_enabled() -> bool:
    """读自动转发开关（hot path）。10s 内存缓存；查库失败/无记录缺省 False。"""
    now = time.monotonic()
    cached = _cache.get(_SETTINGS_ID)
    if cached and cached[1] > now:
        return cached[0]
    try:
        doc = await mongodb.get_db().proxy_settings.find_one({"_id": _SETTINGS_ID})
        enabled = bool(doc.get("auto_forward_enabled")) if doc else False
    except Exception:  # noqa: BLE001 — 查库异常时保守视为关闭
        enabled = False
    _cache[_SETTINGS_ID] = (enabled, now + _CACHE_TTL)
    return enabled


async def set_auto_forward_enabled(enabled: bool) -> None:
    """更新开关并清缓存（立即生效）。"""
    await mongodb.get_db().proxy_settings.update_one(
        {"_id": _SETTINGS_ID},
        {"$set": {
            "auto_forward_enabled": bool(enabled),
            "updated_at": datetime.now(timezone.utc),
        }},
        upsert=True,
    )
    _clear_cache()


async def get_forwarding_config() -> dict:
    """返回完整配置（admin GET 用，不走缓存，保证读到最新）。"""
    try:
        doc = await mongodb.get_db().proxy_settings.find_one({"_id": _SETTINGS_ID})
    except Exception:  # noqa: BLE001
        doc = None
    return {
        "auto_forward_enabled": bool(doc.get("auto_forward_enabled")) if doc else False,
        "updated_at": doc.get("updated_at") if doc else None,
    }
