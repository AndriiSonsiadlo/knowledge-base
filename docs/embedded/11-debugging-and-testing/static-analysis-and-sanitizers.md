---
id: static-analysis-and-sanitizers
title: Static Analysis and Sanitizers
sidebar_label: Static Analysis and Sanitizers
sidebar_position: 11
tags: [embedded, testing, static-analysis, cppcheck, clang-tidy, sanitizers, ci]
---

# Static Analysis and Sanitizers

There is a tool that finds real defects, requires no new install, no configuration file, and no CI integration beyond a flag already accepted by the compiler you are already invoking on every build — and most projects run it in a mode that throws its findings away. That tool is the compiler itself. `arm-none-eabi-gcc` already builds a fully type-checked internal representation of your program to generate code from; a warning is analysis it already did, offered back to you, and the default build configuration in a great many embedded projects is `-Wall` at best, or nothing at all, which means the cheapest static analysis available is routinely left switched off.

The mental model worth carrying through the rest of this page: **static analysis is a spectrum, not a single tool**, ordered roughly by how much it costs to run and how deep the defects it finds are buried. Compiler warnings sit at one end — instantaneous, part of every build, catching the class of bug that is visible from a single function's syntax tree. A dedicated linter like `cppcheck` or `clang-tidy` sits further along — a separate pass, slower, catching patterns that need more context than one function. Dynamic sanitizers are a different axis entirely: they do not read the source at all, they instrument a *running* binary and catch defects only in the code paths that binary actually executes. And commercial whole-program analyzers sit at the far end, paying for depth and for the audit trail a certification process needs, not for finding a bug a free tool would have found for nothing.

None of these replace each other, and none of them replace a test. A tool in this list tells you a piece of code is *suspicious*; only running it — on the host, per [Unit Testing Firmware](./unit-testing-firmware.md), or on the target — tells you it is *wrong*.

:::info[Prerequisites]
[Unit Testing Firmware](./unit-testing-firmware.md) owns the host build target that this page's sanitizer section depends on — ASan and UBSan run against that binary, not against `firmware.elf`, and the reason is explained below.
:::

## Compiler warnings, at a concrete flag set

`-Wall` and `-Wextra` are the two names everyone knows, and both undersell what GCC can be asked to check. A set worth putting in every embedded project's build, as a starting point rather than a ceiling:

```makefile title="Warning flags for arm-none-eabi-gcc, added once, kept forever"
CFLAGS += -Wall -Wextra -Wshadow -Wconversion -Wsign-conversion \
          -Wdouble-promotion -Wformat=2 -Wundef -Wcast-align \
          -Wpointer-arith -Wlogical-op -Wduplicated-cond \
          -Wduplicated-branches -Wnull-dereference
```

| Flag | Catches | Why it earns a place on an embedded build specifically |
|---|---|---|
| `-Wall -Wextra` | The broad baseline: unused variables, comparisons that are always true/false, missing `switch` cases, and dozens more | The floor everything else builds on; GCC's own documentation calls out that `-Wall` alone omits several checks most people expect it to include, which is why `-Wextra` is not optional |
| `-Wshadow` | A local variable or parameter that hides an outer one of the same name | The specific embedded shape: a global `status` and a local `status` inside an ISR — the assignment you meant for the global silently updates a local that vanishes at return |
| `-Wconversion` / `-Wsign-conversion` | Implicit narrowing (`uint32_t` truncated into a register's `uint8_t` field) and signed/unsigned mismatches | Register-level code moves values between differently-sized integer types constantly; this is where an off-by-a-bit-width bug in a bitfield write hides |
| `-Wdouble-promotion` | A `float` silently promoted to `double` in an expression | On a Cortex-M4F with a single-precision FPU, a promoted double falls back to slow software floating point and pulls extra library code into flash — a correctness-adjacent warning that is really a performance and code-size one on this class of part |
| `-Wformat=2` | `printf`-family format strings that do not match their arguments | The classic way a `%d` against a `uint32_t` argument writes garbage or crashes a minimal `printf` implementation |
| `-Wundef` | An `#ifdef`/`#if` testing a macro that was never `#define`d | A silently-false conditional compiles the wrong branch of a feature flag with no error at all |
| `-Wcast-align` | A cast that increases a pointer's required alignment | The Cortex-M4 tolerates some unaligned access but not all of it, and a bad cast here is a MemManage or UsageFault waiting for the wrong compiler flags to expose it |
| `-Wlogical-op`, `-Wduplicated-cond`, `-Wduplicated-branches` | `&&`/`||` typos, and copy-pasted `if`/`else if` chains with a duplicated or dead condition | The unglamorous but common defect of a state machine's transition table with one condition pasted twice and the intended one missing |
| `-Wnull-dereference` | A pointer used after a path that could have left it null | Catches a subset of the null derefs that would otherwise only surface as a HardFault — see [HardFault Forensics](./hardfault-debugging.md) for what happens when this one gets through anyway |

Add `-Werror` once the flag set is clean, so a new warning is a build failure rather than scrollback nobody reads. The single biggest reason projects skip this entirely is that turning it on for the first time against years of accumulated code produces hundreds of warnings at once — the section on rolling this into CI below is specifically about not letting that discourage you into leaving it off forever.

## Tool against defect class

| Tool | Runs where | Representative defect class | Notes |
|---|---|---|---|
| Compiler warnings (`-Wall -Wextra` and the set above) | Every build, both host and target | Type mismatches, shadowing, format-string errors, dead conditions | Free — already part of the toolchain, zero extra CI time |
| `cppcheck` | Source, no build required | Null dereference, resource leaks, out-of-bounds array index, uninitialized variables the compiler's local view misses | Very low false-positive rate by design; the MISRA addon is the same binary in a different mode |
| `clang-tidy` | Source plus a compile database | Everything `cppcheck` finds, plus modernization (`modernize-*`), bug-prone patterns (`bugprone-*`), and portability/CERT-style rules | Needs `compile_commands.json` from the *actual* cross-compilation, or it checks the wrong preprocessor definitions |
| Commercial (Coverity, Polyspace, Klocwork) | CI, often cloud or license-server based | Deep interprocedural data-flow bugs across translation units, plus certification-grade MISRA/CERT compliance reports with an audit trail | Where the price buys something free tools do not: whole-program reasoning and a paper trail a DO-178C/IEC 61508/ISO 26262 audit will ask for |
| AddressSanitizer (`-fsanitize=address`) | Host build only | Out-of-bounds heap/stack/global access, use-after-free, double-free | Requires a hosted OS underneath it — see below for why it cannot run on `firmware.elf` |
| UndefinedBehaviorSanitizer (`-fsanitize=undefined`) | Host build only | Signed integer overflow, shift by an out-of-range amount, misaligned pointer use, null-pointer arithmetic | Catches the exact category of bug that "works today, breaks with the next compiler upgrade" |

## `cppcheck`: fast, low noise, and the MISRA addon

`cppcheck` is deliberately tuned to keep its false-positive rate low rather than to flag every conceivably suspicious pattern, which is what makes `--enable=all` livable as a default rather than a firehose:

```bash
cppcheck --enable=all --inconclusive --error-exitcode=1 src/
```

`--inconclusive` widens the net to findings `cppcheck` is not fully certain about — worth a look interactively, worth thinking twice about before gating a merge on. `--error-exitcode=1` is what turns a finding into a CI failure rather than a line of scrollback. Suppress a specific known-acceptable finding, with a reason, rather than disabling the whole category:

```text title="suppressions.txt — every line is a decision, not a blanket exemption"
// Intentional: fixed-size ring buffer, index arithmetic wraps by design
arrayIndexOutOfBounds:src/ring_buffer.c:42
```

The **MISRA addon** is the same binary, a different flag: `cppcheck --addon=misra.json --enable=style src/`. MISRA C is a licensed standard, so `cppcheck` reports rule numbers (`c2012-21.3`) rather than the rule text itself — a `--rule-texts` file with the actual guideline wording, obtained separately, is what turns a bare rule number into something a reviewer can act on without a paper copy of the standard open on the desk (documentation checked 2026-08-27).

## `clang-tidy`: broader checks, and the compile-database trap

`clang-tidy` needs to understand the same preprocessor definitions, include paths and target flags the real build uses, which for cross-compiled firmware means it needs `compile_commands.json` generated from the **actual `arm-none-eabi-gcc` invocation**, not a host-flavoured approximation — CMake's `CMAKE_EXPORT_COMPILE_COMMANDS=ON` or `compiledb` for a Makefile project both produce it directly from the real build log. Point `clang-tidy` at a database built any other way and it silently analyzes the wrong preprocessor branches — an `#ifdef STM32F411xE` that never got defined because the compile database used a host `gcc` invocation instead of the cross one — and either misses real findings or invents ones that do not apply.

A `.clang-tidy` file at the project root scopes which check families run, which matters because the full check set is large and not all of it is embedded-relevant:

```yaml title=".clang-tidy"
Checks: >
  bugprone-*,
  cert-*,
  -bugprone-easily-swappable-parameters,
  performance-*,
  readability-magic-numbers
```

Start with `bugprone-*` and a handful of `cert-*` checks — the categories closest to "this is a defect," not "this is a style preference" — and add `readability-*`/`modernize-*` checks deliberately, one at a time, rather than accepting the tool's full default set on day one.

## Where commercial tools earn their price

Free tools find a large fraction of real bugs for zero license cost, and it is worth being honest about where they stop. `cppcheck` and `clang-tidy` both reason mostly within a translation unit or a shallow call chain; a defect that only manifests through a data-flow path crossing a dozen files — a value set in one module, checked incorrectly three call frames later in another — is the kind of finding a commercial whole-program analyzer (Coverity, Polyspace, Klocwork) is built to trace and a free tool routinely misses by design, not by bug. The other thing the license buys, separate from raw finding quality, is the paper trail: a MISRA or CERT compliance report with per-rule sign-off and a tool-qualification record is what a DO-178C, IEC 61508 or ISO 26262 audit actually asks for, and that artifact is part of what the commercial license is paying for, not an incidental extra. If the project has no certification requirement, that half of the value is not on the table, and the case for a commercial tool narrows to "does its data-flow analysis find bugs the free tools miss, often enough to justify the cost" — worth trialling against your own codebase before buying, not assuming.

## ASan and UBSan: on the host build, not on `firmware.elf`

AddressSanitizer and UndefinedBehaviorSanitizer work by instrumenting every memory access and arithmetic operation the compiler generates, surrounding heap and stack allocations with "redzones" the instrumentation watches, and reporting through the host's signal-handling and symbolization machinery. All of that assumes a hosted operating system underneath the binary — `mmap` for the redzones, signal handlers for trapping the fault, a symbolizer that reads the binary's own debug info off a filesystem. None of that exists on bare-metal firmware running directly on a Cortex-M4 with no OS, and porting the sanitizer runtime to run that way is a much larger undertaking than most projects need to take on.

What is practical, and worth doing on every project with a host test target from [Unit Testing Firmware](./unit-testing-firmware.md), is building that *same* logic — the pure functions, the state machines, the parsers, and the device-driver layer behind [Mocking Hardware](./mocking-hardware.md)'s seam — a second time with the sanitizers enabled, purely for the host build:

```bash
gcc -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
    -c frame.c mcp9808.c -o /dev/null   # compile-and-check; link into the test binary for a real run
```

Because it is the *same source file* compiled for the host in [Unit Testing Firmware](./unit-testing-firmware.md)'s dual-build structure, a sanitizer finding in the host build is a finding in code that also ships to the target — the sanitizer is testing your logic, using a capability the target's own toolchain cannot offer, without ever needing to run on hardware at all.

:::warning[A cast that silences the warning instead of fixing the defect, and a sanitizer that only watched the paths you exercised]
**Silencing `-Wconversion` with a cast instead of reading what it found.** `-Wconversion` on a codebase that has never had it enabled produces a wave of findings, and the fastest way to make the wave stop is `(uint8_t)value` at every site the compiler complains about. Some of those casts are genuinely correct — the value really is known to fit. Some are not: a millivolt reading truncated into a byte because a struct field was sized for a different sensor, silenced rather than fixed, ships a defect that is now permanently invisible to the compiler because the cast is an explicit instruction to stop checking. The tell, months later, is a value that is subtly wrong only near the truncation boundary — which is precisely the range a suspicious cast should have been checked against before being silenced. Treat every new cast added purely to quiet a warning as a code-review flag in its own right, not a resolution.

**Treating a clean sanitizer run as proof of no undefined behaviour.** ASan and UBSan report defects in code that *actually executed* during the run — they are dynamic tools, not static ones, and a code path the test suite never reaches is a code path the sanitizer never watched. A "0 issues found" result from a suite that only covers the happy path is evidence about the happy path, not about the error-handling branches, the boundary conditions, or the code the suite forgot to call at all. Pair sanitizer runs with a coverage report (most host toolchains support `--coverage`/`gcov` on the same build) and read the two together — a clean sanitizer run over 40% branch coverage is a much weaker claim than the same clean run over 90%, and the number by itself does not tell you which one you have.
:::

## Integrating into CI without drowning in noise

The failure mode that kills static analysis adoption is not a tool being wrong — it is a tool being *right about too much at once*. Turning on `-Wconversion -Werror` or `cppcheck --enable=all` against an established codebase for the first time routinely produces hundreds of findings in one run, and a team faced with that either spends a week fixing all of it (rare) or disables the check entirely (common, and worse than never having tried).

The practical rollout is incremental and asymmetric — strict on what is new, forgiving of what already exists:

- **Gate new and changed code, grandfather the rest.** A script that runs the analyzer only against files touched in a diff, or that compares today's finding count against a checked-in baseline and fails only on an *increase*, gets the benefit on every future change without demanding a mass cleanup up front.
- **Start with the highest-confidence check subset**, not the full set. `cppcheck`'s default checks before `--enable=all`, `clang-tidy`'s `bugprone-*` before its full catalogue, `-Wall -Wextra` before the wider flag list above. Expand once the current tier is clean and trusted, rather than accepting every category at once and needing to triage all of it simultaneously.
- **A suppression needs a reason attached, not a blanket disable.** `// NOLINT` or a `cppcheck` suppression with no comment is indistinguishable, six months later, from "nobody looked at this" — the annotation is what makes the difference visible in a code review.
- **Run the fast tools on every commit, the slow ones on a schedule.** Compiler warnings and `cppcheck` are fast enough for every push; a commercial whole-program analyzer or a full `clang-tidy` pass over a large codebase is often better run nightly or on a merge to the main branch, so the everyday inner-loop feedback stays fast.
:::note
`-Wall`, `-Wextra`, and every `cppcheck`/`clang-tidy` check in this page run identically well on host tooling and on `arm-none-eabi-gcc` — none of it is Cortex-M-specific. `-Wdouble-promotion`'s *relevance* is what changes: it is a minor style nit on a desktop with a hardware double-precision FPU and a real code-size and performance concern on a Cortex-M4F with a single-precision-only FPU, which is exactly the kind of part-specific reading a static-analysis finding needs before you decide how much it matters.
:::

## See also

- [Unit Testing Firmware](./unit-testing-firmware.md) — the host build target ASan and UBSan run against, and the dual-build structure that makes a host-side sanitizer finding a finding in code that also ships.
- [Mocking Hardware](./mocking-hardware.md) — the seam and the fakes whose logic is exactly what a host-side sanitizer build exercises.
- [HardFault Forensics](./hardfault-debugging.md) — what happens on the target when a null-dereference or misaligned-access defect that `-Wnull-dereference`/`-Wcast-align` could have caught statically ships anyway.
- [Simulation and Emulation](./simulation-and-emulation.md) — running the real cross-compiled binary under QEMU or Renode, a complementary check to static analysis for defects that only appear against a modelled target environment.

## References

- Free Software Foundation — [**GCC Warning Options**](https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html), consulted at **GCC 15.2.0**. The authoritative description of every flag in the recommended set above, including the `-Wdouble-promotion` example of an implicit `float`-to-`double` promotion and the note that `-Wall` alone omits several checks `-Wextra` supplies (documentation checked 2026-08-27).
- Cppcheck team — [**Cppcheck manual**](https://github.com/cppcheck-opensource/cppcheck/blob/main/man/manual.md) and [**addons README**](https://github.com/cppcheck-opensource/cppcheck/blob/main/addons/README.md). `--enable=all`, `--inconclusive`, `--error-exitcode`, the suppressions-file format, and the `misra.py` addon's rule-number-only output and `--rule-texts` option (documentation checked 2026-08-27).
- LLVM Project — [**Clang-Tidy**](https://clang.llvm.org/extra/clang-tidy/) and [**Clang Tools overview**](https://clang.llvm.org/docs/ClangTools.html). The check-family naming convention (`bugprone-*`, `cert-*`, `modernize-*`), the `.clang-tidy` configuration format, and the requirement for a `compile_commands.json` compilation database (documentation checked 2026-08-27).
- LLVM Project — [**AddressSanitizer**](https://clang.llvm.org/docs/AddressSanitizer.html), [**LeakSanitizer**](https://clang.llvm.org/docs/LeakSanitizer.html) and [**UndefinedBehaviorSanitizer**](https://clang.llvm.org/docs/UsersManual.html#controlling-code-generation) documentation. The `-fsanitize=address`/`-fsanitize=undefined` flags, the redzone and interceptor mechanism that requires a hosted OS underneath the instrumented binary, and `-fno-omit-frame-pointer` for usable stack traces (documentation checked 2026-08-27).
