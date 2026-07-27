# v0.2.1 execution report

Status: `LLAMA_CPP_RUNTIME_OR_MODEL_SMOKE_FAILED`. The runtime tree is
provisioned and verified clean at
`c588c4f47683e73ad2d69f50480bec6cc85fd0f7`; both GGUF files are present.

Toolchain: Git 2.55.0, Node v26.5.0, npm 11.17.0, GCC/G++ 15.2.0,
CMake 4.4.0 and Ninja 1.13.2. The pinned CPU runtime and the opt-in TimeWeaver
adapter both compile successfully with Ninja.

Independent runtime test:

- Qwen acceptance model generated 16 greedy tokens successfully.
- The smoke model loaded its metadata but aborted with Windows access violation
  `0xC0000005` before token generation. It also warned that the default
  `n_ctx_seq=256` exceeds its training context 128.

Per protocol, the campaign stops before TimeWeaver checkpoint/restore because
the independent smoke prerequisite failed. No central zero-reprocessing metric
is claimed.
