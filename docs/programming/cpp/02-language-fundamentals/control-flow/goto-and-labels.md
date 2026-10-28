---
id: goto-and-labels
title: goto and Labels
sidebar_label: goto
sidebar_position: 3
tags: [c++, control-flow, goto, labels]
---

# `goto` and Labels

`goto label;` jumps unconditionally to a **label** (a name followed by `:`) elsewhere in the same
function. C code uses it for error cleanup; idiomatic C++ almost never does, because destructors do
that job. This page gives the rules so you can read `goto` in existing code, recognise the one case
where it is still defensible, and know what replaces it.

**Prerequisites:** [Loops](./loops.md), [Conditional Statements](./if-switch.md).

```cpp
    if (!ok) goto cleanup;   // jump forward
    // ...                   // skipped when !ok
cleanup:                     // the label
    release();
```

## The rules

- A label's scope is the **whole function**: you can jump forwards or backwards, but never into
  another function. Label names don't clash with variable names.
- You **cannot jump past a declaration with an initialiser** into the part of the scope where that
  variable is visible. `int x = 5;` is enough to trigger it, as is any variable whose constructor
  would be skipped. Only scalar or trivial types declared *without* an initialiser (`int x;`) may be
  jumped over. The `case` labels of a `switch` follow the same rule.
- A label must label a statement. Before C++23, a label just before a closing `}` needed an empty
  statement (`done: ;`); C++23 allows the label alone.

```cpp
void f(bool b, std::mutex& m) {
    if (b) goto skip;               // error: jump bypasses initialization of 'guard'
    std::lock_guard<std::mutex> guard(m);
skip:
    return;
}
```

The rule exists so that no code can see an object whose constructor never ran.

## What to use instead

| You reached for `goto` to… | Use |
|---|---|
| run cleanup on every exit path | [RAII](../../13-idioms-and-design/01-raii.md): an object whose destructor does the cleanup |
| leave several nested loops | move the loops into a function and `return` |
| retry an operation | a `while` or `do`-`while` loop |
| skip the rest of the work | `continue`, `break`, or an early `return` |

## C-style cleanup and its C++ replacement

In C, each acquired resource gets a label, and failures jump to the label that releases everything
acquired so far, in reverse order:

<Tabs groupId="lang">
  <TabItem value="c" label="C: goto cleanup">

```c
int process(const char* path, size_t n) {
    int rc = -1;
    FILE* f = fopen(path, "r");
    if (!f) goto done;
    char* buf = malloc(n);   // valid C; in C++ the goto above would be ill-formed
    if (!buf) goto close_file;
    /* ... work; on error: goto free_buf ... */
    rc = 0;
free_buf:
    free(buf);
close_file:
    fclose(f);
done:
    return rc;
}
```

  </TabItem>
  <TabItem value="cpp" label="C++: destructors">

```cpp
int process(const std::string& path, std::size_t n) {
    std::ifstream f(path);              // closed by its destructor
    if (!f) return -1;
    std::vector<char> buf(n);           // freed by its destructor
    // ... work; any return or exception cleans up both
    return 0;
}
```

  </TabItem>
</Tabs>

The C version only works if every label stays in the right order as the function changes, and it
cannot handle exceptions. In C++, objects are destroyed automatically on every exit, so the labels
disappear. This is the main reason C++ code has no `goto`.

## The defensible case: leaving nested loops

`break` leaves only the innermost loop. When moving the loops into a function would be awkward, a
forward `goto` out of the nest is clear:

```cpp
for (int i = 0; i < rows; ++i)
    for (int j = 0; j < cols; ++j)
        if (grid[i][j] == target) goto found;
not_found();
return;
found:
report();
```

A separate `find` function returning the position is usually cleaner still.

## Key points

- `goto` jumps within one function only.
- Jumping past an initialised declaration into its scope does not compile.
- RAII replaces C's `goto cleanup`.
- The only common justified use is escaping nested loops, and a function with `return` is usually better.

## Related

- [RAII](../../13-idioms-and-design/01-raii.md) — why C++ doesn't need cleanup labels
- [Loops](./loops.md) — `break` and `continue`
