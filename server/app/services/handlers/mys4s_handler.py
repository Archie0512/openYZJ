"""金斗云道闸 Handler：解析车牌+事由，调用 MYS4S API 发送通行证。"""
from __future__ import annotations

import logging
import re
import time
from typing import List, Optional, Tuple

from fastapi import BackgroundTasks

from app.config import settings
from app.db import mongodb
from app.models.command_log import ApiCallLog, CommandLogDoc
from app.models.yunzhijia import (
    CardBaseInfo,
    CardParam,
    YunzhijiaPayload,
    YunzhijiaResponseData,
)
from app.services.card_builder import build_pass_card_data
from app.services.handlers.base import BaseHandler
from app.services.passcard_service import send_passcard
from app.services.storage import save_command_log

log = logging.getLogger(__name__)

# 车牌正则：
#   常规/新能源车牌：省份简称 + 字母 + 5~6位字母数字
#   无牌车：无 + 7位数字和英文（不含O/o，避免与0混淆）
_PLATE_RE = re.compile(
    r"(无[A-NP-Za-np-z0-9]{7}"
    r"|[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁][A-Za-z][A-Za-z0-9]{5,6})"
)


class MYS4SHandler(BaseHandler):
    name = "mys4s"
    is_async = False

    async def handle(
        self,
        payload: YunzhijiaPayload,
        sessionId: str,
        bg: BackgroundTasks,
        robot_code: str = "",
    ) -> YunzhijiaResponseData:
        """解析车牌+事由，查 sid，调用金斗云 API（通过 passcard_service）。"""
        start = time.monotonic()

        # 1. 解析车牌和事由
        car_no, service = _parse_plate_and_service(payload.content)
        if not car_no:
            return YunzhijiaResponseData(
                type=2,
                content=f"请输入正确格式：车牌号 事由\n例如：沪A12345 来访接待\n[机器人:{robot_code}]",
            )

        # 2. 查 sid
        sid = await _get_sid(robot_code)
        if not sid:
            return YunzhijiaResponseData(
                type=2,
                content=f"当前机器人({robot_code})未配置门店 SID，请联系管理员",
            )

        # 3. 调用 passcard_service
        result = await send_passcard(
            car_no=car_no,
            service=service,
            sid=sid,
            operator_name=payload.operatorName,
        )
        cost_ms = int((time.monotonic() - start) * 1000)

        if result.get("success"):
            reply = f"通行证发送成功\n车牌：{car_no}\n事由：{service}\n操作人：{payload.operatorName}"
            status = "success"
            error_msg = None

            # 检查是否为无牌车（有 qr_url），返回卡片消息
            if result.get("qr_url"):
                try:
                    company_name = await _get_company_name(robot_code)
                    data_content = build_pass_card_data(
                        pass_data=result.get("pass_data", {}),
                        company_name=company_name,
                        car_no=car_no,
                        service=service,
                        qr_image_url=result["qr_url"],
                    )

                    # 无牌车提前写 command_log 再返回卡片
                    bg.add_task(
                        _write_command_log,
                        payload=payload,
                        sessionId=sessionId,
                        reply_content=reply,
                        cost_ms=cost_ms,
                        status="success",
                        error_msg=None,
                        car_no=car_no,
                        service=service,
                        sid=sid,
                    )

                    return YunzhijiaResponseData(
                        type=25,
                        content="无牌车通行证发送成功",
                        forwardControl="1",
                        param=CardParam(
                            baseInfo=CardBaseInfo(
                                templateId=settings.mys4s_card_template_id,
                                dataContent=data_content,
                            )
                        ),
                    )
                except Exception as e:
                    log.warning("生成二维码/卡片失败: %s", e)
        else:
            reply = f"调用道闸接口失败：{result.get('error', '未知错误')}"
            status = "failed"
            error_msg = result.get("error")
            log.warning("mys4s_handler failed: %s", error_msg)

        # 4. 后台写 command_log
        bg.add_task(
            _write_command_log,
            payload=payload,
            sessionId=sessionId,
            reply_content=reply,
            cost_ms=cost_ms,
            status=status,
            error_msg=error_msg,
            car_no=car_no,
            service=service,
            sid=sid,
        )

        return YunzhijiaResponseData(type=2, content=reply)


def _parse_plate_and_service(content: str) -> Tuple[Optional[str], str]:
    """从消息内容解析车牌号和事由。返回 (car_no, service)。"""
    text = (content or "").strip()
    match = _PLATE_RE.search(text)
    if not match:
        return None, ""
    car_no = match.group(1).upper()
    # 车牌之后的文本作为 service
    after = text[match.end():].strip()
    # 车牌之前的文本如果有也考虑作为 service（用户可能写 "来访 沪A12345"）
    before = text[:match.start()].strip()
    service = after or before or "来访"
    return car_no, service


async def _get_sid(robot_code: str) -> Optional[str]:
    """从 robots 集合中查找 robot_code 对应的 sid。"""
    if not robot_code:
        return None
    db = mongodb.get_db()
    doc = await db.robots.find_one({"robot_code": robot_code}, {"sid": 1})
    if doc and doc.get("sid"):
        return str(doc["sid"])
    return None


async def _get_company_name(robot_code: str) -> str:
    """从 robots 集合中查找 robot_code 对应的门店名称。"""
    if not robot_code:
        return ""
    db = mongodb.get_db()
    doc = await db.robots.find_one({"robot_code": robot_code}, {"company_name": 1})
    if doc and doc.get("company_name"):
        return str(doc["company_name"])
    return ""


async def _write_command_log(
    payload: YunzhijiaPayload,
    sessionId: str,
    reply_content: str,
    cost_ms: int,
    status: str,
    error_msg: Optional[str],
    car_no: Optional[str],
    service: str,
    sid: Optional[str],
) -> None:
    """后台写入 command_logs。"""
    doc = CommandLogDoc(
        msgId=payload.msgId,
        robotId=payload.robotId,
        sessionId=sessionId,
        command="mys4s",
        handler="mys4s",
        status=status,
        request_content=payload.content,
        response_content=reply_content,
        cost_ms=cost_ms,
        error=error_msg,
        external_api_calls=[
            ApiCallLog(
                url=f"{settings.mys4s_base_url}/vehicle/passcard/send",
                method="POST",
                cost_ms=cost_ms,
                error=error_msg,
            )
        ],
    )
    await save_command_log(doc)
