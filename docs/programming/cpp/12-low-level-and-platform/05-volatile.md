---
id: volatile
title: volatile
sidebar_label: volatile
sidebar_position: 5
tags: [cpp, volatile, memory-mapped-io, signals, deprecated, embedded]
---

# `volatile`

`volatile` is a type qualifier that tells the compiler an object's accesses have effects it cannot see:
reading may return a different value each time, and writing may do something besides storing. The
compiler must therefore perform every access the program text asks for, in program order relative to other
`volatile` accesses. That is exactly what memory-mapped hardware registers need. It is **not** what
shared data between threads needs: `volatile` gives no atomicity and no ordering with other memory, and a
program that races on a `volatile` object has undefined behaviour just like one that races on an
`int`. This page defines what `volatile` guarantees, where it is the right tool, and which uses C++20 deprecated.

**Prerequisites:** [cv-qualifiers](../03-types-and-values/cv-qualifiers.md) (how qualifiers attach to types
and pointers). The atomic alternative is on [Atomics and fences](../11-concurrency-and-memory-model/02-atomics-and-fences.md).

## What the compiler must do

The standard treats an access (read or write) to a `volatile` glvalue as part of the program's
**observable behavior**: the abstract machine performs it, with its value, in the order the program
specifies relative to other `volatile` accesses and to I/O. An optimiser may not remove, merge, duplicate or reorder them.
The same two functions with and without `volatile`, compiled with g++ 15.2 `-std=c++20 -O2 -S -masm=intel`
on x86-64:

```cpp title="vopt.cpp" showLineNumbers
volatile int reg;
int twice()       { int a = reg; int b = reg; return a + b; }   // two loads required
void two_writes() { reg = 1; reg = 2; }                          // two stores required

int plain_g;
void two_plain()  { plain_g = 1; plain_g = 2; }                  // first store is dead
```

```text
twice:       mov eax, DWORD PTR reg[rip]        two_writes:  mov DWORD PTR reg[rip], 1
             mov edx, DWORD PTR reg[rip]                     mov DWORD PTR reg[rip], 2
             add eax, edx                       two_plain:   mov DWORD PTR plain_g[rip], 2
```

(Instructions trimmed to the memory operations; the register names are an artifact of this compiler.)
The `volatile` version keeps both loads and both stores. For the plain variable the first store disappears.

What the compiler does *not* have to do:

| Not guaranteed | Consequence |
|---|---|
| **Atomicity** | A `volatile long long` store on a 32-bit target may be two instructions. Nothing says a `volatile` access is one machine access of the object's width. The choice of access width is implementation-defined |
| **Ordering against non-volatile accesses** | The compiler may move ordinary loads and stores across a `volatile` access |
| **CPU-level ordering** | No fence or barrier instruction is emitted. The processor and the interconnect may still reorder accesses |
| **Freedom from data races** | Two threads touching one `volatile` object without synchronisation is still a [data race](../11-concurrency-and-memory-model/03-data-races.md): undefined behaviour |

Because of the first three rows, `volatile` is the wrong tool for flags, counters or any shared state in a
program with threads. Use `std::atomic`, which supplies all three. The reasoning behind that
is on [the C++ memory model](../11-concurrency-and-memory-model/01-cpp-memory-model.md).

## Where `volatile` is the right tool

### Memory-mapped I/O

A device register is not memory: reading a status register can clear a flag, and two writes to a command register
are two commands. On bare-metal and embedded targets you map the register block onto a struct of `volatile`
members at a fixed address:

```cpp title="uart.cpp (fragment: the address is device-specific)" showLineNumbers
#include <cstdint>

struct Uart {
    volatile std::uint32_t status;
    volatile std::uint32_t data;
};

inline Uart& uart() {
    return *reinterpret_cast<Uart*>(0x4000'1000);    // an address from the device's data sheet
}

void send(std::uint8_t byte) {
    while ((uart().status & 0x1) == 0) { }           // each iteration re-reads status
    uart().data = byte;
}
```

Notes that the language does not cover but hardware work depends on:

- **Read-only registers**: declare `const volatile std::uint32_t status;`. The object may not be written by
  the program (`const`) but is changed by the device (`volatile`).
- **Width**: the data sheet may require 32-bit accesses. A `volatile std::uint32_t` normally compiles to one, but
  the standard does not promise it. Check the generated assembly for the target.
- **Ordering between registers and with memory**: `volatile` orders only against other `volatile` accesses at
  the compiler level. If the device must see a write to RAM before a doorbell register write, you also need a
  hardware barrier or a compiler fence. For those, use the platform's barrier or an intrinsic
  ([Inline assembly](./06-inline-assembly.md) shows the memory clobber), or
  `std::atomic_thread_fence` where its guarantees fit.
- The `reinterpret_cast` from an integer constant is an implementation-defined conversion, valid on the
  targets this idiom is used for. It does not create an object in the C++ sense. That is the
  idiom's accepted limitation, see [object lifetime](../05-memory-and-object-lifetime/object-lifetime.md).

### Signal handlers

The only object a portable signal handler may write is a `volatile std::sig_atomic_t` (or a lock-free
`std::atomic`, in C++11 and later). `std::sig_atomic_t` (`<csignal>`) is an integer type whose reads and writes are
not torn by the arrival of a signal; `volatile` stops the main code from caching the flag:

```cpp title="sigint.cpp" showLineNumbers
#include <csignal>
#include <cstdio>

volatile std::sig_atomic_t stop = 0;

extern "C" void on_sigint(int) { stop = 1; }

int main() {
    std::signal(SIGINT, on_sigint);
    std::raise(SIGINT);               // deliver the signal to ourselves
    while (!stop) { }                 // re-reads stop each iteration
    std::puts("stopped");
}
```

```text
stopped
```

(g++ 15 and clang++ 21, `-std=c++20`, `-O0` and `-O2`, x86-64 Linux.) This is the one case where `volatile` communicates between two
flows of control, and it works because a signal handler interrupts the *same thread*; no other thread is
involved, so there is no race. The single-thread restriction is the point.

### Other, rarer uses

- `setjmp`/`longjmp`: a local modified after `setjmp` and read after `longjmp` has an indeterminate value
  unless it is `volatile`.
- Preventing a benchmark loop's work from being deleted. This is a pragmatic compiler-dependent trick, and
  libraries such as Google Benchmark provide `DoNotOptimize` for it. `volatile` is not defined for this purpose.

## What `volatile` does to types

`volatile` is a cv-qualifier and follows the same placement rules as `const`: `volatile int* p` is a
pointer to a volatile `int` (the pointee is volatile, the pointer is not), `int* volatile p` is a volatile
pointer, and `volatile int* const p` is a constant pointer to a volatile `int`, the usual register-pointer shape. A
non-`volatile` pointer cannot point at a `volatile` object without a cast, and casting the qualifier away
and accessing the object is undefined behaviour.

A member function can be `volatile`-qualified (`void poke() volatile;`), and a `volatile` object may call
only such functions. Standard-library facilities are not `volatile`-aware: `std::memcpy` does not accept a pointer to `volatile`, and standard algorithms do not promise one access per element. Copy element by element with explicit volatile reads.

## What C++20 deprecated, and what C++23 restored

Code that treats `volatile` like an ordinary variable (`++counter`, `a = b = c`) tends to hide how many
reads and writes happen: does `v += 1` do one volatile read and one volatile write, or an atomic
update? The language never promised the latter. [P1152R4](https://wg21.link/p1152r4) deprecated several
such uses in C++20. The wording, read from the C++20 (N4861) and C++23 (N4950) drafts, [depr.volatile.type]:

| Use | C++20 | C++23 |
|---|---|---|
| `++v`, `v++`, `--v`, `v--` on a volatile arithmetic or pointer lvalue | Deprecated | Still deprecated |
| Compound assignment `v += x`, `v \|= x`, ... used as a statement | Deprecated as first published; the DRs below remove it | **Not deprecated**: P2327R1 for the bitwise operators `\|=`, `&=`, `^=`, CWG 2654 for the rest. Both were adopted as defect reports, so compilers apply them in C++20 mode |
| Simple assignment `v = x` used as a *statement*, or in an unevaluated operand | Not deprecated | Not deprecated |
| Any assignment, simple or compound, whose *result is used*: `a = v = x`, `a = (v += 1)` | Deprecated | Still deprecated ([expr.ass]/5) |
| A function parameter or return type that is volatile-qualified (`void f(volatile int)`) | Deprecated | Still deprecated |
| A structured binding declared `volatile` | Deprecated | Still deprecated |

Pointers to volatile in parameters (`void f(volatile int*)`) are fine. Deprecated here means "compilers may warn"; it does not
mean ill-formed. In practice, g++ 15 (`-Wvolatile`) and clang++ 21 (`-Wdeprecated-volatile`), given this:

```cpp title="vol.cpp" showLineNumbers
volatile int g;
int main() {
    g++;            // deprecated
    g += 1;         // statement: fine (DR against C++20)
    int y = (g += 1);  // result used: deprecated
    int x = g = 1;  // result of a volatile assignment used: deprecated
    g = 2;          // fine
    return x + y;
}
```

warn on the `g++` and the chained assignment under `-std=c++20` and `-std=c++23` alike and say nothing under
`-std=c++17`. They did **not** warn about `g += 1`, even with `-std=c++20`, because P2327R1 and CWG 2654 are defect
reports against C++20 and compilers apply them in C++20 mode too. Using the result of a compound assignment,
`int y = (g += 1);`, is still deprecated: g++ 15 warned on it in both modes, clang++ 21 did not (g++ 15.2 and clang++ 21.1, x86-64 Linux).
Write the two-step form (`g = g + 1`) when you want it obvious that the read and write are separate accesses.

## Pitfalls

| Mistake | Why it is wrong | Fix |
|---|---|---|
| `volatile bool done;` set by another thread | Data race, undefined behaviour. The loop may spin forever or see stale state | `std::atomic<bool>` |
| `volatile int counter; ++counter;` from threads | Load, add and store are separate and unsynchronised | `std::atomic<int>` or a mutex |
| Using `volatile` as a barrier between normal stores | It orders only against other volatile accesses, and emits no fence | `std::atomic` with a memory order, or a hardware barrier |
| `volatile` on ordinary data "to stop the optimiser" | Defeats optimisation without defining behaviour | Fix the real problem, or use a benchmark library's escape hatch |
| Assuming a `volatile` register access is one bus access | Width is implementation-defined | Check the generated code on the target |
| Writing a handler that sets a non-`sig_atomic_t` or non-lock-free-atomic object | Undefined behaviour unless the handler restrictions are met | `volatile std::sig_atomic_t` |

## Key points

- `volatile` makes each access an observable side effect that is performed in order with other volatile accesses. It
  does not add atomicity, CPU ordering or thread safety.
- Right for memory-mapped registers (`const volatile` for read-only ones) and for flags a signal handler sets in the
  same thread (`volatile std::sig_atomic_t`).
- Wrong for communicating between threads: use `std::atomic`.
- C++20 deprecated `++`/`--`, compound assignment, chained assignment, volatile parameters/returns and volatile
  structured bindings. Compound assignment used as a statement is no longer deprecated (P2327R1 for `|=` `&=` `^=`, CWG 2654 for the rest, both DRs against C++20); using the result of any assignment, `++`/`--`, volatile parameters/returns and volatile structured bindings stay deprecated.

## References

- [cppreference: `volatile`, cv type qualifiers](https://en.cppreference.com/w/cpp/language/cv)
- [P1152R4: Deprecating `volatile`](https://wg21.link/p1152r4)
- [C++23 draft N4950, [depr.volatile.type]](https://timsong-cpp.github.io/cppwp/n4950/depr.volatile.type)
- [cppreference: `std::sig_atomic_t`](https://en.cppreference.com/w/cpp/utility/program/sig_atomic_t)
