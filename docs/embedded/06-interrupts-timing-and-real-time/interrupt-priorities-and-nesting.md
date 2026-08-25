---
id: interrupt-priorities-and-nesting
title: Priorities and Nesting
sidebar_label: Priorities and Nesting
sidebar_position: 2
tags: [embedded, cortex-m, interrupts, nvic, priorities, basepri, real-time, stm32]
---

# Priorities and Nesting

Every interrupt on a Cortex-M comes out of reset at priority 0 — the most urgent level there is. A program that enables six interrupts and never calls `NVIC_SetPriority` has six handlers that all sit at the top, none of which can pre-empt any other, serviced in exception-number order when several arrive at once. That configuration is not "no priority scheme". It is a specific, and usually wrong, priority scheme: it says every interrupt in the system is equally urgent and none may interrupt another, which means the worst-case latency of your fastest deadline is the sum of every other handler's execution time.

The mental model: **a priority scheme is a statement about whose deadline you are willing to miss.** Preemption is not a performance feature; it is a mechanism for choosing, in advance and on purpose, which piece of work gets to be late. Everything on this page is in service of writing that choice down before the hardware makes it for you.

Two properties of the Cortex-M implementation shape how you express it, and both trip people who have used other architectures.

:::info[Prerequisites]
[The NVIC](../02-processor-architecture/the-nvic.md) owns the register-level detail: the `NVIC_IPR` byte array, `AIRCR.PRIGROUP` and its full binary-point table, and the enabled/pending/active state machine. This page assumes it and is about the design decision on top. [Critical Sections and Atomicity](../04-bare-metal-programming/critical-sections-and-atomicity.md) owns `PRIMASK` and `BASEPRI` as mechanisms; the priority *ceiling* they impose is the last section here.
:::

## Numbers run backwards, and there are four of them

Two facts established on [The NVIC](../02-processor-architecture/the-nvic.md) constrain everything below, and both are worth restating as *design* rules rather than register rules.

**Numerically lower means more urgent**, so English works against you the whole time. "Raising the priority of the interrupt" means writing a *smaller* number; "raising `BASEPRI`" also means writing a smaller number, which blocks *more*. Adopt a convention in comments and identifiers and never break it: say **more urgent** and **less urgent**, never higher and lower. Half the confusion in this area is vocabulary, not hardware.

**You have 16 usable levels, numbered 0–15**, because the STM32F411 implements four priority bits — and every raw register write must be pre-shifted, which is why nothing below writes a bare number. The NVIC page has the bit layout, the shift, and the `NVIC_SetPriority` arithmetic.

Sixteen levels sounds generous and is not, once you start reserving space. Plan on using six to eight of them.

## Preempt priority versus sub-priority

This is the distinction that gives the page its reason to exist, and it is routinely misread as "two-level sorting".

The priority byte is split by a binary point set globally in `AIRCR.PRIGROUP` (PM0214 Rev 10 §4.4.5, with the mandatory `0x5FA` write key). The bits above the point are the **group** or **preempt** priority. The bits below are the **sub-priority**. The rule:

- **Preempt priority decides whether an exception may interrupt what is currently running.** A newly pending exception starts immediately only if its preempt priority is numerically lower than the processor's current execution priority.
- **Sub-priority decides nothing about preemption at all.** It is a tie-break, used only when two exceptions are *already pending simultaneously* at the same preempt priority, to choose which of them is serviced first. Neither can interrupt the other. Neither can interrupt a handler at that same preempt level.

Concretely: two interrupts at preempt 5 with sub-priorities 0 and 3. If both go pending while the core is in thread mode, sub-0 runs first and sub-3 tail-chains behind it. If sub-3's handler is *already running* and sub-0 goes pending, sub-0 waits — the entire duration of sub-3's handler — and then tail-chains. Sub-priority buys you ordering, never responsiveness. If two things must not delay each other, they need different **preempt** priorities, full stop.

### Choosing a `PRIGROUP`, given what it costs

[The NVIC](../02-processor-architecture/the-nvic.md) tabulates what every `PRIGROUP` value splits the priority byte into, with a column giving the effective result on this part's four implemented bits. The design consequence of that table is a single trade, and it is the only thing you need to carry into a scheme: **every sub-priority you buy costs you a preemption level.** The default (`NVIC_PRIORITYGROUP_4`) spends all four bits on preemption; the alternatives take bits away from it.

Since sub-priority never causes preemption, that trade is almost always bad. Preemption levels are the scarce resource — they are the only thing that can protect a deadline — and sub-priority only reorders things that were already going to wait. Take the default unless you can name the two interrupts whose *ordering* matters while their *latency* does not.

The one setting worth a second look is the far end, where no bits are left for preemption at all: every interrupt then runs to completion, one exception frame is the maximum, and all handlers get free mutual exclusion against each other. For a small system with uniformly short handlers that is a defensible configuration rather than a degenerate one — and it is what Armv6-M parts get whether they choose it or not.

### What nests against what

Take the band scheme below and the default 16-preempt-level grouping. The nesting matrix is then simply "numerically lower interrupts the rest":

| Running ↓ / Arrives → | Safety (0) | Control (2) | Fast I/O (6) | Bulk I/O (8) | Housekeeping (12) |
|---|---|---|---|---|---|
| **Safety (0)** | tail-chains | waits | waits | waits | waits |
| **Control (2)** | **pre-empts** | tail-chains | waits | waits | waits |
| **Fast I/O (6)** | **pre-empts** | **pre-empts** | tail-chains | waits | waits |
| **Bulk I/O (8)** | **pre-empts** | **pre-empts** | **pre-empts** | tail-chains | waits |
| **Housekeeping (12)** | **pre-empts** | **pre-empts** | **pre-empts** | **pre-empts** | tail-chains |

Everything on the diagonal is the useful part: **two interrupts at the same preempt level cannot interleave**, which is mutual exclusion at zero cost. Everything below the diagonal is a stack frame you must budget for. Everything above the diagonal is latency one interrupt inflicts on another, and it is the column you read when someone asks why the housekeeping tick is late.

## What preemption actually looks like

```wavedrom title="An urgent EXTI handler pre-empting a less urgent timer handler" alt="Timeline in which a timer interrupt at priority 8 is being serviced when an EXTI interrupt at priority 2 arrives, causing a nested stack push, the EXTI handler, then resumption of the timer handler"
{ "signal": [
  { "name": "TIM2 IRQ (prio 8)", "wave": "0.10.........................." },
  { "name": "EXTI IRQ (prio 2)", "wave": "0.......10...................." },
  { "name": "core",             "wave": "3...4.5..4.6....5....9..3.....",
    "data": ["thread", "stack", "ISR A (8)", "stack again", "ISR B (2)", "ISR A resumes", "unstack", "thread"] }
], "config": { "hscale": 1 } }
```

Three things this makes visible:

- **The second stack push is real.** Nesting costs another exception frame: 32 bytes, or 104 if floating-point context is live. It is not tail-chaining, which is the *cheap* case; nesting is the expensive one.
- **ISR A resumes where it was, not from the top.** It was never told it was interrupted. Any hardware state it had latched, any half-updated structure it left, was visible to ISR B while B was running.
- **A's total execution time now includes all of B.** If A had a deadline, B just spent its budget.

That third point is why the answer to "should I allow nesting?" is not automatically yes.

## Designing the scheme

Start from deadlines, not from importance. The question is never "how important is the UART" — it is "what is the longest this can wait before something breaks, and what breaks".

A workable procedure:

1. **List every interrupt with its worst-case inter-arrival time and its deadline.** A UART at 115200 baud 8N1 delivers a byte every 86.8 µs, and the deadline for reading `DR` is one byte time before the overrun error — so 86.8 µs. A motor commutation ISR might have a 50 µs deadline. A 1 Hz housekeeping tick has a deadline of a second.
2. **Sort by deadline, shortest first, and assign priority numbers in that order.** That is rate-monotonic assignment applied to interrupts, and for a set of periodic activities it is the assignment that is optimal among fixed-priority schemes.
3. **Leave gaps.** Assign 0, 2, 4, 6, 8… not 0, 1, 2, 3. The interrupt you have to add next year needs somewhere to go, and inserting it should not mean renumbering everything.
4. **Reserve a band for the maskable interrupts** — see the ceiling section below.
5. **Write the table down in a header**, as an enum, so the scheme is a reviewable artefact rather than sixteen scattered calls.

A concrete band layout for a mixed system on this part:

| Level | Band | Contents | May it be masked by a critical section? |
|---|---|---|---|
| 0 | Safety | Hardware protection: overcurrent, emergency stop | **No.** Must never be delayed, and must touch no shared state |
| 2 | Control | Motor commutation, current loop | No |
| 4 | Reserved | — | — |
| 6 | Fast I/O | High-rate UART/SPI RX, input capture | Yes |
| 8 | Bulk I/O | DMA transfer-complete, ADC sequences | Yes |
| 10 | Application | Button EXTI, sensor ready, comms protocol timers | Yes |
| 12 | Housekeeping | 1 kHz tick, LED, watchdog refresh | Yes |
| 15 | Deferred | `PendSV`-style bottom halves, lowest of everything | Yes |

The two rows worth defending: **level 0 and 2 sit above the masking ceiling**, so nothing your firmware does with `BASEPRI` can delay them, and in exchange they are forbidden from touching any variable that a critical section protects. And **level 15 is deliberately empty of hardware**; it is where deferred work runs so that it cannot delay any real interrupt. Under an RTOS, the kernel's context-switch exception conventionally lives at the least-urgent level for exactly the same reason.

Written down, the scheme becomes an artefact a reviewer can argue with:

```c title="irq_priority.h — the scheme, in one place"
/* CMSIS scale: 0 = most urgent, 15 = least. STM32F411 implements 4 bits. */
enum irq_priority {
    PRIO_SAFETY       =  0,   /* above the masking ceiling: touches no shared state */
    PRIO_CONTROL      =  2,   /* above the masking ceiling                          */
    /* ---- BASEPRI masking ceiling sits here: nothing below is delayed by a lock -- */
    PRIO_MASK_CEILING =  5,
    PRIO_FAST_IO      =  6,
    PRIO_BULK_IO      =  8,
    PRIO_APPLICATION  = 10,
    PRIO_HOUSEKEEPING = 12,
    PRIO_DEFERRED     = 15,
};

#define BASEPRI_LOCK_VALUE  (PRIO_MASK_CEILING << (8u - __NVIC_PRIO_BITS))

void irq_priorities_init(void)
{
    NVIC_SetPriorityGrouping(3u);                 /* 4 preempt bits, 0 sub bits */

    NVIC_SetPriority(TIM1_UP_TIM10_IRQn, PRIO_CONTROL);
    NVIC_SetPriority(USART2_IRQn,        PRIO_FAST_IO);
    NVIC_SetPriority(DMA2_Stream0_IRQn,  PRIO_BULK_IO);
    NVIC_SetPriority(EXTI15_10_IRQn,     PRIO_APPLICATION);
    NVIC_SetPriority(SysTick_IRQn,       PRIO_HOUSEKEEPING);
    /* ... every interrupt this program enables appears above, no exceptions ... */
}
```

The `BASEPRI_LOCK_VALUE` macro is there because the pre-shift is the single most repeated bug in this area, and computing it once from `__NVIC_PRIO_BITS` means no call site ever writes a bare number.

:::tip
Set the priority of every interrupt you enable, including the ones you think are obviously fine at the default. `grep -c NVIC_EnableIRQ` and `grep -c NVIC_SetPriority` over the project should return the same number. When they differ, the missing one is running at level 0, above everything you carefully designed.
:::

## System exceptions are set somewhere else

An easy hour to lose: `SysTick`, `PendSV`, `SVCall` and the faults are **not** in the NVIC's `IPR` array. They are exceptions 1–15, and their priorities live in the System Handler Priority registers `SHPR1`–`SHPR3` in the SCB (PM0214 Rev 10 §4.4.8–§4.4.10). CMSIS hides the difference — `NVIC_SetPriority()` takes a signed `IRQn_Type` and routes negative numbers to `SHPR` — so calling `NVIC_SetPriority(SysTick_IRQn, 12)` is correct and does the right thing. Writing `NVIC->IP[SysTick_IRQn]` by hand is not, because the index is negative.

Three consequences:

- **`SysTick` resets to the *least* urgent priority** on most vendor startup paths (`SysTick_Config()` sets it to the maximum value), which is the opposite of the reset default for peripheral interrupts. If your tick is being delayed, that is why.
- **`PendSV` belongs at the least urgent level**, always. It is the standard place to run deferred work and, under an RTOS, the context switch — and putting anything below it means that work can never complete.
- **`HardFault` cannot be given a configurable priority at all.** It sits at −1, above everything you can configure, which is what makes it able to report on a failure inside any handler.

## Which interrupts may nest

Nesting is allowed automatically between any two different preempt levels — you do not opt in, you opt out by giving things the same level. So the real design question is which pairs you *forbid* from nesting, by flattening them onto one level.

Reasons to flatten:

- **They share data.** Two handlers at the same preempt priority cannot interrupt each other, which is a free mutual exclusion between them — no masking, no cost, no bug. This is the cheapest synchronisation mechanism on the part and it is under-used.
- **Stack depth.** Each nesting level costs 32 bytes, or 104 with FP context, on top of whatever the handler itself uses. Eight distinct levels all active at once is 256 bytes of frames before any locals. The nasty part is that stack overflow on this part is not a fault by default — it is a quiet write past the end of the region into whatever is next. Budget the worst case: the deepest chain of distinct preempt levels that can genuinely be in flight together, times frame size, plus each handler's own frame.
- **Reentrancy.** A handler that is pre-empted by *another instance of a shared driver* is the classic way to corrupt peripheral state. Two SPI-using handlers at different levels means the urgent one can start a transaction in the middle of the other's transaction.

Reasons to allow it:

- **One deadline is genuinely shorter than another handler's execution time.** That is the whole reason preemption exists. If your control loop must respond in 50 µs and the logging handler takes 200 µs, they must be at different levels and there is no other answer.

The default `PRIGROUP` on this part gives you 16 preempt levels, so flattening is a decision you make, not one the hardware makes for you.

## The ceiling that `BASEPRI` imposes

[Critical Sections and Atomicity](../04-bare-metal-programming/critical-sections-and-atomicity.md) establishes the mechanism and the discipline that comes with it: a `BASEPRI` threshold splits the system into interrupts that keep running during every critical section — and must therefore touch no protected state — and interrupts that are maskable and may. What that page leaves open is the question this one has to answer: **where in your numbering do you put the line, and what does putting it there cost?**

Two design consequences follow, and neither is a property of the mechanism.

**The ceiling has to be a number in your scheme, decided before the first interrupt is assigned.** In the band table above it sits at 5, between Control and Fast I/O, which is why levels 0 and 2 are documented as "touches no shared state" — that restriction is not a property of those interrupts, it is the price of putting them above the line. Move the line and the restriction moves with it. Deciding it late means auditing every handler you already wrote.

**Keep a spare level on the unmaskable side.** Level 4 in the table has no occupant on purpose. With the ceiling at 5, levels 0, 2 and 4 are the interrupts no critical section can delay, and 4 is the slot for the one you discover six months in — something that must not wait for a lock but does not belong beside the emergency stop. Without a spare there, the only way to add it is to renumber the safety band, which is the change you least want to be making late.

The ceiling also sets a floor on latency for everything maskable, which is the number you carry into a budget:

> worst-case added latency for any interrupt at or above the threshold = the longest critical section anywhere in the program, including inside the vendor HAL and inside the kernel.

That is a number you have to go and find, not one you can assume. A HAL function that disables interrupts around a multi-register peripheral update is invisible in your source and fully present in your latency.

:::warning[The sub-priority field that does nothing, and the interrupt that quietly sits at level 0]
Two configuration mistakes that produce a system which appears to have a priority design and does not.

**The sub-priority that is not there.** CubeMX's NVIC dialog offers a "preemption priority" and a "sub priority" box for every interrupt, and with the default `NVIC_PRIORITYGROUP_4` the second box has no effect whatsoever — all four implemented bits are preempt bits, and the sub-priority bits it writes are unimplemented and read back as zero. Teams set "preempt 5, sub 0" and "preempt 5, sub 1" believing they have ordered two interrupts, and what they actually have is two interrupts at the same level, tie-broken by exception number, permanently. The symptom is a rare ordering-dependent bug that reverses when you rename a peripheral in CubeMX and the IRQ numbers shift. Check it in the debugger: read `SCB->AIRCR` bits `[10:8]` and `NVIC->IP[irq]` for the two interrupts. If the two `IP` bytes are equal, the sub-priority did nothing.

**The interrupt nobody gave a priority.** Every interrupt is at 0 — the most urgent — until something sets it. Add a peripheral late in the project, enable it in the NVIC, forget the `NVIC_SetPriority` call, and its handler now pre-empts your motor control loop. Nothing warns you; the system works, slightly worse, in a way that only shows up as jitter under load. The tell in a debugger is `NVIC->IP[irq] == 0` for something that should not be urgent, and the durable fix is a single init function that sets *every* priority from a table and is the only place `NVIC_EnableIRQ` is ever called.
:::

## See also

- [Interrupt Latency](./interrupt-latency.md) — the budget this page's preemption term feeds into, and how to measure the result.
- [Deferred Work](./deferred-work.md) — how to make a handler short enough that its priority stops mattering so much.
- [The NVIC](../02-processor-architecture/the-nvic.md) — the priority registers, the full `PRIGROUP` table, and the enabled/pending/active state machine underneath all of this.
- [Critical Sections and Atomicity](../04-bare-metal-programming/critical-sections-and-atomicity.md) — `BASEPRI` as a mechanism, the pre-shift it requires, and the save-and-restore form.
- [Interrupt Handlers in C](../04-bare-metal-programming/interrupt-handlers-in-c.md) — the handler side: naming, flag clearing, and what must never appear inside one.

## References

- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), Rev 10. §2.3.5 for the priority ordering rule that makes lower numbers more urgent; §4.4.8–§4.4.10 for `SHPR1`–`SHPR3`, the system-handler priority registers that hold `SysTick`, `PendSV` and `SVCall` rather than the NVIC's `IPR` array; §4.4.5 for `AIRCR` and the `PRIGROUP` field whose trade-off this page's scheme is built around.
- Arm — [***Armv7-M Architecture Reference Manual***](https://developer.arm.com/documentation/ddi0403/latest/) (DDI 0403E.e). §B1.5.4 for execution priority and the exact definition of when a pending exception pre-empts; §B3.2 for the priority-grouping definition, which is where "sub-priority never causes preemption" is normative rather than descriptive.
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), Rev 4. §10.1.1 for this device's 16 programmable priority levels and its maskable channel count; **Table 37** for the interrupt position numbers that break ties when two exceptions share a priority.
- Arm — [**CMSIS-Core (Cortex-M) documentation**](https://arm-software.github.io/CMSIS_6/latest/Core/index.html). `NVIC_SetPriority`, `NVIC_SetPriorityGrouping`, `NVIC_EncodePriority` and the `__NVIC_PRIO_BITS` device macro — worth reading rather than only calling, because the shift they perform is the difference between the 0–15 scale and the register contents.
