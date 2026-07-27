# Safe-point semantics

Pause is cooperative only: after tokenization, prefill, generated token, agent step, or before a new suffix. No arbitrary kernel/layer pause is claimed. Checkpoints record safe point, cursor, sequence and generated count.
