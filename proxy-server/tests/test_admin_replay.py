"""callback-events replay 端点测试。"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import app

_AUTH_H = {"Authorization": "Bearer unit-test-admin-token"}
_OID = "64d0f0a0f0a0f0a0f0a0f0a0"


def _invoice_doc(**over):
    """构造一条 by-invoice 落库 doc（parsed 为明文，方便断言）。"""
    doc = {
        "_id": ObjectId(_OID),
        "endpoint": "by-invoice",
        "parsed": {"interfaceCode": "INVOICE.OPEN", "returnCode": "0",
                   "data": {"billNo": "B1", "invoiceNum": "123"}},
        "matched_client_id": None,
        "forward_attempts": 0,
    }
    doc.update(over)
    return doc


@pytest.fixture
def fake_cb():
    coll = MagicMock()
    coll.find_one = AsyncMock(return_value=None)
    coll.update_one = AsyncMock()
    return coll


@pytest.fixture
def fake_clients():
    coll = MagicMock()
    coll.find_one = AsyncMock(return_value=None)
    return coll


@pytest.fixture
def fake_db(fake_cb, fake_clients):
    db = MagicMock()
    db.kdcloud_callbacks = fake_cb
    db.proxy_clients = fake_clients
    return db


@pytest.fixture
def client(fake_db):
    with patch("app.admin.mongodb.get_db", return_value=fake_db):
        yield TestClient(app)


def test_replay_invalid_id(client):
    r = client.post("/api/admin/callback-events/not-oid/replay", headers=_AUTH_H)
    assert r.status_code == 400


def test_replay_not_found(client, fake_cb):
    fake_cb.find_one = AsyncMock(return_value=None)
    r = client.post(f"/api/admin/callback-events/{_OID}/replay", headers=_AUTH_H)
    assert r.status_code == 404


def test_replay_unsupported_endpoint(client, fake_cb):
    """by-apply 不支持转发 → 422 且标 unsupported。"""
    fake_cb.find_one = AsyncMock(return_value=_invoice_doc(endpoint="by-apply"))
    r = client.post(f"/api/admin/callback-events/{_OID}/replay", headers=_AUTH_H)
    assert r.status_code == 422
    fake_cb.update_one.assert_awaited()  # 标记 unsupported
    set_doc = fake_cb.update_one.call_args.args[1]["$set"]
    assert set_doc["forward_status"] == "unsupported"


def test_replay_no_target_url(client, fake_cb):
    """无 target_url、无 client callback_url → 400。"""
    fake_cb.find_one = AsyncMock(return_value=_invoice_doc())
    r = client.post(f"/api/admin/callback-events/{_OID}/replay", headers=_AUTH_H)
    assert r.status_code == 400


def test_replay_with_explicit_target_url(client, fake_cb):
    """显式 target_url：转发成功并回写。"""
    # find_one 第一次返回 doc；record 后再查 forward_attempts
    fake_cb.find_one = AsyncMock(side_effect=[_invoice_doc(), {"forward_attempts": 1}])
    fake_result = {"ok": True, "status_code": 200, "error": None, "target_url": "http://sysA/cb"}
    with patch("app.admin.forward_to_system_a", AsyncMock(return_value=fake_result)) as fwd, \
         patch("app.admin.record_forward_result", AsyncMock()) as rec:
        r = client.post(
            f"/api/admin/callback-events/{_OID}/replay",
            headers=_AUTH_H,
            json={"target_url": "http://sysA/cb"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["forwarded"] is True
    assert body["status_code"] == 200
    assert body["target_url"] == "http://sysA/cb"
    assert body["forward_attempts"] == 1
    fwd.assert_awaited_once()
    rec.assert_awaited_once()


def test_replay_resolves_client_callback_url(client, fake_cb, fake_clients):
    """无 target_url 时用 matched_client_id 的 callback_url。"""
    fake_cb.find_one = AsyncMock(side_effect=[
        _invoice_doc(matched_client_id="systemA"),
        {"forward_attempts": 2},
    ])
    fake_clients.find_one = AsyncMock(return_value={"callback_url": "http://sysA/from-client"})
    fake_result = {"ok": True, "status_code": 200, "error": None, "target_url": "http://sysA/from-client"}
    with patch("app.admin.forward_to_system_a", AsyncMock(return_value=fake_result)), \
         patch("app.admin.record_forward_result", AsyncMock()):
        r = client.post(f"/api/admin/callback-events/{_OID}/replay", headers=_AUTH_H)
    assert r.status_code == 200
    assert r.json()["target_url"] == "http://sysA/from-client"


def test_replay_requires_auth(client):
    r = client.post(
        f"/api/admin/callback-events/{_OID}/replay",
        headers={"Authorization": "Bearer wrong"},
    )
    assert r.status_code == 401
