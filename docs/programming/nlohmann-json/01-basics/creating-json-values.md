---
id: creating-json-values
title: Creating JSON values
sidebar_label: Creating values
sidebar_position: 2
tags: [c++, nlohmann-json, construction, basics]
---

# Creating JSON values

Construction is where the library's convenience is loudest — you can build a document out of
ordinary C++ values and braces with almost no ceremony — and it's also where its one genuinely
famous ambiguity lives, because braces mean two different things in JSON depending on context.

## Assignment from C++ values

Any of the built-in scalar types, plus `std::vector`-like and `std::map`-like containers, convert
into a `json` on assignment or construction:

```cpp
json j;
j["count"] = 42;
j["ratio"] = 0.5;
j["label"] = "widget";
j["enabled"] = true;
j["parent"] = nullptr;
j["values"] = std::vector<int>{1, 2, 3};
j["lookup"] = std::map<std::string, int>{{"a", 1}, {"b", 2}};
```

Each assignment infers the JSON type from the C++ type on the right: a `std::vector<int>` becomes a
JSON array, a `std::map<std::string, int>` becomes a JSON object, and so on.

## Initializer-list construction

The same values can be written as a single nested initializer list, which reads close to the JSON
text itself:

```cpp
json j = {
    {"a", 1},
    {"b", {1, 2, 3}}
};
```

## The array-vs-object ambiguity

:::danger[Braces are ambiguous between array and object]
`json::json` interprets `{{"a", 1}}` as an object (a list containing one two-element array,
`{"a", 1}`, which looks exactly like a key-value pair) but interprets `{1, 2}` as an array, because
there's no way to read `1` and `2` as a key-value pair. The rule is: a braced initializer list is
treated as an object *only if* every element is itself a two-element array whose first element is a
string — otherwise it's an array. This mostly does the right thing, until it doesn't:

```cpp
json j = json::array({{"a", 1}});   // without json::array(...), this compiles to
                                     // an OBJECT: {"a": 1} — not an array containing
                                     // one two-element array, which is what {{"a",1}} alone means
```

When the shape is ambiguous or the code needs to be unambiguous to a reader, use the explicit
factories instead of bare braces:

```cpp
json arr = json::array({1, 2, 3});
json obj = json::object({{"a", 1}, {"b", 2}});
```
:::

## Building incrementally

Beyond bulk construction, values grow the way STL containers do: `push_back` and `emplace_back` for
arrays, `emplace` for objects, and `operator[]` for either — with the caveat that `operator[]` on a
non-const `json` **auto-vivifies** missing keys/indices rather than reporting them as absent. See
[Element access](../02-accessing-and-modifying/element-access.md) for the full set of accessors and
when that auto-vivification bites.

```cpp
json arr;
arr.push_back(1);
arr.emplace_back(2);

json obj;
obj.emplace("name", "ada");
obj["age"] = 36;   // operator[] creates the "age" key if it doesn't exist yet
```

## ordered_json for stable key order

The default `json` alias stores objects in a `std::map`, which means keys come back out sorted
alphabetically regardless of the order you inserted them — a document built as
`{"z": 1, "a": 2}` dumps as `{"a":2,"z":1}`. That's rarely a problem for machine-to-machine JSON,
but it matters when the output is meant to be diffed, reviewed by a human, or matched against a
reference file with a specific key order. `nlohmann::ordered_json` uses an insertion-order-preserving
map instead, so keys dump in the order they were added.

## See also

- <Icon icon="lucide:box" inline /> [The JSON value type](./the-json-value-type.md) — what these constructions actually produce underneath.
- <Icon icon="lucide:file-json" inline /> [Parsing JSON](./parsing-json.md) — building a value from text instead of C++ code.
- <Icon icon="lucide:pointer" inline /> [Element access](../02-accessing-and-modifying/element-access.md) — the auto-vivification behaviour of `operator[]` in detail.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
