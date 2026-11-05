---
id: strict-aliasing
title: Strict Aliasing Rule
sidebar_label: Strict Aliasing
sidebar_position: 8
tags: [c++, strict-aliasing, type-punning, bit-cast, memcpy, undefined-behavior, optimization]
---

# Strict Aliasing Rule

Strict aliasing is the rule that decides **which types may be used to access an object**. Reading or
writing an `int` object through a `float` glvalue is undefined behavior, even when the bytes are
there and the hardware would happily load them. The compiler is allowed to assume you never do it,
and it uses that assumption to keep values in registers and to reorder or delete memory accesses.
This page is the canonical home of the rule, of type punning, and of `-fno-strict-aliasing`.

**Prerequisites:** [Object lifetime](./object-lifetime.md) (what "an object of type T" means) and
[Memory alignment](./alignment.md). Casts themselves are covered in
[Conversions and promotions](../03-types-and-values/conversions-and-promotions.md).

:::danger[Undefined behavior]
A program that violates the rule has no defined behavior at all. It can print the "right" answer at
`-O0` and a different one at `-O2`, and the same binary can change behavior after an unrelated edit
that changes inlining.
:::

## The rule

An object has a type (its *dynamic type*, fixed by [how it was created](./object-lifetime.md)). The
standard ([basic.lval]) says that accessing the stored value of an object through a glvalue of any
other type is undefined behavior, apart from this list:

| Allowed access type | Example for an object of dynamic type `int` |
|---|---|
| The dynamic type itself | `int` |
| The signed or unsigned type corresponding to the dynamic type | `unsigned int` |
| `char`, `unsigned char`, `std::byte` | byte-wise reads and writes of any object |

Each row applies to a type that is merely *similar* to the listed one. Roughly, similar types differ
only in cv-qualification at each level (see cppreference, "Similar types", for the full definition,
which also covers arrays of known and unknown bound). So `const int` and `volatile int` are covered by
the first row, `int*` and `const int*` are similar, and `int*` and `float*` are unrelated.

Earlier standards (C++17) also listed aggregate/union types containing the dynamic type and base
classes of it as separate bullets; the current draft has only the three above. Accessing a member or a
base-class subobject is an access to that subobject's own type, so ordinary code is unaffected.

Things that are **not** exceptions, despite folklore:

- **`void*` is not a free pass.** You cannot dereference it. The cast chain `int*` to `void*` and back
  to `int*` is fine because you end up accessing an `int` as an `int`. Going through `void*` to
  `float*` is a violation like any other.
- **`short` and `int`, or `int` and `long`, never alias**, even if they have the same size on your
  platform. Only the signed/unsigned pair of the *same* integer type counts.
- **`char` is special in one direction.** Any object may be *accessed* through `unsigned char*`,
  `char*` or `std::byte*`. The reverse is not true: you may not treat a `char` buffer as an `int`
  by casting its address. That is exactly the [lifetime](./object-lifetime.md) problem solved by
  placement new and, since C++23, `std::start_lifetime_as`.

Merely **forming** the pointer with `reinterpret_cast` is not the violation. The violation is the
*access* (`*fp`, `fp->x`) through a glvalue of a disallowed type.

## Why compilers exploit it

If the compiler could not assume `int*` and `float*` point to different objects, every store through
a `float*` would force it to reload every `int` it had cached in a register. With the rule, it knows
better. This is called *type-based alias analysis* (TBAA).

```cpp title="alias.cpp" showLineNumbers
#include <cstdio>

__attribute__((noinline)) int store_both(int* i, float* f) {
    *i = 1;
    *f = 2.0f;      // the compiler may assume this cannot modify *i
    return *i;      // so it may return the constant 1 without reloading
}

int main() {
    int x = 0;
    int r = store_both(&x, reinterpret_cast<float*>(&x));  // UB: x is an int, accessed as float
    std::printf("%d\n", r);
}
```

(`__attribute__((noinline))` is a GCC/Clang extension used here only to keep the optimiser from
seeing both pointers at once.) Compiled with `-std=c++20 -Wall -Wextra`, with g++ 15.2.0 and
clang++ 21.1.8 on x86-64 Linux, no warnings, and both compilers printed:

| Flags | g++ 15.2.0 | clang++ 21.1.8 |
|---|---|---|
| `-O0` | `1073741824` (the bit pattern of `2.0f`, `0x40000000`) | `1073741824` |
| `-O2` | `1` | `1` |

Same source, two answers. At `-O0` the load after the store really reads the memory, which the
`float` store overwrote. At `-O2` the compiler reasons "a `float` store cannot change an `int`", so
`*i` is still `1`. Because the program is undefined, **neither result is guaranteed**: a different
compiler or version could print anything, or the optimiser could delete the code path entirely.

:::tip
The rule is a *contract that buys speed*, not a quirk. Code that respects it lets the compiler keep
values in registers across stores to unrelated types. Compare `-O2` with `-O2 -fno-strict-aliasing` on
your own code before claiming a number; the gain is workload-dependent, and this page does not quote
one.
:::

## Safe type punning

*Type punning* means reading the bits of an object as a different type. The tools that are defined:

### `std::memcpy`

`std::memcpy` copies bytes between two objects, and byte access is always allowed. The destination
must be a real object of the target type (here a local `std::uint32_t`), and both types must be
trivially copyable. With optimisation on, GCC and Clang turn a fixed-size `memcpy` like this into a
plain move; there is no call.

### `std::bit_cast` *(C++20, `<bit>`)*

`std::bit_cast<To>(from)` returns a `To` whose object representation is that of `from`. It requires
`sizeof(To) == sizeof(From)` and both trivially copyable (checked at compile time), and it is
`constexpr` where the types allow it.

```cpp title="punning.cpp" showLineNumbers
#include <bit>
#include <cstdint>
#include <cstdio>
#include <cstring>

std::uint32_t bits_memcpy(float f) {
    static_assert(sizeof(float) == sizeof(std::uint32_t));
    std::uint32_t u;
    std::memcpy(&u, &f, sizeof u);
    return u;
}

constexpr std::uint32_t bits_cast(float f) { return std::bit_cast<std::uint32_t>(f); }
static_assert(bits_cast(1.0f) == 0x3f800000u);   // usable at compile time (IEEE 754 binary32)

int main() {
    float f = 1.0f;
    std::printf("%08x %08x\n", bits_memcpy(f), bits_cast(f));

    // Byte view through unsigned char is always allowed.
    unsigned char bytes[sizeof f];
    std::memcpy(bytes, &f, sizeof f);
    const unsigned char* p = reinterpret_cast<const unsigned char*>(&f);
    std::printf("%d\n", bytes[sizeof f - 1] == p[sizeof f - 1]);
}
```

Output, identical with g++ 15.2.0 and clang++ 21.1.8 at both `-O0` and `-O2` (`-std=c++20 -Wall
-Wextra`, x86-64, no warnings):

```text
3f800000 3f800000
1
```

The numeric value `0x3f800000` assumes IEEE 754 `float`; the *byte order* of the result in memory is
a separate matter, see [endianness](../12-low-level-and-platform/04-endianness.md).

Prefer `std::bit_cast` on C++20, `std::memcpy` before that. Both give the optimiser everything it
needs; the `bit_cast` form is shorter, cannot silently get `sizeof` wrong, and works in constant
expressions.

### Unions are not a portable alternative

Writing one union member and reading another is undefined in ISO C++ (only the common initial
sequence of standard-layout members is exempt). GCC documents that it allows this when the memory is
accessed through the union type (GCC manual, `-fstrict-aliasing`), but that is a compiler extension,
not C++, and this page makes no claim about other compilers. Use `bit_cast` or
`memcpy`. The [undefined behavior](../10-error-handling-and-safety/06-undefined-behavior.md) page lists
this among the common UB sources.

### Walking an object's bytes

Reading any object through `unsigned char*`, `char*` or `std::byte*` is allowed, which is how
serialisers, hashes and `memcmp`-style code inspect objects:

```cpp
// fragment
const auto* bytes = reinterpret_cast<const unsigned char*>(&obj);
for (std::size_t i = 0; i < sizeof obj; ++i) use(bytes[i]);
```

Note that padding bytes have unspecified values, so hashing or comparing whole structs this way can
differ between equal objects (see [padding](../12-low-level-and-platform/03-padding-and-offsetof.md)).

## What about `reinterpret_cast`?

`reinterpret_cast` between unrelated object pointer types compiles and produces a pointer, but any
access through it is the violation, as in `alias.cpp`. Legitimate uses are casts **to** byte types
(above), and round trips (`T*` to another pointer type and back to `T*`) in which the object is only
ever accessed as its real type. Casting a suitably aligned byte buffer to `T*` is only valid if a
`T` object really lives there; see [placement new](./placement-new.md) and
[object lifetime](./object-lifetime.md).

## Compiler flags and tools

- **`-fno-strict-aliasing`** (GCC, Clang) disables the assumption, so the optimiser treats any
  pointers as possibly aliasing. It is a legitimate escape hatch for code you cannot fix (the Linux
  kernel builds with it). It is not a language guarantee: the program is still not valid C++, other
  compilers behave differently, and you lose the optimisation. Verified: `alias.cpp` built with
  `-O2 -fno-strict-aliasing` printed `1073741824` on both g++ 15.2.0 and clang++ 21.1.8.
- **`-Wstrict-aliasing`** (GCC; `-Wall` enables level 3, `-Wstrict-aliasing=N` selects strictness) is a
  best-effort warning. On `alias.cpp` with `-O2 -Wall -Wextra` g++ 15.2.0 printed nothing, while
  `-Wstrict-aliasing=2` reported "dereferencing type-punned pointer will break strict-aliasing rules".
  It misses violations that cross function boundaries, so do not rely on it to find them.
- **UBSan has no strict-aliasing check.** `-fsanitize=undefined` on `alias.cpp` (g++ 15.2.0, `-O2`)
  still printed `1` with no report. Differential testing (compare `-O0`, `-O2` and
  `-fno-strict-aliasing`) is the portable way to detect violations.
- **Clang's TypeSanitizer** (`-fsanitize=type`, experimental, Clang only) does check this. On
  `alias.cpp`, clang++ 21.1.8 with `-O1 -fsanitize=type` reported
  `type-aliasing-violation ... WRITE of size 4 ... with type float accesses an existing object of type int`.
  See the Clang TypeSanitizer documentation for its limits (it cannot be combined with other
  sanitizers such as ASan).

## Pitfalls

| Mistake | Why it is wrong | Fix |
|---|---|---|
| `*reinterpret_cast<float*>(&u32)` | Accesses a `uint32_t` as `float` | `std::bit_cast<float>(u32)` |
| `reinterpret_cast<Pkt*>(char_buf)` then `p->field` | No `Pkt` object lives in the buffer (and alignment may be wrong) | `std::memcpy` into a `Pkt`, or placement new / `std::start_lifetime_as` |
| `int*` and `long*` to the same memory because "both 8 bytes" | Different types, no exception | Use one type, or `memcpy` |
| Union write one member, read another | UB in ISO C++ | `bit_cast` / `memcpy` |
| Assuming "it works at `-O0`, so it is fine" | The optimiser is what exploits the rule | Test at `-O2` and consider `-fsanitize=undefined` for the other UB |

## Key points

- You may access an object only through a type similar to its own, to its signed/unsigned counterpart,
  or to a byte type (`char`, `unsigned char`, `std::byte`).
- `void*` is not an exception, and same-size integer types do not alias.
- The compiler uses the rule for type-based alias analysis; with a violation, `-O0` and `-O2` can
  disagree (shown above), and neither answer is guaranteed.
- Punning: `std::bit_cast` (C++20) or `std::memcpy`. Not pointer casts, not unions.
- `-fno-strict-aliasing` is a workaround for legacy code, not a fix. UBSan and `-Wstrict-aliasing`
  will not reliably catch violations; Clang's experimental TypeSanitizer can.
