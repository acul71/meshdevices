"""Build a libp2p `Swarm` with an explicit `ITransport` (e.g. `IrohTransport`)."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Literal

from libp2p import (
    DEFAULT_MUXER,
    MUXER_MPLEX,
    MUXER_YAMUX,
    create_mplex_muxer_option,
    create_yamux_muxer_option,
    generate_peer_id_from,
)
from libp2p.abc import (
    INetworkService,
    IPeerStore,
    ISecureTransport,
    ITransport,
)
from libp2p.crypto.keys import KeyPair
from libp2p.crypto.x25519 import create_new_key_pair as create_new_x25519_key_pair
from libp2p.custom_types import (
    TMuxerOptions,
    TProtocol,
    TSecurityOptions,
)
from libp2p.network.config import (
    ConnectionConfig,
    RetryConfig,
)
from libp2p.network.swarm import Swarm
from libp2p.peer.peerstore import PeerStore
from libp2p.rcmgr import ResourceManager
from libp2p.security.insecure.transport import (
    PLAINTEXT_PROTOCOL_ID,
    InsecureTransport,
)
from libp2p.security.noise.transport import (
    PROTOCOL_ID as NOISE_PROTOCOL_ID,
    Transport as NoiseTransport,
)
from libp2p.security.tls.transport import (
    PROTOCOL_ID as TLS_PROTOCOL_ID,
    TLSTransport,
)
import libp2p.security.secio.transport as secio
from libp2p.stream_muxer.mplex.mplex import Mplex
from libp2p.stream_muxer.yamux.yamux import Yamux
from libp2p.transport.upgrader import TransportUpgrader

logger = logging.getLogger(__name__)


def new_swarm_with_transport(
    transport: ITransport,
    *,
    key_pair: KeyPair | None = None,
    muxer_opt: TMuxerOptions | None = None,
    sec_opt: TSecurityOptions | None = None,
    peerstore_opt: IPeerStore | None = None,
    muxer_preference: Literal["YAMUX", "MPLEX"] | None = None,
    enable_autotls: bool = False,
    retry_config: RetryConfig | None = None,
    connection_config: ConnectionConfig | None = None,
    resource_manager: ResourceManager | None = None,
    psk: str | None = None,
) -> INetworkService:
    """
    Same as `libp2p.new_swarm` but uses the provided transport (e.g. iroh-backed).

    Security: defaults match `libp2p.new_swarm` (Noise + TLS + secio + plaintext).
    iroh already encrypts QUIC; Noise adds libp2p identity binding on the byte pipe.
    """
    if key_pair is None:
        from libp2p import generate_new_ed25519_identity

        key_pair = generate_new_ed25519_identity()

    id_opt = generate_peer_id_from(key_pair)

    noise_key_pair = create_new_x25519_key_pair()

    secure_transports_by_protocol: Mapping[TProtocol, ISecureTransport] = sec_opt or {
        NOISE_PROTOCOL_ID: NoiseTransport(
            key_pair, noise_privkey=noise_key_pair.private_key
        ),
        TLS_PROTOCOL_ID: TLSTransport(key_pair, enable_autotls=enable_autotls),
        TProtocol(secio.ID): secio.Transport(key_pair),
        TProtocol(PLAINTEXT_PROTOCOL_ID): InsecureTransport(
            key_pair, peerstore=peerstore_opt
        ),
    }

    if muxer_preference is not None:
        temp_pref = muxer_preference.upper()
        if temp_pref not in [MUXER_YAMUX, MUXER_MPLEX]:
            raise ValueError(
                f"Unknown muxer: {muxer_preference}. Use 'YAMUX' or 'MPLEX'."
            )
        active_preference = temp_pref
    else:
        active_preference = DEFAULT_MUXER

    if muxer_opt is not None:
        muxer_transports_by_protocol = muxer_opt
    else:
        if active_preference == MUXER_MPLEX:
            muxer_transports_by_protocol = create_mplex_muxer_option()
        else:
            muxer_transports_by_protocol = create_yamux_muxer_option()

    upgrader = TransportUpgrader(
        secure_transports_by_protocol=dict(secure_transports_by_protocol),
        muxer_transports_by_protocol=muxer_transports_by_protocol,
    )

    peerstore = peerstore_opt or PeerStore()
    peerstore.add_key_pair(id_opt, key_pair)

    swarm = Swarm(
        id_opt,
        peerstore,
        upgrader,
        transport,
        retry_config=retry_config,
        connection_config=connection_config,
        psk=psk,
    )

    if resource_manager is None:
        try:
            from libp2p.rcmgr import new_resource_manager as _new_rm

            resource_manager = _new_rm()
        except Exception:
            resource_manager = None

    if resource_manager is not None:
        swarm.set_resource_manager(resource_manager)

    return swarm
