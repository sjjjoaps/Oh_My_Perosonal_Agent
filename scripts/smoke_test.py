"""离线冒烟测试（P0 跑通流程）：
   mock 一条群 @ 消息 → ingress → orchestrator → 真实调 Qwen → mock 渠道收到回复 → Trace 落盘。

用法：python scripts/smoke_test.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# 让脚本能 import 项目根的 src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.channel.mock_channel import MockChannel
from src.config import Settings
from src.ingress.pipeline import IngressPipeline
from src.llm.client import LLMClient
from src.models import IncomingMessage
from src.orchestrator.orchestrator import Orchestrator
from src.tracing.tracer import Tracer


async def run() -> None:
    settings = Settings()
    tracer = Tracer(settings)
    llm = LLMClient(settings)
    channel = MockChannel()
    orch = Orchestrator(settings, llm, tracer, channel)
    ingress = IngressPipeline(settings, handler=orch.handle_batch)
    await ingress.start()

    # 构造一条群 @ 消息
    msg = IncomingMessage(
        msg_id="smoke-0001",
        msg_seq=1,
        conversation_key="group:test-group",
        sender="user_alice",
        content="@小同事 你好，用一句话介绍你自己",
        at_me=True,
    )

    print("=== 1) 投递消息到 ingress ===")
    await ingress.accept(msg)

    # 等 coalescer idle(2s) + LLM 调用完成（Qwen flash 约 10-15s）
    print("=== 2) 等待合并窗口 + LLM 响应（约 20s）===")
    await asyncio.sleep(20.0)

    await ingress.stop()

    print("=== 3) 结果 ===")
    if channel.sent:
        for key, text in channel.sent:
            print(f"  已回复 [{key}]: {text}")
    else:
        print("  ✗ 未收到回复")
        sys.exit(1)

    # 校验 Trace 落盘
    trace_dir = settings.root / "runs" / "traces"
    files = list(trace_dir.rglob("*.jsonl"))
    print(f"=== 4) Trace 文件数：{len(files)} ===")
    for f in files:
        print(f"  - {f.relative_to(settings.root)}")
        print("    内容：")
        for line in f.read_text(encoding="utf-8").splitlines():
            print(f"      {line}")


if __name__ == "__main__":
    asyncio.run(run())
