---
id: bitwise-operators
title: Bitwise Operators
sidebar_label: Bitwise
sidebar_position: 3
tags: [c++, operators, bitwise, bit-manipulation]
---

# Bitwise Operators

Bitwise operators manipulate the individual bits of integer values. They are the building blocks of
flag sets, masks, packed data, and low-level protocol code.

:::info Where to go deeper
This page is the C++ operator reference. For the *algorithmic* side — counting bits, isolating the
lowest set bit, parity tricks — see [Bit Manipulation Techniques](../../../../computer-science/bit-manipulation/techniques.md).
:::

## The operators

| Operator | Name        | Effect                                             |
|----------|-------------|----------------------------------------------------|
| `&`      | AND         | bit set in result iff set in **both** operands     |
| `\|`     | OR          | bit set iff set in **either** operand              |
| `^`      | XOR         | bit set iff set in **exactly one** operand         |
| `~`      | NOT         | flips every bit (unary)                            |
| `<<`     | left shift  | multiply by 2ⁿ (bits shifted in are zero)          |
| `>>`     | right shift | divide by 2ⁿ (sign-dependent — see below)          |

```cpp showLineNumbers
unsigned a = 0b1100;
unsigned b = 0b1010;
a & b;    // 0b1000  (8)
a | b;    // 0b1110  (14)
a ^ b;    // 0b0110  (6)
~a;       // all bits flipped — depends on width of the type
a << 1;   // 0b11000 (24)
a >> 1;   // 0b0110  (6)
```

## Flag sets — the canonical use

```cpp showLineNumbers
enum Perm : unsigned { Read = 1u << 0, Write = 1u << 1, Exec = 1u << 2 };

unsigned p = Read | Write;     // set bits         -> 0b011
p |=  Exec;                    // add a flag       -> 0b111
p &= ~Write;                   // clear a flag     -> 0b101
bool can_read = p & Read;      // test a flag      (non-zero == set)
p ^=  Exec;                    // toggle a flag
```

## Shifts: the sharp edges

:::warning Two real traps
- **Shift by ≥ the type width is undefined behaviour.** `x << 32` on a 32-bit `int` is UB, not 0.
- **Right-shifting a *negative* signed value is implementation-defined** (arithmetic on every
  mainstream compiler, but not guaranteed by the standard pre-C++20).

Do bit work on **unsigned** types. `uint32_t`/`uint64_t` make width explicit and shifts well-defined.
:::

```cpp showLineNumbers
uint32_t mask = 1u << 31;     // OK: uint32_t literal, bit 31 set
// int bad   = 1  << 31;      // UB on most platforms: overflows signed int
```

## Bitwise vs logical

A recurring beginner bug is writing `&`/`|` where `&&`/`||` was meant. Bitwise operators do **not**
short-circuit and compare bit patterns, not truth values:

```cpp showLineNumbers
if (a & b)  { ... }   // true when a and b share any set bit
if (a && b) { ... }   // true when both a and b are non-zero
```

See [Logical Operators](./logical.md) for the short-circuiting pair.

## `std::bitset` and `<bit>`

For readable flag handling and portable bit utilities, prefer the library over hand-rolled tricks:

```cpp showLineNumbers
#include <bitset>
#include <bit>                 // C++20
std::bitset<8> bs{0b1010};
bs.set(0); bs.flip(); bs.count();              // legible bit ops
int n = std::popcount(0b1011u);                // 3 — set-bit count
bool p = std::has_single_bit(16u);             // is power of two?
```

## Summary

- `&` `|` `^` `~` work per bit; `<<`/`>>` scale by powers of two.
- Use **unsigned, fixed-width** types — signed shifts and overflow invite UB.
- Shifting by `≥` the bit width is undefined behaviour.
- `&`/`|` are not `&&`/`||`: no short-circuit, different meaning.
- Reach for `std::bitset` and `<bit>` (`popcount`, `has_single_bit`, `rotl`) before clever tricks.

## Related

- [Bit Manipulation Techniques](../../../../computer-science/bit-manipulation/techniques.md) — algorithms
- [Logical Operators](./logical.md)
- [Signedness](../../03-types-and-values/signedness.md)
