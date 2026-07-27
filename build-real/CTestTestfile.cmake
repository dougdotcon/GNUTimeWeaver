# CMake generated Testfile for 
# Source directory: D:/GNUTimeWeaver
# Build directory: D:/GNUTimeWeaver/build-real
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(native_store "D:/GNUTimeWeaver/build-real/timeweaver_tests.exe")
set_tests_properties(native_store PROPERTIES  _BACKTRACE_TRIPLES "D:/GNUTimeWeaver/CMakeLists.txt;74;add_test;D:/GNUTimeWeaver/CMakeLists.txt;0;")
subdirs("llama.cpp")
