# Opaque runtime state object store

Runtime blobs belong under `runtime/objects/<sha256>.bin`, with manifests under `runtime/manifests`. The publication algorithm is temp write, flush/fsync, size+SHA-256 validation, atomic rename, then graph publication. Blobs are `opaque_runtime_state`, never `block_native_kv`; full-blob deduplication is not KV CoW.
