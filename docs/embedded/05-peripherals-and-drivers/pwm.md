---
id: pwm
title: PWM
sidebar_label: PWM
sidebar_position: 3
tags: [embedded, peripherals, pwm, timers, dead-time, motor-control, stm32]
---

# PWM

A microcontroller pin has two output voltages and nothing in between. Pulse-width modulation is the trick that gets the third: switch fast enough and whatever is downstream — an LED and your eye, a motor and its inductance, an RC filter and a slow ADC — averages the square wave into a level. The pin is still only ever fully on or fully off, which is why it dissipates almost no power doing it. That is the whole reason PWM won over analogue drive for everything from a status LED to a 10 kW inverter.

The mental model: **PWM is a comparator watching the same free-running counter the timer already has.** The counter sweeps from 0 to `ARR` and starts over; the compare register `CCRx` holds a threshold; the output is one level while `CNT < CCRx` and the other while `CNT ≥ CCRx`. The period is entirely `ARR`'s business and the duty cycle is entirely `CCRx`'s, and because they are separate registers you can change duty on every cycle without disturbing the frequency at all. Everything else in this page is consequences of that one sentence.

The consequence that decides your design is that `ARR` is doing two jobs at once. It sets the period *and* it is the number of distinct duty cycles you can express. There is exactly one clock, and every step of resolution you spend costs you frequency.

:::info[Prerequisites]
[Timers and Counters](./timers-and-counters.md) owns the counter, the prescaler, `ARR`, and the timer-clock doubling rule — this page assumes all of it and only covers the compare side. [The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md) has the bring-up sequence. [How a GPIO Pin Really Behaves](../01-hardware-foundations/gpio-electrical-behaviour.md) covers the drive current and slew rate that decide whether the pin can actually switch the load you have attached to it.
:::

## Duty cycle from a compare register

```wavedrom title="Two duty cycles on one period. ARR = 7, so eight counter ticks per cycle; CCR1 = 2 gives 25%, CCR2 = 6 gives 75%" alt="Waveform with an update event pulse at the start of each of two periods, a 25 percent duty channel high for two of eight ticks, and a 75 percent duty channel high for six of eight ticks, both sharing the same period"
{ "signal": [
  { "name": "UEV",            "wave": "10......10......" },
  { "name": "OC1 (CCR1 = 2)", "wave": "1.0.....1.0....." },
  { "name": "OC2 (CCR2 = 6)", "wave": "1.....0.1.....0." }
], "config": { "hscale": 1 } }
```

Both channels share `CNT`, `PSC` and `ARR`, so both edges align to the same period and the two rising edges are simultaneous. That alignment is not cosmetic: it is why four channels on one timer can drive four LEDs of an RGBW module without beating against each other, and why a three-phase inverter needs its three phases on the *same* timer rather than three timers you started at roughly the same moment.

In **PWM mode 1** (`OCxM = 110`) with up-counting, the channel is active while `CNT < CCRx`. So:

```text
duty = CCRx / (ARR + 1)

CCRx = 0            ->   0 %   (never active)
CCRx = ARR + 1      -> 100 %   (never inactive)
CCRx = ARR          -> ARR / (ARR + 1), which is NOT 100 %
```

That last line is a real off-by-one and it bites on fades. With `ARR = 999`, full brightness is `CCR1 = 1000`, not `999` — writing `999` leaves a 1 µs gap every millisecond. `CCRx` is allowed to exceed `ARR` precisely so that 100 % is expressible; the hardware simply never reaches the compare value. **PWM mode 2** (`OCxM = 111`) is the same comparison inverted, which is occasionally cleaner than flipping `CCER.CCxP` when a driver chip wants active-low.

## Resolution versus frequency

Both divisions come out of the same timer clock, so the trade is arithmetic, not engineering judgement:

```text
f_PWM = f_TIM / ((PSC + 1) x (ARR + 1))
steps = ARR + 1
bits  = log2(f_TIM / f_PWM)          with PSC = 0
```

At `f_TIM` = 100 MHz on the F411 (see the timer-clock table on the [timers page](./timers-and-counters.md)), with `PSC = 0`:

| Resolution | `ARR` | Max `f_PWM` at 100 MHz | Typical use |
|---|---|---|---|
| 8 bits (256 steps) | 255 | **390.6 kHz** | Fast switching supplies, IR carriers |
| 10 bits (1024) | 1023 | **97.7 kHz** | Class-D audio, LED drivers |
| 12 bits (4096) | 4095 | **24.4 kHz** | Motor control just above audible |
| 14 bits (16384) | 16383 | **6.10 kHz** | Servo-grade positioning |
| 16 bits (65536) | 65535 | **1.526 kHz** | The floor of a 16-bit timer with no prescaler |

Read the table in the direction your problem is stated. If you need 20 kHz for a motor, `ARR = 100e6 / 20000 - 1 = 4999`, which is 5000 steps — 12.3 bits, and a duty resolution of 0.02 %. If you need 1 Hz you cannot get there with `PSC = 0` on any of them, and the prescaler buys the range back at the cost of nothing, because `PSC` divides the counting rate without touching the step count.

The honest limit: at 100 MHz you cannot have 16-bit resolution and 20 kHz on the same timer, because that would need 1.31 GHz. Wanting both is the usual reason a design moves to a part with a faster timer clock or accepts dithering — varying the duty by one step between consecutive periods so the *average* has more resolution than any single period does.

## A PWM channel, end to end

Following the six-step bring-up from [The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md). TIM2 channel 1 is on `PA5`, alternate function 1 — the same pin as LD2 on a Nucleo, which makes this directly testable.

```c title="pwm.c"
#include "stm32f4xx.h"

/* 20 kHz PWM on TIM2_CH1 / PA5 (AF1). 5000 steps of duty resolution. */
#define PWM_ARR   4999u

void pwm_init(void)
{
    /* 1 + 2: clock, read-back, reset. */
    RCC->APB1ENR |= RCC_APB1ENR_TIM2EN;
    (void)RCC->APB1ENR;
    RCC->APB1RSTR |=  RCC_APB1RSTR_TIM2RST;
    RCC->APB1RSTR &= ~RCC_APB1RSTR_TIM2RST;

    /* 3: PA5 to AF1, push-pull. See the GPIO driver page for gpio_configure(). */
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;
    (void)RCC->AHB1ENR;
    /* ... MODER = alternate, AFRL[5] = 1, OTYPER = push-pull, OSPEEDR = low ... */

    /* 4: configure with CEN clear. 100 MHz / 5000 = 20 kHz. */
    TIM2->PSC = 0u;
    TIM2->ARR = PWM_ARR;

    TIM2->CCMR1 = (6u << TIM_CCMR1_OC1M_Pos)   /* 110 = PWM mode 1        */
                | TIM_CCMR1_OC1PE;             /* CCR1 preload ON         */
    TIM2->CR1  |= TIM_CR1_ARPE;                /* ARR preload ON          */
    TIM2->CCER  = TIM_CCER_CC1E;               /* channel 1 output enable */

    TIM2->CCR1 = 0u;                           /* start at 0 % */
    TIM2->EGR  = TIM_EGR_UG;                   /* load PSC, ARR, CCR1 now */

    /* 6: start. (No interrupts here, so step 5 has nothing to do.) */
    TIM2->CR1 |= TIM_CR1_CEN;
}

/* Safe to call at any time, from anywhere. One 32-bit store to a preloaded
   register: the new value takes effect at the next update event, atomically
   with respect to the waveform. */
void pwm_set_permille(uint16_t per_mille)          /* 0..1000 */
{
    if (per_mille > 1000u) { per_mille = 1000u; }
    TIM2->CCR1 = ((uint32_t)per_mille * (PWM_ARR + 1u)) / 1000u;
}
```

`OC1PE` and `ARPE` are the two bits people leave out, and leaving them out is not a small error. With preload disabled, a write to `CCR1` takes effect immediately — including halfway through a period, where it can produce an output pulse that is neither the old duty nor the new one. See the second half of the warning below.

## Driving an LED

Frequency first: the eye integrates, but not infinitely fast. Below about 100 Hz the flicker is directly visible; up to a few hundred hertz it shows as a shimmer when the LED or your eye moves, and it beats badly against camera shutters. **1 kHz is the sensible floor** for anything a person looks at, and there is no reason to go higher — faster switching gains nothing perceptually and costs resolution.

The part that surprises people is that linear duty does not look linear. Perceived brightness follows roughly a power law, so a linear ramp from 0 to 100 % duty appears to rush through the dark half and crawl through the bright half. The fix is a gamma table, and on a microcontroller it is a lookup table in flash rather than a `pow()` call:

```c
/* Perceptual brightness -> duty. duty = (level/255)^2.2, scaled to ARR+1.
   Generated on the host; const, so it lives in flash and costs no RAM. */
static const uint16_t gamma_lut[256] = { 0, 0, 0, 0, 0, 1, 1, 1, /* ... */ 5000 };

void led_set_brightness(uint8_t level) { TIM2->CCR1 = gamma_lut[level]; }
```

An exponent of 2.2 is the sRGB-ish convention and is a good default; 2.8 looks better on a very bright LED in a dark room. The right way to choose is to build the ramp and look at it. The current-limiting resistor still sets the maximum brightness — PWM controls the *average*, not the peak, and an LED at 100 % duty is being driven exactly as hard as it would be with no timer at all.

## Driving a motor

Different constraints entirely, and each of them pushes the frequency somewhere.

- **Above audible.** A motor winding is a solenoid; at 5 kHz it sings the PWM frequency loudly enough to be the most-complained-about feature of the product. 20 kHz clears the top of most people's hearing. Higher is quieter for the few who can hear 20 kHz, and costs switching losses.
- **Below the switching loss wall.** Every transition dissipates energy in the MOSFET while it is partly on. Loss scales linearly with frequency, so a bridge that is cool at 20 kHz can be over-temperature at 100 kHz with no change in load.
- **Above the current-ripple limit.** The winding inductance smooths the current between edges; a longer period means more ripple, which means more heating for the same torque. This sets a *floor* on frequency that the motor's `L/R` decides.

20 kHz is where those three meet for most small brushed and brushless motors, which is why it is the number everybody uses.

**Centre-aligned mode** (`CR1.CMS ≠ 00`) is the other motor-control default. The counter runs up and back down, so each pulse is centred in its period rather than aligned to the start, and the edges of the three phases in an inverter are spread out instead of stacked. That reduces the peak current the DC link has to supply and moves the switching harmonics somewhere friendlier. The cost is on the [timers page](./timers-and-counters.md): the period doubles for the same `ARR`, so a 20 kHz centre-aligned PWM needs `ARR = 2500`, not 5000, and you keep half the resolution.

### Complementary outputs and dead time

A half-bridge has a high-side and a low-side switch across the supply. If both conduct at once, even for a hundred nanoseconds, the supply is shorted through them — *shoot-through*, and it destroys MOSFETs quickly and quietly. Real switches turn off more slowly than they turn on, so "drive them with exactly inverted signals" is not sufficient.

TIM1, the advanced-control timer, generates the pair in hardware and inserts a programmable gap on both edges:

```wavedrom title="TIM1 complementary outputs. Both are held inactive for the dead time after each transition of the internal reference" alt="Waveform showing the internal OC1REF reference, the high-side output OC1 whose rising edge is delayed by the dead time, and the low-side output OC1N whose rising edge is likewise delayed, so the two are never high together"
{ "signal": [
  { "name": "OC1REF (internal)", "wave": "1...0...1...0..." },
  { "name": "OC1  (high side)",  "wave": "01..0....1..0..." },
  { "name": "OC1N (low side)",   "wave": "0....1..0......." }
], "config": { "hscale": 1 } }
```

Neither output rises at the instant the other falls. The delay is `DTG[7:0]` in `TIM1_BDTR`, and its encoding is piecewise — four ranges with progressively coarser steps, so a single 8-bit field spans three orders of magnitude (RM0383 Rev 4, `TIMx_BDTR` in §12.4). With `CR1.CKD = 00` and `CK_INT` = 100 MHz, `t_DTS` = 10 ns:

| `DTG[7:5]` | Dead time | Step | Range at 100 MHz |
|---|---|---|---|
| `0xx` | `DTG[7:0] × t_DTS` | 10 ns | 0 – 1270 ns |
| `10x` | `(64 + DTG[5:0]) × 2 t_DTS` | 20 ns | 1280 – 2540 ns |
| `110` | `(32 + DTG[4:0]) × 8 t_DTS` | 80 ns | 2560 – 5040 ns |
| `111` | `(32 + DTG[4:0]) × 16 t_DTS` | 160 ns | 5120 – 10080 ns |

So the maximum expressible dead time on this part at 100 MHz is about **10.1 µs**, and the finest step is 10 ns. The value you want comes from the MOSFET datasheet — turn-off delay plus fall time, plus the gate driver's propagation mismatch, plus margin — and it is one of the few numbers in firmware that is genuinely determined by a component you can hold.

`BDTR` also holds the **break** input (`BKE`, `BKP`) which forces all outputs to their safe state on an external fault, and `MOE`, the master output enable, which is the subject of the warning.

## PWM as the DAC this part does not have

The STM32F411 has no digital-to-analogue converter — see [Analog Basics: ADC and DAC](../01-hardware-foundations/analog-basics-adc-and-dac.md). A PWM channel plus a resistor and a capacitor gets you most of the way there, and the arithmetic tells you honestly how far.

A single-pole RC filter on a PWM output settles to `V × duty`, with a residual triangular ripple. Its peak-to-peak amplitude is worst at 50 % duty and is approximately:

```text
V_ripple(pk-pk)  ~=  V_supply / (4 x f_PWM x R x C)
settling (99%)   ~=  5 x R x C
```

Two configurations, both at 3.3 V with `R` = 10 kΩ and `C` = 100 nF (`RC` = 1 ms):

| `f_PWM` | Resolution at 100 MHz | Ripple | Step size | Settling |
|---|---|---|---|---|
| 20 kHz | 5000 steps (12.3 bits) | **41 mV** pk-pk | 0.66 mV | 5 ms |
| 390 kHz | 256 steps (8 bits) | **2.1 mV** pk-pk | 12.9 mV | 5 ms |

The tension is the point. Raising the frequency crushes the ripple and destroys the resolution; both columns are the same timer clock spent differently. Enlarging `RC` reduces ripple without costing resolution, but the settling time grows with it, so a control loop that updates faster than `5RC` never reaches the value it commanded. A PWM DAC is excellent for a slow-moving setpoint — a contrast voltage, a bias, a reference — and a poor choice for anything that has to move quickly and settle exactly.

:::warning[TIM1 configured perfectly and the pin never moves]
Two failures, both of which leave a register dump that looks completely correct.

**`MOE` is clear.** Take working PWM code from TIM3, change the register names to TIM1, and nothing comes out of the pin. `CCMR1` is right, `CCER.CC1E` is set, `CNT` is visibly counting in the debugger, `CCR1` holds a sensible value, and the pin sits at whatever the GPIO says. The advanced-control timers have one extra gate that the general-purpose timers do not: **`BDTR.MOE`, the main output enable, bit 15, which is `0` at reset.** Until it is set, the whole output stage of TIM1 is disconnected. The fix is one line — `TIM1->BDTR |= TIM_BDTR_MOE;` — and the reason it costs a day is that nothing in the timer's status registers indicates it. It exists so that a fault can kill all six inverter outputs in a single write, which is exactly the right design and exactly why it defaults to off.

The relative that bites afterwards: **`MOE` is cleared by hardware on a break event.** A floating `BKIN` pin with `BDTR.BKE` set will trip on noise, the outputs go dead mid-run, and only the `SR.BIF` flag records it. If you enable the break input, tie `BKIN` to its inactive level with a real resistor and check `BIF` in your fault handler. Setting `BDTR.AOE` makes the hardware re-enable the outputs at the next update event, which is convenient and is also how a genuine fault turns into a fault every 50 µs forever.

**Preload disabled, and the runt pulse.** With `CCMR1.OCxPE` clear, a write to `CCRx` lands in the live compare register immediately. Write a *smaller* value while `CNT` is already past it and the compare for this period never happens: the output stays active for the whole period. Write a larger value just after the comparison and you get a double-length pulse. On an LED this is a visible flash during a fade — a bright frame in the middle of a smooth ramp, which everyone misdiagnoses as a bug in the gamma table. On a motor bridge, a full-duty period instead of a 20 % one is a current spike through the winding and the switch. The same applies to `ARR` without `CR1.ARPE`: shortening the period below the current `CNT` means the counter runs all the way to its maximum before wrapping, producing one period that is thirteen times too long. Set `OCxPE` for every channel you write at runtime and `ARPE` whenever `ARR` is not a compile-time constant, and issue `EGR = UG` once at the end of initialisation so the first period is already correct.
:::

## See also

- [Timers and Counters](./timers-and-counters.md) — the counter, prescaler and `ARR` arithmetic every number on this page is built from, including the APB timer-clock doubling rule.
- [Input Capture and Encoders](./input-capture-and-encoders.md) — the same channels configured as inputs, and how to measure a PWM signal someone else is generating.
- [The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md) — the bring-up sequence, and why `TIM1->BDTR` belongs in step 4 rather than step 6.
- [How a GPIO Pin Really Behaves](../01-hardware-foundations/gpio-electrical-behaviour.md) — drive current, slew rate and why a pin cannot drive a motor directly.
- [Analog Basics: ADC and DAC](../01-hardware-foundations/analog-basics-adc-and-dac.md) — PWM plus an RC filter as the DAC this part does not have, and what that costs in ripple and settling time.

## References

- STMicroelectronics — [**RM0383**, *STM32F411xC/E advanced Arm-based 32-bit MCUs reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). §13.3.9 "PWM mode" for the `OCxM` encodings, the `CNT < CCRx` comparison and the edge-aligned and centre-aligned timing figures; §13.3.8 "Output compare mode" for `OCxPE` and the preload mechanism; §12.3 "Complementary outputs and dead-time insertion" for the pairing and the `DTG` piecewise encoding in the table above; the `TIMx_BDTR` register description in §12.4 for `MOE`, `AOE`, `BKE`, `BKP` and `LOCK`.
- STMicroelectronics — [**AN4013**, *STM32 cross-series timer overview*](https://www.st.com/resource/en/application_note/an4013-stm32-crossseries-timer-overview-stmicroelectronics.pdf). Which timer instances on which parts have complementary outputs, a break input and a dead-time generator — the check to do before committing a pin assignment to a half-bridge.
- STMicroelectronics — [**AN4776**, *General-purpose timer cookbook for STM32 microcontrollers*](https://www.st.com/resource/en/application_note/an4776-generalpurpose-timer-cookbook-for-stm32-microcontrollers-stmicroelectronics.pdf). §3 works PWM generation register by register, including the preload behaviour and the `UG` event at the end of initialisation.
- International Rectifier / Infineon — [**AN-978**, *HV Floating MOS-Gate Driver ICs*](https://www.infineon.com/dgdl/an-978.pdf). Where the dead-time number actually comes from: gate-driver propagation delay, turn-off delay and the shoot-through mechanism the `DTG` field exists to prevent.
- Elecia White — *Making Embedded Systems*, 2nd edition (O'Reilly, 2024). Chapter 4 for PWM as a system-level tool — LED brightness, motor drive and DAC emulation treated as one technique with three sets of constraints. Purchase required.
