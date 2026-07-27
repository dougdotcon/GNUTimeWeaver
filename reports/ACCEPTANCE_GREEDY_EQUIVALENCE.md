# Acceptance greedy equivalence

With temperature 0 and greedy sampling, all 16 continuation token IDs matched
between checkpoint-process reference and restore-process continuation for
prefixes 512, 1024 and 2048. Cursor and positions matched; no stop divergence
was observed in the 16-token window.
