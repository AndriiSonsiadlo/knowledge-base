---
id: to-json-and-from-json
title: to_json and from_json
sidebar_label: to_json / from_json
sidebar_position: 1
tags: [c++, nlohmann-json, custom-types, adl]
---

# to_json and from_json

The library never sees your type definitions — it doesn't know what a `Person` or an `Order` is.
You extend it through two free functions, `to_json` and `from_json`, found by argument-dependent
lookup (ADL) whenever a `json` needs to convert to or from your type.

## The customization point

```cpp showLineNumbers title="person.hpp"
#include <nlohmann/json.hpp>
#include <string>

namespace people {

struct Person {
    std::string name;
    int age;
};

void to_json(nlohmann::json& j, const Person& p) {
    j = nlohmann::json{{"name", p.name}, {"age", p.age}};
}

void from_json(const nlohmann::json& j, Person& p) {
    j.at("name").get_to(p.name);
    j.at("age").get_to(p.age);
}

}  // namespace people
```

Once these two functions exist, `json` and `Person` convert both ways using the ordinary API —
`json(p)`, `j.get<Person>()`, assignment — with no registration step and no virtual dispatch
involved.

## Why the same namespace

:::danger[to_json in the wrong namespace is never found]
`to_json`/`from_json` are located via ADL, which only looks in the namespaces associated with the
function's argument types — here, `people::` (because of `Person`) and `nlohmann::` (because of
`json`). Defining `to_json` in the global namespace, or in an unrelated namespace, for a type that
lives in `people::` means the compiler never finds it: instead of a "no matching function" error at
the call site, you typically get a confusing error deep inside the library about `Person` not being
convertible to `json`. The fix is always the same — the free functions must live in the same
namespace as the type they convert (or in `nlohmann::` itself, though that's reserved for the
library's own specializations and third-party types you don't own).
:::

## Requirements on your type

`from_json` needs to construct a `Person` first (implicitly, via `j.get<Person>()`), which requires
`Person` to be default-constructible so the library can default-construct it and then populate it
field by field.

:::note[No default constructor? Use adl_serializer]
If your type genuinely can't be default-constructed — an immutable value type, a type wrapping a
reference, anything with mandatory constructor arguments — the free-function pattern doesn't apply.
See [adl_serializer and template types](./adl_serializer-and-templates.md) for the
`static T from_json(const json&)` form that returns a fully-constructed value instead of populating
an existing one.
:::

## Round-tripping

```cpp
using people::Person;

Person p{"ada", 36};
json j = p;                    // calls to_json
Person p2 = j.get<Person>();   // calls from_json, default-constructs then fills

Person p3;
j.get_to(p3);                  // also calls from_json, filling an existing Person
```

## Optional and missing fields

Inside `from_json`, the choice between `.at(key)` and `.value(key, default)` is the same choice as
anywhere else in the library, but here it directly encodes which fields are required for your type
and which are optional:

```cpp
void from_json(const nlohmann::json& j, Person& p) {
    j.at("name").get_to(p.name);                  // required: throws if missing
    p.nickname = j.value("nickname", "");          // optional: defaults to "" if absent
}
```

A field read with `.at()` makes a missing key in the input a hard parse error for `Person`; a field
read with `.value()` makes it silently absent. Choose per field based on what your type actually
requires to be valid.

## See also

- <Icon icon="lucide:code" inline /> [Serialization macros](./serialization-macros.md) — generating these two functions instead of writing them by hand.
- <Icon icon="lucide:layers" inline /> [adl_serializer and template types](./adl_serializer-and-templates.md) — the alternative for types without a default constructor.
- <Icon icon="lucide:check-circle" inline /> [Type checking and conversions](../02-accessing-and-modifying/type-checking-and-conversions.md) — the `get<T>()`/`get_to()` machinery these functions plug into.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
