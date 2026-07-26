#ifndef TIMEWEAVER_DEMO_AGENT_H
#define TIMEWEAVER_DEMO_AGENT_H

#include "timeweaver.h"

#define TW_DEMO_STATE_SIZE (16u * TW_PAGE_SIZE)

int tw_demo_seed(tw_store *store, uint64_t *failed_node, uint64_t *success_node);
int tw_demo_branch(tw_store *store, uint64_t source_node, const char *prompt,
                   uint64_t *fork_node, uint64_t *final_node);
int tw_demo_export_json(tw_store *store);

#endif
