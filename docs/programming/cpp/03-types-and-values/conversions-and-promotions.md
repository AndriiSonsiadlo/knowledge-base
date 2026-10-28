---
id: conversions-and-promotions
title: Type Conversions and Promotions
sidebar_label: Conversions
sidebar_position: 4
tags: [c++, conversions, casting, promotion, implicit, arithmetic]
---

# Type Conversions and Promotions

C++ converts values between types without being asked: when you assign an `int` to a `double`,
pass a `char` to a function taking `int`, or add a `short` to an `unsigned`. Most of these
conversions are harmless. A few change the value, such as `-1` becoming `4294967295` or `3.9`
becoming `3`, and nothing in the source shows where. This page gives the rules the compiler applies:
the kinds of implicit conversion, the **integral promotions**, and the **usual arithmetic
conversions** that pick a common type for a binary operator. It ends with explicit casts.

**Prerequisites:** [Fundamental Types](./fundamental-types.md), [Signedness](./signedness.md)

## Kinds of implicit conversion

| Conversion | Example | Value preserved? |
|---|---|---|
| Integral promotion | `short` → `int` | Always |
| Floating-point promotion | `float` → `double` | Always |
| Integral conversion | `int` → `unsigned`, `long` → `short` | Only if it fits. Otherwise reduced modulo 2^N (see [Signedness](./signedness.md#converting-between-signed-and-unsigned)) |
| Floating-point conversion | `double` → `float` | Rounded if not exactly representable. UB if out of range |
| Floating-integral | `double` → `int`, `int` → `float` | Float to integer truncates toward zero, **UB if the result doesn't fit**. Integer to float rounds |
| Boolean | `int`, pointer → `bool` | Zero and null become `false`, anything else `true` |
| Pointer | `Derived*` → `Base*`, `T*` → `void*`, `nullptr` → `T*` | Yes |

The full list, with the exact conditions, is on
[cppreference: Implicit conversions](https://en.cppreference.com/w/cpp/language/implicit_conversion).

A **narrowing** conversion is one that can lose information: floating to integer, `double` to
`float`, or integer to a type that can't hold every value of the source (unless the source is a
constant that fits). Narrowing is allowed in `int i = 3.9;`, but brace initialization rejects it:
`int i{3.9};` is an error. See [Uniform Initialization](../05-memory-and-object-lifetime/initialization/uniform-initialization.md).

## Integral promotions

Built-in arithmetic doesn't operate on types smaller than `int`. Before `+`, `*`, `<<`, unary `-`
and the other arithmetic operators, each operand of a small integer type is promoted:

- `signed char`, `unsigned char`, `short`, `unsigned short`, `char`: to `int` if `int` can
  represent every value of the type, otherwise to `unsigned int`. On every mainstream platform
  `int` is wider than `short`, so they all become `int`.
- `bool`: to `int` (`false` → 0, `true` → 1).
- `char8_t`, `char16_t`, `char32_t`, `wchar_t`: to the first of `int`, `unsigned int`, `long`,
  `unsigned long`, `long long`, `unsigned long long` that holds every value.
- An unscoped enum: to its underlying type if fixed, otherwise to the first type in the same list
  that can hold all its values. Scoped enums (`enum class`) are never promoted.
- A bit-field: to `int` if it fits, otherwise `unsigned int`, otherwise not promoted.

```cpp title="promote.cpp" showLineNumbers
#include <type_traits>

int main() {
    unsigned char a = 200, b = 100;
    auto sum = a + b;                       // int 300, not unsigned char 44
    static_assert(std::is_same_v<decltype(sum), int>);

    char16_t c = u'x';
    static_assert(std::is_same_v<decltype(+c), int>);    // unary + promotes too
    static_assert(std::is_same_v<decltype(+true), int>);
    (void)sum;
}
```

Promotion explains a common surprise: `uint8_t x = 255; x + 1` is `256`, not `0`, because the
addition happens in `int`. The wrap only appears if you store the result back into a `uint8_t`.

**Floating-point promotion** (`float` → `double`) is not applied to arithmetic operands: `f * 2.0f`
is computed as `float`. It happens only where a promotion is explicitly called for, such as passing
a `float` to a variadic function like `printf`.

## The usual arithmetic conversions

Binary operators like `+`, `-`, `*`, `/`, `<`, `==`, and the second and third operands of `?:`,
need both operands to have the same type. The **usual arithmetic conversions** choose it
([\[expr.arith.conv\]](https://eel.is/c++draft/expr.arith.conv)):

1. If either operand is a scoped enumeration, no conversion is done. The other operand must have
   the same type, or the program is ill-formed.
2. If either operand is floating-point, the other converts to the floating type of higher
   conversion rank: `long double` over `double` over `float`. An integer operand converts to that
   floating type.
3. Otherwise both are integers. Apply the **integral promotions** to both. If the types now match,
   stop.
4. If both are signed, or both unsigned, the one with the lower **conversion rank** converts to the
   other. Ranks increase from `int` to `long` to `long long`, with each unsigned type ranked equal to its signed
   counterpart.
5. Otherwise one is signed and one unsigned:
   - if the unsigned type's rank is **greater than or equal to** the signed type's rank, the signed
     operand converts to the **unsigned** type;
   - else, if the signed type can represent **every value** of the unsigned type, the unsigned
     operand converts to the **signed** type;
   - else both convert to the **unsigned version of the signed type**.

Rule 5 is where signed values silently become huge unsigned ones. Its middle branch depends on
type widths, so the same code can behave differently by platform:

<Tabs groupId="data-model">
  <TabItem value="lp64" label="Linux, macOS (LP64)">

`long` is 64 bits and `unsigned int` 32 bits. `long` can hold every `unsigned int`, so
`-1L < 1u` converts `1u` to `long` and is **true**. `1L + 1u` has type `long`.

  </TabItem>
  <TabItem value="llp64" label="Windows x64 (LLP64)">

`long` and `unsigned int` are both 32 bits. `long` can't hold every `unsigned int`, so both
convert to `unsigned long`: `-1L` becomes 4294967295 and `-1L < 1u` is **false**. `1L + 1u` has
type `unsigned long`.

  </TabItem>
</Tabs>

Both tabs were checked with `static_assert`: LP64 with GCC 15 and Clang 21 on x86-64 Linux, LLP64
with `clang++ --target=x86_64-pc-windows-msvc -fsyntax-only`.

### Tracing a mixed expression

Here is one expression with five operand types, evaluated on x86-64 Linux:

```cpp title="mixed.cpp" showLineNumbers
#include <cstdio>

int main() {
    unsigned char uc = 200;
    short         s  = -3;
    unsigned      u  = 1;
    long          l  = -1;
    float         f  = 0.5f;

    auto r = uc * s + u + l + f;        // parsed as (((uc * s) + u) + l) + f
    std::printf("%d %u %ld %.1f\n", uc * s, uc * s + u, uc * s + u + l, r);
}
```

```text
-600 4294966697 4294966696 4294966784.0
```

Output from GCC 15 and Clang 21, `-std=c++23 -Wall -Wextra`. Each intermediate type was also
confirmed with `static_assert(std::is_same_v<decltype(...), ...>)`.

<Walkthrough title="Evaluating uc * s + u + l + f" caption="x86-64 Linux: int 32-bit, long 64-bit, float IEEE-754 single." accent="amber">
  <Step title="uc * s">

Rule 3: both operands are smaller than `int`, so both are promoted. `uc` becomes `int` 200, `s`
becomes `int` -3. The types match, so the multiplication is done in `int`:
<StepChange>`int` -600</StepChange>.

  </Step>
  <Step title="(-600) + u">

`int` and `unsigned int` have equal rank, so rule 5's first branch applies: the signed operand
converts to `unsigned int`. -600 becomes 2^32 - 600 = 4294966696, plus 1:
<StepChange>`unsigned int` 4294966697</StepChange>.

  </Step>
  <Step title="4294966697u + l">

`long` outranks `unsigned int`, and a 64-bit `long` holds every 32-bit `unsigned` value, so rule 5's
second branch applies: the unsigned operand converts to `long`. 4294966697 + (-1):
<StepChange>`long` 4294966696</StepChange>. The value is positive: the -600 from step 1 was lost
at step 2 and isn't recovered.

  </Step>
  <Step title="4294966696L + f">

Rule 2: one operand is floating, so the `long` converts to `float`. A `float` has a 24-bit
significand, and between 2^31 and 2^32 consecutive floats are 256 apart. 4294966696 rounds to the
nearest one, 4294966784. Adding 0.5 changes nothing at that spacing:
<StepChange>`float` 4294966784.0</StepChange>.

  </Step>
</Walkthrough>

On Windows the third step would take rule 5's last branch instead: both operands become
`unsigned long`. The value is the same here, 4294966696, but its type is unsigned.

## Explicit conversions

When a conversion is intended, say so with a named cast. Each cast does a limited set of things,
which makes the intent searchable and lets the compiler reject the ones you didn't mean.

| Cast | Does | Typical use |
|---|---|---|
| `static_cast<T>(e)` | Any implicit conversion, plus its reverse where defined (`void*` → `T*`, `Base*` → `Derived*` without a check, `int` → enum) | Narrowing on purpose: `static_cast<int>(d)` |
| `const_cast<T>(e)` | Adds or removes `const`/`volatile` | Calling an old API that isn't `const`-correct. See [const and Pointers](../06-pointers-references-and-smart-pointers/const-and-pointers.md#casting-away-const) |
| `reinterpret_cast<T>(e)` | Reinterprets a pointer or integer as an unrelated pointer type | Hardware addresses, byte views. See [Strict Aliasing](../05-memory-and-object-lifetime/strict-aliasing.md) |
| `dynamic_cast<T>(e)` | Checked downcast in a polymorphic hierarchy | See [Virtual Functions](../07-classes-and-oop/virtual-functions.md) |
| `std::bit_cast<T>(e)` *(C++20, `<bit>`)* | Copies the object representation into a `T` of the same size | Viewing a `float`'s bits as `std::uint32_t` |
| `(T)e`, `T(e)` | C-style: tries `const_cast`, `static_cast`, then `reinterpret_cast` | Avoid. It silently picks the most permissive one that works |

User-defined types join this system through converting constructors and conversion operators
(`operator double() const`). Marking them `explicit` limits them to direct initialization and
casts. That belongs to class design and is covered with
[Constructors and Destructors](../07-classes-and-oop/constructors-and-destructors.md).

## Common mistakes

- **Comparing signed with unsigned.** `if (i < v.size())` with a negative `i` is false, because `i`
  becomes huge. GCC warns with `-Wall` (`-Wsign-compare`), Clang with `-Wextra`. C++20's
  `std::cmp_less(i, v.size())` compares the mathematical values.
- **Converting after the damage.** `double avg = sum / count;` with two `int`s divides in `int`
  first and truncates. Convert an operand, not the result: `static_cast<double>(sum) / count`.
- **Out-of-range float to integer.** `static_cast<int>(1e10)` is undefined behavior, not a
  saturated `INT_MAX`. Check the range first.
- **Large integers into `float`.** Integers above 2^24 (16777216) aren't all representable in
  `float`, as the walkthrough shows. Use `double` (exact up to 2^53) when integers flow into
  floating point.

## Key points

- Arithmetic never happens below `int`: small types are promoted first.
- One floating operand makes the whole operation floating, at the wider floating type.
- Signed meets unsigned of equal or higher rank: the signed value becomes unsigned.
- Whether `long` and `unsigned` mix as signed or unsigned depends on the platform.

## Related

- [Arithmetic Operators](../02-language-fundamentals/operators/arithmetic.md): the operators these
  rules apply to.
- [Signedness](./signedness.md): what happens to the value when it changes signedness.
