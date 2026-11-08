---
id: algorithms
title: STL Algorithms
sidebar_label: Algorithms
sidebar_position: 3
tags: [c++, stl, algorithms, sort, find, erase-remove, binary-search, numeric, execution-policy]
---

# Standard Library Algorithms

The algorithms in `<algorithm>` and `<numeric>` are function templates that work on a pair of
[iterators](./iterators.md) `[first, last)` and never see the container. The same `std::find`
searches a `vector`, a `list` or an input stream, and each algorithm states the weakest iterator
category it needs and the number of operations it may perform. Using them says what you mean
(`std::count_if`) where a hand-written loop says how, and they are specified to give the best
complexity the category allows. This page covers the classic iterator-pair algorithms. The C++20
`std::ranges::` versions with projections and views are on [Ranges](./ranges.md).

**Prerequisites:** [Iterators](./iterators.md), [Containers](./containers.md),
[lambdas](../07-classes-and-oop/lambdas.md) (for predicates).

## How the algorithms are shaped

- **They never change a container's size.** `std::remove` cannot erase, `std::copy` cannot grow
  its destination. To add elements, write through an inserter (`std::back_inserter`).
- **Naming conventions.** `_if` takes a predicate instead of a value (`find_if`); `_n` takes a
  count (`copy_n`); `_copy` writes the result to a new range instead of in place (`reverse_copy`,
  `remove_copy_if`).
- **Callable arguments** (predicates, comparators, transforms) are copied by value, so pass
  cheap function objects or lambdas, or wrap a stateful one in `std::ref`. Algorithms may copy a
  predicate and call the copies in any order, so it must not depend on its own mutable state, and
  must not modify the elements it examines.
- **Comparators** passed to sorting, searching and set algorithms must be a **strict weak ordering**:
  irreflexive (`comp(a, a)` false), transitive, and with transitive equivalence (incomparability). `<=` is
  not one, and a comparator that violates this is undefined behavior; in practice `std::sort` can read
  out of bounds (observed with libstdc++'s unguarded insertion sort).
- **Output ranges** must have room, and must not overlap the input unless the algorithm says so.

## Searching and counting

| Algorithm | Returns | Complexity |
|---|---|---|
| `find(f, l, v)`, `find_if`, `find_if_not` | iterator to first match, or `l` | at most N applications of `==` or the predicate |
| `count(f, l, v)`, `count_if` | number of matches | exactly N |
| `all_of`, `any_of`, `none_of` | `bool` (stop early) | at most N |
| `adjacent_find` | first position where two neighbours match | at most N-1 |
| `search(f, l, f2, l2)` | first occurrence of a subsequence | at most N x M |
| `equal`, `mismatch` | whole-range comparison / first difference | at most N |
| `min_element`, `max_element`, `minmax_element` | iterator to extreme | N-1 (about 3N/2 for `minmax_element`) |
| `for_each(f, l, fn)` | `fn` (by value, so you can read its final state) | exactly N applications |

`all_of` on an empty range is `true`; `any_of` is `false`. `std::find` on a sorted range is wasted
work: use a [binary search](#binary-search-on-sorted-ranges). Containers with their own `find`
(`set`, `map`, `unordered_*`) have a faster member, so prefer that to `std::find`. `std::search`
may be given a searcher object (`std::boyer_moore_searcher`) *(C++17)*.

## Copying, transforming and filling

```cpp title="transform.cpp" showLineNumbers
#include <algorithm>
#include <iostream>
#include <iterator>
#include <numeric>
#include <vector>

int main() {
    std::vector<int> src(5);
    std::iota(src.begin(), src.end(), 1);                    // 1 2 3 4 5

    std::vector<int> sq;
    std::transform(src.begin(), src.end(), std::back_inserter(sq),
                   [](int x) { return x * x; });              // exactly N applications

    std::vector<int> evens;
    std::copy_if(sq.begin(), sq.end(), std::back_inserter(evens),
                 [](int x) { return x % 2 == 0; });

    for (int x : evens) std::cout << x << ' ';
    std::cout << '\n';
}
```

```text
4 16 
```

Other members of the family: `copy`/`copy_n`/`copy_backward` (use `copy_backward` when the output
overlaps the input from the right), `move` (the algorithm, element-wise move; `<algorithm>`, unrelated
to `std::move` the cast), `fill`/`fill_n`, `generate`/`generate_n`, `replace`/`replace_if`, `swap_ranges`.
`std::transform` has a two-input form `transform(f1, l1, f2, out, binary_op)`. Library implementations commonly lower `std::copy`
to `memmove` for trivially copyable types (not guaranteed).

## Removing, uniquifying and reordering

`std::remove`, `remove_if` and `unique` **do not shrink the container**. They shift the elements
to keep towards the front, preserving their order, and return the new logical end; what lies after
that iterator is valid but unspecified (moved-from) values. You must then call the container's
`erase` to drop the tail. This is the **erase-remove idiom**:

```cpp title="erase-remove.cpp" showLineNumbers
#include <algorithm>
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3, 2, 4, 2, 5};

    // Pre-C++20:
    v.erase(std::remove(v.begin(), v.end(), 2), v.end());

    std::vector<int> w{1, 1, 2, 2, 2, 3, 1};
    w.erase(std::unique(w.begin(), w.end()), w.end());        // removes *consecutive* duplicates

    std::vector<int> x{1, 2, 3, 4, 5, 6};
    std::erase_if(x, [](int n) { return n % 3 == 0; });       // C++20 for all std containers

    for (int n : v) std::cout << n << ' ';
    std::cout << "| ";
    for (int n : w) std::cout << n << ' ';
    std::cout << "| ";
    for (int n : x) std::cout << n << ' ';
    std::cout << '\n';
}
```

```text
1 3 4 5 | 1 2 3 1 | 1 2 4 5 
```

`std::erase(c, value)` and `std::erase_if(c, pred)` *(C++20)* do the whole job as non-member functions.
`erase` exists for the sequence containers (`vector`, `deque`, `list`, `forward_list`) and `basic_string`;
`erase_if` also covers the ordered and unordered associative containers. Neither exists for `std::array`.
For `std::list` the member `list::remove` / `remove_if` is equivalent.
`unique` only removes *adjacent* equal elements, so sort first to deduplicate globally.
Both algorithms are O(N); `std::erase` on a `vector` is therefore O(N) in total, where erasing
elements one at a time in a loop is O(N^2).

Reordering without removal: `reverse`, `rotate` (a left rotation in O(N) that is also the way to
move a block of a range), `shuffle` *(C++11, needs a random engine; `random_shuffle` was removed
in C++17)*, `partition` (elements satisfying the predicate first), `stable_partition`,
`is_partitioned`.

## Sorting and selecting

| Algorithm | Guarantee |
|---|---|
| `sort(f, l)` | O(N log N) comparisons (guaranteed worst case since C++11); **not stable**; needs random access |
| `stable_sort` | O(N log N) comparisons if there is enough extra memory, otherwise O(N log^2 N); equal elements keep their order |
| `partial_sort(f, mid, l)` | sorts the smallest `mid - f` elements into front, about N log M comparisons |
| `nth_element(f, nth, l)` | O(N) on average; afterwards `*nth` is what a full sort would put there, with no larger element before and no smaller after |
| `is_sorted`, `is_sorted_until` | at most N-1 comparisons |

`std::list` has no random access, so use the member `list::sort` (stable, O(N log N), relinks nodes).
Sorting with a comparator:

```cpp title="sort.cpp" showLineNumbers
#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

struct Person { std::string name; int age; };

int main() {
    std::vector<Person> p{{"Ann", 30}, {"Bob", 25}, {"Cy", 30}, {"Di", 25}};

    // By age; ties keep their original order only because the sort is stable
    std::stable_sort(p.begin(), p.end(),
                     [](const Person& a, const Person& b) { return a.age < b.age; });

    for (const auto& x : p) std::cout << x.name << ' ';
    std::cout << '\n';
}
```

```text
Bob Di Ann Cy 
```

Never write `a.age <= b.age` as the comparator: it breaks the strict weak ordering and makes the
behavior undefined, and it can crash `std::sort` on equal elements. To sort by several fields,
compare with `std::tie(a.x, a.y) < std::tie(b.x, b.y)` or use `<=>` *(C++20)*.

## Binary search on sorted ranges

These require the range to be **partitioned** with respect to the value (in practice: sorted by the
same comparator). They do O(log N) comparisons; with a non-random-access iterator the comparisons
stay logarithmic but the iterator steps are O(N), so for `set` and `map` use the container's member
functions.

| Function | Returns |
|---|---|
| `lower_bound(f, l, v)` | first element **not less than** `v` |
| `upper_bound(f, l, v)` | first element **greater than** `v` |
| `equal_range(f, l, v)` | `[lower_bound, upper_bound)` as a pair |
| `binary_search(f, l, v)` | `bool` only: is there an equivalent element |

```cpp title="bound.cpp" showLineNumbers
#include <algorithm>
#include <iostream>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 4, 4, 4, 7, 9};

    auto lo = std::lower_bound(v.begin(), v.end(), 4);
    auto hi = std::upper_bound(v.begin(), v.end(), 4);
    std::cout << (lo - v.begin()) << ' ' << (hi - v.begin()) << '\n';   // [2, 5)

    v.insert(std::lower_bound(v.begin(), v.end(), 5), 5);               // sorted insert
    std::cout << std::binary_search(v.begin(), v.end(), 7) << ' ' << v[5] << '\n';
}
```

```text
2 5
1 5
```

## Set operations and merging

On **sorted** ranges: `merge`, `inplace_merge`, `includes`, `set_union`, `set_intersection`,
`set_difference`, `set_symmetric_difference`. Each writes the result in sorted order to an output
iterator. `merge` does at most N1 + N2 - 1 comparisons, and the other set operations at most
2 x (N1 + N2) - 1 (`inplace_merge` uses extra memory when available, else N log N). They treat equal elements as multisets: if a value appears 3 times in
one input and 2 in the other, `set_intersection` outputs 2.

## Heaps

A **binary heap** laid out in a random-access range gives you the largest element at the front
(`std::less` ordering) at the cost of O(log N) per insertion or removal. It is what
`std::priority_queue` wraps. The primitives: `make_heap` (O(N)), `push_heap` (call after
`push_back`; O(log N)), `pop_heap` (moves the max to the back; call `pop_back` after; O(log N)),
`sort_heap` (O(N log N)), `is_heap`. Use the adapter unless you need to access the underlying array.

## Min, max and clamp

`std::min`/`std::max` of two values or an `initializer_list`, `std::minmax`, `std::clamp(v, lo, hi)`
*(C++17; undefined behavior if `hi < lo`)*. Both of the two-argument forms return a **reference**:
`const auto& m = std::max(a, 3);` dangles when one argument is a temporary that dies at the end of
the full expression.

## Permutations

`next_permutation(f, l)` rearranges into the next lexicographic order and returns `false` (and
resets to sorted order) after the last; start from a sorted range to enumerate all N! arrangements.
`prev_permutation`, `is_permutation` (quadratic without help), and `rotate` complete the family.

## Numeric algorithms (`<numeric>`)

| Algorithm | Computes | Note |
|---|---|---|
| `accumulate(f, l, init, op = +)` | left fold | result type is the type of `init` |
| `reduce(f, l, init, op = +)` *(C++17)* | fold in **unspecified order** | `op` must be associative and commutative; can be parallel |
| `transform_reduce` *(C++17)* | map then reduce (inner product) | |
| `inner_product`, `partial_sum`, `adjacent_difference` | classic sequential forms | |
| `inclusive_scan`, `exclusive_scan` *(C++17)* | prefix sums, parallelizable | |
| `iota(f, l, start)` | start, start+1, ... | |
| `gcd`, `lcm` *(C++17)*, `midpoint`, `lerp` *(C++20)* | scalar helpers | |

The classic accumulate trap: the accumulator takes the type of `init`.

```cpp title="accumulate.cpp" showLineNumbers
#include <iostream>
#include <numeric>
#include <vector>

int main() {
    std::vector<double> v{0.5, 0.5, 0.5};
    std::cout << std::accumulate(v.begin(), v.end(), 0) << '\n';     // int accumulator: 0
    std::cout << std::accumulate(v.begin(), v.end(), 0.0) << '\n';   // double: 1.5
}
```

```text
0
1.5
```

With `int` init, each partial sum is converted back to `int`, truncating 0.5 to 0 on each step.
`reduce` with floating-point values can give a slightly different result than `accumulate`,
because floating-point addition is not associative and the order is unspecified.

## Execution policies *(C++17)*

Most algorithms have an overload taking a policy as first argument, from `<execution>`:
`std::execution::seq`, `par`, `par_unseq` (and `unseq` *(C++20)*). Using `par` permits the
implementation to run the callback on several threads; `par_unseq` additionally allows
vectorization.

```cpp
#include <algorithm>
#include <execution>
std::sort(std::execution::par, v.begin(), v.end());   // fragment: v is a large std::vector<int>
```

The rules that matter: your callbacks must not cause data races, and with `par_unseq` they must
not take locks or otherwise block. Exceptions thrown from a callback call `std::terminate`, and
iterators must be at least forward. The standard only *permits* parallel execution:
whether you get a speedup depends on the library (libstdc++ needs Intel TBB installed and `-ltbb`
to run in parallel; MSVC has its own backend) and on the amount of work per element. Measure.

## Related

- [Ranges](./ranges.md): `std::ranges::sort(v)`, projections, and lazy views over the same algorithms
- [Iterators](./iterators.md): the categories each algorithm requires
- [Containers](./containers.md): member `sort`/`remove`/`find` that beat the generic ones, and `erase_if`
- [Lambdas](../07-classes-and-oop/lambdas.md): the usual predicate and comparator
- [Data races](../11-concurrency-and-memory-model/03-data-races.md): what parallel policies require of your callbacks

## References

- [Algorithms library, cppreference](https://en.cppreference.com/w/cpp/algorithm)
- [Numeric library, cppreference](https://en.cppreference.com/w/cpp/numeric)
- ISO C++ [algorithms], [numerics]
