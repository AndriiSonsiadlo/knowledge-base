---
id: the-kernel-c-dialect
title: "The Kernel Is Not C You Know"
sidebar_label: "The kernel C dialect"
sidebar_position: 6
tags: [linux, kernel]
prerequisites:
  - linux/kernel-architecture-and-idioms/the-source-tree-map
draft: false
---

# The Kernel Is Not C You Know

Freestanding C with no libc, no floating point, a tiny stack, GCC extensions in daily use, and the annotations sparse checks.

Kernel code is C. It is compiled by the same GCC or Clang that builds ordinary programs, and its syntax is
unmistakably C. And yet the first unfamiliar file you open reads *wrong* — functions that look like they
should exist don't, macros expand into things that look nothing like C, and every third declaration carries
a word you've never seen attached to a type before. None of that is an accident or a house quirk to shrug
off. The kernel is *freestanding* C — a C dialect that runs with no operating system underneath it, because
it *is* the operating system — with a deliberate house style and a small, closed set of annotations layered
on top. Once the five or six unfamiliar constructs are named, the strangeness disappears; it turns out to be
a small vocabulary, reused constantly.

## Freestanding, not hosted

A *hosted* C implementation — the one taught in every C course — assumes an operating system underneath it:
a C standard library to link against, a `main()` the OS calls to start the program, and a heap the OS manages
for `malloc`. A *freestanding* implementation assumes none of that, because there is nothing underneath it to
provide it. The kernel is the canonical freestanding C program, and it supplies its own version of
everything a hosted program takes for granted:

- No libc. There is no `printf` — there is `printk`, which formats into a ring buffer instead of a file
  descriptor and tags each line with a priority. There is no `malloc`/`free` — there is `kmalloc`/`kfree`
  (and `vmalloc`, and the per-CPU and slab allocators besides), each with different guarantees about
  physical contiguity and the context it's safe to call from.
- No `main()`. Execution doesn't begin at a function the compiler and runtime conspire to call for you —
  it begins at an architecture-specific boot entry point, works through early setup with almost nothing
  initialized yet, and eventually reaches `start_kernel()` in `init/main.c`, which is as close to "the
  kernel's `main`" as anything gets.
- No standard headers. `<stdio.h>`, `<stdlib.h>`, and friends don't exist in kernel context; the kernel's own
  `include/linux/` and `lib/` supply the equivalents it actually needs — `memcpy`, `strlen`, `snprintf`, and
  so on are real functions with real implementations in `lib/string.c`, not calls into a C library the
  kernel doesn't have.

The pattern to notice is not "the kernel renamed some functions" — it's that there is no runtime beneath
kernel code to reach for. Every convenience a hosted program gets for free, the kernel had to build for
itself, and each one has a kernel-specific name precisely so nobody mistakes it for the libc version with
libc's assumptions attached.

## No floating point

This one surprises people early enough that it's worth stating before anything else: kernel code, by
default, does not use floating-point or SIMD registers, and the reason is not a stylistic preference — it's
that the kernel does not save and restore FPU/SSE/AVX register state across a context switch the way it
saves general-purpose registers. Doing so on every switch would cost cycles that the overwhelming majority
of kernel code, which never touches a `float`, shouldn't have to pay. So the kernel simply doesn't; ordinary
kernel code that used `float` or `double` would be silently corrupting whatever user-space task last used
those registers, or reading garbage left behind by one.

The small set of places that genuinely need vector instructions — some cryptography, some RAID
implementations — bracket that use explicitly with `kernel_fpu_begin()` and `kernel_fpu_end()`, which save
the current FPU state, make it safe to use SIMD for the duration, and restore it on the way out. Outside
that bracket, floating point in kernel context is not merely unidiomatic, it's a bug.

## The stack is 16 KB (and used to be 8), and that is all

A user-space thread's stack grows on demand, typically up to several megabytes, and a stack overflow is
something most programs never think about. A kernel stack is a small, fixed-size allocation carved out once
per task, and there is nothing behind it that grows — overrun it and you corrupt whatever memory happens to
sit past the end.

The size is architecture- and configuration-dependent. On x86-64 at v6.18, with a stock (non-`KASAN`)
configuration, `THREAD_SIZE` works out to one page shifted left by `THREAD_SIZE_ORDER`, which is `2` — four
4&nbsp;KB pages, i.e. **16&nbsp;KB** — and `CONFIG_KASAN` adds one more order of shift stack-instrumentation
overhead needs, pushing it to 32&nbsp;KB. The historical "8 or 16&nbsp;KB" framing you'll see in older
writing about the kernel reflects other architectures and older x86 configurations; on current x86-64 the
floor is 16&nbsp;KB. Either way, the number is small enough that the rules it implies are absolute, not
stylistic advice:

- No large local arrays or structs on the stack. A `char buf[4096]` local variable is a quarter of the
  entire budget.
- No deep or unbounded recursion. A recursive algorithm with no hard depth bound is a latent stack overflow
  waiting for sufficiently adversarial input.
- `CONFIG_FRAME_WARN` catches what review misses, at build time: it warns when any single function's stack
  frame exceeds a configured byte threshold, which is exactly the failure mode — one function silently
  eating an unreasonable share of a fixed 16&nbsp;KB budget — that's easy to introduce by accident and hard
  to notice by reading.

## GCC extensions in daily use

The kernel's minimum-supported compilers accept a set of GNU C extensions beyond strict ISO C, and the
kernel leans on several of them constantly enough that reading kernel code fluently means recognising them
on sight.

**Statement expressions** — `({ ... })` — let a block of statements evaluate to a value, used everywhere a
macro needs to do more than one thing and still act like an expression:

```c
#define max(a, b) ({ \
	typeof(a) _a = (a); \
	typeof(b) _b = (b); \
	_a > _b ? _a : _b; })
```

Simplified — the real `max()`/`min()` in `include/linux/minmax.h` wrap this in the more elaborate
`__careful_cmp` machinery, which also catches signedness mismatches between `a` and `b` at build time.

**`typeof`** recovers a variable's type without naming it, which is what makes the macro above type-generic
and is the same trick `container_of` (later on this page's sibling) depends on.

**`__attribute__((packed))`, `__attribute__((aligned(N)))`, `__attribute__((always_inline))`** control layout
and inlining precisely where the compiler's defaults would be wrong — `packed` for a struct that mirrors an
on-the-wire or on-disk format with no compiler-inserted padding, `aligned` for DMA buffers and cache-line
separation, `always_inline` where a function must not become a real call (some lock-acquire fast paths).

**Designated initialisers** are used pervasively for the kernel's ubiquitous "ops struct" pattern — a struct
of function pointers that a subsystem fills in to plug an implementation into a generic framework:

```c
static const struct file_operations my_fops = {
	.owner   = THIS_MODULE,
	.open    = my_open,
	.release = my_release,
	.read    = my_read,
};
```

Only the fields that matter are named; the rest are zero-initialized, which for a function-pointer field
means "this operation isn't supported" — the framework checks for `NULL` before calling it.

**`__builtin_*`** functions — `__builtin_expect` (branch-prediction hints, usually seen wrapped as `likely()`
/`unlikely()`), `__builtin_offsetof` (which `offsetof()` itself expands to), `__builtin_unreachable`, and
others — are the compiler-intrinsic layer the kernel's own macros are frequently built on top of.

## The annotations

A handful of `__`-prefixed tokens attached to types and declarations aren't decoration — some are compiler
attributes with real enforcement, some are markers `sparse` (below) understands and the compiler otherwise
ignores.

| Annotation | Meaning | Enforced by |
|---|---|---|
| `__init` | Placed in a discardable code section; the memory is freed after boot completes | Compiler (section placement) — freeing after boot is the boot code's doing |
| `__exit` | Placed in a code section that's discarded entirely in a non-modular build (a function that only matters when unloading, which can't happen if the code was never a module) | Compiler (section placement) |
| `__initdata` | Same discardable-section treatment as `__init`, for data instead of code | Compiler (section placement) |
| `__user` | Pointer into user-space address space; must never be dereferenced directly in kernel context | `sparse` only — the compiler accepts a bare dereference silently |
| `__percpu` | Pointer to a per-CPU variable, not a plain address — must go through the per-CPU accessor API | `sparse` only |
| `__iomem` | Pointer to memory-mapped I/O; must go through `readl`/`writel`-style accessors, not ordinary loads/stores | `sparse` only |
| `__rcu` | Pointer protected by RCU; must be read and updated through the RCU accessor API | `sparse` only |
| `__must_check` | Caller must inspect the return value | Compiler (`-Wunused-result`, a real warning) |

The split matters: `__init`/`__exit`/`__initdata` and `__must_check` change what the compiler actually does.
`__user`/`__percpu`/`__iomem`/`__rcu` change nothing about the compiled output by themselves — the compiler
treats the annotated pointer as an ordinary pointer of the same underlying type. They exist so a separate
tool can catch the class of bug where kernel code treats a special address space as if it were an ordinary
one.

## sparse

`sparse` is that separate tool: a static checker built for exactly this job, invoked with `make C=1` (or
`C=2` to check even files that didn't need recompiling). It understands the address-space annotations above
as real types with real rules — a `__user` pointer assigned directly to a plain pointer, or dereferenced
without going through `copy_from_user()`/`copy_to_user()`, is a `sparse` error even though it's a perfectly
legal, silently-accepted assignment as far as the C compiler is concerned. Without `sparse`, `__user` is a
comment a reviewer might notice; with it, `__user` is enforced.

## Optimisation barriers you will meet

Two more names appear constantly in code that touches memory shared between CPUs or between a CPU and an
interrupt handler: `READ_ONCE()`/`WRITE_ONCE()`, which force a single, non-elided, non-reordered-by-the-
compiler memory access instead of one the compiler is free to cache in a register or split into pieces; and
`barrier()`, a compiler-only ordering fence with no CPU instruction behind it. Both matter a great deal and
neither is explained here — memory ordering is a large enough topic that it gets its own treatment in
folder&nbsp;09. For now, recognise the names and know they exist for correctness under concurrency, not
performance.

<KernelFacts
  structure={[["__init / __exit / __initdata", "include/linux/init.h"], ["__user / __percpu / __iomem / __rcu", "include/linux/compiler_types.h"]]}
  path="annotated source → compiler sections and attributes → sparse (make C=1) checks the address-space annotations → linker discards __init sections after boot"
  observe='dmesg | grep -i "freeing unused kernel"'
  trap="`__init` is not documentation. The function is placed in a section that is unmapped and freed once boot completes, so calling one later — from a code path that survives past boot, holding a stale function pointer — dereferences memory that no longer exists." />

## References

- [Linux kernel coding style](https://docs.kernel.org/process/coding-style.html) — the house style, which
  explains as much of the kernel's strangeness as the language extensions do.
- [Sparse: a semantic parser for C](https://docs.kernel.org/dev-tools/sparse.html) — what the address-space
  annotations buy you, and how to run the checker over a subtree.
- [GCC: C extensions](https://gcc.gnu.org/onlinedocs/gcc/C-Extensions.html) — the primary reference for the
  compiler extensions the kernel relies on daily: statement expressions, `typeof`, and the attributes.
