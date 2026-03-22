"""Map libp2p PeerId / keys to iroh `PublicKey` (32-byte Ed25519 material)."""

from __future__ import annotations

import iroh

from libp2p.crypto.keys import KeyPair, PublicKey
from libp2p.peer.id import ID as PeerID


def libp2p_peer_id_to_iroh_public_key(peer_id: PeerID) -> iroh.PublicKey:
    """
    Extract Ed25519 pubkey bytes from a libp2p PeerId and build iroh PublicKey.

    Uses identity-multihash extraction when available (Ed25519 libp2p peers).
    """
    pub = peer_id.extract_public_key()
    if pub is None:
        raise ValueError(
            "PeerId does not embed a public key (e.g. hashed RSA); "
            "use Ed25519 identities or supply an iroh NodeTicket."
        )
    raw = pub.to_bytes()
    if len(raw) != 32:
        raise ValueError(f"Unexpected pubkey length {len(raw)} for iroh mapping")
    return iroh.PublicKey.from_bytes(raw)


def libp2p_public_key_to_iroh(pub: PublicKey) -> iroh.PublicKey:
    """Build iroh PublicKey from a libp2p public key (Ed25519: 32 bytes)."""
    b = pub.to_bytes()
    if len(b) != 32:
        raise ValueError("Only Ed25519 raw pubkeys (32 bytes) supported for iroh bridge")
    return iroh.PublicKey.from_bytes(b)


def ed25519_keypair_to_iroh_secret_bytes(key_pair: KeyPair) -> bytes:
    """32-byte secret seed for `iroh.NodeOptions(secret_key=...)`."""
    sk = key_pair.private_key
    if hasattr(sk, "to_bytes"):
        return sk.to_bytes()
    raise TypeError("Expected Ed25519 private key with to_bytes()")
