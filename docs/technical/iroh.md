# iroh

## Local clone

- `/home/luca/Informatica/Learning/PNL_Launchpad_Curriculum/Libp2p/iroh`

Clone command (from `Libp2p/`):

```bash
git clone https://github.com/n0-computer/iroh.git
```

## Docs

- Site: [iroh.computer/docs](https://iroh.computer/docs)
- Rust API: [docs.rs/iroh](https://docs.rs/iroh)

## Concepts to track (from upstream README)

- **Dial by key:** API centers on connecting to a remote identity rather than pinning IPs.
- **QUIC:** Built on QUIC (authenticated encryption, bidirectional streams, datagrams).
- **NAT:** Hole-punching when possible; relay ecosystem as fallback.
- **Application protocols:** ALPN strings; `Endpoint::bind`, `connect`, `ProtocolHandler`, `Router` pattern in examples.

## Notes (fill while reading)

- Map **iroh `NodeId` / `EndpointId`** to how you think about **libp2p `PeerId`** in py-libp2p (see [libp2p-iroh-bridge.md](libp2p-iroh-bridge.md) for the Rust mapping code).
- List any **crates** you rely on for deeper reading (e.g. main `iroh` crate layout under `iroh/` in the repo).
