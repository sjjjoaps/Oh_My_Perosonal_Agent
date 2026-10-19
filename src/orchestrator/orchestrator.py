"""编排主流程（设计文档 §7.4 / §8.1）。"""
from __future__ import annotations

import logging

from src.config import Settings
from src.llm.client import LLMClient
from src.models import IncomingMessage
from src.orchestrator.context_builder import ContextBuilder
from src.orchestrator.reply_formatter import ReplyFormatter
from src.orchestrator.trigger_router import TriggerRouter
from src.tracing.tracer import Tracer

log = logging.getLogger(__name__)


class Orchestrator:
    def __init__(
        self,
        settings: Settings,
        llm: LLMClient,
        tracer: Tracer,
        channel,  # Channel Protocol
    ) -> None:
        self._s = settings
        self._llm = llm
        self._tracer = tracer
        self._channel = channel
        self._trigger = TriggerRouter()
        self._ctx_builder = ContextBuilder()
        self._formatter = ReplyFormatter(
            mode=settings.get("reply.emoji", "auto"),
            max_length=settings.get("reply.max_length", 2000),
        )

    async def handle_batch(self, batch: list[IncomingMessage]) -> None:
        """接入层调用入口：一批合并后的消息。"""
        # 以批次首条建 trace；整批共享一个 trace_id
        head = batch[0]
        trace = self._tracer.start(head)

        try:
            decision = await self._trigger.decide(head)
            self._tracer.span(trace, "trigger", decision=decision, reason="at_me" if head.at_me else "silent")

            if decision == "silent":
                self._tracer.finish(trace)
                return

            ctx = await self._ctx_builder.build(head, batch)
            self._tracer.span(trace, "context", memory_hits=len(ctx.memory_hits), kb_hits=ctx.kb_hits)

            resp = await self._llm.complete(messages=ctx.messages)
            self._tracer.span(
                trace, "llm",
                model=resp.model, tokens_in=resp.prompt_tokens,
                tokens_out=resp.completion_tokens, latency_ms=resp.latency_ms,
            )

            content = self._formatter.format(resp.text, category=ctx.category)
            ok = await self._channel.send_reply(head, content)
            self._tracer.span(trace, "reply", channel=head.conversation_key.split(":", 1)[0], ok=ok)
        except Exception as e:
            log.exception("orchestrator handle_batch failed")
            self._tracer.span(trace, "error", error=repr(e))
        finally:
            self._tracer.finish(trace)
