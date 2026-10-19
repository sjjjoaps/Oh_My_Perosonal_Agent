"""Mock 渠道：离线跑通用，把回复收集到内存列表。"""
from __future__ import annotations

from src.models import IncomingMessage


class MockChannel:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []   # (conversation_key, content)

    async def send_reply(self, msg: IncomingMessage, content: str) -> bool:
        self.sent.append((msg.conversation_key, content))
        print(f"\n[MockChannel → {msg.conversation_key}] {content}\n")
        return True

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
