#!/usr/bin/env bash
# Start meshdevices server and client in the background; append logs to logs/*.log
# Usage (from repo root, after configuring server.toml + client.toml):
#   ./scripts/mesh-pair.sh [server.toml] [client.toml]
# Monitor: ./scripts/mesh-tail.sh   or: tail -f logs/mesh-server.log logs/mesh-client.log
# Stop:    ./scripts/mesh-pair-stop.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
PYTHON="${PYTHON:-python3}"
SERVER_CFG="${1:-server.toml}"
CLIENT_CFG="${2:-client.toml}"

if [[ ! -f "$SERVER_CFG" ]]; then
  echo "Missing server config: $SERVER_CFG" >&2
  exit 1
fi
if [[ ! -f "$CLIENT_CFG" ]]; then
  echo "Missing client config: $CLIENT_CFG" >&2
  exit 1
fi

echo "Starting server ($SERVER_CFG) -> logs/mesh-server.log"
nohup "$PYTHON" -m meshdevices --config "$SERVER_CFG" serve >> logs/mesh-server.log 2>&1 &
echo $! > logs/mesh-server.pid

sleep 2

echo "Starting client ($CLIENT_CFG) -> logs/mesh-client.log"
nohup "$PYTHON" -m meshdevices --config "$CLIENT_CFG" serve >> logs/mesh-client.log 2>&1 &
echo $! > logs/mesh-client.pid

echo ""
echo "PIDs: server=$(cat logs/mesh-server.pid) client=$(cat logs/mesh-client.pid)"
echo "Monitor:  $ROOT/scripts/mesh-tail.sh"
echo "Stop:     $ROOT/scripts/mesh-pair-stop.sh"
