---
id: boost-iostreams
title: Boost.Iostreams
sidebar_label: Boost.Iostreams
sidebar_position: 2
tags: [c++, boost, iostreams, filter, compression, stream]
---

# Boost.Iostreams

`boost::iostreams` is a framework for building **filtering streams** — chains of sources, sinks, and
filters that process data as it flows through standard `iostream` interfaces. Instead of writing raw
zlib calls or hand-rolling buffered I/O, you compose a pipeline: read from a file, decompress with
gzip, count lines, and deliver UTF-8 text — all through a single `std::istream` interface.

:::info The problem it solves
The standard `<iostream>` hierarchy gives you sources and sinks (`filebuf`, `stringbuf`), but no way
to *chain* processing steps. Boost.Iostreams introduces the **filter** concept: a reusable
transformation that sits between a source/sink and the user-facing stream, letting you stack
compression, encryption, checksumming, or any custom transformation without rewriting your I/O code.
:::

## Core concepts

```mermaid
flowchart LR
    S[Source / Device] --> F1[Filter 1 -- e.g. gzip decompressor]
    F1 --> F2[Filter 2 -- e.g. line counter]
    F2 --> U[User reads from stream]
```

- **Device** — a source (readable), a sink (writable), or both. Files, memory buffers, and file
  descriptors are built-in devices.
- **Filter** — transforms data passing through a chain. Filters are composable: stack as many as
  you like.
- **Chain** — a `filtering_istream` or `filtering_ostream` that binds filters and a terminal device
  into a usable `std::istream` or `std::ostream`.

## Reading a gzip-compressed file

```cpp showLineNumbers title="gzip_read.cpp"
#include <boost/iostreams/filtering_stream.hpp>
#include <boost/iostreams/filter/gzip.hpp>
#include <boost/iostreams/device/file.hpp>
#include <iostream>
#include <string>

namespace io = boost::iostreams;

int main() {
    io::filtering_istream in;
    in.push(io::gzip_decompressor());
    in.push(io::file_source("data.gz", std::ios_base::binary));

    std::string line;
    while (std::getline(in, line)) {
        std::cout << line << "\n";
    }
}
```

The `gzip_decompressor` filter transparently decompresses data as the stream reads from the file
source. Swap it for `zlib_decompressor` or `bzip2_decompressor` to handle other formats.

## Writing compressed output

```cpp showLineNumbers title="gzip_write.cpp"
#include <boost/iostreams/filtering_stream.hpp>
#include <boost/iostreams/filter/gzip.hpp>
#include <boost/iostreams/device/file.hpp>

namespace io = boost::iostreams;

int main() {
    io::filtering_ostream out;
    out.push(io::gzip_compressor());
    out.push(io::file_sink("output.gz", std::ios_base::binary));

    out << "line one\n";
    out << "line two\n";
    // closing or flushing finalises the gzip stream
}
```

:::warning Always close or flush compressed output streams
Gzip and bzip2 compressors buffer internally and write a footer on close. If you let the stream
destruct without flushing, the output file may be truncated or invalid.
:::

## Writing a custom filter

A filter is any type that satisfies the filter concept. The simplest form is a
`multichar_input_filter` or `output_filter`:

```cpp showLineNumbers title="uppercase_filter.cpp"
#include <boost/iostreams/filtering_stream.hpp>
#include <boost/iostreams/device/file.hpp>
#include <boost/iostreams/categories.hpp>
#include <cctype>

namespace io = boost::iostreams;

struct uppercase_filter : io::output_filter {
    template <typename Sink>
    bool put(Sink& dest, char c) {
        return io::put(dest, static_cast<char>(std::toupper(
            static_cast<unsigned char>(c))));
    }
};

int main() {
    io::filtering_ostream out;
    out.push(uppercase_filter());
    out.push(io::file_sink("upper.txt"));

    out << "hello boost iostreams\n";
    // file contains: HELLO BOOST IOSTREAMS
}
```

## Memory-mapped files

Boost.Iostreams also provides `mapped_file_source` and `mapped_file_sink` for memory-mapped I/O:

```cpp showLineNumbers title="mmap.cpp"
#include <boost/iostreams/device/mapped_file.hpp>
#include <iostream>
#include <string_view>

namespace io = boost::iostreams;

int main() {
    io::mapped_file_source mf("large_file.dat");
    std::string_view contents(mf.data(), mf.size());

    std::cout << "first 80 chars: " << contents.substr(0, 80) << "\n";
}
```

:::tip When to use memory-mapped I/O
Memory-mapped files are fastest for random-access reads over large files — the OS handles paging
automatically. For sequential, filtered reads (compression, line-by-line), the filter-chain approach
is usually cleaner and more composable.
:::

## Built-in filters and devices

| Category | Examples |
|----------|----------|
| Compression | `gzip_compressor/decompressor`, `bzip2_*`, `zlib_*`, `lzma_*` |
| Text | `newline_filter` (line-ending conversion), `regex_filter` |
| Utility | `counter` (byte/line counting), `tee_filter` (duplicate to two sinks) |
| Devices | `file_source/sink`, `mapped_file`, `array_source/sink`, `null_sink` |

## Linking

Boost.Iostreams is a **compiled** library. Compression filters require their respective C libraries
(zlib, libbz2, liblzma):

```cmake
find_package(Boost REQUIRED COMPONENTS iostreams)
target_link_libraries(myapp PRIVATE Boost::iostreams)
```

## See also

- <Icon icon="lucide:hard-drive" inline /> [Boost.Filesystem](./boost-filesystem.md) — portable path and directory operations, often paired with Iostreams.
- <Icon icon="lucide:settings" inline /> [Boost.System](./boost-system.md) — error handling used by Iostreams devices.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
