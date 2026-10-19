"""模型路由占位（T 调优阶段实现，原型期直通 default_model）。"""
from __future__ import annotations


class Router:
    async def route(self, ctx) -> str:  # noqa: ANN001
        return "default"
