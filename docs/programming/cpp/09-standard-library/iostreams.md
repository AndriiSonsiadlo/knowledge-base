---
id: iostreams
title: Input/Output Streams
sidebar_label: IOStreams
sidebar_position: 9
tags: [c++, iostreams, cout, cin, fstream, stringstream, stream-state, manipulators, binary-io]
---

# Input/Output Streams

A **stream** is a character sequence with a typed interface: `os << value` formats a value as text
into an output stream, and `is >> value` parses text from an input stream. The same interface works
on the console (`std::cout`), files (`std::fstream`) and in-memory strings (`std::stringstream`),
because all of them are classes derived from `std::basic_ios` that talk to a **stream buffer**
which does the real reading and writing. This page is the canonical home for the stream classes, the
state flags, formatting and binary I/O. Path handling is on [Filesystem](./filesystem.md).

**Prerequisites:** [Strings](./strings.md), [operator overloading](../02-language-fundamentals/operators/operator-overloading.md),
[exceptions](../10-error-handling-and-safety/01-exceptions.md) (streams can throw, but do not by default).

<Diagram title="Stream classes and the buffer behind them" accent="blue">
  <DiagramRow>
    <DiagramNode title="istream / ostream">formatted + unformatted operations, state flags</DiagramNode>
    <DiagramArrow direction="right" label="owns / uses" />
    <DiagramNode title="streambuf" accent>buffer, talks to the device</DiagramNode>
    <DiagramArrow direction="right" />
    <DiagramNode title="file, string, console" />
  </DiagramRow>
</Diagram>

| Header | Classes | Purpose |
|---|---|---|
| `<iostream>` | `cin`, `cout`, `cerr`, `clog` | standard input, output, unbuffered error, buffered log |
| `<fstream>` | `ifstream`, `ofstream`, `fstream` | files |
| `<sstream>` | `istringstream`, `ostringstream`, `stringstream` | in-memory text |
| `<iomanip>` | `setw`, `setprecision`, `setfill`, ... | manipulators with arguments |
| `<spanstream>` | `ispanstream`, `ospanstream` *(C++23)* | streams over a caller-owned buffer |

Each has a wide-character variant (`wcout`, `wifstream`, ...); text I/O is almost always `char`.

## Reading and writing text

`operator>>` is a **formatted** read: it skips leading whitespace, then parses up to the next
character that cannot be part of the value. So `cin >> name` reads one word, and
`std::getline(is, str)` reads a whole line (and removes the `'\n'`).

```cpp title="read-loop.cpp" showLineNumbers
#include <iostream>
#include <sstream>
#include <string>

int main() {
    std::istringstream in("alice 30\nbob 25\nbroken line\n");

    std::string line;
    while (std::getline(in, line)) {                // loop on the read, not on eof()
        std::istringstream row(line);
        std::string name; int age = 0;
        if (row >> name >> age)
            std::cout << name << " is " << age << '\n';
        else
            std::cout << "bad line: " << line << '\n';
    }
}
```

```text
alice is 30
bob is 25
bad line: broken line
```

Always use the read operation itself as the loop condition (`while (std::getline(in, s))`,
`while (in >> x)`): a stream converts to `bool` (false when it has failed), and testing
`while (!in.eof())` runs the body once more after the last failed read and processes garbage.

The classic mixing bug: after `cin >> n`, the newline is still in the buffer, so a following
`getline(cin, s)` reads an empty line. Discard it with
`cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n')`, or read everything with `getline` and parse.

## Stream state

Every stream carries a state of four bits, tested by member functions:

| Bit | Test | Meaning | Set when |
|---|---|---|---|
| `goodbit` | `good()` | none of the below | |
| `eofbit` | `eof()` | end of input reached | a read tried to go past the end |
| `failbit` | `fail()` | a formatting/extraction **operation failed**; stream data is intact | parse error (`"abc"` read as `int`), or EOF before anything was read |
| `badbit` | `bad()` | the stream or buffer itself is broken | a lost-integrity I/O error, an exception from the buffer |

`operator bool` (and `!stream`) is `!fail()`, so it is false for `failbit` or `badbit` but true at
`eofbit` alone. Once `failbit` is set **every later operation is a no-op** until you call `clear()`;
recovering from bad input means `clear()` and then discarding the offending characters.

```cpp title="state.cpp" showLineNumbers
#include <iostream>
#include <limits>
#include <sstream>

int main() {
    std::istringstream in("12 oops 34");
    int a = 0, b = 0, c = 0;

    in >> a;                       // ok
    in >> b;                       // fails on "oops": b is set to 0 (C++11), failbit set
    std::cout << a << ' ' << b << ' ' << in.fail() << '\n';

    in >> c;                       // no-op: stream is already in a failed state
    std::cout << c << '\n';

    in.clear();                                                      // reset the flags
    in.ignore(std::numeric_limits<std::streamsize>::max(), ' ');     // drop "oops"
    in >> c;
    std::cout << c << '\n';
}
```

```text
12 0 1
0
34
```

You can ask streams to throw instead with `stream.exceptions(std::ios::failbit | std::ios::badbit)`.
That is useful in code that treats any I/O failure as exceptional, but EOF handling then needs care
(a loop ending on failbit throws unless you handle it).

## Output formatting

Formatting state lives in the stream (`flags()`, `width()`, `precision()`, `fill()`) and manipulators change
it. **Most settings stick** (`std::hex`, `std::fixed`, `std::setprecision`), while `std::setw` applies only
to the next output.

```cpp title="format.cpp" showLineNumbers
#include <iomanip>
#include <iostream>

int main() {
    std::cout << std::boolalpha << true << ' ' << std::noboolalpha << true << '\n';
    std::cout << std::hex << 255 << ' ' << std::showbase << 255 << std::dec << '\n';
    std::cout << std::fixed << std::setprecision(2) << 3.14159 << '\n';
    std::cout << '[' << std::setw(6) << std::setfill('*') << 42 << ']' << '\n';
    std::cout << '[' << std::left << std::setw(6) << 42 << ']' << '\n';
}
```

```text
true 1
ff 0xff
3.14
[****42]
[42****]
```

(`setfill` also sticks, which is why the last line is still filled with `*`.) For long-lived changes in a
library function, save and restore the flags, or format to a temporary `ostringstream`. Since C++20,
`std::format` is the better choice for new code: it has no sticky state, is type safe, and `std::print`
*(C++23, `<print>`)* writes the result directly. See [Strings](./strings.md#formatting).

## Files

`std::ifstream`, `std::ofstream` and `std::fstream` open in the constructor (from a `const char*`,
`std::string` or `std::filesystem::path`) and close in the destructor, so they are
[RAII](../13-idioms-and-design/01-raii.md) objects: no explicit `close()` is needed, and the stream
is closed on every exit path. Check that the open worked:

```cpp
std::ofstream out("data.txt", std::ios::app);   // fragment: modes combine with |
if (!out) { /* open failed: missing directory, permissions, ... */ }
```

| Mode (`std::ios::`) | Meaning |
|---|---|
| `in`, `out` | read / write (`ifstream` and `ofstream` set theirs implicitly) |
| `app` | every write goes to the end |
| `ate` | seek to the end once, after opening |
| `trunc` | discard existing contents (the default for `out` alone) |
| `binary` | no newline translation (matters on Windows) |

A file is written to disk only when the buffer is flushed (`flush()`, destructor, `close()`, or when the
buffer fills). `std::endl` writes `'\n'` **and flushes**, which is slow in a loop; use `'\n'`. `cin` is
tied to `cout`, so `cout` flushes before `cin` reads, so interactive prompts still appear.

## Binary I/O

Use `read`/`write` (unformatted, byte for byte) with the `binary` mode:

```cpp title="binary.cpp" showLineNumbers
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>

struct Header { std::uint32_t magic; std::uint16_t version; std::uint16_t flags; };

int main() {
    auto path = std::filesystem::temp_directory_path() / "kb_header.bin";
    Header h{0xCAFEBABE, 3, 1};
    {
        std::ofstream out(path, std::ios::binary);
        out.write(reinterpret_cast<const char*>(&h), sizeof h);
    }
    Header r{};
    std::ifstream in(path, std::ios::binary);
    in.read(reinterpret_cast<char*>(&r), sizeof r);
    std::cout << in.gcount() << ' ' << std::hex << r.magic << ' ' << r.version << '\n';
    std::filesystem::remove(path);
}
```

```text
8 cafebabe 3
```

This works only because `Header` is trivially copyable and writer and reader run the same ABI. The file
contains the struct's padding and the host's byte order, so it is not a portable format. For a file that
you share between machines, write each field with a fixed width and a chosen byte order (see
[endianness](../12-low-level-and-platform/04-endianness.md)), and check `gcount()` after `read`.

## In-memory streams

`std::ostringstream` builds text with the stream's formatting, and `str()` returns a copy. `std::istringstream`
parses text with `>>`, as in the loop above. `std::stringstream` does both. They allocate and are
slower than `std::format`, `std::to_chars` or `std::from_chars` (see [Strings](./strings.md)); use
them when you need stream formatting or parsing with manipulators.

## Making your type streamable

Overload `operator<<` as a free function that takes the stream by reference and returns it, so
chains work. Don't make it a member of your class (the stream would have to be on the left):

```cpp title="stream-operator.cpp" showLineNumbers
#include <iostream>
#include <sstream>

struct Point { int x, y; };

std::ostream& operator<<(std::ostream& os, const Point& p) {
    return os << '(' << p.x << ", " << p.y << ')';
}

std::istream& operator>>(std::istream& is, Point& p) {
    Point tmp;
    char open, comma, close;
    if (is >> open >> tmp.x >> comma >> tmp.y >> close && open == '(' && comma == ',' && close == ')')
        p = tmp;
    else
        is.setstate(std::ios::failbit);       // report the failure, keep p unchanged
    return is;
}

int main() {
    Point p{1, 2};
    std::cout << p << '\n';
    Point q{};
    std::istringstream in("(3, 4)");
    in >> q;
    std::cout << q << '\n';
}
```

```text
(1, 2)
(3, 4)
```

Keep the output operator free of side effects on stream formatting state: formatting a user type
should not leave the stream in `hex` mode.

## Performance notes

- By default `cin`/`cout` are synchronized with C's `stdin`/`stdout` so mixed use keeps its order.
  `std::ios::sync_with_stdio(false)` removes that overhead, but afterwards do not mix `printf` and `cout`.
  `std::cin.tie(nullptr)` stops flushing `cout` before every read.
- Avoid `std::endl` in loops; avoid reading a file character by character through `operator>>`.
- To read a whole file, `std::ifstream` + `std::istreambuf_iterator<char>` or `read` into a sized string
  (use `file_size`) is much faster than line-by-line when you do not need lines.
- Whether streams are "slow" depends on the library and the workload; measure your case.

## Related

- [Strings](./strings.md): `to_chars`/`from_chars`, `std::format`, and `string_view` for parsing
- [Filesystem](./filesystem.md): paths, `file_size`, and creating directories before opening files
- [Iterators](./iterators.md): `istream_iterator`, `ostream_iterator`, `istreambuf_iterator`
- [RAII](../13-idioms-and-design/01-raii.md): why file streams close themselves
- [Endianness](../12-low-level-and-platform/04-endianness.md): byte order in binary files

## References

- [Input/output library, cppreference](https://en.cppreference.com/w/cpp/io)
- ISO C++ [input.output]
