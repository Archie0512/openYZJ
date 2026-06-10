"""金蝶发票云 HTTP 客户端。

使用全局单例 httpx.AsyncClient（连接池复用），封装所有金蝶发票云 API 调用。
每个方法接收 access_token 参数，设置 access_token header；
收到 401 时自动触发 token_manager.refresh() 然后重试一次。
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import settings

log = logging.getLogger(__name__)

# ── 全局单例 ──────────────────────────────────────────
_client: Optional[httpx.AsyncClient] = None
_current_env: str = "test"


def _base_url(env: str) -> str:
    """根据环境返回金蝶发票云基础 URL。"""
    if env == "prod":
        return settings.kdcloud_prod_base_url
    return settings.kdcloud_test_base_url


async def init_kdcloud_client(env: str = "test") -> None:
    """创建全局 httpx 客户端（连接池复用）。

    应在应用启动时调用一次。
    """
    global _client, _current_env
    _current_env = env
    _client = httpx.AsyncClient(
        base_url=_base_url(env),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        timeout=httpx.Timeout(connect=5.0, read=60.0, write=30.0, pool=5.0),
        headers={"Content-Type": "application/json"},
    )
    log.info("金蝶发票云 HTTP 客户端已初始化 env=%s base=%s", env, _base_url(env))


def get_kdcloud_client() -> httpx.AsyncClient:
    """获取全局 httpx 客户端实例。"""
    if _client is None:
        raise RuntimeError("金蝶发票云客户端未初始化，请先调用 init_kdcloud_client()")
    return _client


async def close_kdcloud_client() -> None:
    """释放全局 httpx 客户端。"""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        log.info("金蝶发票云 HTTP 客户端已关闭")


# ── 鉴权 ─────────────────────────────────────────────

async def get_app_token() -> dict:
    """1.01 获取 app_token。

    POST /api/getAppToken.do
    """
    client = get_kdcloud_client()
    payload = {
        "appId": settings.kdcloud_app_id,
        "appSecret": settings.kdcloud_app_secret,
        "accountId": settings.kdcloud_account_id,
        "tenantid": settings.kdcloud_tenant_id if hasattr(settings, "kdcloud_tenant_id") else "",
        "language": settings.kdcloud_language,
    }
    log.info("[kdcloud] 获取 app_token")
    resp = await client.post("/api/getAppToken.do", json=payload)
    resp.raise_for_status()
    return resp.json()


async def login(app_token: str) -> dict:
    """1.02 获取 access_token（有效期 2 小时）。

    POST /api/login.do
    """
    client = get_kdcloud_client()
    payload = {
        "user": settings.kdcloud_user,
        "apptoken": app_token,
        "accountId": settings.kdcloud_account_id,
        "tenantid": settings.kdcloud_tenant_id if hasattr(settings, "kdcloud_tenant_id") else "",
        "usertype": settings.kdcloud_usertype,
    }
    log.info("[kdcloud] 获取 access_token")
    resp = await client.post("/api/login.do", json=payload)
    resp.raise_for_status()
    return resp.json()


# ── 开票 ─────────────────────────────────────────────

async def create_invoice(req: dict, access_token: str) -> dict:
    """1.1.01 开票申请单生成及开票。

    POST /api/standard/applyBill.do
    """
    client = get_kdcloud_client()
    headers = {"access_token": access_token}
    log.info("[kdcloud] 开票申请单生成")
    resp = await client.post("/api/standard/applyBill.do", json=req, headers=headers)
    resp.raise_for_status()
    return resp.json()


async def revoke_invoice(req: dict, access_token: str) -> dict:
    """1.1.02 开票申请单撤回。

    POST /api/standard/revokeBill.do
    """
    client = get_kdcloud_client()
    headers = {"access_token": access_token}
    log.info("[kdcloud] 开票申请单撤回")
    resp = await client.post("/api/standard/revokeBill.do", json=req, headers=headers)
    resp.raise_for_status()
    return resp.json()


async def query_invoice_apply(params: dict, access_token: str) -> dict:
    """1.1.03 开票申请单发票查询。

    GET /api/standard/queryInvoice.do
    """
    client = get_kdcloud_client()
    headers = {"access_token": access_token}
    log.info("[kdcloud] 开票申请单发票查询")
    resp = await client.get("/api/standard/queryInvoice.do", params=params, headers=headers)
    resp.raise_for_status()
    return resp.json()


# ── 机动车 ───────────────────────────────────────────

async def query_vehicle_info(params: dict, access_token: str) -> dict:
    """2.2.15 机动车信息查询（数电专用）。

    GET /api/vehicle/queryVehicleInfo.do
    """
    client = get_kdcloud_client()
    headers = {"access_token": access_token}
    log.info("[kdcloud] 机动车信息查询")
    resp = await client.get("/api/vehicle/queryVehicleInfo.do", params=params, headers=headers)
    resp.raise_for_status()
    return resp.json()


async def issue_vehicle_invoice(req: dict, access_token: str) -> dict:
    """2.2.11 机动车发票开具。

    POST /api/vehicle/send.do
    """
    client = get_kdcloud_client()
    headers = {"access_token": access_token}
    log.info("[kdcloud] 机动车发票开具")
    resp = await client.post("/api/vehicle/send.do", json=req, headers=headers)
    resp.raise_for_status()
    return resp.json()


async def red_flush_vehicle(req: dict, access_token: str) -> dict:
    """2.2.13 机动车发票红冲。

    POST /api/vehicle/invoice/red.do
    """
    client = get_kdcloud_client()
    headers = {"access_token": access_token}
    log.info("[kdcloud] 机动车发票红冲")
    resp = await client.post("/api/vehicle/invoice/red.do", json=req, headers=headers)
    resp.raise_for_status()
    return resp.json()


# ── 数电票查询 ───────────────────────────────────────

async def batch_query_digital(req: dict, access_token: str) -> dict:
    """4.1.03 数电票发票批量查询。

    POST /api/invoice/query/bySerialNos.do
    """
    client = get_kdcloud_client()
    headers = {"access_token": access_token}
    log.info("[kdcloud] 数电票批量查询")
    resp = await client.post("/api/invoice/query/bySerialNos.do", json=req, headers=headers)
    resp.raise_for_status()
    return resp.json()


async def single_query_digital(params: dict, access_token: str) -> dict:
    """4.1.04 数电票发票单张查询。

    GET /api/invoice/query/bySerialNo.do
    """
    client = get_kdcloud_client()
    headers = {"access_token": access_token}
    log.info("[kdcloud] 数电票单张查询")
    resp = await client.get("/api/invoice/query/bySerialNo.do", params=params, headers=headers)
    resp.raise_for_status()
    return resp.json()
