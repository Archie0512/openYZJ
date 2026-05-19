"""Admin API Bearer Token 鉴权依赖。"""
import hmac

from fastapi import Header, HTTPException

from app.config import settings


async def require_admin(
    authorization: str = Header(..., alias="Authorization"),
) -> None:
    """验证 Authorization: Bearer <ADMIN_TOKEN>，使用常量时间比较防止侧信道。"""
    expected = f"Bearer {settings.admin_token}"
    if not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="invalid admin token")
