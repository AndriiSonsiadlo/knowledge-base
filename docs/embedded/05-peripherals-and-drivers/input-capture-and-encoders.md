---
id: input-capture-and-encoders
title: Input Capture and Encoders
sidebar_label: Input Capture and Encoders
sidebar_position: 4
tags: [embedded, peripherals, timers, input-capture, quadrature, encoder, stm32]
---

# Input Capture and Encoders

PWM points the timer outward: the counter drives a pin. Input capture points it inward. The counter free-runs, an edge on a pin tells the hardware "now", and the value of `CNT` at that instant is copied into a capture register before software has had a chance to be late. That last clause is the entire value of the peripheral. A GPIO interrupt can also tell you an edge happened, but by the time your handler reads a counter it has been anywhere from 12 to several hundred cycles — jittering with whatever else the NVIC was doing — and the measurement carries that jitter. The capture unit's latch has no jitter at all.

The mental model: **input capture is a hardware timestamp.** Everything you build with it is arithmetic on timestamps. The difference between two consecutive rising edges is a period. The difference between a rising and the next falling edge is a pulse width. Two channels timestamping two related signals give you phase. The complications are all in one place — the counter is finite, so the timestamps wrap, and a wrapped subtraction is only correct if you know how many wraps happened.

Quadrature encoder mode is the same silicon arranged differently: instead of timestamping edges, the counter itself is driven by them, up or down according to which of two signals moved first. Position becomes a register read.

:::info[Prerequisites]
[Timers and Counters](./timers-and-counters.md) owns `CNT`, `PSC`, `ARR` and the update event; this page reuses all of them and adds only the capture side. [PWM](./pwm.md) covers the same channels as outputs and is worth reading first — `CCMR1` is the same register with different field meanings depending on the direction. [How a GPIO Pin Really Behaves](../01-hardware-foundations/gpio-electrical-behaviour.md) covers input thresholds and why a slow edge produces several transitions.
:::

## Capturing an edge

```wavedrom title="A rising-edge capture on TI1. CNT is latched into CCR1 at the edge; CC1IF is set until software reads CCR1" alt="Waveform showing an input signal TI1 with two rising edges, a free-running counter, the capture register CCR1 taking the counter values 2 and 8 at those edges, and the CC1IF flag setting at each capture and clearing when software reads"
{ "signal": [
  { "name": "TI1",   "wave": "0.1..0..1..0." },
  { "name": "CNT",   "wave": "2222222222222",
    "data": ["0","1","2","3","4","5","6","7","8","9","10","11","12"] },
  { "name": "CCR1",  "wave": "x.3.....3....", "data": ["2","8"] },
  { "name": "CC1IF", "wave": "0.1..0..1..0." }
], "config": { "hscale": 2 } }
```

The period is `8 - 2 = 6` counter ticks, and if you set `PSC` so that one tick is one microsecond — the habit from the [timers page](./timers-and-counters.md) — it is 6 µs with no conversion. `CC1IF` sets on the capture and is cleared by reading `CCR1`, which is the third clearing convention from [The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md): the act of consuming the data is the acknowledgement.

The capture path has three configurable stages before the latch, all in `TIMx_CCMR1` and `TIMx_CCER`:

| Field | Register | What it does |
|---|---|---|
| `CC1S[1:0]` | `CCMR1` | Selects the input. `01` = this channel's own pin (TI1), `10` = the *other* channel's pin (TI2), `11` = the internal trigger. Writing a non-zero value is what makes the channel an input. |
| `IC1F[3:0]` | `CCMR1` | Digital filter: sampling rate and how many identical consecutive samples are needed. `0000` = off. |
| `IC1PSC[1:0]` | `CCMR1` | Capture prescaler: latch on every event, or every 2nd, 4th, or 8th. |
| `CC1P`, `CC1NP` | `CCER` | Active edge. `00` rising, `01` falling, `11` both edges. |
| `CC1E` | `CCER` | Capture enable. |

`CC1S` selecting the *other* channel's pin is the feature that makes PWM input mode work, and it is easy to misread as a typo in the reference manual. It is not: one physical signal can feed two capture units.

## Measuring frequency: two methods and where they cross

**Period measurement** — capture consecutive rising edges, subtract. Resolution is one counter tick out of however many ticks the period contains, so the relative error is `f_signal / f_counter`. Excellent at low frequencies, useless at high ones: with a 1 MHz counter, a 200 kHz signal is only five ticks long and one tick of quantisation is a 20 % error.

**Gate counting** — configure the timer to count *edges of the signal* rather than the internal clock (external clock mode, `SMCR.ECE` or `SMS = 111`), and read `CNT` at fixed intervals. Resolution is one edge per gate window, so the relative error is `1 / (f_signal × T_gate)`. Excellent at high frequencies, terrible at low ones: a 1 Hz signal needs a one-second gate to resolve at all.

The two errors are equal when `f_signal = sqrt(f_counter / T_gate)`. With a 1 MHz counter and a 1-second gate that crossover is **1 kHz** — below it, measure the period; above it, count edges. A tachometer spanning both regimes switches method mid-range, and that switch is the design decision, not an implementation detail.

**Pulse width** needs both edges of the same signal. Two ways:

- Set `CC1P`/`CC1NP` to `11` (both edges) on one channel and subtract consecutive captures. Simple, and you have to track which edge you just got.
- **PWM input mode** (RM0383 Rev 4 §13.3.6): route TI1 to both capture units — `CC1S = 01` on channel 1 (rising) and `CC2S = 10` on channel 2 (falling) — and put the slave-mode controller in reset mode triggered by TI1FP1. Every rising edge zeroes the counter, so `CCR1` reads the **period** and `CCR2` reads the **high time**, both directly, with no subtraction and no state machine. Duty cycle is `CCR2 / CCR1`.

PWM input mode costs a whole timer for one signal and only works on channels 1 and 2. It is the correct choice for decoding an RC servo signal, an ultrasonic rangefinder's echo pulse, or any single stream where you want period and width every cycle without software in the loop.

## The digital filter, and what it does not do

`ICxF` is a majority filter: the hardware samples the input at a divided clock and only propagates a transition when *N* consecutive samples agree. That kills ringing on an edge, a glitch coupled from a neighbouring trace, and the multiple transitions a slow rising edge produces as it crawls through the Schmitt trigger's hysteresis band.

The maximum it can do is bounded, and the bound is worth computing once. The slowest setting is `f_SAMPLING = f_DTS / 32` with `N = 8`, where `f_DTS` comes from `CR1.CKD` (÷1, ÷2 or ÷4 of `CK_INT`):

```text
CK_INT = 100 MHz
CKD = 00  ->  f_DTS = 100 MHz  ->  f_DTS/32 = 3.125 MHz  ->  8 samples =  2.56 us
CKD = 11  ->  f_DTS =  25 MHz  ->  f_DTS/32 =  781 kHz   ->  8 samples = 10.24 us
```

**About ten microseconds is the ceiling.** A mechanical switch bounces for one to twenty *milliseconds* — three orders of magnitude more. So: the timer input filter is for electrical noise, and it will not debounce a button. Debouncing a contact is a software job (a state machine sampled at 5–10 ms, or a one-shot timer armed on the first edge), and reaching for `ICxF` to do it is a well-worn dead end.

## Overflow: when the signal is slower than the counter

A 16-bit counter at 1 MHz wraps every 65.536 ms. Any signal slower than about 15 Hz produces captures whose difference is meaningless unless you account for the wraps.

Unsigned subtraction handles **exactly one** wrap for free, which is the first thing to know and the reason this bug hides:

```c
uint16_t delta = (uint16_t)(now - previous);   /* correct across one wrap */
```

Modular arithmetic makes `0x0005 - 0xFFF0` come out as `0x0015` = 21, which is right. It is right for one wrap and silently wrong for two, and there is no flag distinguishing the two cases.

The general fix is to widen the timestamp by counting update events:

```c title="capture64.c"
static volatile uint32_t overflows;
static volatile uint64_t last_stamp;

void TIM3_IRQHandler(void)
{
    uint32_t sr = TIM3->SR;

    if (sr & TIM_SR_UIF) {
        TIM3->SR = ~TIM_SR_UIF;
        overflows++;
    }

    if (sr & TIM_SR_CC1IF) {
        uint16_t cc = (uint16_t)TIM3->CCR1;      /* the read clears CC1IF */
        uint32_t ovf = overflows;

        /* Both flags were pending in the same read of SR. The overflow may
           have happened before OR after the capture, and SR does not say.
           A capture value near the bottom of the range means the counter had
           already wrapped when the edge arrived, so count that overflow in. */
        if ((sr & TIM_SR_UIF) && cc < 0x8000u) {
            ovf++;
        }

        uint64_t stamp = ((uint64_t)ovf << 16) | cc;
        uint64_t period = stamp - last_stamp;
        last_stamp = stamp;
        (void)period;
    }
}
```

The heuristic in the middle is the standard one and it is worth understanding rather than copying. When both flags are pending you cannot tell the order from the hardware, so you infer it from the captured value: a capture in the bottom half of the range, seen alongside a pending overflow, almost certainly happened *after* the wrap. It is correct whenever the interrupt latency is well under half a counter period — which is the same condition under which the whole scheme works at all.

Three ways to avoid needing it:

- **Use TIM2 or TIM5.** A 32-bit counter at 1 MHz wraps every 71.6 minutes. For nearly every measurement problem on this part, that removes the overflow question entirely and it costs nothing.
- **Prescale harder.** A 1 kHz counting rate wraps a 16-bit counter every 65 seconds, at the cost of millisecond resolution.
- **Check `CCxOF`.** Distinct from overflow of the counter: `TIMx_SR.CC1OF` is the **over-capture** flag, set when a new capture arrives while `CC1IF` is still set — meaning software was too slow and one timestamp was overwritten and lost. Almost nobody reads it, and it is the difference between "my frequency reading is occasionally double" and knowing why. Clear it write-1-to-clear alongside `CC1IF` and count the occurrences; a non-zero count is a real-time budget failure, not a measurement error.

## Quadrature encoders

An incremental rotary encoder produces two square waves 90° out of phase. Neither alone tells you direction; together they do, because which one changes first depends on which way the shaft turned.

```wavedrom title="Quadrature: the same two signals, in the two directions. Only the order of the edges differs" alt="Two waveform groups. In the first, channel A rises before channel B, which the encoder interface counts as forward. In the second, B rises before A, counted as reverse. The signals are otherwise identical square waves ninety degrees apart"
{ "signal": [
  ["A leads B — count up",
    { "name": "A (TI1)", "wave": "0.1.0.1.0.1." },
    { "name": "B (TI2)", "wave": "0..1.0.1.0.1" }
  ],
  {},
  ["B leads A — count down",
    { "name": "A (TI1)", "wave": "0..1.0.1.0.1" },
    { "name": "B (TI2)", "wave": "0.1.0.1.0.1." }
  ]
], "config": { "hscale": 2 } }
```

The two groups contain exactly the same edges. What differs is the order, and the encoder interface decodes it with one rule: **at each active edge, sample the other signal's level; that level decides up or down.** No software involvement, no interrupt per edge, no missed counts at speed.

Set it up with `SMCR.SMS`, having first put both channels into input mode (`CC1S = 01`, `CC2S = 01`):

| `SMS` | Counts on | Effective resolution | Notes |
|---|---|---|---|
| `001` | TI2 edges only | **×2** | Direction from TI1's level |
| `010` | TI1 edges only | **×2** | Direction from TI2's level |
| `011` | Both TI1 and TI2 edges | **×4** | The usual choice — four counts per encoder cycle |

A 1000 pulse-per-revolution encoder in `SMS = 011` therefore gives 4000 counts per revolution. `CNT` is the position, readable at any time with a single load; `CR1.DIR` is read-only in this mode and reports the last direction of travel. Velocity is a difference of `CNT` over a fixed sampling interval, which is the one part you do write in software.

```c title="encoder.c"
void encoder_init(void)                     /* TIM3, PA6 = CH1, PA7 = CH2, AF2 */
{
    RCC->APB1ENR |= RCC_APB1ENR_TIM3EN;
    (void)RCC->APB1ENR;
    RCC->APB1RSTR |=  RCC_APB1RSTR_TIM3RST;
    RCC->APB1RSTR &= ~RCC_APB1RSTR_TIM3RST;
    /* ... PA6/PA7 to AF2, pull-up if the encoder is open-collector ... */

    TIM3->CCMR1 = (1u << TIM_CCMR1_CC1S_Pos)     /* CH1 <- TI1 */
                | (1u << TIM_CCMR1_CC2S_Pos)     /* CH2 <- TI2 */
                | (0xFu << TIM_CCMR1_IC1F_Pos)   /* max filter: f_DTS/32, N=8 */
                | (0xFu << TIM_CCMR1_IC2F_Pos);
    TIM3->CCER  = 0u;                            /* both non-inverted          */
    TIM3->SMCR  = (3u << TIM_SMCR_SMS_Pos);      /* encoder mode 3 = x4        */
    TIM3->ARR   = 0xFFFFu;                       /* free-running, wraps cleanly */
    TIM3->CNT   = 0u;
    TIM3->CR1  |= TIM_CR1_CEN;
}

int16_t encoder_delta(void)      /* counts since the last call; signed, wraps correctly */
{
    static uint16_t last;
    uint16_t now = (uint16_t)TIM3->CNT;
    int16_t  d   = (int16_t)(now - last);
    last = now;
    return d;
}
```

`ARR = 0xFFFF` and the `int16_t` cast do the work together: the counter wraps through the full 16-bit range, the unsigned subtraction is modular, and the cast reinterprets the result as a signed delta that is correct in both directions as long as you call it more often than the shaft moves 32768 counts.

An **index pulse** — the once-per-revolution Z output on many encoders — has no dedicated support in the encoder interface. Route it to an EXTI line and zero `CNT` in the handler, or feed it to the timer's external trigger with the slave-mode controller in reset mode. Either way it converts an incremental encoder into an absolute one after the first revolution, which is what makes homing possible.

:::warning[The encoder that gains a hundred counts while the machine is switched off]
Two failures, both silent, both about counting edges that are not motion.

**A stationary encoder resting on a transition.** Park the shaft so one channel sits exactly at its switching threshold and the input buffer will chatter on thermal noise, mains hum, or the motor drive's switching harmonics. The encoder interface faithfully counts every one of those transitions. In `SMS = 011` the count usually oscillates ±1 harmlessly — but if both channels are noisy, or if the noise is correlated with something periodic, the count drifts steadily in one direction. A machine that homes at power-on and then reports being 3 mm from where it physically is, having sat still overnight, is this. Nothing in the timer flags it.

The tell is direct: log `CNT` for a minute with the drive powered but the shaft mechanically locked. It should be constant. If it walks, you have this. The fixes, in order of how much they help: enable the input filter (`ICxF = 0xF` gives ~2.6 µs of noise immunity at 100 MHz, which handles switching pickup), use a differential encoder with an RS-422 receiver instead of single-ended outputs, and route the encoder pair away from the motor phases. Adding a pull-up will not help — the problem is not a floating input, it is a valid input sitting at the threshold.

**Missed wraps on a slow signal.** Frequency measurement by period capture works beautifully during development, when everything is spinning, and reads nonsense at low speed. The reason is that the unsigned subtraction across two captures is correct for one counter wrap and wrong for two, with no flag to distinguish them: a 5 Hz signal on a 16-bit counter running at 1 MHz wraps three times per period, so the delta comes back as `period mod 65536` and the computed frequency is a plausible-looking multiple of the truth. Everything above ~15 Hz is exact; everything below is confidently wrong.

Two guards. Extend the timestamp with an overflow counter as shown above and check `TIMx_SR.CC1OF` for lost captures, or — much simpler, and free on this part — use TIM2 or TIM5, where the 32-bit counter pushes the wrap out to 71 minutes and the problem stops existing. If you must stay on a 16-bit timer, declare the minimum measurable frequency in the driver's header and return an explicit "too slow" error below it rather than a number.
:::

## See also

- [Timers and Counters](./timers-and-counters.md) — `CNT`, `PSC`, `ARR`, the update event and the timer-clock arithmetic every measurement here depends on.
- [PWM](./pwm.md) — the same `CCMR1` and `CCER` registers with the channels pointed outward; read together, the two pages cover the whole capture/compare unit.
- [The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md) — the bring-up sequence, and the "read the data register to clear the flag" convention `CCR1` follows.
- [Writing Interrupt Handlers in C](../04-bare-metal-programming/interrupt-handlers-in-c.md) — the single `SR` read, the clear-first discipline, and the latency budget the over-capture flag measures.
- [How a GPIO Pin Really Behaves](../01-hardware-foundations/gpio-electrical-behaviour.md) — Schmitt-trigger hysteresis and slow edges, which is what the input filter exists to clean up.

## References

- STMicroelectronics — [**RM0383**, *STM32F411xC/E advanced Arm-based 32-bit MCUs reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). §13.3.5 "Input capture mode" for the capture path, `CCxS`, `ICxPSC` and the `CCxIF`/`CCxOF` flag pair; §13.3.6 "PWM input mode" for the two-channels-one-signal configuration that yields period and width directly; §13.3.12 "Encoder interface mode" for the `SMS` encodings and the counting-direction table this page condenses; §13.4.7 for the `ICxF` filter encodings and the `f_DTS`/N combinations used in the filter calculation.
- STMicroelectronics — [**AN4776**, *General-purpose timer cookbook for STM32 microcontrollers*](https://www.st.com/resource/en/application_note/an4776-generalpurpose-timer-cookbook-for-stm32-microcontrollers-stmicroelectronics.pdf). §4 and §5 work input capture and PWM input mode register by register, including the frequency-measurement resolution trade-off and the counter-overflow extension.
- STMicroelectronics — [**AN4013**, *STM32 cross-series timer overview*](https://www.st.com/resource/en/application_note/an4013-stm32-crossseries-timer-overview-stmicroelectronics.pdf). Which timers on which parts implement the slave-mode controller and therefore encoder mode — TIM10 and TIM11 on this part do not, which is not obvious from the register map.
- Jack Ganssle — [*A Guide to Debouncing*](http://www.ganssle.com/debouncing.htm). Measured bounce durations for dozens of real switches, which is the evidence behind the claim above that no hardware input filter on this timer is remotely long enough to debounce a contact.
- Elecia White — *Making Embedded Systems*, 2nd edition (O'Reilly, 2024). Chapter 4 for input capture as a sensor-interface technique and Chapter 6 for the sampling-rate reasoning behind converting encoder counts into a velocity. Purchase required.
