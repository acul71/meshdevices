# Overview

**Mesh Devices** is a learning and design space focused on connecting personal devices (home, studio, mobile) over the internet **without relying on a traditional VPN or managed overlay** as the primary abstraction.

The concrete north star, as captured in the project prompt, is:

> **Replicate patterns like “run heavy workloads on one machine, use them from another,” using libp2p as the connection layer.**

That pattern shows up in many forms: remote inference, shared build hosts, file sync, or control of lab hardware. Today, people often reach for WireGuard, Tailscale, or similar to get stable reachability. This project asks: **what if libp2p (and related Rust networking stacks) carried that role instead?**

## Scope (for now)

- **In scope:** Reading upstream code and docs, sketching architectures, and eventually prototypes that exercise transports, discovery, and application protocols on top of libp2p.
- **In scope (concrete example):** The same *capability* people get from LM Studio’s remote setup (or from llama.cpp behind a VPN): **a user reaches a model running on another machine and can chat or call inference over that link**. Mesh Devices targets **libp2p as that link**—reachability and secure streams—while the model can still be served by **LM Studio, llama.cpp, vLLM, or any OpenAI-compatible HTTP API** on the “server” side, and the client can be a browser UI, a small custom app, or another tool that speaks the same protocol.

## Relationship to `PROMPT.md`

[`PROMPT.md`](../PROMPT.md) is the raw capture: links, a social-post transcription for context, and the one-line goal. These docs distill that into something you can navigate and extend as the repo grows.
