---
id: chrono
title: Chrono Library (Time)
sidebar_label: Chrono
sidebar_position: 7
tags: [c++, chrono, duration, time-point, clocks, steady-clock, system-clock, calendar, time-zones]
---

# Chrono Library (Time)

`<chrono>` is a type-safe way to talk about time. It has three ideas: a **duration** (an amount of
time, such as 250 ms), a **time point** (a duration since a clock's epoch), and a **clock** (a source
of "now" with a stated epoch and properties). Making the unit part of the type removes the classic bug
of passing seconds to a function that wants milliseconds, and conversions are checked at compile time.
C++20 adds calendar dates, time-of-day, time zones and `std::format` support to the same library.

**Prerequisites:** [Class templates](../08-templates-and-metaprogramming/class-templates.md),
[operator overloading](../02-language-fundamentals/operators/operator-overloading.md).

<Diagram title="The three concepts" accent="blue">
  <DiagramRow>
    <DiagramNode title="clock" icon="clock">epoch, tick period, <code>now()</code></DiagramNode>
    <DiagramArrow direction="right" label="now() returns" />
    <DiagramNode title="time_point" accent>duration since the clock's epoch</DiagramNode>
    <DiagramArrow direction="right" label="difference of two" />
    <DiagramNode title="duration">count of ticks of a period</DiagramNode>
  </DiagramRow>
</Diagram>

## Durations

`std::chrono::duration<Rep, Period>` stores a count of type `Rep` of ticks, where each tick is
`Period` seconds (a `std::ratio`, so `std::milli` is 1/1000). The named types are
`nanoseconds`, `microseconds`, `milliseconds`, `seconds`, `minutes`, `hours` (C++11) and `days`,
`weeks`, `months`, `years` (C++20). The first six use signed integers of at least 64, 55, 45, 35,
29 and 23 bits respectively. `months` and `years` are averages (the length of a Gregorian year: 365.2425
days), not calendar units.

```cpp title="durations.cpp" showLineNumbers
#include <chrono>
#include <iostream>

using namespace std::chrono_literals;     // 5s, 250ms, 2h  (C++14)

int main() {
    auto a = 1500ms;                      // std::chrono::milliseconds
    std::chrono::seconds s = 2s;
    auto total = a + s;                   // common type: milliseconds
    std::cout << total.count() << "ms\n"; // count() is the raw tick count

    // Widening is implicit, narrowing needs an explicit cast that truncates
    // std::chrono::seconds bad = a;      // error: would lose precision
    auto trunc = std::chrono::duration_cast<std::chrono::seconds>(total);   // 3 (truncates toward zero)
    auto rnd   = std::chrono::round<std::chrono::seconds>(total);           // 4 (C++17: floor, ceil, round)

    // Floating-point representation: no truncation, fractional seconds are allowed
    std::chrono::duration<double> frac = a;           // 1.5 seconds
    std::cout << trunc.count() << ' ' << rnd.count() << ' ' << frac.count() << '\n';
}
```

```text
3500ms
3 4 1.5
```

- Arithmetic between durations picks the **common type** (the coarsest period that can represent
  both exactly). `+`, `-`, `*` by a number, `/` by a number, and `%` all work.
- Implicit conversion is allowed only when it cannot lose information: integer duration to a finer
  integer duration, or anything to a floating-point duration. Otherwise use `duration_cast`
  (truncates toward zero), or `floor`, `ceil`, `round` *(C++17)*.
- Overflow of the integer representation is signed overflow, which is undefined behavior; for very long
  spans use a larger `Rep`.
- `std::chrono::duration<int, std::ratio<1, 60>>` is a frame at 60 Hz, a typical custom duration.

## Clocks and time points

`std::chrono::time_point<Clock, Duration>` is a `Duration` since the `Clock`'s epoch. Subtracting two
time points of the same clock gives a duration; you cannot mix time points of different clocks.
The standard defines these clocks:

| Clock | Use | Properties |
|---|---|---|
| `system_clock` | wall-clock time, converts to `time_t` | **can jump** when the system time is adjusted; epoch is Unix epoch since C++20 |
| `steady_clock` | measuring intervals and timeouts | `is_steady == true`: never goes backwards; epoch unspecified |
| `high_resolution_clock` | alias for one of the above, depends on the library | libstdc++ makes it `system_clock`; avoid it |
| `utc_clock`, `tai_clock`, `gps_clock`, `file_clock` | *(C++20)* UTC with leap seconds, atomic time, GPS, filesystem timestamps | |

The rule: **use `steady_clock` for elapsed time and timeouts, `system_clock` only for timestamps
you show to people or store**. Measuring with `system_clock` gives wrong, even negative, durations when
NTP or the user steps the clock.

```cpp title="timing.cpp" showLineNumbers
#include <chrono>
#include <iostream>
#include <thread>

int main() {
    using namespace std::chrono;
    using namespace std::chrono_literals;

    auto t0 = steady_clock::now();
    std::this_thread::sleep_for(50ms);                         // at least 50 ms, not exactly
    auto elapsed = steady_clock::now() - t0;

    std::cout << (elapsed >= 50ms) << '\n';                    // 1: sleep_for never wakes early
    std::cout << duration_cast<milliseconds>(elapsed).count() / 1000 << '\n';   // 0 (well under 1 s)
    std::cout << steady_clock::is_steady << '\n';

    auto deadline = steady_clock::now() + 2s;                  // time point + duration
    std::this_thread::sleep_until(deadline - 1990ms);          // absolute-time sleep avoids drift
}
```

```text
1
0
1
```

`sleep_for` has a lower bound only: the OS scheduler can add delay. For a periodic task, compute the next
deadline from the previous **deadline** and use `sleep_until`, so errors do not accumulate. Resolution
and the cost of `now()` are platform dependent (libstdc++ on Linux builds `steady_clock` on `CLOCK_MONOTONIC`;
an implementation detail).

Converting `system_clock` to a calendar form: `system_clock::to_time_t(tp)` gives a `time_t` for
the C APIs (`std::localtime` is not thread-safe; prefer the C++20 types below or `localtime_r`/`localtime_s`).

## Calendar types *(C++20)*

C++20 adds calendar types that do not depend on the C library:

- `year`, `month`, `day`, `weekday`; combinations `year_month_day`, `year_month_weekday`;
  literals `2024y`, `std::chrono::March`, `15d`, and the operator `/` to build dates: `2024y/3/15`
  or `March/15/2024`.
- `sys_days` is a `time_point<system_clock, days>`: the bridge between a calendar date and an
  instant. `year_month_day` converts to `sys_days` and back, and `ok()` tells you if the date exists.
- `hh_mm_ss<Duration>` splits a duration into hours, minutes, seconds and sub-seconds.
- `last` (e.g. `2024y/2/last`) names the last day or weekday of a month.

```cpp title="calendar.cpp" showLineNumbers
#include <chrono>
#include <iostream>

int main() {
    using namespace std::chrono;

    year_month_day d = 2024y / February / 29;
    std::cout << d.ok() << ' ' << (2023y / February / 29).ok() << '\n';

    year_month_day next = d + years{1};                        // 2025-02-29 does not exist
    std::cout << next.ok() << '\n';                            // 0: check ok() or normalize via sys_days

    sys_days sd = sys_days{d} + days{1};
    std::cout << weekday{sd}.c_encoding() << '\n';             // 0 = Sunday ... 6 = Saturday: 2024-03-01 is a Friday (5)

    hh_mm_ss hms{3h + 25min + 7s};
    std::cout << hms.hours().count() << ':' << hms.minutes().count() << ':' << hms.seconds().count() << '\n';
}
```

```text
1 0
0
5
3:25:7
```

Adding `years` or `months` to a `year_month_day` can produce a day that does not exist (Feb 29
plus a year). The result is stored as is and `ok()` returns `false`; you decide whether to clamp
(`year_month_day_last`) or convert through `sys_days`.

### Time zones *(C++20)*

`std::chrono::zoned_time` pairs a time point with a `time_zone` taken from the IANA database
(`std::chrono::locate_zone("Europe/Warsaw")`, or `current_zone()`). Needs a tz database at run
time, which Linux builds usually read from the system `tzdata`. `locate_zone` throws `std::runtime_error` for an unknown name. Converting a `local_time` to an
instant (`to_sys`, or building a `zoned_time` from a `local_time`) throws `nonexistent_local_time` or
`ambiguous_local_time` when a DST change skips or repeats that time. Library support for time zones and for `<format>` of chrono types arrived later than the calendar
types and differs between libstdc++, libc++ and MSVC, so check yours before relying on it.

```cpp
// fragment: needs a C++20 library with tzdb support and installed tzdata
auto now = std::chrono::floor<std::chrono::seconds>(std::chrono::system_clock::now());
std::chrono::zoned_time warsaw{"Europe/Warsaw", now};
std::cout << std::format("{:%F %T %Z}", warsaw) << '\n';   // e.g. 2025-06-01 14:03:20 CEST
```

## Formatting and parsing *(C++20)*

`std::format("{}", tp)` and `std::format("{:%Y-%m-%d %H:%M}", tp)` print time points, durations and calendar
types, with `strftime`-like specifiers (`<format>` support in your library is required).
`std::chrono::from_stream` / `std::chrono::parse` read them back. Durations print their unit:

```cpp title="format.cpp"
// compile: g++ -std=c++20
#include <chrono>
#include <format>
#include <iostream>

int main() {
    using namespace std::chrono_literals;
    std::cout << std::format("{} {} {}\n", 90s, 1500ms, 2h);
    std::cout << std::format("{:%Y-%m-%d}\n", std::chrono::year_month_day{2024y / 3 / 15});
}
```

```text
90s 1500ms 2h
2024-03-15
```

## Pitfalls

- **Using `system_clock` to measure intervals.** Use `steady_clock`.
- **Integer division in conversions**: `duration_cast<seconds>(1999ms)` is 1, not 2. Use
  `round`, or a `duration<double>`.
- **Mixing `count()` and unit-less numbers**: `sleep_for(std::chrono::milliseconds(n))` is
  explicit, whereas `.count()` loses the unit. Keep values in duration types until the
  last moment (for example, when calling a C API).
- **Timing one tiny operation**: `now()` itself costs time and the clock has finite resolution. Time
  many iterations and divide.
- **`high_resolution_clock`** can be an alias of `system_clock` (so not steady). Use `steady_clock`.
- **Benchmarking**: the compiler may delete code whose result is unused; see [perf tools](../14-debugging-and-profiling/06-perf-tools.md).

## Related

- [Threads](../11-concurrency-and-memory-model/04-threads.md): `sleep_for`, `sleep_until`, `wait_for`
  and `wait_until` take durations and time points
- [Filesystem](./filesystem.md): `file_time_type` is a `time_point<file_clock>`
- [Strings](./strings.md): `std::format`, and converting numbers to text
- [Algorithms](./algorithms.md): `std::chrono` durations work with `std::accumulate` and friends

## References

- [Date and time library, cppreference](https://en.cppreference.com/w/cpp/chrono)
- ISO C++ [time]
