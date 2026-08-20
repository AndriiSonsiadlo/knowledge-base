---
id: systick-and-core-peripherals
title: SysTick and the Core Peripherals
sidebar_label: SysTick and the Core Peripherals
sidebar_position: 8
tags: [embedded, cortex-m, arm, systick, debug, timing, stm32]
---

# SysTick and the Core Peripherals

Almost everything on a microcontroller is the vendor's. The timers, the UARTs, the clock tree, the GPIO blocks — all of it is ST's design, at ST's addresses, described in ST's reference manual, and none of it transfers to a part from a different vendor. A handful of peripherals are not like that. They are **Arm's**, they are built into the processor itself, they sit at the same addresses on every Cortex-M ever made, and code that uses them ports between vendors without changes.

There are four worth knowing, and they cover a surprising amount of ground:

- **SysTick** — a 24-bit down-counter with an interrupt. The portable timebase every RTOS uses.
- **The SCB** (System Control Block) — the processor's own control panel: `VTOR`, `AIRCR`, the fault status registers, `CPUID`.
- **The DWT** (Data Watchpoint and Trace) — whose cycle counter gives you a free, exact, zero-overhead profiler.
- **The ITM** (Instrumentation Trace Macrocell) — a `printf` that costs a few cycles instead of a few hundred microseconds.

The last two are the ones people do not know they have. A cycle-accurate stopwatch and a low-cost trace channel are sitting in every Cortex-M4 you own, and neither requires a vendor library.

:::info[Prerequisites]
[The Cortex-M Memory Map](./memory-map-and-bit-banding.md) covers the Private Peripheral Bus these all live in, and the word-access rule that governs them. [The NVIC](./the-nvic.md) covers the other resident of the System Control Space.
:::

## Where they live

| Block | Base address | Owner | What it is for |
|---|---|---|---|
| ITM | `0xE000_0000` | Arm | Instrumentation trace — `printf`-style output over SWO. |
| DWT | `0xE000_1000` | Arm | Cycle counter, watchpoints, event counters. |
| SysTick | `0xE000_E010` | Arm | The 24-bit system timer. |
| NVIC | `0xE000_E100` | Arm | Interrupt controller — see [The NVIC](./the-nvic.md). |
| SCB | `0xE000_ED00` | Arm | `CPUID`, `ICSR`, `VTOR`, `AIRCR`, `SCR`, `CCR`, `SHPR`, `SHCSR`, fault status. |
| MPU | `0xE000_ED90` | Arm | Region-based protection — see [The Memory Protection Unit](./the-mpu.md). |
| CoreDebug | `0xE000_EDF0` | Arm | `DHCSR`, `DEMCR` — including the `TRCENA` bit the DWT and ITM need. |
| TPIU | `0xE004_0000` | Arm | Trace port / SWO output stage. |
| ROM table | `0xE00F_F000` | Arm | Identifies which of the above are actually present. |

Addresses are *Armv7-M ARM* DDI 0403E.e §B3.1 (System Control Space) and Appendix C1 (debug components). The point of the table is not the numbers — CMSIS gives you `SysTick->`, `SCB->`, `DWT->`, `ITM->` — but the fact that they are *fixed*. A driver written against `SysTick->LOAD` compiles for an STM32, a Nordic nRF52, an NXP LPC and a Raspberry Pi RP2040 without an `#ifdef`.

## SysTick

A 24-bit counter that decrements once per clock, reloads from `STK_LOAD` when it reaches zero, and optionally raises exception 15. That is the whole peripheral. It exists so an operating system has a timer it can rely on without knowing anything about the chip it is running on.

```wavedrom title="STK_CTRL — the SysTick control and status register" alt="Bit-field strip of the SysTick control and status register showing ENABLE, TICKINT, CLKSOURCE and COUNTFLAG"
{ reg: [
    { bits: 1, name: "ENABLE", type: 2 },
    { bits: 1, name: "TICKINT", type: 2 },
    { bits: 1, name: "CLKSOURCE", type: 4 },
    { bits: 13, name: "reserved", type: 1 },
    { bits: 1, name: "COUNTFLAG", type: 3 },
    { bits: 15, name: "reserved", type: 1 }
  ],
  config: { bits: 32, hspace: 1000, lanes: 2 }
}
```

| Bits | Field | Reset | Meaning |
|---|---|---|---|
| 0 | `ENABLE` | `0` | Start the counter. |
| 1 | `TICKINT` | `0` | Raise the SysTick exception when the counter reaches zero. Independent of `ENABLE` — the counter can run without interrupting. |
| 2 | `CLKSOURCE` | `0` | `1` = processor clock (`AHB`); `0` = the external reference clock, which on the STM32F4 family is **`AHB/8`**. |
| 15:3 | — | `0` | Reserved. |
| 16 | `COUNTFLAG` | `0` | Set when the counter reaches zero. **Cleared by reading this register** — or by writing `STK_VAL`. |
| 31:17 | — | `0` | Reserved. |

Field definitions are PM0214 Rev 10 §4.5 ("SysTick timer (STK)"); the `AHB/8` meaning of `CLKSOURCE = 0` on this family is RM0383 Rev 4 §10.1 and the clock-tree figure in §6.2.

The other three registers are `STK_LOAD` (24-bit reload value), `STK_VAL` (24-bit current value, write-any-value-to-clear) and `STK_CALIB` (a calibration hint, discussed below).

```c
/* A 1 ms tick at 100 MHz HCLK. PM0214 Rev 10, section 4.5. */
SysTick->LOAD = (100000000u / 1000u) - 1u;   /* N-1 for a period of N cycles */
SysTick->VAL  = 0u;                          /* clears the counter and COUNTFLAG */
SysTick->CTRL = SysTick_CTRL_CLKSOURCE_Msk   /* processor clock, not AHB/8      */
              | SysTick_CTRL_TICKINT_Msk
              | SysTick_CTRL_ENABLE_Msk;
```

Four behaviours that are easy to get wrong:

**The reload value is N−1.** The counter counts *through* zero, so a reload of `N-1` produces a period of `N` clocks. Writing `100000` rather than `99999` gives a tick that is one part in 100,000 slow — invisible on an oscilloscope, and about 8.6 seconds of drift per day.

**Writing `STK_VAL` does not raise the interrupt.** It clears the counter and `COUNTFLAG`; the exception logic is untouched. This is the documented way to restart the timer cleanly.

**`COUNTFLAG` is cleared by reading `STK_CTRL`.** Two pieces of code that both poll it will steal ticks from each other, and a debugger watch window that displays `SysTick->CTRL` will steal them from both. For anything other than a dead-simple polled delay, use the interrupt.

**24 bits is not many.** The maximum reload is `0x00FF_FFFF` = 16,777,215, so at 100 MHz the longest period SysTick can produce is about **168 ms**. There is no way to configure a one-second SysTick on this part at full speed — you count ticks in software, or select `AHB/8` and get about 1.34 s, at the cost of eight times coarser resolution. A tick of 1 ms is the near-universal choice, and it is a compromise between interrupt overhead and timing granularity, not a law.

`STK_CALIB` deserves a specific caution. Architecturally its `TENMS` field is meant to hold the reload value for a 10 ms interval, with `SKEW` and `NOREF` flags describing how trustworthy it is — and the *Armv7-M ARM* (§B3.3, `SYST_CALIB`) states that if `TENMS` reads as zero, the calibration value is not known. On STM32 parts the field is a fixed value tied to an assumed clock configuration that is very unlikely to be yours. Do not derive a tick from it. Derive it from the clock you configured, which you know, ideally through the CMSIS `SystemCoreClock` variable that your clock setup code updates.

One more scoping note: SysTick is clocked from the core clock domain, so it stops in the deeper low-power modes. Firmware that sleeps aggressively cannot use it as a wall clock and needs an always-on RTC or a low-power timer instead — a topic the low-power material later in this section covers.

## The System Control Block

The SCB is the processor's control panel. Most of it is documented elsewhere in this folder; this is the index.

| Register | Offset from `0xE000_ED00` | What you use it for | Covered in |
|---|---|---|---|
| `CPUID` | `0x00` | Identify the core at runtime — part number, revision. | — |
| `ICSR` | `0x04` | Set/clear `PendSV` and SysTick pending; read `VECTACTIVE`. | [Exceptions](./exceptions-and-the-vector-table.md) |
| `VTOR` | `0x08` | Relocate the vector table. | [Exceptions](./exceptions-and-the-vector-table.md) |
| `AIRCR` | `0x0C` | Priority grouping; **`SYSRESETREQ`** for a software reset. | [The NVIC](./the-nvic.md) |
| `SCR` | `0x10` | `SLEEPONEXIT`, `SLEEPDEEP`, `SEVONPEND`. | — |
| `CCR` | `0x14` | `STKALIGN`, `DIV_0_TRP`, `UNALIGN_TRP`, `USERSETMPEND`. | [The Register Model](./cortex-m-register-model.md) |
| `SHPR1`–`SHPR3` | `0x18`–`0x20` | Priorities of the system exceptions (MemManage … SysTick). | [The NVIC](./the-nvic.md) |
| `SHCSR` | `0x24` | Enable MemManage / BusFault / UsageFault handlers. | [Exceptions](./exceptions-and-the-vector-table.md) |
| `CFSR`, `HFSR` | `0x28`, `0x2C` | Fault status — what actually went wrong. | [Exceptions](./exceptions-and-the-vector-table.md) |
| `MMFAR`, `BFAR` | `0x34`, `0x38` | The faulting address, when the status register says it is valid. | [The Memory Protection Unit](./the-mpu.md) |
| `CPACR` | `0x88` | Enable coprocessors 10 and 11 — i.e. the FPU. | [Floating Point and DSP](./floating-point-and-dsp.md) |

Offsets are PM0214 Rev 10 §4.4 and its SCB register map. Two entries earn a mention here because nothing else in this folder covers them:

**`AIRCR.SYSRESETREQ` is how firmware reboots itself.** CMSIS wraps it as `NVIC_SystemReset()`, which sets the bit along with the `0x5FA` write key and then spins. Worth knowing that it requests a *system* reset from the vendor's reset controller — on most STM32 parts that is a full reset of everything except the debug logic and the backup domain, but the exact scope is the vendor's choice, not Arm's.

**`SCR.SLEEPONEXIT` is the single best power win in interrupt-driven firmware.** Set it, and the processor returns to sleep automatically when the last handler exits instead of returning to a `while (1)` loop that immediately calls `WFI`. The main loop becomes genuinely empty and the core is awake only inside handlers.

## The DWT cycle counter

The DWT's `CYCCNT` is a free-running 32-bit counter that increments once per core clock. It is the most useful debugging facility on the chip that most people never enable.

```c
/* Enable once, early. Armv7-M ARM DDI 0403E.e, appendix C1. */
CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;   /* powers up the trace block */
DWT->CYCCNT = 0u;
DWT->CTRL  |= DWT_CTRL_CYCCNTENA_Msk;

/* Then, anywhere: */
uint32_t t0 = DWT->CYCCNT;
do_the_thing();
uint32_t elapsed = DWT->CYCCNT - t0;    /* exact, in core clocks */
```

The properties that make it worth the six lines:

- **Exact, not sampled.** It counts clocks, so the answer is the number of cycles the code took, including cache and wait-state effects. This is how you settle "is this function actually slow" arguments and how the cycle counts on [Floating Point and DSP Extensions](./floating-point-and-dsp.md) get measured on your own hardware.
- **Free to read.** One load from the PPB. No function call into a HAL, no timer to allocate.
- **Wraparound is a non-issue if you subtract.** The counter wraps every 2³² cycles — about 43 seconds at 100 MHz. Unsigned subtraction `now - then` gives the correct interval across a single wrap, which covers every measurement short enough to be interesting.

Two caveats. `TRCENA` must be set first; without it the DWT registers are inert and `CYCCNT` stays at zero, which reads as "my code takes no time". And the cycle counter is **optional**: `DWT->CTRL` bit 25 (`NOCYCCNT`) reads 1 when it is absent, which is the case on many Armv6-M parts (Cortex-M0, and M0+ implementations with the minimal DWT). Check it before relying on it in portable code.

## The ITM

The ITM is a set of 32 stimulus ports. Writing a byte or word to a port pushes it into a trace FIFO, which the TPIU serialises out of the SWO pin (`PB3` on the STM32F4, shared with `JTDO`), where the debug probe collects it. A write is a store to a PPB address — a handful of cycles — versus the hundreds of microseconds a `printf` over a 115200-baud UART costs.

```c
/* ITM port 0, the port every debugger's "SWV console" listens on. */
if ((ITM->TCR & ITM_TCR_ITMENA_Msk) && (ITM->TER & 1u)) {
    while (ITM->PORT[0].u32 == 0u) { /* FIFO full, wait */ }
    ITM->PORT[0].u8 = (uint8_t)c;
}
```

Bringing it up needs, in order: `DEMCR.TRCENA` set; the lock register at offset `0xFB0` unlocked by writing `0xC5ACCE55`; `ITM_TCR.ITMENA` set with a trace bus ID; the port enabled in `ITM_TER`; and the TPIU configured for the right SWO encoding and baud rate. In practice the debugger does most of that when you enable SWV in its trace configuration — which is why ITM output usually "just works" from the IDE and needs a page of setup code when you try to bring it up yourself.

The guard in that snippet is not optional, and the reason is in the warning below.

:::warning[Two ways the debug peripherals stop the firmware they were meant to instrument]
**An unguarded ITM write hangs the board when no debugger is attached.** The idiom `while (ITM->PORT[0].u32 == 0);` waits for FIFO space. With a probe connected the FIFO drains and the loop exits after a few cycles. With no probe — on the bench, in the field, in the customer's hands — the TPIU never drains it, the FIFO stays full, and the loop never exits. The result is firmware that works perfectly under the debugger and hangs on power-up, which is the single most demoralising failure mode in embedded development because the tool you would use to investigate it makes it disappear. Always test `TCR.ITMENA` and the `TER` bit first, as above: both are zero when trace was never enabled, so the write is skipped entirely.

**`COUNTFLAG` disappearing into a debugger watch window.** A polled `while (!(SysTick->CTRL & SysTick_CTRL_COUNTFLAG_Msk));` delay works until you add `SysTick->CTRL` to the live watch view. The debugger's periodic read clears the flag, your loop misses it, and the delay becomes 168 ms instead of 1 ms — sometimes. The behaviour changes depending on whether a window is open, which is exactly the property that makes a bug take a day. The same trap exists for any read-to-clear status bit on the chip; SysTick is just the one that catches people first.

And a smaller one worth pre-empting: **`DWT->CYCCNT` reading zero forever** almost always means `DEMCR.TRCENA` was never set. It is a silent no-op, not an error, and the resulting "this function takes 0 cycles" is a measurement people have been known to believe for an hour.
:::

## See also

- [The NVIC](./the-nvic.md) — the other System Control Space resident, and the `AIRCR` and `SHPR` registers listed above.
- [The Cortex-M Memory Map](./memory-map-and-bit-banding.md) — why everything on this page is at a fixed address, and the PPB access rules.
- [Exceptions and the Vector Table](./exceptions-and-the-vector-table.md) — SysTick as exception 15, and the SCB fault registers this page only indexes.
- [Floating Point and DSP Extensions](./floating-point-and-dsp.md) — the cycle counts the DWT counter is the right way to verify on your own board.
- [Clocks and Oscillators](../01-hardware-foundations/clocks-and-oscillators.md) — where the `AHB` clock that SysTick divides comes from, and why `SystemCoreClock` has to be kept honest.

## References

- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), consulted at **Rev 10** (March 2020). §4.5 "SysTick timer (STK)" for `STK_CTRL`, `STK_LOAD`, `STK_VAL` and `STK_CALIB` field definitions and reset values; §4.4 "System control block (SCB)" and its register map for every SCB offset in the table above, including `SCR.SLEEPONEXIT` and `AIRCR.SYSRESETREQ`; §4.1 for the list of which core peripherals this device implements.
- Arm — [***Armv7-M Architecture Reference Manual***](https://developer.arm.com/documentation/ddi0403/latest/), consulted at **DDI 0403E.e (ID021621)**. §B3.1 for the System Control Space layout and the fixed base addresses; §B3.3 "The system timer, SysTick" for the counter semantics, the reload-of-N−1 rule, the write-to-`SYST_CVR` behaviour and the `SYST_CALIB` `TENMS`/`SKEW`/`NOREF` definition including the "calibration value is not known" case; **Appendix C1** "Debug" for the DWT and ITM register maps, `DEMCR.TRCENA`, `DWT_CTRL.NOCYCCNT` and the ITM lock-access key.
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). §10.1 for the SysTick external reference clock being `AHB/8` on this family; §6.2 for the clock tree that produces `HCLK`; §7.3 for the `PB3` / `JTDO-TRACESWO` pin assignment used for SWO output.
- Arm — **CMSIS-Core(M)**, `core_cm4.h`. The `SysTick_Type`, `SCB_Type`, `DWT_Type` and `ITM_Type` structures and the `SysTick_Config()` and `NVIC_SystemReset()` helpers. `SysTick_Config()` is worth reading once: it writes `LOAD` with `ticks - 1`, sets the SysTick priority to the lowest configurable value, and returns non-zero if the requested reload does not fit in 24 bits.
