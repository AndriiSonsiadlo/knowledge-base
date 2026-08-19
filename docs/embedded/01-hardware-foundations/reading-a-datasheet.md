---
id: reading-a-datasheet
title: Reading a Datasheet
sidebar_label: Reading a Datasheet
sidebar_position: 2
tags: [embedded, hardware, documentation, stm32, datasheet]
---

# Reading a Datasheet

Coming from software, the instinct when you meet a new chip is to look for "the docs" — one document, searchable, that tells you everything. That document does not exist, and looking for it is the reason people bounce off hardware. Silicon vendors ship a *set* of documents, deliberately separated, because they answer questions that different people ask at different times: the person choosing a part, the person laying out the board, the person writing the firmware, and the person whose product works on the bench but fails one unit in fifty. Each document is written for one of those people and is close to useless for the others.

Once you know the shape of the set, the whole thing becomes tractable — you stop reading and start *looking things up*, which is the only way anyone has ever used an eight-hundred-page manual. This page is about the shape of the set, using the NUCLEO-F411RE's documents as the worked example, and about the one member of the set that everybody skips and regrets.

## The four kinds of document

| Document | Answers | For the STM32F411RE | Typical length |
|---|---|---|---|
| **Datasheet** | *Can I use this part?* Electrical limits, pin assignments, package, timing, current consumption, operating conditions, ordering codes. Numbers with tolerances. | **DS10314** — *STM32F411xC/E datasheet* | ~150 pages |
| **Reference manual** | *How do I program it?* Every peripheral, every register, every bit field, and the sequences you must follow. No electrical numbers. | **RM0383** — *STM32F411xC/E advanced Arm-based 32-bit MCUs* | ~840 pages |
| **Errata sheet** | *What is broken in this silicon?* Known hardware defects, which die revisions they affect, and whether a workaround exists. | **ES0287** — *STM32F411xC/xE device errata* | Short — tens of pages |
| **Application note** | *How do people normally do this?* Design guidance for one specific problem, written once so the support engineers stop answering it. | e.g. **AN2867** — *Oscillator design guide*, cited by both the datasheet and UM1724 | Varies; usually tens of pages |

Two more sit alongside them for this board, and they matter as much:

- **PM0214** — *STM32 Cortex-M4 MCUs and MPUs programming manual*. The reference manual covers ST's peripherals; it deliberately does **not** cover the processor core. Anything about registers `R0`–`R15`, the NVIC, SysTick, the MPU, `PRIMASK`/`BASEPRI`, fault handling, or the instruction set lives here (or in Arm's own architecture documentation), and RM0383 will simply refer you to it.
- **UM1724** — *STM32 Nucleo-64 boards (MB1136)*. A **user manual** describes a *board*, not a chip: which microcontroller pin the LED is on, which jumper selects the power source, and what the solder bridges do. The chip documents cannot know any of that. See [Reading a Schematic](./schematics-and-board-basics.md).

:::info[The mental split that makes this stick]
**Datasheet = the chip's physics. Reference manual = the chip's API. Errata = the chip's bug tracker. Application note = the chip's blog post. User manual = the board's wiring.** If your question has a unit attached to it — volts, milliamps, nanoseconds, picofarads, degrees Celsius — it is a datasheet question. If your question has a register name in it, it is a reference-manual question. That single rule resolves most "which document do I open" moments.
:::

## The datasheet: read the tables, not the prose

A datasheet's first pages are marketing — a feature bullet list and a block diagram. The value is further in, in the numbered tables, and there are three groups worth knowing by name.

**Absolute maximum ratings** are the destruction limits. For the STM32F411, Table 11 ("Voltage characteristics") gives the supply rail as `−0.3 V` to `4.0 V` and the input voltage on a non-5 V-tolerant pin as `VSS − 0.3 V` to `4.0 V`; Table 12 ("Current characteristics") caps the current sunk or sourced by any single I/O pin at `25 mA` and by all I/Os together at `120 mA`. The datasheet's own framing is worth quoting because people misread it constantly: "These are stress ratings only and functional operation of the device at these conditions is not implied" (§6.2). Exceeding them may destroy the part; *approaching* them is already outside the specified behaviour.

**Operating conditions** are where the part is guaranteed to work. Table 14 gives `VDD` as `1.7 V` to `3.6 V`, the AHB clock as `0` to `100 MHz` in the highest voltage-scaling mode, and — a detail that catches everyone once — the APB1 bus as `0` to `50 MHz` while APB2 goes to `100 MHz`.

**Characteristics tables** are the per-block numbers: I/O thresholds (Table 53), output levels (Table 54), oscillator accuracy (Tables 37–40), PLL behaviour (Table 41). These are the numbers you cite when someone asks why your firmware does something, and they are the reason [Voltage Levels and Logic](./voltage-levels-and-logic.md) and [Clocks and Oscillators](./clocks-and-oscillators.md) both keep pointing back here.

## Navigating an 800-page reference manual

RM0383 is about 840 pages. The reference manual for the larger STM32F4 parts, RM0090, runs to roughly 1,750 pages. Nobody reads either. The structure is completely regular, and exploiting that regularity is the whole skill.

Every peripheral chapter has the same five-part shape:

1. **Introduction** — one paragraph on what the block does.
2. **Main features** — a bullet list, useful for "does this peripheral even support what I need."
3. **Functional description** — the prose that explains the *mechanism*, and the part people wrongly skip on their way to the register list.
4. **Register description** — every register, its address offset, reset value, and each bit field's meaning.
5. **Register map** — a one-page table of the whole peripheral's registers, which is what you actually want open while writing code.

So the lookup procedure is: find the chapter, then go to part 4 or 5. Worked example — *"how do I make a pin open-drain?"*

1. **Contents → chapter.** "General-purpose I/Os (GPIO)" is chapter 8, starting at page 145.
2. **Skim the functional description.** §8.3 lists the modes a port bit can be in, and Table 23 ("Port bit configuration table") maps register-bit combinations to configurations. There is the answer in principle: `OTYPER` selects push-pull vs open-drain.
3. **Go to the register description** for `GPIOx_OTYPER` and read the bit definitions and the reset value.
4. **Cross-check the datasheet** for anything with a unit — how much current that pin may sink, how fast it may switch.
5. **Cross-check the errata** for the peripheral you just configured.

The three-step habit worth building is: *reference manual for what the bits mean, datasheet for what the pin can survive, errata for whether it works.*

:::tip[Use the PDF's bookmarks, not full-text search]
Full-text searching "OTYPER" in RM0383 returns dozens of hits scattered across chapters. The bookmark pane gives you the chapter and section tree, which is how the document is meant to be navigated. When you do search, search for a *register name* rather than a concept — register names are unique strings, concepts are not.
:::

## The errata: the one people skip

The errata sheet is a short document listing defects in the silicon itself: things the chip does that the reference manual says it should not. Every complex chip has them. ST's errata sheets tabulate each limitation against the affected device revisions and label it with whether a workaround exists — ES0287 uses `A` for "workaround available", `P` for partial, and `N` for none.

It gets skipped for a completely understandable reason: it is the only document in the set whose contents you cannot guess from the title, it is written in dense negative language, and reading it feels like pessimism at a stage where you are trying to get an LED to blink. The cost of skipping it is asymmetric, though. A missing feature announces itself in five minutes. A silicon erratum announces itself as *intermittent* misbehaviour — a bus that hangs one time in ten thousand, a timer that occasionally reports a stale value, a peripheral that must not be reconfigured while a transfer is in flight — and you will spend days assuming your code is wrong, because the reference manual says the hardware works.

The habit that costs nothing: **when you start using a peripheral for the first time, open the errata and read only the entries for that peripheral.** It takes two minutes and it is the highest-yield two minutes in embedded development.

:::warning[Check you are reading the right manual for your exact part]
Search engines and AI assistants routinely return **RM0090** — the reference manual for the STM32F405/407/415/417/427/429 families — for STM32F4 questions. It is a different document for different silicon. The STM32F411 has fewer peripherals, a different clock tree, and different register defaults. Following RM0090 for an F411 produces code that compiles, flashes, and quietly does not work, and the debugging session that follows is miserable because your reference says the register exists.

The same trap applies one level up: the *series* is STM32F4, the *family* is STM32F411xC/E, and the *part* is STM32F411RET6. Documentation is written per family. Before trusting any number, check the document's cover page says **STM32F411xC/E**.
:::

## A note on revisions

Every ST document carries a revision number and a date on its cover, and both the content and the *table numbering* change between revisions. The revisions consulted while writing this section are RM0383 Rev 3, the STM32F411xC/E datasheet Rev 7, and UM1724 Rev 12; ST has since published newer revisions of all three. When a table number cited on these pages does not match your copy, the fix is to search for the table's *title* rather than its number — titles are far more stable. When a *value* does not match, believe your copy: it is newer.

## See also

- [What Hardware to Buy](./what-hardware-to-buy.md) — the board these documents describe, and where to get it.
- [Reading a Schematic](./schematics-and-board-basics.md) — UM1724 in practice: what the board's jumpers, bridges, and LEDs are wired to.
- [Voltage Levels and Logic](./voltage-levels-and-logic.md) — a worked read of the datasheet's I/O characteristics tables.
- [Clocks and Oscillators](./clocks-and-oscillators.md) — a worked read of RM0383's RCC chapter and the datasheet's oscillator tables.
- [Glossary](../00-overview/glossary.md) — the acronyms these documents assume you already know.

## References

- STMicroelectronics — [**RM0383**, *STM32F411xC/E advanced Arm-based 32-bit MCUs reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf). The programming reference for every peripheral on this part. Consulted here at Rev 3; ST's current revision is newer.
- STMicroelectronics — [**STM32F411xC/E datasheet**](https://www.st.com/resource/en/datasheet/stm32f411re.pdf) (DS10314). Absolute maximum ratings (§6.2), operating conditions (§6.3.1), and every per-block characteristics table.
- STMicroelectronics — [**ES0287**, *STM32F411xC/xE device errata*](https://www.st.com/resource/en/errata_sheet/es0287-stm32f411xcxe-device-errata-stmicroelectronics.pdf). The list of things this silicon gets wrong, with per-revision applicability and workaround status. Read the entries for a peripheral before you use it.
- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf). The core-side companion to RM0383: registers, exceptions, NVIC, MPU, and the instruction set.
- STMicroelectronics — [STM32F411 documentation index](https://www.st.com/en/microcontrollers-microprocessors/stm32f411/documentation.html). The authoritative list of every current document for this family, which is where to go when a revision cited here has moved on.
