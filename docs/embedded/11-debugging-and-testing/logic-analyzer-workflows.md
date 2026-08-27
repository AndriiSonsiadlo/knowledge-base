---
id: logic-analyzer-workflows
title: Logic Analyzer Workflows
sidebar_label: Logic Analyzer Workflows
sidebar_position: 6
tags: [embedded, debugging, logic-analyzer, sigrok, i2c, spi, uart, protocol-decoding]
---

# Logic Analyzer Workflows

"The bus doesn't work" is not a bug report a logic analyzer can answer by itself, and the gap between clipping on four wires and actually learning something is where most of a session goes. [Lab Equipment and What It Answers](../01-hardware-foundations/lab-equipment.md) makes the case for reaching for the analyzer first and works one I²C bug through it end to end; this page assumes you have already made that choice and is about running the capture well enough that the answer it gives you is true.

The trap worth naming up front, because it undoes more sessions than any other mistake: **a protocol decoder is a piece of software that trusts its input completely.** It takes a stream of above-threshold and below-threshold samples and turns them into bytes, addresses, and ACK bits with total confidence, because nothing in that process ever asks whether the electrical signal underneath was actually good. A bus with marginal levels, borderline timing, or a wrong sample rate can still produce a decode that looks plausible — clean-looking bytes, sensible-looking addresses — and the plausibility is exactly what makes it dangerous. The decoder cannot tell you it doesn't know; it will simply tell you something, and something wrong reads the same as something right until you have burned an afternoon on it.

Everything below is built around closing that gap: choosing a sample rate that can actually place an edge, triggering on the failure instead of drowning it in good frames, and knowing the specific decode signatures that mean "the electricity is the problem" rather than "the firmware is the problem."

:::info[Prerequisites]
[Lab Equipment and What It Answers](../01-hardware-foundations/lab-equipment.md) argues for the logic analyzer as the first instrument to buy and covers the multimeter-versus-analyzer-versus-scope division of labour; read it for instrument selection. [The Debug Toolbox](./the-debug-toolbox.md) places the analyzer among every other instrument in this folder and the perturbation cost of each.
:::

## Sample rate: you are placing edges, not reconstructing a waveform

Nyquist's theorem — sample at twice the highest frequency of interest — is the answer to a different question. It tells you the minimum rate to reconstruct an *analog* signal's frequency content without aliasing. A logic analyzer is not reconstructing a waveform; it is deciding, sample by sample, whether a wire was above or below one threshold, and a protocol decoder then has to find *where in time* each transition happened from nothing but that stream of ones and zeros. Sample at exactly the clock rate and every edge lands somewhere in a window as wide as a full bit period — the decoder cannot tell a clean edge from one that arrived a half-cycle late, cannot measure a clock's duty cycle, and cannot see a glitch narrower than one sample.

The practical rule that follows: **oversample the edge rate you care about by roughly 4–10×**, not the data rate. For a clocked bus that means the *clock* frequency, not the bit rate the clock implies — I²C at 400 kHz (Fast Mode) wants at least 1.6–4 MHz and comfortably more if the budget allows; a cheap `fx2lafw`-based clone sampling at 24 MHz gives 60× headroom on that bus for free. An 8 MHz SPI clock is a different story: 4–10× puts the requirement at 32–80 MHz, which the same $12 analyzer cannot deliver, and [Lab Equipment](../01-hardware-foundations/lab-equipment.md)'s own worked SPI bug is exactly this shape — traffic that decodes cleanly at 1 MHz and falls apart at 8 MHz, where the fix on the wire turned out to be ringing a scope could see and an analyzer at the wrong sample rate could not.

The signature of an undersampled capture is specific enough to recognise: decoded bytes that are wrong in a way that changes if you retry the exact same transaction, or bytes that are wrong only at one particular byte position in every frame. Real data corruption on the wire tends to be either systematic (every transaction, same symptom) or genuinely random (bus noise, an EMI event); an undersampled capture produces something in between — occasionally right, because the sample happened to land in the right half of the bit, occasionally wrong, because it didn't. If retrying an identical, deterministic transaction gives you a different decode each time, suspect the analyzer's sample rate before the device.

Sample rate and capture duration are not independent. Onboard capture memory is fixed, so a higher rate buys edge resolution at the direct cost of how long a capture window you get before the buffer fills — sigrok's streaming mode trades this the other way, sending samples to the host continuously at the cost of USB bandwidth becoming the ceiling instead of onboard memory. Know which regime you are in before you conclude a capture "wasn't long enough" — it may simply have been sampled too fast for its own buffer.

## Triggering: capture the failure, not ten thousand good frames

A bus that fails once in ten thousand transactions defeats a free-running capture two ways at once: the buffer fills with good data long before the bad transaction arrives, and even if it didn't, finding one bad frame in ten thousand by eye is not a plan. The fix is the same principle as everywhere else in debugging — [The Debug Toolbox](./the-debug-toolbox.md) makes the general case — **trigger on the condition you are trying to catch, not on "recording."**

- **Edge and pulse triggers** — start capture on a rising or falling edge on a specific channel, or on a pulse shorter or longer than a threshold — are the baseline every analyzer offers, hardware or `fx2lafw`-based. A chip-select edge is the natural trigger for an SPI transaction; a start condition (`SDA` falling while `SCL` is high) is the natural one for I²C.
- **A firmware-side marker beats a bus-pattern trigger when the failure isn't a fixed byte pattern.** If the fault is "the sensor eventually stops answering" rather than "a specific byte value appears," toggle a spare GPIO immediately before the suspect operation and trigger the capture on that pin instead. It costs one line of firmware and turns an ambiguous protocol-level trigger condition into an unambiguous edge.
- **Capture position matters as much as the trigger condition.** A trigger that starts the buffer *at* the event of interest gives you no context for what led up to it. Set the trigger to sit partway through the buffer — most capture position, or "pre-trigger," settings exist for exactly this — so the recording holds both the failure and the handful of good transactions immediately before it, which is usually where the actual divergence from correct behaviour is visible.

## What a decoder does and does not tell you

A decoder consumes exactly one thing: a sequence of digital samples already reduced to `0`/`1`. Everything before that reduction — whether the "1" you are looking at actually reached a valid high, how fast it got there, whether it was still settling when the next edge arrived — is thrown away before the decoder ever runs. That is not a flaw in any particular tool; it is what "digital" means, and it is also exactly the information a marginal bus fails on.

The result is the classic trap named at the top of this page: **a decoder that shows plausible bytes on a bus with bad levels.** The canonical case is I²C with missing or under-strength pull-ups. Open-drain lines rely entirely on a resistor to pull the line back to a valid `1` — [I2C in Depth](../05-peripherals-and-drivers/i2c-in-depth.md) owns the electrical model — and a resistor charging a capacitive bus has a rise time. At low speed, light bus loading, and a short cable, a too-weak or missing pull-up can still charge the line to a valid high *before the analyzer's sample lands on it*, and the decode comes back clean: correct address, correct ACK, correct data. The moment the bus gets longer, faster, or gains a second device, the same rise time no longer finishes in time, and the bus that "worked" starts failing intermittently — a symptom that reads as flaky hardware rather than a documented consequence of a resistor value, because the decoder told you the bus was fine.

The decoder telling you the bytes were right never told you the edges were fast enough to keep being right.

## Failure signatures worth recognising

Three protocols, three specific decode signatures, each pointing at a different layer of the problem:

| Symptom in the decode | Likely cause | How to confirm |
|---|---|---|
| I²C: address NAKed on every attempt, or the bus never reads back to a clean idle high between transactions | Missing or too-weak pull-ups — the line isn't reaching `V`<sub>`IH`</sub> before the next edge | Check idle `SDA`/`SCL` sit at a firm high, not a slow crawl; the fix is [I2C in Depth](../05-peripherals-and-drivers/i2c-in-depth.md)'s bus-recovery and resistor sizing |
| SPI: every byte looks shifted by one bit, or data is consistently the bitwise complement of something plausible | `CPOL`/`CPHA` mismatch — controller and target sample on different clock edges | Re-run the same capture through the decoder with each of the four SPI mode settings; if one mode produces clean bytes from the *same* electrical capture, the bug is a mode-register mismatch in firmware, not the bus — see [SPI in Depth](../05-peripherals-and-drivers/spi-in-depth.md) |
| UART: a framing error (stop bit not where expected) on **every** byte, not sporadically | Baud-rate mismatch between transmitter and receiver | A *consistent* framing error on every byte points at a systematic clock-rate cause; a sporadic one points at noise or contention instead — [UART In Depth](../05-peripherals-and-drivers/uart-in-depth.md) has the bit-centre-drift mechanism that produces this exact signature |

The SPI row deserves the extra sentence, because it is the one case here where the fix is entirely on the analysis side rather than the bus: most decoder software lets you re-interpret an already-captured file under a different `CPOL`/`CPHA` setting without recapturing anything. If trying the other three modes against the same capture turns garbage into clean bytes, you have proven the wire was never the problem — the fix is in the SPI peripheral's mode configuration, and no amount of re-probing the hardware will find it.

The UART row is the one with a real underlying mechanism rather than a coincidence, and it is worth carrying the reason rather than just the symptom: a UART receiver resynchronises once per frame, on the start bit's falling edge, and free-runs for the rest of the frame on its own clock. A steady baud-rate error does not fail one bit at random — it accumulates across the frame, so the first data bit samples close to correct and the last one samples close to an edge, which is why a baud mismatch shows up as the *same* class of framing error on *every* byte rather than as occasional garbage. [UART In Depth](../05-peripherals-and-drivers/uart-in-depth.md) derives that asymmetry in full; the recognition rule here is simply that consistency across every frame is the tell, and it is what separates "wrong baud rate" from "noisy wire" at a glance, before you have looked at a single decoded byte.

```wavedrom title="I2C SDA: a clean pull-up versus one too weak to reach a valid high before the next edge" alt="Two-lane WaveDrom comparison of an I2C bus. The expected lane shows SCL and SDA with SDA making a clean, fast transition from low to a stable high well before the next SCL rising edge. The observed lane shows the same nominal transaction but SDA rising slowly through an undefined region for two sample periods before finally settling high, illustrating a rise time too slow for a weak or missing pull-up resistor to reach a valid logic high in time."
{ "signal": [
    {},
    ["Expected (proper pull-up)",
      { "name": "SCL", "wave": "1.0.1.0.1." },
      { "name": "SDA", "wave": "1.0.1......" }
    ],
    {},
    ["Observed (missing/weak pull-up)",
      { "name": "SCL", "wave": "1.0.1.0.1." },
      { "name": "SDA", "wave": "1.0.x.x.1.." }
    ]
  ],
  "config": { "hscale": 2 }
}
```

`SDA` in the "expected" lane reaches a firm `1` within one sample period of being released. In the "observed" lane the same release is followed by two sample periods of `x` — not a third logic state, but this page's way of drawing "the analyzer's single-threshold sample landed in the region where the RC charge curve had not yet crossed `V`<sub>`IH`</sub>." A real capture never shows you that `x`; it shows you either a `0` or a `1`, depending on exactly when the sample landed relative to the curve, which is precisely why this failure mode is so easy to miss on a single capture and so consistent once you know to look for it across several.

:::warning[Trusting a decode with no reference to the wire it came from]
The single most expensive mistake with a logic analyzer is treating a clean decode as proof the bus is healthy. A decoder answers "were these particular samples consistent with valid protocol framing" — it cannot answer "was the signal underneath actually a good digital signal," because the samples it received have already thrown that information away. The missing-pull-up case above is the sharpest example: the exact same electrical fault decodes perfectly at low speed and light load and fails only when conditions get marginally worse, so a single "it decoded fine" capture taken during bring-up, on the bench, with one device on the bus, tells you nothing about the unit that comes back from the field three months later with two extra sensors added to the same two wires.

The recognition rule is the fix: when a decode *looks* fine but the symptom persists — retries needed, occasional NAKs, a device that "usually" works — stop trusting the decoder's bytes and look at the raw sample trace for edges that are slow, rounded, or landing close to a sample boundary rather than cleanly inside one. [Lab Equipment and What It Answers](../01-hardware-foundations/lab-equipment.md) covers the oscilloscope as the next instrument for exactly this question — edge shape and rise time are outside a logic analyzer's physics entirely, by design, not by a tool limitation you can configure your way around.
:::

## See also

- [The Debug Toolbox](./the-debug-toolbox.md) — where the logic analyzer sits among every instrument on the bench, and the ordering that reaches it before or after a debugger.
- [Lab Equipment and What It Answers](../01-hardware-foundations/lab-equipment.md) — the instrument-selection case for buying an analyzer before a scope, worked through one real I²C bug.
- [I2C in Depth](../05-peripherals-and-drivers/i2c-in-depth.md) — the open-drain electrical model the missing-pull-up signature above depends on, and bus recovery.
- [SPI in Depth](../05-peripherals-and-drivers/spi-in-depth.md) — the four `CPOL`/`CPHA` modes and why there is no such thing as an SPI read.
- [UART In Depth](../05-peripherals-and-drivers/uart-in-depth.md) — the once-per-frame resynchronisation mechanism the baud-mismatch signature above is derived from.

## References

- sigrok — [**PulseView**](https://sigrok.org/wiki/PulseView), [**Protocol decoders**](https://sigrok.org/wiki/Protocol_decoders), and [**fx2lafw**](https://sigrok.org/wiki/Fx2lafw). The open-source capture application, the full list of supported protocol decoders including stacked decoders, and the firmware behind the sub-$15 Cypress FX2 clones that make this workflow accessible without a commercial analyzer.
- Saleae — [**Trigger**](https://support.saleae.com/getting-started/trigger) and [**Capture Modes**](https://support.saleae.com/user-guide/using-logic/capture-modes). The edge and pulse trigger types, digital channel qualifiers, and buffer/capture-position behaviour referenced in the triggering section above; [**"What Sample Rate Settings Are Available?"**](https://support.saleae.com/faq/technical-faq/what-sample-rate-settings-are-available) for how sample rate trades against channel count and capture memory on Saleae hardware specifically (documentation checked 2026-08-27).
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). Cross-referenced only for consistency with the I²C, SPI and UART peripheral pages this page links to rather than re-derives from.
- Ben Eater — [*The RS-232 protocol*](https://www.youtube.com/watch?v=AHYNxpqKqwo) and the rest of his serial-communication series at [eater.net](https://eater.net/). Reconstructing a protocol from a raw captured signal by hand, which is the skill that makes it possible to recognise when a decoder's confident output should not be trusted.
