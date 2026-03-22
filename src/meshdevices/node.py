"""Assemble iroh transport, libp2p swarm, DHT, GossipSub, LM proxy."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import trio
from libp2p import generate_new_ed25519_identity, generate_peer_id_from
from libp2p.crypto.keys import KeyPair
from libp2p.custom_types import TProtocol
from libp2p.host.basic_host import BasicHost
from libp2p.kad_dht.kad_dht import (
    DHTMode,
    KadDHT,
)
from libp2p.pubsub.gossipsub import GossipSub
from libp2p.pubsub.pubsub import Pubsub
from libp2p.tools.anyio_service import background_trio_service
from libp2p.tools.utils import info_from_p2p_addr
from multiaddr import Multiaddr

from meshdevices.allowlist import PeerAllowlist
from meshdevices.gossip_allowlist import gossip_allowlist_sync_validator
from meshdevices.identity import ed25519_keypair_to_iroh_secret_bytes
from meshdevices.iroh_loop import iroh_uniffi_loop
from meshdevices.lm_proxy import register_lm_proxy_handler
from meshdevices.swarm_builder import new_swarm_with_transport
from meshdevices.transport import IrohTransport

if TYPE_CHECKING:
    from meshdevices.config import MeshConfig

logger = logging.getLogger(__name__)

GOSSIPSUB_PROTOCOL_ID = TProtocol("/meshsub/1.0.0")


async def mesh_run_forever(cfg: MeshConfig, *, key_pair: KeyPair | None = None) -> None:
    async with iroh_uniffi_loop():
        kp = key_pair or generate_new_ed25519_identity()
        sk = ed25519_keypair_to_iroh_secret_bytes(kp)

        transport = IrohTransport(
            secret_key=sk,
            peer_tickets=cfg.peer_tickets,
        )
        swarm = new_swarm_with_transport(transport, key_pair=kp)
        # Do not pass `bootstrap=` into BasicHost: py-libp2p's BootstrapDiscovery only
        # accepts TCP multiaddrs and will skip /p2p-only peers. We dial via IrohTransport
        # using `connect_to_bootstrap_peers` below instead.
        host = BasicHost(swarm, bootstrap=None)

        mode = DHTMode.SERVER if cfg.dht_mode == "server" else DHTMode.CLIENT
        dht = KadDHT(host, mode)
        allow = PeerAllowlist.from_strings(cfg.allow_peer_ids)
        register_lm_proxy_handler(host, lm_base=cfg.lm_studio_base, allowlist=allow)

        gossipsub = GossipSub(
            protocols=[GOSSIPSUB_PROTOCOL_ID],
            degree=3,
            degree_low=2,
            degree_high=4,
        )
        pubsub = Pubsub(host, gossipsub)
        if cfg.allow_peer_ids:
            pubsub.set_topic_validator(
                cfg.gossip_topic,
                gossip_allowlist_sync_validator(allow),
                is_async_validator=False,
            )

        # No TCP bind; iroh listens via its stack. Empty multiaddr matches libp2p-iroh `listen_on` style.
        listen_maddrs = (Multiaddr(""),)

        async with host.run(listen_addrs=listen_maddrs), trio.open_nursery() as nursery:
            nursery.start_soon(host.get_peerstore().start_cleanup_task, 60)

            async def _log_ticket_when_ready() -> None:
                await trio.sleep(1.0)
                try:
                    t = await transport.get_node_ticket_string()
                    logger.info("iroh NodeTicket (for peer_tickets / dial-in): %s", t)
                except Exception as e:
                    logger.warning("iroh NodeTicket not ready: %s", e)

            nursery.start_soon(_log_ticket_when_ready)

            async with background_trio_service(dht):
                async with background_trio_service(pubsub):
                    # Dial only after Pubsub has a service manager; otherwise inbound
                    # gossip streams can run stream_handler before _manager exists.
                    if cfg.bootstrap:
                        await connect_to_bootstrap_peers(host, cfg.bootstrap)
                    async with background_trio_service(gossipsub):
                        await pubsub.wait_until_ready()
                        sub = await pubsub.subscribe(cfg.gossip_topic)
                        logger.info("meshdevices node up peer=%s", host.get_id().pretty())
                        logger.info("subscribed gossip topic=%s", cfg.gossip_topic)
                        del sub  # silence lint; orchestration uses topic later
                        await trio.sleep_forever()


async def mesh_print_ticket(cfg: MeshConfig, *, key_pair: KeyPair | None = None) -> None:
    """
    Start iroh only (no libp2p swarm), print libp2p PeerId and iroh NodeTicket to stdout, exit.

    If ``key_pair`` is None, a random identity is used. Otherwise use the same key file as
    ``serve`` for stable PeerId / ticket sampling.
    """
    async with iroh_uniffi_loop():
        kp = key_pair or generate_new_ed25519_identity()
        sk = ed25519_keypair_to_iroh_secret_bytes(kp)
        peer_id = generate_peer_id_from(kp).pretty()

        transport = IrohTransport(
            secret_key=sk,
            peer_tickets=cfg.peer_tickets,
        )
        await transport._ensure_node()
        ticket = await transport.get_node_ticket_string()
        print(f"PEER_ID={peer_id}")
        print(f"NODE_TICKET={ticket}")


async def connect_to_bootstrap_peers(host, bootstrap: list[str]) -> None:
    for addr in bootstrap:
        try:
            info = info_from_p2p_addr(Multiaddr(addr))
            host.get_peerstore().add_addrs(info.peer_id, info.addrs, 3600)
            await host.connect(info)
            logger.info("connected bootstrap %s", addr)
        except Exception as e:
            logger.warning("bootstrap %s: %s", addr, e)
