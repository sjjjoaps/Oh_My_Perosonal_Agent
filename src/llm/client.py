"""LLM 客户端（设计文档 §7.5）：litellm 封装，原型期单模型直通。"""
from __future__ import annotations

import time

import litellm

from src.config import Settings
from src.models import LLMResponse


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self._s = settings
        litellm.suppress_debug_info = True

    async def complete(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> LLMResponse:
        model = self._s.qwen_model
        # litellm OpenAI 兼容模式：model 前缀 openai/，base_url/api_key 注入
        t0 = time.perf_counter()
        resp = await litellm.acompletion(
            model=f"openai/{model}",
            messages=messages,
            temperature=temperature,
            base_url=self._s.base_url,
            api_key=self._s.api_key,
            timeout=self._s.get("orchestrator.llm_timeout_sec", 30),
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)

        choice = resp.choices[0]
        usage = resp.usage
        return LLMResponse(
            text=choice.message.content or "",
            model=model,
            prompt_tokens=getattr(usage, "prompt_tokens", 0),
            completion_tokens=getattr(usage, "completion_tokens", 0),
            cost=0.0,  # 原型期不计费，调优期接 litellm 成本估算
            latency_ms=latency_ms,
        )
