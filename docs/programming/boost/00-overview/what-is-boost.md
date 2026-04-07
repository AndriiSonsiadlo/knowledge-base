---
id: what-is-boost
title: What is Boost?
sidebar_label: What is Boost
sidebar_position: 1
tags: [ c++, boost, overview, introduction ]
---

# What is Boost?

Boost is a set of free, open-source, **peer-reviewed C++ libraries** that extend the standard library
with facilities the language committee either hasn't standardised yet or never will. It is portable,
header-heavy, and deliberately written to the same quality bar as `std` — to the point that Boost is
the single largest source of *future* standard-library features.

:::info Key characteristics
**Standard-track**: many components (`shared_ptr`, `optional`, `variant`, `filesystem`, `thread`) graduated into the ISO C++ standard.
**Mostly header-only**: most libraries need no separate build step — just add the include path.
**Peer-reviewed**: every library passes a formal community review before acceptance.
:::

## Why Boost exists

The C++ standard library is intentionally small and slow-moving. Boost fills the gap between "what
the standard ships" and "what large C++ projects actually need": networking, parsing, graph
algorithms, multiprecision arithmetic, serialization, and dozens of utilities. It acts as a staging
ground — ideas are battle-tested in Boost for years before the committee considers standardising
them.

```mermaid
flowchart LR
    I[Idea / need] --> B[Boost library]
    B --> R[Community review]
    R --> U[Years of real-world use]
    U --> S[Proposed for ISO C++]
    S --> STD[Standard library]
```

This pipeline is why Boost and `std` feel so similar: `std::shared_ptr`, `std::optional`,
`std::filesystem`, and `std::thread` are all descendants of Boost components. See
[Boost and the standard](./boost-and-the-standard.md) for the full lineage.

## A library *of* libraries

"Boost" is not one library — it is ~160 independent libraries shipped together under one umbrella,
one license, and one release cadence. They range from tiny header-only helpers to large subsystems:

| Scale | Examples | What they are |
|-------|----------|----------------|
| Small utilities | `Optional`, `Any`, `lexical_cast`, `Assert` | Drop-in helpers, header-only |
| Mid-size libraries | `Filesystem`, `Program_options`, `Date_Time` | Focused, sometimes compiled |
| Large subsystems | `Asio`, `Spirit`, `Graph`, `Serialization` | Whole frameworks in themselves |

:::note Capitalisation convention
By convention library names are capitalised and prefixed in prose — *Boost.Asio*, *Boost.Optional* —
but the code lives in lowercase headers (`<boost/asio.hpp>`) and the `boost::` namespace
(`boost::optional`).
:::

## A first taste

Most Boost libraries are header-only, so using one is just an include away:

```cpp showLineNumbers title="optional_demo.cpp"
#include <boost/optional.hpp>
#include <iostream>

boost::optional<int> parse_positive(int x) {
    if (x > 0) return x;       // engaged
    return boost::none;        // empty
}

int main() {
    if (auto v = parse_positive(42)) {
        std::cout << "got " << *v << "\n";
    }
}
```

```bash
# Header-only: just point the compiler at the Boost include root
g++ -std=c++17 -I/usr/include optional_demo.cpp -o demo
```

No `-lboost_optional` is needed — there is no such library to link. The few libraries that *do* need
linking (`Filesystem`, `Thread`, `Program_options`, ...) are covered in
[header-only vs compiled](./header-only-vs-compiled.md).

## What Boost is good for

- **Filling standard-library gaps** — networking ([Asio](../09-concurrency-and-async/boost-asio.md)),
  parsing ([Spirit](../05-strings-and-text/boost-spirit.md)),
  graphs ([BGL](../14-graph-and-geometry/boost-graph.md)).
- **Getting future-standard features early** — use `boost::optional` on a C++14 toolchain that lacks
  `std::optional`.
- **Heavy-duty utilities** — multiprecision integers, dimensional analysis, lock-free queues.
- **Portability** — [Boost.Config](../01-build-and-integration/boost-config.md) abstracts away
  compiler and platform differences.

:::warning Boost is not "free" to depend on
Boost is large. Pulling in even one library brings a sprawling web of internal headers, which inflates
compile times and binary size. Prefer the [standard equivalent](./boost-and-the-standard.md) when one
exists and your toolchain supports it; reach for Boost when it genuinely adds something `std` lacks.
:::

## Where to go next

- [History and philosophy](./history-and-philosophy.md) — how Boost came to be and the principles behind it.
- [Installation](./installation.md) — getting Boost onto your machine.
- [Header-only vs compiled](./header-only-vs-compiled.md) — which libraries need a build step.
- [Boost and the standard](./boost-and-the-standard.md) — the `std` lineage and how to choose.
