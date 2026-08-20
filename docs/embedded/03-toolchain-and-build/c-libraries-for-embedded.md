---
id: c-libraries-for-embedded
title: "C Libraries: newlib, newlib-nano, picolibc"
sidebar_label: C Libraries for Embedded
sidebar_position: 3
tags: [embedded, toolchain, newlib, picolibc, libc, printf, stm32]
---

# C Libraries: newlib, newlib-nano, picolibc

The C standard library is written as though a process exists. `printf` writes to a file descriptor. `malloc` asks the kernel for more address space. `exit` tells a parent that a child finished. `fopen` needs a filesystem, `time` needs a clock somebody set, `errno` needs somewhere thread-local to live. On a Cortex-M4 with no OS, not one of those things is true — and yet `#include <stdio.h>` compiles fine and `printf` links, because the library was built with the bottom of every one of those paths left as a hole for you to fill.

That is the mental model: an embedded libc is a **library with the floor missing**. Everything above the syscall boundary — the format-string parser, the string functions, the maths routines — is ordinary portable C and works unchanged. Everything below it is a small set of functions the library calls and does not define, and if you do not supply them the link fails or, worse, succeeds against stubs that silently return failure. Choosing "which libc" is mostly choosing *how much* is above that boundary and how expensive it is.

:::info[Prerequisites]
[Cross-Compilation](./cross-compilation.md) explains why the `none` in `arm-none-eabi` is what creates this hole in the first place, and how multilib selects which pre-built copy of the library gets linked.
:::

## The three choices

| | **newlib** | **newlib-nano** | **picolibc** |
|---|---|---|---|
| Origin | Cygnus/Red Hat, maintained at sourceware.org | Arm's size-optimised configuration of newlib | Newlib plus AVR-libc, maintained by Keith Packard |
| How you select it | Default in Arm GNU Toolchain | `--specs=nano.specs` | `--specs=picolibc.specs`, or the default in the LLVM Embedded Toolchain for Arm |
| `printf` implementation | Full C99 `vfprintf`: floats, `%n$` positional args, wide chars, locales | Reduced `vfprintf`; float support **excluded by default** | `tinystdio` by default — a compact reimplementation; the full newlib stdio is a build option |
| `printf("%f")` works out of the box | Yes | **No** — needs `-u _printf_float` | Yes, if built with float support (the usual distribution default) |
| `malloc` | Full dlmalloc-derived allocator | `nano-malloc`, a simpler and much smaller allocator | Same family; smaller by default |
| Reentrancy model | `struct _reent` — a large per-thread state block | Reduced `struct _reent` | Thread-local storage (`__thread`), no `_reent` struct |
| Locale support | Full | Reduced | Minimal |
| Licence | Mixed BSD-style / GPL-compatible; some files LGPL | Same as newlib | BSD 3-clause throughout, deliberately |
| Relative flash cost of a `printf`-using "hello world" | Largest — tens of KB | Roughly a quarter to a third of full newlib | Smallest — typically a small fraction of newlib-nano's stdio |
| When to pick it | You genuinely need full C99 stdio and have the flash | Default for GCC bare-metal work | New projects, tight flash, or you are already on LLVM |

**Read the last-but-one row as an ordering, not as numbers.** Published footprint comparisons exist — picolibc's documentation carries them — but the absolute figures depend on the compiler version, the optimisation level, which format specifiers the linker can prove are unused, and whether `--gc-sections` is on. The ordering (newlib > newlib-nano > picolibc-with-tinystdio) is stable across every configuration; the multipliers are not. Measure your own build rather than quoting anyone's table:

```bash
arm-none-eabi-size -A build/firmware.elf                       # per-section totals
arm-none-eabi-nm --size-sort -S -C build/firmware.elf | tail -20  # the 20 biggest symbols
```

If `_vfprintf_r` or `__ssputs_r` is near the top of that second list, you have found where your flash went.

## `printf` is the largest single thing most firmwares link

This deserves its own section because the size is so far out of proportion to what the call looks like.

A conforming `printf` contains a complete interpreter for a small language. It has to parse a format string at runtime, handle every conversion specifier, implement integer-to-decimal conversion in several bases and widths, and — the expensive part — implement correctly-rounded binary-to-decimal floating-point conversion, which drags in `libm`-adjacent code and multi-precision arithmetic. Full newlib's float-capable `vfprintf` is routinely tens of kilobytes on its own. On a part with 512 KB of flash that is survivable; on a 32 KB part it is the entire budget.

The practical hierarchy, cheapest first:

1. **Do not format on the device.** Send binary or a fixed-layout record over the link and format it on the host. This is free and is usually the right answer for telemetry.
2. **Use a tiny purpose-built formatter.** A few hundred bytes of hand-written integer-to-string is enough for most logging.
3. **Use `tinystdio` (picolibc) or newlib-nano without float.** Adequate for real diagnostics at a fraction of the cost.
4. **Scale integers instead of using floats.** `printf("%d.%03d", mv / 1000, mv % 1000)` prints 3.3 V from millivolts with no floating-point formatter linked at all. This one trick removes the single biggest chunk.
5. **Link the full float formatter.** Only when you have measured that you can afford it.

## The stubs you must supply

Newlib calls a small set of underscore-prefixed functions at the syscall boundary. They are documented in the newlib manual as the porting layer, and on a bare-metal target you supply them yourself. The ones that matter in practice:

| Stub | Called by | What you must do on bare metal |
|---|---|---|
| `_write(fd, buf, len)` | `printf`, `puts`, `fwrite` | The one that makes output appear. Push the bytes at a UART or the ITM/SWO trace port. Return `len`. |
| `_read(fd, buf, len)` | `scanf`, `fgets` | Read from the UART, or return `0` for EOF if you have no input. |
| `_sbrk(incr)` | `malloc` | Hand out memory between the linker's `end` symbol and the stack. **This is the one that must be correct**, because a naive version happily grows the heap into the stack. |
| `_close`, `_fstat`, `_isatty`, `_lseek` | stdio internals | Minimal answers: `_isatty` returns `1`, `_fstat` reports a character device, `_lseek` returns `0`, `_close` returns `-1`. |
| `_exit(status)` | `exit`, and `main` returning | There is nowhere to exit *to*. Disable interrupts and spin, or trigger a reset. Never return. |
| `_kill`, `_getpid` | `abort`, `raise` | Stubs; `_getpid` returns `1`, `_kill` sets `errno = EINVAL` and returns `-1`. |

Three ways to satisfy them, in increasing order of how much you mean it:

- **`--specs=nosys.specs`** links `libnosys`, whose stubs all fail politely — they set `errno` and return `-1`. This gets you a clean link immediately. It also means `printf` produces no output and `malloc` fails, which surprises people who expected "nosys" to mean "no problem".
- **`--specs=rdimon.specs`** links the semihosting implementation, which routes I/O through the debugger over a `BKPT` instruction. Genuinely useful during bring-up: `printf` appears in your OpenOCD console with no UART configured. It is also *extremely* slow, halts the core on every call, and **hangs the firmware if no debugger is attached** — never ship it.
- **Write your own.** The normal end state. A `_write` that blocks on the UART transmit-empty flag, a `_sbrk` that respects the linker symbols, and failing stubs for the rest.

A correct `_sbrk` is short, and the check in it is the entire point:

```c
#include <errno.h>
#include <stddef.h>

/* Both provided by the linker script (see The Linker Script):
   `end` is the first free byte after .bss; `_estack` is the top of RAM. */
extern char end;
extern char _estack;

#define STACK_RESERVE 1024u   /* bytes the heap must never eat into */

void *_sbrk(ptrdiff_t incr)
{
    static char *brk = NULL;
    if (brk == NULL) {
        brk = &end;
    }

    char *const ceiling = &_estack - STACK_RESERVE;
    if (incr > 0 && (brk + incr > ceiling)) {
        errno = ENOMEM;
        return (void *)-1;          /* the sentinel malloc checks for */
    }

    char *prev = brk;
    brk += incr;
    return prev;
}
```

The `(void *)-1` return is not optional decoration — it is the sentinel `malloc` tests. A `_sbrk` that returns a plain `NULL` on failure, or that omits the ceiling check entirely, produces a heap that grows silently into the stack and a crash somewhere else entirely, minutes later.

Picolibc's porting layer is smaller and differently shaped: with `tinystdio` you register console hooks rather than implementing `_write`, and there is no `struct _reent` at all because per-thread state uses ordinary thread-local storage. That last difference is why picolibc integrates more cleanly with an RTOS — newlib's reentrancy model requires the RTOS to swap a `_reent` pointer on every context switch, and every RTOS integration guide has a section about getting that wrong.

:::warning[`printf("%f")` prints nothing, and the build gave you no warning]
This is the single most common newlib-nano surprise, and it wastes an afternoon roughly once per engineer.

You add `--specs=nano.specs` to shrink the binary — a completely reasonable thing to do. The build succeeds and gets 15 KB smaller. Later, someone adds a diagnostic:

```c
printf("vbat = %f V\r\n", volts);
```

and the output is `vbat =  V`, or `vbat = f V`, or a garbage integer. No compiler warning, no linker error, no runtime fault. The format string is valid C and the compiler's `-Wformat` check passes, because the *declaration* of `printf` is fine — it is the *implementation* that was configured without the floating-point conversion path.

Newlib-nano excludes float formatting by default and expects you to ask for it explicitly at link time:

```bash
-specs=nano.specs -u _printf_float      # and -u _scanf_float if you use scanf("%f")
```

`-u SYMBOL` forces the linker to treat that symbol as undefined, which pulls in the object that defines it. Adding it costs roughly 6–10 KB of flash — which is precisely the size you were trying to save by using nano in the first place.

Two related traps in the same family:

- **`%lld` and `%zu`.** Some reduced stdio configurations omit the long-long and `size_t` conversions too. The symptom is identical: silently wrong output.
- **Fixing it by switching back to full newlib.** It works, and it undoes the size saving completely. Before doing that, check whether the call actually needs a float at all — scaled-integer formatting (`"%d.%03d"`) is free and covers most sensor and voltage logging.

The habit that prevents all of it: after any change to the libc selection, run one deliberate smoke test that prints a float, a `long long` and a `size_t`, and *look at the output*. Thirty seconds, once, versus an afternoon of suspecting your ADC driver.
:::

## See also

- [Cross-Compilation](./cross-compilation.md) — why the library has a hole in it, and which multilib copy gets linked.
- [Choosing a Toolchain](./toolchains-and-compilers.md) — the toolchain half of the choice; IAR's DLIB and Arm's microlib are the commercial equivalents.
- [The Linker Script](./the-linker-script.md) — where `end`, the heap ceiling and the stack region that `_sbrk` has to respect are defined.
- [Memory Sections and VMA vs LMA](./memory-sections.md) — where the heap sits relative to `.bss` and the stack, and why the two grow towards each other.
- [Startup Code: Reset to `main`](./startup-code.md) — `__libc_init_array`, and what happens when `main` returns into `exit`.

## References

- Red Hat / sourceware.org — [**The Red Hat newlib C Library**](https://sourceware.org/newlib/libc.html). The reference manual for newlib itself. The chapter on "Reentrancy" defines `struct _reent` and the `_r` function family; the "Syscalls" section is the normative list of the underscore-prefixed stubs the library expects a bare-metal port to supply, with the required return values for each.
- picolibc — [**picolibc README and documentation**](https://github.com/picolibc/picolibc). Explains the newlib + AVR-libc heritage, the `tinystdio` versus full-stdio choice and the flags that select it, the TLS-based reentrancy model, and the BSD relicensing rationale. `doc/` also carries the size comparisons that the ordering in the table above reflects — read them as a shape, and re-measure on your own build.
- Arm — [**Arm GNU Toolchain downloads and release notes**](https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads). Documents that the distribution ships both newlib and newlib-nano, and that `--specs=nano.specs` is the switch between them. Release notes are where changes to the default libc configuration are announced.
- Free Software Foundation — [**GNU `ld` manual, "Command-line Options"**](https://sourceware.org/binutils/docs/ld/Options.html). The definition of `-u SYMBOL`: "Force SYMBOL to be entered in the output file as an undefined symbol… this may, for example, trigger linking of additional modules from standard libraries" — the exact mechanism `-u _printf_float` relies on.
- Arm — [**Arm Compiler for Embedded, microlib user guide**](https://developer.arm.com/documentation/100073/latest/). The commercial point of comparison, and useful for its explicit list of the ways a size-optimised C library stops conforming to the standard — the same trade newlib-nano and `tinystdio` make less loudly.
