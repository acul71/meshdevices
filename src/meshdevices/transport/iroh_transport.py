from __future__ import annotations

"""
`ITransport` implementation that carries libp2p bytes over iroh QUIC (Python bindings).

Inbound: iroh `ProtocolHandler` accepts a QUIC connection, waits for the first bidi stream
(initiator opens it on dial), then passes a `ReadWriteCloser` to the swarm listener handler
(which wraps it in `RawConnection` once — same as TCP/WebSocket).

Outbound: `dial` connects via iroh `Endpoint.connect`, opens a bidi stream, wraps as `RawConnection`.

Callers must run under :func:`meshdevices.iroh_loop.iroh_uniffi_loop` (see :mod:`meshdevices.node`).
"""

import asyncio
import logging
from typing import TYPE_CHECKING

import iroh
import trio
import trio_asyncio
from libp2p.abc import (
    IListener,
    IRawConnection,
    ITransport,
)
from libp2p.custom_types import (
    THandler,
)
from libp2p.network.connection.raw_connection import (
    RawConnection,
)
from libp2p.tools.utils import (
    info_from_p2p_addr,
)
from libp2p.transport.exceptions import (
    OpenConnectionError,
)
from multiaddr import Multiaddr

from meshdevices.identity import (
    libp2p_peer_id_to_iroh_public_key,
)
from meshdevices.iroh_loop import await_iroh

from .bistream_adapter import (
    BiStreamReadWriteCloser,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ALPN for the single libp2p-over-iroh pipe (Noise + yamux + protocols on top).
DEFAULT_LIBP2P_OVER_IROH_ALPN = b"meshdevices-libp2p/1"


class IrohTransport(ITransport):
    """
    Transport using iroh for wire bytes. Requires `secret_key` (32 bytes) matching
    the libp2p host Ed25519 seed.

    For dialing, supply `peer_tickets` mapping `PeerID.to_base58()` -> iroh NodeTicket
    string when discovery-only `NodeAddr` is insufficient.
    """

    def __init__(
        self,
        *,
        secret_key: bytes,
        alpn: bytes = DEFAULT_LIBP2P_OVER_IROH_ALPN,
        peer_tickets: dict[str, str] | None = None,
    ) -> None:
        if len(secret_key) != 32:
            raise ValueError("secret_key must be 32 bytes (Ed25519 seed)")
        self._secret_key = secret_key
        self._alpn = alpn
        self._peer_tickets = peer_tickets or {}
        self._conn_handler: THandler | None = None
        self._iroh: iroh.Iroh | None = None
        self._node: iroh.Node | None = None
        self._endpoint: iroh.Endpoint | None = None
        self._node_lock = trio.Lock()

    def _protocol_creator(self) -> iroh.ProtocolCreator:
        outer = self

        class Creator:
            def create(self, _endpoint: iroh.Endpoint) -> object:
                return _Libp2pOverIrohHandler(outer)

        return Creator()

    async def _ensure_node(self) -> None:
        async with self._node_lock:
            if self._endpoint is not None:
                return
            opts = iroh.NodeOptions(
                secret_key=self._secret_key,
                protocols={self._alpn: self._protocol_creator()},
            )
            self._iroh = await await_iroh(iroh.Iroh.memory_with_options(opts))
            self._node = self._iroh.node()
            self._endpoint = self._node.endpoint()
            logger.info("iroh node started; local node_id=%s", self._endpoint.node_id())

    async def dial(self, maddr: Multiaddr) -> IRawConnection:
        await self._ensure_node()
        assert self._endpoint is not None
        try:
            pinfo = info_from_p2p_addr(maddr)
        except Exception as e:
            raise OpenConnectionError(f"Bad multiaddr for iroh dial: {maddr}: {e}") from e

        peer = pinfo.peer_id
        pk = libp2p_peer_id_to_iroh_public_key(peer)
        ticket_str = self._peer_tickets.get(peer.to_base58())
        if ticket_str:
            na = iroh.NodeTicket.parse(ticket_str).node_addr()
        else:
            na = iroh.NodeAddr(pk, None, [])

        try:
            conn = await await_iroh(self._endpoint.connect(na, self._alpn))
        except Exception as e:
            raise OpenConnectionError(f"iroh connect failed: {e}") from e

        try:
            bi = await await_iroh(conn.open_bi())
        except Exception as e:
            raise OpenConnectionError(f"iroh open_bi failed: {e}") from e

        rw = BiStreamReadWriteCloser(bi, initiator=True)
        return RawConnection(rw, initiator=True)

    async def get_node_ticket_string(self, *, max_wait_s: float = 20.0) -> str:
        """
        After :meth:`_ensure_node`, return a serialized iroh ``NodeTicket`` for out-of-band dial
        (see config ``peer_tickets``). Polls ``node.status()`` until the ticket string is non-empty.
        """
        await self._ensure_node()
        assert self._node is not None
        deadline = trio.current_time() + max_wait_s
        last_exc: BaseException | None = None
        while trio.current_time() < deadline:
            try:
                status = await await_iroh(self._node.status())
                addr = status.node_addr()
                ticket = iroh.NodeTicket(addr)
                text = str(ticket).strip()
                if text:
                    return text
            except Exception as e:
                last_exc = e
            await trio.sleep(0.4)
        msg = f"iroh NodeTicket not available after {max_wait_s}s"
        if last_exc is not None:
            msg += f": {last_exc}"
        raise RuntimeError(msg)

    def create_listener(self, handler_function: THandler) -> IListener:
        self._conn_handler = handler_function
        return IrohListener(self)


class _Libp2pOverIrohHandler:
    """iroh `ProtocolHandler`: first bidi stream carries libp2p bytes."""

    def __init__(self, transport: IrohTransport) -> None:
        self._transport = transport

    async def accept(self, conn: iroh.Connection) -> None:
        handler = self._transport._conn_handler
        if handler is None:
            logger.warning("iroh inbound connection but no libp2p handler yet; closing")
            conn.close(0, b"no-handler")
            return
        try:
            # ProtocolHandler runs on the trio-asyncio loop (asyncio semantics).
            bi = await conn.accept_bi()
        except Exception as e:
            logger.error("accept_bi: %s", e)
            return
        rw = BiStreamReadWriteCloser(bi, initiator=False)
        try:
            # iroh invokes this on the asyncio side of trio-asyncio; swarm's listener
            # handler is trio-native — must bridge (see trio_asyncio.trio_as_aio).
            # UniFFI schedules this coroutine without trio_asyncio's current_loop set;
            # pass the running asyncio loop explicitly (the open_loop instance).
            aio_loop = asyncio.get_running_loop()
            await trio_asyncio.trio_as_aio(handler, loop=aio_loop)(rw)
        except Exception as e:
            logger.exception("libp2p handler error: %s", e)

    async def shutdown(self) -> None:
        return None


class IrohListener(IListener):
    def __init__(self, transport: IrohTransport) -> None:
        self._transport = transport
        self._listeners: list[object] = []

    async def listen(self, maddr: Multiaddr, nursery: trio.Nursery) -> None:
        # iroh listens via the magic socket stack; we only need the node up.
        await self._transport._ensure_node()

    def get_addrs(self) -> tuple[Multiaddr, ...]:
        # Real addresses are iroh NodeTickets; share those out-of-band.
        return ()

    async def close(self) -> None:
        if self._transport._node is not None:
            try:
                await await_iroh(self._transport._node.shutdown())
            except Exception as e:
                logger.debug("iroh node shutdown: %s", e)
            self._transport._node = None
            self._transport._endpoint = None
            self._transport._iroh = None
