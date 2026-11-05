---
id: filesystem
title: Filesystem Library
sidebar_label: Filesystem
sidebar_position: 8
tags: [c++, c++17, filesystem, path, directory-iterator, error-code, permissions, symlink]
---

# Filesystem Library

`<filesystem>` *(C++17)* gives portable names to the things every program does with files and
directories: build and take apart paths, ask whether something exists and what it is, create, copy,
rename and delete, and walk a directory tree. It is a thin layer over the operating system, so many
results (case sensitivity, symlinks, permissions, timestamps) still depend on the platform. Reading
and writing a file's *contents* is not this library's job; use [IOStreams](./iostreams.md).

**Prerequisites:** [Strings](./strings.md) (`path` converts to and from strings),
[Containers](./containers.md) and [Iterators](./iterators.md) (directory iterators are input
iterators), [Chrono](./chrono.md) (timestamps).

All names are in `std::filesystem`; the usual alias is `namespace fs = std::filesystem;`. With GCC 8 and older, and with libc++ before 9, you had to link `-lstdc++fs` / `-lc++fs`.

## `path`: a string with structure

`fs::path` stores a pathname as text in the platform's native encoding (`char` with UTF-8 on Linux;
`wchar_t` UTF-16 on Windows) and offers *lexical* operations that never touch the disk. Decomposition:

| Call | For `/home/ann/report.tar.gz` |
|---|---|
| `root_path()`, `root_directory()` | `/` |
| `parent_path()` | `/home/ann` |
| `filename()` | `report.tar.gz` |
| `stem()` | `report.tar` |
| `extension()` | `.gz` (the part from the **last** dot) |
| `relative_path()` | `home/ann/report.tar.gz` |

`operator/` joins components and inserts the separator; `operator+=` appends text with no separator.
A subtle rule: **if the right-hand side is absolute, `/` replaces the left side**, so
`fs::path("/data") / "/etc"` is `/etc`.

```cpp title="path.cpp" showLineNumbers
#include <filesystem>
#include <iostream>

namespace fs = std::filesystem;

int main() {
    fs::path p = "/home/ann/report.tar.gz";
    std::cout << p.parent_path() << ' ' << p.filename() << ' ' << p.stem() << ' ' << p.extension() << '\n';

    fs::path q = fs::path("/data") / "logs" / "a.txt";
    q.replace_extension(".csv");
    std::cout << q.string() << '\n';

    std::cout << (fs::path("/data") / "/etc").string() << '\n';             // absolute rhs wins
    std::cout << fs::path("a/./b/../c//d").lexically_normal().string() << '\n';
    std::cout << fs::path("/a/b/c").lexically_relative("/a/x").string() << '\n';

    for (const auto& part : fs::path("/usr/local/bin"))                     // iterates components
        std::cout << '[' << part.string() << ']';
    std::cout << '\n';
}
```

```text
"/home/ann" "report.tar.gz" "report.tar" ".gz"
/data/logs/a.csv
/etc
a/c/d
../b/c
[/][usr][local][bin]
```

(`operator<<` on a `path` prints it in quotes with escapes; use `.string()` for plain text.)

- `lexically_normal`, `lexically_relative` and `lexically_proximate` look only at the text. They do
  not resolve symlinks or `..` through a link, so they can give the wrong answer on a real
  disk. For that, use `fs::canonical` (resolves, path must exist), `fs::weakly_canonical`
  (resolves the part that exists), or `fs::absolute` (no symlink resolution).
- `path` is not `std::string`: converting needs `string()`, `u8string()` (a `std::u8string` since C++20),
  or `native()`. Building a path from a `std::u8string` or `char8_t` data is how you say "this is UTF-8"
  portably. Using `std::string` that holds UTF-8 on Windows is a bug because it is interpreted
  in the ANSI code page.
- Comparison is component-wise and lexical: `fs::path("a/b") == "a//b"` is `true`, and `fs::equivalent(a, b)`
  asks the OS whether two paths name the same file.

## Querying files

`fs::status(p)` follows symlinks and `fs::symlink_status(p)` does not; both return a `file_status` with
`type()` (`regular`, `directory`, `symlink`, `not_found`, ...) and `permissions()`. The shortcuts:
`fs::exists`, `is_regular_file`, `is_directory`, `is_symlink`, `is_empty`, `file_size` (regular files
only; bytes), `last_write_time` (a `file_time_type`, whose clock `file_clock` has an unspecified
epoch before C++20), `fs::space(p)` (capacity, free, available), and `fs::equivalent`.

Exists-then-act sequences are **racy**: another process can create or delete the file between
the check and the use (a time-of-check/time-of-use bug). Prefer to attempt the operation and handle
the error, or use the single call that does both.

## Changing the filesystem

| Function | Behavior |
|---|---|
| `create_directory(p)` | one level; returns `false` (no error) if it already exists |
| `create_directories(p)` | like `mkdir -p`; returns `true` if something was created |
| `remove(p)` | one file or empty directory; returns `false` if it does not exist |
| `remove_all(p)` | recursive; returns the number of items removed. **No undo; check the path** |
| `rename(from, to)` | atomic on POSIX on the same filesystem; replaces an existing file, not portable across volumes |
| `copy_file(from, to, options)` | one regular file; fails if `to` exists unless `copy_options::overwrite_existing` or `skip_existing` / `update_existing` |
| `copy(from, to, options)` | files or directories; `copy_options::recursive` copies a tree |
| `create_symlink`, `create_hard_link`, `read_symlink`, `resize_file`, `permissions` | as named |
| `current_path()`, `temp_directory_path()` | process working directory / a temp directory |

There is no function that creates a unique temporary file or directory; `temp_directory_path()`
returns only the base. Create a name with a random or counter suffix (and handle collisions), or use
`mkstemp` on POSIX. Do not rely on `std::tmpnam`.

## Iterating directories

`fs::directory_iterator(p)` yields the entries of one directory, and `fs::recursive_directory_iterator(p)`
walks the whole tree. Both are **input iterators** (single pass) over `directory_entry` objects, in an
**unspecified order** that differs between filesystems; sort the results if you need a stable order.
`directory_entry` caches attributes, so `entry.is_directory()` or `entry.file_size()` may avoid an extra
system call. Both iterators are usable with range-based `for`, and with `std::ranges` algorithms
(they are `borrowed_range`s since C++20).

```cpp title="walk.cpp" showLineNumbers
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

int main() {
    fs::path root = fs::temp_directory_path() / "kb_fs_demo";
    fs::remove_all(root);                                   // start clean (returns count removed)
    fs::create_directories(root / "sub" / "deep");
    std::ofstream(root / "a.txt") << "hello";
    std::ofstream(root / "sub" / "b.txt") << "world!";
    std::ofstream(root / "sub" / "deep" / "c.log") << "x";

    std::vector<std::string> txt;
    std::uintmax_t bytes = 0;
    for (const auto& e : fs::recursive_directory_iterator(root)) {
        if (e.is_regular_file()) {
            bytes += e.file_size();
            if (e.path().extension() == ".txt")
                txt.push_back(fs::relative(e.path(), root).generic_string());
        }
    }
    std::sort(txt.begin(), txt.end());                      // iteration order is unspecified
    for (const auto& s : txt) std::cout << s << '\n';
    std::cout << bytes << " bytes\n";

    fs::remove_all(root);
    std::cout << fs::exists(root) << '\n';
}
```

```text
a.txt
sub/b.txt
12 bytes
0
```

By default `recursive_directory_iterator` does not follow directory symlinks (set
`directory_options::follow_directory_symlink` to do so, and beware loops). Erasing or creating
entries while iterating is not safe: collect first, then change. A modification during iteration
gives an unspecified result about whether the new entry is visited.

## Error handling: two overload sets

Every function that touches the OS comes in two forms. The plain one throws
`fs::filesystem_error` (derived from `std::system_error`, with `path1()`, `path2()` and `code()`).
The overload with a trailing `std::error_code& ec` never throws for filesystem errors; it sets
`ec` (and clears it on success). Use error codes when failure is routine (probing, cleanup),
and exceptions where failure is exceptional. See
[error codes](../10-error-handling-and-safety/03-error-codes.md) for `std::error_code` itself.

Note that "not found" is not always an error: `fs::remove` returns `false` rather than throwing when
the file does not exist, and `fs::exists(p, ec)` returns `false` with `ec` set only for real failures.

```cpp title="errors.cpp" showLineNumbers
#include <filesystem>
#include <iostream>
#include <system_error>

namespace fs = std::filesystem;

int main() {
    fs::path missing = "/no/such/dir/file.txt";

    std::cout << fs::remove(missing) << '\n';              // 0: nothing to remove, no error

    try {
        (void)fs::file_size(missing);                           // throws: file_size needs it to exist
    } catch (const fs::filesystem_error& e) {
        std::cout << "threw, path1=" << e.path1() << " code=" << (e.code() == std::errc::no_such_file_or_directory) << '\n';
    }

    std::error_code ec;
    auto n = fs::file_size(missing, ec);                    // does not throw
    std::cout << (ec == std::errc::no_such_file_or_directory) << ' ' << n << '\n';
}
```

```text
0
threw, path1="/no/such/dir/file.txt" code=1
1 18446744073709551615
```

On failure the error-code `file_size` returns `static_cast<uintmax_t>(-1)`.

## Permissions

`fs::permissions(p, perms::owner_all | perms::group_read, fs::perm_options::add)` sets or changes POSIX-style
permission bits (`replace`, `add`, `remove`). On Windows only the read-only attribute is meaningful.
The bits are the file mode; they do not tell you whether *this process* may access the file, and
the answer can change at any moment, so try the operation and handle the failure.

## Pitfalls

- **Check-then-act races**: see above; handle the error instead.
- **`remove_all(path)` with a wrong or empty path** can delete far more than you meant. Build
  the path from a known base and validate it.
- **Encoding**: on Windows, build paths from wide or `u8` strings; on POSIX the bytes are opaque.
  Filenames need not be valid UTF-8.
- **Iteration order** is unspecified; sort before comparing results or writing tests.
- **Case sensitivity and separators** are platform choices: `generic_string()` gives a form
  with `/` for output you compare or store.
- **Symlinks**: `status` follows them, `symlink_status` does not; `remove` deletes the link, not the target.

## Related

- [IOStreams](./iostreams.md): `std::ifstream` / `std::ofstream` take a `path` to read and write contents
- [Chrono](./chrono.md): `file_time_type` and converting it to `system_clock`
- [Error codes](../10-error-handling-and-safety/03-error-codes.md): `std::error_code` and `std::errc`
- [Strings](./strings.md): `string_view` and UTF-8 text handling for path components

## References

- [Filesystem library, cppreference](https://en.cppreference.com/w/cpp/filesystem)
- ISO C++ [filesystems]
