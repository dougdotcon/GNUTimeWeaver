# vLLM connector follow-up

Future v0.3 maps TimeWeaver manifests to KV Connector events: block hash/parent hash, token IDs, block size, cursor, refcount, eviction, scheduler safe points, and per-layer load/save. GPU requirements, connector versioning, and scheduler crash tests remain open. llama.cpp opaque state prepares provenance and compatibility, but does not substitute for block-native KV.
