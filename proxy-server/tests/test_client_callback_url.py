"""proxy_clients 的 callback_url 字段读写测试。

覆盖 create / get / update 三条路径对 callback_url 的支持。
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

_AUTH_H = {"Authorization": "Bearer unit-test-admin-token"}
_CB_URL = "http://baodetest.haverise.com:23822/callback/invoiceCallback"


@pytest.fixture
def fake_collection():
    coll = MagicMock()
    coll.find_one = AsyncMock(return_value=None)
    coll.insert_one = AsyncMock()
    coll.find_one_and_update = AsyncMock(return_value=None)
    return coll


@pytest.fixture
def fake_db(fake_collection):
    db = MagicMock()
    db.proxy_clients = fake_collection
    return db


@pytest.fixture
def client(fake_db):
    with patch("app.admin.mongodb.get_db", return_value=fake_db):
        yield TestClient(app)


def test_create_client_with_callback_url(client, fake_collection):
    """创建 client 时 callback_url 落库且回显。"""
    fake_collection.find_one = AsyncMock(return_value=None)
    r = client.post(
        "/api/admin/proxy-clients",
        headers=_AUTH_H,
        json={
            "client_name": "systemA",
            "api_key": "key1",
            "api_secret": "secret1",
            "callback_url": _CB_URL,
        },
    )
    assert r.status_code == 200
    assert r.json()["callback_url"] == _CB_URL
    doc = fake_collection.insert_one.call_args.args[0]
    assert doc["callback_url"] == _CB_URL


def test_create_client_callback_url_defaults_empty(client, fake_collection):
    """不传 callback_url 时默认空字符串。"""
    fake_collection.find_one = AsyncMock(return_value=None)
    r = client.post(
        "/api/admin/proxy-clients",
        headers=_AUTH_H,
        json={"client_name": "sysB", "api_key": "k2", "api_secret": "s2"},
    )
    assert r.status_code == 200
    assert r.json()["callback_url"] == ""


def test_get_client_returns_callback_url(client, fake_collection):
    """详情返回 callback_url。"""
    now = datetime(2026, 7, 15, tzinfo=timezone.utc)
    fake_collection.find_one = AsyncMock(return_value={
        "client_id": "systemA",
        "client_name": "systemA",
        "api_key": "key1",
        "callback_url": _CB_URL,
        "allowed_endpoints": [],
        "rate_limit": 60,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    })
    r = client.get("/api/admin/proxy-clients/systemA", headers=_AUTH_H)
    assert r.status_code == 200
    assert r.json()["callback_url"] == _CB_URL


def test_update_client_callback_url(client, fake_collection):
    """更新 callback_url：$set 含该字段且回显更新值。"""
    now = datetime(2026, 7, 15, tzinfo=timezone.utc)
    new_url = "http://new-host/callback/invoiceCallback"
    fake_collection.find_one_and_update = AsyncMock(return_value={
        "client_id": "systemA",
        "client_name": "systemA",
        "api_key": "key1",
        "callback_url": new_url,
        "allowed_endpoints": [],
        "rate_limit": 60,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    })
    r = client.put(
        "/api/admin/proxy-clients/systemA",
        headers=_AUTH_H,
        json={"callback_url": new_url},
    )
    assert r.status_code == 200
    assert r.json()["callback_url"] == new_url
    # 校验 $set 里带上了 callback_url
    set_doc = fake_collection.find_one_and_update.call_args.args[1]["$set"]
    assert set_doc["callback_url"] == new_url
