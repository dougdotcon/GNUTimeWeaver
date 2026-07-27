# v0.2.1 execution report

Status: `REAL_MODEL_BRIDGE_NOT_VERIFIED`. The runtime tree is
provisioned and verified clean at
`c588c4f47683e73ad2d69f50480bec6cc85fd0f7`; both GGUF files are present.

Toolchain: Git 2.55.0, Node v26.5.0, npm 11.17.0, GCC/G++ 15.2.0,
CMake 4.4.0 and Ninja 1.13.2. The pinned CPU runtime and the opt-in TimeWeaver
adapter both compile successfully with Ninja.

Independent runtime test:

- Qwen acceptance model generated 16 greedy tokens successfully.
- The smoke model initially aborted with Windows access violation `0xC0000005`.
  A controlled rebuild identified b10103's `GGML_CPU_REPACK` path as the cause.
  With `GGML_CPU_REPACK=OFF`, the same pinned runtime/model generated 16 greedy
  tokens successfully (`132.11 tokens/s`) without modifying the runtime tree.

The independent runtime prerequisite now passes. A real two-process TimeWeaver
probe checkpointed and restored 128 prefix tokens. It serialized 886,440 bytes,
restored the same byte count, and validated memory positions 0..127. Restore
reported zero prefix tokenizer invocations and zero prefix tokens submitted to
decode. Continuation, greedy equivalence, forks, atomic publication, hashes and
fault injection are not yet implemented by this probe, so the smoke campaign is
not promoted.
