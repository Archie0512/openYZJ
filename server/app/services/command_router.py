"""命令路由：按 content 前缀匹配命中对应 handler。

匹配规则（大小写不敏感，前缀以空白 / 冒号 / 字符串结尾分隔）：
  - /ai, #ai      → AIHandler   异步占位
  - /api, #api    → ApiHandler  同步快速
  - /echo         → EchoHandler 同步
  - 其余兜底 → EchoHandler
"""
from __future__ import annotations

from typing import List, Tuple

from app.services.handlers.ai_handler import AIHandler
from app.services.handlers.api_handler import ApiHandler
from app.services.handlers.base import BaseHandler
from app.services.handlers.echo_handler import EchoHandler

# Handler 单例（无状态，可复用）
_AI = AIHandler()
_API = ApiHandler()
_ECHO = EchoHandler()

# 前缀 → handler 映射；按数组顺序匹配，先匹配长前缀
_HANDLERS: List[Tuple[Tuple[str, ...], BaseHandler]] = [
    (("/ai", "#ai"), _AI),
    (("/api", "#api"), _API),
    (("/echo",), _ECHO),
]
_DEFAULT: BaseHandler = _ECHO

# 允许出现在前缀之后、与正文之间的分隔符
_SEPARATORS = (" ", "\t", ":", "：")


def route(content: str) -> BaseHandler:
    """返回与 content 匹配的 handler；无任何匹配时回退默认。

    判定规则：
      1. 整体小写 + strip 后做 startswith
      2. 命中前缀后，要么字符串恰好等于前缀，要么紧跟分隔符（避免 /apixxx 误命中 /api）
    """
    text = (content or "").strip().lower()
    if not text:
        return _DEFAULT

    for prefixes, handler in _HANDLERS:
        for p in prefixes:
            if text == p or (text.startswith(p) and text[len(p):len(p) + 1] in _SEPARATORS):
                return handler
    return _DEFAULT
