---
id: software-timers-and-delays
title: Software Timers and Delays
sidebar_label: Software Timers and Delays
sidebar_position: 9
tags: [embedded, rtos, freertos, timers, delays, tick, jitter, drift]
---

# Software Timers and Delays

There are three clocks in a system running an RTOS and it is worth separating them before writing a single delay. There is the **hardware timer**, counting a crystal-derived clock in silicon, which does not know or care what software is doing. There is the **tick**, a periodic interrupt that increments a counter and is the only time the kernel can see. And there is the **task's own experience of time**, which is the tick as filtered through whether that task was actually running when something expired.

The mental model, and the source of nearly every timing complaint in a first RTOS project: **only the first of those three is a guarantee.** The tick is a quantised approximation of real time. A task's view is the tick plus an unbounded queue of higher-priority work that ran instead of it. A delay is therefore a statement about a *minimum*, never about a period, and never about a deadline.

Within that, one distinction does more damage than all the others. `vTaskDelay(n)` computes its wake time from the tick count *at the moment the call executes*. Everything that happened between the previous wake and that call — the task's own work, and every pre-emption it suffered — has already been spent, and the delay is added on top of it. The period is not `n`; it is `n` plus whatever that was. `xTaskDelayUntil()` computes its wake time from a stored value instead, and the accumulated error is exactly zero forever.

:::info[Prerequisites]
[Tasks and Scheduling](./tasks-and-scheduling.md) owns the tick itself — `xTaskIncrementTick()`, the delayed lists, `xNextTaskUnblockTime`, and the trade-off in choosing `configTICK_RATE_HZ`. This page is what application code should do with it. [Timers and Counters](../05-peripherals-and-drivers/timers-and-counters.md) owns the hardware timers that the last section of this page redirects you to.
:::

## The drift, concretely

Take a task that wants to run every 10 ms on a 1000 Hz tick, and that does 2 ms of work each time.

```wavedrom title="One character is 2 ms; the coloured pulse is the task running. Both loops ask for a 10 ms period. The vTaskDelay loop achieves 12 ms and has lost a whole period by the fifth activation; the xTaskDelayUntil loop stays locked to the grid" alt="Three waveforms over 60 milliseconds. The top trace marks the intended 10 millisecond deadlines. The middle trace, labelled vTaskDelay, shows the task running once every 12 milliseconds so its pulses drift steadily to the right of the grid. The bottom trace, labelled xTaskDelayUntil, shows pulses that stay aligned with every grid mark"
{ "signal": [
  { "name": "10 ms grid",      "wave": "10...10...10...10...10...10..." },
  {},
  { "name": "vTaskDelay",      "wave": "30....30....30....30....30...." },
  { "name": "xTaskDelayUntil", "wave": "30...30...30...30...30...30..." }
], "config": { "hscale": 1 } }
```

*Derived from the stated 2 ms execution time, not measured.*

The arithmetic, with one cycle disturbed by a 3 ms pre-emption to show that the error never recovers:

| Cycle | Work + pre-emption before the delay call | `vTaskDelay(10)` wakes at | `xTaskDelayUntil(&prev, 10)` wakes at |
|---|---|---|---|
| 1 | 2 ms | 12 ms | 10 ms |
| 2 | 2 ms | 24 ms | 20 ms |
| 3 | **5 ms** (3 ms of pre-emption) | 39 ms | 30 ms |
| 4 | 2 ms | 51 ms | 40 ms |
| 5 | 2 ms | 63 ms | 50 ms |

*Derived arithmetic from the model above, not a measurement.*

Two things to take from the table. The steady-state error is **2 ms per cycle**, which is a period of 12 ms rather than 10 — an activation rate of 1000/12 ≈ 83 Hz where 100 Hz was intended, a 17 % error that no amount of testing will make go away. And the one-off 3 ms disturbance in cycle 3 is *added permanently* to the phase: the `vTaskDelay` column never catches up, while the `xTaskDelayUntil` column absorbs it completely and cycle 4 is back on the grid.

In real firmware the extra term is not a constant. It is execution time plus pre-emption, both of which vary with load, so the period jitters as well as drifts — a sample interval that is 12 ms on an idle system and 19 ms while the radio is transmitting.

## `xTaskDelayUntil`, and the return value that is an overrun detector

```c
void sample_task(void *arg)
{
    const TickType_t period = pdMS_TO_TICKS(10);
    TickType_t last = xTaskGetTickCount();      /* ONCE, before the loop */

    for (;;) {
        if (xTaskDelayUntil(&last, period) == pdFALSE) {
            overruns++;                          /* we were already late */
        }
        read_sensor();
        process();
    }
}
```

The kernel updates `last` to the *computed* wake time — `last + period` — not to the time the task actually resumed. That is the whole mechanism: the phase reference is arithmetic, so jitter in one cycle cannot leak into the next.

Three consequences worth having in your head:

- **`last` is initialised once and then owned by the kernel.** Assigning `last = xTaskGetTickCount()` inside the loop turns `xTaskDelayUntil` back into `vTaskDelay` while looking like it did not.
- **`xTaskDelayUntil()` returns `pdFALSE` when the deadline was already in the past**, and in that case it does not block at all. That return value, counted as above, is the cheapest deadline-overrun detector in the system — it is a direct measurement of the thing [Scheduling Theory for Firmware](../06-interrupts-timing-and-real-time/scheduling-theory.md) computes on paper. `vTaskDelayUntil()` is the older, functionally identical function with no return value; `xTaskDelayUntil()` was added in kernel V10.4.2 specifically to expose it. Use the `x` form in new code.
- **After an overrun the task runs back-to-back** until it catches up, because each call advances `last` by one period regardless. A task that persistently overruns therefore consumes the core continuously rather than degrading gracefully, which is another reason to count the `pdFALSE` returns rather than ignoring them.

`vTaskDelay(n)` remains correct for what it is: "sleep for at least n ticks from now". Poll intervals, retry back-offs, debounce settling, a watchdog service loop that does not need a stable phase. The rule is simply that if the interval is a *period*, it is the wrong call.

## Tick quantisation, and the conversion that silently returns zero

`pdMS_TO_TICKS(ms)` is `ms × configTICK_RATE_HZ / 1000` in integer arithmetic, and integer arithmetic truncates. At the common 1000 Hz tick that is harmless — 1 ms is 1 tick. At 100 Hz, chosen for power reasons, `pdMS_TO_TICKS(1)` evaluates to **0**, and `vTaskDelay(0)` does not block at all: it yields. A retry loop written as `vTaskDelay(pdMS_TO_TICKS(1))` becomes a busy-wait that starves every equal-priority task, and it does so only on the low-tick-rate build.

The quantisation that survives the conversion is the other half. [Tasks and Scheduling](./tasks-and-scheduling.md) states it precisely: a wake is aligned to the tick, so `vTaskDelay(1)` is anything from just over zero to one full tick, and the task then runs whenever the scheduler gets to it. Every delay is a lower bound with an open upper bound.

## Never use a delay for a hardware timing requirement

This deserves to be stated as a rule with no exceptions, because the failures it prevents are the expensive kind.

- **Sub-tick timing is not expressible.** A 20 µs reset pulse, an I2C bus-recovery clock, a bit-banged one-wire slot — none of these can be written with a delay at any tick rate you would actually run.
- **Supra-tick timing is a minimum, not a bound.** "Wait 5 ms for the display controller to come out of reset" written as `vTaskDelay(pdMS_TO_TICKS(5))` waits *at least* 5 ms, and on a loaded system may wait 40. That direction is usually safe. The reverse — "assert this line for exactly 5 ms" — is not expressible at all, and the code that appears to do it works on the bench and fails in the field.
- **The tick can stop.** Under `configUSE_TICKLESS_IDLE` the kernel suppresses ticks and corrects the count on wake. Timing derived from it stays consistent; timing measured against the outside world does not.

What to use instead, in order of preference: a **hardware timer** in output-compare or one-pulse mode ([Timers and Counters](../05-peripherals-and-drivers/timers-and-counters.md)), which produces the edge in silicon with no software in the path; **PWM** for anything repetitive ([PWM](../05-peripherals-and-drivers/pwm.md)); the **DWT cycle counter** for a short, calibrated busy-wait where an edge must be produced from code; and the **RTC** for wall-clock intervals that must survive sleep ([RTC and Timekeeping](../05-peripherals-and-drivers/rtc-and-timekeeping.md)). The tick's own hardware — SysTick, PM0214 §4.5 — belongs to the kernel and should not be borrowed.

## Software timers and the daemon task

A software timer is not a timer. It is a callback that the kernel arranges to be executed by an ordinary task, at a tick it has calculated. `configUSE_TIMERS` defaults to **0**; setting it to 1 makes `vTaskStartScheduler()` create the timer service task — the "daemon" — alongside the idle task.

```c
/* FreeRTOSConfig.h
     #define configUSE_TIMERS             1
     #define configTIMER_TASK_PRIORITY    ( configMAX_PRIORITIES - 1 )
     #define configTIMER_QUEUE_LENGTH     10
     #define configTIMER_TASK_STACK_DEPTH configMINIMAL_STACK_SIZE * 2   */

static void link_timeout_cb(TimerHandle_t t)
{
    /* Runs in the DAEMON's context. Never blocks. Never delays.
       pvTimerGetTimerID lets one callback serve many timers. */
    cmd_t msg = { .kind = CMD_LINK_DOWN,
                  .link = (uint32_t)(uintptr_t)pvTimerGetTimerID(t) };
    (void) xQueueSend(cmd_q, &msg, 0);   /* post and return; do not do work here */
}

TimerHandle_t t = xTimerCreate("link", pdMS_TO_TICKS(3000),
                               pdFALSE,                 /* xAutoReload: one-shot */
                               (void *)(uintptr_t)1,    /* pvTimerID              */
                               link_timeout_cb);
configASSERT(t != NULL);
if (xTimerStart(t, pdMS_TO_TICKS(10)) != pdPASS) {
    /* the timer command queue was full for 10 ms — this can happen */
}
```

Four properties of that arrangement decide whether software timers are a good fit for a given job.

**Commands are queued, not executed.** `xTimerStart()`, `xTimerStop()`, `xTimerReset()`, `xTimerChangePeriod()` and `xTimerDelete()` all post a message to the timer command queue and return. They do not touch the timer list themselves. So each takes a block time for space in that queue and each can return `pdFAIL` when `configTIMER_QUEUE_LENGTH` is exhausted — a return value that application code almost never checks and that goes wrong exactly when a burst of events restarts a lot of timers at once. Commands issued before `vTaskStartScheduler()` are legal; they sit in the queue and take effect when the daemon first runs.

**`configTIMER_TASK_PRIORITY` decides when callbacks actually run.** The daemon is a task and is scheduled like one. Set it below your application tasks and a 10 ms timer whose expiry lands during a busy period fires whenever the core next becomes free — the timer is accurate, the *callback* is late, and the lateness scales with load. Set it above them and a slow callback pre-empts real work, which is the same problem with the sign reversed. The default position is to put the daemon near the top and keep every callback to a handful of instructions, because a short high-priority callback perturbs less than a long low-priority one delays.

**Callbacks run in the daemon's context and must not block.** There is one daemon serving every timer in the system, so a callback that calls `vTaskDelay()`, or `xQueueReceive()` with a non-zero timeout, or takes a mutex that is held, stops *every other timer in the system* for the duration. This is also why the daemon's stack (`configTIMER_TASK_STACK_DEPTH`) has to cover the deepest callback you write, not the shallowest.

**Auto-reload timers do not skip.** With `xAutoReload` set to `pdTRUE` the timer restarts itself on expiry. Since kernel V10.4.4, an auto-reload timer whose execution time was missed — because the daemon could not run — executes immediately rather than waiting for the next period, so missed expiries surface as bunched callbacks rather than as silently dropped ones. `xTimerGetAutoReload()` returns the flag as a `BaseType_t`; the older `uxTimerGetAutoReload()` returning `UBaseType_t` is retained for compatibility.

One further use of the daemon is worth knowing because other parts of the kernel rely on it: `xTimerPendFunctionCall()` and `xTimerPendFunctionCallFromISR()` run an arbitrary function in the daemon's context. That is the standard way to move unbounded work out of an interrupt handler, and it is exactly what `xEventGroupSetBitsFromISR()` does internally (see [Notifications and Event Groups](./notifications-and-event-groups.md)) — which means that on a build with `configUSE_TIMERS` at 0, that ISR-safe event-group call does not exist.

:::note[Timer APIs are restricted on MPU ports]
On the Armv7-M and Armv8-M MPU ports, `MPU_xTimerCreate()`, `MPU_xTimerCreateStatic()` and `MPU_xTimerPendFunctionCall()` were removed from the unprivileged API surface, because a task able to register a callback with the daemon can run code in the daemon's privilege context. If you are moving a design to an MPU-protected build, timer creation is one of the things that has to move to privileged start-up code.
:::

:::warning[The 100 Hz loop that samples at 83 Hz, and the timer callback that stopped every other timer]
Two failures that are visible on a scope in ten seconds and invisible in code review for months.

**The drifting sample loop.** A 100 Hz sensor loop written with `vTaskDelay(pdMS_TO_TICKS(10))`, doing 2 ms of work, actually runs at about 83 Hz — the arithmetic is in the table above. Nothing reports an error, because nothing in the system knows what rate was intended. The consequence surfaces far downstream: an FFT whose bins are all 17 % off, a PID loop whose derivative gain is wrong by the same factor and which was then retuned by hand to compensate, a data logger whose timestamps are generated by counting samples and which disagrees with the RTC by a minute an hour. Retuning the controller is what makes this permanent — the defect gets absorbed into a magic constant and stops being findable. Two tells, both cheap: toggle a GPIO once per loop and measure the period on a scope, which is the ground truth and takes two minutes; or log `xTaskGetTickCount()` deltas and compare the mean against the period you asked for. The fix is `xTaskDelayUntil()`, and the check that it worked is that the `pdFALSE` return count stays at zero.

**The blocking timer callback.** A callback that logs over a UART using a blocking write, or takes a mutex the SPI task holds, runs in the daemon. While it waits, every other software timer in the system is not being serviced — the connection watchdog, the LED blink, the debounce timeout. The symptom is that several unrelated timed behaviours all become erratic together, and only under the load that makes the logging call block. Because the callbacks themselves are correct in isolation and the timers are correct in isolation, the fault looks like a kernel or hardware problem. The tell is decisive if you look for it: put a GPIO toggle at the entry and exit of every timer callback, or read the daemon task's stack high-water mark and its run-time counter from `uxTaskGetSystemState()` — a daemon consuming meaningful CPU, or Blocked on anything other than its own command queue, is the whole diagnosis. Callbacks post to a queue and return; the work happens in a task that is allowed to wait.
:::

## See also

- [Tasks and Scheduling](./tasks-and-scheduling.md) — the tick that everything here is quantised to, the delayed lists, and how to choose `configTICK_RATE_HZ`.
- [Notifications and Event Groups](./notifications-and-event-groups.md) — `xEventGroupSetBitsFromISR()`, which is implemented on top of the daemon task described above.
- [Timers and Counters](../05-peripherals-and-drivers/timers-and-counters.md) — the hardware that every hard timing requirement belongs on instead of a delay.
- [Scheduling Theory for Firmware](../06-interrupts-timing-and-real-time/scheduling-theory.md) — the response-time analysis that the `xTaskDelayUntil()` overrun counter measures empirically.
- [RTC and Timekeeping](../05-peripherals-and-drivers/rtc-and-timekeeping.md) — wall-clock time that survives sleep and reset, which no tick-derived value does.

## References

- Amazon Web Services — [**FreeRTOS: software timers**](https://www.freertos.org/Documentation/02-Kernel/02-Kernel-features/04-Software-timers/01-Software-timers) and the [**`xTimerCreate` API reference**](https://www.freertos.org/Documentation/02-Kernel/04-API-references/11-Software-timers/01-xTimerCreate). Verified against these: the `xTimerCreate(pcTimerName, xTimerPeriodInTicks, xAutoReload, pvTimerID, pxCallbackFunction)` signature; the timer service (daemon) task created by `vTaskStartScheduler()` when `configUSE_TIMERS` is 1; `configTIMER_TASK_PRIORITY`, `configTIMER_QUEUE_LENGTH` and `configTIMER_TASK_STACK_DEPTH`; the fact that `xTimerStart` and its siblings post to the timer command queue rather than acting directly, and can therefore fail; and the prohibition on blocking inside a callback. (Documentation checked 2026-08-26.)
- Amazon Web Services — [**FreeRTOS: `xTaskDelayUntil` API reference**](https://www.freertos.org/Documentation/02-Kernel/04-API-references/02-Task-control/02-vTaskDelayUntil) and [**`vTaskDelay`**](https://www.freertos.org/Documentation/02-Kernel/04-API-references/02-Task-control/01-vTaskDelay). The statement that `vTaskDelay()` specifies a time relative to the moment it is called while `xTaskDelayUntil()` specifies an absolute time derived from `pxPreviousWakeTime`, that the kernel updates `pxPreviousWakeTime` to the calculated wake time, and that `xTaskDelayUntil()` returns `pdFALSE` when the wake time was already in the past. (Documentation checked 2026-08-26.)
- FreeRTOS-Kernel — [**`History.txt`**](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/main/History.txt), [**`timers.c`**](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/main/timers.c) and [**`include/FreeRTOS.h`**](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/main/include/FreeRTOS.h). Confirmed from the changelog: `xTaskDelayUntil()` introduced in V10.4.2 as a returning equivalent of `vTaskDelayUntil()`; the V10.4.3-to-V10.4.4 change making auto-reload timers that miss their execution time run immediately; `uxAutoReload` renamed to `xAutoReload` with `xTimerGetAutoReload()` returning `BaseType_t`; and the removal of `MPU_xTimerCreate`, `MPU_xTimerCreateStatic` and `MPU_xTimerPendFunctionCall` from the MPU ports. `FreeRTOS.h` carries the `configUSE_TIMERS` default of 0 and the compile-time check that `configUSE_DAEMON_TASK_STARTUP_HOOK` cannot be set without it. (Source checked 2026-08-26.)
- Richard Barry and the FreeRTOS team — [***Mastering the FreeRTOS Real Time Kernel***](https://www.freertos.org/Documentation/02-Kernel/07-Books-and-manual/01-RTOS_book) (free PDF). Chapter 6, "Software Timer Management", covers one-shot versus auto-reload, the command queue and the daemon's priority; §3.13 works the `vTaskDelay` versus `vTaskDelayUntil` comparison with the same drift argument used above.
- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), Rev 10. §4.5 for the SysTick timer that generates the tick every delay here is quantised to, and the Data Watchpoint and Trace chapter for the `DWT->CYCCNT` cycle counter used for sub-tick busy-waits.
