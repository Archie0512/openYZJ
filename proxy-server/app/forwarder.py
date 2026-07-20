"""出站转发到 System A（EAS InvoiceCallback）。

把已落库的金蝶按票回调（5.1.02）转换为 System A 期望格式并 POST：
- 取金蝶回调 data（内层为 base64 字符串）→ 解码 → 提取 7 字段 → 重新 base64
- 组装外层 { interfaceCode, returnCode, returnMsg?, data(base64) }
- POST 到 client.callback_url（Content-Type: application/json; charset=UTF-8，无鉴权）

范围限制：只支持单张 by-invoice；data 为数组（by-apply）抛 ForwardUnsupportedError。

多单据合并开票处理：当金蝶内层 billNo 为逗号拼接（多张 EAS 单据合开一张发票）时，
按 invoiceDetail 逐行拆分，每张单据携带对应明细行的 amount/taxAmount 独立转发。
拆分前校验 invoiceDetail 行数与 split 后的 billNo 数量一致，不一致则标 unsupported。
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
    """从金蝶回调 parsed 中取出内层发票 dict。

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


def _build_outer(parsed: dict, inner_b64: str) -> dict:
    """组装 System A 外层 payload。"""
    outer: dict[str, Any] = {
        "interfaceCode": parsed.get("interfaceCode") or "INVOICE.OPEN",
        "returnCode": parsed.get("returnCode") or "0",
        "data": inner_b64,
    }
    return_msg = parsed.get("returnMsg")
    if return_msg is not None:
        outer["returnMsg"] = return_msg
    return outer


def _build_system_a_payloads(parsed: dict) -> list[dict]:
    """组装 System A payload 列表。

    单张发票 → list 长度 1。
    多单据合并（billNo 含逗号）→ 逐张拆分，每张取对应 invoiceDetail 行的金额。
    拆分前校验 invoiceDetail 行数 == split 后的 billNo 数量，不一致抛 ForwardUnsupportedError。
    """
    invoice = _decode_invoice(parsed)
    bill_no_raw = invoice.get("billNo", "")
    if not bill_no_raw:
        raise ForwardUnsupportedError("发票数据缺少 billNo，System A 无法定位单据")

    if "," not in bill_no_raw:
        # 单张：原有逻辑，用总金额
        inner = {k: invoice[k] for k in _INNER_FIELDS if invoice.get(k) is not None}
        inner_b64 = base64.b64encode(
            json.dumps(inner, ensure_ascii=False).encode("utf-8")
        ).decode("utf-8")
        return [_build_outer(parsed, inner_b64)]

    # ── 多单据拆分 ─────────────────────────────────
    bill_nos = [b.strip() for b in bill_no_raw.split(",")]
    details = invoice.get("invoiceDetail", [])
    if len(bill_nos) != len(details):
        raise ForwardUnsupportedError(
            f"billNo 含 {len(bill_nos)} 张单据，invoiceDetail {len(details)} 行，"
            f"无法一一对应，需要人工核实"
        )

    payloads = []
    for i, bill_no in enumerate(bill_nos):
        detail = details[i]
        inner = {
            "billNo": bill_no,
            "invoiceDate": invoice.get("invoiceDate"),
            "invoiceNum": invoice.get("invoiceNum"),
            "totalAmount": detail.get("amount"),
            "totalTaxAmount": detail.get("taxAmount"),
            "invoicePdfFileUrl": invoice.get("invoicePdfFileUrl"),
            "drawer": invoice.get("drawer"),
        }
        inner = {k: v for k, v in inner.items() if v is not None}
        inner_b64 = base64.b64encode(
            json.dumps(inner, ensure_ascii=False).encode("utf-8")
        ).decode("utf-8")
        payloads.append(_build_outer(parsed, inner_b64))

    log.info(
        "[forwarder] 多单据拆分 %d 张: %s",
        len(bill_nos), ", ".join(bill_nos),
    )
    return payloads


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


async def _send_one(cli: httpx.AsyncClient, target_url: str, payload: dict) -> dict:
    """POST 单个 payload 给 System A，返回 { ok, status_code, error }。"""
    try:
        resp = await cli.post(
            target_url,
            json=payload,
            headers={"Content-Type": "application/json; charset=UTF-8"},
        )
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "status_code": None, "error": f"{type(e).__name__}: {e}"}

    ok: bool
    error: str | None = None
    try:
        body = resp.json()
        ok = bool(body.get("success")) or str(body.get("code")) == "200"
        if not ok:
            error = str(body.get("message") or body)[:500]
    except Exception:  # noqa: BLE001 — 响应非 JSON，用 HTTP 状态兜底
        ok = 200 <= resp.status_code < 300
        if not ok:
            error = resp.text[:500]
    return {"ok": ok, "status_code": resp.status_code, "error": error}


async def forward_to_system_a(doc: dict, target_url: str) -> dict:
    """把一条落库回调转换并 POST 给 System A。

    多单据合并时自动拆分后逐张发送。返回聚合结果：
    { ok, status_code, error, target_url }。不抛网络异常。

    不抛 ForwardConfigError / ForwardUnsupportedError —— 由调用方处理。
    """
    if not target_url:
        raise ForwardConfigError("System A 目标 URL 未配置")

    parsed = _resolve_parsed(doc)
    payloads = _build_system_a_payloads(parsed)

    async with httpx.AsyncClient(timeout=settings.system_a_forward_timeout) as cli:
        results = [await _send_one(cli, target_url, p) for p in payloads]

    # 聚合
    all_ok = all(r["ok"] for r in results)
    errors = [r["error"] for r in results if r["error"]]
    return {
        "ok": all_ok,
        "status_code": results[0]["status_code"],
        "error": "; ".join(errors)[:500] if errors else None,
        "target_url": target_url,
    }


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
