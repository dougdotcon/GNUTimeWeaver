# Preregistration — GNU TimeWeaver Real Model Bridge v0.2

Protocol ID: `timeweaver-real-model-bridge-v0.2:5e3c0592fba5c1a574e628d1ae4d93d5fb7794830a937ed4844b2705363d114c`

The frozen runtime target is llama.cpp, pinned by an externally supplied source tree and exact commit before execution. The adapter ABI is `tw-runtime-adapter/0.2`; checkpoints are `opaque_runtime_state` (sequence scope), stored content-addressed outside the v1 graph. Acceptance requires an actual GGUF, close/reopen, deterministic token comparison, fork immutability, fail-closed compatibility checks, and `prefix_tokens_decoded_after_restore == 0`. Missing runtime or `TIMEWEAVER_MODEL_PATH` yields `ADAPTER_PROTOCOL_READY_NO_REAL_MODEL`.

No weights are downloaded or committed. This preregistration does not claim KV block CoW, VRAM savings, GPU support, zero-copy restore, arbitrary kernel pause, or vLLM integration.
