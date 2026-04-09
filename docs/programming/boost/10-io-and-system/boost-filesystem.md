---
id: boost-filesystem
title: Boost.Filesystem
sidebar_label: Boost.Filesystem
sidebar_position: 1
tags: [c++, boost, filesystem, path, directory]
---

# Boost.Filesystem

`boost::filesystem` provides **portable file and directory operations** — path manipulation,
directory traversal, file status queries, and file management — all without touching a single
platform-specific API yourself. It is one of the most successful Boost libraries: it was adopted
almost wholesale into C++17 as `std::filesystem`, and its design shaped how every major C++ project
handles paths today.

:::info The problem it solves
Before Boost.Filesystem, portable file handling meant `#ifdef _WIN32` blocks everywhere, hand-rolled
path concatenation with `/` vs `\`, and calling `stat()` or `GetFileAttributesW()` depending on
platform. Boost.Filesystem replaces all of that with a single, cross-platform API built around the
`path` class.
:::

## The path class

A `path` is the library's core type. It is *not* a validated path — it is a structured string that
knows how to decompose into root, parent, stem, and extension, and how to concatenate portably.

```cpp showLineNumbers title="path_basics.cpp"
#include <boost/filesystem.hpp>
#include <iostream>

namespace fs = boost::filesystem;

int main() {
    fs::path p("/usr/local/include/boost/optional.hpp");

    std::cout << "root:      " << p.root_path()      << "\n"
              << "parent:    " << p.parent_path()     << "\n"
              << "filename:  " << p.filename()        << "\n"
              << "stem:      " << p.stem()            << "\n"
              << "extension: " << p.extension()       << "\n";

    fs::path built = fs::path("/var") / "log" / "app.log";
    std::cout << "built:     " << built << "\n";
}
```

The `/` operator builds paths portably — on Windows it emits `\`, on POSIX it emits `/`.

## Querying file status

```cpp showLineNumbers title="status.cpp"
#include <boost/filesystem.hpp>
#include <iostream>

namespace fs = boost::filesystem;

void report(const fs::path& p) {
    boost::system::error_code ec;
    fs::file_status st = fs::status(p, ec);

    if (ec) {
        std::cout << p << ": " << ec.message() << "\n";
        return;
    }

    if (fs::is_regular_file(st))
        std::cout << p << ": file, " << fs::file_size(p) << " bytes\n";
    else if (fs::is_directory(st))
        std::cout << p << ": directory\n";
    else if (fs::is_symlink(st))
        std::cout << p << ": symlink\n";
}
```

:::tip Error-code overloads
Every function that touches the filesystem has two overloads: one that throws
`boost::filesystem::filesystem_error` on failure, and one that writes to an `error_code` reference.
Prefer the `error_code` overload in performance-sensitive or expected-failure paths.
:::

## Directory iteration

```cpp showLineNumbers title="listing.cpp"
#include <boost/filesystem.hpp>
#include <iostream>

namespace fs = boost::filesystem;

int main() {
    for (const auto& entry : fs::directory_iterator("/tmp")) {
        std::cout << entry.path().filename() << "\n";
    }

    std::cout << "\n--- recursive ---\n";
    for (const auto& entry : fs::recursive_directory_iterator("/usr/local/include/boost")) {
        if (fs::is_regular_file(entry) && entry.path().extension() == ".hpp") {
            std::cout << entry.path() << "\n";
        }
    }
}
```

`directory_iterator` is shallow; `recursive_directory_iterator` descends into subdirectories
automatically and can optionally follow or skip symlinks.

## Common operations

```cpp showLineNumbers title="operations.cpp"
#include <boost/filesystem.hpp>

namespace fs = boost::filesystem;

void demo() {
    fs::create_directories("/tmp/app/logs");

    fs::copy_file("src.txt", "dst.txt", fs::copy_options::overwrite_existing);

    fs::rename("old_name.dat", "new_name.dat");

    fs::remove("/tmp/app/logs/stale.log");
    fs::remove_all("/tmp/app");  // recursive delete

    fs::path canon = fs::canonical("../relative/../path");

    fs::path tmp = fs::temp_directory_path() / fs::unique_path("%%%%-%%%%-%%%%.tmp");
}
```

:::danger remove_all is irreversible
`remove_all` recursively deletes an entire directory tree without confirmation. Double-check the
path — especially when it comes from user input — before calling it.
:::

## Boost.Filesystem versus std::filesystem

```mermaid
flowchart LR
    BFS[boost::filesystem] --> STD[std::filesystem -- C++17]
    BFS --> EXTRA[boost extras -- unique_path, wpath legacy]
    STD -.-> P0[no unique_path in std]
```

| Feature | `boost::filesystem` | `std::filesystem` |
|---------|---------------------|-------------------|
| Header | `<boost/filesystem.hpp>` | `<filesystem>` |
| Namespace | `boost::filesystem` | `std::filesystem` |
| Path separator | `/` operator | `/` operator |
| Unique temp path | `unique_path()` | not available |
| Relative path | `relative()` (Boost 1.60+) | `relative()` |
| `error_code` overloads | yes | yes |
| Compiled library | yes, link `-lboost_filesystem` | usually header-only or auto-linked |
| Requires | Boost | C++17 compiler |

:::note Which to choose
On C++17 and later, prefer `std::filesystem` — it needs no external dependency and is ABI-stable
across standard-library updates. Reach for Boost.Filesystem when you need `unique_path()`, must
support a pre-C++17 toolchain, or need portable behaviour that your vendor's `std::filesystem`
does not yet implement correctly. See
[Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) for the broader story.
:::

## Linking

Boost.Filesystem is a **compiled** library. With CMake:

```cmake
find_package(Boost REQUIRED COMPONENTS filesystem)
target_link_libraries(myapp PRIVATE Boost::filesystem)
```

With b2 or raw compiler flags, link `-lboost_filesystem -lboost_system`.

## See also

- <Icon icon="lucide:hard-drive" inline /> [Boost.Iostreams](./boost-iostreams.md) — filtered stream I/O, often paired with filesystem operations.
- <Icon icon="lucide:terminal" inline /> [Boost.Process](./boost-process.md) — launch child processes, another system-level building block.
- <Icon icon="lucide:settings" inline /> [Boost.System](./boost-system.md) — the `error_code` framework that Filesystem relies on.
- <Icon icon="lucide:hammer" inline /> [CMake integration](../01-build-and-integration/cmake-integration.md) — linking compiled Boost libraries.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) — the `std::filesystem` lineage.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
