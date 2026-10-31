---
id: loops
title: Loops (for, while, do-while)
sidebar_label: Loops
sidebar_position: 2
tags: [c++, control-flow, loops, iteration]
---

# Loops (`for`, `while`, `do-while`)

A loop repeats a statement while a condition holds. C++ has four forms. Any of them can express any
loop, so the choice is about **intent**: pick the one that tells the reader what kind of repetition
this is, whether a count, a condition, "at least once", or "each element".

**Prerequisites:** [Expressions and Statements](../expressions-and-statements.md),
[Conditional Statements](./if-switch.md).

## The four forms

```cpp
for (int i = 0; i < n; ++i) { /* ... */ }      // counted: init; condition; step
while (cond) { /* ... */ }                     // zero or more times: test before each pass
do { /* ... */ } while (cond);                 // one or more times: test after each pass
for (const auto& x : container) { /* ... */ }  // range-based (C++11): each element
```

| Form | Condition tested | Use when |
|---|---|---|
| `for` | before each pass | an index or counter is part of the logic |
| `while` | before each pass | you repeat until something happens (input ends, queue empties) |
| `do`-`while` | after each pass | the body must run at least once (prompt, then validate) |
| range-`for` | (iterator compare) | you need each element and not its position |

## How a `for` loop runs

The three parts of the `for` header run at different times. Tracing `for (int i = 0; i < 3; ++i)`
with a body that prints `i`:

<Walkthrough title="for (int i = 0; i < 3; ++i) std::cout << i;" caption="init once; then condition → body → step, until the condition is false." accent="blue">
  <Step title="Init, once">

`int i = 0` runs exactly once. `i` exists only inside the loop. State: <StepChange>`i == 0`</StepChange>

  </Step>
  <Step title="Condition, body, step">

`0 < 3` is true, so the body prints `0`. Then the step `++i` runs: <StepChange>`i == 1`</StepChange>

  </Step>
  <Step title="Repeat">

`1 < 3`: print `1`, `i` becomes 2. `2 < 3`: print `2`, `i` becomes <StepChange>`3`</StepChange>.

  </Step>
  <Step title="Condition false: exit">

`3 < 3` is false. The body and step do not run; the loop ends and `i` goes out of scope.
Output: `012`. The body ran 3 times; the condition was tested 4 times.

  </Step>
</Walkthrough>

Any part of the header may be empty; `for (;;)` loops forever (until `break` or `return`). A
`while (cond) body` is the same as `for (; cond;) body`.

## Range-based `for`

When you need only the elements, the range form removes the index, the bounds and the off-by-one
errors that come with them. It works on arrays, standard containers, and anything with
`begin()`/`end()`.

```cpp
for (const auto& item : items) total += item.price;   // read without copying
for (auto& item : items)       item.price *= 2;        // modify in place
for (const auto& [key, value] : table) use(key, value); // map entries via structured bindings (C++17)
```

The loop variable's type decides what happens to each element:

| Loop variable | Effect |
|---|---|
| `const auto&` | reads each element without copying: the default choice |
| `auto&` | modifies the elements in the container |
| `auto` | copies each element: fine for `int`, wasteful for strings or large objects |

*(C++20)* adds an init-statement: `for (auto v = load(); const auto& x : v)`.

## `break` and `continue`

```cpp
for (const auto& job : jobs) {
    if (job.cancelled) continue;   // skip the rest of this pass, go to the next
    if (job.fatal)     break;      // leave the loop entirely
    run(job);
}
```

Both affect only the **innermost** loop (and `break` also leaves a `switch`). To leave several nested
loops at once, move them into a function and `return`; see [`goto`](./goto-and-labels.md) for the
alternative.

## Pitfalls

**Erasing while iterating.** `v.erase(it)` invalidates `it`, so `++it` afterwards is undefined:

```cpp
for (auto it = v.begin(); it != v.end(); ++it)
    if (is_bad(*it)) v.erase(it);              // bug: it is invalid after erase

std::erase_if(v, is_bad);                       // (C++20) correct
v.erase(std::remove_if(v.begin(), v.end(), is_bad), v.end());   // before C++20
```

A range-`for` uses iterators internally, so adding or removing elements inside one is the same bug.
Rules per container: [Iterators](../../09-standard-library/iterators.md).

**Counting down with an unsigned index.** `for (std::size_t i = n - 1; i >= 0; --i)` never ends:
an unsigned value is always `>= 0`, and `0 - 1` wraps to the largest value. Test before decrementing:

```cpp
for (std::size_t i = n; i-- > 0; ) use(v[i]);   // visits n-1 down to 0
```

**Comparing signed and unsigned.** `for (int i = 0; i < v.size(); ++i)` mixes `int` with
`std::size_t`; `-Wall -Wextra` warns (`-Wsign-compare`). Use `std::size_t`, or a range-`for`.

**A semicolon after the header.** `while (x > 0);` has an empty body and loops forever if `x > 0`.

## Algorithms instead of loops

Many loops are a standard algorithm written out by hand. Naming the algorithm states the intent:

```cpp
auto evens = std::ranges::count_if(v, is_even);   // instead of a counting loop (C++20)
std::ranges::sort(v);
```

See [Algorithms](../../09-standard-library/algorithms.md) and [Ranges](../../09-standard-library/ranges.md).

## Key points

- `for` for counts, `while` for conditions, `do`-`while` for at least once, range-`for` for elements.
- A `for` header runs init once, then condition → body → step until the condition fails.
- Default the range-`for` variable to `const auto&`; `auto&` to modify.
- `break`/`continue` act on the innermost loop only.
- Never change a container's size while iterating it; use `std::erase_if`.

## Related

- [Conditional Statements](./if-switch.md)
- [goto and Labels](./goto-and-labels.md) — leaving nested loops
- [Iterators](../../09-standard-library/iterators.md) — what range-`for` uses underneath
