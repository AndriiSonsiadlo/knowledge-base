---
id: simulation-and-emulation
title: Simulation and Emulation
sidebar_label: Simulation and Emulation
sidebar_position: 12
tags: [embedded, testing, qemu, renode, simulation, ci, cortex-m]
---

# Simulation and Emulation

Every technique in the rest of this folder needs a board on the desk, or at minimum a physical binary running somewhere real. [Unit Testing Firmware](./unit-testing-firmware.md) and [Mocking Hardware](./mocking-hardware.md) sidestep that by pulling *logic* out from behind a seam and running it on the host — a deliberate, narrow substitute for one driver's register interface. Simulation is a different move entirely: instead of extracting the logic, it models the *chip*, and runs the actual, unmodified cross-compiled `firmware.elf` against that model — the same instruction stream, the same startup code, the same register pokes, executing against a virtual STM32 instead of a real one.

The mental model: **a simulator trades fidelity for reach.** It cannot see a rise time, cannot reproduce a real sensor's exact noise floor, and cannot tell you whether a real board's decoupling network is adequate — nothing about the underlying silicon's analog behaviour is modelled at all. What it buys in exchange is a firmware image that boots, runs its real interrupt handlers, and can be driven through a CI pipeline on hardware that does not physically exist yet, does not need a probe attached, does not tie up a bench, and can be spun up in parallel by the hundred. Every page in this folder up to here answers "does this work" by getting closer to the real chip. Simulation answers a narrower question — "does this firmware image boot and run its logic correctly against a model of the chip" — for the price of a laptop instead of a lab.

:::info[Prerequisites]
[Unit Testing Firmware](./unit-testing-firmware.md) and [Mocking Hardware](./mocking-hardware.md) cover the alternative that pulls logic out from behind a seam rather than modelling the chip underneath it; read them for when that narrower, faster technique is the better fit than the whole-firmware approach this page covers. [The Debug Toolbox](./the-debug-toolbox.md) places simulation among every other instrument in this folder by what it can and cannot answer.
:::

## QEMU: Cortex-M silicon models, and a second, unrelated use for Linux targets

QEMU's Arm system emulation covers a genuinely wide range of boards, and the STM32 family is a small, deliberately maintained corner of it. There is no `NUCLEO-F411RE` machine type — QEMU's STM32 support currently covers a small number of specific parts, and the closest available to this board's silicon is **`netduinoplus2`** or **`olimex-stm32-h405`**, both modelling an **STM32F405RGT6** with a Cortex-M4F core: not the exact part, but the same family, the same core, and a large fraction of the same peripheral set as the NUCLEO-F411RE's STM32F411RE.

```bash
qemu-system-arm -M netduinoplus2 -kernel build/firmware.bin -nographic
```

`-kernel` loads the firmware image directly and starts execution at the reset vector, the same way real silicon does — there is no bootloader stage to emulate for a Cortex-M target, unlike the Linux-oriented boards QEMU also supports. `-nographic` routes the emulated UART to the host terminal, which is usually all the I/O a headless CI run needs. `-semihosting` is also available and is the fastest way to get a bring-up test's `printf` output out of the emulator with zero UART configuration at all, at the same emulated-halt cost [Logging Without Breaking Timing](./printf-debugging-done-right.md) describes for real hardware.

The peripheral coverage is the honest limit, and QEMU's own documentation is explicit about it: significant blocks are simply **not modelled** on the STM32 machines, including GPIO, I²C, DMA, USB OTG and the independent watchdog. Firmware that only touches a UART, a timer and the core (NVIC, SysTick, the fault registers) runs faithfully; firmware that depends on any of the unmodelled peripherals either does not run correctly or — the more dangerous case, covered in the warning below — appears to run correctly for the wrong reason.

QEMU's *second*, essentially unrelated use for "Linux targets" is worth naming separately so it is not confused with the above: for a product built around an embedded Linux SoC rather than (or alongside) a bare-metal Cortex-M, QEMU's `virt` board boots a real Linux kernel and root filesystem with good general-purpose fidelity — PCI, virtio devices, large RAM — because Linux userspace mostly does not care about the exact hardware underneath it the way bare-metal firmware does. That is a different emulation problem with a different fidelity story, solved by the same tool.

## Renode: multi-node systems with modelled peripherals

Renode starts from a different design point: rather than one emulated chip, a Renode session can instantiate **multiple independent "machines"** — each running its own firmware image against its own modelled SoC — and connect them through a modelled medium: a wired UART link, a simulated radio for BLE or 802.15.4, a shared bus. That is the capability QEMU does not have and the one Renode is built around: testing a *system* of several boards talking to each other — a mesh of sensor nodes, a CAN bus of several ECUs — in one deterministic, scriptable session, without a rack of physical boards and the wiring to match.

```text title="two-node.resc — two independent machines, connected"
mach create "central"
machine LoadPlatformDescription @platforms/boards/stm32f4_discovery-kit.repl
sysbus LoadELF @build/central.elf

mach create "peripheral"
machine LoadPlatformDescription @platforms/boards/stm32f4_discovery-kit.repl
sysbus LoadELF @build/peripheral.elf

showAnalyzer sysbus.usart2
start
```

A `.repl` ("Renode platform") file is the peripheral model — CPU, memory map, and the specific peripheral blocks Renode implements for that part — and `.resc` scripts are ordinary Renode Monitor commands saved to a file, so the same session that would be typed interactively becomes a repeatable, version-controlled CI artefact. As with QEMU, there is no `.repl` for the exact NUCLEO-F411RE; the closest maintained platform description is the **STM32F4 Discovery** family (STM32F407/F429), close enough in silicon family to be a reasonable stand-in and not a substitute for validating against the actual part.

## QEMU against Renode: fidelity and setup cost

| | QEMU | Renode |
|---|---|---|
| Peripheral fidelity on STM32 | Partial — core, NVIC, SysTick, USART modelled; **GPIO, I²C, DMA, USB OTG, watchdog not modelled** on the STM32 machines | Broader per-platform peripheral coverage where a `.repl` model exists; still not exhaustive, and coverage varies by board |
| Exact NUCLEO-F411RE support | No machine for this part; nearest is `netduinoplus2`/`olimex-stm32-h405` (STM32F405, same M4F family) | No platform for this part; nearest is the STM32F4 Discovery `.repl` family |
| Multi-node / networked systems | Not a first-class concept — one machine per QEMU process | **Core capability** — multiple machines in one session, connected via a modelled bus or radio |
| Setup cost for a single board | Low — one command line, a `-M` machine name and a `-kernel` image | Moderate — a `.repl`/`.resc` pair, more configuration surface, more power once written |
| Scripting and CI integration | Command-line flags; straightforward to script headless | Built-in Robot Framework test integration and a Python-scriptable Monitor, purpose-built for CI |
| Best fit | A quick boot-and-smoke-test of core logic against a related part, fastest to stand up | A system of several communicating nodes, or a project already investing in Renode's peripheral models and test framework |

Neither column is "the fidelity winner" outright — QEMU's STM32 support is thinner but nearly zero-configuration; Renode's peripheral models are generally richer and its multi-node capability has no QEMU equivalent at all, at the cost of a steeper setup for a single-board case that QEMU handles in one command line.

## Running the real firmware binary in CI

The shared payoff of both tools is the same: the exact `firmware.elf` that would be flashed to a board can instead boot inside a CI job, headless, on every commit, with no hardware in the loop.

<Tabs>
<TabItem value="qemu-ci" label="QEMU, headless">

```bash
timeout 30 qemu-system-arm -M netduinoplus2 -kernel build/firmware.bin \
  -nographic -serial mon:stdio \
  | tee boot.log
grep -q "self-test: PASS" boot.log
```

A `timeout` guard is not optional — firmware that never reaches its expected output otherwise hangs the CI job indefinitely, and the emulator gives no independent watchdog to save you the way real hardware's own watchdog might.

</TabItem>
<TabItem value="renode-ci" label="Renode, scripted test">

```bash
renode-test tests/boot-smoke-test.robot
```

```text title="tests/boot-smoke-test.robot — Robot Framework driving the Renode testing API"
*** Settings ***
Library    Process

*** Test Cases ***
Firmware Boots And Passes Self-Test
    Execute Command    mach create "dut"
    Execute Command    machine LoadPlatformDescription @platforms/boards/stm32f4_discovery-kit.repl
    Execute Command    sysbus LoadELF @build/firmware.elf
    Execute Command    start
    Wait For Line On Uart    self-test: PASS    timeout=30
```

</TabItem>
</Tabs>

This is the practical form of "simulation supplements hardware" — it does not replace the on-target checks elsewhere in this folder, it runs on every pull request in seconds to catch a class of regression (a boot hang, a crash in the first few hundred milliseconds of `main`, a self-test that a code change silently broke) before anyone needs to reach for a board at all.

## The fidelity limit, stated plainly

A green run under QEMU or Renode is evidence that the firmware boots and that its modelled logic runs correctly against the peripherals the simulator implements. It is not evidence about anything neither tool models: exact interrupt latency in cycles ([WCET and Timing Analysis](../06-interrupts-timing-and-real-time/wcet.md) owns that measurement, and it has to be made against real silicon or a cycle-accurate model, not a functional one), a real sensor's actual noise and drift, a genuine bus electrical fault ([Logic Analyzer Workflows](./logic-analyzer-workflows.md) and [The Oscilloscope for Firmware Engineers](./oscilloscope-for-firmware-engineers.md) are the instruments for that), or a silicon errata specific to a revision the simulator's authors never modelled because nothing in the simulator's own testing needed it to. Treat a passing simulation run the way [Unit Testing Firmware](./unit-testing-firmware.md) insists a passing host test be treated: necessary, fast, catches real regressions early — and not a substitute for the on-target validation that answers the questions only real hardware can.

:::warning[The bug QEMU cannot show you, and the race Renode cannot reproduce]
**An unimplemented peripheral register that silently "works" under QEMU and HardFaults on real silicon.** Touch a genuinely nonexistent address on real Cortex-M hardware and you get a BusFault — [HardFault Forensics](./hardfault-debugging.md) is the procedure for reading exactly why. QEMU's handling of an MMIO region it does not model is often far gentler: an unimplemented peripheral's registers commonly read back as zero and accept writes silently, rather than faulting the way real, unpopulated bus space does. The consequence is specific and dangerous: firmware with a genuine bug — an uninitialized peripheral pointer, a driver written against the wrong instance's base address, code that assumed a DMA controller QEMU does not model would actually complete a transfer — can boot cleanly, pass its self-test, and merge, purely because the simulator's forgiving default response to an unmodelled register masked the exact defect real hardware would have faulted on immediately. A clean simulation run for firmware that touches any of QEMU's unmodelled STM32 peripherals (GPIO, I²C, DMA, USB OTG, the watchdog) is not proof those code paths are correct — it may only be proof they were never really exercised.

**A race that depends on real clock drift, which two synchronized virtual machines will never reproduce.** Renode's multiple "machines" share a coordinated virtual time base, which is exactly what makes a multi-node session deterministic and repeatable — and exactly why a bug that only manifests from two *real* oscillators drifting apart by a few parts per million over an hour will not appear in Renode's more tightly synchronized virtual clocks. A field failure traced to clock drift between two boards can look "fixed" under a Renode reproduction that never actually recreated the drift, which is a false negative dressed up as a passing regression test. Where clock drift is a real suspect, the reproduction has to happen on real hardware, or with the drift modelled deliberately rather than assumed away by the simulator's own consistency.
:::

## See also

- [Unit Testing Firmware](./unit-testing-firmware.md) — the narrower, faster alternative that pulls logic out from behind a seam instead of modelling the whole chip, and when that is the better fit.
- [Mocking Hardware](./mocking-hardware.md) — faking one peripheral's interface deliberately, as opposed to this page's whole-chip model.
- [The Debug Toolbox](./the-debug-toolbox.md) — where simulation sits among every other instrument in this folder, and what each one can and cannot answer.
- [HardFault Forensics](./hardfault-debugging.md) — the real-hardware fault behaviour QEMU's unimplemented-peripheral handling can mask, named in the warning above.
- [Logic Analyzer Workflows](./logic-analyzer-workflows.md) — the instrument for the electrical-fidelity questions no simulator answers at all.

## References

- QEMU Project — [**Arm System emulator**](https://www.qemu.org/docs/master/system/arm/cpu-features.html) and [**STMicroelectronics STM32 boards**](https://www.qemu.org/docs/master/system/arm/stm32.html) documentation. The `-M` machine list including `netduinoplus2` and `olimex-stm32-h405`, the `-kernel` boot process for M-profile targets, and the explicit statement that GPIO, I²C, DMA, USB OTG and watchdog peripherals are not modelled on the current STM32 machines (documentation checked 2026-08-27).
- Antmicro / Renode — [**Renode documentation**](https://renode.readthedocs.io/), consulted at **latest**. The `.repl` platform description format, `.resc` script structure, multi-machine sessions connected through a modelled medium (the BLE two-node example this page's `.resc` snippet is adapted from), and the Robot Framework-based `renode-test` integration for CI (documentation checked 2026-08-27).
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). Cross-referenced for the peripheral set on the real STM32F411 that this page's fidelity comparison is measured against.
- Antmicro — [**"Cortex-M MCU Emulation with Renode"**, Memfault Interrupt guest post](https://interrupt.memfault.com/blog/intro-to-renode). A practical worked walkthrough of standing up an STM32 target in Renode from a project that did not start out using it, useful as a second, independent account alongside the primary documentation above.
