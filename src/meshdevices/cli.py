"""CLI entry: trio-only; iroh is bridged via trio-asyncio inside the node."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import trio

from meshdevices.config import DEFAULT_LM_STUDIO_MODEL, load_config
from meshdevices.identity_store import load_or_create_keypair, resolve_identity_key_path
from meshdevices.node import mesh_print_ticket, mesh_run_forever


def _extract_question_from_request(raw_request: bytes | None, fallback_prompt: str | None) -> str:
    if raw_request:
        try:
            payload = json.loads(raw_request.decode("utf-8"))
            msgs = payload.get("messages")
            if isinstance(msgs, list):
                for message in reversed(msgs):
                    if isinstance(message, dict) and message.get("role") == "user":
                        content = message.get("content")
                        if isinstance(content, str) and content.strip():
                            return content.strip()
        except Exception:
            pass
    if fallback_prompt and fallback_prompt.strip():
        return fallback_prompt.strip()
    return "(unknown)"


def _render_lm_chat_output(raw: bytes, *, question: str) -> None:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        # If backend returned non-JSON output, preserve behavior and print raw text.
        text = raw.decode("utf-8", errors="replace")
        print(text, end="" if text.endswith("\n") else "\n")
        return

    answer = ""
    reasoning = ""
    if isinstance(payload, dict):
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        answer = content.strip()
                    reason = message.get("reasoning_content")
                    if isinstance(reason, str):
                        reasoning = reason.strip()

    if not reasoning:
        reasoning = "_(not provided by model)_"
    if not answer:
        answer = "_(empty response)_"

    md = (
        f"# Question\n\n{question}\n\n"
        f"# Reasoning\n\n{reasoning}\n\n"
        f"# Answer\n\n{answer}\n"
    )

    try:
        from rich.console import Console
        from rich.markdown import Markdown

        Console().print(Markdown(md))
    except Exception:
        # Fallback keeps readable markdown if rich is unavailable.
        print(md, end="" if md.endswith("\n") else "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mesh Devices node (iroh + py-libp2p)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
        "  %(prog)s --config server.toml serve\n"
        "  %(prog)s --config client.toml lm-chat --peer 12D3KooW... --model qwen/qwen3.5-9b\n"
        "  %(prog)s --config server.toml print-ticket\n",
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to TOML config (see examples/allowlist.example.toml)",
    )
    parser.add_argument(
        "-v",
        "--debug",
        "--verbose",
        action="store_true",
        help="Enable debug logs and raw lm-chat JSON output",
    )
    sub = parser.add_subparsers(dest="command", required=False, metavar="COMMAND")
    sub.add_parser("serve", help="Run mesh node (default if COMMAND omitted)")
    p_chat = sub.add_parser("lm-chat", help="Send one OpenAI-style chat request via LM proxy stream")
    p_chat.add_argument(
        "--peer",
        required=True,
        help="Full remote libp2p PeerId (base58) from server log; not a shortened placeholder",
    )
    p_chat.add_argument(
        "--prompt",
        default="Say hello in one short sentence.",
        help="User message when not using --json-file",
    )
    p_chat.add_argument(
        "--json-file",
        type=Path,
        default=None,
        help="Raw HTTP body bytes for POST /v1/chat/completions (overrides --prompt)",
    )
    p_chat.add_argument(
        "--model",
        default=None,
        help=(
            "OpenAI model id for default JSON (overrides config lm_studio_model; "
            f"else {DEFAULT_LM_STUDIO_MODEL})"
        ),
    )
    sub.add_parser(
        "print-ticket",
        help="Print PEER_ID and NODE_TICKET once (uses identity_key_file if set)",
    )

    args = parser.parse_args()
    cmd = args.command or "serve"
    if args.debug:
        log_level = logging.DEBUG
    elif cmd == "lm-chat":
        log_level = logging.WARNING
    else:
        log_level = logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    cfg = load_config(args.config)

    def _resolve_kp():
        p = resolve_identity_key_path(cfg, args.config)
        if p is None:
            return None
        return load_or_create_keypair(p)

    kp = _resolve_kp()

    if cmd == "lm-chat":
        from meshdevices.lm_chat_client import peer_id_from_base58_cli, run_lm_chat

        try:
            peer_id_from_base58_cli(args.peer)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            raise SystemExit(2) from e

        body = args.json_file.read_bytes() if args.json_file else None

        async def _chat() -> bytes:
            return await run_lm_chat(
                cfg,
                peer_b58=args.peer,
                request_body=body,
                prompt=None if body else args.prompt,
                key_pair=kp,
                model_override=args.model,
            )

        raw = trio.run(_chat)
        if args.debug:
            sys.stdout.buffer.write(raw)
            if raw and not raw.endswith(b"\n"):
                sys.stdout.buffer.write(b"\n")
        else:
            question = _extract_question_from_request(raw_request=body, fallback_prompt=args.prompt)
            _render_lm_chat_output(raw, question=question)
        return

    if cmd == "print-ticket":

        async def _pt() -> None:
            await mesh_print_ticket(cfg, key_pair=kp)

        trio.run(_pt)
        return

    async def _serve() -> None:
        await mesh_run_forever(cfg, key_pair=kp)

    trio.run(_serve)


if __name__ == "__main__":
    main()
