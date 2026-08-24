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

## How this section is organised

Sixteen folders is a lot to land on with no map. The organising idea behind this section is that embedded engineering isn't one linear skill you learn top to bottom — it's several tracks (hardware, the toolchain, bare-metal fundamentals, concurrency, connectivity, safety, and so on) that a real project touches in a different order depending on what you're actually trying to do. A folder map tells you where a topic lives; a **learning path** tells you a sane order to read folders in for a specific goal.

Numeric prefixes (`00`, `01`, `02`...) exist only to order folders on disk — the label you see in the sidebar comes from each folder's `_category_.json`, not the number. Reading the prefix as "difficulty level" or "required order" is the wrong way to use it; use the learning paths below instead.

## Sections

| Folder | Covers |
|---|---|
| <Icon name="book-open" /> [`00-overview`](./00-overview/what-embedded-means.md) | What "embedded" means as a discipline, the microcontroller/microprocessor/SoC distinction, the landscape of architectures and vendors, bare-metal vs. RTOS vs. Linux, and a glossary |
| <Icon name="wrench" /> [`01-hardware-foundations`](./01-hardware-foundations/what-hardware-to-buy.md) | Choosing hardware, schematics and board basics, power and reset behaviour, and what a datasheet actually tells you |
| <Icon name="cpu" /> [`02-processor-architecture`](./02-processor-architecture/arm-cortex-m-profiles.md) | The Cortex-M register model, memory map and bit-banding, and the pipeline and instruction-set concerns specific to microcontroller cores |
| <Icon name="hammer" /> [`03-toolchain-and-build`](./03-toolchain-and-build/cross-compilation.md) | Cross-compilers, CMake for embedded, linker scripts, ELF/map files, and the build pipeline from source to flashable image |
| <Icon name="zap" /> [`04-bare-metal-programming`](./04-bare-metal-programming/your-first-bare-metal-blink.md) | Startup code, vector tables, register-level programming, critical sections, and your first bare-metal blink |
| <Icon name="plug" /> `05-peripherals-and-drivers` | GPIO, UART/SPI/I2C in depth, DMA, external memory, and flash/EEPROM emulation |
| <Icon name="timer" /> `06-interrupts-timing-and-real-time` | The NVIC, timing determinism, scheduling theory as it applies to interrupts, and what breaks determinism on cores with caches |
| <Icon name="git-fork" /> `07-rtos` | Task and scheduling concepts, synchronization primitives, FreeRTOS, and Zephyr |
| <Icon name="wifi" /> `08-connectivity-and-protocols` | USB device stacks, Ethernet and TCP/IP on constrained devices, and wireless connectivity |
| <Icon name="battery" /> `09-low-power-design` | Sleep modes, power budgeting, and low-power peripheral design |
| <Icon name="terminal" /> `10-embedded-linux` | When Linux is the right call, the boot chain, device drivers, and build systems (Yocto, Buildroot) |
| <Icon name="bug" /> `11-debugging-and-testing` | JTAG/SWD, hardfault debugging, unit testing firmware, and hardware-in-the-loop testing |
| <Icon name="shield" /> `12-safety-and-reliability` | IEC 61508, ISO 26262, DO-178C, and IEC 62304 — structure, intent, and engineering consequences, not the normative text |
| <Icon name="lock" /> `13-security` | Secure boot, TrustZone-M, secure communication on MCUs, and firmware update security |
| <Icon name="refresh-cw" /> `14-firmware-lifecycle` | Versioning, OTA updates, field diagnostics, and long-term maintenance of shipped firmware |
| <Icon name="puzzle" /> `15-languages-and-practice` | Firmware architecture and layering, embedded Rust, MicroPython, and machine learning on microcontrollers |

`00-overview` through `04-bare-metal-programming` are published, so their row links straight to
the folder's first page; `05` onward stay plain text until their tasks land in Phases 2 and 3.

## Four learning paths

These are reading orders through the folders above by name, not literal links yet — most of the target pages don't exist until later tasks in this build finish, at which point the section's navigation gets wired up so you can click straight through.

**Day one** — you have no embedded background and want to see something work before you study why it worked. `00-overview` (this folder) → `01-hardware-foundations` (what to buy) → `04-bare-metal-programming` (your first bare-metal blink) → then back to `02-processor-architecture` and `03-toolchain-and-build` to understand why it worked. This path deliberately defers the toolchain and architecture theory until after a first success, because motivation matters more than sequencing when you're starting from zero.

**I have a board and nothing works** — a troubleshooting path, not a syllabus. `01-hardware-foundations` (is it even powered correctly) → `03-toolchain-and-build` (is the image actually getting onto the chip) → `04-bare-metal-programming` (is the startup code doing what you think) → `11-debugging-and-testing` (systematic hardfault and JTAG/SWD debugging once the basics check out).

**I'm building a product** — the path from a working prototype to something shippable. `04-bare-metal-programming` → `05-peripherals-and-drivers` → `07-rtos` → `09-low-power-design` → `14-firmware-lifecycle`. This is roughly the order real product timelines hit these concerns: get something running, add the drivers a real product needs, add concurrency once the driver count makes a main loop unwieldy, then power and lifecycle once the product itself is close to done.

**I'm moving to Linux** — for engineers whose target has (or will have) an MMU-capable microprocessor or SoC. `02-processor-architecture` (what's different about an applications core) → `10-embedded-linux` (boot chain, drivers, build systems) → `11-debugging-and-testing` (debugging looks different again once there's an OS in the way).

## Why some links leave the section — the no-duplication policy

This section does not re-teach material that already has a good home elsewhere on this site. General bus protocol theory (I2C, SPI, UART framing), general interrupt handling, scheduling theory, CPU architecture fundamentals, and bit manipulation all live under `computer-science/`, and embedded pages link out to that material instead of restating it. What embedded pages add on top is the part that's genuinely specific to this domain: register-level detail, Cortex-M-specific behavior, and the real-time and resource constraints from [What "Embedded" Actually Means](./00-overview/what-embedded-means.md) that general computer-science treatments don't need to worry about.

Concretely: a page here explaining I2C at the register level assumes you already know what I2C *is* — the wire protocol, addressing, clock stretching — because [Serial Buses: I2C, SPI, UART](../computer-science/buses-and-io/serial-buses-i2c-spi-uart.md) already covers that well, and duplicating it here would mean two pages to keep in sync every time either one is corrected. The same logic applies to [Scheduling](../computer-science/operating-systems/scheduling.md) for RTOS scheduling theory and to [Instruction Set Architecture](../computer-science/cpu-architecture/instruction-set-architecture.md) for what an ISA is before a page here gets into Cortex-M's specific instruction subset. If a link in this section takes you outside `docs/embedded/`, that's this policy working as intended, not a sign the section is incomplete.

:::warning
Don't skip the cross-referenced `computer-science/` page assuming "I'll pick it up from context." Embedded pages are written assuming you've already read the linked prerequisite — a page on I2C register configuration will use terms like "clock stretching" or "multi-master arbitration" without re-explaining them, because that explanation lives one click away. Reading the embedded-specific page first, without the foundation, is a common way to come away with a plausible-sounding but wrong mental model of what a register field is actually doing — and that wrong model is expensive to unlearn once you've built code around it.
:::


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
