"""代理客户端管理接口。

提供 proxy_clients 集合的 CRUD，鉴权复用 require_admin。
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.core.admin_auth import require_admin
from app.core.crypto import encrypt_secret
from app.db import mongodb
from app.proxy.models import (
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
