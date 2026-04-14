---
id: gtest-basics
title: GTest Basics
sidebar_label: GTest Basics
sidebar_position: 1
tags: [gtest, googletest, testing, unit-test, assertions]
---

# GTest Basics

Google Test (GTest) is Google's C++ testing framework. Tests are plain functions wrapped in macros; GTest collects them automatically and reports failures with file name, line number, and the expected vs. actual values.

## Setup

### CMake (FetchContent)

The recommended approach: CMake downloads GTest at configure time, so there is no manual install. `gtest_discover_tests` registers each `TEST()`/`TEST_F()` as a separate CTest target, enabling per-test filtering and parallel runs.

```cmake
include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
)
FetchContent_MakeAvailable(googletest)

add_executable(my_tests test_foo.cpp)
target_link_libraries(my_tests GTest::gtest_main)

include(GoogleTest)
gtest_discover_tests(my_tests)
```

### Package manager

```bash
# vcpkg
vcpkg install gtest

# apt
sudo apt install libgtest-dev
```

## Test Structure

A test is declared with `TEST(SuiteName, TestName)`. Suite groups related tests; name describes what this specific case verifies. GTest discovers all tests at link time — no registration needed. Linking against `GTest::gtest_main` provides a `main()` that initializes GTest and runs all tests, so you only need to write one if you want custom initialization logic.

```cpp
#include <gtest/gtest.h>

TEST(MathTest, AddsTwoIntegers) {
    EXPECT_EQ(2 + 2, 4);
}

TEST(MathTest, DividesCorrectly) {
    EXPECT_DOUBLE_EQ(10.0 / 3.0, 10.0 / 3.0);
}

// Only needed if you want custom init before RUN_ALL_TESTS
int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
```

## Assertions

GTest provides two flavors for every assertion:

- `EXPECT_*` — records failure and **continues** the test. Use when a failed check doesn't invalidate the rest of the test.
- `ASSERT_*` — records failure and **aborts the current test immediately**. Use when a failed check would make subsequent code crash or produce meaningless results (e.g., a null pointer dereference).

### Equality / Comparison

These work with any type that has the corresponding operator defined.

```cpp
EXPECT_EQ(a, b);      // a == b
EXPECT_NE(a, b);      // a != b
EXPECT_LT(a, b);      // a <  b
EXPECT_LE(a, b);      // a <= b
EXPECT_GT(a, b);      // a >  b
EXPECT_GE(a, b);      // a >= b
```

### Boolean

```cpp
EXPECT_TRUE(condition);
EXPECT_FALSE(condition);
```

### Floating point

Never use `EXPECT_EQ` for floats — rounding makes exact equality unreliable. GTest provides ULP-based comparison (4 ULPs by default) and an absolute-error variant.

```cpp
EXPECT_FLOAT_EQ(a, b);       // within 4 ULPs (float precision)
EXPECT_DOUBLE_EQ(a, b);      // within 4 ULPs (double precision)
EXPECT_NEAR(a, b, abs_err);  // |a - b| <= abs_err (explicit tolerance)
```

### Strings

For C-style strings (`char*`), use the `STR` variants — they compare content, not pointer addresses. For `std::string`, `EXPECT_EQ` works fine.

```cpp
EXPECT_STREQ(c_str1, c_str2);     // strcmp == 0
EXPECT_STRNE(c_str1, c_str2);
EXPECT_STRCASEEQ(c_str1, c_str2); // case-insensitive
// For std::string just use EXPECT_EQ
```

### Exceptions

These test that code throws (or doesn't). The expression is executed inside the macro; the test doesn't crash if an exception is thrown.

```cpp
EXPECT_THROW(expr, ExceptionType); // throws exactly ExceptionType (or subclass)
EXPECT_NO_THROW(expr);             // must not throw anything
EXPECT_ANY_THROW(expr);            // must throw something
```

### Death tests

Death tests verify that code terminates the process — useful for testing `assert()`, `std::abort()`, or intentional `exit()` calls. GTest forks a child process, runs the expression there, and checks the outcome.

```cpp
EXPECT_DEATH(expr, regex);      // process crashes, stderr matches regex
EXPECT_EXIT(expr, pred, regex); // process exits, exit code matches predicate
```

### Custom failure message

Any assertion accepts a `<<` chain to attach context shown only on failure. Useful when the assertion values alone don't explain what went wrong.

```cpp
EXPECT_EQ(result, expected) << "Input was: " << input;
```

## Test Fixtures

When multiple tests need the same objects, constructing them in every `TEST()` body is repetitive and error-prone. A fixture centralizes setup and teardown in a class. `SetUp()` runs before each test, `TearDown()` after — each test gets a **fresh** instance, so tests cannot affect each other through shared state.

```cpp
class VectorTest : public ::testing::Test {
protected:
    void SetUp() override {
        v = {1, 2, 3};
    }
    void TearDown() override {
        // optional — destructor also works for cleanup
    }

    std::vector<int> v;
};

// TEST_F takes the fixture class as the first argument instead of a suite name
TEST_F(VectorTest, SizeIsThree) {
    EXPECT_EQ(v.size(), 3u);
}

TEST_F(VectorTest, FirstElementIsOne) {
    EXPECT_EQ(v[0], 1);
}
```

## Parameterized Tests

Parameterized tests run the same test body against a set of inputs, eliminating copy-pasted test cases that differ only in values. Inherit from `::testing::TestWithParam<T>`, retrieve the current value with `GetParam()`, then instantiate with `INSTANTIATE_TEST_SUITE_P`.

```cpp
class EvenTest : public ::testing::TestWithParam<int> {};

TEST_P(EvenTest, IsEven) {
    EXPECT_EQ(GetParam() % 2, 0);
}

INSTANTIATE_TEST_SUITE_P(
    EvenValues,   // instance name (prefix in test output)
    EvenTest,
    ::testing::Values(2, 4, 6, 100)
);
```

**Typed tests** run against multiple *types* rather than multiple values — useful for generic containers or algorithms that should work for `int`, `float`, `std::string`, etc.

```cpp
using MyTypes = ::testing::Types<int, long, float>;
TYPED_TEST_SUITE(FooTest, MyTypes);

TYPED_TEST(FooTest, IsZeroInitialized) {
    TypeParam val{};
    EXPECT_EQ(val, TypeParam{0});
}
```

## Running Tests

The test binary accepts GTest flags directly. No CTest required for development — just run the binary.

```bash
./my_tests                           # run all tests
./my_tests --gtest_filter="Suite.*"  # run all tests in Suite
./my_tests --gtest_filter="-*Death*" # exclude tests matching *Death*
./my_tests --gtest_repeat=10         # repeat all tests 10 times (catch flakiness)
./my_tests --gtest_shuffle           # randomize order (catch order dependencies)
./my_tests --gtest_output=xml:report.xml  # machine-readable output for CI
```

Filter syntax: `SuiteName.TestName`, wildcards `*`, exclude with `-` prefix, separate multiple patterns with `:`.

## Disabling Tests

Prefix a suite or test name with `DISABLED_` to skip it without deleting the code. Disabled tests still compile (so they don't rot silently) but are excluded from runs and listed separately in the output.

```cpp
TEST(DISABLED_FlakyTest, SometimesFails) { ... }
TEST_F(MyFixture, DISABLED_NotImplementedYet) { ... }
```
