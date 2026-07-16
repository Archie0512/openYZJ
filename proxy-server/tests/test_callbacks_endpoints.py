"""callbacks 端点集成测试。

使用 fastapi.testclient.TestClient + unittest.mock 替换 mongodb.get_db()，
不依赖真实 MongoDB。

覆盖：
- 落库成功路径（by-invoice / by-apply / apply-return）
- 响应格式严格符合金蝶规范
- 无 Content-Type 也不返回 422
- 坏 JSON body 也照样入库
- DB 写失败仍返回 200 ACK（降级）
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


# ── 通用 fixture ─────────────────────────────────

@pytest.fixture
def fake_collection():
    """一个 insert_one 可 assert 的假 collection。"""
    coll = MagicMock()
    coll.insert_one = AsyncMock()
    return coll


@pytest.fixture
def fake_db(fake_collection):
    """假 db，其 kdcloud_callbacks 属性指向 fake_collection。"""
    db = MagicMock()
    db.kdcloud_callbacks = fake_collection
    return db


@pytest.fixture
def client(fake_db):
    """TestClient + patch mongodb.get_db。

    不进入 lifespan（TestClient(app) 不用 `with`），所以不触发真实 mongodb.connect。
    """
    with patch("app.endpoints.callbacks.mongodb.get_db", return_value=fake_db):
        yield TestClient(app)


# ── 响应格式 ────────────────────────────────────

_EXPECTED_ACK = {"message": "回调成功", "errorCode": "0", "success": True}


def test_ack_format_strict(client, fake_collection):
    """响应体必须严格匹配金蝶规范。"""
    r = client.post(
        "/api/proxy/v1/callbacks/by-invoice",
        json={"interfaceCode": "INVOICE.OPEN", "data": {"serialNo": "S1"}},
    )
    assert r.status_code == 200
    assert r.json() == _EXPECTED_ACK


def test_no_content_type_still_200(client, fake_collection):
    """不带 Content-Type header 也不能返回 422（旧 pydantic 依赖会导致 422）。"""
    r = client.post(
        "/api/proxy/v1/callbacks/by-invoice",
        content=b'{"interfaceCode":"INVOICE.OPEN"}',
        # 无 headers，requests 默认不给 Content-Type
    )
    assert r.status_code == 200
    assert r.json() == _EXPECTED_ACK


def test_bad_json_body_still_persists(client, fake_collection):
    """body 不是合法 JSON 也照样入库（parse_error 记原因）。"""
    r = client.post(
        "/api/proxy/v1/callbacks/by-invoice",
        content=b"this is not json {{",
        headers={"Content-Type": "text/plain"},
    )
    assert r.status_code == 200
    assert r.json() == _EXPECTED_ACK
    # 检查落库时 parse_error 有值
    fake_collection.insert_one.assert_called_once()
    doc = fake_collection.insert_one.call_args.args[0]
    assert doc["parse_error"] is not None
    assert doc["parsed"] is None
    assert doc["raw_body"] == "this is not json {{"


# ── 落库 + 打平字段 ─────────────────────────────

def test_persist_by_invoice_flat_fields(client, fake_collection):
    """5.1.02 按票回调：单个 serialNo/billNo 提取到打平字段。"""
    body = {
        "interfaceCode": "INVOICE.OPEN",
        "returnCode": "0",
        "returnMsg": "success",
        "data": {"serialNo": "SN123", "billNo": "BILL001"},
    }
    r = client.post(
        "/api/proxy/v1/callbacks/by-invoice?eid=17812029",
        json=body,
    )
    assert r.status_code == 200

    fake_collection.insert_one.assert_called_once()
    doc = fake_collection.insert_one.call_args.args[0]
    assert doc["endpoint"] == "by-invoice"
    assert doc["interface_code"] == "INVOICE.OPEN"
    assert doc["return_code"] == "0"
    assert doc["serial_nos"] == ["SN123"]
    assert doc["bill_nos"] == ["BILL001"]
    assert doc["batches"] == []
    assert doc["query_params"] == {"eid": "17812029"}
    assert doc["parsed"] == body
    assert json.loads(doc["raw_body"]) == body


def test_persist_by_apply_flattens_array(client, fake_collection):
    """5.1.03 按单回调：data 数组打平成 serial_nos/bill_nos 完整数组。"""
    body = {
        "interfaceCode": "INVOICE.OPEN",
        "returnCode": "0",
        "data": [
            {"serialNo": "SN1", "billNo": "B1", "batch": "BT1"},
            {"serialNo": "SN2", "billNo": "B1", "batch": "BT1"},
            {"serialNo": "SN3", "billNo": "B2", "batch": "BT2"},
        ],
    }
    r = client.post("/api/proxy/v1/callbacks/by-apply", json=body)
    assert r.status_code == 200

    doc = fake_collection.insert_one.call_args.args[0]
    assert doc["endpoint"] == "by-apply"
    assert doc["serial_nos"] == ["SN1", "SN2", "SN3"]
    assert doc["bill_nos"] == ["B1", "B1", "B2"]
    assert doc["batches"] == ["BT1", "BT1", "BT2"]


def test_persist_apply_return(client, fake_collection):
    """5.1.01 apply-return 也走同一 helper。"""
    r = client.post(
        "/api/proxy/v1/callbacks/apply-return",
        json={"anything": "goes"},
    )
    assert r.status_code == 200
    doc = fake_collection.insert_one.call_args.args[0]
    assert doc["endpoint"] == "apply-return"


# ── 降级：DB 写失败仍 ACK 200 ──────────────────

def test_db_failure_still_acks_200(fake_db, fake_collection):
    """MongoDB insert_one 抛异常时，端点仍返回 200 + 金蝶格式 ACK。"""
    fake_collection.insert_one.side_effect = RuntimeError("mongo down")
    with patch("app.endpoints.callbacks.mongodb.get_db", return_value=fake_db):
        c = TestClient(app)
        r = c.post(
            "/api/proxy/v1/callbacks/by-invoice",
            json={"interfaceCode": "INVOICE.OPEN"},
        )
    assert r.status_code == 200
    assert r.json() == _EXPECTED_ACK
    fake_collection.insert_one.assert_called_once()
