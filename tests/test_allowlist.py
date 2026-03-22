"""Unit tests for allowlist and config."""

from __future__ import annotations

from pathlib import Path
import tempfile

from libp2p import generate_new_ed25519_identity, generate_peer_id_from
from libp2p.peer.id import ID
from libp2p.pubsub.pb import rpc_pb2

from meshdevices.allowlist import PeerAllowlist
from meshdevices.config import load_config
from meshdevices.gossip_allowlist import gossip_allowlist_sync_validator


def _two_peer_ids() -> tuple[ID, ID]:
    a = generate_peer_id_from(generate_new_ed25519_identity())
    b = generate_peer_id_from(generate_new_ed25519_identity())
    return a, b


def test_peer_allowlist_contains_base58() -> None:
    pid, _ = _two_peer_ids()
    allow = PeerAllowlist.from_strings([pid.to_base58()])
    assert pid.to_base58() in allow
    assert pid in allow


def test_gossip_validator_accepts_allowlisted() -> None:
    pid, _ = _two_peer_ids()
    allow = PeerAllowlist.from_strings([pid.to_base58()])
    v = gossip_allowlist_sync_validator(allow)
    msg = rpc_pb2.Message(from_id=pid.to_bytes(), data=b"hi", topicIDs=["meshdevices/v1"])
    assert v(None, msg) is True


def test_gossip_validator_rejects_other() -> None:
    allowed, other = _two_peer_ids()
    allow = PeerAllowlist.from_strings([allowed.to_base58()])
    v = gossip_allowlist_sync_validator(allow)
    msg = rpc_pb2.Message(from_id=other.to_bytes(), data=b"hi", topicIDs=["t"])
    assert v(None, msg) is False


def test_load_config_toml() -> None:
    pid = generate_peer_id_from(generate_new_ed25519_identity())
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".toml", delete=False, encoding="utf-8"
    ) as f:
        f.write(
            'lm_studio_base = "http://127.0.0.1:1"\n'
            f'allow_peer_ids = ["{pid.to_base58()}"]\n'
            'gossip_topic = "t"\n'
        )
        path = Path(f.name)
    try:
        cfg = load_config(path)
        assert cfg.lm_studio_base == "http://127.0.0.1:1"
        assert len(cfg.allow_peer_ids) == 1
        assert cfg.gossip_topic == "t"
    finally:
        path.unlink(missing_ok=True)


def test_load_config_lm_studio_model() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".toml", delete=False, encoding="utf-8"
    ) as f:
        f.write(
            'lm_studio_base = "http://127.0.0.1:1"\n'
            'lm_studio_model = "qwen/qwen3.5-9b"\n'
        )
        path = Path(f.name)
    try:
        cfg = load_config(path)
        assert cfg.lm_studio_model == "qwen/qwen3.5-9b"
    finally:
        path.unlink(missing_ok=True)
