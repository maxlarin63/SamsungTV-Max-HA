"""Tests for tizen/key_sender.py."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from custom_components.samsungtv_max.tizen.key_sender import KeySender


@pytest.fixture
def send_fn():
    return AsyncMock(return_value=True)


class TestKeySender:
    async def test_single_key_sent(self, send_fn):
        ks = KeySender(send_fn, delay=0)
        ks.enqueue("KEY_MUTE")
        await asyncio.sleep(0.01)
        send_fn.assert_awaited_once_with("KEY_MUTE")

    async def test_count_sends_multiple(self, send_fn):
        ks = KeySender(send_fn, delay=0)
        ks.enqueue("KEY_VOLUMEUP", count=3)
        await asyncio.sleep(0.05)
        assert send_fn.await_count == 3
        send_fn.assert_any_await("KEY_VOLUMEUP")

    async def test_multiple_enqueue_calls_serialised(self, send_fn):
        ks = KeySender(send_fn, delay=0)
        ks.enqueue("KEY_UP")
        ks.enqueue("KEY_DOWN")
        await asyncio.sleep(0.05)
        assert send_fn.await_count == 2
        calls = [c.args[0] for c in send_fn.await_args_list]
        assert calls == ["KEY_UP", "KEY_DOWN"]

    async def test_clear_discards_pending(self, send_fn):
        slow_fn = AsyncMock(side_effect=lambda k: asyncio.sleep(1))
        ks = KeySender(slow_fn, delay=0)
        ks.enqueue("KEY_SLOW")
        ks.enqueue("KEY_NEVER")
        ks.clear()
        await asyncio.sleep(0.05)
        # At most the first key was sent; the rest were discarded
        assert slow_fn.await_count <= 1
