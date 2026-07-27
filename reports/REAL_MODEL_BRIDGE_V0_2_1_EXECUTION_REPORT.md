# v0.2.1 execution report

Status: `ADAPTER_PROTOCOL_READY_NO_REAL_MODEL`. The required pin and acceptance
profiles are frozen. The runtime tree is now provisioned and verified clean at
`c588c4f47683e73ad2d69f50480bec6cc85fd0f7`; CMake is unavailable on this host
and no GGUF is present. No smoke or acceptance test is counted as passed.

Toolchain: Git 2.55.0, Node v26.5.0, npm 11.17.0, GCC 15.2.0; `cmake` and
MSVC `cl` are unavailable. `npm test` passes. The next blocking artifact is an
explicit smoke model at `TIMEWEAVER_MODEL_PATH`.
