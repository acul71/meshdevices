"""
Stream protocol: forward one HTTP/1.1 request to LM Studio (OpenAI-compatible), return response bytes.

MVP: read request up to `max_request`, forward with httpx, write response.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from libp2p.abc import INetStream
from libp2p.custom_types import TProtocol

if TYPE_CHECKING:
    from meshdevices.allowlist import PeerAllowlist

logger = logging.getLogger(__name__)

LM_PROXY_PROTOCOL = TProtocol("/meshdevices/lm-proxy/1.0.0")
MAX_REQUEST_BYTES = 8 * 1024 * 1024


async def handle_lm_proxy_stream(
    stream: INetStream,
    *,
    lm_base: str,
    allowlist: PeerAllowlist | None,
    remote_peer_b58: str | None,
) -> None:
    if allowlist is not None and remote_peer_b58 is not None:
        if remote_peer_b58 not in allowlist:
            logger.warning("denied LM proxy for non-allowlisted peer %s", remote_peer_b58)
            await stream.reset()
            return

    try:
        req_bytes = await stream.read(MAX_REQUEST_BYTES)
    except Exception as e:
        logger.error("read request: %s", e)
        return

    if not req_bytes:
        await stream.close()
        return

    base = lm_base.rstrip("/")
    async with httpx.AsyncClient(timeout=600.0) as client:
        try:
            resp = await client.post(
                f"{base}/v1/chat/completions",
                content=req_bytes,
                headers={"Content-Type": "application/json"},
            )
        except Exception as e:
            err = f"HTTP error: {e}\n".encode()
            await stream.write(err)
            await stream.close()
            return

    try:
        await stream.write(resp.content)
    finally:
        await stream.close()


def register_lm_proxy_handler(host, *, lm_base: str, allowlist: PeerAllowlist | None) -> None:
    """Register `/meshdevices/lm-proxy/1.0.0` on the host."""

    async def _handler(stream: INetStream) -> None:
        remote = None
        try:
            remote = stream.muxed_conn.peer_id.to_base58()
        except Exception:
            pass
        await handle_lm_proxy_stream(
            stream, lm_base=lm_base, allowlist=allowlist, remote_peer_b58=remote
        )

    host.set_stream_handler(LM_PROXY_PROTOCOL, _handler)
