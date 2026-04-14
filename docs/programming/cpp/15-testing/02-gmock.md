---
id: gmock
title: GMock
sidebar_label: GMock
sidebar_position: 2
tags: [gmock, googlemock, mock, stub, dependency-injection, matchers, expectations]
---

# GMock

Google Mock (GMock) generates mock objects from interfaces. Instead of passing a real database, filesystem, or network client to the code under test, you pass a mock that records calls and lets you assert on them. This isolates the unit under test from its dependencies, making tests fast, deterministic, and independent of external systems.

```cpp
#include <gmock/gmock.h>
#include <gtest/gtest.h>
```

GMock ships with GTest since v1.8 — no separate fetch needed. Link against `GTest::gmock_main` instead of `GTest::gtest_main`.

## Creating a Mock

Define the interface as a pure-virtual class, then use `MOCK_METHOD` to generate the implementation. The macro expands to a method that records calls, checks expectations, and returns whatever the test told it to return.

```cpp
class IDatabase {
public:
    virtual ~IDatabase() = default;
    virtual bool Connect(const std::string& url) = 0;
    virtual std::string Query(const std::string& sql) = 0;
    virtual void Disconnect() = 0;
};

class MockDatabase : public IDatabase {
public:
    MOCK_METHOD(bool, Connect, (const std::string& url), (override));
    MOCK_METHOD(std::string, Query, (const std::string& sql), (override));
    MOCK_METHOD(void, Disconnect, (), (override));
};
```

Signature: `MOCK_METHOD(ReturnType, MethodName, (Args...), (Specifiers...))`. Common specifiers: `override`, `const`, `noexcept`.

## Setting Expectations

`EXPECT_CALL` declares what calls the mock should receive and what it should return. It must be set up **before** the code under test runs. When the mock destructs at end of test, GMock verifies that all expectations were met — unfulfilled or unexpected calls are test failures.

```cpp
TEST(ServiceTest, QueriesOnceAfterConnect) {
    MockDatabase db;

    EXPECT_CALL(db, Connect("localhost"))
        .Times(1)
        .WillOnce(::testing::Return(true));

    EXPECT_CALL(db, Query("SELECT 1"))
        .Times(1)
        .WillOnce(::testing::Return("1"));

    EXPECT_CALL(db, Disconnect())
        .Times(1);

    MyService svc(&db);
    svc.Run();  // must call Connect, Query, Disconnect exactly once each
}
```

## Cardinality (Times)

`Times` specifies how many times a call is expected. If you omit it, GMock infers: one `WillOnce` implies `Times(1)`; `WillRepeatedly` implies `AnyNumber()`.

```cpp
.Times(0)                        // must NOT be called
.Times(1)                        // exactly once (default with one WillOnce)
.Times(3)                        // exactly 3 times
.Times(::testing::AnyNumber())   // zero or more (don't care)
.Times(::testing::AtLeast(2))    // 2 or more
.Times(::testing::AtMost(5))     // 0 to 5
.Times(::testing::Between(2, 5)) // 2 to 5 inclusive
```

## Actions (WillOnce / WillRepeatedly)

Actions define what the mock returns or does when called. `WillOnce` applies to a single call; `WillRepeatedly` applies to all subsequent ones. You can chain multiple `WillOnce` to return different values on successive calls.

```cpp
using ::testing::Return;
using ::testing::ReturnRef;
using ::testing::Throw;

.WillOnce(Return(42))
.WillRepeatedly(Return(0))
.WillOnce(ReturnRef(some_ref))          // return a reference
.WillOnce(Throw(std::runtime_error("oops")))

// Return different values on successive calls, then fall back to default
EXPECT_CALL(db, Query(_))
    .WillOnce(Return("first"))
    .WillOnce(Return("second"))
    .WillRepeatedly(Return("default"));
```

### Custom actions

When you need to inspect arguments or run logic, use `Invoke` to delegate to a lambda or function. `DoAll` lets you chain multiple actions — the return value comes from the last one.

```cpp
.WillOnce(::testing::Invoke([](const std::string& sql) {
    return "result for: " + sql;
}));

// Invoke a free function
.WillOnce(::testing::Invoke(&MyFreeFunction));

// Do nothing (void methods)
.WillOnce(::testing::DoNothing());
```

## Matchers

Matchers describe expected argument values in `EXPECT_CALL`. When you pass a plain value like `Connect("localhost")`, GMock wraps it in `Eq()` implicitly. Use explicit matchers when you need partial matching, wildcards, or structural checks.

### Basic

```cpp
::testing::Eq(val)   // == val  (default when you pass val directly)
::testing::Ne(val)   // != val
::testing::Lt(val)
::testing::Le(val)
::testing::Gt(val)
::testing::Ge(val)
::testing::_         // wildcard — matches any value
```

### String

```cpp
::testing::StartsWith("prefix")
::testing::EndsWith("suffix")
::testing::HasSubstr("part")
::testing::MatchesRegex("fo+")    // full match
::testing::ContainsRegex("fo+")   // partial match
::testing::StrCaseEq("abc")       // case-insensitive equality
```

### Numeric

```cpp
::testing::DoubleEq(3.14)          // within 4 ULPs
::testing::FloatEq(3.14f)
::testing::DoubleNear(3.14, 0.01)  // absolute tolerance
```

### Composite

Combine matchers with logical operators to express range constraints or alternatives.

```cpp
::testing::AllOf(Gt(0), Lt(10))    // both must match (&&)
::testing::AnyOf(Eq(1), Eq(2))     // either must match (||)
::testing::Not(Eq(0))
```

### Pointer / reference

```cpp
::testing::IsNull()
::testing::NotNull()
::testing::Pointee(Eq(5))   // dereferences pointer, then matches — *ptr == 5
```

### Container

```cpp
::testing::IsEmpty()
::testing::SizeIs(3)
::testing::Contains(7)
::testing::ElementsAre(1, 2, 3)          // exact elements in order
::testing::UnorderedElementsAre(3, 1, 2) // same elements, any order
::testing::Each(Gt(0))                   // every element matches the inner matcher
```

### EXPECT_THAT

`EXPECT_THAT(value, matcher)` applies a matcher outside of a mock call — useful for asserting on return values and containers in regular GTest tests.

```cpp
std::vector<int> v = {1, 2, 3};
EXPECT_THAT(v, ::testing::ElementsAre(1, 2, 3));
EXPECT_THAT(v, ::testing::Each(::testing::Gt(0)));
EXPECT_THAT("hello world", ::testing::HasSubstr("world"));
```

## Argument Capture (SaveArg)

When you need to verify the exact value that was passed to a mock — after the call happens — use `SaveArg<N>` to capture argument N into a variable, then assert on it later.

```cpp
std::string captured_sql;
EXPECT_CALL(db, Query(_))
    .WillOnce(::testing::DoAll(
        ::testing::SaveArg<0>(&captured_sql),  // capture first argument
        ::testing::Return("ok")                // still need a return value
    ));

svc.Run();
EXPECT_EQ(captured_sql, "SELECT * FROM users");
```

`DoAll` chains multiple actions; only the last action's return value is used.

## Strict / Nice / Naggy Mocks

By default (naggy), unexpected calls print a warning but don't fail the test. Choose a stricter or looser policy by wrapping the mock type.

```cpp
// NiceMock: unexpected calls silently ignored — good for stubs/fakes
::testing::NiceMock<MockDatabase> nice_db;

// NaggyMock (default): unexpected calls print a warning but don't fail
::testing::NaggyMock<MockDatabase> naggy_db;

// StrictMock: any unexpected call is a test failure — maximum strictness
::testing::StrictMock<MockDatabase> strict_db;
```

Use `StrictMock` when every interaction with a dependency is semantically meaningful. Use `NiceMock` for dependencies that are mostly irrelevant to the test, to avoid noise from unset expectations.

## Ordered Expectations

By default, `EXPECT_CALL` expectations can be satisfied in any order. To enforce a specific call sequence, create an `InSequence` object — GMock then requires that expectations declared afterward are satisfied in the order they appear.

```cpp
{
    ::testing::InSequence seq;  // ordering enforced within this scope

    EXPECT_CALL(db, Connect(_)).Times(1);
    EXPECT_CALL(db, Query(_)).Times(1);
    EXPECT_CALL(db, Disconnect()).Times(1);
    // Connect → Query → Disconnect; any other order is a failure
}
```

## Mocking Non-Virtual Methods (Templates)

GMock requires virtual dispatch to intercept calls. When the class under test calls a non-virtual method and you can't add `virtual`, use a template seam: make the dependency a template parameter so tests can substitute a mock at compile time without any virtual overhead in production.

```cpp
template<typename DB>
class Service {
public:
    Service(DB& db) : db_(db) {}
    void Run() { db_.Connect("localhost"); }
private:
    DB& db_;
};

TEST(ServiceTest, Connects) {
    MockDatabase db;
    EXPECT_CALL(db, Connect("localhost")).WillOnce(::testing::Return(true));
    Service<MockDatabase> svc(db);
    svc.Run();
}
```

## Common Patterns

### Return different values on successive calls

Chain multiple `WillOnce` to simulate stateful behavior (e.g., first call returns data, second call returns empty).

```cpp
EXPECT_CALL(mock, GetValue())
    .WillOnce(::testing::Return(1))
    .WillOnce(::testing::Return(2))
    .WillRepeatedly(::testing::Return(-1));  // all subsequent calls
```

### Verify call count without caring about arguments

```cpp
EXPECT_CALL(mock, SomeMethod(::testing::_)).Times(3);
```

### Assert a method is never called

```cpp
EXPECT_CALL(mock, ShouldNotBeCalled()).Times(0);
```

### ON_CALL — default behavior without an expectation

`ON_CALL` sets what the mock returns by default, without asserting that the call happens. Use it in fixture `SetUp` to establish sane defaults; then use `EXPECT_CALL` only in tests that care about whether the call happened.

```cpp
ON_CALL(db, Connect(_)).WillByDefault(::testing::Return(true));
```

The rule: `ON_CALL` for behavior, `EXPECT_CALL` for assertions.
