#!/usr/bin/env bash
# Stop processes started by mesh-pair.sh (reads logs/mesh-server.pid and logs/mesh-client.pid).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
for name in mesh-server mesh-client; do
  f="logs/${name}.pid"
  if [[ -f "$f" ]]; then
    pid=$(cat "$f")
    if kill -0 "$pid" 2>/dev/null; then
      echo "Stopping $name (PID $pid)"
      kill "$pid" 2>/dev/null || true
    fi
    rm -f "$f"
  fi
done
echo "Done."
