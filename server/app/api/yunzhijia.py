"""云之家机器人 Webhook 路由。

实现签名验证 + 测试请求通道，支持 SHA256/SHA1 双路径校验。
落库（messages / sessions）通过 FastAPI BackgroundTasks 在响应发出后异步执行，不阻塞 3s 响应窗口。
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException

from app.core.deps import TEST_ROBOT_ID, get_db, get_robot_secret
from app.core.security import verify_sign
from app.models.yunzhijia import (
    YunzhijiaPayload,
    YunzhijiaResponse,
    YunzhijiaResponseData,
)
from app.services.storage import save_message, upsert_session
from app.services import message_processor

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/yunzhijia", tags=["yunzhijia"])


@router.post("/webhook/{robot_code}", response_model=YunzhijiaResponse)
async def webhook(
    robot_code: str,
    payload: YunzhijiaPayload,
    bg: BackgroundTasks,
    sign: str = Header(..., alias="sign"),
    sessionId: str = Header(..., alias="sessionId"),
    db=Depends(get_db),
):
    """接收云之家消息推送。测试请求跳过验签，正式请求走完整验签。"""
    # ── 测试请求直接返回，不验签 ──────────────────────
    # 原因：测试阶段无公开密钥，云之家用内部密钥签名，仅验证我方响应格式
    is_test = payload.robotId == TEST_ROBOT_ID
    if is_test:
        payload_dict = payload.model_dump()
        bg.add_task(save_message, payload_dict, robot_code, sessionId, "test-skip", True)
        bg.add_task(upsert_session, payload_dict, robot_code, sessionId)
        return YunzhijiaResponse(
            success=True,
            data=YunzhijiaResponseData(
                type=2, content="你好，我是机器人，已经准备好为你服务~"
            ),
        )

    # ── 正式请求：验签 ────────────────────────────────
    secret = await get_robot_secret(payload.robotId, db)

    ok, algo = verify_sign(
        secret,
        payload.robotId,
        payload.robotName,
        payload.operatorOpenid,
        payload.operatorName,
        str(payload.time),
        payload.msgId,
        payload.content,
        sign,
    )
    if not ok:
        log.warning("sign verification failed for robotId=%s", payload.robotId)
        raise HTTPException(status_code=401, detail="invalid sign")

    log.info(
        "verified algo=%s robot=%s session=%s content=%s",
        algo, payload.robotId, sessionId, payload.content,
    )

    # ── 落库副作用（响应发出后执行）──────────────────
    payload_dict = payload.model_dump()
    bg.add_task(save_message, payload_dict, robot_code, sessionId, algo, False)
    bg.add_task(upsert_session, payload_dict, robot_code, sessionId)

    # ── 正式请求走 message_processor 路由调度 ────────
    data = await message_processor.handle(payload, sessionId, bg)
    return YunzhijiaResponse(success=True, data=data)
