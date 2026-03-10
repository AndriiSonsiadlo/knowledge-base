---
id: goto-and-labels
title: goto and Labels
sidebar_label: goto
sidebar_position: 3
tags: [c++, control-flow, goto, labels]
---

# `goto` and Labels

`goto` jumps unconditionally to a **label** in the same function. It exists, it is occasionally the
clearest tool, and in idiomatic C++ it is almost always the wrong one. This page explains the rules
so you recognise the rare legitimate use — and the modern constructs that replace the rest.

```cpp showLineNumbers
    if (!ok) goto cleanup;     // jump forward to the label
    // ...
cleanup:                       // a label: an identifier followed by ':'
    release();
```

## Why it is discouraged

Unrestricted jumps produce "spaghetti" control flow that is hard to read, hard to verify, and hard
for the optimiser to reason about. C++ already provides structured replacements for every common use:

| You reached for `goto` to… | Use instead |
|----------------------------|-------------|
| break out of nested loops  | extract the nest into a function and `return` |
| run cleanup on every exit path | [RAII](../../13-idioms-and-design/01-raii.md) — destructors free resources automatically |
| retry a block              | a `while`/`do-while` loop |
| jump over remaining work   | `continue`, `break`, early `return` |

## The C-style cleanup pattern (and its C++ replacement)

In C, `goto cleanup` is the standard way to free resources acquired so far. In C++ this is exactly
what RAII removes — the destructor runs no matter how the scope exits, including on exceptions.

```cpp showLineNumbers
// C-style: manual, error-prone, must keep labels in sync with acquisitions
FILE* f = fopen(p, "r");
if (!f) goto done;
buf = malloc(n);
if (!buf) goto close_file;
// ... work ...
close_file: fclose(f);
done:       free(buf);

// C++: no goto, no leaks, exception-safe
std::ifstream f(p);                 // closed by destructor
std::vector<char> buf(n);           // freed by destructor
// ... work ...  every exit path cleans up automatically
```

See [RAII](../../13-idioms-and-design/01-raii.md) — this is the single biggest reason day-to-day C++
has no `goto`.

## Hard rules

:::danger You cannot jump over an initialization
A `goto` that enters the scope of a variable with a non-trivial initializer is **ill-formed** — the
compiler rejects it. This protects you from using an object that was never constructed.

```cpp
goto skip;          // error: jumps into scope of 'guard'
std::lock_guard guard(m);
skip:;
```
:::

Other limits: `goto` cannot cross function boundaries (it is local to one function), and labels
share a single per-function namespace.

## A defensible use

The one case that still comes up: breaking out of a **deeply nested loop** when refactoring into a
function is genuinely awkward. Even here, a flag or extracted function is usually cleaner.

```cpp showLineNumbers
for (int i = 0; i < n; ++i)
    for (int j = 0; j < m; ++j)
        if (grid[i][j] == target) goto found;   // forward jump out of both loops
found:
    // ...
```

## Summary

- `goto` jumps to a label within the same function; it cannot leave the function.
- Prefer structured flow: `return` from an extracted function, loops for retry, RAII for cleanup.
- Jumping *into* the scope of a non-trivially-initialized variable is a compile error.
- The only semi-legitimate use is escaping deeply nested loops — and even that has cleaner alternatives.

## Related

- [RAII](../../13-idioms-and-design/01-raii.md) — replaces goto-based cleanup
- [Loops](./loops.md) · [Conditional Statements](./if-switch.md)
