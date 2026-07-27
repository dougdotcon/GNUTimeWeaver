# Acceptance object-store atomicity

The 512-token Qwen state (6,298,200 bytes) was published as a SHA-256 object
after temporary write, fsync, validation and atomic rename. Faults at
mid-write, before rename, after rename and before node publish produced no
node referencing a partial object. The parent remained valid.
