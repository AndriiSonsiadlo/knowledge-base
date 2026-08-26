---
id: sleep-modes
title: Sleep Modes
sidebar_label: Sleep Modes
sidebar_position: 2
tags: [embedded, low-power, power-management, pwr, cortex-m, stm32]
---

# Sleep Modes

A low-power mode is not one switch, it is a set of trade-offs arranged along a slider: how much of the chip stays clocked, how much of it stays powered, and how quickly it can come back. Turn more of the chip off and the current drops by orders of magnitude, but so does how much the chip remembers and how fast it can react. Every low-power decision on this part is a choice of where to sit on that slider, and the three points ST put on it — **Sleep**, **Stop**, and **Standby** — are not arbitrary; each one turns off exactly the next layer down: first the CPU clock, then every clock and the main regulator, then the regulator's own supply to everything but a small backup island.

The mental model worth keeping: **Sleep leaves the chip running and stops asking it to run**, **Stop leaves the chip powered and stops giving it a clock**, and **Standby stops powering most of the chip at all**. Each step down costs more to come back from, because there is more to restart — clocks that must relock, a regulator that must ramp, in the extreme case a core that has to boot from reset because it forgot everything. Reading a datasheet current table without this framing looks like an arbitrary list of microamp figures; reading it with this framing, every number is explained by exactly one design decision: what did this mode choose to leave on.

:::info[Prerequisites]
[SysTick and the Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md) covers `SCR.SLEEPONEXIT` and `SCR.SLEEPDEEP` — the Cortex-M bits this page's `PWR_CR` settings work alongside — and [Configuring the Clock Tree](../04-bare-metal-programming/clock-tree-configuration.md) covers the PLL lock time this page's wake latencies are built from. [RTC and Timekeeping](../05-peripherals-and-drivers/rtc-and-timekeeping.md) owns the RTC alarm and wakeup-timer mechanics that recur here as wake sources, and [Watchdogs](../05-peripherals-and-drivers/watchdogs.md) owns the IWDG behaviour this page's warning depends on.
:::

## Two instructions, one register field, one chip-specific register

Entering any of the three modes starts with the same Cortex-M instruction, `WFI` (or `WFE`) — "wait for interrupt," which stalls the pipeline until an exception is pending. What that instruction actually *does* depends on two bits outside the core entirely:

- **`SCB->SCR.SLEEPDEEP`** (PM0214 §4.4.5) — clear for Sleep, set for Stop or Standby. This is the switch between "just gate the CPU clock" and "hand control to the PWR peripheral for something deeper."
- **`PWR_CR.PDDS`** — with `SLEEPDEEP` set, this second bit chooses Stop (`PDDS = 0`) or Standby (`PDDS = 1`). Two more `PWR_CR` bits shape *which* Stop: `LPDS` selects the low-power regulator over the main regulator, and `FPDS` powers the flash down as well.

So the three modes are not three unrelated procedures — they are one instruction with an escalating set of flags, and the table below is what each combination buys and costs.

## The comparison

*Current figures below are corroborated against the STM32F411xC/E datasheet (DS10314)'s Stop-mode and Standby-mode current-consumption tables — consistent across multiple independent sources quoting DS10314 — rather than read directly from a fetched copy of the PDF, and are marked typical or maximum as stated. Verify against the primary datasheet table before designing to these; where a specific supply/temperature pair is not attached, treat the number as an order-of-magnitude guide and read the datasheet table directly for your operating point. Wake latency is described qualitatively — datasheet timing tables give exact figures per configuration; the ordering (Sleep fastest, Standby slowest) is what matters for the architectural decision.*

| Mode | Core clock | Other clocks | Regulator | SRAM & registers | Typical current | Wake latency | Wake sources |
|---|---|---|---|---|---|---|---|
| **Sleep** | stopped | running | main, on | fully retained | Run-mode current for the active frequency, minus the core's own share (DS10314, "Current consumption in Sleep mode" table) | ~1–2 clock cycles — every clock but the CPU's was already running | any enabled interrupt or event |
| **Stop**, main regulator | stopped | stopped (HSI/HSE/PLL off) | main, on | fully retained | low hundreds of µA — regulator stays on, so nothing needs to ramp on the way out | fastest of the Stop variants: no regulator wake-up | EXTI lines, RTC alarm/wakeup/tamper/timestamp, USB OTG FS wakeup, comparator |
| **Stop**, low-power regulator | stopped | stopped | low-power (`LPDS=1`) | fully retained | lower than main-regulator Stop | slower: the LP regulator must switch back to the main regulator before the core resumes | same as above |
| **Stop**, LP regulator + flash power-down | stopped | stopped | low-power | fully retained (flash itself is off, not read) | **typ. 9 µA, max 28 µA** (`TA = 25 °C`, `LPDS=1`, `FPDS=1`, DS10314 Stop-mode table) | slowest Stop variant: regulator switch-back *and* flash wake | same as above |
| **Standby** | stopped | stopped, backup domain only | off | **lost**, except `RTC_BKPxR` and the RTC itself | **typ. 1.8 µA** (`TA = 25 °C`, `VDD = 1.7 V`, RTC off) / **max 11 µA** (`TA = 85 °C`, `VDD = 1.7 V`) (DS10314 Standby-mode table) | comparable to a power-on reset — the core restarts from the reset vector, not from where it left off | `WKUP` pin (PA0), RTC alarm/wakeup/tamper/timestamp, `NRST`, IWDG reset |

Two things in that table are easy to misread on a skim.

**"Fully retained" in Sleep and Stop means SRAM and every register**, including peripheral registers — nothing needs re-initialising on the way out except whatever clocks you turned off going in. **Standby retains almost nothing.** The 1.2 V domain that holds the CPU, SRAM, and every peripheral register is powered down entirely; only the backup domain — the RTC, its 20 backup registers, and the three PC13–PC15 pins — survives, and it survives because it runs from `VBAT`, exactly as in [RTC and Timekeeping](../05-peripherals-and-drivers/rtc-and-timekeeping.md). Waking from Standby is not "resuming"; it is a reset, and firmware distinguishes it from a power-on reset by reading `PWR_CSR.SBF` (standby flag) before clearing it.

**Wake latency grows in the same order current drops.** That is not a coincidence, it is the same trade paid twice: the low-power regulator in Stop mode must hand control back to the main regulator before the core can run at full speed, and that hand-off takes time proportional to how far down the regulator was allowed to go. Flash power-down adds a second, independent wake cost on top: the flash interface must re-power and the ART accelerator's buffers are empty, so the first several fetches are slow in exactly the way a cold cache is slow. Standby pays the largest cost of all because there is no "resume" path — the core boots.

## Choosing between Stop variants

The three Stop variants in the table exist because "how fast do I need to be back" and "how little can I draw" are genuinely different questions with genuinely different answers depending on the application:

- **Main regulator, clocks stopped.** Rarely the right choice on its own — it pays almost the full Stop-mode wake-latency reduction for only a fraction of the current saving, because the regulator itself, the largest single consumer in the chip at rest, is still on. Its niche is a very short, very frequent sleep where the LP regulator's switch-back time would dominate the whole cycle.
- **Low-power regulator, flash active.** The usual middle ground: a meaningful current drop, a wake time still measured in single-digit microseconds, and no flash-wake penalty because flash never powered down. This is the default choice for a design that wakes often (milliseconds to low seconds) and needs to get back to work quickly each time.
- **Low-power regulator, flash powered down (`FPDS=1`).** The deepest current a Stop mode reaches on this part, at the cost of the largest Stop wake latency. This is [Clock and Peripheral Gating](./clock-and-peripheral-gating.md)'s "run fast, then sleep deep" strategy taken to its floor — correct when the sleep interval is long relative to the wake cost, wrong when it is not.

Standby is a different category of decision entirely, not a deeper point on the same slider: it is for intervals where nothing in RAM needs to survive, because a reset on wake is acceptable — a device that samples once an hour and re-derives all of its working state from the RTC backup registers and non-volatile storage each time, for example. Reaching for Standby because "it has the lowest number in the table" without checking that the reset-on-wake behaviour is tolerable is the most common design mistake this mode invites.

## What actually enters a mode

```c title="low_power.c — the three modes as CMSIS + PWR bit operations"
#include "stm32f4xx.h"

void enter_sleep(void)
{
    SCB->SCR &= ~SCB_SCR_SLEEPDEEP_Msk;   /* Sleep: shallow */
    __WFI();                              /* wakes on the next interrupt */
}

void enter_stop_lp_flash_off(void)
{
    PWR->CR |= PWR_CR_LPDS | PWR_CR_FPDS; /* low-power regulator, flash off */
    PWR->CR &= ~PWR_CR_PDDS;              /* PDDS = 0 selects Stop, not Standby */
    SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk;
    __WFI();
    /* Execution resumes here. SYSCLK is HSI again — the PLL did not
       survive Stop and must be reconfigured before anything timing-
       sensitive runs. See Configuring the Clock Tree. */
}

void enter_standby(void)
{
    PWR->CR |= PWR_CR_PDDS;               /* PDDS = 1 selects Standby */
    PWR->CR |= PWR_CR_CWUF;               /* clear any stale wake-up flag first */
    SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk;
    __WFI();
    /* Execution does NOT resume here. On wake, the core restarts from
       the reset vector; check PWR_CSR.SBF at startup to detect it. */
}
```

`PWR_CR.CWUF` matters more than its one-line comment suggests: `PWR_CSR.WUF` sets the instant a wake event occurs and is **not** cleared by entering or leaving a low-power mode. Enter Standby with a stale `WUF` already set from an earlier, already-handled event and the chip wakes immediately — sometimes before `WFI` has even finished retiring, which looks indistinguishable from Standby simply not working.

## See also

- [Energy Budgets](./energy-budgets.md) — turning the Stop-mode current above into an actual battery lifetime, with the arithmetic worked through.
- [Clock and Peripheral Gating](./clock-and-peripheral-gating.md) — why "run fast, then enter the deepest Stop variant" usually beats running slowly the whole time, worked as energy rather than current.
- [Wake Sources and Event-Driven Design](./wake-sources-and-event-driven-design.md) — the architectural half of this page: which sources can wake which mode, and structuring firmware so sleep is the default state rather than an afterthought.
- [SysTick and the Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md) — `SCR.SLEEPONEXIT`, the mechanism that turns an interrupt-driven main loop into one that re-enters Sleep automatically.
- [Watchdogs](../05-peripherals-and-drivers/watchdogs.md) — the IWDG behaviour this page's warning is built on, and the `DBGMCU` freeze bits that make it invisible during debugging.

:::warning[The Stop mode that resets the board, twice over]
Two independent mechanisms turn "the chip went to sleep" into "the chip reset," and both look identical from outside a debugger: the board goes dark, comes back a while later, and every peripheral is back at its power-on default.

**The IWDG keeps counting through Stop and Standby.** It is deliberately immune to almost everything, including the low-power modes — [Watchdogs](../05-peripherals-and-drivers/watchdogs.md) documents this in its Stop/Standby row, and it is not a bug, it is the watchdog doing its job. If firmware enters a Stop mode intended to last longer than the configured IWDG timeout without refreshing it first, the watchdog fires *during* the intended sleep and the chip resets rather than waking on schedule. The symptom is a device that appears to work — it does come back, it does resume its loop — but never actually reaches the deep-sleep current the datasheet promises, because it is quietly reset-cycling every few seconds instead of sleeping for the interval the code asked for. Check `RCC_CSR.WDGRSTF` on boot; if it is set on every cycle, the watchdog, not the wake source, is what is waking the board.

**The `nRST_STDBY` / `nRST_STOP` option bytes force a reset instead of entering the mode at all.** These are FLASH option bits, not runtime registers — factory or programmer-tool default in some toolchains sets one of them such that *attempting* to enter Stop or Standby generates a system reset immediately, before the mode is ever really entered. Code that correctly sets `PDDS`, `LPDS`, and `SLEEPDEEP` and then calls `__WFI()` simply reboots on the spot, with no fault, no hang, and every symptom of a brown-out. `RCC_CSR.LPWRRSTF` — "low-power management reset" — is the tell: read it immediately after boot, before anything clears `RMVF`, and its presence means the option bytes, not the sleep code, are the actual problem.
:::

:::note[Part-specificity: this is not "the STM32 low-power modes," it is the F411's]
Sleep, Stop, and Standby are the complete set on the STM32F411. Several other STM32 families add a fourth, deeper mode called **Shutdown** — the STM32L4, L5, U5, and G0 series among them — which powers off the backup domain's regulator too and typically reaches tens of nanoamps at the cost of losing the RTC and backup registers as well. The F411 does not implement Shutdown; code, application notes, or vendor examples written for an L4 that reference it do not apply here, and `PWR_CR` on those parts has bit layouts and additional fields (`ULP`, `SHDN`) that RM0383 does not define at all. Current figures are equally part-specific: a different die, package, or process node changes every number in the table above, sometimes by an order of magnitude, even within the F4 family.
:::

## References

- STMicroelectronics — [**RM0383**, *STM32F411xC/E advanced Arm-based 32-bit MCUs reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at Rev 2 (DocID026448). Chapter 5, "Power controller (PWR)," for the Sleep/Stop/Standby procedures and the `PWR_CR`/`PWR_CSR` bit definitions (`LPDS`, `PDDS`, `FPDS`, `CWUF`, `WUF`, `SBF`, `EWUP`); §5.1.2 for the backup domain that Standby leaves powered; §6.3.18 for `RCC_CSR` and the `LPWRRSTF`/`WDGRSTF` reset-cause flags used in the warning above.
- STMicroelectronics — [**STM32F411xC/STM32F411xE datasheet**](https://www.st.com/resource/en/datasheet/stm32f411re.pdf) (DS10314). The Stop-mode and Standby-mode current-consumption tables this page's figures are corroborated against, each parameterised by supply voltage, temperature, and regulator/flash configuration — read the exact row for your design rather than the typical figures quoted here. (This page's figures were cross-checked against secondary sources quoting this datasheet, not read from a fetched copy of the PDF; verify the primary table directly before committing to a design.)
- Arm — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), Rev 10. §4.4.5 for `SCB->SCR`, `SLEEPDEEP`, `SLEEPONEXIT`, and `SEVONPEND`; §2.4.4 for the `WFI`/`WFE` instruction forms this whole page is built on.
- STMicroelectronics — [**AN4365**, *Using STM32F4 MCU power modes with best dynamic efficiency*](https://www.st.com/resource/en/application_note/an4365-using-stm32f4-mcu-power-modes-with-best-dynamic-efficiency-stmicroelectronics.pdf). The application-level companion: worked comparisons across the F4 family of exactly the Stop-variant trade-offs described above, and measured wake-time numbers for a representative board.
