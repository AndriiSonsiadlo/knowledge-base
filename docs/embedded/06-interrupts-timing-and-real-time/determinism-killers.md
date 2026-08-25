---
id: determinism-killers
title: Determinism Killers
sidebar_label: Determinism Killers
sidebar_position: 9
tags: [embedded, cortex-m, real-time, determinism, wcet, flash, dma, stm32]
---

# Determinism Killers

Almost every mechanism that makes a computer fast makes it less predictable, and the trade is usually invisible in source code. Caches, prefetchers, branch speculation, bus arbitration and dynamic memory allocation are all bets on history repeating: they are fast when the recent past resembles the present and slow when it does not. In a throughput-oriented system that is an unambiguously good bargain. In a system with deadlines it means the number you have to defend — the worst case — is set by the *unlucky* path through every one of them, while every measurement you take is dominated by the lucky one.

The mental model: **a determinism killer is any mechanism whose duration depends on something other than the code you are looking at.** History, data values, what another bus master is doing, how many times an interrupt happened to fire. That dependency is exactly what makes it impossible to read a worst case off the page, and dealing with it is either bounding it (put a documented ceiling on the dependency) or removing it (turn the mechanism off and pay the average-case cost).

[Interrupt Latency](./interrupt-latency.md) enumerates the contributors to the delay before a handler starts — instruction completion, stacking, vector fetch, flash wait states, higher-priority preemption and your own critical sections. This page is the other half of that picture and does not repeat the list. It asks a different question of each mechanism: **what does it do to the worst case specifically, and can that be bounded?**

:::info[Prerequisites]
[Worst-Case Execution Time](./wcet.md) establishes why the maximum matters and why measurement cannot establish it — this page is the catalogue of reasons the measured maximum and the true maximum diverge. [Interrupt Latency](./interrupt-latency.md) owns the latency chain itself. [CPU Caches](../../computer-science/memory-hierarchy/cpu-caches.md) owns cache theory: lines, associativity, replacement policy, hit and miss costs.
:::

## The catalogue

Each mechanism against what it does to the average case, what it does to the *worst* case, and whether you can do anything about it. Rows marked "not on this part" are here because they dominate the literature and you need to know they do not apply to a NUCLEO-F411RE.

| Mechanism | Effect on average | Effect on the worst case | Bounded? Disable? |
|---|---|---|---|
| **Flash wait states** | Constant penalty on every miss | **3 wait states per access at 100 MHz** — constant, documented, fully bounded | Cannot disable. Reduce by lowering HCLK or by running code from SRAM |
| **ART accelerator** (instruction cache, literal cache, prefetch) | Large improvement on hot code | **Unchanged** — a miss costs exactly what no ART costs. The harm is that measurements stop representing the bound | Disable via `FLASH_ACR`, or reset the cache before each timing run |
| **L1 I/D caches** | Very large improvement | Miss penalty plus line fill; plus DMA coherency hazards | **Not on this part.** Cortex-M7 only — STM32F7, STM32H7 |
| **Branch / pipeline refill** | Small improvement | A few cycles of pipeline refill per taken branch. Small and bounded on Cortex-M4 | Nothing to do. Not a real problem here |
| **DMA bus contention** | Improves system throughput enormously | Core stalls for the duration of a competing DMA burst on the same bus slave | Bound by burst length; separate slaves where the part allows it |
| **Interrupt storms** | None | **Unbounded.** Arrival rate with no ceiling means interference with no ceiling | Bound by enforcing a minimum interarrival time in hardware or software |
| **Dynamic allocation** (`malloc`/`free`) | Convenient, usually fast | **Unbounded and history-dependent.** Fragmentation makes allocation time a function of everything allocated before | Remove it. Static allocation or fixed-block pools |
| **Blocking on shared resources** | None | Unbounded without a protocol; one critical section long with priority inheritance or ceiling | Bound with a protocol, then add it as the `B` term |
| **Flash program/erase while running from flash** | None | **Hundreds of milliseconds** — the core cannot fetch instructions from flash while the flash controller is busy | Relocate the routine and everything that must run during it into SRAM |
| **APB peripheral access** | None | A few core cycles per access; APB1 runs at up to 50 MHz against a 100 MHz core | Bounded and small. Count it, do not fight it |

The ordering is roughly by how much trouble each one causes in practice. The bottom half of the table contains the ones that produce genuine field failures; the top half contains the ones people spend their time worrying about.

## Flash wait states: the constant you cannot remove

At the NUCLEO-F411RE's maximum 100 MHz, every flash access that misses the ART costs **3 wait states**. RM0383 Rev 4 §3.4.1, Table 5 gives the requirement for VDD in the 2.7–3.6 V range: 0 wait states up to 30 MHz, 1 to 64 MHz, 2 to 90 MHz, 3 to 100 MHz.

This is a determinism *helper*, not a killer: it is a constant. What makes it worth a section is that it is the floor under the ART's behaviour and therefore under every sound bound on this part — the cold-cache cost of an instruction fetch is a documented number, which is unusual and useful.

Two operational points that produce bugs when missed:

- **The latency must be raised before the clock, and lowered after it.** Increasing HCLK past a boundary with `LATENCY` still at the old value means the core reads garbage from flash. RM0383 spells out the sequence, and it is one of the standard failure modes when reconfiguring the clock tree at run time — [Clock Tree Configuration](../04-bare-metal-programming/clock-tree-configuration.md) covers the full procedure.
- **Read `LATENCY` back after writing it.** The write does not take effect instantly and the reference manual's procedure has you poll for the new value before touching the clock.

## The ART accelerator: better on average, harder to bound

The STM32F411's Cortex-M4 has **no instruction cache and no data cache**. What it has is the ART accelerator, which sits in the *flash interface* rather than in the core (RM0383 Rev 4 §3.4.2): 64 lines of 128 bits for instructions, 8 lines of 128 bits for the literal pool, and a prefetch buffer that reads ahead sequentially. A 128-bit line is four to eight Thumb-2 instructions, so 64 lines is on the order of 1 KB of hot code held at zero wait states.

Be precise about what this does to timing, because it is the opposite of what people assume:

- **It does not make the worst case worse.** An ART miss costs the same as if the ART did not exist: the wait states you would have paid anyway. The bound is unaffected.
- **It makes the worst case much harder to observe.** Hot code runs at roughly four times the cold speed, so anything you measure in a loop is measuring the hit path. The gap between what you measure and what you must budget is the ART's speedup — which is exactly the quantity you cannot recover by measuring harder.
- **It cannot be modelled.** RM0383 describes the ART functionally. It does not publish a replacement policy or a timing model, so a static analyser has nothing to work with and a sound bound must assume every fetch misses. That is the honest position from [Worst-Case Execution Time](./wcet.md): the ART-cold bound is the provable one.

The controls live in one register.

```wavedrom title="FLASH_ACR, low 16 bits — the ART and wait-state controls" alt="Bit-field strip for the FLASH access control register showing LATENCY in bits 3 to 0, then PRFTEN, ICEN, DCEN, ICRST and DCRST in bits 8 to 12"
{ "reg": [
  { "bits": 4, "name": "LATENCY", "attr": "rw" },
  { "bits": 4, "name": "reserved", "type": 1 },
  { "bits": 1, "name": "PRFTEN", "attr": "rw" },
  { "bits": 1, "name": "ICEN", "attr": "rw" },
  { "bits": 1, "name": "DCEN", "attr": "rw" },
  { "bits": 1, "name": "ICRST", "attr": "rw" },
  { "bits": 1, "name": "DCRST", "attr": "rw" },
  { "bits": 3, "name": "reserved", "type": 1 }
], "config": { "bits": 16, "lanes": 1 } }
```

| Bits | Field | Meaning | Reset |
|---|---|---|---|
| 3:0 | `LATENCY` | Flash wait states, per RM0383 §3.4.1 Table 5. Must be set before raising HCLK and after lowering it | 0 |
| 7:4 | reserved | — | 0 |
| 8 | `PRFTEN` | Prefetch enable — sequential read-ahead into the buffer | 0 |
| 9 | `ICEN` | Instruction cache enable — the 64 instruction lines | 0 |
| 10 | `DCEN` | Data cache enable — the 8 literal-pool lines | 0 |
| 11 | `ICRST` | Instruction cache reset. **Writable only while `ICEN` is 0** | 0 |
| 12 | `DCRST` | Data cache reset. **Writable only while `DCEN` is 0** | 0 |

*Fields and reset values from RM0383 Rev 4, embedded flash memory chapter, `FLASH_ACR` register description (§3.5.1). The register's reset value is `0x00000000` — no wait states, no prefetch, no cache — which is correct for the 16 MHz HSI the part boots on.*

Two things you do with this register in a timing context:

```c
/* Force the ART instruction cache cold before a timing run, so the measurement
   approaches the bound instead of the hit path. RM0383 §3.5.1: ICRST may only
   be written while ICEN is 0. */
FLASH->ACR &= ~FLASH_ACR_ICEN;
FLASH->ACR |=  FLASH_ACR_ICRST;
FLASH->ACR &= ~FLASH_ACR_ICRST;
FLASH->ACR |=  FLASH_ACR_ICEN;

/* Or, for a run where repeatability matters more than speed: leave the
   accelerator off entirely. Everything gets slower and nothing varies. */
FLASH->ACR &= ~(FLASH_ACR_ICEN | FLASH_ACR_DCEN | FLASH_ACR_PRFTEN);
```

Ship with the ART enabled. Measure with it cold or disabled. Those are not in conflict — one is how the product should run and the other is how you learn what it can cost.

## Caches, on the parts that have them

If your part is a Cortex-M7 — STM32F7 or STM32H7 — you have real L1 instruction and data caches, and the timing picture changes substantially:

- A miss costs a line fill from a slower memory, and the miss *pattern* depends on the address layout of your data, so an innocuous change to a struct can change timing.
- The write-back data cache introduces a coherency problem with DMA that does not exist on this part at all. A DMA engine writing into a buffer the core has cached reads stale data; a core writing a descriptor that has not been cleaned to memory gives the DMA engine stale data. The remedies are cache maintenance operations at each handover, or marking the buffer region non-cacheable in the MPU. ST's AN4839 is written specifically about this.
- Static WCET analysis becomes hard, because cache-state modelling is the expensive part of micro-architectural analysis.

None of that applies to a NUCLEO-F411RE. If you are reading advice about `SCB_CleanDCache_by_Addr` and wondering why your DMA works without it, this is why. [CPU Caches](../../computer-science/memory-hierarchy/cpu-caches.md) covers how caches work; the point here is only which parts have them.

## Branch behaviour on this core

The Cortex-M4 does limited branch speculation in its fetch stage and has no dynamic branch predictor with a history table — that is a Cortex-M7 feature. Arm's *Cortex-M4 Technical Reference Manual* quotes branch instruction timings in the form `1 + P`, where `P` is a pipeline-refill penalty of a small number of cycles. The worst case is therefore a few cycles per taken branch, which is bounded, documented and almost never the thing that breaks a budget.

Mentioning it at all is defensive: branch prediction is a headline determinism killer on application processors, and it gets copied into embedded advice where it does not belong. On this part, count the refill and move on.

## DMA bus contention

The DMA controllers and the core are independent masters on the AHB bus matrix (RM0383 Rev 4 §2.1, system architecture). When two masters want the same slave, the matrix arbitrates, and the loser waits. That is the mechanism: **the core's execution time depends on what a DMA stream is doing at the time**, which is a dependency on something outside the code being timed.

The size of the effect is set by how long a competing master holds the bus, which is set by burst configuration. A DMA stream configured for long bursts through its FIFO moves data more efficiently and holds the bus for longer contiguous intervals; single transfers interleave better and are less efficient. That is a real, tunable trade between throughput and worst-case core stall — [DMA](../05-peripherals-and-drivers/dma.md) covers the FIFO and burst settings.

One part-specific note that changes the usual advice: **the STM32F411 has a single contiguous 128 KB SRAM block.** On parts with a core-coupled memory or multiple independently-arbitrated SRAM banks, the standard mitigation is to place CPU working data in one bank and DMA buffers in another so they never contend. That option does not exist here. What does work on this part:

- **Run the timed code from flash** so instruction fetch goes to a different slave than the DMA traffic. Relocating a hot handler into SRAM removes the flash wait states and *adds* DMA contention — measure before assuming it is a win.
- **Bound the burst size** on streams that run concurrently with deadline-carrying code.
- **Do not model DMA contention as zero.** It is small per access and it is not nothing, and it is one of the mechanisms measurement is genuinely better at capturing than analysis, because it depends on real traffic.

## Interrupt storms

This is the only row in the table whose worst case is *unbounded*, which makes it the most dangerous. An interrupt source with no ceiling on its arrival rate contributes interference with no ceiling, and no scheduling analysis can produce a response time. The analysis does not give a large answer — it gives no answer.

Sources that do this:

- A level-triggered line that stays asserted because the handler failed to clear the peripheral's flag. The handler returns, the NVIC immediately re-pends it, and the core executes that handler forever. The main loop never runs again.
- A mechanical switch on an EXTI line. Contact bounce produces many transitions during settling — measure yours on a scope rather than trusting a number, but it is a burst, not one edge.
- A UART at a high baud rate with an interrupt per byte, when the peer starts a bulk transfer.
- A sensor with an open-drain interrupt output and a fault condition that reasserts immediately.

The repairs all consist of imposing a minimum interarrival time, which is what turns the source into something a sporadic-task model can analyse:

1. **Fix it in hardware where possible.** An RC filter and a Schmitt input on a switch line removes the burst rather than coping with it.
2. **Disable and re-arm.** In the handler, mask the source in the NVIC or the peripheral and re-enable it from a timer after a defined settling interval — say 10 ms for a switch. The interarrival time is then a number you chose, which is exactly what the analysis needs.
3. **Move to DMA.** A stream of items with an interrupt per item is the case DMA exists for; one interrupt per buffer converts an unbounded rate into a bounded one ([Polling, Interrupt, or DMA](./polling-interrupt-or-dma.md)).
4. **Detect it.** Count activations per unit time in the handler and report anything implausible. A storm that trips a diagnostic is a bug report; a storm that does not is a field return with no information attached.

## Dynamic allocation and blocking

**`malloc` and `free`.** Allocation time depends on the state of the heap, which depends on every allocation and free that came before. Fragmentation makes it worse over time, and a `free` that coalesces adjacent blocks does a different amount of work depending on what its neighbours are. There is no worst case you can state, only one you have not hit yet — and the eventual failure mode is an allocation returning `NULL` after weeks of uptime, in code written by someone who assumed it could not. The newlib implementation additionally takes a lock and may call `_sbrk`, so it is not even reentrant by default. [Static Memory and No `malloc`](../04-bare-metal-programming/static-memory-and-no-malloc.md) covers the alternatives; a fixed-block pool allocator has constant-time allocation and a stateable worst case, which is the entire reason it exists.

**Blocking on shared resources.** A high-priority task waiting for a resource held by a lower-priority one is blocked from below, and without a protocol that blocking is unbounded — the classic priority inversion, where a medium-priority task preempts the holder and the high-priority task waits indefinitely. Priority inheritance or an immediate ceiling protocol bounds it to one critical section, at which point it enters response-time analysis as a single additive `B` term ([Scheduling Theory for Firmware](./scheduling-theory.md)). The general theory belongs to [Concurrency and Synchronization](../../computer-science/operating-systems/concurrency-and-synchronization.md).

:::warning[The log write that reset the board, and the button that starved the control loop]
Two determinism failures that reach the field because neither is reproducible on a desk.

**Flash erase stalls everything that executes from flash.** A logging subsystem writes records into a flash sector, and when the sector fills it erases the next one. On the STM32F411 there is no dual-bank read-while-write: while the flash controller is programming or erasing, core instruction fetches from flash stall until it finishes. A sector erase is not microseconds — the STM32F411RE datasheet (DS10314) tabulates program and erase times in its flash memory characteristics table, and for a full sector they run from hundreds of milliseconds to seconds depending on sector size and supply voltage. During that window, *every* interrupt handler whose code lives in flash is stalled too, which means the ones you most want to keep running are the ones that stop. The symptom is a watchdog reset that happens once every few days, always when the log wraps, and never on the bench because a bench session never fills a sector. The fix is to place the erase routine and everything that must remain live during it in SRAM with a linker section (a `.ramfunc`-style attribute), or simply not to erase while any deadline is live — schedule maintenance writes into a defined window. Note the second-order trap: the vector table is also in flash by default, so relocating the handler but not the table leaves you stalled on the vector fetch.

**A bouncing switch on an EXTI line at a priority above the control loop.** Contact bounce turns one press into a burst of edges over the settling interval. Each is an interrupt. If that EXTI has a numerically lower priority value than the control-loop timer — which it easily can, because nobody assigns priorities to a button deliberately — the control loop is preempted throughout the burst and misses activations. The tell is that the misbehaviour correlates with a human touching the enclosure, which nobody records in a log, so the bug report says "it glitches sometimes". Confirm it by counting EXTI activations in the handler and reading the counter over your diagnostic interface after a press: if one press produces more than one activation, you have found it. Debounce in hardware, or mask the line in the handler and re-arm from a timer after a settling interval you chose and wrote down.
:::

## What to actually do

The list, in the order that pays:

1. **Remove the unbounded ones first.** Interrupt storms, dynamic allocation and unbounded blocking are the only three rows whose worst case has no number. Everything else is arithmetic; these are the ones that make the arithmetic impossible.
2. **Bound what you cannot remove.** A minimum interarrival time, a burst-length cap, a protocol on shared resources. Each of these converts an unknown into a term.
3. **Make measurement represent the bound.** Reset or disable the ART for timing runs, drive the worst-case input deliberately, and run with the rest of the system loaded.
4. **Leave the average-case optimisations enabled in the product.** The ART and the prefetch cost nothing in the worst case and buy a great deal in the typical one. Disabling them to "improve determinism" gives up real performance for a bound you already had.

Point 4 is the one that gets argued about. Turning off the ART does not lower your worst case by a single cycle — it only makes the average approach it. That is worth doing on the bench and almost never worth shipping.

## See also

- [Worst-Case Execution Time](./wcet.md) — why the gap between measured and true worst case matters, and what each analysis method can prove about it.
- [Interrupt Latency](./interrupt-latency.md) — the latency chain this page's mechanisms feed into, term by term.
- [DMA](../05-peripherals-and-drivers/dma.md) — the FIFO and burst configuration that sets how long a competing master holds the bus.
- [Static Memory and No `malloc`](../04-bare-metal-programming/static-memory-and-no-malloc.md) — the alternatives to the one determinism killer with no upper bound at all.
- [CPU Caches](../../computer-science/memory-hierarchy/cpu-caches.md) — how caches work, for the Cortex-M7 parts where the cache rows of the table above apply.

## References

- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), Rev 4. §2.1 for the AHB bus matrix and which masters contend for which slaves; §3.4.1 Table 5 for the wait-state table and its VDD conditions; §3.4.2 for the ART accelerator's 64 instruction lines, 8 literal lines and prefetch buffer; §3.5.1 for the `FLASH_ACR` fields and the rule that `ICRST` and `DCRST` are writable only while the corresponding cache is disabled.
- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), Rev 10. §2.3 for exception entry and the NVIC re-pending behaviour behind a level-triggered interrupt storm; §4.3 for the NVIC registers used to mask a storming source.
- Arm — [***Cortex-M4 Technical Reference Manual***](https://developer.arm.com/documentation/ddi0439/latest/) (DDI 0439). The instruction-timing summary, including the `1 + P` branch notation and the pipeline-refill penalty quoted above, and confirmation of what this core does and does not contain — notably that there is no L1 cache.
- STMicroelectronics — [**AN4839**, *Level 1 cache on STM32F7 Series and STM32H7 Series*](https://www.st.com/resource/en/application_note/an4839-level-1-cache-on-stm32f7-series-and-stm32h7-series-stmicroelectronics.pdf). The document to read when your part *does* have caches: cache maintenance around DMA buffers, MPU non-cacheable regions, and the write-back coherency hazards that do not exist on an STM32F4.
- STMicroelectronics — [**DS10314**, *STM32F411xC/E datasheet*](https://www.st.com/resource/en/datasheet/stm32f411re.pdf). The flash memory characteristics table, for program and erase times by sector size and supply voltage — the figures behind the stall described in the warning above. Take them from the table for your sector size and VDD rather than from any secondary source.
- Reinhard Wilhelm et al. — [***The Worst-Case Execution-Time Problem***](https://dl.acm.org/doi/10.1145/1347375.1347389), *ACM Transactions on Embedded Computing Systems* 7(3), Article 36, April 2008. The micro-architectural analysis section explains why each of these mechanisms is hard to model soundly, and why an unmodellable accelerator forces an analyser into the pessimistic assumption used above.
