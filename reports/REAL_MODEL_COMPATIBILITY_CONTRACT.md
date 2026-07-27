# Compatibility contract

Restore is fail-closed on model/GGUF, tokenizer, chat template, runtime commit, adapter ABI, architecture, context/RoPE, quantization, LoRA, sequence, cursor, manifest version, size, or hash mismatch. Required errors include `MODEL_FINGERPRINT_MISMATCH`, `RUNTIME_VERSION_MISMATCH`, `TOKENIZER_MISMATCH`, `CONTEXT_CONFIGURATION_MISMATCH`, `STATE_HASH_MISMATCH`, `STATE_TRUNCATED`, and `UNSUPPORTED_CHECKPOINT_VERSION`.
