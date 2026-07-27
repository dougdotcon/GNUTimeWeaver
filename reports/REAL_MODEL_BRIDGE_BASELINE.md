# Real Model Bridge baseline

Date: 2026-07-26; repository: `b81e1a863928cbfa0536a4d240fb3ad5f32576b9`.

`npm run build` and `npm test` pass (native invariants and CLI rewind/fork/resume integration). The baseline is unchanged by the bridge scaffolding. The host is Windows x64 with Node v26.5.0 and GCC 15.2.0; CMake is not installed. The project is a C11 `mmap`/file-page store with a C CLI, local Node server/dashboard, and deterministic mock `demo_agent`; no C++ runtime, llama.cpp checkout, GGUF model, CUDA, vLLM, WAL, or concurrency layer is present.

Native sources: `src/native/{platform,store,demo_agent,cli}.{c,h}`; public ABI: `include/timeweaver.h`. Existing limits are 512 KiB checkpoint payloads, 2,048 nodes, and 64 MiB arena. Active commands are `init`, `demo`, `branch`, `export`, and `validate`; `npm run start` serves the dashboard.

Architecture document hashes (SHA-256): `ARCHITECTURE.md` `9ccfb95f...116f0e1`, `MVP.md` `366c1aa9...988c4b7`, `VISION.md` `671af5f1...1d971b4`. No legacy path was removed. Real-model tests are therefore `REAL_MODEL_TEST_NOT_EXECUTED`, not passes.

Evidence commands:

```text
npm run build
npm test
```

Linux-only demo/export/validate execution was not applicable on this Windows host.
