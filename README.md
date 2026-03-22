# Mesh Devices

Exploring **peer-to-peer connectivity for personal and lab devices** using **libp2p**, with inspiration from modern Rust stacks like [iroh](https://github.com/n0-computer/iroh).

## Goal

Replicate workflows where **one machine runs heavy work** (inference, builds, services) and **another machine uses it remotely**—a pattern often solved today with VPNs or managed overlays—**using libp2p as the primary connection layer**.

## MVP (Python)

- **Stack:** [py-libp2p](https://github.com/libp2p/py-libp2p) (GossipSub, DHT, LM proxy) over an **iroh** Python transport (`IrohTransport`). Application concurrency is **trio**; **trio-asyncio** bridges iroh’s UniFFI layer (see [docs/mvp.md](docs/mvp.md)).
- **Install:** `pip install -e ../py-libp2p` then `pip install -e .` from this repo (Python 3.11+).
- **Run:** `meshdevices --config examples/allowlist.example.toml serve` (or omit `serve`). See [docs/network-test.md](docs/network-test.md) for LM Studio + two-node checks (`lm-chat`, tickets).

## Documentation

| Resource | Description |
| -------- | ----------- |
| [docs/](docs/README.md) | Project documentation (overview, motivation, study plan) |
| [docs/mvp.md](docs/mvp.md) | MVP architecture, trio + iroh bridge, runbook |
| [PROMPT.md](PROMPT.md) | Original brief, links, and raw context |

Suggested path: [docs/overview.md](docs/overview.md) → [docs/study-resources.md](docs/study-resources.md).

## Quick links

- [n0-computer/iroh](https://github.com/n0-computer/iroh) — modular Rust networking (“dial keys instead of IPs”)
- [rustonbsd/libp2p-iroh](https://github.com/rustonbsd/libp2p-iroh) — iroh QUIC as a libp2p transport

## Status

MVP code under `src/meshdevices/`; docs describe architecture and local curriculum clones.
