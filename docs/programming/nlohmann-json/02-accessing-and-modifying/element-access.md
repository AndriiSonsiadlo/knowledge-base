---
id: element-access
title: Element access
sidebar_label: Element access
sidebar_position: 1
tags: [c++, nlohmann-json, access, operator, at]
---

# Element access

There are four ways to read a key or index out of a `json`, and they disagree on what happens when
the key is missing — the choice is rarely which one is "correct" and always which behaviour you
actually want at that call site.

## The four accessors

| Accessor | Missing key | Wrong type | Const-safe |
|---|---|---|---|
| `operator[]` | Creates it (non-const) / UB-adjacent throw (const) | `type_error` | No — mutates on non-const |
| `.at(key)` | Throws `out_of_range` | Throws `type_error` | Yes |
| `.value(key, default)` | Returns `default` | Throws `type_error` | Yes |
| `.find(key)` | Returns `end()` | — (returns iterator regardless) | Yes |

## Auto-vivification

:::danger[Non-const operator[] inserts]
`operator[]` on a non-const `json` object silently creates the key if it's missing, with a `null`
value — even in code that only meant to *read*:

```cpp showLineNumbers
json config = json::parse(R"({"host": "localhost"})");

if (config["port"] == 0) {   // looks like a read...
    // ...but config now HAS a "port" key with value null,
    // because operator[] just created it to evaluate the comparison
}

std::cout << config.dump(2);
// {
//   "host": "localhost",
//   "port": null
// }
```

The fix is to not use `operator[]` for a conditional read: `.contains("port")` checks existence
without creating anything, and `.at("port")` throws instead of silently inserting:

```cpp
if (config.contains("port")) { /* ... */ }
auto port = config.at("port");  // throws out_of_range if missing, never inserts
```
:::

## contains(), find(), count()

```cpp
if (config.contains("port")) {
    // safe, doesn't create "port"
}

auto it = config.find("port");
if (it != config.end()) {
    std::cout << *it << "\n";
}

std::size_t n = config.count("port");   // 0 or 1 for an object
```

`find()` is the cheapest "check then use" pattern — it does a single lookup and gives you both the
existence check and the value in one call, versus `contains()` followed by a separate `operator[]`
or `.at()` doing the lookup twice.

## Arrays

Arrays have the same `operator[]` vs `.at()` split, but the failure mode for `operator[]` is
different again:

:::danger[Array operator[] past the end resizes, it doesn't throw]
```cpp
json arr = json::array({1, 2, 3});
arr[10] = 99;   // resizes the array to 11 elements, filling 3..9 with null
```

`.at(index)` throws `out_of_range` instead of resizing, which is almost always what you want when
the index came from anywhere other than code that's deliberately growing the array.
:::

## Erasing

`erase()` is overloaded for a key, an iterator, or an index, matching whichever container shape the
`json` currently has:

```cpp
obj.erase("port");        // erase by key (object)
obj.erase(obj.find("x")); // erase by iterator
arr.erase(0);              // erase by index (array)
```

## See also

- <Icon icon="lucide:check-circle" inline /> [Type checking and conversions](./type-checking-and-conversions.md) — extracting a typed value once you've located it.
- <Icon icon="lucide:repeat" inline /> [Iterating JSON](./iterating-json.md) — walking every element instead of looking one up.
- <Icon icon="lucide:map-pin" inline /> [JSON Pointer and JSON Patch](./json-pointer-and-patch.md) — addressing deeply nested elements by path.
- <Icon icon="lucide:plus" inline /> [Creating JSON values](../01-basics/creating-json-values.md) — the construction side of `operator[]`.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
