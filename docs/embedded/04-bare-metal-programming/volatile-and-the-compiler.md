---
id: volatile-and-the-compiler
title: What volatile Does and Does Not Do
sidebar_label: volatile and the Compiler
sidebar_position: 3
tags: [embedded, bare-metal, volatile, compiler, barriers, atomicity, dma, cortex-m]
---

# What `volatile` Does and Does Not Do

`volatile` has a reputation for being either a magic word that makes hardware access work or a deprecated relic that nobody should use. Both readings come from the same place: people learn what it does by observing that adding it fixed a bug, and never learn the boundary of the guarantee. The boundary is narrow, it is written down precisely in the C standard, and knowing exactly where it stops is what separates code that works from code that works on your desk.

The one-sentence model: **`volatile` is a promise the compiler makes about the accesses it emits, and nothing more.** It says every read and write you wrote will appear in the generated code, in the order you wrote them relative to other volatile accesses. It says nothing about how many instructions each one takes, whether anything can happen in between, or what the memory system, the bus matrix, or a DMA engine does afterwards.

:::info[Prerequisites]
[Register-Level Programming](./register-level-programming.md) establishes the memory-mapped I/O model and why every register pointer carries the qualifier. [The Register Model](../02-processor-architecture/cortex-m-register-model.md) covers the instruction set the assembly below is written in. [Optimization for Size and Speed](../03-toolchain-and-build/optimization-flags.md) covers the optimisation levels that make the difference visible.
:::

## What the standard actually says

ISO C is unusually direct here. C17 §6.7.3¶8: an object with volatile-qualified type "may be modified in ways unknown to the implementation or have other unknown side effects. Therefore any expression referring to such an object shall be evaluated strictly according to the rules of the abstract machine". And §5.1.2.3 lists accessing a volatile object among the *side effects* that define observable behaviour, alongside modifying a file and calling an I/O function.

That yields three guarantees and no more:

1. **No elision.** A read you wrote is a read the processor performs, even if the value is discarded. A write you wrote reaches memory, even if you immediately overwrite it.
2. **No invention or duplication.** The compiler will not add an access you did not write, nor turn one read into two.
3. **Order preserved among volatile accesses.** Two volatile accesses appear in the generated code in the order the source has them.

Everything people assume beyond this — atomicity, ordering against non-volatile accesses, visibility to another bus master, memory barriers, thread safety — is absent. §5.1.2.3¶6 is explicit that "what constitutes an access to an object that has volatile-qualified type is implementation-defined", which is why the compiler's own documentation matters as much as the standard.

## Seeing the difference

The canonical case is polling a hardware flag. `RCC_CR` bit 1 is `HSIRDY`, set by the hardware when the internal oscillator has stabilised (RM0383 Rev 4 §6.3.1) — nothing in your program sets it.

<Tabs>
<TabItem value="nonvolatile" label="Without volatile" default>

```c
uint32_t *const rcc_cr = (uint32_t *)0x40023800u;

void wait_hsi_ready(void)
{
    while ((*rcc_cr & 2u) == 0u) {
    }
}
```

```armasm
wait_hsi_ready:
        ldr     r3, =0x40023800
        ldr     r3, [r3]          @ ONE load, hoisted out of the loop
        tst     r3, #2
        bne     .Lreturn
.Lspin:
        b       .Lspin            @ nothing left to re-read: hangs forever
.Lreturn:
        bx      lr
```

The compiler reasons, correctly under the abstract machine, that nothing in the loop body modifies `*rcc_cr`, so the value cannot change. It loads once. If the bit was clear at that instant the loop can never terminate, and the compiler emits exactly that: an unconditional branch to itself.

This is not a compiler bug. Under the rules the compiler is given, the program says "loop until a value that never changes becomes non-zero".

</TabItem>
<TabItem value="volatile" label="With volatile">

```c
volatile uint32_t *const rcc_cr = (volatile uint32_t *)0x40023800u;

void wait_hsi_ready(void)
{
    while ((*rcc_cr & 2u) == 0u) {
    }
}
```

```armasm
wait_hsi_ready:
        ldr     r2, =0x40023800
.Lloop:
        ldr     r3, [r2]          @ reloaded on every iteration
        tst     r3, #2
        beq     .Lloop
        bx      lr
```

The load is inside the loop, where you wrote it. The qualifier moved one instruction, and that one instruction is the difference between working firmware and a hang.

</TabItem>
</Tabs>

*Both listings: GCC 14.2.Rel1, `-O2 -mcpu=cortex-m4 -mthumb`. Labels renamed and the literal pool folded into the `ldr =` pseudo-instruction for readability; the instruction sequence is unmodified.*

Note what happens at `-O0`: both versions produce the reloading form, because `-O0` keeps nothing in registers across statements. That is precisely why this class of bug is invisible in a debug build and appears when you first build a release image — and why "it works at `-O0`, it must be an optimiser bug" is almost always the wrong conclusion. [Optimization for Size and Speed](../03-toolchain-and-build/optimization-flags.md) has more of that family.

## The other side: `volatile` also costs you

The same guarantee that forces the reload forbids the compiler from *ever* keeping the value in a register. Read a volatile register eight times in a function and you get eight loads, no common-subexpression elimination, no hoisting.

```c
/* Eight bus reads. */
for (int i = 0; i < 8; i++) {
    if (GPIOA->IDR & (1u << i)) { count++; }
}

/* One bus read, then eight tests on a register. */
uint32_t idr = GPIOA->IDR;    /* one volatile access, snapshotted */
for (int i = 0; i < 8; i++) {
    if (idr & (1u << i)) { count++; }
}
```

The second form is faster and — more importantly — **coherent**: all eight tests see the same instant. The first form reads the pin state eight times and can observe a pin changing halfway through, which turns "read the switch bank" into a source of impossible states. Snapshotting a volatile register into a local is the correct instinct whenever you need several fields of one register to be consistent with each other.

## What it does not give you: atomicity

This is the misconception that produces real bugs rather than hangs.

```c
volatile uint32_t flags;    /* shared between main and an ISR */

flags |= FLAG_A;            /* looks like one operation */
```

```armasm
        ldr     r3, [r2]        @ load   ← an interrupt here...
        orr     r3, r3, #1      @ modify
        str     r3, [r2]        @ store  ← ...loses whatever the ISR wrote
```

Three instructions, and the qualifier did not merge them. If an interrupt fires between the load and the store, and the handler sets `FLAG_B`, the store writes back a value computed before `FLAG_B` existed. `FLAG_B` is gone. Nothing reports it. The bug is rate-dependent — it needs the interrupt to land in a two-instruction window — so it appears under load, in the field, and not in your tests.

`volatile` did its job perfectly and the code is still wrong. Three ways out, cheapest first:

- **Use hardware that is atomic by construction.** For GPIO output this is exactly what `BSRR` is for: a single `str` that sets and clears named bits, with no read. [A GPIO Driver from Scratch](./gpio-driver-from-scratch.md) covers it. Many peripherals offer a set/clear register pair for the same reason.
- **Use the exclusive monitor.** `LDREX`/`STREX`, or the GCC `__atomic_*` builtins that compile to them, give you a read-modify-write that detects interference and retries.
- **Disable interrupts around the sequence.** Correct and blunt; it adds latency to every other interrupt in the system. The nesting-safe way to do it, and how to choose between these three, is the subject of the critical-sections page later in this folder.

There is one narrow atomicity guarantee worth knowing: on Armv7-M, a naturally aligned single load or store of a byte, half-word or word is a single-copy atomic access. So `flags = 0;` and `x = flags;` on an aligned `uint32_t` cannot tear. That is a property of the architecture, not of `volatile`, and it stops at read-modify-write and at anything wider than a word.

## What it does not give you: ordering against the world

The compiler emits volatile accesses in order. That is not the same as those accesses *becoming visible* in order.

Two separate reorderings can happen after the compiler is done:

- **Non-volatile accesses move freely across volatile ones.** Filling a buffer in normal RAM and then writing a "go" bit to a DMA controller: the compiler is entirely within its rights to sink some of the buffer stores past the volatile register write, because nothing tells it those stores are related to the register.
- **The memory system reorders.** Writes to Normal memory (your SRAM) can complete out of order relative to writes to Device memory (the peripheral). Write buffers, the bus matrix, and the AHB/APB bridge all sit in between.

The tools, in increasing strength:

```c
/* 1. Compiler barrier only. Nothing crosses this line in the generated code.
      Costs zero instructions. Does nothing about the memory system. */
__asm volatile ("" ::: "memory");

/* 2. Data Memory Barrier. Every explicit memory access before it is observed
      by the system before any after it. This is the one you want before
      handing a buffer to a DMA engine or another bus master. */
__DMB();

/* 3. Data Synchronization Barrier. Stronger: execution does not continue
      until all preceding memory accesses have COMPLETED, not merely ordered. */
__DSB();

/* 4. Instruction Synchronization Barrier. Flushes the pipeline so instructions
      after it are refetched. Needed after changing something that affects how
      instructions are fetched or decoded -- VTOR, MPU config, enabling the FPU. */
__ISB();
```

`__DMB`, `__DSB` and `__ISB` are CMSIS-Core intrinsic functions and compile to the single Arm instruction of the same name — see [CMSIS and Vendor HALs](./cmsis-and-vendor-hals.md). Without CMSIS they are `__asm volatile ("dmb" ::: "memory")` and so on; note the `"memory"` clobber, which makes each of them a compiler barrier as well.

The rules of thumb that cover most real code:

| Situation | What you need |
|---|---|
| One CPU, polling one peripheral register | `volatile` alone. Device memory is already ordered with respect to itself. |
| Fill a buffer in SRAM, then start a DMA transfer of it | `__DMB()` between the last buffer write and the DMA enable. |
| DMA completes, you read the buffer | `__DMB()` after observing the completion flag, before reading. |
| Share a flag between `main` and an ISR on one core | `volatile` plus atomicity (see above). No barrier — exception entry and return are already ordering points. |
| Write `SCB->VTOR`, then enable an interrupt | `__DSB()` then `__ISB()`. |
| Enable the MPU or the FPU | `__DSB()` then `__ISB()`. |

The middle rows are the ones people get wrong, and the symptom is data corruption at the start or end of a DMA buffer that appears only when the cache or write buffer is under pressure. On a Cortex-M7 with caches enabled the same situation additionally requires cache maintenance, which is a different problem with a different fix.

## When not to use it

`volatile` is right for memory-mapped registers and for variables shared with an interrupt handler on the same core. It is wrong, or insufficient, for several things it gets reached for:

- **As a substitute for atomics in multithreaded code.** It gives no atomicity and no cross-core ordering. C11 `_Atomic` or the `__atomic_*` builtins are the right tool; on Cortex-M they lower to `LDREX`/`STREX` or to interrupt masking.
- **To stop the compiler "optimising away" a struct member.** If something is being removed that you need, understand why first — very often the real answer is `used`, `KEEP` in the linker script, or a missing declaration, not `volatile`.
- **On a whole struct, reflexively.** Qualifying a large `volatile` struct and then copying it forces a member-by-member load/store and can be dramatically slower than the `memcpy` it prevents.
- **On the shared buffer in a DMA transfer.** The buffer is ordinary memory; what you need is a barrier at the handover point, not a qualifier that pessimises every access to it. Marking it `volatile` makes the code slower and still does not fix the ordering.

:::warning[Your timing delay disappears when you raise the optimisation level]
Every embedded codebase has a `delay()` written as a counted loop, and it is the most reliable way to discover what `volatile` is for.

```c
static void delay(uint32_t n) { while (n--) { } }
```

At `-O0` this loops. At `-O1` and above GCC observes that the loop has no side effects, that `n` is a local whose final value is unused, and deletes it entirely — the whole function becomes `bx lr`. The build succeeds, the image shrinks, and the LED stops blinking: the toggles are still there but with nothing between them, so the pin runs at a few megahertz and the LED reads as continuously half-lit. People conclude the GPIO configuration broke, because the visible symptom is about the LED.

The fix is to make the loop counter an access the compiler cannot elide:

```c
static void delay(volatile uint32_t n) { while (n--) { } }
```

Now every decrement is a load, a subtract and a store to the stack slot, and the loop must run. This is the mechanism the blink page relies on.

Two things to be clear about, because this is where people over-learn the lesson:

- **The number of iterations is not a duration.** It depends on the optimisation level, the compiler version, the flash wait states, whether the prefetch buffer and instruction cache are enabled, and the current clock frequency — which the clock-tree page is about to change by a factor of six. A "1 ms" delay calibrated at `-Og` on the 16 MHz reset clock is not 1 ms at `-Os` at 100 MHz. Treat the constant as a calibration knob and nothing more.
- **A busy-wait loop is the wrong mechanism for anything real.** It burns power, it cannot be interrupted usefully, and it makes timing a property of your build flags. Use SysTick or a hardware timer — [SysTick and the Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md) covers the one that is built into every Cortex-M. The `volatile` loop is for the fifteen minutes before you have a clock configured, and for nothing after that.

The same optimisation, applied to the `.data` copy in startup code, produces a much nastier version of this: GCC rewrites the loop into a call to `memcpy` rather than deleting it. [Startup Code](../03-toolchain-and-build/startup-code.md) has that one.
:::

## See also

- [Register-Level Programming](./register-level-programming.md) — the memory-mapped I/O model, and why status registers must never be read-modify-written.
- [A GPIO Driver from Scratch](./gpio-driver-from-scratch.md) — `BSRR`, the hardware answer to the read-modify-write race above.
- [CMSIS and Vendor HALs](./cmsis-and-vendor-hals.md) — where `__DMB`, `__DSB` and `__ISB` come from.
- [The Cortex-M Memory Map](../02-processor-architecture/memory-map-and-bit-banding.md) — Normal versus Device memory, and the ordering each provides.
- [Optimization for Size and Speed](../03-toolchain-and-build/optimization-flags.md) — the optimisation levels at which each transformation above switches on.

## References

- ISO/IEC — **9899:2018** (C17). §6.7.3¶8 for the volatile guarantee quoted above; §5.1.2.3 "Program execution" for volatile access as an observable side effect and for the statement that what constitutes an access is implementation-defined; §6.5.16 and §6.7.3 for qualifier semantics on assignment. The freely available [N2310 working draft](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n2310.pdf) tracks the published C17 text closely.
- Free Software Foundation — [**GCC manual, "Volatiles"**](https://gcc.gnu.org/onlinedocs/gcc/Volatiles.html). GCC's implementation-defined answer to "what is an access": which expressions involving volatile objects generate a load, a store, or neither, and the cases where the standard leaves it open. Also [**"Extended Asm"**](https://gcc.gnu.org/onlinedocs/gcc/Extended-Asm.html) for the `"memory"` clobber that makes `__asm volatile ("" ::: "memory")` a compiler barrier, and [**`__atomic` builtins**](https://gcc.gnu.org/onlinedocs/gcc/_005f_005fatomic-Builtins.html) for the atomicity `volatile` does not provide.
- Arm — [**Armv7-M Architecture Reference Manual**](https://developer.arm.com/documentation/ddi0403/latest/). §A3.4 for single-copy atomicity of naturally aligned byte, half-word and word accesses; §A3.5 "Memory access order" for Normal versus Device memory ordering; §A3.7 for `DMB`, `DSB` and `ISB` semantics.
- Arm — [**CMSIS-Core documentation**](https://arm-software.github.io/CMSIS_6/latest/Core/index.html) (verified via context7, 2026-08-24). The barrier intrinsics `__DMB()`, `__DSB()` and `__ISB()` used above, documented under "Compiler Control" — `__ISB` "flushes the processor pipeline", `__DSB` "ensures all memory accesses prior to it are completed".
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). §6.3.1 "RCC clock control register" for `HSIRDY` at bit 1 of `RCC_CR`, the hardware-set flag the polling example waits on.
