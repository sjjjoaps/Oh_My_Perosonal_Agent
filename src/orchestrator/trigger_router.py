"""触发路由（设计文档 §7.4 / FR-06）：@ 必回，非 @ 关注模式不回。"""
from __future__ import annotations

from src.models import IncomingMessage


class TriggerRouter:
    async def decide(self, msg: IncomingMessage) -> str:
        if msg.at_me:
            return "reply"
        if msg.conversation_key.startswith("c2c:"):
            return "reply"
        return "silent"
