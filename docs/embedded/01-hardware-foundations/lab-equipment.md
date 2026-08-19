---
id: lab-equipment
title: Lab Equipment and What It Answers
sidebar_label: Lab Equipment
sidebar_position: 11
tags: [embedded, hardware, tooling, debugging, logic-analyzer, oscilloscope]
---

# Lab Equipment and What It Answers

The debugger on your Nucleo can single-step your code, read every register, and show you the contents of memory — and it is blind to everything that happens outside the package. It will tell you, truthfully, that you wrote `0xA5` to the SPI data register. It cannot tell you whether `0xA5` left the pin, whether the clock that carried it was clean, whether the device on the other end was even powered.

That gap is the whole reason a bench exists. Each instrument on it answers exactly one class of question, and the useful skill is not operating them — it is **knowing which question you are actually asking**, so that you reach for the one instrument that can answer it instead of staring at the three that cannot. Most lost days in embedded work are spent measuring the wrong thing very carefully.

:::info[Prerequisites]
[What Hardware to Buy](./what-hardware-to-buy.md) lists the starter kit and its prices, and argues for buying a logic analyzer before an oscilloscope. This page is the follow-on: what each instrument is actually *for*, with a worked bug per instrument.
:::

## The mapping, in one table

| Instrument | The question it answers | What it cannot see | Approx. cost |
|---|---|---|---|
| **Multimeter** | "Is this real?" — is the rail at the right voltage, are these two points connected, are these two nets shorted | Anything that happens fast. It reports a steady state, not an event. | $30–60 |
| **Logic analyzer** | "What actually went out on the wire?" — the bits, their timing, decoded back into I²C addresses or UART bytes | Voltage. It reduces every signal to above-threshold or below-threshold and throws the shape away. | $12–15 |
| **Oscilloscope** | "What does the signal really look like?" — edge shape, ringing, overshoot, rail sag, noise | Long captures of many channels; protocol context without effort | $150+ |
| **Debugger (on-board ST-LINK)** | "What is my code doing?" — breakpoints, single-stepping, memory and peripheral registers live | Anything outside the chip, and anything whose timing your stopping would change | included |
| **Serial console (ST-LINK VCP)** | "What does my code think is happening?" — a running narrative in your own words | The truth, as opposed to your program's belief about it | included |
| **Current measurement (`JP6` + meter, or a power profiler)** | "Where is my energy going?" — average draw, and with a profiler, the shape of the current over time | Anything about correctness | $0 with `JP6`; $100+ for a profiler |
| **Bench power supply** | "What happens at 3.0 V? At 2.7 V?" — behaviour across the supply envelope, with a current limit protecting a suspect board | Anything about signals | $60+ |

Prices are approximate, in USD, and were checked in **August 2026** — the same basis as the kit table in [What Hardware to Buy](./what-hardware-to-buy.md), which is the source for the multimeter and logic-analyzer figures. The oscilloscope, power-profiler and bench-supply rows are order-of-magnitude entry points rather than quotes for a specific model; treat them as "which shelf", not as a price.

The rest of this page is one real bug per row.

## The multimeter — "is this real?"

**The bug.** An LED wired from a GPIO through a resistor to ground does not light. The code is three lines long and obviously correct: enable the port clock, set `MODER` to output, set the bit in `BSRR`.

**The measurement.** Put the black probe on a ground pin and the red one on the `+3V3` header pin: `3.29 V`. The board is powered. Now put the meter in continuity mode and check from the microcontroller's pin at the morpho header to the LED's anode — silence. The jumper wire is broken inside its insulation, which happens constantly and is invisible.

That is the multimeter's entire personality. It is slow, and it answers questions about *existence*: is there voltage here, is there a connection here, is there a short here. No amount of firmware reasoning substitutes, because the premise the reasoning rests on — that the circuit is what the schematic says — is exactly what the meter tests.

Three habits worth forming:

- **Continuity mode is the most-used function on the instrument.** Buy one with a fast beeper; you will use it more than everything else combined.
- **Measure the rail *at the chip*, not at the connector.** A rail that is 3.3 V at the regulator and 3.0 V at the load has a resistance problem you would otherwise never find.
- **Never leave the meter in current mode.** More on this in the warning below.

## The logic analyzer — "what actually went out on the wire?"

**The bug.** An I²C sensor returns `0xFF` for every register. The HAL call returns an error. You have checked the address three times against the datasheet.

**The measurement.** Clip four channels onto `SCL`, `SDA`, `+3V3` and ground, capture, and let the decoder do the work. There are exactly three things you can see, and each points somewhere completely different:

1. **Nothing on either line.** The peripheral never transmitted — a clock-enable or pin-alternate-function problem inside the chip. Go back to the debugger.
2. **Address byte transmitted, no ACK.** The bus works; nothing at that address answered. Wrong address (the `0x76`/`0x77` pin-strap variants of most sensors are the classic), or the device is not powered, or its own reset is asserted.
3. **Address ACKed, then data reads as `0xFF`.** The device is there and talking. Now it is a register-map or a timing problem — and you have eliminated two whole layers in thirty seconds.

This is what a logic analyzer is *for*: it collapses "somewhere in this stack of five layers" into "this layer". The `$12` FX2-based clones are supported by the open-source `fx2lafw` firmware and decoded by **sigrok/PulseView**, whose protocol-decoder list covers I²C, SPI, UART, 1-Wire, CAN, and well over a hundred more — including stacked decoders that turn raw I²C traffic into named registers of a specific chip.

Two operating notes that matter more than any setting:

- **Sample fast enough.** A capture at only two or three times the signal rate will alias edges and produce decoded nonsense that looks authoritative. Sample at several times the fastest edge you care about, and if the decode looks impossible, suspect the sample rate before you suspect the device.
- **Connect the ground.** A logic analyzer with no common ground reference is measuring the difference between two arbitrary potentials. It will show you something, and the something will be fiction.

### When the logic analyzer beats the debugger

This deserves its own heading because it is the most commonly missed judgement call.

- **The bug involves timing.** A breakpoint stops the CPU and does not stop the peripheral, the sensor, or the other end of the bus. A timing bug observed under a breakpoint is a different bug.
- **The bug is intermittent.** A logic analyzer can capture continuously and trigger on a specific pattern; a human watching a debugger cannot.
- **The bug is on the far side of the pin.** The debugger's model stops at the package boundary, and half of embedded bugs live past it.
- **The question is "who is at fault, me or the device?"** The wire is the neutral witness. It is the only evidence both sides of that argument accept.

Conversely, the debugger wins the moment the answer is inside the chip: a wrong register value, a null pointer, a stack that has overflowed into something else.

## The oscilloscope — "what does the signal really look like?"

**The bug.** SPI to a display works perfectly at 1 MHz and produces garbage at 8 MHz. The logic analyzer shows clean, correctly decoded traffic at both speeds.

**The measurement.** A scope on the clock line shows what the analyzer discarded: at 8 MHz, with the display on 20 cm of jumper wire, each rising edge overshoots well above the rail and rings for several nanoseconds before settling. The receiver's input sees more than one crossing per edge and clocks extra bits. The analyzer, which reduces everything to a single threshold decision per sample, could never have shown this.

That is the division of labour. A logic analyzer answers *what* the bits were; a scope answers *what the electricity was doing*. You need the scope when:

- Edges are suspect — ringing, slow rise, overshoot ([Signal Integrity and Noise](./signal-integrity-and-noise.md) is the companion page).
- The supply is suspect — a sag lasting microseconds when a load switches is invisible to a multimeter and obvious on a scope.
- The signal is analog at all — a sensor output, a filtered PWM, a decaying RC.

And the discipline that makes scope measurements trustworthy: **use the short spring-tip ground, not the crocodile lead.** The long ground lead forms a loop with the probe tip that rings at its own frequency, so a large fraction of "the overshoot I measured" is often the probe. The tell is that it changes when you move the lead.

## Current measurement — "where is my energy going?"

**The bug.** A battery-powered design is meant to draw about 10 µA asleep. It draws 2 mA, and the battery lasts days instead of years.

**The measurement.** The Nucleo makes this unusually easy. UM1724 Rev 17 §7.8: "Jumper `JP6`, labeled `IDD`, is used to measure the STM32 microcontroller consumption by removing the jumper and connecting an ammeter." That jumper sits in series with the microcontroller's supply, so a meter across its two pins reads the STM32's own draw, with the ST-LINK and the LEDs excluded.

Now compare against the datasheet. DS10314 Rev 8 gives Stop mode with the flash in deep power-down as `10 µA` typical, and Standby as `2.1–2.8 µA` typical at 25 °C (Tables 28 and 30). Reading two milliamps against those numbers is not a marginal discrepancy — it is a factor of two hundred, which means something is simply still on. The usual culprits, in order: a peripheral clock never disabled, a GPIO left driving a load, or a floating input sitting near its switching threshold and leaving both input transistors partly conducting. [How a GPIO Pin Really Behaves](./gpio-electrical-behaviour.md) covers that last one, which is the one people do not guess.

A dedicated **power profiler** adds the axis a multimeter cannot: current *over time*, sampled fast enough to show the shape. That is what you need when the question is "how much energy does one wake-radio-sleep cycle cost", because the answer is an integral, not an average. It is a genuinely later purchase — buy it when you have a product with a battery life target, not before.

## The bench supply — "what happens at 3.0 V?"

**The bug.** A board resets occasionally in the field. Never on the desk.

**The measurement.** Power the board from a bench supply instead of USB and walk the voltage down. If the fault appears reliably below some threshold, you have converted an intermittent field failure into a repeatable bench one, which is most of the work. Set the supply's current limit slightly above the expected draw and it will also protect a board you suspect of having a short — the limit engages instead of something releasing smoke.

This is the instrument that turns "sometimes" into "always", and that transformation is worth more than any measurement it makes.

## The serial console you already have

The Nucleo's ST-LINK presents a virtual COM port, so `printf` over `USART2` reaches your terminal on the same cable that flashes the board (UM1724 Rev 17, §7.10, "USART communication"). It is the cheapest instrument on the bench and the easiest to over-trust: it tells you what your program *believes*, in your own words, which is exactly the thing already suspect when you are debugging. It also changes timing — a blocking `printf` at 115200 baud takes roughly 87 µs per character at 8-N-1 — which is enough to hide or create a race.

Use it for narrative and state. Use the wire for truth.

:::warning[The ammeter mistake, which destroys the meter or the board]
A multimeter in **current** mode is close to a short circuit: it measures current by putting a very low resistance in the path. That is correct and necessary in series. Placed in *parallel* — probes across a rail and ground, the way you measure voltage — it connects 3.3 V to ground through a fraction of an ohm.

The good outcome is a blown fuse inside the meter. The bad outcomes are a damaged regulator, a damaged microcontroller, or, on a supply that can deliver real current, something that gets hot enough to matter. This happens most often *after* a legitimate current measurement: you measure through `JP6`, get your number, and then reflexively probe a voltage without moving the red lead back from the current jack.

Three rules that make it a non-event:

1. **The current jack is a separate physical socket.** Move the lead out of it the instant you finish, before you do anything else. Make it muscle memory.
2. **Current is measured in series; voltage in parallel.** If you did not break the circuit to insert the meter, you are not measuring current.
3. **Start on the high current range** and work down. The µA range usually has the smallest fuse.

The same care applies to `JP6` itself in the other direction: with the jumper removed and no ammeter fitted, the microcontroller simply has no supply, and a perfectly healthy board looks dead. [Reading a Schematic](./schematics-and-board-basics.md) covers where `JP6` sits in the rail chain.
:::

:::tip[Buy in this order, and let frustration choose the next one]
Multimeter, then logic analyzer, then — much later — an oscilloscope. The first two cost about $50 together and cover the overwhelming majority of first-year problems, because the overwhelming majority of first-year problems are "is it connected" and "what did the bus actually send". Buying a scope before you have hit a problem the other two cannot explain means buying an expensive instrument with a steep learning curve for questions you are not yet asking. The moment you *do* hit that problem is recognisable, and it is the right moment to buy.
:::

## See also

- [What Hardware to Buy](./what-hardware-to-buy.md) — the priced starter kit, and what to skip at the start.
- [Signal Integrity and Noise](./signal-integrity-and-noise.md) — the symptom-to-cause table these instruments are used to resolve.
- [How a GPIO Pin Really Behaves](./gpio-electrical-behaviour.md) — leakage, floating inputs, and the sleep-current bugs the ammeter finds.
- [Power Supplies and Regulators](./power-supply-and-regulators.md) — what the rail should measure, and what a sag means.
- [Reading a Schematic](./schematics-and-board-basics.md) — `JP6`, the rail chain, and finding the test point you want to probe.

## References

- STMicroelectronics — [**UM1724**, *STM32 Nucleo-64 boards (MB1136)*](https://www.st.com/resource/en/user_manual/um1724-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf), consulted at **Rev 17** (September 2025). §7.4 "Embedded ST-LINK/V2-1" for the debugger and its mass-storage and VCP interfaces, §7.8 "JP6 (IDD)" for the current-measurement jumper, §7.10 "USART communication" for the virtual COM port, §7.14 for the morpho connector as a probing surface. Rev 17 renumbered this chapter from §6.x to §7.x.
- sigrok — [**PulseView**](https://sigrok.org/wiki/PulseView), [**Protocol decoders**](https://sigrok.org/wiki/Protocol_decoders), and [**fx2lafw**](https://sigrok.org/wiki/Fx2lafw). The open-source capture application, the list of supported protocol decoders (including stacked decoders that turn raw bus traffic into named device registers), and the firmware that makes a generic Cypress FX2 clone usable — with the table of which specific clones work.
- Ben Eater — [*The RS-232 protocol*](https://www.youtube.com/watch?v=AHYNxpqKqwo) and the rest of his serial-communication series at [eater.net](https://eater.net/). The best available demonstration of reading a real signal off a real wire and reconstructing the protocol from it by hand. Watch it before you trust a decoder, because it teaches you what the decoder is doing.
- STMicroelectronics — [**STM32F411xC/E datasheet**](https://www.st.com/resource/en/datasheet/stm32f411re.pdf) (DS10314), consulted at **Rev 8** (January 2024). Tables 22–23 (run current), Table 28 (Stop), Table 30 (Standby) — the numbers your ammeter reading is compared against, and without which the reading means nothing.
