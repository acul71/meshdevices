#!/usr/bin/env bash
# Phase-1 helper: verifies CLI and prints the exact commands for two-terminal + lm-chat smoke.
# Does not start LM Studio or long-lived nodes (use two terminals per docs/network-test.md).

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
if ! "$PYTHON" -m meshdevices --help >/dev/null 2>&1; then
  echo "Run from repo with venv: pip install -e .  (PYTHON=$PYTHON)" >&2
  exit 1
fi

echo "OK: meshdevices CLI ($PYTHON -m meshdevices)"
echo ""
echo "Phase 1 (see docs/network-test.md):"
echo "  Terminal A: $PYTHON -m meshdevices --config examples/server.local.example.toml serve"
echo "  (edit server config: add client PeerId to allow_peer_ids; set lm_studio_base)"
echo "  Terminal B: $PYTHON -m meshdevices --config examples/client.local.example.toml serve"
echo "  (edit client: bootstrap /p2p/<server>, [peer_tickets] with server NodeTicket)"
echo "  Then:       $PYTHON -m meshdevices --config examples/client.local.example.toml lm-chat --peer SERVER_PEER_ID"
