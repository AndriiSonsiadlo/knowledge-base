---
id: spi-in-depth
title: SPI in Depth
sidebar_label: SPI in Depth
sidebar_position: 6
tags: [embedded, peripherals, spi, cpol, cpha, signal-integrity, stm32, drivers]
---

# SPI in Depth

SPI is a shift register with a wire between two halves of it. That is the whole protocol, and holding it in mind explains everything the peripheral does. The controller has eight bits, the target has eight bits, and the clock the controller generates walks them past each other in a ring: the controller's MSB goes out on MOSI and into the target's LSB position, the target's MSB goes out on MISO and into the controller's. After eight clocks the two registers have swapped contents. There is no addressing, no acknowledgement, no error detection and no notion of a transaction — every one of those has to be built on top by whatever protocol the target's datasheet defines.

The mental model that follows from this, and the one that most surprises people coming from I²C: **there is no such thing as an SPI read.** There is only an exchange. To get a byte out of a target you must clock eight bits *in* to it, which means you must transmit something — conventionally `0x00` or `0xFF`, and the choice is not always free, because a target that is still parsing a command interprets those bytes. Every SPI driver you write will have a line that writes a dummy value purely to make clocks happen, and if you do not understand why, that line looks like a bug.

:::info[Prerequisites]
[The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md) owns the bring-up sequence — clock enable with read-back, reset pulse, pins, configure while `SPE = 0`, clear flags, enable last — and the SPI2 example there is the one this page extends. [Serial Buses — I2C, SPI & UART](../../computer-science/buses-and-io/serial-buses-i2c-spi-uart.md) owns what SPI *is*, its pin count, and how it compares to the other two buses; this page is about the four clock modes, chip-select timing, and why the clock rate you can actually run is decided by your wiring rather than by either datasheet.
:::

## CPOL and CPHA, one diagram each

Two bits in `SPI_CR1` decide when the data is valid. **`CPOL`** is the level the clock idles at. **`CPHA`** selects which clock edge samples: `0` means the *first* edge of each bit period, `1` means the *second*. Combined they give the four modes, universally numbered 0 through 3 with `CPOL` as the high bit.

The rule that makes all four readable at a glance: **data changes on one edge and is sampled on the other, always.** The diagrams below each show the transmitting side's data changing at the shaded transitions and the sampling edge marked.

**Mode 0 — `CPOL = 0`, `CPHA = 0`.** Clock idles low, sample on the rising edge, shift out on the falling edge. This is what an unspecified target almost always wants, and it is the mode of SD cards, most sensors, and every serial NOR flash.

```wavedrom title="Mode 0: clock idles low, data sampled on the rising edge, shifted on the falling edge. The first bit is presented by the falling edge of NSS, before any clock exists" alt="Waveform of SPI mode 0 showing NSS going low, SCK idling low with four clock pulses, MOSI presenting bits b7 through b4 that change on falling clock edges, and MISO returning bits q7 through q4, with sampling on rising edges"
{ "signal": [
  { "name": "NSS",  "wave": "10..........1." },
  { "name": "SCK",  "wave": "0..10101010..." },
  { "name": "MOSI", "wave": "x3..3.3.3..x..", "data": ["b7","b6","b5","b4"] },
  { "name": "MISO", "wave": "x5..5.5.5..x..", "data": ["q7","q6","q5","q4"] }
], "config": { "hscale": 1 } }
```

**Mode 1 — `CPOL = 0`, `CPHA = 1`.** Clock still idles low, but the rising edge now *shifts* and the falling edge samples. The first bit is presented by the first clock edge rather than by chip-select.

```wavedrom title="Mode 1: clock idles low, the rising edge presents the bit and the falling edge samples it. Same SCK as mode 0, data shifted half a period" alt="Waveform of SPI mode 1 showing NSS low, SCK idling low, and MOSI data transitions aligned to rising clock edges with sampling on falling edges"
{ "signal": [
  { "name": "NSS",  "wave": "10..........1." },
  { "name": "SCK",  "wave": "0..10101010..." },
  { "name": "MOSI", "wave": "x..3.3.3.3.x..", "data": ["b7","b6","b5","b4"] },
  { "name": "MISO", "wave": "x..5.5.5.5.x..", "data": ["q7","q6","q5","q4"] }
], "config": { "hscale": 1 } }
```

**Mode 2 — `CPOL = 1`, `CPHA = 0`.** Clock idles high, sample on the falling edge. Same relationship as mode 0 with the clock inverted; a target that works in mode 0 usually works in mode 2 as well, which is why the two are so often confused.

```wavedrom title="Mode 2: clock idles high, data sampled on the falling edge, first bit presented by NSS. Mode 0 with the clock inverted" alt="Waveform of SPI mode 2 showing SCK idling high, four clock pulses going low then high, MOSI presenting data from the NSS falling edge, and sampling occurring on falling clock edges"
{ "signal": [
  { "name": "NSS",  "wave": "10..........1." },
  { "name": "SCK",  "wave": "1..01010101..." },
  { "name": "MOSI", "wave": "x3..3.3.3..x..", "data": ["b7","b6","b5","b4"] },
  { "name": "MISO", "wave": "x5..5.5.5..x..", "data": ["q7","q6","q5","q4"] }
], "config": { "hscale": 1 } }
```

**Mode 3 — `CPOL = 1`, `CPHA = 1`.** Clock idles high, sample on the rising edge. Together with mode 0 it covers the overwhelming majority of parts, and the reason so many targets accept modes 0 and 3 interchangeably is visible in the table below: **both sample on the rising edge and shift on the falling one.** They differ only in where SCK rests between transfers, which a target ignores while chip-select is deasserted.

```wavedrom title="Mode 3: clock idles high, the falling edge presents the bit and the rising edge samples it" alt="Waveform of SPI mode 3 showing SCK idling high, MOSI data transitions aligned to falling clock edges, and sampling on rising clock edges"
{ "signal": [
  { "name": "NSS",  "wave": "10..........1." },
  { "name": "SCK",  "wave": "1..01010101..." },
  { "name": "MOSI", "wave": "x..3.3.3.3.x..", "data": ["b7","b6","b5","b4"] },
  { "name": "MISO", "wave": "x..5.5.5.5.x..", "data": ["q7","q6","q5","q4"] }
], "config": { "hscale": 1 } }
```

| Mode | `CPOL` | `CPHA` | Clock idles | Sampling edge | Shifting edge |
|---|---|---|---|---|---|
| 0 | 0 | 0 | Low | Rising (1st) | Falling (2nd) |
| 1 | 0 | 1 | Low | Falling (2nd) | Rising (1st) |
| 2 | 1 | 0 | High | Falling (1st) | Rising (2nd) |
| 3 | 1 | 1 | High | Rising (2nd) | Falling (1st) |

When a target's datasheet does not name a mode number — most do not — it gives you a timing diagram instead, and you read the mode off it in two steps: **where does SCK sit when nothing is happening** (that is `CPOL`), and **does the first data bit appear before the first clock edge or on it** (before ⇒ `CPHA = 0`, on ⇒ `CPHA = 1`).

The consequence of `CPHA = 0` that people trip over: in modes 0 and 2, the target has to have its first output bit on MISO *before the first clock edge exists*, so the only event that can trigger it is the falling edge of chip-select. **Chip-select is part of the protocol in `CPHA = 0`, not just an enable.** Tying `NSS` permanently low, which works fine in modes 1 and 3 for a single target, breaks byte framing in modes 0 and 2 and is a genuinely popular way to lose a day.

## Which bits, in `SPI_CR1`

Configure all of these with `SPE = 0`, per step 4 of the bring-up sequence.

| Field | Bits | Reset | What it does, and the trap |
|---|---|---|---|
| `CPHA` | 0 | `0` | Sampling edge selector. Wrong value ⇒ every byte off by one bit, so `0x9F` reads as `0x3E` or `0xCF`. |
| `CPOL` | 1 | `0` | Idle clock level. Wrong value alone often still works with a target that only cares about edge order. |
| `MSTR` | 2 | `0` | Controller mode. Clears itself to 0 on a mode fault — see the `SSM`/`SSI` note below. |
| `BR[2:0]` | 5–3 | `000` | Baud prescaler, `000` = `f_PCLK/2` through `111` = `f_PCLK/256`. |
| `SPE` | 6 | `0` | Enable. The start button; set it last. |
| `LSBFIRST` | 7 | `0` | Bit order. Almost every target is MSB-first; leave it clear. |
| `SSI`, `SSM` | 8, 9 | `0` | Software slave management. With `SSM = 1` the internal `NSS` takes the value of `SSI`; **a controller with `SSM = 1` and `SSI = 0` sees itself deselected, raises a mode fault, and clears `MSTR`.** Set both. |
| `RXONLY` | 10 | `0` | Receive-only, which suppresses the MOSI output. Rarely what you want. |
| `DFF` | 11 | `0` | 8- or 16-bit frames. |
| `BIDIMODE` | 15 | `0` | Single-wire half-duplex. Needed for three-wire targets; changes what `MOSI` means. |

Two access-width details that produce corrupt data rather than an error:

- **Match the `SPI_DR` access width to `DFF`.** With `DFF = 0` a byte access is what the hardware expects; ST's own HAL casts the pointer for exactly this reason — `*(__IO uint8_t *)&hspi->Instance->DR`. A plain `SPI1->DR = x;` in C is a 16-bit access because `DR` is declared `uint16_t`, and that is not the same transaction.
- **`SPI1` and `SPI2` are the same block on different buses.** `BR = 000` gives `PCLK2/2` = 50 MHz on SPI1 and `PCLK1/2` = 25 MHz on SPI2 with the clock tree at its maximum. The identical driver code produces two different clock rates, which is the bus-membership point made in [The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md).

## Chip-select timing, and the two ends of it

The STM32's hardware `NSS` output (`SSM = 0`, `CR2.SSOE = 1`) is not what most drivers need. It drives `NSS` low when `SPE` is set and releases it when `SPE` is cleared — **it does not pulse per frame**. There is no `NSSP` pulse-mode bit on the F4's SPI; that arrived on later families. So a driver that needs chip-select asserted across a multi-byte command and deasserted between commands — which is every serial flash, every SD card, every display — drives it as an ordinary GPIO.

That puts both edges under software control, and both have a rule:

**The assertion edge** must precede the first clock edge by the target's `t_SU(NSS)` — typically tens of nanoseconds, and free, because the GPIO write and the `SPE`/`DR` write are several instructions apart anyway. It is also, in modes 0 and 2, the event that makes the target present its first bit.

**The deassertion edge** is where the bug lives, and the rule is: *do not deassert on `TXE`.* `TXE` means the transmit buffer has been copied into the shift register and you may queue the next word. It does not mean the last word has left the pin — there are still eight clock periods to go. RM0383 §20.3.8, "Disabling the SPI", gives the exact procedure and it is worth following literally:

```c
static void spi_transfer(const uint8_t *tx, uint8_t *rx, size_t n)
{
    cs_assert();

    for (size_t i = 0; i < n; i++) {
        while (!(SPI1->SR & SPI_SR_TXE)) { }
        *(volatile uint8_t *)&SPI1->DR = tx ? tx[i] : 0xFFu;   /* the dummy write */

        while (!(SPI1->SR & SPI_SR_RXNE)) { }
        uint8_t got = *(volatile uint8_t *)&SPI1->DR;
        if (rx) { rx[i] = got; }
    }

    /* RM0383 §20.3.8: the last frame is not on the wire yet. */
    while (!(SPI1->SR & SPI_SR_TXE)) { }
    while (SPI1->SR & SPI_SR_BSY)    { }

    cs_deassert();
}
```

Dropping `cs_deassert()` in before the `BSY` wait truncates the final byte's clock pulses. The symptom is specific and recognisable: **writes to the target lose their last byte, reads come back right, and a slower clock makes it worse rather than better** — because the slower the clock, the longer the shift register is still busy after `TXE` sets. That last detail is what sends people down the wrong path, since "slow it down" fixes almost every other SPI problem.

Note also that this loop is deliberately lock-step: one word out, one word in, before the next. It halves throughput compared to keeping the shift register fed, but it makes the receive side impossible to get wrong. The fast version — write word *n+1* as soon as `TXE` sets and read word *n* when `RXNE` sets — is where the overrun flag `OVR` becomes relevant, and where a driver that ignores `OVR` silently drops received bytes exactly as the UART one does.

## Why the achievable clock is a wiring property

Every SPI target's front page quotes a maximum clock — 133 MHz on a common serial NOR flash, 50 MHz on a display controller. That number describes the target's internal logic. It does not describe your board, and it is not the number you can run.

The binding constraint is the **round trip on MISO**. In modes 0 and 2, the controller launches a clock edge and samples MISO half a clock period later. In that half period, five things have to finish:

```text
T/2  ≥  t_prop(SCK, controller → target)
      + t_v(SO)      target's clock-edge-to-MISO-valid delay
      + t_prop(MISO, target → controller)
      + t_su(MI)     controller's input setup requirement
      + margin for skew, jitter and rise time
```

Worked, for a Winbond W25Q-class serial NOR on a short PCB trace, using the parameter names the parts actually use:

| Term | Value | Source |
|---|---|---|
| `t_prop` each way, 50 mm of FR-4 stripline | ≈ 0.3 ns | ~6 ns/m propagation delay |
| `t_CLQV` — target clock-to-output-valid | 6 ns at 3.0–3.6 V | W25Q128JV datasheet, AC characteristics |
| `t_su(MI)` — controller data setup | 5 ns | DS10314, "SPI characteristics" |
| Margin | 5 ns | judgement |
| **Total** | **≈ 16.6 ns** | ⇒ `f_SCK ≤ 1/(2 × 16.6 ns) ≈ 30 MHz` |

So 30 MHz on a well-laid-out board with a part rated at 133 MHz. Now change one input — the same flash on jumper wires to a breadboard, where the propagation delay is a couple of nanoseconds each way but the real cost is capacitance and reflection, and where `t_CLQV` degrades because the target's output driver is charging 50–80 pF instead of 15 pF. The honest working range on a breadboard is **1–4 MHz**, and above roughly 8 MHz you are gambling.

Three effects are what actually break it, in order of how often they do:

- **Ringing on SCK.** SCK is the only signal where a glitch adds or removes a *bit*, and one extra clock edge shifts every subsequent bit by one position for the rest of the transaction. The symptom is unmistakable once you have seen it: received bytes are the correct value shifted left or right by one, so `0x9F` arrives as `0x3E` or `0x4F`. The cheap fix on STM32 is free — turn the pin's drive strength *down* in `GPIOx_OSPEEDR`. A slower edge rings less, and at 4 MHz you do not need a 100 MHz edge rate. A 22–33 Ω series resistor at the controller's SCK pin is the other half of the fix.
- **Capacitive loading on MISO.** Adds directly to `t_CLQV` and eats the budget above. It is why adding a second target on the same bus can break a link that worked with one.
- **Ground.** MOSI, MISO and SCK all return through the ground connection. A single thin jumper as the ground between two breadboards is a shared inductor, and it turns SCK's edges into everyone else's noise.

And the property that makes all of this expensive to debug: **SPI has no acknowledgement and no error detection.** A bus running above what the wiring supports does not report anything. It returns plausible-looking wrong data, and the first symptom is usually a filesystem that corrupts once an hour.

:::warning[The transaction that lost its last byte, and the controller that deselected itself]
Two SPI failures whose symptoms point away from their causes.

**Chip-select dropped on `TXE`.** The write path loses exactly its final byte; the read path is perfect. Slowing the clock makes it *worse*, which is the opposite of every other SPI problem and is why it survives a day of bisecting. On a logic analyser it is visible immediately: the `NSS` rising edge sits in the middle of the last byte's clock burst, or truncates it entirely. The fix is the `TXE`-then-`BSY` wait from RM0383 §20.3.8 before deasserting, shown above. If you are using DMA, the transfer-complete interrupt fires when the DMA has finished writing `DR` — which is again *not* when the wire is idle, so the same `BSY` wait is required there.

**`MSTR` clearing itself.** You configure `SPI1->CR1` with `MSTR | SPE`, forget `SSM` and `SSI`, and leave `NSS` as an unconnected input. The pin floats low, the peripheral reads that as "another controller has selected me", raises a mode fault (`SR.MODF`), and **clears `MSTR` and `SPE` in hardware**. Your driver then runs a target-mode peripheral that never generates a clock. Every register you inspect looks almost right — which is the trap, because `CR1` reads back with `MSTR` clear and it is easy to assume you never wrote it. Read `SPI1->CR1` and `SPI1->SR` together: `MSTR = 0` with `MODF = 1` is the whole diagnosis. Set `SSM` and `SSI` for a software-managed chip-select, or set `CR2.SSOE` if you genuinely want the hardware output. Clearing `MODF` needs the documented sequence — a read of `SR` followed by a write to `CR1` (RM0383 §20.3.10).
:::

## Daisy-chaining, and why it is rarer than the diagrams suggest

Because SPI is one long shift register, several targets can be wired in series — MISO of the first to MOSI of the second, one shared clock and one shared chip-select — so that *N* targets behave as one *N*-byte-wide register. Shift-register expanders (74HC595), LED drivers and some DAC families are designed for it and say so.

It is far less common than the topology diagrams imply, for a reason worth knowing: **every target on the chain must tolerate being clocked continuously and must pass data through**, which most sensors and all memories do not. A serial flash decodes the first byte as a command and starts responding; it has no pass-through path. Check the datasheet for an explicit daisy-chain or cascade section before wiring one, and where a part does not support it, the answer is one chip-select GPIO per target — which costs a pin each and is what almost every real board does.

:::note[Modes, numbering, and the missing standard]
SPI has no formal specification. The mode numbering, the names `CPOL` and `CPHA`, and the register semantics all descend from Motorola's SPI block guide, and vendors follow it with varying fidelity. Some datasheets call the modes "SPI mode 0" and some describe them only as a timing diagram; a few invert the sense of `CPHA` in their prose while drawing the standard picture. Trust the timing diagram over the prose, and when a target is stated to support "modes 0 and 3", that is a real and common combination rather than a typo — the two share a sampling edge (rising) and a shifting edge (falling), and differ only in the level SCK rests at between transfers.
:::

## See also

- [The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md) — the bring-up sequence, the RCC read-back guard, and the SPI2 worked example this page continues.
- [UART in Depth](./uart-in-depth.md) — the same peripheral shape without a clock wire, and the sampling-tolerance problem that a shared clock removes entirely.
- [I2C in Depth](./i2c-in-depth.md) — two wires instead of four, at the cost of open-drain edges and every failure mode that follows from them.
- [Serial Buses — I2C, SPI & UART](../../computer-science/buses-and-io/serial-buses-i2c-spi-uart.md) — what SPI is, its pin and topology cost, and when to pick it over the other two.
- [Signal Integrity and Noise](../01-hardware-foundations/signal-integrity-and-noise.md) — the ringing, ground-return and capacitive-loading effects that set the clock ceiling derived above.

## References

- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4**. §20.3.2 for the `CPOL`/`CPHA` definitions and the four-mode timing figures; §20.3.3 for hardware and software `NSS` management and the mode-fault mechanism; §20.3.8 "Disabling the SPI" for the `TXE`-then-`BSY` shutdown procedure used above; §20.3.10 for `MODF` and its clear sequence; §20.5.1 for the `SPI_CR1` field table.
- STMicroelectronics — [**DS10314**, *STM32F411xC/E datasheet*](https://www.st.com/resource/en/datasheet/stm32f411re.pdf). The "SPI characteristics" table for `t_su(MI)`, `t_v(MO)` and the maximum `f_SCK` with its stated load conditions — the controller-side half of the round-trip budget, and the reason a load capacitance is quoted alongside every timing figure.
- Motorola / NXP — **SPI Block Guide** (S12SPIV3, document S12SPIV3/D). The nearest thing to a normative SPI document: the origin of `CPOL`/`CPHA`, the mode numbering used everywhere since, and the definition of the shift-register exchange that makes every read a write.
- Winbond — [**W25Q128JV datasheet**](https://www.winbond.com/hq/product/code-storage-flash-memory/serial-nor-flash/?__locale=en). AC characteristics table for `t_CLQV` (clock low to output valid), the target-side term in the round-trip arithmetic above, and the per-voltage-range clock ceilings that show how far the front-page "133 MHz" is from a usable board number.
- STMicroelectronics — [**AN4899**, *STM32 GPIO configuration for hardware settings and low-power consumption*](https://www.st.com/resource/en/application_note/an4899-stm32-gpio-configuration-for-hardware-settings-and-lowpower-consumption-stmicroelectronics.pdf). Output speed settings versus edge rate and the resulting emissions and ringing — the basis for the "turn `OSPEEDR` down" fix above.
