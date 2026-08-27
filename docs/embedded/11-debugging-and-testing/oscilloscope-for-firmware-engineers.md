---
id: oscilloscope-for-firmware-engineers
title: The Oscilloscope for Firmware Engineers
sidebar_label: The Oscilloscope for Firmware Engineers
sidebar_position: 7
tags: [embedded, debugging, oscilloscope, signal-integrity, hardware-bringup, stm32]
---

# The Oscilloscope for Firmware Engineers

A logic analyzer and an oscilloscope look like they answer the same question — "what happened on this wire" — and firmware engineers who own one tend to reach for it for everything, because a protocol decode is easier to read than a wobbly trace. They are not the same instrument. A logic analyzer's front end does one thing: at every sample instant, compare the voltage to a threshold and emit a `0` or a `1`. Everything about *how* the signal got to that voltage — how fast, how far past it, whether it wobbled on the way — is discarded before the decoder ever sees a bit. An oscilloscope keeps that information. It is not a better logic analyzer; it answers a different class of question, and it is the only instrument in this folder that can.

The mental model worth carrying: **a digital signal is an analog signal that a receiver has agreed to interpret categorically, and the categories can fail even when the decode looks fine.** [Logic Analyzer Workflows](./logic-analyzer-workflows.md) already made this case from the decoder's side — a decoder that shows plausible bytes on a bus with bad levels — and worked one I²C pull-up failure through it. This page is the instrument that answers the question the decoder cannot: not "were the bits plausible" but "did the electricity actually behave."

The failures a scope finds share a signature: they are **conditional**. They pass at low speed and fail at high speed, pass on a short cable and fail on a long one, pass on the bench and fail once ten boards are in an enclosure together. A logic analyzer's clean decode on the good day is exactly what makes the bad day so hard to diagnose without one.

:::info[Prerequisites]
[Lab Equipment and What It Answers](../01-hardware-foundations/lab-equipment.md) argues for buying a logic analyzer before a scope and covers the division of labour between multimeter, analyzer and scope in more depth than this page repeats. [GPIO Electrical Behaviour](../01-hardware-foundations/gpio-electrical-behaviour.md) owns `V_IH`/`V_IL`, drive strength and sink/source current — the thresholds this page's failures cross. [Signal Integrity and Noise](../01-hardware-foundations/signal-integrity-and-noise.md) owns reflections, termination and ground bounce at the level of *why*; this page is about *seeing* them on the bench.
:::

## What only a scope reveals

| Symptom | What only a scope reveals |
|---|---|
| I²C decodes cleanly at 100 kHz, fails intermittently at 400 kHz | The rise time of `SDA`/`SCL` against the pull-up's RC curve — a logic analyzer sees a clean `1` the moment the edge crosses threshold, never how close it cut it |
| The board resets randomly, only under load (motor start, radio TX burst) | Supply rail droop during the current transient — invisible to any purely digital instrument, because nothing digital changed |
| A signal decodes correctly but the device on the other end still misbehaves | Overshoot past the receiver's absolute maximum rating, or undershoot that forward-biases an ESD clamp diode and injects current into the rail |
| Works on a 10 cm bench wire, flaky on a 50 cm cable in the enclosure | Reflections off an unterminated or impedance-mismatched run — a stair-stepped edge that a threshold-crossing sampler quantizes into a clean-looking but late transition |
| A fault that happens once an hour, with no known trigger condition | A runt pulse or a single-cycle glitch, caught by single-shot capture with the right trigger — a logic analyzer's fixed sample grid can quantize a narrow glitch out of existence entirely |
| A crystal oscillator that "won't start", or starts intermittently | The startup amplitude envelope ramping up from noise — before the first valid clock edge exists, there is nothing for a digital instrument to trigger on at all |
| A GPIO toggles in the debugger but the receiving device never responds | The edge is real but too slow for the receiver's setup time — a drive-strength or load-capacitance problem a decoded `0`/`1` stream cannot show |

Read the table both ways. Every row on the right is also a class of bug that a clean logic-analyzer capture will not surface, which is the argument for keeping a scope on the bench rather than trusting a good decode as proof of a healthy signal.

## Bandwidth and rise time: the two numbers that decide what you can trust

A scope's headline bandwidth spec answers one question: the highest-frequency sine wave it can measure without attenuating the amplitude significantly (the −3 dB point). The number that matters for a digital edge is derived from it: **rise time ≈ 0.35 / bandwidth** (Tektronix's own primer states this relationship and its practical corollary — a scope's *measured* rise time is the combination in quadrature of the signal's real rise time and the scope's own, so a scope needs meaningfully more bandwidth than the signal it is characterizing, not merely "more than the clock rate"). A 100 MHz scope reading a genuinely 2 ns edge will report an edge measurably slower than 2 ns, because the instrument's own limit is folding in.

This is the practical trap for anyone coming from digital tools: **the relevant frequency is not the bus's data rate, it is the edge rate.** An I²C bus running at 400 kHz has data transitions nowhere near 400 MHz, but a clean digital edge on a modern GPIO can have a rise time in the low nanoseconds, which by the 0.35/BW rule already wants on the order of 100–300 MHz of scope bandwidth to represent faithfully — two to three orders of magnitude above the bus's nominal clock. This is exactly why a scope that looks generously overspecified for "just I²C" is often the one that finally shows the ringing a cheaper unit rounded away.

Probe selection interacts with the same limit, and the two settings people get backwards most often are attenuation and bandwidth limiting:

| Setting | ×1 (unity) probe or ×1 setting | ×10 probe |
|---|---|---|
| Attenuation | None — 1:1 | 10:1 — scope must be told, or the trace reads 10× too small |
| Typical probe bandwidth | A few tens of MHz, often much less | Full rated bandwidth of the scope, commonly 100s of MHz |
| Input capacitance loading the circuit | High — 30–100+ pF is common, enough to slow a fast edge by itself | Low — typically 10–15 pF |
| Dynamic range | Better for small, slow, low-amplitude signals | Standard choice for digital logic and anything with real edge rate |

The practical rule that follows: **×10 is the default for digital firmware work**, and ×1 is a special-purpose choice for slow, small signals where the extra sensitivity is worth the bandwidth and loading cost. Leaving a probe in ×1 mode "because the wires are simpler to connect" is a common, silent way to lose the exact bandwidth this page's whole argument depends on.

## Triggering for the fault that happens once an hour

A free-running capture on a scope with a few divisions of screen time will never catch an event that occurs once an hour — the display simply is not looking when it happens. The instruments converge on the same principle covered in [The Debug Toolbox](./the-debug-toolbox.md): trigger on the condition, do not wait for it to scroll past.

- **Edge trigger** on the suspect signal, with the level set at the actual threshold you care about (a receiver's `V_IH`, not the scope's default 1.4 V or 50%) — the baseline for "capture when this line does something."
- **Pulse-width trigger** ("less than" a threshold) is the direct tool for a runt pulse or a glitch narrower than a normal transaction — set the width just under the shortest legitimate pulse and the scope arms only on the anomaly.
- **Single-shot (normal/single sequence) acquisition** with a long record length is what actually catches a rare event: the scope arms once, waits indefinitely, and stops the instant the trigger condition fires, preserving pre-trigger history around it. Free-run or auto-trigger mode overwrites the display continuously and the rare capture is gone before you look.
- **A GPIO marker beats a bus-pattern trigger** for the same reason it does on a logic analyzer: toggle a spare pin immediately around the suspect operation in firmware, and trigger the scope on that pin instead of trying to describe an ambiguous analog condition to the trigger system.

## Probe compensation: the edge you thought was real

Every passive ×10 probe has a small trimmer capacitor, and it is not cosmetic. The probe forms an RC divider with the scope's input; if the probe's compensation capacitor is not matched to the scope input's capacitance, the divider is frequency-dependent and a clean square edge comes back rounded (undercompensated — the trimmer capacitance too low) or overshot with a spike at each transition (overcompensated — too high). Every scope provides a calibration square-wave output (commonly a few kHz, a few volts) specifically to check this by eye: a correctly compensated probe shows a flat top; either miscompensation shows an obviously wrong edge shape on that same reference signal.

The trap is not that people never compensate a probe — it is that they do it once, on delivery, and then swap probes between benches or hand one to a colleague, and the trimmer drifts or gets bumped. A miscompensated probe does not fail loudly; it produces a trace that looks like ringing or rounding on the actual signal under test, and both of those are exactly the failure modes this page exists to find. Compensate on the calibration signal *first*, every session, before trusting a shape on the real circuit.

## Correlating a scope trace with a marker in code

The scope has no idea what your firmware was doing when an edge occurred. The fix is the same one used throughout this folder: make the firmware say so.

```c title="Toggle a spare GPIO immediately around the suspect operation"
GPIOB->BSRR = GPIO_BSRR_BS8;      /* PB8 high: about to start the transfer */
hal_spi_transmit(dev, buf, len);
GPIOB->BSRR = GPIO_BSRR_BR8;      /* PB8 low: transfer call returned */
```

Probe the marker pin on one channel and the signal under investigation on another, trigger on the marker's rising edge, and the scope now shows exactly what the electrical world was doing during a *named* span of code — not "somewhere in the SPI driver" but the interval between these two lines. [SysTick and the Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md) covers `DWT->CYCCNT` as the software-side complement: read it immediately before and after the same span, and a discrepancy between the cycle count and what the scope shows on the wire tells you whether the time is being spent in the core or on the bus.

The cost of the marker itself is two store instructions — negligible next to the operation it is bracketing, and far cheaper than anything that touches a UART. It shares the same caveat as everywhere else logging touches timing: if the marker toggle itself measurably changes when the bug reproduces, the bug was timing-sensitive at a scale close to two GPIO writes, which is itself useful information.

:::warning[Two probe settings that quietly lie, and cost a day each]
**A probe left in ×1 when the circuit needs ×10 bandwidth.** Most probes ship with a switch for ×1/×10 and default to whichever position it was last left in. A ×1 setting's few-tens-of-MHz bandwidth is more than enough for a slow analog signal and hopelessly inadequate for a digital edge — the trap is that the scope still shows *a* waveform, at full amplitude, that looks like a real if slightly soft edge. Nothing on the display says "this is bandwidth-limited." The tell is that ringing or overshoot the datasheet warns about never appears no matter how bad the layout is, because the probe itself is filtering it out before the scope ever sees it. Check the probe's switch and the scope's attenuation setting together, every time you change probes.

**AC coupling hiding the exact droop you are looking for.** AC coupling removes the DC component of a signal, which is the right choice for looking at ripple riding on a rail, and the wrong choice for the moment you are trying to catch a supply sagging under a load transient — AC coupling will show you the *shape* of the dip but center it around zero, discarding the one number that tells you whether the rail actually crossed a brownout threshold. The symptom is a trace that looks like a perfectly normal transient artifact, because the coupling mode has erased the context needed to tell "normal ripple" from "the rail dropped below 2.7 V for 40 µs and the regulator's UVLO tripped." Confirm the coupling mode is DC before measuring anything you intend to compare against an absolute voltage limit.
:::

## See also

- [Logic Analyzer Workflows](./logic-analyzer-workflows.md) — the decoder's side of this same argument, the missing-pull-up case worked in full, and where a clean decode is not proof of a healthy signal.
- [The Debug Toolbox](./the-debug-toolbox.md) — where the scope sits among every other instrument, and the "trigger on the condition, not on recording" principle in general form.
- [Lab Equipment and What It Answers](../01-hardware-foundations/lab-equipment.md) — the instrument-selection case for a logic analyzer first, and when the budget for a scope is worth spending.
- [GPIO Electrical Behaviour](../01-hardware-foundations/gpio-electrical-behaviour.md) — `V_IH`/`V_IL`, drive strength and the thresholds this page's failures cross.
- [Signal Integrity and Noise](../01-hardware-foundations/signal-integrity-and-noise.md) — the reflection and termination theory behind the "works on a short cable, fails on a long one" row above.

## References

- Tektronix — [**"XYZs of Oscilloscopes" Primer**](https://www.tek.com/en/documents/primer/xyzs-oscilloscopes-primer). The vendor-educational reference this page is built around: bandwidth and the 0.35/BW rise-time relationship, probe compensation and its calibration-square-wave procedure, triggering modes including single-sequence acquisition, and AC-versus-DC coupling.
- Keysight — [**"Evaluating Oscilloscope Bandwidths for Your Application"**](https://www.keysight.com/us/en/assets/7018-04814/application-notes/5991-2224.pdf) application note. The bandwidth-versus-edge-rate relationship worked through several worked examples, and why "5× the clock frequency" undercounts a fast digital edge.
- STMicroelectronics — [**DS10314**, *STM32F411xC/E datasheet*](https://www.st.com/resource/en/datasheet/stm32f411re.pdf), the "I/O AC characteristics" table (Table 55 as of Rev 8, January 2024) for the GPIO output-speed-versus-load-capacitance figures that determine how fast a real edge on this part can be. **Corroborated, not read directly**: the fetch of the datasheet PDF timed out while this page was written, so the table number and the figures attributed to it here rest on secondary corroboration rather than a verified read of the primary. Look up the row for your GPIO speed setting and load in your own copy before assuming a number (checked 2026-08-27).
- Keithley/Tektronix — [**"Oscilloscope Probe Compensation"**, DigiKey TechForum](https://forum.digikey.com/t/oscilloscope-probe-compensation/45045). A short, practical walkthrough of the compensation adjustment and the over/undercompensated waveform shapes to recognize by eye.
