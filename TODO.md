# TODO

- [ ] **Identity key persistence:** After upstream `py-libp2p` supports configurable paths and stable formats for `save_keypair` / `load_keypair` (today they use a fixed `libp2p-forge/peer1/ed25519.pem` PEM path), consider switching `meshdevices.identity_store` from raw 32-byte files to those APIs—or a thin wrapper—so persistence stays aligned with libp2p while keeping iroh’s 32-byte secret derivation in sync.
