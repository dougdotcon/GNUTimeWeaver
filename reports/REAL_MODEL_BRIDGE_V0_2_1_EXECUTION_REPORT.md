# v0.2.1 execution report

Status: `SMOKE_REAL_MODEL_BRIDGE_PASSED_NO_ACCEPTANCE_MODEL`. The runtime tree is
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

The independent runtime prerequisite passes. A real two-process TimeWeaver
probe checkpointed and restored 128 prefix tokens. It serialized 886,440 bytes,
restored the same byte count, and validated memory positions 0..127. Restore
reported zero prefix tokenizer invocations and zero prefix tokens submitted to
decode. Sixteen greedy continuation tokens were identical after restore.

Branches A and B restored the same parent, decoded zero prefix tokens, tokenized
8 and 10 suffix tokens respectively, and produced different continuation hashes
(`be8ccd7ea1b4e9d5` and `be8c4f7ea1b413bb`). The parent SHA-256 remained
`bfd17f7b0352b5c61ea87f0caaeec7442563d92b7278b9348f99f4a6465140d2`.

The state was published content-addressed with temp write, fsync, SHA-256
validation, atomic rename, manifest, then node. Faults at mid-write,
before-rename, after-rename and before-node-publish produced no node referencing
partial state. Acceptance remains unexecuted.
