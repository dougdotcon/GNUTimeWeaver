# No-prefix-reprocessing evidence

The acceptance counters are tokenizer calls, tokens tokenized, decode calls, prefill tokens decoded, restored prefix tokens, prefix tokens decoded after restore, suffix tokens decoded, and generated tokens decoded. The required result is `prefix_tokens_decoded_after_restore == 0` and `prefix_tokens_restored == expected_prefix_tokens`. This repository has no GGUF execution yet; result is `REAL_MODEL_TEST_NOT_EXECUTED`.
