---
id: boost-test
title: Boost.Test
sidebar_label: Boost.Test
sidebar_position: 1
tags: [c++, boost, testing, unit-test, test-framework]
---

# Boost.Test

Boost.Test is a **unit testing framework** for C++ that provides test case definition, rich
assertion macros, test organisation into suites, fixtures, and data-driven testing. It was one
of the first full-featured C++ testing frameworks and remains widely used, particularly in
projects that already depend on Boost.

:::info The problem it solves
Writing ad-hoc test harnesses with `assert()` and `main()` gets painful fast: no structured
output, no test isolation, no way to continue after a failure. Boost.Test gives you a framework
that discovers and runs tests automatically, reports results cleanly, and keeps going when one
check fails so you see all failures at once.
:::

## A first test file

```cpp showLineNumbers title="test_math.cpp"
#define BOOST_TEST_MODULE MathTests
#include <boost/test/unit_test.hpp>

BOOST_AUTO_TEST_CASE(addition) {
    BOOST_CHECK_EQUAL(2 + 2, 4);
    BOOST_CHECK_EQUAL(0 + 0, 0);
}

BOOST_AUTO_TEST_CASE(division) {
    BOOST_CHECK_CLOSE(1.0 / 3.0, 0.3333, 0.1);  // tolerance in percent
}
```

```bash
g++ -std=c++17 test_math.cpp -lboost_unit_test_framework -o test_math
./test_math
```

:::note Header-only mode
Boost.Test can run header-only (no linking) if you define `BOOST_TEST_MODULE` before including
`<boost/test/included/unit_test.hpp>` (note the `included/` path). This is convenient for small
projects but increases compile time in larger ones.
:::

## Assertion macros

Boost.Test provides three severity levels for each check:

| Macro | On failure |
|-------|-----------|
| `BOOST_CHECK_*` | Records failure, **continues** running the test |
| `BOOST_REQUIRE_*` | Records failure, **aborts the current test case** |
| `BOOST_WARN_*` | Records a warning, continues (does not count as failure) |

Common assertion variants:

```cpp showLineNumbers
BOOST_CHECK(condition);                 // boolean
BOOST_CHECK_EQUAL(a, b);               // a == b with value printing
BOOST_CHECK_NE(a, b);                  // a != b
BOOST_CHECK_LT(a, b);                  // a < b
BOOST_CHECK_CLOSE(a, b, tolerance);    // floating-point, tolerance in %
BOOST_CHECK_THROW(expr, ExType);       // expr throws ExType
BOOST_CHECK_NO_THROW(expr);            // expr does not throw
BOOST_CHECK_MESSAGE(cond, "msg");      // custom failure message
```

:::danger BOOST_CHECK vs BOOST_REQUIRE
Use `REQUIRE` when a failure makes subsequent checks meaningless (e.g. a pointer is null — no
point dereferencing it). Use `CHECK` by default so the test reports all failures, not just the
first.
:::

## Test suites

Group related test cases into named suites for better organisation and selective execution:

```cpp showLineNumbers title="test_suites.cpp"
#define BOOST_TEST_MODULE MySuites
#include <boost/test/unit_test.hpp>

BOOST_AUTO_TEST_SUITE(StringOps)

BOOST_AUTO_TEST_CASE(empty_string) {
    std::string s;
    BOOST_CHECK(s.empty());
}

BOOST_AUTO_TEST_CASE(concatenation) {
    BOOST_CHECK_EQUAL(std::string("ab") + "cd", "abcd");
}

BOOST_AUTO_TEST_SUITE_END()
```

Run only one suite from the command line: `./test_math --run_test=StringOps`.

## Fixtures

Fixtures set up and tear down shared state for a group of tests:

```cpp showLineNumbers title="test_fixture.cpp"
#define BOOST_TEST_MODULE FixtureDemo
#include <boost/test/unit_test.hpp>
#include <vector>

struct VectorFixture {
    std::vector<int> v;
    VectorFixture() : v{1, 2, 3, 4, 5} {}
};

BOOST_FIXTURE_TEST_CASE(size_check, VectorFixture) {
    BOOST_CHECK_EQUAL(v.size(), 5u);
}

BOOST_FIXTURE_TEST_CASE(front_check, VectorFixture) {
    BOOST_CHECK_EQUAL(v.front(), 1);
}
```

## Data-driven tests

Run the same test logic over multiple data sets:

```cpp showLineNumbers title="test_data.cpp"
#define BOOST_TEST_MODULE DataDriven
#include <boost/test/unit_test.hpp>
#include <boost/test/data/test_case.hpp>
#include <boost/test/data/monomorphic.hpp>

namespace bdata = boost::unit_test::data;

BOOST_DATA_TEST_CASE(squares,
    bdata::make({1, 2, 3, 4}) ^ bdata::make({1, 4, 9, 16}),
    input, expected)
{
    BOOST_CHECK_EQUAL(input * input, expected);
}
```

## Comparison with other frameworks

| Feature | Boost.Test | Google Test | Catch2 |
|---------|-----------|-------------|--------|
| Header-only mode | Yes | No | Yes |
| Auto-registration | Yes | Yes | Yes |
| Fixtures | Yes | Yes | Sections |
| Data-driven | Yes (built-in) | Parameterised | Generators |
| BDD style | No | No | Yes (SCENARIO) |
| Matchers | Limited | Yes (rich) | Yes (rich) |
| Part of Boost | Yes | No | No |

:::tip Choosing a framework
If your project already uses Boost, Boost.Test integrates with zero extra dependencies. For
greenfield projects, Catch2 (header-only, BDD-style sections) and Google Test (rich matchers,
mocking via GMock) are popular alternatives.
:::

## See also

- <Icon icon="lucide:bug" inline /> [Boost.Stacktrace](./boost-stacktrace.md) — capture stack traces in test failure handlers.
- <Icon icon="lucide:file-text" inline /> [Boost.Log](./boost-log.md) — structured logging, useful alongside testing.
- <Icon icon="lucide:shield" inline /> [Boost.Assert](../02-core-utilities/boost-assert.md) — assertion macros for production code.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
