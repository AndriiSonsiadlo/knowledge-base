---
id: boost-process
title: Boost.Process
sidebar_label: Boost.Process
sidebar_position: 4
tags: [c++, boost, process, subprocess, child]
---

# Boost.Process

`boost::process` provides **cross-platform subprocess management** — launch child processes, capture
their standard output and error, pipe data in, set environment variables, and wait for or
asynchronously monitor completion. It replaces platform-specific calls like `fork`/`exec`, `popen`,
or `CreateProcess` with a single portable API.

:::info The problem it solves
Launching a child process from C++ is surprisingly platform-dependent: POSIX uses `fork`/`exec`
with file-descriptor plumbing, Windows uses `CreateProcess` with `STARTUPINFO` handles. Error
handling, pipe setup, and environment manipulation differ completely. Boost.Process wraps all of
this into a clean, cross-platform interface that works with Boost.Asio for async I/O.
:::

## Launching a simple command

```cpp showLineNumbers title="simple_launch.cpp"
#include <boost/process.hpp>
#include <iostream>

namespace bp = boost::process;

int main() {
    int result = bp::system("ls -la /tmp");  // blocks until child exits
    std::cout << "exit code: " << result << "\n";
}
```

`bp::system` is the simplest form — it runs the command, waits, and returns the exit code. For more
control, use `bp::child` directly.

## Capturing output

```cpp showLineNumbers title="capture_output.cpp"
#include <boost/process.hpp>
#include <iostream>
#include <string>

namespace bp = boost::process;

int main() {
    bp::ipstream out_stream;
    bp::child c("uname -a", bp::std_out > out_stream);

    std::string line;
    while (std::getline(out_stream, line)) {
        std::cout << "child says: " << line << "\n";
    }

    c.wait();
    std::cout << "exit code: " << c.exit_code() << "\n";
}
```

Redirect operators control where standard streams go:

| Syntax | Effect |
|--------|--------|
| `bp::std_out > stream` | capture stdout into a `bp::ipstream` |
| `bp::std_err > stream` | capture stderr |
| `bp::std_in < stream` | feed stdin from a `bp::opstream` |
| `bp::std_out > bp::null` | discard stdout |
| `bp::std_err > bp::std_out` | merge stderr into stdout |

## Piping data to a child

```cpp showLineNumbers title="pipe_input.cpp"
#include <boost/process.hpp>
#include <iostream>

namespace bp = boost::process;

int main() {
    bp::opstream in_stream;
    bp::ipstream out_stream;
    bp::child c("sort", bp::std_in < in_stream, bp::std_out > out_stream);

    in_stream << "banana\napple\ncherry\n";
    in_stream.pipe().close();  // signal EOF so sort produces output

    std::string line;
    while (std::getline(out_stream, line))
        std::cout << line << "\n";

    c.wait();
}
```

:::warning Close the input pipe
Many child programs (like `sort`, `cat`, `wc`) only produce output after receiving EOF on stdin.
Call `in_stream.pipe().close()` to signal end of input, or the child will block forever.
:::

## Setting the environment

```cpp showLineNumbers title="environment.cpp"
#include <boost/process.hpp>

namespace bp = boost::process;

int main() {
    auto env = boost::this_process::environment();
    env["MY_VAR"] = "hello";

    bp::child c("printenv MY_VAR", bp::env(env));
    c.wait();
}
```

## Async I/O with Asio

For non-blocking process I/O, integrate with `boost::asio::io_context`:

```cpp showLineNumbers title="async_process.cpp"
#include <boost/process.hpp>
#include <boost/asio.hpp>
#include <iostream>
#include <string>

namespace bp = boost::process;

int main() {
    boost::asio::io_context ioc;
    std::string output;

    bp::child c("find /usr -name '*.h' -maxdepth 3",
                bp::std_out > boost::asio::buffer(output),
                bp::on_exit([](int code, const std::error_code&) {
                    std::cout << "child exited with " << code << "\n";
                }),
                ioc);

    ioc.run();
    c.wait();
}
```

:::note Boost.Process v2
Boost 1.84+ ships a redesigned **Boost.Process v2** with tighter Asio integration, `async_pipe`,
and a process-handle concept. If you are starting new code, consider v2. The examples above use the
v1 API which remains available and widely deployed.
:::

## Linking

Boost.Process is mostly header-only but depends on Boost.Filesystem and Boost.System at link time
(and optionally Boost.Asio for async):

```cmake
find_package(Boost REQUIRED COMPONENTS filesystem system)
target_link_libraries(myapp PRIVATE Boost::filesystem Boost::system)
```

## See also

- <Icon icon="lucide:hard-drive" inline /> [Boost.Filesystem](./boost-filesystem.md) — path handling, often used to locate executables.
- <Icon icon="lucide:waypoints" inline /> [Boost.Asio](../09-concurrency-and-async/boost-asio.md) — the async I/O framework that Process integrates with.
- <Icon icon="lucide:package" inline /> [Boost.DLL](./boost-dll.md) — load shared libraries at runtime, the in-process counterpart.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
