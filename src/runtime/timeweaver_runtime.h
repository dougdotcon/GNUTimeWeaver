/* SPDX-License-Identifier: AGPL-3.0-or-later */
#ifndef TIMEWEAVER_RUNTIME_H
#define TIMEWEAVER_RUNTIME_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define TW_RUNTIME_ADAPTER_ABI "tw-runtime-adapter/0.2"
typedef enum tw_checkpoint_kind { TW_CHECKPOINT_OPAQUE_RUNTIME_STATE = 1 } tw_checkpoint_kind;
typedef enum tw_safe_point_kind { TW_SAFE_AFTER_TOKENIZATION, TW_SAFE_AFTER_PREFILL,
  TW_SAFE_AFTER_GENERATED_TOKEN, TW_SAFE_AFTER_AGENT_STEP, TW_SAFE_BEFORE_NEW_SUFFIX } tw_safe_point_kind;
typedef struct tw_runtime_capabilities {
  bool real_model_inference, sequence_state_save, sequence_state_restore;
  bool deterministic_resume, append_suffix_fork, arbitrary_prefix_mutation;
  bool cpu_backend, gpu_backend, block_native_kv, zero_copy_restore;
} tw_runtime_capabilities;
typedef struct tw_runtime_error { int code; char message[256]; } tw_runtime_error;
typedef struct tw_runtime_manifest {
  char runtime_fingerprint[65], model_fingerprint[65], tokenizer_fingerprint[65];
  char adapter_abi_version[32], state_sha256[65];
  tw_checkpoint_kind checkpoint_kind; tw_safe_point_kind safe_point_kind;
  uint64_t token_cursor, sequence_id, generated_token_count, serialized_state_bytes;
} tw_runtime_manifest;
const char *tw_runtime_name(void);
int tw_runtime_probe(tw_runtime_capabilities *caps, tw_runtime_error *error);
int tw_runtime_open(const char *source_tree, tw_runtime_error *error);
int tw_runtime_close(tw_runtime_error *error);
#endif
