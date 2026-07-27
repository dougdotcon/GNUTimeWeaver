/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "llama_cpp_adapter.h"
#include <cstring>
extern "C" int tw_llama_model_load(const char *p, tw_runtime_error *e) {
  if (!p || !*p) { if(e){e->code=10; std::strcpy(e->message,"MODEL_PATH_REQUIRED");} return -1; }
  if(e){e->code=0;e->message[0]=0;} return 0;
}
extern "C" int tw_llama_model_unload(tw_runtime_error *e){if(e){e->code=0;e->message[0]=0;}return 0;}
extern "C" int tw_llama_request_checkpoint(tw_runtime_manifest *m, tw_runtime_error *e){
  if(!m){if(e){e->code=11;std::strcpy(e->message,"CHECKPOINT_MANIFEST_REQUIRED");}return -1;}
  std::memset(m,0,sizeof *m); m->checkpoint_kind=TW_CHECKPOINT_OPAQUE_RUNTIME_STATE; m->safe_point_kind=TW_SAFE_AFTER_PREFILL;
  std::strcpy(m->adapter_abi_version,TW_RUNTIME_ADAPTER_ABI); if(e){e->code=12;std::strcpy(e->message,"LLAMA_CPP_SOURCE_NOT_LINKED");} return -1;
}
extern "C" int tw_llama_request_restore(const tw_runtime_manifest*,tw_runtime_error *e){if(e){e->code=12;std::strcpy(e->message,"LLAMA_CPP_SOURCE_NOT_LINKED");}return -1;}
