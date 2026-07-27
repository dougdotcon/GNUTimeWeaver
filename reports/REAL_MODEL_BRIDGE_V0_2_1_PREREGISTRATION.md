# Real Model Bridge v0.2.1 preregistration

Protocol ID: `timeweaver-real-model-bridge-v0.2.1:0a3f090dbd76c9d9de0e1e9f7cf3f1d2e9a9ed9b0ef14a0c46c9ecb8fd955a69`

Runtime is fixed to llama.cpp b10103, commit `c588c4f`, CPU backend, clean source tree. Smoke (`stories15M-q4_0.gguf`) is diagnostic only; acceptance (`qwen2.5-coder-0.5b-q8_0.gguf`) alone can promote status. Both require explicit `TIMEWEAVER_MODEL_PATH`; no download is performed. Greedy sampling, temperature 0, seed 42, sequence-state APIs, and zero prefix tokenizer/decode calls after restore are frozen criteria.

Current execution is blocked only by missing `TIMEWEAVER_LLAMA_CPP_DIR` and GGUF. Therefore no real result is reported.
