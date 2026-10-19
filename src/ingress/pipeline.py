"""接入流水线（设计文档 §7.3）：dedup → coalesce → session queue。"""
from __future__ import annotations

import asyncio
import logging

from src.config import Settings
from src.ingress.coalescer import Coalescer
from src.ingress.deduper import Deduper
from src.ingress.session import SessionRouter
from src.models import IncomingMessage

log = logging.getLogger(__name__)


class IngressPipeline:
    def __init__(self, settings: Settings, handler) -> None:  # noqa: ANN001
        self._deduper = Deduper(ttl_sec=settings.get("ingress.dedup_ttl_sec", 3600))
        self._coalescer = Coalescer(
            idle_sec=settings.get("ingress.coalesce_idle_sec", 2),
            max_batch=settings.get("ingress.coalesce_max_batch", 5),
            window_sec=settings.get("ingress.coalesce_window_sec", 10),
        )
        self._router = SessionRouter(
            cap=settings.get("ingress.session_queue_cap", 20),
            worker_pool=settings.get("ingress.worker_pool", 4),
            handler=handler,
        )
        self._idle_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._idle_task = asyncio.create_task(self._idle_flush_loop())

    async def stop(self) -> None:
        if self._idle_task:
            self._idle_task.cancel()

    async def accept(self, msg: IncomingMessage) -> None:
        # 1) 去重
        if self._deduper.seen(msg.msg_id, msg.msg_seq):
            log.info("dedup drop %s/%s", msg.msg_id, msg.msg_seq)
            return
        # 2) 合并（先尝试立即吐批；未达阈值的由 idle 循环兜底）
        batch = self._coalescer.push(msg)
        if batch is None:
            return
        # 3) 会话队列
        if not self._router.submit(batch):
            log.warning("backpressure: queue full for %s", msg.conversation_key)

    async def _idle_flush_loop(self) -> None:
        while True:
            await asyncio.sleep(1.0)
            for batch in self._coalescer.flush_idle().values():
                self._router.submit(batch)
