"""渠道抽象（设计文档 §7.2）：输出端可插拔（group_at / c2c）。"""
from __future__ import annotations

from typing import Protocol

from src.models import IncomingMessage


class Channel(Protocol):
    async def send_reply(self, msg: IncomingMessage, content: str) -> bool: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
