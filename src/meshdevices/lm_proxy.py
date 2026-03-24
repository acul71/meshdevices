"""
Stream protocol: forward one HTTP/1.1 request to LM Studio (OpenAI-compatible), return response bytes.

MVP: read request up to `max_request`, forward with httpx, write response.
"""

from __future__ import annotations

import functools
import logging
from typing import TYPE_CHECKING

import httpx
import trio

from libp2p.abc import INetStream
from libp2p.custom_types import TProtocol

if TYPE_CHECKING:
    from meshdevices.allowlist import PeerAllowlist

logger = logging.getLogger(__name__)

LM_PROXY_PROTOCOL = TProtocol("/meshdevices/lm-proxy/1.0.0")
MAX_REQUEST_BYTES = 8 * 1024 * 1024
# Chunk outbound response bodies so yamux/QUIC flow control can make progress vs one huge write.
_RESPONSE_WRITE_CHUNK = 32 * 1024


def _post_chat_completions_sync(url: str, content: bytes) -> tuple[int, bytes]:
    """Blocking LM Studio POST (runs in a worker thread)."""
    with httpx.Client(timeout=600.0) as client:
        r = client.post(
            url,
            content=content,
            headers={"Content-Type": "application/json"},
        )
        return r.status_code, r.content


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

    logger.info(
        "lm proxy: read %d-byte request, forwarding to %s/v1/chat/completions",
        len(req_bytes),
        lm_base.rstrip("/"),
    )
    base = lm_base.rstrip("/")
    url = f"{base}/v1/chat/completions"
    # Inbound libp2p runs under trio_asyncio (asyncio-driven). httpx.AsyncClient there
    # often follows asyncio and can starve trio: yamux/QUIC make no progress while LM
    # Studio works, so the client never sees bytes. Sync httpx in to_thread keeps trio free.
    try:
        status_code, body = await trio.to_thread.run_sync(
            functools.partial(_post_chat_completions_sync, url, req_bytes),
        )
    except Exception as e:
        logger.error("lm proxy: httpx POST failed: %s", e)
        err = f"HTTP error: {e}\n".encode()
        await stream.write(err)
        await stream.close()
        return

    logger.info(
        "lm proxy: LM Studio HTTP %s response body %d bytes",
        status_code,
        len(body),
    )
    try:
        if len(body) <= _RESPONSE_WRITE_CHUNK:
            await stream.write(body)
            await trio.sleep(0)
        else:
            for i in range(0, len(body), _RESPONSE_WRITE_CHUNK):
                chunk = body[i : i + _RESPONSE_WRITE_CHUNK]
                await stream.write(chunk)
                await trio.sleep(0)
                logger.debug(
                    "lm proxy: wrote chunk %d..%d (%d bytes)",
                    i,
                    min(i + _RESPONSE_WRITE_CHUNK, len(body)),
                    len(chunk),
                )
    finally:
        logger.debug("lm proxy: closing stream after response")
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
