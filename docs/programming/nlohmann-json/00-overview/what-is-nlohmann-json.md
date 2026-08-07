---
id: what-is-nlohmann-json
title: What is nlohmann/json?
sidebar_label: What is nlohmann/json
sidebar_position: 1
tags: [c++, nlohmann-json, overview, introduction]
---

# What is nlohmann/json?

Before this library, JSON in C++ meant one of two things: a hand-rolled recursive-descent parser
that grew warts with every new corner case, or something like RapidJSON — fast, but with a DOM API
built around explicit allocators, `Value` handles, and a memory pool you had to manage yourself.
Both worked. Neither felt like C++ you'd want to write on a Tuesday afternoon.

[nlohmann/json](https://github.com/nlohmann/json), published under the tagline "JSON for Modern
C++", set out to change that by making a JSON document behave like an ordinary C++ value: something
you can assign into, compare, iterate, and pass around by value, without learning a second API on
top of the standard library you already know.

## One header, C++11, no dependencies

The library ships two ways. The one most people start with is a single amalgamated header,
`json.hpp`, generated from the full source tree — drop it into your include path and you're done.
The other is the `include/nlohmann/` tree, which splits the implementation across many headers and
is what you get from a package manager or `find_package`.

```bash
# grab the single-header release directly
curl -LO https://github.com/nlohmann/json/releases/latest/download/json.hpp
mkdir -p include/nlohmann && mv json.hpp include/nlohmann/
```

Either way, the only thing your code needs is:

```cpp
#include <nlohmann/json.hpp>
using json = nlohmann::json;
```

## JSON as an STL container

The core type, `json`, behaves like a container whenever the underlying value is one. It has
`size()`, `begin()`/`end()`, `push_back()`, `find()` — the same vocabulary you'd use on a
`std::vector` or `std::map`, because internally that's roughly what it is.

```cpp
json j = {{"name", "ada"}, {"skills", json::array({"math", "engines"})}};

std::cout << j.size() << "\n";              // 2 — two top-level keys
for (auto& [key, value] : j.items()) {       // range-for with structured bindings
    std::cout << key << "\n";
}
j["skills"].push_back("navigation");         // "skills" is an array; push_back just works
if (j.find("name") != j.end()) {             // find() like any associative container
    std::cout << "has a name\n";
}
```

That container-first design is why the library reads as C++ rather than as a JSON API bolted onto
C++: once you know `json` can be an object, an array, or a scalar, the rest of the surface follows
from the STL idioms you already have.

## What it deliberately isn't

nlohmann/json is not the fastest JSON parser available for C++, and it doesn't try to be. Parsing
builds a full in-memory DOM with real allocations for every string, array, and object — there's no
zero-copy mode, no SIMD-accelerated tokenizer, no memory arena you control. For most applications
(config files, small-to-medium API payloads, test fixtures) that cost is invisible. For
gigabyte-scale documents or a hot path parsing thousands of small messages per second, it isn't.

:::note[When to look elsewhere]
If throughput or peak memory is the actual constraint, see
[Comparison with alternatives](./comparison-with-alternatives.md) for how RapidJSON, simdjson, and
Boost.JSON trade ergonomics for speed — and when that trade is worth making.
:::

## A first taste

```cpp showLineNumbers title="hello_json.cpp"
#include <nlohmann/json.hpp>
#include <iostream>

using json = nlohmann::json;

int main() {
    // parse a literal
    json j = json::parse(R"({
        "name": "ada",
        "born": 1815
    })");

    // read a field, checked
    std::string name = j.at("name");

    // add a field
    j["profession"] = "mathematician";

    // pretty-print
    std::cout << j.dump(2) << std::endl;
}
```

Running this prints a re-indented document with the new `profession` key included — parse, modify,
and serialize, all without a single explicit allocator or handle in sight.

## See also

- <Icon icon="lucide:compass" inline /> [Design philosophy](./design-philosophy.md) — the goals behind the API and what they cost.
- <Icon icon="lucide:download" inline /> [Installation and integration](./installation-and-integration.md) — the six ways to actually add this to a project.
- <Icon icon="lucide:scale" inline /> [Comparison with alternatives](./comparison-with-alternatives.md) — how it stacks up against RapidJSON, Boost.JSON, and simdjson.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
