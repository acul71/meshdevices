#!/usr/bin/env bash
# Create .venv with uv and install meshdevices (editable, with dev extras).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv not found. Install: https://docs.astral.sh/uv/getting-started/installation/" >&2
  exit 1
fi

if [[ -d "$ROOT/.venv" ]]; then
  echo "Using existing venv: $ROOT/.venv"
else
  uv venv "$ROOT/.venv"
fi
uv pip install --python "$ROOT/.venv/bin/python" -e ".[dev]"

echo "Done. Activate: source \"$ROOT/.venv/bin/activate\""
