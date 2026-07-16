"""代理网关数据库索引初始化。

只管代理网关专属的集合：
- ``kdcloud_callbacks`` 金蝶发票云回调持久化

其他共享集合（proxy_clients / kdcloud_tokens / proxy_rate_counters 等）的索引
由主服务 server/app/db/indexes.py 集中创建；本模块只补 proxy 独有的部分，
保证 proxy-server 单独启动时也能建好自己需要的索引。

参考实现风格：server/app/db/indexes.py。
"""
from __future__ import annotations

import logging

from pymongo.asynchronous.database import AsyncDatabase

log = logging.getLogger(__name__)


async def _safe_create_index(coll, keys, **opts) -> None:
    """容错地创建索引，若已存在或冲突仅记录日志。"""
    try:
        name = await coll.create_index(keys, **opts)
        log.info("索引就绪: %s.%s opts=%s", coll.name, name, opts or "")
    except Exception as e:  # noqa: BLE001
        log.warning(
            "索引创建失败（可能已存在）coll=%s keys=%s err=%s",
            coll.name, keys, e,
        )


# 90 天 TTL，秒数：90 * 24 * 3600
_CALLBACK_TTL_SECONDS = 90 * 24 * 3600


async def ensure_indexes(db: AsyncDatabase) -> None:
    """确保代理网关专属集合的索引已创建。

    集合与索引规划：
      kdcloud_callbacks:
        (endpoint ASC, received_at DESC)  普通：按端点+时间倒序列表分页
        serial_nos                        普通：按发票流水号定位（数组字段多键索引）
        bill_nos                          普通：按单据号定位
        received_at (TTL 90 天)           自动清理老回调记录
    """
    # ── kdcloud_callbacks ─────────────────────────
    await _safe_create_index(
        db.kdcloud_callbacks,
        [("endpoint", 1), ("received_at", -1)],
    )
    await _safe_create_index(db.kdcloud_callbacks, "serial_nos")
    await _safe_create_index(db.kdcloud_callbacks, "bill_nos")
    await _safe_create_index(
        db.kdcloud_callbacks,
        "received_at",
        expireAfterSeconds=_CALLBACK_TTL_SECONDS,
    )

    log.info("代理网关索引初始化完成")
