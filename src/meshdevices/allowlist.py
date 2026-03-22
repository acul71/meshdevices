"""Pre-approved libp2p PeerIds (base58)."""

from __future__ import annotations

from libp2p.peer.id import ID as PeerID


class PeerAllowlist:
    def __init__(self, peer_ids: set[str]) -> None:
        self._ids = {p.strip() for p in peer_ids if p.strip()}

    def __contains__(self, peer: PeerID | str) -> bool:
        if isinstance(peer, PeerID):
            s = peer.to_base58()
        else:
            s = str(peer).strip()
        return s in self._ids

    @classmethod
    def from_strings(cls, items: list[str]) -> PeerAllowlist:
        return cls(set(items))
