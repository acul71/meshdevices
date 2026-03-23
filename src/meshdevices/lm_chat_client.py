"""One-shot outbound LM proxy stream: POST JSON to peer's `/meshdevices/lm-proxy/1.0.0`."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import trio
from libp2p import generate_new_ed25519_identity
from libp2p.host.basic_host import BasicHost
from libp2p.network.stream.exceptions import StreamReset
from libp2p.peer.id import ID
from libp2p.tools.utils import info_from_p2p_addr
from multiaddr import Multiaddr

from meshdevices.identity import ed25519_keypair_to_iroh_secret_bytes
from meshdevices.iroh_loop import iroh_uniffi_loop
from meshdevices.config import DEFAULT_LM_STUDIO_MODEL
from meshdevices.lm_proxy import LM_PROXY_PROTOCOL, MAX_REQUEST_BYTES
from meshdevices.node import connect_to_bootstrap_peers
from meshdevices.swarm_builder import new_swarm_with_transport
from meshdevices.transport import IrohTransport

if TYPE_CHECKING:
    from libp2p.crypto.keys import KeyPair

    from meshdevices.config import MeshConfig

logger = logging.getLogger(__name__)

# py-libp2p + iroh: full `NetStream.close()` can block a long time after reads complete
# (QUIC half-close / swarm notify). Response bytes are already buffered; do not hold the CLI.
_CLOSE_STREAM_BUDGET_S = 15.0
_RESET_STREAM_BUDGET_S = 5.0


async def _close_lm_proxy_stream(stream) -> None:
    with trio.move_on_after(_CLOSE_STREAM_BUDGET_S) as scope:
        await stream.close()
    if scope.cancelled_caught:
        logger.warning(
            "lm-chat: stream.close() exceeded %.0fs; resetting stream",
            _CLOSE_STREAM_BUDGET_S,
        )
        with trio.move_on_after(_RESET_STREAM_BUDGET_S) as scope2:
            await stream.reset()
        if scope2.cancelled_caught:
            logger.warning(
                "lm-chat: stream.reset() also exceeded %.0fs; continuing",
                _RESET_STREAM_BUDGET_S,
            )


def peer_id_from_base58_cli(peer_b58: str) -> ID:
    """Parse ``--peer``; raise ``ValueError`` with a clear message if placeholder or invalid."""
    s = peer_b58.strip()
    if "..." in s:
        raise ValueError(
            "--peer must be the full libp2p PeerId (base58) from the server log, "
            "not a placeholder such as 12D3KooW..."
        )
    try:
        return ID.from_base58(s)
    except Exception as e:
        raise ValueError(
            f"Invalid --peer (expected base58 libp2p PeerId): {e}. "
            "Copy the full value after: meshdevices node up peer="
        ) from e


def _default_chat_json(prompt: str, *, model: str) -> bytes:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    return json.dumps(body).encode("utf-8")


async def run_lm_chat(
    cfg: MeshConfig,
    *,
    peer_b58: str,
    request_body: bytes | None = None,
    prompt: str | None = None,
    key_pair: "KeyPair | None" = None,
    model_override: str | None = None,
) -> bytes:
    """
    Connect to `peer_b58` using `cfg.peer_tickets` / bootstrap, open LM proxy stream, return response bytes.

    For default JSON, ``model`` is ``model_override`` if set, else ``cfg.lm_studio_model``, else
    :data:`DEFAULT_LM_STUDIO_MODEL`.
    """
    if request_body is None:
        if prompt is None:
            prompt = "Say hello in one short sentence."
        model = (
            model_override
            or cfg.lm_studio_model
            or DEFAULT_LM_STUDIO_MODEL
        )
        request_body = _default_chat_json(prompt, model=model)

    peer_id = peer_id_from_base58_cli(peer_b58)

    async with iroh_uniffi_loop():
        kp = key_pair or generate_new_ed25519_identity()
        sk = ed25519_keypair_to_iroh_secret_bytes(kp)
        transport = IrohTransport(secret_key=sk, peer_tickets=cfg.peer_tickets)
        swarm = new_swarm_with_transport(transport, key_pair=kp)
        host = BasicHost(swarm, bootstrap=None)
        listen_maddrs = (Multiaddr(""),)

        async with host.run(listen_addrs=listen_maddrs), trio.open_nursery() as nursery:
            nursery.start_soon(host.get_peerstore().start_cleanup_task, 60)
            if cfg.bootstrap:
                await connect_to_bootstrap_peers(host, cfg.bootstrap)

            info = info_from_p2p_addr(Multiaddr(f"/p2p/{peer_b58}"))
            logger.debug("lm-chat: dialing / ensuring connection to %s", peer_b58)
            await host.connect(info)
            logger.debug("lm-chat: opening LM proxy stream")
            stream = await host.new_stream(peer_id, [LM_PROXY_PROTOCOL])
            logger.debug("lm-chat: sending request (%d bytes)", len(request_body))
            try:
                await stream.write(request_body)
            except StreamReset as e:
                raise RuntimeError(
                    "LM proxy stream was reset by the server before the request was sent. "
                    "If the server uses allow_peer_ids, add this node's PeerId (from "
                    "`print-ticket` / identity) to the server's allow_peer_ids, or use an "
                    "empty allow_peer_ids list to allow any peer for local testing."
                ) from e
            response = await stream.read(MAX_REQUEST_BYTES)
            await _close_lm_proxy_stream(stream)
            logger.info("lm-chat: received %d bytes from LM proxy", len(response))
            return response
