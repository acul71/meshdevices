# Study resources

Read in this order: **iroh** (Rust networking model), **libp2p-iroh** (libp2p transport on iroh QUIC), then **py-libp2p** (what Mesh Devices will implement against).

Clones and the Python stack live **next to each other** under your `Libp2p/` curriculum folder—not inside the `meshdevices` git repo (keeps this repository small).

## Local layout

Typical absolute paths (use whichever matches your machine):

| Component | Path |
| --------- | ---- |
| **py-libp2p** | `/home/luca/Informatica/Learning/PNL_Launchpad_Curriculum/Libp2p/py-libp2p` (also: `/home/luca/PNL_Launchpad_Curriculum/Libp2p/py-libp2p` if you use the short tree) |
| **iroh** (clone) | `.../Libp2p/iroh` |
| **libp2p-iroh** (clone) | `.../Libp2p/libp2p-iroh` |

## Git clone (iroh + libp2p-iroh)

From the same directory that contains `py-libp2p`:

```bash
cd /home/luca/Informatica/Learning/PNL_Launchpad_Curriculum/Libp2p

git clone https://github.com/n0-computer/iroh.git
git clone https://github.com/rustonbsd/libp2p-iroh.git
```

Optional shallow clone for a quicker first checkout:

```bash
git clone --depth 1 https://github.com/n0-computer/iroh.git
git clone --depth 1 https://github.com/rustonbsd/libp2p-iroh.git
```

## Iroh (n0-computer)

- **Repository:** [github.com/n0-computer/iroh](https://github.com/n0-computer/iroh)
- **Docs:** [iroh.computer/docs](https://iroh.computer/docs), [docs.rs/iroh](https://docs.rs/iroh)
- **Tagline:** Dial by public key; QUIC via [noq](https://github.com/n0-computer/noq); hole-punching and relay fallback.
- **Why here:** Reference for how modern P2P stacks structure **endpoints**, **NodeId**, relays, and application **ALPN** protocols—useful even though Mesh Devices code will be Python-first.

## libp2p-iroh (rustonbsd)

- **Repository:** [github.com/rustonbsd/libp2p-iroh](https://github.com/rustonbsd/libp2p-iroh) (`main`)
- **Docs:** [docs.rs/libp2p-iroh](https://docs.rs/libp2p-iroh)
- **libp2p stack:** **[rust-libp2p](https://github.com/libp2p/rust-libp2p)** — the `libp2p` crate on crates.io (e.g. v0.56 in upstream `Cargo.toml`), not py-libp2p or Go/JS implementations.
- **Summary:** A **libp2p `Transport`** backed by **iroh QUIC** (NAT traversal and relay via iroh).
- **Why here:** Shows how **libp2p `PeerId` / multiaddr** map onto **iroh**—architecture reference, not the runtime you ship in Python.

## libp2p implementation for Mesh Devices: py-libp2p

- **Local checkout:** see table above.
- **Upstream:** [github.com/libp2p/py-libp2p](https://github.com/libp2p/py-libp2p)
- **Spec:** [docs.libp2p.io](https://docs.libp2p.io/)
- **Python API:** [py-libp2p.readthedocs.io](https://py-libp2p.readthedocs.io/)

**rust-libp2p** and **libp2p-iroh** are **Rust**; they inform design and interop expectations. **Implementation work** for this repo targets **py-libp2p** unless you add a Rust component later.

## Suggested reading flow

1. Skim **iroh** `README.md` and the docs site; note `Endpoint`, `connect`, QUIC streams, `ProtocolHandler`.
2. Open **libp2p-iroh** `README.md`, then trace `src/transport.rs` and `src/helper.rs` (PeerId ↔ iroh `EndpointId`).
3. In **py-libp2p**, map one user story to code: *“client opens a long-lived stream to a home peer for chat / proxy traffic.”*
   - Concepts: **Peer ID**, **multiaddr**, **transport** (TCP/QUIC/WebSocket per [feature table](https://github.com/libp2p/py-libp2p)), **Noise** (or TLS), **muxer**, **stream**, **protocol** handler.
   - Start under `libp2p/host/` (e.g. `basic_host.py`), `libp2p/network/swarm.py`, and the transport packages you enable for your prototype.

## Technical notes in this repo

Deeper pointers and placeholders live under [docs/technical/](technical/README.md) (`py-libp2p.md`, `iroh.md`, `libp2p-iroh-bridge.md`).
