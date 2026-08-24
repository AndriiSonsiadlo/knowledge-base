---
id: build-systems-and-vendor-tools
title: Build Systems and Vendor Tooling
sidebar_label: Build Systems and Vendor Tooling
sidebar_position: 9
tags: [embedded, toolchain, build, cmake, platformio, stm32cubemx, zephyr, west]
---

# Build Systems and Vendor Tooling

Choosing a build system for firmware feels like a taste question and is not. The real question underneath it is **who owns the generated code**, and it has consequences that outlive the project: whether a colleague can build your firmware without installing an IDE, whether CI can build it at all, and whether the day you need to change a pin assignment costs ten minutes or a merge conflict across forty files you did not write.

The mental model: every option on this page sits somewhere on a line between two extremes. At one end, **you write everything** — a Makefile or `CMakeLists.txt` that names each source file, each flag, each linker option. Maximum effort up front, complete understanding, nothing surprises you at 3 a.m. At the other end, **a generator writes most of it** — CubeMX emits clock setup and peripheral init from a GUI, PlatformIO resolves a board name into a toolchain and a framework, `west` assembles a Zephyr tree from manifests. Minimum effort up front, and a maintenance relationship you have entered into whether you noticed or not.

Neither end is wrong. The mistake is not knowing which end you are at.

:::info[Prerequisites]
[Cross-Compilation](./cross-compilation.md) covers the toolchain every one of these drives, and [CMake for Embedded](./cmake-for-embedded.md) is the hand-written CMake option in full. General build-system material lives in [Build Systems: CMake](../../programming/cpp/01-toolchain-and-build/build-systems-cmake.md) and [Makefiles](../../programming/cpp/01-toolchain-and-build/makefiles.md).
:::

## The five options, compared

| | **Make** | **CMake** | **PlatformIO** | **STM32CubeIDE / CubeMX** | **Zephyr `west`** |
|---|---|---|---|---|---|
| **What it is** | A build tool you write rules for | A build-system generator | A package manager + build wrapper over SCons | A vendor IDE plus a code generator | A meta-tool over CMake + Kconfig + device tree |
| **Who writes the build** | You, entirely | You, entirely | PlatformIO, from `platformio.ini` | CubeIDE, from the `.ioc` file | Zephyr, from manifests and Kconfig |
| **Generates C source?** | No | No | No (frameworks are pre-written) | **Yes** — clock, pin and peripheral init | Only glue; drivers are Zephyr's |
| **Headless / CI build** | Trivial | Trivial | Trivial (`pio run`) | Possible but awkward; needs the IDE or exported makefiles | Trivial (`west build`) |
| **Editor lock-in** | None | None | VS Code favoured, CLI works standalone | Strong — Eclipse-based IDE | None |
| **Multi-target / multi-board** | Manual | Good | Good — one `[env:]` per board | Poor — one `.ioc` per project | Excellent, it is the design centre |
| **Dependency management** | None | FetchContent / find_package | Built-in library registry | None | Manifest-driven (`west update`) |
| **Time to first blink** | Hours | ~1 hour | Minutes | Minutes | ~1 hour, mostly install |
| **Understand every byte?** | Yes | Yes | No | Partly — you can read it, it is a lot | No, and that is the point |
| **Best when** | Tiny project, or you want the education | Production firmware, C/C++, your own drivers | Hobby, prototyping, Arduino-adjacent, many boards | Exploring an STM32 peripheral, or committed to ST's HAL | Networking, multiple SoC vendors, an RTOS anyway |

A short version of the recommendation, since the table hedges: for a **production C or C++ firmware you intend to own**, hand-written CMake. For **learning what a build actually does**, a Makefile once, then never again. For **exploring an unfamiliar STM32 peripheral**, CubeMX — and read what it emits. For **anything that needs a network stack, Bluetooth, or a second silicon vendor next year**, Zephyr, because you will otherwise write a worse version of it.

## Make

`make` is the substrate everything else eventually produces. Writing one Makefile by hand is worth doing exactly once, because after that every "why did it rebuild" and "why did it not rebuild" question has an answer you can reason about.

```makefile title="Makefile (abridged)"
TARGET   = blink
MCU      = -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard
CFLAGS   = $(MCU) -Os -Wall -ffunction-sections -fdata-sections -g3 -MMD -MP
LDFLAGS  = $(MCU) -T stm32f411re.ld --specs=nano.specs --specs=nosys.specs \
           -Wl,--gc-sections -Wl,-Map=$(TARGET).map,--cref -Wl,--print-memory-usage

OBJS = main.o startup.o

$(TARGET).elf: $(OBJS)
	arm-none-eabi-gcc $(LDFLAGS) $^ -o $@
	arm-none-eabi-size $@

%.o: %.c
	arm-none-eabi-gcc $(CFLAGS) -c $< -o $@

-include $(OBJS:.o=.d)
```

`$(MCU)` appearing in both `CFLAGS` and `LDFLAGS` is the whole discipline from [Cross-Compilation](./cross-compilation.md) expressed in one variable. `-MMD -MP` with the `-include` at the bottom is the header-dependency trick that makes `make` correct rather than merely fast — without it, editing a header rebuilds nothing and you debug a stale object file.

Where hand-written Make stops scaling: no configure step, no dependency fetching, no multi-configuration builds, and recursive Make across directories is a well-documented way to get subtly wrong incremental builds. Fifty files is comfortable. Five hundred is not.

## CMake

The default answer for firmware you own. [CMake for Embedded](./cmake-for-embedded.md) is the whole story — toolchain file, `CMAKE_TRY_COMPILE_TARGET_TYPE`, linker script wiring, a `flash` target. Two properties earn it the default slot:

- **It is what the rest of the C++ world uses**, so IDE integration, `compile_commands.json` for `clangd`, `ctest`, sanitizer builds of your platform-independent code on the host, and every static analyser work without special arrangements.
- **Zephyr, ESP-IDF, the Raspberry Pi Pico SDK and nRF Connect are all CMake underneath.** Learning it once transfers to every vendor ecosystem that matters.

## PlatformIO

A dependency manager and build wrapper, configured by one small INI file, that resolves a board name into a toolchain, a framework and an upload protocol — and downloads all three.

```ini title="platformio.ini"
[env:nucleo_f411re]
platform      = ststm32
board         = nucleo_f411re
framework     = stm32cube        ; or arduino, or omit for bare metal
upload_protocol = stlink
build_flags   = -Os -Wall
monitor_speed = 115200
```

`pio run -t upload` compiles and flashes. There is no toolchain to install, and adding a second board is four more lines. For prototyping, for teaching, and for anything where the board might change, that is a genuinely large saving.

The costs are real too: the build is opinionated and pushing back on it means learning PlatformIO's own extension mechanism rather than the underlying build system; toolchain versions are pinned by PlatformIO's platform packages rather than by you, which is a version-pinning question ([Choosing a Toolchain](./toolchains-and-compilers.md)) with someone else's hand on it; and the framework abstraction that makes it fast is also a layer between you and the register you are trying to debug.

## STM32CubeMX and CubeIDE

CubeMX is the interesting one, because it is not a build system — it is a **code generator** that happens to ship inside an IDE. You configure pins, the clock tree and peripherals in a GUI, and it emits C: `SystemClock_Config()`, `MX_GPIO_Init()`, `MX_USART2_UART_Init()`, a linker script, a startup file, and the HAL sources to support them.

What that buys is real. The clock tree in particular — where the PLL multiplier and divider arithmetic is fiddly and the constraints come from several tables at once ([Clocks and Oscillators](../01-hardware-foundations/clocks-and-oscillators.md) covers the hardware side) — is a place where a GUI that validates your dividers against the datasheet limits prevents a class of bug. Pin-conflict detection across alternate functions is the same story. For "which timer can drive this pin", CubeMX answers in seconds what the datasheet answers in twenty minutes.

The maintenance debt is equally real, and it has a specific shape. Regeneration is not a merge — CubeMX rewrites its files, and the only content it preserves is what sits between its markers:

```c
/* USER CODE BEGIN 2 */
  led_init();          /* this survives regeneration */
/* USER CODE END 2 */

  MX_GPIO_Init();      /* this is regenerated every time */

  /* anything you write out here is gone */
```

Three rules keep this manageable, and they are the difference between CubeMX being a tool and being a trap:

1. **Commit the `.ioc` file, and treat it as the source of truth.** It is the input; the generated C is output. A pin change is an `.ioc` change plus a regeneration, never a hand-edit of `MX_GPIO_Init()`.
2. **Keep your code out of generated files entirely.** Not in `USER CODE` blocks either, beyond one-line calls into your own modules. Your application lives in `src/` files CubeMX has never heard of; the generated `main.c` calls into it and does nothing else.
3. **Commit the generated code anyway.** It is a build input, and a colleague — or CI — must be able to build without running a GUI. The alternative, regenerating in CI, means pinning a CubeMX version and a firmware-package version and driving a Java application headlessly.

CubeMX can also emit a Makefile or a CMake project instead of a CubeIDE project, which decouples the generator from the IDE and is almost always the right selection. Take it.

## Zephyr and `west`

`west` is a meta-tool: a manifest-driven repository manager plus a thin front end over Zephyr's CMake, Kconfig and device tree.

```bash
west build -b nucleo_f411re samples/basic/blinky
west flash
```

That single `-b` flag is doing an enormous amount. The board name selects a device tree that describes the SoC and the board's peripherals, Kconfig resolves the feature set, and CMake builds the tree that results. Change `-b` to a different vendor's board and the same application source builds — which is the entire proposition, and it is not available anywhere else on this page.

The price is a much larger conceptual surface: device tree, Kconfig, the Zephyr driver model and the manifest system are four things to learn before the first non-trivial change, and `west update` pulls a multi-gigabyte tree. For a blink, that is absurd. For a product that needs BLE, a filesystem, an IP stack and a supported update path across two SoC families, writing all of that yourself is more absurd. Device tree, Kconfig and the RTOS itself are subjects for later sections.

## What generated code costs, in general

The pattern generalises past CubeMX. A generator is a relationship with three failure modes worth naming before you enter it:

- **Regeneration overwrites.** Anything not inside the sanctioned markers is lost, silently, at the moment you change a pin.
- **Diffs become unreadable.** A one-pin change produces a 400-line diff across generated files. Real review stops happening, and a genuine defect hides in the noise. Regenerating in its own commit, separate from your changes, is the cheap mitigation.
- **The abstraction leaks exactly when you need it not to.** Generated init code is written for the general case. The moment your requirement is unusual — a peripheral in a mode the GUI does not expose, a clock configuration the validator rejects — you are reading the generated code anyway, and it was not written to be read.

None of that is an argument against generators. It is an argument for keeping the boundary between generated and owned code sharp enough that you can always tell which side you are on.

:::warning[Regenerating from CubeMX silently deletes the code you wrote in the wrong place]
The most common way to lose an afternoon's work on an STM32 project, and it happens without an error, a prompt, or a diff you will notice in time.

You add a peripheral in CubeMX and click "Generate Code". CubeMX rewrites `main.c`, `stm32f4xx_hal_msp.c`, `stm32f4xx_it.c` and the peripheral init files. Everything inside `/* USER CODE BEGIN X */ … /* USER CODE END X */` is carried across. **Everything else you added to those files is gone.** No warning, because from CubeMX's point of view nothing was lost — those files are its output, and it just produced a new version of its output.

The three ways it bites hardest:

- **An interrupt handler written directly into `stm32f4xx_it.c`** outside the user blocks. It disappears, and the symptom is not a build error — the weak default handler in the startup file takes over, so the firmware links and runs and simply stops responding to that interrupt. Tracking that back to a regeneration you did an hour ago is genuinely hard.
- **A hand-edited linker script.** Add a `.RamFunc` section or move the heap, then regenerate: CubeMX rewrites the `.ld` too, and you are back to the default layout. `--print-memory-usage` output that changed for no reason is the tell.
- **A hand-tuned `SystemClock_Config()`.** Regenerated from the GUI's model of the clock tree, discarding whatever you changed by hand.

Three defences, in order of how much they help:

1. **Commit before you regenerate. Every time, no exceptions.** Then the regeneration is one reviewable diff and `git checkout -- <file>` is the undo. This alone converts the problem from data loss to an inconvenience.
2. **Keep your code in files CubeMX does not generate.** A handler becomes one line inside `USER CODE` that calls `my_uart_isr()` in your own file. Then a regeneration cannot destroy anything but a call.
3. **Read the diff after regenerating,** especially the linker script and `SystemClock_Config`. CubeMX changes things you did not ask it to change when you update the firmware package version.

The same discipline applies to any generator — protobuf stubs, SVD-derived headers, `west`'s generated device-tree headers. The rule is the file-level one: **a file is either generated or hand-written, never both.** CubeMX's `USER CODE` blocks are a well-intentioned attempt to make "both" work, and they are exactly the part that fails.
:::

## See also

- [CMake for Embedded](./cmake-for-embedded.md) — the hand-written CMake option in full, including the toolchain file.
- [Choosing a Toolchain](./toolchains-and-compilers.md) — the version-pinning question that PlatformIO and vendor tools answer on your behalf.
- [Cross-Compilation](./cross-compilation.md) — the flags every one of these build systems is ultimately passing.
- [Reading the Map File](./elf-map-files-and-size.md) — what to check after any of these produces a binary.
- [Flashing and Programming](./flashing-and-programming.md) — what `pio run -t upload`, `west flash` and the CubeIDE run button do underneath.

## References

- STMicroelectronics — [**UM1718**, *STM32CubeMX for STM32 configuration and initialization C code generation*](https://www.st.com/resource/en/user_manual/um1718-stm32cubemx-for-stm32-configuration-and-initialization-c-code-generation-stmicroelectronics.pdf). The authority on the generator: the `.ioc` project file, the clock-tree and pinout validators, the Makefile/CMake/IDE toolchain selection, and — the section that matters most here — the `USER CODE` marker contract and exactly what is preserved across a regeneration.
- STMicroelectronics — [**UM2609**, *STM32CubeIDE user guide*](https://www.st.com/resource/en/user_manual/um2609-stm32cubeide-user-guide-stmicroelectronics.pdf). The IDE around the generator: project structure, the embedded CubeMX perspective, and headless build invocation for CI.
- PlatformIO — [**PlatformIO documentation**](https://docs.platformio.org/). [`platformio.ini` configuration reference](https://docs.platformio.org/en/latest/projectconf/index.html) for the `[env:]` sections, `build_flags` and `upload_protocol` used above, and the [ST STM32 platform page](https://docs.platformio.org/en/latest/platforms/ststm32.html) for the `nucleo_f411re` board definition and its supported frameworks.
- Zephyr Project — [**Zephyr documentation**](https://docs.zephyrproject.org/latest/). [`west`](https://docs.zephyrproject.org/latest/develop/west/index.html) for the manifest and repository model, and the [build system overview](https://docs.zephyrproject.org/latest/build/cmake/index.html) for how `-b <board>` resolves through device tree and Kconfig into a CMake configuration.
- Kitware — [**CMake documentation**](https://cmake.org/cmake/help/latest/). The generator behind Zephyr, ESP-IDF and the Pico SDK as well as the hand-written option; see [CMake for Embedded](./cmake-for-embedded.md) for the embedded-specific parts.
- Free Software Foundation — [**GNU Make manual**](https://www.gnu.org/software/make/manual/make.html). Pattern rules, automatic variables and the `-include` of generated `.d` files that makes the header-dependency idiom above work.
