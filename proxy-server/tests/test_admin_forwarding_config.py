"""forwarding-config 运行时开关端点 + runtime_config 缓存测试。"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app import runtime_config
from app.main import app

_AUTH_H = {"Authorization": "Bearer unit-test-admin-token"}


@pytest.fixture(autouse=True)
def _clear_cache():
    """每个用例前后清 runtime_config 缓存，避免串扰。"""
    runtime_config._clear_cache()
    yield
    runtime_config._clear_cache()


@pytest.fixture
def fake_collection():
    coll = MagicMock()
    coll.find_one = AsyncMock(return_value=None)
    coll.update_one = AsyncMock()
    return coll


@pytest.fixture
def fake_db(fake_collection):
    db = MagicMock()
    db.proxy_settings = fake_collection
    return db


@pytest.fixture
def client(fake_db):
    with patch("app.runtime_config.mongodb.get_db", return_value=fake_db):
        yield TestClient(app)


# ── admin 端点 ──────────────────────────────────

def test_get_config_default_false(client, fake_collection):
    """无记录时默认 auto_forward_enabled=false。"""
    r = client.get("/api/admin/forwarding-config", headers=_AUTH_H)
    assert r.status_code == 200
    assert r.json()["auto_forward_enabled"] is False


def test_get_config_requires_auth(client):
    r = client.get("/api/admin/forwarding-config", headers={"Authorization": "Bearer wrong"})
    assert r.status_code == 401


def test_put_config_enables(client, fake_collection):
    """PUT true：upsert 写入且回显 true。"""
    # PUT 后 get_forwarding_config 再查库，返回已启用
    fake_collection.find_one = AsyncMock(return_value={"_id": "forwarding", "auto_forward_enabled": True})
    r = client.put(
        "/api/admin/forwarding-config",
        headers=_AUTH_H,
        json={"auto_forward_enabled": True},
    )
    assert r.status_code == 200
    assert r.json()["auto_forward_enabled"] is True
    # upsert 被调用
    fake_collection.update_one.assert_awaited_once()
    args = fake_collection.update_one.call_args
    assert args.kwargs.get("upsert") is True
    assert args.args[1]["$set"]["auto_forward_enabled"] is True


def test_put_config_validation_error(client):
    """缺 auto_forward_enabled → 422。"""
    r = client.put("/api/admin/forwarding-config", headers=_AUTH_H, json={})
    assert r.status_code == 422


# ── runtime_config 缓存行为 ─────────────────────

def test_get_auto_forward_enabled_caches(fake_db, fake_collection):
    """10s 内命中缓存：第二次不再查库。"""
    fake_collection.find_one = AsyncMock(return_value={"auto_forward_enabled": True})
    with patch("app.runtime_config.mongodb.get_db", return_value=fake_db):
        v1 = asyncio.run(runtime_config.get_auto_forward_enabled())
        v2 = asyncio.run(runtime_config.get_auto_forward_enabled())
    assert v1 is True and v2 is True
    # 只查库一次（第二次命中缓存）
    assert fake_collection.find_one.await_count == 1


def test_set_clears_cache(fake_db, fake_collection):
    """set 后缓存失效，下次重新查库。"""
    fake_collection.find_one = AsyncMock(return_value={"auto_forward_enabled": False})
    with patch("app.runtime_config.mongodb.get_db", return_value=fake_db):
        asyncio.run(runtime_config.get_auto_forward_enabled())      # 填充缓存
        asyncio.run(runtime_config.set_auto_forward_enabled(True))  # 清缓存
        fake_collection.find_one = AsyncMock(return_value={"auto_forward_enabled": True})
        v = asyncio.run(runtime_config.get_auto_forward_enabled())  # 重新查库
    assert v is True
