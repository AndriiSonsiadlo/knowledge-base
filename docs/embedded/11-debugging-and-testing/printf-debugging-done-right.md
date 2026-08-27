---
id: printf-debugging-done-right
title: Logging Without Breaking Timing
sidebar_label: Logging Without Breaking Timing
sidebar_position: 3
tags: [embedded, debugging, logging, itm, swo, rtt, semihosting, dma, cortex-m]
---

# Logging Without Breaking Timing

Here is the observation this page exists to explain. You have a fault that happens once every few minutes — a corrupted buffer, a missed deadline, a state machine that ends up somewhere it cannot reach. You add a `printf` to narrow it down. The fault stops happening. You remove the `printf` and it comes back.

That is not a mystery and it is not bad luck. `printf` over a blocking UART at 115200 baud costs **about 3.5 milliseconds for a forty-character line**, and the derivation is arithmetic anyone can check: 8N1 framing is one start bit, eight data bits and one stop bit, so 10 bit-times per byte; at 115200 baud one bit-time is 8.68 µs and one byte is 86.8 µs; forty bytes is 3.47 ms. At 100 MHz that is **347,000 core cycles** during which your firmware does nothing but wait on a `TXE` flag. You did not add a diagnostic. You added a three-and-a-half-millisecond stall into a code path, and every race, every deadline, and every interrupt-arrival window in the system moved.

The mental model that follows: **a log statement is a piece of the program, and it must be cheap enough that its presence does not change the program's behaviour.** Not "cheap enough not to matter for throughput" — cheap enough that a timing-dependent bug still reproduces with logging on. That is a hard requirement, it rules out blocking `printf` entirely, and everything below is a way of meeting it.

If adding logging makes the bug disappear, treat that as a result rather than a nuisance. You have just learned that the fault is timing-dependent, which narrows the search enormously: a race between an ISR and a main-loop reader, a peripheral whose flag is being polled too late, an unhandled overrun, a deadline that was already marginal.

:::info[Prerequisites]
[SysTick and the Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md) owns the ITM: what a stimulus port is, the `DEMCR.TRCENA` / lock-key / `TCR` / `TER` bring-up order, and the unguarded-write hang. [UART In Depth](../05-peripherals-and-drivers/uart-in-depth.md) owns the framing and the DMA-with-idle-line reception this page's transmit path is the mirror of. [DMA](../05-peripherals-and-drivers/dma.md) owns the transfer mechanics.
:::

## The four transports, and what each costs

| Transport | What one log call costs the core | Sustained throughput | Needs a probe? | Intrusiveness |
|---|---|---|---|---|
| **Semihosting** | A `BKPT 0xAB`, then **the core is halted** until the host services it — order of **milliseconds** per call | Irrelevant; the bottleneck is the halt | **Yes, always** | **Extreme.** Nothing runs, including interrupts |
| **Blocking UART `printf`** | Formatting, then a busy-wait on the wire: **86.8 µs per byte at 115200** | 11.5 KB/s | No | High — the core waits for the wire |
| **SWO / ITM** | One store to a PPB address, a few core cycles (**tens of ns**), plus a wait if the FIFO is full | SWO baud limited; at 2 MHz NRZ, **~100 KB/s of payload** | Yes (SWO pin) | Low |
| **SEGGER RTT** | A `memcpy` into a RAM ring buffer — **"one microsecond or less" for a line of text** | SEGGER: up to ~3.5 MB/s in background mode | Yes (probe reads RAM) | Low |
| **DMA-backed UART ring** | A `memcpy` into a RAM ring buffer, ~**1 µs**; the DMA drains it later | UART baud limited: 11.5 KB/s at 115200, 460 KB/s at 4.6 Mbaud | **No** | Low, until the ring fills |

Reading the throughput column carefully matters, because it is a different constraint from the per-call cost. RTT's per-call cost is a `memcpy`; if you log faster than the probe drains the buffer, you either block or drop — the buffer size and the drop policy become the design decision, not the transport.

The SWO figure is derived and worth showing the working for, because you will want to redo it for your own probe. An 8-bit ITM stimulus write produces a two-byte packet on the wire (one header byte, one payload byte). SWO in NRZ mode is UART-framed at 10 bit-times per byte. At a 2 MHz trace clock — a common ST-LINK/V2-1 setting — that is 200,000 bytes/s on the wire and therefore about **100,000 payload bytes per second**. Writing 32-bit words instead (`ITM->PORT[0].u32`) gives five bytes per packet for four of payload and lifts the payload rate to about 160 KB/s. Neither number is a spec; both are consequences of the encoding.

## Semihosting is the most intrusive option, by a very long way

Semihosting works by executing `BKPT 0xAB` with a request code in `R0`. The processor takes a debug halt, the host's debugger notices, reads the argument block out of target memory, performs the file operation on the host's own filesystem, writes the result back, and resumes the core. The appeal is obvious — `printf` works with no UART, no pins, and no target-side driver, and you also get `fopen` on the host's disk.

The cost is that **the entire processor is stopped for the duration**, and the duration is a USB round trip to your laptop. That is not a hundred cycles; on any real setup it is a hundred thousand or more. Measure it on your own probe rather than trusting a number, but the shape is unambiguous: it is three orders of magnitude worse than a UART write and six worse than an ITM store.

The stall has a property the others do not, and this is what makes it categorically different: **interrupts do not run either.** A blocking UART `printf` at least lets your ISRs fire. A semihosting call halts the core, so a SysTick that should have ticked does not, a UART that receives during the call overruns, and a watchdog whose refresh was due is missed. Anything with a real-time constraint is not merely slowed, it is suspended.

Two more traps, both of which ship:

- **With no debugger attached, the `BKPT` faults.** No host is listening, nothing services the halt request, and on a Cortex-M4 the breakpoint becomes a HardFault with `HFSR.DEBUGEVT` set — see [HardFault Forensics](./hardfault-debugging.md). Firmware built with `--specs=rdimon.specs` therefore works perfectly on your desk and dies on power-up. This is the same failure shape as an unguarded ITM write, from a different cause.
- **It must be enabled on both sides.** `monitor arm semihosting enable` in OpenOCD, plus `rdimon` in the link. A build with the syscalls linked and the host support off just hangs.

Use semihosting for exactly one thing: bring-up on a board where nothing else works yet, on code with no timing requirements at all. Then take it out.

## SWO and ITM

The ITM's virtue is that a log write is a **store to a memory-mapped address** — the same cost as writing any peripheral register. There is no driver, no interrupt, no DMA channel and no buffer of yours to manage; the FIFO and the TPIU do the work, and the data leaves on a dedicated pin (`PB3` on this part, shared with `JTDO`) that costs you nothing in application I/O.

[SysTick and the Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md) covers the register-level bring-up and the guard that keeps an ITM write from hanging a board with no probe attached; do not write ITM code without reading that guard. What belongs here is how you use it as a logging transport:

- **Retarget `_write` to port 0** and `printf` goes out over SWO. That gives you familiar syntax with a microsecond-scale transport — but you still pay `vfprintf`'s formatting cost on the target, which for a `%d` is hundreds of cycles and for a `%f` is thousands, and roughly 4 KB of flash against newlib-nano ([Reading the Map File](../03-toolchain-and-build/elf-map-files-and-size.md) measures that).
- **Use the other 31 ports as channels.** Port 0 for text, port 1 for a state-machine ID, port 2 for a timestamped event code. Each is a distinct address, so the discrimination costs nothing at runtime and the host tool can filter.
- **The DWT feeds the same pipe.** PC sampling, exception entry/exit events and data-watchpoint traces are ITM packets, which is how a trace tool reconstructs behaviour without any logging code at all. That is a topic in its own right and this folder covers it separately.

The limits worth knowing before you build on it: SWO needs a probe that implements it (many cheap CMSIS-DAP clones do not), the trace clock is derived from the core clock so **changing `HCLK` at runtime desynchronises the host decoder**, and if you overrun the FIFO the ITM sets an overflow flag and drops packets — silently, unless your host tool surfaces it.

## RTT: the debug probe reads your RAM

SEGGER's Real-Time Transfer inverts the problem. Instead of pushing data out of a pin, the target writes into a ring buffer in ordinary SRAM and the **probe reads that buffer over SWD while the core keeps running**, using the AHB-AP's independent bus access. The target-side cost is a `memcpy` and a pointer update. SEGGER documents "an average line of text can be output in one microsecond or less. Basically only the time to do a single `memcopy()`", and up to about 3.5 MB/s in background mode.

The design detail that makes it safe without any locking is worth internalising because it is reusable: for an up-buffer, **the write pointer is only ever written by the target and the read pointer only ever by the probe.** Neither side writes what the other writes, so there is no shared-word race to protect — the same single-producer/single-consumer discipline as a lock-free ring buffer, with the consumer living on your laptop.

Practical notes:

- The probe locates the control block by **scanning target RAM for the ASCII signature `SEGGER RTT`**, which is why RTT "just works" without configuration and why it can also fail to attach if your linker placed the block outside the region the tool searches. Both J-Link and `probe-rs` support it; OpenOCD implements it too via `rtt setup`/`rtt start`.
- It is **bidirectional**. Down-buffers give you a console into the firmware — a command interface with no UART.
- The licensing is the thing to check: the target-side implementation is SEGGER's, distributed under their terms, and the smooth path assumes a J-Link. `probe-rs` and OpenOCD implement the protocol independently.

## The DMA-backed ring buffer: no probe required

Every option above needs a debug probe, which means none of them is your product's field logging. The version that ships is a ring buffer in RAM drained by DMA to a UART.

```c title="log.c — the shape that matters"
static volatile uint8_t  ring[2048];
static volatile uint16_t head;          /* written by producers only */
static volatile uint16_t tail;          /* written by the DMA-complete ISR only */
static volatile bool     dma_busy;
static volatile uint32_t dropped;       /* count what you throw away */

void log_write(const uint8_t *p, size_t n)
{
    uint16_t h = head;
    if (ring_free(h, tail) < n) { dropped += n; return; }  /* drop, never block */
    for (size_t i = 0; i < n; i++) { ring[(h + i) % sizeof ring] = p[i]; }
    head = (uint16_t)((h + n) % sizeof ring);              /* publish last */
    log_kick();                                            /* start DMA if idle */
}
```

Four decisions in that sketch, and each one is where an implementation usually goes wrong:

- **Drop, do not block.** A logger that blocks when the buffer is full has reintroduced the exact problem this page opened with — and it will do so precisely when the system is busiest, which is when you most need it not to. Drop, and **count the drops**, so the log itself tells you it is incomplete. A log with a silent gap is worse than no log.
- **`head` is published after the payload is written.** A reader that sees the new `head` must see complete data behind it. On a single-core Cortex-M with a DMA engine reading the same memory this needs a `__DMB()` before the `head` store, not just `volatile` — `volatile` orders nothing with respect to the bus.
- **Timestamp on entry, not on transmission.** The whole point is knowing *when* something happened; a line stamped when the DMA drained it is stamped with the wrong time. `DWT->CYCCNT` is the cheap source.
- **Calling it from an ISR must be safe.** Either make the producer path lock-free for one producer and mask briefly for the general case, or accept that only one priority level may log. Do not put a mutex in it.

The transport can then be a UART, and it can be fast: at 4.6 Mbaud — `PCLK/16` with `OVER8` on this part — the same forty-character line takes 87 µs on the wire and zero microseconds of your core's time.

## When even a `memcpy` is too much: deferred and binary logging

The last cost left is the formatting. `printf("temp=%d.%02d C, state=%s\n", ...)` runs `vfprintf` on your microcontroller to produce bytes whose only reader is a laptop that could have done it itself.

Deferred formatting removes that: log the **address of the format string** and the raw arguments, and let the host do the rendering. The format string never goes on the wire and — with the right linker trickery — never goes into flash either, only into a section the host reads out of the ELF. A twelve-byte binary record replaces a forty-byte string, the target-side cost drops from hundreds of cycles to a handful of stores, and the flash cost of the strings goes to zero.

This is what Rust's **`defmt`** does, and what **Trice** and SEGGER's SystemView event encoding do in C. The trade is real and worth stating: your log is no longer human-readable without the matching ELF, so **the binary and its decoder must be versioned together**, and a field device's log stream is useless if you cannot identify which build produced it. Put a build ID in the first record.

The intermediate step, if a full binary scheme is too much machinery, is to log **event codes with numeric arguments** — a `uint8_t` event ID and two `uint32_t`s — through a small enum with a table on the host. That is fifty lines of code, gets most of the benefit, and keeps working when the decoder is a Python script someone wrote in an afternoon.

:::warning[The logger that blocked, and the log that lied about when]
**A "non-blocking" logger that blocks under load.** A ring buffer plus DMA is non-blocking exactly until the buffer is full, and the usual implementation then spins waiting for space. On a quiet bench it never fills; in the field, during the burst of activity that accompanies the failure you are trying to log, it fills immediately and the logger becomes a blocking `printf` at the worst possible moment. The symptom is a device that misses deadlines only when something is going wrong — which reads as a cascade failure and sends you looking for the wrong root cause. The fix is a policy decision made explicitly: drop, count drops, and expose the counter. Then a log that says `[dropped: 812]` tells you what happened instead of hiding it.

**Timestamps applied at transmission.** Stamp each line as the DMA sends it and every timestamp is the time the buffer drained, not the time the event occurred. Under load those differ by however long the queue was — tens of milliseconds — and, worse, the *error* varies with load, so the interval between two events in the log is not the interval between the events. Engineers reconstruct causality from this and get it backwards: B appears before A because A's line waited behind a burst. The recognition rule is that suspiciously round or suspiciously uniform inter-line gaps mean you are looking at drain times. Capture `DWT->CYCCNT` in `log_write`, before anything else.

**Logging from an ISR into a non-reentrant formatter.** `vsnprintf` from newlib is not guaranteed reentrant, and a `printf` in an ISR that pre-empts a `printf` in `main` produces interleaved garbage at best and corrupted internal state at worst. The output looks like a memory corruption bug and is not one. Format outside the ISR, or use a formatter you know to be reentrant, or make the ISR path emit binary records only.
:::

## See also

- [The Debug Toolbox](./the-debug-toolbox.md) — the perturbation table this page is the detailed version of, and when logging is the wrong instrument entirely.
- [SysTick and the Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md) — the ITM registers, the bring-up order, the `DWT->CYCCNT` timestamp source, and the guard that stops an ITM write hanging an unprobed board.
- [UART In Depth](../05-peripherals-and-drivers/uart-in-depth.md) — the framing the 86.8 µs comes from, `OVER8`, and the overrun that a halted core causes.
- [DMA](../05-peripherals-and-drivers/dma.md) — the transfer, the complete interrupt that advances `tail`, and the memory barrier the ring buffer needs.
- [Reading the Map File](../03-toolchain-and-build/elf-map-files-and-size.md) — the measured flash cost of linking `printf` at all, which is the other reason to avoid it.

## References

- SEGGER — [**Real Time Transfer (RTT)**](https://kb.segger.com/RTT). The protocol, the control block and its `SEGGER RTT` signature, the up/down buffer structure, the single-writer-per-pointer rule that removes the need for locking, the "~1 µs per line, basically one `memcopy()`" figure and the "up to ~3.5 MB/s" background-mode throughput quoted above (documentation checked 2026-08-26).
- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), consulted at **Rev 10** (March 2020). The ITM chapter for the stimulus-port registers, `ITM_TCR`, `ITM_TER`, the lock-access key and the trace-bus ID; the DWT chapter for the packets the ITM also carries and for `CYCCNT` as a timestamp source.
- Arm — [***Armv7-M Architecture Reference Manual***](https://developer.arm.com/documentation/ddi0403/latest/), **DDI 0403E.e**, Appendix C1 "Debug". The ITM packet formats that the SWO throughput derivation above depends on — specifically that an 8-bit stimulus write produces a one-byte header plus one payload byte — and the TPIU's NRZ and Manchester SWO encodings.
- Arm — [**Semihosting for AArch32 and AArch64**](https://github.com/ARM-software/abi-aa/blob/main/semihosting/semihosting.rst). The normative specification: the `BKPT 0xAB` trap on Thumb, the operation numbers, the parameter block convention, and the explicit statement that the debug agent handles the request while the target is stopped — which is the halt cost described above.
- Ferrous Systems / Knurling — [**`defmt` book**](https://defmt.ferrous-systems.com/). The best-documented deferred-formatting logger: how the format strings are interned into a link section instead of the image, what goes on the wire, and the versioning coupling between firmware and decoder that this design forces on you.
