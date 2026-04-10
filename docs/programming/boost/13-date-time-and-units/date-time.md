---
id: date-time
title: Boost.Date_Time
sidebar_label: Boost.Date_Time
sidebar_position: 1
tags: [c++, boost, date, time, calendar, posix-time]
---

# Boost.Date_Time

Boost.Date_Time provides **date and time types** for C++: calendar dates (`gregorian::date`),
time-of-day values (`posix_time::ptime`, `posix_time::time_duration`), time zones, periods, and
date arithmetic. It was the first serious date/time library for C++ and influenced both
`std::chrono` (C++11, for durations and clocks) and the calendar additions in C++20.

:::info The problem it solves
`<ctime>` gives you `time_t` and `struct tm` — a raw integer and a broken-down struct with no type
safety, no date arithmetic, no time zones, and one-second resolution. Boost.Date_Time replaces this
with value types where adding "3 months" to a date is a single function call and the compiler
rejects nonsensical operations.
:::

## Gregorian dates

```cpp showLineNumbers title="dates.cpp"
#include <boost/date_time/gregorian/gregorian.hpp>
#include <iostream>

namespace greg = boost::gregorian;

int main() {
    greg::date today  = greg::day_clock::local_day();
    greg::date launch(2026, greg::Apr, 7);

    std::cout << "today:  " << today << "\n";
    std::cout << "launch: " << launch << "\n";

    greg::date_duration diff = today - launch;
    std::cout << "days since launch: " << diff.days() << "\n";

    greg::date next_month = launch + greg::months(1);
    std::cout << "one month later: " << next_month << "\n";
}
```

## Date arithmetic

| Operation | Code | Result type |
|-----------|------|-------------|
| Difference | `d2 - d1` | `date_duration` (days) |
| Add days | `d + days(7)` | `date` |
| Add months | `d + months(3)` | `date` (end-of-month clamped) |
| Add years | `d + years(1)` | `date` |
| Day of week | `d.day_of_week()` | `greg_weekday` (0 = Sunday) |

:::tip End-of-month clamping
Adding one month to January 31 gives February 28 (or 29 in a leap year) — it clamps to the last
valid day rather than overflowing.
:::

## Posix time — date + time of day

`ptime` combines a `date` with a `time_duration` to represent a point in time with microsecond
resolution.

```cpp showLineNumbers title="ptime.cpp"
#include <boost/date_time/posix_time/posix_time.hpp>
#include <iostream>

namespace pt = boost::posix_time;
namespace greg = boost::gregorian;

int main() {
    pt::ptime now = pt::second_clock::local_time();
    std::cout << "now: " << now << "\n";

    pt::ptime meeting(greg::date(2026, 4, 10),
                      pt::hours(14) + pt::minutes(30));
    std::cout << "meeting: " << meeting << "\n";

    pt::time_duration until = meeting - now;
    std::cout << "hours until meeting: " << until.hours() << "\n";
}
```

## Time periods

A `time_period` represents a half-open interval `[begin, end)`. Useful for scheduling, overlap
detection, and containment queries.

```cpp showLineNumbers title="periods.cpp"
#include <boost/date_time/posix_time/posix_time.hpp>

namespace pt = boost::posix_time;
namespace greg = boost::gregorian;

int main() {
    pt::ptime start(greg::date(2026, 4, 7), pt::hours(9));
    pt::ptime end(greg::date(2026, 4, 7), pt::hours(17));
    pt::time_period workday(start, end);

    pt::ptime lunch(greg::date(2026, 4, 7), pt::hours(12));
    bool during_work = workday.contains(lunch); // true
    (void)during_work;
}
```

## Parsing and formatting

```cpp showLineNumbers title="format.cpp"
#include <boost/date_time/posix_time/posix_time.hpp>
#include <iostream>

namespace pt = boost::posix_time;
namespace greg = boost::gregorian;

int main() {
    // Parsing
    greg::date d = greg::from_string("2026-04-07");
    pt::ptime t = pt::time_from_string("2026-04-07 14:30:00");

    // ISO format
    std::cout << greg::to_iso_extended_string(d) << "\n";   // 2026-04-07
    std::cout << pt::to_iso_string(t) << "\n";               // 20260407T143000

    // Simple string
    std::cout << pt::to_simple_string(t) << "\n";            // 2026-Apr-07 14:30:00
}
```

## Boost.Date_Time versus `std::chrono` and C++20 calendar

| Feature | Boost.Date_Time | `std::chrono` (C++11) | C++20 calendar |
|---------|----------------|----------------------|----------------|
| Duration types | `time_duration` | `duration<>` | `duration<>` |
| Calendar dates | `gregorian::date` | No | `year_month_day` |
| Date arithmetic | `+ months(3)` | No | `+ months{3}` |
| Time zones | `local_date_time` | No | `zoned_time` |
| Parsing/formatting | Built-in | `from_stream` (C++20) | `from_stream` |
| Resolution | Microseconds | Arbitrary | Arbitrary |

:::note When to use which
`std::chrono` is the go-to for durations, clocks, and benchmarking. For calendar operations on
C++17 or earlier, Boost.Date_Time fills the gap that `std::chrono` left until C++20. On C++20,
prefer `std::chrono`'s calendar types unless you need Date_Time's time-zone database or are already
using Boost.
:::

## Linking

Date_Time is partially compiled:

```bash
g++ -std=c++17 dates.cpp -lboost_date_time
```

## See also

- <Icon icon="lucide:clock" inline /> [Boost.Chrono](./boost-chrono.md) — Boost's duration/clock library, closer to `std::chrono`.
- <Icon icon="lucide:ruler" inline /> [Boost.Units](./boost-units.md) — dimensional analysis where time is one of the base dimensions.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the standard](../00-overview/boost-and-the-standard.md) — the `std::chrono` lineage.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
