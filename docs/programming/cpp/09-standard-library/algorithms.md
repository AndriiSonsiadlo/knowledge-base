---
id: algorithms
title: STL Algorithms
sidebar_label: Algorithms
sidebar_position: 3
tags: [c++, stl, algorithms, sort, find, transform]
---

# Standard Library Algorithms

STL algorithms are generic functions that work with any container through iterators. They provide tested, optimized implementations of common operations. Never write your own sort or search - use the STL!

:::info Algorithms + Iterators = Generic Code
Algorithms work on ranges defined by iterators. One algorithm works with vector, list, array, or any container providing compatible iterators.
:::

## Non-Modifying Sequence Operations

### std::find - Linear Search

```cpp showLineNumbers 
#include <algorithm>
#include <vector>

std::vector<int> vec = {1, 2, 3, 4, 5};

auto it = std::find(vec.begin(), vec.end(), 3);
if (it != vec.end()) {
    std::cout << "Found at position: " << std::distance(vec.begin(), it);
} else {
    std::cout << "Not found";
}

// find_if with predicate
auto it2 = std::find_if(vec.begin(), vec.end(), [](int x) {
    return x > 3;  // Find first element > 3
});

// find_if_not (first not matching)
auto it3 = std::find_if_not(vec.begin(), vec.end(), [](int x) {
    return x < 3;  // Find first element >= 3
});
```

**Complexity:** O(n)

### std::count - Count Elements

```cpp showLineNumbers 
std::vector<int> vec = {1, 2, 3, 2, 5, 2};

// Count occurrences
int count = std::count(vec.begin(), vec.end(), 2);  // 3

// Count with predicate
int even_count = std::count_if(vec.begin(), vec.end(), [](int x) {
    return x % 2 == 0;  // Count even numbers
});
```

### std::all_of, any_of, none_of

```cpp showLineNumbers 
std::vector<int> vec = {2, 4, 6, 8};

// All satisfy predicate?
bool all_even = std::all_of(vec.begin(), vec.end(), [](int x) {
    return x % 2 == 0;
});  // true

// Any satisfy predicate?
bool any_greater_5 = std::any_of(vec.begin(), vec.end(), [](int x) {
    return x > 5;
});  // true

// None satisfy predicate?
bool none_odd = std::none_of(vec.begin(), vec.end(), [](int x) {
    return x % 2 != 0;
});  // true
```

### std::for_each - Apply Function

```cpp showLineNumbers 
std::vector<int> vec = {1, 2, 3, 4, 5};

// Apply function to each element
std::for_each(vec.begin(), vec.end(), [](int x) {
    std::cout << x << " ";
});

// Modify elements (need reference)
std::for_each(vec.begin(), vec.end(), [](int& x) {
    x *= 2;  // vec becomes {2, 4, 6, 8, 10}
});

// Return function object
auto sum_func = [total = 0](int x) mutable { return total += x; };
auto final_func = std::for_each(vec.begin(), vec.end(), sum_func);
// Can access accumulated value from final_func
```

## Modifying Sequence Operations

### std::copy - Copy Elements

```cpp showLineNumbers 
std::vector<int> src = {1, 2, 3, 4, 5};
std::vector<int> dst(5);

// Copy range
std::copy(src.begin(), src.end(), dst.begin());

// copy_if with predicate
std::vector<int> even;
std::copy_if(src.begin(), src.end(), std::back_inserter(even), [](int x) {
    return x % 2 == 0;
});  // even = {2, 4}

// copy_n - copy n elements
std::vector<int> first_three(3);
std::copy_n(src.begin(), 3, first_three.begin());  // {1, 2, 3}
```

### std::move - Move Elements

```cpp showLineNumbers 
std::vector<std::string> src = {"one", "two", "three"};
std::vector<std::string> dst(3);

// Move elements (src elements left in valid but unspecified state)
std::move(src.begin(), src.end(), dst.begin());
// dst = {"one", "two", "three"}
// src = {?, ?, ?} (moved-from)
```

### std::transform - Apply Function and Store Result

```cpp showLineNumbers 
std::vector<int> vec = {1, 2, 3, 4, 5};
std::vector<int> result(5);

// Unary transform
std::transform(vec.begin(), vec.end(), result.begin(), [](int x) {
    return x * x;  // Square each element
});  // result = {1, 4, 9, 16, 25}

// Binary transform (combine two ranges)
std::vector<int> vec2 = {10, 20, 30, 40, 50};
std::transform(vec.begin(), vec.end(), vec2.begin(), result.begin(),
    [](int a, int b) {
        return a + b;
    });  // result = {11, 22, 33, 44, 55}
```

### std::fill and std::generate

```cpp showLineNumbers 
std::vector<int> vec(10);

// Fill with value
std::fill(vec.begin(), vec.end(), 42);  // All elements = 42

// Fill with generated values
int counter = 0;
std::generate(vec.begin(), vec.end(), [&counter]() {
    return counter++;  // 0, 1, 2, ..., 9
});
```

### std::replace - Replace Elements

```cpp showLineNumbers 
std::vector<int> vec = {1, 2, 3, 2, 5, 2};

// Replace all 2s with 99
std::replace(vec.begin(), vec.end(), 2, 99);
// vec = {1, 99, 3, 99, 5, 99}

// replace_if with predicate
std::replace_if(vec.begin(), vec.end(), [](int x) {
    return x % 2 == 0;  // Replace even numbers
}, 0);
```

### std::remove - Remove Elements

```cpp showLineNumbers 
std::vector<int> vec = {1, 2, 3, 2, 5, 2};

// Remove all 2s (doesn't actually delete!)
auto new_end = std::remove(vec.begin(), vec.end(), 2);
vec.erase(new_end, vec.end());  // Actually delete
// vec = {1, 3, 5}

// Or in one line (C++20)
std::erase(vec, 2);  // Combines remove + erase

// remove_if with predicate
auto new_end2 = std::remove_if(vec.begin(), vec.end(), [](int x) {
    return x % 2 == 0;
});
vec.erase(new_end2, vec.end());
```

**Important:** `remove` doesn't actually delete elements, just moves them to end!

### std::unique - Remove Consecutive Duplicates

```cpp showLineNumbers 
std::vector<int> vec = {1, 1, 2, 2, 2, 3, 3, 1};

// Must be sorted for full deduplication!
std::sort(vec.begin(), vec.end());  // {1, 1, 1, 2, 2, 2, 3, 3}

auto new_end = std::unique(vec.begin(), vec.end());
vec.erase(new_end, vec.end());
// vec = {1, 2, 3}
```

### std::reverse - Reverse Range

```cpp showLineNumbers 
std::vector<int> vec = {1, 2, 3, 4, 5};

std::reverse(vec.begin(), vec.end());
// vec = {5, 4, 3, 2, 1}

// reverse_copy - copy reversed
std::vector<int> reversed(5);
std::reverse_copy(vec.begin(), vec.end(), reversed.begin());
```

### std::rotate - Rotate Elements

```cpp showLineNumbers 
std::vector<int> vec = {1, 2, 3, 4, 5};

// Rotate left (move first element to end)
std::rotate(vec.begin(), vec.begin() + 1, vec.end());
// vec = {2, 3, 4, 5, 1}

// Rotate right (move last to beginning)
std::rotate(vec.rbegin(), vec.rbegin() + 1, vec.rend());
// vec = {1, 2, 3, 4, 5}
```

## Sorting and Related Operations

### std::sort - Sort Range

```cpp showLineNumbers 
std::vector<int> vec = {3, 1, 4, 1, 5, 9, 2, 6};

// Sort ascending
std::sort(vec.begin(), vec.end());
// vec = {1, 1, 2, 3, 4, 5, 6, 9}

// Sort descending
std::sort(vec.begin(), vec.end(), std::greater<int>());

// Custom comparator
std::vector<std::string> words = {"apple", "zoo", "cat", "dog"};
std::sort(words.begin(), words.end(), [](const auto& a, const auto& b) {
    return a.length() < b.length();  // Sort by length
});
```

**Complexity:** O(n log n) average  
**Note:** Not stable (equal elements may be reordered)

### std::stable_sort - Stable Sort

```cpp showLineNumbers 
struct Person {
    std::string name;
    int age;
};

std::vector<Person> people = {
    {"Alice", 30}, {"Bob", 25}, {"Charlie", 30}
};

// Stable sort preserves relative order of equal elements
std::stable_sort(people.begin(), people.end(), [](const auto& a, const auto& b) {
    return a.age < b.age;
});
// Alice and Charlie (both 30) stay in original order
```

### std::partial_sort - Partially Sort

```cpp showLineNumbers 
std::vector<int> vec = {3, 1, 4, 1, 5, 9, 2, 6};

// Sort first 4 elements, rest can be in any order
std::partial_sort(vec.begin(), vec.begin() + 4, vec.end());
// vec = {1, 1, 2, 3, ...(rest unsorted)}
```

**Use case:** Finding top N elements efficiently

### std::nth_element - Find Nth Element

```cpp showLineNumbers 
std::vector<int> vec = {3, 1, 4, 1, 5, 9, 2, 6};

// Partition so vec[4] is in correct sorted position
std::nth_element(vec.begin(), vec.begin() + 4, vec.end());
// Elements before vec[4] are <= vec[4]
// Elements after vec[4] are >= vec[4]
// But not fully sorted

// Use case: Finding median
size_t mid = vec.size() / 2;
std::nth_element(vec.begin(), vec.begin() + mid, vec.end());
int median = vec[mid];
```

**Complexity:** O(n) average - faster than sorting!

## Binary Search (on sorted ranges)

### std::binary_search - Check if Element Exists

```cpp showLineNumbers 
std::vector<int> vec = {1, 2, 3, 4, 5, 6, 7, 8, 9};

bool found = std::binary_search(vec.begin(), vec.end(), 5);  // true
```

**Complexity:** O(log n)  
**Requirement:** Range must be sorted!

### std::lower_bound - First >= Value

```cpp showLineNumbers 
std::vector<int> vec = {1, 2, 4, 4, 4, 6, 7};

auto it = std::lower_bound(vec.begin(), vec.end(), 4);
// Points to first 4
int index = std::distance(vec.begin(), it);  // 2
```

### std::upper_bound - First > Value

```cpp showLineNumbers 
auto it = std::upper_bound(vec.begin(), vec.end(), 4);
// Points to 6 (first element > 4)
```

### std::equal_range - Range of Equal Elements

```cpp showLineNumbers 
auto [lower, upper] = std::equal_range(vec.begin(), vec.end(), 4);
// lower points to first 4
// upper points to 6
// Range [lower, upper) contains all 4s

int count = std::distance(lower, upper);  // 3 (three 4s)
```

## Set Operations (on sorted ranges)

```cpp showLineNumbers 
std::vector<int> v1 = {1, 2, 3, 4, 5};
std::vector<int> v2 = {3, 4, 5, 6, 7};
std::vector<int> result;

// Union (all elements from both)
std::set_union(v1.begin(), v1.end(), v2.begin(), v2.end(),
               std::back_inserter(result));
// result = {1, 2, 3, 4, 5, 6, 7}

// Intersection (common elements)
result.clear();
std::set_intersection(v1.begin(), v1.end(), v2.begin(), v2.end(),
                     std::back_inserter(result));
// result = {3, 4, 5}

// Difference (in v1 but not v2)
result.clear();
std::set_difference(v1.begin(), v1.end(), v2.begin(), v2.end(),
                   std::back_inserter(result));
// result = {1, 2}

// Symmetric difference (in one but not both)
result.clear();
std::set_symmetric_difference(v1.begin(), v1.end(), v2.begin(), v2.end(),
                             std::back_inserter(result));
// result = {1, 2, 6, 7}
```

## Heap Operations

```cpp showLineNumbers 
std::vector<int> vec = {3, 1, 4, 1, 5, 9};

// Make heap (max heap by default)
std::make_heap(vec.begin(), vec.end());
// vec = {9, 5, 4, 1, 1, 3} (heap property satisfied)

// Push to heap
vec.push_back(7);
std::push_heap(vec.begin(), vec.end());

// Pop from heap
std::pop_heap(vec.begin(), vec.end());
vec.pop_back();  // Actually remove

// Sort heap
std::sort_heap(vec.begin(), vec.end());
// vec is now sorted
```

## Min/Max Operations

```cpp showLineNumbers 
std::vector<int> vec = {3, 1, 4, 1, 5, 9, 2, 6};

// Min/max element
auto min_it = std::min_element(vec.begin(), vec.end());
auto max_it = std::max_element(vec.begin(), vec.end());

std::cout << "Min: " << *min_it;  // 1
std::cout << "Max: " << *max_it;  // 9

// Min and max together
auto [min, max] = std::minmax_element(vec.begin(), vec.end());

// Min/max of values
int smaller = std::min(5, 10);
int larger = std::max(5, 10);
auto [a, b] = std::minmax(5, 10);  // {5, 10}
```

## Permutations

```cpp showLineNumbers 
std::vector<int> vec = {1, 2, 3};

// Next permutation
do {
    for (int x : vec) std::cout << x << " ";
    std::cout << "\n";
} while (std::next_permutation(vec.begin(), vec.end()));

// Prints all permutations:
// 1 2 3
// 1 3 2
// 2 1 3
// 2 3 1
// 3 1 2
// 3 2 1

// Previous permutation
std::prev_permutation(vec.begin(), vec.end());
```

## Numeric Algorithms

```cpp showLineNumbers 
#include <numeric>

std::vector<int> vec = {1, 2, 3, 4, 5};

// Sum (accumulate)
int sum = std::accumulate(vec.begin(), vec.end(), 0);  // 15

// Product
int product = std::accumulate(vec.begin(), vec.end(), 1, std::multiplies<>());

// Custom operation
int result = std::accumulate(vec.begin(), vec.end(), 0, [](int acc, int x) {
    return acc + x * x;  // Sum of squares
});  // 55

// Inner product
std::vector<int> vec2 = {1, 2, 3, 4, 5};
int dot = std::inner_product(vec.begin(), vec.end(), vec2.begin(), 0);
// 1*1 + 2*2 + 3*3 + 4*4 + 5*5 = 55

// Partial sum
std::vector<int> partial(5);
std::partial_sum(vec.begin(), vec.end(), partial.begin());
// partial = {1, 3, 6, 10, 15}

// Adjacent difference
std::vector<int> diff(5);
std::adjacent_difference(vec.begin(), vec.end(), diff.begin());
// diff = {1, 1, 1, 1, 1}

// iota - fill with incrementing values
std::vector<int> seq(10);
std::iota(seq.begin(), seq.end(), 0);
// seq = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
```

## C++17 Parallel Algorithms

```cpp showLineNumbers 
#include <execution>

std::vector<int> vec(1000000);

// Sequential
std::sort(vec.begin(), vec.end());

// Parallel
std::sort(std::execution::par, vec.begin(), vec.end());

// Parallel unsequenced (most aggressive)
std::sort(std::execution::par_unseq, vec.begin(), vec.end());

// Works with many algorithms:
std::for_each(std::execution::par, vec.begin(), vec.end(), [](int& x) {
    x *= 2;
});

std::transform(std::execution::par, vec.begin(), vec.end(), vec.begin(), 
    [](int x) { return x * x; });
```

:::success Algorithm Quick Reference

**Finding**: find, find_if, count, count_if  
**Copying**: copy, copy_if, move  
**Transforming**: transform, replace, fill, generate  
**Removing**: remove, remove_if, unique  
**Sorting**: sort, stable_sort, partial_sort, nth_element  
**Searching**: binary_search, lower_bound, upper_bound  
**Set ops**: set_union, set_intersection, set_difference  
**Min/Max**: min_element, max_element  
**Numeric**: accumulate, inner_product, partial_sum  
**Always O(n log n) or better** when sorted  
**Parallel (C++17)** = add execution policy for speedup
:::