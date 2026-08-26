---
id: clock-and-peripheral-gating
title: Clock and Peripheral Gating
sidebar_label: Clock and Peripheral Gating
sidebar_position: 3
tags: [embedded, low-power, power-management, rcc, pwr, clocks, stm32]
---

# Clock and Peripheral Gating

Two habits do most of the work in a low-power design that never touches Sleep, Stop, or Standby at all: turn off the clock to anything you are not using, and choose the frequency you run at on purpose rather than by inheriting whatever a previous project left in `clock_init()`. Neither costs anything to implement — both are single register writes — and neither is obviously worth doing until you have seen the arithmetic, because "clock gating saves power" is true in a way that is easy to state and easy to get wrong in the details, particularly the detail this page spends most of its length on: **the energy cost of a fixed piece of work is not simply proportional to clock speed.**

That claim runs against the usual intuition, so it is worth stating the mental model precisely before the numbers. Current in Run mode is, to a first approximation, proportional to frequency — double the clock, roughly double the current. But energy is current multiplied by *time*, and doubling the frequency also roughly halves the time the work takes. Multiply those together and, for the work itself, the two effects cancel: a fixed job costs roughly the same energy whether it is done at 16 MHz or 100 MHz. The frequency choice does not primarily change how much the *work* costs — it changes how much *time is left over*, and what you do with that time is where the real energy is won or lost.

:::info[Prerequisites]
[Configuring the Clock Tree](../04-bare-metal-programming/clock-tree-configuration.md) owns the PLL arithmetic, the flash wait-state ordering, and the ~200 µs PLL lock figure this page's worked example reuses. [Sleep Modes](./sleep-modes.md) owns the Stop-mode current this page compares Run-mode current against.
:::

## Gating what you are not using

Every peripheral on the F411 sits behind a clock-enable bit in `RCC_AHBxENR` / `RCC_APBxENR`, and the reset state of most of them is *off* — [The Anatomy of a Peripheral](../05-peripherals-and-drivers/anatomy-of-a-peripheral.md) covers why you enable one before touching its registers. The low-power discipline is the same rule pointed the other direction: **disable the clock to a peripheral the instant you are done with it**, not just at the end of the program. A UART used once at boot to print a version string and never again should have its clock gated off a few lines later, not left running for the rest of the product's life. A gated-off peripheral draws its full share of dynamic current for nothing — the silicon is switching every clock edge whether or not any code is reading its registers — and that current is drawn continuously, in every mode down to Stop (where the bus clocks themselves stop, gating everything on that bus automatically) but not in Sleep, where the bus clocks and therefore every ungated peripheral keep running.

This matters more than it looks like it should, for two reasons. First, it costs nothing: a peripheral that is genuinely not needed until the next event has no reason to be clocked in between, and un-gating it again is one register write away. Second, forgetting it is invisible in normal testing — the firmware behaves identically whether SPI2's clock is gated or not, because nothing is reading SPI2 either way — so a design review, not a functional test, is what catches it. `RCC_AHB1ENR`, `RCC_AHB2ENR`, `RCC_APB1ENR` and `RCC_APB2ENR` are worth reading back and comparing against "what does this build actually use" as a specific low-power review step, not just at initial bring-up.

## Voltage scaling

[Configuring the Clock Tree](../04-bare-metal-programming/clock-tree-configuration.md) covers the three voltage regulator scales (Scale 1 to 100 MHz, Scale 2 to 84 MHz, Scale 3 to 64 MHz, RM0383 §5.1.4) from the perspective of "what frequency can I reach." The same setting is a power lever read the other way: a lower voltage scale reduces both static leakage and dynamic switching current at a given frequency, because dynamic power scales with the *square* of supply voltage. A design that only ever needs 48 MHz gains nothing from running the regulator at Scale 1 — Scale 2 or 3, whichever the target frequency's ceiling permits, draws measurably less current for identical work. The scale can only be changed with the PLL off, which is the same ordering constraint the clock-tree page's warning covers, applied here for a different reason: getting it backwards there risks a lockup, getting it backwards here just wastes current, silently, for the life of the product.

## The worked comparison: run fast then sleep, versus run slow throughout

This is an illustrative model built from datasheet-typical figures, not a page from the datasheet itself — the point is the *shape* of the trade-off, and the assumptions are stated so the arithmetic can be checked or re-run with your own numbers.

**Setup.** A periodic task must run once every `T = 100 ms`. The work itself takes a fixed number of CPU cycles — call it 160,000 — regardless of frequency. Two strategies:

- **A — run fast, then sleep.** Raise the clock to 100 MHz (needs the PLL), do the work in the time that takes, then drop into the deepest Stop variant from [Sleep Modes](./sleep-modes.md) for whatever remains of the 100 ms.
- **B — run slow, stay awake.** Stay on the 16 MHz HSI (no PLL, no lock time) for the entire 100 ms — do the work, then sit in Run mode doing nothing useful until the next period starts, because nothing dropped the clock or entered a low-power mode.

| Quantity | Value | Basis |
|---|---|---|
| Run-mode current slope | ~100 µA/MHz | ST's headline Run-mode figure for this part (DS10314 Table "Current consumption in Run mode"); treat as illustrative — read the exact table row for your voltage scale and cache/prefetch configuration |
| PLL lock time | ~200 µs | [Configuring the Clock Tree](../04-bare-metal-programming/clock-tree-configuration.md), "on the order of a couple of hundred microseconds," RM0383 |
| Stop-mode current (LP regulator, flash off) | 9 µA typical, `TA = 25 °C` | [Sleep Modes](./sleep-modes.md), DS10314 |
| Supply | 3.3 V | Nucleo board |

**Strategy A — 100 MHz burst, then Stop:**

```text
Work time at 100 MHz  = 160,000 cycles / 100 MHz = 1.6 ms
Active current          = 100 uA/MHz x 100 MHz    = 10.0 mA
Active energy            = 10.0 mA x 3.3 V x 1.6 ms  = 52.8 uJ

PLL-lock overhead (running on HSI @16 MHz while it locks):
  overhead current        = 100 uA/MHz x 16 MHz     = 1.6 mA
  overhead energy          = 1.6 mA x 3.3 V x 0.2 ms  = 1.06 uJ

Remaining time in Stop = 100 ms - 1.6 ms - 0.2 ms = 98.2 ms
  sleep energy            = 9 uA x 3.3 V x 98.2 ms   = 2.92 uJ

Total energy, strategy A ≈ 52.8 + 1.06 + 2.92 = 56.8 uJ
```

**Strategy B — 16 MHz throughout, idling in Run mode after the work is done:**

```text
Work time at 16 MHz    = 160,000 cycles / 16 MHz  = 10.0 ms
Active current           = 100 uA/MHz x 16 MHz     = 1.6 mA
Work energy               = 1.6 mA x 3.3 V x 10.0 ms  = 52.8 uJ

Idle remainder in Run mode = 100 ms - 10.0 ms = 90.0 ms, same clock still
  running at the same current (a simplification — a tight polling loop
  draws close to the same current as the loop that did the real work,
  since it is the clock tree and flash interface being switched that
  costs the current, not the specific instructions retiring):
  idle energy                = 1.6 mA x 3.3 V x 90.0 ms = 475.2 uJ

Total energy, strategy B ≈ 52.8 + 475.2 = 528.0 uJ
```

**The result: strategy A uses about a ninth of the energy of strategy B** (56.8 µJ versus 528.0 µJ, roughly 9.3×) — for *identical* useful work. Two things explain the whole gap, and both are visible directly in the arithmetic:

- **The work itself costs almost exactly the same energy either way** — 52.8 µJ in both strategies, because the 100 µA/MHz model makes current-times-time frequency-invariant for a fixed job. This is the point stated at the top of the page: clock speed alone does not decide the energy cost of the work.
- **All of the difference comes from what happens with the leftover 90-odd milliseconds.** Strategy A spends it at 9 µA in Stop; strategy B spends it at 1.6 mA in Run, because nothing told the core to stop. That is a 178× current ratio (1.6 mA / 9 µA) applied to 90 ms, and it dwarfs everything else in the calculation.

## Where the overhead can eat the win

The 1.06 µJ PLL-lock overhead above was small next to the 475 µJ it saved — but it is not always small, and the case where it is not is worth naming explicitly, because it is the exception that makes "just run fast and sleep" wrong as an unconditional rule. If the work itself is very short — a few tens of microseconds, say — the ~200 µs PLL lock can exceed the work it is paid to accelerate, and a design that pays that fixed cost on every single wake gets none of the benefit strategy A demonstrates above. The general shape: **the run-fast-then-sleep strategy wins when the leftover time it buys, multiplied by the current difference between Run and Stop, exceeds the fixed wake-up overhead it pays to get there.** For a wake that is frequent and whose work is genuinely brief, staying on HSI with no PLL at all — skipping the fast clock entirely — can beat both strategies above, because it avoids the lock-time overhead without paying strategy B's full idle-in-Run cost, provided the work still fits inside the available time at 16 MHz. There is no frequency that is unconditionally correct; the right choice is a function of how much work there is and how the period compares to the wake-up cost, and that is exactly why this section worked the numbers rather than asserting a rule.

:::warning[The clock scaled down to save power, and the flash wait states that never came down with it]
Dropping the system clock to save Run-mode current is a one-line change to `RCC_CFGR.SW` — and it is easy to make that change without touching `FLASH_ACR.LATENCY`, because nothing forces the two together the way [Configuring the Clock Tree](../04-bare-metal-programming/clock-tree-configuration.md)'s warning does for the *raising* direction. The result is not a fault — extra wait states at a lower frequency are merely slower than necessary, not incorrect — but it silently defeats the entire point of the change: a core spending more cycles waiting on flash accesses at a slower clock draws current for those extra stall cycles exactly as it would at the higher frequency, so the current-per-instruction saving the frequency drop was meant to buy is partly or wholly eaten by instructions now taking longer to fetch. The failure is invisible in a current *trace*, because average current still drops when the clock drops — it just drops by less than the frequency ratio predicts, and nobody notices unless they specifically compare the measured saving against the arithmetic in this page. Recompute and lower `LATENCY` every time `SYSCLK` moves down, not only when it moves up.
:::

## See also

- [Sleep Modes](./sleep-modes.md) — the Stop-mode current this page's comparison is built on, and the wake-latency cost that bounds how deep a sleep is worth entering for a short idle interval.
- [Energy Budgets](./energy-budgets.md) — the same active/sleep current split used here, carried through to an actual battery lifetime.
- [Configuring the Clock Tree](../04-bare-metal-programming/clock-tree-configuration.md) — the PLL arithmetic and flash-latency ordering this page's worked example and warning both depend on.
- [Wake Sources and Event-Driven Design](../09-low-power-design/wake-sources-and-event-driven-design.md) — the architectural version of "leftover time spent in Stop instead of Run": restructuring firmware so it is asleep by default rather than idling.
- [Determinism Killers](../06-interrupts-timing-and-real-time/determinism-killers.md) — clock and voltage scaling from the timing side: what changing frequency mid-program does to WCET assumptions.

## References

- STMicroelectronics — [**RM0383**, *STM32F411xC/E advanced Arm-based 32-bit MCUs reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at Rev 4. Chapter 6 ("Reset and clock control (RCC)") for the `RCC_AHBxENR`/`RCC_APBxENR` peripheral clock-gate bits; §5.1.4 for the voltage-scale/frequency table and the requirement that the PLL be off to change scale; Chapter 5 ("Power controller (PWR)") for the low-power-mode context this page's comparison sits alongside.
- STMicroelectronics — [**STM32F411xC/STM32F411xE datasheet**](https://www.st.com/resource/en/datasheet/stm32f411re.pdf) (DS10314). The Run-mode current-consumption table this page's ~100 µA/MHz figure is drawn from, broken out by voltage scale and by which of prefetch/ART/caches are enabled.
- STMicroelectronics — [**AN4365**, *Using STM32F4 MCU power modes with best dynamic efficiency*](https://www.st.com/resource/en/application_note/an4365-using-stm32f4-mcu-power-modes-with-best-dynamic-efficiency-stmicroelectronics.pdf). Works the same run-fast-versus-run-slow question from ST's own measured current traces across the F4 family, including the diminishing-returns case for very short work bursts this page's "where the overhead can eat the win" section describes.
