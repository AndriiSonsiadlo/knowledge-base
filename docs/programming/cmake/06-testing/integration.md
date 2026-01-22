---
id: integration
title: Test Integration
sidebar_label: Test Integration
sidebar_position: 2
tags: [cmake, testing, integration, best-practices]
---

# Test Integration

## Overview

Test integration in CMake involves structuring your project to support different types of tests (unit, integration, system), managing test dependencies, and creating a smooth testing workflow. This goes beyond basic CTest usage to build a comprehensive testing strategy.

## Project Structure for Testing

A well-organized test structure separates concerns and makes tests maintainable:

```
project/
├── CMakeLists.txt
├── src/
│   └── CMakeLists.txt
├── include/
├── tests/
│   ├── CMakeLists.txt
│   ├── unit/
│   │   ├── test_math.cpp
│   │   └── test_string.cpp
│   ├── integration/
│   │   └── test_database.cpp
│   ├── system/
│   │   └── test_e2e.cpp
│   ├── fixtures/
│   │   ├── setup_db.cpp
│   │   └── cleanup.cpp
│   └── data/
│       └── test_data.json
└── examples/
```

## Root CMakeLists.txt Setup

```cmake showLineNumbers  title="CMakeLists.txt"
cmake_minimum_required(VERSION 3.15)
project(MyProject VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Options
option(BUILD_TESTS "Build test suite" ON)
option(BUILD_UNIT_TESTS "Build unit tests" ON)
option(BUILD_INTEGRATION_TESTS "Build integration tests" ON)
option(BUILD_SYSTEM_TESTS "Build system tests" OFF)

# Main library
add_subdirectory(src)

# Testing
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
```

This gives users control over what gets built and tested.

## Test Directory Organization

```cmake showLineNumbers  title="tests/CMakeLists.txt"
# Fetch testing framework
include(FetchContent)

FetchContent_Declare(
    catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.3.2
    GIT_SHALLOW ON
)

set(CATCH_CONFIG_FAST_COMPILE ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(catch2)

# Include Catch2 integration
list(APPEND CMAKE_MODULE_PATH ${catch2_SOURCE_DIR}/extras)
include(Catch)

# Unit tests
if(BUILD_UNIT_TESTS)
    add_subdirectory(unit)
endif()

# Integration tests
if(BUILD_INTEGRATION_TESTS)
    add_subdirectory(integration)
endif()

# System tests
if(BUILD_SYSTEM_TESTS)
    add_subdirectory(system)
endif()

# Test utilities
add_subdirectory(fixtures)
```

## Unit Tests

Fast, isolated tests for individual components:

```cmake showLineNumbers  title="tests/unit/CMakeLists.txt"
add_executable(unit_tests
    test_math.cpp
    test_string_utils.cpp
    test_parser.cpp
)

target_link_libraries(unit_tests PRIVATE
    MyProject::core
    Catch2::Catch2WithMain
)

# Discover individual test cases
catch_discover_tests(unit_tests
    TEST_PREFIX "Unit."
    PROPERTIES
        LABELS "unit;fast"
        TIMEOUT 5
)
```

**Characteristics:**

- Fast execution (< 5 seconds)
- No external dependencies
- Mock all I/O and external services
- High test count

## Integration Tests

Test component interactions:

```cmake showLineNumbers  title="tests/integration/CMakeLists.txt"
add_executable(integration_tests
    test_database.cpp
    test_api_client.cpp
    test_file_processor.cpp
)

target_link_libraries(integration_tests PRIVATE
    MyProject::core
    MyProject::database
    MyProject::network
    Catch2::Catch2WithMain
)

catch_discover_tests(integration_tests
    TEST_PREFIX "Integration."
    PROPERTIES
        LABELS "integration;medium"
        TIMEOUT 30
        COST 50
)

# Copy test data
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/data
    DESTINATION ${CMAKE_CURRENT_BINARY_DIR}
)
```

**Characteristics:**

- Moderate execution time (< 30 seconds)
- May use real databases, files, networks
- Test multiple components together
- Medium test count

## System/End-to-End Tests

Test the complete system:

```cmake showLineNumbers  title="tests/system/CMakeLists.txt"
add_executable(system_tests
    test_full_workflow.cpp
    test_performance.cpp
)

target_link_libraries(system_tests PRIVATE
    MyProject::core
    MyProject::ui
    MyProject::database
    Catch2::Catch2WithMain
)

catch_discover_tests(system_tests
    TEST_PREFIX "System."
    PROPERTIES
        LABELS "system;slow"
        TIMEOUT 300
        COST 100
)
```

**Characteristics:**

- Slow execution (minutes)
- Full system setup required
- Test real-world scenarios
- Low test count

## Test Fixtures and Helpers

Shared setup/teardown code:

```cmake showLineNumbers  title="tests/fixtures/CMakeLists.txt"
add_library(test_fixtures STATIC
    test_database.cpp
    test_server.cpp
    mock_services.cpp
)

target_link_libraries(test_fixtures PUBLIC
    MyProject::core
)

target_include_directories(test_fixtures PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)
```

**Usage in tests:**

```cmake showLineNumbers 
target_link_libraries(integration_tests PRIVATE
    test_fixtures
    Catch2::Catch2WithMain
)
```

```cpp title="test_fixtures/test_database.h"
class TestDatabase {
public:
    TestDatabase() {
        // Setup test database
        initTestDB();
    }
    
    ~TestDatabase() {
        // Cleanup
        cleanupTestDB();
    }
    
    void reset() {
        // Reset state between tests
    }
};
```

## Separate Test Executables

For better organization and parallel execution:

```cmake showLineNumbers  title="tests/unit/CMakeLists.txt"
# Math tests
add_executable(math_tests test_math.cpp)
target_link_libraries(math_tests PRIVATE MyProject::core Catch2::Catch2WithMain)
catch_discover_tests(math_tests TEST_PREFIX "Math.")

# String tests
add_executable(string_tests test_string.cpp)
target_link_libraries(string_tests PRIVATE MyProject::core Catch2::Catch2WithMain)
catch_discover_tests(string_tests TEST_PREFIX "String.")

# File tests
add_executable(file_tests test_file.cpp)
target_link_libraries(file_tests PRIVATE MyProject::core Catch2::Catch2WithMain)
catch_discover_tests(file_tests TEST_PREFIX "File.")
```

**Benefits:**

- Faster compilation (changes to one don't rebuild all)
- Better parallelization
- Clearer organization
- Easier to run specific test suites

## Test Data Management

### Copying Test Data

```cmake showLineNumbers 
# Copy entire directory
file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/data
    DESTINATION ${CMAKE_CURRENT_BINARY_DIR}
)

# Or use configure_file for specific files
configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/data/config.json
    ${CMAKE_CURRENT_BINARY_DIR}/data/config.json
    COPYONLY
)
```

### Generating Test Data

```cmake showLineNumbers 
add_custom_command(
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/test_data.bin
    COMMAND python3 ${CMAKE_CURRENT_SOURCE_DIR}/generate_data.py
        ${CMAKE_CURRENT_BINARY_DIR}/test_data.bin
    DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/generate_data.py
    COMMENT "Generating test data..."
)

add_custom_target(generate_test_data ALL
    DEPENDS ${CMAKE_CURRENT_BINARY_DIR}/test_data.bin
)

add_dependencies(integration_tests generate_test_data)
```

## Test Dependencies

Ensure tests run in correct order:

```cmake showLineNumbers 
# Setup fixture
add_executable(setup_db tests/fixtures/setup_db.cpp)
add_test(NAME DbSetup COMMAND setup_db)
set_tests_properties(DbSetup PROPERTIES
    FIXTURES_SETUP Database
)

# Cleanup fixture
add_executable(cleanup_db tests/fixtures/cleanup_db.cpp)
add_test(NAME DbCleanup COMMAND cleanup_db)
set_tests_properties(DbCleanup PROPERTIES
    FIXTURES_CLEANUP Database
)

# Tests requiring database
catch_discover_tests(integration_tests
    PROPERTIES FIXTURES_REQUIRED "Database"
)
```

**Execution order:**

1. DbSetup runs once
2. All integration tests run (in parallel if using `ctest -j`)
3. DbCleanup runs once (even if tests fail)

## Coverage Integration

### GCC/Clang (gcov/lcov)

```cmake showLineNumbers  title="cmake/CodeCoverage.cmake"
option(ENABLE_COVERAGE "Enable coverage reporting" OFF)

if(ENABLE_COVERAGE)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        # Add coverage flags
        add_compile_options(--coverage -O0 -g)
        add_link_options(--coverage)
    else()
        message(WARNING "Coverage not supported for this compiler")
    endif()
endif()
```

```cmake showLineNumbers  title="CMakeLists.txt"
include(cmake/CodeCoverage.cmake)

if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
    
    # Coverage target
    if(ENABLE_COVERAGE)
        add_custom_target(coverage
            COMMAND ${CMAKE_CTEST_COMMAND}
            COMMAND lcov --capture
                --directory ${CMAKE_BINARY_DIR}
                --output-file coverage.info
            COMMAND lcov --remove coverage.info
                '/usr/*' '*/tests/*'
                --output-file coverage.info
            COMMAND genhtml coverage.info
                --output-directory coverage_html
            WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
            COMMENT "Generating coverage report..."
        )
    endif()
endif()
```

**Usage:**

```bash
cmake -DENABLE_COVERAGE=ON -DCMAKE_BUILD_TYPE=Debug -B build
cmake --build build
cd build
ctest
cmake --build . --target coverage
# Open coverage_html/index.html
```

## Memory Checking

### Valgrind Integration

```cmake showLineNumbers 
find_program(VALGRIND_PROGRAM valgrind)

if(VALGRIND_PROGRAM)
    add_custom_target(memcheck
        COMMAND ${CMAKE_CTEST_COMMAND}
            --force-new-ctest-process
            --test-action memcheck
            --output-on-failure
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
        COMMENT "Running tests with Valgrind..."
    )
    
    # Configure CTest to use Valgrind
    set(MEMORYCHECK_COMMAND ${VALGRIND_PROGRAM})
    set(MEMORYCHECK_COMMAND_OPTIONS
        "--leak-check=full --show-leak-kinds=all --track-origins=yes --error-exitcode=1"
    )
endif()
```

**Usage:**

```bash
cmake --build build --target memcheck
```

### AddressSanitizer

```cmake showLineNumbers 
option(ENABLE_ASAN "Enable AddressSanitizer" OFF)

if(ENABLE_ASAN)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        add_compile_options(-fsanitize=address -fno-omit-frame-pointer)
        add_link_options(-fsanitize=address)
    endif()
endif()
```

```bash
cmake -DENABLE_ASAN=ON -B build
cmake --build build
cd build
ctest
```

## Continuous Integration

### GitHub Actions

```yaml title=".github/workflows/tests.yml"
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure
      run: cmake -B build -DBUILD_TESTS=ON
    
    - name: Build
      run: cmake --build build -j$(nproc)
    
    - name: Test
      run: |
        cd build
        ctest --output-on-failure -j$(nproc)
```

### GitLab CI

```yaml title=".gitlab-ci.yml"
test:
  image: ubuntu:22.04
  
  before_script:
    - apt-get update
    - apt-get install -y cmake g++ git
  
  script:
    - cmake -B build -DBUILD_TESTS=ON
    - cmake --build build -j$(nproc)
    - cd build
    - ctest --output-junit results.xml --output-on-failure
  
  artifacts:
    reports:
      junit: build/results.xml
```

## Test Execution Strategies

### Quick Smoke Test

```bash
# Run only fast unit tests
ctest -L unit -j8

# Or specific pattern
ctest -R "Unit\." --output-on-failure
```

### Full Test Suite

```bash
# All tests, parallel, with output on failure
ctest -j8 --output-on-failure

# With timeout safeguard
ctest -j8 --timeout 300 --output-on-failure
```

### Continuous Integration

```bash
# Generate JUnit XML for CI system
ctest --output-junit results.xml --output-on-failure

# Return code: 0 = all passed, non-zero = failures
ctest || exit 1
```

## Performance Testing

```cmake showLineNumbers 
add_executable(perf_tests
    tests/performance/bench_math.cpp
    tests/performance/bench_parsing.cpp
)

target_link_libraries(perf_tests PRIVATE
    MyProject::core
    Catch2::Catch2WithMain
)

add_test(NAME Performance COMMAND perf_tests)

set_tests_properties(Performance PROPERTIES
    LABELS "performance;benchmark"
    TIMEOUT 600
)
```

Run separately from regular tests:

```bash
ctest -L benchmark
```

## Complete Integration Example

```cmake showLineNumbers  title="Project Root"
cmake_minimum_required(VERSION 3.15)
project(CompleteExample VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 17)

# Options
option(BUILD_TESTS "Build tests" ON)
option(ENABLE_COVERAGE "Enable coverage" OFF)
option(ENABLE_ASAN "Enable AddressSanitizer" OFF)

# Coverage setup
if(ENABLE_COVERAGE AND BUILD_TESTS)
    add_compile_options(--coverage -O0 -g)
    add_link_options(--coverage)
endif()

# AddressSanitizer
if(ENABLE_ASAN AND BUILD_TESTS)
    add_compile_options(-fsanitize=address -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address)
endif()

# Main library
add_subdirectory(src)

# Tests
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
```

```cmake showLineNumbers  title="tests/CMakeLists.txt"
# Fetch Catch2
include(FetchContent)
FetchContent_Declare(
    catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.3.2
)
FetchContent_MakeAvailable(catch2)
include(Catch)

# Test fixtures library
add_library(test_fixtures STATIC
    fixtures/test_utils.cpp
)
target_link_libraries(test_fixtures PUBLIC CompleteExample::core)

# Unit tests
add_executable(unit_tests
    unit/test_math.cpp
    unit/test_string.cpp
)
target_link_libraries(unit_tests PRIVATE
    CompleteExample::core
    test_fixtures
    Catch2::Catch2WithMain
)
catch_discover_tests(unit_tests
    TEST_PREFIX "Unit."
    PROPERTIES LABELS "unit;fast" TIMEOUT 10
)

# Integration tests
add_executable(integration_tests
    integration/test_database.cpp
)
target_link_libraries(integration_tests PRIVATE
    CompleteExample::core
    test_fixtures
    Catch2::Catch2WithMain
)
catch_discover_tests(integration_tests
    TEST_PREFIX "Integration."
    PROPERTIES LABELS "integration;medium" TIMEOUT 60
)
```

## Best Practices

:::success Test Integration Guidelines

1. **Separate test types** - unit, integration, system in different directories
2. **Label everything** - easy to filter and run specific test types
3. **Set appropriate timeouts** - prevent hanging builds
4. **Use fixtures** - for shared setup/teardown
5. **Parallel execution** - faster feedback with `ctest -j`
6. **Make tests optional** - `option(BUILD_TESTS)` for users
7. **Copy test data** - ensure tests have required resources
8. **CI integration** - generate JUnit XML for reporting
9. **Coverage tracking** - know what's tested
10. **Memory checking** - catch leaks and errors early
    :::

## Quick Reference

```cmake showLineNumbers 
# Enable testing
enable_testing()

# Test organization
option(BUILD_TESTS "Build tests" ON)
option(BUILD_UNIT_TESTS "Build unit tests" ON)

# Test fixtures
set_tests_properties(test PROPERTIES
    FIXTURES_SETUP SetupName
    FIXTURES_CLEANUP CleanupName
    FIXTURES_REQUIRED RequiredName
)

# Labels
set_tests_properties(test PROPERTIES
    LABELS "unit;fast"
)

# Coverage
add_compile_options(--coverage -O0 -g)
add_link_options(--coverage)

# Sanitizers
add_compile_options(-fsanitize=address)
add_link_options(-fsanitize=address)
```

```bash
# Run tests
ctest -L unit -j8                    # Unit tests in parallel
ctest -LE slow --output-on-failure   # Exclude slow tests
ctest --output-junit results.xml     # CI integration
```

Good test integration makes testing fast, reliable, and part of your normal development workflow.
