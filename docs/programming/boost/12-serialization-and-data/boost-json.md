---
id: boost-json
title: Boost.JSON
sidebar_label: Boost.JSON
sidebar_position: 3
tags: [c++, boost, json, parsing, serialization]
---

# Boost.JSON

Boost.JSON is a **header-only**, RFC 8259 compliant JSON library added in Boost 1.75. It provides
a DOM-style `value` type (object, array, string, number, bool, null), a SAX-style streaming parser,
and a serializer — all designed for performance, with a `memory_resource` interface for custom
allocation and no dependency on exceptions for error reporting.

:::info The problem it solves
C++ has no standard JSON library. PropertyTree can read JSON but loses type information (everything
becomes a string) and ignores `null`. Third-party libraries like nlohmann/json are popular but
external dependencies. Boost.JSON gives you production-quality JSON with the same trust chain as
the rest of Boost.
:::

## Parsing JSON

```cpp showLineNumbers title="parse.cpp"
#include <boost/json.hpp>
#include <iostream>

namespace json = boost::json;

int main() {
    auto jv = json::parse(R"({
        "name": "Ada",
        "age": 36,
        "languages": ["C++", "Haskell"]
    })");

    auto& obj = jv.as_object();
    std::cout << obj["name"].as_string() << "\n";        // Ada
    std::cout << obj["age"].as_int64() << "\n";           // 36
    std::cout << obj["languages"].as_array()[0] << "\n";  // "C++"
}
```

## Building JSON values

```cpp showLineNumbers title="build.cpp"
#include <boost/json.hpp>
#include <iostream>

namespace json = boost::json;

int main() {
    json::object obj;
    obj["host"] = "localhost";
    obj["port"] = 8080;
    obj["features"] = json::array{"auth", "logging"};

    std::cout << json::serialize(obj) << "\n";
    // {"host":"localhost","port":8080,"features":["auth","logging"]}
}
```

## Value types

| JSON type | C++ accessor | Underlying type |
|-----------|-------------|-----------------|
| object | `as_object()` | `json::object` (ordered key-value) |
| array | `as_array()` | `json::array` |
| string | `as_string()` | `json::string` (SSO-optimised) |
| number (int) | `as_int64()` / `as_uint64()` | `std::int64_t` / `std::uint64_t` |
| number (float) | `as_double()` | `double` |
| boolean | `as_bool()` | `bool` |
| null | `is_null()` | `json::value{}` |

:::tip Kind checking
Use `jv.kind()` or `jv.is_object()`, `jv.is_string()`, etc. before calling `as_*()` — accessing
the wrong kind throws `std::invalid_argument`.
:::

## Custom type conversion with value_from / value_to

Map your own types to and from JSON by specialising `tag_invoke`:

```cpp showLineNumbers title="custom_type.cpp"
#include <boost/json.hpp>

struct Point {
    double x, y;
};

void tag_invoke(json::value_from_tag, json::value& jv, const Point& p) {
    jv = {{"x", p.x}, {"y", p.y}};
}

Point tag_invoke(json::value_to_tag<Point>, const json::value& jv) {
    auto& obj = jv.as_object();
    return {obj.at("x").as_double(), obj.at("y").as_double()};
}

// Usage:
// json::value jv = json::value_from(Point{1.5, 2.5});
// Point p = json::value_to<Point>(jv);
```

## Streaming parser

For large or incrementally arriving JSON, use `json::stream_parser` instead of loading everything
into memory at once:

```cpp showLineNumbers title="stream.cpp"
#include <boost/json.hpp>

namespace json = boost::json;

json::value parse_chunks(const std::vector<std::string>& chunks) {
    json::stream_parser parser;
    for (auto& chunk : chunks)
        parser.write(chunk);
    parser.finish();
    return parser.release();
}
```

## Error handling without exceptions

Every parsing function has an overload that takes a `boost::system::error_code`:

```cpp showLineNumbers
boost::system::error_code ec;
auto jv = json::parse("{invalid", ec);
if (ec) {
    std::cerr << "parse error: " << ec.message() << "\n";
}
```

## Memory resources

Boost.JSON uses `boost::json::memory_resource` (compatible with `std::pmr::memory_resource`) for
all allocations. You can supply a monotonic buffer, a pool, or any custom allocator:

```cpp showLineNumbers
#include <boost/json.hpp>

unsigned char buf[4096];
json::static_resource mr(buf, sizeof(buf));
auto jv = json::parse(R"({"key": "value"})", &mr);
```

:::note Performance
Boost.JSON is designed for speed. It uses short-string optimisation, avoids unnecessary copies,
and allows zero-allocation parsing via memory resources. Benchmarks regularly show it competitive
with RapidJSON.
:::

## Boost.JSON versus alternatives

| Feature | Boost.JSON | nlohmann/json | PropertyTree | RapidJSON |
|---------|-----------|---------------|--------------|-----------|
| RFC 8259 compliant | Yes | Yes | No | Yes |
| Type fidelity | Full | Full | Strings only | Full |
| Header-only | Yes | Yes | Yes | Yes |
| Memory resource | Yes | No | No | Yes |
| Custom type mapping | `value_from` / `value_to` | `to_json` / `from_json` | No | No |
| Part of Boost | Yes | No | Yes | No |

## See also

- <Icon icon="lucide:database" inline /> [Boost.PropertyTree](./boost-property-tree.md) — simpler config-file parsing when type fidelity is not critical.
- <Icon icon="lucide:database" inline /> [Boost.Serialization](./boost-serialization.md) — binary/text serialization of full C++ object graphs.
- <Icon icon="lucide:network" inline /> [Boost.Beast](../11-networking/boost-beast.md) — HTTP client/server that often needs JSON parsing.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
