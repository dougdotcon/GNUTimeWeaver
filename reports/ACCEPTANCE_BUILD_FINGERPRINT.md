# Acceptance build fingerprint

llama.cpp b10103 at
`c588c4f47683e73ad2d69f50480bec6cc85fd0f7`, clean tree; `llama.h` SHA-256
`aff0098c291acda9b19736a145b73ced805fc1595235ecb214cb9442db883546`.
CPU-only MinGW-w64 GCC/G++ 15.2.0, CMake 4.4.0, Ninja 1.13.2,
`GGML_CPU_REPACK=OFF`, CUDA/Vulkan/SYCL/Metal/RPC disabled. The Q4_0 crash
with repack ON is recorded as `KNOWN_RUNTIME_TOOLCHAIN_INCOMPATIBILITY` and is
not used by acceptance.
