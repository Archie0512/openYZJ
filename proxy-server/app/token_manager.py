"""金蝶发票云 Token 生命周期管理器。

管理 app_token → access_token 链路：
- access_token 有效期 2 小时，提前 refresh_margin 秒刷新
- 使用 asyncio.Lock 防止同进程内并发刷新
- MongoDB 原子操作保证跨 worker 一致性
- 后台定时任务主动刷新，避免请求关键路径上的等待
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone

from pymongo.asynchronous.database import AsyncDatabase

from app.config import settings
from app import mongodb
from app import kdcloud_client as kdcloud

log = logging.getLogger(__name__)

# 单例
_token_manager: TokenManager | None = None


class TokenManager:
    """管理金蝶发票云 access_token 的生命周期。"""

    def __init__(self, db: AsyncDatabase) -> None:
        self._db = db
        self._lock = asyncio.Lock()
        self._refresh_margin = settings.proxy_token_refresh_margin  # 默认 600s

    async def get_valid_access_token(self, env: str = "test") -> str:
        """获取有效的 access_token。

        1. 从 MongoDB kdcloud_tokens 读取缓存
        2. 若 access_token 在有效期内且距过期 > refresh_margin，直接返回
        3. 若 app_token 有效，用它换取新 access_token
        4. 否则从 get_app_token() 开始完整流程
        5. 更新 MongoDB，返回 access_token
        """
        # ── 1. 读取缓存 ──
        doc = await self._db.kdcloud_tokens.find_one(
            {"account_id": settings.kdcloud_account_id, "env": env}
        )

        now = time.time()
        if doc and doc.get("access_token"):
            expires_at = doc.get("access_token_expires_at")
            if expires_at:
                expire_ts = expires_at.timestamp() if isinstance(expires_at, datetime) else float(expires_at)
                if now + self._refresh_margin < expire_ts:
                    log.debug("[token_mgr] 缓存 access_token 有效")
                    return doc["access_token"]

        # ── 2. 需要刷新，获取锁 ──
        async with self._lock:
            # 双重检查：锁内重新读取（可能已被其他协程刷新）
            doc = await self._db.kdcloud_tokens.find_one(
                {"account_id": settings.kdcloud_account_id, "env": env}
            )
            now2 = time.time()
            if doc and doc.get("access_token"):
                expires_at = doc.get("access_token_expires_at")
                if expires_at:
                    expire_ts = expires_at.timestamp() if isinstance(expires_at, datetime) else float(expires_at)
                    if now2 + 60 < expire_ts:  # 锁内只需 1 分钟 margin
                        log.debug("[token_mgr] 锁内双重检查：token 已被刷新")
                        return doc["access_token"]

            # ── 3. 执行刷新 ──
            try:
                token_data = await self._do_full_refresh(env)
                log.info("[token_mgr] access_token 刷新成功 env=%s", env)
                return token_data["access_token"]
            except Exception:
                log.exception("[token_mgr] access_token 刷新失败 env=%s", env)
                # 如果缓存中有旧 token（即使即将过期），降级返回
                if doc and doc.get("access_token"):
                    log.warning("[token_mgr] 降级返回即将过期的缓存 token")
                    return doc["access_token"]
                raise

    async def ensure_fresh(self, env: str = "test") -> None:
        """主动确保 token 新鲜（供后台定时任务调用）。"""
        try:
            await self.get_valid_access_token(env)
        except Exception:
            log.exception("[token_mgr] 后台刷新失败")

    async def _do_full_refresh(self, env: str) -> dict:
        """执行 token 刷新：复用有效 app_token，仅刷新 access_token。

        如果 MongoDB 中缓存的 app_token 仍在有效期内（剩余 > 5 分钟），
        复用它跳过 get_app_token 调用，直接获取新 access_token。
        """
        # 先尝试复用缓存的 app_token
        doc = await self._db.kdcloud_tokens.find_one(
            {"account_id": settings.kdcloud_account_id, "env": env}
        )

        app_token = None
        app_expires_at = None
        if doc and doc.get("app_token"):
            app_expires = doc.get("app_token_expires_at")
            if app_expires:
                expire_ts = app_expires.timestamp() if isinstance(app_expires, datetime) else float(app_expires)
                if time.time() + 300 < expire_ts:  # app_token 还有 5 分钟以上
                    app_token = doc["app_token"]
                    app_expires_at = app_expires if isinstance(app_expires, datetime) else datetime.fromtimestamp(expire_ts, tz=timezone.utc)
                    log.debug("[token_mgr] 复用缓存 app_token")

        # 如果 app_token 过期，获取新的
        if not app_token:
            app_resp = await kdcloud.get_app_token(env)
            app_data = app_resp.get("data", {})
            if not app_data.get("success"):
                raise RuntimeError(f"获取 app_token 失败: {app_data.get('error_desc', app_resp)}")
            app_token = app_data["app_token"]
            app_expire_time = app_data.get("expire_time", 0)
            app_expires_at = datetime.fromtimestamp(app_expire_time / 1000, tz=timezone.utc)

        # 获取 access_token（始终刷新）
        login_resp = await kdcloud.login(app_token, env)
        login_data = login_resp.get("data", {})
        if not login_data.get("success"):
            raise RuntimeError(f"获取 access_token 失败: {login_data.get('error_desc', login_resp)}")
        access_token = login_data["access_token"]
        access_expire_time = login_data.get("expire_time", 0)
        access_expires_at = datetime.fromtimestamp(access_expire_time / 1000, tz=timezone.utc)

        # 持久化到 MongoDB
        now = datetime.now(timezone.utc)
        await self._db.kdcloud_tokens.update_one(
            {"account_id": settings.kdcloud_account_id, "env": env},
            {
                "$set": {
                    "app_token": app_token,
                    "access_token": access_token,
                    "app_token_expires_at": app_expires_at,
                    "access_token_expires_at": access_expires_at,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "account_id": settings.kdcloud_account_id,
                    "env": env,
                },
            },
            upsert=True,
        )

        return {"access_token": access_token, "expires_at": access_expires_at}


def _get_db() -> AsyncDatabase:
    return mongodb.get_db()


def get_token_manager() -> TokenManager:
    """获取 TokenManager 单例。"""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager(_get_db())
    return _token_manager


async def init_token_manager() -> None:
    """初始化 TokenManager（在应用启动时调用，预取 token）。

    同时为 test 和 prod 环境预取 token，确保首次请求无需等待冷启动。
    """
    tm = get_token_manager()
    for env in ("test", "prod"):
        try:
            await tm.ensure_fresh(env)
            log.info("[token_mgr] 初始化完成 env=%s，token 已就绪", env)
        except Exception:
            log.warning("[token_mgr] 初始化 env=%s 时预取 token 失败，将在首次请求时重试", env)


async def start_token_refresh_loop() -> None:
    """启动后台 token 刷新循环。

    在 lifespan 中通过 asyncio.create_task() 启动。
    每 (7200 - refresh_margin - 60) 秒主动刷新一次。
    """
    tm = get_token_manager()
    interval = max(60, 7200 - settings.proxy_token_refresh_margin - 60)
    log.info("[token_mgr] 后台刷新循环已启动 interval=%ds", interval)

    while True:
        await asyncio.sleep(interval)
        for env in ("test", "prod"):
            try:
                await tm.ensure_fresh(env)
                log.debug("[token_mgr] 后台主动刷新完成 env=%s", env)
            except Exception:
                log.exception("[token_mgr] 后台主动刷新异常 env=%s", env)
