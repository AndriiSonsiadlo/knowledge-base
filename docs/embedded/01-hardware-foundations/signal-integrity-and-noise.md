---
id: signal-integrity-and-noise
title: Signal Integrity and Noise
sidebar_label: Signal Integrity and Noise
sidebar_position: 10
tags: [embedded, hardware, signal-integrity, emi, grounding]
---

# Signal Integrity and Noise

A schematic draws a wire as a line with no properties. That abstraction holds beautifully for DC and falls apart on the edges — the few nanoseconds after a driver switches, when the wire is not a connection but a *component*, with inductance, capacitance, a characteristic impedance and a finite speed. For most of the time your signal is idle and the abstraction is fine. For the small fraction of time when it is changing, the wire is the circuit.

This matters to a firmware engineer for one specific reason: the symptoms are indistinguishable from software bugs. A bus that works at 100 kHz and fails at 400 kHz. A sensor that reads correctly until the motor starts. A board that passes every test on your desk and comes back from the field with intermittent faults nobody can reproduce. None of those look electrical. All of them can be. The value of this page is not that it will make you a PCB designer — it is that it will let you recognise, quickly, when you are debugging the wrong layer.

:::info[Prerequisites]
[Voltage Levels and Logic](./voltage-levels-and-logic.md) covers the thresholds a receiver uses to decide high from low, which is what ringing threatens. [How a GPIO Pin Really Behaves](./gpio-electrical-behaviour.md) covers `OSPEEDR`, the slew-rate control that is your main firmware-side lever here.
:::

## The three things a wire does that a line on a schematic does not

**It takes time.** Signals propagate at a fraction of the speed of light set by the dielectric around them. TI's SCAA082A Rev A, Table 2 gives measured figures for a 100 mm FR-4 trace: a microstrip carries a signal at about `171.9 mm/ns` (a propagation delay of `582 ps` per 100 mm), and a stripline — surrounded by dielectric on both sides rather than air above — at about `139.8 mm/ns` (`715 ps` per 100 mm).

Put that next to an edge rate. The STM32F411 at its fastest `OSPEEDR` setting produces rise and fall times of `4 ns` or less into a 30 pF load (DS10314 Rev 8, Table 55). A 4 ns edge is therefore about **690 mm long** on a microstrip — physically spread over more than half a metre of copper. Anything much shorter than that behaves like a lumped connection; anything comparable to it does not. SCAA082A §1.3 puts the criterion generally: "If the lengths of traces are in the range of the signal's wavelength, then the user has to consider the effects of transmission lines."

**It reflects.** Wherever the impedance changes — a connector, a via, a stub, the high-impedance input of a receiver — part of the wave bounces back. SCAA082A §1.3.2 gives the reflection coefficient and the two extremes: `ρ = +1` at an open end and `ρ = −1` at a short. Its simulated example is the one to remember, because it is an entirely ordinary case: a 3.3 V clock source with a 25 Ω output impedance driving an unterminated line into a high-impedance receiver produces "approximately 4.4 V instead of 3.3 V, and the minimum voltage is approximately −1 V instead of 0 V", and the report adds without hedging that "these circumstances can damage the input stage of the source and sink."

**What termination is, and the one you can retrofit.** Termination means deliberately putting the line's own characteristic impedance somewhere in the path so the reflection coefficient goes to zero — SCAA082A §1.3.2 lists four ways of doing it (series, parallel, Thevenin and AC termination) and notes that "the designer has to trade off which one is the best solution for his design." Only one of them is available to you on a board that already exists: **series termination**, a single resistor placed *at the driver* and in line with the signal, sized so that the resistor plus the driver's output impedance roughly equals the trace impedance. The reflection returning from the far end is then absorbed at the source instead of bouncing again. SCAA082A's own worked structures make the sizing concrete: its stripline comes out at `Z_0 = 55 Ω` and its example driver at `25 Ω`, so a `30 Ω` resistor in series at the pin brings the source up to the line impedance and the reflection coefficient to zero. It costs one component and no firmware — the only **hardware** fix, as opposed to the firmware levers covered below, that you can add to a board that already exists. This is also what the "series termination or protection resistor" in [Reading a Schematic](./schematics-and-board-basics.md) is doing when you find one already fitted next to a microcontroller pin.

Compare that against your part's limits. DS10314 Rev 8, Table 11 gives the absolute maximum input voltage on `FT` pins as `V_DD + 4.0 V`, and Table 12 caps injected current on an `FT`/`TC` pin at `−5/+0 mA` — so an undershoot below ground has essentially no current budget at all. Ringing is not just a data-integrity problem; sustained, it is a reliability problem. This is exactly why [Analog Basics: ADC and DAC](./analog-basics-adc-and-dac.md) reaches the same conclusion from the analog side, where the datasheet recommends a Schottky diode to ground on any analog pin that might see negative injection.

**It needs a return path.** Every signal current comes back. TI's SZZA009 states the mechanism in a sentence worth keeping: "Every edge transition that is sent from the microcomputer to another chip is a current pulse. The current pulse goes to the receiving device, exits through that device's ground pin, then returns via the ground traces, to the ground pin of the microcomputer… The pulse does not exit the ground lead of the receiving device and return to the battery, but travels in a loop to where it originates." And the corollary: "Any noise voltage and its associated current travels the path(s) of lowest impedance back to the place where it was generated."

The area enclosed by that loop is the antenna — for radiating out, and for picking up. Almost every layout guideline reduces to *make the loop smaller*, which is why a ground plane under the signal layer is worth more than any amount of careful trace routing above it.

## Ground is not a node

The schematic symbol implies that every point marked ground is at the same potential. It is not, and the difference is where a whole family of bugs lives.

Analog Devices' MT-031 draws the classic case: a return path shared between a digital circuit and an analog one. "The ground return wire inductance and resistance is shared between the analog and digital circuits, and this is what causes the interaction and resulting error." A digital block drawing a current spike develops a voltage across the shared return impedance, and that voltage appears — to the analog block — as a shift in its own ground reference. Nothing is broken. Nothing is miswired. The measurement is simply wrong by the amount of the shared drop.

MT-031 is equally clear that the textbook fix does not scale: "Implementing the true single-point ground in a system which contains multiple high frequency return paths is difficult because the physical length of the individual return current wires will introduce parasitic resistance and inductance… In practice, the current returns must consist of large area ground planes for low impedance to high frequency currents. Without a low-impedance ground plane, it is therefore almost impossible to avoid these shared impedances, especially at high frequencies."

Its practical rules are short enough to remember: dedicate at least one complete layer to ground; keep at least 75% of it intact after the vias and crossovers take their share; check afterwards for isolated ground "islands" and for "skinny" connections between large areas; and solder IC ground pins directly to the plane rather than through sockets.

The same reasoning explains why decoupling capacitors are placed where they are. MT-101 puts the requirement plainly: "All decoupling capacitors must connect directly to a low impedance ground plane in order to be effective. Short traces or vias are required for this connection to minimize additional series inductance." A capacitor is only a capacitor up to its self-resonant frequency, `f = 1/(2π√(L·C))`, above which its own equivalent series inductance dominates and it behaves as an inductor — which is why a bulk electrolytic and a small ceramic in parallel are not redundant, and why the wire you connect it with is part of the component. [Reading a Schematic](./schematics-and-board-basics.md) covers what those capacitors look like on the page.

## Symptom to cause

This is the table to come back to. It maps what you actually observe to the mechanism most likely behind it, and — the important column — to the cheapest test that distinguishes it from a firmware bug.

| Symptom | Most likely cause | Why it looks like a firmware bug | Cheapest discriminating test |
|---|---|---|---|
| Bus works at low speed, fails as you raise the clock | Rise/fall times, bus capacitance, or reflections that were tolerable at the slower edge rate | Bit-banging works, the peripheral driver doesn't; smells like a timing bug in the driver | Halve the bus clock. If it works, it is electrical, not logical. |
| Occasional corrupted byte, no pattern | Ringing crossing the receiver threshold twice on one edge, or crosstalk from an adjacent line | Looks like a race condition or a missed interrupt | Logic analyzer on the line. A false extra edge is a hardware answer; a correct waveform with wrong software behaviour is not. |
| Works with short wires, fails with long ones | Transmission-line effects, increased loop area, added capacitance | "It worked yesterday" — because yesterday the wire was 5 cm | Shorten the wire. Nothing else changes this behaviour so cleanly. |
| Works alone, fails when a motor/relay/backlight switches | Supply sag or ground bounce from the load's current step, sharing a return path with your signal | Random resets or wrong readings correlated with an application event | Watch the 3V3 rail while the load switches. Also read `RCC_CSR` — a brownout leaves a trace. |
| ADC readings jump when a digital output toggles | I/O crosstalk into the analog input, or the digital current spike moving the reference | "My filter code is wrong" | Stop toggling the output for one conversion. If the reading settles, it was coupling. |
| Fails only when a hand or a cable is nearby | High-impedance node with no defined level, or an antenna picking up mains hum | Genuinely inexplicable in software terms | Add a pull resistor, or ground the cable shield. A floating input is the usual answer. |
| Fails only at temperature extremes, or on some units | Marginal timing or marginal thresholds — the design was never inside spec, only inside typical | Reported as "intermittent", never reproducible at the desk | Compare the margin you have against the datasheet limit, not against what works. |
| First device on the bus works, the last one doesn't | Signal degraded along the line: capacitance, reflection at branches, insufficient drive | Looks like an addressing or enumeration bug | Swap the physical order of the devices. If the fault follows the position, it is electrical. |
| Radiated noise appears at odd harmonics of your clock | Fast edges: harmonic content is set by rise time, not by frequency | Not a software symptom at all — usually found at EMC testing | Slow the edges. On STM32, that is one `OSPEEDR` field. |

## The two levers firmware actually has

Most signal-integrity fixes are layout fixes, and by the time you have a board they are unavailable. Two are not.

**Slow the edges.** SCAA082A §1.2 explains why this works: a trapezoidal edge's frequency content is set by its rise and fall time, and "the longer the rise time, the smaller the magnitude of the harmonics." On the STM32F411 that is `GPIOx_OSPEEDR`, which trades edge rate against noise and current: `4 MHz`, `25 MHz`, `50 MHz` and `100 MHz` maximum output frequency for the four settings, with rise/fall times from `100 ns` down to `4 ns` (DS10314 Rev 8, Table 55). The habit worth forming is to configure the **slowest setting that meets the signal's real requirement** — the default is not the fast one, and choosing the fast one everywhere is choosing to radiate.

**Slow the bus.** An I²C bus whose pull-ups cannot pull the line to V<sub>IH</sub> within the rise-time budget at 400 kHz will often be perfectly reliable at 100 kHz. That is not a workaround to be ashamed of; it is matching the bit rate to the physical layer you actually have. [How a GPIO Pin Really Behaves](./gpio-electrical-behaviour.md) works through the pull-up sizing arithmetic that decides where the limit is.

:::warning[The bench setup is the noise source, and the probe lies about it]
Two mistakes that cost days, both of them self-inflicted:

**Long jumper wires on a fast bus.** A 20 cm jumper from a breadboard to a sensor is a loop antenna, an inductor, and an unterminated line all at once, and running it alongside another jumper carrying a clock adds crosstalk for free. If a bus works when the sensor is pushed up against the board and fails when it is 20 cm away, you have not found a firmware bug — you have found the length of your wire. Keep signal and ground returns adjacent (twist them, or run a ground jumper right alongside), keep the clock away from everything else, and do not conclude anything about a design from a breadboard's behaviour at 400 kHz.

**The oscilloscope's ground lead.** The 15 cm crocodile-clip ground lead that ships with every probe forms a loop with the probe tip, and that loop rings at its own resonant frequency when you measure a fast edge. The overshoot you are looking at may be entirely an artefact of the measurement. The tell is that it changes when you move the ground lead. For anything with a sub-10 ns edge, use the short spring-tip ground that clips over the probe barrel, grounded within a centimetre or two of the point you are probing. A measurement you cannot trust is worse than no measurement, because you will act on it.
:::

:::note[Why it works on the bench and fails in the field]
Nothing changed electrically — what changed is that the bench was a narrow slice of the operating envelope. The field adds temperature (thresholds and timings drift), supply variation (a battery at 3.0 V rather than a USB port at 3.3 V), longer cables, mechanical stress on connectors, other equipment radiating nearby, and unit-to-unit spread across a production run. A design that works "on every board I tried" and has no measured margin against the datasheet limits is not a working design; it is a design that has not been asked a hard question yet. The discipline is to compare against the specified limit, not against observed behaviour.
:::

## See also

- [Voltage Levels and Logic](./voltage-levels-and-logic.md) — the receiver thresholds ringing has to cross, and what a floating input reads.
- [How a GPIO Pin Really Behaves](./gpio-electrical-behaviour.md) — `OSPEEDR`, drive strength, and the I²C pull-up arithmetic.
- [Reading a Schematic](./schematics-and-board-basics.md) — decoupling capacitors and series resistors as they appear on the page.
- [Analog Basics: ADC and DAC](./analog-basics-adc-and-dac.md) — where this page's noise shows up as measurement error, and the injection-current warning.
- [Lab Equipment and What It Answers](./lab-equipment.md) — which instrument settles which row of the symptom table.

## References

- Texas Instruments — [**SCAA082A**, *High-Speed Layout Guidelines*](https://www.ti.com/lit/an/scaa082a/scaa082a.pdf) (November 2006, revised August 2017). §1.2 for rise time and harmonic content, §1.3 for when a trace becomes a transmission line, Table 2 for the microstrip and stripline propagation delays quoted here, §1.3.2 and Figure 5 for the reflection coefficient and the 4.4 V / −1 V overshoot example, §1.3.2 for the four termination styles, §2 for via stubs and clock distribution.
- Analog Devices — [**MT-031**, *Grounding Data Converters and Solving the Mystery of "AGND" and "DGND"*](https://www.analog.com/media/en/training-seminars/tutorials/MT-031.pdf) (Rev. A). Figure 1 and the surrounding text for shared return impedance; the ground-plane rules (one dedicated layer, 75% coverage, no islands or skinny connections) and the honest assessment of single-point grounding's limits. The clearest short treatment of why "ground" is not one node.
- Analog Devices — [**MT-101**, *Decoupling Techniques*](https://www.analog.com/media/en/training-seminars/tutorials/MT-101.pdf) (Rev. 0). ESR and ESL as the terms that make a real capacitor stop behaving like one, the self-resonant frequency equation, why bulk and ceramic capacitors are complementary rather than redundant, and why the connection to the ground plane is part of the component.
- Texas Instruments — [**SZZA009**, *PCB Design Guidelines For Reduced EMI*](https://www.ti.com/lit/an/szza009/szza009.pdf) (November 1999). §1.4 for the return-current loop, §2 for board zoning, ground grids on two-layer boards, and the specific plane mistakes (buried traces, slots from through-hole rows) that turn a ground plane into an antenna. Written for microcontroller boards specifically, which most signal-integrity material is not.
- STMicroelectronics — [**STM32F411xC/E datasheet**](https://www.st.com/resource/en/datasheet/stm32f411re.pdf) (DS10314), consulted at **Rev 8** (January 2024). Table 55 for the `OSPEEDR` frequency and rise/fall-time figures, Table 11 for absolute-maximum input voltage, Table 12 for the injection-current limits that make overshoot and undershoot a reliability question rather than only a data-integrity one.
