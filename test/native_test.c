#include "timeweaver.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _WIN32
#include <process.h>
#define process_id _getpid
#else
#include <unistd.h>
#define process_id getpid
#endif

static void workspace_path(char *path, size_t size) {
    const char *base = getenv("TEMP");
    if (!base) base = getenv("TMPDIR");
    if (!base) base = ".";
    snprintf(path, size, "%s/timeweaver-test-%ld-%ld", base,
             (long)process_id(), (long)time(NULL));
}

int main(void) {
    char path[512];
    unsigned char root_state[TW_PAGE_SIZE * 2];
    unsigned char child_state[TW_PAGE_SIZE * 2];
    unsigned char fork_state[TW_PAGE_SIZE * 2];
    unsigned char restored[TW_PAGE_SIZE * 2];
    tw_store *store = NULL;
    tw_node root, child, forked;
    tw_stats stats;
    const void *mapped_page = NULL;
    size_t mapped_size = 0;
    uint32_t physical_page = 0;
    uint64_t root_id, child_id, fork_id;
    size_t restored_size = 0;

    workspace_path(path, sizeof(path));
    memset(root_state, 'A', sizeof(root_state));
    memcpy(child_state, root_state, sizeof(root_state));
    memcpy(fork_state, root_state, sizeof(root_state));
    child_state[TW_PAGE_SIZE + 17] = 'B';
    fork_state[23] = 'C';

    assert(tw_open(&store, path, 1) == 0);
    assert(tw_snapshot(store, 0, "root", "", root_state, sizeof(root_state),
                       0, TW_STATUS_CHECKPOINT, &root_id) == 0);
    assert(tw_snapshot(store, root_id, "child", "", child_state, sizeof(child_state),
                       1, TW_STATUS_SUCCESS, &child_id) == 0);
    assert(tw_snapshot(store, root_id, "fork", "", fork_state, sizeof(fork_state),
                       1, TW_STATUS_FORK, &fork_id) == 0);

    assert(tw_find_node(store, root_id, &root) == 0);
    assert(tw_find_node(store, child_id, &child) == 0);
    assert(tw_find_node(store, fork_id, &forked) == 0);
    assert(child.page_ids[0] == root.page_ids[0]);
    assert(child.page_ids[1] != root.page_ids[1]);
    assert(forked.page_ids[0] != root.page_ids[0]);
    assert(forked.page_ids[1] == root.page_ids[1]);
    assert(child.parent_id == root_id && forked.parent_id == root_id);
    assert(tw_get_page_view(store, child_id, 0, &mapped_page, &mapped_size,
                            &physical_page) == 0);
    assert(mapped_size == TW_PAGE_SIZE);
    assert(physical_page == root.page_ids[0]);
    assert(mapped_page != NULL && ((const unsigned char *)mapped_page)[0] == 'A');

    assert(tw_read_state(store, child_id, restored, sizeof(restored),
                         &restored_size) == 0);
    assert(restored_size == sizeof(child_state));
    assert(memcmp(restored, child_state, sizeof(child_state)) == 0);
    assert(tw_checkout(store, root_id) == 0);
    assert(tw_head(store) == root_id);
    assert(tw_get_stats(store, &stats) == 0);
    assert(stats.physical_pages == 4);
    assert(stats.logical_pages == 6);
    assert(stats.shared_page_references == 2);
    assert(stats.saved_ratio > 0.3);
    assert(tw_validate(store) == 0);
    tw_close(store);

    assert(tw_open(&store, path, 0) == 0);
    assert(tw_head(store) == root_id);
    assert(tw_validate(store) == 0);
    assert(tw_read_state(store, fork_id, restored, sizeof(restored), NULL) == 0);
    assert(memcmp(restored, fork_state, sizeof(fork_state)) == 0);
    tw_close(store);

    puts("native store invariants: ok");
    return 0;
}
