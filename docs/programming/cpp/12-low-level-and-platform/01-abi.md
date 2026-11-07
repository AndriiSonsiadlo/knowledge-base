---
id: abi
title: Application Binary Interface (ABI)
sidebar_label: ABI
sidebar_position: 1
tags: [cpp, abi, binary-compatibility, itanium, msvc, linking]
---

# Application Binary Interface (ABI)

The C++ standard defines what a program means, not what bytes the compiler emits. The **ABI** (application
binary interface) is the other half of the contract: the rules that let separately compiled code, built
by different runs of the compiler or even different compilers, work together. If the caller and the
callee disagree about any of them, the program still links and then misbehaves. This page names those rules,
shows which source changes break them, and lists the techniques libraries use to keep them stable.

**Prerequisites:** [Translation units](../01-toolchain-and-build/translation-units.md) and
[linking](../01-toolchain-and-build/linking.md).

:::info[API versus ABI]
An **API** is a source-level contract: names, types and signatures in a header. An **ABI** is the
binary-level contract of the compiled code. A change can keep the API intact and still break the ABI,
which means every client has to be recompiled.
:::

## What an ABI fixes

The standard leaves all of these to the implementation. A C++ ABI document pins them down for one
platform:

| Area | Decided by the ABI | Where this site covers it |
|---|---|---|
| Sizes and alignments of fundamental types | `long` is 8 bytes on x86-64 Linux, 4 on Windows x64 | [Alignment](../05-memory-and-object-lifetime/alignment.md) |
| Class layout | Member offsets, base subobjects, the vptr, virtual-base placement | [Class layout](../07-classes-and-oop/class-layout.md), [Object layout](./02-object-layout.md) |
| Vtable layout | Slot order, offset-to-top, RTTI pointer, thunks | [Object layout](./02-object-layout.md) |
| Calling convention | Argument and result registers, stack, callee-saved registers | [Calling conventions](../04-functions-and-call-mechanics/calling-conventions.md) |
| Name mangling | How a signature becomes a symbol | [Name mangling](../01-toolchain-and-build/name-mangling.md) |
| Exception handling | Unwind tables, how a thrown object is allocated and matched | Itanium ABI, "Exception Handling" chapter |
| Runtime type information | `type_info` layout and naming | Itanium ABI |
| Standard-library types | Layout of `std::string`, `std::vector`, ... | Library vendor (see [below](#library-abis)) |

An ABI is split by **platform** (the instruction set plus OS conventions) and by **C++ flavour**.
The two C++ families you meet are:

| Family | Document | Typical toolchains |
|---|---|---|
| **Itanium C++ ABI** | [itanium-cxx-abi.github.io](https://itanium-cxx-abi.github.io/cxx-abi/abi.html), together with a per-architecture psABI for calling convention | GCC and Clang on Linux, macOS, Android, the BSDs, and MinGW (GCC and Clang targeting Windows) |
| **Microsoft C++ ABI** | Not published as one specification. Microsoft documents parts of it, for example the [x64 calling convention](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention) and [ARM64 conventions](https://learn.microsoft.com/en-us/cpp/build/arm64-windows-abi-conventions) | MSVC, and Clang when targeting `*-windows-msvc` |

The Itanium C++ ABI was written for the Itanium processor but is used on x86-64 and AArch64 with
the architecture's own calling convention plugged in. So "Itanium ABI on x86-64 Linux" and
"Itanium ABI on AArch64 Linux" share layout and mangling rules and differ in registers.

## Why the same source can mean different binaries

Because every item in the table is a platform decision, one source file compiled for two targets gives
different layouts. The numbers below come from Clang 21's record-layout dump (`-Xclang
-fdump-record-layouts`) for an `x86_64` target, once for the Itanium ABI and once with
`--target=x86_64-pc-windows-msvc`. The MSVC column is **Clang's implementation of the MSVC layout rules**, not
output from `cl.exe`, so treat it as indicative:

```cpp title="layouts.cpp (fragment)"
struct A { virtual void fa(); int a; };
struct B { virtual void fb(); int b; };
struct C : A, B { int c; };

struct NonPodBase { int i; char c; NonPodBase() {} };
struct D : NonPodBase { char d; };
```

| Type | Itanium, x86-64 Linux | MSVC layout, x86-64 (Clang) |
|---|---|---|
| `sizeof(C)` | 32 (`int c` at offset 28) | 40 (`int c` at offset 32) |
| `sizeof(D)` | 8 (`d` at offset 5, inside the base's tail padding) | 12 (`d` at offset 8) |

The first difference is tail padding. The Itanium ABI lets a derived class's members reuse the tail
padding of a non-POD base, where "POD" has the C++03 meaning that the ABI still uses. MSVC does not.
Layout details are on [Object layout](./02-object-layout.md).

## What breaks the ABI

An ABI break is any change after which previously compiled clients and the new library disagree on
one of the items above. The following experiment shows the most common one.

```cpp title="v1: the library as shipped"
// widget.h  (v1)
struct Widget { int value; };
int get_value(const Widget* w);          // defined in the .so: return w->value;
```

```cpp title="v2: the client is rebuilt against a header with a new member, the .so is not"
// widget.h  (v2)
struct Widget { int id; int value; };    // new member BEFORE value: offset of value changes 0 -> 4

// main.cpp
Widget w{7, 42};
std::printf("%d\n", get_value(&w));      // library code still reads offset 0
```

Built as a shared library from the v1 header and a client from the v2 header, this printed `7` with g++ 15 and
clang++ 21, at `-O0` and `-O2`, on x86-64 Linux. The standard calls it an ODR violation, so the
result is undefined. What happened is what the offset arithmetic predicts: the old library reads
the bytes where `value` used to be. Nothing was diagnosed by the compiler, the linker or the
dynamic loader.

Changes that commonly break an Itanium-ABI binary interface (for clients compiled against the old header):

| Change | Why it breaks clients |
|---|---|
| Add, remove or reorder non-static data members | Offsets and `sizeof` change |
| Add, remove or reorder virtual functions | Vtable slots move. Calls through the old slot number reach the wrong function |
| Change the base classes, or make a base virtual | Subobject offsets and the vtable change |
| Change a function's parameter types | The mangled name changes, so old clients fail to link. With `extern "C"` there is no such check and the call is simply wrong |
| Add a default argument value | Default arguments are inlined at call sites, so old clients keep the old value (no link error) |
| Change an inline function's body | Old clients keep the old inlined copy |
| Change a type's trivial-ness, for example adding a destructor | Can change how the type is passed or returned. On Itanium, a class with a non-trivial copy constructor or destructor is passed by invisible reference rather than in registers |

Adding a new non-virtual member function or a new free function is binary compatible, because it only
adds symbols. Adding a data member is compatible only if no client can see the object's `sizeof`:
that is, the object is always created by the library and handled by pointer.

## Keeping a library's ABI stable

### Opaque types

If clients only ever hold a pointer to a type whose definition they cannot see, the library may change
the definition freely. The pointer-to-implementation idiom is the C++ form of this and is on
[Pimpl](../13-idioms-and-design/02-pimpl.md). The C form, an opaque handle, is on
[Interop with C](./07-interop-c.md).

### Symbol versioning (GNU ld, ELF)

A library can export several implementations under one name, each tagged with a version node.
Clients record the version they were linked against. This is a GNU toolchain feature for ELF shared
objects, written with `.symver` directives and a linker version script:

```cpp title="v.cpp" showLineNumbers
extern "C" {                              // the labels in .symver must be unmangled
int func_v1() { return 1; }
int func_v2() { return 2; }
}
__asm__(".symver func_v1, func@VER_1.0");   // old, non-default version
__asm__(".symver func_v2, func@@VER_2.0");  // @@ marks the default for new links
```

```text title="v.map"
VER_1.0 { global: func; local: *; };
VER_2.0 { global: func; } VER_1.0;
```

```bash
g++ -shared -fPIC v.cpp -Wl,--version-script=v.map -o libv.so
nm -D libv.so | grep func
```

```text
00000000000010f9 T func@VER_1.0
0000000000001108 T func@@VER_2.0
```

Built with g++ 15 and clang++ 21 on x86-64 Linux (addresses differ between them). A C client linked
against this library binds to `func@@VER_2.0` and printed `2`; a client built earlier against the
first version keeps binding to `func@VER_1.0`. This is the mechanism glibc uses for its own
compatibility. The `extern "C"` matters: without it the labels in the `.symver` lines do not match the mangled
names, and the assembler reports an error.

### Soname and inline namespaces

For a break you cannot avoid, bump the shared-library soname (see
[static vs dynamic linking](../01-toolchain-and-build/static-vs-dynamic-linking.md)) so old programs
keep loading the old library. Inside C++, an **inline namespace** *(C++11)* puts the new version's
names under a different mangled prefix while source code still writes the unqualified name. libstdc++
uses `std::__cxx11` this way.

## Library ABIs

The standard library is part of the ABI, because `std::string` and `std::vector` appear in
signatures and layouts.

- **libstdc++** (GCC) has a *dual ABI*. Since GCC 5, `std::string` and `std::list` are defined in the inline
  namespace `std::__cxx11` to satisfy the C++11 requirements. Defining
  `_GLIBCXX_USE_CXX11_ABI=0` selects the older definitions, with different mangled names.
  Compiling the same function with each setting on GCC 15 gave `_Z4takeNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE`
  and `_Z4takeSs`, so objects built with different settings fail to link, or mis-link, when `std::string` crosses
  the boundary. See the
  [libstdc++ manual](https://gcc.gnu.org/onlinedocs/libstdc++/manual/using_dual_abi.html).
- **libc++** (LLVM) and **libstdc++** are different libraries with different layouts. Mixing them in
  one program, for instance a Clang `-stdlib=libc++` executable with a GCC-built library that exports
  `std::string`, does not work.
- **MSVC STL**: Microsoft documents that the `v140` to `v143` toolsets (Visual Studio 2015 through 2022) and later
  minor updates keep binary compatibility, with restrictions, and that versions up to Visual Studio
  2013 do not. See [C++ binary compatibility between Visual Studio versions](https://learn.microsoft.com/en-us/cpp/porting/binary-compat-2015-2017).
  Debug and release builds, and the static versus DLL runtime (`/MT` against `/MD`), still need to match
  across a boundary that passes standard-library objects, because they define different layouts and
  separate heaps.

## Rules for a boundary you want to keep stable

1. **Pass only types whose layout you control and fix.** Fundamental types of fixed width
   (`std::int32_t`), pointers to opaque types, and standard-layout structs you have pinned with
   `static_assert` on `sizeof` and `offsetof` (see [Padding and offsetof](./03-padding-and-offsetof.md)).
2. **Keep standard-library types out of exported signatures**, or accept that client and library must use
   the same standard library, version and settings.
3. **Do not let exceptions cross it** unless both sides use the same toolchain and runtime. Exception
   propagation is ABI-defined, and the standard does not promise it works between modules. Across a C
   interface they must not cross at all, see [Interop with C](./07-interop-c.md).
4. **Allocate and free on the same side.** Memory from `new` in one module must be released by the
   `delete` of the same runtime. With separate runtimes (for example two MSVC DLLs linked with `/MT`) each
   has its own heap.
5. **Control what is exported.** On ELF, `-fvisibility=hidden` plus an export macro; on Windows,
   `__declspec(dllexport)`/`dllimport` ([Microsoft docs](https://learn.microsoft.com/en-us/cpp/cpp/dllexport-dllimport)).
   An exported inline function or class becomes part of the ABI whether you meant it or not.

## Inspecting an ABI

| Tool | Use |
|---|---|
| `nm -C -D lib.so` | Exported symbols, demangled |
| `readelf -d lib.so \| grep SONAME` | The soname clients record |
| `g++ -fdump-lang-class`, `clang++ -Xclang -fdump-record-layouts` | Class layout as the compiler computed it |
| [`abidiff`](https://sourceware.org/libabigail/manual/abidiff.html) (libabigail) | Compares two builds of a library and reports ABI-relevant differences. Not run for this page |
| `static_assert(sizeof(T) == N && offsetof(...) == ...)` | Fails the build when a layout you promised changes |

## Key points

- An ABI is the binary contract: type sizes, class and vtable layout, calling convention, name mangling,
  exceptions and RTTI. The C++ standard specifies none of it.
- Two C++ families matter: Itanium (GCC, Clang on Linux, macOS, Android, MinGW) and Microsoft (MSVC). Within a
  family, the processor architecture still fixes registers.
- Adding or reordering data members or virtual functions, or changing a base class, breaks previously compiled clients silently.
- Keep a stable boundary opaque, fixed-width, standard-library-free and exception-free; use symbol
  versioning or a soname bump when you must break it.

## References

- [Itanium C++ ABI](https://itanium-cxx-abi.github.io/cxx-abi/abi.html)
- [libstdc++: dual ABI](https://gcc.gnu.org/onlinedocs/libstdc++/manual/using_dual_abi.html)
- [Microsoft: C++ binary compatibility between Visual Studio versions](https://learn.microsoft.com/en-us/cpp/porting/binary-compat-2015-2017)
- [Microsoft: x64 calling convention](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention)
