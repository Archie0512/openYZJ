"""开放 API 鉴权依赖。

1. require_api_auth: HMAC-SHA256 签名鉴权（第三方 ERP/道闸系统）
2. require_bearer_auth: 简化 Bearer Token 鉴权（小程序前端）

签名计算方式：HMAC-SHA256(secret, method + path + timestamp + body_md5)
其中 body_md5 是请求体的 MD5 十六进制摘要。
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import time

from fastapi import HTTPException, Request

from app.config import settings
from app.core.crypto import decrypt_secret
from app.db import mongodb

log = logging.getLogger(__name__)

# 时间戳有效窗口（±5 分钟）
_TIMESTAMP_TOLERANCE = 300


async def require_api_auth(request: Request) -> str:
    """FastAPI 依赖：验证开放 API 签名，返回 client_id。

    Headers 必须包含：
      - X-Api-Key: 客户端分配的 API Key
      - X-Timestamp: Unix 时间戳（秒）
      - X-Signature: HMAC-SHA256 签名的十六进制字符串
    """
    api_key = request.headers.get("X-Api-Key")
    timestamp_str = request.headers.get("X-Timestamp")
    signature = request.headers.get("X-Signature")

    if not api_key or not timestamp_str or not signature:
        raise HTTPException(
            status_code=401,
            detail="缺少鉴权 Headers: X-Api-Key, X-Timestamp, X-Signature",
        )

    # 1. 检查 timestamp 有效性
    try:
        ts = int(timestamp_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="X-Timestamp 格式无效")

    now = int(time.time())
    if abs(now - ts) > _TIMESTAMP_TOLERANCE:
        raise HTTPException(status_code=401, detail="请求时间戳已过期（±5min）")

    # 2. 从 MongoDB 查找客户端
    db = mongodb.get_db()
    client_doc = await db.api_clients.find_one({"api_key": api_key})
    if not client_doc:
        raise HTTPException(status_code=401, detail="无效的 API Key")

    if client_doc.get("status") != "active":
        raise HTTPException(status_code=403, detail="API 客户端已被禁用")

    # 3. 检查端点白名单
    allowed = client_doc.get("allowed_endpoints", [])
    if allowed:
        path = request.url.path
        if not any(path.startswith(ep) for ep in allowed):
            raise HTTPException(status_code=403, detail="该端点未授权")

    # 4. 解密 secret 并验证签名
    try:
        secret = decrypt_secret(client_doc["api_secret_encrypted"])
    except Exception:
        log.error("解密 api_secret 失败 client_id=%s", client_doc.get("client_id"))
        raise HTTPException(status_code=500, detail="服务端鉴权配置异常")

    # 计算预期签名
    body = await request.body()
    body_md5 = hashlib.md5(body).hexdigest() if body else hashlib.md5(b"").hexdigest()
    method = request.method.upper()
    path = request.url.path
    sign_payload = f"{method}{path}{timestamp_str}{body_md5}"

    expected = hmac.new(
        secret.encode("utf-8"),
        sign_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="签名验证失败")

    return str(client_doc["client_id"])


async def require_bearer_auth(request: Request) -> str:
    """简化 Bearer Token 鉴权（小程序场景）。

    检查 Authorization header 中的 Bearer token 是否：
      - 与 admin_token 匹配，或
      - 存在于 api_clients 集合中某个 active 客户端的 api_key

    返回标识字符串（admin 或 client_id）。
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="缺少 Authorization: Bearer <token>",
        )

    token = auth_header[7:]  # strip "Bearer "
    if not token:
        raise HTTPException(status_code=401, detail="Token 不能为空")

    # 检查是否匹配 admin_token
    if hmac.compare_digest(token, settings.admin_token):
        return "admin"

    # 检查是否存在于 api_clients 中
    db = mongodb.get_db()
    client_doc = await db.api_clients.find_one({"api_key": token})
    if client_doc and client_doc.get("status") == "active":
        return str(client_doc["client_id"])

    raise HTTPException(status_code=401, detail="无效的 Bearer Token")
