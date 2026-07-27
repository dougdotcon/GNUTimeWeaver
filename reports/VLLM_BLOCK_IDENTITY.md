# Block identity

`TimeWeaverKVBlockKey` canonicalizes identity fields and hashes canonical JSON
as a local stand-in until vLLM's exact `sha256_cbor` implementation is audited.
Runtime block IDs are never persistent identity.
