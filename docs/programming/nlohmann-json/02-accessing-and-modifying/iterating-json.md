---
id: iterating-json
title: Iterating JSON
sidebar_label: Iterating
sidebar_position: 2
tags: [c++, nlohmann-json, iteration, range-for]
---

# Iterating JSON

Iterating a `json` container gives you *values*, never key-value pairs — a design choice inherited
from treating `json` as a single unified container type, and the single most common surprise for
people arriving from `std::map`.

## Range-for over an array

For an array this is exactly what you'd expect:

```cpp
json arr = json::array({1, 2, 3});
for (auto& v : arr) {
    std::cout << v << "\n";   // 1, 2, 3
}
```

## Range-for over an object gives values only

:::danger[Range-for over an object yields values, not pairs]
```cpp
json obj = {{"a", 1}, {"b", 2}};
for (auto& v : obj) {
    std::cout << v << "\n";   // 1, 2 — the KEYS are gone
}
```

There's no `.first`/`.second` because the iterator's `value_type` is `json`, not a pair — dereferencing
it gives you the value only. The fix is `.items()`, which yields key-value-like reference wrapper
objects instead of raw values.
:::

## .items() and structured bindings

```cpp
json obj = {{"a", 1}, {"b", 2}};

for (auto& [key, value] : obj.items()) {
    std::cout << key << " = " << value << "\n";
}
```

On pre-C++17 toolchains without structured bindings, the equivalent uses the iterator's `.key()` and
`.value()` directly:

```cpp
for (auto it = obj.begin(); it != obj.end(); ++it) {
    std::cout << it.key() << " = " << it.value() << "\n";
}
```

`.items()` works on arrays too — `key` is then the stringified index (`"0"`, `"1"`, …) — but for
arrays a plain range-for is simpler and doesn't need it.

## Iterator categories and invalidation

| Operation | Invalidates |
|---|---|
| `push_back` / `emplace_back` on an array | May invalidate all iterators (like `std::vector`) |
| `emplace` / `operator[]` on an object | Does not invalidate existing iterators (like `std::map`) |
| `erase(iterator)` | Invalidates the erased iterator and any iterators to it; others remain valid |
| Reassigning the whole `json` (`j = other;`) | Invalidates all iterators into the old value |

The array behaviour follows `std::vector`'s reallocation rules; the object behaviour follows
`std::map`'s node-based stability — same guarantees as the containers each type is built on.

## Iterating nested structures

Walking an arbitrarily nested document means recursing whenever the current value is itself a
container:

```cpp showLineNumbers title="walk.cpp"
void walk(const json& j, int depth = 0) {
    if (j.is_structured()) {           // object or array
        for (auto& [key, value] : j.items()) {
            std::cout << std::string(depth * 2, ' ') << key << ":\n";
            walk(value, depth + 1);
        }
    } else {
        std::cout << std::string(depth * 2, ' ') << j.dump() << "\n";
    }
}
```

`is_structured()` is `true` for objects and arrays and `false` for every scalar type, which makes it
the natural recursion guard for a generic tree walk.

## See also

- <Icon icon="lucide:pointer" inline /> [Element access](./element-access.md) — looking up a single element instead of walking all of them.
- <Icon icon="lucide:check-circle" inline /> [Type checking and conversions](./type-checking-and-conversions.md) — inspecting each visited value's type.
- <Icon icon="lucide:box" inline /> [The JSON value type](../01-basics/the-json-value-type.md) — why arrays and objects share one iteration model.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
