# Real object-store atomicity

The existing protocol requires temp write, flush/fsync, hash+size validation,
atomic rename, and node publication last. Fault-injection execution is pending.
