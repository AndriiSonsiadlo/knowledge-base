---
id: cmake-for-embedded
title: CMake for Embedded
sidebar_label: CMake for Embedded
sidebar_position: 8
tags: [embedded, toolchain, cmake, build, cross-compilation, stm32]
---

# CMake for Embedded

CMake's defaults encode one assumption so deeply that it is easy to miss: the machine running the build can also *run* what the build produces. That is what lets CMake test a compiler by compiling and linking a tiny program, what lets `find_package` look in `/usr/lib`, and what lets `check_c_source_runs` exist at all. Every one of those assumptions is false for a Cortex-M4 with 128 KB of RAM and no operating system.

The mental model: **a toolchain file is a set of corrections applied before CMake forms any of its opinions.** It is read first, before the compiler is probed, before `project()` runs, before anything is cached. Get it right and the rest of your `CMakeLists.txt` is ordinary CMake. Get it wrong and CMake fails during *configure*, before it has compiled a line of your code — which is exactly why the failure is so disorienting the first time.

This page is the embedded delta only. [What is CMake?](../../programming/cmake/00-intro/what-is-cmake.md), [CMakeLists Structure](../../programming/cmake/01-basics/cmakelists-structure.md) and [Target Properties](../../programming/cmake/02-targets/target-properties.md) own CMake itself — targets, visibility, variables, generator expressions — and none of that changes because the target is a microcontroller.

:::info[Prerequisites]
[Cross-Compilation](./cross-compilation.md) establishes the `arm-none-eabi` triple and the four target flags this page wires up. [The Linker Script](./the-linker-script.md) is the `stm32f411re.ld` referenced below, and [C Libraries for Embedded](./c-libraries-for-embedded.md) explains `--specs=nano.specs` and `--specs=nosys.specs`.
:::

## The failure everyone hits first

Write the toolchain file the obvious way — name the system, name the compiler — and configure the project:

```cmake title="arm-none-eabi.cmake (incomplete — this version fails)"
set(CMAKE_SYSTEM_NAME       Generic)
set(CMAKE_SYSTEM_PROCESSOR  arm)
set(CMAKE_C_COMPILER        arm-none-eabi-gcc)
set(CMAKE_CXX_COMPILER      arm-none-eabi-g++)
```

```text
$ cmake -S . -B build -DCMAKE_TOOLCHAIN_FILE=arm-none-eabi.cmake
-- The C compiler identification is GNU 14.2.1
-- Detecting C compiler ABI info - failed
-- Check for working C compiler: .../arm-none-eabi-gcc - broken
CMake Error at /usr/share/cmake-4.2/Modules/CMakeTestCCompiler.cmake:67 (message):
  The C compiler

    ".../bin/arm-none-eabi-gcc"

  is not able to compile a simple test program.

  It fails with the following output:
    ...
    ld: libc.a(libc_a-exit.o): in function `exit':
    exit.c:(.text.exit+0x28): undefined reference to `_exit'
    ld: libc.a(libc_a-closer.o): in function `_close_r':
    closer.c:(.text._close_r+0x18): undefined reference to `_close'
    ld: libc.a(libc_a-lseekr.o): in function `_lseek_r':
    lseekr.c:(.text._lseek_r+0x24): undefined reference to `_lseek'
    ld: libc.a(libc_a-readr.o): undefined reference to `_read'
    ld: libc.a(libc_a-writer.o): undefined reference to `_write'
    ld: libc.a(libc_a-sbrkr.o): undefined reference to `_sbrk'
    collect2: error: ld returned 1 exit status
```

Read the message carefully and it is telling the truth about the wrong thing. The compiler is not broken — it compiled `testCCompiler.c` fine. What failed is the *link*, because CMake's compiler check builds an **executable**, and linking an executable against newlib drags in `exit`, `_sbrk` and the `stdio` syscall stubs, none of which exist on a bare-metal target. There is no `_start`, no kernel, and no linker script telling `ld` where anything goes.

The instinct at this point is to start supplying the missing pieces to the test program — a linker script, `--specs=nosys.specs`, stub definitions. That works, and it is the wrong shape of fix: you end up maintaining a second, parallel link configuration whose only purpose is to satisfy a check.

## The fix: `CMAKE_TRY_COMPILE_TARGET_TYPE`

```cmake
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
```

One line. It tells CMake that every internal `try_compile` — the compiler check, the ABI detection, every `check_c_source_compiles` and `check_symbol_exists` a dependency might run — should build a **static library** instead of an executable. A static library is compiled and archived; it is never linked. No `_start`, no `_exit`, no syscall stubs, nothing to resolve.

The tell that it worked is a single word in the configure output:

```text
-- Detecting C compiler ABI info - done
-- Check for working C compiler: .../arm-none-eabi-gcc - skipped
-- Configuring done (3.1s)
```

`skipped`, not `broken`. CMake now knows better than to ask a question it cannot answer.

Two consequences worth understanding rather than just accepting:

- **Anything that needs to *run* a test program is now impossible**, and always was. `check_c_source_runs()` and `try_run()` cannot work when the target is a different computer that is not attached. If a dependency's CMake code calls them, it was never going to cross-compile without patching — this setting makes that fact surface early instead of after a confusing link error.
- **`check_c_source_compiles` and `check_symbol_exists` still work**, because compiling is genuinely all they need. Header and symbol probes remain available.

The alternative some projects use is `set(CMAKE_TRY_COMPILE_TARGET_TYPE OBJECT_LIBRARY)`, which is very slightly cheaper because it skips the `ar` step. `STATIC_LIBRARY` is the value in CMake's own cross-compiling documentation and the one every embedded example uses; take the well-trodden one.

## A complete toolchain file

```cmake title="cmake/arm-none-eabi.cmake"
# Toolchain file for bare-metal Arm Cortex-M with the Arm GNU Toolchain.
# Use:  cmake -S . -B build -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake

# "Generic" means: no operating system. This is what makes CMake stop
# assuming a host-like target, and it is what defines CMAKE_CROSSCOMPILING.
set(CMAKE_SYSTEM_NAME       Generic)
set(CMAKE_SYSTEM_PROCESSOR  arm)

# THE line. Without it the configure step fails; see above.
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

# Let the toolchain be overridden for a pinned or containerised install.
set(TOOLCHAIN_PREFIX arm-none-eabi- CACHE STRING "cross toolchain prefix")

set(CMAKE_C_COMPILER    ${TOOLCHAIN_PREFIX}gcc)
set(CMAKE_CXX_COMPILER  ${TOOLCHAIN_PREFIX}g++)
set(CMAKE_ASM_COMPILER  ${TOOLCHAIN_PREFIX}gcc)
set(CMAKE_OBJCOPY       ${TOOLCHAIN_PREFIX}objcopy CACHE FILEPATH "")
set(CMAKE_SIZE          ${TOOLCHAIN_PREFIX}size    CACHE FILEPATH "")

# The four flags from Cross-Compilation, set once so compile and link agree.
# _INIT variables seed the per-language flags before any cache entry exists.
set(MCU_FLAGS "-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard")
set(CMAKE_C_FLAGS_INIT   "${MCU_FLAGS}")
set(CMAKE_CXX_FLAGS_INIT "${MCU_FLAGS}")
set(CMAKE_ASM_FLAGS_INIT "${MCU_FLAGS}")

# Never search the host filesystem for target libraries or headers.
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM BOTH)   # host tools: openocd, python
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

# Firmware convention: the linked output is an ELF.
set(CMAKE_EXECUTABLE_SUFFIX     ".elf")
set(CMAKE_EXECUTABLE_SUFFIX_C   ".elf")
set(CMAKE_EXECUTABLE_SUFFIX_CXX ".elf")
```

The three parts that do real work, beyond `CMAKE_TRY_COMPILE_TARGET_TYPE`:

**`CMAKE_SYSTEM_NAME Generic`** is CMake's name for "a target with no operating system". Setting *any* `CMAKE_SYSTEM_NAME` in a toolchain file is what sets `CMAKE_CROSSCOMPILING` to true, and `Generic` additionally suppresses the platform modules that would otherwise assume a `Linux`- or `Darwin`-shaped world.

**The `_INIT` flag variables** rather than plain `CMAKE_C_FLAGS`. `CMAKE_<LANG>_FLAGS_INIT` seeds the cache entry the first time CMake configures and then leaves the user's cache value alone on subsequent runs. Assigning `CMAKE_C_FLAGS` directly in a toolchain file re-applies on every configure and duplicates the flags. This matters because these four flags are exactly the ones that must be identical everywhere — [Cross-Compilation](./cross-compilation.md) explains what happens when they drift.

**`CMAKE_FIND_ROOT_PATH_MODE_*`** stops `find_library` and `find_path` from finding your *host's* `libz` and offering it to a Cortex-M4. `PROGRAM BOTH` is deliberate and is the one exception: `find_program(OPENOCD openocd)` should find the host's OpenOCD, because that runs on your laptop.

## The `CMakeLists.txt`

```cmake title="CMakeLists.txt"
cmake_minimum_required(VERSION 3.21)
project(blink LANGUAGES C ASM)

set(LINKER_SCRIPT ${CMAKE_SOURCE_DIR}/stm32f411re.ld)

add_executable(blink
    src/main.c
    src/startup.c
)

target_compile_options(blink PRIVATE
    -Wall -Wextra
    -ffunction-sections -fdata-sections
    $<$<CONFIG:Debug>:-Og -g3>
    $<$<CONFIG:Release>:-Os -g>
)

target_link_options(blink PRIVATE
    -T${LINKER_SCRIPT}
    --specs=nano.specs          # newlib-nano
    --specs=nosys.specs         # stub syscalls; supply your own to replace
    -Wl,--gc-sections
    -Wl,-Map=$<TARGET_FILE_DIR:blink>/blink.map,--cref
    -Wl,--print-memory-usage
)

# Make an edit to the linker script actually trigger a relink. See the warning.
set_target_properties(blink PROPERTIES LINK_DEPENDS ${LINKER_SCRIPT})

# Report flash and RAM, and produce the .bin / .hex a programmer wants.
add_custom_command(TARGET blink POST_BUILD
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE:blink>
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:blink> $<TARGET_FILE_DIR:blink>/blink.bin
    COMMAND ${CMAKE_OBJCOPY} -O ihex   $<TARGET_FILE:blink> $<TARGET_FILE_DIR:blink>/blink.hex
    COMMENT "Size, .bin and .hex"
)
```

Nothing here is embedded-specific CMake — it is ordinary targets, generator expressions and [custom commands](../../programming/cmake/05-advanced/custom-commands.md). What is embedded-specific is *which* options you pass, and every one of them is explained on another page in this folder: the linker script, `--gc-sections` and the map file in [Reading the Map File](./elf-map-files-and-size.md), the specs files in [C Libraries for Embedded](./c-libraries-for-embedded.md), and `-Os` versus `-Og` in [Optimization for Size and Speed](./optimization-flags.md).

`--print-memory-usage` on the link line is the highest-value line in the file. Every build prints:

```text
Memory region         Used Size  Region Size  %age Used
           FLASH:        4500 B       512 KB      0.86%
             RAM:        1992 B       128 KB      1.52%
```

## A `flash` target

```cmake
find_program(OPENOCD_EXECUTABLE openocd)

if(OPENOCD_EXECUTABLE)
    add_custom_target(flash
        COMMAND ${OPENOCD_EXECUTABLE}
                -f interface/stlink.cfg -f target/stm32f4x.cfg
                -c "program $<TARGET_FILE:blink> verify reset exit"
        DEPENDS blink
        USES_TERMINAL
        COMMENT "Flashing over ST-LINK"
    )
endif()
```

`cmake --build build --target flash`. Three details make this behave: `DEPENDS blink` means flashing rebuilds first, so you cannot flash a stale image; `USES_TERMINAL` gives OpenOCD the console directly so its progress and errors are not swallowed by the generator; and guarding on `find_program` means a machine without OpenOCD still configures, it just has no `flash` target. [Flashing and Programming](./flashing-and-programming.md) covers what that OpenOCD command line is doing.

## Presets, so nobody types the toolchain flag

```json title="CMakePresets.json"
{
  "version": 3,
  "configurePresets": [
    {
      "name": "stm32f411re",
      "generator": "Ninja",
      "binaryDir": "${sourceDir}/build/${presetName}",
      "toolchainFile": "${sourceDir}/cmake/arm-none-eabi.cmake",
      "cacheVariables": { "CMAKE_BUILD_TYPE": "Release" }
    }
  ]
}
```

`cmake --preset stm32f411re` then `cmake --build build/stm32f411re`. This is worth adding on day one: the toolchain file is only correct if it is *used*, and a forgotten `-DCMAKE_TOOLCHAIN_FILE` produces a host build that compiles happily and is completely useless. [CMake Presets](../../programming/cmake/01-basics/presets.md) covers the format.

## What each piece is for

| Setting | Where it goes | What breaks without it |
|---|---|---|
| `CMAKE_SYSTEM_NAME Generic` | Toolchain file | `CMAKE_CROSSCOMPILING` stays false; host platform modules apply. |
| `CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY` | Toolchain file | **Configure fails**: "compiler is not able to compile a simple test program". |
| `CMAKE_<LANG>_FLAGS_INIT` | Toolchain file | Wrong multilib, or flags duplicated on every re-configure. |
| `CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY` | Toolchain file | `find_library` offers you host x86 libraries. |
| `-T<script>` in `target_link_options` | `CMakeLists.txt` | Default layout; the image does not match the chip's memory map. |
| `LINK_DEPENDS` | `CMakeLists.txt` | Linker-script edits silently do not relink. See the warning. |
| `--gc-sections` + `-ffunction-sections` | Both | Tens of KB of unreferenced library code stays in the image. |
| `objcopy` post-build | `CMakeLists.txt` | No `.bin`/`.hex` for tools that will not take an ELF. |
| `CMakePresets.json` | Repo root | Someone configures without the toolchain file and builds for the host. |

:::warning[You edit the linker script, rebuild, and CMake links the old one anyway]
This one is quiet, and it wastes the afternoon *after* the afternoon you spent getting the linker script right.

`-T${LINKER_SCRIPT}` inside `target_link_options()` is, to CMake, an opaque string on the link command line. CMake does not parse link flags looking for filenames, so it never learns that `stm32f411re.ld` is an input. The generated build system has no dependency edge from the ELF to the script.

Measured on the project above, without `LINK_DEPENDS`:

```text
$ touch stm32f411re.ld
$ cmake --build build
[100%] Built target blink.elf      # no link step ran
```

The linker never re-ran. You changed `LENGTH` on a RAM region, or moved a section, or fixed the very bug you were chasing — and then flashed the previous binary and concluded the change had no effect. The reasoning that follows from that false observation can burn hours, because every subsequent experiment is also invalidated by the same stale link.

The fix is one line, and the same `touch` afterwards proves it:

```cmake
set_target_properties(blink PROPERTIES LINK_DEPENDS ${LINKER_SCRIPT})
```

```text
$ touch stm32f411re.ld
$ cmake --build build
[ 50%] Linking C executable blink.elf
[100%] Built target blink.elf      # it relinked
```

Two relatives of the same problem, both with the same shape — a real input the build system cannot see:

- **`LINK_DEPENDS` is per-target.** A project with a bootloader and an application, each with its own script, needs it on both.
- **Generated headers and `.ld` fragments.** If the linker script is produced by `configure_file()` or an `add_custom_command`, depend on the *generated* path, not the template.

The habit that catches all of them: when a change to a file appears to have no effect, check whether the build system knows the file exists **before** you doubt the change.
:::

## See also

- [Cross-Compilation](./cross-compilation.md) — where `-mcpu`, `-mthumb`, `-mfpu` and `-mfloat-abi` come from and why they must match everywhere.
- [The Linker Script](./the-linker-script.md) — the `stm32f411re.ld` that `-T` and `LINK_DEPENDS` refer to.
- [Reading the Map File](./elf-map-files-and-size.md) — what to do with the `blink.map` and `--print-memory-usage` output this build produces.
- [What is CMake?](../../programming/cmake/00-intro/what-is-cmake.md) — CMake itself: the model, targets, and everything this page assumes.
- [Custom Commands and Targets](../../programming/cmake/05-advanced/custom-commands.md) — the general form of the `objcopy` post-build step and the `flash` target.
- [Build Systems and Vendor Tooling](./build-systems-and-vendor-tools.md) — when CMake is the right answer and when PlatformIO or `west` is.

## References

- Kitware — [**CMake documentation: Cross Compiling**](https://cmake.org/cmake/help/latest/manual/cmake-toolchains.7.html#cross-compiling). The normative guide to toolchain files, including the [cross-compiling for a bare-metal target](https://cmake.org/cmake/help/latest/manual/cmake-toolchains.7.html#cross-compiling-for-a-microcontroller) section that specifies `CMAKE_SYSTEM_NAME Generic` and gives `CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY` as the documented answer to the `try_compile` link failure.
- Kitware — CMake variable reference: [`CMAKE_TOOLCHAIN_FILE`](https://cmake.org/cmake/help/latest/variable/CMAKE_TOOLCHAIN_FILE.html), [`CMAKE_TRY_COMPILE_TARGET_TYPE`](https://cmake.org/cmake/help/latest/variable/CMAKE_TRY_COMPILE_TARGET_TYPE.html), [`CMAKE_<LANG>_FLAGS_INIT`](https://cmake.org/cmake/help/latest/variable/CMAKE_LANG_FLAGS_INIT.html), [`CMAKE_FIND_ROOT_PATH_MODE_LIBRARY`](https://cmake.org/cmake/help/latest/variable/CMAKE_FIND_ROOT_PATH_MODE_LIBRARY.html) and [`CMAKE_EXECUTABLE_SUFFIX`](https://cmake.org/cmake/help/latest/variable/CMAKE_EXECUTABLE_SUFFIX.html), plus the [`LINK_DEPENDS`](https://cmake.org/cmake/help/latest/prop_tgt/LINK_DEPENDS.html) target property and [`cmake-presets(7)`](https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html).
- Arm — [**Arm GNU Toolchain**](https://developer.arm.com/Tools%20and%20Software/GNU%20Toolchain), release **14.2.Rel1**. The compiler the configure output above was produced with; CMake 4.2.3 was the CMake. Both versions belong in your pin — see [Choosing a Toolchain](./toolchains-and-compilers.md).
- Free Software Foundation — [**GNU `ld` manual, "Command-line Options"**](https://sourceware.org/binutils/docs/ld/Options.html). `-T`, `--gc-sections`, `-Map`, `--cref` and `--print-memory-usage` — every linker option passed through `target_link_options` above.
- Kitware — [**`add_custom_command`**](https://cmake.org/cmake/help/latest/command/add_custom_command.html) and [**`add_custom_target`**](https://cmake.org/cmake/help/latest/command/add_custom_target.html), including `USES_TERMINAL` and the `POST_BUILD` form used for the size report and `objcopy` conversion.
