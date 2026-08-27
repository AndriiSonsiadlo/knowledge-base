---
id: mocking-hardware
title: Mocking Hardware
sidebar_label: Mocking Hardware
sidebar_position: 10
tags: [embedded, testing, mocking, drivers, dependency-injection, tdd]
---

# Mocking Hardware

[Unit Testing Firmware](./unit-testing-firmware.md) drew a clean line around the logic that needs nothing from the hardware at all — a parser, a state machine, a checksum — and pointed at this page for the harder case: logic whose whole job *is* to talk to a peripheral. A driver cannot be tested by giving it inputs and checking outputs the way a parser can, because its inputs and outputs are register writes and register reads, and there is no register to read from on a laptop. Testing it on the host requires something on the other end of the bus that behaves like the real device without being it.

"Mocking hardware" is not one technique with one name, and conflating its two common shapes is where people get stuck. One shape fakes the **register block itself** — a plain struct standing in for `I2C_TypeDef` or `USART_TypeDef`, so the lowest layer of a driver can be exercised without a real peripheral behind it. The other fakes a **higher-level interface** the driver was written against — not the registers, but the abstraction a well-structured driver injects instead of touching registers directly. [Writing a Driver Worth Reusing](../05-peripherals-and-drivers/writing-a-portable-driver.md) already built exactly that abstraction — the `struct i2c_bus` seam — and closed by showing that a second implementation of it is "about forty lines of ordinary C that runs on a host." This page does not re-derive that seam; it takes it as given and covers what that page left for later: simulating interrupts and time on the fake side of the seam, replaying real captured traffic through it, and — the discipline that decides whether any of this is worth doing — keeping a fake honest against the datasheet rather than against whatever made a test pass once.

:::info[Prerequisites]
[Writing a Driver Worth Reusing](../05-peripherals-and-drivers/writing-a-portable-driver.md) owns the three-layer structure, the `struct i2c_bus` seam, and the argument that a host-compilable device layer is proof the seam is real — read it first; this page assumes that structure exists and builds the fake that plugs into it. [Unit Testing Firmware](./unit-testing-firmware.md) owns the host-build mechanics, the framework choice, and the honest limit of what a host test proves; this page is the technique for the case that page hands off to it.
:::

## The seam, concretely: the same driver, two things behind it

The point of the seam is that the device driver's source code does not change between these two cases — only what `dev->bus` is bound to at construction time changes. [Writing a Driver Worth Reusing](../05-peripherals-and-drivers/writing-a-portable-driver.md) shows `mcp9808_read_milli_c()` calling `dev->bus->write_read(...)`; here is what sits behind that call in each world.

<Tabs>
<TabItem value="real" label="Against real hardware">

```c title="stm32f4_i2c.c — from the portable-driver page, bound to I2C1"
static bus_status_t stm32_i2c_write_read(void *ctx, uint8_t addr7,
                                         const uint8_t *tx, size_t ntx,
                                         uint8_t *rx, size_t nrx)
{
    stm32_i2c_t *p = (stm32_i2c_t *)ctx;   /* p->regs == I2C1 */

    p->regs->CR1 |= I2C_CR1_START;
    if (!wait_flag(p, I2C_SR1_SB, true)) { return BUS_ERR_TIMEOUT; }
    /* ... real address phase, real ACK/NACK on the wire, real STOP ... */
    return BUS_OK;
}

/* board_init(): out->ctx points at a struct whose `regs` field
   is the literal I2C1 peripheral base address. */
```

</TabItem>
<TabItem value="fake" label="Against a fake, on the host">

```c title="fake_i2c_bus.c — forty-ish lines, no board required"
typedef struct {
    uint8_t  script_reply[32];
    size_t   script_len;
    uint8_t  last_write[32];
    size_t   last_write_len;
    bool     nack_next;
} fake_i2c_t;

static bus_status_t fake_write_read(void *ctx, uint8_t addr7,
                                    const uint8_t *tx, size_t ntx,
                                    uint8_t *rx, size_t nrx)
{
    fake_i2c_t *f = (fake_i2c_t *)ctx;
    if (f->nack_next) { f->nack_next = false; return BUS_ERR_NACK; }

    memcpy(f->last_write, tx, ntx);      /* record what the driver sent */
    f->last_write_len = ntx;

    memcpy(rx, f->script_reply, nrx);    /* hand back the canned reply */
    return BUS_OK;
}

/* Test setup: bind the same struct i2c_bus vtable, but with
   .ctx pointing at a fake_i2c_t instead of an stm32_i2c_t. */
void fake_i2c_bind(struct i2c_bus *out, fake_i2c_t *state)
{
    out->write_read = fake_write_read;
    out->ctx        = state;
}
```

</TabItem>
</Tabs>

`mcp9808_init()` and `mcp9808_read_milli_c()` are byte-for-byte identical in both columns — neither knows or can tell which `struct i2c_bus` it was handed. That is the entire value of the seam: the fake is not a special build of the driver, it is a second, ordinary implementation of the same three-function interface, small enough to write by hand and read in one sitting.

## Which shape of fake, for which layer

| | Register-struct fake | Interface-level fake (the seam above) |
|---|---|---|
| What it replaces | The memory-mapped register block (`I2C_TypeDef`, `USART_TypeDef`) | The `struct i2c_bus`-style vtable a driver was written against |
| What it exercises | The peripheral access layer itself — flag polling, timeout arithmetic, bit twiddling | Everything *above* the peripheral access layer — the device driver, application logic |
| Fidelity required of the fake | High — must reproduce register semantics (read-clears-flag, write-1-to-clear) or the code under test never takes the real path | Lower — only the documented behaviour of the interface's few functions (`write`, `read`, `write_read` and their status codes) |
| Right for | Testing a peripheral access layer that is complex enough to deserve its own tests (a DMA chain, a bit-banged protocol) | Testing a device driver or anything built on top of a layer that already has the seam |

## Faking the register block itself

The interface-level fake above is the right tool once a driver is already layered the way [Writing a Driver Worth Reusing](../05-peripherals-and-drivers/writing-a-portable-driver.md) describes. Not every driver is, and the peripheral access layer — the code that actually polls `SR1` and writes `DR` — needs its own tests too, on the host, before anyone trusts it. That layer's seam is one level lower: instead of a vtable, it is the register struct's *address* being a parameter rather than a hard-coded peripheral base, exactly as `stm32_i2c_t.regs` is a pointer in the portable-driver page rather than the literal `I2C1`. Point that pointer at a plain struct allocated in host RAM, laid out to match the vendor header's field order, and the register-polling loop itself — the `wait_flag()` logic, the flag interpretation, the timeout arithmetic — runs and can be tested without silicon:

```c title="A register-struct fake for the USART peripheral access layer"
typedef struct {
    volatile uint32_t SR;   /* offset 0x00 — matches USART_TypeDef */
    volatile uint32_t DR;   /* offset 0x04 */
    /* ... remaining fields only if the code under test touches them ... */
} fake_usart_regs_t;

fake_usart_regs_t fake_regs = { .SR = USART_SR_TXE, .DR = 0 };
uart_driver_t     uart      = { .regs = (USART_TypeDef *)&fake_regs, .timeout_us = 1000, .now_us = fake_now_us };
```

This is a *narrower* fake than the interface-level one — it exercises the register-twiddling code path itself rather than substituting for it — and it is the right choice when that low-level code is complex enough to deserve its own tests (a DMA descriptor chain, a bit-banged protocol, a state machine driving a sequence of register writes) rather than being trusted as an unremarkable four lines behind a seam.

## Simulating interrupts and time

A fake on the other end of a seam is not limited to answering synchronous calls. Two things a real peripheral does that a naive fake often does not — react to interrupts and take real time — are exactly the things a good fake should simulate deliberately, because leaving them out is how a test suite quietly stops exercising the paths that matter most in the field.

**Interrupts**, from a fake's perspective, are just a function call the test controls the timing of. If the real driver's completion is signalled by an ISR invoking a registered callback (a DMA-complete or transfer-complete handler), the fake calls that same callback itself, on its own schedule chosen by the test — immediately, after N calls, or never, to exercise the timeout path deliberately:

```c
fake_i2c_t fake = { .complete_after_n_polls = 3 };  /* simulate a slow device */
/* the driver's wait_flag()-equivalent loop calls fake_poll_tick() each
   iteration; the fake only reports "done" on the third call, exercising
   the loop and its bound rather than returning instantly every time. */
```

**Time** is the injected `now_us` function pointer [Writing a Driver Worth Reusing](../05-peripherals-and-drivers/writing-a-portable-driver.md) already argued for — "a driver that calls `HAL_GetTick()` cannot ... have its timeout path exercised deliberately." A fake time source under the test's control turns "wait 5 seconds for the real timeout to fire" into "advance the fake clock past the timeout and assert the driver returned `BUS_ERR_TIMEOUT`," which runs in microseconds and, critically, is the *only* practical way to make a timeout path run in CI at all — nobody actually waits out a five-second timeout on every commit, so without a fake clock that path silently never gets tested.

## Recording and replaying real bus traffic

A hand-written canned reply — `{0x00, 0x54}` for a manufacturer-ID register, say — is only as good as the person who typed it. A faster way to bootstrap a faithful fake, and a good cross-check for one you already wrote by hand, is to capture what the real device actually said and replay exactly that. [Logic Analyzer Workflows](./logic-analyzer-workflows.md) is the instrument for the capture: decode one real transaction against the real sensor, and the decoded byte sequence becomes the fake's canned reply table verbatim, including any quirk of the real part — reserved bits that are not actually zero, a manufacturer ID that does not match the datasheet's stated value on early silicon revisions, an extra byte a "compliant" device does not send. A hand-typed fake reproduces what the datasheet promises; a captured-and-replayed fake reproduces what the actual part on your bench does, which is not always the same thing and is the version worth trusting when the two disagree.

The same technique runs the other direction for verifying what the driver *sends*: capture the real driver's write sequence to a real device once, and assert a fake's `last_write` buffer matches it on every future run — a regression test for the wire protocol itself, not just for the parsed result. CppUTest's built-in mocking library, **CppUMock**, formalizes this expect/verify pattern with `mock().expectOneCall(...)` and `mock().checkExpectations()` rather than a hand-rolled comparison; [Unit Testing Firmware](./unit-testing-firmware.md) covers the framework choice between Unity and CppUTest in general, and CppUMock is the concrete reason some teams pick CppUTest specifically once mocking becomes a first-class need rather than a handful of hand-written fakes.

## Keeping the fake honest against the datasheet

Every value and every behaviour inside a fake is a claim about the real device, and the discipline this whole page rests on is refusing to let that claim drift from its source. Concretely:

- **Comment every canned value with where it came from**, the same way [Writing a Driver Worth Reusing](../05-peripherals-and-drivers/writing-a-portable-driver.md)'s device driver comments its register offsets against the MCP9808 datasheet's section numbers. A fake reply of `{0x00, 0x54}` with no comment is a magic number nobody can later confirm or refute; the same bytes with `/* MFG_ID = 0x0054, datasheet §5.1.2 */` attached is checkable.
- **Model the failure modes the datasheet documents, not only the happy path.** A real device NACKs, times out, and occasionally returns a value outside its documented range on power-up; a fake that only ever returns the golden-path reply has quietly narrowed the test suite to the one case that was easy to fake.
- **Re-validate against a fresh capture when the part or its firmware changes revision.** A fake built against silicon revision A is not guaranteed to describe revision B, and the datasheet's errata section exists precisely because the datasheet itself is sometimes the thing that was wrong.

:::warning[A fake that always answers instantly, and a register fake that does not clear its own flags]
**A fake that completes every transaction in zero simulated time.** The simplest possible `fake_write_read()` returns `BUS_OK` immediately, every time. Every test built on it passes, including the ones that were supposed to exercise `wait_flag()`'s timeout path — that path never runs, because the fake never makes the driver wait for anything. A genuine bug in the timeout arithmetic (an inverted comparison, a counter that never increments) ships with a fully green test suite, because nothing in the suite ever took the branch that bug lives on. The fix is the fake-time technique above: at least one test must configure the fake to withhold completion and assert the driver actually times out, not merely that it eventually succeeds.

**A register-struct fake that does not model a flag clearing on read.** Real UART and I²C peripherals clear specific status flags as a side effect of reading the data register — `USART_SR.RXNE` clears when `USART_DR` is read, for instance (RM0383 §19.3). A naive fake register struct is a plain field: `fake_regs.SR` stays however the test set it, regardless of how many times the code under test reads `DR`. Depending on which way the bug points, the symptom is either a driver that appears to work in every test and hangs on real hardware waiting for a flag that will never re-set, or a test that hangs on the host because the fake's flag never clears and a polling loop spins forever. Both are the same root cause: the fake modelled the register's *value* but not its *behaviour*, and a datasheet's read-clears-flag notes are exactly the behaviour a register-level fake has to reproduce, not just the reset value.
:::

## See also

- [Writing a Driver Worth Reusing](../05-peripherals-and-drivers/writing-a-portable-driver.md) — the `struct i2c_bus` seam this page's fakes are written against, and the layered structure that makes any of this possible.
- [Unit Testing Firmware](./unit-testing-firmware.md) — the framework choice, the host-build mechanics, and the honest limit on what any of these tests prove about the real hardware.
- [Logic Analyzer Workflows](./logic-analyzer-workflows.md) — the instrument for capturing the real bus traffic this page's replay technique is built from.
- [Simulation and Emulation](./simulation-and-emulation.md) — the heavier-weight alternative when a hand-written fake is not enough fidelity: running the actual firmware binary against a modelled peripheral instead of a driver-level substitute.

## References

- James W. Grenning — *Test-Driven Development for Embedded C* (Pragmatic Bookshelf, 2011). The primary source for this page: link-time and pointer-based substitution for hardware, the argument that a fake's job is to make the untestable testable without lying about the hardware, and worked examples of faking both a register interface and a higher-level peripheral seam. Purchase required.
- CppUTest — [**CppUMock documentation**](https://github.com/cpputest/cpputest/blob/master/README.md). The `expectOneCall`/`andReturnValue`/`checkExpectations` mocking API referenced above as the formalized version of the hand-rolled "record the last write and compare" pattern (documentation checked 2026-08-27).
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). §19.3 for the USART status and data registers, including the read-clears-flag behaviour a faithful register-struct fake of a UART must reproduce or its timeout and framing-error paths never actually execute in a test.
- Gerard Meszaros — *xUnit Test Patterns: Refactoring Test Code* (Addison-Wesley, 2007). The general vocabulary this page borrows — Fake Object, Test Double, and the distinction between a fake that stands in for a whole dependency and a mock that verifies a specific interaction — applied here to hardware rather than to a database or network service. Purchase required.
