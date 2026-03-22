# MVP: iroh transport + py-libp2p

## Architecture

- **Wire:** [iroh](https://github.com/n0-computer/iroh) (Python bindings) provides QUIC, relays, and NAT traversal.
- **libp2p:** [py-libp2p](https://github.com/libp2p/py-libp2p) runs **Noise**, **yamux**, **GossipSub**, **Kademlia DHT**, and the **LM Studio proxy** stream protocol on top of a custom [`IrohTransport`](../src/meshdevices/transport/iroh_transport.py).
- **Allowlist:** Only configured **PeerIds** may use the LM proxy stream. When `allow_peer_ids` is non-empty, **GossipSub** messages on `gossip_topic` are rejected unless the sender is allowlisted ([`gossip_allowlist.py`](../src/meshdevices/gossip_allowlist.py) via `Pubsub.set_topic_validator`). See [`allowlist.example.toml`](../examples/allowlist.example.toml).
- **Orchestration:** **Kademlia DHT** (`KadDHT`) and **GossipSub** + **Pubsub** run on the same `BasicHost` as in py-libp2p examples ([`node.py`](../src/meshdevices/node.py)).

## Concurrency: trio only (application code)

Mesh Devices and py-libp2p use **trio**. iroh’s UniFFI layer is asyncio-based.

- [`iroh_uniffi_loop`](../src/meshdevices/iroh_loop.py) opens **[trio-asyncio](https://trio-asyncio.readthedocs.io/)**’s `open_loop()` and registers it with `uniffi_set_event_loop`.
- All iroh `await`s that run from **trio** tasks use [`await_iroh`](../src/meshdevices/iroh_loop.py) (`aio_as_trio`). The iroh `ProtocolHandler.accept` callback runs on the asyncio side of that same loop, so it uses plain `await conn.accept_bi()` there.

There is **no** separate `asyncio` thread in this repository.

## Security (Noise on top of iroh)

**Option B (current):** py-libp2p **Noise** runs on the iroh bidi stream. QUIC is already authenticated; Noise binds the connection to **libp2p PeerId** semantics. This is redundant on the wire but keeps the stock swarm/upgrader path.

## Run

Install py-libp2p from your checkout, then this package:

```bash
cd /path/to/Libp2p
pip install -e py-libp2p
pip install -e meshdevices
meshdevices --config meshdevices/examples/allowlist.example.toml serve
```

Commands: `serve` (default if omitted) runs the node; `print-ticket` prints `PEER_ID` and `NODE_TICKET` once; `lm-chat --peer <base58>` sends one OpenAI-style chat request over the LM proxy stream. Optional `identity_key_file` in TOML keeps the same libp2p PeerId across restarts (see [network-test.md](network-test.md)). Real-network steps: same doc.

Adjust `lm_studio_base` to your LM Studio OpenAI-compatible server. On startup, **serve** logs an **iroh NodeTicket** for dial-in. Share tickets out-of-band and add them under `[peer_tickets]` keyed by libp2p PeerId (base58) when `/p2p`-only dials are not enough.

The node listens with an **empty** `Multiaddr("")` (same idea as rust-libp2p-iroh’s `listen_on` empty addr); there is no `/iroh/...` protocol in the `multiaddr` crate.

## LM proxy protocol

- Protocol ID: `/meshdevices/lm-proxy/1.0.0`
- MVP payload: JSON body for `POST .../v1/chat/completions` (forwarded to `lm_studio_base`).
- Default chat JSON uses `model` from config `lm_studio_model`, or `meshdevices lm-chat --model …`, or the fallback `local-model` (see `DEFAULT_LM_STUDIO_MODEL` in [`config.py`](../src/meshdevices/config.py)).
