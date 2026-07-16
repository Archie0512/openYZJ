"""出站转发到 System A（EAS InvoiceCallback）。

把已落库的金蝶按票回调（5.1.02）转换为 System A 期望格式并 POST：
- 取金蝶回调 data（内层为 base64 字符串）→ 解码 → 提取 7 字段 → 重新 base64
- 组装外层 { interfaceCode, returnCode, returnMsg?, data(base64) }
- POST 到 client.callback_url（Content-Type: application/json; charset=UTF-8，无鉴权）

范围限制：只支持单张 by-invoice；data 为数组（by-apply）抛 ForwardUnsupportedError。
依据：docs/systemA_InvoiceCallback_接口文档.md。
"""
from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings

log = logging.getLogger(__name__)

# System A 内层需要的 7 个字段（金蝶字段名与之完全一致，无需改名）
_INNER_FIELDS = (
    "billNo",
    "invoiceDate",
    "invoiceNum",
    "totalAmount",
    "totalTaxAmount",
    "invoicePdfFileUrl",
    "drawer",
)


class ForwardConfigError(Exception):
    """转发目标 URL 未配置/无法解析。"""


class ForwardUnsupportedError(Exception):
    """回调类型不支持转发（非单张 by-invoice，或数据结构无法识别）。"""


def _decode_invoice(parsed: Any) -> dict:
    """从金蝶回调 parsed 中取出单张发票 dict。

    data 是 base64 str → 解码；已是 dict → 直接用；是 list（by-apply）→ 不支持。
    """
    if not isinstance(parsed, dict):
        raise ForwardUnsupportedError("回调体不是 JSON 对象，无法转发")
    data = parsed.get("data")
    if isinstance(data, str) and data:
        try:
            data = json.loads(base64.b64decode(data))
        except Exception as e:  # noqa: BLE001
            raise ForwardUnsupportedError(f"data base64 解码失败: {e}") from e
    if isinstance(data, list):
        raise ForwardUnsupportedError("按单回调（data 为数组）本期不支持转发")
    if not isinstance(data, dict):
        raise ForwardUnsupportedError("data 结构无法识别，无法转发")
    return data


def _build_system_a_payload(parsed: dict) -> dict:
    """组装 System A 外层 payload：{ interfaceCode, returnCode, returnMsg?, data(base64) }。"""
    invoice = _decode_invoice(parsed)
    if not invoice.get("billNo"):
        raise ForwardUnsupportedError("发票数据缺少 billNo，System A 无法定位单据")

    inner = {k: invoice[k] for k in _INNER_FIELDS if invoice.get(k) is not None}
    inner_b64 = base64.b64encode(
        json.dumps(inner, ensure_ascii=False).encode("utf-8")
    ).decode("utf-8")

    payload: dict[str, Any] = {
        "interfaceCode": parsed.get("interfaceCode") or "INVOICE.OPEN",
        "returnCode": parsed.get("returnCode") or "0",
        "data": inner_b64,
    }
    return_msg = parsed.get("returnMsg")
    if return_msg is not None:
        payload["returnMsg"] = return_msg
    return payload


def _resolve_parsed(doc: dict) -> dict:
    """从落库 doc 取金蝶回调对象：优先 doc['parsed']，否则尝试 parse raw_body。"""
    parsed = doc.get("parsed")
    if isinstance(parsed, dict):
        return parsed
    raw = doc.get("raw_body")
    if isinstance(raw, str) and raw:
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                return obj
        except Exception:  # noqa: BLE001
            pass
    raise ForwardUnsupportedError("落库记录无可用的 JSON 回调体")


async def forward_to_system_a(doc: dict, target_url: str) -> dict:
    """把一条落库回调转换并 POST 给 System A。

    返回 { ok, status_code, error, target_url }。不抛网络异常（捕获后记入 error）；
    但配置/不支持类错误会抛 ForwardConfigError / ForwardUnsupportedError。
    """
    if not target_url:
        raise ForwardConfigError("System A 目标 URL 未配置")

    parsed = _resolve_parsed(doc)
    payload = _build_system_a_payload(parsed)

    result: dict[str, Any] = {
        "ok": False,
        "status_code": None,
        "error": None,
        "target_url": target_url,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.system_a_forward_timeout) as cli:
            resp = await cli.post(
                target_url,
                json=payload,
                headers={"Content-Type": "application/json; charset=UTF-8"},
            )
        result["status_code"] = resp.status_code
        # System A 响应 { message, code:"200"|"500", success:bool }
        try:
            body = resp.json()
            ok = bool(body.get("success")) or str(body.get("code")) == "200"
            if not ok:
                result["error"] = str(body.get("message") or body)[:500]
        except Exception:  # noqa: BLE001 — 响应非 JSON，用 HTTP 状态兜底
            ok = 200 <= resp.status_code < 300
            if not ok:
                result["error"] = resp.text[:500]
        result["ok"] = ok
    except Exception as e:  # noqa: BLE001 — 网络/超时，记入 error 由调用方回写 failed
        result["error"] = f"{type(e).__name__}: {e}"
    return result


async def record_forward_result(db, event_id, target_url: str, result: dict) -> None:
    """把一次转发结果回写 kdcloud_callbacks doc（forward_status/attempts/history）。"""
    now = datetime.now(timezone.utc)
    status = "sent" if result.get("ok") else "failed"
    hist = {
        "at": now,
        "target_url": target_url,
        "ok": bool(result.get("ok")),
        "status_code": result.get("status_code"),
        "error": result.get("error"),
    }
    await db.kdcloud_callbacks.update_one(
        {"_id": event_id},
        {
            "$set": {
                "forward_status": status,
                "last_forward_at": now,
                "last_forward_status_code": result.get("status_code"),
                "last_forward_error": result.get("error"),
            },
            "$inc": {"forward_attempts": 1},
            "$push": {"forward_history": {"$each": [hist], "$slice": -10}},
        },
    )
