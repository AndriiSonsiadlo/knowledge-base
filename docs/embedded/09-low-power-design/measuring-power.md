---
id: measuring-power
title: Measuring Power
sidebar_label: Measuring Power
sidebar_position: 6
tags: [embedded, low-power, power-management, measurement, instrumentation, current-sense, stm32]
---

# Measuring Power

Every figure in this folder so far has come from a datasheet table or from arithmetic built on one. Neither tells you what your board actually draws. A datasheet's Stop-mode current is measured on ST's own characterisation board, with nothing attached to the GPIOs, a specific silicon revision, and every peripheral in the state ST chose to test it in; your board has a pull-up ST did not model, a status LED that never got gated, and firmware that may or may not be entering the mode it claims to. [Energy Budgets](./energy-budgets.md)'s entire arithmetic is only as good as the `I_avg` fed into it, and the only way to know that number is real is to measure it on the actual hardware running the actual release firmware — the warning on that page about a demo build with logging left on exists precisely because nobody measured until it was too late.

The mental model: **a duty-cycled low-power design is not one current to measure, it is two, separated by three or more orders of magnitude, that have to be captured in the same instrument at the same time.** [Sleep Modes](./sleep-modes.md) put the Stop-mode floor at single-digit microamps; [Clock and Peripheral Gating](./clock-and-peripheral-gating.md)'s worked example put an active burst at 10 mA. That is a ratio of roughly 1000:1, and it is exactly the shape that breaks the tools people reach for first.

## Shunt and multimeter: the limits of the simple method

The direct method needs no special equipment: break the supply rail, insert a resistor (a shunt) in series, and read the voltage across it — or let a multimeter do this internally by switching it to a current range. Either way, the reading is only as good as the shunt, and the shunt's resistance is in direct conflict with itself across the load's own range.

**Burden voltage** is the term for the error this introduces: any series resistance in the measurement path drops a voltage under load, and that dropped voltage is subtracted from what the device under test actually receives. A multimeter's internal shunt is chosen per current range — large in the µA range, for enough voltage to resolve on the display; small in the mA/A range, to keep the drop tolerable at higher current. Put the meter in its µA range to resolve a 9 µA Stop-mode floor and the internal shunt is large enough that a sudden 10 mA active burst through the same shunt develops a burden voltage of hundreds of millivolts to several volts, depending on the meter — enough to sag the MCU's actual supply and, on a board running close to its brownout threshold, to trigger the very brownout behaviour [Brownout and Power-Loss Safety](./brownout-and-power-loss-safety.md) covers, an artefact of the measurement rather than anything the design does unpowered by a meter. Put the meter in its mA range instead and the shunt is too small to develop a usable, resolvable voltage at 9 µA — the reading floors at the display's resolution or the meter's own noise, and the number reported means nothing.

**No single fixed range covers both ends of a duty-cycled load.** Some multimeters offer autoranging, but autoranging is built for a signal that changes over tens to hundreds of milliseconds, not for a load that jumps three orders of magnitude in microseconds and back again — the range-switching relay or FET has its own settling time, during which the reading is neither the old range nor the new one. A meter's displayed average, in any case, is a time-integrated number with no time axis: it cannot show *when* current was drawn, only a blended figure across its update interval, which is exactly the information [Clock and Peripheral Gating](./clock-and-peripheral-gating.md)'s run-fast-versus-run-slow comparison needs and a meter alone cannot supply.

| Method | Effective range | What it captures | What it cannot do |
|---|---|---|---|
| Multimeter, fixed µA range | roughly nA–µA, with rising burden voltage error toward the top of the range | a static sleep-mode floor, measured with nothing else happening on the rail | resolve or even survive a simultaneous mA-scale burst without sagging the supply |
| Multimeter, fixed mA range | roughly hundreds of µA–A | active-mode and burst current | resolve a µA-scale sleep floor at all — it is below the range's noise floor |
| Multimeter, autoranging | spans both, sequentially | either extreme, if held there long enough for the range switch to settle | a fast transition between them — the switch itself is blind |
| Shunt + oscilloscope/DAQ, fixed gain | as wide as the chosen shunt and amplifier allow, fixed at capture time | a genuine current-versus-time trace, at the chosen range | the other three orders of magnitude outside that range, in the same capture |
| Dedicated power profiler (autoranging current-sense front end) | continuous nA–A in one capture, no range switch | a full current-versus-time trace across sleep and active current simultaneously | — this is the tool built for exactly this measurement |

## The dedicated profiler: what it does differently

A dedicated power profiler solves the range problem in the analogue front end rather than by choosing a range: instead of one fixed shunt, it holds several shunt/gain stages in parallel (or a single wide-dynamic-range current-sense amplifier) and switches or blends between them fast enough — sample by sample, not manually — that a transition from microamps to milliamps and back is captured continuously rather than lost in a range-change gap. Two named instruments are the common reference points for this class of tool:

- **Nordic Semiconductor's Power Profiler Kit II (PPK2)** sources the device under test itself (it can act as the supply, not just a series ammeter) and captures current at up to roughly 100 thousand samples per second, switching internally between a high-resolution low-current range and a coarser high-current range so a sleep-to-burst-to-sleep cycle is one continuous trace rather than three separate measurements stitched by hand. It also exposes digital input channels that timestamp GPIO logic transitions alongside the current trace in the same capture — the mechanism the next section depends on.
- **Joulescope (the JS110/JS220 family)** takes the same problem from the analogue side: a dual-range current-sense path that blends between a precision low-current shunt and a low-burden high-current shunt in real time, specifically to avoid the settling-time artefact a mechanically or digitally range-switched instrument produces at the transition. It reports current, voltage, power and accumulated energy simultaneously, sampled fast enough to resolve microsecond-scale bursts.

Both instruments exist because the range problem above is a genuine engineering problem, not a documentation gap — a shunt-and-multimeter measurement is not "the same measurement done cheaply," it is a different, narrower measurement, and knowing which one you are looking at matters when you decide how much to trust the number.

## Capturing a trace, and what to look for in it

Whichever instrument produces it, a current-versus-time trace over one or more duty cycles answers three questions a single number cannot:

- **Does the baseline match the datasheet figure for the mode you configured?** A Stop-mode floor sitting visibly above the DS10314 figure from [Sleep Modes](./sleep-modes.md) — even by a small multiple — is the first sign of a gated peripheral clock that was never disabled, exactly the failure [Clock and Peripheral Gating](./clock-and-peripheral-gating.md) warns is invisible to functional testing.
- **Do the burst height and width match the assumptions in the energy budget?** [Energy Budgets](./energy-budgets.md)'s worked example assumed 15 ms of active time at roughly 1.6 mA; a trace showing a burst that runs longer, or draws more, than that assumption directly revises the lifetime estimate built on it, and it is the only way to catch that revision before the product ships rather than after field returns come back short of spec.
- **Are there steps that should not be there at all?** A current level between the sleep floor and the expected active burst, present continuously or on every cycle, is something drawing power that the design did not account for — a debug UART left transmitting, a pull-up on a line that floats during sleep, a sensor never put into its own low-power mode.

## Correlating a spike to a code path

A trace on its own tells you *that* something drew current and roughly *when*; it does not tell you *what code ran*. The standard technique is a **GPIO marker**: toggle a spare pin high at the entry of the code path you want to isolate — an ISR, a DMA-completion callback, a specific state in an event-driven main loop — and low at its exit, then capture that pin alongside the current trace on the same timebase. A power profiler with a digital input channel (the PPK2's digital channels, or a logic analyzer run in parallel with a Joulescope capture) timestamps the toggle in the same data set as the current samples, so the burst that follows a rising edge on that channel is, by construction, attributable to that code path and not to something else that happened to run nearby. This is the same instrumentation discipline used for timing measurement generally — a scope or logic analyzer probing a marker pin against a signal of interest — applied here to current instead of a logic level or a bus transaction.

```wavedrom title="A GPIO marker captured on the same timebase as the current trace turns an anonymous burst into an attributable one" alt="Two aligned waveforms sharing a timebase. The upper, labelled GPIO marker PA5, is low, then goes high for a short interval, low again, high for a longer interval, then low. The lower, labelled measured current, tracks it exactly: nine microamps while the marker is low, ten milliamps while it is high, so each current burst begins and ends on a marker edge and is therefore attributable to the code path that drove that pin"
{ "signal": [
  { "name": "GPIO marker (PA5)", "wave": "0..1...0.....1...0.." },
  { "name": "Measured current",  "wave": "2..3...2.....3...2..", "data": ["9 µA", "10 mA", "9 µA", "10 mA", "9 µA"] },
  {},
  { "name": "Attributed to",     "wave": "x..4...x.....5...x..", "data": ["sensor read ISR", "radio TX"] }
], "config": { "hscale": 2 } }
```

Without the marker channel, the lower trace alone is two anonymous bursts — nothing in it distinguishes a sensor read from a radio transmission, and nothing rules out a third code path you have not thought of. With it, each burst's start and end are bracketed by an edge whose source you wrote yourself, and the attribution is structural rather than inferred. The cost is one spare pin and two register writes; the discipline is to keep the toggle out of the region you are measuring — a marker driven through a slow HAL call adds its own current and its own microseconds to the burst it is supposed to be delimiting.

:::warning[The multimeter that browned out the board it was measuring]
A board that runs correctly from a bench supply and resets repeatedly the moment a multimeter is inserted in series to measure sleep current is not showing a multimeter bug — it is showing the burden-voltage failure described above, and it is easy to misdiagnose as a firmware or hardware fault because the symptom, a spontaneous reset correlated with nothing in the code, looks exactly like [Brownout and Power-Loss Safety](./brownout-and-power-loss-safety.md)'s own subject. The mechanism: the meter is left in its µA range to resolve the Stop-mode floor, its internal shunt for that range is large enough to develop a substantial burden voltage under load, and the moment firmware wakes and draws a Run-mode or peripheral burst through that same shunt, the voltage actually reaching `VDD` sags — on a board already running close to its configured BOR threshold, far enough to trip a reset. The tell is specific and fast to check: the reset only happens with the meter in circuit and only in its most sensitive current range, it does not happen on the bench supply alone, and it does not happen if the meter is switched to a coarser mA range (which resolves the burst fine but can no longer see the sleep floor). The fix is not a firmware change — it is to stop asking one fixed-range instrument to cover both ends of the load, and reach for the shunt-plus-oscilloscope or dedicated-profiler row of the table above, both of which are built to hold a low burden voltage across the full range rather than trading it against resolution.
:::

## See also

- [Sleep Modes](./sleep-modes.md) — the datasheet current figures a captured trace's baseline should be checked against.
- [Clock and Peripheral Gating](./clock-and-peripheral-gating.md) — why an unexplained current step almost always means a peripheral clock that was never gated off.
- [Energy Budgets](./energy-budgets.md) — the average-current arithmetic a measured trace validates or corrects.
- [Brownout and Power-Loss Safety](./brownout-and-power-loss-safety.md) — the failure a measurement's own burden voltage can accidentally trigger, and the real version of the same symptom this page's warning is a false positive for.

## References

- Nordic Semiconductor — [**Power Profiler Kit II (PPK2) user guide**](https://docs.nordicsemi.com/bundle/ug_ppk2/page/UG/ppk/PPK_user_guide_Intro.html). The autoranging source-and-measure architecture, the roughly 100 ksps sample rate, and the digital input channels used for the GPIO-marker correlation technique above.
- Joulescope — [**JS220 Joulescope precision energy analyzer documentation**](https://www.joulescope.com/collections/products) and [**Joulescope user's guide**](https://download.joulescope.com/). The dual-range, seamlessly-blended current-sense architecture and its rationale for avoiding the settling-time artefact of a switched-range instrument.
- STMicroelectronics — [**STM32F411xC/STM32F411xE datasheet**](https://www.st.com/resource/en/datasheet/stm32f411re.pdf) (DS10314). The Stop-mode and Run-mode current figures a captured trace's baseline and burst segments are checked against, referenced throughout this folder.
