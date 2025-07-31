cmake_minimum_required(VERSION 3.12)
project(MyProject C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Use standard locations for installation (e.g., /usr/local/include, /usr/local/lib)
include(GNUInstallDirs)

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# --- 1. Core C Library ---
add_library(c_lib SHARED c_lib/c_lib.c)
target_include_directories(c_lib PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/c_lib>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)

# --- 2. C++ Wrapper Library ---
add_library(cpp_wrapper STATIC cpp_wrapper/cpp_wrapper.cpp)
target_include_directories(cpp_wrapper PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/cpp_wrapper>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)
target_link_libraries(cpp_wrapper PRIVATE c_lib)

# --- 3. C++ Demo Executable ---
add_executable(cpp_demo main.cpp)
target_link_libraries(cpp_demo PRIVATE cpp_wrapper)

# ==============================================================================
# WORKFLOW FOR PYTHON DEVELOPERS
# ==============================================================================
set(PYTHON_PACKAGE_LIB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/src/my_c_wrapper/lib)

# This custom command copies the C shared library into the Python source tree
# immediately after it's built. This prepares the tree for `pip install`.
add_custom_command(
    TARGET c_lib POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${PYTHON_PACKAGE_LIB_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:c_lib> ${PYTHON_PACKAGE_LIB_DIR}
    COMMENT "Copying c_lib to Python package source for packaging..."
)

# ==============================================================================
# WORKFLOW FOR C++ DEVELOPERS
# ==============================================================================
# Defines where `cmake --install` will place the files.
install(
    TARGETS c_lib cpp_wrapper
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)

# Install the public headers into a namespaced directory.
install(
    DIRECTORY c_lib/ cpp_wrapper/
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/my_project
    FILES_MATCHING PATTERN "*.h"
)
