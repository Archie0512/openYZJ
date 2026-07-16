"""forwarder 报文转换与转发核心测试（不依赖真实 System A / MongoDB）。"""
from __future__ import annotations

import asyncio
import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.forwarder import (
    ForwardConfigError,
    ForwardUnsupportedError,
    _INNER_FIELDS,
    _build_system_a_payload,
    _decode_invoice,
    forward_to_system_a,
    record_forward_result,
)


def _b64(obj) -> str:
    return base64.b64encode(json.dumps(obj, ensure_ascii=False).encode("utf-8")).decode("utf-8")


# ── _decode_invoice ────────────────────────────────

def test_decode_invoice_base64():
    parsed = {"data": _b64({"billNo": "B1"})}
    assert _decode_invoice(parsed) == {"billNo": "B1"}


def test_decode_invoice_plain_dict():
    parsed = {"data": {"billNo": "B1"}}
    assert _decode_invoice(parsed) == {"billNo": "B1"}


def test_decode_invoice_list_unsupported():
    parsed = {"data": _b64([{"billNo": "B1"}])}
    with pytest.raises(ForwardUnsupportedError):
        _decode_invoice(parsed)


def test_decode_invoice_bad_base64():
    with pytest.raises(ForwardUnsupportedError):
        _decode_invoice({"data": "@@@not-b64@@@"})


# ── _build_system_a_payload ────────────────────────

def test_build_payload_field_mapping():
    inner = {
        "billNo": "AR-B01A-2026024703",
        "invoiceDate": "2026-06-30",
        "invoiceNum": "26312000004133675116",
        "totalAmount": 700.88,
        "totalTaxAmount": 91.12,
        "invoicePdfFileUrl": "https://example.com/x.pdf",
        "drawer": "黄春萍",
        "serialNo": "SN1",      # 不属于 System A 内层 7 字段，应被过滤
        "systemSource": "sysA",  # 同上
    }
    parsed = {"interfaceCode": "INVOICE.OPEN", "returnCode": "0", "returnMsg": "success", "data": _b64(inner)}
    payload = _build_system_a_payload(parsed)

    assert payload["interfaceCode"] == "INVOICE.OPEN"
    assert payload["returnCode"] == "0"
    assert payload["returnMsg"] == "success"
    decoded = json.loads(base64.b64decode(payload["data"]))
    assert set(decoded.keys()) <= set(_INNER_FIELDS)
    assert "serialNo" not in decoded and "systemSource" not in decoded
    assert decoded["billNo"] == "AR-B01A-2026024703"
    assert decoded["drawer"] == "黄春萍"          # 中文不转义
    assert decoded["totalAmount"] == 700.88


def test_build_payload_missing_billno():
    parsed = {"data": _b64({"invoiceNum": "123"})}
    with pytest.raises(ForwardUnsupportedError):
        _build_system_a_payload(parsed)


def test_build_payload_omits_absent_optional_fields():
    parsed = {"data": _b64({"billNo": "B1"})}  # 只有 billNo
    payload = _build_system_a_payload(parsed)
    decoded = json.loads(base64.b64decode(payload["data"]))
    assert decoded == {"billNo": "B1"}  # 缺失可选字段不出现


# ── forward_to_system_a（mock httpx）────────────────

def _mock_client(status_code=200, json_body=None, raise_exc=None):
    resp = MagicMock()
    resp.status_code = status_code
    if json_body is not None:
        resp.json = MagicMock(return_value=json_body)
    else:
        resp.json = MagicMock(side_effect=ValueError("no json"))
        resp.text = "plain-text-body"
    client = MagicMock()
    client.post = AsyncMock(side_effect=raise_exc) if raise_exc else AsyncMock(return_value=resp)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


_DOC = {"parsed": {"interfaceCode": "INVOICE.OPEN", "returnCode": "0",
                   "data": _b64({"billNo": "B1", "invoiceNum": "123"})}}


def test_forward_no_url_raises():
    with pytest.raises(ForwardConfigError):
        asyncio.run(forward_to_system_a(_DOC, ""))


def test_forward_success_by_success_flag():
    client = _mock_client(200, {"message": "success", "code": "200", "success": True})
    with patch("app.forwarder.httpx.AsyncClient", return_value=client):
        result = asyncio.run(forward_to_system_a(_DOC, "http://sysA/cb"))
    assert result["ok"] is True
    assert result["status_code"] == 200
    assert result["error"] is None
    # 校验发出的 payload 与 header
    call = client.post.call_args
    assert call.kwargs["headers"]["Content-Type"] == "application/json; charset=UTF-8"
    assert "data" in call.kwargs["json"]


def test_forward_failure_by_system_a_500():
    client = _mock_client(200, {"message": "未找到单据：B1", "code": "500", "success": False})
    with patch("app.forwarder.httpx.AsyncClient", return_value=client):
        result = asyncio.run(forward_to_system_a(_DOC, "http://sysA/cb"))
    assert result["ok"] is False
    assert "未找到单据" in result["error"]


def test_forward_timeout_recorded():
    client = _mock_client(raise_exc=httpx.TimeoutException("timed out"))
    with patch("app.forwarder.httpx.AsyncClient", return_value=client):
        result = asyncio.run(forward_to_system_a(_DOC, "http://sysA/cb"))
    assert result["ok"] is False
    assert "Timeout" in result["error"]


def test_forward_non_json_response_uses_http_status():
    client = _mock_client(200, json_body=None)  # json() 抛错，走 HTTP 状态兜底
    with patch("app.forwarder.httpx.AsyncClient", return_value=client):
        result = asyncio.run(forward_to_system_a(_DOC, "http://sysA/cb"))
    assert result["ok"] is True  # 2xx 视为成功


# ── record_forward_result ──────────────────────────

def test_record_forward_result_sent():
    coll = MagicMock()
    coll.update_one = AsyncMock()
    db = MagicMock()
    db.kdcloud_callbacks = coll
    asyncio.run(record_forward_result(
        db, "OID", "http://sysA/cb",
        {"ok": True, "status_code": 200, "error": None},
    ))
    update = coll.update_one.call_args.args[1]
    assert update["$set"]["forward_status"] == "sent"
    assert update["$set"]["last_forward_status_code"] == 200
    assert update["$inc"]["forward_attempts"] == 1
    assert update["$push"]["forward_history"]["$slice"] == -10


def test_record_forward_result_failed():
    coll = MagicMock()
    coll.update_one = AsyncMock()
    db = MagicMock()
    db.kdcloud_callbacks = coll
    asyncio.run(record_forward_result(
        db, "OID", "http://sysA/cb",
        {"ok": False, "status_code": 500, "error": "boom"},
    ))
    update = coll.update_one.call_args.args[1]
    assert update["$set"]["forward_status"] == "failed"
    assert update["$set"]["last_forward_error"] == "boom"
