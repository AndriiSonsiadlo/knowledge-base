---
id: adl-serializer-and-templates
title: adl_serializer and template types
sidebar_label: adl_serializer
sidebar_position: 3
tags: [c++, nlohmann-json, custom-types, templates]
---

# adl_serializer and template types

Free-function `to_json`/`from_json` only works when you can add a function to the type's own
namespace — which you can't do for third-party types you don't own, and which doesn't compose
cleanly for templates. `adl_serializer` is the library's other customization point, and it covers
both cases.

## The template

You specialize `nlohmann::adl_serializer` for the type in question, inside the `nlohmann`
namespace:

```cpp showLineNumbers
namespace nlohmann {

template <>
struct adl_serializer<ThirdPartyType> {
    static void to_json(json& j, const ThirdPartyType& value) {
        j = /* ... */;
    }

    static void from_json(const json& j, ThirdPartyType& value) {
        /* ... */
    }
};

}  // namespace nlohmann
```

This is what the library actually calls internally for every type's conversion — the free-function
mechanism from [to_json and from_json](./to_json-and-from_json.md) is itself implemented as the
*default* `adl_serializer`, which just forwards to `to_json`/`from_json` found by ADL. Specializing
`adl_serializer` directly bypasses that indirection.

## The from_json returning form

For a type that can't be default-constructed, `adl_serializer` supports a second form of
`from_json` that returns a fully-built value instead of populating an existing one:

```cpp
namespace nlohmann {

template <>
struct adl_serializer<NoDefaultCtor> {
    static void to_json(json& j, const NoDefaultCtor& value) { /* ... */ }

    static NoDefaultCtor from_json(const json& j) {
        return NoDefaultCtor(/* args extracted from j */);
    }
};

}  // namespace nlohmann
```

:::tip[This is the only way to support a type with no default constructor]
The free-function `from_json(const json&, T&)` form requires the library to default-construct a `T`
before it can call your function to fill it in. If `T` has no default constructor, that's not
possible — the returning `adl_serializer::from_json(const json&) -> T` form sidesteps the problem
entirely by handing the fully-constructed object back directly.
:::

## Partial specialization for templates

The same mechanism handles template types via partial specialization — one specialization covers
every instantiation of, say, `std::optional<T>`, rather than writing a serializer per concrete type:

```cpp showLineNumbers title="optional_serializer.hpp"
namespace nlohmann {

template <typename T>
struct adl_serializer<std::optional<T>> {
    static void to_json(json& j, const std::optional<T>& opt) {
        if (opt.has_value()) {
            j = *opt;
        } else {
            j = nullptr;
        }
    }

    static void from_json(const json& j, std::optional<T>& opt) {
        if (j.is_null()) {
            opt.reset();
        } else {
            opt = j.get<T>();
        }
    }
};

}  // namespace nlohmann
```

With this in place, `std::optional<int>` (and every other `std::optional<T>`) serializes as either
the wrapped value or `null`, without a separate specialization per `T`.

## Third-party types

The same pattern covers types you can't touch at all, like `std::chrono::system_clock::time_point`,
by defining the conversion in terms of a format you control — here, an ISO-8601 string:

```cpp
namespace nlohmann {

template <>
struct adl_serializer<std::chrono::system_clock::time_point> {
    static void to_json(json& j, const std::chrono::system_clock::time_point& tp) {
        j = format_iso8601(tp);   // your own formatting helper
    }

    static void from_json(const json& j, std::chrono::system_clock::time_point& tp) {
        tp = parse_iso8601(j.get<std::string>());   // your own parsing helper
    }
};

}  // namespace nlohmann
```

## Which mechanism should I use?

| Situation | Free functions | Macro | adl_serializer |
|---|---|---|---|
| You own the type, default-constructible | Yes — simplest option | Yes — less boilerplate | Overkill |
| You own the type, no default constructor | No | No | Yes (returning form) |
| Third-party type you don't own | No (can't add to its namespace) | No | Yes |
| Template type (e.g. `std::optional<T>`) | Awkward — needs a function per instantiation | No | Yes (partial specialization) |
| Need renaming, versioning, or custom logic | Yes | No | Yes |

## See also

- <Icon icon="lucide:shuffle" inline /> [to_json and from_json](./to_json-and-from_json.md) — the mechanism `adl_serializer`'s default implementation forwards to.
- <Icon icon="lucide:code" inline /> [Serialization macros](./serialization-macros.md) — the fastest path when the type is a plain struct you own.
- <Icon icon="lucide:sliders" inline /> [Custom allocators and JSON types](../05-numbers-memory-and-performance/custom-allocators-and-json-types.md) — the `JSONSerializer` template parameter this all plugs into.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
