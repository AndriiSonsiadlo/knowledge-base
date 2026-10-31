---
id: object-files-and-symbols
title: Object Files and Symbols
sidebar_label: Object Files
sidebar_position: 7
tags: [c++, object-files, symbols, elf, linking]
---

# Object Files and Symbols

An object file (`.o`) is what one translation unit becomes after [assembling](./assembling.md): the
machine code and data for that file, cut into named **sections**, plus a **symbol table** listing
what the file defines and what it needs, and **relocations** marking the bytes the linker must patch.
Almost every linker error and most "why is my binary this big" questions are answered by reading
these three tables, so this page is about reading them.

**Prerequisites:** [The Compilation Pipeline](./compilation-pipeline.md),
[Translation Units](./translation-units.md) (for linkage).

Linux uses **ELF** ([specification](https://refspecs.linuxfoundation.org/elf/elf.pdf)), Windows uses
**COFF/PE** (`.obj`), macOS uses **Mach-O**. The ideas are the same; the tools differ (`nm`,
`objdump`, `readelf` on Linux; `dumpbin` on Windows; `nm`, `otool` on macOS). Everything below is
ELF on x86-64, produced with GCC 15.

## Anatomy of an ELF object

<Diagram title="What a .o file contains" caption="Sections hold bytes; the tables describe them for the linker." accent="amber">
  <DiagramGroup label="Sections (contents)">
    <DiagramNode title=".text">Machine code</DiagramNode>
    <DiagramNode title=".data">Initialised, writable globals</DiagramNode>
    <DiagramNode title=".bss">Zero-initialised globals. Size only, no bytes in the file</DiagramNode>
    <DiagramNode title=".rodata">Constants, string literals</DiagramNode>
  </DiagramGroup>
  <DiagramArrow label="described by" />
  <DiagramGroup label="Tables (metadata)">
    <DiagramNode icon="key" title=".symtab" accent>Name → section, offset, size, binding</DiagramNode>
    <DiagramNode icon="workflow" title=".rela.text">"Patch offset N with the address of symbol S"</DiagramNode>
  </DiagramGroup>
</Diagram>

Compile this file to see each kind of entity land somewhere:

```cpp title="sections.cpp"
int initialized = 42;
int zeroed;
static int file_local = 7;
const int folded = 5;
extern const int exported_const;
extern const int exported_const = 9;
const char* msg = "Hello";
extern int defined_elsewhere;

static int helper() { return file_local; }
int answer() { return helper() + defined_elsewhere + folded; }
inline int twice(int x) { return 2 * x; }
int use_twice() { return twice(answer()); }
```

## Reading nm output

`nm` prints one line per symbol: value (offset within its section), a type letter, and the name.
`-C` demangles C++ names ([Name Mangling](./name-mangling.md)).

<Tabs groupId="opt">
  <TabItem value="o0" label="g++ -O0 -c; nm -C">

```text
0000000000000000 W twice(int)
0000000000000010 T answer()
000000000000002a T use_twice()
0000000000000004 d file_local
0000000000000000 r folded
0000000000000000 t helper()
                 U defined_elsewhere
0000000000000004 R exported_const
0000000000000000 D initialized
0000000000000000 D msg
0000000000000000 B zeroed
```

  </TabItem>
  <TabItem value="o2" label="g++ -O2 -c; nm -C">

```text
0000000000000000 T answer()
0000000000000010 T use_twice()
                 U defined_elsewhere
0000000000000000 R exported_const
0000000000000000 D initialized
0000000000000000 D msg
0000000000000000 B zeroed
```

  </TabItem>
</Tabs>

| Letter | Meaning | From the example |
|---|---|---|
| `T` / `t` | Code in `.text`; upper case = global, lower case = local to this file | `answer()` / `helper()` (`static`) |
| `D` / `d` | Initialised data | `initialized` / `file_local` (`static`) |
| `B` / `b` | Zero-initialised data in `.bss` | `zeroed` |
| `R` / `r` | Read-only data | `exported_const` / `folded` |
| `U` | **Undefined**: used here, must be defined in another object or library | `defined_elsewhere` |
| `W` | Weak definition: the linker may pick any one of several, and a strong definition wins | `twice(int)`, an `inline` function |

What the example shows:

- **Internal linkage leaves no global symbol.** `static` variables and functions, anonymous-namespace
  entities and namespace-scope `const` variables get lower-case letters, which the linker never
  matches against other files. At `-O2` they disappear completely: `helper` was inlined, `folded`
  was replaced by `5`, and `file_local` became the constant `7`.
- **`const` at namespace scope is internal by default in C++.** `folded` is `r`; you need
  `extern const` to export a constant (`exported_const`, `R`).
- **`msg` is in `D`, not `R`.** The pointer is writable; only the string `"Hello"` is in `.rodata`.
  (With `-fPIC`-style code, as here, the pointer actually sits in `.data.rel.local` because it needs a
  relocation; `nm` still reports `D`.)
- **`inline` functions are weak**, and their code goes into a separate section group
  (`.text._Z5twicei`), so that the linker keeps one copy when many TUs emit it. At `-O2` the call was
  inlined and no out-of-line copy was needed.

Useful variations:

```bash
nm -C -u file.o            # only undefined symbols: what this file needs
nm -C --defined-only file.o
nm -S --size-sort -C app   # with sizes: what makes the binary big
nm -D lib.so               # the dynamic symbol table: what a shared library exports
```

## Sections and their sizes

```bash
readelf -SW sections.o     # section headers
size -A sections.o         # section sizes
objdump -s -j .rodata sections.o
```

```text
Contents of section .rodata:
 0000 05000000 09000000 48656c6c 6f00      ........Hello.
```

That is `folded` (5), `exported_const` (9) and the string literal, in little-endian order. `.bss`
has a size but no file contents: the loader allocates and zero-fills it. That is why a large
zero-initialised array costs nothing in the file and an initialised one costs its full size.

## Symbol binding: global, local, weak

`readelf -s` shows the binding explicitly:

```text
     4: 0000000000000004     4 OBJECT  LOCAL  DEFAULT    4 _ZL10file_local
     9: 0000000000000000     4 OBJECT  GLOBAL DEFAULT    4 initialized
    15: 0000000000000000    18 FUNC    WEAK   DEFAULT    9 _Z5twicei
```

- **GLOBAL**: visible to the linker; exactly one definition allowed in the program.
- **LOCAL**: private to this object (`static`, anonymous namespace). Two files can each have a local
  `helper` with no conflict.
- **WEAK**: a definition that yields to a global one, and of which duplicates are allowed. The
  compiler uses it for `inline` functions and template instantiations. You can request it with
  `__attribute__((weak))` (GCC/Clang) to provide an overridable default; [Linking](./linking.md#weak-symbols)
  shows that in action.

## Relocations

Every place in `.text` or `.data` that refers to an address unknown at assembly time has a
relocation entry:

```bash
readelf -rW main.o          # or: objdump -r main.o
```

```text
Relocation section '.rela.text' at offset 0x190 contains 2 entries:
    Offset             Info             Type               Symbol's Value  Symbol's Name + Addend
000000000000000e  0000000400000004 R_X86_64_PLT32         0000000000000000 _Z6squarei - 4
0000000000000014  0000000500000002 R_X86_64_PC32          0000000000000000 counter - 4
```

(This is `main.o` from the [pipeline walkthrough](./compilation-pipeline.md#tracing-a-two-file-program).)
Read each line as: *at offset `0xe` in `.text`, write the 32-bit distance to `_Z6squarei`, minus 4*.
The −4 is because x86 measures PC-relative distances from the end of the 4-byte field.

| Type | Used for |
|---|---|
| `R_X86_64_PC32` | PC-relative reference to data or code in the same module |
| `R_X86_64_PLT32` | Function call; goes through the PLT if the target ends up in a shared library |
| `R_X86_64_GOTPCRELX` / `REX_GOTPCRELX` | Load an address from the GOT (position-independent access to a global that may be in another module) |
| `R_X86_64_64` | Absolute 64-bit address (for example, a pointer initialised to `&x` in `.data`) |

## Static libraries are archives of objects

A `.a` file is just a bundle of `.o` files with an index:

```bash
ar rcs libgreet.a greet.o     # create (r: insert, c: create, s: write index)
ar t libgreet.a               # list members
nm -C libgreet.a              # symbols of every member
```

The linker pulls a member out of an archive only if it defines a symbol that is still undefined at
that point, which is why library order on the command line matters
([Linking](./linking.md#library-order)).

## Debug information

`-g` adds DWARF sections (`.debug_info`, `.debug_line`, …) that map machine code back to source
lines and variables. They do not get loaded at run time but can be larger than the code itself.
`readelf --debug-dump=info file.o` dumps them; `strip` or `objcopy --only-keep-debug` removes them
or moves them to a separate file. Using them is covered in
[Debugging Basics](../14-debugging-and-profiling/01-debugging-basics.md).

## Pitfalls

- **Expecting a `static` or `const` global to be visible from another file.** It has internal
  linkage: `nm` shows it lower case (or not at all), and other files get `undefined reference`.
- **Defining a variable in a header.** Every TU that includes it gets a global `D`/`B` symbol, and
  the link fails with `multiple definition`. Declare it `extern` in the header, or make it `inline`
  *(C++17)*: see [Translation Units](./translation-units.md#the-one-definition-rule).
- **Reading `nm` of a stripped binary.** `strip` removes `.symtab`; only `nm -D` (dynamic symbols)
  works then.

## Key points

- An object file = sections (bytes) + symbol table (who defines/needs what) + relocations (holes).
- `nm -C`: upper case is global, lower case is local, `U` is a dependency, `W` is weak.
- Internal-linkage entities never collide across files and often vanish at `-O2`.
- `.bss` costs no file space; `.data` and `.rodata` cost their full size.
