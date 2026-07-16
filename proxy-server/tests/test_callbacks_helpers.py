"""callbacks.py 纯函数单元测试（不依赖 MongoDB）。

覆盖 _try_parse_json / _client_ip / _extract_flat_fields / _build_doc 等纯函数逻辑。
端点集成测试见 test_callbacks_endpoints.py。
"""
from __future__ import annotations

from unittest.mock import MagicMock

from app.endpoints.callbacks import (
    _append_from_dict,
    _build_doc,
    _client_ip,
    _extract_flat_fields,
    _try_parse_json,
)


# ── _try_parse_json ─────────────────────────────────

def test_try_parse_json_valid_object():
    parsed, err = _try_parse_json(b'{"a": 1}')
    assert parsed == {"a": 1}
    assert err is None


def test_try_parse_json_valid_array():
    parsed, err = _try_parse_json(b"[1, 2, 3]")
    assert parsed == [1, 2, 3]
    assert err is None


def test_try_parse_json_empty_body():
    parsed, err = _try_parse_json(b"")
    assert parsed is None
    assert err is None


def test_try_parse_json_invalid():
    parsed, err = _try_parse_json(b"not-json{{")
    assert parsed is None
    assert err is not None
    assert "JSONDecodeError" in err or "ValueError" in err


# ── _client_ip ─────────────────────────────────────

def _make_request(headers: dict, client_host: str | None = "127.0.0.1"):
    """构造 Request 的最小 mock，只需要 headers 和 client 属性。"""
    req = MagicMock()
    req.headers = headers
    if client_host is None:
        req.client = None
    else:
        req.client = MagicMock()
        req.client.host = client_host
    return req


def test_client_ip_prefers_xff_first():
    req = _make_request({"x-forwarded-for": "1.2.3.4, 10.0.0.1", "x-real-ip": "9.9.9.9"})
    assert _client_ip(req) == "1.2.3.4"


def test_client_ip_falls_back_to_xri():
    req = _make_request({"x-real-ip": "9.9.9.9"})
    assert _client_ip(req) == "9.9.9.9"


def test_client_ip_falls_back_to_client_host():
    req = _make_request({}, client_host="127.0.0.1")
    assert _client_ip(req) == "127.0.0.1"


def test_client_ip_no_client_returns_empty():
    req = _make_request({}, client_host=None)
    assert _client_ip(req) == ""


# ── _extract_flat_fields ───────────────────────────

def test_flat_5_1_02_single_data():
    """5.1.02 按票回调 data 是单对象。"""
    parsed = {
        "interfaceCode": "INVOICE.OPEN",
        "returnCode": "0",
        "returnMsg": "success",
        "data": {"serialNo": "SN123", "billNo": "B1"},
    }
    flat = _extract_flat_fields(parsed)
    assert flat["interface_code"] == "INVOICE.OPEN"
    assert flat["return_code"] == "0"
    assert flat["serial_nos"] == ["SN123"]
    assert flat["bill_nos"] == ["B1"]
    assert flat["batches"] == []


def test_flat_5_1_03_array_data():
    """5.1.03 按单回调 data 是数组，打平所有 serialNo/billNo/batch。"""
    parsed = {
        "interfaceCode": "INVOICE.OPEN",
        "returnCode": "0",
        "data": [
            {"serialNo": "SN1", "billNo": "B1", "batch": "BT1"},
            {"serialNo": "SN2", "billNo": "B1", "batch": "BT1"},
            {"serialNo": "SN3", "billNo": "B2"},  # 缺 batch
        ],
    }
    flat = _extract_flat_fields(parsed)
    assert flat["interface_code"] == "INVOICE.OPEN"
    assert flat["serial_nos"] == ["SN1", "SN2", "SN3"]
    assert flat["bill_nos"] == ["B1", "B1", "B2"]
    assert flat["batches"] == ["BT1", "BT1"]  # 只两个非空


def test_flat_empty_data():
    """data 缺失或为空时打平字段为空数组。"""
    flat = _extract_flat_fields({"interfaceCode": "X", "returnCode": "0"})
    assert flat["interface_code"] == "X"
    assert flat["serial_nos"] == []
    assert flat["bill_nos"] == []
    assert flat["batches"] == []


def test_flat_non_dict_parsed():
    """parsed 不是 dict（数组/None/字符串）时全部字段都留空。"""
    for p in (None, [1, 2, 3], "raw string", 42):
        flat = _extract_flat_fields(p)
        assert flat["interface_code"] is None
        assert flat["return_code"] is None
        assert flat["serial_nos"] == []


def test_flat_ignores_empty_string_fields():
    """空字符串 serialNo 不应被加入数组。"""
    parsed = {"data": {"serialNo": "", "billNo": "B1"}}
    flat = _extract_flat_fields(parsed)
    assert flat["serial_nos"] == []
    assert flat["bill_nos"] == ["B1"]


def test_flat_interface_code_type_guard():
    """interfaceCode 若不是字符串，返回 None（防御性）。"""
    parsed = {"interfaceCode": 123, "returnCode": None}
    flat = _extract_flat_fields(parsed)
    assert flat["interface_code"] is None
    assert flat["return_code"] is None


# ── _append_from_dict ──────────────────────────────

def test_append_from_dict_all_keys():
    result = {"serial_nos": [], "bill_nos": [], "batches": []}
    _append_from_dict({"serialNo": "S", "billNo": "B", "batch": "BT"}, result)
    assert result == {"serial_nos": ["S"], "bill_nos": ["B"], "batches": ["BT"]}


def test_append_from_dict_skips_missing():
    result = {"serial_nos": [], "bill_nos": [], "batches": []}
    _append_from_dict({"serialNo": "S"}, result)
    assert result == {"serial_nos": ["S"], "bill_nos": [], "batches": []}


# ── _build_doc ─────────────────────────────────────

def test_build_doc_full():
    """_build_doc 组装的字段齐全，parsed 是 dict 时保留原文。"""
    req = _make_request(
        {"content-type": "application/json", "x-forwarded-for": "1.2.3.4"},
        client_host="127.0.0.1",
    )
    req.query_params = {"eid": "17812029"}
    parsed = {"interfaceCode": "INVOICE.OPEN", "data": {"serialNo": "SN1", "billNo": "B1"}}
    raw = b'{"interfaceCode":"INVOICE.OPEN","data":{"serialNo":"SN1","billNo":"B1"}}'
    doc = _build_doc(req, "by-invoice", raw, parsed, None)

    assert doc["endpoint"] == "by-invoice"
    assert doc["content_type"] == "application/json"
    assert doc["client_ip"] == "1.2.3.4"
    assert doc["query_params"] == {"eid": "17812029"}
    assert doc["raw_body"] == raw.decode("utf-8")
    assert doc["raw_len"] == len(raw)
    assert doc["parsed"] == parsed
    assert doc["parse_error"] is None
    # 打平字段
    assert doc["interface_code"] == "INVOICE.OPEN"
    assert doc["serial_nos"] == ["SN1"]
    assert doc["bill_nos"] == ["B1"]
    # received_at 应为 tz-aware datetime
    assert doc["received_at"] is not None
    assert doc["received_at"].tzinfo is not None


def test_build_doc_parse_error():
    """parsed 是 None、parse_err 有值时，doc 中 parsed 为 None、parse_error 有值。"""
    req = _make_request({"content-type": "text/plain"})
    req.query_params = {}
    doc = _build_doc(req, "by-invoice", b"not-json", None, "JSONDecodeError: xxx")
    assert doc["parsed"] is None
    assert doc["parse_error"] == "JSONDecodeError: xxx"
    assert doc["raw_body"] == "not-json"
    # 打平字段全部留空
    assert doc["serial_nos"] == []


def test_build_doc_parsed_is_array_stored_as_none():
    """parsed 是数组时不放进 parsed 字段（防止 MongoDB doc 结构不一致），打平仍生效。"""
    req = _make_request({})
    req.query_params = {}
    doc = _build_doc(req, "by-apply", b"[]", [], None)
    assert doc["parsed"] is None
    assert doc["serial_nos"] == []
