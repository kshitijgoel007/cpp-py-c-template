cmake_minimum_required(VERSION 3.24)
project(MyProject VERSION 2026.6.0 LANGUAGES C CXX)

# ABI version is separate from the CalVer package version. Bump this only
# when making a backwards-incompatible change to the C ABI.
set(C_CORE_ABI_VERSION 1)

include(CTest)
include(FetchContent)
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

option(MYPROJECT_BUILD_CPP "Build the C++ wrapper" ON)
option(MYPROJECT_BUILD_PYTHON "Copy the C library into the Python package" ON)
option(MYPROJECT_BUILD_EXAMPLES "Build consumer examples" ON)
option(MYPROJECT_FETCH_TEST_DEPS "Download test dependencies when unavailable" ON)
option(MYPROJECT_WARNINGS_AS_ERRORS "Treat compiler warnings as errors" OFF)
option(MYPROJECT_ENABLE_ASAN "Enable AddressSanitizer" OFF)
option(MYPROJECT_ENABLE_UBSAN "Enable UndefinedBehaviorSanitizer" OFF)
option(MYPROJECT_ENABLE_COVERAGE "Enable native coverage instrumentation" OFF)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
foreach(_config DEBUG RELEASE RELWITHDEBINFO MINSIZEREL)
    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_${_config} "${CMAKE_BINARY_DIR}/lib")
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_${_config} "${CMAKE_BINARY_DIR}/lib")
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_${_config} "${CMAKE_BINARY_DIR}/bin")
endforeach()

function(myproject_enable_warnings target)
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4)
        if(MYPROJECT_WARNINGS_AS_ERRORS)
            target_compile_options(${target} PRIVATE /WX)
        endif()
    else()
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
        if(MYPROJECT_WARNINGS_AS_ERRORS)
            target_compile_options(${target} PRIVATE -Werror)
        endif()
    endif()
endfunction()

function(myproject_enable_instrumentation target)
    if(MSVC)
        return()
    endif()
    if(MYPROJECT_ENABLE_ASAN)
        target_compile_options(${target} PRIVATE -fsanitize=address -fno-omit-frame-pointer)
        target_link_options(${target} PRIVATE -fsanitize=address)
    endif()
    if(MYPROJECT_ENABLE_UBSAN)
        target_compile_options(${target} PRIVATE -fsanitize=undefined -fno-omit-frame-pointer)
        target_link_options(${target} PRIVATE -fsanitize=undefined)
    endif()
    if(MYPROJECT_ENABLE_COVERAGE)
        target_compile_options(${target} PRIVATE --coverage -O0 -g)
        target_link_options(${target} PRIVATE --coverage)
    endif()
endfunction()

add_library(c_lib SHARED c_lib/c_lib.c)
add_library(MyProject::core ALIAS c_lib)
set_target_properties(c_lib PROPERTIES
    EXPORT_NAME core
    VERSION   ${PROJECT_VERSION}
    SOVERSION ${C_CORE_ABI_VERSION}
    C_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN YES
    WINDOWS_EXPORT_ALL_SYMBOLS OFF
)
target_compile_definitions(c_lib PRIVATE C_CORE_BUILDING_LIBRARY)
target_include_directories(c_lib PUBLIC
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/c_lib>"
    "$<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>"
)
myproject_enable_warnings(c_lib)
myproject_enable_instrumentation(c_lib)

if(MYPROJECT_BUILD_CPP)
    add_library(cpp_wrapper STATIC cpp_wrapper/cpp_wrapper.cpp)
    add_library(MyProject::cpp_wrapper ALIAS cpp_wrapper)
    set_target_properties(cpp_wrapper PROPERTIES EXPORT_NAME cpp_wrapper)
    target_include_directories(cpp_wrapper PUBLIC
        "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/cpp_wrapper>"
        "$<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>"
    )
    target_link_libraries(cpp_wrapper PUBLIC MyProject::core)
    myproject_enable_warnings(cpp_wrapper)
    myproject_enable_instrumentation(cpp_wrapper)
endif()

if(MYPROJECT_BUILD_EXAMPLES AND MYPROJECT_BUILD_CPP)
    add_executable(cpp_demo main.cpp)
    target_link_libraries(cpp_demo PRIVATE MyProject::cpp_wrapper)
    myproject_enable_warnings(cpp_demo)
    myproject_enable_instrumentation(cpp_demo)
endif()

if(MYPROJECT_BUILD_PYTHON)
    set(PYTHON_PACKAGE_LIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src/my_c_wrapper/lib")
    # Copy the shared library under the name ctypes will search for.
    # On macOS/Linux TARGET_FILE is the versioned binary but the loader needs
    # the unversioned linker name (libc_lib.dylib / libc_lib.so).
    # On Windows TARGET_FILE is already the DLL; TARGET_LINKER_FILE would be
    # the import library (.lib), so we keep TARGET_FILE_NAME there.
    add_custom_command(
        TARGET c_lib POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E make_directory "${PYTHON_PACKAGE_LIB_DIR}"
        COMMAND ${CMAKE_COMMAND} -E copy
            "$<TARGET_FILE:c_lib>"
            "${PYTHON_PACKAGE_LIB_DIR}/$<IF:$<PLATFORM_ID:Windows>,$<TARGET_FILE_NAME:c_lib>,$<TARGET_LINKER_FILE_NAME:c_lib>>"
        COMMENT "Copying c_lib to the Python package..."
    )
endif()

if(BUILD_TESTING)
    add_executable(c_api_tests tests/c/test_c_api.c)
    target_link_libraries(c_api_tests PRIVATE MyProject::core)
    myproject_enable_warnings(c_api_tests)
    myproject_enable_instrumentation(c_api_tests)
    add_test(NAME c_api COMMAND c_api_tests)

    if(MYPROJECT_BUILD_CPP)
        find_package(GTest 1.14 CONFIG QUIET)
        if(NOT GTest_FOUND)
            if(NOT MYPROJECT_FETCH_TEST_DEPS)
                message(FATAL_ERROR "GoogleTest was not found and dependency fetching is disabled")
            endif()
            set(INSTALL_GTEST OFF CACHE BOOL "" FORCE)
            FetchContent_Declare(
                googletest
                GIT_REPOSITORY https://github.com/google/googletest.git
                GIT_TAG v1.17.0
                GIT_SHALLOW TRUE
            )
            FetchContent_MakeAvailable(googletest)
        endif()

        add_executable(cpp_wrapper_tests tests/cpp/test_cpp_wrapper.cpp)
        target_link_libraries(cpp_wrapper_tests PRIVATE
            MyProject::cpp_wrapper
            GTest::gtest_main
        )
        myproject_enable_warnings(cpp_wrapper_tests)
        myproject_enable_instrumentation(cpp_wrapper_tests)
        include(GoogleTest)
        gtest_discover_tests(cpp_wrapper_tests)
    endif()

    configure_file(
        tests/cmake/run_consumer_test.cmake.in
        "${CMAKE_CURRENT_BINARY_DIR}/run_consumer_test.cmake"
        @ONLY
    )
    add_test(
        NAME cmake_consumer
        COMMAND ${CMAKE_COMMAND} -P "${CMAKE_CURRENT_BINARY_DIR}/run_consumer_test.cmake"
    )
endif()

install(
    TARGETS c_lib
    EXPORT MyProjectTargets
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)
if(MYPROJECT_BUILD_CPP)
    install(
        TARGETS cpp_wrapper
        EXPORT MyProjectTargets
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    )
endif()

install(
    FILES c_lib/c_lib.h
    DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}/my_project"
)
if(MYPROJECT_BUILD_CPP)
    install(
        FILES cpp_wrapper/cpp_wrapper.h
        DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}/my_project"
    )
endif()

configure_package_config_file(
    cmake/MyProjectConfig.cmake.in
    "${CMAKE_CURRENT_BINARY_DIR}/MyProjectConfig.cmake"
    INSTALL_DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/MyProject"
)
write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/MyProjectConfigVersion.cmake"
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)
install(
    FILES
        "${CMAKE_CURRENT_BINARY_DIR}/MyProjectConfig.cmake"
        "${CMAKE_CURRENT_BINARY_DIR}/MyProjectConfigVersion.cmake"
    DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/MyProject"
)
install(
    EXPORT MyProjectTargets
    FILE MyProjectTargets.cmake
    NAMESPACE MyProject::
    DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/MyProject"
)
