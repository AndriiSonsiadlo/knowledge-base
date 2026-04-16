---
id: data-representation-overview
title: Data Representation
sidebar_label: Overview
sidebar_position: 1
tags: [computer-science, data-representation, binary, bits]
---

# Data Representation

## Overview

Every value a computer manipulates — an integer, a character, a color, an instruction — is ultimately
a fixed-width string of bits. This section covers how those bits encode meaning: binary/hexadecimal
notation, signed integers (two's complement), and the bitwise techniques programmers use to pack,
test, and transform data directly at the bit level. It deliberately skips grade-school binary/decimal
conversion — the focus is on the representations and tricks that matter for real systems work.

## In this section

1. **[Basics](./basics.md)** — binary/hex notation and bitwise operators as building blocks.
2. **[Integers & Two's Complement](./integers-and-twos-complement.md)** — fixed-width signed integers, overflow, and signed/unsigned comparison pitfalls.
3. **[Floating Point](./floating-point.md)** — IEEE 754 bit layout, rounding error, and special values.
4. **[Character Encoding](./character-encoding.md)** — ASCII, Unicode code points, and UTF-8.
5. **[Bit Manipulation Techniques](./techniques.md)** — practical bit-manipulation patterns (masks, flags, counting bits).

## Why it matters

- **[CPU & Processor Architecture](../cpu-architecture/intro.md)** operates directly on these fixed-width
  encodings — registers are just bit patterns interpreted by an instruction.
- Bitwise tricks are the fastest primitives available in a language: no allocation, no branching (when
  written carefully), a handful of CPU cycles.

## Related Pages

- [How Computers Work — Overview](../overview/intro.md)
- [CPU & Processor Architecture](../cpu-architecture/intro.md)
- C++ operator reference: [Bitwise Operators](../../programming/cpp/02-language-fundamentals/operators/bitwise.md)
