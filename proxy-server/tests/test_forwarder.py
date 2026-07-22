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
    _build_outer,
    _build_system_a_payloads,
    _decode_invoice,
    _send_one,
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


# ── _build_system_a_payloads 单张 ──────────────────

def test_build_single_payload_field_mapping():
    inner = {
        "billNo": "AR-B01A-2026024703",
        "invoiceDate": "2026-06-30",
        "invoiceNum": "26312000004133675116",
        "totalAmount": 700.88,
        "totalTaxAmount": 91.12,
        "invoicePdfFileUrl": "https://example.com/x.pdf",
        "drawer": "黄春萍",
        "serialNo": "SN1",
        "systemSource": "sysA",
    }
    parsed = {"interfaceCode": "INVOICE.OPEN", "returnCode": "0", "returnMsg": "success", "data": _b64(inner)}
    payloads = _build_system_a_payloads(parsed)
    assert len(payloads) == 1
    p = payloads[0]
    assert p["interfaceCode"] == "INVOICE.OPEN"
    assert p["returnCode"] == "0"
    assert p["returnMsg"] == "success"
    decoded = json.loads(base64.b64decode(p["data"]))
    assert set(decoded.keys()) <= set(_INNER_FIELDS)
    assert "serialNo" not in decoded and "systemSource" not in decoded
    assert decoded["billNo"] == "AR-B01A-2026024703"


def test_build_single_missing_billno():
    parsed = {"data": _b64({"invoiceNum": "123"})}
    with pytest.raises(ForwardUnsupportedError):
        _build_system_a_payloads(parsed)


def test_build_single_omits_absent_optional_fields():
    parsed = {"data": _b64({"billNo": "B1"})}
    payloads = _build_system_a_payloads(parsed)
    decoded = json.loads(base64.b64decode(payloads[0]["data"]))
    assert decoded == {"billNo": "B1"}


# ── _build_system_a_payloads 机动车 ────────────────

def test_build_vehicle_field_mapping():
    """机动车：billNo←serialNo、invoiceNum←invoiceNo、不含税←invoiceAmount、PDF←invoiceFileUrl。"""
    inner = {
        "serialNo": "AR-B04A-2026028079",
        "invoiceNo": "26322000005935198201",
        "invoiceAmount": "283805.31",   # 不含税
        "totalAmount": "320700",         # 价税合计（陷阱）
        "totalTaxAmount": "36894.69",
        "invoiceDate": "2026-07-21 09:06:22.0",
        "invoiceFileUrl": "https://api.piaozone.com/rpa/free/preview/x/vehicle?type=0",
        "ofdFileUrl": "https://api.piaozone.com/rpa/free/preview/x/vehicle?type=1",
        "drawer": "谢媛",
        "vehicleIdentificationCode": "LBV21FM02TSK50591",
        "systemSource": "BD_EAS850",
    }
    parsed = {"interfaceCode": "INVOICE.OPEN", "returnCode": "0", "data": _b64(inner)}
    payloads = _build_system_a_payloads(parsed)
    assert len(payloads) == 1
    decoded = json.loads(base64.b64decode(payloads[0]["data"]))
    assert set(decoded.keys()) <= set(_INNER_FIELDS)
    assert decoded["billNo"] == "AR-B04A-2026028079"
    assert decoded["invoiceNum"] == "26322000005935198201"
    # 不含税必须取 invoiceAmount，绝不能是价税合计 320700
    assert decoded["totalAmount"] == "283805.31"
    assert decoded["totalTaxAmount"] == "36894.69"
    assert decoded["invoicePdfFileUrl"].endswith("type=0")
    assert decoded["invoiceDate"] == "2026-07-21"
    assert decoded["drawer"] == "谢媛"
    # 中转字段不外汄
    assert "serialNo" not in decoded and "invoiceNo" not in decoded


def test_build_vehicle_detected_by_vehicle_uuid():
    """无车架号但有 vehicleUuid 也判定为机动车。"""
    inner = {
        "serialNo": "AR-B04A-2026028080",
        "invoiceNo": "26322000005935198202",
        "invoiceAmount": "100.00",
        "totalAmount": "113.00",
        "totalTaxAmount": "13.00",
        "vehicleUuid": "1779264818165577756",
    }
    parsed = {"data": _b64(inner)}
    decoded = json.loads(base64.b64decode(_build_system_a_payloads(parsed)[0]["data"]))
    assert decoded["billNo"] == "AR-B04A-2026028080"
    assert decoded["invoiceNum"] == "26322000005935198202"
    assert decoded["totalAmount"] == "100.00"


# ── _build_system_a_payloads 多单据拆分 ─────────────

def test_build_multi_split_4():
    """4 张单据合开：billNo 逗号拼接，每张取对应 invoiceDetail 行的金额。"""
    details = [
        {"amount": 1243.36, "taxAmount": 161.64},
        {"amount": 553.10, "taxAmount": 71.90},
        {"amount": 3318.58, "taxAmount": 431.42},
        {"amount": 884.96, "taxAmount": 115.04},
    ]
    inner = {
        "billNo": "AR-B06A-2026015292,AR-B06A-2026015291,AR-B06A-2026015290,AR-B06A-2026015293",
        "invoiceDate": "2026-07-20",
        "invoiceNum": "26322000005917243936",
        "invoiceDetail": details,
        "invoicePdfFileUrl": "https://example.com/pdf",
        "drawer": "黄春萍",
    }
    parsed = {"interfaceCode": "INVOICE.OPEN", "returnCode": "0", "data": _b64(inner)}
    payloads = _build_system_a_payloads(parsed)
    assert len(payloads) == 4

    expected_bills = ["AR-B06A-2026015292", "AR-B06A-2026015291", "AR-B06A-2026015290", "AR-B06A-2026015293"]
    for i, p in enumerate(payloads):
        decoded = json.loads(base64.b64decode(p["data"]))
        assert decoded["billNo"] == expected_bills[i]
        assert decoded["totalAmount"] == details[i]["amount"]
        assert decoded["totalTaxAmount"] == details[i]["taxAmount"]
        assert decoded["invoiceNum"] == "26322000005917243936"
        assert decoded["invoicePdfFileUrl"] == "https://example.com/pdf"
        # 确保共享字段不变
        assert p["interfaceCode"] == "INVOICE.OPEN"


def test_build_multi_length_mismatch_raises():
    """billNo 拆分后 3 张，invoiceDetail 只有 2 行 → 抛错。"""
    inner = {
        "billNo": "B1,B2,B3",
        "invoiceDetail": [{"amount": 1}, {"amount": 2}],
    }
    parsed = {"data": _b64(inner)}
    with pytest.raises(ForwardUnsupportedError, match="无法一一对应"):
        _build_system_a_payloads(parsed)


# ── _build_outer ───────────────────────────────────

def test_build_outer_basic():
    out = _build_outer({"interfaceCode": "INVOICE.OPEN", "returnCode": "0"}, "b64data")
    assert out["data"] == "b64data"
    assert out["returnCode"] == "0"


def test_build_outer_includes_returnMsg():
    out = _build_outer({"returnMsg": "success"}, "x")
    assert out["returnMsg"] == "success"


# ── _send_one ─────────────────────────────────────

def _mock_resp(status_code=200, json_body=None, text_body=""):
    resp = MagicMock()
    resp.status_code = status_code
    if json_body is not None:
        resp.json = MagicMock(return_value=json_body)
    else:
        resp.json = MagicMock(side_effect=ValueError("no json"))
        resp.text = text_body
    return resp


def test_send_one_success():
    cli = MagicMock()
    cli.post = AsyncMock(return_value=_mock_resp(200, {"code": "200", "success": True}))
    r = asyncio.run(_send_one(cli, "http://t", {"x": 1}))
    assert r["ok"] is True
    assert r["status_code"] == 200


def test_send_one_system_a_failure():
    cli = MagicMock()
    cli.post = AsyncMock(return_value=_mock_resp(200, {"code": "500", "success": False, "message": "未找到单据"}))
    r = asyncio.run(_send_one(cli, "http://t", {}))
    assert r["ok"] is False
    assert "未找到单据" in r["error"]


def test_send_one_network_error():
    cli = MagicMock()
    cli.post = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
    r = asyncio.run(_send_one(cli, "http://t", {}))
    assert r["ok"] is False
    assert "Timeout" in r["error"]


# ── forward_to_system_a ────────────────────────────

_DOC = {"parsed": {"interfaceCode": "INVOICE.OPEN", "returnCode": "0",
                   "data": _b64({"billNo": "B1", "invoiceNum": "123"})}}


def test_forward_no_url_raises():
    with pytest.raises(ForwardConfigError):
        asyncio.run(forward_to_system_a(_DOC, ""))


def _run_forward(doc=_DOC, target="http://sysA/cb",
                 mock_responses=None):
    """helper：mock httpx.AsyncClient 链式调用后跑 forward_to_system_a。"""
    if mock_responses is None:
        mock_responses = [{"code": "200", "success": True}]

    cli = MagicMock()
    # 每个 payload 调用一次 post，返回对应 mock_responses
    calls = []
    for r in mock_responses:
        if isinstance(r, Exception):
            calls.append(r)
        else:
            calls.append(_mock_resp(200, r))
    cli.post = AsyncMock(side_effect=calls)
    cli.__aenter__ = AsyncMock(return_value=cli)
    cli.__aexit__ = AsyncMock(return_value=None)

    with patch("app.forwarder.httpx.AsyncClient", return_value=cli):
        return asyncio.run(forward_to_system_a(doc, target))


def test_forward_single_success():
    result = _run_forward()
    assert result["ok"] is True
    assert result["status_code"] == 200


def test_forward_single_failure():
    result = _run_forward(mock_responses=[{"code": "500", "success": False, "message": "未找到单据"}])
    assert result["ok"] is False
    assert "未找到单据" in result["error"]


def test_forward_multi_split_aggregates():
    """多单据拆分：4 张全部成功 → ok=True。"""
    inner = {
        "billNo": "B1,B2,B3,B4",
        "invoiceNum": "INV01",
        "invoiceDetail": [
            {"amount": 100, "taxAmount": 13},
            {"amount": 200, "taxAmount": 26},
            {"amount": 300, "taxAmount": 39},
            {"amount": 400, "taxAmount": 52},
        ],
    }
    doc = {"parsed": {"interfaceCode": "INVOICE.OPEN", "returnCode": "0", "data": _b64(inner)}}
    good = {"code": "200", "success": True}
    result = _run_forward(doc=doc, mock_responses=[good, good, good, good])
    assert result["ok"] is True


def test_forward_multi_partial_failure():
    """多单据拆分：1 张失败 → ok=False，error 聚合。"""
    inner = {
        "billNo": "B1,B2",
        "invoiceNum": "INV01",
        "invoiceDetail": [{"amount": 100}, {"amount": 200}],
    }
    doc = {"parsed": {"interfaceCode": "INVOICE.OPEN", "returnCode": "0", "data": _b64(inner)}}
    result = _run_forward(doc=doc, mock_responses=[
        {"code": "200", "success": True},
        {"code": "500", "success": False, "message": "not found"},
    ])
    assert result["ok"] is False
    assert "not found" in result["error"]


# ── record_forward_result ──────────────────────────

def test_record_forward_result_sent():
    coll = MagicMock()
    coll.update_one = AsyncMock()
    db = MagicMock()
    db.kdcloud_callbacks = coll
    asyncio.run(record_forward_result(db, "OID", "http://sysA/cb",
        {"ok": True, "status_code": 200, "error": None}))
    update = coll.update_one.call_args.args[1]
    assert update["$set"]["forward_status"] == "sent"
    assert update["$inc"]["forward_attempts"] == 1
    assert update["$push"]["forward_history"]["$slice"] == -10


def test_record_forward_result_failed():
    coll = MagicMock()
    coll.update_one = AsyncMock()
    db = MagicMock()
    db.kdcloud_callbacks = coll
    asyncio.run(record_forward_result(db, "OID", "http://sysA/cb",
        {"ok": False, "status_code": 500, "error": "boom"}))
    update = coll.update_one.call_args.args[1]
    assert update["$set"]["forward_status"] == "failed"
    assert update["$set"]["last_forward_error"] == "boom"
