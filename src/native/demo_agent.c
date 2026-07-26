#include "demo_agent.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DEMO_MAGIC 0x4757544du

typedef struct demo_header {
    uint32_t magic;
    uint32_t cursor;
    uint32_t status;
    uint32_t steps_executed;
    uint32_t prefix_steps_reused;
    uint32_t tokens_processed;
    char dialect[32];
    char last_action[64];
    char error[192];
} demo_header;

static demo_header *header(unsigned char *state) {
    return (demo_header *)state;
}

static char *prompt(unsigned char *state) {
    return (char *)(state + TW_PAGE_SIZE);
}

static char *response(unsigned char *state) {
    return (char *)(state + 2u * TW_PAGE_SIZE);
}

static char *schema(unsigned char *state) {
    return (char *)(state + 3u * TW_PAGE_SIZE);
}

static int contains_case_insensitive(const char *text, const char *needle) {
    size_t needle_size = strlen(needle);
    size_t i;
    if (!needle_size) return 1;
    for (; *text; ++text) {
        for (i = 0; i < needle_size; ++i) {
            if (!text[i] || tolower((unsigned char)text[i]) !=
                            tolower((unsigned char)needle[i])) break;
        }
        if (i == needle_size) return 1;
    }
    return 0;
}

static void write_kv_block(unsigned char *state, uint32_t step, const char *tag) {
    unsigned char *block = state + (4u + step) * TW_PAGE_SIZE;
    size_t tag_size = strlen(tag);
    size_t i;
    for (i = 0; i < TW_PAGE_SIZE; ++i) {
        block[i] = (unsigned char)(tag[i % tag_size] + (int)(i * 17u + step * 31u));
    }
}

static int checkpoint(tw_store *store, uint64_t parent, unsigned char *state,
                      const char *label, const char *note, tw_status status,
                      uint64_t *created) {
    return tw_snapshot(store, parent, label, note, state, TW_DEMO_STATE_SIZE,
                       header(state)->cursor, status, created);
}

static int execute_from(tw_store *store, uint64_t parent, unsigned char *state,
                        uint64_t *last_node) {
    demo_header *h = header(state);
    uint64_t node = parent;
    while (h->cursor < 5u) {
        uint32_t step = h->cursor;
        h->steps_executed++;
        h->tokens_processed += 128u + step * 37u;
        h->status = TW_STATUS_RUNNING;
        h->error[0] = '\0';
        switch (step) {
            case 0:
                snprintf(h->last_action, sizeof(h->last_action), "request parsed");
                write_kv_block(state, step, "intent");
                h->cursor = 1;
                if (checkpoint(store, node, state, "parse-request",
                               "Intent and constraints captured", TW_STATUS_SUCCESS,
                               &node) != 0) return -1;
                break;
            case 1:
                snprintf(schema(state), TW_PAGE_SIZE,
                         "engine=PostgreSQL; table=orders; columns=created_at,total");
                snprintf(h->last_action, sizeof(h->last_action), "schema loaded");
                write_kv_block(state, step, "schema");
                h->cursor = 2;
                if (checkpoint(store, node, state, "load-schema",
                               "Local database metadata checkpoint", TW_STATUS_SUCCESS,
                               &node) != 0) return -1;
                break;
            case 2:
                if (contains_case_insensitive(prompt(state), "postgres")) {
                    snprintf(h->dialect, sizeof(h->dialect), "postgresql");
                    snprintf(response(state), TW_PAGE_SIZE,
                             "SELECT date_trunc('month', created_at), sum(total) FROM orders GROUP BY 1");
                } else {
                    snprintf(h->dialect, sizeof(h->dialect), "mysql");
                    snprintf(response(state), TW_PAGE_SIZE,
                             "SELECT DATE_FORMAT(created_at, '%%Y-%%m'), sum(total) FROM orders GROUP BY 1");
                }
                snprintf(h->last_action, sizeof(h->last_action), "dialect selected");
                write_kv_block(state, step, h->dialect);
                h->cursor = 3;
                if (checkpoint(store, node, state, "choose-dialect",
                               h->dialect, TW_STATUS_SUCCESS, &node) != 0) return -1;
                break;
            case 3:
                write_kv_block(state, step, "execution");
                if (strcmp(h->dialect, "postgresql") != 0) {
                    snprintf(h->error, sizeof(h->error),
                             "syntax error: DATE_FORMAT is unavailable in PostgreSQL");
                    snprintf(h->last_action, sizeof(h->last_action), "query rejected");
                    h->status = TW_STATUS_ERROR;
                    if (checkpoint(store, node, state, "execute-query",
                                   h->error, TW_STATUS_ERROR, &node) != 0) return -1;
                    if (last_node) *last_node = node;
                    return 1;
                }
                snprintf(h->last_action, sizeof(h->last_action), "query executed");
                h->cursor = 4;
                if (checkpoint(store, node, state, "execute-query",
                               "Query accepted by local PostgreSQL validator",
                               TW_STATUS_SUCCESS, &node) != 0) return -1;
                break;
            case 4:
                snprintf(h->last_action, sizeof(h->last_action), "result delivered");
                write_kv_block(state, step, "delivery");
                h->cursor = 5;
                h->status = TW_STATUS_SUCCESS;
                if (checkpoint(store, node, state, "deliver-result",
                               "Agent completed without replaying the prefix",
                               TW_STATUS_SUCCESS, &node) != 0) return -1;
                break;
            default:
                return -1;
        }
    }
    if (last_node) *last_node = node;
    return 0;
}

int tw_demo_seed(tw_store *store, uint64_t *failed_node, uint64_t *success_node) {
    unsigned char *state;
    uint64_t root;
    uint64_t failure;
    tw_node source;
    size_t i;
    if (tw_node_count(store) != 0) return -1;
    state = (unsigned char *)calloc(1, TW_DEMO_STATE_SIZE);
    if (!state) return -1;
    header(state)->magic = DEMO_MAGIC;
    snprintf(prompt(state), TW_PAGE_SIZE,
             "Generate a monthly revenue report. Follow the legacy MySQL example.");
    snprintf(header(state)->last_action, sizeof(header(state)->last_action), "agent booted");
    if (checkpoint(store, 0, state, "boot", "Local agent memory initialized",
                   TW_STATUS_CHECKPOINT, &root) != 0 ||
        execute_from(store, root, state, &failure) < 0) {
        free(state);
        return -1;
    }
    if (failed_node) *failed_node = failure;
    for (i = 0; i < tw_node_count(store); ++i) {
        if (tw_get_node(store, i, &source) == 0 &&
            strcmp(source.label, "load-schema") == 0) break;
    }
    free(state);
    if (i == tw_node_count(store)) return -1;
    return tw_demo_branch(store, source.id,
                          "Generate monthly revenue SQL. Use PostgreSQL syntax.",
                          NULL, success_node);
}

int tw_demo_branch(tw_store *store, uint64_t source_node, const char *new_prompt,
                   uint64_t *fork_node, uint64_t *final_node) {
    unsigned char *state;
    size_t state_size;
    uint64_t forked;
    demo_header *h;
    int result;
    if (!new_prompt || !new_prompt[0]) return -1;
    state = (unsigned char *)malloc(TW_DEMO_STATE_SIZE);
    if (!state) return -1;
    if (tw_read_state(store, source_node, state, TW_DEMO_STATE_SIZE, &state_size) != 0 ||
        state_size != TW_DEMO_STATE_SIZE || header(state)->magic != DEMO_MAGIC) {
        free(state);
        return -1;
    }
    h = header(state);
    snprintf(prompt(state), TW_PAGE_SIZE, "%s", new_prompt);
    h->prefix_steps_reused = h->cursor < 2u ? h->cursor : 2u;
    if (h->cursor > 2u) h->cursor = 2u;
    h->status = TW_STATUS_FORK;
    h->dialect[0] = '\0';
    h->error[0] = '\0';
    response(state)[0] = '\0';
    snprintf(h->last_action, sizeof(h->last_action), "prompt mutated at fork");
    if (checkpoint(store, source_node, state, "fork",
                   "Prompt mutation; earlier KV pages retained", TW_STATUS_FORK,
                   &forked) != 0) {
        free(state);
        return -1;
    }
    if (fork_node) *fork_node = forked;
    result = execute_from(store, forked, state, final_node);
    free(state);
    return result < 0 ? -1 : 0;
}

static void json_string(const char *value) {
    const unsigned char *p = (const unsigned char *)value;
    putchar('"');
    while (*p) {
        switch (*p) {
            case '"': fputs("\\\"", stdout); break;
            case '\\': fputs("\\\\", stdout); break;
            case '\n': fputs("\\n", stdout); break;
            case '\r': fputs("\\r", stdout); break;
            case '\t': fputs("\\t", stdout); break;
            default:
                if (*p < 32) printf("\\u%04x", *p);
                else putchar(*p);
        }
        ++p;
    }
    putchar('"');
}

int tw_demo_export_json(tw_store *store) {
    tw_stats stats;
    size_t count = tw_node_count(store);
    size_t i;
    if (tw_get_stats(store, &stats) != 0) return -1;
    printf("{\"head\":%llu,\"stats\":{\"nodes\":%llu,\"physicalPages\":%llu,"
           "\"logicalPages\":%llu,\"sharedReferences\":%llu,"
           "\"physicalBytes\":%llu,\"naiveBytes\":%llu,\"savedRatio\":%.6f},\"nodes\":[",
           (unsigned long long)tw_head(store),
           (unsigned long long)stats.nodes,
           (unsigned long long)stats.physical_pages,
           (unsigned long long)stats.logical_pages,
           (unsigned long long)stats.shared_page_references,
           (unsigned long long)stats.physical_bytes,
           (unsigned long long)stats.naive_snapshot_bytes,
           stats.saved_ratio);
    for (i = 0; i < count; ++i) {
        tw_node node;
        unsigned char *state = (unsigned char *)malloc(TW_DEMO_STATE_SIZE);
        size_t state_size = 0;
        demo_header *h;
        uint32_t changed = 0;
        uint32_t page;
        tw_node parent;
        if (!state || tw_get_node(store, i, &node) != 0 ||
            tw_read_state(store, node.id, state, TW_DEMO_STATE_SIZE, &state_size) != 0) {
            free(state);
            return -1;
        }
        h = header(state);
        if (node.parent_id && tw_find_node(store, node.parent_id, &parent) == 0) {
            for (page = 0; page < node.page_count; ++page) {
                if (page >= parent.page_count || node.page_ids[page] != parent.page_ids[page]) changed++;
            }
        } else changed = node.page_count;
        if (i) putchar(',');
        printf("{\"id\":%llu,\"parentId\":%llu,\"createdNs\":%llu,"
               "\"cursor\":%u,\"status\":%u,\"stateHash\":\"%016llx\","
               "\"pages\":%u,\"changedPages\":%u,\"label\":",
               (unsigned long long)node.id, (unsigned long long)node.parent_id,
               (unsigned long long)node.created_ns, node.cursor, node.status,
               (unsigned long long)node.state_hash, node.page_count, changed);
        json_string(node.label);
        fputs(",\"note\":", stdout); json_string(node.note);
        fputs(",\"memory\":{\"prompt\":", stdout); json_string(prompt(state));
        fputs(",\"schema\":", stdout); json_string(schema(state));
        fputs(",\"dialect\":", stdout); json_string(h->dialect);
        fputs(",\"response\":", stdout); json_string(response(state));
        fputs(",\"error\":", stdout); json_string(h->error);
        printf(",\"stepsExecuted\":%u,\"prefixStepsReused\":%u,"
               "\"tokensProcessed\":%u}", h->steps_executed,
               h->prefix_steps_reused, h->tokens_processed);
        fputs("}", stdout);
        free(state);
    }
    fputs("]}\n", stdout);
    return 0;
}
