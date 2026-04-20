# iroh vs libp2p-on-iroh: what iroh already gives you

This note answers two project questions:

1. If we use iroh as transport, did iroh already cover discovery / peer finding / gossip-like exchange?
2. Can we self-host relays with iroh?

Based on local iroh docs in `../docs.iroh.computer`.

## Short answer

- **iroh already covers a lot**: endpoint identity, encrypted connections, NAT traversal, relay fallback, discovery (DNS by default; optional local and DHT), tickets, and optional iroh-gossip protocol.
- **You can absolutely self-host relays** (or use managed dedicated relays).
- **iroh does not natively provide libp2p Kademlia + libp2p GossipSub semantics**. If you need those exact ecosystems/protocols, keeping libp2p on top is valid.

## What iroh already does (relevant to this project)

From docs:

- **Endpoint identity + dial by endpoint id** (`what-is-iroh`, `concepts/endpoints`, `concepts/discovery`).
- **NAT traversal + relay fallback** (`concepts/nat-traversal`, `concepts/relays`).
- **Discovery services** (`concepts/discovery`):
  - DNS discovery: enabled by default.
  - local and DHT discovery: optional/configurable.
- **Tickets** (`concepts/tickets`):
  - include endpoint id + relay/direct addr information.
  - useful bootstrap token, but can become stale as networks change.
- **Gossip option** via `iroh-gossip` (`connecting/gossip`), separate from libp2p GossipSub.

Implication: your original goal ("iroh should do the magic") is correct for connectivity and peer reachability in many scenarios.

## What iroh does *not* replace by default

If your design requires **libp2p-native** protocol behavior or compatibility, iroh alone is not equivalent:

- libp2p Kademlia DHT behavior/routing semantics
- GossipSub mesh scoring and topic behavior
- direct interoperability with other libp2p nodes speaking those protocol IDs

iroh has its own discovery and protocol stack; it is not "drop-in libp2p behavior."

## Decision framework for this repo

Use **iroh-only** if:

- primary goal is robust endpoint connectivity + simple protocol/RPC/data sync;
- you can use iroh discovery + tickets + optional iroh-gossip;
- interop with external libp2p protocol ecosystems is not required.

Keep **libp2p over iroh transport** if:

- you explicitly want libp2p DHT / GossipSub behavior;
- you need libp2p protocol compatibility with other libp2p deployments;
- your architecture already depends on those protocol contracts.

## Self-hosted relays: yes

Docs explicitly support:

- **public relays** (good for dev/test),
- **dedicated relays** (managed or self-hosted),
- custom relay configuration in endpoint builder,
- recommendation for at least two relays in different regions for redundancy.

See:

- `concepts/relays`
- `connecting/custom-relays`
- `deployment/dedicated-infrastructure`
- relay implementation: [iroh-relay](https://github.com/n0-computer/iroh/tree/main/iroh-relay)

## Practical recommendation for meshdevices

Current approach (iroh transport + py-libp2p) is technically coherent:

- iroh gives connectivity + traversal + relay fallback;
- libp2p layer gives DHT/GossipSub semantics and existing app structure.

If complexity/cost becomes too high, a future simplification path is:

1. keep iroh transport and endpoint identity as core,
2. replace libp2p DHT/GossipSub usage with iroh discovery + iroh-gossip where appropriate,
3. keep dedicated/self-hosted relays for production reliability.
