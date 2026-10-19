"""回复格式化（设计文档 §7.4 / FR-38）：emoji 装饰 + 截断。"""
from __future__ import annotations

CATEGORY_EMOJI = {
    "chat": "",
    "success": "✅",
    "clarify": "🤔",
    "failure": "⚠️",
    "done": "🎉",
}


class ReplyFormatter:
    def __init__(self, mode: str = "auto", max_length: int = 2000) -> None:
        self._mode = mode
        self._max = max_length

    def format(self, text: str, *, category: str = "chat") -> str:
        text = text.strip()
        if self._mode != "none":
            emoji = CATEGORY_EMOJI.get(category, "")
            if emoji and not text.startswith(emoji):
                text = f"{emoji} {text}"
        if len(text) > self._max:
            text = text[: self._max - 1] + "…"
        return text
