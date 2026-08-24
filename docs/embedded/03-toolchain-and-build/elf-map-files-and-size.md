---
id: elf-map-files-and-size
title: Reading the Map File
sidebar_label: Reading the Map File
sidebar_position: 7
tags: [embedded, toolchain, binutils, map-file, elf, code-size, stm32]
---

# Reading the Map File

Every firmware project reaches the same afternoon. The build that fitted last week does not fit this week, or it fits but the RAM figure has doubled, and nobody changed anything that should have cost 12 KB. The instinct is to start deleting features. The correct move is to ask the toolchain, which has known the answer the whole time and wrote it down.

The mental model: **the ELF file is the truth, and the map file is the linker's own account of how it got there.** The ELF says what the final image contains — sections, addresses, symbols, sizes. The map file says *why*: which object pulled in which archive member, which input section landed at which address, what was discarded and what survived. Between them there is no such thing as "mystery flash usage". There is only flash usage you have not looked up yet.

Four tools read the ELF and one flag produces the map. None of them need the target, a debugger, or a running program.

:::info[Prerequisites]
[Memory Sections and VMA vs LMA](./memory-sections.md) explains what `.text`, `.data` and `.bss` mean and why `.data` has two addresses — this page assumes those. [The Linker Script](./the-linker-script.md) is the script every listing below is produced against. [Object Files and Symbols](../../programming/cpp/01-toolchain-and-build/object-files-and-symbols.md) owns the general ELF and symbol-table model.
:::

## The measurements on this page are real

Everything quoted below was produced from the NUCLEO-F411RE blink firmware — the `stm32f411re.ld` from [The Linker Script](./the-linker-script.md), the startup file from [Startup Code: Reset to `main`](./startup-code.md), and a `main()` that enables `GPIOA` and toggles `PA5` — built with **Arm GNU Toolchain 14.2.Rel1** (GCC 14.2.1, binutils 2.43.1). The flags:

```bash
TARGET="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
arm-none-eabi-gcc $TARGET -Os -Wall -ffunction-sections -fdata-sections -g3 -c main.c -o main.o
arm-none-eabi-gcc $TARGET -Os -T stm32f411re.ld \
    --specs=nano.specs --specs=nosys.specs \
    -Wl,--gc-sections,-Map=blink.map,--cref \
    startup.o main.o -o blink.elf
```

`-Wl,-Map=blink.map` is the whole cost of having a map file. Add it to every project on the day you create the project, not on the afternoon you need it.

## `size`: the number you watch every build

```text
$ arm-none-eabi-size blink.elf
   text	   data	    bss	    dec	    hex	filename
    440	      8	   1568	   2016	    7e0	blink.elf
```

That is the entire blink: 440 bytes of code and constants, 8 bytes of initialised data, and 1568 bytes of RAM that starts at zero. On a part with 512 KB of flash and 128 KB of SRAM you are using well under one percent of each.

The three columns are **ELF section classes, not your linker script's memory regions**, and the difference matters. GNU `size` in its default Berkeley format sorts every allocated section by its flags: read-only or executable sections become `text`, writable sections with file content become `data`, and allocated sections with no file content (`SHT_NOBITS`) become `bss`. Where *your* script sent them does not enter into it.

`-A` prints the per-section breakdown that shows what the totals are actually made of:

```text
$ arm-none-eabi-size -A blink.elf
blink.elf  :
section              size        addr
.isr_vector            64   134217728     <- 0x08000000, base of flash
.text                 376   134217792
.rodata                 0   134218168
.init_array             4   134218168     <- writable + has content => "data"
.fini_array             4   134218172        ...but it lives in FLASH
.data                   0   536870912     <- 0x20000000, base of RAM, and empty
.bss                   28   536870912
._user_heap_stack    1540   536870940     <- the reservation, counted as "bss"
.ARM.attributes        48           0
.debug_info           636           0     <- not loaded, not in the totals
...
Total               25416                 <- includes debug info; ignore this
```

Two surprises fall out immediately, and both are the general case rather than quirks of this build:

- **The 8 bytes of `data` are not `.data`.** `.data` is empty. The 8 bytes are `.init_array` and `.fini_array`, which carry the writable ELF flag and therefore classify as `data`, while our linker script places them in flash. The Berkeley columns answer "what kind of section is this", not "which chip does it consume".
- **1540 of the 1568 `bss` bytes are the heap and stack reservation.** `._user_heap_stack` from the linker script is `NOLOAD`, so it classifies as `bss`. Real zero-initialised globals account for 28 bytes. If you have ever wondered why an empty firmware "uses" 1.5 KB of RAM, this is why.

:::note
`Total` at the bottom of `size -A` includes `.debug_*`, `.comment` and `.ARM.attributes` — 25416 bytes here against a 448-byte flash image, because `-g3` was on. Debug sections are in the ELF and are never in the device. `objcopy -O binary` drops them, which is why the `.bin` is always dramatically smaller than the `.elf` and why comparing the two file sizes tells you nothing.
:::

## `--print-memory-usage`: the number you actually want

The linker knows your `MEMORY` regions. Ask it, and it answers in the terms the datasheet uses:

```text
$ arm-none-eabi-gcc ... -Wl,--print-memory-usage ...
Memory region         Used Size  Region Size  %age Used
           FLASH:        4500 B       512 KB      0.86%
             RAM:        1992 B       128 KB      1.52%
```

(that run is the `printf` variant from the next section, not the 440-byte baseline)

This is the reporting to wire into your build, because it is the only one that maps onto the constraint you care about, it comes free with the link, and — unlike `size` — it cannot be misread. Pair it with `-Wl,--no-warn-rwx-segments` if the RWX-segment warning from recent binutils bothers you; it is expected on a Cortex-M, whose RAM is legitimately executable.

## The accidental `printf`, measured

The classic finding. The same blink, with one `printf("tick %lu\r\n", ticks++)` added to the loop:

| Build | `text` | `data` | `bss` | Flash image |
|---|---|---|---|---|
| Blink, no `printf` | 440 | 8 | 1568 | **448 B** |
| `+ printf`, newlib-nano, `--gc-sections` | 4400 | 100 | 1900 | **4500 B** |
| `+ printf`, newlib-nano, **no** `--gc-sections` | 6112 | 104 | 1904 | **6216 B** |
| `+ printf`, **full newlib**, `--gc-sections` | 32580 | 1760 | 2356 | **34340 B** |

One call, one format specifier. Against newlib-nano it costs **just under 4 KB of flash** — nine times the entire rest of the firmware. Against full newlib it costs **32 KB**, and RAM goes up too, because `stdio` brings a `FILE` structure and a buffer with it. [C Libraries for Embedded](./c-libraries-for-embedded.md) covers why the two libraries differ by that much and how to choose.

The `--gc-sections` row is the other half of the story: with `-ffunction-sections -fdata-sections` on the compile side, section garbage collection removes 1712 bytes here, 28% of the image. On a firmware that links more of a C library it routinely removes tens of kilobytes.

## Finding the 12 KB: `nm`

`nm` sorted by size is the fastest instrument in the box. `--print-size` adds the size column, `--size-sort` orders by it, `--radix=d` gives decimal so you can do arithmetic in your head:

```text
$ arm-none-eabi-nm --print-size --size-sort --radix=d blink.elf | tail -8
134219052 00000148 T _free_r
134221452 00000168 T __swsetup_r
134220192 00000218 T _printf_common
134219268 00000256 T _malloc_r
134220988 00000260 T __sflush_r
536871032 00000312 B __sf
134219632 00000560 T _vfiprintf_r
134220412 00000576 T _printf_i
```

Read it bottom-up: the largest things in this firmware are `_printf_i` (576 bytes), `_vfiprintf_r` (560), and `__sf` (312 bytes of **`B`, meaning `.bss`** — that is the `FILE` array, RAM, not flash). `main` is 132 bytes and does not make the list. The `printf` machinery is not a suspect; it is the program.

The type letters are the ones from the `nm` manual and the useful subset is small: `T` text (flash), `D` initialised data, `B` `.bss` (RAM), `R` read-only data, `t`/`d`/`b` the same but file-local, `U` undefined — a reference this object needs from somewhere else.

Two companions:

```bash
arm-none-eabi-objdump -h blink.elf     # section headers with VMA *and* LMA
arm-none-eabi-objdump -d blink.elf     # disassembly, to see what a function became
arm-none-eabi-readelf -A blink.elf     # build attributes: the CPU and float ABI actually used
```

`objdump -h` is the direct check on the VMA/LMA split from [Memory Sections and VMA vs LMA](./memory-sections.md); `readelf -A` is the hard-float verification from [Cross-Compilation](./cross-compilation.md).

## The map file, section by section

`-Wl,-Map=blink.map,--cref` produces four parts, in this order. Paths below are shortened for width; a real map file spells out every toolchain path in full, which is why the file is 1200 lines for a firmware this small.

**1. Archive members included, and who asked for them.** The most useful part of the file and the first thing in it. Each pair of lines is "this archive member was linked" / "because this object referenced this symbol":

```text
Archive member included to satisfy reference by file (symbol)

<toolchain>/libc_nano.a(libc_a-printf.o)
                              build/main.o (printf)
<toolchain>/libc_nano.a(libc_a-findfp.o)
                              <toolchain>/libc_nano.a(libc_a-exit.o) (__stdio_exit_handler)
<toolchain>/libc_nano.a(libc_a-impure.o)
                              <toolchain>/libc_nano.a(libc_a-printf.o) (_impure_ptr)
```

That is the 4 KB, traced to its cause in three lines: your `main.o` referenced `printf`, which dragged in `libc_a-printf.o`, which dragged in `_impure_ptr`, and so on down the chain. When something you did not ask for is in your binary, **this is where you look first** — it names the object file that asked for it.

**2. Discarded input sections.** Everything `--gc-sections` deleted. Long and rarely interesting, except when the thing you are hunting for is *missing* — a vector table that vanished for want of a `KEEP` shows up here, which is the confirmation for the failure described in [The Linker Script](./the-linker-script.md).

**3. Memory Configuration** — your `MEMORY` block, echoed back:

```text
Name             Origin             Length             Attributes
FLASH            0x08000000         0x00080000         xr
RAM              0x20000000         0x00020000         xrw
*default*        0x00000000         0xffffffff
```

Check `Origin` and `Length` here when a board of the wrong variant is being blamed for a software problem. `0x00080000` is 512 KB — an `RC` part would need `0x00040000`.

**4. Linker script and memory map** — the body of the file, and the part worth learning to read. Output sections are flush left; the input sections that fed them are indented one space; symbol definitions are indented far right at the address they resolved to.

```text
.isr_vector     0x08000000       0x40
                0x08000000                        . = ALIGN (0x4)
 *(.isr_vector)
 .isr_vector    0x08000000       0x40 build/startup.o
                0x08000000                vector_table
                0x08000040                        . = ALIGN (0x4)

.text           0x08000040     0x10a8
                0x08000040                        . = ALIGN (0x4)
 *(.text)
 .text          0x08000040       0xa0 <toolchain>/libc_nano.a(libc_a-memchr.o)
                0x08000040                memchr
 *(.text*)
 .text.Default_Handler
                0x0800016c        0x2 build/startup.o
                0x0800016c                DebugMon_Handler
                0x0800016c                HardFault_Handler
                0x0800016c                SysTick_Handler
                0x0800016c                PendSV_Handler
                0x0800016c                NMI_Handler
                0x0800016c                Default_Handler
```

Three things this excerpt proves at a glance, none of which you can see from `size`:

- `.isr_vector` is at `0x0800_0000`, is `0x40` bytes, and came from `startup.o`. The vector table survived garbage collection and is where the hardware will look.
- The wildcard order in the script is visible in the output: bare `*(.text)` matched `memchr` from the C library first, then `*(.text*)` picked up the per-function `.text.*` sections that `-ffunction-sections` created.
- **Ten symbols share address `0x0800_016c`.** That is a two-byte `Default_Handler` and the nine weak aliases pointing at it, exactly as [Startup Code: Reset to `main`](./startup-code.md) sets up. If you ever want to check whether your `SysTick_Handler` actually replaced the default, this is the definitive answer: a handler you have defined appears at its own address with its own size, not in this pile.

The `.data` section is where the map shows you the VMA/LMA split directly:

```text
.data           0x20000000       0x5c load address 0x08001138
                0x20000000                        _sdata = .
 .data._impure_data
                0x20000010       0x4c <toolchain>/libc_nano.a(libc_a-impure.o)
                0x2000005c                        _edata = .
```

`0x2000_0000 … 0x2000_005c` in RAM, `load address 0x0800_1138` in flash. `_sidata` is that load address, and 92 bytes is exactly what `Reset_Handler` will copy.

**Plus, with `--cref`: the cross-reference table.** One row per symbol: where it was defined, and every file that referenced it.

```text
printf                                            <toolchain>/libc_nano.a(libc_a-printf.o)
                                                  build/main.o
vector_table                                      build/startup.o
```

`--cref` answers the reverse question from part 1 — not "what did this object pull in" but "who is still referencing this thing I am trying to delete".

## A size budget you can run every build

```bash
arm-none-eabi-size blink.elf                                   # the trend line
arm-none-eabi-nm --print-size --size-sort --radix=d blink.elf | tail -20
```

The habit that pays: record the `size` output in CI on every commit and fail the build on a regression past a threshold. Code size on a microcontroller behaves like a leak — it never grows by 12 KB in one commit, it grows by 300 bytes in forty commits, and the day it stops fitting is a long way from the day the cause was introduced.

:::warning[The RAM number from `size` is a floor, not your RAM usage]
`bss` was 1568 bytes and the linker reported RAM at 1.52% of 128 KB. Neither figure is a statement about how much RAM the firmware needs at runtime, and treating them as one is how a project ships a device that works on the bench and corrupts its own globals in the field.

`size` and `--print-memory-usage` are **static** measurements. They count sections. They cannot count:

- **Actual stack depth.** The linker knows the 1024 bytes of `_Min_Stack_Size` you reserved. It has no idea whether your deepest call path — including an interrupt that preempts it, and an interrupt that preempts *that* — needs 1400. Nothing in the toolchain checks this at link time, and the reservation section in the linker script only proves the *minimum* fits.
- **Heap growth.** `malloc` moves `_sbrk`'s break upward at runtime. Static analysis sees the initial state.
- **The collision between the two.** The stack grows down from `_estack`, the heap grows up from `end`. On a Cortex-M nothing sits between them and nothing traps the crossing. The first symptom is a global with a plausible but wrong value, thousands of cycles after the corruption, in code that has nothing to do with the cause.

What to do instead, in increasing order of confidence:

```bash
# 1. Per-function stack frames, from the compiler. Emits one .su file per object.
arm-none-eabi-gcc -fstack-usage -c main.c
# main.c:16:5:main   24   static
```

`-fstack-usage` gives you frame sizes but not call depth; combining them into a worst case needs a call-graph tool, and it still cannot see through function pointers or recursion.

2. **Paint the stack.** Fill the reserved region with a known pattern at startup, run the worst workload you can construct, then read back how far the pattern was overwritten. This measures the real high-water mark of the real firmware, which is the only number that settles the argument — but only for the paths your test actually exercised.

3. **Put an MPU region at the bottom of the stack** with no access permission. The overflow then faults at the instruction that caused it instead of silently corrupting a neighbour, which converts the worst class of bug in embedded software into an ordinary one. [The Memory Protection Unit](../02-processor-architecture/the-mpu.md) covers the configuration.

The rule worth keeping: `size` tells you whether the image **fits**. It does not tell you whether the firmware **runs**.
:::

## See also

- [Memory Sections and VMA vs LMA](./memory-sections.md) — what the section names in every listing above mean, and the load-vs-run distinction the map file prints.
- [The Linker Script](./the-linker-script.md) — the script that produced these addresses, and the `KEEP` that keeps `.isr_vector` out of the discarded list.
- [C Libraries for Embedded](./c-libraries-for-embedded.md) — why `printf` costs 4 KB against newlib-nano and 32 KB against full newlib.
- [Optimization for Size and Speed](./optimization-flags.md) — the flags that move these numbers, measured on the same binary.
- [Cross-Compilation](./cross-compilation.md) — the rest of the `arm-none-eabi-*` toolset and what `readelf -A` verifies.

## References

- Free Software Foundation — [**GNU Binutils documentation**](https://sourceware.org/binutils/docs/binutils/). The normative reference for the tools on this page: [`size`](https://sourceware.org/binutils/docs/binutils/size.html) and its Berkeley versus System V formats, [`nm`](https://sourceware.org/binutils/docs/binutils/nm.html) for `--print-size`, `--size-sort` and the full symbol-type letter table, [`objdump`](https://sourceware.org/binutils/docs/binutils/objdump.html) for `-h` and `-d`, [`readelf`](https://sourceware.org/binutils/docs/binutils/readelf.html) for `-A` build attributes, and [`objcopy`](https://sourceware.org/binutils/docs/binutils/objcopy.html) for `-O binary`.
- Free Software Foundation — [**GNU `ld` manual, "Command-line Options"**](https://sourceware.org/binutils/docs/ld/Options.html). `-Map`, `--cref`, `--print-memory-usage`, `--gc-sections` and `--print-gc-sections`, and the `--no-warn-rwx-segments` note. The map file's four-part structure is a property of `ld` and is documented here rather than in the binutils manual.
- Free Software Foundation — [**GCC manual, "Options for Code Generation"**](https://gcc.gnu.org/onlinedocs/gcc/Code-Gen-Options.html) and [**"Options for Debugging"**](https://gcc.gnu.org/onlinedocs/gcc/Debugging-Options.html). `-ffunction-sections`, `-fdata-sections` — the compiler half of the `--gc-sections` measurement in the table — and `-fstack-usage` with the `.su` output format quoted in the warning.
- Arm — [**Arm GNU Toolchain**](https://developer.arm.com/Tools%20and%20Software/GNU%20Toolchain), release **14.2.Rel1**. The toolchain every number on this page was measured with; its release notes name the exact GCC and binutils versions in each build, which is what you pin. See [Choosing a Toolchain](./toolchains-and-compilers.md) for why pinning is mandatory.
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). §3.3 "Memory map" for the 512 KB / 128 KB figures the percentages above are taken against.
