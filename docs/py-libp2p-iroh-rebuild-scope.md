# Rebuilding "iroh-like" behavior with py-libp2p: realistic scope

This document answers two questions:

1. Can we build a stack similar to iroh using only py-libp2p?
2. For the current LM-Studio proxy use case, is py-libp2p redundant?

## Executive summary

- **You can build an iroh-like *application experience*** with py-libp2p.
- **You cannot cheaply rebuild full iroh transport ergonomics** (NAT traversal reliability, relay integration, path management) without significant networking work.
- For the current **LM proxy server-client** scope, the default recommendation is **iroh-only** because it is usually sufficient and simpler.
- Choose py-libp2p **only when** you explicitly need libp2p-native DHT/GossipSub semantics or interop with libp2p ecosystems.

## What py-libp2p can realistically provide

With py-libp2p only, you can build:

- peer identity and authenticated streams
- custom stream protocols (your LM proxy protocol)
- pub/sub (`GossipSub`)
- DHT-based discovery (`Kademlia`)
- QR bootstrap/tickets (app-defined encoding)

This is enough to implement a functional P2P LM proxy product.

## What is expensive to replicate from iroh

iroh includes transport/discovery behavior that is hard to reproduce with equivalent reliability:

- deterministic NAT traversal behavior across many NAT combinations
- integrated relay fallback and relay selection
- direct/relay path orchestration and maintenance
- dial-by-key ergonomics with discovery defaults

These are exactly the parts that tend to dominate operational effort in real WAN deployments.

## Minimum "iroh-like with py-libp2p" plan (sane v0)

If you still want to attempt a py-libp2p-only variant, keep scope strict.

### V0 (achievable)

- one protocol: `/meshdevices/lm-proxy/1.0.0`
- one bootstrap mechanism:
  - QR token containing `peer_id` + reachable addresses (or rendezvous URL)
- direct stream request/response, non-streaming body first
- optional allowlist
- clear timeout/error model

### V1 (moderate)

- add DHT discovery for server lookup
- add GossipSub announcement topic for "server online" messages
- refreshable QR/ticket flow

### V2 (hard)

- robust WAN NAT behavior comparable to iroh defaults
- relay strategy with failover and metrics
- connection-quality/path selection

Treat V2 as a separate networking project, not an "incremental feature."

## Is py-libp2p redundant for this repo's current LM proxy scope?

For today's scope (LM-Studio server + clients sending prompts):

- If your requirements are:
  - "connect reliably with minimal infra"
  - "QR/ticket bootstrap"
  - "request/response stream to LM server"
  then **iroh-only architecture is sufficient** and likely simpler.

- If your requirements include:
  - explicit libp2p DHT/GossipSub behavior
  - compatibility/interoperability with libp2p ecosystems
  - educational objective centered on libp2p overlays
  then py-libp2p remains justified.

So for pure LM proxy product delivery, py-libp2p is likely **more than necessary**.
For libp2p learning/interoperability goals, it is **not redundant**.

## Recommended strategy

1. Keep current implementation stable (already working).
2. Define a product-mode branch with iroh-first simplification criteria.
3. Remove py-libp2p only if all of these hold:
   - no hard dependency on libp2p protocol interop,
   - discovery requirements met by iroh services/tickets,
   - operational testing shows better reliability/complexity profile.

This avoids a large rewrite based on assumptions rather than measured outcomes.
