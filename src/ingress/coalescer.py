"""连发合并（设计文档 §9.3 / FR-26）：同会话 2s 静默 / 5 条 / 10s 窗口任一触发。"""
from __future__ import annotations

import time

from src.models import IncomingMessage


class Coalescer:
    def __init__(self, idle_sec: float = 2.0, max_batch: int = 5, window_sec: float = 10.0) -> None:
        self._idle = idle_sec
        self._max = max_batch
        self._window = window_sec
        self._pending: dict[str, list[IncomingMessage]] = {}
        self._first_ts: dict[str, float] = {}

    def push(self, msg: IncomingMessage) -> list[IncomingMessage] | None:
        key = msg.conversation_key
        now = time.time()

        if key not in self._pending:
            self._pending[key] = []
            self._first_ts[key] = now

        self._pending[key].append(msg)
        batch = self._pending[key]
        elapsed = now - self._first_ts[key]

        should_flush = (
            len(batch) >= self._max
            or elapsed >= self._window
        )
        if should_flush:
            return self._flush(key)
        return None

    def flush_idle(self) -> dict[str, list[IncomingMessage]]:
        """由 Worker 周期调用：把静默超过 idle_sec 的批次吐出。"""
        now = time.time()
        ready: dict[str, list[IncomingMessage]] = {}
        for key, batch in list(self._pending.items()):
            if not batch:
                continue
            last = max(m.ts.timestamp() for m in batch)
            if now - last >= self._idle:
                ready[key] = self._flush(key)
        return ready

    def _flush(self, key: str) -> list[IncomingMessage]:
        batch = self._pending.pop(key, [])
        self._first_ts.pop(key, None)
        return batch
