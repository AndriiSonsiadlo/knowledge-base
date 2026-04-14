---
id: test-patterns
title: Test Patterns and Best Practices
sidebar_label: Test Patterns
sidebar_position: 4
tags: [testing, patterns, tdd, aaa, test-doubles, fake, stub, spy, best-practices]
---

# Test Patterns and Best Practices

## Test Doubles Taxonomy

"Mock" is often used loosely to mean any fake dependency. The precise terms matter because they imply different verification strategies.

| Type | What it does | Verified how |
|------|-------------|--------------|
| **Dummy** | Passed but never used; fills required parameters | Not verified |
| **Stub** | Returns canned values; no call verification | State (assert on output) |
| **Fake** | Real working implementation, simplified (e.g., in-memory DB) | State |
| **Spy** | Real implementation that also records calls | Both state and calls |
| **Mock** | Pre-programmed with expectations; fails if not met | Call verification (GMock) |

Choose based on what you're testing: if you care **what** the dependency returns, use a stub or fake; if you care **whether** it was called correctly, use a mock.

### Fake example — in-memory database

```cpp
class FakeDatabase : public IDatabase {
public:
    bool Connect(const std::string&) override { return true; }
    std::string Query(const std::string& sql) override {
        auto it = data_.find(sql);
        return it != data_.end() ? it->second : "";
    }
    void Disconnect() override {}

    void Seed(const std::string& key, const std::string& val) {
        data_[key] = val;
    }
private:
    std::map<std::string, std::string> data_;
};
```

Fakes are more work to write but make tests more realistic and less brittle than mocks.

## AAA Pattern (Arrange-Act-Assert)

Structure every test in three phases. Keep them visually separated — it makes the test intent obvious at a glance.

```cpp
TEST_F(OrderTest, AppliesDiscountForLoyalCustomer) {
    // Arrange
    Customer customer{.id = 1, .loyalty_years = 5};
    Order order{.customer = customer, .subtotal = 100.0};

    // Act
    double total = pricing_.Calculate(order);

    // Assert
    EXPECT_DOUBLE_EQ(total, 90.0);  // 10% loyalty discount
}
```

Avoid interleaving assertions with actions — a failure mid-test hides subsequent state.

## F.I.R.S.T Principles

Good unit tests follow these properties:

| Letter | Meaning | Violation sign |
|--------|---------|---------------|
| **F**ast | Runs in milliseconds | Hits network, disk, sleeps |
| **I**solated | No shared state between tests | Test passes alone but fails in suite |
| **R**epeatable | Same result every run | Depends on time, random seed, env vars |
| **S**elf-validating | Pass/fail without manual inspection | Writes output you manually check |
| **T**imely | Written with (or before) the code | Tests added months after as an afterthought |

## What to Test

Focus tests on **behavior visible through the public interface**, not implementation details. Testing internals makes refactoring painful without adding safety.

**Test:**
- Return values for various inputs (including boundary and error cases)
- State changes observable through getters or output
- Exceptions thrown under specific conditions
- Interactions with dependencies when those interactions are the contract (use mocks only then)

**Don't test:**
- Private methods directly — test them through the public API that calls them
- Implementation details — a sort algorithm test shouldn't care whether it uses insertion sort or quicksort internally
- Trivial getters/setters with no logic
- Third-party library behavior — assume it works

## Test Naming

A test name should read as a sentence describing the expected behavior. The pattern **`MethodName_StateUnderTest_ExpectedBehavior`** or **`does_X_when_Y`** both work — pick one and be consistent.

```cpp
// Bad — tells you nothing about what broke
TEST(CalcTest, Test1) { ... }

// Good — readable as a specification
TEST(Calculator, Divide_ByZero_ThrowsInvalidArgument) { ... }
TEST(Calculator, Add_NegativeNumbers_ReturnsCorrectSum) { ... }
TEST_F(UserServiceTest, CreateUser_DuplicateEmail_ReturnsFalse) { ... }
```

## Boundary and Edge Cases

Most bugs live at boundaries. For any range `[a, b]`, test at least: below `a`, exactly `a`, middle, exactly `b`, above `b`.

```cpp
TEST(ClampTest, BelowMinReturnsMin)    { EXPECT_EQ(Clamp(-1, 0, 10), 0);  }
TEST(ClampTest, AtMinReturnsMin)       { EXPECT_EQ(Clamp(0,  0, 10), 0);  }
TEST(ClampTest, InRangePassesThrough)  { EXPECT_EQ(Clamp(5,  0, 10), 5);  }
TEST(ClampTest, AtMaxReturnsMax)       { EXPECT_EQ(Clamp(10, 0, 10), 10); }
TEST(ClampTest, AboveMaxReturnsMax)    { EXPECT_EQ(Clamp(11, 0, 10), 10); }
```

For collections: empty, single element, two elements (often a distinct case), large input.

## Integration Tests vs Unit Tests

Unit tests isolate one class/function with all dependencies mocked. Integration tests wire real components together and test their interaction.

Structure by test pyramid: many unit tests, fewer integration tests, fewest end-to-end tests.

```
       /\
      /E2E\         few — slow, brittle, cover full user journeys
     /------\
    /Integr. \      some — test component boundaries with real deps
   /----------\
  / Unit Tests \    many — fast, isolated, test one behavior at a time
 /--------------\
```

In GTest, separate them by suite name convention or CMake target:

```cmake
# unit tests — fast, no external deps, always run
add_executable(unit_tests ...)
target_link_libraries(unit_tests GTest::gtest_main)

# integration tests — slower, need real DB/network
add_executable(integration_tests ...)
target_link_libraries(integration_tests GTest::gtest_main)
```

```bash
ctest -R "Unit"        # CI fast path
ctest -R "Integration" # CI slow path or nightly
```

## Test Isolation Techniques

### Dependency injection

Pass dependencies through the constructor instead of constructing them inside the class. This is the prerequisite for mocking — if a class creates its own `Database`, there's no seam to inject a mock.

```cpp
// Hard to test — creates its own dependency
class BadService {
    Database db_{"prod_conn_str"};  // can't substitute in tests
};

// Easy to test — dependency injected
class GoodService {
public:
    explicit GoodService(IDatabase& db) : db_(db) {}
private:
    IDatabase& db_;
};
```

### Seam via template parameter

When you can't change the constructor (legacy code), a template parameter is an alternative seam:

```cpp
template<typename Clock = std::chrono::steady_clock>
class RateLimiter {
    bool Allow() {
        auto now = Clock::now();
        // ...
    }
};

// In tests: inject a fake clock
struct FakeClock { static auto now() { return fixed_time; } };
RateLimiter<FakeClock> limiter;
```

## Avoiding Test Fragility

Fragile tests break when implementation changes even though behavior is correct. Common causes:

- **Over-specifying mocks** — asserting on every call when only one matters. Fix: use `ON_CALL` for irrelevant calls; `EXPECT_CALL` only for the call under test.
- **Testing exact error messages** — messages change, behavior doesn't. Fix: test exception type, not message string.
- **Order-sensitive tests** — tests that only pass in a specific run order have hidden shared state. Fix: run with `--gtest_shuffle` to detect; fix by isolating state.
- **Hardcoded timing** — `sleep()` to wait for async work. Fix: expose a callback or condition variable the test can synchronize on.
