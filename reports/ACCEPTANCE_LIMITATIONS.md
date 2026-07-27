# Acceptance limitations

Status is `REAL_MODEL_BRIDGE_VERIFIED_WITH_LIMITATIONS`: CPU/Windows/MinGW
only, `GGML_CPU_REPACK=OFF`, opaque full-sequence state, no native KV block
introspection or CoW, no GPU/VRAM/zero-copy/vLLM, and incomplete exhaustive
compatibility/fuzz matrix. The 2048 run is supported by the model but not a
formal minimum requirement.
