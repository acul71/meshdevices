"""Load TOML config (meshdevices)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

# Default OpenAI-style `model` id in generated lm-chat JSON when config does not set one.
DEFAULT_LM_STUDIO_MODEL = "qwen/qwen3.5-9b"


@dataclass
class MeshConfig:
    lm_studio_base: str
    allow_peer_ids: list[str]
    peer_tickets: dict[str, str]
    bootstrap: list[str]
    gossip_topic: str
    dht_mode: str  # "client" | "server"
    # Path to 32-byte Ed25519 seed file (created on first run). Resolved vs. config file dir.
    identity_key_file: str | None
    # OpenAI `model` id for lm-chat default JSON (e.g. qwen/qwen3.5-9b). None → DEFAULT_LM_STUDIO_MODEL.
    lm_studio_model: str | None


def load_config(path: Path) -> MeshConfig:
    data = tomllib.loads(path.read_text())
    return MeshConfig(
        lm_studio_base=str(data.get("lm_studio_base", "http://127.0.0.1:1234")),
        allow_peer_ids=list(data.get("allow_peer_ids", [])),
        peer_tickets=dict(data.get("peer_tickets", {})),
        bootstrap=list(data.get("bootstrap", [])),
        gossip_topic=str(data.get("gossip_topic", "meshdevices/v1")),
        dht_mode=str(data.get("dht_mode", "server")).lower(),
        identity_key_file=(
            str(data["identity_key_file"]) if data.get("identity_key_file") else None
        ),
        lm_studio_model=(
            str(data["lm_studio_model"]).strip()
            if data.get("lm_studio_model")
            else None
        )
        or None,
    )
