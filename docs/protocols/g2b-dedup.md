# G2-B1 deduplication

R0 is W0-E1, R1 is byte-identical W0-E1, R2 shares six blocks and branches on block seven, R3 has a different prefix. Reuse requires complete validation of magic, version, canonical header, lengths, payload and object checksums. Identity includes protocol, model/runtime/layout fingerprints, logical hash, group, layer, dtype, shape and payload hash. R1 must commit zero new objects and zero new payload bytes.
