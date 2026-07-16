"""pytest 全局配置：环境变量兜底 + sys.path 注入。

在导入 app 模块之前设置必要的环境变量，避免 pydantic-settings ValidationError。
参考 server/tests/ 的模式。
"""
from __future__ import annotations

import os
import sys

# 让测试能 import 'app' 顶层包（../app）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── pydantic-settings 必需的最小环境变量 ────────────────
os.environ.setdefault("MONGO_USER", "test")
os.environ.setdefault("MONGO_PASSWORD", "test")
os.environ.setdefault("MONGO_HOST", "localhost")
os.environ.setdefault("APP_SECRET_KEY", "unit-test-key-32-bytes-long-placeholder")
os.environ.setdefault("ADMIN_TOKEN", "unit-test-admin-token")
