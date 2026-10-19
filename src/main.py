"""启动入口（设计文档 §3）：真实连 QQ 沙箱群。"""
from __future__ import annotations

import asyncio
import logging

from src.channel.qq_channel import QQChannel
from src.config import Settings
from src.ingress.pipeline import IngressPipeline
from src.llm.client import LLMClient
from src.orchestrator.orchestrator import Orchestrator
from src.tracing.tracer import Tracer


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = Settings()
    tracer = Tracer(settings)
    llm = LLMClient(settings)

    # 构造顺序：channel → orch → ingress → 绑定 → 启动
    channel = QQChannel(settings)
    orch = Orchestrator(settings, llm, tracer, channel)
    ingress = IngressPipeline(settings, handler=orch.handle_batch)
    channel.bind_ingress(ingress)

    await ingress.start()
    await channel.start()

    logging.info("digital-colleague 已启动，在 QQ 沙箱群里 @ 机器人试试（Ctrl+C 退出）")
    try:
        await asyncio.Event().wait()
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        await ingress.stop()
        await channel.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
