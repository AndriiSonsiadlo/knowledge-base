---
id: uart-in-depth
title: UART in Depth
sidebar_label: UART in Depth
sidebar_position: 5
tags: [embedded, peripherals, uart, usart, dma, baud-rate, stm32, drivers]
---

# UART in Depth

A UART has no clock wire. That single fact generates every interesting property of the peripheral and every way it fails. SPI and I²C both ship a clock alongside the data, so the receiver is told exactly when to look; a UART receiver is told nothing. It sees a falling edge, starts its own counter, and from that moment guesses where the bit centres are using an oscillator the transmitter has never met. Everything below — the divider arithmetic, the oversampling modes, the tolerance budget, the overrun flag — is machinery built around that one guess.

The mental model: **the receiver resynchronises exactly once per frame, on the start bit's falling edge, and then free-runs for ten bit times.** A frequency error between the two ends does not cause an immediate failure; it accumulates. The first data bit is sampled almost dead centre and the last one is sampled near an edge, so a link with a 3% error corrupts the *high* bits of a byte and leaves the low ones intact. That asymmetry is the signature you look for on a scope, and it is why "it works at 9600 but not at 115200" is a clock problem and not a wiring problem.

:::info[Prerequisites]
[The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md) owns the universal bring-up sequence — clock enable and read-back, reset pulse, pins, configure while disabled, clear flags, enable last. This page assumes it and only describes what is specific to the USART inside step 4. [Configuring the Clock Tree](../04-bare-metal-programming/clock-tree-configuration.md) is where `PCLK1` and `PCLK2` come from, and every number on this page is a function of one of them. For what a UART *is* and how it compares to SPI and I²C, [Serial Buses — I2C, SPI & UART](../../computer-science/buses-and-io/serial-buses-i2c-spi-uart.md) is the canonical page; this one starts where that one stops.
:::

## The frame, and where the receiver looks

```wavedrom title="One 8-E-1 frame: start bit, eight data bits LSB first, even parity, stop bit. The line idles high" alt="Waveform of a UART frame showing the line idle high, a low start bit, eight data bits b0 through b7 transmitted least significant bit first, a parity bit, and a high stop bit, with an annotation spanning from the start edge to the stop bit sample point"
{ "signal": [
  { "name": "RX",
    "wave": "1.0.2.2.2.2.2.2.2.2.4.1..",
    "data": ["b0","b1","b2","b3","b4","b5","b6","b7","P"],
    "node": "..a....................b." }
],
  "edge": ["a<->b receiver free-runs 9.5 bit times"],
  "config": { "hscale": 1 }
}
```

Four things in that picture are worth stating precisely, because they are the ones people get wrong when hand-decoding a capture:

- **Data goes out LSB first.** A logic analyser configured for MSB-first shows every byte bit-reversed, which looks exactly like a baud mismatch until you notice `0x41` reading back as `0x82`.
- **The stop bit is not a bit, it is a minimum idle time.** One stop bit means "the line must be high for at least one bit period before the next start edge". A receiver that finds the line low where the stop bit should be raises a framing error (`FE`), and that is the flag that actually tells you the baud rate is wrong.
- **Parity, when enabled, replaces a data bit rather than adding one.** The `M` bit in `USART_CR1` selects the *total* word length — 8 bits (`M = 0`) or 9 (`M = 1`) — and with `PCE = 1` the parity bit occupies the most significant position **inside** that word rather than being appended to it (RM0383 §19.6.4). So **8-E-1 requires `M = 1`**: a nine-bit word of which eight bits are payload. Leaving `M = 0` with parity enabled gives you 7-E-1 and a far end that sees every byte truncated to seven bits. Nine bits is also the ceiling — this USART cannot produce a ten-bit word, so 9 data bits *plus* parity is not a configuration that exists on this part.
- **The sample point is 9.5 bit times from the edge for the last bit of an 8-N-1 frame.** That number is the entire tolerance budget, derived below.

## `USART_BRR`: the divider, exactly

The USART divides its input clock (`PCLK1` for USART2, `PCLK2` for USART1 and USART6 on this part) by a fixed-point value `USARTDIV` held in `USART_BRR`.

```wavedrom title="USART_BRR — a 12-bit integer mantissa and a 4-bit fraction, together forming USARTDIV" alt="Bit-field strip of the 16-bit USART baud rate register showing a four-bit DIV_Fraction field in bits 3 to 0 and a twelve-bit DIV_Mantissa field in bits 15 to 4"
{ "reg": [
    { "bits": 4,  "name": "DIV_Fraction", "attr": "rw", "type": 5 },
    { "bits": 12, "name": "DIV_Mantissa", "attr": "rw", "type": 4 }
  ],
  "config": { "bits": 16, "lanes": 1 }
}
```

| Bits | Field | Access | Reset | Meaning |
|---|---|---|---|---|
| 3–0 | `DIV_Fraction[3:0]` | rw | `0x0` | Fractional part of `USARTDIV`, in sixteenths. With `OVER8 = 1` this is only three bits — **bit 3 must be written as 0** and the fraction is in eighths. |
| 15–4 | `DIV_Mantissa[11:0]` | rw | `0x000` | Integer part of `USARTDIV`. Zero is not a usable value. |

The relation between the register and the line rate, from RM0383 §19.3.4:

```text
OVER8 = 0 (oversampling by 16):   baud = f_CK / (16 × USARTDIV)
OVER8 = 1 (oversampling by 8):    baud = f_CK / ( 8 × USARTDIV)
```

Worked, for USART2 on this board — `PCLK1` at its 50 MHz APB1 ceiling, 115200 baud, `OVER8 = 0`:

```text
USARTDIV   = 50 000 000 / (16 × 115 200) = 27.1267…
mantissa   = 27                                  → BRR[15:4] = 0x01B
fraction   = round(0.1267 × 16) = 2              → BRR[3:0]  = 0x2
BRR        = (27 << 4) | 2 = 0x01B2 = 434
USARTDIV   = 434 / 16 = 27.125          (what the hardware actually uses)
baud       = 50 000 000 / 434 = 115 207.37
error      = (115 207.37 − 115 200) / 115 200 = +0.0064 %
```

Six ten-thousandths of a percent. That link will never fail for timing reasons. Now the same arithmetic on a board running from the 16 MHz HSI because nobody configured the PLL:

| `f_CK` | `OVER8` | Target | `BRR` | `USARTDIV` | Achieved | Error |
|---|---|---|---|---|---|---|
| 50 MHz | 0 | 115 200 | `0x01B2` | 27.125 | 115 207.4 | **+0.006 %** |
| 50 MHz | 0 | 921 600 | `0x0036` | 3.375 | 925 925.9 | **+0.47 %** |
| 16 MHz | 0 | 115 200 | `0x008B` | 8.6875 | 115 107.9 | **−0.08 %** |
| 16 MHz | 0 | 230 400 | `0x0045` | 4.3125 | 231 884.1 | **+0.64 %** |
| 16 MHz | 0 | 921 600 | `0x0011` | 1.0625 | 941 176.5 | **+2.12 %** |
| 16 MHz | **1** | 921 600 | `0x0021` | 2.125 | 941 176.5 | **+2.12 %** |

The pattern is the one to internalise: **error grows as `USARTDIV` shrinks**, because the fraction field is a fixed number of sixteenths and those sixteenths are a larger share of a small divider. A divider above about 16 gives you error in the hundredths of a percent for free. A divider below 4 is where links start being flaky on cold mornings.

### `OVER8` does not make the baud rate more accurate

This is the part almost every tutorial gets backwards. The last two rows of the table are the same clock and the same target rate in the two oversampling modes, and the achieved baud rate is *identical* — not similar, identical: 941 176.5 either way, `+2.12 %` either way. The reason is arithmetic: `OVER8` doubles `USARTDIV` and simultaneously coarsens the fraction from sixteenths to eighths, so the granularity in hertz is unchanged.

```text
OVER16:  step in USARTDIV = 1/16,  baud = f/(16·D)   → relative step = (1/16)/D
OVER8:   step in USARTDIV = 1/8,   D' = 2D           → relative step = (1/8)/(2D) = (1/16)/D
```

`OVER8` exists for exactly one reason: it raises the maximum achievable line rate from `f_CK/16` to `f_CK/8` — 12.5 Mbit/s on USART1 with `PCLK2` at 100 MHz. It costs you roughly half the receiver's clock-deviation tolerance, for the reason worked out in the next section. Use it only when you genuinely need a rate above `f_CK/16`.

## Where the 2% ceiling comes from

The receiver's only synchronisation event is the start bit's falling edge. After that, it counts its own oversampling ticks. For an 8-N-1 frame the last bit it must sample is the stop bit, whose centre is **9.5 bit times** after that edge. If the combined transmitter-plus-receiver frequency error is ε, the sample lands 9.5ε bit times away from where it should.

Three things eat the half-bit of margin before ε gets any:

| Consumer of the margin | `OVER8 = 0` (16 ticks/bit) | `OVER8 = 1` (8 ticks/bit) |
|---|---|---|
| Nominal margin: half a bit either side of the bit centre | 0.500 bit | 0.500 bit |
| Start-edge detection lands up to one oversampling tick late | −0.0625 bit | −0.125 bit |
| Outermost of the three majority-vote samples, 1.5 ticks off centre | −0.094 bit | −0.188 bit |
| **Remaining for accumulated frequency error** | **0.344 bit** | **0.188 bit** |
| **Maximum total ε** = remaining ÷ 9.5 bit times | **≈ 3.6 %** | **≈ 2.0 %** |

That is where the folklore number comes from, and it is not folklore — **2% is what the arithmetic gives you when the receiver oversamples by 8.** RM0383 §19.3.5 tabulates ST's own figures for each combination of `M`, `OVER8` and whether `BRR[3:0]` is zero; they land in the same 2-to-4% region, because the table is computing exactly this.

Two more things narrow it further in practice. The figure is the *total* across both ends of the link, so two independent oscillators split it. And it assumes a clean edge — real rise time, cable slew and noise all consume margin before ε gets any. Hence the working rule: **design each end to under 1%, treat 2% total as the ceiling, and never ship a link above 3%.**

Two consequences that follow directly:

- **A crystal is not always necessary, but the HSI is not always sufficient.** The STM32F411's internal HSI is factory-trimmed to ±1% at 25 °C but drifts to roughly ±3% over the full −40 to +105 °C range (STM32F411 datasheet DS10314, "Internal clock source characteristics"). At room temperature a HSI-clocked UART works; in a car in July it does not, and the failure is intermittent framing errors that nobody can reproduce on a desk.
- **A nine-bit word is less tolerant.** The longest frame this USART can send is `M = 1` with `PCE = 1` — one start bit, a nine-bit word carrying eight data bits plus parity, one stop bit. That puts the stop bit's centre **10.5** bit times from the resync edge instead of 9.5, so every figure in the table above scales by 9.5 / 10.5: about **9.5 % less margin**. `OVER16` falls from ≈ 3.6 % to **≈ 3.3 %** and `OVER8` from ≈ 2.0 % to **≈ 1.8 %**. That last number is the one that matters — with parity and eight data bits at `OVER8`, the total budget is already *below* the 2 % rule of thumb, so the rule stops being conservative and becomes the hard limit.

## The overrun error nobody handles

`ORE` sets when a complete word arrives in the shift register while `RXNE` is still 1 — that is, while the previous byte is still sitting in `USART_DR` unread. The new byte is discarded. The old one survives (RM0383 §19.6.1, `USART_SR` bit 3).

The trap is the clearing rule. `ORE` is cleared by **a read of `USART_SR` followed by a read of `USART_DR`**, and that is precisely the sequence a normal receive handler performs anyway:

```c
void USART2_IRQHandler(void)
{
    if (USART2->SR & USART_SR_RXNE) {   /* read of SR   ← half the clear sequence */
        rx_buf[head++] = USART2->DR;    /* read of DR   ← the other half          */
    }
}
```

That handler silently clears `ORE` on every byte. It does not just fail to report the overrun; it **destroys the evidence that one happened**. The application sees a byte stream with occasional holes, blames the cable, and adds a checksum. The correct form tests the error flags from the same `SR` snapshot before consuming the data:

```c
void USART2_IRQHandler(void)
{
    uint32_t sr = USART2->SR;                    /* one snapshot, tested repeatedly */

    if (sr & (USART_SR_ORE | USART_SR_FE | USART_SR_NE | USART_SR_PE)) {
        (void)USART2->DR;                        /* completes the clear sequence    */
        stats.overrun += (sr & USART_SR_ORE) ? 1u : 0u;
        stats.framing += (sr & USART_SR_FE)  ? 1u : 0u;
        rx_resync();                             /* the stream is no longer framed  */
        return;
    }

    if (sr & USART_SR_RXNE) {
        rx_buf[head] = (uint8_t)USART2->DR;
        head = (head + 1u) & (RX_BUF_SIZE - 1u);
    }
}
```

The counters are the point. An overrun rate you can read over the debug console turns "the link is unreliable" into a number that either is or is not zero.

`ORE` in a DMA-driven receiver is worse, because nothing in the DMA path ever reads `USART_SR`. The DMA controller reads `USART_DR` only. Once `ORE` latches it stays latched, and if `CR3.EIE` is set the error interrupt re-asserts the instant your handler returns, giving you a core that does nothing but service one flag. If you enable DMA reception you must also implement the error path that performs the `SR`-then-`DR` sequence.

## DMA reception with idle-line detection

The robust receive architecture for a UART carrying variable-length messages is not an interrupt per byte. It is a **circular DMA into a ring buffer plus the `IDLE` flag**, and it has the property that the CPU touches the peripheral only when a message boundary occurs, not when a byte does.

```wavedrom title="Three bytes, a gap, then two more. The IDLE flag fires one frame time after the last stop bit, marking the message boundary" alt="Waveform showing a UART receive line carrying three bytes back to back, DMA write pulses as each byte lands, an idle gap, the IDLE status flag asserting one frame time into the gap and being cleared by software, then two further bytes"
{ "signal": [
  { "name": "RX",        "wave": "1.2.2.2.1.......2.2.1...", "data": ["B0","B1","B2","B3","B4"] },
  { "name": "DMA write", "wave": "0..101010........1010..." },
  { "name": "IDLE",      "wave": "0.........1..0.........." }
],
  "config": { "hscale": 1 }
}
```

The mechanism, in order:

1. **DMA1 Stream 5, Channel 4** is the USART2 receive request on this part (RM0383 §9.3.3, "DMA1 request mapping"). Configure it peripheral-to-memory, byte-wide, circular, with `NDTR` set to the ring size, and set `USART_CR3.DMAR`.
2. The DMA writes every received byte into the ring with no CPU involvement at all. `NDTR` counts *down*, so the write position is `size − NDTR` at any instant.
3. **`USART_SR.IDLE`** sets when the line has been idle for one full frame time after a byte. Enable it with `USART_CR1.IDLEIE`. It is the only signal you get that a message has ended, because the UART has no packet concept.
4. In the `IDLE` handler, read `NDTR`, compute the new head, and hand `[tail, head)` to the parser. Then advance `tail`. Clear `IDLE` with the same `SR`-then-`DR` sequence `ORE` uses.
5. Also enable the DMA's **half-transfer** and **transfer-complete** interrupts. They handle the case of a message long enough to wrap the ring before any idle gap occurs — without them, a continuous stream silently overwrites unread data.

```c
/* Called from the USART IDLE interrupt and from the DMA HT/TC interrupts alike.
 * Idempotent: it consumes whatever has arrived since the last call. */
static void rx_drain(void)
{
    size_t head = RX_RING_SIZE - (size_t)(DMA1_Stream5->NDTR);

    if (head != rx_tail) {
        if (head > rx_tail) {
            parse(&rx_ring[rx_tail], head - rx_tail);
        } else {                                   /* wrapped: two segments */
            parse(&rx_ring[rx_tail], RX_RING_SIZE - rx_tail);
            parse(&rx_ring[0], head);
        }
        rx_tail = head;
    }
}
```

Two properties make this worth the setup cost. First, the **CPU cost per byte is zero**; at 921600 baud a per-byte interrupt fires every 10.8 µs, which on a 100 MHz M4 is a meaningful fraction of the core spent on entry and exit alone. Second, and more important, **overrun becomes structurally impossible for the peripheral** — the DMA always drains `DR` within one byte time, so `RXNE` never stays set long enough for `ORE` to arise. The overflow risk moves up a level, to the ring buffer, where it is visible and where you can size against it.

:::warning[The link that works on the bench and fails in the field, and the handler that ate its own error flag]
Two UART failures that cost days, both invisible in code review.

**Baud error that only shows up hot.** A board clocked from the HSI at 115200 works perfectly on a desk. Deployed, it drops one message in a few hundred, then more as the enclosure warms. The HSI's ±1% factory trim at 25 °C becomes roughly ±3% across temperature (DS10314, internal clock source characteristics), and the far end contributes its own error. Total ε crosses the ~3.6% ceiling and the *last* bits of each byte start being mis-sampled — which is the tell. Capture the failing traffic: if the corrupted bytes differ from the intended ones only in their high bits, and low bits are always right, it is a clock problem, not noise. The fix is a crystal or an external clock reference, not a lower baud rate — although lowering the rate does buy margin, because it does not change ε at all. Check `FE` counts: framing errors climbing with temperature is the same diagnosis from the other side.

**The `if (SR & RXNE) { DR }` handler.** Shown above, present in most codebases, and it clears `ORE` as a side effect of the read sequence that tests for `RXNE`. Symptom: a protocol that occasionally loses a byte, no error ever reported, and an `HAL_UART_ErrorCallback` that never fires. In a debugger it is worse — single-stepping with `USART2->SR` in a watch window performs the first half of the clear sequence on *every* step, so the flag you are trying to catch disappears as you look at it. Diagnose it by adding an unconditional counter for each of `ORE`, `FE`, `NE` and `PE` tested from a single `SR` read, and print them. If `stats.overrun` is non-zero, the receiver is too slow and the answer is DMA, not a bigger buffer.
:::

## Flow control, and when it is the real fix

`RTS`/`CTS` hardware flow control is enabled by `USART_CR3.RTSE` and `CR3.CTSE` and costs two more pins. `RTS` is asserted by the USART itself when its receiver can accept data and deasserted when it cannot; `CTS` gates the transmitter. It is the only mechanism that stops the far end sending faster than you can consume, and no amount of buffering substitutes for it on a link where the source is genuinely faster than the sink — a buffer only changes how long it takes to overflow.

The reason it is often not the answer on an MCU is that with DMA reception the sink is never the limiting factor. Flow control matters when the *parser* is slow, and in that case the honest fix is usually a bigger ring plus back-pressure at the application layer, because deasserting `RTS` mid-message stalls the far end in a state its firmware may not handle. Reach for `RTS`/`CTS` when talking to a modem, a Bluetooth module, or a PC — devices that implement it properly — and not as a patch over a receive path that drops bytes.

:::note[USART, UART, and which instances have which]
On STM32 the peripheral is a **USART** — it has a synchronous mode with a clock output, plus IrDA, LIN, smartcard and half-duplex modes layered on the same registers. Some instances on larger parts are cut down to plain **UART** and simply lack those registers. On the STM32F411 all three (USART1, USART2, USART6) are full USARTs. This also means `USART_CR2` and `CR3` contain a lot of fields that have nothing to do with asynchronous serial; leaving them at reset is correct and is what step 4 of the bring-up sequence assumes.
:::

## See also

- [The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md) — the six-step bring-up sequence this page's step 4 plugs into, and the read-back guard after the clock enable.
- [SPI in Depth](./spi-in-depth.md) — the same peripheral shape with a clock wire, which is exactly what removes every tolerance problem on this page.
- [I2C in Depth](./i2c-in-depth.md) — the third bus, and the one where the failure modes are electrical rather than temporal.
- [Serial Buses — I2C, SPI & UART](../../computer-science/buses-and-io/serial-buses-i2c-spi-uart.md) — what a UART is, the pin and topology comparison against SPI and I²C, and when to choose it.
- [Configuring the Clock Tree](../04-bare-metal-programming/clock-tree-configuration.md) — where `PCLK1` and `PCLK2` come from, and why an HSI-only configuration is the root cause of half the failures above.

## References

- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4**. §19.3.4 for the `USARTDIV` formula and both oversampling modes; §19.3.5 for the receiver clock-deviation tolerance tables and the `DTRA`/`DQUANT`/`DREC`/`DTCL` budget those tables sum; §19.3.6 for the overrun definition and the `SR`-then-`DR` clear sequence; §19.6.1 for `USART_SR` and §19.6.3 for `USART_BRR`; §9.3.3 for the DMA1 request mapping that puts USART2_RX on Stream 5, Channel 4.
- STMicroelectronics — [**DS10314**, *STM32F411xC/E datasheet*](https://www.st.com/resource/en/datasheet/stm32f411re.pdf). "Internal clock source characteristics" for the HSI accuracy over temperature quoted above (factory trim at 25 °C versus the full −40 to +105 °C range), and Table 9 "Alternate function mapping" for the AF7 assignment of USART1/2 pins.
- STMicroelectronics — [**AN3109**, *Communication peripheral FIFO emulation with DMA and DMA timeout*](https://www.st.com/resource/en/application_note/an3109-communication-peripheral-fifo-emulation-with-dma-and-dma-timeout-in-stm32f10xxx-microcontrollers-stmicroelectronics.pdf). ST's own treatment of the circular-DMA-plus-timeout receive architecture. Written against the F1 but the mechanism and the `NDTR` arithmetic are identical on the F4.
- Tilen Majerle — [**stm32-usart-uart-dma-rx-tx**](https://github.com/MaJerle/stm32-usart-uart-dma-rx-tx). Working, per-family reference implementations of the idle-line plus circular DMA pattern, including the half-transfer/transfer-complete handling for streams that wrap before an idle gap occurs, and the F4-specific `ORE` handling in DMA mode.
- STMicroelectronics — [**UM1724**, *STM32 Nucleo-64 boards*](https://www.st.com/resource/en/user_manual/um1724-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf), Rev 14. §6.8 for the ST-LINK virtual COM port wired to USART2 on PA2/PA3, which is the instance every example on this page targets.
