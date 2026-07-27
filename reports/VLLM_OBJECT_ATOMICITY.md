# Object atomicity

The Python store uses temp write, flush/fsync, hash validation and atomic
replace. This is a protocol/unit capability, not evidence of real KV blocks.
