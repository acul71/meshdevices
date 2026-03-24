#!/usr/bin/env bash
# Deterministic libp2p/yamux smoke test using a local dummy LM HTTP server.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
MODEL="${MODEL:-nvidia/nemotron-3-nano-4b}"
WORKDIR="$(mktemp -d)"
PROMPT="${PROMPT:-Hello over libp2p}"

cleanup() {
  kill "${CLIENT_PID:-}" "${SERVER_PID:-}" "${DUMMY_PID:-}" 2>/dev/null || true
  wait "${CLIENT_PID:-}" "${SERVER_PID:-}" "${DUMMY_PID:-}" 2>/dev/null || true
  rm -rf "$WORKDIR"
}
trap cleanup EXIT

echo "workdir: $WORKDIR"
mkdir -p "$WORKDIR/identity"

cat > "$WORKDIR/client.toml" <<EOF
identity_key_file = "identity/client.key"
lm_studio_base = "http://127.0.0.1:18080"
allow_peer_ids = []
gossip_topic = "meshdevices/v1"
dht_mode = "client"
bootstrap = []
[peer_tickets]
EOF

"$PYTHON" -m meshdevices --config "$WORKDIR/client.toml" print-ticket > "$WORKDIR/client-ticket.txt" 2>&1
CLIENT_PEER="$(sed -n 's/^PEER_ID=//p' "$WORKDIR/client-ticket.txt")"
if [[ -z "$CLIENT_PEER" ]]; then
  echo "failed to obtain client peer id"
  exit 1
fi

cat > "$WORKDIR/server.toml" <<EOF
identity_key_file = "identity/server.key"
lm_studio_base = "http://127.0.0.1:18080"
allow_peer_ids = [ "$CLIENT_PEER" ]
bootstrap = []
gossip_topic = "meshdevices/v1"
dht_mode = "server"
[peer_tickets]
EOF

"$PYTHON" "$ROOT/scripts/dummy_lm_studio.py" > "$WORKDIR/dummy.log" 2>&1 &
DUMMY_PID=$!

"$PYTHON" -m meshdevices -v --config "$WORKDIR/server.toml" serve > "$WORKDIR/server.log" 2>&1 &
SERVER_PID=$!

for _ in $(seq 1 120); do
  if rg -n "meshdevices node up peer=" "$WORKDIR/server.log" >/dev/null 2>&1 && \
     rg -n "iroh NodeTicket \\(for peer_tickets" "$WORKDIR/server.log" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

SERVER_PEER="$(sed -n 's/.*meshdevices node up peer=//p' "$WORKDIR/server.log" | head -n1)"
TICKET="$(sed -n 's/.*iroh NodeTicket (for peer_tickets \/ dial-in): //p' "$WORKDIR/server.log" | tail -n1)"
if [[ -z "$SERVER_PEER" || -z "$TICKET" ]]; then
  echo "server did not publish peer/ticket"
  exit 1
fi

cat > "$WORKDIR/client.toml" <<EOF
identity_key_file = "identity/client.key"
lm_studio_base = "http://127.0.0.1:18080"
allow_peer_ids = []
gossip_topic = "meshdevices/v1"
dht_mode = "client"
bootstrap = [ "/p2p/$SERVER_PEER" ]
[peer_tickets]
"$SERVER_PEER" = "$TICKET"
EOF

echo "server peer: $SERVER_PEER"
echo "prompt: $PROMPT"

"$PYTHON" -m meshdevices -v --config "$WORKDIR/client.toml" lm-chat \
  --peer "$SERVER_PEER" --model "$MODEL" --prompt "$PROMPT" \
  > "$WORKDIR/client.out" 2> "$WORKDIR/client.err" &
CLIENT_PID=$!

wait "$CLIENT_PID"

echo "--- client output ---"
cat "$WORKDIR/client.out"
echo "--- client stderr ---"
cat "$WORKDIR/client.err"

if rg -n "DUMMY_ECHO:" "$WORKDIR/client.out" >/dev/null 2>&1; then
  echo "PASS: libp2p lm-chat received dummy response"
else
  echo "FAIL: no dummy response found"
  echo "--- server log tail ---"
  tail -n 60 "$WORKDIR/server.log" || true
  exit 1
fi
