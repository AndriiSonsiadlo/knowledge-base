---
id: assembling
title: Assembling
sidebar_label: Assembling
sidebar_position: 4
tags: [c++, assembler, object-files, machine-code]
---

# Assembling

Assembling is stage 3 of the [pipeline](./compilation-pipeline.md). The assembler (`as`, from GNU
binutils, on Linux) turns the compiler's assembly text into an **object file**: the instructions
encoded as bytes, plus the bookkeeping the linker needs. It is the simplest stage. It does no
optimisation, and with compiler-generated input it practically never fails. It matters because it
is where the format the linker works with is created.

**Prerequisites:** [The Compilation Pipeline](./compilation-pipeline.md).

What is inside the resulting file (sections, the symbol table, relocation types) is covered on
[Object Files and Symbols](./object-files-and-symbols.md). This page covers the translation itself.

## Running the assembler

`g++ -c` runs stages 1–3 and stops with a `.o`. You can also run `as` directly on a `.s` file, either
one the compiler wrote with `-S` or one you wrote by hand:

```nasm title="five.s"
	.intel_syntax noprefix
	.text
	.globl	five
five:
	mov	eax, 5
	add	eax, 3
	ret
```

```bash
as five.s -o five.o
objdump -d -M intel five.o
nm five.o
```

```text
0000000000000000 <five>:
   0:	b8 05 00 00 00       	mov    eax,0x5
   5:	83 c0 03             	add    eax,0x3
   8:	c3                   	ret

0000000000000000 T five
```

Each instruction became its encoding: `b8` is "move a 32-bit immediate into `eax`", followed by the
immediate `5` in little-endian order. x86-64 instructions are variable-length, from 1 to 15 bytes.
The `.globl five` directive is what made `five` a global symbol (`T`) that other object files can
call. Without it, the label would be local to this file.

## What the assembler cannot know

The assembler sees one file. When an instruction refers to something outside it, the assembler
emits a placeholder and a **relocation**: a note saying "patch these bytes with the address of
symbol X, computed this way".

```cpp title="ext.cpp"
extern int external_var;
int read_external() { return external_var; }
```

<Tabs>
  <TabItem value="pie" label="g++ -O2 -c (default)">

```text
   4:	8b 05 00 00 00 00    	mov    eax,DWORD PTR [rip+0x0]
			6: R_X86_64_PC32	external_var-0x4
   a:	c3                   	ret
```

The four zero bytes at offset 6 will hold the distance from the next instruction to `external_var`.

  </TabItem>
  <TabItem value="pic" label="g++ -O2 -fPIC -c">

```text
   4:	48 8b 05 00 00 00 00 	mov    rax,QWORD PTR [rip+0x0]
			7: R_X86_64_REX_GOTPCRELX	external_var-0x4
   b:	8b 00                	mov    eax,DWORD PTR [rax]
   d:	c3                   	ret
```

For a shared library the variable might live in another library, so the code loads its address
from the **Global Offset Table** first, then reads through it: one extra instruction.

  </TabItem>
</Tabs>

The linker resolves these records later; the walkthrough on the
[pipeline page](./compilation-pipeline.md#tracing-a-two-file-program) shows the before and after.

## Position-independent code

Code compiled with `-fPIC` reaches every global through PC-relative addressing or the GOT, so it
runs correctly wherever the loader maps it. That is required for shared libraries
(`g++ -shared` refuses most non-PIC objects on x86-64). Ubuntu's GCC also builds executables as
position-independent (PIE) by default, which is what lets the loader randomise their address.
[Static vs Dynamic Linking](./static-vs-dynamic-linking.md) covers when you need `-fPIC`.

## Key points

- `as` turns assembly text into an ELF object one-to-one; no optimisation happens here.
- Anything the file does not define becomes a zero-filled hole plus a relocation record.
- `-fPIC` changes which relocations are emitted (GOT-relative), so that the code can be loaded at any
  address.
- `objdump -dr` shows the encoded bytes and the relocations together.
