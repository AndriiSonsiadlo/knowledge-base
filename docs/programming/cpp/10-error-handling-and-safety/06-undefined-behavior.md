---
id: undefined-behavior
title: Undefined Behavior
sidebar_label: Undefined Behavior
sidebar_position: 6
tags: [cpp, undefined-behavior, ub, safety, sanitizers, compiler-optimization]
---

# Undefined Behavior

For some operations the C++ standard imposes **no requirements at all**. It does not say "the result is
unspecified" or "the program crashes". It says the whole program has no defined meaning. That is
**undefined behavior** (UB). The reason this matters is not the crash you might get, but that
**compilers are allowed to assume UB never happens** and optimize on that assumption. A program with UB
can behave correctly in a debug build and wrongly in a release build, or change behavior after a
compiler upgrade. This page defines the term, shows how optimizers exploit it, catalogues the common
sources with links to the pages that own each rule, and shows how to catch UB with tools.

**Prerequisites:** [Compilation](../01-toolchain-and-build/compilation.md) (optimization levels).

## Four kinds of "not fully specified"

| Term | Meaning | Example |
|---|---|---|
| **Well-defined** | One result, fixed by the standard | `unsigned` arithmetic wraps modulo 2^N |
| **Implementation-defined** | Each implementation chooses and **must document** it | `sizeof(int)`, whether `char` is signed |
| **Unspecified** | A set of allowed outcomes, no documentation required | Order of evaluation of function arguments |
| **Undefined** | No requirements on the whole program | Signed overflow, null dereference |

In addition, some rule violations are *ill-formed, no diagnostic required* (IFNDR): the program is invalid,
but the compiler is not obliged to tell you. Examples include certain
[ODR violations](../01-toolchain-and-build/translation-units.md). Treat IFNDR like UB.

UB is not confined to the line that triggers it. Because the standard places no requirement on a program
that executes UB, the compiler's earlier transformations may already have "used" the fact, which is what
people mean by UB *time travel*.

## Why UB exists

The language gives up checking so that the compiler can generate code without it. Bounds checks,
overflow checks, null checks, and aliasing checks cost instructions on every operation. By declaring
those cases UB, the standard lets the optimizer assume, for example, that:

- a signed `int` never overflows, so `x + 1 > x` is always true and loop counters can be widened;
- a pointer that was dereferenced is not null, so a later `if (p == nullptr)` is dead code;
- two pointers to different types do not alias, so loads can be reordered
  ([strict aliasing](../05-memory-and-object-lifetime/strict-aliasing.md));
- control never reaches an unreachable branch.

### What the optimizer does with it

```cpp title="ub_opt.cpp" showLineNumbers
bool always(int x)       { return x + 1 > x; }   // signed: overflow is UB
bool always_u(unsigned x){ return x + 1 > x; }   // unsigned: wraps, so false for UINT_MAX

int table[4];
bool contains(int x) {
    for (int i = 0; i <= 4; ++i)                 // off-by-one: reads table[4], UB
        if (table[i] == x) return true;
    return false;
}
```

At `-O2` on x86-64, g++ 15.2 compiles `always` to `movl $1, %eax; ret`: it returns `true` without
looking at `x`. `always_u` keeps the comparison (`cmpl $-1, %edi; setne %al`), since the unsigned
result really depends on `x`. For `contains`, g++ 15.2 `-O2` emits the equivalent of `return true;`
(the loop can only exit by finding a match without touching `table[4]`, so the compiler assumes it
does), while clang++ 21.1 `-O2` vectorizes the first four comparisons and then loads `table[4]`, one past the end.
Neither compiler is wrong. These are results of particular compiler versions on one target and
will differ elsewhere, which is the point: the standard allows both. `-fwrapv` (GCC/Clang) makes signed
overflow wrap, turning `always` back into a real comparison, but that is a dialect flag, not portable C++.

## Catalogue of common sources

Each rule below has a canonical home; this table is the index. Cause, then how to avoid it.

| Source | Why it is UB | Avoid with | Details |
|---|---|---|---|
| Signed integer overflow | Result not representable in the type | Check before, widen, use unsigned deliberately, `<numeric>` saturating helpers *(C++26)* | [Signed and unsigned types](../03-types-and-values/signedness.md#overflow) |
| Shift by negative or ≥ width | Count out of range for the promoted type | Mask or check the count | [Bitwise operators](../02-language-fundamentals/operators/bitwise.md) |
| Division or modulo by zero (and `INT_MIN / -1`) | No result | Check divisor | [Operators](../02-language-fundamentals/operators/arithmetic.md) |
| Out-of-bounds access, pointer past `end()` | Pointer arithmetic leaves the array | `at()`, `std::span`, ranges, hardened library | [Pointer arithmetic](../06-pointers-references-and-smart-pointers/pointer-arithmetic.md) |
| Null or dangling pointer dereference | No object at that address | Smart pointers, ownership discipline | [Object lifetime](../05-memory-and-object-lifetime/object-lifetime.md), [raw pointers](../06-pointers-references-and-smart-pointers/raw-pointers.md) |
| Use after free, double free, mismatched `new[]`/`delete` | Object's lifetime ended or never began | RAII, [`new`/`delete` rules](../05-memory-and-object-lifetime/new-and-delete.md) | [Object lifetime](../05-memory-and-object-lifetime/object-lifetime.md) |
| Reading an uninitialized object | Indeterminate value (C++26 changes the status of uninitialized automatic variables to *erroneous behavior*, which is not UB; verify your compiler) | Always initialize | [Default initialization](../05-memory-and-object-lifetime/initialization/default-initialization.md) |
| Accessing an object through an incompatible type | Violates the effective-type rules | `std::memcpy`, `std::bit_cast` *(C++20)* | [Strict aliasing](../05-memory-and-object-lifetime/strict-aliasing.md) |
| Misaligned access | Pointer not aligned for its type | `alignas`, `memcpy` | [Alignment](../05-memory-and-object-lifetime/alignment.md) |
| Unsequenced modification, e.g. `i++ + ++i` | Two unsequenced side effects on one scalar | One side effect per statement | [Order of evaluation](../02-language-fundamentals/operators/evaluation-order.md) |
| Data race | Unsynchronized conflicting accesses | Mutexes, atomics | [Data races](../11-concurrency-and-memory-model/03-data-races.md) |
| Modifying a `const` object or a string literal | Object is in read-only storage, or the program promised not to | Use `std::string`, `const` correctness | [Const and pointers](../06-pointers-references-and-smart-pointers/const-and-pointers.md) |
| Invalid `static_cast`/`reinterpret_cast`/`dynamic_cast` result used | Object is not of the target type | Prefer `dynamic_cast` with checks | [Casts](../03-types-and-values/conversions-and-promotions.md) |
| Flowing off the end of a non-`void` function | No value returned | Enable `-Wreturn-type`; `-Werror=return-type` | — |
| Violating the ODR | Two different definitions of one entity | Headers, `inline`, anonymous namespaces | [Translation units](../01-toolchain-and-build/translation-units.md) |
| Calling `std::unreachable()` or a library function with its precondition violated | Documented as UB | Check the documentation | [Assertions](./04-assertions.md) |

The standard library also defines many "narrow contracts" where a violated precondition is UB:
`vector::operator[]` with an invalid index, dereferencing `end()`, `front()` on an empty container,
invalidated iterators, and so on. C++26 contracts and library hardening aim at turning those into
diagnosed failures; see [Contracts](./05-contracts.md).

## How the compiler can make UB worse: a null check that vanishes

```cpp showLineNumbers
// ...  (fragment)
int read(int* p) {
    int v = *p;              // UB if p is null: so the compiler may assume p != nullptr
    if (p == nullptr)        // ...and delete this check
        return -1;
    return v;
}
```

Optimizers routinely drop the later test, since `*p` already committed to a non-null pointer. A
null-pointer dereference is therefore not guaranteed to be a segmentation fault, and reordering the
statements (check first) is the fix. This is a representative example; the actual codegen depends on the
compiler and flags such as `-fdelete-null-pointer-checks` (enabled by default on most targets per the GCC manual).

## Detecting UB

Nothing detects all UB. Combine several layers.

| Tool | Catches | Flags |
|---|---|---|
| **Compiler warnings** | Some obvious cases: missing return, uninitialized use, unsequenced access | `-Wall -Wextra -Wuninitialized -Wreturn-type -Wsequence-point` (GCC) |
| **Constant evaluation** | Core-language UB reached during constant evaluation is a compile error (library UB need not be diagnosed) | `constexpr` variables, `static_assert` |
| **UBSan** | Signed overflow, bad shifts, null dereference, out-of-bounds on arrays of known size, misaligned access, invalid enum/bool loads | `-fsanitize=undefined` (GCC, Clang) |
| **ASan** | Heap/stack/global overflow, use-after-free, use-after-scope | `-fsanitize=address` |
| **TSan** | Data races | `-fsanitize=thread` |
| **MSan** (Clang) | Reads of uninitialized memory | `-fsanitize=memory` |
| **Static analyzers** | Path-sensitive null, leaks, lifetime | `clang-tidy`, `clang --analyze`, `gcc -fanalyzer` |

Sanitizers only detect UB on paths your tests execute, and they slow the program, so use them in test
and CI builds, not in production. See [Sanitizers](../14-debugging-and-profiling/04-sanitizers.md) for use
and options.

The following program was compiled with `-fsanitize=undefined` on g++ 15.2 and clang++ 21.1; the
run-time diagnostics below are what UBSan prints (the program's own behavior after UB is undefined and
not shown):

```cpp title="ubsan.cpp" showLineNumbers
#include <climits>
#include <cstdio>
int main(int argc, char**) {
    int x = INT_MAX - 1 + argc;      // INT_MAX when run with no arguments
    int y = x + 1;                   // signed overflow
    std::printf("%d\n", y);
}
```

```text
ubsan.cpp:5:9: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
```

(Clang reports column 15; the message is otherwise the same.) A `constexpr` context turns the same kind of
mistake into a compile error:

```cpp title="constexpr_ub.cpp" showLineNumbers
constexpr int f(int a, int b) { return a / b; }
constexpr int v = f(1, 0);       // error: not a constant expression (division by zero)
int main() {}
```

g++ 15.2: `error: '(1 / 0)' is not a constant expression`. Clang 21.1: `constexpr variable 'v' must be
initialized by a constant expression`.

## Reducing exposure

- **Make the safe thing the default:** `std::vector::at`, `std::span`, `std::array`, `std::optional`,
  smart pointers, range-for, `std::string_view` with care for lifetime.
- **Initialize everything**, and prefer `const`.
- **Compile with warnings and sanitizers in CI**, and run tests under ASan and UBSan.
- **Harden the standard library** (`-D_GLIBCXX_ASSERTIONS`, libc++ hardening modes) for bounds and
  precondition checks in production builds, accepting a small cost (measure it for your workload).
- **Keep UB out of `constexpr` code**, which gives you a free checker for core-language UB.
- **Don't test for overflow after the fact** (`if (a + b < a)` is UB for signed). Check with
  `a > INT_MAX - b`, or use builtins such as `__builtin_add_overflow` (GCC/Clang), or compare in a wider type.

## Common mistakes

- "It worked in debug, so it's fine." UB is allowed to work, and optimization levels change the outcome.
- Assuming a null dereference always traps, or that signed overflow wraps because the CPU does.
- Using `-fwrapv`/`-fno-strict-aliasing` as a fix. They are workarounds that define some behavior in
  one compiler and leave the code non-portable.
- Treating a sanitizer pass as proof of absence. It only covers executed paths.

## Key points

- UB means no requirements on the entire program, and compilers optimize assuming it never occurs.
- Implementation-defined and unspecified behavior are bounded; undefined and IFNDR are not.
- Most UB is one of a small set: overflow, bad indices, dangling or null pointers, aliasing, races,
  uninitialized reads. Each is owned by a page linked above.
- Catch UB with warnings, `constexpr`, UBSan, ASan and TSan in CI; prevent it with safe types and hardened
  libraries.
