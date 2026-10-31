---
id: compilation-pipeline
title: The Compilation Pipeline
sidebar_label: Compilation Pipeline
sidebar_position: 1
tags: [c++, compilation, build, toolchain, compiler]
---

# The Compilation Pipeline

`g++ main.cpp square.cpp -o app` looks like one step, but the driver runs four separate tools in
sequence: the **preprocessor**, the **compiler proper**, the **assembler**, and the **linker**. Each
one has its own input format, its own output, and its own class of errors. Knowing which stage you
are in tells you what an error message means, which flag affects it, and which tool you need to
inspect it.

This page is the map of the whole section. It traces one small program through every stage with
real tool output. Each stage then has its own page with the detail.

## The four stages

<Diagram title="From source files to an executable" caption="Stages 1–3 run once per .cpp file; the linker runs once for the whole program." accent="blue">
  <DiagramGroup label="Per translation unit (each .cpp separately)">
    <DiagramNode icon="file-text" title="1. Preprocess">`.cpp` + headers → `.ii`. Text only: `#include`, macros, `#if`.</DiagramNode>
    <DiagramNode icon="brain" title="2. Compile">`.ii` → `.s`. Parse, type-check, instantiate templates, optimise.</DiagramNode>
    <DiagramNode icon="binary" title="3. Assemble">`.s` → `.o`. Machine code with holes for unknown addresses.</DiagramNode>
  </DiagramGroup>
  <DiagramArrow label="all .o files + libraries" />
  <DiagramNode icon="workflow" title="4. Link" accent>Resolve symbols across files, fill the holes, write the executable.</DiagramNode>
</Diagram>

The split matters because **each `.cpp` is compiled in isolation**. While compiling `main.cpp`, the
compiler knows nothing about `square.cpp`; it only knows the declarations that the headers pasted
in. Everything that connects the files happens in the linker. One preprocessed `.cpp` file is
called a [translation unit](./translation-units.md), and it is the unit the first three stages work
on.

| Stage | Tool run by `g++` | Stop after it with | Output | Canonical page |
|---|---|---|---|---|
| Preprocess | `cc1plus -E` (the integrated preprocessor) | `-E` | `.ii` (C++ text) | [Preprocessing](./preprocessing.md) |
| Compile | `cc1plus` | `-S` | `.s` (assembly text) | [Compilation](./compilation.md) |
| Assemble | `as` | `-c` | `.o` (ELF relocatable object) | [Assembling](./assembling.md) |
| Link | `collect2` → `ld` | (none: the default) | executable or `.so` | [Linking](./linking.md) |

GCC's documentation names the extensions: `.ii` is preprocessed C++, `.s` is assembly that needs no
further preprocessing ([GCC: Overall Options](https://gcc.gnu.org/onlinedocs/gcc/Overall-Options.html)).
Run `g++ -v` to see the driver print each sub-command it launches; on GCC 15 those are
`/usr/libexec/gcc/x86_64-linux-gnu/15/cc1plus …`, then `as …`, then `collect2 …`.

## Tracing a two-file program

The program below is small enough to read every stage's output in full. `main.cpp` calls a function
defined in another file and writes a global variable, which is exactly what forces the linker to do
real work.

<Tabs>
  <TabItem value="h" label="square.h">

```cpp title="square.h"
#pragma once
#define SCALE 3
int square(int x);
```

  </TabItem>
  <TabItem value="sq" label="square.cpp">

```cpp title="square.cpp"
#include "square.h"

int square(int x) { return x * x; }
```

  </TabItem>
  <TabItem value="main" label="main.cpp">

```cpp title="main.cpp"
#include "square.h"

int counter = 0;

int main() {
    counter = square(SCALE);
    return counter;
}
```

  </TabItem>
</Tabs>

All output below is from GCC 15.2 and GNU binutils 2.46 on x86-64 Linux, with `-O1` so that the
assembly stays short. Assembly is shown in Intel syntax (`-masm=intel`, `objdump -M intel`).

<Walkthrough title="main.cpp through the pipeline" caption="One translation unit followed from text to a linked instruction stream." accent="blue" fixedHeight={false}>
  <Step title="Preprocess: g++ -E">

```bash
g++ -std=c++23 -E -P main.cpp -o main.ii    # -P drops the '# line' markers
```

```cpp title="main.ii"
int square(int x);
int counter = 0;
int main() {
    counter = square(3);
    return counter;
}
```

The `#include` line was replaced by the header's text, `#pragma once` was consumed, and `SCALE`
became <StepChange>`3`</StepChange>. The `#define` itself is gone: the compiler never sees macros.
Without `-P` the file also carries line markers such as `# 1 "square.h" 1`, which is how later
error messages still point at the right header line.

  </Step>
  <Step title="Compile: g++ -S">

```bash
g++ -std=c++23 -O1 -S -masm=intel main.cpp -o main.s
```

```nasm title="main.s (directives trimmed)"
main:
	sub	rsp, 8
	mov	edi, 3
	call	_Z6squarei@PLT
	mov	DWORD PTR counter[rip], eax
	add	rsp, 8
	ret
	.globl	counter
	.bss
counter:
	.zero	4
```

The compiler has type-checked the code and chosen instructions. Two things to notice: the call
target is not `square` but the **mangled** name <StepChange>`_Z6squarei`</StepChange> (`square`
taking an `int`, see [Name Mangling](./name-mangling.md)), and `counter`, zero-initialised, goes in
`.bss`. The compiler does not know where `square` lives. It only emits the name.

  </Step>
  <Step title="Assemble: g++ -c">

```bash
g++ -std=c++23 -O1 -c main.cpp -o main.o
objdump -d -r -M intel main.o
```

```text
0000000000000000 <main>:
   0:	f3 0f 1e fa          	endbr64
   4:	48 83 ec 08          	sub    rsp,0x8
   8:	bf 03 00 00 00       	mov    edi,0x3
   d:	e8 00 00 00 00       	call   12 <main+0x12>
			e: R_X86_64_PLT32	_Z6squarei-0x4
  12:	89 05 00 00 00 00    	mov    DWORD PTR [rip+0x0],eax        # 18 <main+0x18>
			14: R_X86_64_PC32	counter-0x4
  18:	48 83 c4 08          	add    rsp,0x8
  1c:	c3                   	ret
```

The instructions are now bytes, and the addresses start at 0. The call's operand is
<StepChange>`00 00 00 00`</StepChange>: a hole. Each hole has a **relocation** record (the indented
`R_X86_64_…` lines) telling the linker which symbol's address to write there. (`endbr64` was added
because Ubuntu's GCC enables `-fcf-protection` by default.)

  </Step>
  <Step title="Read the symbol table: nm">

```bash
nm main.o
nm square.o
```

```text
                 U _Z6squarei
0000000000000000 B counter
0000000000000000 T main

0000000000000000 T _Z6squarei
```

`main.o` **defines** `main` (`T`, code) and `counter` (`B`, `.bss`), and **needs**
<StepChange>`U _Z6squarei`</StepChange>: undefined, expected from somewhere else. `square.o`
defines exactly that symbol. The letters are explained in
[Object Files and Symbols](./object-files-and-symbols.md#reading-nm-output).

  </Step>
  <Step title="Link: g++ main.o square.o">

```bash
g++ main.o square.o -o app
./app; echo "exit=$?"
objdump -d -M intel app | sed -n '/<main>:/,/^$/p'
```

```text
exit=9
0000000000001129 <main>:
    1129:	f3 0f 1e fa          	endbr64
    112d:	48 83 ec 08          	sub    rsp,0x8
    1131:	bf 03 00 00 00       	mov    edi,0x3
    1136:	e8 0b 00 00 00       	call   1146 <_Z6squarei>
    113b:	89 05 d3 2e 00 00    	mov    DWORD PTR [rip+0x2ed3],eax        # 4014 <counter>
    1141:	48 83 c4 08          	add    rsp,0x8
    1145:	c3                   	ret
```

The linker placed `main` at `0x1129`, `square` at `0x1146` and `counter` at `0x4014`, then filled
both holes: the call operand became <StepChange>`0b 00 00 00`</StepChange> (`0x113b + 0x0b =
0x1146`) and the store's offset became `d3 2e 00 00` (`0x2ed3`). The program returns
`square(3) = 9`. The addresses are offsets because this is a position-independent executable (PIE).
The loader adds a random base at run time.

  </Step>
  <Step title="Remove square.o: the link fails">

```bash
g++ main.o -o app
```

```text
/usr/bin/x86_64-linux-gnu-ld.bfd: main.o: in function `main':
main.cpp:(.text+0xe): undefined reference to `square(int)'
collect2: error: ld returned 1 exit status
```

Compilation of `main.cpp` already succeeded, so this is purely a **linker** error. The offset
<StepChange>`.text+0xe`</StepChange> is exactly the relocation from step 3 that had no symbol to
point at. `ld` demangles `_Z6squarei` back to `square(int)` for the message.

  </Step>
</Walkthrough>

## Which stage produced this error?

Recognising the stage from the message is the fastest way to a fix.

| Message looks like | Stage | Typical cause | Go to |
|---|---|---|---|
| `fatal error: foo.h: No such file or directory` | Preprocess | Missing `-I` path, wrong quotes vs angle brackets | [Headers and Includes](./headers-and-includes.md#where-the-compiler-looks) |
| `error: 'x' was not declared in this scope`, type mismatch, template errors | Compile | Code is ill-formed, missing declaration | [Compilation](./compilation.md) |
| `Error:` from `as`, unknown instruction | Assemble | Almost always hand-written or inline asm | [Assembling](./assembling.md) |
| `undefined reference to …`, `multiple definition of …` (from `ld`/`collect2`) | Link | Missing `.o`/library, wrong library order, ODR violation | [Linking](./linking.md#reading-linker-errors) |
| `error while loading shared libraries: libX.so` | Run time (dynamic loader) | Library not on the loader's search path | [Static vs Dynamic Linking](./static-vs-dynamic-linking.md#how-the-loader-finds-libraries) |

## Which flags affect which stage

`g++` accepts every flag on one command line and passes each to the stage that understands it.

| Flag | Stage | Effect |
|---|---|---|
| `-I dir`, `-D NAME=val`, `-include file` | Preprocess | Add an include path, define a macro, force-include a file |
| `-std=c++23`, `-W…`, `-O…`, `-g`, `-fPIC`, `-march=…` | Compile | Language version, warnings, optimisation, debug info, code model |
| `-Wa,opt` | Assemble | Pass `opt` straight to `as` |
| `-L dir`, `-l name`, `-static`, `-shared`, `-Wl,opt` | Link | Library search path, libraries, link mode, raw linker options |
| `-E`, `-S`, `-c`, `-o file`, `-v` | Driver | Where to stop, where to write, show sub-commands |

## Build artifacts

| File | Produced by | Contains |
|---|---|---|
| `.ii` | `-E` | Preprocessed C++ (one translation unit) |
| `.s` | `-S` | Assembly text for one TU |
| `.o` (`.obj` on MSVC) | `-c` | Relocatable machine code, symbol table, relocations |
| `.a` (`.lib`) | `ar` | Archive of `.o` files: a static library |
| `.so` (`.dll`, `.dylib`) | `-shared` | Shared library, loaded at run time |
| executable | link | Final program; on Linux an ELF executable, usually PIE |

To keep all intermediate files from a normal build, add `-save-temps`: GCC leaves `main.ii`,
`main.s` and `main.o` next to the output.

## Pitfalls

- **Treating a link error as a compile error.** `undefined reference` means the declarations were
  fine and every file compiled; the fix is in what you link (a missing `.cpp`, `-l` flag or library
  order), not in the code that calls the function.
- **Reading `-O0` assembly to judge performance.** Unoptimised code stores every variable to the
  stack. Look at `-O2` output, as [Compilation](./compilation.md#optimisation-levels) shows.
- **Assuming a header change only rebuilds one file.** Every translation unit that includes the
  header, directly or transitively, has to be recompiled. That is why build systems track header
  dependencies ([Build Systems](./build-systems-cmake.md)).

## Key points

- Preprocess, compile and assemble run **per `.cpp`**, blind to other files; only the linker sees
  the whole program.
- An object file is machine code with **holes** plus a list of the symbols it defines and needs.
- `-E`, `-S`, `-c` stop after stages 1, 2, 3; `nm` and `objdump -dr` show what the linker will get.
- The error's source tool (`cc1plus`, `as`, `ld`, the loader) tells you where to look for the fix.

## Related

- [Translation Units](./translation-units.md): what the compiler sees as "one file", and the One
  Definition Rule that the linker enforces.
- [Modules](./modules.md) *(C++20)*: replaces textual inclusion in stage 1 with compiled interfaces.
- [Build Systems and CMake](./build-systems-cmake.md): automating this pipeline for many files.
- [Reading Assembly](../14-debugging-and-profiling/07-reading-assembly.md): how to read the `.s`
  and `objdump` output in more depth.
