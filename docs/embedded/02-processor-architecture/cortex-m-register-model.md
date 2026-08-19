---
id: cortex-m-register-model
title: The Register Model
sidebar_label: The Register Model
sidebar_position: 2
tags: [embedded, cortex-m, arm, registers, exceptions, stm32]
---

# The Register Model

A Cortex-M shows you sixteen 32-bit registers at any moment, and thirteen of them are genuinely interchangeable scratch space. The other three are the processor's control surface — a stack pointer that is secretly one of two, a link register that sometimes holds a return address and sometimes holds a magic number, and a program counter that is one bit weirder than it looks. Alongside those sit half a dozen **special registers** that are not in the main file at all: you cannot load or store them, and the only way to touch them is a pair of dedicated instructions.

That split is the mental model worth carrying. The visible sixteen are what your C compiler manipulates. The special registers are what your *system* code manipulates — startup code, an RTOS context switcher, a critical section, a fault handler — and they are where a firmware engineer's leverage lives. Almost every "how does this even work" moment in Cortex-M firmware resolves to one of them.

This page is the reference the rest of the section builds on. The last section, on `EXC_RETURN`, is the one to bookmark: it is the single value that tells a fault handler where to look for the crash, and getting it wrong sends you to a plausible-looking wrong address.

:::info[Prerequisites]
[Registers and Instructions](../../computer-science/assembly/registers-and-instructions.md) covers what a register file *is* and why compilers care; this page assumes that and goes Cortex-M-specific. [Calling Conventions and the Stack](../../computer-science/assembly/calling-conventions-and-the-stack.md) explains the caller/callee-saved split that the exception stack frame below silently implements in hardware.
:::

## The sixteen visible registers

| Register | Also called | Reset value | What it is |
|---|---|---|---|
| `R0`–`R12` | — | Unknown | General-purpose, 32-bit, for data operations. |
| `R13` | `SP` — banked as `MSP` / `PSP` | `MSP`: see below; `PSP`: unknown | The stack pointer. Two physical registers, one visible name. |
| `R14` | `LR` | `0xFFFFFFFF` | Return address for calls — or an `EXC_RETURN` value inside a handler. |
| `R15` | `PC` | Reset vector, see below | Current program address. |

Reset values are from PM0214 Rev 10, Table 3 "Core register set summary". `LR`'s reset value is not decoration: the *Armv7-M ARM* comments the reset pseudocode line `LR = 0xFFFFFFFF` with "preset to an illegal exception return value" (DDI 0403E.e §B1.5.5), so a return attempted before anything has set `LR` faults rather than jumping somewhere arbitrary.

Three of the four rows have a catch.

**`SP` is two registers wearing one name.** The processor implements a **Main Stack Pointer** (`MSP`) and a **Process Stack Pointer** (`PSP`), and which one `R13` refers to depends on the mode and on one bit of the `CONTROL` register. PM0214 Rev 10 §2.1.2 is blunt about the constraint: "In Handler mode, the processor always uses the main stack." [Privilege Modes and the Two Stacks](./privilege-modes-and-stacks.md) is the page for the details; the thing to hold here is that "the stack pointer" is an ambiguous phrase on this architecture and a debugger that shows you one `SP` is showing you the *current* one.

**The stack is full descending.** PM0214 Rev 10 §2.1.2: "The processor uses a full descending stack. This means the stack pointer indicates the last stacked item on the stack memory. When the processor pushes a new item onto the stack, it decrements the stack pointer and then writes the item to the new memory location." Stacks grow downwards; the initial `MSP` is therefore the *top* address of your stack region, not the bottom.

**`PC` bit 0 is not an address bit.** It carries the instruction-set state. PM0214 Rev 10 §2.1.3, on the program counter: "On reset, the processor loads the PC with the value of the reset vector, which is at address `0x00000004`. Bit[0] of the value is loaded into the EPSR T-bit at reset and must be 1." Every branch target on a Cortex-M has this property — [Thumb-2 and Code Density](./thumb-and-instruction-sets.md) explains why, and what happens when a vector table entry gets the bit wrong.

## xPSR: three registers in one word

`xPSR` is a single 32-bit register whose bits are divided between three named views. Software can read and write them individually or in combination through `MRS` and `MSR`, using the names `APSR`, `IPSR`, `EPSR` or their concatenations (PM0214 Rev 10, Table 4 "PSR register combinations").

```wavedrom title="xPSR: the union of APSR, IPSR and EPSR on Cortex-M4" alt="Bit-field strip of the 32-bit xPSR showing N, Z, C, V, Q, ICI/IT, T, GE and ISR_NUMBER fields"
{ reg: [
    { bits: 9, name: "ISR_NUMBER", type: 3 },
    { bits: 1, name: "align", type: 5 },
    { bits: 6, name: "ICI/IT", type: 4 },
    { bits: 4, name: "GE[3:0]", type: 2 },
    { bits: 4, type: 1 },
    { bits: 1, name: "T", type: 4 },
    { bits: 2, name: "ICI", type: 4 },
    { bits: 1, name: "Q", type: 2 },
    { bits: 1, name: "V", type: 2 },
    { bits: 1, name: "C", type: 2 },
    { bits: 1, name: "Z", type: 2 },
    { bits: 1, name: "N", type: 2 }
  ],
  config: { hspace: 1000, bits: 32, lanes: 2 }
}
```

| Bits | Field | View | Reset | Meaning |
|---|---|---|---|---|
| 31 | `N` | APSR | Unknown | Negative or less-than flag. |
| 30 | `Z` | APSR | Unknown | Zero flag. |
| 29 | `C` | APSR | Unknown | Carry or borrow flag. |
| 28 | `V` | APSR | Unknown | Overflow flag. |
| 27 | `Q` | APSR | Unknown | **Sticky** DSP overflow/saturation flag. Set by `SSAT`/`USAT` saturation or a DSP overflow; "This bit is cleared to zero by software using an `MRS` instruction." |
| 26:25 | `ICI` / `IT` | EPSR | `0` | Execution state: either the resume point of an interrupted `LDM`/`STM`/`PUSH`/`POP`/`VLDM`/`VSTM`/`VPUSH`/`VPOP`, or the `IT` block state. |
| 24 | `T` | EPSR | **`1`** | Thumb state. Must be 1 to execute anything at all. |
| 23:20 | — | — | `0` | Reserved. |
| 19:16 | `GE[3:0]` | APSR | Unknown | Greater-than-or-equal flags, written by the SIMD instructions and consumed by `SEL`. |
| 15:10 | `ICI` / `IT` | EPSR | `0` | Continuation of the `ICI`/`IT` field. |
| 9 | (`align`) | — | `0` | The architecture gives this bit no name — it is reserved in the register. It is labelled here because **when `xPSR` is pushed as part of an exception frame, this bit records whether the hardware realigned the stack**. See the stack-frame section below. |
| 8:0 | `ISR_NUMBER` | IPSR | `0` | Exception number of the currently executing exception; `0` means Thread mode. |

Field definitions are PM0214 Rev 10, Tables 5 (APSR), 6 (IPSR) and 7 (EPSR); the register-level reset value of `0x01000000` for both `PSR` and `EPSR` comes from Table 3, and is just the `T` bit set. The `IPSR` numbering — `2` = NMI, `3` = hard fault, `11` = SVCall, `14` = PendSV, `15` = SysTick, `16` = IRQ0 and upward — is Table 6; [Exceptions and the Vector Table](./exceptions-and-the-vector-table.md) lays it out against the table itself.

Two practical notes on reading this table:

- **`EPSR` cannot be read directly.** PM0214 Rev 10 §2.1.3: "Attempts to read the EPSR directly through application software using the MSR instruction always return zero. Attempts to write the EPSR using the MSR instruction in application software are ignored." The document then names the workaround that fault handlers depend on: "Fault handlers can examine EPSR value in the stacked PSR." A read of `PSR` gives you the `APSR` and `IPSR` bits and zeros where `EPSR` should be — the only place the real `EPSR` is visible is in an exception frame in memory.
- **`IPSR` is how code finds out where it is.** Read it and you know whether you are in Thread mode (`0`) or inside a specific handler. A shared handler used for several interrupts, or a common fault handler, reads `IPSR` to find out which exception invoked it.

## The special registers

These four are not in the register file. `MRS` reads them into a general-purpose register, `MSR` writes them back, and `CPS` provides a shortcut for two. Every one requires privileged execution (PM0214 Rev 10, Table 3, "Required privilege" column).

| Register | Width | Reset | What it does |
|---|---|---|---|
| `PRIMASK` | 1 bit | `0x00000000` | `1` "Prevents the activation of all exceptions with configurable priority." NMI and HardFault still get through. |
| `FAULTMASK` | 1 bit | `0x00000000` | `1` "Prevents the activation of all exceptions except for NMI." Auto-cleared: "The processor clears the FAULTMASK bit to 0 on exit from any exception handler except the NMI handler." |
| `BASEPRI` | 4 implemented bits, `BASEPRI[7:4]` | `0x00000000` | Non-zero sets a priority floor: "The processor does not process any exception with a priority value greater than or equal to BASEPRI." `0x00` means no effect. |
| `CONTROL` | 3 bits | `0x00000000` | Bit 0 `nPRIV` (Thread-mode privilege), bit 1 `SPSEL` (MSP/PSP), bit 2 `FPCA` (floating-point context active). |

All four rows are PM0214 Rev 10 Tables 3 and 8–11.

`BASEPRI` is the one whose shape surprises people. It is an eight-bit field, but the STM32F411 implements only "16 programmable priority levels (4 bits of interrupt priority are used)" (RM0383 Rev 4, §10.1.1), so only `BASEPRI[7:4]` are writable — the low nibble reads back as zero. PM0214 Rev 10, Table 10 adds the trap in a footnote: "Remember that higher priority field values correspond to lower exception priorities." Writing `BASEPRI = 0x20` blocks everything at numeric priority 2 and above (i.e. everything *less* urgent than priority 2), and lets priorities 0 and 1 through. Writing `0x00` blocks nothing.

`CONTROL.FPCA` is the FPU-related one and it matters for `EXC_RETURN` below. PM0214 Rev 10, Table 11: "FPCA: Indicates whether floating-point context currently active… The Cortex-M4 uses this bit to determine whether to preserve floating-point state when processing an exception." The hardware sets it for you: with `FPCCR.ASPEN` enabled, executing any floating-point instruction sets `CONTROL.FPCA` to 1 (PM0214 Rev 10, §4.6.2). And `FPCCR.ASPEN` and `FPCCR.LSPEN` both reset to `1` — the *Armv7-M ARM* reset pseudocode assigns `FPCCR.ASPEN = '1'; FPCCR.LSPEN = '1';` (DDI 0403E.e §B1.5.5) — so on a Cortex-M4F the default behaviour is automatic, lazily-performed floating-point state preservation, without you configuring anything.

## What the hardware stacks on exception entry

When an exception is taken, the processor pushes registers before your handler's first instruction runs. PM0214 Rev 10 §2.3.7 calls it "stacking" and the pushed group "the stack frame". The point of doing it in hardware is that a handler is an ordinary AAPCS C function: the hardware saves exactly the caller-saved registers the ABI says a function may clobber, so the compiler's normal prologue saves the rest and nothing special is required.

There are two frame shapes on a Cortex-M4 with FPU.

### The Basic frame — 8 words, 32 bytes

| Offset from frame pointer | Content |
|---|---|
| `0x00` | `R0` |
| `0x04` | `R1` |
| `0x08` | `R2` |
| `0x0C` | `R3` |
| `0x10` | `R12` |
| `0x14` | `LR` (R14) |
| `0x18` | Return address |
| `0x1C` | `xPSR` |
| `0x20` | (aligner word, present only if the stack needed realigning) |

Offsets are the *Armv7-M ARM*'s Figure B1-3 and its `PopStack()` pseudocode (DDI 0403E.e §B1.5.6–§B1.5.8), which reads `R[0] = MemA[frameptr,4]`, `R[1] = MemA[frameptr+0x4,4]` … `LR = MemA[frameptr+0x14,4]`, `BranchTo(MemA[frameptr+0x18,4])`, `psr = MemA[frameptr+0x1C,4]`. PM0214 Rev 10 §2.3.7 states the useful invariant: "Immediately after stacking, the stack pointer indicates the lowest address in the stack frame."

Note what is at offset `0x18`: PM0214 calls it "the return address… the address of the next instruction in the interrupted program", and it is the value you want when a fault handler is trying to tell you *where* the program died.

### The Extended frame — 26 words, 104 bytes

If `CONTROL.FPCA` was 1 when the exception was taken, the hardware allocates an Extended frame instead: the Basic frame followed by `S0`–`S15` at offsets `0x20` through `0x5C`, `FPSCR` at `0x60`, a reserved word at `0x64`, and an optional aligner at `0x68`. The `PopStack()` pseudocode names the size directly — `if HaveFPExt() && EXC_RETURN<4> == '0' then framesize = 0x68` — and reads `FPSCR = MemA[frameptr+0x60,4]` (*Armv7-M ARM* §B1.5.8). `0x68` is 104 bytes.

Whether the FP registers are actually *written* is a separate question from whether space is *reserved*. The *Armv7-M ARM* §B1.5.7 lists three behaviours, selected by `FPCCR.ASPEN` and `FPCCR.LSPEN`: stack no FP context at all (Basic frame), stack a full Extended frame, or "Reserve space on the stack for an Extended frame, but write-only the Basic frame information… This is an FP lazy context save." With the reset defaults (both bits 1) you get lazy stacking: the space is reserved, `FPCCR.LSPACT` is set, `FPCAR` points at the reserved `S0` slot, and the registers are only written if the handler itself executes a floating-point instruction. As the manual puts it, "Lazy state preservation reduces the exception latency."

The consequence for stack sizing is unavoidable and easy to miss: **on a Cortex-M4F, once any code has touched the FPU, every exception costs 104 bytes of stack, not 32** — whether or not the floating-point registers are ever written to it.

### Bit 9 of the stacked `xPSR`

The frames above are 8-byte aligned. If the stack pointer happened to be only 4-byte aligned when the exception arrived, the hardware inserts a padding word and records that it did so — *Armv7-M ARM* §B1.5.6: "On an exception entry when `CCR.STKALIGN` is set to 1, the exception entry sequence ensures that the stack pointer in use before the exception entry has 8-byte alignment, by adjusting its alignment if necessary. When the processor pushes the PSR value to the stack it uses bit[9] of the stacked PSR value to indicate whether it realigned the stack."

On this part `CCR.STKALIGN` resets to 1 (PM0214 Rev 10, §4.4.19 SCB register map, `CCR` reset value row). So the frame is *at least* 32 bytes and *at most* 36; extended, at least 104 and at most 108. The *Armv7-M ARM* spells out the budgeting consequence: "In the worst case, the increase is 4 bytes per exception entry."

If you are walking a stack by hand — which is what fault debugging amounts to — the manual tells you exactly which bits to consult: "Any exception-handling code that must retrieve arguments from the stack, that were pushed to the stack before the exception was taken, must use the stacked value of `xPSR[9]` to determine whether the previous top-of-stack was at offset `0x20` or `0x24`. If the implementation includes the FP extension, such code must use the stacked value of `xPSR[9]` together with the value of `EXC_RETURN` bit[4] to determine whether the previous top-of-stack was at offset `0x20`, `0x24`, `0x68`, or `0x6C`" (§B1.5.6).

## `EXC_RETURN`

This is the mechanism that makes the whole exception model work, and it is worth understanding precisely because two later chunks of this section — writing startup code and interrupt handlers, and debugging a HardFault — read it directly.

**What it is.** On exception entry the processor writes a value into `LR` instead of a return address. PM0214 Rev 10 §2.3.7: "the processor writes an `EXC_RETURN` value to the `LR`. This indicates which stack pointer corresponds to the stack frame and what operation mode the processor was in before the entry occurred."

**How it is used.** Because it lives in `LR`, an ordinary `BX LR` at the end of a handler triggers an exception return rather than a subroutine return. PM0214 Rev 10 §2.3.7 lists the three instruction forms that count: "an `LDM` or `POP` instruction that loads the PC", "an `LDR` instruction with PC as the destination", "a `BX` instruction using any register". The *Armv7-M ARM* adds that the trigger is the *value*, not the instruction — an exception return happens when "the processor is in Handler mode and one of the following instructions loads a value of `0xFXXXXXXX` into the PC" (§B1.5.8). That is why a handler compiled as an ordinary C function just works.

**The bit layout**, from *Armv7-M ARM* §B1.5.8:

| Bits | Meaning |
|---|---|
| `[31:28]` | "`0xF`. This value identifies the value in a PC load as an `EXC_RETURN` value." |
| `[27:5]` | "Reserved, SBOP" — should be one, and "The effect of writing a value other than 1 to any bit in this field is UNPREDICTABLE." |
| `[4]` | **Frame type.** On a processor *with* the FP extension: "Defines whether the stack frame for this exception has space allocated for FP state information. **Bit[4] is 0 if stack space is allocated.**" On a processor *without* it, bit 4 is reserved, SBOP. |
| `[3:0]` | Return behaviour. Only three encodings are legal. |

Read bit 4 twice, because the polarity is the opposite of intuition: **0 means the Extended (floating-point) frame, 1 means the Basic frame.** The manual explains where the inversion comes from — "On exception entry, the bit[4] value is saved in the `EXC_RETURN` value as the inverse of the `CONTROL.FPCA` bit value when the exception was generated… On exception return, the processor sets `CONTROL.FPCA` to the inverse of the `EXC_RETURN[4]` value."

Bits `[3:0]` are **not** three independent flags. The architecture defines them as one 4-bit field with exactly three legal values, and the `ExceptionReturn()` pseudocode switches on the whole nibble: `when '0001'` → return to Handler using `SP_main`; `when '1001'` → return to Thread using `SP_main`; `when '1101'` → return to Thread using `SP_process`; `otherwise` → "illegal `EXC_RETURN`", `UFSR.INVPC = '1'`, UsageFault (*Armv7-M ARM* §B1.5.8). It is convenient and correct to *read* bit 3 as "return to Thread mode" and bit 2 as "use the Process stack" — but there is no legal encoding with bit 3 clear and bit 2 set, so treating them as freely combinable is a way to construct a value that faults.

**The six legal values on a Cortex-M4 with FPU**, verbatim from *Armv7-M ARM* Table B1-9 and cross-checked against PM0214 Rev 10, Table 18:

| `EXC_RETURN` | Return to | Frame was pushed to, and will be used after return | Frame type |
|---|---|---|---|
| `0xFFFFFFE1` | Handler mode | **`MSP`** | **Extended** (floating-point) |
| `0xFFFFFFE9` | Thread mode | **`MSP`** | **Extended** (floating-point) |
| `0xFFFFFFED` | Thread mode | **`PSP`** | **Extended** (floating-point) |
| `0xFFFFFFF1` | Handler mode | **`MSP`** | Basic |
| `0xFFFFFFF9` | Thread mode | **`MSP`** | Basic |
| `0xFFFFFFFD` | Thread mode | **`PSP`** | Basic |

Three things this table settles:

- **There is no "Handler mode, Process stack" row, in either table.** Handler mode always uses the Main stack, so the combination does not exist. `0xFFFFFFE5` and `0xFFFFFFF5` are reserved values, and using one causes "a chained UsageFault exception" (§B1.5.8).
- **The stack column is doing double duty, deliberately.** *Armv7-M ARM* §B1.5.8: "The entry in the Return stack column is the stack that holds the information that the processor must restore as part of the exception return sequence. This is also the stack the processor will use after returning from the exception." So the same bit tells you both where to *look* for the frame and where execution will *continue*.
- **On a part without an FPU you only ever see the `F`-nibble values** — Table B1-8, the no-FP-extension table, lists exactly `0xFFFFFFF1`, `0xFFFFFFF9` and `0xFFFFFFFD`. If you are reading a Cortex-M3 tutorial, that is why it only shows three.

For a bare-metal application on this board, the value you will see in practice is `0xFFFFFFF9`: everything runs on `MSP`, so an interrupt from `main` gives Thread mode, Main stack, Basic frame. Under an RTOS, tasks run on `PSP`, and the value becomes `0xFFFFFFFD` — or `0xFFFFFFED` for a task that has used the FPU. A handler that is itself interrupted sees `0xFFFFFFF1` or `0xFFFFFFE1`.

### The one idiom to memorise

Every fault handler in this section, and every one you will read elsewhere, opens with the same two steps: work out which stack the frame is on from `EXC_RETURN` bit 2, then read the stacked return address from offset `0x18`.

```c
/* Called from the naked assembly stub with the frame pointer already chosen.
   Offsets are Armv7-M ARM DDI 0403E.e, section B1.5.6, Figure B1-3. */
void fault_report(const uint32_t *frame, uint32_t exc_return)
{
    uint32_t stacked_pc   = frame[6];   /* offset 0x18 -- the faulting address  */
    uint32_t stacked_xpsr = frame[7];   /* offset 0x1C -- includes the real EPSR */
    bool     used_psp     = (exc_return & (1u << 2)) != 0u;
    bool     extended     = (exc_return & (1u << 4)) == 0u;  /* 0 => FP frame */
    /* ... */
}
```

```armasm
    .thumb_func
HardFault_Handler:
    tst   lr, #4              /* EXC_RETURN bit 2: 0 = MSP, 1 = PSP */
    ite   eq
    mrseq r0, msp
    mrsne r0, psp
    mov   r1, lr              /* pass EXC_RETURN itself as the second argument */
    b     fault_report
```

`tst lr, #4` tests bit 2 and nothing else, which is exactly right: bit 2 is the stack selector in all six legal values.

:::warning[Reading the wrong stack is the classic fault-debugging dead end]
The failure looks like this. You write a HardFault handler, it reads `MSP` unconditionally, and it prints a faulting address that is inside your fault handler, or inside the RTOS kernel, or in the middle of nowhere. You then spend an afternoon investigating a function that had nothing to do with the crash.

What happened is that the faulting code was a task running on `PSP`, so the frame is on the process stack, and `MSP` at that instant points at the handler's own stack. Every value you read is real memory and none of it is the crash. There is no error, no exception, and no hint — just a wrong number that looks entirely plausible.

Three variants of the same trap:

- **Assuming `MSP`.** Correct in bare-metal firmware, wrong the moment you add an RTOS. Test bit 2 of `LR` and be right in both cases; it costs one instruction.
- **Assuming a 32-byte frame.** With any floating-point code in the build, the frame may be 104 bytes and `xPSR` still sits at `+0x1C` — but anything you try to read *beyond* the frame, such as arguments the caller pushed, is at a completely different offset. Use `EXC_RETURN` bit 4, and remember that **0 means extended**, not the other way round.
- **Reading `LR` after the handler's prologue.** The compiler is free to push `LR` and reuse the register. If the handler is a plain C function, `LR` may already be gone by the time your first statement runs. Capture it in a `naked` assembly stub, as above, and pass it as an argument.

The one that produces the strangest symptom is constructing an `EXC_RETURN` by hand, treating bits 3 and 2 as free flags. Setting bit 2 on `0xFFFFFFF9` gives `0xFFFFFFFD`, which is legal, so it *works* — and that success is what teaches the wrong lesson. Clearing bit 3 as well, to ask for "Handler mode on the process stack", gives `0xFFFFFFF5`, which is reserved, and you get an `INVPC` UsageFault with the offending value sitting in `LR`. It is a good failure — it is loud — but only if you know that `UFSR.INVPC` means "somebody put a bad value in the PC via `EXC_RETURN`" rather than a wild jump.
:::

## See also

- [Privilege Modes and the Two Stacks](./privilege-modes-and-stacks.md) — `MSP` versus `PSP`, `CONTROL`, and why an RTOS needs both.
- [Exceptions and the Vector Table](./exceptions-and-the-vector-table.md) — where the exception this page's stack frame belongs to came from, and what `IPSR` is counting.
- [Thumb-2 and Code Density](./thumb-and-instruction-sets.md) — why `PC` bit 0 and `EPSR.T` exist, and what happens when they disagree.
- [The Cortex-M Family](./arm-cortex-m-profiles.md) — which cores have the FP extension that makes the Extended frame possible at all.
- [Calling Conventions and the Stack](../../computer-science/assembly/calling-conventions-and-the-stack.md) — the AAPCS caller-saved set that the Basic frame reproduces in hardware.

## References

- Arm — [***Armv7-M Architecture Reference Manual***](https://developer.arm.com/documentation/ddi0403/latest/), consulted at **DDI 0403E.e (ID021621)**. The normative source for everything about `EXC_RETURN` and the stack frames: §B1.5.6 "Exception entry behavior" (the `PushStack()` pseudocode, Figure B1-3, the 8-byte alignment mechanism and `xPSR[9]`), §B1.5.7 "Context state stacking on exception entry with the FP extension" (the three stacking modes, Figure B1-4, lazy context save), §B1.5.8 "Exception return behavior" (the bit-by-bit definition, **Table B1-8** without the FP extension, **Table B1-9** with it, the `ExceptionReturn()` and `PopStack()` pseudocode, and the integrity checks). §B1.5.5 for the reset pseudocode quoted for `LR` and `FPCCR`.
- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), consulted at **Rev 10** (March 2020). §2.1.2 "Stacks" for the full-descending rule and the Handler-mode constraint; §2.1.3 "Core registers" with **Table 3** (register summary and reset values), **Table 4** (PSR combinations) and **Tables 5–11** (APSR, IPSR, EPSR, PRIMASK, FAULTMASK, BASEPRI, CONTROL field definitions); §2.3.7 "Exception entry and return" with **Table 18** for the six `EXC_RETURN` values; §4.4.19 SCB register map for the `CCR.STKALIGN` reset value; §4.6.2 for `FPCCR.ASPEN`/`LSPEN`. Note that PM0214's Table 18 gives the same six values as the Armv7-M ARM's Table B1-9 but does not break out the bit fields — take the bit-level definition from the architecture manual.
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). §10.1.1 for the four implemented priority bits, which is what makes `BASEPRI` a `[7:4]` field on this part rather than a full byte.
