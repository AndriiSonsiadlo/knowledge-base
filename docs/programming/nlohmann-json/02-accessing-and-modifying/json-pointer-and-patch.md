---
id: json-pointer-and-patch
title: JSON Pointer and JSON Patch
sidebar_label: Pointer and patch
sidebar_position: 4
tags: [c++, nlohmann-json, json-pointer, json-patch, rfc]
---

# JSON Pointer and JSON Patch

RFC 6901 (JSON Pointer) and RFC 6902 (JSON Patch) give you standardized addressing and diffing for
JSON documents, so path-based access and structural diffs don't have to be hand-written traversal
code.

## JSON Pointer (RFC 6901)

A JSON Pointer is a `/`-separated path into a document — `/a/b/0` means "key `a`, then key `b`,
then index `0`":

```json
{
  "a": {
    "b": [10, 20, 30]
  }
}
```

```cpp
json::json_pointer ptr("/a/b/0");
int v = doc.at(ptr).get<int>();          // 10, using at() with a pointer

int v2 = doc["/a/b/0"_json_pointer];      // same thing, via the literal
```

Two characters need escaping inside a pointer segment because they're part of the pointer syntax
itself: `~` is written `~0` and `/` is written `~1` — so a key literally named `"a/b"` is addressed
as `/a~1b`.

## flatten() and unflatten()

`flatten()` turns any nested document into a single flat object whose keys are JSON Pointers and
whose values are the corresponding leaf values; `unflatten()` reverses it:

```json showLineNumbers
// before flatten()
{ "a": { "b": [10, 20] } }

// after flatten()
{ "/a/b/0": 10, "/a/b/1": 20 }
```

This round-trips exactly: `doc.flatten().unflatten() == doc`.

## JSON Patch (RFC 6902)

A JSON Patch is a JSON array of operations describing edits to apply to a document. The six
operations are `add`, `remove`, `replace`, `move`, `copy`, and `test`:

```json showLineNumbers title="patch.json"
[
  { "op": "replace", "path": "/a/b/0", "value": 99 },
  { "op": "add", "path": "/a/c", "value": "new" },
  { "op": "remove", "path": "/a/b/1" }
]
```

```cpp
json patch = json::parse(patch_text);
json patched = doc.patch(patch);   // doc itself is unchanged; patched is the result
```

## diff()

`json::diff(source, target)` produces a JSON Patch that turns `source` into `target`:

```cpp
json patch = json::diff(old_doc, new_doc);
json result = old_doc.patch(patch);   // result == new_doc
```

:::note[diff output is minimal, not semantic]
`diff()` produces a syntactically minimal patch by comparing document structure, not a
*semantically* minimal one. Moving an array element from index 0 to index 2, for example, generally
comes out as a sequence of `replace` operations on the affected indices rather than a single `move`
— the algorithm doesn't attempt to recognize that the values were merely reordered. Don't rely on
`diff()` output to convey developer intent, only to reproduce the resulting document.
:::

## Failure modes

- `doc.at(bad_pointer)` throws `out_of_range` when the path doesn't resolve to an existing element.
- Constructing a `json_pointer` from a malformed string (missing leading `/`, invalid escape) throws
  `parse_error`.
- A `test` operation in a patch whose `value` doesn't match the document at that path throws
  `other_error` when the patch is applied, aborting the whole `patch()` call.

## See also

- <Icon icon="lucide:git-merge" inline /> [Merging and comparison](./merging-and-comparison.md) — `update()` and `merge_patch()`, the other ways to combine two documents.
- <Icon icon="lucide:pointer" inline /> [Element access](./element-access.md) — direct key/index access as an alternative to pointers.
- <Icon icon="lucide:alert-triangle" inline /> [Error handling and exceptions](../04-advanced-features/error-handling-and-exceptions.md) — the exceptions this page's failure modes throw.
- <Icon icon="lucide:book-open" inline /> [nlohmann/json overview](../readme.md) — the full section map.
