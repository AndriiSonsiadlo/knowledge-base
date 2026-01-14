---
id: ctest-basics
title: CTest Basics
sidebar_label: CTest Basics
sidebar_position: 1
tags: [cmake, ctest, testing, unit-tests]
---

# CTest Basics

## What is CTest?

CTest is CMake's testing tool that runs tests and reports results. It's integrated with CMake, making it easy to define, build, and run tests as part of your project. While you can use any testing framework (Google Test, Catch2, etc.), CTest provides the infrastructure to execute and aggregate results.

**Key benefits:**

- Simple integration with CMake
- Works with any testing framework
- Parallel test execution
- Flexible result reporting
- CI/CD friendly output

## Enabling Testing

Enable CTest in your project:

```cmake
cmake_minimum_required(VERSION 3.15)
project(MyProject)

# Enable testing
enable_testing()

# Now you can add tests
add_subdirectory(tests)
```

`enable_testing()` must be called in the **root** `CMakeLists.txt` to enable testing for the entire project.

## Adding Tests

### Basic add_test()

The fundamental command for defining tests:

```cmake
add_test(
    NAME test_name
    COMMAND executable arg1 arg2
)
```

**Simple example:**

```cmake
add_executable(test_math test_math.cpp)
target_link_libraries(test_math PRIVATE mylib)

add_test(NAME MathTests COMMAND test_math)
```

### Test with Arguments

```cmake
add_test(NAME test_with_args 
    COMMAND mytest --verbose --iterations=100
)
```

### Working Directory

Set where the test runs:

```cmake
add_test(NAME test_needs_data 
    COMMAND mytest
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/test_data
)
```

## Running Tests

After configuring and building:

```bash
# Run all tests
ctest

# Or from build directory
cd build
ctest

# Verbose output
ctest -V
ctest --verbose

# Show only failures
ctest --output-on-failure

# Parallel execution
ctest -j8
ctest --parallel 8
```

**Output example:**

```
Test project /path/to/build
    Start 1: MathTests
1/3 Test #1: MathTests ........................   Passed    0.01 sec
    Start 2: StringTests
2/3 Test #2: StringTests ......................   Passed    0.02 sec
    Start 3: IntegrationTests
3/3 Test #3: IntegrationTests .................   Passed    0.15 sec

100% tests passed, 0 tests failed out of 3
```

## Test Properties

Configure test behavior with properties:

```cmake
add_test(NAME mytest COMMAND mytest)

set_tests_properties(mytest PROPERTIES
    TIMEOUT 30                    # Fail if takes longer than 30s
    WILL_FAIL TRUE               # Expect test to fail
    PASS_REGULAR_EXPRESSION "Success"  # Must contain "Success"
    FAIL_REGULAR_EXPRESSION "Error"    # Fail if contains "Error"
)
```

### Common Properties

```cmake
# Timeout (seconds)
set_tests_properties(slow_test PROPERTIES TIMEOUT 300)

# Expected to fail
set_tests_properties(known_bug PROPERTIES WILL_FAIL TRUE)

# Environment variables
set_tests_properties(mytest PROPERTIES
    ENVIRONMENT "TEST_MODE=1;DEBUG_LEVEL=2"
)

# Test dependencies (run after other tests)
set_tests_properties(integration_test PROPERTIES
    DEPENDS unit_test
)

# Cost (higher runs first for better parallelization)
set_tests_properties(slow_test PROPERTIES COST 100)
set_tests_properties(fast_test PROPERTIES COST 1)

# Labels for grouping
set_tests_properties(mytest PROPERTIES LABELS "unit;math")
```

## Test Fixtures

Run setup/cleanup code before/after tests:

```cmake
# Setup fixture
add_test(NAME db_setup COMMAND setup_database)
set_tests_properties(db_setup PROPERTIES FIXTURES_SETUP Database)

# Cleanup fixture
add_test(NAME db_cleanup COMMAND cleanup_database)
set_tests_properties(db_cleanup PROPERTIES FIXTURES_CLEANUP Database)

# Test requires fixture
add_test(NAME query_test COMMAND test_queries)
set_tests_properties(query_test PROPERTIES FIXTURES_REQUIRED Database)
```

**Execution order:**

1. `db_setup` runs
2. `query_test` runs
3. `db_cleanup` runs (even if test fails)

Multiple tests can share the same fixture.

## Using Testing Frameworks

### Catch2

```cmake
include(FetchContent)

FetchContent_Declare(
    catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.3.2
)
FetchContent_MakeAvailable(catch2)

add_executable(tests
    test_math.cpp
    test_string.cpp
)

target_link_libraries(tests PRIVATE
    mylib
    Catch2::Catch2WithMain
)

# Simple approach
add_test(NAME AllTests COMMAND tests)

# Or discover tests automatically
include(Catch)
catch_discover_tests(tests)
```

With `catch_discover_tests()`, each TEST_CASE becomes a separate CTest test.

### Google Test

```cmake
include(FetchContent)

FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)
FetchContent_MakeAvailable(googletest)

add_executable(tests
    test_math.cpp
    test_string.cpp
)

target_link_libraries(tests PRIVATE
    mylib
    GTest::gtest_main
)

# Discover tests
include(GoogleTest)
gtest_discover_tests(tests)
```

### doctest

```cmake
FetchContent_Declare(
    doctest
    GIT_REPOSITORY https://github.com/doctest/doctest.git
    GIT_TAG v2.4.11
)
FetchContent_MakeAvailable(doctest)

add_executable(tests test_main.cpp)
target_link_libraries(tests PRIVATE mylib doctest::doctest)

include(doctest)
doctest_discover_tests(tests)
```

## Organizing Tests

### Multiple Test Executables

```cmake
# Unit tests
add_executable(unit_tests
    test_math.cpp
    test_string.cpp
)
target_link_libraries(unit_tests PRIVATE mylib Catch2::Catch2WithMain)
add_test(NAME UnitTests COMMAND unit_tests)

# Integration tests
add_executable(integration_tests
    test_integration.cpp
)
target_link_libraries(integration_tests PRIVATE mylib Catch2::Catch2WithMain)
add_test(NAME IntegrationTests COMMAND integration_tests)

# Mark integration as slow
set_tests_properties(IntegrationTests PROPERTIES
    COST 100
    LABELS "integration"
)
```

### Test Directory Structure

```
tests/
├── CMakeLists.txt
├── unit/
│   ├── test_math.cpp
│   └── test_string.cpp
├── integration/
│   └── test_system.cpp
└── data/
    └── test_input.txt
```

```cmake title="tests/CMakeLists.txt"
# Unit tests
add_executable(unit_tests
    unit/test_math.cpp
    unit/test_string.cpp
)
target_link_libraries(unit_tests PRIVATE mylib Catch2::Catch2WithMain)
catch_discover_tests(unit_tests)

# Integration tests
add_executable(integration_tests
    integration/test_system.cpp
)
target_link_libraries(integration_tests PRIVATE mylib Catch2::Catch2WithMain)
catch_discover_tests(integration_tests)
```

## Filtering Tests

Run specific tests:

```bash
# By name pattern
ctest -R Math          # Run tests matching "Math"
ctest -E Slow          # Exclude tests matching "Slow"

# By label
ctest -L unit          # Run tests labeled "unit"
ctest -LE integration  # Exclude integration tests

# Combine filters
ctest -R Math -L unit  # Math tests that are unit tests

# Run specific test by number
ctest -I 1,5           # Run tests 1-5
```

## Test Output

Control output verbosity:

```bash
# Minimal (default)
ctest

# Show test output on failure
ctest --output-on-failure

# Verbose (all output)
ctest -V
ctest --verbose

# Extra verbose (includes test command)
ctest -VV

# Quiet (just summary)
ctest -Q
```

## Configuration-Aware Testing

Handle different build types:

```cmake
add_test(NAME mytest COMMAND mytest)

# Different timeout per configuration
set_tests_properties(mytest PROPERTIES
    TIMEOUT_DEBUG 60
    TIMEOUT_RELEASE 30
)
```

Run tests for specific configuration:

```bash
# Multi-config generators (Visual Studio, Xcode)
ctest -C Debug
ctest -C Release

# Single-config generators (Unix Makefiles)
cmake -DCMAKE_BUILD_TYPE=Debug ..
ctest
```

## Rerunning Failed Tests

```bash
# Run only tests that failed last time
ctest --rerun-failed

# Useful workflow:
ctest                    # Run all tests
ctest --rerun-failed -V  # Debug failures with verbose output
```

## Test Timeout

Set global timeout for all tests:

```bash
# Timeout after 60 seconds per test
ctest --timeout 60
```

Or per-test:

```cmake
set_tests_properties(slow_test PROPERTIES TIMEOUT 300)
```

## Practical Example

Complete test setup:

```cmake title="CMakeLists.txt"
cmake_minimum_required(VERSION 3.15)
project(MyProject VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 17)

option(BUILD_TESTS "Build tests" ON)

# Library
add_library(mylib
    src/math.cpp
    src/string_utils.cpp
)

target_include_directories(mylib PUBLIC include)

# Enable testing
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
```

```cmake title="tests/CMakeLists.txt"
# Fetch Catch2
include(FetchContent)
FetchContent_Declare(
    catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.3.2
)
FetchContent_MakeAvailable(catch2)

# Unit tests
add_executable(unit_tests
    unit/test_math.cpp
    unit/test_string.cpp
)

target_link_libraries(unit_tests PRIVATE
    mylib
    Catch2::Catch2WithMain
)

# Discover individual test cases
include(Catch)
catch_discover_tests(unit_tests
    TEST_PREFIX "Unit."
    PROPERTIES LABELS "unit"
)

# Integration test
add_executable(integration_test
    integration/test_full_system.cpp
)

target_link_libraries(integration_test PRIVATE
    mylib
    Catch2::Catch2WithMain
)

add_test(NAME Integration COMMAND integration_test)

set_tests_properties(Integration PROPERTIES
    LABELS "integration"
    TIMEOUT 60
    COST 100
)
```

**Running:**

```bash
cd build
cmake -DBUILD_TESTS=ON ..
cmake --build .

# All tests
ctest

# Just unit tests
ctest -L unit

# Parallel, verbose on failure
ctest -j8 --output-on-failure
```

## CI/CD Integration

CTest generates machine-readable output:

```bash
# JUnit XML format (for Jenkins, GitLab CI)
ctest --output-junit results.xml

# Return non-zero on test failure
ctest || exit 1
```

**GitHub Actions example:**

```yaml
- name: Build
  run: cmake --build build

- name: Test
  run: |
    cd build
    ctest --output-on-failure
```

**GitLab CI example:**

```yaml
test:
  script:
    - cmake --build build
    - cd build
    - ctest --output-junit results.xml
  artifacts:
    reports:
      junit: build/results.xml
```

## Dashboard Reporting

CTest can submit results to CDash (CMake's dashboard system):

```cmake
include(CTest)  # Instead of enable_testing()

set(CTEST_PROJECT_NAME "MyProject")
```

```bash
ctest -D Experimental  # Run and submit to dashboard
```

## Best Practices

:::success Testing Guidelines

1. **Enable testing conditionally** - users may not want tests

   ```cmake
   option(BUILD_TESTS "Build tests" ON)
   ```

2. **Use test discovery** - automatic registration of test cases

   ```cmake
   catch_discover_tests(tests)
   ```

3. **Label your tests** - easy filtering

   ```cmake
   set_tests_properties(mytest PROPERTIES LABELS "unit;math")
   ```

4. **Set timeouts** - prevent hanging tests

   ```cmake
   set_tests_properties(mytest PROPERTIES TIMEOUT 30)
   ```

5. **Organize by type** - unit, integration, system tests separate

6. **Use fixtures** - for setup/teardown

   ```cmake
   FIXTURES_SETUP, FIXTURES_CLEANUP, FIXTURES_REQUIRED
   ```

7. **Test in parallel** - faster feedback

   ```bash
   ctest -j8
   ```

8. **Output on failure** - easier debugging

   ```bash
   ctest --output-on-failure
   ```

:::

## Common Issues

:::warning Troubleshooting

**Tests not found:**

- Ensure `enable_testing()` is in root CMakeLists.txt
- Check tests are actually added with `add_test()`
- Re-configure CMake after adding tests

**Tests fail but work manually:**

- Check working directory with `WORKING_DIRECTORY` property
- Set environment variables with `ENVIRONMENT` property
- Verify paths in test executable

**Timeouts:**

- Increase timeout: `set_tests_properties(test PROPERTIES TIMEOUT 60)`
- Or globally: `ctest --timeout 120`

**Tests hang:**

- Add timeouts to all tests
- Check for deadlocks or infinite loops
- Use `ctest --timeout` as safeguard
  :::

## Quick Reference

```cmake
# Enable testing
enable_testing()

# Add test
add_test(NAME test_name COMMAND executable)

# Test properties
set_tests_properties(test PROPERTIES
    TIMEOUT 30
    LABELS "unit;math"
    WILL_FAIL FALSE
    COST 10
)

# Fixtures
set_tests_properties(test PROPERTIES
    FIXTURES_SETUP SetupName
    FIXTURES_CLEANUP CleanupName
    FIXTURES_REQUIRED FixtureName
)
```

```bash
# Run tests
ctest
ctest -j8                      # Parallel
ctest --output-on-failure      # Show output on fail
ctest -R pattern               # Run matching tests
ctest -L label                 # Run labeled tests
ctest --rerun-failed           # Retry failures
ctest -V                       # Verbose
```

CTest provides a simple but powerful testing infrastructure that integrates seamlessly with CMake and works with any testing framework.
