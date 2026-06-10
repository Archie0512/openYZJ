"""MongoDB 连接管理模块（代理网关独立实例）。"""
from __future__ import annotations

import logging
from typing import Optional

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.config import settings

log = logging.getLogger(__name__)

# 全局客户端实例
_client: Optional[AsyncMongoClient] = None


async def connect() -> None:
    """建立 MongoDB 异步连接并校验可达性。"""
    global _client
    _client = AsyncMongoClient(settings.mongo_uri)
    await _client.admin.command("ping")
    log.info("MongoDB 连接成功: %s", settings.mongo_host)


async def close() -> None:
    """关闭 MongoDB 连接。"""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        log.info("MongoDB 连接已关闭")


def get_client() -> AsyncMongoClient:
    """获取全局 MongoDB 客户端实例。"""
    if _client is None:
        raise RuntimeError("MongoDB 客户端未初始化，请先调用 connect()")
    return _client


def get_db() -> AsyncDatabase:
    """获取项目默认数据库实例。"""
    return get_client()[settings.mongo_db]
