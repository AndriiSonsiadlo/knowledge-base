---
id: arm-cortex-m-profiles
title: The Cortex-M Family
sidebar_label: The Cortex-M Family
sidebar_position: 1
tags: [embedded, cortex-m, arm, architecture, stm32]
---

# The Cortex-M Family

Arm does not sell chips. It sells processor designs, and a silicon vendor — ST, NXP, Nordic, Raspberry Pi — licenses one, wraps it in memory and peripherals, and sells you the result. That arrangement is why "it's an Arm chip" tells you almost nothing on its own, and why the useful question is always *which* Arm core, in *which* configuration, from *which* vendor.

The first cut is the **profile**. Arm splits its 32-bit and 64-bit application processor lines into three, and the letters are not marketing: they name genuinely different architectures with different exception models, different register sets and different guarantees.

- **A — Application.** Runs a general-purpose OS. Has a memory management unit, virtual memory, and multiple exception levels. This is the Cortex-A in a phone or a Raspberry Pi.
- **R — Real-time.** Application-class performance with hard-real-time guarantees: memory protection instead of translation, tightly-coupled memories, and bounded interrupt latency. Cortex-R sits in storage controllers and safety-critical automotive.
- **M — Microcontroller.** The smallest and the most deterministic. No MMU, no virtual memory, a single instruction set, a hardware-vectored interrupt controller, and a memory map fixed by the architecture rather than by the vendor.

The M profile exists because the other two are the wrong shape for a microcontroller. A chip that has to respond to an edge in under a microsecond, boot in milliseconds, and cost a dollar cannot afford page tables, cannot afford a software interrupt dispatcher, and cannot afford the two instruction sets that Cortex-A carries. What Arm did instead was strip the model down to something you can hold in your head — and that stripping-down is the reason this whole folder is possible at all. On a Cortex-M you can genuinely know what the processor is doing.

:::info[Prerequisites]
[Microcontroller, Microprocessor, SoC](../00-overview/microcontroller-vs-microprocessor-vs-soc.md) draws the MCU/MPU line this page's A-versus-M split refines. The general theory of pipelines, instruction sets and the fetch-decode-execute cycle is owned by [CPU Architecture](../../computer-science/cpu-architecture/intro.md) — [Pipelining](../../computer-science/cpu-architecture/pipelining.md) in particular explains what "three-stage" in the table below actually buys.
:::

## What the M profile fixes, and what it leaves to the vendor

Three things are worth naming up front, because they are the reason Cortex-M knowledge transfers between vendors in a way that, say, 8-bit knowledge never did.

**The memory map is architectural.** Armv7-M defines eight 0.5 GB partitions with fixed names, fixed default memory types and fixed execute-never attributes — code at `0x00000000`, SRAM at `0x20000000`, peripherals at `0x40000000`, system space at `0xE0000000` (*Armv7-M ARM*, DDI 0403E.e, §B3.1, Table B3-1). A vendor populates those regions; it does not move them. [The Cortex-M Memory Map](./memory-map-and-bit-banding.md) works through the consequences.

**The core peripherals are Arm's.** The interrupt controller, the system timer, the system control block and the memory protection unit live inside the 1 MB Private Peripheral Bus at `0xE0000000`, at addresses the architecture specifies (*Armv7-M ARM* §B1.3: "the architecture assigns a 4KB block, `0xE000E000` to `0xE000EFFF`, as the System Control Space (SCS)"). Your SysTick code is identical on an STM32 and an nRF52. Your UART code is not.

**There is exactly one instruction set.** Cortex-M executes Thumb and nothing else — see [Thumb-2 and Code Density](./thumb-and-instruction-sets.md). There is no ARM state to switch into and no interworking to get wrong.

What the vendor chooses is everything else: how much flash and RAM, which peripherals, how many interrupt lines are wired up, how many priority bits are implemented, and — critically — which *optional* parts of the core are present. An FPU, an MPU, a cache and TrustZone are all configuration options at license time. Two chips with the same core name can differ on every one of them.

## The eight cores, compared

Every entry below comes from Arm's own product-support page for that processor on developer.arm.com; "optional" means Arm's page marks it optional, which means a specific silicon vendor may or may not have taken it.

| Core | Architecture | Pipeline | FPU | DSP / SIMD | MPU | TrustZone | Bit-banding |
|---|---|---|---|---|---|---|---|
| **Cortex-M0** | Armv6-M | 3-stage | — | — | — | — | — |
| **Cortex-M0+** | Armv6-M | 2-stage | — | — | optional, up to 8 regions | — | — |
| **Cortex-M3** | Armv7-M | 3-stage | — | — | optional, up to 8 regions | — | **yes** |
| **Cortex-M4** | Armv7E-M | 3-stage | optional, single-precision | **yes** | optional, up to 8 regions | — | **yes** |
| **Cortex-M7** | Armv7E-M | 6-stage superscalar, branch prediction | optional: none / single / single+double | **yes** | optional, 8 or 16 regions | — | — |
| **Cortex-M23** | Armv8-M Baseline | 2-stage | — | — | optional, up to 16 regions | optional | — |
| **Cortex-M33** | Armv8-M Mainline | 3-stage | optional, single-precision | optional | optional, up to 16 regions | optional | — |
| **Cortex-M55** | Armv8.1-M | 4-stage integer | optional, fp16 / fp32 / fp64 | yes, plus optional Helium vector extension | optional, up to 16 regions | optional | — |

Two columns deserve reading twice.

**The FPU column is "optional" on every core that has one at all.** Arm's Cortex-M4 page says "Optional single precision floating-point unit IEEE 754 compliant"; the Cortex-M7 page offers "choices of none, single precision only, and single and double precision"; the Cortex-M33 page says "Optional single precision floating point unit". "Cortex-M4" on a datasheet does not tell you there is an FPU. ST is unusually clear about this — its documents call the part's core "Cortex-M4 with FPU" throughout, and RM0383 Rev 4 uses that exact phrase in the ART accelerator description (§3.4.2) and in the interrupt chapter (§10.1.1, "not including the 16 interrupt lines of Cortex-M4 with FPU").

**The bit-banding column is not a typo.** It appears on the Cortex-M3 and Cortex-M4 pages ("Integrated Bit-field Processing Instructions and Bus Level Bit Banding" and "Integrated Bit Field Processing Instructions & Bus Level Bit Banding" respectively) and *not* on the Cortex-M7 page, whose Bit Manipulation row reads "Integrated Bit-Field Processing Instructions" and stops there. That absence is deliberate and ST states the consequence outright — PM0253 Rev 6 §3.1.1: "The code designed for other Cortex-M processors is compatible with Cortex-M7 as long as it does not rely on bit-banding." [The Cortex-M Memory Map](./memory-map-and-bit-banding.md) goes into it.

Two things the table cannot show:

- **Interrupt capacity and priority resolution vary widely.** Armv6-M cores (M0, M0+) and the Armv8-M Baseline M23 support up to 32 interrupts with **4 priority levels**; M3, M4 and M7 support up to 240 interrupts with 8 to 256 priority levels; M33 and M55 go to 480. On any given chip the vendor implements fewer than the maximum. The STM32F411 wires up "52 maskable interrupt channels" and implements "16 programmable priority levels (4 bits of interrupt priority are used)" (RM0383 Rev 4, §10.1.1).
- **Cache and tightly-coupled memory arrive with the M7.** Arm's Cortex-M7 page lists an optional 0–64 KB instruction cache, 0–64 KB data cache, and up to 16 MB each of instruction and data TCM. That is a real performance jump and a real determinism problem at the same time; [CPU Caches](../../computer-science/memory-hierarchy/cpu-caches.md) covers the mechanism, and the DMA-versus-cache coherency trap it creates is a later folder's subject.

## Reading a part number

The line from Arm's catalogue to the chip in your hand runs through the vendor's naming scheme, and every vendor has its own. ST spells its scheme out in DS10314 Rev 8, Table 87 "Ordering information scheme", which decodes `STM32F411RE` field by field:

| Field | In `STM32F411RE` | The datasheet's own gloss |
|---|---|---|
| Device family | `STM32` | "Arm-based 32-bit microcontroller" |
| Product type | `F` | "General-purpose" |
| Device subfamily | `411` | "411 family" |
| Pin count | `R` | "64 pins" |
| Flash memory size | `E` | "512 Kbytes of flash memory" |

Note what the scheme does *not* encode: nowhere in the part number is the core named. `F4` is a series designation, not a promise of a Cortex-M4 with any particular configuration — you get the core from the description section, which for this part says "The Arm Cortex-M4 with FPU 32-bit RISC processor… Its single precision FPU (floating-point unit)…" (DS10314 Rev 8, §3.1). And the core name is where the optional features have to be resolved from the vendor's documents, not from the Arm page. For this section's target board the answer is: **Cortex-M4 with a single-precision FPU, an eight-region MPU, no cache, no TrustZone, four implemented priority bits.** The FPU and MPU facts come from PM0214 Rev 10 — its §4.6 documents the floating-point unit and coprocessor access control registers, and its §4.2.5 gives `MPU_TYPER` a reset value of `0x0000 0800`, whose `DREGION` field of `0x08` means "Eight MPU regions" (the same table defines `0x00` as "MPU not present"). The priority-bit count comes from RM0383 Rev 4 §10.1.1.

This is the workflow to internalise: **Arm's page tells you what the core can be; the vendor's reference manual and programming manual tell you what it is.**

:::warning["Cortex-M4" on the box does not mean an FPU, and getting this wrong costs a build or a HardFault]
The FPU is a license-time option, and two failure modes follow from assuming it is there.

The first is a link failure that reads like a toolchain bug. Build with `-mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard` for a part with no FPU and you get an object file whose ABI says floating-point arguments travel in FPU registers; the C library you link against was built soft-float; the linker refuses to combine them and complains about incompatible floating-point ABIs rather than about a missing FPU. The message never mentions the actual mistake.

The second is worse because it builds cleanly. On a part that *does* have an FPU — including this board's STM32F411 — the FPU is **disabled at reset**. The Armv7-M reset sequence sets `CPACR.cp10 = '00'` and `CPACR.cp11 = '00'` (*Armv7-M ARM* §B1.5.5 reset pseudocode), and PM0214 Rev 10 §4.6.1 defines `0b00` for those fields as "Access denied. Any attempted access generates a NOCP UsageFault." So the first floating-point instruction your program executes faults, typically escalating to HardFault, at an address that has nothing obviously to do with floating point. Startup code has to enable coprocessors 10 and 11 before `main` — which is exactly why the fault turns up when you hand-write startup code and not when you use the vendor's.

And a third, quieter one: the Cortex-M4 FPU is **single-precision only**. A stray `double` literal, or a call to `sin()` rather than `sinf()`, drops silently into a software floating-point library that is both large and slow. The compiler will not warn you.
:::

## Which of these you will actually meet

Written in 2026, the practical distribution looks like this. **Cortex-M0+** dominates the very cheap and the very low-power end. **Cortex-M4** is the workhorse of the mid-range and the one most tutorials, most vendor examples and most of this section assume. **Cortex-M7** appears where throughput matters — audio, motor control, graphics — and brings caches and their determinism problems with it. **Cortex-M33** is where new security-conscious designs go, because TrustZone is only available from Armv8-M onwards. **Cortex-M55** and its Helium vector extension are the machine-learning-on-microcontrollers story.

The good news for learning is that the differences are concentrated in the optional features. The register model, the exception model, the vector table, the stack frame and the memory map are shared across all of them, with the Armv8-M cores adding to that model rather than replacing it. Everything in the next five pages of this folder is knowledge that transfers.

## See also

- [The Register Model](./cortex-m-register-model.md) — the register set every core in the table above shares, and what the FPU option adds to it.
- [The Cortex-M Memory Map](./memory-map-and-bit-banding.md) — the architectural address map, and the bit-banding column of the table above worked out properly.
- [Thumb-2 and Code Density](./thumb-and-instruction-sets.md) — the single instruction set, and what Armv7E-M's "E" adds over Armv7-M.
- [Microcontroller, Microprocessor, SoC](../00-overview/microcontroller-vs-microprocessor-vs-soc.md) — the A-profile side of the split this page opens with.
- [Pipelining](../../computer-science/cpu-architecture/pipelining.md) — what the pipeline-depth column means, and why a 6-stage superscalar core is harder to reason about in real time.

## References

- Arm — [**Cortex-M0**](https://developer.arm.com/Processors/Cortex-M0), [**Cortex-M0+**](https://developer.arm.com/Processors/Cortex-M0-Plus), [**Cortex-M3**](https://developer.arm.com/Processors/Cortex-M3), [**Cortex-M4**](https://developer.arm.com/Processors/Cortex-M4), [**Cortex-M7**](https://developer.arm.com/Processors/Cortex-M7), [**Cortex-M23**](https://developer.arm.com/Processors/Cortex-M23), [**Cortex-M33**](https://developer.arm.com/Processors/Cortex-M33) and [**Cortex-M55**](https://developer.arm.com/Processors/Cortex-M55) product-support pages, retrieved 2026-08-19. Every cell of the comparison table is taken from the Specifications block of the corresponding page — the Architecture, Pipeline, Floating-Point Unit, DSP Extension, Memory Protection, Software Security and Bit Manipulation rows. Note that these pages describe the *processor IP*, so "optional" is a statement about what a silicon vendor may configure, not about what your chip has.
- Arm — [***Armv7-M Architecture Reference Manual***](https://developer.arm.com/documentation/ddi0403/latest/), consulted at **DDI 0403E.e (ID021621)**. §B3.1 "The system address map" and Table B3-1 for the architectural memory map claim; §B1.3 for the PPB and System Control Space assignment; §B1.5.5 reset pseudocode for `CPACR.cp10`/`cp11` resetting to `00`. Bit-banding appears nowhere in this document, which is itself the evidence that it is a processor-implementation feature rather than an architectural one.
- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), consulted at **Rev 10** (March 2020). §4.2.5 for `MPU_TYPER` and its `DREGION` encoding; §4.6 for the FPU and §4.6.1 for the `CPACR` access-denied encoding behind the NOCP UsageFault.
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). §10.1.1 for the interrupt-channel count and implemented priority bits; §3.4.2 for the "Cortex-M4 with FPU" naming.
- STMicroelectronics — [**STM32F411xC/E datasheet**](https://www.st.com/resource/en/datasheet/stm32f411re.pdf) (DS10314), consulted at **Rev 8** (January 2024). Table 87 "Ordering information scheme" for the part-number decode; §3.1 for the core description and the single-precision FPU.
- STMicroelectronics — [**PM0253**, *STM32F7 and STM32H7 series Cortex-M7 processor programming manual*](https://www.st.com/resource/en/programming_manual/pm0253-stm32f7-series-and-stm32h7-series-cortexm7-processor-programming-manual-stmicroelectronics.pdf), consulted at **Rev 6** (May 2026). §3.1.1 "Binary compatibility with other Cortex processors" for the explicit statement that Cortex-M7 code compatibility holds only for software that does not rely on bit-banding.
