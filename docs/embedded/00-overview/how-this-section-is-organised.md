---
id: how-this-section-is-organised
title: How This Section Is Organised
sidebar_label: How This Section Is Organised
sidebar_position: 5
tags: [embedded, overview]
---

# How This Section Is Organised

Sixteen folders is a lot to land on with no map. The organising idea behind this section is that embedded engineering isn't one linear skill you learn top to bottom — it's several tracks (hardware, the toolchain, bare-metal fundamentals, concurrency, connectivity, safety, and so on) that a real project touches in a different order depending on what you're actually trying to do. A folder map tells you where a topic lives; a **learning path** tells you a sane order to read folders in for a specific goal. This page gives you both, plus the one policy that explains why some pages here link out to `computer-science/` instead of repeating material you might expect to find locally.

## The folder map

Numeric prefixes (`00`, `01`, `02`...) exist only to order folders on disk — the label you see in the sidebar comes from each folder's `_category_.json`, not the number. Reading the prefix as "difficulty level" or "required order" is the wrong way to use it; use the learning paths below instead.

| Folder | Question it answers |
|---|---|
| 📖 `00-overview` | What does "embedded" mean, and what are the words everyone assumes you already know? |
| 🔧 `01-hardware-foundations` | What hardware do I choose, and what does a datasheet or schematic actually tell me? |
| 🧠 `02-processor-architecture` | How does a Cortex-M core actually work — registers, memory map, pipeline? |
| 🛠️ `03-toolchain-and-build` | How does source code become a flashable image on this target? |
| ⚡ `04-bare-metal-programming` | What runs before `main()`, and how do I write register-level code without an OS? |
| 🔌 `05-peripherals-and-drivers` | How do I talk to GPIO, UART/SPI/I2C, DMA, and external memory correctly? |
| ⏱️ `06-interrupts-timing-and-real-time` | How do interrupts and the NVIC work, and what actually breaks timing determinism? |
| 🧵 `07-rtos` | How do tasks, scheduling, and synchronization work — in FreeRTOS and in Zephyr? |
| 📡 `08-connectivity-and-protocols` | How do I get USB, Ethernet/TCP-IP, or wireless working on constrained hardware? |
| 🔋 `09-low-power-design` | How do I make a battery-powered design actually last? |
| 🐧 `10-embedded-linux` | When is Linux the right call, and how does the boot chain and driver model work? |
| 🐞 `11-debugging-and-testing` | How do I debug a hardfault, and how do I test firmware at all? |
| 🛡️ `12-safety-and-reliability` | What do IEC 61508, ISO 26262, DO-178C, and IEC 62304 actually require of me? |
| 🔒 `13-security` | How do I secure boot, storage, and communication on a constrained device? |
| ♻️ `14-firmware-lifecycle` | How do I version, update, and support firmware after it ships? |
| 🧩 `15-languages-and-practice` | How do I structure firmware well, and what do Rust and MicroPython change? |

## Four learning paths

These are reading orders through the folders above by name, not literal links yet — most of the target pages don't exist until later tasks in this build finish, at which point the section's navigation gets wired up so you can click straight through.

**Day one** — you have no embedded background and want to see something work before you study why it worked. `00-overview` (this folder) → `01-hardware-foundations` (what to buy) → `04-bare-metal-programming` (your first bare-metal blink) → then back to `02-processor-architecture` and `03-toolchain-and-build` to understand why it worked. This path deliberately defers the toolchain and architecture theory until after a first success, because motivation matters more than sequencing when you're starting from zero.

**I have a board and nothing works** — a troubleshooting path, not a syllabus. `01-hardware-foundations` (is it even powered correctly) → `03-toolchain-and-build` (is the image actually getting onto the chip) → `04-bare-metal-programming` (is the startup code doing what you think) → `11-debugging-and-testing` (systematic hardfault and JTAG/SWD debugging once the basics check out).

**I'm building a product** — the path from a working prototype to something shippable. `04-bare-metal-programming` → `05-peripherals-and-drivers` → `07-rtos` → `09-low-power-design` → `14-firmware-lifecycle`. This is roughly the order real product timelines hit these concerns: get something running, add the drivers a real product needs, add concurrency once the driver count makes a main loop unwieldy, then power and lifecycle once the product itself is close to done.

**I'm moving to Linux** — for engineers whose target has (or will have) an MMU-capable microprocessor or SoC. `02-processor-architecture` (what's different about an applications core) → `10-embedded-linux` (boot chain, drivers, build systems) → `11-debugging-and-testing` (debugging looks different again once there's an OS in the way).

## Why some links leave the section — the no-duplication policy

This section does not re-teach material that already has a good home elsewhere on this site. General bus protocol theory (I2C, SPI, UART framing), general interrupt handling, scheduling theory, CPU architecture fundamentals, and bit manipulation all live under `computer-science/`, and embedded pages link out to that material instead of restating it. What embedded pages add on top is the part that's genuinely specific to this domain: register-level detail, Cortex-M-specific behavior, and the real-time and resource constraints from [What "Embedded" Actually Means](./what-embedded-means.md) that general computer-science treatments don't need to worry about.

Concretely: a page here explaining I2C at the register level assumes you already know what I2C *is* — the wire protocol, addressing, clock stretching — because [Serial Buses: I2C, SPI, UART](../../computer-science/buses-and-io/serial-buses-i2c-spi-uart.md) already covers that well, and duplicating it here would mean two pages to keep in sync every time either one is corrected. The same logic applies to [Scheduling](../../computer-science/operating-systems/scheduling.md) for RTOS scheduling theory and to [Instruction Set Architecture](../../computer-science/cpu-architecture/instruction-set-architecture.md) for what an ISA is before a page here gets into Cortex-M's specific instruction subset. If a link in this section takes you outside `docs/embedded/`, that's this policy working as intended, not a sign the section is incomplete.

:::warning
Don't skip the cross-referenced `computer-science/` page assuming "I'll pick it up from context." Embedded pages are written assuming you've already read the linked prerequisite — a page on I2C register configuration will use terms like "clock stretching" or "multi-master arbitration" without re-explaining them, because that explanation lives one click away. Reading the embedded-specific page first, without the foundation, is a common way to come away with a plausible-sounding but wrong mental model of what a register field is actually doing — and that wrong model is expensive to unlearn once you've built code around it.
:::

## See also

- [What "Embedded" Actually Means](./what-embedded-means.md) — the constraint set every later folder assumes you understand.
- [Bare-Metal, RTOS, or Linux](./bare-metal-vs-rtos-vs-linux.md) — the decision that determines which of the "I'm building a product" or "I'm moving to Linux" paths above actually applies to you.
- [Glossary](./glossary.md) — terms used across every folder in this map, defined once here.
- [Embedded Systems](../readme.md) — the full section index this page's folder map summarizes and expands on.

## References

- Docusaurus — [Sidebar](https://docusaurus.io/docs/sidebar) documentation — the mechanism behind the folder map above: sidebars here are autogenerated from folder structure, not hand-edited navigation.
- Write the Docs — [Documentation guide](https://www.writethedocs.org/guide/) — community guidance on organizing reference material into task-based reading paths, the model the four learning paths above follow.
