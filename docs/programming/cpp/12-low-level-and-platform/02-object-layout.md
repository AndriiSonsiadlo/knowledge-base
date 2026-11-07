---
id: object-layout
title: Object Layout and Memory Structure
sidebar_label: Object Layout
sidebar_position: 2
tags: [cpp, object-layout, abi, itanium, msvc, vtable, vptr, ebo]
---

# Object Layout and Memory Structure

[Class layout](../07-classes-and-oop/class-layout.md) explains what a class object contains: members
in declaration order, base subobjects, a vptr when the class is polymorphic, padding. This page goes
one level down. It shows where the Itanium C++ ABI and the Microsoft ABI put those pieces, what is in a
vtable, how virtual bases are found, and where the two ABIs produce different sizes. It is for
readers who must predict `sizeof` and member offsets across compilers, read a debugger's raw memory
view, or write code that depends on a binary layout.

**Prerequisites:** [Class layout](../07-classes-and-oop/class-layout.md),
[virtual functions](../07-classes-and-oop/virtual-functions.md),
[multiple inheritance](../07-classes-and-oop/multiple-inheritance.md) and the
[ABI](./01-abi.md) overview.

:::info[What was measured]
Itanium ABI results come from g++ 15.2 (`-fdump-lang-class`) and clang++ 21.1
(`-Xclang -fdump-record-layouts`) on x86-64 Linux, and agree between the two. "MSVC layout" results
come from **Clang's MSVC-compatible layout engine** (`--target=x86_64-pc-windows-msvc`), not from
`cl.exe`. Microsoft does not publish the record-layout rules, so treat those numbers as indicative and
confirm with `cl /d1reportAllClassLayout` before relying on them.
:::

## Ask the compiler

```bash
g++ -std=c++20 -fdump-lang-class -c file.cpp                  # writes file.cpp.*.class (also vtables)
clang++ -std=c++20 -Xclang -fdump-record-layouts -c file.cpp  # prints layouts to stdout
clang++ --target=x86_64-pc-windows-msvc -Xclang -fdump-record-layouts -c file.cpp   # MSVC-style rules
cl /d1reportAllClassLayout file.cpp                           # MSVC; undocumented flag
```

Every number below was read from one of these dumps, then confirmed with `sizeof` and pointer
arithmetic in a program.

## The vptr and the vtable (Itanium)

In the Itanium ABI a polymorphic class's **primary base** (the first non-virtual polymorphic base) shares its
vptr with the derived class, and the vptr sits at offset 0. The vptr does not point to the start of the
vtable but to the first virtual-function slot, after a small header.

```cpp title="two-bases.cpp" showLineNumbers
struct A { virtual void fa(); int a; };
struct B { virtual void fb(); int b; };
struct C : A, B { int c; };
```

For `C`, g++ reports this vtable (`Vtable for C`, 6 entries):

| Offset | Entry | Meaning |
|---|---|---|
| 0 | `0` | offset-to-top for the `A`/`C` subobject: how far this subobject is from the start of the complete `C` |
| 8 | `&typeinfo for C` | RTTI pointer |
| 16 | `A::fa` | slot used through the `A`-in-`C` vptr (which points here) |
| 24 | `-16` | offset-to-top for the `B` subobject |
| 32 | `&typeinfo for C` | RTTI pointer |
| 40 | `B::fb` | slot used through the `B`-in-`C` vptr |

The offset-to-top entry is what `dynamic_cast<void*>` (and `dynamic_cast` to the most-derived type) uses to find the start of the whole object. When `fb` is overridden in `C`, the second table holds a
small **thunk** instead of `C::fb` directly, which subtracts 16 from `this` before jumping, because
`C::fb` expects a `C*`, not a `B*`.

`sizeof(C)` is 32 and the `B` subobject (with its own vptr) sits at offset 16, so a `B*` into a `C` points 16 bytes in. The pointer-adjustment demo with the diagram is on [Class layout](../07-classes-and-oop/class-layout.md#base-classes-are-subobjects). Here the same numbers were confirmed with both compilers' layout dumps and with a program (g++ 15 and clang++ 21, `-O0` and `-O2`, x86-64 Linux).

### Microsoft ABI

MSVC calls its tables **vftables** and finds virtual bases through a separate **vbtable**. For the same `A`, `B`, `C`,
Clang's MSVC layout puts `A` at offset 0 and `B` at 16, the same as Itanium, but `c` at offset 32 and
`sizeof(C)` at 40, against 28 and 32. `B` has 4 bytes of tail padding and Itanium puts `c` inside it, while
the MSVC layout starts `c` after `B`. This is one case of the general tail-padding difference in
the next section.

## Tail padding of a base

Padding at the end of a base class is a layout choice the two ABIs make differently. In the Itanium ABI,
if the base is not a **POD for the purpose of layout** (the ABI's definition, taken from C++03: roughly,
it has a user-provided constructor, destructor, copy operation, a virtual function, or a non-POD member), a derived class may
place its own members inside the base's tail padding. If the base is POD the tail padding is reserved
and the derived members start after it.

```cpp title="tail-padding.cpp" showLineNumbers
struct PodBase    { int i; char c; };                 // POD:     sizeof 8, 3 bytes tail padding
struct NonPodBase { int i; char c; NonPodBase() {} }; // non-POD: sizeof 8

struct D1 : PodBase    { char d; };   // d goes after the padding
struct D2 : NonPodBase { char d; };   // d fits in the padding on Itanium
```

| | Itanium (g++ 15, clang++ 21, x86-64 Linux; AArch64 Linux Clang agrees) | MSVC layout (Clang, x86-64) |
|---|---|---|
| `sizeof(D1)`, `d` at | 12, offset 8 | 12, offset 8 |
| `sizeof(D2)`, `d` at | 8, offset 5 | 12, offset 8 |

Both Itanium numbers (12 and 8) were also printed by a program under both compilers at `-O0` and `-O2`. The
consequence is that you cannot compute a derived class's size from the `sizeof` of its base: `sizeof(D2)`
equals `sizeof(NonPodBase)` here. It also means that a bytewise copy of a base-class subobject can overwrite a derived member sitting in that padding. This is one reason the standard excludes potentially-overlapping subobjects (bases, `[[no_unique_address]]` members) from the `memcpy` guarantee, even for trivially copyable types.

## Empty base optimization across ABIs

The [class layout](../07-classes-and-oop/class-layout.md#empty-classes-and-the-empty-base-optimization)
page states EBO and `[[no_unique_address]]`. The ABI-level rule is the constraint behind it: two
subobjects of the **same type** must not share an address, because their addresses identify the objects.
So an empty base is placed at offset 0 only if no other subobject of that type is already there.

```cpp title="nua.cpp" showLineNumbers
#include <cstdio>
struct E1 {}; struct E2 {};
struct Same : E1 { [[no_unique_address]] E1 e; char v; };   // e cannot overlap the E1 base
struct Diff : E1 { [[no_unique_address]] E2 e; char v; };   // different type: may overlap
struct Two  { [[no_unique_address]] E1 a; [[no_unique_address]] E1 b; char v; };
int main() { std::printf("%zu %zu %zu\n", sizeof(Same), sizeof(Diff), sizeof(Two)); }
```

```text
2 1 2
```

g++ 15 and clang++ 21, `-std=c++20`, `-O0` and `-O2`, x86-64 Linux. `Diff` has size 1 because the empty
base, the empty member and `v` all fit in one byte; in `Same` and `Two` one of the empty objects is pushed to
offset 1. A plain empty member without the attribute always takes a byte. MSVC does not honour the standard
`[[no_unique_address]]` and spells it `[[msvc::no_unique_address]]`, as noted on the class layout page.

## Virtual bases

A virtual base is shared by every path to it, so its position inside the complete object cannot be fixed
by the intermediate classes. Each class that has a virtual base stores whatever is needed to find it at run time.

```cpp title="diamond.cpp" showLineNumbers
struct VB  { int vb; };
struct L   : virtual VB { int l; };
struct R   : virtual VB { int r; };
struct Bot : L, R { int bot; };
```

**Itanium.** `Bot` is 40 bytes: `L` at 0 (vptr, then `l` at 8), `R` at 16 (vptr, then `r` at 24), `bot` at
28, and the shared `VB` at 32 — virtual bases go after all non-virtual parts. The distance to `VB` is not a compile-time
constant for a `L*` pointing into some unknown most-derived object, so it is stored in the vtable as a
**vbase offset** in the header, before the offset-to-top entry. g++'s dump of `Bot`'s vtable begins `32, 0, &typeinfo for Bot` for the
`L`/`Bot` vptr and `16, -16, &typeinfo for Bot` for `R`'s: the `VB` is 32 bytes from `Bot` and 16 bytes from
the `R` subobject. Reaching `VB` from an `L*` is therefore: load vptr, load the vbase offset below it, add.

**Microsoft.** A class with a virtual base but no virtual
functions gets a **vbtable pointer** at offset 0 instead of a vptr, and the vbtable lists the offsets to
virtual bases. Clang's MSVC layout of the same `Bot` has `L` at 0 (vbtable pointer, `l` at 8), `R` at 16,
`bot` at 32, `VB` at 40, and `sizeof` 48.

<Diagram title="struct Bot with virtual base VB, x86-64" caption="Sizes: 40 bytes (Itanium, g++/clang++) and 48 bytes (MSVC layout as computed by Clang)." accent="amber">
  <DiagramGroup label="Itanium">
    <DiagramRow>
      <DiagramNode title="L">vptr @0, l @8</DiagramNode>
      <DiagramNode title="R">vptr @16, r @24</DiagramNode>
      <DiagramNode title="bot">@28</DiagramNode>
      <DiagramNode title="VB" accent>@32 (virtual base)</DiagramNode>
    </DiagramRow>
  </DiagramGroup>
  <DiagramGroup label="MSVC layout">
    <DiagramRow>
      <DiagramNode title="L">vbptr @0, l @8</DiagramNode>
      <DiagramNode title="R">vbptr @16, r @24</DiagramNode>
      <DiagramNode title="bot">@32</DiagramNode>
      <DiagramNode title="VB" accent>@40 (virtual base)</DiagramNode>
    </DiagramRow>
  </DiagramGroup>
</Diagram>

Because the virtual base is found indirectly, reaching it costs extra loads that a direct base does not. The practical advice on whether to use them is on
[Multiple inheritance](../07-classes-and-oop/multiple-inheritance.md).

The Itanium ABI additionally builds **construction vtables** and a **VTT** (virtual table table)
so that, while `Bot`'s constructor is running `L`'s constructor, `L`'s virtual calls and base lookups
behave as if the object were just an `L`. g++'s dump lists `Construction vtable for L ... in Bot`
and a 4-entry `VTT for Bot`.

## What the standard does and does not promise

Only a [standard-layout](../07-classes-and-oop/class-layout.md#standard-layout-classes) class has a
layout you may depend on at the language level: members in declaration order with increasing addresses,
the first member at the object's address, and compatibility with the C struct of the same members.
Everything on this page about vptrs, vtable contents, thunks and where a non-POD base's padding goes is
an ABI fact, not a language fact. It is stable for a given platform, and
it is what debuggers, `dynamic_cast` implementations and shared libraries rely on, so you can use
it when reading memory or when writing a plug-in interface. Do not derive portable code from it.

:::warning
Hand-calling virtual functions through a vtable pointer, or overwriting a vptr, is undefined behaviour in
C++. COM on Windows and a few C-style "vtable" interfaces use a *defined* layout deliberately, as a
struct of function pointers, not by reaching into the compiler's.
:::

## Key points

- Itanium ABI: vptr at offset 0 shared with the primary base; one extra vptr per further polymorphic
  base; vtable header holds vbase offsets, offset-to-top and the RTTI pointer; `C*` to `B*` adjusts the address.
- A derived class may reuse the tail padding of a non-POD base on Itanium (`sizeof(D2) == 8`) but not of a POD
  base (`sizeof(D1) == 12`). Clang's MSVC layout reserves the padding in both cases.
- Two empty subobjects of the same type cannot overlap, so EBO and `[[no_unique_address]]` sometimes still cost a byte.
- Virtual bases come last in the Itanium layout and are located through the vtable; MSVC uses a vbtable.
- Treat all of this as per-ABI fact. Check it with the compiler's layout dump, and pin what you rely on
  with `static_assert`.

## References

- [Itanium C++ ABI: Virtual Table Layout, Class Layout](https://itanium-cxx-abi.github.io/cxx-abi/abi.html#vtable)
- [cppreference: empty base optimization](https://en.cppreference.com/w/cpp/language/ebo)
- [cppreference: `[[no_unique_address]]`](https://en.cppreference.com/w/cpp/language/attributes/no_unique_address)
