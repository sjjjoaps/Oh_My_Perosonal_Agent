"""去重（设计文档 §9.2 / FR-23）：(msg_id, msg_seq) 唯一。"""
from __future__ import annotations

import time


class Deduper:
    def __init__(self, ttl_sec: int = 3600) -> None:
        self._ttl = ttl_sec
        self._seen: dict[str, float] = {}

    def seen(self, msg_id: str, msg_seq: int = 1) -> bool:
        key = f"{msg_id}:{msg_seq}"
        now = time.time()
        # 清理过期缓存（用户要求：无用缓存及时删除）
        if len(self._seen) > 10000:
            self._evict(now)
        if key in self._seen:
            return True
        self._seen[key] = now
        return False

    def _evict(self, now: float) -> None:
        expired = [k for k, ts in self._seen.items() if now - ts > self._ttl]
        for k in expired:
            del self._seen[k]
