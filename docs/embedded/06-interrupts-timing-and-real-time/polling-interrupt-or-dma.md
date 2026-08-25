---
id: polling-interrupt-or-dma
title: Polling, Interrupt, or DMA
sidebar_label: Polling, Interrupt, or DMA
sidebar_position: 3
tags: [embedded, peripherals, dma, interrupts, polling, timing, real-time, stm32]
---

# Polling, Interrupt, or DMA

There are exactly three ways to get a byte out of a peripheral register and into your program's memory. The CPU can ask repeatedly until the answer is yes. The peripheral can raise a line that makes the CPU stop what it was doing. Or a second bus master can do the load and the store on the CPU's behalf and tell it afterwards. Every driver you will ever write picks one of these, and the choice is made badly far more often than it is made wrong — badly, meaning by reflex rather than from a budget.

The reflex is usually "interrupts are the professional answer, polling is what beginners do, DMA is for when you need speed." All three halves of that are false. Polling is the correct and provably optimal choice for a bootloader. An interrupt per byte at 2 Mbit/s will consume most of your CPU. DMA on a 9600-baud link is a hundred lines of setup buying nothing.

The mental model: **you are spending one of three currencies — CPU cycles, latency, or code complexity — and the three mechanisms spend them in different proportions.** Decide which one you are short of, then pick. The rest of this page is the arithmetic that turns "which am I short of" into a number.

:::info[Prerequisites]
[DMA](../05-peripherals-and-drivers/dma.md) owns the controller itself: streams and channels, circular mode, the half-transfer interrupt, arbitration and what a stream costs on the bus. This page decides *whether* to reach for it and does not re-explain it. [Interrupt Latency](./interrupt-latency.md) supplies the per-event cost model used below. [I/O and Interrupts](../../computer-science/buses-and-io/io-and-interrupts.md) covers the general concept independent of any CPU.
:::

## The cost model

Three numbers, and everything else follows from them.

**One interrupt costs about 30 core cycles of pure overhead** for a minimal handler on this part: 12 cycles of exception entry (Arm, *Cortex-M4 TRM* DDI 0439, zero wait states), the exception return, and a short compiler prologue and epilogue. At 100 MHz that is **≈ 300 ns per event, before your handler does anything at all**. This figure is *derived*, not quoted — the TRM gives the entry cycles, the rest is arithmetic — and it will be larger on your board because of flash wait states on a cold handler. Measure yours with `DWT->CYCCNT` rather than trusting this paragraph.

**One polled iteration costs whatever the loop body costs**, which for a status-bit test on an APB peripheral is a handful of cycles plus the APB read. The CPU is 100 % occupied for the whole wait, but the *latency* is one loop iteration — tens of nanoseconds, an order of magnitude better than an interrupt can achieve.

**One DMA item costs zero CPU cycles and two bus transactions**, one on the peripheral port and one on the memory port ([DMA](../05-peripherals-and-drivers/dma.md) covers arbitration and bursting). The CPU cost appears only at block boundaries, once per half-buffer rather than once per item.

From the first number, the two crossovers worth memorising:

| Event rate at 100 MHz | Interrupt overhead alone | Verdict |
|---|---|---|
| 1 kHz | 0.03 % | Interrupt, obviously |
| 10 kHz | 0.3 % | Interrupt |
| 33 kHz | ~1 % | Interrupt, but start counting |
| 167 kHz | ~5 % | The point where DMA starts paying for itself |
| 1 MHz | ~30 % | Per-event interrupts are not viable |

And the crossover in the other direction: **when the wait is shorter than the interrupt overhead, spinning is literally cheaper than taking the interrupt.** An SPI byte at 25 Mbit/s takes 320 ns. Taking an interrupt to be told about it costs ~300 ns of overhead on top of the handler — you have spent almost as much arranging not to wait as waiting would have cost. Below roughly a microsecond of wait, polling wins on CPU as well as on latency.

## The decision table

| | **Polling** | **Interrupt** | **DMA** |
|---|---|---|---|
| **Data rate it suits** | Any, if the CPU has nothing else to do; or events faster than ~1 µs apart | ~1 event/s to ~100 k events/s | Sustained streams above ~100 k items/s, or any rate where CPU is scarce |
| **Latency achievable** | Best possible (one loop iteration) *if* dedicated; worst possible (one superloop period) if not | ~1 µs, bounded by masking and higher-priority handlers | Item latency is zero; *notification* latency is one half-buffer |
| **CPU cost** | 100 % while waiting, or (poll cost × poll rate) | ~300 ns + handler, per event | ~300 ns + handler, per **block**; plus stolen bus cycles |
| **Worst-case determinism** | Excellent when dedicated; poor in a superloop, where it is the sum of everything else in the loop | Good, if the priority scheme is designed | Excellent for throughput; the bus contention it adds is the thing to bound |
| **Code complexity** | 3 lines | ~20 lines plus shared-state discipline | 60–100 lines, plus buffer ownership, plus error flags |
| **Failure mode when overloaded** | Misses the deadline visibly, blocks everything | Overrun error, or an interrupt storm that starves the main loop | Silent overwrite of unread data in the ring |
| **It wins when** | Nothing else must run, or the wait is sub-microsecond, or it is init code | The event is asynchronous, infrequent relative to the CPU, and the response is short | The rate is high, the data is a stream, and the CPU has other work |

The row people skip is the last-but-one. Each mechanism fails differently under overload, and the DMA row is the dangerous one: it does not complain. A UART interrupt that cannot keep up sets `ORE` and you can count it. A DMA ring that wraps before you drained it overwrites your unread bytes with no flag anywhere ([UART in Depth](../05-peripherals-and-drivers/uart-in-depth.md) shows the half-transfer and transfer-complete interrupts that exist to catch exactly this).

## Worked example: polling, and why it is right

**A serial bootloader receiving a firmware image at 115200 baud 8N1.**

The numbers: 10 bits per byte, so 11 520 bytes/s, one byte every **86.8 µs**. The deadline to read `USART_DR` is one byte time, because the next byte arrives then and sets `ORE`.

The whole receive path:

```c
static uint8_t uart_getc(void)
{
    while ((USART2->SR & USART_SR_RXNE) == 0u) { }   /* spin */
    return (uint8_t)USART2->DR;                       /* clears RXNE */
}
```

Three lines, no shared state, no `volatile`, no critical section, no possibility of a race, and a latency measured in tens of nanoseconds. CPU cost is 100 % — and it is 100 % of a CPU that has nothing else to do, because a bootloader's only job is to receive the image and write it to flash. Buying an interrupt-driven receiver here would add a ring buffer, a handler, an overrun path and a class of concurrency bug, in exchange for freeing cycles that would then be spent spinning in the main loop waiting for the same bytes.

The same argument makes polling right for: peripheral initialisation (`while (!(RCC->CR & RCC_CR_HSERDY)) {}`), the SPI `BSY` flag between short transactions at 25 Mbit/s, an I²C sensor read during startup, and any state machine whose next step is gated on a bit that will be set within a microsecond.

Where polling stops being right is the moment there is a second thing to do. The instant the main loop also refreshes a display, the polled latency for the UART becomes "one whole trip round the main loop, worst case" — which is nobody's design, and is where "it drops characters when the screen updates" comes from.

## Worked example: interrupt, and where it saturates

**A command interface on USART2 at 115200, in a product with a main loop doing real work.**

One byte every 86.8 µs. Per-byte cost: ~300 ns of overhead plus a handler that reads `DR`, checks the error flags, and pushes into a ring — call it another 200 ns. So **~500 ns per byte out of 86.8 µs = 0.6 % of the CPU**, and the main loop never has to know a UART exists. This is the case interrupts were designed for and the design is correct without further thought.

Now scale the same design up and watch it fail:

| Baud | Byte period | Bytes/s | CPU at ~500 ns/byte |
|---|---|---|---|
| 9 600 | 1.04 ms | 960 | 0.05 % |
| 115 200 | 86.8 µs | 11 520 | 0.6 % |
| 921 600 | 10.85 µs | 92 160 | 4.6 % |
| 2 000 000 | 5 µs | 200 000 | 10 % |

Ten per cent of the core spent moving bytes one at a time is the point at which the argument is over. And the CPU percentage understates the harm: at 200 000 interrupts per second, the *other* interrupts in the system are being delayed by up to one handler duration each time, and the ART accelerator is being churned by a handler that runs every 5 µs.

The general shape: **an interrupt per event is the right answer while events are rare relative to the CPU, and the wrong one as soon as they are not.** The transition is not sharp, but 100 kHz on a 100 MHz M4 is a reasonable place to draw the line.

## Worked example: DMA, and what it actually buys

**Continuous ADC sampling at 50 kHz into a circular buffer.**

Per-sample interrupts would be 50 000 events/s ≈ 1.5 % of the core in overhead alone, plus a handler per sample — survivable, and completely unnecessary. The circular stream in [DMA](../05-peripherals-and-drivers/dma.md) uses a 512-entry buffer processed in halves of 256, with both the half-transfer and transfer-complete interrupts enabled:

- Interrupt rate drops from 50 000/s to **50 000 / 256 = 195/s** — a factor of 256.
- The handler now processes 256 samples at once, which is also where block-oriented DSP wants them.
- The CPU cost per sample is not zero, but it is amortised: one entry and exit per 256 samples instead of per sample.
- The cost that replaces it is bus contention — two bus transactions per sample, arbitrated round-robin against the core (RM0383 Rev 4 §2.1.6). At 50 kHz that is invisible; at 2 Msps it is a real term in your WCET.

The same structure is the right answer for UART reception on a fast link, where the DMA plus the `IDLE` flag gives message-boundary interrupts instead of byte interrupts ([UART in Depth](../05-peripherals-and-drivers/uart-in-depth.md) has the mechanism), and for driving a display, where the whole frame is one transfer.

What DMA does **not** buy:

- **It does not reduce latency for a single event.** A one-byte transfer through DMA arrives no sooner, and you find out about it later.
- **It does not reduce CPU cost if you take an interrupt per transfer.** Configuring a fresh single-item transfer from the completion handler of the previous one is a per-item interrupt with extra steps, and it is slower than just reading the register.
- **It does not remove the concurrency problem.** It moves it: instead of an ISR racing `main`, a bus master races `main`, and the buffer ownership rules become the thing you have to get right.

## Hybrids, which is what most real drivers are

The three options are not exclusive, and the good designs mix them:

- **DMA for the payload, interrupt for the boundary.** Circular DMA receive plus `IDLE`-line detection: zero CPU per byte, one interrupt per message.
- **Interrupt for arrival, poll for the rest of the burst.** Take one interrupt when the first byte of a packet arrives, then poll for the remaining bytes if they are only microseconds apart. Costs one entry instead of *n*.
- **Poll a DMA counter instead of taking its interrupt.** `NDTR` counts down and is readable at any moment, so the main loop can ask "how far has it got" with a single load and no interrupt at all. This is the cheapest possible notification mechanism and it is under-used:

  ```c
  /* Circular RX DMA. No interrupt of any kind; called from the superloop. */
  static size_t rx_tail;

  void rx_poll(void)
  {
      size_t head = RX_RING_SIZE - (size_t)DMA1_Stream5->NDTR;   /* counts down */

      while (rx_tail != head) {
          handle(rx_ring[rx_tail]);
          rx_tail = (rx_tail + 1u) & (RX_RING_SIZE - 1u);
      }
  }
  ```

  Zero interrupts, zero shared-state hazard on the producer side (the DMA writes only the buffer, the loop writes only `rx_tail`), and a latency of one superloop period. The one thing it cannot do is detect that the ring wrapped past unread data — if that is possible in your system, you need the half-transfer interrupt as a backstop.
- **Peripheral FIFOs where they exist**, which convert *n* events into one. The STM32F411's USART has no receive FIFO, which is precisely why DMA is the answer for fast links on this part; on families that do have one, the interrupt-per-byte crossover moves out by the FIFO depth.

## Measuring, so the decision is not a guess

Every number on this page is an estimate until you check it on your board. Two measurements settle the argument, and both cost about ten minutes.

**How much CPU is the interrupt path actually using?** Count free iterations of an idle loop and compare against a calibration run with the peripheral quiet:

```c
static volatile uint32_t idle_count;

/* In the superloop, after all real work is done: */
for (;;) {
    do_work();
    idle_count++;          /* only reached when there is nothing to do */
}
```

Sample `idle_count` once per second from a timer handler. Run the system with the traffic switched off to get the baseline, then with it at full rate. The ratio is the CPU fraction the path is consuming — including the handler, the exception entry and exit, and the ART churn, none of which a cycle count of the handler body alone would capture.

**How long is one handler actually taking?** Latch `DWT->CYCCNT` at the first and last statement of the handler and keep a running maximum:

```c
void USART2_IRQHandler(void)
{
    uint32_t t0 = DWT->CYCCNT;
    /* ... the handler ... */
    uint32_t dt = DWT->CYCCNT - t0;          /* wraps correctly: unsigned */
    if (dt > isr_worst) { isr_worst = dt; }  /* ISR-private, no race */
}
```

`DWT_CYCCNT` lives at `0xE0001004` and needs `DEMCR.TRCENA` set before `DWT_CTRL.CYCCNTENA` (*Armv7-M ARM* §C1.8). The unsigned subtraction is correct across the 32-bit wrap, which at 100 MHz happens every 43 seconds. Record the **maximum**, not the mean — the mean tells you about CPU load, the maximum tells you about latency, and they lead to different decisions.

With those two numbers the table above stops being advice and becomes arithmetic: if the path costs 6 % of the CPU and you need that 6 %, move to DMA; if it costs 0.4 %, the argument is over and you should go and do something else.

:::warning[The DMA driver that used more CPU than the interrupt driver it replaced]
The most common way to spend two days and go backwards, and it looks like progress the whole time.

The pattern: a UART receive path taking one interrupt per byte is measured at 5 % CPU and rewritten to use DMA. The new driver configures a transfer of *one byte*, enables the transfer-complete interrupt, and in that handler re-arms the stream for the next byte. It works. It is measured at **7 %**, because every byte now costs an interrupt *plus* a stream reconfiguration — `NDTR`, `M0AR`, a disable, a poll of `EN` until the hardware clears it, and a re-enable — and RM0383 Rev 4 §9.3.14 requires that poll, so it is not optional. The old path did one register read.

The tell is that the DMA is not being used as DMA. DMA earns its cost only when one configuration covers many items: circular mode, or a transfer whose length is a whole message. If your completion handler's job is to set up the next transfer, you have written an interrupt-driven driver with more moving parts.

The second version of the same mistake is subtler and worse: circular DMA is set up correctly, the half-transfer interrupt is *not* enabled, and only transfer-complete is. The consumer therefore learns about data one full buffer late, and while it is processing the first half, the controller is already overwriting it — because in circular mode the stream never stops. The symptom is intermittently corrupted data at the *start* of each block, appearing only when the consumer is slow, which sends everyone looking at the parser. Enable both `HTIE` and `TCIE`, always, and treat each half as owned by exactly one side at a time.
:::

## See also

- [Interrupt Latency](./interrupt-latency.md) — where the ~300 ns per-event overhead comes from and how to measure your own.
- [Deferred Work](./deferred-work.md) — what to do inside the interrupt once you have chosen it, so the handler stays short.
- [DMA](../05-peripherals-and-drivers/dma.md) — the controller, circular mode, the half-transfer interrupt, and the arbitration cost this page prices.
- [UART in Depth](../05-peripherals-and-drivers/uart-in-depth.md) — the worked hybrid: circular DMA plus `IDLE`-line detection, and the overrun error that polling and interrupts both have to handle.
- [The Anatomy of a Peripheral](../05-peripherals-and-drivers/anatomy-of-a-peripheral.md) — the status-flag and enable conventions that every polling loop on this part is written against.

## References

- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), Rev 4. §9 for the DMA controller: §9.3.4 for stream arbitration, §9.3.11 and §9.3.12 for burst and FIFO-threshold constraints, §9.3.14 for the mandatory disable-and-poll before reconfiguring a stream; §2.1.6 for the bus-matrix round-robin that decides what a stream costs the core; §19 for the USART status flags the polling example tests.
- Arm — [***Cortex-M4 Technical Reference Manual***](https://developer.arm.com/documentation/ddi0439/latest/) (DDI 0439), exception-handling chapter. The 12-cycle entry figure that the ~300 ns per-event overhead is derived from, quoted for zero-wait-state memory on this processor implementation.
- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), Rev 10. §2.3.7 for the exception entry and return sequence being priced here; §4.3 for the NVIC registers a driver enables once it has chosen the interrupt option.
- STMicroelectronics — [**AN4031**, *Using the STM32F2, STM32F4 and STM32F7 Series DMA controller*](https://www.st.com/resource/en/application_note/an4031-using-the-stm32f2-stm32f4-and-stm32f7-series-dma-controller-stmicroelectronics.pdf). ST's own treatment of when to use DMA over interrupts on this family, with the bandwidth and latency figures for the bus matrix that the "what a stream costs" argument rests on.
