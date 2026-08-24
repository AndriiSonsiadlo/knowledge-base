---
title: Embedded Systems
sidebar_label: Overview
sidebar_position: 0
tags: [embedded, cortex-m, rtos, linux]
---

# Embedded Systems

Embedded software runs on hardware that was never meant to run much of anything: a few hundred
kilobytes of flash, no operating system by default, hard real-time deadlines a missed interrupt
can blow, and a physical world on the other side of every GPIO pin. This section covers that
discipline end to end — Cortex-M architecture and the bare-metal fundamentals, peripherals and
interrupt-driven drivers, RTOS concepts (FreeRTOS and Zephyr), the point at which embedded Linux
becomes the right answer instead of an RTOS, and the safety, security, and lifecycle concerns
that separate a prototype from a shippable product.

It does not re-teach material that already has a home elsewhere on this site. Bus protocols,
general interrupt theory, scheduling theory, CPU architecture, and bit manipulation are covered
in depth under `computer-science/`; embedded pages link out to that material and add the
register-level and Cortex-M-specific parts on top, rather than repeating it.

:::note[This section is being written]
Folders `00-overview` through `04-bare-metal-programming` are published — 51 pages covering
everything from "what embedded means" through a complete first bare-metal blink. Everything from
`05-peripherals-and-drivers` onward is planned but does not exist yet: those folders will not
appear in the sidebar until later phases land. If you came here looking for a specific topic and
it is not in the sidebar, it has not been published yet — nothing is missing or broken.
:::

:::info[How this is organised]
The section is sixteen numbered folders, `00` through `15`, each self-contained around one
theme — numeric prefixes only order them on disk, the sidebar label comes from each folder's
`_category_.json`. The full folder map (one row per folder, phrased as the question it answers)
and the reasoning behind the "link out to `computer-science/` instead of repeating it" policy
live on [How This Section Is Organised](./00-overview/how-this-section-is-organised.md) — this
page stays a short index; that one is the expanded reference.
:::

## Sections

| Folder | Covers |
|---|---|
| 📖 [`00-overview`](./00-overview/what-embedded-means.md) | What "embedded" means as a discipline, the microcontroller/microprocessor/SoC distinction, the landscape of architectures and vendors, bare-metal vs. RTOS vs. Linux, and a glossary |
| 🔧 [`01-hardware-foundations`](./01-hardware-foundations/what-hardware-to-buy.md) | Choosing hardware, schematics and board basics, power and reset behaviour, and what a datasheet actually tells you |
| 🧠 [`02-processor-architecture`](./02-processor-architecture/arm-cortex-m-profiles.md) | The Cortex-M register model, memory map and bit-banding, and the pipeline and instruction-set concerns specific to microcontroller cores |
| 🛠️ `03-toolchain-and-build` | Cross-compilers, CMake for embedded, linker scripts, ELF/map files, and the build pipeline from source to flashable image |
| ⚡ `04-bare-metal-programming` | Startup code, vector tables, register-level programming, critical sections, and your first bare-metal blink |
| 🔌 `05-peripherals-and-drivers` | GPIO, UART/SPI/I2C in depth, DMA, external memory, and flash/EEPROM emulation |
| ⏱️ `06-interrupts-timing-and-real-time` | The NVIC, timing determinism, scheduling theory as it applies to interrupts, and what breaks determinism on cores with caches |
| 🧵 `07-rtos` | Task and scheduling concepts, synchronization primitives, FreeRTOS, and Zephyr |
| 📡 `08-connectivity-and-protocols` | USB device stacks, Ethernet and TCP/IP on constrained devices, and wireless connectivity |
| 🔋 `09-low-power-design` | Sleep modes, power budgeting, and low-power peripheral design |
| 🐧 `10-embedded-linux` | When Linux is the right call, the boot chain, device drivers, and build systems (Yocto, Buildroot) |
| 🐞 `11-debugging-and-testing` | JTAG/SWD, hardfault debugging, unit testing firmware, and hardware-in-the-loop testing |
| 🛡️ `12-safety-and-reliability` | IEC 61508, ISO 26262, DO-178C, and IEC 62304 — structure, intent, and engineering consequences, not the normative text |
| 🔒 `13-security` | Secure boot, TrustZone-M, secure communication on MCUs, and firmware update security |
| ♻️ `14-firmware-lifecycle` | Versioning, OTA updates, field diagnostics, and long-term maintenance of shipped firmware |
| 🧩 `15-languages-and-practice` | Firmware architecture and layering, embedded Rust, MicroPython, and machine learning on microcontrollers |

`00-overview` through `04-bare-metal-programming` are published, so their row links straight to
the folder's first page; `05` onward stay plain text until their tasks land in Phases 2 and 3.

## Four learning paths

Folders `00`–`04` are published, so each path below links straight through those steps. Steps
that land in folders `05`–`15` are still prose-only — those folders are not written yet, and
`onBrokenLinks: "throw"` means linking to a page that does not exist yet would fail the build.
Once a later phase publishes those folders, the remaining steps get wired up the same way.

| Path | Suggested order | What it gets you |
|---|---|---|
| **Day one** | [`00-overview`](./00-overview/what-embedded-means.md) (what embedded means) → [`01-hardware-foundations`](./01-hardware-foundations/what-hardware-to-buy.md) (what hardware to buy) → [`04-bare-metal-programming`](./04-bare-metal-programming/your-first-bare-metal-blink.md) (your first bare-metal blink) → then back to [`02-processor-architecture`](./02-processor-architecture/arm-cortex-m-profiles.md) and [`03-toolchain-and-build`](./03-toolchain-and-build/cross-compilation.md) for why it worked | A blinking LED before the theory, then the theory that explains it — the fastest way to stay motivated as a beginner |
| **I have a board and nothing works** | [`01-hardware-foundations`](./01-hardware-foundations/what-hardware-to-buy.md) → [`03-toolchain-and-build`](./03-toolchain-and-build/cross-compilation.md) → [`04-bare-metal-programming`](./04-bare-metal-programming/your-first-bare-metal-blink.md) → `11-debugging-and-testing` | A troubleshooting path from "is the board even powered" through toolchain issues to systematic hardfault debugging |
| **I'm building a product** | [`04-bare-metal-programming`](./04-bare-metal-programming/your-first-bare-metal-blink.md) → `05-peripherals-and-drivers` → `07-rtos` → `09-low-power-design` → `14-firmware-lifecycle` | The path from a working prototype to something with drivers, a scheduler, a power budget, and an update story |
| **I'm moving to Linux** | [`02-processor-architecture`](./02-processor-architecture/arm-cortex-m-profiles.md) → `10-embedded-linux` → `11-debugging-and-testing` | What changes when the target has an MMU and runs Linux instead of bare metal or an RTOS |

## Master reference list

A short list of sources worth owning or bookmarking, curated rather than exhaustive. Individual
pages cite the primary, authoritative source for their specific claims (an Arm architecture
reference, a vendor reference manual, `docs.kernel.org`, an RFC); this list is for the reader who
wants to go deeper than any one page.

**Books**

- Joseph Yiu, *The Definitive Guide to Arm Cortex-M3 and Cortex-M4 Processors* (and the
  companion *…Cortex-M0 and Cortex-M0+* edition) — the reference for the core itself: registers,
  exception model, and the instruction set, written by an Arm architect.
- Elecia White, *Making Embedded Systems* (O'Reilly) — the best single first book on the
  discipline as a whole, not just the chip.

**Courses, blogs, and video**

- Memfault's **Interrupt** blog (interrupt.memfault.com) — consistently the best current writing
  on firmware debugging, fault analysis, and build tooling.
- Bootlin's free training materials (bootlin.com/training) — embedded Linux, kernel, and Yocto
  training slides and labs, released under CC BY-SA.
- Nordic DevAcademy (academy.nordicsemi.com) — Bluetooth Low Energy done properly, from a
  silicon vendor with no reason to hand-wave the hard parts.
- Ben Eater (eater.net and YouTube) — signalling and bus protocols built up from first
  principles on a breadboard; unmatched for building real intuition about what a scope is
  showing you.

**Vendor and project documentation**

- [Arm Developer documentation](https://developer.arm.com/) — architecture reference manuals and
  processor technical reference manuals.
- [Zephyr Project documentation](https://docs.zephyrproject.org/) — devicetree, Kconfig, and the
  `west` tool.
- [FreeRTOS](https://www.freertos.org/) — kernel documentation and API reference.
- [The Linux kernel documentation](https://docs.kernel.org/) — driver APIs and subsystem guides,
  relevant once a target moves to embedded Linux.

Where a page below draws on a source that is paywalled or a purchase (the safety standards in
particular — IEC 61508, ISO 26262, DO-178C, and IEC 62304 are all paywalled documents), its
`## References` section says so rather than linking around the cost.
