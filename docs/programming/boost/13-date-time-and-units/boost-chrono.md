---
id: boost-chrono
title: Boost.Chrono
sidebar_label: Boost.Chrono
sidebar_position: 2
tags: [c++, boost, chrono, duration, clock, time]
---

# Boost.Chrono

Boost.Chrono is the **duration, time_point, and clock** library that directly preceded `std::chrono`
in C++11. The standard adopted Boost.Chrono almost verbatim, so the two APIs are nearly identical.
Where Boost.Chrono still adds value today is its **process CPU clocks** — clocks that measure how
much CPU time (user or system) a process has consumed — which `std::chrono` does not provide.

:::info The problem it solves
`clock()` from `<ctime>` returns a count with platform-dependent resolution and semantics. On some
systems it measures wall time, on others CPU time. Boost.Chrono gives you distinct clock types with
well-defined behaviour: `system_clock` for wall time, `steady_clock` for monotonic intervals, and
`process_*_cpu_clock` for profiling.
:::

## Durations

A `duration` is a time span with compile-time-known units:

```cpp showLineNumbers title="durations.cpp"
#include <boost/chrono.hpp>
#include <iostream>

namespace chrono = boost::chrono;

int main() {
    chrono::seconds s(90);
    chrono::minutes m = chrono::duration_cast<chrono::minutes>(s);  // 1

    auto total = chrono::hours(2) + chrono::minutes(30);
    std::cout << total.count() << " minutes\n";  // 150

    chrono::milliseconds ms(1500);
    chrono::seconds sec = chrono::duration_cast<chrono::seconds>(ms);  // 1
    std::cout << sec.count() << "s\n";
}
```

:::note duration_cast
Converting from a finer to a coarser resolution requires an explicit `duration_cast` — it truncates,
not rounds. This prevents accidental precision loss.
:::

## Clocks and time_point

```cpp showLineNumbers title="clocks.cpp"
#include <boost/chrono.hpp>
#include <iostream>
#include <thread>

namespace chrono = boost::chrono;

int main() {
    auto start = chrono::steady_clock::now();

    // simulate work
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    auto end = chrono::steady_clock::now();
    auto elapsed = chrono::duration_cast<chrono::milliseconds>(end - start);
    std::cout << "elapsed: " << elapsed.count() << " ms\n";
}
```

## Available clocks

| Clock | What it measures | Monotonic |
|-------|-----------------|-----------|
| `system_clock` | Wall-clock time (epoch-based) | No |
| `steady_clock` | Monotonic intervals (never goes backward) | Yes |
| `high_resolution_clock` | Finest available tick | Depends |
| `process_real_cpu_clock` | Wall time consumed by the process | Yes |
| `process_user_cpu_clock` | User-mode CPU time | Yes |
| `process_system_cpu_clock` | Kernel-mode CPU time | Yes |
| `process_cpu_clock` | Combined (real, user, system) | Yes |
| `thread_clock` | CPU time for the calling thread | Yes |

:::tip Process clocks — the unique feature
`std::chrono` has `system_clock`, `steady_clock`, and `high_resolution_clock`, but no process or
thread CPU clocks. If you need to measure how much CPU your code actually consumed (excluding I/O
waits and other processes), `process_user_cpu_clock` is the tool.
:::

## Process CPU time example

```cpp showLineNumbers title="cpu_time.cpp"
#include <boost/chrono.hpp>
#include <boost/chrono/process_cpu_clocks.hpp>
#include <iostream>
#include <vector>
#include <algorithm>

namespace chrono = boost::chrono;

int main() {
    auto start = chrono::process_user_cpu_clock::now();

    // CPU-bound work
    std::vector<int> v(10'000'000);
    std::iota(v.begin(), v.end(), 0);
    std::sort(v.begin(), v.end(), std::greater<>());

    auto end = chrono::process_user_cpu_clock::now();
    auto cpu = chrono::duration_cast<chrono::milliseconds>(end - start);
    std::cout << "CPU time: " << cpu.count() << " ms\n";
}
```

## I/O formatting

Boost.Chrono provides stream insertion that automatically selects the right unit suffix:

```cpp showLineNumbers
#include <boost/chrono.hpp>
#include <boost/chrono/chrono_io.hpp>
#include <iostream>

namespace chrono = boost::chrono;

int main() {
    chrono::milliseconds d(4200);
    std::cout << d << "\n";  // "4200 milliseconds"

    auto s = chrono::duration_cast<chrono::seconds>(d);
    std::cout << s << "\n";  // "4 seconds"
}
```

## Boost.Chrono versus std::chrono

| Feature | `boost::chrono` | `std::chrono` (C++11) |
|---------|----------------|----------------------|
| Durations | Yes | Yes (identical API) |
| system / steady / high_res clocks | Yes | Yes |
| Process CPU clocks | Yes | No |
| Thread clock | Yes | No |
| I/O formatting | Built-in | C++20 `std::format` |
| `duration_cast` | Yes | Yes |

:::note Migration
If you only need durations, time_points, and the three standard clocks, `std::chrono` is a direct
replacement — the API was designed to be source-compatible. Keep Boost.Chrono when you use the
process or thread CPU clocks.
:::

## Linking

Boost.Chrono is compiled:

```bash
g++ -std=c++17 clocks.cpp -lboost_chrono -lboost_system
```

## See also

- <Icon icon="lucide:clock" inline /> [Boost.Date_Time](./date-time.md) — calendar dates and time-of-day types.
- <Icon icon="lucide:ruler" inline /> [Boost.Units](./boost-units.md) — dimensional analysis where time is a measured quantity.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the standard](../00-overview/boost-and-the-standard.md) — the `std::chrono` lineage.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
