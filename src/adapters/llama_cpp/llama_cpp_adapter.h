/* SPDX-License-Identifier: AGPL-3.0-or-later */
#ifndef TW_LLAMA_CPP_ADAPTER_H
#define TW_LLAMA_CPP_ADAPTER_H
#include "../../runtime/timeweaver_runtime.h"
#ifdef __cplusplus
extern "C" {
#endif
int tw_llama_model_load(const char *model_path, tw_runtime_error *error);
int tw_llama_model_unload(tw_runtime_error *error);
int tw_llama_request_checkpoint(tw_runtime_manifest *manifest, tw_runtime_error *error);
int tw_llama_request_restore(const tw_runtime_manifest *manifest, tw_runtime_error *error);
#ifdef __cplusplus
}
#endif
#endif
