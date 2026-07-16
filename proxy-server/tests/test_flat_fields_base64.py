"""_extract_flat_fields / _decode_data_field 对 base64 data 的处理测试。

金蝶真实报文 data 是内层 JSON 的 base64 字符串，验证解码后能正确提取
serial_nos / bill_nos / batches / system_sources。
"""
from __future__ import annotations

import base64
import json

from app.endpoints.callbacks import _decode_data_field, _extract_flat_fields


def _b64(obj) -> str:
    return base64.b64encode(json.dumps(obj, ensure_ascii=False).encode("utf-8")).decode("utf-8")


# ── _decode_data_field ─────────────────────────────

def test_decode_dict_passthrough():
    d = {"billNo": "B1"}
    assert _decode_data_field(d) is d


def test_decode_list_passthrough():
    lst = [{"billNo": "B1"}]
    assert _decode_data_field(lst) is lst


def test_decode_base64_object():
    b64 = _b64({"billNo": "B1", "serialNo": "SN1"})
    assert _decode_data_field(b64) == {"billNo": "B1", "serialNo": "SN1"}


def test_decode_base64_array():
    b64 = _b64([{"billNo": "B1"}, {"billNo": "B2"}])
    assert _decode_data_field(b64) == [{"billNo": "B1"}, {"billNo": "B2"}]


def test_decode_invalid_base64_returns_none():
    assert _decode_data_field("not-base64-@@@") is None


def test_decode_empty_and_nonstr_returns_none():
    assert _decode_data_field("") is None
    assert _decode_data_field(None) is None
    assert _decode_data_field(42) is None


# ── _extract_flat_fields with base64 data ──────────

def test_flat_base64_single_invoice():
    """5.1.02：data 是 base64 单张对象。"""
    inner = {
        "billNo": "AR-B01A-2026024703",
        "serialNo": "SN123",
        "systemSource": "systemA",
        "invoiceNum": "26312000004133675116",
    }
    parsed = {"interfaceCode": "INVOICE.OPEN", "returnCode": "0", "data": _b64(inner)}
    flat = _extract_flat_fields(parsed)
    assert flat["interface_code"] == "INVOICE.OPEN"
    assert flat["return_code"] == "0"
    assert flat["bill_nos"] == ["AR-B01A-2026024703"]
    assert flat["serial_nos"] == ["SN123"]
    assert flat["system_sources"] == ["systemA"]


def test_flat_base64_array_invoices():
    """5.1.03：data 是 base64 数组。"""
    inner = [
        {"billNo": "B1", "serialNo": "SN1", "systemSource": "systemA", "batch": "BT1"},
        {"billNo": "B1", "serialNo": "SN2", "systemSource": "systemA", "batch": "BT1"},
    ]
    parsed = {"interfaceCode": "INVOICE.OPEN", "data": _b64(inner)}
    flat = _extract_flat_fields(parsed)
    assert flat["serial_nos"] == ["SN1", "SN2"]
    assert flat["bill_nos"] == ["B1", "B1"]
    assert flat["system_sources"] == ["systemA", "systemA"]
    assert flat["batches"] == ["BT1", "BT1"]


def test_flat_plaintext_dict_still_works():
    """明文 dict data 仍兼容（未来若金蝶发明文）。"""
    parsed = {"data": {"billNo": "B1", "serialNo": "SN1", "systemSource": "sysA"}}
    flat = _extract_flat_fields(parsed)
    assert flat["bill_nos"] == ["B1"]
    assert flat["serial_nos"] == ["SN1"]
    assert flat["system_sources"] == ["sysA"]


def test_flat_unparseable_data_stays_empty():
    """data 是非 base64 乱串时，打平留空，不报错。"""
    parsed = {"interfaceCode": "INVOICE.OPEN", "data": "@@@not-base64@@@"}
    flat = _extract_flat_fields(parsed)
    assert flat["interface_code"] == "INVOICE.OPEN"
    assert flat["serial_nos"] == []
    assert flat["bill_nos"] == []
    assert flat["system_sources"] == []
