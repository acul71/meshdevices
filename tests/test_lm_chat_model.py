"""lm-chat default JSON model resolution."""

from __future__ import annotations

import json

from meshdevices.config import DEFAULT_LM_STUDIO_MODEL, MeshConfig
from meshdevices.lm_chat_client import _default_chat_json


def test_default_chat_json_uses_model() -> None:
    raw = _default_chat_json("Hello", model="qwen/qwen3.5-9b")
    body = json.loads(raw.decode("utf-8"))
    assert body["model"] == "qwen/qwen3.5-9b"
    assert body["messages"][0]["content"] == "Hello"


def test_mesh_config_lm_studio_model_none_uses_constant_name() -> None:
    cfg = MeshConfig(
        lm_studio_base="http://127.0.0.1:1",
        allow_peer_ids=[],
        peer_tickets={},
        bootstrap=[],
        gossip_topic="t",
        dht_mode="server",
        identity_key_file=None,
        lm_studio_model=None,
    )
    m = None or cfg.lm_studio_model or DEFAULT_LM_STUDIO_MODEL
    assert m == DEFAULT_LM_STUDIO_MODEL
