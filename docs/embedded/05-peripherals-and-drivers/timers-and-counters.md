---
id: timers-and-counters
title: Timers and Counters
sidebar_label: Timers and Counters
sidebar_position: 2
tags: [embedded, peripherals, timers, prescaler, arr, stm32, cortex-m]
---

# Timers and Counters

A timer is the least interesting peripheral to describe and the one you will use most. It is a counter that increments on a clock edge, and a comparator that notices when the count reaches a number you chose. Everything else in the chapter — PWM, input capture, encoder decoding, one-pulse output, triggering the ADC — is that counter with different plumbing bolted onto the comparator.

The mental model: **a timer divides a frequency twice.** The prescaler divides the incoming bus clock down to a counting rate you find convenient — typically one tick per microsecond — and the auto-reload register decides how many of those ticks make a period. Two divisions, two registers, and the entire arithmetic of the peripheral is `f_update = f_TIM / ((PSC + 1) × (ARR + 1))`. The reason both exist rather than one wide divider is range: the prescaler buys you long periods, the auto-reload buys you resolution, and a 16-bit timer can cover microseconds to tens of seconds only because you get to choose how to split the work between them.

The part that trips people is not the formula. It is `f_TIM` — the frequency actually arriving at the prescaler, which on an STM32 is not the APB clock you configured and is not printed anywhere on the clock-tree diagram in an obvious place. That is the subject of the warning below, and it is worth reading before you compute your first period.

:::info[Prerequisites]
[The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md) has the six-step bring-up sequence every example here uses — the clock enable, the read-back, and the rule about configuring while disabled. [Configuring the Clock Tree](../04-bare-metal-programming/clock-tree-configuration.md) is where `PCLK1` and `PCLK2` are set, and it states the timer-clock doubling rule this page depends on. [SysTick and the Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md) covers the core's own 24-bit timer, which is a different and much simpler device.
:::

## What the F411 gives you

Eight timers, three shapes (RM0383 Rev 4 §12, §13 and §14).

| Timer | Bus | Counter | Channels | Distinctive |
|---|---|---|---|---|
| **TIM1** | APB2 | 16-bit | 4 + 3 complementary | Advanced-control: dead-time generator, break input, 8-bit repetition counter |
| **TIM2** | APB1 | **32-bit** | 4 | Full-range counter — the one to reach for when a 16-bit period is not enough |
| **TIM3, TIM4** | APB1 | 16-bit | 4 | General purpose, encoder capable |
| **TIM5** | APB1 | **32-bit** | 4 | As TIM2 |
| **TIM9** | APB2 | 16-bit | 2 | No DMA, no encoder mode |
| **TIM10, TIM11** | APB2 | 16-bit | 1 | No DMA, no encoder mode, no slave mode |

The prescaler is 16 bits on every one of them, including TIM2 and TIM5 — only `CNT`, `ARR` and the capture/compare registers widen to 32 bits. That asymmetry decides more designs than it should: it means the maximum divide is `65536 × 65536` on a 16-bit timer and `65536 × 2³²` on a 32-bit one.

## The counting core

Three registers do the work, and one bit starts it.

```wavedrom title="Counter and update event, ARR = 4, in the two counting modes" alt="Waveform showing the timer counter clock, then an up-counting counter running 0 1 2 3 4 0 1 2 3 4 with an update event pulse at each wrap, then a centre-aligned counter running 0 1 2 3 4 3 2 1 0 with an update event at each overflow and underflow"
{ "signal": [
  { "name": "CK_CNT", "wave": "p............" },
  {},
  ["up-counting",
    { "name": "CNT",  "wave": "2222222222222",
      "data": ["0","1","2","3","4","0","1","2","3","4","0","1","2"] },
    { "name": "UEV",  "wave": "0....10...10." }
  ],
  {},
  ["centre-aligned",
    { "name": "CNT",  "wave": "2222222222222",
      "data": ["0","1","2","3","4","3","2","1","0","1","2","3","4"] },
    { "name": "UEV",  "wave": "0...10..10..1" }
  ]
], "config": { "hscale": 2 } }
```

Read the two rows against each other and the trade is visible. Up-counting with `ARR = 4` gives a period of **five** counter ticks and one update event per period. Centre-aligned with the same `ARR` gives a period of **eight** ticks — up to `ARR` and back down to zero, without repeating the endpoints — and *two* update events, one at the overflow and one at the underflow. Both facts matter later: the doubled period is why a centre-aligned PWM at the same `ARR` runs at half the frequency, and the doubled update rate is why an interrupt you sized for up-counting fires twice as often when someone changes the mode.

| Register | Width | Role |
|---|---|---|
| `TIMx_PSC` | 16-bit | Divides `CK_INT` by `PSC + 1` to produce `CK_CNT`. **Always buffered** — a write takes effect at the next update event. |
| `TIMx_ARR` | 16/32-bit | The top of the count. Buffered only if `CR1.ARPE` is set. |
| `TIMx_CNT` | 16/32-bit | The count itself. Readable and writable at any time. |
| `TIMx_EGR.UG` | write-only | Software-generated update: reloads `PSC` and `ARR` immediately and zeroes `CNT`. |

### `TIMx_CR1`

```wavedrom title="TIMx_CR1 — the control register that decides how the counter counts" alt="Bit-field strip of the 16-bit timer control register 1 showing CEN at bit 0, UDIS at 1, URS at 2, OPM at 3, DIR at 4, CMS in bits 6 to 5, ARPE at 7, CKD in bits 9 to 8, and reserved bits 15 to 10"
{ reg: [
    { bits: 1, name: "CEN",  attr: "rw", type: 2 },
    { bits: 1, name: "UDIS", attr: "rw", type: 4 },
    { bits: 1, name: "URS",  attr: "rw", type: 4 },
    { bits: 1, name: "OPM",  attr: "rw", type: 5 },
    { bits: 1, name: "DIR",  attr: "rw", type: 3 },
    { bits: 2, name: "CMS",  attr: "rw", type: 3 },
    { bits: 1, name: "ARPE", attr: "rw", type: 4 },
    { bits: 2, name: "CKD",  attr: "rw", type: 5 },
    { bits: 6, name: "reserved", type: 1 }
  ],
  config: { hspace: 900, bits: 16, lanes: 1 }
}
```

| Bits | Field | Access | Reset | Meaning |
|---|---|---|---|---|
| 0 | `CEN` | rw | `0` | Counter enable. Cleared by hardware in one-pulse mode; otherwise the start button. |
| 1 | `UDIS` | rw | `0` | `1` disables update events entirely — shadow registers are not reloaded and `UIF` is not set. |
| 2 | `URS` | rw | `0` | Update request source. `0`: overflow, `UG`, or a slave-mode reset all raise the interrupt. `1`: **only** an overflow/underflow does. |
| 3 | `OPM` | rw | `0` | One-pulse mode: hardware clears `CEN` at the next update event. |
| 4 | `DIR` | rw | `0` | `0` up, `1` down. Read-only when `CMS ≠ 00`. |
| 6:5 | `CMS` | rw | `00` | `00` edge-aligned (direction from `DIR`); `01`/`10`/`11` centre-aligned, differing only in whether compare interrupts fire while counting down, up, or both. |
| 7 | `ARPE` | rw | `0` | Auto-reload preload. `0`: a write to `ARR` takes effect immediately. `1`: at the next update event. |
| 9:8 | `CKD` | rw | `00` | Clock division for the digital filters and the dead-time generator: `t_DTS` = `t_CK_INT` × 1, 2 or 4. Does **not** divide the counter. |
| 15:10 | reserved | r | `0` | Keep at reset value. |

`URS` is the field worth setting deliberately. With the default `URS = 0`, a software `UG` — which you issue at the end of every reconfiguration, to load the new prescaler — also raises `UIF` and calls your update handler. Setting `URS = 1` restricts the interrupt to real overflows, which is almost always what a periodic-tick driver means.

## Working out `PSC` and `ARR`

Start from the timer clock, not the bus clock. On the [100 MHz configuration from the clock-tree page](../04-bare-metal-programming/clock-tree-configuration.md) — `HCLK` 100 MHz, `PPRE1` ÷2 so `PCLK1` = 50 MHz, `PPRE2` ÷1 so `PCLK2` = 100 MHz — the timer inputs are:

| Timer group | APB prescaler | Bus clock | **Timer clock `CK_INT`** |
|---|---|---|---|
| TIM2–TIM5 (APB1) | ÷2 | 50 MHz | **100 MHz** (`PCLK1 × 2`) |
| TIM1, TIM9–11 (APB2) | ÷1 | 100 MHz | **100 MHz** (`PCLK2 × 1`) |

Both are 100 MHz, which is convenient and also the reason the doubling rule is so easy to miss on this board: nothing in the numbers looks wrong until someone changes `PPRE2` to ÷2 and the APB2 timers keep running at 100 MHz while the APB1 ones… also keep running at 100 MHz. The rule (RM0383 Rev 4 §6.2) is stated in terms of the prescaler, not the bus: **if the APB prescaler is 1, the timer clock equals the APB clock; otherwise it is twice the APB clock.**

**Worked: a 1 kHz tick on TIM3.**

```text
CK_INT   = 100 MHz            (APB1, PPRE1 = /2, so PCLK1 x 2)
PSC = 99   -> CK_CNT = 100 MHz / (99 + 1)  = 1 MHz     one tick per microsecond
ARR = 999  -> f_UEV  = 1 MHz  / (999 + 1)  = 1000 Hz   exactly 1 ms
```

Choosing `PSC` so `CK_CNT` is exactly 1 MHz is the habit worth forming: `ARR` then reads directly as "period in microseconds", every capture value is a microsecond count, and the arithmetic in the rest of the driver stops needing comments.

**Worked: one update per second on a 16-bit timer.**

```text
PSC = 9999 -> CK_CNT = 100 MHz / 10000 = 10 kHz
ARR = 9999 -> f_UEV  =  10 kHz / 10000 =  1 Hz         both fit in 16 bits
```

**Worked: a period the clock does not divide evenly.**

```text
target 44.1 kHz:  100 MHz / 44100 = 2267.5737...       not an integer
PSC = 0, ARR = 2266 -> 100e6 / 2267 = 44111.16 Hz      +0.0253 %
PSC = 0, ARR = 2267 -> 100e6 / 2268 = 44091.71 Hz      -0.0188 %
```

Take `ARR = 2267`. The general form — `ARR = round(f_TIM / f_target) - 1`, then compute the achieved frequency and the error, and *print both* — is worth writing as a small host-side script or a `static_assert` rather than doing by hand, because the failure is silent. A 0.02 % error is irrelevant for an LED and fatal for a UART bit clock; the number that decides is the tolerance of whatever is on the other end of the wire, and you cannot judge it without having computed the error.

**The range limit, which is a design constraint.** At `CK_INT` = 100 MHz the longest period a 16-bit timer can produce is `65536 × 65536 / 100e6` ≈ **42.9 s**, and the shortest is 10 ns. Anything longer needs TIM2 or TIM5 (32-bit `ARR`, so `65536 × 2³² / 100e6` ≈ 2.8 million seconds), a slower clock source, or a software counter that divides further in the update handler. Discover this at the point where you need a 60-second timeout and you will be moving pins.

### Computing the timer clock at runtime

Hard-coding 100 MHz works until someone changes `SystemInit`. The robust form derives it, and the doubling rule is the only interesting line:

```c title="tim_clock.c"
#include "stm32f4xx.h"
#include <stdbool.h>

/* RCC_CFGR PPREx encoding: 0xx = /1, 100 = /2, 101 = /4, 110 = /8, 111 = /16. */
static const uint8_t apb_shift[8] = { 0, 0, 0, 0, 1, 2, 3, 4 };

uint32_t timer_clock_hz(const TIM_TypeDef *tim)
{
    bool apb2 = (tim == TIM1) || (tim == TIM9) || (tim == TIM10) || (tim == TIM11);

    uint32_t sel = apb2 ? (RCC->CFGR & RCC_CFGR_PPRE2_Msk) >> RCC_CFGR_PPRE2_Pos
                        : (RCC->CFGR & RCC_CFGR_PPRE1_Msk) >> RCC_CFGR_PPRE1_Pos;

    uint32_t shift = apb_shift[sel & 7u];
    uint32_t pclk  = SystemCoreClock >> shift;     /* SystemCoreClock is HCLK */

    /* RM0383 section 6.2: prescaler 1 -> x1, anything else -> x2. */
    return (shift == 0u) ? pclk : pclk * 2u;
}
```

`SystemCoreClock` is `HCLK`, not `SYSCLK`, and it is a plain global that only holds the truth after `SystemCoreClockUpdate()` has run — see [CMSIS and Vendor HALs](../04-bare-metal-programming/cmsis-and-vendor-hals.md).

## A periodic timer, end to end

Following the six-step sequence from [The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md):

```c title="tick.c"
#include "stm32f4xx.h"

volatile uint32_t ticks_ms;

/* 1 kHz periodic update interrupt on TIM3. */
void tim3_tick_init(void)
{
    /* 1 + 2: clock, read-back, reset pulse. */
    RCC->APB1ENR |= RCC_APB1ENR_TIM3EN;
    (void)RCC->APB1ENR;
    RCC->APB1RSTR |=  RCC_APB1RSTR_TIM3RST;
    RCC->APB1RSTR &= ~RCC_APB1RSTR_TIM3RST;

    /* 4: configure with CEN still clear. */
    uint32_t f_tim = timer_clock_hz(TIM3);          /* 100000000 here */
    TIM3->PSC = (uint16_t)(f_tim / 1000000u - 1u);  /* -> 1 MHz, 1 us per tick */
    TIM3->ARR = 999u;                               /* -> 1 kHz                */
    TIM3->CR1 = TIM_CR1_URS;                        /* overflow-only interrupt */

    /* Load PSC and ARR now rather than at the first natural update, and
       zero CNT. Because URS = 1 this does NOT raise UIF. */
    TIM3->EGR = TIM_EGR_UG;

    /* 5: clear any stale flag before arming the NVIC. Write-1-to-clear
       registers are assigned, never OR-ed. */
    TIM3->SR = ~TIM_SR_UIF;
    TIM3->DIER = TIM_DIER_UIE;
    NVIC_SetPriority(TIM3_IRQn, 5u);
    NVIC_EnableIRQ(TIM3_IRQn);

    /* 6: start. */
    TIM3->CR1 |= TIM_CR1_CEN;
}

void TIM3_IRQHandler(void)
{
    if (TIM3->SR & TIM_SR_UIF) {
        TIM3->SR = ~TIM_SR_UIF;      /* clear FIRST, then do the work */
        ticks_ms++;
    }
}
```

Two lines are doing more than they look. `TIM3->SR = ~TIM_SR_UIF;` writes zero to `UIF` and one to every other flag — on a write-1-to-clear register that means "clear `UIF`, leave everything else alone", which `TIM3->SR &= ~TIM_SR_UIF;` emphatically does not do: the read-modify-write clears every flag that happened to be set. And clearing before the work, rather than after, means a second overflow during a long handler sets the flag again and you notice, instead of clearing it on the way out and losing the tick. [Writing Interrupt Handlers in C](../04-bare-metal-programming/interrupt-handlers-in-c.md) has the general rule.

## One-shot: `OPM`

Periodic is the default; one-shot is one bit. Set `CR1.OPM` and the hardware clears `CEN` at the next update event, so the counter runs exactly one period and stops. Re-arming is `TIM3->EGR = TIM_EGR_UG; TIM3->CR1 |= TIM_CR1_CEN;`.

This is the right primitive for a timeout — arm it when you start a transaction, and if the counter reaches the end before you cancel it, the transaction failed. It costs nothing while idle, unlike a polled `ticks_ms` deadline, and it cannot drift relative to the thing it is timing.

`OPM` combined with an output-compare channel is **one-pulse mode**: a trigger input starts the counter, the compare unit produces an edge after a programmed delay, and the update event stops everything. One hardware-generated pulse of an exact width, with no software in the timing path at all (RM0383 Rev 4 §13.3.10).

:::warning[The period that is exactly half what you calculated]
This is the most common timer bug on any STM32 and it produces a beautifully misleading symptom: everything works, and every frequency is exactly 2× what you asked for.

You configure `PCLK1` at 50 MHz because APB1 will not run faster. You compute `PSC` and `ARR` from 50 MHz. Your 1 kHz tick comes out at 2 kHz, your 20 kHz PWM whistles at 40 kHz, and your microsecond delay function delays half a microsecond. Nothing errors, no flag sets, and the code reads correctly against the clock-tree diagram.

The cause is a deliberate feature. When the APB prescaler is anything other than 1, the RCC feeds the timers on that bus **twice** the APB frequency (RM0383 Rev 4 §6.2). It exists so that slowing a peripheral bus does not cost you timer resolution — with `PPRE1` = ÷2, APB1 peripherals see 50 MHz and APB1 timers still see 100 MHz. It is drawn on the clock tree as a small `x2` multiplier on the branch to the timers, and it is very easy to read past.

**How to catch it in ten seconds.** Configure a spare pin to toggle in the update handler and put a scope or logic analyser on it. If the measured frequency is exactly double the calculated one — not 1.9×, not 2.1×, exactly 2× — you have found this and not a PLL misconfiguration. The other tell is that APB2 timers are correct while APB1 timers are wrong, or vice versa, on the same board.

**The fix is not to write `× 2` in the constant.** Derive the timer clock with a function like `timer_clock_hz()` above, which reads the live `PPREx` field and applies the rule. Hard-coding the doubled number works until the day someone changes a prescaler for power reasons and every timer in the system moves by a factor of two at once.

A second, quieter version of the same class of bug: **`PSC` is always buffered.** Writing `TIM3->PSC = 99;` while the counter is running does not change anything until the next update event, so the *first* period after a reconfiguration runs at the old rate. If you are changing rate at runtime, follow the write with `TIM3->EGR = TIM_EGR_UG;` to force the load — and set `URS = 1` first, or that `UG` raises a spurious update interrupt.
:::

:::note[SysTick is not one of these]
The Cortex-M SysTick timer is a core peripheral, not an STM32 one: 24 bits, one reload register, no prescaler, no channels, clocked from `HCLK` or `HCLK/8`. It has no APB prescaler and therefore no doubling rule. It is the right choice for an RTOS tick or a plain millisecond counter, and the wrong choice for anything needing a compare output. See [SysTick and the Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md).
:::

## See also

- [PWM](./pwm.md) — the same counter with the compare units turned on; every number on this page is an input to that one.
- [Input Capture and Encoders](./input-capture-and-encoders.md) — the compare units run backwards: the counter is sampled by an external edge instead of driving one.
- [The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md) — the six-step bring-up sequence, the read-back guard, and the write-1-to-clear rule used throughout.
- [Configuring the Clock Tree](../04-bare-metal-programming/clock-tree-configuration.md) — where `PCLK1` and `PCLK2` are chosen, and the `x2` branch that the warning above is about.
- [SysTick and the Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md) — the core's own 24-bit timer, and when to use it instead of one of these.

## References

- STMicroelectronics — [**RM0383**, *STM32F411xC/E advanced Arm-based 32-bit MCUs reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). §13.3.1 "Time-base unit" for the `PSC`/`ARR`/`CNT` chain and the buffered-prescaler behaviour; §13.3.2 "Counter modes" for up, down and the three centre-aligned variants including the timing diagrams this page's waveform condenses; §13.3.10 "One-pulse mode" for `OPM`; §13.4.1 for the `TIMx_CR1` bit definitions and reset values in the table above; §6.2 "Clocks" for the APB timer-clock doubling rule; §12 and §14 for what TIM1 and TIM9–TIM11 add or omit.
- STMicroelectronics — [**AN4013**, *STM32 cross-series timer overview*](https://www.st.com/resource/en/application_note/an4013-stm32-crossseries-timer-overview-stmicroelectronics.pdf). A single table comparing every timer instance across the whole STM32 range — counter width, channel count, which features are present — and the fastest way to answer "does the timer I picked on this part actually have encoder mode".
- STMicroelectronics — [**AN4776**, *General-purpose timer cookbook for STM32 microcontrollers*](https://www.st.com/resource/en/application_note/an4776-generalpurpose-timer-cookbook-for-stm32-microcontrollers-stmicroelectronics.pdf). Worked configurations for periodic interrupts, one-pulse mode, time-base chaining and prescaler selection, with the ARR/PSC arithmetic done alongside the register writes.
- Elecia White — *Making Embedded Systems*, 2nd edition (O'Reilly, 2024). Chapter 4 for timers as a system resource — how many you actually need, and why a single hardware timer plus software counters is usually a worse trade than it looks. Purchase required.
