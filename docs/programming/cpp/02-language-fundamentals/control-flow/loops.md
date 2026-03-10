---
id: loops
title: Loops (for, while, do-while)
sidebar_label: Loops
sidebar_position: 2
tags: [c++, control-flow, loops, iteration]
---

# Loops (`for`, `while`, `do-while`)

Four looping forms cover every case. The decision is rarely about capability — they are mostly
interchangeable — and mostly about **intent**: pick the form that makes the loop's contract obvious
to the reader.

## The four forms

```cpp showLineNumbers
for (int i = 0; i < n; ++i) { ... }      // known/counted iteration; i scoped to the loop
while (cond) { ... }                     // zero-or-more: test BEFORE each pass
do { ... } while (cond);                 // one-or-more: test AFTER each pass
for (const auto& x : container) { ... }  // range-based: "for each element"
```

| Form         | Test timing | Reach for it when…                          |
|--------------|-------------|---------------------------------------------|
| `for`        | before      | the index/count is part of the logic        |
| `while`      | before      | iterations depend on a condition, not a count |
| `do-while`   | after       | the body must run at least once (menus, retry) |
| range-`for`  | before      | you just need each element, not the index   |

## Prefer range-based `for`

When you only need the elements, the range form removes the index, the bounds, and a whole class of
off-by-one and iterator-invalidation bugs.

```cpp showLineNumbers
for (const auto& item : items) total += item.price;   // read-only: const ref, no copy
for (auto& item : items)       item.price *= 1.1;      // mutate in place: non-const ref
for (auto [key, val] : table)  use(key, val);          // structured bindings over a map (C++17)
```

:::tip Choosing the loop variable
- `const auto&` — read elements without copying (the default).
- `auto&` — modify elements in place.
- `auto` (by value) — only when you genuinely want a copy to mutate locally.

Plain `auto` over a container of heavy objects silently copies every element.
:::

## `break`, `continue`, and exit conditions

```cpp showLineNumbers
for (auto& job : queue) {
    if (job.cancelled) continue;   // skip to the next iteration
    if (job.fatal)     break;      // leave the loop entirely
    process(job);
}
```

`break`/`continue` affect only the **innermost** loop. To exit nested loops, prefer extracting the
nest into a function and `return`-ing, rather than reaching for [`goto`](./goto-and-labels.md).

## Common pitfalls

:::warning Iterator/index invalidation
Modifying a container *while* looping over it can invalidate the iterator or index you are using.

```cpp
for (auto it = v.begin(); it != v.end(); ++it)
    if (pred(*it)) v.erase(it);     // BUG: erase invalidates it

v.erase(std::remove_if(v.begin(), v.end(), pred), v.end());   // erase–remove idiom: correct
```
:::

:::warning Unsigned counters and reverse loops
`for (size_t i = n - 1; i >= 0; --i)` never terminates — an unsigned value is always `>= 0`, so it
wraps around instead of going negative. Loop with a signed index, or use iterators / `i-- ` tricks.
:::

## Beyond hand-written loops

Many loops are really an algorithm in disguise. Expressing the intent is clearer and harder to get
wrong than re-deriving the mechanics:

```cpp showLineNumbers
auto n = std::count_if(v.begin(), v.end(), is_even);   // vs a manual counting loop
std::ranges::sort(v);                                  // vs a hand-rolled sort (C++20)
```

See [Algorithms](../../09-standard-library/algorithms.md) and [Ranges](../../09-standard-library/ranges.md).

## Summary

- Match the form to intent: `for` for counts, `while`/`do-while` for conditions, range-`for` for elements.
- Default the range loop variable to `const auto&`; use `auto&` to mutate.
- `break`/`continue` touch only the innermost loop.
- Don't mutate a container's size while iterating it — use the erase–remove idiom.
- Reverse loops with unsigned counters underflow forever; use a signed index.
- If a loop is "count / find / transform / sort", an algorithm says it better.

## Related

- [Conditional Statements (if, switch)](./if-switch.md)
- [goto and Labels](./goto-and-labels.md)
- [Algorithms](../../09-standard-library/algorithms.md) · [Iterators](../../09-standard-library/iterators.md)
