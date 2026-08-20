---
id: cross-compilation
title: Cross-Compilation
sidebar_label: Cross-Compilation
sidebar_position: 1
tags: [embedded, toolchain, cross-compilation, gcc, arm, stm32]
---

# Cross-Compilation

The compiler on your laptop is not a general-purpose translator that happens to be pointed at x86. It is a program that was *built* to emit x86-64 instructions, linked against a C library that was *built* assuming a Linux kernel is underneath it, and wired to a startup object that assumes something already created a process, set up a stack, and handed it `argc` and `argv`. Every one of those assumptions is false on a microcontroller. That is the whole reason a separate toolchain exists — not because the MCU is "different hardware", but because three independent layers of the build all encode a machine and an environment, and all three have to change together.

The mental model to carry is that a toolchain is a **matched set**, not a compiler. Compiler, assembler, linker, C library, startup code, and the pre-built support library (`libgcc`) were all configured for one target and one ABI. Mix a component from a different set and you get either a loud link error or — much worse — a program that links cleanly and behaves wrongly, because two halves of it disagree about how floating-point arguments are passed.

:::info[Prerequisites]
[Cross-Compilation](../../programming/cpp/01-toolchain-and-build/cross-compilation.md) in the C++ section owns the general concept: why you cross-compile at all, host versus target, and the shape of a cross build for desktop-class targets. This page assumes that and covers what changes when the target has no operating system: what `arm-none-eabi` actually encodes, multilib selection, and the ABI mismatches that bite on Cortex-M.
:::

## Three machines, not two

Most explanations say "host and target". The GNU build system uses three names, and the third is the one that resolves the usual confusion. The *Autoconf* manual defines them precisely (§14, "Specifying Target Triplets"):

- **build** — "the type of system on which the package is being configured and compiled."
- **host** — "the type of system on which the package runs."
- **target** — "the type of system for which any compiler tools in the package produce code."

For you, compiling firmware, only two of these are in play: the compiler *runs* on your PC (host) and *emits code for* the STM32F411RE (target). The third matters only to whoever **built the compiler itself**: when Arm builds a Linux-x86-64 `arm-none-eabi-gcc`, that build has build = host = `x86_64-pc-linux-gnu` and target = `arm-none-eabi`. This is why the same tarball is described by two different triples depending on who is talking, and why `gcc -dumpmachine` on a cross compiler prints the *target*, not the machine it is running on.

```bash
gcc -dumpmachine                  # x86_64-pc-linux-gnu   -- your host compiler's target
arm-none-eabi-gcc -dumpmachine    # arm-none-eabi         -- the cross compiler's target
```

A compiler whose target differs from its host is a **cross compiler**. Everything else follows from that one fact.

## Decoding `arm-none-eabi`

The prefix is a GNU *target triplet*: fields separated by hyphens, canonicalised by the `config.sub` script that ships with Autoconf. The nominal form is `cpu-vendor-os`, extended to `cpu-vendor-kernel-os` when a system needs to name both a kernel and a userspace. Fields are omitted rather than padded, which is why the bare-metal triple has three parts and the Linux one has four.

| Field | `arm-none-eabi` | `arm-none-linux-gnueabihf` | What it selects |
|---|---|---|---|
| CPU / architecture | `arm` | `arm` | The 32-bit Arm architecture (A32/T32 instruction sets). AArch64 parts use `aarch64` instead — a *different* toolchain, not a flag. |
| Vendor | `none` | `none` | No vendor-specific customisation. Historically this field carried `pc`, `apple`, `unknown`; for Arm's toolchains it is deliberately empty of meaning. |
| Kernel | *(absent)* | `linux` | Which kernel's system-call interface the C library talks to. **Absent means there is no kernel.** |
| OS / ABI / environment | `eabi` | `gnueabihf` | The calling convention and object-file conventions. `eabi` is the Arm Embedded ABI with no OS layer. `gnueabihf` is the GNU userspace flavour of it, with `hf` = hard-float procedure call standard. |

Three consequences of that table are worth stating out loud, because each one is a real question people ask.

**"none" is the point, not a placeholder.** There is no operating system in the triple, so the C library that ships with the toolchain cannot make a system call. It has to be told how to do I/O, and the mechanism for that — syscall stubs — is the subject of [C Libraries for Embedded](./c-libraries-for-embedded.md). Every "undefined reference to `_write`" you will ever see on this toolchain traces back to this field.

**`eabi` versus `eabihf` is an ABI, not an optimisation.** `hf` means floating-point arguments are passed in VFP registers `s0`/`d0` upward rather than in the core registers. Two objects that disagree cannot be linked. For the bare-metal `arm-none-eabi` toolchain the distinction does not live in the triple at all — it lives in the `-mfloat-abi` flag and the multilib it selects, which is the next section.

**`arm-none-eabi` and `arm-none-eabi` are not necessarily the same thing.** The triple names the ABI family; it says nothing about *which* Arm core. A Cortex-M0 and a Cortex-M4F both use `arm-none-eabi`, and the difference is carried entirely by `-mcpu`, `-mfpu` and `-mfloat-abi`.

## The tools behind the prefix

The prefix is not decoration — it is how several toolchains coexist in one `PATH`. Each is the ordinary binutils/GCC program, configured for that target.

| Tool | What you use it for on firmware |
|---|---|
| `arm-none-eabi-gcc` | Compile, and — importantly — **drive the link**. Call `gcc` to link, not `ld` directly, so the specs files, `libgcc` and the multilib search paths are set up for you. |
| `arm-none-eabi-g++` | Same, for C++. Also links the C++ runtime; see [C Libraries for Embedded](./c-libraries-for-embedded.md) for what that pulls in. |
| `arm-none-eabi-as` | Assembler. Rarely invoked by hand; `gcc` runs it for `.s`/`.S` files. |
| `arm-none-eabi-ld` | The linker. Reads the linker script; see [The Linker Script](./the-linker-script.md). |
| `arm-none-eabi-objcopy` | Convert the ELF into the `.bin` or `.hex` a flashing tool wants. |
| `arm-none-eabi-objdump` | Disassemble, and dump section headers with VMA **and** LMA — the check in [Memory Sections and VMA vs LMA](./memory-sections.md). |
| `arm-none-eabi-size` | Flash and RAM totals per section. The number you watch every build. |
| `arm-none-eabi-nm` | Symbol table; `--size-sort -S` finds what is eating your flash. |
| `arm-none-eabi-readelf` | ELF headers and, usefully here, `-A` prints the build attributes that encode the ABI. |
| `arm-none-eabi-gdb` | Debugger. Talks to OpenOCD or a probe's GDB server over TCP. |

## Multilib: one toolchain, many pre-built libraries

The single biggest practical difference between a hosted cross toolchain and a bare-metal one is that the bare-metal toolchain ships **many** copies of its C library, one per ABI variant, and picks between them at link time from your compile flags. Arm's `arm-none-eabi` toolchain carries dozens.

```bash
arm-none-eabi-gcc -print-multi-lib | head           # every variant that exists
arm-none-eabi-gcc -mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard \
                  -print-multi-directory            # the one your flags select
arm-none-eabi-gcc -mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard \
                  -print-file-name=libc.a           # the exact archive that will be linked
```

For the STM32F411RE — a Cortex-M4 with a single-precision FPU — the flag set is:

```bash
-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard
```

`-mfpu=fpv4-sp-d16` is not a stylistic choice: the Cortex-M4F's FPU is the single-precision-only FPv4-SP with sixteen double-word registers, and PM0214 Rev 10 §4.6 describes it as implementing "the ARMv7E-M architecture… with a single precision FPU". Naming a double-precision unit here would select a multilib whose library assumes hardware the part does not have.

The rule that follows is short and is violated constantly: **these four flags must be identical on every compile command and on the link command.** The compile flags decide which instructions and which calling convention each object uses; the *link* flags decide which pre-built `libc.a`, `libm.a` and `libgcc.a` get pulled in. Set them once in your build system and pass the same variable to both.

## Why your host `gcc` cannot be used

It is worth being concrete, because "wrong architecture" undersells it. Four separate things are wrong at once:

1. **Instruction set.** x86-64 machine code is meaningless to a Cortex-M4, which executes Thumb-2 — see [Thumb-2 and Code Density](../02-processor-architecture/thumb-and-instruction-sets.md).
2. **ABI.** Register roles, argument passing, stack alignment and struct layout all differ. This is what the `eabi` field pins down.
3. **C library.** Your host `libc` reaches a kernel through `syscall`. There is no kernel and no `syscall` instruction on this part.
4. **Startup and link layout.** Host `crt1.o` runs `_start`, which expects a loader to have already mapped the binary and built a stack and an environment. Firmware has to build all of that itself, which is what [Startup Code: Reset to `main`](./startup-code.md) is about, and place it at fixed addresses, which is what [The Linker Script](./the-linker-script.md) is about.

The nearest thing to a sysroot in this world is the toolchain's own bundled headers and libraries. `arm-none-eabi-gcc -print-sysroot` on Arm's distribution typically prints nothing — there is no separate root filesystem image, because there is no filesystem. Contrast that with the Linux cross toolchain `arm-none-linux-gnueabihf-gcc`, which genuinely needs `--sysroot` pointed at a target root containing the target's `glibc` and headers. If a tutorial tells you to set `--sysroot` for bare-metal Cortex-M work, it is a Linux-target tutorial.

:::warning[Flag drift between compiling and linking is the mistake that costs a day]
The failure has two forms and only one of them is loud.

**The loud one.** You compile with `-mfloat-abi=hard` but leave it off the link command. The linker selects the soft-float multilib and then refuses:

```text
error: firmware.elf uses VFP register arguments, libc.a(lib_a-printf.o) does not
error: failed to merge target specific data of file libc.a(lib_a-printf.o)
```

Annoying, but it stops you. The fix is to add the identical flags to the link line.

**The quiet one.** You get the flags consistent but *wrong* — for example `-mcpu=cortex-m3` on a Cortex-M4 part, or `-mfloat-abi=softfp` where the rest of the project uses `hard`. Everything compiles, everything links, and the firmware runs. Then it is 20–40× slower than expected on anything doing arithmetic, because every floating-point operation is going through a `libgcc` software emulation routine instead of a single `VMLA`. There is no warning, no error, and no symptom other than a number in a profiler you have no baseline for. Teams have shipped like this.

Two habits make both forms impossible:

- Define the target flags **once** in the build system and reference the same variable in the compile rule and the link rule.
- Verify the result rather than trusting it. `arm-none-eabi-readelf -A firmware.elf` prints the build attributes; on a correct hard-float Cortex-M4F build it reports `Tag_CPU_name: "Cortex-M4"`, `Tag_FP_arch` naming a VFPv4-D16 single-precision unit, and `Tag_ABI_VFP_args: VFP registers`. If that last line is missing, you built soft-float.
:::

## See also

- [Choosing a Toolchain](./toolchains-and-compilers.md) — which cross toolchain to install, and why the version has to be pinned.
- [C Libraries for Embedded](./c-libraries-for-embedded.md) — what the missing `none` in the triple means you have to supply yourself.
- [The Linker Script](./the-linker-script.md) — the other half of "there is no operating system": deciding where the code goes.
- [Cross-Compilation](../../programming/cpp/01-toolchain-and-build/cross-compilation.md) — the general treatment, including hosted targets and sysroots.
- [Bare-Metal, RTOS, or Linux](../00-overview/bare-metal-vs-rtos-vs-linux.md) — which of the two triples above your project actually needs.

## References

- Free Software Foundation — [***Autoconf* manual, "Specifying Target Triplets"**](https://www.gnu.org/software/autoconf/manual/autoconf.html#Specifying-Target-Triplets). The normative definitions of *build*, *host* and *target* quoted above, and the description of the `config.sub` canonicalisation that turns a loose triple into the form GCC stores.
- Arm — [**Arm GNU Toolchain downloads**](https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads). The distribution page for `arm-none-eabi`, and the place that lists the four target triples Arm publishes: `arm-none-eabi` and `aarch64-none-elf` for bare metal, `arm-none-linux-gnueabihf` and `aarch64-none-linux-gnu` for Linux. Use it to confirm which triple matches your target before installing anything.
- Free Software Foundation — [**GCC manual, "ARM Options"**](https://gcc.gnu.org/onlinedocs/gcc/ARM-Options.html). Definitions of `-mcpu`, `-mthumb`, `-mfpu` and `-mfloat-abi`, including the exact statement that `-mfloat-abi=hard` "allows generation of floating-point instructions and uses FPU-specific calling conventions", which is why it is an ABI switch and not an optimisation.
- Free Software Foundation — [**GCC manual, "Developer Options"**](https://gcc.gnu.org/onlinedocs/gcc/Developer-Options.html). `-print-multi-lib`, `-print-multi-directory`, `-print-file-name` and `-print-sysroot`, the four commands that let you check which library a flag combination will actually select rather than assuming.
- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), consulted at **Rev 10** (March 2020). §4.6 "Floating point unit (FPU)" for the single-precision-only FPU that fixes `-mfpu=fpv4-sp-d16` on this part.
