# libp2p-iroh (libp2p transport on iroh)

## Local clone

- `/home/luca/Informatica/Learning/PNL_Launchpad_Curriculum/Libp2p/libp2p-iroh`

```bash
git clone https://github.com/rustonbsd/libp2p-iroh.git
```

## Docs

- [docs.rs/libp2p-iroh](https://docs.rs/libp2p-iroh)
- Crate README in repo: `README.md` (usage with `libp2p::kad`, `Swarm::listen_on` with empty multiaddr, dial by `/p2p/...`).

## What it implements

- **`libp2p::Transport`** from **rust-libp2p** (crates.io `libp2p`), backed by **iroh** QUIC, using iroh’s relay and NAT behavior.
- **Multiaddr:** peers addressed as `/p2p/<PeerId>`; transport maps between libp2p **`PeerId`** and iroh **`EndpointId`**.

## Source map (read in this order)

| File | Role |
| ---- | ---- |
| `src/lib.rs` | Re-exports: `Transport`, `Connection`, `Stream`; `TransportTrait` = `libp2p::Transport`. |
| `src/transport.rs` | `Transport` struct: holds `iroh::SecretKey`, `iroh::Endpoint`, `ProtocolActor`, libp2p transport event channels; implements dialing/listening. |
| `src/helper.rs` | `multiaddr_to_iroh_node_id`, `peer_id_to_node_id` (PeerId bytes → `EndpointId`), `libp2p_keypair_to_iroh_secret` (Ed25519). |
| `src/connection.rs` | libp2p connection object over iroh. |
| `src/stream.rs` | Stream bridging. |
| `examples/swarm_dht.rs` | Kademlia + swarm demo. |
| `examples/basic.rs` | Minimal usage. |

## Relation to Mesh Devices

Mesh Devices targets **py-libp2p**, not this crate. Use **libp2p-iroh** as a **reference** for:

- How **identity** is shared between libp2p and iroh-style stacks.
- Expectations for **NAT + relay** when comparing to py-libp2p’s transports and relay modules.

## Notes (fill as needed)

- Record version pins (`Cargo.toml`) if you compare behavior with a Rust libp2p swarm.
- Note any **wire / PeerId** interop constraints if you ever pair a py-libp2p node with a rust libp2p-iroh node.
