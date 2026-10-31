---
id: bitwise-operators
title: Bitwise Operators
sidebar_label: Bitwise
sidebar_position: 3
tags: [c++, operators, bitwise, bit-manipulation]
---

# Bitwise Operators

Bitwise operators work on the individual bits of an integer rather than on its numeric value. You
need them for flag sets (several on/off options packed into one integer), masks, hardware registers,
packed file formats and hashing. This page is the C++ operator reference: what each operator does,
and the type and shift rules that make bit code go wrong. Algorithmic tricks (isolating the lowest
set bit, counting bits by hand) are in
[Bit Manipulation Techniques](../../../../computer-science/bit-manipulation/techniques.md).

**Prerequisites:** [Arithmetic Operators](./arithmetic.md) (integer promotion),
[Fundamental Types](../../03-types-and-values/fundamental-types.md).

## The operators

| Operator | Name | Result bit is 1 when… |
|---|---|---|
| `a & b` | AND | the bit is 1 in **both** `a` and `b` |
| `a \| b` | OR | the bit is 1 in **either** |
| `a ^ b` | XOR (exclusive or) | the bit is 1 in **exactly one** |
| `~a` | NOT (complement) | the bit is 0 in `a` (every bit flips) |
| `a << n` | left shift | bits move `n` places towards the high end; zeros enter at the bottom |
| `a >> n` | right shift | bits move `n` places towards the low end (see signed shifts below) |

Each has a compound form: `&=`, `|=`, `^=`, `<<=`, `>>=`. Lined up bit by bit:

```text
a      = 1100  (12)
b      = 1010  (10)
a & b  = 1000  (8)
a | b  = 1110  (14)
a ^ b  = 0110  (6)
a << 1 = 11000 (24)
a >> 1 = 0110  (6)
```

`~a` flips **all** bits of the type, not just the ones you wrote: for a 32-bit `unsigned`
`a = 12`, `~a` is `0xfffffff3`.

## Flag sets

The everyday use: give each option its own bit, then combine, add, remove and test them.

```cpp title="flags.cpp" showLineNumbers
#include <bitset>
#include <iostream>

enum Perm : unsigned { Read = 1u << 0, Write = 1u << 1, Exec = 1u << 2 };

int main() {
    unsigned p = Read | Write;   // combine          -> 011
    p |= Exec;                   // set a flag       -> 111
    p &= ~Write;                 // clear a flag     -> 101
    bool can_write = p & Write;  // test a flag      -> false
    p ^= Exec;                   // toggle a flag    -> 001
    std::cout << std::bitset<3>(p) << ' ' << can_write << '\n';   // prints: 001 0
}
```

The pattern to memorise: **`|=` sets, `&= ~` clears, `^=` toggles, `&` tests.**

## Types: promotion and signedness

Bitwise operators apply the same [integral promotion](./arithmetic.md#mixed-types-conversions-happen-first)
as arithmetic. Anything smaller than `int` becomes `int` first, which surprises people working with
bytes:

```cpp
std::uint8_t byte = 0x0F;
auto flipped = ~byte;                            // int, value -16 (0xFFFFFFF0), not 0xF0
auto low8    = static_cast<std::uint8_t>(~byte); // 0xF0 (240): convert back explicitly
```

Use **unsigned, fixed-width types** (`std::uint32_t`, `std::uint64_t` from `<cstdint>`) for bit
work. The width is then explicit and none of the signed-shift rules below apply.

## Shifts: the rules

| Case | Rule |
|---|---|
| Shift count negative, or ≥ the bit width of the (promoted) left operand | **undefined behaviour** in every version. `x << 32` on a 32-bit type is not 0 |
| Unsigned left operand | always defined: `a << n` is `a · 2ⁿ` modulo 2^width, `a >> n` is `a / 2ⁿ` |
| Signed, non-negative, result fits | `a << n` is `a · 2ⁿ`, `a >> n` is `a / 2ⁿ` rounded down |
| Signed `a << n` with negative `a`, or a result that doesn't fit | undefined before C++20 *(one exception below)*; since **C++20** defined: `a · 2ⁿ` wrapped modulo 2^width |
| Negative `a >> n` | implementation-defined before C++20; since **C++20** an arithmetic shift (copies the sign bit): `-8 >> 1 == -4` |

The C++20 change ([P1236](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p1236r1.html))
followed from requiring two's complement for signed integers. Before it: `-1 << 1` was undefined;
`1 << 31` on a 32-bit `int` was undefined in C++11 and gave an implementation-defined value in
C++14/17. Even in C++20, writing `1u << 31` states the intent and works under every standard.

## Bitwise is not logical

`&` and `|` are not substitutes for `&&` and `||`:

- They compare bit patterns: `2 & 1` is `0` although both values are "true".
- They always evaluate both operands: no [short-circuit](./logical.md).
- They bind **looser than `==`**: `flags & MASK == 0` means `flags & (MASK == 0)`. Write
  `(flags & MASK) == 0`. See [Operator Precedence](./operator-precedence.md).

## Library help: `<bitset>` and `<bit>`

Before writing a bit trick by hand, check the library:

```cpp
#include <bit>      // (C++20)
#include <bitset>

std::bitset<8> bs{0b1010};
bs.set(0);                                 // 00001011
bs.count();                                // 3
std::popcount(0b1011u);                    // 3: number of set bits (unsigned types only)
std::has_single_bit(16u);                  // true: is it a power of two?
std::rotl(std::uint8_t{0b1000'0001}, 1);   // 0b0000'0011: rotate left
```

`std::bitset<N>` gives a fixed-size bit set with readable names and printing; the `<bit>`
functions compile to single instructions where the CPU has them.

## Key points

- `|=` sets, `&= ~` clears, `^=` toggles, `&` tests.
- Operands smaller than `int` are promoted first: `~` on a `uint8_t` gives a negative `int`.
- Do bit work on unsigned fixed-width types.
- Shifting by a negative count or by the full width or more is always undefined.
- `& | ^` bind looser than comparisons and never short-circuit.

## Related

- [Bit Manipulation Techniques](../../../../computer-science/bit-manipulation/techniques.md) — algorithms built on these operators
- [Logical Operators](./logical.md) — `&&` and `||`
- [Signedness](../../03-types-and-values/signedness.md) — signed vs unsigned representation
