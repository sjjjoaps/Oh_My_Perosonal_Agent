"""领域数据模型（设计文档 §7.1）。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class IncomingMessage:
    msg_id: str
    msg_seq: int
    conversation_key: str          # "group:{id}" | "c2c:{openid}"
    sender: str
    content: str
    msg_type: str = "text"
    at_me: bool = False
    ts: datetime = field(default_factory=datetime.now)
    trace_id: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0
    latency_ms: int = 0


@dataclass
class MemoryFact:
    fact_id: str
    subject: str
    predicate: str
    object: str
    source_msg_id: str = ""
    confidence: float = 0.5
    status: str = "active"
    ts: datetime = field(default_factory=datetime.now)


@dataclass
class ToolResult:
    ok: bool
    output: str
    exit_code: int = 0
    duration_ms: int = 0


@dataclass
class Context:
    """编排层组装后的上下文。"""
    messages: list[dict[str, str]] = field(default_factory=list)
    memory_hits: list[MemoryFact] = field(default_factory=list)
    kb_hits: int = 0
    category: str = "chat"        # chat | clarify | tool | failure
