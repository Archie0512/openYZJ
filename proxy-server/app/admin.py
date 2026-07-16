"""代理客户端管理接口。

提供 proxy_clients 集合的 CRUD，鉴权复用 require_admin。
以及 kdcloud_callbacks 集合的只读查询（列表 / 详情）。
"""
from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.admin_auth import require_admin
from app.crypto import encrypt_secret
from app import mongodb
from app.models import (
    ProxyClientCreateReq,
    ProxyClientPublic,
    ProxyClientUpdateReq,
)

router = APIRouter(
    prefix="/api/admin/proxy-clients",
    tags=["Admin - Proxy Clients"],
    dependencies=[Depends(require_admin)],
)


def _to_public(doc: dict) -> ProxyClientPublic:
    """投影到对外安全视图，剥离敏感字段。"""
    return ProxyClientPublic(
        client_id=doc.get("client_id", ""),
        client_name=doc.get("client_name", ""),
        api_key=doc.get("api_key", ""),
        allowed_endpoints=doc.get("allowed_endpoints", []),
        rate_limit=doc.get("rate_limit", 60),
        status=doc.get("status", "active"),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
        updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
    )


@router.post("", response_model=ProxyClientPublic)
async def create_proxy_client(req: ProxyClientCreateReq):
    """注册一个新的代理调用方（System A）。"""
    db = mongodb.get_db()
    if await db.proxy_clients.find_one({"api_key": req.api_key}):
        raise HTTPException(409, "api_key already exists")
    if await db.proxy_clients.find_one({"client_id": req.client_name}):
        raise HTTPException(409, "client_name already exists")

    now = datetime.now(timezone.utc)
    doc = {
        "client_id": req.client_name,
        "client_name": req.client_name,
        "api_key": req.api_key,
        "api_secret_encrypted": encrypt_secret(req.api_secret),
        "allowed_endpoints": req.allowed_endpoints,
        "rate_limit": req.rate_limit,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    await db.proxy_clients.insert_one(doc)
    return _to_public(doc)


@router.get("", response_model=list[ProxyClientPublic])
async def list_proxy_clients():
    """列出全部代理客户端（安全视图，不含密钥）。"""
    db = mongodb.get_db()
    cursor = db.proxy_clients.find({}, {"api_secret_encrypted": 0})
    return [_to_public(doc) async for doc in cursor]


@router.get("/{client_id}", response_model=ProxyClientPublic)
async def get_proxy_client(client_id: str):
    """查询单个代理客户端."""
    db = mongodb.get_db()
    doc = await db.proxy_clients.find_one({"client_id": client_id})
    if not doc:
        raise HTTPException(404, "proxy client not found")
    return _to_public(doc)


@router.put("/{client_id}", response_model=ProxyClientPublic)
async def update_proxy_client(
    client_id: str, req: ProxyClientUpdateReq
):
    """局部更新代理客户端字段；提供 api_secret 时重新加密。"""
    db = mongodb.get_db()
    update = {"updated_at": datetime.now(timezone.utc)}
    for field in ("client_name", "allowed_endpoints", "rate_limit", "status"):
        v = getattr(req, field)
        if v is not None:
            update[field] = v
    if req.api_secret is not None:
        update["api_secret_encrypted"] = encrypt_secret(req.api_secret)

    from pymongo import ReturnDocument

    res = await db.proxy_clients.find_one_and_update(
        {"client_id": client_id},
        {"$set": update},
        return_document=ReturnDocument.AFTER,
    )
    if not res:
        raise HTTPException(404, "proxy client not found")
    return _to_public(res)


@router.delete("/{client_id}")
async def delete_proxy_client(client_id: str):
    """删除代理客户端。"""
    db = mongodb.get_db()
    res = await db.proxy_clients.delete_one({"client_id": client_id})
    if res.deleted_count == 0:
        raise HTTPException(404, "proxy client not found")
    return {"deleted": True}


# ══════════════════════════════════════════════════════════════
# kdcloud_callbacks 只读查询（金蝶发票云回调持久化审计）
# ══════════════════════════════════════════════════════════════

callback_events_router = APIRouter(
    prefix="/api/admin/callback-events",
    tags=["Admin - Callback Events"],
    dependencies=[Depends(require_admin)],
)


# 列表视图去掉大字段，减轻网络负载
_LIST_PROJECTION = {
    "raw_body": 0,
    "headers": 0,
    "parsed": 0,
}


def _parse_date(s: str, field: str) -> datetime:
    """把 YYYY-MM-DD 或 ISO 8601 字符串解析成 tz-aware datetime。

    仅日期（YYYY-MM-DD）视为当日 00:00:00 UTC。
    """
    try:
        # datetime.fromisoformat 从 3.11 起接受纯日期
        dt = datetime.fromisoformat(s)
    except ValueError as e:
        raise HTTPException(400, f"invalid {field}: {s} ({e})") from e
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _serialize(doc: dict) -> dict:
    """把 MongoDB doc 中的 ObjectId / datetime 转成 JSON 安全值。"""
    out = dict(doc)
    if "_id" in out and isinstance(out["_id"], ObjectId):
        out["_id"] = str(out["_id"])
    # datetime 由 FastAPI 默认 JSONEncoder 自动序列化为 ISO 8601，此处无需处理
    return out


@callback_events_router.get("")
async def list_callback_events(
    endpoint: str | None = Query(None, description="by-invoice / by-apply / apply-return"),
    serial_no: str | None = Query(None, description="按发票流水号过滤"),
    bill_no: str | None = Query(None, description="按单据号过滤"),
    interface_code: str | None = Query(None, description="INVOICE.OPEN / INVOICE.RED / INVOICE.CANCEL"),
    date_from: str | None = Query(None, description="起始时间（YYYY-MM-DD 或 ISO 8601）"),
    date_to: str | None = Query(None, description="截止时间（YYYY-MM-DD 或 ISO 8601）"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict:
    """列表查询 kdcloud_callbacks。

    不返回 raw_body/headers/parsed 完整字段，只给汇总字段（_id、endpoint、
    received_at、打平字段、raw_len）。详情用 GET /{event_id}。
    """
    db = mongodb.get_db()
    q: dict = {}
    if endpoint:
        q["endpoint"] = endpoint
    if serial_no:
        q["serial_nos"] = serial_no
    if bill_no:
        q["bill_nos"] = bill_no
    if interface_code:
        q["interface_code"] = interface_code
    if date_from or date_to:
        rng: dict = {}
        if date_from:
            rng["$gte"] = _parse_date(date_from, "date_from")
        if date_to:
            rng["$lte"] = _parse_date(date_to, "date_to")
        q["received_at"] = rng

    total = await db.kdcloud_callbacks.count_documents(q)
    cursor = (
        db.kdcloud_callbacks.find(q, _LIST_PROJECTION)
        .sort("received_at", -1)
        .skip(offset)
        .limit(limit)
    )
    items = [_serialize(doc) async for doc in cursor]
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@callback_events_router.get("/{event_id}")
async def get_callback_event(event_id: str) -> dict:
    """按 _id 返回完整回调 doc（含 raw_body/headers/parsed）。"""
    try:
        oid = ObjectId(event_id)
    except (InvalidId, TypeError) as e:
        raise HTTPException(400, f"invalid event id: {event_id}") from e

    db = mongodb.get_db()
    doc = await db.kdcloud_callbacks.find_one({"_id": oid})
    if not doc:
        raise HTTPException(404, "callback event not found")
    return _serialize(doc)
