# Real object-store atomicity

Smoke state object SHA-256
`bfd17f7b0352b5c61ea87f0caaeec7442563d92b7278b9348f99f4a6465140d2`
was published after temp write, fsync, validation and atomic rename; the node was
last. Mid-write, before-rename, after-rename and before-node faults created no
node pointing to partial state. Orphan objects are permitted and reported.
