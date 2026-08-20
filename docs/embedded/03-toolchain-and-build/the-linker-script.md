---
id: the-linker-script
title: The Linker Script
sidebar_label: The Linker Script
sidebar_position: 4
tags: [embedded, toolchain, linker, ld, memory-map, stm32]
---

# The Linker Script

On a hosted system nobody writes a linker script, because the answer to "where does this code go" is "wherever the loader decides", and the loader is part of the OS. On a microcontroller there is no loader. The addresses in the binary are the addresses the CPU will use, forever, and something has to choose them. That something is a text file, usually about a hundred lines long, that most projects copy once and never read.

The mental model worth having is that the linker script is **the contract between the hardware's memory map and your program's parts**. On one side: this part has flash at `0x0800_0000` and SRAM at `0x2000_0000`, facts from the reference manual that you cannot change. On the other side: a pile of input sections named `.text`, `.rodata`, `.data`, `.bss` produced by the compiler, plus a handful of symbols that the startup code and the C library expect somebody to define. The script maps one onto the other. Almost every "it builds but does not run" failure in bare-metal firmware is a defect in that mapping — which is why it is worth reading the file you copied.

:::info[Prerequisites]
[The Cortex-M Memory Map](../02-processor-architecture/memory-map-and-bit-banding.md) establishes where flash and SRAM live in the address space and why the address itself determines how an access behaves. [Linking](../../programming/cpp/01-toolchain-and-build/linking.md) owns the general linking model — symbol resolution, archives, and what a linker does — and this page assumes it.
:::

## The three things a script must do

1. **Declare the regions.** `MEMORY` names each physical block, its start address, its length, and what may be done in it.
2. **Place the sections.** `SECTIONS` says which input sections go into which output section, in what order, in which region — and for initialised data, from where it is *loaded* separately from where it *lives*.
3. **Define the symbols the rest of the build depends on.** The startup code needs to know where `.data` starts and ends; the C library needs to know where the heap can begin; the vector table needs the top of the stack. None of these are addresses you can hard-code, because they move every time the code changes.

## A complete script for the STM32F411RE

This is the whole file, not an excerpt. It is the script [Startup Code: Reset to `main`](./startup-code.md) is written against, and the one the bare-metal blink in the next folder uses unchanged. It targets the NUCLEO-F411RE's STM32F411RE exactly: 512 KB of flash based at `0x0800_0000` and 128 KB of SRAM based at `0x2000_0000` (RM0383 Rev 4, §3.3 "Memory map" and the block diagram in §2). Save it as `stm32f411re.ld`.

```text title="stm32f411re.ld"
/* Linker script for STM32F411RE (NUCLEO-F411RE).
   512 KB flash @ 0x08000000, 128 KB SRAM @ 0x20000000.  RM0383 Rev 4, section 3.3. */

ENTRY(Reset_Handler)

/* Reserved space, checked by the linker rather than by hope. */
_Min_Heap_Size  = 0x200;   /*  512 bytes */
_Min_Stack_Size = 0x400;   /* 1024 bytes */

MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 512K
  RAM   (xrw) : ORIGIN = 0x20000000, LENGTH = 128K
}

/* Initial stack pointer: top of RAM, because the stack is full descending. */
_estack = ORIGIN(RAM) + LENGTH(RAM);

SECTIONS
{
  /* The vector table must be the first thing in flash. */
  .isr_vector :
  {
    . = ALIGN(4);
    KEEP(*(.isr_vector))
    . = ALIGN(4);
  } >FLASH

  .text :
  {
    . = ALIGN(4);
    *(.text)
    *(.text*)
    KEEP(*(.init))
    KEEP(*(.fini))
    . = ALIGN(4);
    _etext = .;
  } >FLASH

  .rodata :
  {
    . = ALIGN(4);
    *(.rodata)
    *(.rodata*)
    . = ALIGN(4);
  } >FLASH

  /* C++ exception unwind tables. libgcc references these two symbols
     unconditionally, so they must exist even in a C-only build. */
  .ARM.extab :
  {
    *(.ARM.extab* .gnu.linkonce.armextab.*)
  } >FLASH

  .ARM.exidx :
  {
    __exidx_start = .;
    *(.ARM.exidx*)
    __exidx_end = .;
  } >FLASH

  /* Constructor tables walked by __libc_init_array(). */
  .preinit_array :
  {
    PROVIDE_HIDDEN(__preinit_array_start = .);
    KEEP(*(.preinit_array*))
    PROVIDE_HIDDEN(__preinit_array_end = .);
  } >FLASH

  .init_array :
  {
    PROVIDE_HIDDEN(__init_array_start = .);
    KEEP(*(SORT(.init_array.*)))
    KEEP(*(.init_array*))
    PROVIDE_HIDDEN(__init_array_end = .);
  } >FLASH

  .fini_array :
  {
    PROVIDE_HIDDEN(__fini_array_start = .);
    KEEP(*(SORT(.fini_array.*)))
    KEEP(*(.fini_array*))
    PROVIDE_HIDDEN(__fini_array_end = .);
  } >FLASH

  /* Where the initialised-data image sits in flash. Startup copies from here. */
  _sidata = LOADADDR(.data);

  /* Initialised data: lives in RAM, is loaded from flash. */
  .data :
  {
    . = ALIGN(4);
    _sdata = .;
    *(.data)
    *(.data*)
    . = ALIGN(4);
    _edata = .;
  } >RAM AT> FLASH

  /* Zero-initialised data: occupies RAM, occupies nothing in flash. */
  .bss (NOLOAD) :
  {
    . = ALIGN(4);
    _sbss = .;
    __bss_start__ = _sbss;
    *(.bss)
    *(.bss*)
    *(COMMON)
    . = ALIGN(4);
    _ebss = .;
    __bss_end__ = _ebss;
  } >RAM

  /* Not a real section: a reservation, so the link fails if RAM is oversubscribed. */
  ._user_heap_stack (NOLOAD) :
  {
    . = ALIGN(8);
    PROVIDE(end = .);
    PROVIDE(_end = .);
    . = . + _Min_Heap_Size;
    . = . + _Min_Stack_Size;
    . = ALIGN(8);
  } >RAM

  .ARM.attributes 0 : { *(.ARM.attributes) }
}
```

## Reading it line by line

**`ENTRY(Reset_Handler)`** records an entry-point address in the ELF header. The Cortex-M does not use it — the hardware fetches the reset vector from the vector table, not from the ELF — but GDB and `objdump` do, and `ld` uses reachability from the entry symbol as one root when garbage-collecting sections. Getting it wrong costs you `--gc-sections`.

**`MEMORY`** gives each region a name, an origin, a length and an attribute string. The attributes (`r` read, `w` write, `x` execute, and `!` for negation) are only used when an output section has no explicit `>REGION`, so in a script like this one they are documentation — but accurate documentation matters: RAM is declared `xrw` because on Cortex-M the SRAM region is *not* execute-never and running code from RAM is legal.

Writing `512K` rather than `0x80000` is worth the habit. The two most common linker-script defects on an STM32 are a wrong `LENGTH` copied from a different part in the family (the F411 comes in a 256 KB `RC` variant as well as the 512 KB `RE`) and a wrong `ORIGIN` copied from a project that used a bootloader offset.

**`_estack = ORIGIN(RAM) + LENGTH(RAM);`** computes `0x2002_0000`, one past the last byte of SRAM. That is correct precisely because the Cortex-M stack is full descending: PM0214 Rev 10 §2.1.2 states the processor "uses a full descending stack… When the processor pushes a new item onto the stack, it decrements the stack pointer and then writes the item to the new memory location." The first push therefore writes to `0x2001_FFFC`, inside RAM. The assignment must come *after* the `MEMORY` block, because `ORIGIN` and `LENGTH` can only be evaluated once the region exists.

**`.isr_vector` first, and wrapped in `KEEP`.** The vector table has to be at the base of flash because that is where the processor looks on reset. `KEEP` is what stops `--gc-sections` from deleting it — see the warning below.

**`_etext = .;`** is a symbol *assignment* inside an output section. The location counter `.` holds the current address; assigning it to a name creates a linker-defined symbol there. C code declares these as `extern char _etext;` and takes their **address**, never their value — the symbol has no storage, only a location.

**`.ARM.exidx` and its two symbols.** These hold the exception-unwinding index used by C++ exceptions and by backtracing. `libgcc` references `__exidx_start` and `__exidx_end` whether or not you use C++, so a script that omits this section produces undefined-reference errors on a plain C project. Cheap to include, confusing to debug when missing.

**The `*_array` sections and `PROVIDE_HIDDEN`.** Pointers to C++ static constructors and to functions marked `__attribute__((constructor))` land here. `__libc_init_array()`, called from startup, walks the range between `__init_array_start` and `__init_array_end`. `PROVIDE_HIDDEN` defines the symbol only if nothing else defined it, and marks it hidden so it does not leak into the dynamic symbol table — the GNU `ld` manual describes `PROVIDE` as defining a symbol "only if it is referenced and is not defined by any object included in the link". `SORT` before the wildcard preserves the priority ordering that `__attribute__((init_priority(N)))` encodes in the section name.

**`>RAM AT> FLASH`** is the single most important line in the file, and it is the subject of [Memory Sections and VMA vs LMA](./memory-sections.md). It says: assign these symbols RAM addresses, but put the bytes in the flash image. `_sidata = LOADADDR(.data);` captures where they landed so the startup code can find them.

**`(NOLOAD)`** on `.bss` and on the heap/stack reservation marks those output sections as occupying address space while contributing no bytes to the file. For `.bss` this is belt and braces — its input sections are already `SHT_NOBITS`, so the linker would reach the same conclusion — but it states the intent, and it protects the section from an input section that is not. On the heap/stack reservation it is doing real work: that section's contents are pure location-counter arithmetic, and marking it explicitly keeps a later `objcopy -O binary` from padding your image with the reservation.

**`._user_heap_stack`** is not a section anybody links into. It exists so that advancing the location counter by the heap and stack reservations makes the linker check them against the region size. If they do not fit you get, at link time:

```text
arm-none-eabi-ld: firmware.elf section `._user_heap_stack' will not fit in region `RAM'
arm-none-eabi-ld: region `RAM' overflowed by 1424 bytes
```

which is exactly the failure you want: a build error rather than a stack that quietly grows into your globals at 3 a.m. Note that this only reserves the *minimum*; a stack deeper than `_Min_Stack_Size` still overflows silently at runtime, which is a separate problem with separate tooling.

**`PROVIDE(end = .)`** defines the symbol newlib's `_sbrk` uses as the bottom of the heap — the one the `_sbrk` in [C Libraries for Embedded](./c-libraries-for-embedded.md) reads as `extern char end;`. Both spellings are provided because different library versions reference different ones.

## Symbols this script exports, and who consumes them

| Symbol | Defined at | Consumed by |
|---|---|---|
| `_estack` | Top of RAM, `0x20020000` | Entry 0 of the vector table — the value the hardware loads into `MSP`. |
| `_sidata` | Load address of `.data`, in flash | Startup: source of the `.data` copy. |
| `_sdata`, `_edata` | Bounds of `.data` in RAM | Startup: destination and length of the `.data` copy. |
| `_sbss`, `_ebss` | Bounds of `.bss` in RAM | Startup: the range to zero. |
| `__bss_start__`, `__bss_end__` | Same range, GNU-conventional spelling | Some libraries and RTOSes; provided for compatibility. |
| `end` / `_end` | First byte after `.bss` | `_sbrk`: bottom of the heap. |
| `__preinit_array_*`, `__init_array_*`, `__fini_array_*` | Constructor tables | `__libc_init_array()`. |
| `__exidx_start`, `__exidx_end` | Unwind table bounds | `libgcc`'s unwinder. |
| `_etext` | End of `.text` | Convention; some startup code uses it instead of `_sidata` (see the warning). |

Change a name here and the startup code stops linking. That is the good outcome. The *bad* outcome is changing a name that a library references weakly, and getting a zero.

## Putting a function in RAM

Executing from RAM is faster than from flash on parts with wait states, and is mandatory for code that erases or writes the flash it is executing from. The linker-script side is a fourth copied section:

```text
  _siramfunc = LOADADDR(.RamFunc);

  .RamFunc :
  {
    . = ALIGN(4);
    _sramfunc = .;
    *(.RamFunc)
    *(.RamFunc*)
    . = ALIGN(4);
    _eramfunc = .;
  } >RAM AT> FLASH
```

and the C side is an attribute:

```c
__attribute__((section(".RamFunc"), noinline))
void flash_erase_sector(uint32_t sector) { /* ... */ }
```

The half everyone forgets is that **`.RamFunc` needs its own copy loop in the startup code**, exactly like `.data`. Placing the section and not copying it produces a jump into uninitialised RAM. This section is deliberately not in the canonical script above: the blink firmware does not need it, and an uncopied `.RamFunc` is worse than no `.RamFunc`.

:::warning[`--gc-sections` deletes your vector table and the board goes dark]
This is the classic "it built, it flashed, nothing happens, and the debugger will not attach" failure, and it has one cause.

`-ffunction-sections -fdata-sections` with `--gc-sections` is standard practice — it lets the linker drop every function and object nothing references, and on a firmware that links a C library it commonly saves tens of kilobytes. The mechanism is reachability: the linker starts from a set of roots and deletes every section it cannot reach.

Nothing in your program references the vector table. It is not called; the *hardware* reads it. So it is unreachable, and the linker is entirely correct to delete it. What remains at `0x0800_0000` is whatever section landed there instead. The processor fetches an initial `MSP` and a reset vector out of the middle of some function's machine code, loads garbage into `SP` and `PC`, and locks up before a single instruction of yours runs — often before the debug interface is usable, which is why it looks like a dead board rather than a software bug.

`KEEP(*(.isr_vector))` is the fix, and it is why every working script has it.

Three near-relatives of the same bug:

- **Interrupt handlers vanishing.** A handler referenced only from the vector table is reachable *through* the table — so it survives if the table survived. Put a handler in its own section and reference it from nowhere at all and it goes.
- **Constructor tables vanishing.** `.init_array` is reached only by `__libc_init_array` walking a symbol range, not by a relocation the linker can see. Hence `KEEP` on those sections too. Without it, C++ global constructors silently never run, and every static object is left zero-initialised — a much subtler failure than a dead board.
- **`_etext` used as the `.data` load address.** Older startup files copy from `_etext` on the assumption that `.data`'s load image begins exactly where `.text` ends. Add `.rodata`, or any section between them, or an alignment gap, and the assumption breaks — startup then copies the wrong bytes into every initialised global. `LOADADDR(.data)` asks the linker for the real answer and cannot drift. If you inherit a script and a startup file that disagree about this, fix the startup file.

The general lesson generalises past the linker: anything the *hardware* reads, rather than your code, is invisible to every reachability analysis in the toolchain. Vector tables, bootloader headers, option bytes, and CRC footers all need `KEEP` and usually `used` on the C side.
:::

## See also

- [Memory Sections and VMA vs LMA](./memory-sections.md) — what `>RAM AT> FLASH` means, and where each section physically ends up.
- [Startup Code: Reset to `main`](./startup-code.md) — the code that consumes every symbol in the table above.
- [The Cortex-M Memory Map](../02-processor-architecture/memory-map-and-bit-banding.md) — where the regions in `MEMORY` come from and why their addresses are fixed.
- [Linking](../../programming/cpp/01-toolchain-and-build/linking.md) — symbol resolution, archive semantics and the general linking model.
- [C Libraries for Embedded](./c-libraries-for-embedded.md) — `end`, `_sbrk`, and the heap that the reservation section protects.

## References

- Free Software Foundation — [**GNU `ld` manual, "Linker Scripts"**](https://sourceware.org/binutils/docs/ld/Scripts.html). The normative reference for every construct used above: [`MEMORY`](https://sourceware.org/binutils/docs/ld/MEMORY.html) and its attribute characters, [`SECTIONS`](https://sourceware.org/binutils/docs/ld/SECTIONS.html) and the output-section description grammar, the [location counter](https://sourceware.org/binutils/docs/ld/Location-Counter.html), `KEEP`, `SORT`, `PROVIDE`/`PROVIDE_HIDDEN`, `LOADADDR`, and the `AT>` region form that separates load address from virtual address.
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). §3.3 "Memory map" for the flash base `0x0800_0000` and the SRAM base `0x2000_0000`, and §3 generally for the 512 KB / 128 KB sizes that fix `LENGTH` on the `RE` part. Check your exact suffix here — the `RC` variant has half the flash.
- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), consulted at **Rev 10** (March 2020). §2.1.2 "Stacks" for the full-descending rule that makes `_estack` the top of RAM rather than the bottom; §2.3.4 for the vector table's position at the base of memory.
- Free Software Foundation — [**GCC manual, "Options for Code Generation"**](https://gcc.gnu.org/onlinedocs/gcc/Code-Gen-Options.html) and [**"Options That Control Optimization"**](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html). `-ffunction-sections` and `-fdata-sections`, the compiler half of the `--gc-sections` pairing described in the warning.
