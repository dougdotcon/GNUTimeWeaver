#ifndef TIMEWEAVER_H
#define TIMEWEAVER_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define TW_PAGE_SIZE 4096u
#define TW_MAX_LOGICAL_PAGES 128u
#define TW_MAX_NODES 2048u
#define TW_LABEL_SIZE 64u
#define TW_NOTE_SIZE 192u

typedef enum tw_status {
    TW_STATUS_CHECKPOINT = 0,
    TW_STATUS_RUNNING = 1,
    TW_STATUS_SUCCESS = 2,
    TW_STATUS_ERROR = 3,
    TW_STATUS_FORK = 4
} tw_status;

typedef struct tw_node {
    uint64_t id;
    uint64_t parent_id;
    uint64_t created_ns;
    uint64_t state_hash;
    uint32_t state_size;
    uint32_t page_count;
    uint32_t cursor;
    uint32_t status;
    uint32_t page_ids[TW_MAX_LOGICAL_PAGES];
    char label[TW_LABEL_SIZE];
    char note[TW_NOTE_SIZE];
} tw_node;

typedef struct tw_stats {
    uint64_t nodes;
    uint64_t physical_pages;
    uint64_t logical_pages;
    uint64_t shared_page_references;
    uint64_t physical_bytes;
    uint64_t naive_snapshot_bytes;
    double saved_ratio;
} tw_stats;

typedef struct tw_store tw_store;

int tw_open(tw_store **out, const char *directory, int create);
void tw_close(tw_store *store);
const char *tw_last_error(const tw_store *store);

int tw_snapshot(tw_store *store, uint64_t parent_id, const char *label,
                const char *note, const void *state, size_t state_size,
                uint32_t cursor, tw_status status, uint64_t *node_id);
int tw_read_state(tw_store *store, uint64_t node_id, void *state,
                  size_t capacity, size_t *state_size);
int tw_get_page_view(const tw_store *store, uint64_t node_id,
                     uint32_t logical_page, const void **data,
                     size_t *data_size, uint32_t *physical_page);
int tw_checkout(tw_store *store, uint64_t node_id);
uint64_t tw_head(const tw_store *store);

size_t tw_node_count(const tw_store *store);
int tw_get_node(const tw_store *store, size_t index, tw_node *node);
int tw_find_node(const tw_store *store, uint64_t node_id, tw_node *node);
int tw_get_stats(const tw_store *store, tw_stats *stats);
int tw_validate(const tw_store *store);

#ifdef __cplusplus
}
#endif

#endif
