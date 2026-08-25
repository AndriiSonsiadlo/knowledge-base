---
id: adc-and-dac-drivers
title: ADC and DAC Drivers
sidebar_label: ADC and DAC Drivers
sidebar_position: 8
tags: [embedded, peripherals, adc, dac, sampling, calibration, oversampling, stm32]
---

# ADC and DAC Drivers

A successive-approximation ADC is, physically, a capacitor with a switch in front of it. Converting a voltage happens in two completely different phases: first the switch closes and the capacitor is allowed to charge towards your signal through the source impedance, and then the switch opens and a comparator plays twelve rounds of twenty questions against the trapped charge. The second phase is fixed by the hardware and takes exactly twelve clocks. The first phase is the one you configure, the one every tutorial leaves at its reset value, and the one that decides whether your reading means anything at all.

The mental model worth carrying: **the ADC does not measure your signal. It measures whatever voltage its internal capacitor reached during the sampling window.** If the window was long enough relative to the source impedance, those are the same number. If it was not, the reading is low, it is low in a way that varies with the previous channel converted, and nothing anywhere sets an error flag. That single fact explains most of the bad analogue readings in the field.

The DAC is a shorter story on this part, and the honest version is at the bottom: **the STM32F411 does not have one.**

:::info[Prerequisites]
[Analog Basics: ADC and DAC](../01-hardware-foundations/analog-basics-adc-and-dac.md) owns quantisation, reference voltages and the SAR principle itself; this page is the STM32F4 peripheral and its driver. [DMA](./dma.md) is not optional reading here — a multi-channel sequence overruns the single data register in microseconds, so the DMA configuration *is* the ADC driver.
:::

## What the F411's ADC actually is

One 12-bit SAR converter, `ADC1`, on APB2. Sixteen external channels plus three internal ones: `VREFINT` on `ADC1_IN17`, and the temperature sensor sharing `ADC1_IN18` with `VBAT` (RM0383 §11.3.3). Larger F4 parts have two or three ADCs and an interleaved dual/triple mode; this one has a single converter, so every "simultaneous sampling" technique in the family documentation is unavailable and multi-channel means *sequential*.

The clock comes from `PCLK2` through a `/2, /4, /6, /8` prescaler in `ADC_CCR.ADCPRE` (RM0383 §11.3.2). The limit is in the datasheet, not the reference manual:

| Parameter | Value | Conditions | Source |
|---|---|---|---|
| `fADC` | 0.6 to **36 MHz** | VDDA = 2.4 to 3.6 V (typ 30 MHz) | DS Table 65 |
| `fADC` | 0.6 to 18 MHz | VDDA = 1.7 to 2.4 V (typ 15 MHz) | DS Table 65 |
| Sampling rate | 2 Msps | 12-bit, fADC = 30 MHz, 3-cycle sampling | DS Table 65 |
| `RADC` (sampling switch) | ≤ 6 kΩ | max at VDD = 1.7 V | DS Table 65 |
| `CADC` (sample-and-hold cap) | 4 pF typ, 7 pF max | — | DS Table 65 |
| `RAIN` (external input impedance) | ≤ 50 kΩ | absolute ceiling; see Equation 1 | DS Table 65 |

With `PCLK2` at 100 MHz the only prescaler values that stay legal are `/4` (25 MHz) and `/6` (16.7 MHz); `/2` gives 50 MHz and is out of specification. Running the ADC out of specification does not fault — it degrades linearity quietly, which is the theme of this page.

## Sampling, then converting

```wavedrom title="One conversion: a sampling window you choose, then twelve SAR cycles you do not" alt="Waveform of a single ADC conversion showing the ADC clock, a start trigger, the sample-and-hold switch closing for three clocks while the internal capacitor charges, the switch opening, twelve successive-approximation cycles, and the end-of-conversion flag"
{ "signal": [
  { "name": "ADCCLK",     "wave": "P................." },
  { "name": "SWSTART",    "wave": "01.0.............." },
  { "name": "S&H switch", "wave": "0.1..0............" },
  { "name": "C_ADC",      "wave": "x.3..4............", "data": ["charging","held"] },
  { "name": "SAR",        "wave": "x....5...........x", "data": ["12 approximation cycles"] },
  { "name": "EOC",        "wave": "0................1" }
],
  "config": { "hscale": 2 }
}
```

RM0383 §11.5 gives the arithmetic in one line:

```text
T_conv = sampling time + 12 cycles          (12-bit resolution)
```

Sampling time is per channel, chosen from eight values in `ADC_SMPR1`/`ADC_SMPR2`: **3, 15, 28, 56, 84, 112, 144 or 480 `ADCCLK` cycles** (RM0383 §11.12.4). At 30 MHz the extremes are 15 cycles = 500 ns and 492 cycles = 16.4 µs — a factor of 33 in throughput, decided by one three-bit field per channel.

### Resolution, conversion time, and effective bits

Lowering `RES` in `ADC_CR1` shortens the approximation phase by the bits you gave up, and nothing else:

| `RES[1:0]` | Resolution | SAR cycles | Min `T_conv` @ 30 MHz | Max rate | Notes |
|---|---|---|---|---|---|
| `00` | 12-bit | 12 | 15 cycles = **0.50 µs** | 2.00 Msps | The default. DS Table 65 quotes 0.50 µs. |
| `01` | 10-bit | 10 | 13 cycles = 0.433 µs | 2.31 Msps | DS quotes 0.43 µs. |
| `10` | 8-bit | 8 | 11 cycles = 0.367 µs | 2.73 Msps | DS quotes 0.37 µs. |
| `11` | 6-bit | 6 | 9 cycles = 0.300 µs | 3.33 Msps | DS quotes 0.30 µs. |

*Minimum `T_conv` assumes the shortest 3-cycle sampling window, which as the next section shows is almost never legitimate.*

And the number that matters more than any of them — what the converter is actually worth, measured rather than nominal:

| Parameter | Value | Conditions | Source |
|---|---|---|---|
| **ENOB** | 10.3 min / **10.4 typ** bits | fADC = 18 MHz, VDDA = VREF+ = 1.7 V, 20 kHz input, 25 °C | DS Table 69 |
| **ENOB** | 10.6 min / **10.8 typ** bits | fADC = 36 MHz, VDDA = VREF+ = 3.3 V, 20 kHz input, 25 °C | DS Table 70 |
| SINAD | 67 dB typ | as above, 36 MHz | DS Table 70 |
| Total unadjusted error | ±2 LSB typ, ±5 LSB max | fADC = 30 MHz, RAIN &lt; 10 kΩ, VDDA 2.4–3.6 V | DS Table 67 |
| Total unadjusted error | ±4 LSB typ, ±7 LSB max | fADC = 36 MHz, VDDA 2.4–3.6 V | DS Table 68 |

**A 12-bit ADC that delivers 10.8 effective bits is not a defective 12-bit ADC; it is what a 12-bit SAR on a noisy digital die is.** The bottom bit or two of every reading is noise, and code that compares raw counts for equality, or reports four significant figures of a voltage, is reporting noise as signal. Note also that the higher clock and higher supply give the *better* ENOB — the 1.7 V row is worse because the reference is smaller, not because 18 MHz is slower.

## Sampling time versus source impedance

This is the part the tutorials omit and the part that decides whether the numbers above are achievable.

During sampling, `C_ADC` charges through `R_AIN + R_ADC` with a time constant `(R_AIN + R_ADC) × C_ADC`. To settle to within a fraction of an LSB you need several time constants, and "several" is set by the resolution. The STM32F411 datasheet states it as **Equation 1**, immediately below Table 65, for an error below ¼ LSB:

```text
             (k - 0.5)
R_AIN_max = -------------------------------  -  R_ADC
             f_ADC x C_ADC x ln(2^(N+2))

k     = sampling time, in ADCCLK cycles (the SMP setting)
N     = 12
C_ADC = 4 pF typ, 7 pF max      R_ADC <= 6 kOhm      (DS Table 65)
```

*(ST application note **AN2834** §3.2.6 derives the same relation for a ½-LSB budget, where the log term is `ln(2^(N+1))`. The datasheet's `N+2` form is the more conservative of the two and is the one specified for this part.)*

Turned round — which is how you actually use it — the required sampling time for a given source is:

```text
k  >=  0.5 + (R_AIN + R_ADC) x C_ADC x f_ADC x ln(2^14)
```

With `f_ADC` = 30 MHz, `C_ADC` = 4 pF typ, `R_ADC` = 6 kΩ and `ln(2^14)` = 9.704, the coefficient is 1.164 × 10⁻³ cycles per ohm, and the table comes out like this:

| Source `R_AIN` | Cycles required | Nearest legal `SMP` | `T_conv` @ 30 MHz | Typical source |
|---|---|---|---|---|
| 0 Ω (ideal) | 7.5 | **15** | 0.90 µs | nothing real |
| 1 kΩ | 8.7 | **15** | 0.90 µs | op-amp buffer output |
| 10 kΩ | 19.1 | **28** | 1.33 µs | resistive divider from a rail |
| 47 kΩ | 62.2 | **84** | 3.20 µs | 100 kΩ potentiometer at mid-travel |
| 100 kΩ | 123.9 | **144** | 5.20 µs | high-value divider, thermistor bridge |
| 200 kΩ | 240.4 | **480** | 16.4 µs | past the 50 kΩ datasheet ceiling — buffer it |

Two conclusions fall straight out. **The 3-cycle default is never correct at 12 bits** — even a zero-impedance source needs 7.5 cycles at 30 MHz, so the shortest usable setting is 15. And **a bare potentiometer wiper needs the 84-cycle setting**, which most example code does not use, which is why "my pot reading is a bit low and drifts when I read the other channel too" is the most common analogue bug on this family.

The table uses `C_ADC` = 4 pF typ. Designing against the 7 pF maximum multiplies every requirement by 1.75 — the 10 kΩ row moves from 28 cycles to 56. For anything that has to work across the production spread, use the maximum.

## A driver: timer-triggered, DMA-fed, continuous

Free-running continuous mode gives you samples at an interval that depends on the sampling times of everything in the sequence, which is fine for a battery monitor and useless for anything you intend to filter or FFT. **A timer trigger gives you a sample interval you chose**, with jitter set by the timer rather than by software.

```c title="adc_seq.c — TIM2 TRGO triggers a 2-channel scan; DMA2 Stream 0 moves the results"
#include "stm32f4xx.h"

/* Two channels, ping-pong halves: DMA rewrites [0..1] then [2..3]. */
static volatile uint16_t samples[4];

void adc_init(void)
{
    RCC->APB2ENR |= RCC_APB2ENR_ADC1EN;
    (void)RCC->APB2ENR;                             /* read-back guard */

    ADC->CCR = (1u << ADC_CCR_ADCPRE_Pos);          /* PCLK2/4 = 25 MHz @ 100 MHz */

    /* Sampling time is per channel and is the whole point. Channel 0 sits on a
     * 10 kOhm divider (28 cycles); channel 1 on a 100 kOhm pot (144 cycles). */
    ADC1->SMPR2 = (2u << ADC_SMPR2_SMP0_Pos)        /* 010 = 28 cycles  */
                | (6u << ADC_SMPR2_SMP1_Pos);       /* 110 = 144 cycles */

    ADC1->SQR1 = (1u << ADC_SQR1_L_Pos);            /* L = 1 means 2 conversions */
    ADC1->SQR3 = (0u << 0) | (1u << 5);             /* order: IN0, then IN1     */

    ADC1->CR1 = ADC_CR1_SCAN;                       /* walk the sequence        */
    ADC1->CR2 = ADC_CR2_DMA | ADC_CR2_DDS           /* DMA, and keep requesting */
              | (6u << ADC_CR2_EXTSEL_Pos)          /* 0110 = TIM2 TRGO         */
              | (1u << ADC_CR2_EXTEN_Pos);          /* trigger on rising edge   */

    ADC1->CR2 |= ADC_CR2_ADON;                      /* enable last              */
}
```

Three fields in there are the ones that get missed:

- **`DDS` (DMA disable selection)** must be set alongside `DMA`, or the ADC stops issuing DMA requests after the first pass through the sequence and you get one buffer of data followed by silence.
- **`L[3:0]` in `SQR1` is the count minus one.** `L = 1` means two conversions. Setting it to the number of channels gives you one extra, sampled from whatever `SQ3` happens to contain.
- **`EXTEN` must be non-zero.** With `EXTSEL` pointing at TIM2 TRGO but `EXTEN` left at `00`, external triggering is disabled and the ADC waits for `SWSTART` forever. The register dump looks correct.

The DMA side is a circular stream with the half-transfer interrupt, exactly as in [DMA](./dma.md). It is mandatory rather than a convenience here: `ADC_DR` is a single register shared by every channel in the sequence, and at 25 MHz a second conversion lands roughly 1.6 µs after the first. Miss it and `OVR` sets, the sequence stops, and the readings you do get are attributed to the wrong channels — which presents as two sensors that seem to have been swapped.

## Calibration, the internal reference, and the temperature sensor

**The STM32F4 ADC has no self-calibration command.** The `CAL` bit that F1 and L4 users know does not exist here; the converter is trimmed in production and what you get instead is a pair of factory measurements in the system-memory region that let you correct for the two things that actually move: your supply voltage, and die temperature.

`VREFINT` is a bandgap of 1.21 V typ (1.18–1.24 V over −40 to +105 °C, DS Table 74). It is not useful as an absolute reference, but its *ratio* to a factory measurement recovers your true VDDA, because VDDA is the ADC's reference:

```c
/* Factory values, DS Tables 72 and 75. All acquired at VDDA = 3.3 V. */
#define VREFINT_CAL  (*(volatile const uint16_t *)0x1FFF7A2AU) /* at 30 degC  */
#define TS_CAL1      (*(volatile const uint16_t *)0x1FFF7A2CU) /* at 30 degC  */
#define TS_CAL2      (*(volatile const uint16_t *)0x1FFF7A2EU) /* at 110 degC */

/* Recover the real supply from the ratio. */
static uint32_t vdda_mv(uint16_t vrefint_raw)
{
    return (3300u * VREFINT_CAL) / vrefint_raw;
}

/* Two-point interpolation between the factory points, in tenths of a degree. */
static int32_t temperature_dC(uint16_t ts_raw)
{
    int32_t span = (int32_t)TS_CAL2 - (int32_t)TS_CAL1;   /* counts per 80 degC */
    return ((int32_t)(110 - 30) * 10 * ((int32_t)ts_raw - (int32_t)TS_CAL1))
           / span + 300;
}
```

Both internal channels need `ADC_CCR.TSVREFE` set before they read anything but noise (RM0383 §11.12.15) — and they need a sampling time nobody guesses:

- **`TS_temp` ≥ 10 µs** for 1 °C accuracy, and **`TS_vrefint` ≥ 10 µs** (DS Tables 71 and 74). At `fADC` = 30 MHz that is 300 cycles, so **the only legal `SMP` setting is 480** (16 µs). The 144-cycle setting gives 4.8 µs and is not enough. This is the single most common cause of an STM32 temperature reading that is confidently wrong by tens of degrees.
- The factory constants were captured at **VDDA = 3.3 V**. If your board runs at anything else, scale the raw reading to 3.3 V using `vdda_mv()` above *before* interpolating, or the temperature carries your supply error multiplied by the sensor's 2.5 mV/°C slope (DS Table 71).

## Oversampling for extra bits

The F411 ADC has **no hardware oversampler** — that arrived with the L4, G4 and H7. Averaging in software gets you the same result and the same caveat.

Averaging `4^n` samples of a stationary signal gains `n` bits of resolution: 4 samples for one bit, 16 for two, 256 for four. The condition everyone forgets is that **it only works if there is at least one LSB of noise present** (AN2834 §3.3.1). Averaging 256 identical readings of a perfectly clean signal returns that reading 256 times and gains nothing; the noise is what dithers the input across the quantisation boundary so the average lands between codes. On this part the noise is usually there for free — the ENOB figures above say the bottom 1.2 bits are already dither.

The cost is throughput and bandwidth. Sixteen samples at the 144-cycle setting is 16 × 5.2 µs = 83 µs per reading, so a "16-bit" sensor value updates at 12 kHz at best, and the averaging is a boxcar filter whose response you have now built into your control loop whether you meant to or not.

## The DAC this part does not have

**The STM32F411 has no digital-to-analogue converter.** There is no DAC chapter in RM0383, and no `DAC` peripheral in the CMSIS device header — the peripheral is absent from the die, not merely unbonded on this package. Within the family:

| Part | DAC |
|---|---|
| STM32F401, **STM32F411** | none |
| STM32F410 | 1 × 12-bit |
| STM32F405/407/415/417, F427/429/437/439, F446, F469 | 2 × 12-bit |

Where the F4 does have one it is a straightforward affair — a 12-bit voltage-output converter with an optional output buffer, a triangle/noise generator, and a DMA-fed data register that a timer TRGO clocks, which is how arbitrary waveforms are generated. Its buffer limits the output swing to roughly 0.2 V from either rail, so a "0 to 3.3 V" DAC is really 0.2 to 3.1 V unless the buffer is disabled and the load is very light.

On this board the substitute is **PWM plus an RC filter**, and [PWM](./pwm.md) works through that trade in full — the ripple-versus-resolution arithmetic, the settling time, and the two configurations that bracket the useful range. There is no point repeating it here; the summary is that a PWM DAC is excellent for a slowly-moving setpoint and poor for anything that must settle quickly and exactly.

:::warning[The channel that reads its neighbour, and the temperature nobody sampled long enough]
Two analogue failures that produce plausible numbers, which is what makes them expensive.

**Charge sharing between channels in a scan.** Convert channel 0 (a 100 Ω source) then channel 1 (a 100 kΩ potentiometer) with both left at the 3-cycle default. `C_ADC` still holds channel 0's charge when the mux flips, and 3 cycles is nowhere near enough to pull it to channel 1's voltage through 100 kΩ, so **channel 1 reads pulled towards channel 0**. The symptom is unmistakable once you know it: turn the pot and the reading follows, but the whole curve shifts when you change the *other* channel's input, and swapping the order in `SQR3` changes the error. It looks like crosstalk on the PCB and it is not — it is `SMP`. Diagnose by converting the same channel twice in a row: if the second reading differs from the first, the window is too short. The fix is the impedance table above, and, above roughly 50 kΩ, an op-amp buffer, because no `SMP` setting rescues a source the datasheet has already ruled out (DS Table 65: `RAIN` ≤ 50 kΩ).

**A die temperature that is wrong by tens of degrees.** Enable `TSVREFE`, leave `SMP18` at 3 cycles, apply the two-point formula, and you get a number — a stable, repeatable, entirely believable number that is 30 to 50 °C off. The sensor is a high-impedance node and the datasheet requires **≥ 10 µs of sampling for 1 °C accuracy** (DS Table 71), which at 30 MHz means the 480-cycle setting and nothing less. Because the error is monotonic and repeatable it survives review, survives unit test, and is discovered when a thermal cut-out trips in the wrong place. Sanity-check any new temperature path against a thermocouple at two temperatures, not one — a single point cannot distinguish an offset from a slope error, and this bug produces both.
:::

## See also

- [DMA](./dma.md) — the circular-buffer and half-transfer mechanism the ADC driver above depends on, and why a sequence without DMA sets `OVR`.
- [PWM](./pwm.md) — the RC-filtered PWM output that stands in for the DAC this part lacks, with the ripple and settling arithmetic worked through.
- [Timers and Counters](./timers-and-counters.md) — where TIM2's TRGO comes from and how to set a sample interval exactly rather than approximately.
- [Analog Basics: ADC and DAC](../01-hardware-foundations/analog-basics-adc-and-dac.md) — quantisation, references and the SAR principle this page assumes.
- [The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md) — the bring-up sequence, and why `ADON` belongs on its own line at the end.

## References

- STMicroelectronics — [**RM0383**, *STM32F411xC/E advanced Arm-based 32-bit MCUs reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at Rev 2 (DocID026448). §11.3.2 for the `ADCPRE` prescaler; §11.3.3 for the sixteen external channels and the `IN17`/`IN18` internal ones; §11.5 for `T_conv = sampling time + 12 cycles` and the worked 0.5 µs example; §11.12.2 for the `RES[1:0]` encoding and its cycle counts; §11.12.4–§11.12.5 for the eight `SMP` values; §11.12.15 for `TSVREFE` and `ADCPRE` in `ADC_CCR`. The absence of a DAC chapter is itself the citation for the last section.
- STMicroelectronics — [**STM32F411xC/E datasheet**](https://www.st.com/resource/en/datasheet/stm32f411re.pdf) (DS10314 / DocID026289), consulted at Rev 4. Table 65 "ADC characteristics" for `fADC`, `RADC`, `CADC`, `RAIN`, sampling and conversion times, **and Equation 1 immediately beneath it**, which is the source-impedance formula this page is built on; Tables 66–68 for total unadjusted error at 18, 30 and 36 MHz; Tables 69–70 for ENOB and SINAD with their measurement conditions; Tables 71–72 for the temperature sensor slope, the 10 µs sampling requirement and the `TS_CAL` addresses; Tables 74–75 for `VREFINT` and its calibration value.
- STMicroelectronics — [**AN2834**, *How to get the best ADC accuracy in STM32 microcontrollers*](https://www.st.com/resource/en/application_note/an2834-how-to-get-the-best-adc-accuracy-in-stm32-microcontrollers-stmicroelectronics.pdf). §2.2.6 for the source-resistance mechanism; §3.2.6 for the ½-LSB derivation of the maximum source resistance; §3.3.1 for averaging and the requirement that noise be present for it to gain bits; §3.4 for the high-impedance-source workarounds, including the external capacitor trick when no `SMP` setting is long enough.
- STMicroelectronics — [**AN3116**, *STM32 ADC modes and their applications*](https://www.st.com/resource/en/application_note/an3116-stm32s-adc-modes-and-their-applications-stmicroelectronics.pdf). Regular versus injected groups, scan and discontinuous mode, and the external-trigger configurations — the reference for choosing between the modes `ADC_CR1`/`ADC_CR2` offer rather than discovering them one field at a time.
- Analog Devices — [**MT-003**, *Understand SINAD, ENOB, SNR, THD, THD + N, and SFDR*](https://www.analog.com/media/en/training-seminars/tutorials/MT-003.pdf). What the ENOB and SINAD numbers in the datasheet tables mean and how they are measured, which is the background needed to compare this converter against an external one honestly.
