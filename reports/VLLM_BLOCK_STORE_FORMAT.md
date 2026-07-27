# Block store format

`kv3/objects`, `manifests` and `staging` use complete-only atomic publication,
SHA-256 payloads, restricted paths and no pickle. No real KV tensor payload has
been persisted.
