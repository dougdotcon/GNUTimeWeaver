# GNU TimeWeaver

Local-first time-travel debugger for agent memory. TimeWeaver stores agent
checkpoints as a directed acyclic graph (DAG), shares unchanged 4 KiB pages
between descendants, and resumes a mutated branch without executing its prefix
again.

This repository contains an operational CPU/mmap MVP. It proves the storage,
fork, checkout, persistence, and debugger workflow before coupling the same ABI
to a real inference engine's KV cache.

## Real model bridge v0.2

The CPU bridge scaffolding targets a pinned, externally supplied `llama.cpp`
tree and stores `opaque_runtime_state`; it is currently
`ADAPTER_PROTOCOL_READY_NO_REAL_MODEL` until `TIMEWEAVER_MODEL_PATH` points to a
local GGUF and the runtime commit is recorded. vLLM block-native KV and CUDA/
VRAM work remain future phases.

## vLLM connector v0.3

The block-native KV protocol is preregistered in
`config/vllm_block_connector_v0_3.yaml`, with an external Python package under
`python/timeweaver_vllm`. It currently reports
`VLLM_CONNECTOR_PROTOCOL_READY_NO_SUPPORTED_ENVIRONMENT`: this Windows host has
no WSL/Linux distribution, PyTorch, or vLLM. No real block restore or VRAM
claim is made before the pinned vLLM runtime is executed in Linux/WSL2.

The original v0.3 runtime pin was superseded before execution. Amendment v0.3.1
uses official vLLM tag `v0.23.0` at
`0fc695fc6d1d82e9a5ac6835ac8e4e1c83703665` and limits scope to Linux/WSL2 G0
qualification and read-only real KV event lineage G1.

## Run the MVP

Requirements:

- Node.js 22 or newer
- GCC or another C11 compiler available as `gcc`/`cc`
- GNU/Linux, macOS, or Windows (the production target is GNU/Linux)

```bash
npm run build
npm test
npm start
```

Open `http://127.0.0.1:7331`. Select any checkpoint, change its working prompt,
and press **Fork & resume**. The included local agent deliberately produces
MySQL syntax for a PostgreSQL schema, fails, then demonstrates a corrected
branch while retaining the earlier mapped pages.

No package installation, cloud API, account, model download, or network access
is required at runtime.

## Native CLI

```bash
./build/timeweaver demo .timeweaver/manual
./build/timeweaver export .timeweaver/manual
./build/timeweaver branch .timeweaver/manual 5 "Use PostgreSQL syntax only"
./build/timeweaver validate .timeweaver/manual
```

On Windows, use `build\timeweaver.exe`.

## What the MVP proves

- `mmap`/file mapping persistence with immutable 4 KiB physical pages
- Copy-on-Write snapshots: a child allocates only pages different from its parent
- Zero-copy read views over individual immutable mapped pages
- Persistent DAG lineage, state hashes, HEAD checkout, and structural validation
- Mutation and continuation from a checkpoint with semantic dependency invalidation
- Local dashboard and CLI operating through the native C engine
- Measurable memory accounting against naive full-state snapshots

The bundled demonstration creates 9 checkpoints with 144 logical page
references. It uses 35 physical pages instead of 144 full copies, avoiding
approximately 75.7% of the snapshot bytes.

## What it does not claim

This MVP does **not** yet snapshot CUDA allocations, rewrite GPU page tables,
inspect model weights, or integrate directly with vLLM/llama.cpp. POSIX `mmap`
maps CPU virtual memory and files; it is not, by itself, a VRAM remapping API.
The bundled agent still reconstructs a contiguous CPU buffer when it resumes;
the page-view ABI is available for adapters that can consume discontiguous blocks.
The demo agent uses KV-shaped local memory blocks so the storage invariants can
be validated on ordinary hardware. The next milestone is a vLLM KV Connector
adapter using the existing block/event interfaces, followed by GPU-aware
benchmarks.

See [architecture](docs/ARCHITECTURE.md), [MVP scope](docs/MVP.md), and the
[original product vision](docs/VISION.md).

## Design sources

The vLLM design currently organizes prefix caches as fixed token blocks with
hashes and reference counts, while KV cache events expose storage/removal events
to external consumers. TimeWeaver deliberately models its native ABI around
blocks and parent hashes rather than around a historical kernel implementation.

- [vLLM prefix caching design](https://docs.vllm.ai/en/stable/design/prefix_caching/)
- [vLLM KV events configuration](https://docs.vllm.ai/en/latest/api/vllm/config/kv_events/)
- [vLLM KV events example](https://docs.vllm.ai/en/stable/examples/features/kv_events/)

## License

GNU TimeWeaver is free software licensed under
[GNU GPLv3](LICENSE). See [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a
change. TimeWeaver is not currently an official GNU package and does not claim
endorsement by the GNU Project.
