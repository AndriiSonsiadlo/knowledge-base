---
id: strings
title: String Handling
sidebar_label: Strings
sidebar_position: 5
tags: [c++, strings, std-string, string-view, sso, conversion, format, char8_t]
---

# String Handling

`std::string` is a `std::basic_string<char>`: a [container](./containers.md) of characters that
owns its storage, grows on demand, and keeps a terminating `'\0'` so it can hand a C string to C
APIs. `std::string_view` (C++17) is its non-owning counterpart: a pointer and a length that can
look at any character sequence without copying it. This page is the canonical home for both, for
conversions between text and numbers, and for the pitfalls of treating bytes as text.

**Prerequisites:** [Containers](./containers.md) (strings follow the vector model of size,
capacity and reallocation), [fundamental types](../03-types-and-values/fundamental-types.md) (`char`
signedness), [const and pointers](../06-pointers-references-and-smart-pointers/const-and-pointers.md).

## `std::string` basics

```cpp title="string-basics.cpp" showLineNumbers
#include <iostream>
#include <string>

int main() {
    std::string a = "hello";
    std::string b(3, '!');                      // "!!!"
    std::string c = a + ", world" + b;          // operator+ allocates a temporary per step
    c += '?';
    c.append(" ok").insert(0, ">> ");

    std::cout << c << '\n';
    std::cout << c.size() << ' ' << c.find("world") << ' ' << c.find("xyz") << ' '
              << (c.find("xyz") == std::string::npos) << '\n';
    std::cout << c.substr(3, 5) << '|' << c.at(0) << '\n';
}
```

```text
>> hello, world!!!? ok
22 10 18446744073709551615 1
hello|>
```

The large number is `std::string::npos`, the "not found" value (`static_cast<size_t>(-1)`); always
compare against `npos` rather than printing or storing the result in an `int`.

- `operator[]` does no bounds check; `at()` throws `std::out_of_range`. `s[s.size()]` is valid and
  yields `'\0'` (since C++11); writing a non-zero value there is undefined behavior.
- `c_str()` and `data()` return a null-terminated pointer (`data()` is `const`-only before C++17).
  The pointer is invalidated by any modification, as with vector's iterators. A `std::string` can
  contain embedded `'\0'`; `size()` counts them, but C APIs stop at the first.
- `substr(pos, len)` copies and throws `out_of_range` if `pos > size()`. Prefer a `string_view` when
  you only need to look.
- Search functions (`find`, `rfind`, `find_first_of`, `find_last_not_of`, ...) return an index or `npos`.
  `find_first_of("abc")` looks for **any of** the characters, not the substring.
- `starts_with`, `ends_with` *(C++20)* and `contains` *(C++23)* replace the `rfind(x, 0) == 0` hack.
- Comparison operators are lexicographic by `char_traits<char>::compare`, which compares as
  `unsigned char`; `<=>` exists since C++20.
- `resize(n)` pads with `'\0'`; `resize_and_overwrite(n, op)` *(C++23)* lets a C API fill the buffer
  without zero-filling first.

### Size, capacity and reallocation

`size()` is the length, `capacity()` the amount that fits before a reallocation, and `reserve(n)`
and `shrink_to_fit()` behave as for `vector`. Appending in a loop is amortized O(1) per character,
so build a long string with `+=`/`append` (or `std::ostringstream`, see [IOStreams](./iostreams.md)),
and call `reserve` if you know the final size. `s = s + x` makes a temporary each time; `s += x` does not.

Iterator, pointer and reference invalidation is the same as vector's: any call that may
reallocate (`push_back`, `append`, `insert`, `reserve` beyond capacity, `+=`) invalidates them all.
After C++11 a non-const `operator[]`/`at` no longer invalidates anything (copy-on-write was banned).

### Small string optimization

Most implementations store short strings inside the `std::string` object itself, so they need
no heap allocation. The standard does not require it, but libstdc++, libc++ and MSVC all do.
The sizes are implementation details. Measured with g++ 15.2 and clang++ 21.1 (libstdc++) on x86-64 Linux:

```cpp title="sso.cpp" showLineNumbers
#include <iostream>
#include <string>

int main() {
    std::string s;
    std::cout << sizeof(s) << ' ' << s.capacity() << '\n';
}
```

```text
32 15
```

An empty `std::string` is 32 bytes and holds up to 15 characters before allocating (other
standard libraries use different sizes). A consequence: **moving a short string copies its
characters** and does not steal a pointer, and a pointer or `string_view` into a short string
is invalidated by moving or swapping the string, even though no heap buffer was freed.

## `std::string_view` *(C++17)*

`std::string_view` is a pair `{const char*, size_t}` with a read-only string interface (`size`,
`find`, `substr`, `starts_with`, comparison, iterators, `operator[]`). Copying it copies two words.
`substr` returns another view in O(1), not a copy. Use it for **function parameters** that only
read text: it accepts `std::string`, string literals, `char` arrays and substrings with no
allocation. It is implicitly constructible from `std::string` and a C string, so it also avoids
the temporary `std::string` that a `const std::string&` parameter would need for a literal.

```cpp title="string-view.cpp" showLineNumbers
#include <iostream>
#include <string>
#include <string_view>

std::string_view first_word(std::string_view s) {
    return s.substr(0, s.find(' '));        // no allocation, find(' ') == npos means "whole"
}

int main() {
    std::string s = "hello world";
    std::string_view w = first_word(s);     // refers into s
    std::cout << w << ' ' << w.size() << '\n';
    std::cout << first_word("literal text") << '\n';
}
```

```text
hello 5
literal
```

A view **does not own and is not null-terminated**. That has three consequences:

1. **Lifetime.** The view is valid only while the characters it points to are alive and
   unmodified. `std::string_view v = std::string("tmp");` dangles at the end of the statement, and
   returning a view of a local string, or keeping a view across `s += ...` that reallocates, is a
   use-after-free. This is the borrowing hazard of [raw pointers](../06-pointers-references-and-smart-pointers/raw-pointers.md),
   and of [range views](./ranges.md#laziness-caching-and-lifetime).
2. **No `c_str()`.** `view.data()` is not guaranteed to be null-terminated, so passing it to a C
   API that expects a C string is a bug. Construct a `std::string` first.
3. **Storing it.** A class member that outlives the call should usually be a `std::string`. A
   `string_view` member is a deliberate borrow.

There is no implicit `string_view` to `std::string` conversion because it would hide a copy: write
`std::string(sv)` (or, since C++17, `std::string s{sv}` works through an explicit constructor).
Also, `std::string + string_view` has no `operator+` before C++26 (P2591), so build it with `append`.

## Converting between text and numbers

| Direction | Tool | Notes |
|---|---|---|
| number to string | `std::to_string(x)` | floating point uses `%f` and the C locale's formatting until C++26 (P2587 changes it to match `std::format`): `to_string(1.5)` is `"1.500000"` before that |
| number to string | `std::format("{}", x)` *(C++20)* | locale-independent by default, shortest round-trip for floats |
| string to number | `std::stoi/stol/stoll/stod...` | throw `std::invalid_argument` / `std::out_of_range`; skip leading whitespace; stop at the first invalid char; take an optional `size_t* pos` |
| string to number | `std::from_chars` / `std::to_chars` *(C++17, `<charconv>`)* | no exceptions, no allocation, no locale: designed for speed |

`std::from_chars(first, last, value)` returns a `from_chars_result{ptr, ec}`: on success `ec` is
default and `ptr` points past the last character consumed. It does not skip whitespace and does not
accept a leading `+`.

```cpp title="convert.cpp" showLineNumbers
#include <charconv>
#include <iostream>
#include <string>
#include <string_view>
#include <system_error>

int main() {
    std::string_view in = "42abc";
    int v = 0;
    auto [ptr, ec] = std::from_chars(in.data(), in.data() + in.size(), v);
    std::cout << v << ' ' << (ec == std::errc{}) << ' ' << ptr << '\n';   // stops at "abc"

    int bad = 0;
    std::string_view junk = "x1";
    auto r = std::from_chars(junk.data(), junk.data() + junk.size(), bad);
    std::cout << (r.ec == std::errc::invalid_argument) << '\n';

    try { (void)std::stoi("abc"); }
    catch (const std::invalid_argument&) { std::cout << "stoi threw\n"; }
    std::cout << std::stoi("  12 apples") << ' ' << std::to_string(1.5) << '\n';
}
```

```text
42 1 abc
1
stoi threw
12 1.500000
```

`std::from_chars` for floating point is available in GCC 11+ and recent libc++/MSVC; check your
library. Do not use `atoi`/`atof`: they return `0` on failure and give undefined behavior on
out-of-range input.

## Formatting

`std::format("{} is {:>5}", name, n)` *(C++20, `<format>`)* is type-safe, extensible and
locale-independent unless you ask for `L`; `std::print` and `std::println` *(C++23, `<print>`)*
write it to a stream or `stdout`. They are faster and safer than `printf`, and more convenient than
`operator<<` chains. Library support is recent (GCC 13+ for `<format>`, 14+ for `<print>`); see
the [IOStreams](./iostreams.md) page for stream formatting.

## Literals

| Literal | Type | Suffix |
|---|---|---|
| `"text"` | `const char[5]` (null included) | none |
| `"text"s` | `std::string` | `using namespace std::string_literals;` *(C++14)* |
| `"text"sv` | `std::string_view` | `using namespace std::string_view_literals;` *(C++17)* |
| `R"(raw \n text)"` | raw literal, no escapes | |
| `u8"..."`, `u"..."`, `U"..."`, `L"..."` | UTF-8, UTF-16, UTF-32, wide | `char8_t` for `u8` since C++20 |

`"a" "b"` adjacent literals concatenate at compile time. `std::string s = "a" + "b"` does not
compile, since it adds two pointers.

## Strings are bytes, not characters

`std::string` stores `char`s, not characters. UTF-8 text is held as bytes, so `size()` is the byte
count, `s[i]` may be half of a multi-byte code point, and `std::toupper`, `reverse` and `substr`
can cut or corrupt a sequence. The standard library has no Unicode-aware string operations
(`std::wstring`'s `wchar_t` is 16 bits on Windows and 32 bits on Linux and does not solve it).
Treat `std::string` as UTF-8 bytes if your platform does, and use ICU or a similar library when
you need code points, normalization, or case conversion.

`std::toupper` takes an `int` that must be representable as `unsigned char` (or `EOF`), so a plain
`char` argument with a negative value is undefined behavior; cast first:
`static_cast<unsigned char>(c)`.

```cpp title="upper.cpp" showLineNumbers
#include <algorithm>
#include <cctype>
#include <iostream>
#include <string>

int main() {
    std::string s = "Hello";
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    std::cout << s << '\n';
}
```

```text
HELLO
```

## Common operations the library does not provide

There is no standard `split`, `trim` or `join` for strings in C++20 and before; `std::views::split`
*(C++20)* and `views::join_with`, `ranges::to<std::string>` *(C++23)* cover splitting and joining,
and trimming is `find_first_not_of` / `find_last_not_of` plus `erase` or `substr`:

```cpp title="trim.cpp" showLineNumbers
#include <iostream>
#include <string>
#include <string_view>

std::string_view trim(std::string_view s) {
    constexpr std::string_view ws = " \t\n\r";
    const auto b = s.find_first_not_of(ws);
    if (b == std::string_view::npos) return {};
    const auto e = s.find_last_not_of(ws);
    return s.substr(b, e - b + 1);
}

int main() {
    std::cout << '[' << trim("  \t padded text \n") << "]\n";
}
```

```text
[padded text]
```

## Related

- [Containers](./containers.md): the size/capacity/invalidation model that strings share with `vector`
- [Ranges](./ranges.md): `views::split`, `views::join_with` and other range-based text processing
- [IOStreams](./iostreams.md): `ostringstream`, `istringstream`, formatting with manipulators
- [Algorithms](./algorithms.md): `std::transform`, `std::search` over character ranges
- [Utilities](./utilities.md): `std::optional` for a "may be missing" string result

## References

- [Strings library, cppreference](https://en.cppreference.com/w/cpp/string)
- [`std::from_chars`, cppreference](https://en.cppreference.com/w/cpp/utility/from_chars)
- ISO C++ [strings], [string.view]
