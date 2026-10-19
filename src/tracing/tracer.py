"""Trace 观测（设计文档 §6）：JSONL 落盘，trace_id 贯穿全链路。"""
from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import Settings
from src.models import IncomingMessage


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class Trace:
    """一次入站消息的完整追踪句柄。"""

    def __init__(self, trace_id: str, path: Path) -> None:
        self.trace_id = trace_id
        self.path = path
        self.started_at = _now_iso()


class Tracer:
    def __init__(self, settings: Settings) -> None:
        self._root = settings.root / "runs" / "traces"

    def start(self, msg: IncomingMessage) -> Trace:
        trace_id = msg.trace_id or uuid.uuid4().hex
        msg.trace_id = trace_id
        day = datetime.now().strftime("%Y%m%d")
        d = self._root / day
        d.mkdir(parents=True, exist_ok=True)
        trace = Trace(trace_id, d / f"{trace_id}.jsonl")
        self._emit(trace, "ingress", {
            "channel": msg.conversation_key.split(":", 1)[0],
            "msg_type": msg.msg_type,
            "at_me": msg.at_me,
        })
        return trace

    def span(self, trace: Trace, name: str, **attrs: Any) -> None:
        """记录一个即时 span 事件。需要计时时用 with self.timed(...)。"""
        self._emit(trace, name, dict(attrs))

    def finish(self, trace: Trace) -> None:
        self._emit(trace, "finish", {"ts": _now_iso()})

    def _emit(self, trace: Trace, span: str, attrs: dict[str, Any]) -> None:
        record = {
            "trace_id": trace.trace_id,
            "ts": _now_iso(),
            "span": span,
            "attrs": attrs,
        }
        with open(trace.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
