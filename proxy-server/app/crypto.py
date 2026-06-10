"""Fernet 对称加解密工具：用于 proxy client apiSecret 加密落库。

主密钥来源：settings.app_secret_key（.env 中 APP_SECRET_KEY）。
Fernet 要求 32 字节 base64 url-safe 密钥，此处通过 SHA-256 派生。
"""
import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import settings


def _derive_fernet_key(secret: str) -> bytes:
    """从任意字符串派生 32 字节 base64 url-safe Fernet key。"""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_fernet() -> Fernet:
    """获取基于主密钥的 Fernet 实例。"""
    return Fernet(_derive_fernet_key(settings.app_secret_key))


def encrypt_secret(plaintext: str) -> str:
    """加密明文 appSecret，返回密文字符串。"""
    return get_fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_secret(ciphertext: str) -> str:
    """解密密文，返回明文 appSecret。"""
    return get_fernet().decrypt(ciphertext.encode("ascii")).decode("utf-8")
