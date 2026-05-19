"""异步耗时 AI 调用骨架（OpenAI 兼容协议）。

适用于 task #5 中"异步占位模式"——立即返回"思考中…"占位响应给云之家，
后台 BackgroundTask 调用本模块完成真实推理。

特性：
  - 通过环境变量 OPENAI_API_BASE / OPENAI_API_KEY / OPENAI_MODEL 配置
  - 未配置 OPENAI_API_KEY 时降级为 stub，便于无 key 测试
  - 超时较长（默认 30s），异步路径不受 3s 硬约束
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import settings

log = logging.getLogger(__name__)


class AICaller:
    """OpenAI 兼容协议的异步调用器。"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0,
    ):
        # 显式参数优先；否则回退到全局 settings
        self.base_url = base_url or settings.openai_api_base
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.timeout = timeout

    async def chat(self, prompt: str) -> str:
        """对指定 prompt 完成一次同轮对话，返回模型回复文本。

        失败统一抛 RuntimeError，由上层 ai_handler 捕获并写 failed log。
        未配置 api_key 时返回 stub，便于联调。
        """
        # ── stub 分支：未配置 key 时使用，方便集成测试 ──
        if not self.api_key:
            log.info("ai_caller running in stub mode (no OPENAI_API_KEY)")
            return f"[AI 模拟回复] 你说: {prompt}"

        # ── 真实调用 OpenAI 兼容接口 ──
        url = f"{(self.base_url or 'https://api.openai.com/v1').rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                # 兼容 OpenAI 响应结构
                choice = (data.get("choices") or [{}])[0]
                msg = choice.get("message") or {}
                text = msg.get("content")
                if not text:
                    raise RuntimeError(f"AI 响应缺少 content 字段: {data}")
                return text.strip()
        except httpx.HTTPError as e:
            log.warning("ai_caller http error: %s", e)
            raise RuntimeError(f"AI 调用 HTTP 失败: {e}") from e
        except Exception as e:  # noqa: BLE001
            log.warning("ai_caller unexpected error: %s", e)
            raise RuntimeError(f"AI 调用失败: {e}") from e
