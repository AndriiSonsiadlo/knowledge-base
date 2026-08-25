---
id: dma
title: DMA
sidebar_label: DMA
sidebar_position: 9
tags: [embedded, peripherals, dma, circular-buffer, double-buffer, cache-coherency, stm32]
---

# DMA

A DMA controller is not an accelerator bolted onto a peripheral. It is **a second bus master**: a small, dumb machine that sits on the same bus matrix as the Cortex-M4 and, when a peripheral raises a request line, performs the load and the store that your interrupt handler would otherwise have performed. It has no idea what the data means. It knows a source address, a destination address, a count, and whether to increment each pointer.

That framing explains both of the things people get wrong about it. It is not free — every transfer it performs is a bus cycle the core did not get, so a stream running flat out steals cycles from your code even though no interrupt fired. And it is not smart — it will happily keep writing into a buffer you have already finished with, keep servicing a peripheral you thought you had stopped, and never once tell you that the data it delivered is stale. Everything a DMA driver has to do is about *knowing where the machine has got to*, because the machine will not volunteer it.

The single most useful thing the STM32F4 controller offers for that is the **half-transfer interrupt**. It turns one circular buffer into a double buffer, for free, with no second allocation and no pointer swap — and it is the mechanism the rest of this page is built around.

:::info[Prerequisites]
[The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md) owns the clock/reset/configure/enable sequence that a DMA stream follows like any other block; this page covers only what is DMA-specific. [Interrupt Handlers in C](../04-bare-metal-programming/interrupt-handlers-in-c.md) and [Critical Sections and Atomicity](../04-bare-metal-programming/critical-sections-and-atomicity.md) cover the handler side — a DMA completion handler shares state with `main` exactly like any other ISR.
:::

## Streams, channels, and the mapping you do not get to choose

The F411 has **two DMA controllers, DMA1 and DMA2, with eight streams each**. A *stream* is the transfer engine: it owns the source and destination addresses, the count, the direction and the FIFO. A *channel* is which of up to eight peripheral request lines that stream listens to, selected by `CHSEL[2:0]` in `DMA_SxCR` (RM0383 §9.3.3, "Channel selection").

The consequence catches everyone once: **a given peripheral request appears at exactly one or two fixed (stream, channel) pairs, and nowhere else.** You do not assign a peripheral to a stream; you look it up. On this part, from RM0383 Table 27 and Table 28:

| Request | Controller | Stream | Channel |
|---|---|---|---|
| `USART2_RX` | DMA1 | 5 | 4 |
| `USART2_TX` | DMA1 | 6 | 4 |
| `SPI1_RX` | DMA2 | 0 or 2 | 3 |
| `SPI1_TX` | DMA2 | 3 or 5 | 3 |
| `ADC1` | DMA2 | 0 or 4 | 0 |
| `TIM1_UP` | DMA2 | 5 | 6 |

Two peripherals that collide on the same stream cannot both use DMA, full stop — you move one to interrupts or find its alternate stream. Discovering that after the schematic is fixed is how a pin assignment becomes a software problem.

Two further constraints worth knowing before you design around them:

- **Only DMA2 can perform memory-to-memory transfers** (RM0383 §9.2). DMA1 has no software-trigger path. A `memcpy` offloaded to DMA1 simply never starts.
- **Each stream has an independent 4-word FIFO** (RM0383 §9.3.12), with a threshold of ¼, ½, ¾ or full. In *direct mode* (the reset state) the FIFO is bypassed and each request moves one item immediately. Disabling direct mode with `DMDIS` lets the stream batch accesses and burst them, which is what makes a stream cheap on the bus rather than merely functional.

## The half-transfer interrupt as a double buffer

Set `CIRC` in `DMA_SxCR` and the stream reloads `NDTR` and the memory pointer at the end of every pass, so it runs forever. That alone is not useful — the CPU still has to read the buffer while the DMA is writing it, and the two will collide. What makes it useful is that the controller raises **`HTIF` exactly halfway through** (RM0383 §9.4), which partitions the buffer in time:

```wavedrom title="One circular buffer, two halves. HTIF hands the CPU the first half; TCIF hands it the second. The DMA is never writing the half the CPU is reading" alt="Waveform showing DMA writes alternating between the first and second halves of a circular buffer, the half-transfer flag asserting when the first half is complete, the transfer-complete flag asserting when the second half is complete, and the CPU processing the opposite half in each interval"
{ "signal": [
  { "name": "DMA writes", "wave": "3.....4.....3.....4.....", "data": ["first half","second half","first half","second half"] },
  { "name": "HTIF",       "wave": "0.....10....0.....10...." },
  { "name": "TCIF",       "wave": "0...........10.........." },
  { "name": "CPU reads",  "wave": "x.....3.....4.....3.....", "data": ["first half","second half","first half"] }
],
  "config": { "hscale": 1 }
}
```

The invariant is the whole point: **at every instant the DMA is writing one half and the CPU is reading the other.** Nothing is copied, nothing is swapped, and there is no window in which both touch the same bytes. A 512-sample buffer with `HTIF` and `TCIF` enabled gives the application 256 samples at a time with a full 256-sample interval to process them in — which is exactly the deadline you must meet, and exactly the number to put in a comment.

The deadline is the part to take seriously. If processing a half takes longer than the DMA takes to fill the other half, the DMA laps you and there is **no flag for it**. The overrun is silent: you read a buffer that is being overwritten under you and get a seam of new data spliced into old. The defence is a counter incremented in the handler and decremented by the consumer, checked for drift — the same discipline as a ring buffer, because that is what this is.

### Hardware double-buffer mode, and when to prefer it

The F4 also has a genuine two-pointer mode: set `DBM` in `DMA_SxCR`, load `M0AR` and `M1AR`, and the controller swaps between them at every end-of-transaction (RM0383 §9.3.9). `CIRC` is implied and ignored. The `CT` bit tells you which pointer is live.

| | Circular + `HTIF`/`TCIF` | `DBM` double buffer |
|---|---|---|
| Buffers | One, split in halves | Two, independent addresses |
| Interrupts per pass | Two (`HTIF`, `TCIF`) | One (`TCIF`) per buffer |
| Buffer address changeable at run time | No — write-protected while `EN` is set | Yes, the *inactive* one only |
| Which half is safe | Inferred from which flag fired | Read `CT` |
| Buffers must be adjacent | Yes | No |

The reason to reach for `DBM` is the third row. In circular mode the memory address registers are write-protected as soon as the stream is enabled; in `DBM` you may rewrite the pointer that is *not* currently in use, which is what lets you feed a stream from a pool of buffers rather than a fixed pair. RM0383 §9.3.9 is explicit about the hazard: writing `M0AR` while `CT = 0`, or `M1AR` while `CT = 1`, **sets `TEIF` and disables the stream**. Change the address as soon as `TCIF` fires, when the swap has just happened and the rule is unambiguous.

For a fixed-size acquisition buffer, plain circular with `HTIF` is simpler and has fewer ways to go wrong. Use `DBM` when the buffers must come from somewhere else.

## A worked stream: ADC to memory, circular, half-transfer driven

The bring-up follows the universal sequence from [The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md); what is DMA-specific is step 4, and the mandatory disable-and-wait in front of it.

```c title="adc_dma.c — DMA2 Stream 0, Channel 0: ADC1 into a circular buffer"
#include "stm32f4xx.h"

#define ADC_BUF_LEN 512u                       /* halves of 256 samples */
static volatile uint16_t adc_buf[ADC_BUF_LEN];

void adc_dma_init(void)
{
    RCC->AHB1ENR |= RCC_AHB1ENR_DMA2EN;
    (void)RCC->AHB1ENR;                        /* read-back guard */

    /* The stream must be OFF and observed off before any field is written.
     * EN is cleared by hardware asynchronously; polling it is not optional. */
    DMA2_Stream0->CR &= ~DMA_SxCR_EN;
    while (DMA2_Stream0->CR & DMA_SxCR_EN) { }

    /* Stale flags from a previous run would fire the handler immediately. */
    DMA2->LIFCR = DMA_LIFCR_CTCIF0 | DMA_LIFCR_CHTIF0 | DMA_LIFCR_CTEIF0
                | DMA_LIFCR_CDMEIF0 | DMA_LIFCR_CFEIF0;

    DMA2_Stream0->PAR  = (uint32_t)&ADC1->DR;
    DMA2_Stream0->M0AR = (uint32_t)adc_buf;
    DMA2_Stream0->NDTR = ADC_BUF_LEN;          /* items, not bytes */

    DMA2_Stream0->CR =
          (0u << DMA_SxCR_CHSEL_Pos)           /* channel 0 = ADC1        */
        | (2u << DMA_SxCR_PL_Pos)              /* priority high           */
        | DMA_SxCR_MSIZE_0                     /* memory  = 16-bit        */
        | DMA_SxCR_PSIZE_0                     /* periph  = 16-bit        */
        | DMA_SxCR_MINC                        /* increment memory only   */
        | DMA_SxCR_CIRC                        /* wrap forever            */
        | DMA_SxCR_HTIE | DMA_SxCR_TCIE        /* both halves             */
        | DMA_SxCR_TEIE | DMA_SxCR_DMEIE;      /* and both error sources  */
        /* DIR = 00: peripheral-to-memory (reset value, left implicit)    */

    DMA2_Stream0->FCR = 0u;                    /* direct mode: FIFO bypassed */

    NVIC_SetPriority(DMA2_Stream0_IRQn, 6u);
    NVIC_EnableIRQ(DMA2_Stream0_IRQn);

    DMA2_Stream0->CR |= DMA_SxCR_EN;           /* last, on its own */
}

void DMA2_Stream0_IRQHandler(void)
{
    uint32_t isr = DMA2->LISR;

    if (isr & DMA_LISR_HTIF0) {
        DMA2->LIFCR = DMA_LIFCR_CHTIF0;        /* write-1-to-clear, never |= */
        process(&adc_buf[0], ADC_BUF_LEN / 2u);
    }
    if (isr & DMA_LISR_TCIF0) {
        DMA2->LIFCR = DMA_LIFCR_CTCIF0;
        process(&adc_buf[ADC_BUF_LEN / 2u], ADC_BUF_LEN / 2u);
    }
    if (isr & (DMA_LISR_TEIF0 | DMA_LISR_DMEIF0)) {
        DMA2->LIFCR = DMA_LIFCR_CTEIF0 | DMA_LIFCR_CDMEIF0;
        dma_fault();                            /* the stream is already off */
    }
}
```

Three details in there are load-bearing rather than decorative:

- **`NDTR` counts items, not bytes**, and it counts *down*. The current write index is `LEN - NDTR`, which is how you get a byte-accurate position at any moment without an interrupt at all — the trick [UART in Depth](./uart-in-depth.md) uses for idle-line framing.
- **The error interrupts are enabled.** A transfer error disables the stream in hardware; without `TEIE` the symptom is a peripheral that "stops working after a while" with no flag anyone looked at.
- **`ADC1->DR` is on APB2, the buffer is in SRAM**, and the stream touches both through separate AHB ports. That is why arbitration matters, next.

## Arbitration, and what a stream costs

Each controller arbitrates its own eight streams in two stages (RM0383 §9.3.4): first the software priority in `PL[1:0]` — four levels — and then, for equal levels, **the lower stream number wins**. That second rule is hardware and cannot be overridden, which is worth knowing when two equally urgent streams are on stream 2 and stream 6.

Above that sits the bus matrix, which arbitrates between the DMA controllers and the Cortex-M4 itself using round-robin (RM0383 §2.1.6). The practical consequences:

- **A stream running in direct mode costs two bus transactions per item** — one read on the peripheral port, one write on the memory port. At an audio-rate ADC that is invisible; at 2 Msps it is not.
- **Bursting is how you make it cheap.** Disable direct mode (`DMDIS`), set a FIFO threshold, and set `MBURST`, and four items move in one burst instead of four separate arbitrations. The constraint RM0383 §9.3.12 states plainly: the FIFO threshold must correspond to an exact whole number of bursts, or the stream sets `FEIF` and **disables itself the moment you enable it**. Burst size × data size must not exceed the four-word FIFO.
- **Bursts must not cross a 1 KB address boundary** (RM0383 §9.3.11) — the maximum region an AHB slave may occupy. The manual notes that violating it produces an AHB error that *is not reported in the DMA registers*, which is as close to "undebuggable" as the peripheral gets.

### The flags, as bits

```wavedrom title="DMA_LISR, low half — five flags per stream for streams 0 and 1; streams 2 and 3 occupy bits 16–27" alt="Bit-field strip of the low half of the DMA low interrupt status register showing FIFO error, direct-mode error, transfer error, half-transfer and transfer-complete flags for stream 0 in bits 0 to 5 and the same five flags for stream 1 in bits 6 to 11"
{ "reg": [
    { "bits": 1, "name": "FEIF0",  "type": 4 },
    { "bits": 1, "name": "res",    "type": 1 },
    { "bits": 1, "name": "DMEIF0", "type": 4 },
    { "bits": 1, "name": "TEIF0",  "type": 4 },
    { "bits": 1, "name": "HTIF0",  "type": 2 },
    { "bits": 1, "name": "TCIF0",  "type": 3 },
    { "bits": 1, "name": "FEIF1",  "type": 4 },
    { "bits": 1, "name": "res",    "type": 1 },
    { "bits": 1, "name": "DMEIF1", "type": 4 },
    { "bits": 1, "name": "TEIF1",  "type": 4 },
    { "bits": 1, "name": "HTIF1",  "type": 2 },
    { "bits": 1, "name": "TCIF1",  "type": 3 },
    { "bits": 4, "name": "reserved", "type": 1 }
  ],
  "config": { "bits": 16, "lanes": 1, "hspace": 900 }
}
```

| Bits | Field | Access | Reset | Meaning |
|---|---|---|---|---|
| 0, 6 | `FEIFx` | r | `0` | FIFO error: overrun, underrun, or a threshold/burst mismatch. |
| 2, 8 | `DMEIFx` | r | `0` | Direct-mode error: a new request arrived before the previous item was moved. |
| 3, 9 | `TEIFx` | r | `0` | Transfer error — a bus error on either port. **The stream is disabled by hardware.** |
| 4, 10 | `HTIFx` | r | `0` | Half of `NDTR` transferred. The double-buffer signal. |
| 5, 11 | `TCIFx` | r | `0` | Transfer complete. In circular mode, one pass finished and `NDTR` has reloaded. |
| 1, 7, 12–15 | reserved | r | `0` | Read as zero. |

All five are **read-only here and cleared by writing 1 to the matching bit in `DMA_LIFCR`** (RM0383 §9.5.3). Never `|=` that register: a read-modify-write clears every flag that happened to be set at read time, including one another context had not handled. Streams 4–7 live in `DMA_HISR`/`DMA_HIFCR` with the same layout.

## Cache coherency: not a problem on this board, and why

This is the DMA topic that generates the most confused advice, so state it precisely.

**The STM32F411's Cortex-M4 has no data cache and no instruction cache.** There is nothing between the core and SRAM that can hold a stale copy of a DMA buffer. A store by the DMA controller into SRAM is visible to the next load by the core, and vice versa. On this part you do not clean, you do not invalidate, and any code you find that calls `SCB_CleanDCache_by_Addr()` on an F4 is either copied from an F7 project or defensive noise. (The `FLASH_ACR` bits named `ICEN` and `DCEN` are ART-accelerator buffers in the *flash interface* — RM0383 §3.4.2 — not core caches, and they cache flash reads only, which the DMA does not write.)

**The problem is real on Cortex-M7 parts** — the STM32F7 and STM32H7 series — which have a 4–16 KB L1 data cache. There the two failure directions are:

- **Memory to peripheral.** You fill a transmit buffer; the writes sit in the D-cache; the DMA reads main memory and sends whatever was there before. Fix: `SCB_CleanDCache_by_Addr()` *before* starting the stream.
- **Peripheral to memory.** The DMA writes main memory; the core reads a cached line from before the transfer and sees old data. Fix: `SCB_InvalidateDCache_by_Addr()` *after* the transfer completes.

The trap specific to invalidation is granularity: the cache line is 32 bytes, so invalidating a buffer that shares a line with an unrelated variable **discards that variable's cached value too**. DMA buffers on an M7 are aligned to 32 bytes and padded to a multiple of 32, or they corrupt their neighbours. The alternative, and usually the better answer, is to place DMA buffers in a memory region configured as non-cacheable via the MPU, or in a `.dma` section in a RAM the cache does not cover, and stop performing maintenance by hand.

What *does* still apply on the F411 is the compiler-level half of the same problem: a buffer the DMA writes must be `volatile` (or the DMA handover must be separated from the reads by a compiler barrier), or the optimiser is entitled to keep a value in a register across the transfer. That is not a cache; it is [what `volatile` does and does not do](../04-bare-metal-programming/volatile-and-the-compiler.md), and it bites on every Cortex-M.

:::warning[The stream that would not reconfigure, and the handler that fired before `init()` returned]
Two DMA failures with the same non-symptom: the code is right, nothing faults, the transfer is wrong.

**Reconfiguring a stream that is still running.** Clearing `EN` in `DMA_SxCR` does not take effect immediately — the controller finishes the transaction in flight and any data already in the FIFO first, and only then clears `EN` in hardware. Writing `PAR`, `M0AR` or `NDTR` during that window is discarded silently, so the stream restarts pointing at the *old* buffer with the *old* count. The symptom is a driver that works the first time and delivers data into a freed or reused buffer on every subsequent call, which presents as heap corruption or as one client of a shared SPI bus receiving another client's bytes. The tell in a debugger is that `DMA2_Stream0->M0AR` does not hold the address your code just wrote. The fix is the two lines in the listing above — clear `EN`, then `while (CR & EN) { }` — and RM0383 §9.3.14 documents exactly this: software must wait until `EN` reads 0 before reconfiguring. Note that this also means a "stop the transfer" API cannot be a single register write; it has to poll.

**Enabling an interrupt on a flag that is already set.** `HTIF`, `TCIF` and the error flags survive reconfiguration and survive the stream being disabled. Set `HTIE` while `HTIF` is still set from the previous run and the handler is entered *before* `init()` returns, into a driver whose buffer pointer and index are half-written. Symptom: a first pass of garbage after every re-initialisation, and only after a re-initialisation — so it never reproduces on a cold boot, only on the retry path or the second connection. RM0383 §9.4 states the rule as a note: "Before setting an Enable control bit to 1, the corresponding event flag should be cleared, otherwise an interrupt is immediately generated." Write the `DMA_LIFCR`/`HIFCR` clear into your init function unconditionally, not as error handling.
:::

:::note[Streams are an F2/F4/F7 concept, not a Cortex-M one]
The stream-and-channel controller described here is specific to the STM32F2/F4/F7 families. The STM32F1, L0, L4 and G0 use a simpler *channel-only* DMA with no FIFO, no bursts and no double-buffer mode, where the peripheral mapping is fixed per channel; the L4 and G4 add a DMAMUX that makes any request reachable from any channel, removing the lookup table above entirely. The concepts — circular mode, half-transfer, count-down `NDTR` — carry across; the register names and the constraint that a peripheral has only one home do not.
:::

## See also

- [UART in Depth](./uart-in-depth.md) — circular DMA reception with idle-line detection, the canonical use of `NDTR` as a live write position rather than as a completion count.
- [ADC and DAC Drivers](./adc-and-dac-drivers.md) — the peripheral that makes DMA mandatory rather than optional, because a multi-channel sequence overruns a single data register within microseconds.
- [The Anatomy of a Peripheral](./anatomy-of-a-peripheral.md) — the clock/reset/configure/enable sequence a stream follows, and the write-1-to-clear flag family `DMA_LIFCR` belongs to.
- [Interrupt Handlers in C](../04-bare-metal-programming/interrupt-handlers-in-c.md) — what a half-transfer handler may and may not do, and how it shares state with the consumer safely.
- [CPU Caches](../../computer-science/memory-hierarchy/cpu-caches.md) — the cache theory behind the M7 coherency problem this part does not have.

## References

- STMicroelectronics — [**RM0383**, *STM32F411xC/E advanced Arm-based 32-bit MCUs reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at Rev 2 (DocID026448). §9.3.3 and Tables 27–28 for the stream/channel request mapping; §9.3.4 for the two-stage arbiter; §9.3.8–§9.3.9 for circular and double-buffer mode including the `M0AR`/`M1AR` write rule and the `TEIF` it sets when broken; §9.3.12 for the 4-word FIFO, thresholds and the burst constraint; §9.3.14 for the requirement to poll `EN` to zero before reconfiguring; §9.4 for the five interrupt sources and the note about clearing flags before enabling.
- STMicroelectronics — [**AN4031**, *Using the STM32F2, STM32F4 and STM32F7 Series DMA controller*](https://www.st.com/resource/en/application_note/an4031-using-the-stm32f2-stm32f4-and-stm32f7-series-dma-controller-stmicroelectronics.pdf). The application-level companion to the RM chapter: bandwidth budgeting per stream, FIFO threshold and burst sizing worked through with numbers, and the round-robin bus-matrix behaviour when several masters contend.
- STMicroelectronics — [**AN4839**, *Level 1 cache on STM32F7 Series and STM32H7 Series*](https://www.st.com/resource/en/application_note/an4839-level-1-cache-on-stm32f7-series-and-stm32h7-series-stmicroelectronics.pdf). The M7 coherency problem this page says does not apply to the F411: which maintenance operation belongs on which side of a transfer, the 32-byte line-alignment requirement for DMA buffers, and the MPU-based alternative.
- Arm — [**CMSIS-Core (Cortex-M) documentation**](https://arm-software.github.io/CMSIS_6/latest/Core/index.html). `SCB_CleanDCache_by_Addr` and `SCB_InvalidateDCache_by_Addr` — including that they are compiled out on parts without a cache, which is why the wrong advice above is harmless on an F4 and merely misleading.
- STMicroelectronics — [**STM32CubeF4 HAL/LL driver source**](https://github.com/STMicroelectronics/STM32CubeF4). `Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal_dma.c` for ST's own disable-and-poll implementation in `HAL_DMA_Abort()`, which is the same `while (EN)` loop this page argues you cannot skip.
