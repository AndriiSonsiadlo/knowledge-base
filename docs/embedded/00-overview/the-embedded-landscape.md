---
id: the-embedded-landscape
title: The Embedded Landscape
sidebar_label: The Embedded Landscape
sidebar_position: 3
tags: [embedded, overview]
---

# The Embedded Landscape

Picking a chip for a project isn't like picking a library — you can't easily swap it out six months in. The instruction set, the vendor's toolchain, the peripheral register layout, and the ecosystem of drivers and examples around a part are all things you commit to for the life of the product, and products in this field often live for years. So "which family of hardware" is really a question about which toolchain, which debugging workflow, and which vendor's support model you're signing up for — the raw specs are almost a secondary concern. This page maps the major families so that when a later folder says "on Cortex-M" or "targeting RISC-V," you have a sense of where that sits in the wider landscape and what it commits you to.

## The families

**8-bit microcontrollers (AVR, PIC).** Parts like Microchip's AVR (the ATmega328P inside the classic Arduino Uno) and PIC families are simple, cheap, and often run without an operating system on a few KB of RAM. They're common in cost-sensitive consumer goods, simple industrial I/O, and — because of Arduino — as most engineers' first hands-on embedded experience. Their limited address space and lack of a standard 32-bit toolchain ecosystem mean they're rarely chosen for new designs with any real computational or connectivity requirements today, but an enormous installed base of legacy products still runs on them.

**32-bit microcontrollers — Cortex-M.** Arm's Cortex-M profile (M0/M0+, M3, M4, M7, M33...) is the default choice for new microcontroller-class designs across the industry. Vendors including STMicroelectronics (STM32), NXP (LPC, Kinetis), Nordic Semiconductor (nRF52/53), and Texas Instruments (MSPM0) all license the same core and differentiate on peripherals, power, and radios. This section's reference hardware, the NUCLEO-F411RE, is a Cortex-M4F part. Because the instruction set architecture is shared, code written against CMSIS (Arm's common hardware abstraction headers) is far more portable across Cortex-M vendors than 8-bit code ever was — see [Instruction Set Architecture](../../computer-science/cpu-architecture/instruction-set-architecture.md) for what "shared ISA" actually buys you.

**Applications-class / Linux-capable — Cortex-A and comparable.** Chips built around Arm's Cortex-A profile (or a comparable applications core) have an MMU and enough external memory bandwidth to run a full operating system. STM32MP1, NXP's i.MX 8 family, Qualcomm's embedded Snapdragon parts, and the Broadcom SoC inside a Raspberry Pi all sit here. This is the hardware class folder `10-embedded-linux` (not yet published) is about — see [Microcontroller, Microprocessor, SoC](./microcontroller-vs-microprocessor-vs-soc.md) for why the MMU is the deciding property.

**RISC-V.** An open, royalty-free instruction set architecture rather than a single vendor's product line. SiFive ships RISC-V cores and reference designs; Espressif's ESP32-C3 is a mainstream RISC-V microcontroller; GigaDevice's GD32V line offers RISC-V pin-compatible with some STM32 parts. RISC-V is growing fastest at the microcontroller end right now, with application-class RISC-V parts still catching up to Cortex-A's ecosystem maturity. Choosing RISC-V today is as much a bet on tooling maturity and second-source availability as it is a technical decision.

**FPGA and SoC-FPGA.** An FPGA is reconfigurable logic — you're not running instructions on a fixed CPU pipeline at all, you're defining custom hardware. A SoC-FPGA (Xilinx/AMD Zynq, Intel/Altera Cyclone SoC) pairs that reconfigurable fabric with a hard Cortex-A core on the same die, so a Linux-class processor and custom hardware logic share memory and can hand work back and forth. This is a different discipline from software-only embedded work — the toolchains (Vivado, Quartus) are hardware-description-language tools, not C compilers — and it's out of scope for most of this section, but it's worth knowing the category exists for signal-processing and custom-I/O-heavy designs.

## Families, toolchains, and typical applications

| Family | Representative parts | Typical toolchain | Typical application |
|---|---|---|---|
| 8-bit (AVR, PIC) | ATmega328P, PIC16/PIC18 | `avr-gcc`, MPLAB X | Cost-sensitive simple I/O; hobbyist/education; legacy industrial designs |
| Cortex-M (32-bit MCU) | STM32, NXP LPC/Kinetis, Nordic nRF52/53, TI MSPM0 | `arm-none-eabi-gcc` + CMSIS; vendor IDEs (STM32CubeIDE) | Bare-metal or RTOS firmware — the majority of new embedded product designs today |
| Cortex-A / Linux-class | STM32MP1, i.MX 8, Raspberry Pi SoC, embedded Snapdragon | Yocto or Buildroot, standard Linux `gcc` toolchain | Devices needing networking, a filesystem, a GUI stack, or a large driver ecosystem |
| RISC-V | SiFive cores, ESP32-C3, GD32V | `riscv-gnu-toolchain`, vendor SDKs (ESP-IDF, etc.) | Open-ISA microcontrollers today; application-class parts growing |
| FPGA / SoC-FPGA | Xilinx/AMD Zynq, Intel/Altera Cyclone SoC | Vendor HDL toolchains (Vivado, Quartus) + embedded Linux on the hard core | Hardware-defined logic paired with a processor; signal processing, custom I/O |

:::warning
"It's an ARM chip" is not enough information to assume code portability. Cortex-M and Cortex-A implement different Armv7/Armv8 architecture *profiles* with different instruction subsets, different (or absent) MMUs, and a completely different exception model — a binary built for a Cortex-A Linux target will not run on a Cortex-M microcontroller. Even within Cortex-M, code built assuming the Armv7-M instruction set (M3/M4/M7) uses instructions that Armv6-M cores (M0/M0+/M23) simply do not implement, and hard-float code built for an FPU-equipped part like the M4F will not run at all on a part without one. Engineers who assume "ARM" implies binary or even source portability across this landscape lose real time discovering it doesn't at the worst possible point — usually a build or link failure well into a port, not at the design stage where the mismatch would have been cheap to catch.
:::

## What a vendor choice commits you to

Choosing a family is really choosing a support model. A large silicon vendor like ST or NXP ships a hardware abstraction layer, reference manuals for every peripheral, and years of forward part compatibility within a product line — valuable for a product with a multi-year field life, at the cost of a heavier HAL and sometimes vendor lock-in on tooling. A newer or more open ecosystem (RISC-V vendors, some Nordic/Zephyr-first designs) trades some of that long-term institutional weight for openness and, often, a more modern toolchain experience. Neither is universally right; it's a fit question against the product's expected lifetime, team size, and how much you value being able to switch second sources later.

## See also

- [Microcontroller, Microprocessor, SoC](./microcontroller-vs-microprocessor-vs-soc.md) — the hardware property (on-chip memory and the MMU) that cuts across every family listed here.
- [What "Embedded" Actually Means](./what-embedded-means.md) — the constraint set that makes family choice matter more here than "library choice" would elsewhere.
- [Bare-Metal, RTOS, or Linux](./bare-metal-vs-rtos-vs-linux.md) — the software-side decision that follows once a family (and therefore an MMU or not) is chosen.
- [Glossary](./glossary.md) — MCU, SoC, and the other terms used throughout this table.
- [Embedded Systems](../readme.md) — the section index and its four learning paths.

## References

- Arm — [Cortex-M product pages](https://www.arm.com/products/silicon-ip-cpu?families=cortex-m) — the authoritative listing of the Cortex-M core family this table's "32-bit MCU" row is built on.
- RISC-V International — [specifications](https://riscv.org/technical/specifications/) — the open ISA specifications for the RISC-V row, maintained by the standards body itself rather than any one vendor.
- Microchip — [AVR 8-bit MCU](https://www.microchip.com/en-us/products/microcontrollers-and-microprocessors/8-bit-mcus/avr-mcus) product pages — the current home of the AVR line referenced in the 8-bit row.
- AMD/Xilinx — [Zynq-7000 SoC](https://www.xilinx.com/products/silicon-devices/soc/zynq-7000.html) product page — a representative SoC-FPGA part for the last row.
