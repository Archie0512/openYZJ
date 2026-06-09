"""数据库索引初始化模块。

启动时为业务集合创建必要索引；
所有 create_index 都包裹 try/except，避免重复创建（或冲突索引）阻塞应用启动。
TTL 索引语义：MongoDB 后台扫描周期约 60s/次，因此过期文档实际清理最多有 1-2 分钟延迟。
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
        log.warning("索引创建失败（可能已存在）coll=%s keys=%s err=%s",
                    coll.name, keys, e)


async def ensure_indexes(db: AsyncDatabase) -> None:
    """确保所有业务集合的索引已创建。

    集合与索引规划：
      - messages:
          (robotId ASC, time DESC) 普通：按机器人查询历史
          (operatorOpenid ASC, time DESC) 普通：按发送者查询历史
          (msgId) unique：幂等去重，防止云之家重试重复落库
      - sessions:
          (sessionId) unique：会话唯一键
          (updated_at) TTL expireAfterSeconds=1800：30 分钟无活动自动清理
      - command_logs:
          (msgId) 普通：按消息追溯指令处理记录（同一 msgId 可能多条）
          (status ASC, created_at DESC) 普通：按状态+时间排查
    """
    # ── messages ──────────────────────────────────
    await _safe_create_index(db.messages, [("robotId", 1), ("time", -1)])
    await _safe_create_index(db.messages, [("operatorOpenid", 1), ("time", -1)])
    await _safe_create_index(db.messages, "msgId", unique=True)

    # ── sessions ──────────────────────────────────
    await _safe_create_index(db.sessions, "sessionId", unique=True)
    # TTL：MongoDB 后台扫描 60s/次，最大延迟约 1-2 分钟
    await _safe_create_index(db.sessions, "updated_at", expireAfterSeconds=1800)

    # ── command_logs ──────────────────────────────
    await _safe_create_index(db.command_logs, "msgId")
    await _safe_create_index(db.command_logs, [("status", 1), ("created_at", -1)])
    
    # ── robots ───────────────────────────────────
    await _safe_create_index(db.robots, "robot_code", unique=True)
    await _safe_create_index(db.robots, "robotId", unique=True, sparse=True)

    # ── api_clients ──────────────────────────────────
    await _safe_create_index(db.api_clients, "api_key", unique=True)
    await _safe_create_index(db.api_clients, "client_id", unique=True)

    # ── service_reasons ─────────────────────────────
    await _safe_create_index(db.service_reasons, "sort")

    # ── user_stores ─────────────────────────────────
    await _safe_create_index(db.user_stores, "openid", unique=True)

    log.info("索引初始化完成")

    # ── 预置数据：service_reasons ───────────────────
    await _seed_service_reasons(db)


async def _seed_service_reasons(db) -> None:
    """如果 service_reasons 集合为空，插入预置事由数据。"""
    count = await db.service_reasons.count_documents({})
    if count > 0:
        return

    preset = [
        {"name": "来访接待", "sort": 1, "status": "active"},
        {"name": "施工", "sort": 2, "status": "active"},
        {"name": "送货", "sort": 3, "status": "active"},
        {"name": "其他", "sort": 99, "status": "active"},
    ]
    await db.service_reasons.insert_many(preset)
    log.info("预置事由数据已插入（%d 条）", len(preset))
