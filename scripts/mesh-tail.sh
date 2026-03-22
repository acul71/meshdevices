#!/usr/bin/env bash
# Follow server + client logs (Ctrl+C stops tail only, not meshdevices).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec tail -f logs/mesh-server.log logs/mesh-client.log
