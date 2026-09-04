# G2-B2 transaction model

Object and manifest states are `ABSENT → STAGING_CREATED → BYTES_WRITTEN → FILE_SYNCED → VALIDATED → RENAMED → DIRECTORY_SYNCED → COMMITTED`, with `QUARANTINED`, `ORPHANED` and `CORRUPT` diagnostics. Only COMMITTED objects may be referenced by a complete manifest. Journal format is `timeweaver-kv-transaction-journal/1`.
