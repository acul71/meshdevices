# Real-network testing (LM Studio server + meshdevices clients)

This checklist follows the meshdevices MVP: iroh transport, libp2p stack, LM proxy on `/meshdevices/lm-proxy/1.0.0`, and `peer_tickets` for dialing when listen multiaddrs are not advertised.

## Phase 0 — Prerequisites

1. Install LM Studio; enable the **OpenAI-compatible** local server and note `lm_studio_base` (often `http://127.0.0.1:1234`).
2. Install **py-libp2p** (editable from your checkout if needed), then **meshdevices**: `pip install -e .` from this repo.
3. CLI commands used below:
   - `meshdevices --config FILE serve` — long-lived node (logs **libp2p PeerId** and **iroh NodeTicket** after startup).
   - `meshdevices --config FILE print-ticket` — prints `PEER_ID=` and `NODE_TICKET=` once (uses `identity_key_file` when set).
   - `meshdevices --config FILE lm-chat --peer SERVER_PEER_ID` — one chat request over the LM proxy stream to the server.

### Stable PeerId (`identity_key_file`)

**If this key is missing from your TOML, no file is created** — the node uses a random identity each run. Add it to enable persistence.

Without `identity_key_file`, each process generates a **new** libp2p key every run (bad for allowlists). Set in each TOML (path is **relative to the config file**):

```toml
identity_key_file = "identity/server.key"   # server
identity_key_file = "identity/client.key"   # client
```

On first run the file is created (32-byte Ed25519 seed, `0600`). **PeerId stays the same** across restarts. The **iroh NodeTicket** string may still change when network paths change; if the client cannot dial, refresh `[peer_tickets]` from the latest server log.

### Scripts: server + client + logs

From the repo root (with `server.toml` / `client.toml` already filled in):

```bash
./scripts/mesh-pair.sh server.toml client.toml   # backgrounds both; writes logs/mesh-server.log, logs/mesh-client.log
./scripts/mesh-tail.sh                           # follow both logs
./scripts/mesh-pair-stop.sh                      # stop PIDs from mesh-pair.sh
```

## Phase 1 — Single host (two terminals)

Use two config files — copy from [`examples/server.local.example.toml`](../examples/server.local.example.toml) and [`examples/client.local.example.toml`](../examples/client.local.example.toml) — and keep `identity_key_file` so PeerIds are stable.

1. **Terminal A — server**
   - Set `lm_studio_base` to LM Studio.
   - Set `dht_mode = "server"`.
   - Keep `identity_key_file` (e.g. `identity/server.key`).
   - Leave `allow_peer_ids` empty until you know the client PeerId, or restart after editing.
   - Run: `meshdevices --config server.local.toml serve`
   - Copy from logs: `meshdevices node up peer=<SERVER_PEER_ID>` and `iroh NodeTicket ...=<SERVER_TICKET>`.

2. **Terminal B — client**
   - Set `dht_mode = "client"` and `identity_key_file` (e.g. `identity/client.key`).
   - Set `bootstrap = ["/p2p/<SERVER_PEER_ID>"]` — must include the **`/p2p/`** prefix (not the raw PeerId string alone).
   - Under `[peer_tickets]`, add: `"<SERVER_PEER_ID>" = "<SERVER_TICKET>"` (use the full ticket string from the server log).
   - Run: `meshdevices --config client.local.toml serve`
   - Copy the client’s logged **PeerId** (not the ticket-only line).

3. **Allowlist**
   - Stop server (Ctrl+C), add the client’s base58 PeerId to server `allow_peer_ids`, save, restart server, then restart client if needed.

4. **LM proxy smoke**
   - With **server** still running (LM Studio up), in Terminal C:  
     `meshdevices --config client.toml lm-chat --peer <SERVER_PEER_ID> --prompt "Hello"`  
   - Or use the helper: [`scripts/test-lm-chat.sh`](../scripts/test-lm-chat.sh) —  
     `./scripts/test-lm-chat.sh --peer <SERVER_PEER_ID> [--config client.toml] [--prompt "Hello"]`  
   - Expect JSON from LM Studio on stdout (or an error if the model/path is wrong).

## Phase 2 — Two machines (LAN)

Same as Phase 1, but:

- Run **server** on the machine that runs LM Studio; run **client** on another host on the LAN.
- Allow **UDP** (QUIC) through host firewalls between the two machines.
- Exchange **PeerId** and **NodeTicket** securely (chat, USB, etc.); paste into configs as in Phase 1.

## Phase 3 — Internet / NAT

- Prefer **NodeTicket** strings in `[peer_tickets]`; iroh handles relay/NAT when needed.
- Expect higher latency; LM Studio timeouts are already large on the server ([`lm_proxy.py`](../src/meshdevices/lm_proxy.py)).

## Success criteria

- **Network:** Client completes `host.connect` to the server (bootstrap `/p2p/...` + server ticket).
- **LM path:** `lm-chat` returns a JSON body from the chat-completions API.
- **Policy (optional):** A peer not in `allow_peer_ids` gets the LM stream denied when the allowlist is non-empty.

## Troubleshooting

- **`No supported (IPv4+TCP or IPv6+TCP) addresses` / bootstrap noise:** Older meshdevices passed `bootstrap` into py-libp2p’s TCP-only `BootstrapDiscovery`. Current code sets `bootstrap=None` on `BasicHost` and dials `/p2p/...` peers only via `connect_to_bootstrap_peers` + `IrohTransport` + `[peer_tickets]`. Update meshdevices and retry.

- **`failed to negotiate the secure protocol`:** Often follows the above (no valid dial path). If it persists after a clean iroh dial, capture full logs with `meshdevices -v --config ...`.

## See also

- [mvp.md](mvp.md) — architecture and `peer_tickets` note.
