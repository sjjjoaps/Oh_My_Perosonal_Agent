"""会话队列与 WorkerPool（设计文档 §9.1 / FR-24/25/27）。"""
from __future__ import annotations

import asyncio
from collections import deque
from typing import Awaitable, Callable

from src.models import IncomingMessage

Handler = Callable[[list[IncomingMessage]], Awaitable[None]]


class SessionQueue:
    """单会话串行队列；容量上限，满则拒绝（背压）。"""

    def __init__(self, key: str, cap: int) -> None:
        self.key = key
        self._cap = cap
        self._buf: deque[list[IncomingMessage]] = deque()
        self._event = asyncio.Event()
        self._dropped = 0

    def put(self, batch: list[IncomingMessage]) -> bool:
        if len(self._buf) >= self._cap:
            self._dropped += 1
            return False
        self._buf.append(batch)
        self._event.set()
        return True

    async def get(self) -> list[IncomingMessage]:
        while not self._buf:
            await self._event.wait()
        self._event.clear()
        return self._buf.popleft()

    @property
    def dropped(self) -> int:
        return self._dropped


class SessionRouter:
    """按会话 key 分发到独立 SessionQueue；每队列一个消费者协程。"""

    def __init__(self, cap: int, worker_pool: int, handler: Handler) -> None:
        self._cap = cap
        self._handler = handler
        self._queues: dict[str, SessionQueue] = {}
        self._slots: asyncio.Semaphore = asyncio.Semaphore(worker_pool)
        self._tasks: list[asyncio.Task] = []

    def submit(self, batch: list[IncomingMessage]) -> bool:
        key = batch[0].conversation_key
        if key not in self._queues:
            q = SessionQueue(key, self._cap)
            self._queues[key] = q
            self._tasks.append(asyncio.create_task(self._consume(q)))
        return self._queues[key].put(batch)

    async def _consume(self, q: SessionQueue) -> None:
        while True:
            batch = await q.get()
            async with self._slots:
                try:
                    await self._handler(batch)
                except Exception:  # noqa: BLE001 —— 单会话失败不拖垮全局
                    import logging
                    logging.exception("session handler failed: %s", q.key)
