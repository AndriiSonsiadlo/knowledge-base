---
id: notifications-and-event-groups
title: Task Notifications and Event Groups
sidebar_label: Notifications and Event Groups
sidebar_position: 8
tags: [embedded, rtos, freertos, task-notifications, event-groups, ipc, concurrency]
---

# Task Notifications and Event Groups

Queues, semaphores, mutexes and event groups are all *objects*. Each has its own allocation, its own handle, and its own place in the system's RAM budget, and a sender has to be given that handle before it can say anything. The kernel's own header states the distinction plainly: those four are "intermediary objects" for sending an event, and a task notification "is a method of sending an event directly to a task without the need for such an intermediary object."

The mental model is exactly that literal. **A notification is a word that already exists inside the receiving task's TCB.** It is allocated when the task is created, whether you use it or not. There is nothing to create, nothing to size, nothing to fail at start-up, and nothing to free. Sending one is a write to a field of a structure the kernel already has a pointer to, plus the ordinary business of moving a task from a wait list to a ready list — which is why it is both cheaper in RAM and shorter in instructions than any of the alternatives.

The same sentence explains every limitation. A word in *a* TCB is addressed to exactly one task, holds exactly one word, and has no depth. Where you need more than one waiter, more than one item, or more than 32 bits, a notification is not a smaller version of the right primitive — it is the wrong one, and this page is mostly about telling those cases apart.

:::info[Prerequisites]
[Semaphores and Mutexes](./synchronization-primitives.md) and [Queues and Message Passing](./queues-and-message-passing.md) are the objects this page is comparing against; the "cheaper binary semaphore" claim at the end of the first is cashed out here. [Tasks and Scheduling](./tasks-and-scheduling.md) owns the TCB and the Blocked state that every wait below enters.
:::

## The four mechanisms on RAM and speed

| | Task notification | Binary semaphore | Queue | Event group |
|---|---|---|---|---|
| **Separate object** | **None** — lives in the TCB | `Queue_t` | `Queue_t` + storage | `EventGroup_t` |
| **RAM** | 0 additional bytes; the kernel's customisation documentation puts the per-task cost of the feature at **8 bytes per task** with the default one array entry | `sizeof(Queue_t)`, storage 0 | `sizeof(Queue_t)` + `length x item_size` | `sizeof(EventGroup_t)` |
| **Payload** | one 32-bit word (or 16/64, following `TickType_t`) | none — a count of 0 or 1 | anything, `item_size` bytes, `length` deep | 24 usable bits with a 32-bit tick type |
| **Depth** | 1 (or a saturating count, with `eIncrement`) | 1 | `length` | n/a — bits, not items |
| **Waiters** | **exactly one**, named at send time | any number; highest priority wakes first | any number | **any number, all woken together** |
| **Sender needs** | the receiver's `TaskHandle_t` | the object handle | the object handle | the object handle |
| **Blocking send** | no — `xTaskNotify` never blocks | n/a | yes, with a timeout | no |
| **Relative speed** | fastest; no object lock, no copy | one queue operation | one queue operation plus two `memcpy`s | one queue-like operation plus a scan of every waiter |

The kernel's documentation attaches a figure to the top row: unblocking a task with a direct notification is stated as **45 % faster and using less RAM** than unblocking it through an intermediary object such as a binary semaphore. That is the vendor's number, measured on their reference configuration with GCC at full optimisation on a Cortex-M, and it is quoted here as a claim with a source rather than as a measurement of your system. The *mechanism* behind it is the thing to trust and it is not in dispute: no separate object means no second structure to lock, no event list on that object to walk, and no item copy.

The `sizeof()` entries are deliberately algebraic. `Queue_t` and `EventGroup_t` change with the port and with `configUSE_TRACE_FACILITY`, so the only honest number is the one from your own build — bracket the creation call with `xPortGetFreeHeapSize()` as in [Queues and Message Passing](./queues-and-message-passing.md), or read the map file on a static build.

## Notifications as a semaphore replacement

The commonest use is the deferred-interrupt handoff, and it is a one-for-one substitution:

```c
/* Before: a binary semaphore, an object, a handle, a create call that can fail. */
xSemaphoreTake(rx_ready, portMAX_DELAY);

/* After: nothing to create. pdTRUE = clear the count on exit, i.e. binary. */
ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
```

`xTaskNotifyGive()` increments the receiving task's notification value and unblocks it; `ulTaskNotifyTake(xClearCountOnExit, xTicksToWait)` blocks until the value is non-zero, then returns the value it found and either clears it (`pdTRUE` — a binary semaphore) or decrements it by one (`pdFALSE` — a counting semaphore). The counting form is genuinely useful: a task that wakes and finds a value of 3 knows three events happened while it was busy, which a binary semaphore cannot tell it.

For anything richer, `xTaskNotify(handle, ulValue, eAction)` writes the word with one of five actions, and `xTaskNotifyWait(ulBitsToClearOnEntry, ulBitsToClearOnExit, &value, ticks)` reads it:

| `eNotifyAction` | Effect on the notification value | Reads as |
|---|---|---|
| `eNoAction` | unchanged — the task is unblocked and nothing else | a pure signal |
| `eSetBits` | `value \|= ulValue` | a private, single-waiter event group |
| `eIncrement` | `value++` (this is what `xTaskNotifyGive` does) | a counting semaphore |
| `eSetValueWithOverwrite` | `value = ulValue`, always succeeds | `xQueueOverwrite` on a length-1 mailbox |
| `eSetValueWithoutOverwrite` | `value = ulValue` only if the task had no pending notification; otherwise returns `pdFAIL` | `xQueueSend` on a length-1 queue with a zero timeout |

The last two are the pair worth understanding together, because the difference is the entire question of what happens when the receiver has not caught up. `eSetValueWithOverwrite` loses the older value; `eSetValueWithoutOverwrite` loses the newer one and tells you it did. There is no third option in which the sender waits, because a notification has no depth to wait for space in — if you need a blocking send, you need a queue.

## Indexed notifications, and the collision they exist to prevent

Before kernel V10.4.0 each task had exactly one notification. From V10.4.0 each task has an **array** of them, sized by `configTASK_NOTIFICATION_ARRAY_ENTRIES`, and every API gained an `Indexed` sibling: `xTaskNotifyIndexed()`, `xTaskNotifyWaitIndexed()`, `xTaskNotifyGiveIndexed()`, `ulTaskNotifyTakeIndexed()`, `xTaskNotifyAndQueryIndexed()`, `xTaskNotifyStateClearIndexed()` and `ulTaskNotifyValueClearIndexed()`.

The fact that matters is not the new functions. It is this: **the original un-indexed API is not a general form — it is the indexed form with the index fixed at zero.** `xTaskNotifyWait(a, b, c, d)` *is* `xTaskNotifyWaitIndexed(0, a, b, c, d)`. Every piece of code in the image that says "the notification" without an index is competing for the same word.

That is fine while one subsystem owns each task. It stops being fine the moment a task both runs a driver that uses notifications internally and receives notifications from the application — and this is common, because notifications are the default handoff in a great many vendor and middleware libraries:

```c
/* FreeRTOSConfig.h */
#define configTASK_NOTIFICATION_ARRAY_ENTRIES  3

/* One header, owned by nobody, that everything includes. This is the whole
   discipline: indices are a system-wide namespace, so name them once. */
#define NOTIFY_IDX_DRIVER   0    /* what un-indexed calls in libraries hit */
#define NOTIFY_IDX_APP      1
#define NOTIFY_IDX_SHUTDOWN 2

/* The application waits on its own index and cannot be robbed by the driver. */
uint32_t ev;
xTaskNotifyWaitIndexed(NOTIFY_IDX_APP, 0, UINT32_MAX, &ev, portMAX_DELAY);
```

The array is not free: each entry costs a word for the value plus a byte of state, **in every task**, so raising `configTASK_NOTIFICATION_ARRAY_ENTRIES` from 1 to 3 costs roughly two extra words per task across the whole system. On a part with 128 KB of SRAM that is noise; on a 20 KB part with fifteen tasks it is a decision. Reserving index 0 for whatever third-party code does un-indexed, and using explicit indices for everything you write, is the cheap version of the discipline.

## Where a notification cannot replace a queue

Five cases, and the first three are the ones the brief of every "just use notifications, they're faster" refactor runs into:

- **More than one waiter.** A notification is addressed to a `TaskHandle_t`. There is no broadcast, no "whichever task gets there first", and no way for two tasks to wait on the same notification. A semaphore, a queue and an event group all support multiple waiters; a notification structurally cannot.
- **Buffering more than one item.** `eIncrement` counts events but does not hold them. Three sensor readings arriving before the consumer runs become a count of three and one surviving value — or, with `eSetValueWithOverwrite`, one surviving value and no count at all. If the *contents* of each event matter, you need depth, and depth means a queue.
- **Data wider than a word.** The notification value follows `TickType_t`: 32 bits in the usual configuration. A 12-byte struct does not fit. Sending a *pointer* to it does fit — and immediately imports the whole ownership problem from [Queues and Message Passing](./queues-and-message-passing.md), without the queue's copy to protect you.
- **The sender does not know the receiver.** A queue is a rendezvous point that any number of anonymous producers can send to. A notification needs the receiver's handle, which means the producers and the consumer must be wired together at start-up, and adding a second consumer later is a redesign rather than an extra `xQueueSend`.
- **The sender must block until there is room.** `xTaskNotify()` never blocks. Back-pressure — a producer that slows down because the consumer is behind — needs `xQueueSend()` with a timeout.

The honest summary: a notification replaces a *binary or counting semaphore* almost always, and a *length-1 mailbox queue* often. It replaces a real queue essentially never.

## Event groups: waiting on a combination

An event group is a set of bits with a waiting list, and it is the only primitive here that answers "wait until **A and B and C** have all happened" without a task-local state machine. `xEventGroupWaitBits()` carries the two flags that define its behaviour:

```c
EventBits_t bits = xEventGroupWaitBits(
        conn_events,
        EV_LINK_UP | EV_DHCP_DONE | EV_TIME_SYNCED,  /* uxBitsToWaitFor */
        pdFALSE,                                     /* xClearOnExit    */
        pdTRUE,                                      /* xWaitForAllBits */
        pdMS_TO_TICKS(30000));

/* MANDATORY: on timeout the call returns the bits as they stood, not an error. */
if ((bits & (EV_LINK_UP | EV_DHCP_DONE | EV_TIME_SYNCED)) ==
             (EV_LINK_UP | EV_DHCP_DONE | EV_TIME_SYNCED)) {
    start_session();
} else {
    report_bring_up_timeout(bits);      /* and 'bits' says which one is missing */
}
```

- **`xWaitForAllBits`** selects AND against OR, and nothing else. The kernel's `prvTestWaitCondition()` is four lines: `pdFALSE` unblocks if *any* bit in the mask is set, `pdTRUE` only if *all* of them are. Both are re-tested on every `xEventGroupSetBits()` call, which is why setting bits has to walk the whole waiting list.
- **`xClearOnExit`** clears `uxBitsToWaitFor` when the wait is satisfied, making the read destructive. With one waiter that is a convenient auto-reset. With two waiters it is a race: whichever task the scheduler runs first consumes the bits, and the second waits again on an event that has already happened. Event groups broadcast — every waiter whose condition is met is unblocked by one `xEventGroupSetBits()` — and `xClearOnExit` is the flag that quietly turns a broadcast back into a hand-off.
- **The return value is not a status.** It is the event group's value at the moment the condition was met *or the timeout expired*, whichever came first. Code that treats a non-zero return as success is wrong, and the example above shows the only correct shape: mask the return and compare it against what you were waiting for.

**How many bits you get depends on the tick type**, for an implementation reason rather than a conceptual one. `EventBits_t` is the same width as `TickType_t`, and the top byte is reserved for the kernel's own control flags (`eventCLEAR_EVENTS_ON_EXIT_BIT`, `eventUNBLOCKED_DUE_TO_BIT_SET`, `eventWAIT_FOR_ALL_BITS`). So with `configTICK_TYPE_WIDTH_IN_BITS` set to 32 bits — the usual case — bits 0 to 23 are yours and bits 24 to 31 are not; a 16-bit tick type leaves you 8 usable bits, and a 64-bit one leaves 56.

`xEventGroupSync(group, uxBitsToSet, uxBitsToWaitFor, ticks)` is the rendezvous form: set my bit, then block until everyone's bit is set, then clear them all atomically. It is the correct primitive for "no task proceeds past this point until all N have arrived", and it is materially harder to build correctly out of anything else.

One implementation detail is worth knowing because it explains a surprise: **`xEventGroupSetBitsFromISR()` does not set the bits.** Setting bits may unblock an unknown number of tasks, which is not a bounded operation, so the ISR variant defers the work to the timer service task through `xTimerPendFunctionCallFromISR()` — which means it requires `configUSE_TIMERS` and `INCLUDE_xTimerPendFunctionCall`, and the bits become visible only when the daemon task next runs. If `configTIMER_TASK_PRIORITY` is below your application tasks, "immediately" can be a long time; see [Software Timers and Delays](./software-timers-and-delays.md).

:::warning[The two subsystems that shared notification index 0, and the event group whose timeout looked like success]
Two failures that survive code review because each site is individually correct.

**Index 0, twice.** A vendor SPI driver blocks in `ulTaskNotifyTake(pdTRUE, timeout)` waiting for its DMA-complete signal — un-indexed, so index 0. The same task also receives application events sent with `xTaskNotifyGive()` — un-indexed, so index 0. Everything works until the two overlap in time. Then the driver's `ulTaskNotifyTake` returns because the *application* notified, the driver concludes the transfer finished, and it reads a buffer the DMA controller is still writing. Alternatively the application's notification is consumed by the driver's take and is simply lost. The symptom is a driver that intermittently returns short or corrupted data, and it appears only when a feature that happens to notify that task is enabled — so it is reported as "the SPI driver is broken by the logging feature", which is a sentence that sends everyone in the wrong direction. Nothing in either call site is wrong, and grep does not help because neither writes an index. The tells: `xTaskNotifyStateClear()` or a breakpoint on the driver's take shows it returning with no DMA interrupt having fired, and the fault rate tracks application event rate rather than transfer rate. Set `configTASK_NOTIFICATION_ARRAY_ENTRIES` above 1, give everything you own an explicit named index, and leave index 0 to code you did not write.

**The `xEventGroupWaitBits` return read as a status.** `if (xEventGroupWaitBits(g, EV_READY, pdTRUE, pdTRUE, pdMS_TO_TICKS(5000)))` compiles, and it is wrong. On timeout the function returns the group's *current* bits, and if any unrelated bit in that group is set — a status flag, a bit another subsystem owns — the expression is non-zero and the code proceeds as though the event occurred. The failure needs two conditions to coincide (a timeout, and some other bit being set), so it passes every test where the event arrives on time. It then surfaces in the field as a device that continues bring-up without a network link, or starts a motor before a limit switch has reported home. There is no diagnostic; the code took the success branch. Always mask and compare against `uxBitsToWaitFor` explicitly, exactly as in the example above, and prefer separate event groups for unrelated concerns so an irrelevant bit cannot appear in your return value in the first place.
:::

## See also

- [Semaphores and Mutexes](./synchronization-primitives.md) — the intermediary objects a notification replaces, and the ownership property none of these have.
- [Queues and Message Passing](./queues-and-message-passing.md) — what to use when the five conditions above rule a notification out, and where the `sizeof()` measurement recipe lives.
- [Tasks and Scheduling](./tasks-and-scheduling.md) — the TCB the notification array lives in, and the Blocked state every wait here enters.
- [Software Timers and Delays](./software-timers-and-delays.md) — the daemon task that `xEventGroupSetBitsFromISR()` defers to, and what its priority costs you.
- [Deferred Work](../06-interrupts-timing-and-real-time/deferred-work.md) — the ISR-to-task handoff that a direct notification is the cheapest implementation of.

## References

- Amazon Web Services — [**FreeRTOS: direct-to-task notifications**](https://www.freertos.org/Documentation/02-Kernel/02-Kernel-features/03-Direct-to-task-notifications/01-Task-notifications) and the [**task-notification API reference**](https://www.freertos.org/Documentation/02-Kernel/04-API-references/04-Task-notifications/01-xTaskNotifyIndexed). Verified against these for this page: the `xTaskNotifyIndexed` / `xTaskNotifyWaitIndexed` / `xTaskNotifyGiveIndexed` / `ulTaskNotifyTakeIndexed` family and the rule that each un-indexed macro is the indexed call with index 0; the five `eNotifyAction` values and their exact effects including the `pdFAIL` return of `eSetValueWithoutOverwrite`; `configTASK_NOTIFICATION_ARRAY_ENTRIES`; the "45 % faster and uses less RAM" comparison against a binary semaphore; and `configUSE_TASK_NOTIFICATIONS`, whose documentation gives the 8-bytes-per-task figure quoted in the table. (Documentation checked 2026-08-26.)
- FreeRTOS-Kernel — [**`include/task.h`**](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/main/include/task.h) and [**`History.txt`**](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/main/History.txt). The header's own statement that queues, semaphores, mutexes and event groups are "intermediary objects" while notifications go directly to a task — quoted at the top of this page — and the V10.3.1-to-V10.4.0 entry recording the change from a single notification per task to an array with the `Indexed` API. (Source checked 2026-08-26.)
- FreeRTOS-Kernel — [**`include/event_groups.h`**](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/main/include/event_groups.h) and [**`event_groups.c`**](https://github.com/FreeRTOS/FreeRTOS-Kernel/blob/main/event_groups.c). The control-bit constants (`eventCLEAR_EVENTS_ON_EXIT_BIT`, `eventUNBLOCKED_DUE_TO_BIT_SET`, `eventWAIT_FOR_ALL_BITS`, `eventEVENT_BITS_CONTROL_BYTES`) that reserve the top byte and give the 8 / 24 / 56 usable-bit counts; `prvTestWaitCondition()`, the four-line AND-versus-OR test behind `xWaitForAllBits`; and `xEventGroupSetBitsFromISR()`, which forwards to `xTimerPendFunctionCallFromISR()` because setting bits may unblock an unbounded number of tasks. (Source checked 2026-08-26.)
- Amazon Web Services — [**FreeRTOS: event groups**](https://www.freertos.org/Documentation/02-Kernel/02-Kernel-features/06-Event-groups/00-Event-groups) and the [**`xEventGroupWaitBits` reference**](https://www.freertos.org/Documentation/02-Kernel/04-API-references/12-Event-groups-or-flags/02-xEventGroupWaitBits). The `xClearOnExit` and `xWaitForAllBits` parameter semantics, `xEventGroupSync()`, and the explicit statement that the return value is the event group value at the moment the condition was met or the block time expired — the basis of the second warning. (Documentation checked 2026-08-26.)
- Richard Barry and the FreeRTOS team — [***Mastering the FreeRTOS Real Time Kernel***](https://www.freertos.org/Documentation/02-Kernel/07-Books-and-manual/01-RTOS_book) (free PDF). Chapter 10 covers task notifications with worked substitutions for semaphores and mailboxes and a list of the limitations reproduced above; Chapter 9 covers event groups, including the rendezvous built with `xEventGroupSync()`.
