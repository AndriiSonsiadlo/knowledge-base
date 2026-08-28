---
id: two-pointers-and-sliding-window
title: Two Pointers & Sliding Window
sidebar_label: Two Pointers & Sliding Window
sidebar_position: 1
tags: [computer-science, algorithms, patterns, two-pointers, sliding-window]
---

# Two Pointers & Sliding Window


Both patterns replace a nested loop with a single pass by maintaining two indices that only ever move
forward. The result is $O(n)$ where brute force is $O(n^2)$, and the saving comes from **not re-examining**
what earlier positions already ruled out.

They are the same idea applied to two different structures: two pointers exploits an **ordering**,
sliding window exploits **contiguity**.

## Core Concepts

| | Two pointers | Sliding window |
|---|---|---|
| Pointers | Usually from both ends, converging | Both from the left, `right` leads |
| Requires | Sorted data, or a monotonic property | Contiguous subarray or substring |
| Maintains | A candidate pair | A window and some summary of it |
| Answers | "Find a pair/triple with…" | "Longest/shortest/best contiguous run with…" |

## Mechanism

### Two pointers on sorted data

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def pair_with_sum(a, target):
    """a is sorted. Find indices of two values summing to target."""
    lo, hi = 0, len(a) - 1
    while lo < hi:
        s = a[lo] + a[hi]
        if s == target:
            return lo, hi
        if s < target:
            lo += 1          # need more: the smallest value cannot be part of any answer
        else:
            hi -= 1          # need less: the largest value cannot be either
    return None
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// a is sorted. Find indices of two values summing to target.
std::optional<std::pair<int, int>> pair_with_sum(const std::vector<int>& a, int target) {
    int lo = 0, hi = static_cast<int>(a.size()) - 1;
    while (lo < hi) {
        int s = a[lo] + a[hi];
        if (s == target) return std::pair{lo, hi};
        if (s < target) ++lo;    // need more: the smallest value cannot be part of any answer
        else            --hi;    // need less: the largest value cannot be either
    }
    return std::nullopt;
}
```

</TabItem>
</Tabs>

The correctness argument is what makes this work, and it is worth stating: when `s < target`, `a[lo]`
paired with the *largest* remaining value is already too small, so it cannot pair with anything
smaller either — discarding it loses no solution. Each step eliminates one element permanently, so
the loop runs at most n times.

Without sorting, that argument collapses and you need a [hash table](../data-structures/hash-tables.md)
instead.

### Sliding window

The window `[left, right)` expands to include new elements and contracts when it violates a
constraint. Because both pointers only advance, the total work is $O(n)$ even though the code contains
nested loops:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def longest_unique_substring(s):
    seen = {}                       # character -> most recent index
    left = best = 0
    for right, ch in enumerate(s):
        if ch in seen and seen[ch] >= left:
            left = seen[ch] + 1     # contract past the previous occurrence
        seen[ch] = right
        best = max(best, right - left + 1)
    return best

def min_window_with_sum(a, target):
    """Shortest contiguous run of positive numbers summing to >= target."""
    left = total = 0
    best = float("inf")
    for right, x in enumerate(a):
        total += x
        while total >= target:      # contract while the constraint still holds
            best = min(best, right - left + 1)
            total -= a[left]
            left += 1
    return best if best < float("inf") else 0
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int longest_unique_substring(std::string_view s) {
    std::unordered_map<char, int> seen;         // character -> most recent index
    int left = 0, best = 0;
    for (int right = 0; right < static_cast<int>(s.size()); ++right) {
        auto it = seen.find(s[right]);
        if (it != seen.end() && it->second >= left)
            left = it->second + 1;              // contract past the previous occurrence
        seen[s[right]] = right;
        best = std::max(best, right - left + 1);
    }
    return best;
}

// Shortest contiguous run of positive numbers summing to >= target.
int min_window_with_sum(const std::vector<int>& a, int target) {
    int left = 0, total = 0;
    int best = std::numeric_limits<int>::max();
    for (int right = 0; right < static_cast<int>(a.size()); ++right) {
        total += a[right];
        while (total >= target) {               // contract while the constraint still holds
            best = std::min(best, right - left + 1);
            total -= a[left];
            ++left;
        }
    }
    return best == std::numeric_limits<int>::max() ? 0 : best;
}
```

</TabItem>
</Tabs>

:::info[The inner `while` does not make this quadratic]
`left` never decreases and never exceeds n, so across the entire outer loop the inner loop executes
at most n times in total. The complexity is $O(n)$, not $O(n^2)$ — an **amortized** argument of the same
shape as the one for [dynamic arrays](../data-structures/arrays.md).
:::

### Fast and slow pointers

A third variant, where one pointer moves faster than the other. On a
[linked list](../data-structures/linked-lists.md) this finds the middle or detects a cycle in one
pass and $O(1)$ space; on an array it removes elements in place:

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def remove_duplicates(a):
    """a is sorted. Compact unique values into the front; return the new length."""
    write = 0
    for read in range(len(a)):
        if read == 0 or a[read] != a[read - 1]:
            a[write] = a[read]
            write += 1
    return write
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// a is sorted. Compact unique values into the front; return the new length.
std::size_t remove_duplicates(std::vector<int>& a) {
    std::size_t write = 0;
    for (std::size_t read = 0; read < a.size(); ++read)
        if (read == 0 || a[read] != a[read - 1])
            a[write++] = a[read];
    return write;     // the standard library spells this std::unique(a.begin(), a.end())
}
```

</TabItem>
</Tabs>

## Practical Usage

| Problem | Pattern |
|---|---|
| Two/three values summing to a target (sorted) | Two pointers converging |
| Container with most water, trapping rain water | Two pointers converging |
| Longest substring without repeating characters | Sliding window, variable size |
| Maximum sum of any k consecutive elements | Sliding window, fixed size |
| Smallest subarray with sum ≥ target | Sliding window, variable size |
| Merging two sorted sequences | Two pointers advancing together |
| Removing or partitioning in place | Fast/slow (read/write) pointers |
| Palindrome check | Two pointers converging |
| Cycle detection in a linked list | Fast/slow (Floyd's) |

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# Fixed-size window: compute the first sum, then roll it forward
def max_sum_of_k(a, k):
    total = sum(a[:k])
    best = total
    for i in range(k, len(a)):
        total += a[i] - a[i - k]     # add the entrant, drop the leaver — O(1) per step
        best = max(best, total)
    return best
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
// Fixed-size window: compute the first sum, then roll it forward
int max_sum_of_k(const std::vector<int>& a, int k) {
    int total = std::accumulate(a.begin(), a.begin() + k, 0);
    int best = total;
    for (std::size_t i = k; i < a.size(); ++i) {
        total += a[i] - a[i - k];    // add the entrant, drop the leaver — O(1) per step
        best = std::max(best, total);
    }
    return best;
}
```

</TabItem>
</Tabs>

## Edge Cases & Pitfalls

- **Two pointers on unsorted data is simply wrong.** The elimination argument depends on the
  ordering. Either sort first — $O(n \log n)$, which may still be worth it — or use a hash table.
- **Sorting destroys original indices.** If the answer must be reported as positions in the input,
  sort `(value, index)` pairs.
- **`while left < right` vs `<=`** decides whether an element can pair with itself. Choose
  deliberately.
- **A window over values that can be negative breaks the monotonic contraction.** `min_window_with_sum`
  above requires non-negative numbers; with negatives, growing the window can *decrease* the sum, and
  you need prefix sums plus a hash table instead.
- **Off-by-one in window length.** With an inclusive `right`, the size is `right - left + 1`; with a
  half-open window it is `right - left`. Pick one convention per function.

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms* — the merge step of [mergesort](../sorting/mergesort.md) (§2.3) is the canonical two-pointer procedure.
- Floyd's cycle-detection algorithm — described under [linked lists](../data-structures/linked-lists.md), the classic fast/slow application.

### Books & Videos

- Bentley, J., *Programming Pearls*, Ch. 8 — the maximum-subarray problem, developed from $O(n^3)$ down to $O(n)$ through exactly this kind of reasoning.

## Related Pages

- [Linked Lists](../data-structures/linked-lists.md) — where fast/slow pointers are indispensable.
- [Binary Search](../searching/binary-search.md) — another way of discarding half the candidates each step.
- [Hash Tables](../data-structures/hash-tables.md) — the fallback when the data is not sorted.
