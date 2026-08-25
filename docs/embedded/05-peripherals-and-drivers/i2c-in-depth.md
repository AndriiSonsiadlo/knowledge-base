---
id: i2c-in-depth
title: I2C in Depth
sidebar_label: I2C in Depth
sidebar_position: 7
tags: [embedded, peripherals, i2c, addressing, clock-stretching, bus-recovery, stm32]
---

# I2C in Depth

I²C is the only one of the three common serial buses whose electrical design is part of its protocol. SPI and UART drive their lines push-pull: a driver holds each wire at a rail and nothing else may contend. I²C wires are **open-drain** — every device can pull them low and nobody can drive them high. The high level is produced by a resistor. That one decision buys the bus everything it is known for: multiple controllers on the same two wires, targets that can pause the controller, collision detection that costs no extra hardware, and the ability to hang three sensors off two pins.

It also buys every one of its failure modes. A resistor charging a capacitive wire has a rise time you can measure, which is why the specification quotes a maximum bus capacitance next to every speed. A device that can pull a line low can hold it low forever, which is why a bus can be wedged by a target that no longer exists as far as your firmware is concerned. And because "released" and "high" are the same state, the controller cannot tell the difference between a well-behaved target and a broken wire.

The mental model: **on I²C, nobody drives high. Every transition to a one is a resistor charging a capacitor, and every deadlock is somebody still holding a zero.**

:::info[Prerequisites]
[The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md) owns the six-step bring-up sequence this page's configuration slots into, including the RCC clock-enable read-back. [Serial Buses — I2C, SPI & UART](../../computer-science/buses-and-io/serial-buses-i2c-spi-uart.md) owns what I²C is, its two-wire topology, its speed grades and the comparison against SPI and UART; this page is the register-level configuration, the addressing trap, and the recovery procedure for a wedged bus.
:::

## One transaction, exactly

```wavedrom title="A single-byte write: START, 7-bit address plus R/W low, target ACK, one data byte, target ACK, STOP" alt="Waveform of an I2C transaction showing SDA falling while SCL is high for the START condition, seven address bits, a write bit, an acknowledge pulled low by the target, eight data bits, a second acknowledge, and SDA rising while SCL is high for the STOP condition"
{ "signal": [
  { "name": "SCL", "wave": "1.01010101010101010101010101010101010101." },
  { "name": "SDA", "wave": "103.3.3.3.3.3.3.6.4.5.5.5.5.5.5.5.5.4.0.1",
    "data": ["a6","a5","a4","a3","a2","a1","a0","W","ACK","d7","d6","d5","d4","d3","d2","d1","d0","ACK"],
    "node":  ".a......................................b" }
],
  "edge": ["a START", "b STOP"],
  "config": { "hscale": 1 }
}
```

The two conditions that frame everything are defined by **SDA moving while SCL is high**, which is illegal at every other moment:

- **START** — SDA falls while SCL is high. The bus becomes busy.
- **STOP** — SDA rises while SCL is high. The bus becomes free.
- **Repeated START** — a second START issued instead of a STOP, so the controller keeps ownership of the bus across a direction change. This is what a register read is: write the register address, repeated START, read. Issuing a STOP there instead gives another controller a window to interleave, and on a multi-controller bus that is a real corruption, not a theoretical one.

Everywhere else, SDA is only allowed to change while SCL is low, which is what makes the START and STOP patterns unambiguous. The acknowledge is the ninth clock of every byte: the transmitter releases SDA and the receiver pulls it low to say "got it". A *not*-acknowledge — SDA left high on the ninth clock — is the only error signal the protocol has, and it means either "no device at this address" or "I am done reading".

## The 7-bit address shift, which is where a day goes

This is the single most common I²C bring-up failure, and it is not a subtle one. The address occupies **bits 7 through 1** of the first byte on the wire. Bit 0 is the read/write direction. So the byte on the wire is:

```text
wire byte = (address7 << 1) | direction     /* direction: 0 = write, 1 = read */
```

The problem is that **datasheets and APIs disagree about which of those two numbers they print**, with no convention to tell them apart. The same MPU-6050 accelerometer is documented, correctly, in all of these forms:

| What a document says | What it means | On the wire (write) |
|---|---|---|
| "Slave address `0x68`" | 7-bit address | `0xD0` |
| "Device address `0b1101000`" | 7-bit address | `0xD0` |
| "Write address `0xD0`, read address `0xD1`" | 8-bit, already shifted | `0xD0` |
| "I²C address `0xD0`" | 8-bit, already shifted | `0xD0` |

And the software you call splits the same way:

| API | Expects | Same device |
|---|---|---|
| Linux `i2cdetect`, `i2c-tools`, device tree `reg` | 7-bit | `0x68` |
| Arduino `Wire.beginTransmission()` | 7-bit | `0x68` |
| Zephyr `i2c_write_dt()`, `struct i2c_dt_spec` | 7-bit | `0x68` |
| **ST HAL `HAL_I2C_Master_Transmit(hi2c, DevAddress, …)`** | **8-bit, pre-shifted** | **`0xD0`** |
| Writing `I2C1->DR` directly on this part | 8-bit, pre-shifted | `0xD0` |

ST's HAL is the outlier in the list, and it is the one a reader of this page is most likely to be using. Passing `0x68` to `HAL_I2C_Master_Transmit` sends `0x34` on the wire — the address of nothing — and you get `HAL_ERROR` with `AF` set. Passing `0xD0` to Arduino's `Wire` shifts it again to `0xA0`, truncated from `0x1A0`, which is the address of a completely different class of device (a 24-series EEPROM) and may well ACK if one is on your bus.

Two habits remove the problem permanently:

- **Write an address scanner and run it first.** Loop 0x08 to 0x77, issue a START with the write bit, look for an ACK, issue a STOP. Print the **7-bit** value, and say so in the output. Whatever the scanner finds is ground truth, and it takes ten minutes to write.
- **Store 7-bit in your code and shift at the register.** Make the shift happen in exactly one place — the peripheral access layer described in [Writing a Driver Worth Reusing](./writing-a-portable-driver.md) — so that every device driver above it speaks the same convention as every datasheet's "slave address" line.

The failure signature is worth memorising: **`SR1.AF` set immediately after the address byte, and a logic analyser showing the ninth clock with SDA high.** Nothing responded. If the scanner finds the device at an address exactly half of what you are sending, or exactly double, you have found a shift.

## Configuring the timing on this part

The STM32F411 carries the older I²C block — `CCR`, `TRISE` and `CR2.FREQ`, not the `TIMINGR` register of the L4/F7 generation. Three registers have to agree, and all three are derived from `PCLK1`.

**`CR2.FREQ[5:0]`** must be set to the APB1 frequency **in MHz** as an integer. It is not a prescaler; it tells the block how long a microsecond is, so that it can enforce the specification's minimum setup and hold times. At `PCLK1 = 50 MHz` you write `50`. Getting it wrong does not scale the clock — it corrupts the internal timing, which is more confusing.

**`CCR[11:0]`** sets the clock period, with different arithmetic per mode:

| Mode | `F/S` | `DUTY` | Period | `CCR` for `PCLK1` = 50 MHz | Achieved SCL |
|---|---|---|---|---|---|
| Standard, 100 kHz | 0 | — | `2 × CCR × T_PCLK1` | `50e6 / (2 × 100e3)` = **250** | 100.0 kHz |
| Fast, 400 kHz, 1:2 duty | 1 | 0 | `3 × CCR × T_PCLK1` | `50e6 / (3 × 400e3)` = 41.7 → **42** | 396.8 kHz |
| Fast, 400 kHz, 16:9 duty | 1 | 1 | `25 × CCR × T_PCLK1` | `50e6 / (25 × 400e3)` = **5** | 400.0 kHz |

**`TRISE[5:0]`** is the maximum permitted SDA/SCL rise time expressed in `PCLK1` periods, plus one:

```text
TRISE = (t_r,max × f_PCLK1) + 1

Standard mode, t_r,max = 1000 ns:   (1000e-9 × 50e6) + 1 = 51
Fast mode,     t_r,max =  300 ns:   ( 300e-9 × 50e6) + 1 = 16
```

Those 1000 ns and 300 ns limits are not ST's; they come from the bus specification (NXP UM10204 Table 10), and that is the point of the register — it is how the peripheral enforces a standard it did not write. `TRISE` must be programmed while `PE = 0`.

`CCR` and `TRISE` are the two most commonly wrong registers on a working-looking bus. An `SCL` measured at 396.8 kHz instead of 400 kHz is fine and expected. An `SCL` at 250 kHz when you asked for 400 means `FREQ` or `CCR` disagrees with the actual `PCLK1`, which usually means the clock tree was reconfigured after `I2C_Init` ran.

## Pull-up resistors, sized rather than guessed

4.7 kΩ is the number everyone uses and it is right about half the time. The bus specification gives both bounds directly (UM10204 §7.1).

**Minimum**, set by how much current the open-drain output can sink while still holding a valid low. A device must pull SDA below `V_OL,max` = 0.4 V while sinking `I_OL` = 3 mA:

```text
R_p(min) = (V_DD − V_OL,max) / I_OL = (3.3 − 0.4) / 3 mA ≈ 970 Ω
```

**Maximum**, set by the rise time the resistor can achieve against the bus capacitance. The rise is an RC charge from 0.3 V_DD to 0.7 V_DD, giving the specification's constant of `ln(7/3) = 0.847`:

```text
R_p(max) = t_r,max / (0.847 × C_b)
```

| Mode | `t_r,max` | `C_b` | `R_p(max)` |
|---|---|---|---|
| Standard, 100 kHz | 1000 ns | 100 pF (short PCB, two devices) | 11.8 kΩ |
| Standard, 100 kHz | 1000 ns | 400 pF (the spec's ceiling) | 2.95 kΩ |
| Fast, 400 kHz | 300 ns | 200 pF | 1.77 kΩ |
| Fast, 400 kHz | 300 ns | 400 pF | 0.89 kΩ — **below `R_p(min)`; the bus cannot be built** |

The last row is the one that matters. **At 400 kHz with a fully loaded bus there is no valid resistor value.** The specification's 400 pF ceiling and its 300 ns rise time are mutually satisfiable only with a stronger pull-down than a standard I²C output provides. In practice that means: at Fast mode you must keep the bus short, and 4.7 kΩ — a perfectly good Standard-mode value on a small board — gives a rise time of about 1.6 µs at 400 pF, which is five times the Fast-mode limit and produces exactly the intermittent, temperature-sensitive, "works with the scope probe attached" behaviour that makes I²C infamous. Fit 2.2 kΩ for a 400 kHz bus and measure the rise time rather than assuming it.

Every device on the bus contributes 5–10 pF of pin capacitance, every centimetre of PCB trace roughly 1 pF, and a breadboard jumper considerably more. Two sensors and 10 cm of wire is comfortably inside budget; six sensors on a ribbon cable is not.

## Clock stretching

A target that needs time — an EEPROM committing a page, a sensor finishing a conversion, or a microcontroller acting as a target and taking an interrupt — **holds SCL low after the acknowledge**. The controller, which only *releases* SCL and never drives it high, sees the line stay low and waits. There is no timeout in the base specification; the controller simply cannot proceed.

```wavedrom title="The target holds SCL low after the ACK. The controller has released SCL but the line does not rise until the target lets go" alt="Waveform showing an I2C acknowledge followed by the controller releasing SCL while the line stays low because the target is stretching the clock, then the line rising and clocking resuming when the target releases it"
{ "signal": [
  { "name": "SCL — controller", "wave": "010101......010" },
  { "name": "SCL — the wire",   "wave": "01010.....1.010" },
  { "name": "SDA",              "wave": "3.4.x.......5..", "data": ["d0","ACK","d7"] },
  { "name": "target pulls SCL", "wave": "0...1.....0...." }
],
  "config": { "hscale": 2 }
}
```

Three consequences a driver has to handle:

- **Your controller must not time out too aggressively.** An AT24C-series EEPROM can stretch for milliseconds after a page write. A watchdog kicked only from the main loop will reset the board mid-transaction, which is one of the ways a bus ends up wedged in the first place.
- **The STM32 stretches too, and it will surprise you in a debugger.** As a controller, this block holds SCL low whenever `BTF` is set and software has not yet read or written `DR`. Halt on a breakpoint inside an I²C interrupt handler and the bus sits stretched for as long as you are looking at it. Many devices tolerate this; anything implementing SMBus does not, because SMBus defines a 25–35 ms timeout after which a target must release the bus and reset itself. That is a genuinely nasty debugging experience — the device state changes because you stopped to look at it.
- **As a target, stretching is optional and off is dangerous.** `CR1.NOSTRETCH` disables it. Setting it means an STM32 in target mode that is not ready simply loses the byte. The block also stretches SCL after an address match until software performs the `SR1`-then-`SR2` read sequence that clears `ADDR` — which is why that sequence is not optional and why a target driver that forgets it stalls the whole bus.

## Arbitration

Because SDA is open-drain and wired-AND, two controllers can start transmitting simultaneously without damage. Each one reads back the line while driving it. A controller that transmits a `1` — releases SDA — and reads back a `0` knows another controller is driving low, **loses arbitration immediately, stops driving, and reverts to target mode**. On this part that sets `SR1.ARLO`.

The elegance is that the winner never notices. The two controllers agreed bit-for-bit up to the point of divergence, so the winning message is transmitted intact and no data is lost. The loser retries when the bus is free.

Arbitration is also why a bus with two controllers needs both to have the same clock rate configured, or at least compatible ones: SCL is wired-AND too, so the effective clock is the slowest controller's low period and the fastest one's high period — a shape neither of them programmed.

## Recovering a bus a target has locked

This is the failure nobody documents and everybody hits. The sequence:

1. Your controller is mid-transaction, reading a byte from a target. The target is driving SDA low for a `0` bit.
2. The MCU resets — a watchdog, a debugger, a power glitch, or you pressed the button.
3. The MCU comes back with no memory of the transaction. The target does not reset; it has no reset line and no reason to.
4. The target is still waiting for the rest of its clocks, still driving SDA low.
5. Your firmware tries to issue a START, which requires pulling SDA low **while SCL is high**. SDA is already low. The START never appears on the wire, the peripheral's `SR2.BUSY` never clears, and every transaction times out.

The bus is not broken and no hardware is damaged. There is a target sitting mid-byte waiting for clock pulses that nobody is sending. **The fix is to send them.**

The bus specification prescribes the procedure directly (UM10204 §3.1.16, "Bus clear"): if SDA is stuck low, the controller sends **up to nine clock pulses** on SCL. Nine, because a byte is eight bits plus the acknowledge slot — after at most nine clocks the target has shifted out everything it had and released SDA. Then a manual STOP returns the bus to idle.

```c
/* Bus recovery for I2C1 on PB8 (SCL) / PB9 (SDA), AF4, open-drain.
 * Call before I2C init, and from the error path when BUSY is stuck. */
static void i2c1_bus_recover(void)
{
    I2C1->CR1 &= ~I2C_CR1_PE;                 /* 1. release the peripheral's grip */

    /* 2. Take both pins as GPIO open-drain outputs, driven high (= released). */
    GPIOB->BSRR   = GPIO_BSRR_BS8 | GPIO_BSRR_BS9;
    GPIOB->OTYPER |= GPIO_OTYPER_OT8 | GPIO_OTYPER_OT9;
    gpio_set_mode(GPIOB, 8, GPIO_MODE_OUTPUT);
    gpio_set_mode(GPIOB, 9, GPIO_MODE_OUTPUT);

    /* 3. Up to nine SCL pulses at ~100 kHz, stopping as soon as SDA is released. */
    for (int i = 0; i < 9 && !(GPIOB->IDR & GPIO_IDR_ID9); i++) {
        GPIOB->BSRR = GPIO_BSRR_BR8;  delay_us(5);   /* SCL low  */
        GPIOB->BSRR = GPIO_BSRR_BS8;  delay_us(5);   /* SCL high */
    }

    /* 4. A manual STOP: SDA low while SCL is high, then SDA released. */
    GPIOB->BSRR = GPIO_BSRR_BR9;  delay_us(5);       /* SDA low, SCL already high */
    GPIOB->BSRR = GPIO_BSRR_BS9;  delay_us(5);       /* SDA rises with SCL high = STOP */

    /* 5. Pins back to alternate function, then reset the peripheral. */
    gpio_set_af(GPIOB, 8, 4);  gpio_set_mode(GPIOB, 8, GPIO_MODE_AF);
    gpio_set_af(GPIOB, 9, 4);  gpio_set_mode(GPIOB, 9, GPIO_MODE_AF);

    I2C1->CR1 |=  I2C_CR1_SWRST;              /* RM0383 §18.6.1: forced reset      */
    I2C1->CR1 &= ~I2C_CR1_SWRST;
    i2c1_init();                               /* full re-init: FREQ, CCR, TRISE, PE */
}
```

Four details that decide whether it works:

- **Step 1 is not optional.** While `PE` is set the peripheral owns the pins' alternate function; the GPIO output data register has no effect until you release it.
- **Step 5 is not optional either.** The peripheral's internal state machine is still where the reset left it, and `BUSY` is latched. `CR1.SWRST` is documented for exactly this — RM0383 §18.6.1 describes it as a way to reinitialise the peripheral after an error or a locked state. Pulsing `RCC_APB1RSTR.I2C1RST` works as well and is stronger.
- **Nine clocks is a maximum, not a fixed count.** Check SDA after each pulse and stop early. Clocking a target that has already released SDA is harmless, but stopping early avoids confusing any other device that is listening.
- **Call it unconditionally at startup**, not just from an error path. A board that resets mid-transaction comes up with the bus already wedged, and running recovery once before `i2c1_init()` costs about 100 µs and removes an entire class of "needs a power cycle" bug reports.

If nine clocks do not free SDA, the target is not mid-byte — it has genuinely latched up, and only a hardware reset or a power cycle will clear it (UM10204 §3.1.16 says this in as many words). That is the argument for putting a MOSFET on the sensor rail on a board that must recover unattended.

:::warning[The bus that only works after a power cycle, and the address that was already shifted]
Two I²C failures, both of which look like broken hardware and neither of which is.

**`BUSY` stuck at 1 from the first transaction after a reset.** Every call returns a timeout, the peripheral never generates a START, and power-cycling the board fixes it until the next time. On a logic analyser SDA sits low with no activity at all. This is the wedged-target case above; the recovery routine is the fix and it belongs in start-up, not in a support note. On this part there is a second, sneakier cause with the same symptom: the STM32F4 erratum *"I²C analog filter may provide wrong value, locking `BUSY` flag and preventing master mode entry"* (ES0287) — a glitch on the bus can leave the analog filter's state wrong and `BUSY` latched with no target misbehaving at all. ST's published workaround is the same GPIO-toggling sequence, followed by `SWRST`. Implement it once and both causes are covered.

**`AF` set on the very first byte, on a device you can see on the board.** The address byte went out and nothing acknowledged the ninth clock. Ninety percent of the time this is the shift: you passed a 7-bit address to an API expecting 8-bit, or the reverse. Confirm with a scanner that prints 7-bit values, then compare against your constant — if the scanner says `0x68` and your code holds `0x68` but you are calling ST's HAL, that is the bug, and `0xD0` is the fix. The remaining cases are a missing pull-up (the whole bus reads as a flat line, since without a resistor nothing ever goes high), or a device whose address-select pin is floating rather than tied.
:::

:::note[This is the old I²C block]
The STM32F411 uses ST's first-generation I²C peripheral: `CR2.FREQ`, `CCR`, `TRISE`, and the event-driven `SR1`/`SR2` sequence with its `ADDR`-clearing double read. From the F0/F3/F7/L4 generation onward ST replaced it with a redesign whose timing lives in a single `TIMINGR` register generated by CubeMX, and which handles the one- and two-byte reception cases the old block requires special handling for. Code and app notes for one do not transfer to the other, and the register names are your quickest way to tell which generation a piece of example code targets. The bus specification itself, of course, is unchanged.
:::

## See also

- [The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md) — the bring-up sequence this page's `FREQ`/`CCR`/`TRISE` configuration is step 4 of, and the RCC read-back guard before it.
- [Writing a Driver Worth Reusing](./writing-a-portable-driver.md) — the layer boundary that the 7-bit-to-8-bit address shift belongs on, and the I²C seam used as its worked example.
- [SPI in Depth](./spi-in-depth.md) — the push-pull alternative, four wires instead of two, with none of the electrical failure modes above and none of the addressing either.
- [Serial Buses — I2C, SPI & UART](../../computer-science/buses-and-io/serial-buses-i2c-spi-uart.md) — what I²C is, its speed grades and topology, and how to choose between the three buses.
- [GPIO Electrical Behaviour](../01-hardware-foundations/gpio-electrical-behaviour.md) — open-drain outputs, internal versus external pull-ups, and the sink-current limits that set `R_p(min)` above.

## References

- NXP Semiconductors — [**UM10204**, *I2C-bus specification and user manual*](https://www.nxp.com/docs/en/user-guide/UM10204.pdf), Rev 7.0. The normative document. §3.1.4 for START/STOP and the SDA-changes-only-while-SCL-low rule; §3.1.9 for clock stretching; §3.1.8 for arbitration; **§3.1.16 "Bus clear"** for the nine-clock recovery procedure implemented above; §7.1 for the `R_p(min)`/`R_p(max)` derivation and the `0.847` constant; Table 10 for the per-mode rise-time and bus-capacitance limits that `TRISE` encodes.
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4**. §18.3.3 for controller-mode transfer sequencing and the `SR1`-then-`SR2` `ADDR` clear; §18.6.1 for `I2C_CR1` including `SWRST` and `NOSTRETCH`; §18.6.2 for `CR2.FREQ`; §18.6.8 for `CCR` and the `F/S`/`DUTY` period formulas; §18.6.9 for `TRISE`.
- STMicroelectronics — [**ES0287**, *STM32F411xC/E device errata*](https://www.st.com/resource/en/errata_sheet/es0287-stm32f411xcstm32f411xe-device-errata-stmicroelectronics.pdf). The I²C section, in particular "I²C analog filter may provide wrong value, locking `BUSY` flag and preventing master mode entry" — ST's own statement of the second `BUSY`-stuck cause and the GPIO-toggling plus `SWRST` workaround.
- STMicroelectronics — [**AN2824**, *STM32F10xxx I2C optimized examples*](https://www.st.com/resource/en/application_note/an2824-stm32f10xxx-i2c-optimized-examples-stmicroelectronics.pdf). Written for the F1 but describes the same first-generation block used on the F411. The definitive treatment of the `EV5`/`EV6`/`EV7` event sequence and of the awkward one-byte and two-byte reception cases where `ACK` and `POS` must be manipulated before the last byte arrives.
- Texas Instruments — [**SLVA689**, *Understanding the I2C Bus*](https://www.ti.com/lit/an/slva689/slva689.pdf). A short, vendor-neutral treatment of pull-up sizing and bus capacitance with worked examples, useful as a cross-check on the arithmetic above and clearer than UM10204 on why the two bounds can cross.
