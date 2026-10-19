"""QQ 官方渠道（设计文档 §7.2）：botpy 封装。

继承 botpy.Client，把群 @ 事件转成 IncomingMessage 喂给 ingress；
回复走被动消息（5 分钟窗口，引用原 msg_id）。
"""
from __future__ import annotations

import asyncio
import logging

import botpy
from botpy.message import GroupMessage

from src.config import Settings
from src.ingress.pipeline import IngressPipeline
from src.models import IncomingMessage

log = logging.getLogger(__name__)


class _QQBotClient(botpy.Client):
    """内部 botpy 客户端，事件回调转发给 ingress。"""

    def __init__(self, settings: Settings, ingress: IngressPipeline, **kwargs) -> None:
        super().__init__(intents=botpy.Intents(public_messages=True), **kwargs)
        self._s = settings
        self._ingress = ingress

    async def on_ready(self) -> None:
        log.info("QQ bot 已上线：%s", self.robot)

    async def on_group_at_message_create(self, message: GroupMessage) -> None:
        log.info("=== 收到群 @ 消息 ===")
        log.info("group_openid=%s, author=%s, content=%r, id=%s",
                 message.group_openid,
                 getattr(message.author, "member_openid", "?"),
                 message.content, message.id)
        msg = IncomingMessage(
            msg_id=message.id,
            msg_seq=int(getattr(message, "seq", 1) or 1),
            conversation_key=f"group:{message.group_openid}",
            sender=message.author.member_openid or "unknown",
            content=message.content or "",
            at_me=True,
        )
        await self._ingress.accept(msg)


class QQChannel:
    """对外暴露 send_reply / start / stop，与 MockChannel 同接口。"""

    def __init__(self, settings: Settings, ingress: IngressPipeline | None = None) -> None:
        self._s = settings
        self._ingress = ingress
        self._client: _QQBotClient | None = None
        self._task: asyncio.Task | None = None

    def bind_ingress(self, ingress: IngressPipeline) -> None:
        self._ingress = ingress

    async def start(self) -> None:
        app_id = self._s.qq_app_id
        secret = self._s.qq_app_secret
        if not app_id or not secret:
            raise RuntimeError("QQ 凭据缺失：请在 .env 填 app_ID / app_SECRET")

        self._client = _QQBotClient(
            self._s,
            self._ingress,
            is_sandbox=self._s.get("channel.qq.sandbox", True),
            bot_log=True,
        )
        # botpy.start() 是长循环，作为后台任务跑
        self._task = asyncio.create_task(
            self._client.start(appid=app_id, secret=secret)
        )
        log.info("QQChannel 启动中（app_id=%s, sandbox=%s）",
                 app_id, self._s.get("channel.qq.sandbox", True))

    async def send_reply(self, msg: IncomingMessage, content: str) -> bool:
        if not self._client:
            log.warning("QQ client 未就绪，丢弃回复")
            return False
        group_openid = msg.conversation_key.split(":", 1)[1]
        try:
            await self._client.api.post_group_message(
                group_openid=group_openid,
                content=content,
                msg_type=0,           # 纯文本
                msg_id=msg.msg_id,    # 被动回复窗口
                msg_seq=1,
            )
            return True
        except Exception:
            log.exception("post_group_message failed")
            return False

    async def stop(self) -> None:
        if self._client:
            await self._client.close()
        if self._task:
            self._task.cancel()
