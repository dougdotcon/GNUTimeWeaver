cmake_minimum_required(VERSION 3.16)
project(timeweaver VERSION 0.1.0 LANGUAGES C CXX)
option(TIMEWEAVER_WITH_LLAMA_CPP "Build the pinned llama.cpp adapter" OFF)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS ON)

add_library(timeweaver_core STATIC
    src/native/platform.c
    src/native/store.c
)
target_include_directories(timeweaver_core PUBLIC include)
target_include_directories(timeweaver_core PRIVATE src/native)

if(MSVC)
    target_compile_options(timeweaver_core PRIVATE /W4)
else()
    target_compile_options(timeweaver_core PRIVATE -Wall -Wextra -Wpedantic)
endif()

add_executable(timeweaver src/native/cli.c src/native/demo_agent.c)
target_link_libraries(timeweaver PRIVATE timeweaver_core)
target_include_directories(timeweaver PRIVATE include src/native)

if(TIMEWEAVER_WITH_LLAMA_CPP)
    if(NOT DEFINED TIMEWEAVER_LLAMA_CPP_DIR)
        message(FATAL_ERROR "TIMEWEAVER_LLAMA_CPP_DIR is required when TIMEWEAVER_WITH_LLAMA_CPP=ON")
    endif()
    if(NOT EXISTS "${TIMEWEAVER_LLAMA_CPP_DIR}/include/llama.h")
        message(FATAL_ERROR "Pinned llama.cpp tree must contain include/llama.h")
    endif()
    if(EXISTS "${TIMEWEAVER_LLAMA_CPP_DIR}/CMakeLists.txt")
        if(MINGW)
            # GCC 15's MinGW headers do not expose THREAD_POWER_THROTTLING_STATE.
            # Targeting Windows 7 disables only that optional scheduling hint.
            add_compile_definitions(_WIN32_WINNT=0x0601)
        endif()
        set(LLAMA_BUILD_TESTS OFF CACHE BOOL "" FORCE)
        set(LLAMA_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
        set(LLAMA_BUILD_SERVER OFF CACHE BOOL "" FORCE)
        set(LLAMA_CURL OFF CACHE BOOL "" FORCE)
        set(GGML_CUDA OFF CACHE BOOL "" FORCE)
        set(GGML_VULKAN OFF CACHE BOOL "" FORCE)
        set(GGML_SYCL OFF CACHE BOOL "" FORCE)
        set(GGML_RPC OFF CACHE BOOL "" FORCE)
        set(GGML_NATIVE ON CACHE BOOL "" FORCE)
        add_subdirectory("${TIMEWEAVER_LLAMA_CPP_DIR}" "${CMAKE_BINARY_DIR}/llama.cpp" EXCLUDE_FROM_ALL)
    endif()
    add_library(timeweaver_llama_adapter STATIC
        src/runtime/runtime_registry.c
        src/adapters/llama_cpp/llama_cpp_adapter.cpp)
    target_include_directories(timeweaver_llama_adapter PRIVATE
        include src/runtime src/adapters/llama_cpp "${TIMEWEAVER_LLAMA_CPP_DIR}/include")
    target_compile_definitions(timeweaver_llama_adapter PRIVATE
        TIMEWEAVER_LLAMA_CPP_COMMIT="c588c4f")
    target_link_libraries(timeweaver_llama_adapter PRIVATE llama)
endif()

enable_testing()
add_executable(timeweaver_tests test/native_test.c)
target_link_libraries(timeweaver_tests PRIVATE timeweaver_core)
target_include_directories(timeweaver_tests PRIVATE include src/native)
add_test(NAME native_store COMMAND timeweaver_tests)
