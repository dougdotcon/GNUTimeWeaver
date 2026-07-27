# Architecture

## The three concepts

TimeWeaver applies the three concepts required by the product vision as concrete
engineering constraints.

1. **DAG + Copy-on-Write.** Each `tw_node` has one parent and a table of logical
   page references. A snapshot compares each 4 KiB logical page with its parent.
   Equal pages retain the existing physical page ID; changed pages are appended
   and never modified afterward.
2. **Cognitive sovereignty + GPLv3.** The native store, agent demonstration,
   server, and UI run locally. Runtime behavior needs no hosted API or telemetry.
   The repository is licensed as GPL-3.0-only.
3. **Memory snapshots + mmap.** `graph.twm` and `pages.twd` are mapped into the
   process address space. GNU/Linux uses POSIX `mmap(..., MAP_SHARED, ...)` and
   `msync`; the Windows development port uses `CreateFileMapping` and
   `FlushViewOfFile` with equivalent semantics.

## Disk format v1

`graph.twm` contains a versioned header followed by a fixed-capacity node array.
A node records lineage, timestamp, cursor, status, state hash, label, note, and
up to 128 physical page IDs. `pages.twd` is a sparse arena of 16,384 immutable
4 KiB physical pages.

The v1 limits are intentionally static:

| Limit | Value |
| --- | ---: |
| State per checkpoint | 512 KiB |
| Nodes per workspace | 2,048 |
| Physical page arena | 64 MiB |
| Logical page size | 4 KiB |

These constraints make corruption checks and address calculations explicit for
the MVP. A later format will use segmented arenas and an append-only write-ahead
journal before supporting concurrent writers.

## Snapshot transaction

1. Validate the parent and state bounds.
2. Split the state into zero-padded logical pages.
3. Compare each page with the corresponding immutable parent page.
4. Reuse the old physical ID or append the changed page.
5. Append the node projection and advance HEAD.
6. Flush the page arena, then graph metadata.

`tw_validate` checks format identity, capacity bounds, monotonically increasing
node IDs, backward-only parent references, and valid physical page references.

## Agent adapter boundary

The native store is model-agnostic: it snapshots byte ranges and never interprets
tensors. The demo adapter reserves 16 pages for control state, prompt, response,
schema, and KV-shaped blocks. Its dependency rule knows that changing the prompt
invalidates dialect selection but not request parsing or local schema loading.

Adapters can call `tw_get_page_view` to read an individual immutable mapped page
without reconstructing the complete state. `tw_read_state` remains available for
consumers that need one contiguous buffer, including the current demo adapter.

A vLLM adapter belongs above this boundary. It must translate KV block hashes,
reference counts, allocation/removal events, and request cursors into TimeWeaver
nodes. It must not treat SSD `mmap` as direct VRAM page remapping.

## Failure model

The MVP is single-writer. Physical pages are immutable, but the metadata header
does not yet have a write-ahead log, so power loss between arena and metadata
flushes can leak unreachable pages. It cannot make an existing node refer to
partially written content because metadata is flushed last. Concurrent writers,
garbage collection, compaction, encryption at rest, and untrusted workspace
parsing are outside the v1 boundary.
# Runtime bridge boundary (v0.2)

The existing C11 storage ABI remains unchanged. `llama.cpp` is isolated behind
the versioned C adapter in `src/runtime` and `src/adapters/llama_cpp`; its
serialized state is an opaque content-addressed object, not block-native KV.
