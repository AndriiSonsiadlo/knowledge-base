---
id: error-codes
title: Error Codes and std::error_code
sidebar_label: Error Codes
sidebar_position: 3
tags: [cpp, error-codes, error-handling, std-error-code, std-expected, errno]
---

# Error Codes and std::error_code

When failure is *expected* (a parse of user input, a file that may not exist), reporting it through
the return value is often clearer and cheaper than throwing. C++ offers three layers for that:
raw integer codes like `errno`, the extensible `std::error_code` family *(C++11)*, and
`std::expected<T, E>` *(C++23)*, which returns either a value or an error. This page covers all three
and how to choose between them and [exceptions](./01-exceptions.md).

**Prerequisites:** [Exceptions](./01-exceptions.md).
`std::optional`, `std::variant` and friends live on [Utilities](../09-standard-library/utilities.md).

## Choosing between exceptions and return values

| Question | Leans to exceptions | Leans to error codes / `expected` |
|---|---|---|
| How often does it fail? | Rarely | Routinely (parsing, lookup, I/O polling) |
| Can the direct caller handle it? | Usually not, it propagates far | Yes, immediately |
| Does the function have a return channel? | No (constructors, operators) | Yes |
| Can the build use exceptions? | Yes | `-fno-exceptions`, kernels, embedded |

Throwing is expensive relative to a return on typical implementations (see
[Costs](./01-exceptions.md#costs-and-when-to-use-them)), and a return value makes the failure path
visible in the signature. The price is that every caller must check, which `[[nodiscard]]` helps
enforce.

## C-style codes: errno and return values

A C API reports failure with a return value (`-1`, `NULL`) and sets the thread-local `errno`.
`errno` is only meaningful right after a call that reported failure, and any later library call may
overwrite it, so copy it immediately.

```cpp showLineNumbers
// ...  (fragment)
#include <cerrno>
#include <cstdio>
#include <cstring>

std::FILE* f = std::fopen("data.txt", "r");
if (!f) {
    int saved = errno;                         // copy before calling anything else
    std::fprintf(stderr, "open failed: %s\n", std::strerror(saved));
}
```

Plain `int` codes have no type safety, no way to tell whose code `5` is, and silently compare equal
across unrelated libraries. `std::error_code` fixes that.

## std::error_code and categories

A `std::error_code` (in `<system_error>`) is a pair: an `int` value plus a reference to a
**`std::error_category`** that gives the number its meaning. It is cheap to copy (two words), never
allocates, and `explicit operator bool` is true when the value is non-zero, i.e. "there is an error".

- `ec.value()` is the number, `ec.category()` the category object, `ec.message()` a description.
- Standard categories are `std::generic_category()` (the portable POSIX-style `std::errc` values) and
  `std::system_category()` (the OS's native codes: `errno` values on POSIX, `GetLastError` on Windows).
  `std::iostream_category()` and `std::future_category()` cover those libraries.
- `std::make_error_code(std::errc::no_such_file_or_directory)` builds a portable one.
- The text returned by `message()` comes from the implementation and the OS, so don't compare it.

Many standard functions have overloads taking `std::error_code&` instead of throwing, notably
[`<filesystem>`](../09-standard-library/filesystem.md) and `std::from_chars`/`std::to_chars` (which
return an `errc`). Those without such an overload throw `std::system_error`, which wraps an
`error_code`.

### error_code versus error_condition

Different platforms spell the same failure differently. A `std::error_condition` is the *portable*
meaning and a `std::error_code` is the *platform-specific* cause. Comparing a code with a condition
(`ec == std::errc::no_such_file_or_directory`) asks "does this code mean that?", and each category
decides through `default_error_condition` and `equivalent`. Test against `std::errc` conditions, not
against raw numbers.

### Defining your own category

Three pieces: a category class, a single global instance, and the two hooks that let your enum
convert to `std::error_code`.

```cpp title="category.cpp" showLineNumbers
#include <cstdio>
#include <string>
#include <system_error>

enum class ParseErrc { empty = 1, bad_digit, overflow };

class ParseCategory : public std::error_category {
public:
    const char* name() const noexcept override { return "parse"; }
    std::string message(int c) const override {
        switch (static_cast<ParseErrc>(c)) {
            case ParseErrc::empty:     return "empty input";
            case ParseErrc::bad_digit: return "bad digit";
            case ParseErrc::overflow:  return "value too large";
        }
        return "unknown parse error";
    }
    std::error_condition default_error_condition(int c) const noexcept override {
        if (static_cast<ParseErrc>(c) == ParseErrc::overflow)
            return std::errc::result_out_of_range;   // map to a portable condition
        return std::error_condition(c, *this);
    }
};
const std::error_category& parse_category() noexcept {
    static const ParseCategory c;                    // categories are compared by address
    return c;
}
namespace std { template <> struct is_error_code_enum<ParseErrc> : true_type {}; }
std::error_code make_error_code(ParseErrc e) noexcept { return {static_cast<int>(e), parse_category()}; }

int main() {
    std::error_code ec = ParseErrc::overflow;        // implicit, via is_error_code_enum
    std::printf("%s: %s (%d)\n", ec.category().name(), ec.message().c_str(), ec.value());
    std::printf("== result_out_of_range: %d\n", ec == std::errc::result_out_of_range);
    std::printf("== bad_digit enum: %d\n", ec == ParseErrc::bad_digit);
    std::printf("bool(ec)=%d bool(error_code{})=%d\n", static_cast<bool>(ec), static_cast<bool>(std::error_code{}));
}
```

```text
parse: value too large (3)
== result_out_of_range: 1
== bad_digit enum: 0
bool(ec)=1 bool(error_code{})=0
```

Verified with g++ 15.2 and clang++ 21.1, `-std=c++23`, `-O0` and `-O2`. `make_error_code` is found by
ADL, so it must live in the enum's namespace (the global one here).

## std::expected \{#stdexpected\}

`std::expected<T, E>` *(C++23, `<expected>`)* holds either a `T` (the expected result) or an `E` (the
error), never both and never empty. Unlike `std::optional` it says *why* there is no value. Library
support: libstdc++ 12+, libc++ 16+, MSVC 19.33+ (verify for your toolchain).

```cpp title="expected.cpp" showLineNumbers
#include <charconv>
#include <cstdio>
#include <expected>
#include <string_view>
#include <system_error>

enum class ParseError { empty, bad_digit, out_of_range };

[[nodiscard]] std::expected<int, ParseError> parse_int(std::string_view s) {
    if (s.empty()) return std::unexpected(ParseError::empty);
    int v = 0;
    auto [p, ec] = std::from_chars(s.data(), s.data() + s.size(), v);
    if (ec == std::errc::result_out_of_range) return std::unexpected(ParseError::out_of_range);
    if (ec != std::errc{} || p != s.data() + s.size()) return std::unexpected(ParseError::bad_digit);
    return v;
}
std::expected<int, ParseError> checked_half(int n) {
    if (n % 2) return std::unexpected(ParseError::bad_digit);   // reusing the enum for brevity
    return n / 2;
}
const char* name(ParseError e) {
    switch (e) { case ParseError::empty: return "empty"; case ParseError::bad_digit: return "bad_digit";
                 case ParseError::out_of_range: return "out_of_range"; }
    return "?";
}
int main() {
    for (std::string_view in : {"42", "", "4x", "99999999999", "7"}) {
        auto r = parse_int(in).and_then(checked_half).transform([](int h) { return h + 1; });
        if (r) std::printf("'%.*s' -> %d\n", (int)in.size(), in.data(), *r);
        else   std::printf("'%.*s' -> error %s\n", (int)in.size(), in.data(), name(r.error()));
    }
    std::printf("value_or: %d\n", parse_int("abc").value_or(-1));
    try { (void)parse_int("abc").value(); }
    catch (const std::bad_expected_access<ParseError>& e) { std::printf("bad_expected_access: %s\n", name(e.error())); }
}
```

```text
'42' -> 22
'' -> error empty
'4x' -> error bad_digit
'99999999999' -> error out_of_range
'7' -> error bad_digit
value_or: -1
bad_expected_access: bad_digit
```

Same output on g++ 15.2 and clang++ 21.1 at `-O0` and `-O2`.

Access and composition:

| Operation | Meaning | Since |
|---|---|---|
| `if (r)`, `r.has_value()` | Holds a value? | C++23 |
| `*r`, `r->` | Access the value. **Undefined behavior** if it holds an error | C++23 |
| `r.value()` | Value, or throws `std::bad_expected_access<E>` | C++23 |
| `r.error()` | The error. Undefined behavior if it holds a value | C++23 |
| `r.value_or(x)` | Value, or `x` | C++23 |
| `r.and_then(f)` | If value: `f(value)` (must return an `expected` with the same `E`); else propagate the error | C++23 |
| `r.transform(f)` | If value: wrap `f(value)` in a new `expected`; else propagate | C++23 |
| `r.or_else(f)`, `r.transform_error(f)` | Operate on the error side | C++23 |

`and_then` and `transform` give you railway-style chaining without checking after each step, as in
`main` above. There is no `?`-like early-return operator; the explicit
`if (!r) return std::unexpected(r.error());` is the idiom.

C++23 `expected` has a `void` specialization (`expected<void, E>`) for operations that return nothing on
success. Before C++23, `tl::expected` and `boost::outcome` offer the same shape.

### Pitfalls

- `*r` on an error is UB, not an exception. Test first, or call `value()`.
- Don't use `std::expected<T, std::string>` on hot paths if string allocation matters; an enum or
  `std::error_code` does not allocate.
- `std::optional<T>` is enough when "no value" has only one reason.
- Mixing styles: a function that is `noexcept` and returns `expected` can still run out of memory
  inside; decide what "failure" covers.

## Key points

- Use return-value errors for expected, locally handled failures; use exceptions for rare ones that
  propagate.
- Copy `errno` immediately; prefer `std::error_code` with a category over bare integers.
- Compare against `std::errc` conditions for portability, and define a category only when you own an
  error domain.
- `std::expected<T, E>` is C++23. Never dereference it without checking, and mark producers
  `[[nodiscard]]`.
