---
id: what-embedded-means
title: What "Embedded" Actually Means
sidebar_label: What Embedded Means
sidebar_position: 1
tags: [embedded, overview]
---

# What "Embedded" Actually Means

Ask most software engineers what "embedded" means and they'll say something about small chips, or soldering, or blinking an LED. That's the wrong mental model, and it's why so many engineers who are perfectly competent on servers and desktops write their first firmware the way they'd write a desktop app — and then spend a week debugging failures that a desktop never produces. Embedded isn't defined by the chip. A phone's application processor and a pacemaker's microcontroller are both "chips," and the software practices around them could not be more different. What actually defines the field is a fixed set of constraints that never fully goes away, no matter how big or small the target is. Understand the constraints, and the rest of this section — why bare-metal code looks the way it does, why an RTOS exists, why "just add more RAM" isn't always an option — falls out as a consequence rather than a pile of arbitrary rules to memorize.

Every constraint below is a *default*, not an absolute — some embedded targets run Linux with gigabytes of RAM, and some have OTA update pipelines as smooth as a phone app's. But the discipline is shaped by the fact that these are what you get **unless you go out of your way to buy your way out of them**, and a lot of embedded engineering is deciding which of these constraints you actually need to fight and which you should just accept.

## The constraint set

**Memory is measured in kilobytes, not gigabytes, and it's fixed at build time.** The reference board this section uses, a NUCLEO-F411RE carrying an STM32F411RE, has 512 KB of flash for code and 128 KB of SRAM for everything else — stack, heap (if you use one), globals, and any buffers your peripherals need. There's no swap file, no virtual memory backing it up, and no way to add more once the board is manufactured. A desktop program that leaks a few hundred KB is sloppy; a firmware program that does the same runs out of memory in minutes.

**There's no operating system unless you put one there.** On a desktop, "start the program" means the OS loader maps your binary, sets up a stack, and calls `main()` inside a process the kernel manages. On a microcontroller, the very first instruction that runs after reset is *your* code (or code you linked in) — there is no scheduler, no process isolation, no file descriptors, and no `malloc` guarantee unless you build one. Folder `04-bare-metal-programming` (not yet published) covers what runs before `main()` even starts.

**Deadlines are correctness, not performance.** A web server that responds in 300 ms instead of 100 ms under load is slow. A motor controller that computes the wrong PWM duty cycle 2 ms late can be *wrong* — the motor oversteps, the control loop goes unstable, or a safety interlock trips. This is what "real-time" means in embedded work: not "fast," but "late is a bug."

**Bugs have physical consequences.** A crashed desktop app loses unsaved work. A crashed firmware image can mean a valve stays open, a brake doesn't release, or a battery keeps charging past its safe limit. Not every embedded product is safety-critical, but the possibility that the software controls something with mass, voltage, or heat behind it is the reason embedded teams take failure modes far more seriously than most application teams do.

**Products ship and then live for years without a hotfix.** A web service gets patched the same day a bug is found. A shipped microcontroller might not get a software update ever — many products have no update mechanism at all, and even ones that support over-the-air (OTA) updates treat every update as a real, field-tested release, not a quick `git push`. The bug you ship is often the bug the product has for its entire service life, which is routinely measured in years.

## The same constraints, next to what you already know

| Constraint | Typical desktop/server default | Typical embedded default |
|---|---|---|
| Working memory | GBs of RAM, backed by virtual memory and swap | Tens to hundreds of KB of SRAM, fixed at manufacture, no swap |
| Code storage | SSD/HDD, effectively unbounded | On-chip flash, often 128 KB–2 MB, fixed at manufacture |
| Execution environment | Full OS: processes, virtual memory, file system, scheduler | Nothing, until you add it — bare-metal loop, or an RTOS you configure yourself |
| Timing | "Fast" is a UX/performance goal | A missed deadline can be a correctness failure, not just latency |
| Failure consequence | Crash, restart, maybe lost data | Possible physical harm: motion, heat, voltage, chemical, pressure |
| Update cadence | Continuous deployment, same-day patches | Often no update path at all; where OTA exists, updates are rare and high-stakes |
| Service life | Software rewritten or replaced within a few years | Years to decades in the field, sometimes with no way to touch it again |

## Why the constraints, not the chip, define the field

It's tempting to draw the line at "small chip = embedded," but that line breaks immediately. A modern car's infotainment system runs Linux on a chip more powerful than a laptop from a decade ago — the code that plays a video is barely "embedded" in the constrained sense at all. Meanwhile, a smoke detector's microcontroller with 8 KB of RAM absolutely is, even though "8 KB of RAM" sounds almost comically small next to a phone. The honest dividing line is which of the five constraints above are actually pressing on the engineer writing the code, not what the chip is called or how it's marketed. That's also why this section spends real time on the microcontroller/microprocessor/SoC distinction next — because it's the property that determines *which* of these constraints you're negotiating with, not the constraints themselves.

:::warning
Don't assume a heap on a microcontroller behaves like a heap on your desktop. Repeated `malloc()`/`free()` churn on a device with a few tens of KB of SRAM and no virtual memory to paper over fragmentation will, after days or weeks of continuous operation, fragment the heap until an allocation that used to succeed starts returning `NULL` — and if the calling code doesn't check that return value (a lot of ported desktop code doesn't), the result is silent memory corruption discovered in the field, not a crash caught in testing. This is common enough that many embedded teams avoid a general-purpose heap allocator entirely in favor of static allocation or fixed-size memory pools.
:::

## See also

- [Microcontroller, Microprocessor, SoC](./microcontroller-vs-microprocessor-vs-soc.md) — the hardware property that determines which of these constraints you're actually negotiating with.
- [The Embedded Landscape](./the-embedded-landscape.md) — how these constraints play out differently across 8-bit parts, Cortex-M, Linux-class SoCs, and RISC-V.
- [Bare-Metal, RTOS, or Linux](./bare-metal-vs-rtos-vs-linux.md) — the three ways to structure software around the "no OS by default" constraint.
- [Glossary](./glossary.md) — MCU, RTOS, and the other terms used above, defined precisely.
- [Embedded Systems](../readme.md) — the section index and the four suggested learning paths through it.

## References

- Elecia White, *Making Embedded Systems* (O'Reilly, 2011) — the book this page's framing is drawn from; makes the case in far more depth that embedded is a discipline defined by constraints, not by chip size.
- STMicroelectronics, *STM32F411xC/E datasheet* — the source for the NUCLEO-F411RE's 512 KB flash / 128 KB SRAM figures cited above; this section's later folders build on this exact part.
- Memfault's [Interrupt blog](https://interrupt.memfault.com/blog) — consistently the best current writing on what these constraints look like in day-to-day firmware engineering practice, from a company that builds tooling for exactly this.
