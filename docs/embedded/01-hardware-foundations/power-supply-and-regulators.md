---
id: power-supply-and-regulators
title: Power Supplies and Regulators
sidebar_label: Power Supplies and Regulators
sidebar_position: 7
tags: [embedded, hardware, power, regulators, stm32, nucleo]
---

# Power Supplies and Regulators

Firmware is written as though the supply rail were a constant — a number in the datasheet, `3.3 V`, always there. The rail is not a constant. It is the output of a control loop with finite bandwidth, fed through traces with real resistance and inductance, feeding a load whose current draw your own code is modulating thousands of times a second. Every time the CPU switches from an idle loop to a burst of floating-point work, every time a GPIO drives an LED, every time the chip wakes from Stop mode, the load steps and the rail moves.

Most of the time that movement is small enough not to matter. The reason to understand it anyway is that when it *does* matter, the symptom is never "the power supply is bad." The symptom is a peripheral that misbehaves at one clock speed and not another, a flash write that corrupts a page, a board that runs perfectly on your desk and resets every few minutes in the field. Those are power problems wearing firmware costumes, and they are only diagnosable if you already know what a supply rail is made of.

:::info[Prerequisites]
[Reading a Schematic](./schematics-and-board-basics.md) traces the Nucleo's rails end to end — `USB → JP5 → +5V → U4 → SB2 → +3V3 → JP6 → VDD` — and covers decoupling capacitors. This page starts one level up: what the regulator itself is doing, what it costs, and how the chip behaves when the rail leaves its window.
:::

## What a regulator is actually being asked to do

A regulator takes an input voltage that varies — a USB port that sags, a battery that falls from 4.2 V to 3.0 V over its discharge — and holds an output voltage steady while the load underneath it changes. Two families do this, and they fail in different ways.

A **linear regulator**, of which the low-dropout (LDO) is the modern form, is a variable resistor in a feedback loop. It burns the difference between input and output as heat. That makes it simple, quiet, and cheap, and it makes its efficiency a fixed function of the voltage ratio: pushing 300 mA from 5 V down to 3.3 V dissipates `(5 − 3.3) × 0.3 ≈ 0.51 W` in the regulator package, no matter how good the part is.

A **switching regulator**, in the step-down (buck) form, chops the input with a transistor and averages the result through an inductor and capacitor. Energy that a linear part would have burned is instead stored and delivered, so efficiency is set by switching and conduction losses rather than by the voltage ratio — 85–95% is ordinary. The price is an inductor, a more complex control loop, and a switching node that is a deliberate square-wave noise source sitting on your board.

## LDO versus buck, with real parts

The abstract comparison is less useful than two specific devices. The left column is the LDO actually fitted to your Nucleo; the right is a low-power buck chosen because it breaks the oldest rule of thumb about switchers.

| | **LDO** — ST LD39050PU33R | **Buck** — TI TPS62740 |
|---|---|---|
| Fitted where | `U4` on the Nucleo-64, the `+5V → +3V3` step (UM1724 Rev 17, Table 10, `SB2` row) | Battery-powered designs; not on this board |
| Principle | Series pass element in a feedback loop; the difference is dissipated | Transistor chops the input; `L` and `C` average it |
| Input range | `1.5 V` to `5.5 V` (DocID15470 Rev 5, Features) | `2.2 V` to `5.5 V` (SLVSB02B Rev B, §1) |
| Output current | `500 mA` guaranteed | up to `300 mA` |
| Efficiency, 5 V → 3.3 V | ≈ V<sub>OUT</sub>/V<sub>IN</sub> = **66%** — the rest is heat | up to **90%**, and TI specifies that figure holding down to `10 µA` of load |
| Quiescent current | `20 µA` typ. at no load, `100 µA` typ. at 500 mA, `1 µA` max. in OFF mode | `360 nA` typ. |
| Dropout | `200 mV` typ. at 500 mA | n/a — enters a non-switching 100% duty mode as V<sub>IN</sub> approaches V<sub>OUT</sub> |
| Output noise | "very low noise without bypass capacitor" | ripple at the switching frequency, up to `2 MHz` |
| External parts | one capacitor in, one `1 µF` ceramic out | `2.2 µH` inductor plus `10 µF` output capacitor |
| Choose it when | the drop is small, the load is modest, or the rail feeds analog | the drop is large, the load is large, or the energy comes from a battery |

Two things in that table are worth stopping on.

**Efficiency is not the only cost of an LDO.** It is also a *thermal* cost. The Nucleo's `U4` running a 300 mA shield off the 5 V rail is dissipating roughly half a watt into a DFN6 package the size of a grain of rice. The LD39050 has an internal thermal limit and will fold back rather than destroy itself, but a board that quietly current-limits under load is a board with an intermittent fault, not a board that is fine.

**"Switchers have terrible quiescent current" is out of date.** It was true, and it is the reason a generation of engineers reached for an LDO in every battery design. The TPS62740's `360 nA` is over fifty times *lower* than the LD39050's no-load `20 µA`. If your product spends 99.9% of its life asleep, that difference dominates the entire energy budget — and it points the opposite way from the folklore.

## Where the Nucleo's own power budget goes

The same board's numbers make the shape of the problem concrete. All of these are from the STM32F411xC/E datasheet (DS10314 Rev 8) at T<sub>A</sub> = 25 °C:

| Mode | Typical I<sub>DD</sub> | Source |
|---|---|---|
| Run, 100 MHz from flash, ART on, all peripherals enabled | `20.7 mA` | Table 23 (V<sub>DD</sub> = 3.6 V) |
| Run, 100 MHz from flash, ART on, all peripherals disabled | `11.6 mA` | Table 23 |
| Run, 16 MHz HSI, PLL off, all peripherals disabled | `1.9 mA` | Table 23 |
| Stop, flash in deep power-down, low-power low-voltage regulator | `10 µA` | Table 28 |
| Standby, LSE and RTC on | `2.8 µA` | Table 30 |
| Standby, RTC and LSE off | `2.1 µA` | Table 30 |
| **In-rush** at regulator power-on (POR, or wakeup from Standby) | `160 mA` typ., `200 mA` max | Table 19 |

Read the first and last rows together. The chip's *steady* draw at full tilt is about 21 mA. Its *transient* draw the instant the internal 1.2 V regulator starts up is up to 200 mA — an order of magnitude more. Table 19 also gives the in-rush *energy*, `5.4 µC`, under the stated condition "V<sub>DD</sub> = 1.7 V, T<sub>A</sub> = 125 °C, I<sub>RUSH</sub> = 171 mA for 31 µs" — so ST's own characterisation point puts the spike in the tens of microseconds, not the milliseconds. A supply sized for the average will brown out on that spike, and it will do so at exactly the moment you can least observe it: before any of your code has run.

And read the run and standby rows together: a factor of about ten thousand separates them. This is why regulator quiescent current is not a rounding error. A regulator that idles at 100 µA in a system whose sleeping microcontroller draws 2.8 µA is spending 97% of the sleep budget on the regulator.

## What the chip does when the rail goes wrong

The STM32F411 does not simply stop when its supply sags — it has three separate supervisors watching V<sub>DD</sub>, and knowing which one is armed matters. All thresholds below come from DS10314 Rev 8, §6.3.5, Table 19 "Embedded reset and power control block characteristics".

- **POR/PDR — power-on/power-down reset.** Always active. The device is held in reset below `V_POR/PDR`: `1.68 V` typical on a falling edge, `1.72 V` typical rising. This is the floor; it exists so that the part never executes instructions on a rail too low to be trustworthy.
- **BOR — brownout reset.** Three selectable thresholds, chosen through the option bytes: `2.19 V` (BOR level 1), `2.50 V` (level 2), `2.83 V` (level 3), each typical on a falling edge, each with `100 mV` of hysteresis. The datasheet's §3.15.1 describes the sequence: POR ensures operation from 1.8 V, "after the 1.8 V POR threshold level is reached, the option byte loading process starts, either to confirm or modify default thresholds, or to disable BOR permanently."
- **PVD — programmable voltage detector.** Eight software-selectable levels from `2.14 V` to `3.14 V` typical (rising edge), with `100 mV` of hysteresis. Unlike the other two, the PVD does not reset anything: it raises an interrupt. The datasheet's framing is exactly right — "the interrupt service routine can then generate a warning message and/or put the MCU into a safe state."

The PVD is the interesting one for firmware, because it is the only supervisor that gives you a *chance to act*. A board that can detect its rail falling through 2.9 V while it still has a working 3.3 V regulator output has a window — short, but real — to abandon a flash write, park a motor, or flush a log.

:::warning[The board that works on USB and dies on a battery]
This is the single most common power surprise, and it has four independent causes that all present as "it worked yesterday on my desk."

1. **The USB port was supplying more current than your battery can.** UM1724 Rev 17, §7.5.1: the Nucleo requests `300 mA` during enumeration, and if the host grants it, "the STM32 Nucleo board and its shield can consume a maximum of 300 mA current, not more." A CR2032 coin cell cannot deliver a tenth of that, and its terminal voltage collapses when you ask.
2. **Nothing was watching the rail.** DS10314 Rev 8, Appendix A states plainly: **"By default BOR is OFF."** On a fresh part only the POR/PDR is guarding you, so the chip will happily keep executing down to about 1.7 V — through the region where flash programming is out of specification and peripheral behaviour is undefined. Set a BOR level in the option bytes for anything battery-powered.
3. **The in-rush spike was invisible on USB.** A host port sourcing 500 mA does not notice the `200 mA` peak of Table 19. A near-empty battery through a few hundred milliohms of internal resistance does, and the resulting sag can drop the rail below POR — producing a *reset loop* that looks exactly like a firmware crash at startup.
4. **The regulator's quiescent current is now a significant load.** Irrelevant on a bench supply; potentially the largest single consumer in a sleeping battery product.

The diagnostic that separates these from firmware bugs takes about a minute: put a multimeter on the 3V3 rail and watch it while the symptom happens, then read the reset reason out of `RCC_CSR` after the fact. [Reset and Boot Configuration](./reset-and-boot-configuration.md) covers reading those flags, and [Lab Equipment and What It Answers](./lab-equipment.md) covers seeing the sag itself.
:::

## The analog rail is a separate problem

On the LQFP64 package that the Nucleo carries, pin 13 is labelled **`VDDA/VREF+`** and pin 12 **`VSSA/VREF-`** (DS10314 Rev 8, Table 8 "Pin definitions"). The ADC's reference voltage and its analog supply are the same physical pin. On this board that pin reaches the ordinary `+3V3` rail through solder bridge `SB57`, which UM1724 Rev 17, Table 10 documents as "V<sub>DDA</sub>/V<sub>REF+</sub> on STM32 is connected to V<sub>DD</sub>" when fitted.

The consequence is direct: **every millivolt of noise on the 3.3 V rail is a millivolt of error in every ADC reading.** The datasheet is correspondingly firm about decoupling (§6.3.20, "General PCB design guidelines"): "Power supply decoupling should be performed as shown in Figure 42 or Figure 43… The 10 nF capacitors should be ceramic (good quality). They should be placed them as close as possible to the chip." Figure 43, the case that applies here, specifies `1 µF` in parallel with `10 nF` on the `VREF+/VDDA` pin.

This is also the reason the LDO/buck choice is not purely an efficiency question. A switching regulator puts ripple at its switching frequency onto the rail; if that rail is also your ADC reference, you have chosen to inject a periodic error into every measurement. The usual answer in a mixed design is a buck for the bulk conversion and a small LDO downstream of it feeding the analog rail — the buck for efficiency, the LDO for quiet. [Analog Basics: ADC and DAC](./analog-basics-adc-and-dac.md) works through what that error actually costs in bits.

## Reading the board's own supply table as an engineering document

UM1724 Rev 17, Table 7 "External power sources" lists the Nucleo's `VIN` input as accepting 7 V to 12 V, with a maximum input current that *falls as the input voltage rises*:

| V<sub>IN</sub> | Max input current (UM1724 Rev 17, Table 7) |
|---|---|
| 7 V | 800 mA |
| 7 V < V<sub>IN</sub> ≤ 9 V | 450 mA |
| 9 V < V<sub>IN</sub> ≤ 12 V | 250 mA |

Multiply each row out against the 5 V rail the on-board regulator produces and the pattern is unmistakable: `(7−5) × 0.8 = 1.6 W`, `(9−5) × 0.45 = 1.8 W`, `(12−5) × 0.25 = 1.75 W`. The limit is not a current limit at all — it is a **constant power-dissipation budget of roughly 1.6 to 1.8 W** in a linear regulator. (The arithmetic is inference from Table 7's own numbers, not a figure ST prints; the table is what is sourced.)

That is worth internalising as a habit, because it generalises. When a vendor's table has a shape you did not expect, the shape usually *is* the specification — the physical constraint the designer was working against, showing through the numbers. Reading it that way tells you something no sentence in the manual says: feed this board 12 V and you have two thirds less current available than at 7 V, because the extra volts are being turned into heat.

## See also

- [Reading a Schematic](./schematics-and-board-basics.md) — the Nucleo's rail chain traced component by component, the jumpers that select it, and what decoupling capacitors are for.
- [Reset and Boot Configuration](./reset-and-boot-configuration.md) — what POR, BOR, and the reset flags do with the supervisor thresholds on this page.
- [Analog Basics: ADC and DAC](./analog-basics-adc-and-dac.md) — why V<sub>DDA</sub> being the ADC reference turns rail noise into measurement noise.
- [Lab Equipment and What It Answers](./lab-equipment.md) — the instruments that let you see a sag, a spike, or a quiescent current rather than infer them.
- [Glossary](../00-overview/glossary.md) — brownout, and the other terms this folder assumes.

## References

- STMicroelectronics — [**STM32F411xC/E datasheet**](https://www.st.com/resource/en/datasheet/stm32f411re.pdf) (DS10314), consulted at **Rev 8** (January 2024). §3.14 power supply schemes, §3.15 power supply supervisor, §6.1.6 and Figure 17 power supply scheme, §6.3.5 Table 19 for every POR/PDR, BOR, PVD and in-rush figure quoted, Tables 22–23 run current, Table 28 Stop current, Table 30 Standby current, Table 8 pin definitions, and Appendix A for "By default BOR is OFF".
- STMicroelectronics — [**UM1724**, *STM32 Nucleo-64 boards (MB1136)*](https://www.st.com/resource/en/user_manual/um1724-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf), consulted at **Rev 17** (September 2025). §7.5 "Power supply and power selection" for the USB/VIN/E5V/+3.3V options and the 300 mA enumeration limit, Table 6 (`JP1`), Table 7 (external power sources), Table 8 (`JP5`), Table 9 (+3.3 V input), and Table 10 (solder bridges, including `SB2` naming the regulator and `SB57` tying V<sub>DDA</sub> to V<sub>DD</sub>). Note that Rev 17 renumbered the hardware-configuration chapter from §6.x to §7.x; older write-ups citing "§6.5" mean this section.
- STMicroelectronics — [**LD39050 datasheet**](https://www.st.com/resource/en/datasheet/ld39050.pdf) (DocID15470 Rev 5, December 2019). The part fitted as `U4`. Its Features page carries the dropout, quiescent-current, tolerance and output-capacitor figures used in the comparison table; the electrical tables behind them are the authority if you need limits rather than typicals.
- Texas Instruments — [**TPS62740 / TPS62742 datasheet**](https://www.ti.com/lit/ds/symlink/tps62740.pdf) (SLVSB02B, revised July 2014). Chosen as the buck counterexample: §1 Features and §8 for the 360 nA quiescent current, the up-to-90%-at-10 µA efficiency claim, and the DCS-Control PFM/PWM behaviour that produces it.
- Analog Devices — [**MT-101**, *Decoupling Techniques*](https://www.analog.com/media/en/training-seminars/tutorials/MT-101.pdf) (Rev. 0). Why a bulk capacitor and a small ceramic are not redundant, how ESL sets a capacitor's self-resonant frequency, and why the connection to the ground plane is part of the component. The best short treatment of why "just add a capacitor" is not advice.
