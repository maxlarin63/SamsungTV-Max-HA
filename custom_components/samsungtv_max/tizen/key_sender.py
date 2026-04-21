"""Key-sending queue with inter-key delay.

Ported from keyControl.lua.  Keys are queued and dispatched sequentially with
TIZEN_KEY_DELAY (120 ms) between each send to avoid dropped inputs on the TV.
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from collections.abc import Callable, Coroutine
from typing import Any

from ..const import TIZEN_KEY_DELAY

_LOGGER = logging.getLogger(__name__)

SendFn = Callable[[str], Coroutine[Any, Any, bool]]


class KeySender:
    """Serialises key commands through an asyncio queue."""

    def __init__(self, send_fn: SendFn, delay: float = TIZEN_KEY_DELAY) -> None:
        self._send_fn = send_fn
        self._delay = delay
        self._queue: deque[str] = deque()
        self._task: asyncio.Task | None = None

    def enqueue(self, key: str, count: int = 1) -> None:
        """Add *count* copies of *key* to the send queue."""
        for _ in range(max(1, count)):
            self._queue.append(key)
        if self._task is None or self._task.done():
            self._task = asyncio.ensure_future(self._drain())

    def clear(self) -> None:
        """Discard all pending keys (e.g. on disconnect)."""
        self._queue.clear()

    async def _drain(self) -> None:
        while self._queue:
            key = self._queue.popleft()
            _LOGGER.debug("Sending key: %s", key)
            try:
                await self._send_fn(key)
            except Exception as exc:  # noqa: BLE001
                _LOGGER.debug("Key send error (%s): %s", key, exc)
                self._queue.clear()
                return
            if self._queue:
                await asyncio.sleep(self._delay)
