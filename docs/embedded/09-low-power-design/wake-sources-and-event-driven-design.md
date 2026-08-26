---
id: wake-sources-and-event-driven-design
title: Wake Sources and Event-Driven Design
sidebar_label: Wake Sources and Event-Driven Design
sidebar_position: 4
tags: [embedded, low-power, power-management, exti, dma, rtc, event-driven, stm32]
---

# Wake Sources and Event-Driven Design

Every page so far in this folder has been about what happens once the core decides to sleep. This one is about the decision that matters more than any of them: **most firmware never asks the core to sleep often enough, because it was not structured to.** A superloop that polls a sensor, checks a flag, services a state machine, and only occasionally calls `WFI` between iterations spends the overwhelming majority of its time in Run mode doing nothing, because polling *is* running — it just is not doing useful work while it runs. The energy arithmetic in [Clock and Peripheral Gating](./clock-and-peripheral-gating.md) already showed the size of that mistake: 90 ms of idle Run mode cost roughly two orders of magnitude more than the same 90 ms in Stop.

The mental model this page argues for: **the default state of an event-driven, low-power design is asleep.** Not "asleep when there is nothing to do," which still requires code to notice there is nothing to do and act on it — asleep *by construction*, where the main loop is empty or nearly so, every peripheral that can act without the core does, and the core exists only to be woken by something that already knows it is needed. This is a restructuring of the firmware's control flow, not a register setting, and it is the single highest-leverage change available before any of the mode selection or clock arithmetic in the rest of this folder is even relevant.

:::info[Prerequisites]
[Sleep Modes](./sleep-modes.md) covers what each mode retains and what wakes it. [DMA](../05-peripherals-and-drivers/dma.md) covers the circular-buffer and half-transfer mechanics this page's "core stays asleep" argument depends on. [SysTick and the Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md) covers `SCR.SLEEPONEXIT`, the mechanism that turns an interrupt-driven loop into a genuinely empty one.
:::

## What can wake which mode

Not every wake source reaches every mode, because a source that requires an active clock cannot wake a mode that stopped that clock. The EXTI controller is the workhorse here because its edge-detection logic is asynchronous — it operates directly off the pad, independent of the AHB/APB clocks that Stop mode turns off (RM0383, EXTI chapter) — which is exactly why it can wake Stop mode at all.

| Wake source | Wakes Sleep | Wakes Stop | Wakes Standby |
|---|---|---|---|
| Any enabled interrupt (timer, peripheral, EXTI) | yes | — | — |
| EXTI line (any GPIO configured as an external interrupt) | yes | yes | no — GPIO state is not retained |
| RTC alarm | yes | yes | yes |
| RTC wakeup timer (periodic) | yes | yes | yes |
| RTC tamper / timestamp | yes | yes | yes |
| USB OTG FS wakeup, analog comparator | yes | yes | no |
| `WKUP` pin (PA0) | yes | n/a — chip never left Run far enough to need it | yes |
| `NRST`, IWDG timeout | resets, not a "wake" | resets | resets |

The RTC is the only peripheral on this row that reaches all three modes, and that is not an accident of the table — it is why [RTC and Timekeeping](../05-peripherals-and-drivers/rtc-and-timekeeping.md) frames the RTC as "the timekeeping *and* the scheduling element in a battery-powered design." A design whose only wake source were GPIO interrupts would be unable to use Standby at all for anything periodic, because Standby's own domain does not retain the GPIO EXTI configuration that would need to fire one.

## DMA running while the core sleeps

The core does not have to be awake for the chip to be doing useful work. A DMA stream configured before the core enters Sleep continues to run — it is a second bus master, as [DMA](../05-peripherals-and-drivers/dma.md) frames it, and Sleep mode stops only the CPU clock, not the AHB bus the DMA controller sits on. An ADC sampling into a circular buffer via DMA, with the half-transfer and transfer-complete interrupts enabled, can run for its entire buffer-fill cycle with the core in Sleep the whole time; the core wakes only when a buffer half is actually ready to be processed, does the processing, and returns to Sleep. This is strictly better than the naive alternative of waking the core on every single conversion: the same [DMA](../05-peripherals-and-drivers/dma.md) page's half-transfer mechanism that turns one circular buffer into a double buffer for free also turns "wake the core once per sample" into "wake the core once per buffer," which for a 256-sample half is a 256× reduction in wake events for identical data throughput.

Note the boundary this only reaches Sleep, not Stop — DMA needs `HCLK` to move data, and Stop mode stops `HCLK`. A design that wants both "the bulk of the sampling happens with no core involvement" and "the deepest available current between bursts" typically alternates: Sleep while DMA fills a buffer, briefly wake to hand the filled buffer off or decide there is nothing more to do, then Stop for the interval where nothing at all — not even DMA — needs to run.

## Thresholds in hardware: waking on the answer, not on every sample

The deepest form of "let the peripheral decide" is a peripheral that does not just move data without the core, but evaluates it and only raises an interrupt when the data crosses a threshold the core cares about. The STM32F411's analog watchdog on the ADC is the concrete example available on this part: configure `ADC_LTR`/`ADC_HTR` with a low and high bound, enable `AWDEN` and the watchdog interrupt, and the ADC raises `AWD` only when a converted sample falls outside the configured window — every in-range sample is simply discarded by hardware, never touching the core at all. A temperature or light sensor whose firmware only cares "did this cross a limit" can run the ADC continuously, timer-triggered, DMA-fed or not, and let the core sleep through every single conversion that does not matter, waking only for the one that does. This is the sharpest version of the architectural point: the lowest-energy way to check a value one thousand times is to have hardware check it one thousand times and the core check it once.

The same shape recurs elsewhere on the part in weaker forms worth knowing about even though they are not literally analog thresholds: the RTC's alarm compares the running calendar against a target and only interrupts on a match, rather than requiring the core to poll the calendar every second to notice; a timer's input-capture-with-compare can flag "this pulse was outside the expected width" without the core inspecting every edge. The unifying idea is the same one the analog watchdog demonstrates most directly — push the comparison into hardware, and the core's job shrinks from "evaluate everything" to "handle the exceptions."

## The wake–process–sleep cycle

```wavedrom title="One wake cycle: EXTI event wakes the core from Stop, DMA is already primed, the core processes and re-arms, then returns to Stop" alt="Waveform showing an EXTI event pulse, the core state transitioning from Stop through a wake-up latency period into active processing at high current and back to Stop, and a current trace with a low flat baseline in Stop, a step up during the wake-up latency, a higher plateau during active processing, and a drop back to baseline once the core re-enters Stop"
{ "signal": [
  { "name": "EXTI/RTC event", "wave": "0..10..............." },
  { "name": "Core state", "wave": "2.3.4...........2...", "data": ["Stop", "waking", "active: read, process, re-arm", "Stop"] },
  { "name": "Current (approx)", "wave": "2.3.4...........2...", "data": ["9 uA", "~1.6 mA", "~10 mA", "9 uA"] }
],
  "config": { "hscale": 2 }
}
```

The shape to internalise is the asymmetry between the flat baseline and the brief spike: **the wide majority of this diagram's time axis is the 9 µA Stop-mode floor, and the entire point of the architecture in this page is to make that true in practice, not just in a diagram.** The waking segment costs current at the pre-PLL HSI rate while clocks stabilise; the active segment is where the actual work happens, at whatever current the chosen Run frequency draws; and the cycle's total energy cost is dominated by how short the active-plus-waking segment is relative to the Stop segment — exactly the arithmetic [Clock and Peripheral Gating](./clock-and-peripheral-gating.md) worked through in isolation.

## Restructuring around it

Three changes, applied together, are what turn a polling superloop into the shape this page argues for:

- **Replace every `if (flag_is_set())` poll with the interrupt that would set the flag**, and let `SCB->SCR.SLEEPONEXIT` (see [SysTick and the Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md)) return the core to sleep automatically when the handler that processed the event returns, instead of falling through to a loop body that runs regardless of whether anything happened.
- **Move data collection onto DMA wherever the peripheral supports it**, so the core's involvement per sample drops from "every sample" to "every buffer," per the half-transfer pattern above.
- **Push comparisons the firmware would otherwise perform on every sample into hardware thresholds** where the peripheral offers them, so the core's involvement per *measurement* drops further, from "every buffer" to "only the buffers containing something interesting."

None of these three requires touching `PWR_CR` at all. They are why this page's argument is described as mattering more than any single register setting: a design that never enters anything deeper than Sleep, but is structured this way, will very often out-perform a design that carefully tunes Stop-mode regulator and flash bits but still spends most of its time awake because nothing told it not to be.

:::warning[The peripheral configured to wake the core, and the pending flag that fired the interrupt before the core finished sleeping]
Configuring an EXTI line, an RTC alarm, or an ADC watchdog to wake the core is not the same as configuring it *safely* to wake the core, and the gap between the two produces a specific, easy-to-miss bug: a wake source whose event flag is already set — left over from configuration, from a transient during power-up, or from an earlier cycle whose handler never cleared it — fires its interrupt the instant it is unmasked, which can be *before* the `WFI` that was supposed to be the sleep entry point has even executed. The symptom is a core that appears to never sleep at all despite every low-power register being configured correctly: current stays at the Run-mode figure continuously, because each attempted sleep is immediately pre-empted by a pending interrupt that re-enters the handler, clears nothing relevant, and returns straight back to the loop that tries to sleep again. This is the same failure family the [Sleep Modes](./sleep-modes.md) warning describes for `PWR_CSR.WUF`, generalised to every wake source: EXTI's pending register (`EXTI_PR`), the RTC's alarm flag, and the ADC's `AWD` flag are all write-1-to-clear and none of them are cleared automatically by entering or leaving a low-power mode. Clear the specific flag for every wake source immediately before arming it, not just once at start-up, and check the relevant pending register in the debugger if a design's measured current never drops the way the datasheet promises it should.
:::

## See also

- [Sleep Modes](./sleep-modes.md) — which of Sleep, Stop, and Standby each wake source in the table above actually reaches, and the stale-flag failure this page's warning builds on.
- [Clock and Peripheral Gating](./clock-and-peripheral-gating.md) — the energy arithmetic behind why minimising awake time matters as much as it does.
- [DMA](../05-peripherals-and-drivers/dma.md) — the half-transfer and circular-buffer mechanics this page's "core stays asleep during acquisition" section is built on.
- [RTC and Timekeeping](../05-peripherals-and-drivers/rtc-and-timekeeping.md) — the alarm and periodic wakeup timer that are the only wake sources reaching every mode including Standby.
- [SysTick and the Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md) — `SCR.SLEEPONEXIT`, the register bit that makes an interrupt-driven main loop genuinely empty.

## References

- STMicroelectronics — [**RM0383**, *STM32F411xC/E advanced Arm-based 32-bit MCUs reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at Rev 4. The EXTI chapter for the asynchronous, clock-independent edge-detection behaviour that lets an EXTI line wake Stop mode; the ADC chapter for `ADC_LTR`/`ADC_HTR`/`AWDEN` and the analog watchdog interrupt; Chapter 5 ("Power controller") for the wake-source-to-mode mapping in the table above.
- STMicroelectronics — [**STM32F411xC/STM32F411xE datasheet**](https://www.st.com/resource/en/datasheet/stm32f411re.pdf) (DS10314). The wake-source list in the Stop- and Standby-mode sections that the comparison table above is drawn from.
- Nordic Semiconductor — [**nRF24L01+ product specification**](https://www.nordicsemi.com/Products/nRF24L01P). Referenced in [Energy Budgets](./energy-budgets.md) for a representative radio current figure; relevant here as the kind of peripheral whose own low-power/wake-on-address modes are a second layer of the same "let hardware decide when the core is needed" argument, one level removed from the MCU itself.
