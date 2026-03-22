"""GossipSub / pubsub topic validators that enforce a PeerId allowlist."""

from __future__ import annotations

import logging

from libp2p.peer.id import ID
from libp2p.pubsub.pb import rpc_pb2

from meshdevices.allowlist import PeerAllowlist

logger = logging.getLogger(__name__)


def gossip_allowlist_sync_validator(allowlist: PeerAllowlist):
    """
    Sync pubsub validator: accept messages only from peers in ``allowlist``.

    Compatible with ``Pubsub.set_topic_validator(..., is_async_validator=False)``.
    Signature matches py-libp2p: ``(msg_forwarder, msg) -> bool``.
    """

    def _validate(_msg_forwarder: object, msg: rpc_pb2.Message) -> bool:
        sender = ID(msg.from_id)
        ok = sender in allowlist
        if not ok:
            logger.debug("gossip rejected from non-allowlisted peer %s", sender.to_base58())
        return ok

    return _validate
