---
id: thumb-and-instruction-sets
title: Thumb-2 and Code Density
sidebar_label: Thumb-2 and Code Density
sidebar_position: 3
tags: [embedded, cortex-m, arm, thumb, assembly, stm32]
---

# Thumb-2 and Code Density

On a desktop CPU, instruction encoding is an implementation detail you can go a whole career without thinking about. On a microcontroller it is a **budget**. The STM32F411RE has 512 KB of flash and 128 KB of RAM, and that flash figure is one of the two or three numbers that set the price of the chip. Every byte an instruction occupies is a byte of product cost, multiplied by the production run.

Arm's answer to that pressure was Thumb: a 16-bit encoding of a 32-bit machine. The trade is obvious — half the bits means fewer registers reachable per instruction, smaller immediates, shorter branches — and the original Thumb paid it hard enough that real programs mixed Thumb and full ARM code, switching between them at function boundaries. **Thumb-2** removed the need to switch by allowing 32-bit instructions *inside* the Thumb instruction stream, decoded from the same stream, with no mode change. You get the 16-bit encoding for the common cases and a 32-bit encoding for everything that doesn't fit, chosen per instruction by the assembler.

Cortex-M took the logical next step and dropped the ARM instruction set entirely. PM0214 Rev 10 §2.1.3 states it in one line: **"The Cortex-M4 processor only supports execution of instructions in Thumb state."** There is no other state to be in, no interworking to configure, and — as the last section of this page shows — one very specific way to make the processor angry about it.

:::info[Prerequisites]
[Instruction Set Architecture](../../computer-science/cpu-architecture/instruction-set-architecture.md) covers what an ISA is and the RISC/CISC framing this page assumes; [Reading Disassembly](../../computer-science/assembly/reading-disassembly.md) covers the general skill of reading a listing. This page is the Cortex-M-specific layer on both.
:::

## How the processor knows an instruction's length

There is no length prefix and no alignment trick. The rule is a five-bit test on the first halfword, and it is short enough to memorise. *Armv7-M ARM*, DDI 0403E.e §A5.1:

> The Thumb instruction stream is a sequence of halfword-aligned halfwords. Each Thumb instruction is either a single 16-bit halfword in that stream, or a 32-bit instruction consisting of two consecutive halfwords in that stream. If bits [15:11] of the halfword being decoded take any of the following values, the halfword is the first halfword of a 32-bit instruction: `0b11101`, `0b11110`, `0b11111`. Otherwise, the halfword is a 16-bit instruction.

| Bits `[15:11]` of the halfword | Length | Meaning |
|---|---|---|
| `0b11101`, `0b11110`, `0b11111` | 32 bits | First halfword of a two-halfword instruction |
| anything else | 16 bits | A complete instruction |

Three consequences fall out of this immediately.

- **Instructions are halfword-aligned, never word-aligned.** A 32-bit Thumb-2 instruction can straddle a word boundary. This is why a disassembly listing shows addresses stepping by 2 as often as by 4, and why you cannot find instruction boundaries by scanning for aligned words.
- **The encoding space is carved out of the 16-bit space.** `0b11101`–`0b11111` used to be part of the 16-bit map; Thumb-2 reclaimed it. That is the reason the 16-bit instruction set has the slightly lopsided shape it does — see the allocation in *Armv7-M ARM* Table A5-1.
- **You cannot disassemble backwards.** Starting mid-stream, the decode is ambiguous until you find a known-good boundary. This is why a debugger that has lost the plot shows nonsense instructions, and why a corrupted `PC` produces garbage rather than a clean error.

## 16-bit versus 32-bit: what the extra halfword buys

The 16-bit encodings are the ones that carry a program's routine work: register-to-register moves, small-immediate arithmetic, stack pushes and pops, short branches. The 32-bit encodings exist for the cases where 16 bits genuinely cannot express the operation. Here is the same instruction family at both widths, with the constraints taken directly from the architecture manual's encoding definitions.

| Operation | Narrow (16-bit) | Wide (32-bit) | What the extra halfword buys |
|---|---|---|---|
| Move an immediate | `MOVS Rd,#imm8` — encoding T1 | `MOVW Rd,#imm16` — encoding T3 | Range grows from `0`–`255` to `0`–`65535`; T2 instead offers the "modified immediate" set. A full 32-bit constant needs `MOVW` + `MOVT`, i.e. **8 bytes**. |
| Unconditional branch | `B label` — encoding T2, offset `SignExtend(imm11:'0')` | `B.W label` — encoding T4, offset `SignExtend(S:I1:I2:imm10:imm11:'0')` | Range grows from a 12-bit signed byte offset (±2 KB) to **−16 MB to +16 MB**. |
| Conditional branch | `Bcond label` — encoding T1, offset `SignExtend(imm8:'0')` | `Bcond.W label` — encoding T3, offset `SignExtend(S:J2:J1:imm6:imm11:'0')` | Range grows from a 9-bit signed byte offset (±256 bytes) to **−1 MB to +1 MB**. |
| Register access | Most 16-bit forms reach `R0`–`R7` only | 32-bit forms reach `R0`–`R12` freely | The high registers. This is the single biggest reason a function spills to 32-bit encodings. |

Encodings and their pseudocode are *Armv7-M ARM* §A7.7.76 (`MOV` immediate) and §A7.7.12 (`B`); the ±16 MB and ±1 MB figures are stated as such in PM0214 Rev 10, **Table 34 "Branch ranges"** — "`B label` −16 MB to +16 MB", "`Bcond label` (outside IT block) −1 MB to +1 MB". The ±2 KB and ±256-byte figures are read off the 16-bit encodings' own sign-extended offsets in §A7.7.12.

The choice is normally the assembler's, and the rule is spelled out in *Armv7-M ARM* §A7.2: the `.N` qualifier "specifies that the assembler must select a 16-bit encoding… If this is not possible, an assembler error is produced", `.W` forces 32-bit, "and if neither `.W` nor `.N` is specified, the assembler can select either 16-bit or 32-bit encodings. **If both are available, it must select a 16-bit encoding.**"

That last sentence is the whole code-density story in one line: the toolchain gives you the narrow form whenever the narrow form works, automatically, and the wide form only when your operands demand it.

## A worked size comparison

Because the assembler picks encodings by operand, small changes to source code change the size of the machine code in ways that are entirely predictable once you know the rules. Take loading a constant into a register:

| Source | Encoding chosen | Bytes | Why |
|---|---|---|---|
| `x = 200;` | `MOVS Rd,#200` — T1 | **2** | `200` fits in `imm8` (T1 range is 0–255). |
| `x = 300;` | `MOV.W Rd,#300` — T2 | **4** | Too big for `imm8`; expressible as a modified immediate. |
| `x = 0x1234;` | `MOVW Rd,#0x1234` — T3 | **4** | Fits `imm16` (T3 range is 0–65535). |
| `x = 0x12345678;` | `MOVW` + `MOVT` | **8** | No single encoding holds 32 bits of immediate. |

Every row is a direct consequence of the ranges §A7.7.76 gives: "The range of permitted values is 0-255 for encoding T1 and 0-65535 for encoding T3."

Now scale that up. A hundred-instruction function that fits entirely in narrow encodings occupies 200 bytes; the same function forced wide throughout occupies 400. On a part with 512 KB of flash that difference does not matter for one function — but the same mechanism operates on the whole binary, and it is the reason two compilers, or two optimisation levels, can produce firmware images that differ by tens of kilobytes with identical behaviour. It is also why `-Os` is a *default* choice on microcontrollers rather than a special case.

What actually drives a function towards wide encodings, in rough order of impact:

- **Using more than eight live variables at once**, which forces `R8`–`R12` into play and with them the 32-bit forms.
- **Large constants**, as above. A table of magic numbers in code costs more than the same table in `.rodata`.
- **Long branches** — a `switch` over a large body, or a jump out of a big function.
- **Conditional execution.** Thumb-2's `IT` block makes up to four following instructions conditional (PM0214 Rev 10, §3.9.7 `IT`), which avoids a branch — but the `IT` instruction itself is a halfword, and the state it maintains lives in `EPSR` bits `[26:25,15:10]`, which is why an interrupt taken mid-`IT`-block has to save and restore that field. See [The Register Model](./cortex-m-register-model.md).

## What Armv7E-M adds

The Cortex-M4's architecture is not plain Armv7-M but **Armv7E-M** — the "E" is the DSP extension. Arm's Cortex-M4 product page lists what that means: "DSP and SIMD instructions: Single cycle 16/32-bit MAC, Single cycle dual 16-bit MAC, 8 or 16-bit SIMD arithmetic". Concretely, on top of the Armv7-M base, you get saturating arithmetic (`SSAT`, `USAT` — PM0214 Rev 10, Table 30), packing and unpacking instructions (Table 31), and multiply-accumulate forms that treat a 32-bit register as two 16-bit lanes (Table 29).

Two visible consequences for ordinary firmware, both of which show up in the register model:

- `APSR.Q` exists and is **sticky**: it records that a saturation occurred at some point and stays set until software clears it with an `MRS` (PM0214 Rev 10, Table 5).
- `APSR.GE[3:0]` exists, written by SIMD instructions and consumed by `SEL` (Table 5 again).

Neither appears on a Cortex-M3, whose architecture is plain Armv7-M. This is also, incidentally, why ST's own documentation is careful: DS10314 Rev 8 §3.1 says the processor "supports a set of DSP instructions, which allow efficient signal processing and complex algorithm execution", and PM0253 Rev 6 §3.1.1 warns that you cannot move code to a Cortex-M3 "if it contains floating-point operations or DSP extensions".

## Reading a disassembly listing without knowing every mnemonic

You do not need the instruction set memorised to get value out of a listing. Four habits cover most of what a disassembly is asked for during debugging:

1. **Read the address column for instruction width.** A step of 2 is a narrow encoding, a step of 4 is wide. The pattern tells you at a glance whether a function is register-pressured.
2. **Trust the `.W` suffix.** GNU tools print it, and it is the assembler telling you it could not use the narrow form.
3. **Find the function boundaries by the prologue and epilogue.** A Cortex-M function almost always opens with a `PUSH` of the callee-saved registers plus `LR`, and closes with a `POP` that loads `PC` directly — which is both the return *and*, in a handler, the exception return, because a `POP` into `PC` is one of the three instruction forms that consume an `EXC_RETURN` value (PM0214 Rev 10, §2.3.7).
4. **Ignore the mnemonics you don't know and read the operands.** Which registers, which memory addresses, which constants — that is where the bug usually is.

The general craft of this is owned by [Reading Disassembly](../../computer-science/assembly/reading-disassembly.md); what is Cortex-M-specific is the width rule, the `.W` marker and the `POP {PC}` idiom.

:::warning[The missing Thumb bit: a function pointer or vector entry with bit 0 clear]
`PC` bit 0 is not an address bit — it selects the instruction set state, and on Cortex-M there is only one legal value. Everything that writes `PC` therefore has to carry a 1 there:

- **Vector table entries.** PM0214 Rev 10 §2.3.4: "The least-significant bit of each vector must be 1, indicating that the exception handler is Thumb code."
- **The reset vector.** §2.1.3: "Bit[0] of the value is loaded into the EPSR T-bit at reset and must be 1."
- **Function pointers**, which the toolchain sets for you as long as the symbol is a real function symbol.

The C compiler and linker get this right automatically. The places it goes wrong are the places where you take control:

- A **hand-written vector table in assembly** that emits raw addresses with `.word my_handler` where `my_handler` was never declared `.thumb_func` or `.type %function`. The assembler emits the even address and the entry is silently wrong.
- A **function pointer computed arithmetically** — a jump table built from offsets, a bootloader jumping to an application's reset vector by adding a base address, a callback address parsed out of a data blob.
- A **linker script or `.word` constant** that places a raw address in a table the hardware will branch through.

The symptom, from PM0214 Rev 10 §2.1.3: "Attempting to execute instructions when the T bit is 0 results in a fault or lockup." Concretely you get an `INVSTATE` UsageFault — PM0214 Table 19 lists "Attempt to enter an invalid instruction set state" against `INVSTATE`, and §4.4.11 defines the bit as set when "The processor has attempted to execute an instruction that makes illegal use of the EPSR" — which, because `SHCSR.USGFAULTENA` resets to 0 and PM0214 §2.4.2 escalates any fault "for which the priority is the same as or lower than the currently executing exception" — and specifically any fault where "the handler for that fault is not enabled" — arrives as a **HardFault**. Your firmware dies on the *first branch into the bad address*, so the stacked `PC` points at the branch, not at anything wrong with the target.

The lockup case is the one that wastes the most time: if the fault occurs where it cannot be handled — inside the HardFault handler, or from the reset vector itself — the processor enters lockup and stops. A bootloader that jumps to an application whose reset vector was built without the Thumb bit produces a board that appears completely dead after the jump, with no fault handler ever running to tell you why. The fix in that specific case is one line: OR the target address with `1` before branching.
:::

## See also

- [The Register Model](./cortex-m-register-model.md) — `EPSR.T`, the `ICI/IT` field, and `APSR.Q`/`GE` that the DSP extension adds.
- [Exceptions and the Vector Table](./exceptions-and-the-vector-table.md) — where the "least-significant bit must be 1" rule bites hardest.
- [The Cortex-M Family](./arm-cortex-m-profiles.md) — which cores implement Armv7-M, Armv7E-M and the Armv8-M instruction sets.
- [Reading Disassembly](../../computer-science/assembly/reading-disassembly.md) — the general skill this page layers Cortex-M specifics onto.
- [Instruction Set Architecture](../../computer-science/cpu-architecture/instruction-set-architecture.md) — the RISC/CISC and encoding-design background.

## References

- Arm — [***Armv7-M Architecture Reference Manual***](https://developer.arm.com/documentation/ddi0403/latest/), consulted at **DDI 0403E.e (ID021621)**. §A5.1 "Thumb instruction set encoding" for the `[15:11]` length rule quoted above and Table A5-1 for the 16-bit allocation map; §A5.3 for the 32-bit encoding space; §A7.2 "Standard assembler syntax fields" for the `.N`/`.W` qualifiers and the narrow-preferred rule; §A7.7.76 `MOV (immediate)` for the T1/T2/T3 immediate ranges; §A7.7.12 `B` for the four branch encodings and their sign-extended offsets.
- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), consulted at **Rev 10** (March 2020). §2.1.3 for "only supports execution of instructions in Thumb state", the reset-vector bit-0 rule and the fault-or-lockup consequence; §2.3.4 for the vector-table LSB rule; §2.3.7 for `POP {PC}` as an exception-return form; **Table 34 "Branch ranges"** for the ±16 MB and ±1 MB figures; Tables 29–31 for the DSP multiply, saturating and packing instruction groups; Table 5 for `APSR.Q` and `APSR.GE`; §4.4.11 for the `INVSTATE` bit; Table 19 for the fault-to-handler mapping.
- Arm — [**Cortex-M4 product support page**](https://developer.arm.com/Processors/Cortex-M4), retrieved 2026-08-19. The Architecture row (Armv7E-M) and DSP Extension row (single-cycle MAC, dual 16-bit MAC, 8/16-bit SIMD).
- STMicroelectronics — [**STM32F411xC/E datasheet**](https://www.st.com/resource/en/datasheet/stm32f411re.pdf) (DS10314), consulted at **Rev 8** (January 2024). §3.1 for the DSP-instruction and code-efficiency description, and the front-page memory figures that make code density a cost question on this part.
- STMicroelectronics — [**PM0253**, *STM32F7 and STM32H7 series Cortex-M7 processor programming manual*](https://www.st.com/resource/en/programming_manual/pm0253-stm32f7-series-and-stm32h7-series-cortexm7-processor-programming-manual-stmicroelectronics.pdf), consulted at **Rev 6** (May 2026). §3.1.1 for the binary-compatibility limits that make the DSP extension visible as a portability boundary.
