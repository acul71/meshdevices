# Technical references

Working notes for stacks used by Mesh Devices: **local clone paths**, **docs links**, and **where to read code** first.

## Local checkouts (curriculum `Libp2p/` folder)

| Project | Typical path |
| ------- | ------------ |
| py-libp2p | `/home/luca/Informatica/Learning/PNL_Launchpad_Curriculum/Libp2p/py-libp2p` |
| iroh | `/home/luca/Informatica/Learning/PNL_Launchpad_Curriculum/Libp2p/iroh` |
| libp2p-iroh | `/home/luca/Informatica/Learning/PNL_Launchpad_Curriculum/Libp2p/libp2p-iroh` |

If you use the shorter home path `~/PNL_Launchpad_Curriculum/Libp2p/`, the same directory names apply.

**Note:** These trees are **not** vendored inside the `meshdevices` repository.

## Reading order

1. [iroh.md](iroh.md) — QUIC endpoint model (Rust).
2. [libp2p-iroh-bridge.md](libp2p-iroh-bridge.md) — how libp2p sits on iroh (Rust).
3. [py-libp2p.md](py-libp2p.md) — Python stack for actual prototypes.

## Rust vs Python

- **iroh** and **libp2p-iroh** are **Rust**. Use them for **architecture and spec alignment** (identity, transports, NAT story).
- **py-libp2p** is the **default implementation target** for Mesh Devices unless you introduce a Rust crate or sidecar later.
