"""落库副作用封装：messages / sessions / command_logs。

设计要点：
  - 所有函数均为 async，由 FastAPI BackgroundTasks 在响应发出后调度
  - 不抛异常给上层（webhook 已经返回响应，落库失败仅记录日志）
  - sessions 通过 update_one(upsert=True) 原子复用并刷新 updated_at，
    依赖 sessions.updated_at 上的 TTL 索引（expireAfterSeconds=1800）实现 30 分钟过期
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from app.db import mongodb
from app.models.command_log import CommandLogDoc
from app.models.message import MessageDoc

log = logging.getLogger(__name__)


async def save_message(
    payload_dict: dict,
    robot_code: str,
    sessionId: str,
    sign_algo: Optional[str],
    is_test: bool,
) -> None:
    """将单条云之家消息写入 messages 集合。

    重复 msgId（unique 索引冲突）会被忽略，仅记录 warning，
    避免因云之家重试触发异常导致 BackgroundTask 报错。
    """
    db = mongodb.get_db()
    doc = MessageDoc(
        robot_code=robot_code,
        robotId=payload_dict["robotId"],
        robotName=payload_dict["robotName"],
        operatorOpenid=payload_dict["operatorOpenid"],
        operatorName=payload_dict["operatorName"],
        msgId=payload_dict["msgId"],
        content=payload_dict["content"],
        type=payload_dict["type"],
        time=payload_dict["time"],
        sessionId=sessionId,
        sign_algo=sign_algo,
        is_test=is_test,
        raw_payload=payload_dict,
    ).model_dump()
    try:
        await db.messages.insert_one(doc)
        log.debug("save_message ok msgId=%s session=%s", doc["msgId"], sessionId)
    except Exception as e:  # noqa: BLE001 - 重复 msgId 等兜底处理
        # 唯一索引冲突属于"幂等已生效"，其他异常仅记录 warning
        log.warning("save_message failed msgId=%s err=%s", doc.get("msgId"), e)


async def upsert_session(
    payload_dict: dict,
    robot_code: str,
    sessionId: str,
) -> None:
    """upsert sessions 文档，刷新 updated_at 以重置 TTL 倒计时。

    - 首次出现的 sessionId：通过 $setOnInsert 写入静态字段
    - 再次命中：通过 $set 更新 last_msgId / last_content / updated_at，
      并 $inc message_count
    """
    db = mongodb.get_db()
    now = datetime.now(timezone.utc)
    try:
        res = await db.sessions.update_one(
            {"sessionId": sessionId},
            {
                "$setOnInsert": {
                    "sessionId": sessionId,
                    "robot_code": robot_code,
                    "robotId": payload_dict["robotId"],
                    "operatorOpenid": payload_dict["operatorOpenid"],
                    "operatorName": payload_dict["operatorName"],
                    "created_at": now,
                    "context": {},
                },
                "$set": {
                    "last_msgId": payload_dict["msgId"],
                    "last_content": payload_dict["content"],
                    # 关键：刷新 TTL 倒计时
                    "updated_at": now,
                },
                "$inc": {"message_count": 1},
            },
            upsert=True,
        )
        log.debug(
            "upsert_session sessionId=%s upserted=%s modified=%s",
            sessionId, res.upserted_id, res.modified_count,
        )
    except Exception as e:  # noqa: BLE001
        log.warning("upsert_session failed sessionId=%s err=%s", sessionId, e)


async def save_command_log(doc: CommandLogDoc) -> None:
    """写入 command_logs 集合。

    任务 #5 接入 handler 后调用；本任务仅提供接口签名以便后续平滑接入。
    """
    db = mongodb.get_db()
    try:
        await db.command_logs.insert_one(doc.model_dump())
        log.debug("save_command_log ok msgId=%s status=%s", doc.msgId, doc.status)
    except Exception as e:  # noqa: BLE001
        log.warning("save_command_log failed msgId=%s err=%s", doc.msgId, e)


async def update_command_log(filter_: dict, update: dict) -> None:
    """按条件更新 command_logs 中的一条记录。

    典型场景：异步 handler 在后台完成后将 status=pending 更新为 success/failed。
    """
    db = mongodb.get_db()
    try:
        res = await db.command_logs.update_one(filter_, {"$set": update})
        log.debug(
            "update_command_log filter=%s matched=%d modified=%d",
            filter_, res.matched_count, res.modified_count,
        )
    except Exception as e:  # noqa: BLE001
        log.warning("update_command_log failed filter=%s err=%s", filter_, e)
