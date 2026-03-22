# Motivation

## The pattern people already use

A common setup looks like this:

1. **Compute** lives on a powerful or always-on machine (e.g. a workstation in a studio).
2. **Interaction** happens from a lighter device (e.g. a laptop or mini PC at home).
3. **Connectivity** is provided by a VPN or managed overlay so both sides see each other reliably.

In public write-ups, that stack often combines **local inference servers** (for example llama.cpp-style endpoints), **remote access**, and **tunneling** so the client can reach the server as if it were local. Managed overlays (Tailscale and similar) are popular because they reduce friction: keys, NAT traversal, and routing are handled for you.

## What changes with libp2p

libp2p emphasizes **peer identity, modular transports, and multiplexed streams** instead of “join this virtual LAN.” For mesh-style device connectivity, that can mean:

- Dialing **peers by cryptographic identity** rather than remembering which IP is current.
- Composing **QUIC, TCP, relays, and discovery** as needed for different networks.
- Building **application protocols** (request/response, pub/sub, etc.) on stable stream semantics.

The open question for this project is how close that comes—in ergonomics and reliability—to what VPN users expect, and where hybrid designs (libp2p for app traffic, something else for legacy sockets) still make sense.

## Attribution note

The original [`PROMPT.md`](../PROMPT.md) includes a transcription of a post by [Jeff Geerling](https://twitter.com/geerlingguy) describing remote LLM usage across machines with VPN/overlay-style connectivity. It is **motivation only**: this repository is not affiliated with those tools or posts; it uses the scenario to clarify the kind of “mesh device” problem we want to explore with libp2p.
