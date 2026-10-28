---
id: signedness
title: Signed and Unsigned Types
sidebar_label: Signedness
sidebar_position: 3
tags: [c++, signed, unsigned, types, overflow, cpp20]
---

# Signed and Unsigned Types

Every integer type except `bool` comes in a signed and an unsigned version. The two differ in more
than range: unsigned arithmetic wraps around by definition, signed overflow is undefined behavior,
and when the two meet in one expression the signed value is often converted to unsigned without a
warning. This page covers the ranges, the overflow rules, what happens to a value when it changes
signedness, and how to avoid the mixed-sign bugs.

**Prerequisites:** [Fundamental Types](./fundamental-types.md)

## Ranges and representation

Since C++20 the standard requires **two's complement** for signed integers
([P0907](https://wg21.link/p0907r4)). For a type with N bits:

| | Range | `int` with N = 32 |
|---|---|---|
| Signed | -2^(N-1) to 2^(N-1) - 1 | -2147483648 to 2147483647 |
| Unsigned | 0 to 2^N - 1 | 0 to 4294967295 |

Before C++20, ones' complement and sign-magnitude were allowed in principle. No mainstream
compiler used them, so C++20 standardized existing practice. The limits are available as
`std::numeric_limits<T>::min()` / `max()` in `<limits>`, or as `INT_MIN`, `UINT_MAX` and friends in
`<climits>`.

`signed` is the default for `short`, `int`, `long`, and `long long`: `int` and `signed int` are the
same type. `char` is different: plain `char`, `signed char`, and `unsigned char` are three distinct
types, and whether plain `char` is signed is implementation-defined. It is signed on x86-64 Linux
and Windows and unsigned on ARM Linux. GCC and Clang let you choose with `-fsigned-char` /
`-funsigned-char`. Use `signed char` or `unsigned char` (or `std::int8_t`/`std::uint8_t`) when you
mean a small number.

## Overflow

<Tabs>
  <TabItem value="unsigned" label="Unsigned: wraps">

Unsigned arithmetic is defined modulo 2^N. Going past the maximum wraps to 0, and going below 0
wraps to the maximum:

```cpp title="wrap.cpp" showLineNumbers
#include <climits>
#include <cstdio>

int main() {
    unsigned x = UINT_MAX;
    x++;                         // 0
    unsigned y = 0;
    y--;                         // UINT_MAX
    std::printf("%u %u\n", x, y);
}
```

```text
0 4294967295
```

  </TabItem>
  <TabItem value="signed" label="Signed: undefined behavior">

Signed overflow is undefined. The compiler may assume it never happens, and optimizers use that:
`x + 1 > x` can be folded to `true` for a signed `x`.

```cpp title="overflow.cpp" showLineNumbers
#include <climits>

int next(int x) { return x + 1; }   // UB when x == INT_MAX

int main() { return next(INT_MAX) == INT_MIN; }   // no guaranteed result
```

`-fsanitize=undefined` reports it at run time; see [Sanitizers](../14-debugging-and-profiling/04-sanitizers.md).
For checked arithmetic, GCC and Clang provide `__builtin_add_overflow`. Two's complement in C++20
fixed the representation, not overflow: it is still UB.

  </TabItem>
</Tabs>

## Converting between signed and unsigned

Conversions are defined by value, not by "reinterpreting the bits", although on two's complement
hardware the two coincide:

- **To an unsigned type:** the result is the source value modulo 2^N. `-1` becomes 2^32 - 1 =
  4294967295 as `unsigned int`. This has always been well-defined.
- **To a signed type:** if the value fits, it is unchanged. If it doesn't, the result was
  implementation-defined before C++20. Since C++20 it is the unique value congruent to the source
  modulo 2^N, so `static_cast<int>(4294967291u)` is -5.

That is why the classic "unsigned subtraction" example gives the right number when you store it in
an `int`, but for a fragile reason:

```cpp title="subtract.cpp" showLineNumbers
#include <cstdio>

int main() {
    unsigned a = 5, b = 10;
    unsigned d1 = a - b;   // 4294967291: wrapped
    int      d2 = a - b;   // -5: the wrapped value converted back, modulo 2^32
    std::printf("%u %d\n", d1, d2);
}
```

```text
4294967291 -5
```

`d2` is correct only because the conversion back to `int` undoes the wrap at the same width. The
intermediate value is still 4294967291, and anything that uses it before the conversion, such as a
comparison `a - b > 0` (true) or a division, sees the wrapped value. Convert the operands to a
signed type before subtracting, or don't mix signedness at all.

## Mixed-sign expressions

When a signed and an unsigned operand meet in a binary operator, the
[usual arithmetic conversions](./conversions-and-promotions.md#the-usual-arithmetic-conversions)
choose a common type. If the unsigned type has the same or higher rank, as with `int` and
`unsigned`, the signed operand becomes unsigned:

```cpp title="compare.cpp" showLineNumbers
#include <cstdio>
#include <utility>

int main() {
    int x = -1;
    unsigned y = 1;
    std::printf("%d\n", x < y);                 // 0: -1 converted to 4294967295
    std::printf("%d\n", std::cmp_less(x, y));   // 1: compares the actual values (C++20)
}
```

```text
0
1
```

The first comparison is the most common signedness bug. GCC warns about it with `-Wall` and Clang
with `-Wextra` (`-Wsign-compare`). The `std::cmp_equal`, `std::cmp_less` family in `<utility>`
*(C++20)* compares integers of any signedness by mathematical value, and `std::in_range<T>(x)`
tells you whether `x` fits in `T`.

Not every mixed pair converts to unsigned: `long` and `unsigned int` on 64-bit Linux convert to
`long`. The rules and a traced example are on [Conversions and Promotions](./conversions-and-promotions.md).

## Common mistakes

**A countdown loop that never ends.** An unsigned counter is never negative, so `i >= 0` is always
true:

```cpp title="countdown.cpp" showLineNumbers
#include <cstddef>
#include <vector>

void visit(int) {}

void backwards(const std::vector<int>& v) {
    // for (std::size_t i = v.size() - 1; i >= 0; --i)   // infinite: wraps from 0 to SIZE_MAX
    for (std::size_t i = v.size(); i-- > 0;)            // tests before decrementing
        visit(v[i]);
}

int main() { backwards({1, 2, 3}); }
```

GCC with `-Wextra` warns that the commented condition is always true (`-Wtype-limits`).

**`v.size() - 1` on an empty container.** It is `SIZE_MAX`, not -1. Check `empty()` first, or use
`std::ssize(v)` *(C++20)*, which returns a signed `std::ptrdiff_t`.

**Using unsigned as "can't be negative".** An `unsigned` parameter doesn't stop a caller from
passing -1. The value is silently converted to 4294967295. The C++ Core Guidelines
([ES.106](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)) advise
against it.

## When to use which

- **Signed** for quantities and anything you subtract: counts, indices you compute with, offsets,
  differences.
- **Unsigned** for bit patterns (masks, flags, hashes), for deliberate modular arithmetic, and
  where an interface demands it (`std::size_t` from `size()`).

## Key points

- Unsigned wraps modulo 2^N. Signed overflow is undefined behavior, even in C++20.
- Converting to unsigned is modulo 2^N. Converting an out-of-range value to signed is also modulo
  2^N since C++20.
- `int` meeting `unsigned` turns the `int` into `unsigned`. Use `std::cmp_less` and friends.
- Plain `char` may be signed or unsigned.

## Related

- [Bitwise Operators](../02-language-fundamentals/operators/bitwise.md): shifts and masks, where
  unsigned is the right choice.
- [Undefined Behavior](../10-error-handling-and-safety/06-undefined-behavior.md): why the
  optimizer exploits signed overflow.
