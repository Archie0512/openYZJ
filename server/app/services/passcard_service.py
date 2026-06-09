"""通行证公共服务：抽取金斗云 API 调用逻辑，供 webhook handler 和 open_api 复用。"""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
import urllib.parse

import httpx

from app.config import settings
from app.db import mongodb
from app.services.qrcode_generator import generate_qrcode_png

log = logging.getLogger(__name__)


def _generate_sign(params: dict) -> str:
    """HMAC-SHA1 签名，参数按 key 排序后 URL-encode 拼接。"""
    sorted_params = sorted(params.items())
    sign_str = "&".join(
        f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in sorted_params
    )
    digest = hmac.new(
        settings.mys4s_secret_key.encode(),
        sign_str.encode(),
        hashlib.sha1,
    ).digest()
    return base64.b64encode(digest).decode()


async def _call_mys4s_api(
    car_no: str,
    service: str,
    user_tel: str,
    sid: str,
    desc: str,
) -> dict:
    """调用金斗云通行证 API。"""
    params = {
        "car_no": car_no,
        "service": service,
        "user_tel": user_tel,
        "sid": sid,
        "desc": desc,
    }
    sign = _generate_sign(params)
    params["sign"] = sign

    url = f"{settings.mys4s_base_url}/vehicle/passcard/send"
    headers = {
        "Content-Type": "application/json",
        "Api-Key": settings.mys4s_api_key,
    }

    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(url, json=params, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def send_passcard(
    car_no: str,
    service: str,
    sid: str,
    operator_name: str = "",
) -> dict:
    """发送通行证核心逻辑。

    参数：
        car_no        车牌号
        service       事由
        sid           门店 SID
        operator_name 操作人名称

    返回：
        {success, car_no, service, operator_name, qr_url?, pass_data?, error?}
    """
    start = time.monotonic()
    try:
        result = await _call_mys4s_api(
            car_no=car_no,
            service=service,
            user_tel="",
            sid=sid,
            desc=operator_name,
        )
        cost_ms = int((time.monotonic() - start) * 1000)
        log.info(
            "passcard_service.send_passcard 调用成功 car=%s sid=%s cost=%dms",
            car_no, sid, cost_ms,
        )
    except Exception as e:
        log.warning("passcard_service.send_passcard 调用失败: %s", e)
        return {
            "success": False,
            "car_no": car_no,
            "service": service,
            "operator_name": operator_name,
            "error": str(e),
        }

    # 解析返回结果
    if not isinstance(result, dict):
        return {
            "success": False,
            "car_no": car_no,
            "service": service,
            "operator_name": operator_name,
            "error": f"API 返回格式异常: {result}",
        }

    if result.get("code") == 0 or result.get("success"):
        resp: dict = {
            "success": True,
            "car_no": car_no,
            "service": service,
            "operator_name": operator_name,
            "pass_data": result.get("data", {}),
        }
        # 检查是否为无牌车，生成二维码
        api_data = result.get("data", {})
        info = api_data.get("Info", "")
        if "无" in info:
            try:
                png_path = generate_qrcode_png(api_data)
                qr_url = f"{settings.base_url}{png_path}"
                resp["qr_url"] = qr_url
            except Exception as e:
                log.warning("生成二维码失败: %s", e)
        return resp
    else:
        msg = result.get("msg") or result.get("message") or str(result)
        return {
            "success": False,
            "car_no": car_no,
            "service": service,
            "operator_name": operator_name,
            "error": msg,
        }


async def get_passcard_info(pass_id: str) -> dict:
    """查询通行证信息（从 command_logs 查）。

    参数：
        pass_id  通行证 ID（对应 command_logs 中的记录标识）

    返回：
        查找到的记录字典，或 None
    """
    db = mongodb.get_db()
    doc = await db.command_logs.find_one({"_id": pass_id})
    if not doc:
        # 尝试按 msgId 查找
        doc = await db.command_logs.find_one({"msgId": pass_id})
    if doc:
        doc.pop("_id", None)
        return doc
    return None
