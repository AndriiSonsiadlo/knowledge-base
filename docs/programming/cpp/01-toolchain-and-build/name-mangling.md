---
id: name-mangling
title: Name Mangling
sidebar_label: Name Mangling
sidebar_position: 8
tags: [c++, name-mangling, abi, linking, symbols]
---

# Name Mangling

The linker matches symbols by plain string. C++ allows many entities with the same name: overloads
(`print(int)` and `print(double)`), the same name in different namespaces and classes, template
instantiations. **Name mangling** is how the compiler gives each of them a unique linker name, by
encoding the scope and the parameter types into the symbol. It is invisible until a link fails,
and then the mangled name in the message is usually the clue.

**Prerequisites:** [Object Files and Symbols](./object-files-and-symbols.md).

## Mangled names in practice

```bash
nm main.o            # raw:        U _Z6squarei
nm -C main.o         # demangled:  U square(int)
c++filt _Z4funcPKc   # one name:   func(char const*)
```

GCC and Clang on Linux, macOS and most other non-Windows platforms use the scheme from the
[Itanium C++ ABI](https://itanium-cxx-abi.github.io/cxx-abi/abi.html#mangling). Every name below was
produced by compiling the declarations with GCC 15 and reading `nm`.

## Reading an Itanium name

<Diagram title="_ZN4math6Vector9normalizeEv" caption="Nested name between N and E, each component prefixed by its length; then the parameter types." accent="violet">
  <DiagramRow>
    <DiagramNode title="_Z">C++ symbol prefix</DiagramNode>
    <DiagramNode title="N … E">Nested (qualified) name</DiagramNode>
    <DiagramNode title="4math 6Vector 9normalize" accent>Length + identifier, outermost first</DiagramNode>
    <DiagramNode title="v">Parameter list: `void` = no parameters</DiagramNode>
  </DiagramRow>
</Diagram>

The function's **return type is not encoded** for ordinary functions, only the parameters. That is
why two functions that differ only in return type cannot be overloaded: they would get the same
symbol.

### Parameter types

| Declaration | Symbol | Codes |
|---|---|---|
| `void func(int)` | `_Z4funci` | `i` int |
| `void func(char)` | `_Z4funcc` | `c` char |
| `void func(bool)` | `_Z4funcb` | `b` bool |
| `void func(float)` | `_Z4funcf` | `f` float |
| `void func(double)` | `_Z4funcd` | `d` double |
| `void process(long)` | `_Z7processl` | `l` long |
| `void func(void*)` | `_Z4funcPv` | `P` pointer to, `v` void |
| `void func(int*)` | `_Z4funcPi` | |
| `void func(int**)` | `_Z4funcPPi` | |
| `void func(const int*)` | `_Z4funcPKi` | `K` const |
| `void func(int&)` | `_Z4funcRi` | `R` lvalue reference (`O` is rvalue reference) |
| `void calculate(int, double)` | `_Z9calculateid` | parameters in order |

### Members, constructors, templates

| Declaration | Symbol | Notes |
|---|---|---|
| `void Widget::setValue(int)` | `_ZN6Widget8setValueEi` | |
| `int Widget::getValue() const` | `_ZNK6Widget8getValueEv` | `K` after `N`: const member function |
| `static void Widget::reset()` | `_ZN6Widget5resetEv` | Same form as a non-static member: `static` is not encoded |
| `Widget::Widget()` | `_ZN6WidgetC1Ev`, `_ZN6WidgetC2Ev` | `C1` complete-object, `C2` base-object constructor; both are emitted |
| `Widget::~Widget()` | `_ZN6WidgetD1Ev`, `_ZN6WidgetD2Ev` | `D0` (deleting) also appears for virtual destructors |
| `template void sort<int>(int*, int)` | `_Z4sortIiEvPT_i` | `IiE` template arguments; for templates the return type `v` **is** encoded; `T_` refers back to the first template parameter |
| `extern "C" void c_style_function(int)` | `c_style_function` | No mangling at all |

### MSVC is different

MSVC uses its own scheme: `void func(int, double)` becomes `?func@@YAXHN@Z`. Objects from MSVC and
from GCC/MinGW therefore cannot be linked together even for the same source, which is one reason
C++ libraries are distributed per compiler. Mangling is one part of the wider
[ABI](../12-low-level-and-platform/01-abi.md), along with object layout, vtables and calling
conventions.

## `extern "C"`: switching mangling off

C has no overloading, so C compilers emit the plain name. To call C from C++, or to make a C++
function callable from C, `dlsym` or another language, declare it `extern "C"`:

```cpp title="api.h"
#ifdef __cplusplus
extern "C" {
#endif

void api_function(int x);    // symbol: api_function

#ifdef __cplusplus
}
#endif
```

`__cplusplus` is defined only by C++ compilers, so the same header works from both languages. An
`extern "C"` function cannot be overloaded, because two of them would have the same symbol. The
full interop rules are on [C Interoperability](../12-low-level-and-platform/07-interop-c.md).

## Signature mismatches

The most common mangling-related bug: the header and the definition disagree on a parameter type.
Both files compile; the link fails, and the error names the signature the *caller* expected.

```cpp title="fragment: three files"
// calc.h
void calculate(int a, int b);

// calc.cpp: the definition takes a double by mistake
void calculate(int a, double b) { /* ... */ }    // defines _Z9calculateid

// main.cpp
#include "calc.h"
int main() { calculate(5, 10); }                 // needs   _Z9calculateii
```

```text
undefined reference to `calculate(int, int)'
```

Diagnose it by comparing what is needed against what is defined:

```bash
nm -C main.o | grep calculate     #   U calculate(int, int)
nm -C calc.o | grep calculate     # T   calculate(int, double)
```

The same mismatch happens without a typo when a library is rebuilt with a different signature
(`int` changed to `long`), or with a different standard library ABI: GCC's `std::string` mangles
as `std::__cxx11::basic_string<…>` since GCC 5, so objects built with
`-D_GLIBCXX_USE_CXX11_ABI=0` do not link with ones built without it.

## Demangling at run time

`typeid(T).name()` returns the mangled type name on GCC and Clang. The ABI library provides
`abi::__cxa_demangle` to decode it:

```cpp title="demangle.cpp"
#include <cxxabi.h>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <string>
#include <typeinfo>
#include <vector>

std::string demangle(const char* name) {
    int status = 0;
    std::unique_ptr<char, void (*)(void*)> result(
        abi::__cxa_demangle(name, nullptr, nullptr, &status), std::free);
    return status == 0 ? result.get() : name;
}

int main() {
    const char* raw = typeid(std::vector<int>).name();
    std::cout << raw << '\n' << demangle(raw) << '\n';
}
```

```text
St6vectorIiSaIiEE
std::vector<int, std::allocator<int> >
```

`<cxxabi.h>` is a GCC/Clang header, not standard C++; MSVC's `name()` already returns a readable
string.

## Pitfalls

- **Declaring a C library's functions without `extern "C"`.** The C++ caller looks for `_Z…`, the
  library has the plain name: `undefined reference`. Well-behaved C headers include the
  `__cplusplus` guard; for ones that don't, wrap the `#include` in `extern "C" { }`.
- **Overloading on return type, or on `static`.** Neither is part of the symbol; the compiler
  rejects it before mangling would collide.
- **Mixing compilers or standard-library ABIs** in one link. The symbols simply don't match.

## Key points

- Mangling encodes scope and parameter types (not the return type) into a unique linker name.
- `nm -C` and `c++filt` decode it; compare needed (`U`) against defined (`T`) to find mismatches.
- `extern "C"` disables mangling for C interop and `dlsym`, at the cost of overloading.
- Itanium (GCC/Clang) and MSVC schemes differ, so their objects don't link together.
