"""开放 API 路由：允许第三方 ERP/道闸系统直接调用业务功能。

所有端点使用 HMAC-SHA256 签名鉴权，返回格式统一：
  {"code": 0, "data": ..., "message": "success"}
  {"code": 错误码, "data": null, "message": "错误描述"}
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.api_auth import require_api_auth
from app.db import mongodb
from app.services.outbound import push_card_message
from app.services.passcard_service import get_passcard_info, send_passcard

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Open API"])


# ── 请求/响应模型 ──────────────────────────────────────

class PasscardSendReq(BaseModel):
    """发送通行证请求体。"""
    car_no: str
    service: str
    sid: Optional[str] = None
    operator_name: Optional[str] = ""


class MessagePushReq(BaseModel):
    """推送消息请求体。"""
    robot_code: str
    content: str
    target_openid: Optional[str] = None


class ApiResponse(BaseModel):
    """统一响应格式。"""
    code: int = 0
    data: Optional[dict] = None
    message: str = "success"


# ── 工具函数 ────────────────────────────────────────────

def _ok(data: dict = None, message: str = "success") -> dict:
    """成功响应。"""
    return {"code": 0, "data": data, "message": message}


def _err(code: int, message: str) -> dict:
    """失败响应。"""
    return {"code": code, "data": None, "message": message}


# ── 路由 ─────────────────────────────────────────────────

@router.post("/passcard/send", summary="发送通行证")
async def api_passcard_send(
    req: PasscardSendReq,
    client_id: str = Depends(require_api_auth),
):
    """发送通行证到金斗云道闸系统。

    如果未提供 sid，从 robots 集合获取默认 sid。
    """
    sid = req.sid
    if not sid:
        # 从 robots 集合获取第一个可用的 sid
        db = mongodb.get_db()
        robot_doc = await db.robots.find_one(
            {"status": "active", "sid": {"$ne": None}},
            {"sid": 1},
        )
        if robot_doc and robot_doc.get("sid"):
            sid = str(robot_doc["sid"])
        else:
            return _err(400, "未提供 sid 且无默认门店配置")

    result = await send_passcard(
        car_no=req.car_no,
        service=req.service,
        sid=sid,
        operator_name=req.operator_name or "",
    )

    if result.get("success"):
        log.info(
            "[open_api] passcard/send 成功 client=%s car=%s",
            client_id, req.car_no,
        )
        return _ok(data=result)
    else:
        log.warning(
            "[open_api] passcard/send 失败 client=%s car=%s err=%s",
            client_id, req.car_no, result.get("error"),
        )
        return _err(500, result.get("error", "通行证发送失败"))


@router.get("/passcard/{pass_id}", summary="查询通行证")
async def api_passcard_get(
    pass_id: str,
    client_id: str = Depends(require_api_auth),
):
    """查询通行证信息。"""
    info = await get_passcard_info(pass_id)
    if info:
        return _ok(data=info)
    return _err(404, "未找到对应通行证记录")


@router.post("/message/push", summary="推送消息到机器人")
async def api_message_push(
    req: MessagePushReq,
    client_id: str = Depends(require_api_auth),
):
    """推送消息到云之家机器人。"""
    db = mongodb.get_db()
    robot_doc = await db.robots.find_one(
        {"robot_code": req.robot_code},
        {"robotId": 1, "status": 1},
    )
    if not robot_doc:
        return _err(404, f"机器人 {req.robot_code} 不存在")
    if robot_doc.get("status") != "active":
        return _err(403, f"机器人 {req.robot_code} 已禁用")

    robot_id = robot_doc.get("robotId")
    if not robot_id:
        return _err(400, f"机器人 {req.robot_code} 未激活（无 robotId）")

    # 使用 target_openid 作为 sessionId，如果未提供则用空字符串
    session_id = req.target_openid or ""

    try:
        await push_card_message(
            robot_id=robot_id,
            sessionId=session_id,
            content=req.content,
            robot_code=req.robot_code,
        )
        log.info(
            "[open_api] message/push 成功 client=%s robot=%s",
            client_id, req.robot_code,
        )
        return _ok(message="消息推送成功")
    except Exception as e:
        log.error("[open_api] message/push 失败: %s", e)
        return _err(500, f"消息推送失败: {e}")


@router.get("/robots", summary="查询已配置机器人列表")
async def api_robots_list(
    client_id: str = Depends(require_api_auth),
):
    """返回已配置机器人列表（公开安全视图）。"""
    db = mongodb.get_db()
    cursor = db.robots.find(
        {},
        {"robot_code": 1, "name": 1, "company_name": 1, "sid": 1, "status": 1, "_id": 0},
    )
    robots = await cursor.to_list(length=100)
    return _ok(data={"robots": robots})
