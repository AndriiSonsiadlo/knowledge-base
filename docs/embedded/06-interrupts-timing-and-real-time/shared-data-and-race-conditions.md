---
id: shared-data-and-race-conditions
title: Shared Data and Race Conditions
sidebar_label: Shared Data and Race Conditions
sidebar_position: 5
tags: [embedded, cortex-m, concurrency, volatile, atomicity, sig-atomic-t, race-conditions]
---

# Shared Data and Race Conditions

A single-core MCU with interrupts enabled runs a concurrent program, and the reason people are surprised by that is that the concurrency is invisible in the source. There is one `main`, one call stack in view, no threads to create, and nothing that looks like it could run at the same time as anything else. But between any two machine instructions the hardware may insert an entire function of someone else's code, and if that function touches a variable you were half-way through updating, the update is lost — or worse, the value it reads is one that never existed.

The mental model: **the source line is not the unit of execution.** `count++` is one line, one expression, and three instructions, and preemption happens between instructions. Everything on this page follows from taking that sentence literally: to reason about a shared variable you have to look at the machine code, or at least know what shape it has.

[Concurrency and Synchronization](../../computer-science/operating-systems/concurrency-and-synchronization.md) owns the general theory — what a race condition is, what mutual exclusion means, why deadlock happens. This page is the specific, concrete case: one core, one ISR, one `main`, and the exact instructions between which the damage occurs.

:::info[Prerequisites]
[What `volatile` Does and Does Not Do](../04-bare-metal-programming/volatile-and-the-compiler.md) establishes the guarantee the qualifier gives (the access happens, in order, at the width you wrote) and the one it does not (atomicity). [Critical Sections and Atomicity](../04-bare-metal-programming/critical-sections-and-atomicity.md) owns the *fixes* — `PRIMASK`, `BASEPRI`, `LDREX`/`STREX`, hardware-atomic registers — and the decision tree between them. This page is about recognising the problem before you go looking for a mechanism.
:::

## The canonical failure, at instruction level

A pulse counter. An EXTI interrupt increments it; the main loop periodically consumes the accumulated count and resets it to zero. Two contexts, one variable, and `volatile` correctly applied.

<Tabs>
<TabItem value="c" label="C — one line each, looks obviously fine" default>

```c
static volatile uint32_t pulses;

void EXTI0_IRQHandler(void)          /* producer */
{
    EXTI->PR = EXTI_PR_PR0;
    pulses++;
}

void main_loop(void)                 /* consumer */
{
    for (;;) {
        total  += pulses;            /* read  */
        pulses  = 0;                 /* clear */
        report(total);
    }
}
```

</TabItem>
<TabItem value="asm" label="Thumb-2 — the gap the source does not show">

```armasm
@ main_loop: total += pulses; pulses = 0;
        ldr     r3, =pulses
        ldr     r2, [r3]        @ (1) read pulses         ← ISR here: fine
        ldr     r1, =total
        ldr     r0, [r1]
        adds    r0, r0, r2
        str     r0, [r1]        @     total updated       ← ISR here: LOST
        movs    r2, #0
        str     r2, [r3]        @ (2) pulses = 0          ← the increment is erased

@ EXTI0_IRQHandler: pulses++;
        ldr     r3, =pulses
        ldr     r2, [r3]        @ read
        adds    r2, #1          @ modify — in a register nobody else can see
        str     r2, [r3]        @ write
```

</TabItem>
</Tabs>

*The load-modify-store shape any Armv7-M compiler must emit for a read-modify-write on a `volatile` object; literal pools folded into `ldr =` for readability. Check yours with `arm-none-eabi-objdump -d` rather than assuming — see [Reading Disassembly](../../computer-science/assembly/reading-disassembly.md).*

The interleaving that loses data, with `pulses` starting at 7:

| Step | Context | Action | `pulses` in memory | Registers |
|---|---|---|---|---|
| 1 | main | `ldr r2, [r3]` — reads 7 | 7 | `r2 = 7` |
| 2 | **ISR** | reads 7, adds 1, stores 8 | **8** | — |
| 3 | **ISR** | (returns) | 8 | — |
| 4 | main | adds 7 to `total` | 8 | — |
| 5 | main | `str #0` — clears | **0** | — |

The pulse counted at step 2 is gone. Not delayed, not double-counted — gone, with no error anywhere, and the deficit is exactly one pulse per occurrence. At a low pulse rate the window is narrow and you might lose a count an hour; the calibration is then 0.03 % out and nobody ever finds out why.

The window is the *whole* sequence from step 1 to step 5, not just the increment. That is the part people miss: it is not `pulses++` that is unsafe here so much as the consumer's read-then-clear, which is a read-modify-write with a lot of code in the middle of it.

**The fix is to make read-and-clear one operation**, which the architecture provides directly:

```c
uint32_t n = __atomic_exchange_n(&pulses, 0u, __ATOMIC_RELAXED);
total += n;
```

That compiles to an `LDREX`/`STREX` retry loop — no interrupt is delayed by a single cycle, and if the ISR fires inside the loop the `STREX` fails and the sequence runs again. [Critical Sections and Atomicity](../04-bare-metal-programming/critical-sections-and-atomicity.md) covers the mechanism and the alternatives; the point here is that the *shape* of the operation had to change. No amount of qualifying the variable would have helped.

## Why `volatile` is necessary and not sufficient

Both halves matter, and firmware codebases usually get one of them wrong.

**Necessary.** Without `volatile`, the compiler is entitled to assume nothing else modifies the object, so it may hoist the load out of a loop entirely — `while (!flag) {}` becomes a load, a test, and an infinite branch to itself. Every variable shared with an ISR or a DMA controller needs it.

**Not sufficient.** `volatile` constrains the *accesses*: it guarantees each one happens, in program order relative to other volatile accesses, at the width you declared. It says nothing whatever about what happens between two accesses. In the listing above, every load and store is exactly as `volatile` promised, and the data is still lost — because the loss happens in the gap, in a register, where `volatile` has no jurisdiction.

Two consequences worth stating plainly:

- **`volatile` is not a synchronisation primitive.** It orders volatile accesses against each other, not against ordinary memory, and it emits no barrier instruction. It cannot make a two-word update atomic, cannot make a read-modify-write indivisible, and cannot prevent a struct from being observed half-written.
- **Removing it can make a race disappear.** Aggressive optimisation sometimes keeps a value in a register across the whole window, shrinking or closing it. That is not a fix; it is the same defect with a different reproduction rate, which is how a bug ends up marked "cannot reproduce in the release build".

## `sig_atomic_t`, and exactly what it promises

The C standard's only concession to asynchronous interruption predates threads and is narrower than it looks. `sig_atomic_t` is "an integer type of an object that can be accessed as an atomic entity even in the presence of asynchronous interrupts" (ISO/IEC 9899 §7.14), and the object an asynchronous signal handler may portably touch is a `volatile sig_atomic_t`.

What that buys you, and what it does not:

| It guarantees | It does not guarantee |
|---|---|
| A single **load** is not torn — you never read half of one value and half of another | That `x++` is atomic. That is a load, a modify and a store, and the type says nothing about the sequence |
| A single **store** is not torn | Any ordering with respect to other objects — it is not a barrier |
| That the type exists and is an integer | Any particular width. It is implementation-defined; on Arm GNU Toolchain's newlib it is `int`, but read your sysroot's `<signal.h>` rather than assuming |
| Portability of the *access* | That an interrupt is a signal. The C model is signals; the mapping to MCU interrupts is by analogy, and the standard has never been asked about `BASEPRI` |

On Armv7-M every naturally aligned 32-bit access is already single-copy atomic by architecture (*Armv7-M ARM* §A3.5.3), so `volatile sig_atomic_t` and `volatile uint32_t` behave identically on this part. Use the standard type where portability across toolchains matters; do not mistake it for the atomicity you actually need, which is almost always atomicity of a *sequence*.

## The shapes that go wrong

[Interrupt Handlers in C](../04-bare-metal-programming/interrupt-handlers-in-c.md) has the table of which sharing patterns are safe. Three of them deserve the instruction-level treatment, because each has a standard correct answer that is not "disable interrupts".

### A 64-bit counter read from thread context

A millisecond counter that must not wrap in 49 days needs 64 bits, and a 32-bit core reads it as two loads. If the ISR increments across a carry between them, the reader gets a value that was never in memory — typically 4 294 967 296 ms wrong, once every 49 days, for one instruction window. The fix does not require masking:

```c
static volatile uint32_t ms_lo, ms_hi;      /* ISR increments lo, carries into hi */

uint64_t millis(void)
{
    uint32_t hi, lo;
    do {
        hi = ms_hi;
        __atomic_signal_fence(__ATOMIC_ACQUIRE);   /* compiler barrier, no instruction */
        lo = ms_lo;
        __atomic_signal_fence(__ATOMIC_ACQUIRE);
    } while (hi != ms_hi);                          /* carry happened — read again */
    return ((uint64_t)hi << 32) | lo;
}
```

The loop terminates because the ISR can only carry once per 2³² milliseconds. Note the fences: without them the compiler may reorder the two loads relative to the re-read, and the whole argument collapses. They emit no code.

### A multi-field struct written by an ISR

A GPS fix, a sensor sample with a timestamp, a set of motor currents. The reader can observe the new value of one field beside the old value of another, and the result is a data point that is internally inconsistent rather than merely stale. Two standard answers:

- **Double buffering.** The ISR fills the inactive buffer and then publishes a pointer or an index with a single aligned store. The reader takes the published index once, and reads only that buffer. One store publishes the whole structure. This is the same idea the DMA half-transfer interrupt implements in hardware ([DMA](../05-peripherals-and-drivers/dma.md)).
- **A sequence counter.** The writer increments a counter to an odd value before touching the struct and to an even value after; the reader retries while the counter is odd or changed across the read.

```c
/* Writer — must be the ISR side. */
seq++;                                          /* odd: update in progress */
__atomic_signal_fence(__ATOMIC_RELEASE);
fix = new_fix;
__atomic_signal_fence(__ATOMIC_RELEASE);
seq++;                                          /* even: consistent again */
```

The constraint that decides which one you can use: **a sequence counter is only safe when the retrying side is the one that can be pre-empted.** Reader in thread context, writer in the ISR — fine, the reader retries and eventually wins. Reader in an ISR, writer in thread context — the reader spins forever, because the writer it is waiting for cannot run. That is a one-line deadlock on a single core, and it looks like a hardware lockup. Double buffering has no such restriction.

### A buffer shared with a DMA controller

Not a race between two instruction streams but between the core and a second bus master, and the failure mode is different. On this part there is no cache, so there is no coherency problem to solve — [DMA](../05-peripherals-and-drivers/dma.md) is explicit that cache maintenance on an F4 is copied-from-F7 noise. What remains is **ordering**: your stores into the buffer are accesses to Normal memory, and the store that enables the stream is an access to Device memory, and the architecture does not order those against each other for free (*Armv7-M ARM* §A3.8). A `__DMB()` between filling the buffer and enabling the stream is the correct and cheap insurance, and the symmetric one after the transfer-complete flag before reading results.

## Why the ring buffer needs none of this

The single-producer/single-consumer ring buffer in [Deferred Work](./deferred-work.md) shares two indices and a data array between an ISR and `main`, uses no critical section, and is correct. The argument is worth spelling out, because it generalises:

**Every mutable location has exactly one writer.** The producer writes `head` and the slots at `head`. The consumer writes `tail` and reads slots below `head`. Neither ever performs a read-modify-write on a variable the other writes. The only cross-context operations are single aligned loads and single aligned stores, both of which are atomic by architecture.

A race needs two writers, or one writer and a read-modify-write. Eliminate that and there is nothing left to protect. Adding a `count` field — incremented by one side, decremented by the other — reintroduces exactly the failure this page opened with, which is why the listing does not have one.

The general principle: **prefer restructuring ownership over adding a lock.** A lock costs latency for every interrupt in the system and can be forgotten at one call site out of twenty. An invariant like "only the ISR writes `head`" is checkable by grep.

:::warning[The waypoint from the middle of the Atlantic, and the bug that only exists at `-O2`]
Two shapes of the same defect, both of which get misdiagnosed for days.

**The half-updated struct.** A GPS module's ISR writes a `struct fix { double lat, lon; uint32_t t; }` and the navigation loop reads it. Nothing is `++`'d, nothing is read-modify-written, and every field is `volatile` — so a code review passes it. Then the ISR fires between the reader's load of `lat` and its load of `lon`, and the loop computes a course from the new latitude and the previous longitude. On land the two fixes differ by metres and nothing happens. Cross a degree boundary, or come out of a tunnel with a large jump, and one waypoint lands in the ocean; the track has a single spike and the next point is fine. The symptom is reported as "occasional GPS glitch", which sends everyone to the antenna and the module's firmware. The tell: the bad point's coordinates are always a *mixture* of two real fixes, never a value from nowhere. Publish the struct with a single store — double-buffer it — or use a sequence counter, and never let a reader take two loads from a structure that a handler can rewrite.

**The race that only exists in the release build.** Compile at `-O0` and the compiler spills everything to the stack around every statement, which changes the width of the window; sometimes it closes it, and sometimes it opens a new one. So the bug reproduces at `-O2` and vanishes under the debugger, which is exactly the pattern that makes people say "it's an optimiser bug" and add `volatile` to more variables until it goes away. It is not an optimiser bug and `volatile` is not the fix. Disassemble the function in the failing build (`arm-none-eabi-objdump -d`), find the load and the store that bracket the update, and ask what the ISR does if it runs between them. If the answer is "writes the same location", you have found it, and the fix is an atomic operation or a critical section — not a build flag.
:::

## See also

- [Deferred Work](./deferred-work.md) — the single-producer/single-consumer ring buffer whose safety argument is the last section here.
- [Priorities and Nesting](./interrupt-priorities-and-nesting.md) — putting two handlers at the same preempt priority as free mutual exclusion between them.
- [Critical Sections and Atomicity](../04-bare-metal-programming/critical-sections-and-atomicity.md) — the mechanisms that fix everything on this page, and the decision tree for choosing between them.
- [What `volatile` Does and Does Not Do](../04-bare-metal-programming/volatile-and-the-compiler.md) — the qualifier's exact guarantee, which this page depends on being understood precisely.
- [Concurrency and Synchronization](../../computer-science/operating-systems/concurrency-and-synchronization.md) — the general theory of races, mutual exclusion and deadlock, independent of any processor.

## References

- ISO/IEC — **9899:2018**, *Programming languages — C*. §7.14 for `sig_atomic_t` and the rule restricting what an asynchronous signal handler may access; §7.17.4.2 for `atomic_signal_fence`, the compiler-only ordering primitive used above; §5.1.2.4 for the memory model that makes an unsynchronised conflicting access undefined behaviour rather than merely unlucky. (The published standard is a purchase; committee draft N2176 is free and identical in these clauses.)
- Arm — [***Armv7-M Architecture Reference Manual***](https://developer.arm.com/documentation/ddi0403/latest/) (DDI 0403E.e). §A3.5.3 for single-copy atomicity, which is what makes an aligned 32-bit load or store safe to share without any mechanism at all; §A3.8 for the memory-ordering rules between Normal and Device memory that the DMA `__DMB()` above relies on; §A3.4 for the exclusive monitor behind `__atomic_exchange_n`.
- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), Rev 10. §2.1.3 for the masking registers a critical section manipulates; §2.4 "Cortex-M4 instruction set" for `LDREX`/`STREX`/`CLREX` — what `__atomic_exchange_n` compiles to on this core — and for the `DMB`, `DSB` and `ISB` barrier instructions with a statement of what each one orders.
- Free Software Foundation — [**GCC manual, "Built-in Functions for Memory Model Aware Atomic Operations"**](https://gcc.gnu.org/onlinedocs/gcc/_005f_005fatomic-Builtins.html). `__atomic_exchange_n`, `__atomic_load_n` and `__atomic_signal_fence`, and the documented behaviour on targets without native exclusive instructions — relevant if the same source has to build for Cortex-M0.
