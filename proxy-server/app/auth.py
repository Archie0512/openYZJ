"""代理网关独立鉴权模块。

使用独立的 header 命名空间（X-Proxy-*）和独立的 MongoDB 集合（proxy_clients），
与开放 API 的 api_auth.py 完全隔离。

签名算法：HMAC-SHA256(api_secret, method + path + timestamp + body_md5)
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import time

from fastapi import HTTPException, Request

from app.crypto import decrypt_secret
from app import mongodb

log = logging.getLogger(__name__)

_TIMESTAMP_TOLERANCE = 300  # ±5 分钟


async def require_proxy_auth(request: Request) -> str:
    """FastAPI 依赖：验证代理调用方身份，返回 client_id。

    Headers 必须包含：
      - X-Proxy-Api-Key: 代理客户端 API Key
      - X-Proxy-Timestamp: Unix 时间戳（秒）
      - X-Proxy-Signature: HMAC-SHA256 签名（十六进制）
    """
    api_key = request.headers.get("X-Proxy-Api-Key")
    timestamp_str = request.headers.get("X-Proxy-Timestamp")
    signature = request.headers.get("X-Proxy-Signature")

    if not api_key or not timestamp_str or not signature:
        raise HTTPException(
            status_code=401,
            detail="缺少鉴权 Headers: X-Proxy-Api-Key, X-Proxy-Timestamp, X-Proxy-Signature",
        )

    # 1. 检查 timestamp 有效性
    try:
        ts = int(timestamp_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="X-Proxy-Timestamp 格式无效")

    now = int(time.time())
    if abs(now - ts) > _TIMESTAMP_TOLERANCE:
        raise HTTPException(status_code=401, detail="请求时间戳已过期（±5min）")

    # 2. 从 MongoDB 查找代理客户端
    db = mongodb.get_db()
    client_doc = await db.proxy_clients.find_one({"api_key": api_key})
    if not client_doc:
        raise HTTPException(status_code=401, detail="无效的 Proxy API Key")

    if client_doc.get("status") != "active":
        raise HTTPException(status_code=403, detail="代理客户端已被禁用")

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
        log.error("解密 proxy api_secret 失败 client_id=%s", client_doc.get("client_id"))
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
