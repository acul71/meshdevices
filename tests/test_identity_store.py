"""Tests for persistent identity key files."""

from __future__ import annotations

import tempfile
from pathlib import Path

from libp2p import generate_peer_id_from

from meshdevices.config import MeshConfig
from meshdevices.identity_store import load_or_create_keypair, resolve_identity_key_path


def test_load_or_create_keypair_stable() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "k.key"
        a = load_or_create_keypair(p)
        b = load_or_create_keypair(p)
        assert generate_peer_id_from(a) == generate_peer_id_from(b)


def test_resolve_identity_key_path_relative() -> None:
    cfg = MeshConfig(
        lm_studio_base="http://127.0.0.1:1",
        allow_peer_ids=[],
        peer_tickets={},
        bootstrap=[],
        gossip_topic="t",
        dht_mode="server",
        identity_key_file="identity/x.key",
        lm_studio_model=None,
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".toml", delete=False, encoding="utf-8"
    ) as f:
        f.write("lm_studio_base = 'http://x'\n")
        config_path = Path(f.name)
    try:
        r = resolve_identity_key_path(cfg, config_path)
        assert r == config_path.parent / "identity" / "x.key"
    finally:
        config_path.unlink(missing_ok=True)
