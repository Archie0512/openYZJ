"""admin callback-events 查询接口测试。

覆盖列表 / 详情 / 鉴权 / 错误路径。
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import app


_ADMIN_TOKEN = "unit-test-admin-token"  # 与 conftest.py 中的 ADMIN_TOKEN 保持一致
_AUTH_H = {"Authorization": f"Bearer {_ADMIN_TOKEN}"}


class _FakeCursor:
    """模拟 pymongo AsyncCursor：支持链式 sort/skip/limit + async 迭代。"""

    def __init__(self, items):
        self._items = list(items)

    def sort(self, *args, **kwargs):
        return self

    def skip(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def __aiter__(self):
        async def gen():
            for x in self._items:
                yield x
        return gen()


@pytest.fixture
def fake_collection():
    """kdcloud_callbacks 的假 collection。"""
    coll = MagicMock()
    coll.count_documents = AsyncMock(return_value=0)
    coll.find = MagicMock(return_value=_FakeCursor([]))
    coll.find_one = AsyncMock(return_value=None)
    return coll


@pytest.fixture
def fake_db(fake_collection):
    db = MagicMock()
    db.kdcloud_callbacks = fake_collection
    return db


@pytest.fixture
def client(fake_db):
    with patch("app.admin.mongodb.get_db", return_value=fake_db):
        yield TestClient(app)


# ── 鉴权 ────────────────────────────────────────

def test_list_requires_auth(fake_db):
    """未带 Bearer Token → 401（require_admin 拒绝）。"""
    with patch("app.admin.mongodb.get_db", return_value=fake_db):
        c = TestClient(app)
        r = c.get("/api/admin/callback-events")
    # 缺 Authorization header 会命中 FastAPI 422（Header 必填）
    # 带错误 token 才是 401。这里断言不是 200 就足够（严格路径见 test_list_wrong_token）
    assert r.status_code != 200


def test_list_wrong_token(fake_db):
    """错误的 Bearer Token → 401。"""
    with patch("app.admin.mongodb.get_db", return_value=fake_db):
        c = TestClient(app)
        r = c.get(
            "/api/admin/callback-events",
            headers={"Authorization": "Bearer wrong-token"},
        )
    assert r.status_code == 401


# ── 列表 ────────────────────────────────────────

def test_list_empty(client, fake_collection):
    """空表：返回 total=0, items=[]。"""
    r = client.get("/api/admin/callback-events", headers=_AUTH_H)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["limit"] == 50
    assert data["offset"] == 0


def test_list_filter_by_serial_no(client, fake_collection):
    """按 serial_no 过滤命中：查询条件正确传给 MongoDB。"""
    now = datetime(2026, 7, 15, 6, 0, 0, tzinfo=timezone.utc)
    fake_collection.count_documents = AsyncMock(return_value=1)
    fake_collection.find = MagicMock(return_value=_FakeCursor([
        {
            "_id": ObjectId("64d0f0a0f0a0f0a0f0a0f0a0"),
            "endpoint": "by-invoice",
            "received_at": now,
            "serial_nos": ["SN123"],
            "bill_nos": ["B1"],
            "interface_code": "INVOICE.OPEN",
            "return_code": "0",
            "raw_len": 42,
        },
    ]))

    r = client.get(
        "/api/admin/callback-events?serial_no=SN123&endpoint=by-invoice",
        headers=_AUTH_H,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["_id"] == "64d0f0a0f0a0f0a0f0a0f0a0"
    assert item["endpoint"] == "by-invoice"
    assert item["serial_nos"] == ["SN123"]

    # 校验 find 收到的 query dict 正确
    call_args = fake_collection.find.call_args
    q = call_args.args[0]
    assert q["serial_nos"] == "SN123"
    assert q["endpoint"] == "by-invoice"
    # 列表投影不返回大字段
    projection = call_args.args[1]
    assert projection == {"raw_body": 0, "headers": 0, "parsed": 0}


def test_list_date_range(client, fake_collection):
    """date_from / date_to 被解析成 tz-aware datetime 传入查询。"""
    r = client.get(
        "/api/admin/callback-events?date_from=2026-07-01&date_to=2026-07-15",
        headers=_AUTH_H,
    )
    assert r.status_code == 200
    q = fake_collection.find.call_args.args[0]
    assert "received_at" in q
    assert q["received_at"]["$gte"].tzinfo is not None
    assert q["received_at"]["$gte"].year == 2026
    assert q["received_at"]["$gte"].month == 7
    assert q["received_at"]["$gte"].day == 1


def test_list_invalid_date_returns_400(client, fake_collection):
    """非法日期字符串返回 400。"""
    r = client.get(
        "/api/admin/callback-events?date_from=notadate",
        headers=_AUTH_H,
    )
    assert r.status_code == 400


def test_list_limit_out_of_range(client, fake_collection):
    """limit 超出 [1, 500] 范围返回 422（pydantic 校验）。"""
    r = client.get(
        "/api/admin/callback-events?limit=1000",
        headers=_AUTH_H,
    )
    assert r.status_code == 422


# ── 详情 ────────────────────────────────────────

def test_get_by_id_returns_full_doc(client, fake_collection):
    """详情接口返回完整 doc（含 raw_body/headers/parsed）。"""
    now = datetime(2026, 7, 15, 6, 0, 0, tzinfo=timezone.utc)
    oid = ObjectId("64d0f0a0f0a0f0a0f0a0f0a0")
    fake_collection.find_one = AsyncMock(return_value={
        "_id": oid,
        "endpoint": "by-invoice",
        "received_at": now,
        "raw_body": '{"interfaceCode":"INVOICE.OPEN"}',
        "headers": {"content-type": "application/json"},
        "parsed": {"interfaceCode": "INVOICE.OPEN"},
        "serial_nos": ["SN1"],
    })
    r = client.get(f"/api/admin/callback-events/{oid}", headers=_AUTH_H)
    assert r.status_code == 200
    data = r.json()
    assert data["_id"] == str(oid)
    assert data["raw_body"].startswith("{")
    assert data["headers"]["content-type"] == "application/json"
    assert data["parsed"]["interfaceCode"] == "INVOICE.OPEN"
    fake_collection.find_one.assert_awaited_once_with({"_id": oid})


def test_get_by_id_invalid_format(client, fake_collection):
    """非 ObjectId 格式 → 400。"""
    r = client.get("/api/admin/callback-events/not-an-oid", headers=_AUTH_H)
    assert r.status_code == 400


def test_get_by_id_not_found(client, fake_collection):
    """合法 ObjectId 但库里没有 → 404。"""
    fake_collection.find_one = AsyncMock(return_value=None)
    r = client.get(
        "/api/admin/callback-events/64d0f0a0f0a0f0a0f0a0f0a0",
        headers=_AUTH_H,
    )
    assert r.status_code == 404
