---
id: glossary
title: Glossary
sidebar_label: Glossary
sidebar_position: 6
tags: [embedded, overview, glossary]
---

# Glossary

Embedded engineering has its own vocabulary, and a lot of it is acronyms that mean something quite specific in this field even when the letters look familiar from elsewhere. The problem isn't that the terms are hard — it's that skimming past one you half-recognize (assuming "MPU" means the same thing every time, or that "RTOS" is just "a small OS") is exactly how a plausible-but-wrong mental model gets built, and those are expensive to unlearn once you've written code around them. This page defines the terms every later folder in this section assumes you already know, once, in one place, so you can look one up instead of re-deriving it from context. Where a term's proper home is a folder that doesn't exist in this build yet, it's still defined here — it just isn't linked anywhere yet.

## The terms

**MCU — microcontroller unit.** A chip that integrates a CPU core, flash memory for code, and SRAM for data all on one die, with no external memory bus required. See [Microcontroller, Microprocessor, SoC](./microcontroller-vs-microprocessor-vs-soc.md) for the full picture, including on-chip vs. external memory.

**MPU — this acronym means two unrelated things, and mixing them up is one of the most common points of confusion for newcomers.** On a microcontroller, MPU means **memory protection unit** — a small piece of hardware (8–16 regions on most Cortex-M parts) that allow/deny-lists fixed *physical* address ranges, with no address translation involved. As a product category, MPU also means **microprocessor unit** — a chip like an applications-class Arm Cortex-A part that runs code from external memory and includes an MMU. The two things share nothing but the abbreviation; always check context. Both senses, and why they're easy to confuse, are covered in [Microcontroller, Microprocessor, SoC](./microcontroller-vs-microprocessor-vs-soc.md).

**MMU — memory management unit.** Hardware that translates virtual addresses to physical ones and enforces per-process memory isolation — the mechanism a full operating system's virtual memory and process model are built on. Microcontrollers generally don't have one; microprocessors and SoCs capable of running Linux do. See [Virtual Memory and Paging](../../computer-science/memory-hierarchy/virtual-memory-and-paging.md) for how the translation itself works.

**HAL — hardware abstraction layer.** A vendor-supplied (or occasionally self-written) library that wraps direct register access behind function calls — `HAL_GPIO_WritePin()` instead of writing a bit into a GPIO output data register directly. Trades a small amount of code size and sometimes timing predictability for portability and much faster development. Covered in depth once the toolchain and bare-metal folders of this section are published.

**BSP — board support package.** The collection of startup code, linker script, pin/clock configuration, and drivers specific to one particular board (as opposed to just the chip on it) — the layer that lets the same application code run on different boards carrying the same or similar microcontrollers. Covered alongside the toolchain material later in this section.

**ISR — interrupt service routine.** The function that runs when a hardware interrupt fires, interrupting whatever the CPU was doing to service the event immediately. General interrupt-handling theory — including how an ISR gets invoked and what a handler is expected to do — is covered in [I/O & Interrupts](../../computer-science/buses-and-io/io-and-interrupts.md); this section's later folders add the Cortex-M-specific mechanics on top.

**NVIC — nested vectored interrupt controller.** The Cortex-M core's built-in interrupt controller: it prioritizes interrupts, supports nesting (a higher-priority interrupt can preempt a lower-priority one already running), and dispatches directly to a handler address without software having to poll a status register first. Specific to Arm Cortex-M; covered once the processor-architecture and interrupts folders of this section are published.

**SWD — Serial Wire Debug.** Arm's 2-wire debug protocol (clock plus bidirectional data) used to program and debug Cortex-M microcontrollers — the interface most Cortex-M debug probes (like ST-Link) use by default. Covered alongside JTAG once the debugging folder of this section is published.

**JTAG — Joint Test Action Group.** An industry-standard 4- or 5-wire hardware debug and boundary-scan interface, older and more general-purpose than SWD, still common on more complex SoCs and for board-level manufacturing test. Covered alongside SWD once the debugging folder of this section is published.

**RTOS — real-time operating system.** A small operating system built around a preemptive, priority-based scheduler with bounded, reasoned-about timing behavior — not a scaled-down desktop OS. FreeRTOS and Zephyr are the two this section covers. See [Bare-Metal, RTOS, or Linux](./bare-metal-vs-rtos-vs-linux.md) for when reaching for one is (and isn't) the right call.

**Tick.** The periodic timer interrupt an RTOS uses as its scheduling heartbeat — each tick, the scheduler gets a chance to decide whether to switch which task is running. Tick rate is a real design parameter: a faster tick gives finer-grained scheduling and timeout resolution at the cost of more CPU time spent in the scheduler itself. Covered in depth once the RTOS folder of this section is published.

**WCET — worst-case execution time.** The longest amount of time a piece of code could possibly take to run, accounting for the worst plausible combination of branches, cache misses, and pipeline stalls — not the typical or average time. Hard real-time systems are designed and proven against WCET, not against measured average-case performance, because a system that's fast on average but occasionally blows its deadline is still wrong. Covered in depth once the interrupts-and-real-time folder of this section is published.

**Jitter.** The variation in *when* a periodic event actually happens relative to when it was supposed to happen — a control loop meant to run every 1 ms that actually fires anywhere from 0.9 ms to 1.3 ms apart has 0.4 ms of jitter. Jitter can be tolerable where absolute latency isn't, and intolerable where it is, depending entirely on what the timing is driving. Covered in depth once the interrupts-and-real-time folder of this section is published.

**Brownout.** A supply voltage that sags below the level a chip needs to operate correctly, but doesn't drop all the way to zero — the dangerous case, because logic can behave unpredictably (partial resets, corrupted flash writes, garbled register states) rather than cleanly stopping. Most microcontrollers include a brownout detector that forces a clean reset once supply voltage crosses a threshold specifically to turn this failure mode into a predictable one. Covered alongside power topics once the hardware-foundations folder of this section is published.

**XIP — execute in place.** Running code directly out of flash memory, instruction by instruction, without first copying it into RAM. Most microcontrollers execute this way by default, which is part of why they can start running code microseconds after reset rather than needing a load step first. Covered alongside the boot and startup material once the toolchain and bare-metal folders of this section are published.

**OTA — over-the-air (update).** A firmware update delivered to a device wirelessly after it has shipped, rather than requiring a physical connection. Far from universal in embedded products — many shipped devices have no update mechanism at all — and where it exists, it's treated as a high-stakes, carefully tested release path rather than a routine deploy, because a failed update on inaccessible hardware can mean a permanently bricked device. Covered in depth once the firmware-lifecycle folder of this section is published.

**SIL — Safety Integrity Level.** A discrete risk-reduction rating (defined by IEC 61508) that a safety function must meet, from SIL 1 (lowest) to SIL 4 (highest), driving how rigorously that function must be designed, verified, and documented. Covered once the safety-and-reliability folder of this section is published.

**ASIL — Automotive Safety Integrity Level.** ISO 26262's automotive-specific equivalent of SIL, rated QM (no safety requirement) then A through D (highest), assigned per hazard based on severity, exposure, and controllability. Covered once the safety-and-reliability folder of this section is published.

**Devicetree.** A data structure (and the text-format `.dts` files that describe it) used to describe hardware — which peripherals exist, their addresses, and how they're wired — so the same kernel or firmware binary can support different boards by loading a different devicetree rather than being recompiled per board. Most associated with embedded Linux, but just as central to Zephyr, which this section also covers. Covered once the embedded-Linux folder of this section is published.

**`no_std`.** A Rust attribute that opts a program out of Rust's standard library (which assumes an OS underneath it — heap allocation, threads, file I/O) in favor of just `core`, the subset that works with no operating system present at all. The mechanism that makes Rust usable for bare-metal embedded firmware. Covered once the languages-and-practice folder of this section is published.

## The full list at a glance

| Term | Meaning | Home in this section |
|---|---|---|
| MCU | Microcontroller unit — CPU, flash, and SRAM on one die | [MCU vs MPU vs SoC](./microcontroller-vs-microprocessor-vs-soc.md) |
| MPU | Memory protection unit **or** microprocessor unit — two unrelated meanings | [MCU vs MPU vs SoC](./microcontroller-vs-microprocessor-vs-soc.md) |
| MMU | Memory management unit — virtual-to-physical translation and isolation | Outside this section — [Virtual Memory and Paging](../../computer-science/memory-hierarchy/virtual-memory-and-paging.md) |
| HAL | Hardware abstraction layer over direct register access | Not yet published |
| BSP | Board support package — board-specific startup, drivers, config | Not yet published |
| ISR | Interrupt service routine | Outside this section — [I/O & Interrupts](../../computer-science/buses-and-io/io-and-interrupts.md) |
| NVIC | Cortex-M's nested vectored interrupt controller | Not yet published |
| SWD | Serial Wire Debug — Arm's 2-wire debug protocol | Not yet published |
| JTAG | Industry-standard hardware debug/boundary-scan interface | Not yet published |
| RTOS | Real-time operating system with a preemptive, bounded scheduler | [Bare-Metal, RTOS, or Linux](./bare-metal-vs-rtos-vs-linux.md) |
| Tick | The RTOS's periodic scheduling-heartbeat interrupt | Not yet published |
| WCET | Worst-case execution time | Not yet published |
| Jitter | Variation in the timing of a periodic event | Not yet published |
| Brownout | A supply sag that doesn't fully lose power, but corrupts behavior | Not yet published |
| XIP | Execute in place — running code directly from flash | Not yet published |
| OTA | Over-the-air firmware update | Not yet published |
| SIL | Safety Integrity Level (IEC 61508) | Not yet published |
| ASIL | Automotive Safety Integrity Level (ISO 26262) | Not yet published |
| Devicetree | Hardware-description data structure used by embedded Linux and Zephyr alike | Not yet published |
| `no_std` | Rust without the OS-dependent standard library | Not yet published |

:::warning
Don't assume "MPU" means the same thing every time you see it, including within a single vendor's documentation. Reading "the MPU" in a Cortex-M reference manual and carrying that meaning (a fixed-region physical protection unit) into a sentence about an "MPU" product line (a full microprocessor with an MMU) — or the reverse — produces a genuinely wrong belief about what the hardware can do, and it's one of the most common mix-ups newcomers to this field make. When in doubt, check whether the sentence is talking about a *feature on a microcontroller* or a *category of chip*.
:::

## See also

- [Microcontroller, Microprocessor, SoC](./microcontroller-vs-microprocessor-vs-soc.md) — the MCU/MPU/MMU/SoC distinction this glossary's most confusable entries come from.
- [Bare-Metal, RTOS, or Linux](./bare-metal-vs-rtos-vs-linux.md) — RTOS, tick, and jitter in the context of the decision they actually drive.
- [What "Embedded" Actually Means](./what-embedded-means.md) — why this many acronyms exist in the first place: real constraints that needed names.
- [Embedded Systems](../readme.md) — the section index and its four learning paths.

## References

- Arm, *Cortex-M4 Devices Generic User Guide* (document DUI0553), publisher Arm Limited — the Arm reference that defines the NVIC and the MPU in the same terms used throughout this glossary; cited by title rather than linked because the specific document URL Arm serves this from changes across doc-version updates.
- Joseph Yiu, *The Definitive Guide to Arm Cortex-M3 and Cortex-M4 Processors* — covers MCU, MPU, MMU, NVIC, SWD, and JTAG at the level of detail this glossary summarizes, written by an Arm architect.
- FreeRTOS — [RTOS concepts and terminology](https://www.freertos.org/features.html) — the source for this glossary's tick and RTOS definitions, from the kernel's own documentation.
- IEC 61508 and ISO 26262 (the standards themselves, paywalled documents) — the normative sources for the SIL and ASIL definitions above; this glossary summarizes their intent rather than reproducing normative text.
- The Rust Embedded Working Group — [The Embedded Rust Book](https://docs.rust-embedded.org/book/) — the primary source for `no_std` and what it means to write Rust with no operating system underneath it.
