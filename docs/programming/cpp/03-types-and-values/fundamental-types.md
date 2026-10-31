---
id: fundamental-types
title: Fundamental Types
sidebar_label: Fundamental Types
sidebar_position: 1
tags: [c++, types, primitives, int, float, char, bool]
---

# Fundamental Types

The **fundamental types** are the ones built into the language rather than defined in a library:
integers, characters, `bool`, floating-point types, `void`, and `std::nullptr_t`. Everything else
(classes, enums, pointers, arrays) is built from them. The standard fixes only *minimum* widths and
an ordering for most of them, so `long` is 8 bytes on 64-bit Linux and 4 bytes on 64-bit Windows.
This page lists the types, what is guaranteed about each, what typical platforms actually use, and
when to reach for a fixed-width alias instead.

**Prerequisites:** [Basic Syntax](../02-language-fundamentals/basic-syntax.md)

<Diagram title="The fundamental types" accent="blue">
  <DiagramRow>
    <DiagramGroup label="Arithmetic">
      <DiagramNode title="Integral" accent>`bool`, character types, `short`, `int`, `long`, `long long`, each signed or unsigned</DiagramNode>
      <DiagramNode title="Floating-point">`float`, `double`, `long double`</DiagramNode>
    </DiagramGroup>
    <DiagramNode title="void">No values. Return type of functions that return nothing</DiagramNode>
    <DiagramNode title="std::nullptr_t">The type of `nullptr` *(C++11)*</DiagramNode>
  </DiagramRow>
</Diagram>

## Integer types

| Type | Minimum width | x86-64 Linux, macOS (LP64) | x86-64 Windows (LLP64) |
|---|---|---|---|
| `signed char` / `unsigned char` | 8 bits | 8 | 8 |
| `short` | 16 bits | 16 | 16 |
| `int` | 16 bits | 32 | 32 |
| `long` | 32 bits | **64** | **32** |
| `long long` *(C++11)* | 64 bits | 64 | 64 |

The minimum widths are from the standard ([\[basic.fundamental\]](https://eel.is/c++draft/basic.fundamental)).
The platform columns were measured with GCC 15 on x86-64 Linux and checked for Windows with
`clang++ --target=x86_64-pc-windows-msvc`. The standard also guarantees the order
`sizeof(signed char) == 1 <= sizeof(short) <= sizeof(int) <= sizeof(long) <= sizeof(long long)`.

Each type has an `unsigned` counterpart of the same size. The ranges, overflow behavior and the
traps of mixing the two are on [Signedness](./signedness.md).

The names combine freely: `unsigned`, `unsigned int`, `int unsigned` are the same type, as are
`long`, `long int`, and `signed long int`. Integer literals choose their type by suffix: `42` is
`int`, `42u` `unsigned`, `42L` `long`, `42LL` `long long`, `42uz` `std::size_t` *(C++23)*. An
unsuffixed literal too large for `int` takes the first of `long`, `long long` that fits.

### Fixed-width aliases

`<cstdint>` *(C++11)* names integer types by width:

| Alias | Meaning | Guaranteed to exist? |
|---|---|---|
| `std::int8_t` … `std::int64_t`, `std::uint8_t` … `std::uint64_t` | Exactly N bits, no padding | Only if the platform has such a type. All mainstream platforms do |
| `std::int_least16_t`, … | Smallest type with at least N bits | Yes |
| `std::int_fast16_t`, … | Type with at least N bits the implementation considers fastest | Yes |
| `std::intptr_t`, `std::uintptr_t` | Can hold a converted `void*` | Optional |
| `std::size_t` (`<cstddef>`) | Result type of `sizeof`; unsigned | Yes |
| `std::ptrdiff_t` (`<cstddef>`) | Result of subtracting two pointers; signed | Yes |

Use the exact-width types where the width is part of a contract: file formats, network protocols,
hardware registers. For ordinary arithmetic `int` is fine and is what the language promotes to
anyway. One catch: on GCC and Clang, `std::int8_t` is `signed char` and `std::uint8_t` is
`unsigned char`, so `std::cout << std::uint8_t{65}` prints `A`. Convert to `int` before printing.

## Character types

| Type | Size | Holds |
|---|---|---|
| `char` | 1 byte | A byte of the execution character set (in practice UTF-8 text). Signedness is implementation-defined |
| `signed char`, `unsigned char` | 1 byte | Small integers. `unsigned char` is also the type for raw object bytes |
| `wchar_t` | 4 bytes on Linux, 2 on Windows | A wide character in a platform-specific encoding |
| `char8_t` *(C++20)* | 1 byte | A UTF-8 code unit. `u8"..."` literals have this element type since C++20 |
| `char16_t`, `char32_t` *(C++11)* | 2, 4 bytes | UTF-16 and UTF-32 code units (`u"..."`, `U"..."`) |

`char`, `signed char`, and `unsigned char` are three distinct types, even though `char` has the
same representation as one of the other two. Character types are integers: `'A' + 1` is the `int`
66. `std::byte` *(C++17, `<cstddef>`)* is an enum type for raw bytes that supports only bitwise
operations, which makes it harder to mistake for a number or a character.

## `bool`

`bool` holds `true` or `false`. In arithmetic it is promoted to `int` (`true` → 1). Any number or
pointer converts to `bool`: zero or null gives `false`, anything else `true`. `sizeof(bool)` is
implementation-defined; it is 1 on all the platforms above.

## Floating-point types

| Type | x86-64 Linux | x86-64 Windows (MSVC ABI) | Decimal digits (`digits10`) |
|---|---|---|---|
| `float` | IEEE-754 binary32 | binary32 | 6 |
| `double` | IEEE-754 binary64 | binary64 | 15 |
| `long double` | x87 80-bit extended, stored in 16 bytes | Same as `double`, 8 bytes | 18 on Linux |

The standard only requires `double` to be at least as precise as `float`, and `long double` at
least as precise as `double`. IEEE-754 formats for `float` and `double` are what every mainstream
platform uses; `std::numeric_limits<double>::is_iec559` tells you at compile time. Literals:
`3.14` is `double`, `3.14f` `float`, `3.14L` `long double`.

C++23 adds optional fixed-format types in `<stdfloat>`: `std::float16_t`, `std::float32_t`,
`std::float64_t`, `std::float128_t`, `std::bfloat16_t`. GCC 15 provides them. Clang 21 with
libstdc++ does not define them yet.

Binary floating point can't represent most decimal fractions exactly, so results carry rounding
error:

```cpp title="precision.cpp" showLineNumbers
#include <cstdio>

int main() {
    float  f = 1.0f / 3.0f;
    double d = 1.0 / 3.0;
    std::printf("%.20f\n%.20f\n", f, d);
    std::printf("%d\n", 0.1 + 0.2 == 0.3);
}
```

```text
0.33333334326744079590
0.33333333333333331483
0
```

`float` is correct to about 7 significant digits here, `double` to about 16. Comparing computed
values with `==` is rarely meaningful; compare with a tolerance appropriate to the computation.
`double` is the usual default. `float` makes sense when memory or bandwidth matters, such as large
arrays or GPU code.

## Checking your platform

`sizeof` and `std::numeric_limits` (`<limits>`) report the actual properties, and `static_assert`
turns an assumption into a compile error instead of a bug:

```cpp title="sizes.cpp" showLineNumbers
#include <cstdio>
#include <limits>

static_assert(sizeof(int) >= 4, "this code assumes a 32-bit int");

int main() {
    std::printf("int %zu, long %zu, long double %zu, wchar_t %zu, void* %zu\n",
                sizeof(int), sizeof(long), sizeof(long double), sizeof(wchar_t), sizeof(void*));
    std::printf("int max %d, double digits10 %d\n",
                std::numeric_limits<int>::max(), std::numeric_limits<double>::digits10);
}
```

```text
int 4, long 8, long double 16, wchar_t 4, void* 8
int max 2147483647, double digits10 15
```

Output from GCC 15 on x86-64 Linux.

## Common mistakes

- **Assuming `long` is 64 bits.** It is 32 bits on Windows. Use `long long` or `std::int64_t`
  when you need 64.
- **Printing `std::uint8_t` with iostreams.** It prints a character. Write `+x` or
  `static_cast<int>(x)`.
- **Assuming plain `char` is signed.** It is unsigned on ARM Linux, so `char c = 200;` holds -56
  on x86-64 and 200 on ARM.
- **Storing money in `double`.** `0.1` isn't representable. Use an integer count of the smallest
  unit (cents).

## Key points

- The standard guarantees minimum widths and an ordering, not exact sizes.
- `long` differs between Linux (64-bit) and Windows (32-bit). That is the LP64 versus LLP64 split.
- Use `<cstdint>` aliases when width is part of a contract.
- `char`, `signed char`, `unsigned char` are three types; `char`'s signedness varies.

## Related

- [Signedness](./signedness.md): ranges, overflow, and signed/unsigned conversion.
- [Conversions and Promotions](./conversions-and-promotions.md): what happens when these types meet
  in an expression.
- [auto](./type-deduction/auto.md): letting the compiler pick the type from an initializer.
