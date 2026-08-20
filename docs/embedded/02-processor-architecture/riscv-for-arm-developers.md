---
id: riscv-for-arm-developers
title: RISC-V for Arm Developers
sidebar_label: RISC-V for Arm Developers
sidebar_position: 11
tags: [embedded, riscv, cortex-m, arm, architecture, comparison]
---

# RISC-V for Arm Developers

Everything in this folder so far has described one architecture. The reason that is a reasonable way to spend eleven pages is that Cortex-M is what the overwhelming majority of microcontroller work is written against. The reason it is not the *only* thing worth knowing is that RISC-V parts are now genuinely shipping in volume — the ESP32-C3 in a hobbyist's hands, the CH32V003 at ten cents, the RISC-V management cores inside SoCs whose application processors are Arm — and the transition is much easier than a new instruction set sounds, provided you know which of your Cortex-M assumptions are architectural and which are Arm's.

That is what this page is for. **Almost every concept transfers; almost none of the register names do.** The interrupt controller has a different name and a different programming model, but it still arbitrates priorities. Special registers still exist and still need dedicated instructions; they are just called CSRs and reached with `csrrw` instead of `MSR`. The one genuinely new idea is that RISC-V is a *specification with options*, not a processor you licence — so two RISC-V microcontrollers can differ in ways that two Cortex-M4s cannot.

And there is one genuinely missing convenience, which is worth flagging up front because it produces the most common porting bug: **RISC-V does not stack registers in hardware on a trap.** A Cortex-M handler can be an ordinary C function because the processor pushed the caller-saved set before the first instruction. A RISC-V handler cannot.

:::info[Prerequisites]
This page assumes the rest of folder 02 — the register model, exception handling, the NVIC, the MPU — because it is written as a mapping *from* those things. [Instruction Set Architecture](../../computer-science/cpu-architecture/instruction-set-architecture.md) owns the general RISC-versus-CISC and ISA-design material this page does not repeat.
:::

## The side-by-side map

| Concept | Cortex-M (Armv7-M) | RISC-V | Notes on the difference |
|---|---|---|---|
| Instruction set | Thumb-2, fixed by the profile | `RV32I` base + optional extensions | RISC-V lets you *choose*; Arm ships you a fixed set. |
| Code density | 16/32-bit mixed Thumb-2 | `C` extension, 16-bit compressed | Same idea, different mechanism. |
| General registers | `R0`–`R12`, plus `SP`, `LR`, `PC` | `x0`–`x31`; `x0` hardwired to zero | 32 registers, none of them the PC. |
| Zero constant | An immediate or a spare register | `x0` — reads 0, writes discarded | Removes the need for many pseudo-ops. |
| Program counter | `R15`, readable and writable | Not a GPR; `auipc` reads it | Arm's PC-as-a-register is unusual. |
| Link register | `LR` (`R14`) | `ra` (`x1`), by ABI convention | Convention, not architecture. |
| Stack pointer | Banked `MSP` / `PSP` | `sp` (`x2`); no banking | No hardware two-stack split. |
| Condition flags | `APSR` — `N`, `Z`, `C`, `V` | **None.** Comparisons live in the branch | `beq`, `blt`, `bltu` compare and branch in one instruction. |
| Conditional execution | `IT` blocks | None | Branches only. |
| Special registers | `MSR` / `MRS` on `CONTROL`, `BASEPRI`… | **CSRs** via `csrrw`, `csrrs`, `csrrc` | Same idea: a separate namespace with its own access instructions. |
| Where handlers live | Vector table of addresses at `VTOR` | `mtvec` — one handler address, or a vectored base | A table of *code*, not of pointers, in vectored mode. |
| Which exception fired | `IPSR` / `EXC_RETURN` | `mcause` | `mcause` bit 31 distinguishes interrupt from exception. |
| Faulting address | `MMFAR` / `BFAR` | `mtval` | |
| Return address | Stacked at frame offset `0x18` | `mepc` (a CSR, not the stack) | |
| Return from handler | `BX LR` with `EXC_RETURN` | `mret` | A real instruction, not a magic value. |
| Register save on entry | **Hardware** stacks 8 (or 26) words | **Software.** Nothing is stacked | The biggest practical difference. |
| Interrupt controller | NVIC — integral, priorities, nesting | CLINT + PLIC, or the optional CLIC | PLIC is a separate device with claim/complete. |
| System timer | SysTick, 24-bit, in the core | `mtime` / `mtimecmp` in the CLINT, 64-bit | 64 bits removes SysTick's 168 ms ceiling. |
| Software-triggered switch | `PendSV` | `msip` software interrupt in the CLINT | |
| Global interrupt disable | `PRIMASK` / `CPS` | `mstatus.MIE` | |
| Priority-threshold masking | `BASEPRI` | PLIC priority threshold register | Per-hart, in the controller, not the core. |
| Privilege levels | Privileged / unprivileged, Thread / Handler | **M / S / U** modes | S-mode exists for OS use; MCUs use M, or M+U. |
| Memory protection | MPU, 8 power-of-two regions | **PMP**, 16 entries, NAPOT/TOR | Same purpose, different encoding. |
| Memory map | Architecturally fixed PPB at `0xE000_0000` | **Nothing is fixed.** The SoC decides | The portability difference that bites hardest. |
| Barriers | `DMB`, `DSB`, `ISB` | `fence`, `fence.i` | |
| Atomics | `LDREX` / `STREX` | `A` extension: `lr.w`/`sc.w`, plus AMOs | RISC-V also has fetch-and-add style AMOs. |
| Toolchain triple | `arm-none-eabi-` | `riscv32-unknown-elf-` (or `riscv64-`) | |

## Reading a RISC-V ISA string

Arm tells you the core name and you look up what it implies. RISC-V tells you the ISA string and it *is* the specification.

| Letter | Extension | Notes |
|---|---|---|
| `RV32` / `RV64` | Register width | `RV32` for microcontrollers. |
| `I` | Base integer instruction set | 32 registers. Always present. |
| `E` | Embedded base | 16 registers instead of 32, for the very smallest cores. |
| `M` | Integer multiply and divide | Without it, `a * b` is a library call. |
| `A` | Atomics | Load-reserved / store-conditional and atomic memory operations. |
| `F` | Single-precision floating point | The equivalent of the Cortex-M4F's FPU. |
| `D` | Double-precision floating point | Implies `F`. |
| `C` | Compressed 16-bit encodings | The density feature; near-universal on MCUs. |
| `Zicsr` | CSR access instructions | Split out of `I` in later spec versions — needed for *any* trap handling. |
| `Zifencei` | Instruction-fetch fence | Needed for self-modifying or newly-loaded code. |
| `B` (`Zba`/`Zbb`/`Zbs`) | Bit manipulation | Counterparts to Arm's `CLZ`, `RBIT`, bitfield instructions. |
| `V` | Vector | The Helium/NEON analogue. Rare on small MCUs. |
| `G` | Shorthand for `IMAFDZicsr_Zifencei` | "General purpose". |

So `RV32IMAC` is a 32-bit core with multiply/divide, atomics and compressed instructions — and **no floating-point unit**, which is the string the ESP32-C3 and many other MCU-class parts carry. `RV32EC` is the ten-cent end of the market. The string goes straight into the compiler: `-march=rv32imac -mabi=ilp32`. Get it wrong and you either fail to link against a differently-built libc or execute an instruction the silicon does not implement.

This is the mental shift that matters most. On Arm, "Cortex-M4" narrows things down and the vendor's optional choices are a short list ([The Cortex-M Family](./arm-cortex-m-profiles.md) covers reading them out). On RISC-V, the ISA string *is* the contract, and it is the first thing to look for in a datasheet.

## Traps: one entry point, and nothing saved for you

A Cortex-M exception is dispatched by hardware through a table of function pointers, with the caller-saved registers already pushed. RISC-V does considerably less.

On a trap, the hardware writes `mepc` with the address to return to, writes `mcause` with the reason, writes `mtval` with a relevant address or instruction, saves the previous interrupt-enable state into `mstatus.MPIE` and clears `mstatus.MIE`, and jumps to the address in `mtvec`. **That is all.** No registers are stacked. The handler starts executing with the interrupted program's register values still live, and the moment it uses `t0` it has destroyed them.

`mtvec` also carries a 2-bit `MODE` field in its low bits:

| `MODE` | Behaviour |
|---|---|
| `0` — Direct | Every trap jumps to `BASE`. The handler reads `mcause` and dispatches in software. |
| `1` — Vectored | Exceptions jump to `BASE`; *interrupts* jump to `BASE + 4 × cause`. Each slot holds an **instruction**, so it is normally a jump. |

Note the difference from a Cortex-M vector table: in vectored mode the table is four bytes of *code* per entry, not a pointer. And `BASE` must be aligned — 4 bytes in direct mode, and implementations commonly require more in vectored mode.

The two handler shapes, side by side:

```c
/* Cortex-M: the hardware already pushed R0-R3, R12, LR, PC, xPSR.
   An ordinary C function is a correct handler. */
void TIM2_IRQHandler(void)
{
    TIM2->SR = ~TIM_SR_UIF;
    tick++;
}
```

```c
/* RISC-V: nothing was pushed. The attribute makes the compiler emit a
   prologue that saves every register the body touches, and end with mret
   instead of ret. Without it, this function silently corrupts the
   interrupted code's registers. */
__attribute__((interrupt)) void machine_timer_handler(void)
{
    tick++;
    set_next_timer_compare();
}
```

```armasm
    # What the attribute buys you, in outline: save, dispatch, restore, mret.
    addi  sp, sp, -64
    sw    ra,  0(sp)
    sw    t0,  4(sp)
    # ... every caller-saved register the handler body uses ...
    csrr  a0, mcause
    call  dispatch
    lw    ra,  0(sp)
    lw    t0,  4(sp)
    addi  sp, sp, 64
    mret
```

`mret` restores `mstatus.MIE` from `MPIE` and jumps to `mepc`. There is no `EXC_RETURN`, no bit encoding the stack in use, and no frame type — because the frame is entirely the software's construction.

The trade is real in both directions. Arm's hardware stacking costs 12 cycles that a handler doing almost nothing did not need; RISC-V's software stacking costs whatever the handler actually requires, which can be less for a tiny handler and more for a large one. What Arm buys with those cycles is tail-chaining and late arrival — optimisations that only exist because the hardware owns the frame ([The NVIC](./the-nvic.md) covers what they are worth).

## The CSR namespace

CSRs are RISC-V's answer to `CONTROL`, `PRIMASK`, `BASEPRI` and the SCB: a separate 12-bit address space, reachable only through dedicated atomic read-modify-write instructions.

| CSR | Purpose | Cortex-M analogue |
|---|---|---|
| `mstatus` | Global state; `MIE` enables interrupts, `MPIE`/`MPP` hold the pre-trap state | `PRIMASK` + `CONTROL` |
| `mtvec` | Trap handler base address and mode | `VTOR` |
| `mepc` | Address to return to | Stacked return address |
| `mcause` | Why the trap happened; bit 31 = interrupt | `IPSR` + `CFSR` |
| `mtval` | Faulting address or instruction | `MMFAR` / `BFAR` |
| `mie` / `mip` | Interrupt enable and pending, per class | `NVIC_ISER` / `NVIC_ISPR` |
| `mscratch` | A word for the handler's own use, typically a stack pointer | (no equivalent — Arm banks `SP` instead) |
| `misa` | Which extensions this hart implements | `CPUID` |
| `mhartid` | Which hart (hardware thread) this is | (no equivalent on single-core M) |
| `pmpcfg0`–`3`, `pmpaddr0`–`15` | Physical memory protection | `MPU_RASR` / `MPU_RBAR` |

`csrrw rd, csr, rs` swaps a register with a CSR; `csrrs` and `csrrc` set and clear bits; each has an immediate form. The assembler's `csrr`, `csrw`, `csrs` and `csrc` pseudo-instructions cover the common cases. The parallel with `MRS`/`MSR` is close enough that the habit transfers directly — including the habit of remembering that these are privileged.

`mscratch` deserves a note because it substitutes for something Arm does in hardware. Cortex-M banks the stack pointer so a handler automatically runs on `MSP` while a task's `PSP` is preserved ([Privilege Modes and the Two Stacks](./privilege-modes-and-stacks.md)). RISC-V has one `sp`, so the convention is to keep the handler's stack pointer in `mscratch` and swap it with `sp` on entry using a single `csrrw sp, mscratch, sp`. Same outcome, one instruction of software instead of a banked register.

## Interrupt controllers and the timer

Three names, and which ones your part has is an SoC decision:

- **CLINT** — Core-Local Interruptor. Provides the machine timer (`mtime`, a 64-bit up-counter, and `mtimecmp`, its compare register: an interrupt fires when `mtime >= mtimecmp`) and the software interrupt (`msip`). This is the SysTick and `PendSV` of RISC-V. The 64-bit width is a genuine improvement — none of SysTick's 24-bit ceiling, and no wraparound to handle.
- **PLIC** — Platform-Level Interrupt Controller. Routes external device interrupts. Per-source priorities, per-hart enables, and a per-hart threshold register that works like `BASEPRI`. The distinctive part is the **claim/complete protocol**: the handler reads the claim register to learn which source won *and* to acknowledge it, then writes the same value back on completion. The base PLIC does not preempt or nest — a single external-interrupt line reaches the core, and priorities only decide who is claimed next.
- **CLIC** — Core-Local Interrupt Controller, an optional newer specification that adds vectoring, preemption and hardware nesting. This is the closest thing to an NVIC, and where a part has one, Cortex-M interrupt intuitions transfer almost unchanged.

The addresses of all three are **not architectural**. There is no equivalent of `0xE000_E010`; the CLINT's base address on a SiFive FE310 is not the CLINT's base address on a CH32V003. They come from the SoC's manual or its device tree.

:::warning[The three assumptions that break when Cortex-M habits meet a RISC-V part]
**Writing a trap handler as a plain C function.** This is the big one. On Cortex-M, `void TIM2_IRQHandler(void)` is a complete and correct handler because the hardware pushed the caller-saved set. Write the equivalent on RISC-V without `__attribute__((interrupt))` and the compiler emits a normal function: it saves the *callee*-saved registers it uses, per the ABI, and freely clobbers `t0`–`t6` and `a0`–`a7` — which belong to the interrupted code and were never saved. It also ends with `ret`, jumping to `ra` instead of `mepc`. The result is not a crash; it is the interrupted program resuming with several registers holding the handler's leftovers. The corruption is intermittent, depends on the compiler's register allocation, and moves when you add a printf. Days.

**Assuming the interrupt controller preempts.** A plain PLIC does not nest. Priorities decide which pending source is *claimed next*, not whether a running handler is interrupted; while a handler runs, `mstatus.MIE` is clear and nothing preempts it unless the handler explicitly re-enables interrupts after saving `mepc` and `mstatus`. A latency-critical interrupt designed around a Cortex-M's automatic preemption will not behave the same way. Check whether the part has a CLIC before assuming nesting.

**Assuming a fixed memory map.** There is no architectural PPB, so a driver that hardcodes a timer or controller address is bound to one SoC. This is also why RISC-V embedded code leans on device trees and generated headers far earlier in the stack than Cortex-M code does — the information genuinely is not in the architecture.

And a smaller one that costs a confusing afternoon: **`mtvec`'s low two bits are the mode field.** Writing a handler address that happens to have bit 0 or 1 set does not fault; it silently selects vectored mode, and traps start dispatching to `BASE + 4 × cause` — an address inside or past your handler. It is the exact mirror of the Cortex-M vector-table LSB rule from [Thumb-2 and Code Density](./thumb-and-instruction-sets.md), with the opposite polarity: on Arm the low bit must be **set**, on RISC-V it must be **clear** unless you mean it.
:::

## What transfers, and what to relearn

Everything conceptual transfers. Interrupt latency, priority inversion, critical sections, the cost of a context switch, stack budgeting, the discipline of `volatile` on memory-mapped registers, why a peripheral flag must be cleared before returning — all of it is the same engineering on both architectures, and all of it is what the rest of this section is about.

What has to be relearned is a list, not a discipline: register names, CSR names, the trap-entry sequence, the controller's programming model, and the ISA string. A firmware engineer comfortable with Cortex-M is productive on RISC-V in a few days, and the thing that slows them down is almost always the missing hardware stacking rather than anything about the instruction set.

## See also

- [The Cortex-M Family](./arm-cortex-m-profiles.md) — the Arm side of the "what did the vendor actually configure" question that an ISA string answers on RISC-V.
- [Exceptions and the Vector Table](./exceptions-and-the-vector-table.md) — the vector table and hardware stacking that `mtvec` and `mret` replace.
- [The NVIC](./the-nvic.md) — priorities, nesting, tail-chaining and late arrival, and what a plain PLIC does not give you.
- [The Memory Protection Unit](./the-mpu.md) — the region model that PMP re-implements with a different encoding.
- [Instruction Set Architecture](../../computer-science/cpu-architecture/instruction-set-architecture.md) — the general ISA-design material this page's comparison sits on top of.

## References

- RISC-V International — [***The RISC-V Instruction Set Manual, Volume I: Unprivileged Architecture***](https://riscv.org/technical/specifications/). The base `RV32I` register file including the hardwired `x0`, the absence of condition flags, the branch-comparison instructions, `auipc`, and the `M`, `A`, `F`, `D` and `C` extensions plus the `Zicsr` and `Zifencei` sets and the ISA naming scheme. This is the document to check an ISA string against.
- RISC-V International — [***The RISC-V Instruction Set Manual, Volume II: Privileged Architecture***](https://riscv.org/technical/specifications/). The normative source for everything in the CSR and trap sections: machine-mode CSRs (`mstatus`, `mtvec` with its `MODE` field, `mepc`, `mcause`, `mtval`, `mie`, `mip`, `mscratch`, `misa`, `mhartid`), the trap-entry and `mret` semantics, the M/S/U privilege model, and **Physical Memory Protection** with the `pmpcfg`/`pmpaddr` registers and their `OFF`/`TOR`/`NA4`/`NAPOT` address-matching modes.
- RISC-V International — [**RISC-V Platform-Level Interrupt Controller (PLIC) specification**](https://github.com/riscv/riscv-plic-spec) and the **CLIC specification** (`riscv/riscv-fast-interrupt`). The claim/complete protocol, the per-hart priority threshold, and — in the CLIC document — the vectoring and preemption the base PLIC lacks. Both are separate specifications from the ISA manuals precisely because they are platform components, not architecture.
- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), consulted at **Rev 10** (March 2020), for the Cortex-M column of the comparison table — §2.1 for the register model, §2.3 for the exception model and hardware stacking, §4.2–§4.6 for the MPU, NVIC, SCB, SysTick and FPU rows.
- SiFive — [**FE310-G002 manual**](https://www.sifive.com/documentation). A concrete, freely available example of an `RV32IMAC` microcontroller with a CLINT and a PLIC at documented, SoC-specific addresses — useful for seeing how much of a real RISC-V part's programming model comes from the platform rather than the ISA.
