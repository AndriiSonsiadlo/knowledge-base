---
id: toolchains-and-compilers
title: Choosing a Toolchain
sidebar_label: Choosing a Toolchain
sidebar_position: 2
tags: [embedded, toolchain, gcc, llvm, iar, keil, build]
---

# Choosing a Toolchain

For a hobby project the toolchain question is nearly free: install Arm GNU, move on. For a product it is one of the longest-lived decisions in the codebase. A toolchain choice outlives the engineers who made it, because the compiler is baked into every build artefact you have ever released and into every certification argument you have ever made. Changing it later is not a flag change; it is a re-qualification.

The useful way to frame the decision is that you are not buying a compiler — code generation quality between the serious options is close enough that it rarely decides anything. You are buying a **support and evidence relationship**. A commercial vendor sells you someone to call when the optimiser miscompiles your interrupt handler, and a folder of documents that says an independent assessor examined the compiler against a functional-safety standard. Open toolchains sell you neither, and cost nothing, and are what the overwhelming majority of firmware in the world is built with.

:::info[Prerequisites]
[Cross-Compilation](./cross-compilation.md) explains what a toolchain *is* — the matched set of compiler, assembler, linker, C library and startup code — and how the target triple selects one. This page is about picking between the sets.
:::

## The four that matter

| | **Arm GNU Toolchain** | **LLVM Embedded Toolchain for Arm** | **IAR Embedded Workbench for Arm** | **Keil MDK / Arm Compiler for Embedded** |
|---|---|---|---|---|
| Maintainer | Arm | Arm (open-source project) | IAR Systems | Arm |
| Compiler | GCC | Clang / LLVM | IAR C/C++ Compiler (`iccarm`) | Arm Compiler 6 (`armclang`, Clang-based) |
| Linker | GNU `ld` | LLD | IAR XLINK/ILINK | `armlink` |
| Default C library | newlib, plus newlib-nano | picolibc | IAR DLIB | Arm C library, plus microlib |
| Licence / cost | GPL, free | Apache 2.0 with LLVM exception, free | Commercial, per-seat | Commercial, per-seat; a size-limited free tier exists |
| Safety certification | None supplied | None supplied | Functional-safety edition, independently certified | FuSa-qualified edition available |
| Vendor support contract | Community, plus Arm's issue tracker | Community | Yes | Yes |
| Linker script format | GNU `ld` script (`.ld`) | GNU `ld` script (LLD is compatible) | IAR linker config (`.icf`) — different syntax | Scatter file (`.scat`) — different syntax |
| CI story | Trivial: tarball, no licence server | Trivial | Needs a licence server or a floating licence in the runner | Needs a licence server |
| What you actually get | The default for everything non-certified | Smaller binaries in some workloads, better diagnostics | Support, certification evidence, mature IDE | Support, certification evidence, tight CMSIS/Keil integration |

Two rows in that table do more work than the rest.

**The linker-script row is a portability wall.** GNU `ld` scripts, IAR `.icf` files and Arm `.scat` scatter files describe the same thing in three incompatible syntaxes, and the *symbols* they export differ too. Startup code written against `_sdata`/`_edata`/`_sbss` (the GNU convention this section uses — see [The Linker Script](./the-linker-script.md)) does not compile against IAR's `__ICFEDIT_` symbols or Arm's `Image$$RW_IRAM1$$Base`. Porting a project between toolchain families means rewriting the linker script and the startup file, not recompiling. Budget days, not hours.

**The certification row is the only one worth paying for.** If you are building to IEC 61508, ISO 26262, IEC 62304 or EN 50128, the assessor will ask what evidence you have that your compiler does not silently corrupt your code. A certified toolchain answers that with a certificate and a safety manual listing known deviations. With GCC or Clang you must construct the argument yourself — typically via a qualification kit, a validation suite, or the "proven in use" route — and that work is expensive, so the commercial licence is often the cheaper path in a safety project even at several thousand euros a seat. Outside safety work this row is worth nothing and should not enter the decision.

## When each one is the right answer

**Arm GNU Toolchain** is the default, and should be your default. It is what nearly every open-source embedded project, every Zephyr and FreeRTOS example, every STM32 tutorial and every CI pipeline in this section assumes. It is a plain tarball with no licence server, which makes it trivial to pin in a container. Every page in this folder uses it.

**LLVM Embedded Toolchain for Arm** is the interesting alternative. It is a packaging of Clang, LLD, `compiler-rt` and picolibc into a ready-to-use bare-metal Arm toolchain, and it accepts GNU linker scripts, which means an existing GCC project can often be tried under it with only flag changes. Clang's diagnostics are noticeably better, and its static-analysis and sanitiser ecosystem is stronger. Code size versus GCC is workload-dependent — sometimes better, sometimes worse — so "smaller binaries" is a claim to measure on *your* firmware, not to accept. Treat it as a second opinion you can run in CI alongside GCC: a build under both compilers catches a surprising amount of latent undefined behaviour for the cost of one extra job.

**IAR** is chosen for support and certification, and for teams that have used it for fifteen years and have a working process built around it. Its debugger and its static analysis integration are mature. The cost is per seat, the build is hard to containerise, and the project is locked to it by the `.icf` file.

**Keil MDK / Arm Compiler for Embedded** occupies similar ground, with the additional pull that it is Arm's own compiler and integrates tightly with CMSIS packs and Keil's device database. `armclang` is Clang-based, so its language support tracks Clang, but its linker and library are Arm's own. `microlib` is a genuinely tiny C library, smaller than newlib-nano, at the cost of standards conformance — it is not a fully conforming C library and its documentation says so.

## Version pinning is a requirement

This is the part that is not a preference. A toolchain version is an input to the build in exactly the way your source files are, and an unpinned one makes your build non-reproducible in a way that will eventually cost you a release.

Three concrete failure modes, all common:

- **The optimiser changes and latent undefined behaviour changes with it.** Code with a missing `volatile`, a strict-aliasing violation, or a signed-overflow assumption behaves one way under GCC 10 and another under GCC 13. Nothing in your source changed. Nothing in your test suite necessarily catches it. Peripheral registers are the most fragile case, because they live at addresses the compiler is free to assume nothing ever changes behind its back — [The Cortex-M Memory Map](../02-processor-architecture/memory-map-and-bit-banding.md) covers why the address itself does not save you.
- **Library defaults move.** Which newlib variant is default, what `printf` supports out of the box, and which multilib a flag set selects have all changed across releases. A firmware that fit in flash last year may not this year.
- **You cannot reproduce a shipped binary.** A customer reports a fault in release 2.3.1. You check out the tag, build, and get a binary that differs from the one in the field. Now you are debugging two things.

What pinning looks like in practice:

```bash
# Record the exact toolchain in the build output, every build.
arm-none-eabi-gcc --version | head -1
arm-none-eabi-gcc -print-multi-directory -mcpu=cortex-m4 -mthumb \
                  -mfpu=fpv4-sp-d16 -mfloat-abi=hard
```

- Pin the **exact release string** — Arm's naming is of the form `14.2.Rel1`, not `14.2`. The `.Rel` suffix is a distinct build.
- Record the **SHA-256 of the tarball** you install from, in the repository, next to the version. A version number alone does not tell you the artefact was not re-rolled.
- Install it from a **container image or a checked-in setup script**, not from a developer's package manager. `apt install gcc-arm-none-eabi` gives a different version on every distribution release and is the single most common source of "works on my machine".
- Treat a toolchain upgrade as a **change with a test cycle**, on its own commit, with a size and behaviour comparison in the commit message. Never bundle it with feature work.

:::warning[The unpinned toolchain bug you cannot reproduce]
The shape of this failure is always the same, and it always eats a week.

A build that has worked for a year starts failing on one engineer's machine — or worse, on the CI runner after an image rebuild — with a fault that appears in code nobody has touched. Everyone assumes a race condition, because that is what non-deterministic failures usually are. Days go into instrumenting the wrong subsystem.

The actual cause is that the toolchain moved. A newer GCC decided that a loop whose exit condition depends on a variable modified by an interrupt handler — a variable someone forgot to mark `volatile` — can be hoisted, so the loop now never terminates. Or it inlined a function across a `__disable_irq()` boundary. Or it noticed a strict-aliasing violation in a protocol parser and optimised on the assumption that two pointers cannot alias. The source was always wrong; the old compiler was just being generous.

Two things prevent the whole class:

- **Pin the toolchain and record it in the build artefact.** When the failure appears, the very first diff you can run is old-toolchain versus new-toolchain, and the investigation is over in an hour instead of a week.
- **Build under a second compiler in CI.** Clang and GCC do not make the same optimisation choices, so undefined behaviour that is benign under one frequently breaks under the other — at your desk, on a scheduled CI job, rather than in the field. This is the practical argument for having the LLVM toolchain installed even if you ship GCC.

The tempting non-fix is to pin the toolchain and stop there, leaving the missing `volatile` in place. That works until the next upgrade, which is now scarier than it was before, because you know the codebase does not survive one.
:::

## See also

- [Cross-Compilation](./cross-compilation.md) — what a toolchain is made of, and how the target triple selects one.
- [C Libraries for Embedded](./c-libraries-for-embedded.md) — the library half of the choice: newlib, newlib-nano and picolibc.
- [The Linker Script](./the-linker-script.md) — the GNU `ld` script format that ties this section to the GNU toolchain.
- [Startup Code: Reset to `main`](./startup-code.md) — the other toolchain-specific file a port would have to rewrite.
- [What is CMake](../../programming/cmake/00-intro/what-is-cmake.md) — the build system these toolchains are usually driven from.

## References

- Arm — [**Arm GNU Toolchain downloads**](https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads). The canonical distribution: release naming (`14.2.Rel1` and similar), the four supported target triples, and per-release notes. This is the page to pin against; the release notes are where library and multilib default changes are announced.
- Arm — [**LLVM Embedded Toolchain for Arm**](https://github.com/arm/LLVM-embedded-toolchain-for-Arm). The project README documents what the distribution contains (Clang, LLD, `compiler-rt`, picolibc), which Arm architectures are supported, and the flags needed to select a target — including that it consumes ordinary GNU linker scripts, which is what makes trying it on an existing GCC project cheap.
- IAR Systems — [**IAR Embedded Workbench for Arm**](https://www.iar.com/products/architectures/arm/iar-embedded-workbench-for-arm/). Product and functional-safety-edition documentation, including which standards the certified edition is assessed against and what the safety manual covers. Read the safety manual's deviation list before assuming certification removes work.
- Arm — [**Arm Compiler for Embedded documentation**](https://developer.arm.com/documentation/100748/latest/). The `armclang`/`armlink` user guide, the scatter-file syntax, and the microlib documentation — including microlib's explicit statement of where it does not conform to the C standard, which is the trade you are making when you select it.
- Free Software Foundation — [**GCC manual, "Options That Control Optimization"**](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html). Background for the version-pinning argument: which optimisations are enabled at each level, and which of them (`-fstrict-aliasing`, `-ftree-loop-distribute-patterns`) are the ones whose behaviour changes across releases on code that has latent undefined behaviour.
