---
id: voltage-levels-and-logic
title: Voltage Levels and Logic
sidebar_label: Voltage Levels and Logic
sidebar_position: 4
tags: [embedded, hardware, electronics, gpio, stm32]
---

# Voltage Levels and Logic

There is no `1` on a wire. There is a voltage, and there is a receiver that has decided in advance which range of voltages it will call one and which it will call zero. Digital logic is an *agreement* layered on top of an analogue quantity, and the reason firmware normally gets to ignore that is that the agreement usually holds — the hardware on both ends was designed to the same convention, so the bits you read are the bits that were sent.

What makes this worth a page is the failure mode when the agreement breaks. A misconfigured, floating, or badly-matched input does not throw an exception. It hands your code a value, confidently, that has nothing to do with the world. You get a sensor that reports plausible garbage, a button that presses itself, a bus that decodes to nonsense — all with no diagnostic anywhere, because from the microcontroller's point of view nothing went wrong. Knowing where the thresholds are is what lets you look at a symptom and say "that is an electrical problem, stop reading the code."

## The thresholds on this part

The NUCLEO-F411RE runs its STM32F411RE at **3.3 V** — an on-board `LD39050PU33R` LDO regulator supplies the `+3V3` rail (UM1724, Table 10, `SB2`). The chip itself is specified from `1.7 V` to `3.6 V` (STM32F411xC/E datasheet, Table 14, "General operating conditions"), and — importantly — its input thresholds are expressed as *fractions of V<sub>DD</sub>*, not as fixed voltages.

| Parameter | Symbol | Datasheet value | At V<sub>DD</sub> = 3.3 V | Source |
|---|---|---|---|---|
| Input low level (guaranteed read as `0`) | V<sub>IL</sub> | ≤ 0.3 × V<sub>DD</sub> | ≤ 0.99 V | Table 53, "I/O static characteristics" |
| Input high level (guaranteed read as `1`) | V<sub>IH</sub> | ≥ 0.7 × V<sub>DD</sub> | ≥ 2.31 V | Table 53 |
| Input hysteresis | V<sub>HYS</sub> | 10% of V<sub>DD</sub> typical, minimum 200 mV | ≈ 0.33 V | Table 53 and its note 3 |
| Input leakage current | I<sub>lkg</sub> | ±1 µA max, for V<sub>SS</sub> ≤ V<sub>IN</sub> ≤ V<sub>DD</sub> | ±1 µA | Table 53 |
| Output low level, sinking 8 mA | V<sub>OL</sub> | ≤ 0.4 V (for 2.7 V ≤ V<sub>DD</sub> ≤ 3.6 V) | ≤ 0.4 V | Table 54, "Output voltage characteristics" |
| Output high level, sourcing 8 mA | V<sub>OH</sub> | ≥ V<sub>DD</sub> − 0.4 V (same conditions) | ≥ 2.9 V | Table 54 |
| Output low level, sinking 20 mA | V<sub>OL</sub> | ≤ 1.3 V | ≤ 1.3 V | Table 54 |
| Output high level, sourcing 20 mA | V<sub>OH</sub> | ≥ V<sub>DD</sub> − 1.3 V | ≥ 2.0 V | Table 54 |

Three consequences worth internalising:

**There is a band in the middle where nothing is guaranteed.** Between `0.99 V` and `2.31 V` on a 3.3 V system, the datasheet promises nothing about what the pin reads. It will read *something* — inputs are digital, they produce a bit — but which bit is not specified, may differ between two pins on the same chip, and may change with temperature. This band is 40% of the supply range, which is much wider than most people's intuition, and it is why "the voltage looked about right on the meter" is not a diagnosis.

**Noise margin is the gap between what a driver guarantees and what a receiver requires.** An STM32 output sinking 8 mA guarantees at most `0.4 V`; an STM32 input accepts anything up to `0.99 V` as low. The difference — about `0.59 V` — is how much noise the connection can pick up before a `0` stops reading as a `0`. Push the same pin to 20 mA and `V_OL` is allowed to rise to `1.3 V`, which is *above* the receiver's `V_IL` limit. Driving hard enough and reading the same net is a real way to build a link with no margin at all.

**Hysteresis is why a slowly-changing input does not produce a burst of edges.** The input stage is a Schmitt trigger: the threshold for a low-to-high transition sits higher than the threshold for high-to-low, separated by V<sub>HYS</sub> — typically 10% of V<sub>DD</sub>, and at least 200 mV (datasheet Table 53, note 3). A signal that drifts slowly through the middle of the band therefore switches once and stays switched, rather than chattering. It is a small piece of hardware doing debouncing you would otherwise have to write.

## Interfacing 3.3 V and 5 V: two different problems

The two directions fail differently, and only one of them destroys hardware.

| Direction | What happens | Verdict |
|---|---|---|
| **5 V device output → STM32 input** | The 5 V driver puts up to 5 V on an STM32 pin. Survivable *only* if the pin is 5 V-tolerant, and only under the conditions below. | Dangerous. Check the pin. |
| **STM32 output → 5 V device input** | The STM32 sources at most V<sub>DD</sub>, about 3.3 V. Nothing is damaged; the question is only whether the receiver reads it as a `1`. | Safe, but may not work. Check the receiver's V<sub>IH</sub>. |

For the second direction, the arithmetic is the same arithmetic as above, applied to the other chip. A 5 V CMOS receiver following the same `0.7 × V_DD` convention the STM32 uses needs at least `3.5 V` to see a `1` — more than a 3.3 V driver can produce, so the link does not work even though nothing is harmed. A 5 V part with TTL-style input levels has a much lower V<sub>IH</sub> and will read 3.3 V fine. There is no way to know which you have without opening the receiving part's own datasheet and reading its V<sub>IH</sub> line. Do that; do not assume.

### What "5 V tolerant" actually buys you on this part

The datasheet classifies every pin by its **I/O structure**, and the legend has exactly four entries (Table 7, "Legend/abbreviations used in the pinout table"):

| Code | Definition, verbatim |
|---|---|
| `FT` | 5 V tolerant I/O |
| `TC` | Standard 3.3 V I/O |
| `B` | Dedicated BOOT0 pin |
| `NRST` | Bidirectional reset pin with embedded weak pull-up resistor |

Only `FT` means 5 V tolerant. `TC` is an ordinary 3.3 V pin, and there is no third grade in between.

Going through Table 8 ("STM32F411xC/xE pin definitions") row by row, this part has **80 I/O rows: 78 are `FT` and exactly two are `TC`** — **`PA0-WKUP`** and **`PB5`**. Both of the two are on the Nucleo's Arduino headers: `PA0` is **`A0`** (`CN8` pin 1, `ADC1_0`) and `PB5` is **`D4`** (`CN9` pin 5), per UM1724 Rev 17, Table 16, "Arduino connectors on NUCLEO-F401RE and NUCLEO-F411RE". The two pins least able to take 5 V are precisely the two a beginner reaches for first.

Even on the 78 `FT` pins the tolerance is fenced by two conditions people routinely miss:

1. **It does not apply in every mode.** Table 8's own note 4 reads: "FT = 5 V tolerant except when in analog mode or oscillator mode (for PC14, PC15, PH0 and PH1)." Configure an `FT` pin as an ADC input and its 5 V tolerance is gone.
2. **The internal pull resistors must be off.** Table 53, note 5: "To sustain a voltage higher than V<sub>DD</sub> +0.3 V, the internal pull-up/pull-down resistors must be disabled."

Even within spec, an `FT` pin at 5 V is not free: the datasheet's leakage row for `V_IN = 5 V` allows up to `3 µA`, against `±1 µA` within the normal range (Table 53). That row is titled "I/O FT/TC input leakage current" and names both structures, but a leakage figure is not a tolerance rating — what makes a pin 5 V tolerant is the `FT` marking in Table 7 and nothing else.

:::warning[The datasheet is ambiguous about `TC` pins, so treat them as 3.3 V]
This is the one place where DS10314 does not agree with itself, and it is worth seeing the disagreement rather than being handed a rule.

The **Table 7 legend** classifies the pin: `FT` = "5 V tolerant I/O", `TC` = "Standard 3.3 V I/O". That is the only place in the document that distinguishes them.

Every table that carries a *number*, however, groups them together:

| Table | What it says about `TC` |
|---|---|
| Table 11, "Voltage characteristics" (absolute maximum) | V<sub>IN</sub> "on FT and TC pins" is `V_SS − 0.3 V` to `V_DD + 4.0 V` |
| Table 12, "Current characteristics" (absolute maximum) | Injected current "on FT and TC pins" is `−5/+0 mA` |
| Table 14, "General operating conditions" | V<sub>IN</sub> "on RST, FT and TC pins" is `−0.3` to **`5.5 V`** for `2 V ≤ V_DD ≤ 3.6 V`, with footnote 6: "To sustain a voltage higher than V<sub>DD</sub>+0.3, the internal Pull-up and Pull-Down resistors must be disabled" |

Table 14 is the operating-conditions table — the "where the part is guaranteed to work" table described in [Reading a Datasheet](./reading-a-datasheet.md). Read literally, it does permit 5 V on a `TC` pin. So it is not true that the datasheet is silent on the question; it is that the datasheet answers it two different ways.

**Obey the Table 7 legend.** It is the classification ST states per pin and per structure, it is the more conservative of the two readings, and the cost of being wrong is asymmetric: following the legend on an `FT` pin costs you nothing, while following Table 14 on a `TC` pin risks a pin that the part's own pinout table says is a standard 3.3 V I/O. Concretely: do not feed 5 V into `PA0-WKUP` or `PB5`. Level-shift instead, as below.

Beyond the classification, everything past V<sub>DD</sub> + 0.3 V on *any* pin is fenced by the same current limits, and that is where the real damage happens.

What happens above V<sub>DD</sub> is that the pin's internal protection diode to V<sub>DD</sub> starts conducting, and current flows *into the chip's supply rail through your signal wire*. That current is not something you have a budget to spend: Table 12 ("Current characteristics") allows **at most `−5 mA` and no positive injection at all** on `FT` and `TC` pins, `±25 mA` summed over every pin — and these are absolute maximum ratings, which the datasheet itself frames as "stress ratings only… functional operation of the device at these conditions is not implied" (§6.2). Table 52 ("I/O current injection susceptibility") is stricter still per pin: for `PB5`, along with `PB3`, `PB4`, `PB6`–`PB9`, `PC13`–`PC15` and others, the permitted negative injection is `−0 mA` — none.

So the correct reading is "design for no injected current". For the pins Table 52 lists at `−0 mA`, `PB5` among them, that is literally the number. For the rest, `PA0-WKUP` included, `−5 mA` is an absolute maximum rather than a design allowance — the same section that publishes it calls it a stress rating. Inject anyway and you get some combination of a dead pin, a chip that resets at random, an ADC that reads wrong on completely unrelated channels — the datasheet warns explicitly that "negative injection disturbs the analog performance of the device" — or a part that works today and fails in three weeks.

That last outcome is the dangerous one, because it teaches the wrong lesson. "I connected a 5 V sensor and it worked fine" is not evidence that it was safe. **Check the `FT`/`TC` marking for the specific pin, in Table 8, before you connect anything that is not 3.3 V.**
:::

## Getting between the two: level shifting

When you genuinely must connect a 3.3 V part to a 5 V part, there are three approaches, in rough order of how often you should reach for them.

- **Open-drain plus a pull-up to the lower rail.** If both ends can be configured as open-drain — which is what I²C requires anyway — neither ever drives the line high. A single pull-up resistor to 3.3 V sets the high level for the whole bus, and both parts happily pull it down. No extra components, no direction logic. This is the reason the open-drain output stage exists, and it is covered in [How a GPIO Pin Really Behaves](./gpio-electrical-behaviour.md).
- **A dedicated level-shifter IC.** For unidirectional signals a buffer from a family like `74LVC` translates cleanly and fast. For bidirectional lines there are purpose-built parts (the `TXS`/`TXB` families, and the classic single-MOSFET-per-line circuit) that handle direction without being told. This is the correct answer for anything fast or anything you are going to ship.
- **A resistive divider.** Two resistors dropping 5 V to roughly 3.3 V. It works, it costs nothing, and it is limited to *slow, one-directional, input-only* signals — the divider's source impedance combines with the receiver's input capacitance (`5 pF` typical for this part, datasheet Table 53) and the wiring to round off the edges. Acceptable for a pushbutton, not for a 1 MHz SPI clock.

Never solve this with "it's only a bit over, it'll be fine."

## What a floating input actually reads

A pin configured as an input with no pull-up, no pull-down, and nothing driving it is **floating** — a high-impedance node connected to essentially nothing. It is not `0`. It is not `1`. It is a tiny capacitor holding whatever charge last landed on it, coupling in from every nearby switching signal and from the mains hum in the room.

In practice a floating input:

- reads a value, always, with no indication that the value is meaningless;
- may read *consistently* on your desk and differently on someone else's, which is how a bug survives review;
- changes when you bring your hand near the board — the classic diagnostic, and a genuinely useful one;
- can oscillate, if the pin is near the switching threshold, producing edges that fire interrupts that nothing physically caused;
- **costs power**, because an input sitting mid-rail leaves both transistors of the input stage partly conducting. This is why low-power design guides insist that unused pins be driven or pulled rather than left floating.

This is not an exotic condition. RM0383 §8.3.1 is explicit that "during and just after reset, the alternate functions are not active and the I/O ports are configured in input floating mode" — floating is the **default state of almost every pin on the chip** until your firmware says otherwise.

The fix is to give the net a defined idle state. The STM32 has internal pull-up and pull-down resistors on every GPIO, selected by `GPIOx_PUPDR` (RM0383 §8.3.3, "I/O port control registers"), with an equivalent resistance of `30–50 kΩ`, typically `40 kΩ` (datasheet, Table 53). That is weak — fine for a button, too weak for a fast bus or a noisy environment, where an external resistor of a few kilohms is the right answer.

:::tip[The hand test]
If a reading changes when you wave your hand near a wire, that net is floating or very high impedance. It takes two seconds and it separates "my code is wrong" from "my circuit is wrong" faster than any amount of stepping through a debugger.
:::

## See also

- [How a GPIO Pin Really Behaves](./gpio-electrical-behaviour.md) — the output stages, internal pull resistors, and drive strengths behind the numbers on this page.
- [Reading a Datasheet](./reading-a-datasheet.md) — how to find Tables 11, 12, 53, and 54 in the document they came from.
- [Reading a Schematic](./schematics-and-board-basics.md) — tracing which rail a given pin is actually referenced to.
- [What Hardware to Buy](./what-hardware-to-buy.md) — why the shopping list says "3.3 V sensor breakouts".
- [Glossary](../00-overview/glossary.md) — the surrounding vocabulary, defined once.

## References

- STMicroelectronics — [**STM32F411xC/E datasheet**](https://www.st.com/resource/en/datasheet/stm32f411re.pdf) (DS10314). Table 11 voltage absolute maximum ratings, Table 12 current absolute maximum ratings, Table 14 general operating conditions, Table 52 I/O current injection susceptibility, Table 53 I/O static characteristics, Table 54 output voltage characteristics, Table 7 legend and Table 8 per-pin `FT`/`TC` markings. Every number on this page comes from here; the revision consulted was **DS10314 Rev 8** (January 2024).
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), §8.3.1 for the reset state of the I/O ports and §8.3.3 for the `GPIOx_PUPDR` control of the internal pull resistors. Consulted at Rev 4 (May 2025).
- STMicroelectronics — [**UM1724**, *STM32 Nucleo-64 boards (MB1136)*](https://www.st.com/resource/en/user_manual/um1724-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf), §7.5 "Power supply and power selection" and Table 16 "Arduino connectors on NUCLEO-F401RE and NUCLEO-F411RE". Which rail the board actually runs at, and which header pin is which microcontroller pin. Consulted at Rev 17 (September 2025).
- Ben Eater — [Digital logic on a breadboard](https://eater.net/) video series. Free. Watching a logic level be built out of transistors, on real hardware, makes the threshold tables stop feeling arbitrary.
