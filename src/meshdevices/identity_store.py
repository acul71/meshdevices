"""Load or create persistent libp2p Ed25519 keys for stable PeerIds across restarts."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from libp2p import generate_new_ed25519_identity
from libp2p.crypto.ed25519 import Ed25519PrivateKey
from libp2p.crypto.keys import KeyPair

from meshdevices.config import MeshConfig

logger = logging.getLogger(__name__)


def resolve_identity_key_path(cfg: MeshConfig, config_path: Path) -> Path | None:
    """Resolve ``identity_key_file`` relative to the config file directory."""
    if not cfg.identity_key_file:
        return None
    p = Path(cfg.identity_key_file)
    if not p.is_absolute():
        p = (config_path.parent / p).resolve()
    return p


def load_or_create_keypair(path: Path) -> KeyPair:
    """
    Read 32-byte Ed25519 seed from ``path``, or generate a new key and write it (mode 0600).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raw = path.read_bytes()
        if len(raw) != 32:
            raise ValueError(
                f"identity key file {path} must contain exactly 32 raw Ed25519 seed bytes"
            )
        pvt = Ed25519PrivateKey.from_bytes(raw)
        logger.info("loaded libp2p identity key from %s", path)
        return KeyPair(pvt, pvt.get_public_key())

    kp = generate_new_ed25519_identity()
    raw = kp.private_key.to_bytes()
    if len(raw) != 32:
        raise ValueError("expected 32-byte Ed25519 private key material")
    path.write_bytes(raw)
    os.chmod(path, 0o600)
    logger.info("created libp2p identity key file %s (32 bytes, mode 0600)", path)
    return kp
