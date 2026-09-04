# G2-B — Transaction integrity and cross-request deduplication

Preparation only. G2-A remains frozen as `VLLM_KV_PAYLOAD_SAVE_VERIFIED_NO_RESTORE`; no load/restore is allowed. Gates are independent: B1 dedup, B2 fault injection, B3 crash/staging recovery, B4 final audit. Single writer, serial requests, one engine, one cache group.

Compatibility remains v0.4.0 because object/manifest identity and formats are unchanged; only store validation, journaling and recovery policy are prepared.
