"""crypto 模块单元测试：Fernet 加密往返 + 密钥派生。

降级策略：若 cryptography 未安装，仅运行 _derive_fernet_key 的纯哈希派生检查
（不依赖 Fernet）。
"""
import base64
import hashlib
import os
import unittest

# 设置最小环境变量，避免 pydantic-settings 报错
os.environ.setdefault("MONGO_USER", "test")
os.environ.setdefault("MONGO_PASSWORD", "test")
os.environ.setdefault("APP_SECRET_KEY", "unit-test-key-for-crypto")
os.environ.setdefault("ADMIN_TOKEN", "test-admin-token")

# 检查是否安装了 cryptography
try:
    import cryptography  # noqa: F401
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


def _derive_fernet_key_local(secret: str) -> bytes:
    """本地重实现 _derive_fernet_key，避免在缺 cryptography 时无法 import 整个模块。"""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


class TestDeriveFernetKey(unittest.TestCase):
    """测试 _derive_fernet_key 输出合法 Fernet key 形态（不依赖 cryptography）。"""

    def test_key_length_is_44_bytes(self):
        """Fernet key 是 base64url 编码的 32 字节 = 44 字符。"""
        # 本地派生与模块行为一致的验证（不引入 cryptography）
        key = _derive_fernet_key_local("any-secret")
        self.assertEqual(len(key), 44)

    def test_key_is_valid_base64(self):
        """生成的 key 可以被 base64 解码回 32 字节。"""
        key = _derive_fernet_key_local("another-secret")
        raw = base64.urlsafe_b64decode(key)
        self.assertEqual(len(raw), 32)

    def test_different_secrets_produce_different_keys(self):
        k1 = _derive_fernet_key_local("secret-a")
        k2 = _derive_fernet_key_local("secret-b")
        self.assertNotEqual(k1, k2)

    @unittest.skipUnless(HAS_CRYPTOGRAPHY, "cryptography not installed")
    def test_module_derive_matches_local(self):
        """app.core.crypto._derive_fernet_key 与本地实现等价。"""
        from app.core.crypto import _derive_fernet_key
        for secret in ("a", "abc", "云之家"):
            self.assertEqual(_derive_fernet_key(secret), _derive_fernet_key_local(secret))


@unittest.skipUnless(HAS_CRYPTOGRAPHY, "cryptography not installed")
class TestEncryptDecrypt(unittest.TestCase):
    """测试加密→解密往返（依赖 cryptography）。"""

    def test_roundtrip(self):
        """encrypt_secret → decrypt_secret 应还原原文。"""
        from app.core.crypto import encrypt_secret, decrypt_secret
        plaintext = "my-super-secret-app-key-123"
        ciphertext = encrypt_secret(plaintext)
        self.assertNotEqual(ciphertext, plaintext)
        self.assertEqual(decrypt_secret(ciphertext), plaintext)

    def test_different_plaintext_different_ciphertext(self):
        from app.core.crypto import encrypt_secret
        c1 = encrypt_secret("aaa")
        c2 = encrypt_secret("bbb")
        self.assertNotEqual(c1, c2)

    def test_decrypt_with_wrong_key_fails(self):
        """用不同主密钥派生出的 Fernet 解密原密文应失败。"""
        from app.core.crypto import encrypt_secret
        ciphertext = encrypt_secret("test-data")

        from cryptography.fernet import Fernet, InvalidToken
        wrong_key = base64.urlsafe_b64encode(
            hashlib.sha256(b"wrong-key").digest()
        )
        f = Fernet(wrong_key)
        with self.assertRaises(InvalidToken):
            f.decrypt(ciphertext.encode("ascii"))


if __name__ == "__main__":
    unittest.main()
