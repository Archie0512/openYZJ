"""命令路由单元测试：验证 route() 按前缀正确匹配 handler。

独立可运行：python tests/test_router.py
pytest 兼容：pytest tests/test_router.py
"""
from __future__ import annotations

import sys
import os

# 让测试能 import app 模块（与 test_security.py 保持一致）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── 在 command_router（及 handler）import app.config.settings 之前 ──
# 设置必要的环境变量以避免 pydantic-settings ValidationError
os.environ.setdefault("MONGO_USER", "test")
os.environ.setdefault("MONGO_PASSWORD", "test")
os.environ.setdefault("MONGO_HOST", "localhost")
os.environ.setdefault("APP_SECRET_KEY", "test-key-32-bytes-long-placeholder")
os.environ.setdefault("ADMIN_TOKEN", "test-token")

from app.services.command_router import route
from app.services.handlers.ai_handler import AIHandler
from app.services.handlers.api_handler import ApiHandler
from app.services.handlers.echo_handler import EchoHandler
from app.services.handlers.mys4s_handler import MYS4SHandler


# ── /ai 前缀 → AIHandler ────────────────────────
def test_route_ai_slash():
    h = route("/ai 你好")
    assert isinstance(h, AIHandler), f"expected AIHandler, got {type(h).__name__}"
    assert h.name == "ai"

def test_route_ai_hash():
    h = route("#AI 你好世界")
    assert isinstance(h, AIHandler)

def test_route_ai_colon():
    h = route("/ai:你好")
    assert isinstance(h, AIHandler)

def test_route_ai_only():
    """仅输入 /ai 无后续文字也应命中。"""
    h = route("/ai")
    assert isinstance(h, AIHandler)


# ── /api 前缀 → ApiHandler ──────────────────────
def test_route_api_slash():
    h = route("/api foo")
    assert isinstance(h, ApiHandler), f"expected ApiHandler, got {type(h).__name__}"
    assert h.name == "api_call"

def test_route_api_hash():
    h = route("#api bar")
    assert isinstance(h, ApiHandler)

def test_route_api_case_insensitive():
    h = route("/API something")
    assert isinstance(h, ApiHandler)


# ── /echo 前缀 → EchoHandler ────────────────────
def test_route_echo():
    h = route("/echo 测试内容")
    assert isinstance(h, EchoHandler)
    assert h.name == "echo"


# ── 默认 → MYS4SHandler ─────────────────────────
def test_route_default_text():
    h = route("hello")
    assert isinstance(h, MYS4SHandler)

def test_route_empty():
    h = route("")
    assert isinstance(h, MYS4SHandler)

def test_route_none():
    h = route(None)
    assert isinstance(h, MYS4SHandler)


# ── 边界：/apixxx 不应误命中 /api ────────────────
def test_route_no_false_positive():
    """确保 /apixxx 不命中 /api（需要分隔符才匹配）。"""
    h = route("/apixyz")
    assert isinstance(h, MYS4SHandler), "/apixyz should NOT match /api"


if __name__ == "__main__":
    tests = [
        test_route_ai_slash,
        test_route_ai_hash,
        test_route_ai_colon,
        test_route_ai_only,
        test_route_api_slash,
        test_route_api_hash,
        test_route_api_case_insensitive,
        test_route_echo,
        test_route_default_text,
        test_route_empty,
        test_route_none,
        test_route_no_false_positive,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
        except AssertionError as e:
            print(f"  FAIL: {t.__name__} - {e}")
            failed += 1
    print(f"\n{'All tests passed!' if not failed else f'{failed} test(s) failed.'}")
    sys.exit(failed)
