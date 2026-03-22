"""Wrap `iroh.BiStream` as `libp2p.io.abc.ReadWriteCloser` for `RawConnection`."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from libp2p.io.abc import ReadWriteCloser
from multiaddr import Multiaddr

from meshdevices.iroh_loop import await_iroh

if TYPE_CHECKING:
    import iroh

logger = logging.getLogger(__name__)

_DEFAULT_READ_CHUNK = 65536


class BiStreamReadWriteCloser(ReadWriteCloser):
    """Adapts iroh QUIC `BiStream` to libp2p's stream interface."""

    is_initiator: bool

    def __init__(
        self,
        stream: iroh.BiStream,
        *,
        initiator: bool,
        transport_addrs: list[Multiaddr] | None = None,
    ) -> None:
        import iroh as iroh_mod

        self._iroh = iroh_mod
        self._stream = stream
        self._recv = stream.recv()
        self._send = stream.send()
        self._closed = False
        self.is_initiator = initiator
        self._transport_addrs = transport_addrs or []

    async def read(self, n: int | None = None) -> bytes:
        limit = _DEFAULT_READ_CHUNK if n is None else int(n)
        return await await_iroh(self._recv.read(limit))

    async def write(self, data: bytes) -> None:
        await await_iroh(self._send.write_all(data))

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            await await_iroh(self._send.finish())
        except Exception as e:
            logger.debug("send finish: %s", e)
        try:
            await await_iroh(self._recv.stop(0))
        except Exception as e:
            logger.debug("recv stop: %s", e)

    def get_remote_address(self) -> tuple[str, int] | None:
        return None

    def get_transport_addresses(self) -> list[Multiaddr]:
        return list(self._transport_addrs)
