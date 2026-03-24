#!/usr/bin/env python3
"""Tiny OpenAI-compatible dummy for /v1/chat/completions and /v1/models."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    server_version = "dummy-lm-studio/0.1"

    def _json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[dummy-lm] {self.address_string()} - {fmt % args}")

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/v1/models":
            self._json(
                200,
                {
                    "data": [
                        {
                            "id": "nvidia/nemotron-3-nano-4b",
                            "object": "model",
                            "owned_by": "dummy",
                        }
                    ]
                },
            )
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self._json(404, {"error": "not found"})
            return

        raw_len = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(raw_len) if raw_len > 0 else b"{}"
        try:
            req = json.loads(raw.decode("utf-8"))
        except Exception:
            self._json(400, {"error": "invalid JSON"})
            return

        model = req.get("model", "nvidia/nemotron-3-nano-4b")
        messages = req.get("messages") or []
        prompt = ""
        if messages and isinstance(messages[-1], dict):
            prompt = str(messages[-1].get("content", ""))

        self._json(
            200,
            {
                "id": "chatcmpl-dummy",
                "object": "chat.completion",
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": f"DUMMY_ECHO: {prompt}",
                        },
                    }
                ],
            },
        )


def main() -> None:
    host = "127.0.0.1"
    port = 18080
    print(f"dummy-lm listening on http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
