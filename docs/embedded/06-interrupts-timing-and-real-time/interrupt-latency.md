---
id: interrupt-latency
title: Interrupt Latency
sidebar_label: Interrupt Latency
sidebar_position: 1
tags: [embedded, cortex-m, interrupts, latency, timing, real-time, stm32]
---

# Interrupt Latency

Ask what the interrupt latency of a Cortex-M4 is and you get "12 cycles", which is true and almost never the number you need. Twelve cycles is what the *processor* contributes when the memory is instant, nothing else is running, and the exception arrives at a convenient moment. The number that decides whether your product works is the one measured from the event at the pin to the first instruction of your handler that does something about it — and on a real board, at a real clock, with the rest of your firmware present, that number is dominated by things the core designer had no say in.

The mental model: **latency is a sum of terms, most of which are properties of your program rather than of the silicon.** The hardware terms are small, fixed, and documented. The software terms — how long your other handlers run, how long your critical sections are, how far your code has drifted from the flash accelerator's cache — are unbounded by default, and the whole job of a real-time design is to bound them. A latency figure without the software terms is a marketing number.

The second thing worth internalising early: **you care about the worst case, not the average.** The average is what your scope shows you in ten seconds of idle bench time. The worst case is the one alignment of events that happens twice a day in the field, and it is the only one that can miss a deadline.

:::info[Prerequisites]
[The NVIC](../02-processor-architecture/the-nvic.md) covers arbitration, priority numbers, and the tail-chaining and late-arrival optimisations this page quantifies. [Exceptions and the Vector Table](../02-processor-architecture/exceptions-and-the-vector-table.md) covers the entry sequence itself — the stack frame, the vector fetch, `EXC_RETURN`. [Critical Sections and Atomicity](../04-bare-metal-programming/critical-sections-and-atomicity.md) owns the masking mechanisms whose duration appears below as a latency term.
:::

## The chain, end to end

```wavedrom title="From pin edge to the first instruction of the handler body" alt="Timeline showing the pin edge, the NVIC pending bit, the core finishing its instruction, stacking, vector fetch, handler prologue and body, and a GPIO probe rising at the start of the body"
{ "signal": [
  { "name": "EXTI pin",     "wave": "0.1........................." },
  { "name": "NVIC pending", "wave": "0..1......0................." },
  { "name": "core",         "wave": "3...4..5..6.7.....8.........",
    "data": ["thread code", "finish insn", "stack 8 words", "vector fetch", "prologue", "handler body"] },
  { "name": "GPIO probe",   "wave": "0.................1.....0..." }
], "config": { "hscale": 1 } }
```

Read left to right, the terms are:

| # | Term | Bounded by | Typical on this board | Who controls it |
|---|---|---|---|---|
| 1 | Peripheral detection and synchronisation | Peripheral design | 1–2 APB cycles | Nobody — read the peripheral's chapter |
| 2 | **Masking**: `PRIMASK`/`BASEPRI` held by your own code | Longest critical section | 0, or however long your worst section is | **You** |
| 3 | **Preemption**: a handler at equal or higher priority is already running | Sum of higher-priority handler times | 0, or unbounded | **You** |
| 4 | Completing the current instruction | Longest non-abandonable instruction | 1–10+ cycles | Mostly you |
| 5 | Stacking 8 words (26 with FP context) | SRAM speed | 8 bus cycles, zero wait states | Partly you |
| 6 | Vector fetch from the table | Table location, wait states | 1 word from flash or SRAM | You |
| 7 | Handler prologue, up to your first useful statement | Compiler, handler shape | a few cycles | **You** |

Terms 4–6 are what Arm's "12 cycles" measures. Terms 2, 3 and 7 are usually larger, and term 3 can be arbitrarily large. That ordering is the point of the page.

## Term 4: finishing the current instruction

The core does not abandon whatever it was doing the instant a request arrives. Most Thumb-2 instructions are one or two cycles, so the expected cost is small, but the *worst* case is set by the longest instruction that cannot be interrupted part-way.

Armv7-M is explicit about this. A load-multiple or store-multiple (`LDM`, `STM`, and the `PUSH`/`POP` they underlie) *may* be abandoned mid-sequence and resumed afterwards, with the number of registers already transferred recorded in the **ICI** bits of the `EPSR` — so a 14-register `LDM` from SRAM does not add fourteen cycles to your latency. The architecture withholds that permission in one case: when the access is to **Device or Strongly-ordered memory**, the instruction must run to completion, because the accesses have side effects that cannot be replayed (*Armv7-M ARM* §B1.5.10, "Exceptions in Load Multiple and Store Multiple operations"). Every peripheral register on this part is Device memory.

So the instruction-completion term is small unless your code does one of these:

- **A multiple load or store against a peripheral aperture.** `memcpy` into a peripheral FIFO, or a struct copy that the compiler turned into `LDM`/`STM` over memory-mapped registers.
- **A single access that stalls.** An APB1 read on this part runs at up to 50 MHz while the core runs at 100 MHz (RM0383 Rev 4 §6.2, clock tree), so a peripheral read costs several core cycles before anything else happens.
- **Integer divide.** `SDIV`/`UDIV` are multi-cycle on Cortex-M4. They are restartable, so they do not pin the core, but they are worth knowing about when you are counting.

The worst case worth writing into a budget is the peripheral store-multiple. A driver that copies a five-word command block into a peripheral's registers with a struct assignment gets an `STM` of five words to Device memory. It cannot be abandoned, so the core finishes all five before it even begins exception entry. On APB1 at 50 MHz, with the core at 100 MHz, each of those accesses occupies at least two core cycles and more if the bus matrix has the DMA controller ahead of it — so the term is on the order of **10–20 cycles, or 100–200 ns**, where a normal instruction would have cost one.

That is small next to a 200 µs handler, and it is the correct order of magnitude to write down: instruction completion is a **sub-microsecond** term unless something pathological is happening. The reason to enumerate it at all is that it is the only term of the seven that is genuinely a property of the core's arbitration rules rather than of your design, so it sets the floor nothing can go below.

## Terms 5 and 6: stacking, the vector fetch, and flash wait states

Exception entry pushes eight words — `R0`–`R3`, `R12`, `LR`, `PC`, `xPSR` — and if the FPU context is live, reserves 18 more. That happens onto whichever stack was active, which on a bare-metal program is SRAM. On the STM32F411, SRAM is zero-wait-state at every supported frequency, so stacking is as fast as the bus allows; there is no equivalent of the flash penalty here.

The flash penalty is real, though, and it lands on the *fetch* side. RM0383 Rev 4 §3.4.1, Table 5 ("Number of wait states according to CPU clock frequency") gives the requirement for VDD in the 2.7–3.6 V range:

| HCLK | Wait states |
|---|---|
| 0 < HCLK ≤ 30 MHz | 0 |
| 30 < HCLK ≤ 64 MHz | 1 |
| 64 < HCLK ≤ 90 MHz | 2 |
| 90 < HCLK ≤ 100 MHz | 3 |

At the NUCLEO-F411RE's maximum 100 MHz, **every flash access costs 3 wait states** unless it hits the ART accelerator. The ART (RM0383 Rev 4 §3.4.2) is not a CPU cache — this is a Cortex-M4 and it has neither an instruction nor a data cache in the Cortex-M7 sense. It is a small cache *in the flash interface*: 64 lines of 128 bits for instructions, plus 8 lines for the literal pool, fed by a prefetch buffer. A 128-bit line is four to eight Thumb-2 instructions, so 64 lines is roughly 1 KB of hot code.

Two consequences for latency:

- **The vector fetch reads a word from the vector table.** If the table is in flash and cold, that read pays the wait states. Relocating the table to SRAM with `SCB->VTOR` removes that term, which is one of the reasons a bootloader-plus-application build does it anyway.
- **The handler's first instructions come from flash too.** A handler that ran a microsecond ago is in the ART and effectively free. A handler that runs once per second, in a program whose main loop has evicted it, pays 3 wait states on its first line fetch and again on every line boundary until the prefetcher catches up.

That is the mechanism behind a latency distribution with a long tail and no obvious cause.

:::note
Everything about wait states and the ART is part-specific. Another STM32 family has a different table, an M0+ typically has none, and an M7 adds real L1 caches with genuinely different behaviour. Take the table from your part's reference manual, not from this page.
:::

## Terms 2 and 3: the parts you wrote

These are the ones that actually decide the number, and neither appears in any Arm document.

**Masking.** Every instruction executed with `PRIMASK` set adds directly to the worst-case latency of *every* interrupt in the system, and every instruction executed under a `BASEPRI` threshold adds to the latency of everything at or below that threshold. A 200-instruction critical section at 100 MHz is 2 µs of latency added to everything — more than a hundred times the hardware entry cost. [Critical Sections and Atomicity](../04-bare-metal-programming/critical-sections-and-atomicity.md) covers the mechanisms; the discipline it demands ("short and bounded") is a latency requirement, not an aesthetic one.

**Preemption.** An interrupt cannot start while an equal-or-higher-priority handler is active. So the worst-case latency of interrupt *i* includes the execution time of every handler that can be ahead of it — and if two of them can arrive back-to-back, both. This is the term that goes unbounded quietly: add a handler that occasionally takes 300 µs because it does a flash page write, give it a priority number lower than your control loop, and you have added 300 µs to the control loop's worst case without touching the control loop.

The bound is structural, not arithmetical. You get it by deciding which handlers may sit above which, which is what [Priorities and Nesting](./interrupt-priorities-and-nesting.md) is about.

## Tail-chaining and late arrival

Two hardware behaviours change the arithmetic when exceptions arrive close together, and both make things better rather than worse.

**Tail-chaining.** When a handler returns and another exception is already pending, the processor does not unstack and then re-stack — the exception frame it would pop is exactly the frame the next handler would push, so it keeps it and goes straight to the next vector fetch. Arm's *Cortex-M4 Technical Reference Manual* (DDI 0439, exception-handling chapter) quotes **6 cycles** for a tail-chained transition against **12 cycles** for entry from thread mode. [The NVIC](../02-processor-architecture/the-nvic.md) shows the two timelines side by side.

**Late arrival.** A higher-priority exception that becomes pending while the frame for a lower-priority one is still being stacked takes over the vector fetch. Stacking is not restarted — the frame is generic — so the late arriver's latency is *shorter* than if it had waited, and the pre-empted one is tail-chained afterwards.

The practical reading: back-to-back interrupts are cheaper than two isolated ones, so a burst is not as expensive as `n × entry cost`. What you must not conclude is that entry is therefore negligible. Six cycles saved does nothing about a 300 µs handler ahead of you in the queue.

:::note[Where the numbers come from]
PM0214 describes the exception entry and return sequence, tail-chaining and late arrival (Rev 10, §2.3.7 "Exception entry and return"), but it is a programming manual and does not tabulate cycle counts. The 12-cycle and 6-cycle figures above are from Arm's *Cortex-M4 Technical Reference Manual* (DDI 0439), and they are properties of that processor implementation with zero-wait-state memory — not of the architecture, and not of your board once flash wait states are in play. Where this page states a *derived* number, it says so and shows the arithmetic.
:::

## Measuring it: a GPIO and a scope

The authoritative measurement is a two-channel capture of the stimulus and a pin your handler toggles. Nothing else tells you what the system actually does, because nothing else includes terms 2 and 3.

```c
/* PA5 is LD2 on the NUCLEO-F411RE (UM1724 §6.4); PA6 and PA7 are free on CN5.
   Configure PA6 as a push-pull output at high speed before enabling anything. */
#define PROBE_PIN   6u

void EXTI0_IRQHandler(void)
{
    GPIOA->BSRR = (1u << PROBE_PIN);        /* rising edge: first line of the body */

    EXTI->PR = EXTI_PR_PR0;                 /* acknowledge (write-1-to-clear) */
    handle_event();

    GPIOA->BSRR = (1u << (PROBE_PIN + 16)); /* falling edge: handler done */
}
```

Method, in the order that matters:

1. **Drive the stimulus yourself.** A signal generator into the EXTI pin at a known rate gives you a clean channel-1 trigger. A button does not — it bounces, and you will measure the bounce.
2. **Set the probe with `BSRR`, never `ODR`.** `GPIOA->ODR |= bit` is a read-modify-write: three instructions plus an APB read, and it is *itself* part of what you are measuring. `BSRR` is one store (RM0383 Rev 4 §8.4.7).
3. **Trigger on channel 1's edge and measure to channel 2's rise.** That interval is the full latency: detection, masking, preemption, instruction completion, stacking, vector fetch, prologue.
4. **Use infinite persistence and leave it running under load.** Ten seconds of an idle board shows you the best case. The distribution you need appears only when the rest of the firmware is doing its worst — logging, flash writes, the display refresh.
5. **Read the maximum, then find out what produced it.** The tail is the answer. If the tail is 40 µs and the mode is 300 ns, something specific is holding the core for 40 µs, and it is nearly always one critical section or one long handler.

Two cheaper instruments for when a scope is not on the desk:

- **`DWT->CYCCNT`.** A free-running 32-bit core-cycle counter at `0xE0001004`; enable trace with `DEMCR.TRCENA` (bit 24 of `0xE000EDFC`), then set `DWT_CTRL.CYCCNTENA` (*Armv7-M ARM* §C1.8, "Data Watchpoint and Trace unit"). Latch it in the handler, subtract the value latched by whatever raised the request, and you have a cycle-exact interval with no external hardware. This measures software-to-software; it cannot see the pin.
- **A logic analyser on the probe pin alone**, histogramming the interval between stimulus and rise. Cheaper than a scope and better at catching rare tails, because it can run for hours.

The board also carries an SWO pin, so the same intervals can be timestamped by the trace hardware and correlated with which handler was running — a considerably better tool for finding *what* caused a tail than for measuring the tail itself. That is a debugging workflow rather than a timing one, and it is treated separately.

## A worst-case budget you can defend

Latency budgets are written, not measured — you measure to check the budget, not to discover it. A defensible one for a single interrupt looks like this, with every row sourced:

| Term | Figure | Source |
|---|---|---|
| Peripheral detect + sync | 2 APB2 cycles @ 100 MHz = 20 ns | RM0383 §10.3, EXTI |
| Longest critical section | 40 instructions ≈ 400 ns @ 100 MHz | **Your code.** Count the worst one |
| Higher-priority handlers ahead | Σ of their WCETs | **Your design** |
| Instruction completion | ≤ 10 cycles = 100 ns | *Armv7-M ARM* §B1.5.10; bounded by your own peripheral `LDM`/`STM` usage |
| Hardware entry (stack + vector + fetch) | 12 cycles = 120 ns, zero wait states | Cortex-M4 TRM DDI 0439 |
| Flash wait states on a cold handler | +3 WS per 128-bit line missed in the ART | RM0383 §3.4.1 Table 5, §3.4.2 |
| Prologue to first useful statement | Read the disassembly | Your compiler |

Everything except rows 2, 3 and 7 sums to well under a microsecond. Rows 2 and 3 are where a system's real latency lives, and they are the two rows a datasheet can never tell you. If your budget's total is dominated by the hardware terms, you have either an unusually disciplined system or a budget that forgot to include the rest of the firmware.

## When the number is too big

The budget tells you which row to attack, and the rows have very different remedies. In descending order of how much they usually buy:

1. **Shorten the handlers ahead of it.** If term 3 dominates — and it usually does — the fix is not in the late interrupt, it is in the early one. Move work out of the offending handler into thread context ([Deferred Work](./deferred-work.md)). This routinely takes tens of microseconds off a worst case and costs nothing.
2. **Change the priority assignment.** Giving the urgent interrupt a numerically lower priority than the long-running one removes that handler from its worst case entirely, at the cost of adding preemption to the long one. This is a reallocation, not a saving — someone else pays.
3. **Find and shorten the critical sections.** Term 2 is invisible in source review and shows up as a floor under every latency in the system. Grep for `__disable_irq`, `__set_BASEPRI`, and whatever the vendor HAL's lock macro expands to, and put a bound on the longest one.
4. **Relocate the vector table to SRAM.** `SCB->VTOR` takes a 512-byte-aligned base address; copy the table into RAM at startup and the vector fetch stops paying flash wait states. Worth perhaps a hundred nanoseconds — meaningful only once terms 2 and 3 are already dealt with.
5. **Put the handler itself in SRAM.** A linker section that places a hot handler in RAM removes the wait states and the ART miss from its instruction fetches. It costs RAM and build complexity, and it is the last thing to reach for, not the first.
6. **Stop taking the interrupt.** If the event is a stream rather than an event, the lowest-latency design is one where the CPU is not involved per item at all — see [Polling, Interrupt, or DMA](./polling-interrupt-or-dma.md).

The ordering matters more than the list. Steps 4 and 5 are the ones people try first, because they are technical and satisfying, and they address the two smallest terms in the budget.

:::warning[The measurement that said 400 ns and the field that said 40 µs]
Two ways to measure interrupt latency and get a number that is real, repeatable, and useless.

**Measuring the hot path.** Drive the stimulus at 10 kHz on an otherwise idle board and the handler runs every 100 µs. It is resident in the ART accelerator's 64-line instruction cache, the branch to it is predicted, and the measurement is beautiful. In the field the event happens once every few seconds, the main loop has long since evicted the handler, and the first fetch of every 128-bit line costs 3 wait states at 100 MHz (RM0383 §3.4.1). The symptom is a latency histogram with a mode you can reproduce and a tail you cannot — and every attempt to reproduce it makes it disappear, because running it in a loop is exactly what makes it fast. Measure at the *event rate the product will see*, with the rest of the firmware running.

**Measuring with the probe you are measuring.** `GPIOA->ODR |= (1u << 6)` as the first line of the handler is a load, an OR and a store against Device memory on APB2. It adds cycles to the interval you are timing and, worse, it races with any other code that writes `ODR` for a different pin — the classic read-modify-write lost update, which will silently switch off an LED somewhere else in the program while you are debugging something unrelated. Use `BSRR`. It is one store, it is atomic in hardware, and it cannot touch a pin you did not name.

Both failures leave a system that passes on the bench and misses deadlines in the field, which is the most expensive class of timing bug there is.
:::

## See also

- [Priorities and Nesting](./interrupt-priorities-and-nesting.md) — how to bound the preemption term, which is the largest and least visible contributor above.
- [Deferred Work](./deferred-work.md) — the technique that keeps handler execution time short, and therefore keeps everyone else's latency short.
- [The NVIC](../02-processor-architecture/the-nvic.md) — arbitration, the priority byte, and the tail-chaining timeline this page refers to.
- [Critical Sections and Atomicity](../04-bare-metal-programming/critical-sections-and-atomicity.md) — the masking mechanisms whose duration is term 2 of the budget.
- [Tracing](../11-debugging-and-testing/tracing.md) — capturing the actual interrupt-to-ISR gap on hardware instead of trusting the budget's arithmetic.

## References

- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), Rev 10. §2.3.7 "Exception entry and return" for the entry sequence, the stack frame contents, tail-chaining and late arrival; §2.3.5 for the priority comparison that decides whether an exception can start at all. Note that it describes the sequence without quoting cycle counts.
- Arm — [***Cortex-M4 Technical Reference Manual***](https://developer.arm.com/documentation/ddi0439/latest/) (DDI 0439), exception-handling chapter. The source of the 12-cycle entry and 6-cycle tail-chain figures, stated for zero-wait-state memory. These are implementation figures for this core, not architectural guarantees — an M0+ and an M7 differ.
- Arm — [***Armv7-M Architecture Reference Manual***](https://developer.arm.com/documentation/ddi0403/latest/) (DDI 0403E.e). §B1.5.10 for the rule that `LDM`/`STM` may be abandoned and resumed via the `EPSR.ICI` bits except when the access is to Device or Strongly-ordered memory; §C1.8 for the DWT unit, `DWT_CYCCNT` and the `DEMCR.TRCENA` enable used in the measurement section.
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), Rev 4. §3.4.1 Table 5 for the wait-state table reproduced above and its VDD conditions; §3.4.2 for the ART accelerator's 64 instruction lines and 8 data lines; §8.4.7 for `GPIOx_BSRR`, the atomic set/reset register used by the probe.
- STMicroelectronics — [**UM1724**, *STM32 Nucleo-64 boards user manual*](https://www.st.com/resource/en/user_manual/um1724-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf). §6.4 for LD2 on PA5 and the Arduino/Morpho connector pinout, for choosing a probe pin that is not already committed.
