# Runtime adapter ABI

`tw-runtime-adapter/0.2` is a C ABI boundary in `src/runtime/timeweaver_runtime.h`. C++ implementation details remain in `src/adapters/llama_cpp`; the core only receives opaque manifests and structured errors. Probe/open/close are available now; model/request operations return an explicit not-linked error until a pinned llama.cpp tree is supplied.
