#include "timeweaver.h"
#include "platform.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TW_VERSION 1u
#define TW_MAX_PHYSICAL_PAGES 16384u
#define TW_META_FILE "graph.twm"
#define TW_DATA_FILE "pages.twd"

typedef struct tw_header {
    char magic[8];
    uint32_t version;
    uint32_t page_size;
    uint32_t max_nodes;
    uint32_t max_physical_pages;
    uint64_t node_count;
    uint64_t physical_pages;
    uint64_t head_id;
    uint64_t generation;
} tw_header;

typedef struct tw_disk_meta {
    tw_header header;
    tw_node nodes[TW_MAX_NODES];
} tw_disk_meta;

struct tw_store {
    tw_mapping meta_mapping;
    tw_mapping data_mapping;
    tw_disk_meta *meta;
    unsigned char *pages;
    char error[256];
};

static void set_error(tw_store *s, const char *message) {
    snprintf(s->error, sizeof(s->error), "%s", message);
}

static void join_path(char *out, size_t size, const char *dir, const char *file) {
    size_t length = strlen(dir);
    const char *separator = (length && (dir[length - 1] == '/' ||
                              dir[length - 1] == '\\')) ? "" : "/";
    snprintf(out, size, "%s%s%s", dir, separator, file);
}

static uint64_t hash_bytes(const unsigned char *data, size_t size) {
    uint64_t hash = 1469598103934665603ULL;
    size_t i;
    for (i = 0; i < size; ++i) {
        hash ^= data[i];
        hash *= 1099511628211ULL;
    }
    return hash;
}

static tw_node *find_mutable(tw_store *s, uint64_t id) {
    size_t i;
    for (i = 0; i < s->meta->header.node_count; ++i) {
        if (s->meta->nodes[i].id == id) return &s->meta->nodes[i];
    }
    return NULL;
}

int tw_open(tw_store **out, const char *directory, int create) {
    tw_store *s;
    char meta_path[1024];
    char data_path[1024];
    if (!out || !directory) return -1;
    s = (tw_store *)calloc(1, sizeof(*s));
    if (!s) return -1;
#ifndef _WIN32
    s->meta_mapping.fd = -1;
    s->data_mapping.fd = -1;
#endif
    if (create && tw_platform_mkdir(directory) != 0) {
        set_error(s, "could not create workspace directory");
        *out = s;
        return -1;
    }
    join_path(meta_path, sizeof(meta_path), directory, TW_META_FILE);
    join_path(data_path, sizeof(data_path), directory, TW_DATA_FILE);
    if (tw_platform_map(&s->meta_mapping, meta_path, sizeof(tw_disk_meta),
                        create, s->error, sizeof(s->error)) != 0) {
        *out = s;
        return -1;
    }
    if (tw_platform_map(&s->data_mapping, data_path,
                        (size_t)TW_MAX_PHYSICAL_PAGES * TW_PAGE_SIZE,
                        create, s->error, sizeof(s->error)) != 0) {
        tw_platform_unmap(&s->meta_mapping);
        *out = s;
        return -1;
    }
    s->meta = (tw_disk_meta *)s->meta_mapping.address;
    s->pages = (unsigned char *)s->data_mapping.address;
    if (memcmp(s->meta->header.magic, "TIMEWV1", 7) != 0) {
        if (!create) {
            set_error(s, "workspace has no valid TimeWeaver header");
            *out = s;
            return -1;
        }
        memset(s->meta, 0, sizeof(*s->meta));
        memcpy(s->meta->header.magic, "TIMEWV1", 7);
        s->meta->header.version = TW_VERSION;
        s->meta->header.page_size = TW_PAGE_SIZE;
        s->meta->header.max_nodes = TW_MAX_NODES;
        s->meta->header.max_physical_pages = TW_MAX_PHYSICAL_PAGES;
        if (tw_platform_flush(&s->meta_mapping, s->error,
                              sizeof(s->error)) != 0) {
            *out = s;
            return -1;
        }
    }
    if (s->meta->header.version != TW_VERSION ||
        s->meta->header.page_size != TW_PAGE_SIZE) {
        set_error(s, "unsupported workspace format");
        *out = s;
        return -1;
    }
    *out = s;
    return 0;
}

void tw_close(tw_store *s) {
    if (!s) return;
    tw_platform_unmap(&s->data_mapping);
    tw_platform_unmap(&s->meta_mapping);
    free(s);
}

const char *tw_last_error(const tw_store *s) {
    return s ? s->error : "invalid store";
}

int tw_snapshot(tw_store *s, uint64_t parent_id, const char *label,
                const char *note, const void *state, size_t state_size,
                uint32_t cursor, tw_status status, uint64_t *node_id) {
    tw_node *parent = NULL;
    tw_node pending;
    uint32_t logical_pages;
    uint32_t i;
    const unsigned char *bytes = (const unsigned char *)state;
    if (!s || !state || state_size == 0) return -1;
    if (state_size > (size_t)TW_MAX_LOGICAL_PAGES * TW_PAGE_SIZE) {
        set_error(s, "state exceeds maximum snapshot size");
        return -1;
    }
    if (s->meta->header.node_count >= TW_MAX_NODES) {
        set_error(s, "node capacity exhausted");
        return -1;
    }
    if (parent_id) {
        parent = find_mutable(s, parent_id);
        if (!parent) {
            set_error(s, "parent node not found");
            return -1;
        }
    }
    memset(&pending, 0, sizeof(pending));
    memset(pending.page_ids, 0xff, sizeof(pending.page_ids));
    pending.id = s->meta->header.node_count + 1;
    pending.parent_id = parent_id;
    pending.created_ns = tw_platform_now_ns();
    pending.state_hash = hash_bytes(bytes, state_size);
    pending.state_size = (uint32_t)state_size;
    pending.cursor = cursor;
    pending.status = (uint32_t)status;
    snprintf(pending.label, sizeof(pending.label), "%s", label ? label : "snapshot");
    snprintf(pending.note, sizeof(pending.note), "%s", note ? note : "");
    logical_pages = (uint32_t)((state_size + TW_PAGE_SIZE - 1) / TW_PAGE_SIZE);
    pending.page_count = logical_pages;

    for (i = 0; i < logical_pages; ++i) {
        unsigned char page[TW_PAGE_SIZE];
        size_t offset = (size_t)i * TW_PAGE_SIZE;
        size_t remaining = state_size - offset;
        size_t copy_size = remaining < TW_PAGE_SIZE ? remaining : TW_PAGE_SIZE;
        int reuse = 0;
        memset(page, 0, sizeof(page));
        memcpy(page, bytes + offset, copy_size);
        if (parent && i < parent->page_count) {
            uint32_t old_id = parent->page_ids[i];
            if (old_id < s->meta->header.physical_pages &&
                memcmp(page, s->pages + (size_t)old_id * TW_PAGE_SIZE,
                       TW_PAGE_SIZE) == 0) {
                pending.page_ids[i] = old_id;
                reuse = 1;
            }
        }
        if (!reuse) {
            uint64_t physical = s->meta->header.physical_pages;
            if (physical >= TW_MAX_PHYSICAL_PAGES) {
                set_error(s, "physical page capacity exhausted");
                return -1;
            }
            memcpy(s->pages + (size_t)physical * TW_PAGE_SIZE, page, TW_PAGE_SIZE);
            pending.page_ids[i] = (uint32_t)physical;
            s->meta->header.physical_pages++;
        }
    }

    s->meta->nodes[s->meta->header.node_count] = pending;
    s->meta->header.node_count++;
    s->meta->header.head_id = pending.id;
    s->meta->header.generation++;
    if (tw_platform_flush(&s->data_mapping, s->error, sizeof(s->error)) != 0 ||
        tw_platform_flush(&s->meta_mapping, s->error, sizeof(s->error)) != 0) {
        return -1;
    }
    if (node_id) *node_id = pending.id;
    return 0;
}

int tw_read_state(tw_store *s, uint64_t node_id, void *state,
                  size_t capacity, size_t *state_size) {
    tw_node *node;
    unsigned char *out = (unsigned char *)state;
    uint32_t i;
    if (!s || !state) return -1;
    node = find_mutable(s, node_id);
    if (!node) {
        set_error(s, "node not found");
        return -1;
    }
    if (capacity < node->state_size) {
        set_error(s, "output buffer is too small");
        return -1;
    }
    for (i = 0; i < node->page_count; ++i) {
        size_t offset = (size_t)i * TW_PAGE_SIZE;
        size_t remaining = node->state_size - offset;
        size_t copy_size = remaining < TW_PAGE_SIZE ? remaining : TW_PAGE_SIZE;
        uint32_t physical = node->page_ids[i];
        if (physical >= s->meta->header.physical_pages) {
            set_error(s, "node references an invalid physical page");
            return -1;
        }
        memcpy(out + offset, s->pages + (size_t)physical * TW_PAGE_SIZE, copy_size);
    }
    if (state_size) *state_size = node->state_size;
    return 0;
}

int tw_get_page_view(const tw_store *s, uint64_t node_id,
                     uint32_t logical_page, const void **data,
                     size_t *data_size, uint32_t *physical_page) {
    tw_node node;
    uint32_t physical;
    size_t offset;
    size_t remaining;
    if (!s || !data || tw_find_node(s, node_id, &node) != 0 ||
        logical_page >= node.page_count) return -1;
    physical = node.page_ids[logical_page];
    if (physical >= s->meta->header.physical_pages) return -1;
    offset = (size_t)logical_page * TW_PAGE_SIZE;
    remaining = node.state_size - offset;
    *data = s->pages + (size_t)physical * TW_PAGE_SIZE;
    if (data_size) *data_size = remaining < TW_PAGE_SIZE ? remaining : TW_PAGE_SIZE;
    if (physical_page) *physical_page = physical;
    return 0;
}

int tw_checkout(tw_store *s, uint64_t node_id) {
    if (!s || !find_mutable(s, node_id)) {
        if (s) set_error(s, "node not found");
        return -1;
    }
    s->meta->header.head_id = node_id;
    s->meta->header.generation++;
    return tw_platform_flush(&s->meta_mapping, s->error, sizeof(s->error));
}

uint64_t tw_head(const tw_store *s) {
    return s ? s->meta->header.head_id : 0;
}

size_t tw_node_count(const tw_store *s) {
    return s ? (size_t)s->meta->header.node_count : 0;
}

int tw_get_node(const tw_store *s, size_t index, tw_node *node) {
    if (!s || !node || index >= s->meta->header.node_count) return -1;
    *node = s->meta->nodes[index];
    return 0;
}

int tw_find_node(const tw_store *s, uint64_t node_id, tw_node *node) {
    size_t i;
    if (!s || !node) return -1;
    for (i = 0; i < s->meta->header.node_count; ++i) {
        if (s->meta->nodes[i].id == node_id) {
            *node = s->meta->nodes[i];
            return 0;
        }
    }
    return -1;
}

int tw_get_stats(const tw_store *s, tw_stats *stats) {
    size_t i;
    uint64_t logical = 0;
    uint64_t shared = 0;
    if (!s || !stats) return -1;
    memset(stats, 0, sizeof(*stats));
    for (i = 0; i < s->meta->header.node_count; ++i) {
        uint32_t page;
        logical += s->meta->nodes[i].page_count;
        if (s->meta->nodes[i].parent_id) {
            tw_node parent;
            if (tw_find_node(s, s->meta->nodes[i].parent_id, &parent) == 0) {
                for (page = 0; page < s->meta->nodes[i].page_count; ++page) {
                    if (page < parent.page_count &&
                        s->meta->nodes[i].page_ids[page] == parent.page_ids[page]) {
                        shared++;
                    }
                }
            }
        }
    }
    stats->nodes = s->meta->header.node_count;
    stats->physical_pages = s->meta->header.physical_pages;
    stats->logical_pages = logical;
    stats->shared_page_references = shared;
    stats->physical_bytes = stats->physical_pages * TW_PAGE_SIZE;
    stats->naive_snapshot_bytes = stats->logical_pages * TW_PAGE_SIZE;
    if (stats->naive_snapshot_bytes) {
        stats->saved_ratio = 1.0 - (double)stats->physical_bytes /
                                      (double)stats->naive_snapshot_bytes;
    }
    return 0;
}

int tw_validate(const tw_store *s) {
    size_t i;
    if (!s || memcmp(s->meta->header.magic, "TIMEWV1", 7) != 0) return -1;
    if (s->meta->header.node_count > TW_MAX_NODES ||
        s->meta->header.physical_pages > TW_MAX_PHYSICAL_PAGES) return -1;
    for (i = 0; i < s->meta->header.node_count; ++i) {
        const tw_node *node = &s->meta->nodes[i];
        uint32_t page;
        if (node->id != i + 1 || node->page_count > TW_MAX_LOGICAL_PAGES) return -1;
        if (node->parent_id >= node->id) return -1;
        for (page = 0; page < node->page_count; ++page) {
            if (node->page_ids[page] >= s->meta->header.physical_pages) return -1;
        }
    }
    return 0;
}
