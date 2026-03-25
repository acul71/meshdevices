# `demo-lm-chat.sh` guide

This document explains:

- how to run the automated demo script (`scripts/demo-lm-chat.sh`)
- how to run the same LM proxy flow manually with shell commands
- how to run the client from another device (LAN)

## What the demo script does

`scripts/demo-lm-chat.sh` creates a temporary workspace, then:

1. creates a client identity and gets its PeerId
2. starts a temporary server node with that client in `allow_peer_ids`
3. discovers server PeerId + NodeTicket from server logs
4. writes a client config with bootstrap + `[peer_tickets]`
5. sends two `lm-chat` prompts and prints Question -> Answer

The default model is:

- `nvidia/nemotron-3-nano-4b`

Override with `MODEL=...` if needed.

## Run the script

From repo root:

```bash
cd /home/luca/Informatica/Learning/PNL_Launchpad_Curriculum/Libp2p/meshdevices
source .venv/bin/activate
./scripts/demo-lm-chat.sh
```

Useful options:

```bash
MODEL=nvidia/nemotron-3-nano-4b ./scripts/demo-lm-chat.sh
VERBOSE_DEMO=1 ./scripts/demo-lm-chat.sh
KEEP_DEMO_WORKDIR=1 VERBOSE_DEMO=1 ./scripts/demo-lm-chat.sh
LM_CHAT_TIMEOUT_S=900 ./scripts/demo-lm-chat.sh
```

## Manual run (same machine, no demo script)

Use three terminals.

### Terminal A: start server

```bash
cd /home/luca/Informatica/Learning/PNL_Launchpad_Curriculum/Libp2p/meshdevices
source .venv/bin/activate
python -m meshdevices -v --config server.toml serve
```

Copy from logs:

- `SERVER_PEER_ID` from `meshdevices node up peer=...`
- `SERVER_TICKET` from `iroh NodeTicket (for peer_tickets / dial-in): ...`

### Terminal B: get client PeerId

```bash
cd /home/luca/Informatica/Learning/PNL_Launchpad_Curriculum/Libp2p/meshdevices
source .venv/bin/activate
python -m meshdevices --config client.toml print-ticket
```

Copy:

- `CLIENT_PEER_ID` from `PEER_ID=...`

Add `CLIENT_PEER_ID` to `server.toml`:

```toml
allow_peer_ids = ["CLIENT_PEER_ID"]
```

Restart Terminal A server after editing.

Then set in `client.toml`:

```toml
bootstrap = ["/p2p/SERVER_PEER_ID"]

[peer_tickets]
"SERVER_PEER_ID" = "SERVER_TICKET"
```

### Terminal C: run prompts

```bash
cd /home/luca/Informatica/Learning/PNL_Launchpad_Curriculum/Libp2p/meshdevices
source .venv/bin/activate
python -m meshdevices -v --config client.toml lm-chat --peer SERVER_PEER_ID --model nvidia/nemotron-3-nano-4b --prompt "Hello"
```

```bash
cd /home/luca/Informatica/Learning/PNL_Launchpad_Curriculum/Libp2p/meshdevices
source .venv/bin/activate
python -m meshdevices -v --config client.toml lm-chat --peer SERVER_PEER_ID --model nvidia/nemotron-3-nano-4b --prompt "Write me a hello world in Python."
```

## Manual run (client from another device)

Scenario:

- server machine runs LM Studio + `meshdevices serve`
- client machine runs only `meshdevices lm-chat`

### 1) On server machine

Start server:

```bash
python -m meshdevices -v --config server.toml serve
```

Share with client machine:

- `SERVER_PEER_ID`
- `SERVER_TICKET`

### 2) On client machine

Create/read client identity once:

```bash
python -m meshdevices --config client.toml print-ticket
```

Share `CLIENT_PEER_ID` back to server machine, then add it to server allowlist:

```toml
allow_peer_ids = ["CLIENT_PEER_ID"]
```

Restart server after allowlist change.

Set client config:

```toml
bootstrap = ["/p2p/SERVER_PEER_ID"]

[peer_tickets]
"SERVER_PEER_ID" = "SERVER_TICKET"
```

Run chat from client machine:

```bash
python -m meshdevices --config client.toml lm-chat --peer SERVER_PEER_ID --model nvidia/nemotron-3-nano-4b --prompt "Hello"
```

## Notes

- `lm-chat` clients do not serve GossipSub/Kademlia protocols; seeing `/meshsub` or `/ipfs/kad` "not supported" noise on the server can be normal.
- If dialing fails after restart, refresh NodeTicket values (tickets can change when network paths change).
- Prefer `bash` or `./scripts/demo-lm-chat.sh` over `sh demo-lm-chat.sh` because the script uses Bash features.
