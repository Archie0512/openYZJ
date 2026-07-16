"""回调端点。

- 5.1.01 开票申请单回退接口
- 5.1.02 回调接口-按票回调
- 5.1.03 回调接口-按单回调

设计要点：
- **不使用 pydantic 解析 body**，直接读取 raw body 落库，避免 Content-Type / 结构不符时
  在校验阶段被 FastAPI 挡回 422（那样连 body 都拿不到）。
- 回调为入站接收，不使用 HMAC 鉴权（金蝶不会携带 X-Proxy-* 头）。
- 响应必须严格按金蝶文档要求返回 ``{"message":"回调成功","errorCode":"0","success":true}``，
  否则金蝶会判定失败并反复重推（见 docs/kdcloud_md.md 5.1.03 返回示例）。
- **落库失败仍返回 200 ACK**（降级）：金蝶重推风暴比单次事件丢失更危险，ERROR 日志由
  运维监控兜底手动 replay。
- 打平字段 (``serial_nos``/``bill_nos``/``batches``/``interface_code``/``return_code``) 从
  parsed body 提取，方便 admin 端 API 按发票维度过滤查询。
"""
from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app import mongodb

log = logging.getLogger(__name__)

router = APIRouter()

# 金蝶发票云要求的回调 ACK 格式（见 docs/kdcloud_md.md 5.1.03 返回示例）
_ACK: dict[str, Any] = {"message": "回调成功", "errorCode": "0", "success": True}


def _try_parse_json(raw: bytes) -> tuple[Any, str | None]:
    """尝试将 raw body 解析为 JSON。空 body 返回 (None, None)。"""
    if not raw:
        return None, None
    try:
        return json.loads(raw), None
    except Exception as e:  # noqa: BLE001 — 任何解析异常都记入 parse_error
        return None, f"{type(e).__name__}: {e}"


def _client_ip(request: Request) -> str:
    """按 X-Forwarded-For → X-Real-IP → request.client.host 顺序提取真实 IP。"""
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        # XFF 可能是逗号分隔的链，第一个是原始客户端
        return xff.split(",")[0].strip()
    xri = request.headers.get("x-real-ip", "")
    if xri:
        return xri.strip()
    if request.client:
        return request.client.host
    return ""


def _decode_data_field(data: Any) -> Any:
    """把金蝶回调 data 规整为 dict/list。

    金蝶真实报文的 data 是内层 JSON 的 base64 字符串，需先解码；
    若已是 dict/list（明文）直接返回；解码失败返回 None（打平留空，不影响落库）。
    """
    if isinstance(data, (dict, list)):
        return data
    if isinstance(data, str) and data:
        try:
            return json.loads(base64.b64decode(data))
        except Exception:  # noqa: BLE001 — 非 base64 或非 JSON，视为无法解析
            return None
    return None


def _append_from_dict(item: dict, result: dict) -> None:
    """从单张发票 dict 中提取 serialNo/billNo/batch/systemSource 追加到 result 打平数组。"""
    for key, target in (
        ("serialNo", "serial_nos"),
        ("billNo", "bill_nos"),
        ("batch", "batches"),
        ("systemSource", "system_sources"),
    ):
        v = item.get(key)
        if v is not None and v != "":
            result[target].append(v)


def _extract_flat_fields(parsed: Any) -> dict[str, Any]:
    """从 parsed body 中提取打平字段，供索引查询。

    金蝶回调结构：
      5.1.02: {interfaceCode, returnCode, returnMsg, data: <单张发票，可能是 base64 字符串>}
      5.1.03: {interfaceCode, returnCode, returnMsg, data: [<多张发票>]}
      5.1.01: 结构未文档化，尝试按 5.1.02 规则；提取不到则打平字段留空数组。

    data 字段先经 _decode_data_field 规整（金蝶真实报文为 base64 字符串）。
    """
    result: dict[str, Any] = {
        "interface_code": None,
        "return_code": None,
        "serial_nos": [],
        "bill_nos": [],
        "batches": [],
        "system_sources": [],
    }
    if not isinstance(parsed, dict):
        return result

    ic = parsed.get("interfaceCode")
    rc = parsed.get("returnCode")
    result["interface_code"] = ic if isinstance(ic, str) else None
    result["return_code"] = rc if isinstance(rc, str) else None

    data = _decode_data_field(parsed.get("data"))
    if isinstance(data, dict):
        _append_from_dict(data, result)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                _append_from_dict(item, result)

    return result


def _build_doc(
    request: Request,
    tag: str,
    raw: bytes,
    parsed: Any,
    parse_err: str | None,
) -> dict[str, Any]:
    """组装写入 kdcloud_callbacks 的 doc。"""
    flat = _extract_flat_fields(parsed)
    return {
        "endpoint": tag,
        "received_at": datetime.now(timezone.utc),
        "content_type": request.headers.get("content-type", ""),
        "raw_body": raw.decode("utf-8", errors="replace"),
        "raw_len": len(raw),
        "query_params": dict(request.query_params),
        "headers": dict(request.headers),
        "client_ip": _client_ip(request),
        # 仅当 parsed 是 dict 时才存进 parsed 字段；数组/标量放弃（打平字段仍会提取）
        "parsed": parsed if isinstance(parsed, dict) else None,
        "parse_error": parse_err,
        **flat,
    }


async def _persist_and_ack(request: Request, tag: str) -> JSONResponse:
    """读原始 body → 解析 → 落库 → 返回金蝶格式 ACK。

    降级：DB 写失败时仍返回 200 ACK（避免金蝶重推风暴），ERROR 日志兜底。
    """
    raw = await request.body()
    parsed, parse_err = _try_parse_json(raw)
    doc = _build_doc(request, tag, raw, parsed, parse_err)
    try:
        await mongodb.get_db().kdcloud_callbacks.insert_one(doc)
        log.info(
            "[proxy] callback/%s 已入库 raw_len=%d interface_code=%s "
            "serial_nos=%s bill_nos=%s parse_err=%s",
            tag, doc["raw_len"], doc["interface_code"],
            doc["serial_nos"], doc["bill_nos"], parse_err,
        )
    except Exception as e:  # noqa: BLE001 — 降级保护：DB 挂了不能拖累金蝶重推
        log.error(
            "[proxy] callback/%s DB 写入失败（仍返回 200 ACK）err=%s raw=%s",
            tag, e, doc["raw_body"],
        )
    return JSONResponse(_ACK)


@router.post("/apply-return")
async def callback_apply_return(request: Request):
    """5.1.01 开票申请单回退接口（星瀚发起退回开票申请单）。"""
    return await _persist_and_ack(request, "apply-return")


@router.post("/by-invoice")
async def callback_by_invoice(request: Request):
    """5.1.02 回调接口-按票回调（一次回调一张发票信息）。"""
    return await _persist_and_ack(request, "by-invoice")


@router.post("/by-apply")
async def callback_by_apply(request: Request):
    """5.1.03 回调接口-按单回调（单据对应的所有发票开票完毕后一起回调）。"""
    return await _persist_and_ack(request, "by-apply")
