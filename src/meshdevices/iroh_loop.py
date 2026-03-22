"""
Trio integration for iroh’s Python bindings (UniFFI).

Application code uses **trio** only. iroh internally awaits **asyncio** futures; we:

1. Open a **trio-asyncio** loop (:func:`iroh_uniffi_loop`) and register it with UniFFI.
2. Bridge each iroh awaitable with :func:`await_iroh` (``trio_asyncio.aio_as_trio``).

No separate asyncio thread; the asyncio loop runs on top of trio.
"""

from __future__ import annotations

from collections.abc import Awaitable
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, TypeVar

import trio_asyncio
from trio_asyncio import current_loop as _trio_aio_current_loop

_T = TypeVar("_T")

# Set while :func:`iroh_uniffi_loop` is active. Inbound libp2p work runs in a Trio task
# spawned via ``trio_as_future`` from asyncio (iroh ProtocolHandler); that task may
# not have trio-asyncio's ``current_loop`` ContextVar set, so :func:`await_iroh` falls
# back to this handle for ``run_aio_coroutine``.
_active_trio_asyncio_loop: Any | None = None


async def await_iroh(awaitable: Awaitable[_T]) -> _T:
    """Await an iroh/asyncio coroutine or future from trio code."""
    loop = _trio_aio_current_loop.get()
    if loop is None:
        loop = _active_trio_asyncio_loop
    if loop is None:
        raise RuntimeError(
            "await_iroh: no trio-asyncio loop (use inside iroh_uniffi_loop)"
        )
    return await loop.run_aio_coroutine(awaitable)


@asynccontextmanager
async def iroh_uniffi_loop() -> AsyncIterator[None]:
    """
    Enter trio-asyncio and register the loop for iroh UniFFI.

    Use together with :func:`await_iroh` for every ``await`` on iroh async APIs.
    """
    global _active_trio_asyncio_loop
    async with trio_asyncio.open_loop() as loop:
        _active_trio_asyncio_loop = loop
        try:
            from iroh.iroh_ffi import uniffi_set_event_loop

            uniffi_set_event_loop(loop)
            yield
        finally:
            _active_trio_asyncio_loop = None
