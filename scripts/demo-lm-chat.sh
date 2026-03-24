#!/usr/bin/env bash
# End-to-end demo: spawn meshdevices server, run two lm-chat prompts, print Q -> A report.
#
# Prerequisites:
#   - From repo root: pip install -e .
#   - LM Studio (or compatible) listening at LM_URL (default http://127.0.0.1:1234)
#
# Usage:
#   ./scripts/demo-lm-chat.sh
#   MODEL=nvidia/nemotron-3-nano-4b ./scripts/demo-lm-chat.sh
#
# qwen/qwen3.5-9b often spends 30–90s+ per reply (reasoning tokens); the terminal stays
# quiet until lm-chat returns — heartbeat lines on stderr every 15s mean it is not stuck.
#
# Env:
#   PYTHON   Python with meshdevices (default: .venv/bin/python if present, else python3)
#   MODEL    Optional --model for both lm-chat calls (otherwise config default)
#   LM_URL   Base URL written into generated configs (default http://127.0.0.1:1234)
#   KEEP_DEMO_WORKDIR  If set to 1, do not delete the temp directory (for debugging)
#   LM_CHAT_TIMEOUT_S  Per-request timeout for lm-chat (default 900). Requires GNU timeout(1).
#   PROMPT1 / PROMPT2   Override the two demo prompts
#   VERBOSE_DEMO=1      Pass -v to meshdevices; DEBUG logs go to server.log / *.err AND stderr (this terminal)

set -euo pipefail
export PYTHONUNBUFFERED=1
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
else
  PYTHON="${PYTHON:-python3}"
fi

LM_URL="${LM_URL:-http://127.0.0.1:1234}"
MODEL="${MODEL:-nvidia/nemotron-3-nano-4b}"
KEEP_DEMO_WORKDIR="${KEEP_DEMO_WORKDIR:-0}"
LM_CHAT_TIMEOUT_S="${LM_CHAT_TIMEOUT_S:-900}"

PROMPT1="${PROMPT1:-Hello}"
PROMPT2="${PROMPT2:-Write me a hello world in Python.}"
VERBOSE_DEMO="${VERBOSE_DEMO:-0}"
VERBOSE_FLAG=()
if [[ "$VERBOSE_DEMO" == "1" ]]; then
  VERBOSE_FLAG=(-v)
fi

if ! "$PYTHON" -m meshdevices --help >/dev/null 2>&1; then
  echo "error: meshdevices not importable; run: pip install -e .  (PYTHON=$PYTHON)" >&2
  exit 1
fi

WORKDIR=$(mktemp -d)
cleanup() {
  if [[ -n "${SERVER_PID:-}" ]]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  if [[ "$KEEP_DEMO_WORKDIR" != "1" ]]; then
    rm -rf "$WORKDIR"
  else
    echo "" >&2
    echo "KEEP_DEMO_WORKDIR=1: left files in $WORKDIR" >&2
  fi
}
trap cleanup EXIT

cd "$WORKDIR"
mkdir -p identity

# --- Client identity + PeerId for server allowlist ---
cat > client.toml <<EOF
identity_key_file = "identity/client.key"
lm_studio_base = "$LM_URL"
allow_peer_ids = []
gossip_topic = "meshdevices/v1"
dht_mode = "client"
bootstrap = []
[peer_tickets]
EOF

"$PYTHON" -m meshdevices --config client.toml print-ticket > print-ticket.out 2>&1
CLIENT_PEER=$(grep '^PEER_ID=' print-ticket.out | cut -d= -f2)
if [[ -z "$CLIENT_PEER" ]]; then
  echo "error: could not get PEER_ID from print-ticket" >&2
  cat print-ticket.out >&2
  exit 1
fi

# --- Server config (allow this client only) ---
cat > server.toml <<EOF
identity_key_file = "identity/server.key"
lm_studio_base = "$LM_URL"
allow_peer_ids = [ "$CLIENT_PEER" ]
bootstrap = []
gossip_topic = "meshdevices/v1"
dht_mode = "server"
[peer_tickets]
EOF

echo "== meshdevices lm-chat demo =="
echo "Workdir: $WORKDIR"
echo "Client PeerId (allowlisted on server): $CLIENT_PEER"
echo ""
if [[ "$VERBOSE_DEMO" == "1" ]]; then
  echo "VERBOSE_DEMO=1: DEBUG from server + lm-chat is copied to this terminal (and still saved under the workdir)." >&2
fi

# Without tee, -v DEBUG only lands in server.log / *.err — easy to miss. With VERBOSE_DEMO, tee duplicates to stderr.
if [[ "$VERBOSE_DEMO" == "1" ]]; then
  "$PYTHON" "${VERBOSE_FLAG[@]}" -m meshdevices --config server.toml serve > >(tee server.log) 2>&1 &
else
  "$PYTHON" "${VERBOSE_FLAG[@]}" -m meshdevices --config server.toml serve > server.log 2>&1 &
fi
SERVER_PID=$!

for _ in $(seq 1 120); do
  if grep -q "iroh NodeTicket (for peer_tickets" server.log 2>/dev/null \
    && grep -q "meshdevices node up peer=" server.log 2>/dev/null; then
    break
  fi
  sleep 0.5
done

if ! grep -q "meshdevices node up peer=" server.log 2>/dev/null; then
  echo "error: server did not become ready in time. Log:" >&2
  cat server.log >&2
  exit 1
fi

SERVER_PEER=$(grep "meshdevices node up peer=" server.log | head -1 | sed -n 's/.*peer=//p')
TICKET=$(grep "iroh NodeTicket (for peer_tickets" server.log | tail -1 | sed -n 's/.*: //p' | tr -d '\r' | sed 's/[[:space:]]*$//')

if [[ -z "$SERVER_PEER" || -z "$TICKET" ]]; then
  echo "error: could not parse server PeerId or NodeTicket" >&2
  cat server.log >&2
  exit 1
fi

echo "Server PeerId: $SERVER_PEER"
echo ""

# --- Client config for lm-chat ---
cat > client.toml <<EOF
identity_key_file = "identity/client.key"
lm_studio_base = "$LM_URL"
allow_peer_ids = []
gossip_topic = "meshdevices/v1"
dht_mode = "client"
bootstrap = [ "/p2p/$SERVER_PEER" ]
[peer_tickets]
"$SERVER_PEER" = "$TICKET"
EOF

run_chat() {
  local prompt=$1
  local out=$2
  local -a extra=()
  if [[ -n "$MODEL" ]]; then
    extra=(--model "$MODEL")
  fi
  set +e
  if command -v timeout >/dev/null 2>&1; then
    if [[ "$VERBOSE_DEMO" == "1" ]]; then
      timeout "$LM_CHAT_TIMEOUT_S" "$PYTHON" "${VERBOSE_FLAG[@]}" -m meshdevices --config client.toml lm-chat \
        --peer "$SERVER_PEER" --prompt "$prompt" "${extra[@]}" > "$out" 2> >(tee "${out}.err" >&2) &
    else
      timeout "$LM_CHAT_TIMEOUT_S" "$PYTHON" "${VERBOSE_FLAG[@]}" -m meshdevices --config client.toml lm-chat \
        --peer "$SERVER_PEER" --prompt "$prompt" "${extra[@]}" > "$out" 2> "${out}.err" &
    fi
  else
    if [[ "$VERBOSE_DEMO" == "1" ]]; then
      "$PYTHON" "${VERBOSE_FLAG[@]}" -m meshdevices --config client.toml lm-chat \
        --peer "$SERVER_PEER" --prompt "$prompt" "${extra[@]}" > "$out" 2> >(tee "${out}.err" >&2) &
    else
      "$PYTHON" "${VERBOSE_FLAG[@]}" -m meshdevices --config client.toml lm-chat \
        --peer "$SERVER_PEER" --prompt "$prompt" "${extra[@]}" > "$out" 2> "${out}.err" &
    fi
  fi
  local pid=$!
  (
    local w=0
    while kill -0 "$pid" 2>/dev/null; do
      sleep 15
      kill -0 "$pid" 2>/dev/null || exit 0
      w=$((w + 15))
      echo "    … ${w}s elapsed, still waiting (LM Studio + libp2p; qwen3.5 reasoning can be 30–120s/turn) …" >&2
    done
  ) &
  local hb=$!
  wait "$pid"
  local ec=$?
  kill "$hb" 2>/dev/null || true
  wait "$hb" 2>/dev/null || true
  set -e
  return "$ec"
}

extract_answer() {
  local file=$1
  "$PYTHON" - "$file" <<'PY'
import json, sys
from json import JSONDecoder

path = sys.argv[1]
raw = open(path, "rb").read()
text = raw.decode(errors="replace")

def parse_first_json_object(s: str):
    dec = JSONDecoder()
    for i, ch in enumerate(s):
        if ch != "{":
            continue
        try:
            obj, _ = dec.raw_decode(s, i)
            return obj
        except Exception:
            continue
    return None

try:
    d = parse_first_json_object(text)
    if d is None:
        raise ValueError("no JSON object found in output")
    msg = d["choices"][0]["message"]
    c = (msg.get("content") or "").strip()
    r = (msg.get("reasoning_content") or "").strip()
    if r and len(r) > 400:
        r = r[:400] + "…"
    if c:
        print(c)
    elif r:
        print("(no content; reasoning excerpt)\n" + r)
    else:
        print(text[:2000])
except Exception as e:
    print("__parse_error__", e)
    print(text[:4000])
PY
}

echo "-------------------------------------------------------------------"
echo "Conversation (libp2p LM proxy -> LM Studio)"
echo "Each turn stays silent until done; stderr shows a line every 15s while waiting."
echo "Reasoning models (e.g. qwen3.5-9b) often need 30–120s per prompt — use a smaller"
echo "MODEL=… for a snappier demo."
echo "-------------------------------------------------------------------"

ANS1=$(mktemp)
ANS2=$(mktemp)
ERR1="${ANS1}.err"
ERR2="${ANS2}.err"

ec1=0
ec2=0
echo ""
echo "[1] Question: $PROMPT1"
echo "    (waiting — first output below is the answer when ready)" >&2
run_chat "$PROMPT1" "$ANS1" || ec1=$?
echo "    Answer:"
if [[ "$ec1" -eq 0 ]]; then
  extract_answer "$ANS1" | sed 's/^/    /'
elif [[ "$ec1" -eq 124 ]]; then
  echo "    (timed out after ${LM_CHAT_TIMEOUT_S}s — set LM_CHAT_TIMEOUT_S or use a smaller/faster MODEL)" >&2
  cat "$ERR1" >&2 || true
else
  echo "    (failed, exit $ec1)" >&2
  cat "$ERR1" >&2 || true
  cat "$ANS1" >&2 || true
fi

echo ""
echo "[2] Question: $PROMPT2"
echo "    (waiting — first output below is the answer when ready)" >&2
run_chat "$PROMPT2" "$ANS2" || ec2=$?
echo "    Answer:"
if [[ "$ec2" -eq 0 ]]; then
  extract_answer "$ANS2" | sed 's/^/    /'
elif [[ "$ec2" -eq 124 ]]; then
  echo "    (timed out after ${LM_CHAT_TIMEOUT_S}s — set LM_CHAT_TIMEOUT_S or use a smaller/faster MODEL)" >&2
  cat "$ERR2" >&2 || true
else
  echo "    (failed, exit $ec2)" >&2
  cat "$ERR2" >&2 || true
  cat "$ANS2" >&2 || true
fi

echo ""
echo "-------------------------------------------------------------------"
if [[ "$ec1" -ne 0 || "$ec2" -ne 0 ]]; then
  echo "Demo finished with errors (lm-chat exit: $ec1, $ec2)." >&2
  exit 1
fi
echo "Demo finished OK."
exit 0
