"""Regression test for lm-chat over libp2p/yamux with dummy LM backend."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "test-lm-chat-dummy.sh"


def test_lm_chat_dummy_network_path_completes() -> None:
    env = os.environ.copy()
    env["PYTHON"] = sys.executable
    env["MODEL"] = "nvidia/nemotron-3-nano-4b"
    env["PROMPT"] = "Regression hello"

    proc = subprocess.run(
        [str(SCRIPT)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = f"{proc.stdout}\n{proc.stderr}"
    assert proc.returncode == 0, out
    assert "PASS: libp2p lm-chat received dummy response" in out, out
    assert "DUMMY_ECHO: Regression hello" in out, out
