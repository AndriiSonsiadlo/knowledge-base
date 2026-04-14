---
id: advanced-gtest
title: Advanced GTest
sidebar_label: Advanced GTest
sidebar_position: 3
tags: [gtest, custom-matcher, test-environment, suite-setup, listener, coverage]
---

# Advanced GTest

## Suite-Level Setup (SetUpTestSuite)

`SetUp` / `TearDown` run per test. For expensive resources (starting a server, opening a DB connection) that should be shared across all tests in a suite, use the static `SetUpTestSuite` / `TearDownTestSuite` pair. GTest calls these once per fixture class, not once per test.

```cpp
class DatabaseTest : public ::testing::Test {
protected:
    static void SetUpTestSuite() {
        // runs once before any test in DatabaseTest
        db_ = new RealDatabase("test_db");
        db_->Migrate();
    }

    static void TearDownTestSuite() {
        // runs once after all tests in DatabaseTest
        delete db_;
        db_ = nullptr;
    }

    static RealDatabase* db_;
};

RealDatabase* DatabaseTest::db_ = nullptr;

TEST_F(DatabaseTest, InsertRow) {
    EXPECT_TRUE(db_->Insert({.id = 1, .name = "Alice"}));
}
```

:::caution
Tests sharing state via `SetUpTestSuite` can affect each other. Only use for truly read-only or idempotent resources; for mutable state, prefer per-test `SetUp`.
:::

## Global Test Environment

A `::testing::Environment` runs once for the entire test binary — before any suite's `SetUpTestSuite`. Use it to initialize global resources (e.g., network stack, logging) that every test needs.

```cpp
class GlobalEnv : public ::testing::Environment {
public:
    void SetUp() override {
        Logger::Init("test.log");
    }
    void TearDown() override {
        Logger::Shutdown();
    }
};

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    ::testing::AddGlobalTestEnvironment(new GlobalEnv);
    return RUN_ALL_TESTS();
}
```

## Custom Matchers

When built-in matchers don't express your domain well, define your own. Custom matchers produce readable failure messages and can be composed with `AllOf`, `AnyOf`, etc.

### MATCHER macro (simplest)

```cpp
// MATCHER(Name, description) { return ...; }
MATCHER(IsEven, "is even") {
    return arg % 2 == 0;
}

MATCHER_P(IsDivisibleBy, n, "is divisible by " + ::testing::PrintToString(n)) {
    return arg % n == 0;
}

// Usage
EXPECT_THAT(42, IsEven());
EXPECT_THAT(42, IsDivisibleBy(7));
EXPECT_THAT(std::vector<int>{2, 4, 6}, ::testing::Each(IsEven()));
```

### Full matcher class (for complex logic)

```cpp
class HasValidEmailMatcher {
public:
    using is_gtest_matcher = void;

    bool MatchAndExplain(const std::string& s,
                         ::testing::MatchResultListener* listener) const {
        bool valid = s.find('@') != std::string::npos;
        if (!valid) *listener << "missing '@'";
        return valid;
    }

    void DescribeTo(std::ostream* os) const { *os << "is a valid email"; }
    void DescribeNegationTo(std::ostream* os) const { *os << "is not a valid email"; }
};

auto HasValidEmail() {
    return ::testing::MakeMatcher(new HasValidEmailMatcher{});
}

EXPECT_THAT("user@example.com", HasValidEmail());
```

## Parameterized Tests — Custom Names

By default, parameterized test names are `Suite/Instance.Test/0`, `Suite/Instance.Test/1`, etc. Pass a name generator as the fourth argument to `INSTANTIATE_TEST_SUITE_P` for readable names in test output and filters.

```cpp
struct Config {
    int threads;
    bool use_cache;
    std::string name;
};

class PerfTest : public ::testing::TestWithParam<Config> {};

TEST_P(PerfTest, Throughput) {
    auto cfg = GetParam();
    // ...
}

INSTANTIATE_TEST_SUITE_P(
    Configs,
    PerfTest,
    ::testing::Values(
        Config{1, false, "single_no_cache"},
        Config{4, true,  "multi_with_cache"}
    ),
    [](const ::testing::TestParamInfo<Config>& info) {
        return info.param.name;  // used in test name
    }
);
// Produces: Configs/PerfTest.Throughput/single_no_cache
//           Configs/PerfTest.Throughput/multi_with_cache
```

## Test Listeners

Listeners hook into GTest's event stream — test start/end, suite start/end, assertion results. Use them for custom output formats, metrics, or integration with external systems.

```cpp
class TimingListener : public ::testing::EmptyTestEventListener {
public:
    void OnTestStart(const ::testing::TestInfo& info) override {
        start_ = std::chrono::steady_clock::now();
    }

    void OnTestEnd(const ::testing::TestInfo& info) override {
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start_).count();
        if (ms > 100) {
            std::cerr << "[SLOW] " << info.name() << " took " << ms << "ms\n";
        }
    }

private:
    std::chrono::steady_clock::time_point start_;
};

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    ::testing::TestEventListeners& listeners =
        ::testing::UnitTest::GetInstance()->listeners();
    listeners.Append(new TimingListener);
    return RUN_ALL_TESTS();
}
```

## Code Coverage

GTest doesn't measure coverage itself — that's the compiler's job. Compile with coverage instrumentation, run the tests, then generate a report.

```bash
# Compile with coverage (GCC/Clang)
g++ -fprofile-arcs -ftest-coverage -O0 -g test.cpp -o test -lgtest_main

# Run tests (generates .gcda files)
./test

# Generate report with gcov
gcov test.cpp

# Or use lcov for HTML report
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_html
```

With CMake, enable via a coverage preset or toolchain:
```cmake
target_compile_options(my_tests PRIVATE --coverage)
target_link_options(my_tests PRIVATE --coverage)
```

:::tip
Use `--gtest_filter` to run specific tests when debugging coverage gaps — no need to rebuild.
:::

## Running with CTest

After `gtest_discover_tests(my_tests)`, each `TEST()` becomes an individual CTest. CTest supports parallel execution, retry on failure, and timeout per test.

```bash
ctest --test-dir build -j8              # parallel, 8 jobs
ctest --test-dir build -R "MathTest"    # filter by regex
ctest --test-dir build --rerun-failed   # only run previously failing
ctest --test-dir build --output-on-failure
ctest --test-dir build --timeout 30     # 30s max per test
```

CTest also produces JUnit XML for CI:
```bash
ctest --test-dir build --output-junit report.xml
```
