---
id: boost-dll
title: Boost.DLL
sidebar_label: Boost.DLL
sidebar_position: 5
tags: [c++, boost, dll, shared-library, plugin]
---

# Boost.DLL

`boost::dll` provides **portable shared-library loading** — open a `.so`, `.dll`, or `.dylib` at
runtime, import functions and variables by name, and build plugin architectures where new
functionality can be added without recompiling the host application. It replaces the platform-specific
`dlopen`/`LoadLibrary` dance with a single, type-safe C++ API.

:::info The problem it solves
Loading shared libraries at runtime is fully platform-dependent: POSIX uses `dlopen` + `dlsym`,
Windows uses `LoadLibrary` + `GetProcAddress`, macOS has its own quirks with `@rpath`. Error
messages differ, symbol decoration rules differ, and none of it is type-safe. Boost.DLL wraps all
of this with a cross-platform interface and adds features like alias-based plugin systems.
:::

## Loading a library and importing a function

```cpp showLineNumbers title="import_function.cpp"
#include <boost/dll/import.hpp>
#include <boost/filesystem.hpp>
#include <iostream>

int main() {
    namespace dll = boost::dll;

    // load the shared library and import a function
    auto greet = dll::import<std::string(const std::string&)>(
        "libgreeter",                     // library name (no extension needed)
        "greet",                          // exported symbol name
        dll::load_mode::append_decorations // adds lib prefix and .so/.dll suffix
    );

    std::cout << greet("World") << "\n";
}
```

The returned object is a `boost::shared_ptr<function_type>` that keeps the library loaded as long
as the function handle is alive.

## The shared_library class

For lower-level control, use `shared_library` directly:

```cpp showLineNumbers title="shared_library.cpp"
#include <boost/dll/shared_library.hpp>
#include <iostream>

int main() {
    namespace dll = boost::dll;

    dll::shared_library lib("libmath_plugin.so", dll::load_mode::rtld_lazy);

    if (!lib.has("compute")) {
        std::cerr << "symbol not found\n";
        return 1;
    }

    auto& compute = lib.get<double(double, double)>("compute");
    std::cout << "result: " << compute(3.14, 2.0) << "\n";

    std::cout << "loaded from: " << lib.location() << "\n";
}
```

:::warning Symbol names and C++ mangling
C++ function names are mangled by the compiler. To export a function with a predictable name, either
declare it `extern "C"` or use `BOOST_DLL_ALIAS` (see below). Without one of these, `get<>()` will
fail to find the symbol.
:::

## Building a plugin system with BOOST_DLL_ALIAS

The cleanest approach for plugins: define an alias in the plugin library and import it in the host.

```cpp showLineNumbers title="plugin_api.hpp"
#include <string>

class plugin_api {
public:
    virtual std::string name() const = 0;
    virtual void execute() = 0;
    virtual ~plugin_api() = default;
};
```

```cpp showLineNumbers title="my_plugin.cpp"
#include "plugin_api.hpp"
#include <boost/dll/alias.hpp>
#include <iostream>
#include <memory>

class my_plugin : public plugin_api {
public:
    std::string name() const override { return "my_plugin"; }
    void execute() override { std::cout << "plugin running\n"; }

    static std::shared_ptr<plugin_api> create() {
        return std::make_shared<my_plugin>();
    }
};

BOOST_DLL_ALIAS(my_plugin::create, create_plugin)
```

```cpp showLineNumbers title="host.cpp"
#include "plugin_api.hpp"
#include <boost/dll/import.hpp>
#include <iostream>

int main() {
    namespace dll = boost::dll;

    auto creator = dll::import<std::shared_ptr<plugin_api>()>(
        "./libmy_plugin",
        "create_plugin",
        dll::load_mode::append_decorations
    );

    auto plugin = creator();
    std::cout << "loaded: " << plugin->name() << "\n";
    plugin->execute();
}
```

:::tip BOOST_DLL_ALIAS vs extern "C"
`BOOST_DLL_ALIAS` exports a mangling-safe symbol without requiring `extern "C"`, and it works with
overloaded functions, static member functions, and lambdas. Prefer it over raw `extern "C"` exports
for any non-trivial plugin interface.
:::

## Inspecting the current executable

```cpp showLineNumbers title="self_location.cpp"
#include <boost/dll/runtime_symbol_info.hpp>
#include <iostream>

int main() {
    std::cout << "executable: " << boost::dll::program_location() << "\n";
    std::cout << "this module: " << boost::dll::this_line_location() << "\n";
}
```

`program_location()` returns the full path of the running executable — useful for locating plugin
directories relative to the binary.

## Linking

Boost.DLL is mostly header-only but depends on Boost.Filesystem and Boost.System:

```cmake
find_package(Boost REQUIRED COMPONENTS filesystem system)
target_link_libraries(myapp PRIVATE Boost::filesystem Boost::system ${CMAKE_DL_LIBS})
```

`${CMAKE_DL_LIBS}` adds `-ldl` on Linux (required for `dlopen`).

## See also

- <Icon icon="lucide:terminal" inline /> [Boost.Process](./boost-process.md) — out-of-process execution, the complement to in-process loading.
- <Icon icon="lucide:hard-drive" inline /> [Boost.Filesystem](./boost-filesystem.md) — path handling for locating plugins.
- <Icon icon="lucide:hammer" inline /> [CMake integration](../01-build-and-integration/cmake-integration.md) — building shared libraries and linking Boost.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
