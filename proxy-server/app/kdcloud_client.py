"""金蝶发票云 HTTP 客户端。

使用全局单例 httpx.AsyncClient（连接池复用），封装所有金蝶发票云 API 调用。
每个方法接收 access_token 参数，设置 access_token header。
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
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
        "usertype": settings.kdcloud_usertype,
    }
    log.info("[kdcloud] 获取 access_token")
    resp = await client.post("/api/login.do", json=payload)
    resp.raise_for_status()
    return resp.json()


# ── Base64 / AES 编解码 ─────────────────────────────

# 缓存派生后的 AES 密钥（避免每次请求都重新计算）
_cached_aes_key: Optional[bytes] = None
_cached_aes_key_raw: Optional[str] = None


def _derive_aes_key(raw_key: str) -> bytes:
    """用 SHA1PRNG 风格从原始密钥字符串派生 128 位 AES 密钥。"""
    global _cached_aes_key, _cached_aes_key_raw
    if _cached_aes_key_raw == raw_key and _cached_aes_key:
        return _cached_aes_key
    # SHA1PRNG 等价：SHA-1(seed) 取前 16 字节
    key = hashlib.sha1(raw_key.encode("utf-8")).digest()[:16]
    _cached_aes_key = key
    _cached_aes_key_raw = raw_key
    return key


def _aes_encrypt(plaintext: str) -> bytes:
    """AES-128-GCM 加密，返回 IV(12) || ciphertext(n) || authTag(16)。"""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = _derive_aes_key(settings.kdcloud_aes_key)
    iv = secrets.token_bytes(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
    return iv + ciphertext  # ciphertext 已经包含 authTag(16) 在末尾


def _aes_decrypt(data: bytes) -> str:
    """AES-128-GCM 解密，data 格式为 IV(12) || ciphertext(n) || authTag(16)。"""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = _derive_aes_key(settings.kdcloud_aes_key)
    iv = data[:12]
    ciphertext = data[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(iv, ciphertext, None)
    return plaintext.decode("utf-8")


def _encode_data(payload: dict | list) -> str:
    """将业务数据编码：JSON 序列化 → [AES 加密] → Base64。"""
    json_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if settings.kdcloud_aes_key:
        encrypted = _aes_encrypt(json_str)
        return base64.b64encode(encrypted).decode("ascii")
    return base64.b64encode(json_str.encode("utf-8")).decode("ascii")


def _decode_data(encoded: str) -> dict:
    """将响应 data 字段解码：Base64 解码 → [AES 解密] → JSON 反序列化。"""
    raw = base64.b64decode(encoded)
    if settings.kdcloud_aes_key:
        json_str = _aes_decrypt(raw)
    else:
        json_str = raw.decode("utf-8")
    return json.loads(json_str)


def _build_gateway_request(interface_code: str, data_content: dict | list, request_id: str) -> dict:
    """构造统一网关请求体。requestId 由调用方 (System A) 提供，保证唯一性。"""
    return {
        "requestId": request_id,
        "businessSystemCode": settings.kdcloud_business_system_code,
        "interfaceCode": interface_code,
        "data": _encode_data(data_content),
    }


def _build_gateway_headers(access_token: str) -> dict:
    """构造统一网关请求头。"""
    return {
        "access_token": access_token,
        "Content-Type": "application/json",
    }


async def _call_gateway(
    interface_code: str,
    data_content: dict | list,
    access_token: str,
    label: str,
    request_id: str,
) -> dict:
    """统一网关调用：构造请求 → POST /kapi/app/sim/openApi → 解码响应 data。"""
    client = get_kdcloud_client()
    req = _build_gateway_request(interface_code, data_content, request_id)
    headers = _build_gateway_headers(access_token)
    log.info("[kdcloud] %s interfaceCode=%s requestId=%s", label, interface_code, request_id)
    body_preview = json.dumps(req, ensure_ascii=False)
    log.info("[kdcloud] >>> 请求体: %s", body_preview) if len(body_preview) < 5000 else log.info("[kdcloud] >>> 请求体(截断): %s...", body_preview[:5000])
    resp = await client.post("/kapi/app/sim/openApi", json=req, headers=headers)
    resp.raise_for_status()
    result = resp.json()
    # 解码响应中的 data 字段
    if isinstance(result.get("data"), str):
        try:
            result["data"] = _decode_data(result["data"])
        except Exception as e:
            log.warning("[kdcloud] 响应 data 解码失败, 保留原始值: %s", e)
    return result


# ── 开票 ─────────────────────────────────────────────

async def create_invoice(data_content: dict, access_token: str, request_id: str) -> dict:
    """1.1.01 开票申请单生成及开票。

    POST /kapi/app/sim/openApi  interfaceCode=BILL.PUSH
    """
    return await _call_gateway("BILL.PUSH", data_content, access_token, "开票申请单生成", request_id)


async def revoke_invoice(data_content: dict, access_token: str, request_id: str) -> dict:
    """1.1.02 开票申请单撤回。

    POST /kapi/app/sim/openApi  interfaceCode=BILL.WITHDRAW
    """
    return await _call_gateway("BILL.WITHDRAW", data_content, access_token, "开票申请单撤回", request_id)


async def query_invoice_apply(data_content: dict, access_token: str, request_id: str) -> dict:
    """1.1.03 开票申请单发票查询。

    POST /kapi/app/sim/openApi  interfaceCode=BILL.INVOICE.QUERY
    """
    return await _call_gateway("BILL.INVOICE.QUERY", data_content, access_token, "开票申请单发票查询", request_id)


# ── 机动车 ───────────────────────────────────────────

async def query_vehicle_info(data_content: dict, access_token: str, request_id: str) -> dict:
    """2.2.15 机动车信息查询（数电专用）。

    POST /kapi/app/sim/openApi  interfaceCode=QUIERY.VEHICLE.INFO
    """
    return await _call_gateway("QUIERY.VEHICLE.INFO", data_content, access_token, "机动车信息查询", request_id)


async def issue_vehicle_invoice(data_content: dict, access_token: str, request_id: str) -> dict:
    """2.2.11 机动车发票开具。

    POST /kapi/app/sim/openApi  interfaceCode=INVOICE.OPEN.VEHICLE
    """
    return await _call_gateway("INVOICE.OPEN.VEHICLE", data_content, access_token, "机动车发票开具", request_id)


async def red_flush_vehicle(data_content: dict, access_token: str, request_id: str) -> dict:
    """2.2.13 机动车发票红冲。

    POST /kapi/app/sim/openApi  interfaceCode=INVOICE.RED.VEHICLE
    """
    return await _call_gateway("INVOICE.RED.VEHICLE", data_content, access_token, "机动车发票红冲", request_id)


# ── 数电票查询 ───────────────────────────────────────

async def batch_query_digital(data_content: dict, access_token: str, request_id: str) -> dict:
    """4.1.03 数电票发票批量查询。

    POST /kapi/app/sim/openApi  interfaceCode=ALLE.BATCH.QUERY
    """
    return await _call_gateway("ALLE.BATCH.QUERY", data_content, access_token, "数电票批量查询", request_id)


async def single_query_digital(data_content: dict, access_token: str, request_id: str) -> dict:
    """4.1.04 数电票发票单张查询。

    POST /kapi/app/sim/openApi  interfaceCode=ALLE.INVOICE.QUERY
    """
    return await _call_gateway("ALLE.INVOICE.QUERY", data_content, access_token, "数电票单张查询", request_id)
