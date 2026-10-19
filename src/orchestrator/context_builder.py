"""上下文构建（设计文档 §7.4 / FR-07）：人设 + 会话窗口 + 记忆检索。"""
from __future__ import annotations

from src.models import Context, IncomingMessage

SYSTEM_PROMPT = (
    "你是常驻在 QQ 群里的数字同事，名叫「显显」。"
    "回答简洁、口语化，自然带 1-2 个小表情。"
    "不知道就说不知道，不要编造。"
)


class ContextBuilder:
    async def build(self, msg: IncomingMessage, batch: list[IncomingMessage]) -> Context:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        for m in batch:
            role = "assistant" if m.at_me and m.content.startswith("@") else "user"
            # 群消息统一按 user 视角喂入
            text = m.content
            if m.at_me:
                text = text.lstrip("@ ").strip()
            messages.append({"role": "user", "content": f"[{m.sender}] {text}"})
        return Context(messages=messages, category="chat")
