---
id: isr-safe-apis
title: ISR-Safe APIs
sidebar_label: ISR-Safe APIs
sidebar_position: 11
tags: [embedded, rtos, freertos, cortex-m, interrupts, basepri, isr]
---

# ISR-Safe APIs

Every kernel object in the previous six pages — the ready lists, the delayed list, each queue's two event lists, each mutex's holder field — is an ordinary linked list in RAM, and the kernel keeps it consistent by the only means a single-core Cortex-M offers: it masks interrupts around the update. That is the entire content of `taskENTER_CRITICAL()`. So a kernel API is not "thread-safe code" in the hosted sense; it is code that assumes **nothing else on this core is running while it edits the list**.

Two facts follow, and both of them are this page.

The first is that an interrupt handler is not a task. It has no TCB, so it cannot be put on an event list, so it cannot block; and it runs at a priority the scheduler does not control, so it cannot be de-scheduled. The `FromISR` family exists because every blocking API needs a non-blocking twin for callers that have nothing to block. The second, and the one that costs people days: **the kernel's critical section is a `BASEPRI` threshold, not `PRIMASK`.** Interrupts more urgent than that threshold keep running *through* the kernel's list update. If one of them calls into the kernel, it edits a half-updated list, and the machine does not fault until much later and somewhere else entirely.

The threshold has a name — `configMAX_SYSCALL_INTERRUPT_PRIORITY` — and getting its value right is the single highest-value configuration decision in a FreeRTOS port.

:::info[Prerequisites]
[Critical Sections and Atomicity](../04-bare-metal-programming/critical-sections-and-atomicity.md) owns the `BASEPRI` mechanism and its pre-shift; [Priorities and Nesting](../06-interrupts-timing-and-real-time/interrupt-priorities-and-nesting.md) owns where to put the ceiling in your numbering scheme and what putting it there costs. This page is the FreeRTOS-specific rule that sits on top of both. [Semaphores and Mutexes](./synchronization-primitives.md) established *why a mutex has no ISR form at all* and deliberately left this ceiling to here. [Deferred Work](../06-interrupts-timing-and-real-time/deferred-work.md) is the design pattern every API below serves.
:::

## The `FromISR` family

The naming is mechanical, which is the point: if a function exists in both forms, you must use the right one, and the compiler will not help you.

| Task-context API | ISR-context API | Difference beyond the name |
|---|---|---|
| `xQueueSend()`, `xQueueSendToFront()` | `xQueueSendFromISR()`, `xQueueSendToFrontFromISR()` | no `xTicksToWait`; gains `pxHigherPriorityTaskWoken` |
| `xQueueReceive()` | `xQueueReceiveFromISR()` | same |
| `xQueuePeek()` | `xQueuePeekFromISR()` | **no** woken parameter — a peek cannot unblock anything |
| `xSemaphoreGive()`, `xSemaphoreTake()` | `xSemaphoreGiveFromISR()`, `xSemaphoreTakeFromISR()` | binary and counting only |
| `xSemaphoreGive()` on a **mutex** | *(none, and never will be)* | no task handle to write to `xMutexHolder`; see [Semaphores and Mutexes](./synchronization-primitives.md) |
| `xTaskNotifyGive()` | `vTaskNotifyGiveFromISR()` | note the `v` — it returns `void` |
| `xTaskNotify()` | `xTaskNotifyFromISR()` | plus the `Indexed` siblings of both |
| `xEventGroupSetBits()` | `xEventGroupSetBitsFromISR()` | **does not set the bits itself** — see below |
| `xTimerStart()`, `xTimerReset()` | `xTimerStartFromISR()`, `xTimerResetFromISR()` | commands the daemon rather than the timer |
| `xTaskGetTickCount()` | `xTaskGetTickCountFromISR()` | avoids a critical section that is unnecessary in a handler |
| `taskENTER_CRITICAL()` | `taskENTER_CRITICAL_FROM_ISR()` | **returns** a saved mask; the exit takes it back, because ISRs nest |
| `vTaskDelay()`, `vTaskDelayUntil()`, `vTaskSuspend()` | *(none — they block or de-schedule)* | there is nothing to delay |

Two entries earn a second look. `taskENTER_CRITICAL_FROM_ISR()` returns a value and `taskEXIT_CRITICAL_FROM_ISR( x )` consumes it, for exactly the reason [Critical Sections and Atomicity](../04-bare-metal-programming/critical-sections-and-atomicity.md) gives for save-and-restore: a nested handler must not clear a mask an outer handler set. And `vTaskNotifyGiveFromISR()` returning `void` is not an oversight — a notify-give always succeeds, so there is no status to report, only the woken flag.

## The yield-from-ISR pattern

`xQueueSendFromISR()` moves data onto a queue and, if that unblocks a task, moves that task from the queue's event list to the ready list. What it does **not** do is switch to it. A handler that decided the schedule mid-flight would be pre-empting itself, and on Cortex-M the switch has to happen through PendSV anyway ([Context Switching](./context-switching.md)). So the API reports its finding through an out-parameter and leaves the decision to the end of the handler:

```c
void USART2_IRQHandler(void)
{
    BaseType_t higher_woken = pdFALSE;   /* MUST be initialised */
    uint8_t    byte;

    while (USART2->SR & USART_SR_RXNE) {
        byte = (uint8_t)USART2->DR;
        xQueueSendFromISR(rx_queue, &byte, &higher_woken);
    }

    /* Exactly once, at the end. Not inside the loop. */
    portYIELD_FROM_ISR(higher_woken);
}
```

The kernel sets `*pxHigherPriorityTaskWoken` to `pdTRUE` only when the unblocked task's priority is **higher than the task that was interrupted** — not merely when a task woke. So `pdFALSE` on exit is a positive statement that no switch is needed, and calling the yield macro with it is free.

```mermaid
sequenceDiagram
    participant HW as USART2
    participant ISR as Handler (level 6)
    participant K as Kernel lists
    participant PSV as PendSV (level 15)
    participant T as Tasks
    T->>T: LOW task running
    HW->>ISR: RXNE, IRQ taken
    ISR->>K: xQueueSendFromISR(&woken)
    K->>K: copy item, move HIGH<br/>task to ready list
    K-->>ISR: woken = pdTRUE
    ISR->>PSV: portYIELD_FROM_ISR → set PENDSVSET
    ISR-->>PSV: handler returns; PendSV tail-chains
    PSV->>T: switch to HIGH task
```

`portYIELD_FROM_ISR( x )` and `portEND_SWITCHING_ISR( x )` are the same macro on the Cortex-M ports — the kernel's own header tells you to check which name your port documents. Its body is one comparison and, if the flag is set, `portYIELD()`: a store of `PENDSVSET` into `SCB->ICSR`, followed by `DSB` and `ISB`. PendSV is configured at the least-urgent priority, so it cannot run until every pending interrupt has drained, and it usually tail-chains directly off your handler's exception return — which is why the switch costs no second stacking.

### Forgetting the yield is a latency bug, not a crash

Omit `portYIELD_FROM_ISR` and nothing is corrupted. The task is genuinely on the ready list; the scheduler simply has not been asked to look. The interrupted low-priority task resumes and keeps running until something else pends PendSV — normally the next tick, because `xTaskIncrementTick()` requests a switch when it finds a higher-priority ready task.

```wavedrom title="The same wake, with and without the yield at the end of the handler" alt="Timeline with a UART interrupt and its handler at the top; below, a PendSV pulse immediately after the handler returns and the high-priority task starting there; below that, no PendSV, with the high-priority task starting only when the next SysTick fires much later"
{ "signal": [
  { "name": "USART2 IRQ",     "wave": "0.10.................." },
  { "name": "handler",        "wave": "0..10................." },
  {},
  { "name": "PendSV (yield)", "wave": "0...10................" },
  { "name": "HIGH task",      "wave": "0....1................" },
  {},
  { "name": "SysTick",        "wave": "0................10..." },
  { "name": "HIGH (no yield)","wave": "0.................1..." }
], "config": { "hscale": 2 } }
```

The cost is therefore *up to one tick period*, and which number that is depends entirely on `configTICK_RATE_HZ`: 1 ms at the common 1000 Hz, 10 ms at 100 Hz. Under a tickless idle configuration, where the tick is suppressed while the system sleeps, there may be no next tick for a very long time. The symptom is a system that works and is intermittently, unaccountably slow to respond — a UART echo that is sometimes instant and sometimes a millisecond late, with a latency histogram that has a hard shoulder at exactly the tick period. That shoulder is the diagnosis: a latency distribution quantised to the tick means something is waiting for the tick that should not be.

## The priority ceiling, and the rule

Here is the constraint the whole page builds to, stated so it can be checked against code:

> On Cortex-M, FreeRTOS masks with `BASEPRI`. **Only an interrupt whose priority is at or below `configMAX_SYSCALL_INTERRUPT_PRIORITY` in urgency — that is, whose priority *number* is greater than or equal to it — may call a `FromISR` API.** An interrupt more urgent than the threshold must call nothing in the kernel at all.

Cortex-M priority numbers are inverted: **numerically lower means more urgent**. Almost every mistake in this area is that sentence not being applied. "A higher-priority interrupt must not call the API" is true and is read backwards by half the people who read it, because the number is smaller. Adopt the vocabulary [Priorities and Nesting](../06-interrupts-timing-and-real-time/interrupt-priorities-and-nesting.md) insists on — *more urgent* and *less urgent*, never higher and lower — and the rule stops being ambiguous. Note also that this inversion is the opposite of FreeRTOS **task** priorities, where a bigger number is more urgent; [Tasks and Scheduling](./tasks-and-scheduling.md) flags that collision, and a config file that contains both numbering systems is where it bites.

What the threshold physically does is visible in the port's own PendSV handler, which raises `BASEPRI` to `configMAX_SYSCALL_INTERRUPT_PRIORITY` around its call to `vTaskSwitchContext()` and drops it to zero afterwards. Everything less urgent than the ceiling is frozen while the kernel picks the next task. Everything more urgent is not — and is therefore executing while `pxCurrentTCB` and the ready lists are inconsistent.

## Configuring it: two numbering systems in one file

The generated `FreeRTOSConfig.h` on an STM32 project contains both, and the difference is the trap:

```c
/* Logical priority levels — small integers, 0..15 on this part. */
#define configPRIO_BITS                              4
#define configLIBRARY_LOWEST_INTERRUPT_PRIORITY     15
#define configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY 5

/* Raw register values — pre-shifted into the implemented bits.
   Never write a bare number here. */
#define configKERNEL_INTERRUPT_PRIORITY \
    ( configLIBRARY_LOWEST_INTERRUPT_PRIORITY << (8 - configPRIO_BITS) )      /* 0xF0 */
#define configMAX_SYSCALL_INTERRUPT_PRIORITY \
    ( configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY << (8 - configPRIO_BITS) ) /* 0x50 */
```

- **Both `configKERNEL_*` and `configMAX_SYSCALL_*` are raw priority-register bytes**, ORed straight into `SHPR2`/`SHPR3` and written straight to `BASEPRI` with no further shifting. Why the shift is needed and what a bare number does instead is [Critical Sections and Atomicity](../04-bare-metal-programming/critical-sections-and-atomicity.md); the FreeRTOS-specific consequence is that `0x50` and `0xF0` above are levels 5 and 15 **already in register form**, while the `configLIBRARY_*` pair beside them are plain level numbers and are the only two you should ever edit. Get that backwards — `#define configMAX_SYSCALL_INTERRUPT_PRIORITY 5` — and the kernel masks with a `BASEPRI` of zero, which that page shows means no masking at all.
- **`configKERNEL_INTERRUPT_PRIORITY` must be the least-urgent level available.** It is the priority given to SysTick and PendSV, and it is what makes tail-chaining into the switch safe. `0xF0` on this part; anything more urgent lets a context switch delay a real interrupt.
- **`configMAX_SYSCALL_INTERRUPT_PRIORITY` must not be zero.** The port asserts this at `vTaskStartScheduler()` time, because a ceiling of 0 would mask nothing.
- **Task priorities are unrelated to both.** `xTaskCreate(..., uxPriority, ...)` takes `0` to `configMAX_PRIORITIES - 1`, bigger is more urgent, and no shift is involved anywhere.

Placing the ceiling at level 5 matches the band table in [Priorities and Nesting](../06-interrupts-timing-and-real-time/interrupt-priorities-and-nesting.md): levels 0–4 sit above the line and are forbidden both from touching protected state and from calling the kernel; levels 5–15 are the kernel-aware band. That page argues where the line goes; this one only adds that FreeRTOS is one of the things that lives on it.

The best money you will spend here is one line:

```c
#define configASSERT(x)  if ((x) == 0) { taskDISABLE_INTERRUPTS(); for (;;); }
```

With `configASSERT` defined, the Cortex-M ports compile in `vPortValidateInterruptPriority()`, which every `FromISR` API calls on entry. It reads the active exception's byte out of the NVIC priority registers and asserts that it is numerically **greater than or equal to** the masked ceiling — the rule above, enforced at the first offending call rather than at the eventual crash. The kernel gained this check for nesting-capable ports in **V7.5.0 (July 2013)** and the ARMv8-M ports later; if your port predates it or `configASSERT` is undefined, you have no check at all. It also verifies that `AIRCR.PRIGROUP` leaves enough pre-emption bits for the scheme to mean anything.

## Bounded work: the constraint behind the constraint

The ceiling is about safety. There is a second, softer rule about *duration*, and the kernel enforces it on itself in a way worth copying.

[Task Notifications and Event Groups](./notifications-and-event-groups.md) establishes that `xEventGroupSetBitsFromISR()` does not set the bits. Setting bits in an event group may unblock an unknown number of waiting tasks — the operation walks the whole waiting list and re-tests each condition — and "unknown number" is not something a handler is allowed to spend. So the ISR variant packages the work as a call to `xTimerPendFunctionCallFromISR()`, and the timer daemon performs it in task context. That is why the function needs `configUSE_TIMERS` and `INCLUDE_xTimerPendFunctionCall`, and why the bits appear only when the daemon next runs.

Read that as the kernel demonstrating its own rule: **an ISR-safe API is one whose worst-case execution time is a constant you can state.** `xQueueSendFromISR()` copies `item_size` bytes and unblocks at most one task — bounded. Setting event bits is not, so it does not happen in the handler. `xTimerPendFunctionCallFromISR( pvFunction, pvParameter1, ulParameter2, &woken )` is the general escape hatch: anything unbounded that an interrupt discovers should be posted to the daemon or to your own worker task and returned from immediately, which is precisely the split [Deferred Work](../06-interrupts-timing-and-real-time/deferred-work.md) describes.

:::warning[The DMA interrupt at level 0, and the yield inside the loop]
Two failures with completely different signatures, both traceable to this page.

**The urgent interrupt that called the kernel.** A DMA-complete handler is left at the reset default priority — `NVIC->IP[irq] == 0`, the most urgent level, because nobody called `NVIC_SetPriority` — and it calls `vTaskNotifyGiveFromISR()`. It is above the ceiling, so `BASEPRI` never masks it, so it can fire in the middle of `vTaskSwitchContext()` or `xTaskIncrementTick()`. Most of the time it lands harmlessly. Occasionally it lands between the two stores that unlink an item from a list, and it writes a `pxNext` that points at a freed or half-initialised item. The firmware then runs perfectly for minutes and takes a HardFault inside `vListInsert()`, `xTaskRemoveFromEventList()` or the PendSV handler — with a call stack containing nothing you wrote and a fault address that changes every time. `list.c` carries a comment at exactly that spot naming this as one of the two likely causes, and the other is a stack overflow, which sends people to [Stacks and Heaps in an RTOS](./stacks-and-heaps-in-an-rtos.md) first because it is the more familiar suspect. The diagnosis takes ten seconds if you know where to look: halt, read `NVIC->IP[n]` for every interrupt that calls a `FromISR` function, and compare each against `configMAX_SYSCALL_INTERRUPT_PRIORITY >> (8 - configPRIO_BITS)`. Any byte numerically **less** than the ceiling is the bug. Define `configASSERT` and the kernel finds it for you on the first call instead.

**The yield inside the loop.** `portYIELD_FROM_ISR(higher_woken)` written inside the receive loop rather than after it. It compiles, and it is not a corruption — but it pends PendSV on the first byte, so the switch is requested while the FIFO still has data. On a burst the handler now runs, yields, gets tail-chained back for the next byte, yields again, and each character costs a full context switch instead of a queue copy. Throughput collapses under exactly the load the buffering existed to survive, run-time statistics show the kernel consuming a startling share of the CPU, and the code reviews as correct because the macro is present and the variable is right. The pattern is one initialisation before the loop, one yield after it, and nothing in between.
:::

## See also

- [Deferred Work](../06-interrupts-timing-and-real-time/deferred-work.md) — the top-half/bottom-half split these APIs implement, and the lock-free ring buffer that needs none of them.
- [Priorities and Nesting](../06-interrupts-timing-and-real-time/interrupt-priorities-and-nesting.md) — where to place the ceiling in a numbering scheme, and the latency it costs everything below it.
- [Critical Sections and Atomicity](../04-bare-metal-programming/critical-sections-and-atomicity.md) — `BASEPRI` itself, the pre-shift, and the save-and-restore form the `FROM_ISR` critical-section macros use.
- [Context Switching](./context-switching.md) — what PendSV does once `portYIELD_FROM_ISR` has pended it, and why tail-chaining makes the switch cheap.
- [Semaphores and Mutexes](./synchronization-primitives.md) — the full argument for why the mutex row of the table above is permanently empty.

## References

- Amazon Web Services — [**FreeRTOS: RTOS for Arm Cortex-M — configuration**](https://www.freertos.org/Documentation/02-Kernel/03-Supported-devices/02-Customization#configmax_syscall_interrupt_priority) and the [**"Interrupt Service Routines" / ISR-safe API pages**](https://www.freertos.org/Documentation/02-Kernel/02-Kernel-features/11-Interrupt-management/01-Interrupt-management). Verified against these for this page: that `configMAX_SYSCALL_INTERRUPT_PRIORITY` and `configKERNEL_INTERRUPT_PRIORITY` are **raw, pre-shifted priority-register values** while task priorities are not; that only interrupts at or below the max-syscall priority in urgency may call `FromISR` functions; and that `configKERNEL_INTERRUPT_PRIORITY` should be the lowest-urgency level. (Documentation checked 2026-08-26.)
- FreeRTOS-Kernel V11.3.0 — [**`include/queue.h`**](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/main/include/queue.h) and [**`queue.c`**](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/main/queue.c). The `xQueueSendToBackFromISR()` documentation block, whose worked example is the source of the pattern above — initialise `xHigherPriorityTaskWoken = pdFALSE`, pass it in, test it once at the end, and call `portYIELD_FROM_ISR()` or `portEND_SWITCHING_ISR()` "refer to the documentation page for the port being used". `xQueueGenericSendFromISR()` shows `taskENTER_CRITICAL_FROM_ISR()` / `taskEXIT_CRITICAL_FROM_ISR()` and the exact condition under which `*pxHigherPriorityTaskWoken` is set. (Source checked 2026-08-26.)
- FreeRTOS-Kernel — [**`portable/GCC/ARM_CM4F/port.c`**](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/main/portable/GCC/ARM_CM4F/port.c) and [**`History.txt`**](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/main/History.txt). `xPortPendSVHandler()` raising `BASEPRI` to `configMAX_SYSCALL_INTERRUPT_PRIORITY` around `vTaskSwitchContext()`; `vPortValidateInterruptPriority()` and `ucMaxSysCallPriority`; and the V7.5.0 entry (19 July 2013) adding the `configASSERT()` that fires when an interrupt-safe function is called from an interrupt more urgent than the max-syscall priority, with the equivalent ARMv8-M assertions added later. (Source checked 2026-08-26.)
- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), Rev 10. §2.1.3 for `BASEPRI` semantics and the rule that zero disables masking; §4.3.7 for the interrupt priority register layout and the four implemented bits in the upper nibble that make `5 << 4` the correct encoding of level 5.
- Richard Barry and the FreeRTOS team — [***Mastering the FreeRTOS Real Time Kernel***](https://www.freertos.org/Documentation/02-Kernel/07-Books-and-manual/01-RTOS_book) (free PDF from freertos.org). Chapter 7, "Interrupt Management", is the narrative treatment: deferred interrupt processing, the `pxHigherPriorityTaskWoken` idiom with worked examples, and an extended section on Cortex-M interrupt priorities written specifically because the inversion causes so many failures.
