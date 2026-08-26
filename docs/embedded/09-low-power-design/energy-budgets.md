---
id: energy-budgets
title: Energy Budgets
sidebar_label: Energy Budgets
sidebar_position: 1
tags: [embedded, low-power, power-management, battery, energy-budget, stm32]
---

# Energy Budgets

Every battery-powered product answers one question before any other design decision matters: how long does it last. That number is not a firmware property or a battery property in isolation — it falls out of an equation with the average current draw on one side and the battery's real, usable, temperature- and load-derated capacity on the other. Get either side wrong and the estimate is fiction: a firmware team that only measures active current and ignores what the part draws asleep will overestimate lifetime by orders of magnitude, and a team that only reads the nameplate mAh off a battery datasheet without reading the discharge curves will do the same in the opposite direction.

The mental model: **a coin cell is not a bucket of charge, it is a chemical reaction with a rate limit**, and a duty-cycle firmware budget is not "average the currents," it is "spend most of the budget in the mode that costs least, and account honestly for what you cannot avoid spending regardless." Two costs are unavoidable and independent of how good the firmware is: the sleep-mode floor current from [Sleep Modes](./sleep-modes.md), and the battery's own self-discharge. This page works one concrete example end to end, with a named cell and its manufacturer's numbers, specifically so the arithmetic and its failure modes are visible rather than asserted.

:::info[Prerequisites]
[Sleep Modes](./sleep-modes.md) establishes the Stop-mode current figure this page's baseline is built on. [Clock and Peripheral Gating](./clock-and-peripheral-gating.md) covers the active-current side of the same budget in more depth.
:::

## The cell: Panasonic CR2032

A CR2032 lithium coin cell is a reasonable choice for a low-duty-cycle sensor node and it is well characterised, which is exactly why it is the standard teaching example. Figures below are Panasonic's published values for the CR2032 (lithium/manganese dioxide, 3.0 V nominal):

| Property | Value | Condition |
|---|---|---|
| Nominal voltage | 3.0 V | — |
| Nominal capacity | 225 mAh | standard continuous drain (~0.19 mA) to a 2.0 V end voltage, 20 °C |
| Operating temperature | −20 °C to +60 °C | — |
| Self-discharge | < 1 % per year | 23 °C storage |
| Recommended maximum continuous current | on the order of a few hundred µA | continuous-drain rating; higher currents are rated separately as pulses |

**The 225 mAh is not a number you get to keep unconditionally.** It is measured at a specific, low, continuous drain current and a specific temperature. Two things erode it in a real design, and a credible energy budget has to address both rather than pretend the nameplate figure is the answer.

## Pulse current versus nameplate capacity

A CR2032 has real internal impedance, and that impedance rises as the cell ages and as temperature drops. Draw a current the datasheet's continuous rating did not anticipate and the terminal voltage sags under load — sometimes below what the regulator or the MCU's brown-out threshold needs — even though the cell has plenty of chemical energy left. Manufacturer datasheets address this with pulse-discharge curves: capacity delivered as a function of pulse current, pulse width, and duty cycle, separate from the continuous-drain figure. A firmware load that spends most of its time at microamps and only pulses to milliamps for a few milliseconds at a time is exactly the shape coin-cell datasheets are drawn for, and it is usually fine; a load that pulses to tens of milliamps — driving a radio at full transmit power is the textbook case — needs the manufacturer's pulse curve consulted directly, because the *usable* capacity at that pulse current can be well below 225 mAh. This is also why "the radio usually dominates every other line item" in a real IoT power budget: a Sub-GHz or BLE radio's transmit current is commonly 10–30 mA (for reference, Nordic's nRF24L01+ datasheet lists roughly 11.3 mA at 0 dBm transmit), one to four orders of magnitude above anything the MCU alone draws, and pulling that current from a coin cell is precisely the case the pulse derating exists for.

The worked example below deliberately stays inside the continuous-drain-like regime — a short MCU burst, no radio — so the nameplate 225 mAh is a defensible number to use. State that assumption explicitly whenever you reuse this arithmetic for a design that adds a radio.

## The worked budget

**Scenario:** a sensor node samples once a minute, does a few milliseconds of work, and sleeps the rest of the time in the deepest Stop-mode variant from [Sleep Modes](./sleep-modes.md).

| Quantity | Value | Source |
|---|---|---|
| Sleep current, `I_sleep` | 9 µA typical | DS10314 Stop-mode table, `LPDS=1, FPDS=1`, `TA = 25 °C` — see [Sleep Modes](./sleep-modes.md) |
| Active current, `I_active` | 1.6 mA | 16 MHz HSI Run mode at ST's ~100 µA/MHz Run-mode figure (DS10314 Table "Current consumption in Run mode") — see [Clock and Peripheral Gating](./clock-and-peripheral-gating.md) for the caveats on this figure |
| Active time per wake, `t_active` | 15 ms | assumed: sample a sensor, compute, write to a backup register |
| Wake period, `T` | 60 s | assumed sampling interval |
| Supply | 3.0 V nominal | CR2032 |

**Duty cycle:**

```text
d = t_active / T = 0.015 s / 60 s = 2.5 x 10^-4   (0.025 %)
```

**Average current**, weighting each state by the fraction of time spent in it:

```text
I_avg = I_sleep + d x (I_active - I_sleep)
      = 9 uA + 0.00025 x (1600 uA - 9 uA)
      = 9 uA + 0.00025 x 1591 uA
      = 9 uA + 0.40 uA
      = 9.40 uA
```

**Check the arithmetic makes sense before trusting it:** the duty cycle is a quarter of a thousandth, so the active state should contribute a correspondingly tiny fraction of the average — 0.40 µA out of 9.40 µA is about 4 %, which is small but not negligible, and the sleep floor dominates as expected for a 15 ms burst once a minute. If the active contribution had come out larger than the sleep term, that would be a sign either the duty cycle or the current figures were entered wrong, and it is worth this sanity check every time — a mis-typed millisecond becomes a hundred-fold error in an average-current estimate that nobody catches because the final number still "looks like" a plausible microamp figure.

**Naive lifetime from nameplate capacity:**

```text
lifetime = 225 mAh / 9.40 uA
         = 225,000 uAh / 9.40 uA
         ≈ 23,936 hours
         ≈ 997 days
         ≈ 2.7 years
```

## The self-discharge ceiling

That 2.7-year figure assumes the only thing draining the cell is the circuit. It is not. **A CR2032 loses capacity to its own internal chemistry regardless of what, or whether, anything is connected to it** — Panasonic's figure above is under 1 % per year at 23 °C, which sounds negligible until you compute what it implies as a current: roughly `0.01 x 225 mAh / 8760 h ≈ 0.26 µA` of self-discharge, continuously, forever. In this example that is small next to the 9.40 µA circuit draw — self-discharge is not the limiting factor here, the Stop-mode floor is — but the ceiling it sets is absolute: **no firmware optimisation can push a CR2032's achievable lifetime meaningfully past its shelf life**, which manufacturers typically rate around ten years to a stated end-of-life voltage. A design whose computed lifetime already approaches or exceeds that figure has stopped being a firmware problem and become a battery-chemistry problem; shaving another microamp off `I_sleep` buys nothing once self-discharge, not the circuit, is the dominant term. The way to notice you have crossed that line is exactly the arithmetic above: compute self-discharge as a current, in the same microamp units as everything else in the table, and compare it directly against `I_avg`.

Temperature works against the budget from both ends at once, which is worth stating rather than eliding: the STM32's own Stop-mode current rises with temperature — the datasheet's maximum Stop-mode figure of 28 µA versus the 9 µA typical is largely a temperature effect — while a lithium coin cell's *deliverable* capacity falls in cold conditions, because the same internal-impedance rise that limits pulse current gets worse as the electrolyte's conductivity drops. A product specified for outdoor use needs both derating curves, from the MCU datasheet and the battery datasheet respectively, not just the room-temperature figures used above for clarity.

:::warning[The lifetime estimate that only measured the demo]
A lifetime budget built from current measured on a bench, mid-development, with logging left on and a debug UART transmitting every wake cycle, is not measuring the shipping firmware — it is measuring the shipping firmware plus every convenience left in for development. UART transmission, even brief, adds milliamps for the duration of every byte; an always-on debug LED adds a fixed current that runs continuously rather than during the duty cycle at all, which is often worse than a larger *pulsed* current precisely because it never turns off. The failure this produces is specific and expensive: a product spec written from a bench measurement that included the debug path promises a battery life the shipping build cannot hit, discovered only after the first field returns come back with cells dead in a fraction of the rated time. The fix is procedural, not technical — measure average current on the actual release build, with every debug output physically disabled (not just quiet), and re-measure after every change that touches the sleep path, not once at the start of the project.
:::

## See also

- [Sleep Modes](./sleep-modes.md) — where the 9 µA `I_sleep` figure and its measurement conditions come from, and the other Stop/Standby variants trading current against wake latency.
- [Clock and Peripheral Gating](./clock-and-peripheral-gating.md) — the active-current side of this budget, including why the ~100 µA/MHz figure used above is not the whole story once wake-up overhead is counted.
- [Wake Sources and Event-Driven Design](./wake-sources-and-event-driven-design.md) — reducing `d`, the duty cycle, by waking less often and doing less when awake, which is the highest-leverage lever in the equation above.
- [RTC and Timekeeping](../05-peripherals-and-drivers/rtc-and-timekeeping.md) — the peripheral that generates the periodic wake in a design like the one worked here, at a current cost far below waking the whole core with a timer.

## References

- Panasonic Industry — [**CR2032 technical data sheet**](https://na.industrial.panasonic.com/products/batteries/primary-lithium-batteries/coin-type/coin-type-manganese-dioxide-lithium/model/CR2032). Nominal voltage and capacity, the standard continuous-drain test condition the 225 mAh figure is measured under, self-discharge rate, and the pulse-discharge characteristic curves referenced above for higher-current loads.
- STMicroelectronics — [**STM32F411xC/STM32F411xE datasheet**](https://www.st.com/resource/en/datasheet/stm32f411re.pdf) (DS10314). The Stop-mode current table this page's `I_sleep` is drawn from, and the Run-mode current-per-MHz figure used for `I_active`.
- Nordic Semiconductor — [**nRF24L01+ product specification**](https://www.nordicsemi.com/Products/nRF24L01P). Cited for the representative radio transmit-current figure (~11.3 mA at 0 dBm) used to illustrate why a radio dominates a battery budget the way this page's MCU-only example does not.
