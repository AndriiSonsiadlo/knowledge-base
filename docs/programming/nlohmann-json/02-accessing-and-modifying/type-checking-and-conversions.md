---
id: type-checking-and-conversions
title: Type checking and conversions
sidebar_label: Type checking
sidebar_position: 3
tags: [c++, nlohmann-json, conversion, type-checking]
---

# Type checking and conversions

This is where the library's "intuitive syntax" goal collides most directly with C++ overload
resolution: there are five distinct ways to pull a typed value out of a `json`, and picking the
wrong one for the context is the source of most of the library's rough edges.

## is_*() predicates

```cpp
j.is_null();
j.is_boolean();
j.is_number();            // true for any of the three number kinds below
j.is_number_integer();    // signed integer storage
j.is_number_unsigned();   // unsigned integer storage
j.is_number_float();      // floating-point storage
j.is_string();
j.is_array();
j.is_object();
j.is_binary();
j.is_structured();        // true for object or array
j.is_primitive();         // true for anything that isn't structured
```

`is_number_integer()` and `is_number_unsigned()` reflect how the parser or your code *stored* the
number, not a property of the JSON value itself — see
[Number handling and precision](../05-numbers-memory-and-performance/number-handling-and-precision.md)
for how that storage type gets picked.

## `get<T>()`

Returns a new `T` by value, throwing `type_error` if the stored value can't convert:

```cpp
json j = 42;
int n = j.get<int>();          // 42

json s = "hello";
std::string str = s.get<std::string>();
```

## get_to(x)

Fills an existing object of a deduced type instead of constructing and returning a new one — useful
when `x` already exists and you want to avoid the extra move/copy that `get<T>()` implies:

```cpp
std::string name;
j.at("name").get_to(name);
```

:::tip[Prefer get_to in hot paths]
`get_to` writes into `x` in place rather than constructing a temporary and moving it, which matters
for types where that move isn't free (containers with small-buffer optimizations, types with
non-trivial move constructors). In code that isn't performance-sensitive, `get<T>()` is usually more
readable; reach for `get_to` once profiling says the copy matters.
:::

## `get_ref<T&>()` and `get_ptr<T*>()`

Both give you a reference or pointer directly into the `json`'s internal storage, with no copy at
all:

```cpp
const auto& s = j.get_ref<const json::string_t&>();
auto* p = j.get_ptr<json::number_integer_t*>();
```

:::danger[The reference/pointer dangles if the json is modified or destroyed]
`get_ref` and `get_ptr` hand you a view into memory owned by the `json` object. If that object is
reassigned, destroyed, or the referenced element is erased, the reference or pointer is left
dangling — exactly the same lifetime hazard as taking `&vec[0]` and then calling `push_back` on the
vector. Only use these when the `json`'s lifetime and stability are both guaranteed for as long as
you hold the reference.
:::

## The implicit conversion operator

`json` defines a templated implicit conversion operator, which is why this compiles:

```cpp
json j = "hello";
std::string s = j;   // implicit conversion, deduces T = std::string from the target
```

but `auto s = j;` does **not** give you a `std::string` — `auto` has no target type to deduce the
conversion against, so it just copies the `json` itself. The same ambiguity shows up passing a
`json` to an overloaded function, where the compiler may not have enough context to pick the
conversion you intended.

:::danger[A concrete ambiguity]
```cpp
void handle(int);
void handle(const std::string&);

json j = 42;
handle(j);   // ambiguous: json can implicitly convert to either overload's parameter type
```
If this kind of overload ambiguity is a recurring problem, define `JSON_USE_IMPLICIT_CONVERSIONS 0`
before including the header to disable the operator entirely and force every extraction through
`get<T>()`/`get_to()` explicitly.
:::

## Comparison table

| Method | Copies | Throws | Works on const |
|---|---|---|---|
| `get<T>()` | Yes (returns by value) | `type_error` on mismatch | Yes |
| `get_to(x)` | Depends on `T`'s assignment | `type_error` on mismatch | Yes |
| `get_ref<T&>()` | No | `type_error` on mismatch | Yes (with `const T&`) |
| `get_ptr<T*>()` | No | Never — returns `nullptr` on mismatch | Yes (with `const T*`) |
| Implicit conversion | Yes | `type_error` on mismatch | Yes |
| `.value(key, default)` | Yes | `type_error` if present but wrong type | Yes |

## See also

- <Icon icon="lucide:pointer" inline /> [Element access](./element-access.md) — locating the value before converting it.
- <Icon icon="lucide:shuffle" inline /> [to_json and from_json](../03-custom-type-conversion/to_json-and-from_json.md) — extending `get<T>()` to your own types.
- <Icon icon="lucide:box" inline /> [The JSON value type](../01-basics/the-json-value-type.md) — the underlying storage these methods read from.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
