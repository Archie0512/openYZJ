"""FastAPI 依赖注入辅助函数。"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException

from app.config import settings
from app.core.crypto import decrypt_secret, encrypt_secret
from app.db import mongodb

log = logging.getLogger(__name__)

# ── 测试请求常量 ──────────────────────────────────
TEST_ROBOT_ID = "test-robotId"
TEST_SECRET = "test-secret"
# 非生产环境集合：仅在这些环境下，TEST_ROBOT_ID 走固定密钥兜底
_NON_PROD_ENVS = {"dev", "test"}


def get_db():
    """获取 MongoDB 数据库实例（同步调用，返回 AsyncDatabase）。"""
    return mongodb.get_db()


async def get_robot_secret(robot_id: str, db) -> str:
    """根据 robotId 获取对应的验签密钥。

    逻辑：
      1. 测试 robotId='test-robotId' 且 env in {dev,test} → 固定返回 'test-secret'
         （生产环境下不走此兜底，避免公开测试密钥永久暴露；
          运维如需临时通过测试请求，可在 robots 集合插入 robotId=test-robotId 的文档）
      2. 从 robots 集合查找，用 Fernet 解密 appSecret_encrypted
      3. 兼容旧明文字段 appSecret：返回明文同时在后台自动加密回写并 unset 明文
      4. 找不到 → 401
    """
    # 测试兜底仅在非生产环境生效
    if robot_id == TEST_ROBOT_ID and settings.env in _NON_PROD_ENVS:
        return TEST_SECRET

    doc = await db.robots.find_one({"robotId": robot_id})
    if not doc:
        print(f"[ROBOT-DISCOVERY] 未注册的 robotId={robot_id}，请通过 admin API 注册")
        raise HTTPException(status_code=401, detail=f"Unknown robotId: {robot_id}")

    # 优先解密密文字段
    enc = doc.get("appSecret_encrypted")
    if enc:
        try:
            return decrypt_secret(enc)
        except Exception as e:
            log.error("decrypt appSecret failed for %s: %s", robot_id, e)
            raise HTTPException(status_code=500, detail="appSecret decrypt failed")

    # 兼容旧明文字段：返回明文，同时尝试加密迁移并清理明文字段
    plain = doc.get("appSecret")
    if plain:
        try:
            new_enc = encrypt_secret(plain)
            await db.robots.update_one(
                {"_id": doc["_id"]},
                {
                    "$set": {
                        "appSecret_encrypted": new_enc,
                        "updated_at": datetime.now(timezone.utc),
                    },
                    "$unset": {"appSecret": ""},
                },
            )
            log.info("auto-migrated plaintext appSecret for robotId=%s", robot_id)
        except Exception as e:  # 迁移失败不阻塞当前请求
            log.warning("auto-migrate plaintext appSecret failed: %s", e)
        return plain

    raise HTTPException(status_code=500, detail="robot has no secret")
