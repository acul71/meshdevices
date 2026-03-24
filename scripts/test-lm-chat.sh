#!/usr/bin/env bash
# Run one LM proxy chat request (meshdevices lm-chat). Requires:
#   - LM Studio (or compatible) reachable from the *server* node's lm_studio_base
#   - Server meshdevices running with that config
#   - Client config with bootstrap + [peer_tickets] for the server, and server allowlist
#     including this client's PeerId (if allow_peer_ids is non-empty)
#
# Usage:
#   ./scripts/test-lm-chat.sh --peer 12D3KooW... [--config client.toml] [--prompt "Hello"] [--model qwen/qwen3.5-9b]
#   PEER=12D3KooW... MODEL=qwen/qwen3.5-9b ./scripts/test-lm-chat.sh
#
# Env: PYTHON, CONFIG (default client.toml), PEER (required), PROMPT, MODEL (optional → --model)

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"
CONFIG="${CONFIG:-client.toml}"
PEER="${PEER:-}"
PROMPT="${PROMPT:-Say hello in one short sentence.}"
MODEL="${MODEL:-nvidia/nemotron-3-nano-4b}"

usage() {
  sed -n '1,20p' "$0" | tail -n +2
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      CONFIG="$2"
      shift 2
      ;;
    --peer)
      PEER="$2"
      shift 2
      ;;
    --prompt)
      PROMPT="$2"
      shift 2
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    -h|--help)
      usage 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage 1
      ;;
  esac
done

if [[ -z "$PEER" ]]; then
  echo "error: set --peer <server libp2p PeerId base58> or PEER=..." >&2
  exit 1
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "error: config not found: $CONFIG (cwd: $ROOT)" >&2
  exit 1
fi

if ! "$PYTHON" -m meshdevices --help >/dev/null 2>&1; then
  echo "error: meshdevices not importable; run: pip install -e .  (PYTHON=$PYTHON)" >&2
  exit 1
fi

echo "lm-chat: config=$CONFIG peer=$PEER model=$MODEL"
echo "---"
extra=(--model "$MODEL")
"$PYTHON" -m meshdevices --config "$CONFIG" lm-chat --peer "$PEER" --prompt "$PROMPT" "${extra[@]}"
ec=$?
echo "---"
if [[ "$ec" -eq 0 ]]; then
  echo "OK (exit 0)"
else
  echo "Failed (exit $ec)" >&2
fi
exit "$ec"
