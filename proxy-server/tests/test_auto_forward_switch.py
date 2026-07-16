"""自动转发 hook 开关行为测试（默认关；开关开 + by-invoice 才调度）。"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import app

_OID = ObjectId("64d0f0a0f0a0f0a0f0a0f0a0")
_BODY = {
    "interfaceCode": "INVOICE.OPEN",
    "returnCode": "0",
    "data": {"billNo": "B1", "systemSource": "systemA"},
}


@pytest.fixture
def fake_cb():
    coll = MagicMock()
    coll.insert_one = AsyncMock(return_value=MagicMock(inserted_id=_OID))
    return coll


@pytest.fixture
def fake_db(fake_cb):
    db = MagicMock()
    db.kdcloud_callbacks = fake_cb
    clients = MagicMock()
    clients.find_one = AsyncMock(return_value=None)
    db.proxy_clients = clients
    return db


@pytest.fixture
def client(fake_db):
    with patch("app.endpoints.callbacks.mongodb.get_db", return_value=fake_db):
        yield TestClient(app)


def test_switch_off_no_forward(client):
    """开关关：不调度自动转发。"""
    with patch("app.endpoints.callbacks.get_auto_forward_enabled", AsyncMock(return_value=False)), \
         patch("app.endpoints.callbacks.asyncio.create_task") as ct:
        r = client.post("/api/proxy/v1/callbacks/by-invoice", json=_BODY)
    assert r.status_code == 200
    ct.assert_not_called()


def test_switch_on_by_invoice_triggers(client):
    """开关开 + by-invoice：调度一次自动转发。"""
    with patch("app.endpoints.callbacks.get_auto_forward_enabled", AsyncMock(return_value=True)), \
         patch("app.endpoints.callbacks._safe_auto_forward", MagicMock(return_value=MagicMock())), \
         patch("app.endpoints.callbacks.asyncio.create_task") as ct:
        r = client.post("/api/proxy/v1/callbacks/by-invoice", json=_BODY)
    assert r.status_code == 200
    ct.assert_called_once()


def test_switch_on_non_by_invoice_no_forward(client):
    """开关开但端点是 apply-return：短路不调度（仅 by-invoice 自动转发）。"""
    with patch("app.endpoints.callbacks.get_auto_forward_enabled", AsyncMock(return_value=True)), \
         patch("app.endpoints.callbacks.asyncio.create_task") as ct:
        r = client.post("/api/proxy/v1/callbacks/apply-return", json=_BODY)
    assert r.status_code == 200
    ct.assert_not_called()
