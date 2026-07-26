cmake_minimum_required(VERSION 3.16)
project(timeweaver VERSION 0.1.0 LANGUAGES C)

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

enable_testing()
add_executable(timeweaver_tests test/native_test.c)
target_link_libraries(timeweaver_tests PRIVATE timeweaver_core)
target_include_directories(timeweaver_tests PRIVATE include src/native)
add_test(NAME native_store COMMAND timeweaver_tests)
