"""Smoke tests for meshdevices CLI (help + print-ticket)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_meshdevices_help() -> None:
    r = subprocess.run(
        [sys.executable, "-m", "meshdevices", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "lm-chat" in r.stdout
    assert "print-ticket" in r.stdout


def test_meshdevices_lm_chat_help_includes_model() -> None:
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "meshdevices",
            "--config",
            str(ROOT / "examples" / "allowlist.example.toml"),
            "lm-chat",
            "--help",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "--model" in r.stdout


def test_meshdevices_print_ticket() -> None:
    cfg = ROOT / "examples" / "allowlist.example.toml"
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "meshdevices",
            "--config",
            str(cfg),
            "print-ticket",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    assert "PEER_ID=" in r.stdout
    assert "NODE_TICKET=" in r.stdout
    assert "node" in r.stdout.lower() or "12D3KooW" in r.stdout
