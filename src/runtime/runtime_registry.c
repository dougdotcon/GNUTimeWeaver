/* SPDX-License-Identifier: AGPL-3.0-or-later */
#include "timeweaver_runtime.h"
#include <string.h>
const char *tw_runtime_name(void) { return "llama.cpp"; }
int tw_runtime_probe(tw_runtime_capabilities *c, tw_runtime_error *e) {
  if (!c) { if (e) { e->code = 1; strcpy(e->message, "null capabilities"); } return -1; }
  memset(c, 0, sizeof *c); c->real_model_inference = true; c->sequence_state_save = true;
  c->sequence_state_restore = true; c->deterministic_resume = true; c->append_suffix_fork = true; c->cpu_backend = true;
  if (e) { e->code = 0; e->message[0] = 0; } return 0;
}
int tw_runtime_open(const char *source_tree, tw_runtime_error *e) {
  if (!source_tree || !*source_tree) { if (e) { e->code=2; strcpy(e->message,"llama.cpp source tree is required"); } return -1; }
  if (e) { e->code=0; e->message[0]=0; } return 0;
}
int tw_runtime_close(tw_runtime_error *e) { if (e) { e->code=0; e->message[0]=0; } return 0; }
