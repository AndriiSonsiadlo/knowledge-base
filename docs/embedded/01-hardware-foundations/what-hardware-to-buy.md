---
id: what-hardware-to-buy
title: What Hardware to Buy
sidebar_label: What Hardware to Buy
sidebar_position: 1
tags: [embedded, hardware, tooling, stm32, nucleo]
---

# What Hardware to Buy

Firmware is the one branch of software engineering where you genuinely cannot do the work on the machine you write the code on. A simulator will run your `main()`, but it will not show you that the sensor holds the clock line low for 40 microseconds longer than the datasheet suggests, that your board browns out when the motor starts, or that the pin you thought was an output has been floating since reset. Every important lesson in this section arrives through a physical board, and the reason newcomers stall here is not the money — the whole kit costs less than a mid-range monitor — but the catalogue. There are hundreds of development boards, every tutorial assumes a different one, and nothing on the vendor's site tells you which one the thing you are reading was written against.

So this page removes the choice. Every hands-on page in this section assumes one specific board, and the rest of the list is the smallest set of instruments that lets you answer the questions that actually come up — is the pin doing what I told it to, is the chip powered, and what did the bus really transmit. Buy this and you are unblocked; add to it later, when a specific frustration tells you which instrument you are missing.

## The board: NUCLEO-F411RE

Order the **NUCLEO-F411RE**. It carries an STM32F411RE — an Arm Cortex-M4 with a single-precision FPU, 512 KB of flash, 128 KB of SRAM, running at up to 100 MHz ([STM32F411xC/E datasheet](https://www.st.com/resource/en/datasheet/stm32f411re.pdf), cover page and Table 14, "General operating conditions") — in a 64-pin LQFP package on a board that ST calls a Nucleo-64.

Three things make it the right first board rather than merely an adequate one:

- **The debugger is already on it.** ST's own words: "The STM32 Nucleo boards do not require any separate probe as they integrate the ST-LINK/V2-1 debugger and programmer" ([UM1724](https://www.st.com/resource/en/user_manual/um1724-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf), Introduction). One USB cable gives you flashing, source-level debugging over SWD, *and* a virtual COM port for `printf` output. This is the single biggest saving on the list — a standalone probe would otherwise be one of the more expensive items.
- **All of the I/O is brought out, on two sets of headers.** The Arduino Uno V3 headers let you plug in off-the-shelf shields; the ST morpho headers beside them expose all of the microcontroller's I/O (UM1724 §6.10, "Extension connectors"). You will use the morpho headers, because the interesting pins are never the Arduino ones.
- **The part is documented to the transistor.** There is a datasheet, an 800-plus-page reference manual, an errata sheet, and a board user manual with full schematics — all free, all from ST. [Reading a Datasheet](./reading-a-datasheet.md) is about navigating exactly this set.

Two things it does *not* have, so you are not surprised later: no Ethernet MAC, and — being a Cortex-M4 rather than an M23/M33 — no Arm TrustZone.

## The kit, with approximate prices

Prices below are approximate, in USD, and were checked in **August 2026**. They move; treat them as an order of magnitude, not a quote.

| Item | Approx. price | What it is for |
|---|---|---|
| **NUCLEO-F411RE** development board | $19 | The target. Debugger included. |
| **USB Type-A to Mini-B cable** | $5 | Power, flashing, debug, and serial console — all over this one cable. |
| Solderless breadboard (830-point) and a jumper-wire assortment | $12 | Everything you wire up for the first few months. |
| Autoranging digital multimeter with a continuity beeper | $30–60 | "Is it powered, is it connected, what voltage is that." |
| Low-cost 8-channel USB logic analyzer | $12–15 | "What did the bus *actually* transmit." |
| Two or three I²C/SPI sensor breakouts (e.g. an environmental sensor and a 6-axis IMU) | $15–25 | Something real to talk to. Pick parts with published datasheets. |
| **Total** | **≈ $90–140** | |

:::tip[Get the cable right]
UM1724 §5.2 specifies a **USB Type-A to Mini-B** cable for the Nucleo-64. Mini-B is the older, wider, trapezoidal connector — not Micro-B, and not USB-C. It is the single most common thing missing from a first order, and the board will not power up without it.
:::

## Why each instrument, and what only it can tell you

These three tools do not overlap as much as they look like they do, and knowing which question belongs to which saves hours of confused staring.

- **The multimeter answers "is this real."** Is 3V3 actually at 3.3 volts? Is this jumper wire actually conducting? Are these two nets shorted together? It is a slow instrument — it tells you about a steady state, not about events — but it is the one that catches the class of problem where no amount of firmware reasoning will help, because the hardware is not what you think it is. Buy an autoranging one with a *fast* continuity beeper; you will use continuity mode more than every other function combined.
- **The logic analyzer answers "what actually went out on the wire."** A debugger tells you what your code believed it sent. A logic analyzer tells you what appeared on the pin, with timing, and decodes it back into I²C addresses or UART bytes. The moment you have a bus that half-works, this is the tool that ends the argument. The cheap 8-channel USB units are built around the Cypress FX2 and are supported by the open-source [`fx2lafw`](https://sigrok.org/wiki/Fx2lafw) firmware, so they work with **sigrok/PulseView** on Linux, macOS, and Windows. At roughly the price of two coffees they are, by a wide margin, the best value on this list.
- **The debugger — already on the board — answers "what is my code doing."** Breakpoints, single-stepping, and reading memory and peripheral registers live. It cannot see anything that happens outside the chip.

## What to skip at the start

- **A separate debug probe.** Redundant. The ST-LINK/V2-1 is on the board (UM1724 §6.2).
- **An oscilloscope.** This is the honest one. A scope shows you *analogue* truth — ringing, slow edges, sagging rails, noise — and none of your first three months of problems will need that. A logic analyzer covers digital timing, and the multimeter covers DC levels. Buy a scope when you hit a problem the other two cannot explain, which is a real and recognisable moment; buying one before that is buying an expensive paperweight with a learning curve.
- **A bench power supply.** USB powers the board. You need a bench supply when you start driving motors or characterising battery behaviour, not before.
- **An expensive logic analyzer.** The $12 unit and the $500 unit tell you the same thing about a 400 kHz I²C bus. The upgrade path, when the cheap one's sample rate or channel count starts biting, is something like a **DSLogic Plus** (about $149) or a **Saleae Logic 8** (about $499, checked August 2026) — but let the frustration come first.
- **A soldering station.** Nothing in this section requires soldering. Add it when you want to build something permanent.

:::warning[The 5 V mistake, which is a real and permanent one]
Most of the STM32F411's I/O pins are marked **FT — "5 V tolerant I/O"** in the datasheet's pinout table, and beginners read that as "this board is fine with 5 V." Three separate qualifications make that dangerous:

1. **Not all pins are FT.** On the STM32F411, `PA0-WKUP` and `PB5` are marked **TC — "Standard 3.3 V I/O"** (STM32F411xC/E datasheet, Table 7 legend and Table 8, "Pin definitions"). `PB5` is Arduino pin **D4** on this board (UM1724, Table 16), so it is on a header a beginner will absolutely use. Driving 5 V into it exceeds the absolute maximum rating of `VSS − 0.3 V` to `4.0 V` for a non-FT pin (datasheet Table 11, "Voltage characteristics") and can destroy the pin.
2. **FT tolerance does not survive every mode.** The datasheet's own footnote to Table 8 reads: "FT = 5 V tolerant except when in analog mode or oscillator mode." A 5 V-tolerant pin configured as an ADC input is no longer 5 V tolerant.
3. **FT tolerance requires the internal pull-ups off.** Datasheet Table 53, note 5: "To sustain a voltage higher than V<sub>DD</sub> +0.3 V, the internal pull-up/pull-down resistors must be disabled."

The practical rule: buy **3.3 V** sensor breakouts, or breakouts with an on-board regulator and level shifter, and treat 5 V as something the board *outputs* to a shield rather than something you feed back into it. [Voltage Levels and Logic](./voltage-levels-and-logic.md) works through the numbers.
:::

## Where to buy

Order the board from a distributor that carries genuine ST stock — DigiKey, Mouser, Farnell/Newark, RS, or ST's own eStore. Nucleo boards are cloned, and a clone with a non-genuine ST-LINK will eventually refuse a firmware upgrade or fail to enumerate. The breadboard, wires, multimeter, and logic analyzer can come from anywhere; the sensors should come with a part number you can look up, because a breakout board with no identifiable chip on it is a breakout board you cannot write a driver for.

## See also

- [Reading a Datasheet](./reading-a-datasheet.md) — the four ST documents for this board, and how to find one register in eight hundred pages.
- [Reading a Schematic](./schematics-and-board-basics.md) — what the jumpers, solder bridges, and LEDs on the board you just ordered actually do.
- [Voltage Levels and Logic](./voltage-levels-and-logic.md) — the numbers behind the 5 V warning above, taken from the datasheet's I/O tables.
- [Microcontroller, Microprocessor, SoC](../00-overview/microcontroller-vs-microprocessor-vs-soc.md) — what class of part the STM32F411RE is, and what that rules in and out.
- [Embedded Systems](../readme.md) — the section index and its learning paths.

## References

- STMicroelectronics — [**UM1724**, *STM32 Nucleo-64 boards (MB1136)*](https://www.st.com/resource/en/user_manual/um1724-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf). The board's own manual: jumper defaults, power options, LED and button pin assignments, connector pinouts, and full schematics. The revision consulted here is Rev 12 (DocID025833). Read §5.1 "Getting started" before you plug anything in.
- STMicroelectronics — [**STM32F411xC/E datasheet**](https://www.st.com/resource/en/datasheet/stm32f411re.pdf) (DS10314; the revision consulted here is Rev 7, DocID026289). Table 7 and Table 8 carry the FT/TC per-pin markings that the 5 V warning above depends on.
- STMicroelectronics — [NUCLEO-F411RE product page](https://www.st.com/en/evaluation-tools/nucleo-f411re.html). Current ordering information, board revision notes, and the full document set in one place; check it for the latest revisions of everything cited here.
- sigrok — [**fx2lafw**](https://sigrok.org/wiki/Fx2lafw) and [PulseView](https://sigrok.org/wiki/PulseView). The open-source firmware and capture software that turn a generic $12 FX2-based analyzer into a usable instrument, with the list of clones known to work.
- Elecia White, *Making Embedded Systems* (O'Reilly) — a purchase, not free. The best first book on the discipline, and useful here for its framing of what a development setup is actually for.
