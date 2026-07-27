# Long-prefix sequence state

Acceptance results (separate checkpoint and restore processes):

| Prefix | State bytes | Restored positions | Zero prefix tokenizer/decode | Greedy equal |
|---:|---:|---:|---:|:---:|
| 512 | 6,298,200 | 0..511 | yes / yes | yes |
| 1024 | 12,595,800 | 0..1023 | yes / yes | yes |
| 2048 | 25,191,000 | 0..2047 | yes / yes | yes |
