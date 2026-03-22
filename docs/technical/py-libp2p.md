# py-libp2p

## Local checkout

- `/home/luca/Informatica/Learning/PNL_Launchpad_Curriculum/Libp2p/py-libp2p`
- Alternate: `/home/luca/PNL_Launchpad_Curriculum/Libp2p/py-libp2p`

## Canonical URLs

- [py-libp2p on ReadTheDocs](https://py-libp2p.readthedocs.io/)
- [Repository README (feature matrix)](https://github.com/libp2p/py-libp2p/blob/main/README.md)
- [libp2p concepts (spec)](https://docs.libp2p.io/)

## Feature matrix (see upstream README)

Transports include TCP, QUIC, WebSocket; NAT traversal includes circuit relay v2, AutoNAT, hole punching; security includes Noise; discovery includes bootstrap, mDNS, rendezvous; Kademlia DHT for peer routing. Confirm current status in the README table before relying on a module.

## First files to open (Mesh Devices angle)

Rough order for “dial peer, open stream, run app protocol”:

| Area | Path under `py-libp2p/libp2p/` |
| ---- | ------------------------------ |
| Host | `host/basic_host.py`, `host/routed_host.py`, `host/defaults.py` |
| Swarm / connections | `network/swarm.py`, `network/connection/swarm_connection.py` |
| Transports | `transport/tcp/`, `transport/quic/`, `transport/websocket/` (per your enabled stack) |
| Security | `security/noise/` (common choice) |
| Streams / protocols | follow examples under `examples/` and doc snippets on ReadTheDocs |

## Mesh Devices integration

- **Custom transport:** [`IrohTransport`](../../src/meshdevices/transport/iroh_transport.py) implements `ITransport` over the **iroh** Python package (QUIC), then the normal py-libp2p **Noise + yamux** stack runs on that byte pipe.
- **Trio only in app code:** py-libp2p and Mesh Devices use **trio**. iroh’s UniFFI layer expects an asyncio loop; we use **[trio-asyncio](https://trio-asyncio.readthedocs.io/)** (`open_loop` + `aio_as_trio` via [`await_iroh`](../../src/meshdevices/iroh_loop.py))—no free-standing `asyncio` thread in our code.

## Notes (fill as you prototype)

- **Inference / chat proxy:** decide whether the app speaks HTTP (OpenAI-compatible) over a libp2p stream, a custom framed protocol, or multiplexed substreams; record multiaddr and protocol IDs here.
- **Interop:** other peers may be Go/Rust libp2p; note codec (protobuf, length-prefixed) and protocol string matches.
