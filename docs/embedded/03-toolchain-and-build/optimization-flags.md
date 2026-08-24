---
id: optimization-flags
title: Optimization for Size and Speed
sidebar_label: Optimization Flags
sidebar_position: 11
tags: [embedded, toolchain, gcc, optimization, lto, volatile, code-size, stm32]
---

# Optimization for Size and Speed

Raising the optimization level is the one build change that routinely alters what a firmware *does*. Not what it does more quickly — what it does. A delay loop disappears. A register write that was there at `-O0` is gone at `-O2`. Code that worked for two years starts failing, and nothing in the source changed.

None of that is the compiler misbehaving. It is the compiler doing exactly what the C standard permits, on a program that was quietly relying on it not to. The mental model worth carrying: **the compiler optimizes against the abstract machine, and the abstract machine has no peripherals.** It knows about objects, lifetimes and observable behaviour as the standard defines them. It does not know that the address `0x4002_0014` is a GPIO output register, or that a loop that computes nothing is measuring time. If you do not tell it — with `volatile`, with barriers, with a real timer — it is entitled to assume the obvious.

So there are two questions on this page, and they are separate. *Which level should I ship?* is a small question with a boring answer. *What did raising the level reveal about my code?* is the one that costs days.

:::info[Prerequisites]
[Cross-Compilation](./cross-compilation.md) covers the target flags that accompany these on every command line. [Reading the Map File](./elf-map-files-and-size.md) is how you measure the effect of anything here. [C Libraries for Embedded](./c-libraries-for-embedded.md) matters because on a small firmware the library often dominates whatever the optimizer does to your code.
:::

## The levels, measured

Same NUCLEO-F411RE blink as [Reading the Map File](./elf-map-files-and-size.md) — `stm32f411re.ld`, the startup file from [Startup Code: Reset to `main`](./startup-code.md), a `main()` that enables `GPIOA` and toggles `PA5` — built with **Arm GNU Toolchain 14.2.Rel1** (GCC 14.2.1), `-ffunction-sections -fdata-sections -g3`, linked with `--specs=nano.specs --specs=nosys.specs -Wl,--gc-sections`. Only the optimization flag varies.

| Flag | `text` | `data` | `bss` | vs `-O0` | Debuggability | What it is for |
|---|---|---|---|---|---|---|
| `-O0` | 540 | 8 | 1568 | — | **Perfect** — every variable live, every line steppable | Never ship it; use it when a variable reads as `<optimized out>` |
| `-Og` | 460 | 8 | 1568 | −15% | **Very good** — designed to stay steppable | The default *debug* configuration |
| `-O1` | 480 | 8 | 1568 | −11% | Fair | Rarely chosen deliberately |
| `-O2` | 504 | 8 | 1568 | −7% | Poor — inlining and reordering scramble stepping | The default *speed* answer on a part with room |
| `-O3` | 504 | 8 | 1568 | −7% | Poor | Only with a benchmark showing it beats `-O2` |
| `-Os` | **440** | 8 | 1568 | **−19%** | Poor | **The default for firmware.** `-O2` minus the size-increasing passes |
| `-Oz` | **440** | 8 | 1568 | **−19%** | Poor | Size at any speed cost; identical here, wins on larger code |
| `-Os -flto` | **432** | 8 | 1568 | **−20%** | Poor, and worse diagnostics | When `-Os` alone does not fit |

Read the two useful surprises out of that table rather than the headline:

- **`-O3` is not smaller or larger than `-O2` here, and on a bigger firmware it is usually bigger.** `-O3` enables aggressive inlining and loop vectorisation — trades size for speed. On a Cortex-M4 running from flash with wait states, a bigger image can also be a *slower* one, because instruction fetch is the bottleneck. `-O3` is a hypothesis to be tested with a benchmark, never a default.
- **`-O2` is larger than `-O1` here.** Inlining decisions on a tiny program are noisy. Do not draw conclusions about your firmware from a 500-byte one; measure your own.

And the honest caveat this table earns: at 440 bytes of code, **these differences are noise next to the C library**. Adding one `printf` to the same firmware costs 3960 bytes — nine times the entire `-O0`-to-`-Os` spread. Before tuning optimization flags for size, check what you are linking. [Reading the Map File](./elf-map-files-and-size.md) has that measurement.

## Which one to ship

Two configurations, not five:

- **Debug: `-Og -g3`.** `-Og` is the level GCC documents as offering "a reasonable level of optimization while maintaining fast compilation and a good debugging experience". Variables stay live, stepping follows the source, and it is close enough in size and speed that a debug build still behaves like the real thing — which matters when the bug is a timing bug.
- **Release: `-Os -g3`.** Size is the binding constraint on most microcontrollers, and `-Os` is `-O2` with the passes that inflate code disabled. Keep `-g3` — debug information is not loaded onto the device (see the `size -A` breakdown in [Reading the Map File](./elf-map-files-and-size.md)), so it is free in flash and invaluable when you need to decode a fault address from a shipped build.

Then the rule that makes both safe: **test the release build.** A team that develops at `-Og` and ships `-Os` and only ever exercises the debug build has not tested its product. Every optimization-level bug on this page appears at the level you did not run.

## LTO, and when it is worth it

`-flto` defers code generation to link time so the compiler can inline and eliminate across translation units. It saved 8 bytes here, which is nothing; on a real firmware it commonly saves 5–15%, and it removes whole unreferenced functions that `--gc-sections` cannot, because it sees through the call graph rather than through section boundaries.

Three practical conditions:

- **`-flto` must be on the compile *and* link commands.** Same discipline as the target flags in [Cross-Compilation](./cross-compilation.md) — the link step re-runs code generation and needs the flags.
- **Diagnostics get worse.** Warnings and errors surface at link time with less context, and a fault address maps back to source less reliably.
- **It exposes latent undefined behaviour.** Cross-module type mismatches and strict-aliasing violations that were invisible when each file was compiled alone become visible — usually as `-Wodr` and `-Wlto-type-mismatch` warnings, occasionally as changed behaviour. That is LTO finding a real bug, but it finds it late.

Turn it on when you need the space, keep the build reproducible, and re-run the full test suite when you do.

## What actually changes behaviour

Raising the level does not introduce bugs. It stops compensating for them. Four categories, in the order they bite:

### 1. A missing `volatile` on a memory-mapped register

The most common one, and the compiler is entirely within its rights. Given a plain pointer to a register:

```c
static uint32_t *const odr_plain = (uint32_t *)(0x40020000UL + 0x14UL);

void set_then_clear(void)
{
    *odr_plain = (1UL << 5);   /* pulse the pin high */
    *odr_plain = 0UL;          /* then low */
}
```

At `-O0`, both stores happen — two `str` instructions:

```armasm
00000044 <set_then_clear>:
  48:	4b05      	ldr	r3, [pc, #20]
  4a:	2220      	movs	r2, #32
  4c:	601a      	str	r2, [r3, #0]      @ write 0x20
  4e:	4b04      	ldr	r3, [pc, #16]
  50:	2200      	movs	r2, #0
  52:	601a      	str	r2, [r3, #0]      @ write 0
```

At `-O2`, one store:

```armasm
00000010 <set_then_clear>:
  10:	4b01      	ldr	r3, [pc, #4]
  12:	2200      	movs	r2, #0
  14:	615a      	str	r2, [r3, #20]     @ only the write of 0 survives
  16:	4770      	bx	lr
```

The first write is a **dead store** — an ordinary object written twice with no intervening read — so it is deleted. Your pulse never reaches the pin. Mark the pointer `volatile` and both writes are preserved, because `volatile` makes every access observable behaviour the compiler may not elide. That is what the `volatile` in every register definition on this site is for, and the guarantees it does and does not give are a subject of their own in the bare-metal material.

### 2. A delay loop that computes nothing

```c
static void delay_plain(uint32_t n) { while (n--) { } }

void toggle_plain(void)
{
    GPIOA_ODR ^= (1UL << 5);
    delay_plain(400000);
}
```

At `-O0` the call is there — `bl delay_plain` at offset `0x34`. At `-O2`, the entire function is:

```armasm
00000000 <toggle_plain>:
   0:	4a02      	ldr	r2, [pc, #8]
   2:	6953      	ldr	r3, [r2, #20]
   4:	f083 0320 	eor.w	r3, r3, #32
   8:	6153      	str	r3, [r2, #20]
   a:	4770      	bx	lr                @ the delay is simply not here
```

The loop has no side effects and no observable result, so the compiler removed it, then inlined the empty function away. The LED toggles at several megahertz and looks permanently on. Marking the counter `volatile` — as the blink firmware in this section does — forces the loop to survive, and is why that code reads `static void delay(volatile uint32_t n)`.

But a `volatile` spin loop is still a bad clock: its duration depends on the optimization level, the flash wait states, and whether an interrupt fired. Use it for a power-on delay where "roughly this long" is the requirement, and use SysTick or a hardware timer whenever the number matters. [SysTick and Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md) covers the right instrument.

### 3. Undefined behaviour that was benign at `-O0`

Signed overflow, reading through an incompatible pointer type, using an uninitialised variable, a shift past the width of the type. At `-O0` the generated code usually does the naive thing and the program appears to work. At `-O2` the optimizer *assumes UB does not happen* and propagates that assumption — a null check after a dereference can be deleted, because the dereference already proved the pointer non-null. The report is "it works at `-O0` and breaks at `-O2`", and the fix is never the optimization level.

Two flags earn their place in every firmware build for this reason:

```bash
-fno-strict-aliasing    # if you punt types through pointers (protocol parsing does)
-fwrapv                 # signed overflow wraps instead of being UB
```

Neither is free — both disable real optimizations — but both convert a class of silent miscompilation into predictable behaviour, and on firmware that is usually the better trade. Better still, run your platform-independent code under `-fsanitize=undefined` on the host, where the sanitizer can actually report.

### 4. Shared state the compiler cannot see

A variable written by an interrupt handler and read by the main loop is, from the compiler's point of view, written by nobody — it cannot see the handler running. Without `volatile` the read gets hoisted out of the loop and you spin forever on a stale value. `volatile` fixes the elision but says nothing about atomicity or ordering against DMA; those need their own mechanisms, and they belong with the bare-metal concurrency material rather than here.

## Flags that are not optimization levels but change size more

```bash
-ffunction-sections -fdata-sections   # compile: one section per function/object
-Wl,--gc-sections                     # link: delete the unreferenced ones
```

Measured on the `printf` variant of the same firmware: **6112 bytes without, 4400 with — 28% of the image**, which is more than every optimization level on this page combined. This pairing belongs in every embedded build. Its one hazard is that the linker will happily garbage-collect the vector table too; `KEEP` in the linker script is the guard, and [The Linker Script](./the-linker-script.md) explains the failure in full.

:::warning[The firmware works at `-O0`, so the team ships `-O0`]
The reasoning is seductive and it is how a project ends up unable to raise its optimization level ever again.

It starts reasonably. Someone raises `-O0` to `-Os` before a release, something breaks — a delay collapses, a peripheral stops responding, a state machine gets stuck — the release is near, and the level goes back. The build works again. The decision is never revisited, because now every attempt to raise it breaks *several* things at once and nobody can afford to investigate.

What has actually happened is that `-O0` is masking real defects, and the count only grows:

- **Every one of those bugs is still a bug at `-O0`.** Code that depends on a dead store surviving is wrong; it happens to work because the compiler is not looking. The same code will break on a toolchain upgrade, on a different vendor's compiler, or when someone adds `-flto`. [Choosing a Toolchain](./toolchains-and-compilers.md) covers why a toolchain upgrade you did not plan is a matter of when.
- **You are paying for it continuously.** `-O0` on this trivial blink is 19% larger than `-Os`; on real firmware doing arithmetic the gap is much wider, in both flash and cycles. That is flash you cannot use and battery life you do not get back.
- **The debt compounds silently.** Every month at `-O0` adds more code written against the wrong mental model, and the eventual migration gets strictly harder.

Getting out, when you are already there:

1. **Raise the level on one file at a time**, not the project. Per-file optimization via your build system localises the breakage, and the file that breaks *is* the file with the defect.
2. **When something breaks, find the defect — do not lower the level back.** Diff the disassembly between the two levels for the function involved (`arm-none-eabi-objdump -d`, as in the listings above). The instruction that disappeared names the bug.
3. **Grep for the two usual suspects first.** Every memory-mapped register access that is not through a `volatile` pointer, and every variable shared between an interrupt handler and `main` that is not `volatile`. Those two account for most of it.
4. **Then hold the line.** CI builds the release configuration, and the tests run against *that* binary, not the debug one.

The general principle underneath: **an optimization level is not a correctness setting.** If changing it changes what your program does, the program was already wrong and you have just been told where.
:::

## See also

- [Reading the Map File](./elf-map-files-and-size.md) — how every number in the table above was measured, and why `printf` dwarfs all of them.
- [Startup Code: Reset to `main`](./startup-code.md) — `-ftree-loop-distribute-patterns`, an optimization that turns the `.data` copy loop into a `memcpy` call that is not usable yet.
- [The Linker Script](./the-linker-script.md) — `KEEP`, and why `--gc-sections` deletes vector tables that are not protected.
- [Choosing a Toolchain](./toolchains-and-compilers.md) — why the compiler version is part of the answer, and why pinning it is mandatory.
- [SysTick and Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md) — the timer to use instead of a spin loop.

## References

- Free Software Foundation — [**GCC manual, "Options That Control Optimization"**](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html). The normative list of what each level enables: `-O0` through `-O3`, `-Os` as "optimize for size… enables all `-O2` optimizations except those that often increase code size", `-Oz` for size at the expense of speed, `-Og` as the level intended for "a good debugging experience", plus `-flto`, `-fno-strict-aliasing`, `-fwrapv` and `-ftree-loop-distribute-patterns`.
- Free Software Foundation — [**GCC manual, "Options for Code Generation"**](https://gcc.gnu.org/onlinedocs/gcc/Code-Gen-Options.html) and [**"Program Instrumentation Options"**](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html). `-ffunction-sections` and `-fdata-sections` behind the 28% measurement, and `-fsanitize=undefined` for host-side testing of platform-independent code.
- Free Software Foundation — [**GCC manual, "When is a Volatile Object Accessed?"**](https://gcc.gnu.org/onlinedocs/gcc/Volatiles.html). GCC's own statement of what it guarantees for `volatile` accesses and what it explicitly does not — the normative basis for the two disassembly listings above.
- Arm — [**Arm GNU Toolchain**](https://developer.arm.com/Tools%20and%20Software/GNU%20Toolchain), release **14.2.Rel1** (GCC 14.2.1). Every size figure and disassembly listing on this page was produced with it; a different release will give different numbers, which is itself the argument for pinning.
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). §3.4 for the flash `ART` accelerator and prefetch, and the wait-state table behind the claim that a larger image can be a slower one; §8.4.6 for `GPIOx_ODR` at offset `0x14`, the register in both listings.
