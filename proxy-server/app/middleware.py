"""代理网关中间件。

- RateLimitMiddleware: 基于 MongoDB 的简单速率限制
- RequestLoggingMiddleware: 结构化请求日志
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app import mongodb

log = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """代理路径速率限制中间件。

    仅拦截 /api/proxy/v1/* 路径，每个 client_id 独立计数。
    使用 MongoDB proxy_rate_counters 集合，基于分钟窗口。
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        if not path.startswith("/api/proxy/v1/"):
            return await call_next(request)

        # 尝试获取 client_id（从已认证的请求中）
        caller_id = getattr(request.state, "caller_id", None)
        if caller_id is None:
            # 尚未鉴权，放行让 auth 处理
            return await call_next(request)

        db = mongodb.get_db()
        window_start = int(time.time() / 60) * 60  # 分钟级窗口
        counter_id = f"{caller_id}:{window_start}"

        # 查询或获取 client 的 rate_limit 配置
        client_doc = await db.proxy_clients.find_one(
            {"client_id": caller_id}, {"rate_limit": 1}
        )
        rate_limit = (client_doc.get("rate_limit") if client_doc else None) or settings.proxy_rate_limit_default

        # 原子增加计数
        result = await db.proxy_rate_counters.find_one_and_update(
            {"_id": counter_id},
            {
                "$inc": {"count": 1},
                "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
            },
            upsert=True,
            return_document=True,
        )
        current_count = result["count"] if result else 1

        if current_count > rate_limit:
            retry_after = 60 - (int(time.time()) % 60)
            return Response(
                content='{"code":429,"message":"请求过于频繁，请稍后重试"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """代理请求日志中间件。

    记录每个 /api/proxy/v1/* 请求的调用方、端点、延迟、状态码。
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        if not path.startswith("/api/proxy/v1/"):
            return await call_next(request)

        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        request.state.start_time = time.monotonic()

        response = await call_next(request)

        elapsed_ms = int((time.monotonic() - request.state.start_time) * 1000)
        caller_id = getattr(request.state, "caller_id", "unknown")

        log.info(
            "[proxy] request_id=%s caller=%s method=%s path=%s status=%d latency=%dms",
            request_id, caller_id, request.method, path, response.status_code, elapsed_ms,
        )

        return response
