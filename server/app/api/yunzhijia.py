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
    """接收云之家消息推送并验签，落库由 BackgroundTasks 异步执行。

    路径参数 robot_code 作为逻辑路由标识（不参与验签）。
    验签使用 body 中 robotId 对应的 appSecret。
    """
    # 获取验签密钥
    secret = await get_robot_secret(payload.robotId, db)

    # 双路径签名验证（保留 SHA256 / SHA1 双路径，不改动签名逻辑）
    ok, algo = verify_sign(
        secret,
        payload.robotId,
        payload.robotName,
        payload.operatorOpenid,
        payload.operatorName,
        str(payload.time),  # 关键：毫秒时间戳作为字符串拼接
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

    # ── 落库副作用（响应发出后执行，不阻塞 3s 响应窗口）──────
    is_test = payload.robotId == TEST_ROBOT_ID
    payload_dict = payload.model_dump()
    # 测试请求（robotId='test-robotId'）同样落库，标记 is_test=True 便于后续清理
    bg.add_task(save_message, payload_dict, robot_code, sessionId, algo, is_test)
    bg.add_task(upsert_session, payload_dict, robot_code, sessionId)

    # ── 构建回复 ──────────────────────────────────
    if is_test:
        # 测试请求阶段保留欢迎语，确保激活成功率
        return YunzhijiaResponse(
            success=True,
            data=YunzhijiaResponseData(
                type=2, content="你好，我是机器人，已经准备好为你服务~"
            ),
        )

    # 正式请求走 message_processor 路由调度（echo / api / ai）
    data = await message_processor.handle(payload, sessionId, bg)
    return YunzhijiaResponse(success=True, data=data)
