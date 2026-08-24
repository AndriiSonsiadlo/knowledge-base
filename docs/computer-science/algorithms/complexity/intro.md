---
id: complexity-intro
title: Complexity & Analysis — Overview
sidebar_label: Overview
sidebar_position: 0
tags: [computer-science, algorithms, complexity, big-o]
---

# Complexity & Analysis — Overview


Measuring an algorithm by timing it tells you about your laptop, your compiler, your input, and the
background processes competing with you. **Complexity analysis** asks a different question — how does
the work grow as the input grows? — and answers it in a way that survives all four.

That is the whole trade. You give up knowing whether something takes 3 ms or 30 ms, and in exchange
you learn whether doubling the input doubles the time or quadruples it. For deciding between two
approaches before writing either, the second answer is far more useful.

## In This Section

- **[Big-O Notation](./big-o-notation.md)** — what the notation actually asserts, why constants and
  lower-order terms disappear, and how Big-O relates to Ω and Θ.
- **[Common Complexities](./common-complexities.md)** — the handful of growth rates you will
  actually meet, what problem shapes produce each, plus amortized and space complexity.

## Why It Matters

<Figure src="/img/cs/algorithms/complexity-growth-rates.png"
        alt="Eight growth curves on shared axes — 1, log₂n, √n, n, n log₂n, n², 2ⁿ and n! — where the last three climb almost vertically within the first ten inputs while the first three stay nearly flat across all one hundred"
        caption="All eight on the same axes, for n up to 100. n², 2ⁿ and n! have already left the chart before n = 10; log₂ n has not reached 7 by n = 100. No amount of micro-optimisation moves a program between these curves."
        source="Wikimedia Commons" href="https://commons.wikimedia.org/wiki/File:Comparison_computational_complexity.svg"
        license="CC BY-SA 4.0" />

A concrete version of that picture — operations performed, at one billion operations per second:

| n | O(log n) | O(n) | O(n log n) | O(n²) | O(2ⁿ) |
|---|---|---|---|---|---|
| 10 | 3 | 10 | 33 | 100 | 1,024 |
| 1,000 | 10 | 1,000 | ~10,000 | 1,000,000 | *heat death* |
| 1,000,000 | 20 | 1,000,000 | ~20,000,000 | 10¹² (~17 min) | — |
| 1,000,000,000 | 30 | 10⁹ (~1 s) | ~3×10¹⁰ (~30 s) | 10¹⁸ (~32 years) | — |

The lesson is not that O(n²) is forbidden — for n = 100 it is entirely fine and often the simplest
correct code. The lesson is that the input size decides, and that the decision changes character
somewhere around n = 10,000.

## Related Pages

- [Sorting Algorithms](../sorting/intro.md) — the classic worked example of an O(n²) versus O(n log n) choice.
- [Data Structures](../data-structures/intro.md) — every structure is a set of complexity trade-offs made concrete.
