"""--peer base58 validation for lm-chat."""

from __future__ import annotations

import pytest
from libp2p import generate_new_ed25519_identity, generate_peer_id_from

from meshdevices.lm_chat_client import peer_id_from_base58_cli


def test_peer_id_placeholder_rejected() -> None:
    with pytest.raises(ValueError, match="placeholder"):
        peer_id_from_base58_cli("12D3KooW...")


def test_peer_id_valid() -> None:
    pid = generate_peer_id_from(generate_new_ed25519_identity())
    got = peer_id_from_base58_cli(pid.to_base58())
    assert got == pid
