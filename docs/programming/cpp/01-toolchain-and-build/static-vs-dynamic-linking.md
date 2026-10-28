---
id: static-vs-dynamic-linking
title: Static vs Dynamic Linking
sidebar_label: Static vs Dynamic
sidebar_position: 6
tags: [c++, linking, static, dynamic, shared-libraries]
---

# Static vs Dynamic Linking

A library can reach your program in two ways. With **static linking**, the linker copies the needed
object files out of an archive (`.a`) into the executable, and the library is no longer needed. With
**dynamic linking**, the executable only records the library's name; the **dynamic loader**
(`ld-linux-x86-64.so.2` on x86-64 Linux) finds the shared library (`.so`) and maps it into the
process every time the program starts. The choice decides what you ship, what can be updated
independently, and what can fail at start-up.

**Prerequisites:** [Linking](./linking.md), [Object Files and Symbols](./object-files-and-symbols.md).

<Diagram title="Where the library code ends up" accent="green">
  <DiagramGroup label="Static (.a)">
    <DiagramNode icon="package" title="libgreet.a">Archive of .o files</DiagramNode>
    <DiagramNode icon="cpu" title="app">Contains greet() itself</DiagramNode>
  </DiagramGroup>
  <DiagramGroup label="Dynamic (.so)">
    <DiagramNode icon="cpu" title="app">Contains `NEEDED libgreet.so`</DiagramNode>
    <DiagramNode icon="server" title="ld-linux.so" accent>Finds and maps the .so at every start</DiagramNode>
    <DiagramNode icon="package" title="libgreet.so">Shared by every process using it</DiagramNode>
  </DiagramGroup>
</Diagram>

## One library, both ways

```cpp title="greet.cpp"
#include <string>
std::string greet(const std::string& who) { return "Hello, " + who; }
```

```cpp title="main.cpp"
#include <iostream>
#include <string>
std::string greet(const std::string& who);
int main() { std::cout << greet("linker") << '\n'; }
```

<Tabs groupId="link">
  <TabItem value="static" label="Static library">

```bash
g++ -std=c++23 -O2 -c greet.cpp -o greet.o
ar rcs libgreet.a greet.o
g++ -std=c++23 -O2 main.cpp -L. -l:libgreet.a -o app_static_lib
./app_static_lib
```

```text
Hello, linker
```

`app_static_lib` runs from any directory: `greet()` is inside it. `libstdc++` and `libc` are still
linked dynamically, because only `libgreet` was named as an archive.

  </TabItem>
  <TabItem value="shared" label="Shared library">

```bash
g++ -std=c++23 -O2 -fPIC -shared greet.cpp -o libgreet.so
g++ -std=c++23 -O2 main.cpp -L. -lgreet -o app_shared
./app_shared
```

```text
./app_shared: error while loading shared libraries: libgreet.so: cannot open shared object file: No such file or directory
```

The link succeeded (`-L.` told `ld` where to look), but the loader does not search `.` at run time.
The next section fixes this.

  </TabItem>
</Tabs>

Sizes from that run (GCC 15, `-O2`, not stripped):

| File | Bytes |
|---|---|
| `libgreet.a` | 4,216 |
| `libgreet.so` | 16,120 |
| `app_static_lib` (libgreet static, rest dynamic) | 17,024 |
| `app_shared` | 16,744 |
| `app_full_static` (`-static`: also libstdc++ and libc) | 2,417,768 |

For a small library the difference is noise. What makes a static binary large is pulling in
`libstdc++` and `libc` with `-static`; `ldd app_full_static` then reports
`not a dynamic executable`.

## How the loader finds libraries

The executable stores library **names** in `NEEDED` entries of its dynamic section. At start-up,
`ld.so` searches for each in this order (per [ld.so(8)](https://man7.org/linux/man-pages/man8/ld.so.8.html)):

1. `DT_RPATH` in the executable, **only if** it has no `DT_RUNPATH` (legacy).
2. The `LD_LIBRARY_PATH` environment variable.
3. `DT_RUNPATH` in the executable.
4. The cache in `/etc/ld.so.cache` (rebuilt by `ldconfig`).
5. The default directories `/lib` and `/usr/lib` (and their multiarch variants).

```bash
LD_LIBRARY_PATH=. ./app_shared                                   # works: for testing
g++ -O2 main.cpp -L. -lgreet -Wl,-rpath,'$ORIGIN' -o app_rpath   # works: path embedded
readelf -d app_rpath | grep -E 'NEEDED|RUNPATH'
```

```text
 0x0000000000000001 (NEEDED)             Shared library: [libgreet.so]
 0x0000000000000001 (NEEDED)             Shared library: [libstdc++.so.6]
 0x0000000000000001 (NEEDED)             Shared library: [libgcc_s.so.1]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
 0x000000000000001d (RUNPATH)            Library runpath: [$ORIGIN]
```

`-rpath` produced a `RUNPATH` here because Ubuntu's linker defaults to `--enable-new-dtags`.
`$ORIGIN` means "the directory of the executable", so the program finds `libgreet.so` next to
itself wherever it is installed. `ldd app` shows what the loader would resolve now, including
`libgreet.so => not found` when it fails.

## Shared library versioning

Linux shared libraries carry an **soname**: the name a program records in `NEEDED`, which changes
only when the ABI breaks.

```bash
g++ -fPIC -shared -Wl,-soname,libgreet.so.1 greet.cpp -o libgreet.so.1.0.0
ln -s libgreet.so.1.0.0 libgreet.so.1     # soname: what the loader looks for
ln -s libgreet.so.1 libgreet.so           # dev link: what -lgreet finds at link time
readelf -d libgreet.so.1.0.0 | grep SONAME
```

```text
 0x000000000000000e (SONAME)             Library soname: [libgreet.so.1]
```

A program linked against this records `libgreet.so.1`. Installing `libgreet.so.1.0.1` and moving
the `libgreet.so.1` link updates every program at once. An incompatible release gets soname
`libgreet.so.2`, and old programs keep using `.so.1`. What counts as an ABI break in C++ (changing a
class layout, a virtual function, a signature) is on [ABI](../12-low-level-and-platform/01-abi.md).

## Exported symbols and visibility

By default every non-`static` function in a `.so` is exported, so it becomes part of the library's
ABI and can be interposed by another library defining the same name. Build with
`-fvisibility=hidden` and mark the public API explicitly:

```cpp title="greet_api.h"
#if defined(_WIN32)
  #define GREET_API __declspec(dllexport)   // when building the DLL; dllimport when using it
#else
  #define GREET_API __attribute__((visibility("default")))
#endif

GREET_API std::string greet(const std::string& who);
```

```bash
g++ -O2 -fPIC -shared greet.cpp -o libgreet.so && nm -D --defined-only libgreet.so | c++filt
g++ -O2 -fPIC -shared -fvisibility=hidden greet.cpp -o libhidden.so && nm -D --defined-only libhidden.so
```

The first lists `greet(std::__cxx11::basic_string<…> const&)`; the second lists nothing, because
`greet.cpp` above does not use the macro. Hidden symbols cannot clash with other libraries and let
the compiler optimise calls within the library. See [GCC: Visibility](https://gcc.gnu.org/wiki/Visibility).
On Windows, DLLs export nothing unless marked `dllexport`, so the macro is required there.

## Loading code at run time: `dlopen`

A program can also load a shared library that it was never linked against, for plugins:

<Tabs>
  <TabItem value="plugin" label="plugin.cpp">

```cpp title="plugin.cpp"
#include <cstdio>
extern "C" void plugin_init() { std::puts("plugin loaded"); }
```

  </TabItem>
  <TabItem value="host" label="host.cpp">

```cpp title="host.cpp"
#include <dlfcn.h>
#include <iostream>

int main() {
    void* handle = dlopen("./plugin.so", RTLD_NOW);
    if (!handle) {
        std::cerr << "dlopen failed: " << dlerror() << '\n';
        return 1;
    }
    using init_fn = void (*)();
    auto init = reinterpret_cast<init_fn>(dlsym(handle, "plugin_init"));
    if (!init) {
        std::cerr << "dlsym failed: " << dlerror() << '\n';
        return 1;
    }
    init();
    dlclose(handle);
}
```

  </TabItem>
</Tabs>

```bash
g++ -std=c++23 -fPIC -shared plugin.cpp -o plugin.so
g++ -std=c++23 host.cpp -o host && ./host
```

```text
plugin loaded
```

`extern "C"` keeps the name unmangled so `dlsym` can find it by the plain string `"plugin_init"`
([C Interoperability](../12-low-level-and-platform/07-interop-c.md)). On glibc 2.34 and later,
`dlopen` is in `libc` itself, so no `-ldl` is needed. Windows uses `LoadLibrary`/`GetProcAddress`.
See [dlopen(3)](https://man7.org/linux/man-pages/man3/dlopen.3.html).

## Choosing

| | Static | Dynamic |
|---|---|---|
| Deployment | One file to copy | Executable plus every `.so`, on the loader's path |
| Security fixes in the library | Rebuild and redeploy every program | Replace the `.so` once |
| Memory across processes | Each process has its own copy of the code | One copy of read-only pages shared by all processes |
| Start-up | No library lookup | Loader resolves and maps libraries, and binds symbols |
| Failure modes | None at start-up | Missing `.so`, wrong version (`GLIBCXX_3.4.xx not found`) |
| Licences | LGPL code linked statically has extra obligations | Usual choice for LGPL libraries |

A common split: link your own libraries statically and the system libraries (`libc`, `libstdc++`)
dynamically. Fully static glibc binaries have caveats (functions such as `getpwnam` and `dlopen`
still try to load shared modules), so use musl or a container if you need a single portable file.

## Pitfalls

- **`LD_LIBRARY_PATH` in production.** It applies to every child process and overrides `RUNPATH`.
  Use `-Wl,-rpath,'$ORIGIN/../lib'` or install to a system directory and run `ldconfig`.
- **`version 'GLIBCXX_3.4.NN' not found`.** The program was built with a newer GCC than the target
  machine's `libstdc++.so.6`. Build on the oldest target you support, or ship the newer
  `libstdc++` (or link it with `-static-libstdc++`).
- **Two copies of one static library in one process.** If both your executable and a `.so` link
  `libfoo.a` statically, each has its own globals; a singleton exists twice.
- **Forgetting `-fPIC`** for objects that go into a `.so`: the link fails with
  `recompile with -fPIC`.

## Key points

- Static: code is copied in at link time. Dynamic: only the name is stored, and `ld.so` resolves it
  at every start.
- A successful link says nothing about run time: check `ldd`/`readelf -d` for `NEEDED` and `RUNPATH`.
- Version shared libraries with an soname; hide everything that is not the public API.
- `dlopen` + `extern "C"` is the portable-on-POSIX plugin mechanism.
