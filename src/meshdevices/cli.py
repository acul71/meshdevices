"""CLI entry: trio-only; iroh is bridged via trio-asyncio inside the node."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import trio

from meshdevices.config import DEFAULT_LM_STUDIO_MODEL, load_config
from meshdevices.identity_store import load_or_create_keypair, resolve_identity_key_path
from meshdevices.node import mesh_print_ticket, mesh_run_forever


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
        "--verbose",
        action="store_true",
        help="DEBUG logging",
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
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    cfg = load_config(args.config)
    cmd = args.command or "serve"

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
        sys.stdout.buffer.write(raw)
        if raw and not raw.endswith(b"\n"):
            sys.stdout.buffer.write(b"\n")
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
