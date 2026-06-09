"""开放 API 路由：允许第三方 ERP/道闸系统直接调用业务功能。

鉴权方式：
  - HMAC-SHA256 签名（第三方系统）
  - Bearer Token 简化鉴权（小程序前端）

返回格式统一：
  {"code": 0, "data": ..., "message": "success"}
  {"code": 错误码, "data": null, "message": "错误描述"}
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel

from app.core.api_auth import require_api_auth, require_bearer_auth
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


# ── 小程序端点（Bearer Token 鉴权）────────────────────────

# 车牌号正则：兼容新能源（8位）与普通车牌（7位）
_PLATE_RE = re.compile(
    r"[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁]"
    r"[A-HJ-NP-Z]"
    r"[A-HJ-NP-Z0-9]{4,6}"
    r"[A-HJ-NP-Z0-9挂学警港澳]"
)


async def _recognize_plate(file: UploadFile) -> list[str]:
    """车牌识别核心逻辑。

    当前为桩实现（返回空列表），生产环境 Linux 下可替换为 hyperlpr3 引擎。
    接口契约保持不变，前端在结果为空时提示用户手动输入。
    """
    # TODO: 生产环境集成 hyperlpr3
    # from hyperlpr3 import LicensePlateCatcher
    # import numpy as np
    # from PIL import Image
    # catcher = LicensePlateCatcher()
    # contents = await file.read()
    # img = Image.open(io.BytesIO(contents)).convert("RGB")
    # img_array = np.array(img)
    # results = catcher(img_array)
    # plates = [r[0] for r in results if r[1] > 0.7]
    # return plates

    _ = await file.read()  # 消费文件流
    return []


@router.post("/ocr/plate", summary="车牌 OCR 识别")
async def api_ocr_plate(
    file: UploadFile = File(...),
    client_id: str = Depends(require_bearer_auth),
):
    """接收车辆图片，返回识别到的车牌号列表。

    如果未识别到车牌，返回空列表，前端引导用户手动输入。
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        return _err(400, "请上传图片文件")

    try:
        plates = await _recognize_plate(file)
        return _ok(data={"plates": plates})
    except Exception as e:
        log.error("[open_api] ocr/plate 失败: %s", e)
        return _err(500, f"OCR 识别失败: {e}")


@router.get("/service-reasons", summary="获取事由列表")
async def api_service_reasons(
    client_id: str = Depends(require_bearer_auth),
):
    """返回当前激活的来访事由列表（按 sort 排序）。"""
    db = mongodb.get_db()
    cursor = db.service_reasons.find(
        {"status": "active"},
        {"name": 1, "_id": 0},
    ).sort("sort", 1)
    docs = await cursor.to_list(length=100)
    reasons = [doc["name"] for doc in docs]
    return _ok(data={"reasons": reasons})


@router.get("/user/store", summary="查询用户门店映射")
async def api_user_store(
    openid: str = Query(..., description="用户 openid"),
    client_id: str = Depends(require_bearer_auth),
):
    """根据 openid 查询用户所属门店信息。

    如果用户未注册映射，则 fallback 到 robots 集合获取第一个可用门店。
    """
    db = mongodb.get_db()

    # 1. 查 user_stores 集合
    store_doc = await db.user_stores.find_one(
        {"openid": openid, "status": "active"},
        {"_id": 0, "sid": 1, "company_name": 1, "robot_code": 1},
    )
    if store_doc:
        return _ok(data={
            "sid": store_doc.get("sid", ""),
            "company_name": store_doc.get("company_name", ""),
            "robot_code": store_doc.get("robot_code", ""),
        })

    # 2. Fallback: 从 robots 集合获取第一个可用门店
    robot_doc = await db.robots.find_one(
        {"status": "active", "sid": {"$ne": None}},
        {"_id": 0, "sid": 1, "company_name": 1, "robot_code": 1},
    )
    if robot_doc:
        return _ok(data={
            "sid": str(robot_doc.get("sid", "")),
            "company_name": robot_doc.get("company_name", ""),
            "robot_code": robot_doc.get("robot_code", ""),
        })

    return _err(404, "未找到可用门店配置")
