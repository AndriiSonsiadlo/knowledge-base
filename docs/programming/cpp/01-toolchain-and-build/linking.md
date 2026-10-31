---
id: linking
title: Linking
sidebar_label: Linking
sidebar_position: 5
tags: [c++, linker, symbols, libraries, executable]
---

# Linking

Linking is the last stage of the [pipeline](./compilation-pipeline.md) and the first one that sees
the whole program. The linker (`ld`, run by `g++` through `collect2`) takes every object file and
library, matches each undefined symbol to exactly one definition, lays the sections out in memory,
patches every relocation with a real address, and writes the executable. Because every translation
unit was compiled blind to the others, this is where missing functions, duplicate definitions and
wrong library order finally surface.

**Prerequisites:** [Object Files and Symbols](./object-files-and-symbols.md) (symbol tables and
relocations), [Translation Units](./translation-units.md) (the One Definition Rule).

## The linker's two jobs

<Diagram title="Resolve, then relocate" accent="blue">
  <DiagramRow>
    <DiagramNode icon="binary" title="main.o">defines `main`, `counter`; needs `_Z6squarei`</DiagramNode>
    <DiagramNode icon="binary" title="square.o">defines `_Z6squarei`</DiagramNode>
    <DiagramNode icon="package" title="libc.so, libstdc++.so" dashed>define the runtime</DiagramNode>
  </DiagramRow>
  <DiagramArrow label="1. symbol resolution" />
  <DiagramNode icon="key" title="One definition per global name" accent>Every `U` matched to a `T`/`D`/`B`; otherwise an error</DiagramNode>
  <DiagramArrow label="2. layout + relocation" />
  <DiagramNode icon="cpu" title="app">Sections merged, addresses assigned, holes patched</DiagramNode>
</Diagram>

1. **Symbol resolution.** Build one global table from all inputs. Each undefined reference must
   find exactly one strong definition (weak definitions yield to a strong one, and duplicate weak
   ones are allowed).
2. **Layout and relocation.** Concatenate all `.text` sections into one, all `.data` into one, and so
   on; assign each its address; then apply every relocation record.

The [pipeline walkthrough](./compilation-pipeline.md#tracing-a-two-file-program) shows both on real
bytes: `call` with operand `00 00 00 00` in `main.o` becomes `call 1146 <_Z6squarei>` in `app`.

## Linking libraries

```bash
g++ main.o util.o -o app                     # objects only
g++ main.o -L./lib -lgreet -o app            # library libgreet.so or libgreet.a from ./lib
g++ main.o -l:libgreet.a -o app              # this exact file name
g++ main.o ./lib/libgreet.a -o app           # an archive given by path, like an object
```

- `-lNAME` searches for `libNAME.so` and then `libNAME.a` in each directory: first every `-L`
  directory in order, then the system directories. In a directory that has both, the `.so` wins
  unless `-static` is given (checked with `-Wl,--trace` on binutils 2.46). See
  [GCC: Link Options](https://gcc.gnu.org/onlinedocs/gcc/Link-Options.html).
- `LD_LIBRARY_PATH` does **not** change where `-l` looks at link time. It is a run-time setting for
  the dynamic loader: [Static vs Dynamic Linking](./static-vs-dynamic-linking.md#how-the-loader-finds-libraries).
- `g++` (not `ld` or `gcc`) should drive the final link of C++ code: it adds `libstdc++`, `libm` and
  the C runtime start files automatically.

### Library order

The GNU linker reads inputs left to right and keeps a list of symbols still undefined. When it
reaches an **archive** (`.a`), it extracts only the members that define something on that list *at
that moment*. A library placed before the objects that need it contributes nothing:

<Tabs>
  <TabItem value="bad" label="Library first: fails">

```bash
g++ -L. -lutil um.o -o app
```

```text
/usr/bin/x86_64-linux-gnu-ld.bfd: um.o: in function `main':
um.cpp:(.text+0x9): undefined reference to `lib_fn()'
collect2: error: ld returned 1 exit status
```

  </TabItem>
  <TabItem value="good" label="Objects first: works">

```bash
g++ um.o -L. -lutil -o app
```

  </TabItem>
</Tabs>

Here `libutil.a` contains `l.o`, which defines `lib_fn()`.

Rule: **objects first, then libraries, each library before the libraries it depends on**. Two
archives that depend on each other need to be repeated (`-la -lb -la`) or grouped with
`-Wl,--start-group -la -lb -Wl,--end-group`. Build systems order the flags for you when you declare
dependencies between targets ([CMake: linking](../../cmake/02-targets/linking.md)).

## Reading linker errors

| Message | Meaning | Fix |
|---|---|---|
| `undefined reference to 'square(int)'` | A `U` symbol has no definition in any input | Add the `.cpp`/`.o` or `-l` that defines it; check library order; check the definition's signature matches the declaration (different parameter types mangle to a different name: [Name Mangling](./name-mangling.md#signature-mismatches)) |
| `undefined reference to 'int biggest<int>(int, int)'` | Template declared in a header, defined in a `.cpp` | Put the template definition in the header ([Translation Units](./translation-units.md#templates-and-inline-functions)) |
| `undefined reference to 'vtable for Widget'` | A class's first non-inline virtual function (the "key function") is declared but never defined | Define it, or every virtual function you declared |
| `multiple definition of 'global'; … first defined here` | Two strong definitions of one name | Define it once; `extern` in the header, or `inline` *(C++17)*: [ODR](./translation-units.md#the-one-definition-rule) |
| `relocation … can not be used when making a shared object; recompile with -fPIC` | Non-PIC object linked into a `.so` | Compile that object with `-fPIC` |
| `cannot find -lfoo` | No `libfoo.so`/`libfoo.a` on the search path | Add `-L dir`, or install the development package |

The real duplicate-definition message, from two files that each define `int global`:

```text
/usr/bin/x86_64-linux-gnu-ld.bfd: /tmp/ccmaT9So.o:(.data+0x0): multiple definition of `global'; /tmp/ccuSHkJ3.o:(.data+0x0): first defined here
collect2: error: ld returned 1 exit status
```

The `/tmp/cc….o` names appear because `g++ d1.cpp d2.cpp` compiled to temporary objects; link named
`.o` files to get readable messages.

## Weak symbols

A weak definition is a default that any strong definition replaces, without a duplicate-definition
error:

<Tabs>
  <TabItem value="lib" label="lib_default.cpp">

```cpp title="lib_default.cpp"
#include <cstdio>
__attribute__((weak)) void on_event() { std::puts("default handler"); }
void fire() { on_event(); }
```

  </TabItem>
  <TabItem value="ovr" label="app_override.cpp">

```cpp title="app_override.cpp"
#include <cstdio>
void fire();
void on_event() { std::puts("custom handler"); }
int main() { fire(); }
```

  </TabItem>
  <TabItem value="plain" label="app_plain.cpp">

```cpp title="app_plain.cpp"
void fire();
int main() { fire(); }
```

  </TabItem>
</Tabs>

```text
$ g++ lib_default.o app_override.o -o w1 && ./w1
custom handler
$ g++ lib_default.o app_plain.o -o w2 && ./w2
default handler
```

`__attribute__((weak))` is a GCC/Clang extension (ELF and Mach-O); MSVC has no direct equivalent.
Embedded startup code uses it heavily for overridable interrupt handlers. Weak symbols are also how
`inline` functions and template instantiations, emitted in many TUs, link without conflict: the
linker keeps one copy and discards the rest.

## Link-time optimisation

Normally the optimiser never sees across translation units, so a call to a function in another file
cannot be inlined. With `-flto`, the compiler writes its intermediate representation into the
object files and the optimiser runs again at link time on the whole program:

<Tabs>
  <TabItem value="no" label="g++ -O2">

```nasm
<main>:
	endbr64
	mov    edi,0x3
	jmp    1140 <_Z6squarei>      # call into the other TU
```

  </TabItem>
  <TabItem value="lto" label="g++ -O2 -flto">

```nasm
<main>:
	endbr64
	mov    eax,0x9                # square(3) inlined and folded
	ret
```

  </TabItem>
</Tabs>

Pass `-flto` both when compiling and when linking. The gain depends on the program and has to be
measured; the cost is a slower, more memory-hungry link. In CMake, set
`INTERPROCEDURAL_OPTIMIZATION` on the target instead of adding flags by hand.

## Seeing what the linker did

```bash
g++ main.o -L. -lgreet -Wl,--trace -o app        # which files were opened
g++ main.o -L. -lgreet -Wl,-Map=app.map -o app   # map file: every section and symbol address
g++ -v main.o -o app                              # the full collect2/ld command line
readelf -d app | grep NEEDED                      # shared libraries the result depends on
```

A map file is the authoritative answer to "where did this symbol end up, and which input provided
it". Embedded projects use it with a custom **linker script** (`-T file.ld`) that places sections at
fixed memory addresses; see [The Linker Script](../../../embedded/03-toolchain-and-build/the-linker-script.md).

## Pitfalls

- **Fixing `undefined reference` in the calling code.** The caller compiled fine. The problem is in
  what you link, or a signature that differs between the declaration and the definition.
- **Linking C++ objects with `gcc` or `ld` directly.** You get undefined references to `std::`
  internals because `libstdc++` is missing. Link with `g++`.
- **Silencing `multiple definition` with `-Wl,--allow-multiple-definition` or `-fcommon`.** The
  linker then picks one definition arbitrarily; the other file's code reads a variable it did not
  initialise. Fix the definition instead.
- **Expecting `LD_LIBRARY_PATH` to fix `cannot find -lfoo`.** That is a link-time error; use `-L`.

## Key points

- The linker resolves every undefined symbol to one definition, then patches the relocations.
- Order on the command line matters for archives: objects first, then libraries in dependency order.
- `undefined reference` and `multiple definition` are linker messages; the fix is in what is linked
  or in the One Definition Rule, not in the call site.
- `-flto` lets the optimiser cross translation-unit boundaries; measure before relying on it.
