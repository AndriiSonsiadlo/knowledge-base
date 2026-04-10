---
id: boost-stacktrace
title: Boost.Stacktrace
sidebar_label: Boost.Stacktrace
sidebar_position: 2
tags: [c++, boost, stacktrace, debugging, backtrace]
---

# Boost.Stacktrace

Boost.Stacktrace lets you **capture and print call stacks programmatically** from within a C++
program. It is invaluable for diagnostics: you can attach a stack trace to an exception, log it
on assertion failure, or dump it in a signal handler for post-mortem debugging. It directly
inspired C++23's `std::stacktrace`.

:::info The problem it solves
When something goes wrong in production, knowing *what* went wrong is only half the story — you
need to know *where*. A debugger is not always available. Boost.Stacktrace captures the call
chain at any point in the program so you can log it, attach it to an error report, or print it
to stderr before aborting.
:::

## Capturing a stack trace

```cpp showLineNumbers title="capture.cpp"
#include <boost/stacktrace.hpp>
#include <iostream>

void inner() {
    std::cout << boost::stacktrace::stacktrace() << "\n";
}

void outer() { inner(); }

int main() {
    outer();
}
```

```bash
g++ -std=c++17 capture.cpp -lboost_stacktrace_backtrace -ldl -DBOOST_STACKTRACE_USE_BACKTRACE -o capture
./capture
```

Output shows function names, source files, and line numbers (when debug info is available):

```
 0# inner() at capture.cpp:5
 1# outer() at capture.cpp:8
 2# main at capture.cpp:11
```

## Backends

Boost.Stacktrace supports multiple backends, chosen at compile time via a preprocessor define
and the corresponding library to link:

| Backend | Define | Link | Platform | Quality |
|---------|--------|------|----------|---------|
| `backtrace` | `BOOST_STACKTRACE_USE_BACKTRACE` | `-lboost_stacktrace_backtrace -ldl` | Linux/macOS | Best on Linux |
| `addr2line` | `BOOST_STACKTRACE_USE_ADDR2LINE` | `-lboost_stacktrace_addr2line -ldl` | Linux | Slower, no library needed |
| `noop` | `BOOST_STACKTRACE_USE_NOOP` | `-lboost_stacktrace_noop` | Any | Compiles but captures nothing |
| `windbg` | `BOOST_STACKTRACE_USE_WINDBG` | (automatic) | Windows | Uses DbgHelp |
| Basic (default) | (none) | `-lboost_stacktrace_basic` | Any | Mangled names only |

:::tip Choosing a backend
On Linux, prefer `backtrace` — it gives demangled names and line numbers with minimal overhead.
On Windows, `windbg` is the natural choice. Use `noop` to compile out stack traces in release
builds with zero cost.
:::

## Attaching to exceptions

A powerful pattern: capture the stack trace at the throw site and carry it inside the exception:

```cpp showLineNumbers title="exception_trace.cpp"
#include <boost/stacktrace.hpp>
#include <stdexcept>
#include <sstream>
#include <iostream>

class traced_error : public std::runtime_error {
    boost::stacktrace::stacktrace trace_;
public:
    traced_error(const std::string& msg)
        : std::runtime_error(msg)
        , trace_(boost::stacktrace::stacktrace()) {}

    const boost::stacktrace::stacktrace& trace() const { return trace_; }
};

void might_fail() {
    throw traced_error("something broke");
}

int main() {
    try {
        might_fail();
    } catch (const traced_error& e) {
        std::cerr << e.what() << "\nStack:\n" << e.trace() << "\n";
    }
}
```

## Signal handlers

Dump a stack trace on SIGSEGV or SIGABRT for post-mortem analysis. Boost.Stacktrace provides a
safe helper that writes to a file descriptor (async-signal-safe):

```cpp showLineNumbers title="signal_handler.cpp"
#include <boost/stacktrace.hpp>
#include <csignal>
#include <cstdlib>

void handler(int signum) {
    ::signal(signum, SIG_DFL);
    boost::stacktrace::safe_dump_to("./backtrace.dump");
    ::raise(signum);
}

int main() {
    ::signal(SIGSEGV, &handler);
    ::signal(SIGABRT, &handler);

    int* p = nullptr;
    *p = 42;  // triggers SIGSEGV
}
```

:::warning Async-signal safety
Most Boost.Stacktrace operations are **not** async-signal-safe. Inside a signal handler, use only
`safe_dump_to()`, which writes raw addresses to a file. Decode the dump later with
`boost::stacktrace::stacktrace::from_dump()` in a separate process.
:::

## Iterating over frames

```cpp showLineNumbers
auto st = boost::stacktrace::stacktrace();
for (const auto& frame : st) {
    std::cout << frame.name()        << " "
              << frame.source_file() << ":"
              << frame.source_line() << "\n";
}
```

## Boost.Stacktrace vs std::stacktrace (C++23)

| Feature | `boost::stacktrace` | `std::stacktrace` |
|---------|--------------------|--------------------|
| Standard | Boost | C++23 |
| Header | `<boost/stacktrace.hpp>` | `<stacktrace>` |
| Backend selection | Compile-time defines | Implementation-defined |
| Signal-safe dump | `safe_dump_to()` | Not specified |
| Compiler support | GCC, Clang, MSVC | GCC 12+, MSVC 19.34+ |

:::note Which to choose
On C++23 with a supporting compiler, prefer `std::stacktrace` for portability. Use
Boost.Stacktrace when you need signal-safe dumps, backend selection, or must support pre-C++23
toolchains. See [Boost and the standard](../00-overview/boost-and-the-standard.md) for more
lineage stories.
:::

## See also

- <Icon icon="lucide:flask-conical" inline /> [Boost.Test](./boost-test.md) — attach stack traces to test failure reports.
- <Icon icon="lucide:file-text" inline /> [Boost.Log](./boost-log.md) — log stack traces alongside structured messages.
- <Icon icon="lucide:shield" inline /> [Boost.Assert](../02-core-utilities/boost-assert.md) — custom assertion handlers that can capture a trace.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
