---
id: boost-uuid
title: Boost.UUID
sidebar_label: Boost.UUID
sidebar_position: 2
tags: [ c++, boost, identifiers ]
---

# Boost.UUID

Boost.UUID is a small, header-only library for creating and manipulating **Universally Unique
Identifiers** — the 128-bit values you see written as `f47ac10b-58cc-4372-a567-0e02b2c3d479`. When you
need an identifier that is globally unique without coordinating with a central server or database
sequence, a UUID is the standard answer, and Boost.UUID is the idiomatic way to produce one in C++.

:::info What a UUID actually is
A UUID is 128 bits (16 bytes) with a defined layout (RFC 4122). The canonical text form is 36
characters: 32 hex digits in five hyphen-separated groups, `8-4-4-4-12`. A handful of bits encode the
*version* (how it was generated) and the *variant* (the layout family). Boost.UUID gives you the raw
bytes plus generators and converters.
:::

## The core type: boost::uuids::uuid

`boost::uuids::uuid` is a trivial, fixed-size value type — essentially a `std::array<uint8_t, 16>` with
UUID-aware members. It is cheap to copy, comparable, and has no dynamic allocation. You almost never
fill one in by hand; you ask a *generator* to make one.

```cpp showLineNumbers title="basics.cpp"
#include <boost/uuid/uuid.hpp>            // the uuid type
#include <boost/uuid/uuid_generators.hpp> // the generators
#include <boost/uuid/uuid_io.hpp>         // streaming / to_string
#include <iostream>

int main() {
    boost::uuids::random_generator gen;   // a generator object
    boost::uuids::uuid id = gen();        // produce a value
    std::cout << id << "\n";              // e.g. f47ac10b-58cc-4372-a567-0e02b2c3d479
    std::cout << "size = " << id.size() << " bytes\n";  // 16
    std::cout << "is_nil = " << id.is_nil() << "\n";    // 0
}
```

## Generators

A *generator* is a callable that returns a fresh `uuid`. Which one you choose depends on whether you
want randomness, determinism, or a placeholder.

| Generator | Header | Version | Use it for |
|-----------|--------|---------|------------|
| `random_generator` | `<boost/uuid/random_generator.hpp>` | v4 (random) | The default; unguessable, no inputs |
| `name_generator_sha1` | `<boost/uuid/name_generator_sha1.hpp>` | v5 (name-based) | Deterministic IDs from a namespace + name |
| `string_generator` | `<boost/uuid/string_generator.hpp>` | n/a (parser) | Building a `uuid` from existing text |
| `nil_generator` | `<boost/uuid/nil_generator.hpp>` | nil | The all-zero "no value" UUID |

### random_generator (version 4)

The everyday choice. It draws from a cryptographically seeded PRNG, so collisions are astronomically
unlikely and the value reveals nothing about who or when it was created.

```cpp showLineNumbers title="random.cpp"
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/random_generator.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <iostream>

int main() {
    boost::uuids::random_generator gen;
    for (int i = 0; i < 3; ++i)
        std::cout << gen() << "\n";   // three distinct v4 UUIDs
}
```

### name_generator_sha1 (version 5, deterministic)

Sometimes you want the *same* input to always map to the *same* UUID — for example, deriving a stable
ID for a user from their email, or for a resource from its URL. A name-based generator hashes a
**namespace UUID** together with a **name string**, so the result is reproducible across runs and
machines.

```cpp showLineNumbers title="name_based.cpp"
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/name_generator_sha1.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <iostream>

int main() {
    // Boost ships the standard RFC 4122 namespaces, e.g. ns::url(), ns::dns().
    boost::uuids::name_generator_sha1 gen(boost::uuids::ns::url());

    auto a = gen("https://example.com/users/42");
    auto b = gen("https://example.com/users/42");
    std::cout << (a == b ? "stable\n" : "changed\n");  // stable: same input -> same UUID
    std::cout << a << "\n";
}
```

:::note v3 vs v5
The older `name_generator_md5` produces version-3 (MD5-based) UUIDs. Prefer the SHA1-based
`name_generator_sha1` (version 5) for new code; MD5 only matters for interoperating with systems that
already mandate v3.
:::

### nil_generator and string_generator

`nil_generator` yields the all-zero UUID, useful as a sentinel "no id yet." `string_generator` parses
text back into a `uuid` and is lenient about surrounding braces and hyphens.

```cpp showLineNumbers title="nil_and_parse.cpp"
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/nil_generator.hpp>
#include <boost/uuid/string_generator.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <cassert>

int main() {
    boost::uuids::uuid none = boost::uuids::nil_generator{}();
    assert(none.is_nil());

    boost::uuids::string_generator parse;
    auto a = parse("f47ac10b-58cc-4372-a567-0e02b2c3d479");
    auto b = parse("{f47ac10b-58cc-4372-a567-0e02b2c3d479}"); // braces tolerated
    assert(a == b);
}
```

## Converting to and from strings

For output, `boost::uuids::to_string` (or the `<<` operator from `uuid_io.hpp`) gives the canonical
36-character form. For input, use `string_generator` as shown above. The round trip is lossless.

```cpp showLineNumbers title="round_trip.cpp"
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/random_generator.hpp>
#include <boost/uuid/string_generator.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <string>
#include <cassert>

int main() {
    boost::uuids::uuid original = boost::uuids::random_generator{}();

    std::string text = boost::uuids::to_string(original);   // serialize
    boost::uuids::uuid restored = boost::uuids::string_generator{}(text);

    assert(original == restored);   // exact round trip
}
```

:::tip Storing UUIDs compactly
The text form is 36 bytes; the binary form is only 16. For databases or wire protocols, store the raw
bytes — iterate `id.begin()`/`id.end()`, or copy `id.data` directly — and reserve the string form for
logs and human-facing output.
:::

## Hashing and use as map keys

`uuid` is fully ordered (`<`, `==`) so it works in `std::map` and `std::set` with no extra effort. For
the hashed containers, Boost provides a `std::hash` specialization via `<boost/uuid/uuid_hash.hpp>`,
so `uuid` drops straight into `std::unordered_map`.

```cpp showLineNumbers title="as_keys.cpp"
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_hash.hpp>      // enables std::hash<boost::uuids::uuid>
#include <boost/uuid/random_generator.hpp>
#include <unordered_map>
#include <map>
#include <string>

int main() {
    boost::uuids::random_generator gen;

    std::unordered_map<boost::uuids::uuid, std::string> sessions; // hashed
    std::map<boost::uuids::uuid, std::string> ordered;            // tree-based

    auto id = gen();
    sessions[id] = "alice";
    ordered[id]  = "alice";
}
```

## Thread-safety

:::warning random_generator is not thread-safe to share
A single `random_generator` wraps mutable PRNG state. Calling `operator()` on the **same** instance
from multiple threads concurrently is a data race. The simple, fast fix is to give each thread its own
generator (for example a `thread_local` instance); do **not** guard one shared generator with a mutex
unless you have measured that contention is acceptable.
:::

```cpp showLineNumbers title="per_thread_gen.cpp"
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/random_generator.hpp>

boost::uuids::uuid new_id() {
    thread_local boost::uuids::random_generator gen; // one per thread, no sharing
    return gen();
}
```

`uuid` values themselves are immutable once created, so passing copies between threads is perfectly
safe — only the *generators* carry mutable state.

## See also

- <Icon icon="lucide:flask-conical" inline /> [Boost.Random](../08-math-and-numerics/boost-random.md) — the random-number engines behind `random_generator`.
- <Icon icon="lucide:database" inline /> [Boost.Serialization](../12-serialization-and-data/boost-serialization.md) — persisting UUIDs alongside other state.
- <Icon icon="lucide:type" inline /> [Boost.LexicalCast](../02-core-utilities/lexical-cast.md) — general text/value conversion.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost overview](../readme.md).
