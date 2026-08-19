---
id: analog-basics-adc-and-dac
title: "Analog Basics: ADC and DAC"
sidebar_label: Analog Basics
sidebar_position: 9
tags: [embedded, hardware, adc, dac, analog, stm32]
---

# Analog Basics: ADC and DAC

An analog-to-digital converter looks, from firmware, like a register you read. That framing hides the two things that actually determine whether the number is right. First, the conversion is a **comparison against a reference**, so the answer is a ratio, not a voltage — and a wrong or noisy reference is invisible in the result. Second, before any comparing happens the converter must **charge a small capacitor through your circuit**, and if you did not give it long enough, it will confidently report the voltage it managed to reach rather than the voltage that was there.

Both failures produce plausible numbers. Neither produces an error flag. That is why "my ADC reading is wrong" is one of the hardest first bugs in embedded work, and why this page spends most of its length on the second one — the sampling-time-versus-source-impedance relationship, which the datasheet states as a formula and most tutorials omit entirely.

:::info[Prerequisites]
[Power Supplies and Regulators](./power-supply-and-regulators.md) explains why V<sub>DDA</sub> — which on this part *is* the ADC's reference — is a rail you have to care about. [How a GPIO Pin Really Behaves](./gpio-electrical-behaviour.md) covers analog mode, which disconnects a pin's digital input buffer.
:::

## What the hardware does in one conversion

The STM32F411 has one 12-bit successive-approximation ADC (`ADC1`) with up to 16 external channels, plus internal channels for the temperature sensor and V<sub>BAT</sub> (RM0383 Rev 4, chapter 11). A single conversion has two distinct phases, and they are billed separately.

```wavedrom title="One 12-bit conversion: sampling then successive approximation" alt="ADC sample-and-hold timing showing the sampling window followed by the SAR phase"
{ signal: [
  { name: "ADCCLK",             wave: "p................." },
  { name: "SWSTART / trigger",  wave: "010.............." },
  { name: "sampling switch",    wave: "0.1....0........." , node: "..a....b" },
  { name: "C_ADC voltage",      wave: "x.2....3........." , data: ["charging via R_ADC + R_AIN", "held"] },
  { name: "SAR comparisons",    wave: "0......1......0.." , node: ".......c......d" },
  { name: "EOC flag",           wave: "0.............10." },
  { name: "ADC_DR",             wave: "x.............4.." , data: ["result"] }
 ],
 edge: [ "a<->b t_S (SMP cycles)", "c<->d 12 cycles" ],
 config: { hscale: 2 }
}
```

| Phase | Duration | What is happening |
|---|---|---|
| **Sample** | `t_S`, programmable per channel: 3, 15, 28, 56, 84, 112, 144 or 480 ADCCLK cycles (`SMP[2:0]` in `ADC_SMPR1`/`ADC_SMPR2`) | The sampling switch closes and the internal hold capacitor `C_ADC` charges towards the input voltage through the switch resistance `R_ADC` **plus whatever impedance your circuit presents**. |
| **Convert** | 12 ADCCLK cycles at 12-bit resolution | The switch opens; the captured charge is compared against successive fractions of V<sub>REF+</sub>, one bit at a time. Your circuit is disconnected and irrelevant during this phase. |

RM0383 Rev 4 §11.5 states the total plainly: `Tconv = Sampling time + 12 cycles`, and gives the worked case — "With ADCCLK = 30 MHz and sampling time = 3 cycles: Tconv = 3 + 12 = 15 cycles = 0.5 µs".

Every conversion problem that is not a reference problem lives in the first row of that table.

## Sampling time versus source impedance — the calculation nobody shows you

`C_ADC` charges through a resistance. The datasheet gives both halves: `R_ADC`, the sampling switch resistance, is up to `6 kΩ`, and `C_ADC`, the internal sample-and-hold capacitor, is `4 pF` typical and `7 pF` maximum (DS10314 Rev 8, §6.3.20, Table 65). Add your source's output impedance `R_AIN` in series and the time constant becomes `(R_ADC + R_AIN) × C_ADC`. AN2834 Rev 10 §3.2.7 states the consequence in one sentence: "If the sampling time is less than the time required to fully charge the C<sub>ADC</sub> through R<sub>ADC</sub> + R<sub>AIN</sub> (t<sub>s</sub> < t<sub>c</sub>), the digital value converted by the ADC is less than the actual value."

DS10314 Rev 8 turns that into a limit. Its **Equation 1**, on the page following Table 65, gives the maximum external impedance for an error below ¼ LSB:

```text
                 (k - 0.5)
R_AIN(max) = ------------------------- - R_ADC
              f_ADC x C_ADC x ln(2^(N+2))
```

where, in the datasheet's own words, "N = 12 (from 12-bit resolution) and k is the number of sampling periods defined in the ADC_SMPR1 register".

Now put this board's numbers in. On a Nucleo-F411RE running SYSCLK at 100 MHz, `PCLK2` is also at most 100 MHz (DS10314 Rev 8, Table 14). The ADC prescaler only offers ÷2, ÷4, ÷6 and ÷8 (RM0383 Rev 4, `ADCPRE` in `ADC_CCR`), and Table 65 caps `f_ADC` at `36 MHz` for V<sub>DDA</sub> = 2.4 to 3.6 V (the cap is `18 MHz` below that, for V<sub>DDA</sub> = 1.7 to 2.4 V) — so ÷2 (50 MHz) is illegal and **÷4, giving `f_ADC = 25 MHz`, is the fastest legal setting** at full core speed. With `C_ADC` at its `7 pF` worst case and `R_ADC` at its `6 kΩ` worst case:

| `SMP[2:0]` | `k` (cycles) | `t_S` at 25 MHz | Max source impedance for ¼ LSB | Full conversion | Max rate |
|---|---|---|---|---|---|
| `000` | 3 | 0.12 µs | **impossible** — the formula returns a negative number | 0.60 µs | 1.67 Msps |
| `001` | 15 | 0.60 µs | 2.5 kΩ | 1.08 µs | 926 ksps |
| `010` | 28 | 1.12 µs | 10.2 kΩ | 1.60 µs | 625 ksps |
| `011` | 56 | 2.24 µs | 26.7 kΩ | 2.72 µs | 368 ksps |
| `100` | 84 | 3.36 µs | 43.2 kΩ | 3.84 µs | 260 ksps |
| `101` | 112 | 4.48 µs | 50 kΩ (formula gives 59.7 kΩ; Table 65 caps R<sub>AIN</sub> at 50 kΩ) | 4.96 µs | 202 ksps |
| `110` | 144 | 5.76 µs | 50 kΩ (capped) | 6.24 µs | 160 ksps |
| `111` | 480 | 19.20 µs | 50 kΩ (capped) | 19.68 µs | 51 ksps |

Read the first row again. **At the reset default of 3 cycles, with worst-case internal parameters, there is no source impedance low enough** — the switch's own `6 kΩ` already consumes the entire budget. `(3 − 0.5) / (25 MHz × 7 pF × ln 2¹⁴)` comes to about `1.5 kΩ`, and subtracting `6 kΩ` leaves you negative. Even with the typical `4 pF` capacitor the margin is thin. The three-cycle setting exists for very fast, very low-impedance signals converted at a lower ADC clock, not for a sensor on a jumper wire.

And note how brutal the practical numbers are. A 10 kΩ potentiometer — the canonical first analog experiment — presents up to 2.5 kΩ at its midpoint. That needs `SMP = 010` (28 cycles) at this clock, nine times the default. A resistive divider built from 100 kΩ resistors presents 50 kΩ and is at the absolute limit of Table 65's `R_AIN` specification even at 480 cycles. A thermistor circuit, a photodiode, a strain-gauge bridge — all of these are high impedance, and all of them read low with default settings, in a way that looks exactly like a calibration error.

:::note[The table is deliberately pessimistic, and by how much]
It uses both worst-case internal parameters. `C_ADC` is `7 pF` max against `4 pF` typical, and — the one that is easy to miss — Table 65's note 4 says "`R_ADC` maximum value is given for V<sub>DD</sub> = 1.7 V, and minimum value for V<sub>DD</sub> = 3.3 V". At 3.3 V, which is where this board runs, the real switch resistance is therefore *below* the `6 kΩ` used here. So a spreadsheet built with typical values will give you noticeably larger permitted impedances than this table, and it will not be wrong — it will be less conservative. Design against the table; debug against the fact that your part is probably better than it.
:::

:::warning[The default sampling time is the single most common cause of wrong ADC readings]
The failure has a signature, and once you know it you will recognise it immediately:

- Readings are **consistently low**, never high. The capacitor was still charging when the switch opened, so the result is always short of the truth.
- The error **gets worse as the source impedance gets higher** — swapping a 10 kΩ pot for a 1 kΩ one visibly improves it.
- The error **gets worse as you scan more channels**, because a high-impedance channel converted right after a very different voltage starts from further away.
- The reading is **stable**. It is not noise. It is a wrong number that does not move, which is why it gets mistaken for a gain error and "fixed" with a scale factor that then breaks at a different temperature.

The fix is one field: raise `SMP[2:0]` for that channel until the reading stops changing. Sampling time is per channel, so a fast low-impedance signal and a slow sensor can coexist. Work out the number you need from the formula rather than by trial, and remember that the answer depends on `f_ADC` — halving the ADC clock doubles the impedance you can tolerate at the same `SMP` setting.
:::

## The reference is your 3.3 V rail

A ratiometric converter is only as good as what it compares against. On the LQFP64 package the Nucleo carries, there is no separate reference pin: DS10314 Rev 8, Table 8 names pin 13 **`VDDA/VREF+`** and pin 12 **`VSSA/VREF-`**, and Table 65's note 3 confirms "V<sub>REF+</sub> is internally connected to V<sub>DDA</sub> and V<sub>REF-</sub> is internally connected to V<sub>SSA</sub>". On the board, `SB57` then connects V<sub>DDA</sub>/V<sub>REF+</sub> to V<sub>DD</sub> (UM1724 Rev 17, Table 10).

So the reference is the ordinary 3.3 V rail, produced by the on-board LDO, shared with every digital thing on the chip. Three consequences follow directly:

- **Absolute accuracy is limited by the regulator's tolerance, not the ADC's.** The `LD39050` is specified at ±2.0% output tolerance at 25 °C (DocID15470 Rev 5). Two percent of 3.3 V is 66 mV — about 82 LSB at 12 bits. Any measurement you express in volts inherits that error — unless you measure the reference itself, which the chip gives you a way to do (next section).
- **Rail noise is measurement noise, one for one.** AN2834 Rev 10 §3.2.1: "As the ADC output is the ratio between the analog signal voltage and the reference voltage, any noise on the analog reference causes a change in the converted digital value." It then works an example that is worth memorising: with V<sub>REF+</sub> = V<sub>DDA</sub> = 3.3 V and a 1 V input, the ideal code is `0x4D9`; add `40 mV` of peak-to-peak ripple to the reference and, at the ripple's peak, the code becomes `0x4CA` — an error of **15 LSB from 40 millivolts of rail noise**.
- **Ratiometric measurements dodge all of this.** If your sensor is a resistive divider powered from the *same* 3.3 V rail, its output moves with the reference and the ratio stays correct. That is not a trick; it is why sensor breakouts are so often built that way.

The datasheet's decoupling requirement follows from the same logic (§6.3.20, "General PCB design guidelines"): "Power supply decoupling should be performed as shown in Figure 42 or Figure 43… The 10 nF capacitors should be ceramic (good quality). They should be placed them as close as possible to the chip."

### Measuring the reference: `V_REFINT` and its factory calibration

The chip carries a bandgap reference whose voltage does *not* move with the rail, wired to an internal ADC channel so you can convert it like any other input. RM0383 Rev 4 §11.3.3, under the heading "Temperature sensor, V<sub>REFINT</sub> and V<sub>BAT</sub> internal channels": "The internal reference voltage V<sub>REFINT</sub> is connected to `ADC1_IN17`." It is enabled by the same `TSVREFE` bit in `ADC_CCR` that wakes the temperature sensor — §11.9 spells that out: "The TSVREFE bit must be set to enable the conversion of both internal channels: the `ADC1_IN16` or `ADC1_IN18` (temperature sensor) and the `ADC1_IN17` (V<sub>REFINT</sub>)." All three are available only on `ADC1`. DS10314 Rev 8, Table 74 specifies it as `1.18 / 1.21 / 1.24 V` (min/typ/max) over −40 °C to +125 °C, with a temperature coefficient of `30 ppm/°C` typical and `50 ppm/°C` maximum.

The part that makes it genuinely useful is that ST measured *your specific die* and left the answer in system memory. DS10314 Rev 8, Table 75 "Internal reference voltage calibration values" gives `VREFIN_CAL` as the "raw data acquired at temperature of 30 °C, V<sub>DDA</sub> = 3.3 V", stored at addresses `0x1FFF 7A2A`–`0x1FFF 7A2B`. Since both the calibration reading and your reading are ratios against V<sub>DDA</sub>, dividing one by the other cancels the converter and leaves the rail:

```c
/* Both readings are codes for the same bandgap voltage, so their ratio is the ratio
   of the two rails. VREFIN_CAL was captured at VDDA = 3.3 V (DS10314 Table 75). */
const uint16_t *VREFIN_CAL = (const uint16_t *)0x1FFF7A2AU;

/* adc_read_channel(17) must use SMP = 0b111 (480 cycles) -- see below. */
uint32_t vdda_mv = (3300U * (uint32_t)(*VREFIN_CAL)) / adc_read_channel(17);
```

Once `vdda_mv` is known, any other channel's code scales against it instead of against a nominal 3.3 V. That turns the LDO's ±2.0% into a measurement rather than an error, with no external components — the counterpart to the ratiometric trick above, for the cases where your sensor is *not* powered from the same rail.

Two conditions to respect, both of them the sampling-time lesson resurfacing:

- **V<sub>REFINT</sub> needs a long sampling window.** DS10314 Rev 8, Table 74 specifies `T_S_vrefint`, the "ADC sampling time when reading the internal reference voltage", as `10 µs` minimum. At `f_ADC = 25 MHz` that is 250 ADC cycles, so the only `SMP[2:0]` setting that satisfies it is `111` — 480 cycles, `19.2 µs`. Every shorter setting reads the bandgap low, and then your computed V<sub>DDA</sub> is wrong in a way that quietly biases every other channel.
- **The internal channels share.** RM0383 Rev 4 §11.10 is explicit: "The V<sub>BAT</sub> and temperature sensor are connected to the same ADC internal channel (`ADC1_IN18`). Only one conversion, either temperature sensor or V<sub>BAT</sub>, must be selected at a time. When both conversion are enabled simultaneously, only the V<sub>BAT</sub> conversion is performed." (§11.3.3 adds that both are also mapped to `ADC1_IN16`.) `V_REFINT` on `ADC1_IN17` is separate and unaffected, but a scan sequence that enables both `VBATE` and the temperature sensor silently returns V<sub>BAT</sub> twice — with no error flag, in the house style of this whole page.

## Resolution is not accuracy, and neither is ENOB

`RES[1:0]` in `ADC_CR1` selects the resolution, and the trade is against conversion length (RM0383 Rev 4, §11.12.2). Note carefully what the cycle counts in the third column are: they are **totals**, with the minimum 3-cycle sampling window already included — 12-bit is `3 + 12 = 15`, exactly the worked example §11.5 gives. Do not add your sampling time to them, or you will count those three cycles twice. For any other `SMP` setting, the total is `t_S + 12` at 12-bit, as the table in the previous section computes.

| `RES[1:0]` | Resolution | Total conversion at minimum (3-cycle) sampling | 1 LSB at V<sub>REF+</sub> = 3.3 V |
|---|---|---|---|
| `00` | 12-bit | 15 | 806 µV |
| `01` | 10-bit | 13 | 3.22 mV |
| `10` | 8-bit | 11 | 12.9 mV |
| `11` | 6-bit | 9 | 51.6 mV |

Those LSB figures are what the *code* is worth. What the *measurement* is worth is a different set of tables, and this is where the "a 12-bit ADC rarely gives 12 useful bits" claim gets its teeth. All figures below are from DS10314 Rev 8:

| Metric | Conditions | Value | Table |
|---|---|---|---|
| Total unadjusted error, E<sub>T</sub> | f<sub>ADC</sub> = 18 MHz, V<sub>DDA</sub> = 1.7–3.6 V | ±3 LSB typ., ±4 LSB max | Table 66 |
| Total unadjusted error, E<sub>T</sub> | f<sub>ADC</sub> = 30 MHz, R<sub>AIN</sub> < 10 kΩ, V<sub>DDA</sub> = 2.4–3.6 V | ±2 LSB typ., ±5 LSB max | Table 67 |
| Total unadjusted error, E<sub>T</sub> | f<sub>ADC</sub> = 36 MHz, V<sub>DDA</sub> = 2.4–3.6 V | ±4 LSB typ., ±7 LSB max | Table 68 |
| Effective number of bits, ENOB | f<sub>ADC</sub> = 18 MHz, V<sub>DDA</sub> = V<sub>REF+</sub> = 1.7 V, 20 kHz input, 25 °C | 10.3 min, 10.4 typ | Table 69 |
| Effective number of bits, ENOB | f<sub>ADC</sub> = 36 MHz, V<sub>DDA</sub> = V<sub>REF+</sub> = 3.3 V, 20 kHz input, 25 °C | 10.6 min, 10.8 typ | Table 70 |

These two families of numbers measure different things and should not be blended. **Total unadjusted error** is a DC figure: the worst deviation between the real transfer curve and the ideal one, including offset, gain and linearity (DS10314 Rev 8, Figure 40 defines each term). At `±5 LSB` the code you read sits somewhere in a ten-count window, so roughly `log₂ 10 ≈ 3.3` bits of the twelve are consumed by uncertainty. **ENOB** is an AC figure derived from signal-to-noise-and-distortion on a sine wave, measured under the narrow "limited test conditions" the tables name; 10.4 to 10.8 bits is what the converter resolves dynamically under those conditions.

Either way the honest summary is the same: **you have a 12-bit code and roughly ten bits of meaning**, before your circuit, your reference and your layout take their cut. Notice also that Table 67 (30 MHz) is *better* than Table 68 (36 MHz) — running the ADC slower buys accuracy. And Table 67's conditions include `R_AIN < 10 kΩ`, which quietly makes the same point the sampling-time section made at length.

:::note[The errata adds one more, and it is not your fault]
ES0287 Rev 6 §2.2.8, "Internal noise impacting the ADC accuracy": "An internal noise generated on V<sub>DD</sub> supplies and propagated internally may impact the ADC accuracy. This noise is always present whatever the power mode of the MCU (Run or Sleep)." The workaround ST gives is two-part: configure the flash ART with "prefetch OFF and data + instruction cache ON", and "use averaging and filtering algorithms on ADC output codes".

That first item is genuinely surprising — a *flash accelerator* setting that changes your *analog* accuracy — and it is the kind of thing you only ever find by reading the errata. It is also a reminder that on a microcontroller the ADC shares a die with a hundred megahertz of digital logic.
:::

## Getting the bits back: averaging, and what it can and cannot fix

Averaging N samples of a signal buried in uncorrelated noise improves the signal-to-noise ratio by `√N` — sixteen samples buy you two bits. AN4073 Rev 5 §2.1 describes the technique and adds the practical detail worth copying: take N as a power of two so the division is a right shift rather than a divide. It also describes a refinement — take N samples, sort them, discard the X most extreme, average the rest — which handles the occasional single wild reading that a plain mean would smear across everything.

What averaging cannot fix:

- **A systematically low reading from insufficient sampling time.** The error is not noise; it is bias. Averaging a biased measurement gives you a very precise wrong answer.
- **Aliasing.** Sampling at `f_s` folds every frequency component above `f_s/2` back down into your band, indistinguishably from real signal. A 60 Hz hum sampled at 100 Hz appears as a 40 Hz signal that no digital filter can remove, because by the time you have the samples the information is gone. The fix is an analog low-pass filter *before* the ADC — and note that the resistor in that filter adds to `R_AIN`, which sends you back to the sampling-time table.
- **Reference error.** A 2% high reference makes every reading 2% low, forever, however many you take.

AN4073 Rev 5 §2.2 adds the firmware-side hygiene, and it is worth taking literally: do not start a communication peripheral just before a conversion, do not toggle high-current outputs during one, and do not toggle digital outputs on the same port as the analog input you are converting.

## Injection current: the one hardware precaution the datasheet asks for

There is a failure mode here that is not about accuracy on the pin you are converting — it is about accuracy on *every other* pin. If a voltage outside the supply rails appears on any analog input, the pin's protection diode conducts and current is injected into the die, and that current perturbs the converter itself. DS10314 Rev 8 states it as a note in §6.3.20, immediately after Equation 1:

> **Note:** ADC accuracy vs. negative injection current: injecting a negative current on any analog input pins should be avoided as this significantly reduces the accuracy of the conversion being performed **on another analog input**. It is recommended to add a Schottky diode (pin to ground) to analog pins which may potentially inject negative currents.

The datasheet repeats the same recommendation at the end of §6.3.15, under Table 52 "I/O current injection susceptibility", and adds the reassuring half in §6.3.20: "Any positive injection current within the limits specified for I<sub>INJ(PIN)</sub> and ΣI<sub>INJ(PIN)</sub>… does not affect the ADC accuracy." So the asymmetry is real — it is *negative* injection, an input dragged below V<sub>SS</sub>, that corrupts unrelated channels.

Look at what the current budget actually is. Table 52 gives the negative-injection functional-susceptibility limit as `−5 mA` for a general `FT` pin, and **`−0 mA`** — that is, none at all — for a long list of pins including `PC0`, `PC1`, `PC2`, `PC3`, `PB3`–`PB9`, `PC13`–`PC15`, `PH1`, `NRST`, `BOOT0` and `PDR_ON`. On the Nucleo, `PC0` and `PC1` are exactly the pins the board routes to the Arduino `A4`/`A5` positions when `SB56`/`SB51` are fitted (UM1724 Rev 17, Table 10) — analog inputs, on the header, with a zero-milliamp negative-injection budget.

The circumstances that produce negative injection are ordinary rather than exotic: an inductive sensor whose output rings below ground, a long cable with a ground offset, a signal that is live before the board is powered, or ringing on a fast adjacent edge — which is where [Signal Integrity and Noise](./signal-integrity-and-noise.md) and this page meet. A Schottky diode from the pin to ground, conducting at a few hundred millivolts, clamps the excursion before the internal protection diode has to. It is one component, and it is the only external precaution the datasheet actually asks you to take on an analog input.

## The DAC: this part does not have one

The STM32F411 has **no digital-to-analog converter**. This is easy to get wrong because it is a widely available fact about the *STM32F4 family* that some members have two 12-bit DAC channels. This member does not: RM0383 Rev 4 goes from chapter 11 (ADC) straight to chapter 12 (advanced-control timer TIM1), and DS10314 Rev 8's feature list and block diagram (Figure 3) show `ADC1` and no DAC. The only appearances of the word "DAC" in either document refer to an *external* DAC or codec being fed over I²S.

The concept is still worth holding, because you will meet it on other parts and because the alternative on this one is shaped by it. A DAC does the inverse of the ADC: it takes a code and drives its output to `code / 2ⁿ × V_REF`, continuously, with a real output amplifier behind it. Its specifications mirror the ADC's — resolution, settling time, output impedance, and the same dependence on a clean reference.

What this board offers instead is **PWM plus a low-pass filter**. A timer drives a pin with a square wave whose duty cycle you control; an RC filter turns the average into a DC level. The honest comparison:

| | True DAC | PWM plus RC filter |
|---|---|---|
| Output | Continuous voltage, settles in microseconds | Average of a square wave; settles over several filter time constants |
| Resolution | Set by the converter (12 bits typical) | Set by timer counts per period — and traded directly against carrier frequency |
| Ripple | Essentially none | Always present at the carrier frequency; more filtering means slower response |
| Output drive | Buffered amplifier, can drive a load | A GPIO through a resistor; needs an op-amp buffer for anything real |
| Cost | A peripheral you either have or do not | A timer channel and two passive components |

The resolution-versus-frequency trade is pure arithmetic and it bites quickly. With the APB2 prescaler at 1, `TIMxCLK` equals `HCLK` (RM0383 Rev 4, §6.2), so at 100 MHz a timer counting 4096 steps per period produces a carrier at `100 MHz / 4096 ≈ 24.4 kHz`. Filtering 24.4 kHz down to a ripple you would accept as "DC" needs a corner well below it, and every decade of filtering costs you response time. Want 16-bit resolution instead? The carrier drops to about 1.5 kHz and the filter has to be slower still. That trade — resolution against carrier against settling time — is the entire design problem, and it is why a real DAC is worth having when you need one.

## See also

- [Power Supplies and Regulators](./power-supply-and-regulators.md) — why V<sub>DDA</sub> is the reference, and what the on-board LDO's tolerance costs you.
- [How a GPIO Pin Really Behaves](./gpio-electrical-behaviour.md) — analog mode, input leakage, and why the digital buffer must be off on an analog pin.
- [Signal Integrity and Noise](./signal-integrity-and-noise.md) — where the noise the averaging section is fighting comes from.
- [Reading a Datasheet](./reading-a-datasheet.md) — how to find Table 65 and Equation 1 in a 151-page datasheet, and why the errata matters.
- [Lab Equipment and What It Answers](./lab-equipment.md) — the instruments that distinguish "my sensor is wrong" from "my sampling time is wrong".

## References

- STMicroelectronics — [**STM32F411xC/E datasheet**](https://www.st.com/resource/en/datasheet/stm32f411re.pdf) (DS10314), consulted at **Rev 8** (January 2024). §6.3.20 "12-bit ADC characteristics" is the source for everything numeric here: Table 65 (f<sub>ADC</sub> limits, `R_ADC`, `C_ADC`, `R_AIN` cap, sampling and conversion times), **Equation 1** and its accompanying note defining `k` and `N`, Tables 66–68 (total unadjusted error at three ADC clocks), Tables 69–70 (ENOB), Figure 40 (what each error term means), Figures 42–43 (reference decoupling). Table 74 (embedded internal reference voltage, §6.3.23) and Table 75 (`VREFIN_CAL` and its memory address) for the reference-measurement section; the negative-injection note at the end of §6.3.15 and the one following Equation 1 in §6.3.20, with Table 52 for the per-pin injection limits. Table 8 for the `VDDA/VREF+` pin sharing on LQFP64; Table 14 for `f_PCLK2`.
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). Chapter 11 "Analog-to-digital converter (ADC)": §11.3.3 for the internal-channel assignments (`ADC1_IN17` = V<sub>REFINT</sub>), §11.5 for `Tconv = Sampling time + 12 cycles`, §11.9 for `TSVREFE`, §11.10 for the V<sub>BAT</sub>/temperature-sensor channel clash, §11.12.4–§11.12.5 for the `SMP[2:0]` encodings, §11.12.2 for `RES[1:0]` in `ADC_CR1`, §11.12.15 for `ADCPRE` in `ADC_CCR`. Also §6.2 for the timer-clock rule used in the PWM arithmetic. The absence of a DAC chapter between 11 and 12 is itself the citation for this part having none.
- STMicroelectronics — [**AN2834**, *How to optimize the ADC accuracy in the STM32 MCUs*](https://www.st.com/resource/en/application_note/cd00211314-how-to-get-the-best-adc-accuracy-in-stm32-microcontrollers-stmicroelectronics.pdf), consulted at **Rev 10** (October 2024). The family-wide treatment: §3.2.7 source resistance, §3.2.8 source and PCB capacitance, §4.2.6 sampling-time prerequisites, §4.2.13 layout, §4.4 measuring genuinely high-impedance sources. Note that its Table 1 minimum-sampling-time figures are given for the STM32H7 series and must not be applied to this part — use DS10314's Equation 1 instead.
- STMicroelectronics — [**AN4073**, *How to improve ADC accuracy when using STM32F2xx and STM32F4xx microcontrollers*](https://www.st.com/resource/en/application_note/an4073-how-to-improve-adc-accuracy-when-using-stm32f2xx-and-stm32f4xx-microcontrollers-stmicroelectronics.pdf), consulted at **Rev 5** (July 2013). §2.1 for the two averaging algorithms and their CPU cost, §2.2 for the firmware noise-hygiene list. Its own Table 1 lists STM32F405/407/415/417/42x/43x rather than the F411, but ES0287 §2.2.8 directs F411 readers here for detailed workarounds; treat the averaging material as applicable and the device-specific `ADCDC1`/`ADCxDC2` bits as not.
- STMicroelectronics — [**UM1724**, *STM32 Nucleo-64 boards (MB1136)*](https://www.st.com/resource/en/user_manual/um1724-stm32-nucleo64-boards-mb1136-stmicroelectronics.pdf), consulted at **Rev 17** (September 2025). Table 10 "Solder bridges": the `SB57` row for V<sub>DDA</sub>/V<sub>REF+</sub> being tied to V<sub>DD</sub>, and the `SB56`/`SB51` row for `PC1` and `PC0` reaching the Arduino `A4`/`A5` positions.
- STMicroelectronics — [**ES0287**, *STM32F411xC/xE device errata*](https://www.st.com/resource/en/errata_sheet/es0287-stm32f411xcxe-device-errata-stmicroelectronics.pdf), consulted at **Rev 6**. §2.2.8 "Internal noise impacting the ADC accuracy" and §2.4.1 "ADC sequencer modification during conversion". Read both before trusting a measurement.
