---
id: iterators
title: Iterators
sidebar_label: Iterators
sidebar_position: 2
tags: [c++, stl, iterators, ranges, algorithms]
---

# Iterators

Iterators are the glue between containers and algorithms. They provide a uniform interface for traversing and accessing elements in different container types, enabling generic algorithms.

:::info Iterator Abstraction
Iterators abstract away container details. Algorithms work with any container through iterators, not caring if it's a vector, list, or custom type.
:::

## Iterator Basics

```cpp showLineNumbers 
#include <vector>
#include <iostream>

std::vector<int> vec = {1, 2, 3, 4, 5};

// Get iterators
auto begin = vec.begin();  // Points to first element
auto end = vec.end();      // Points PAST last element

// Dereference to access element
std::cout << *begin;  // 1

// Advance iterator
++begin;
std::cout << *begin;  // 2

// Iterate through container
for (auto it = vec.begin(); it != vec.end(); ++it) {
    std::cout << *it << " ";
}
```

**Key point:** `end()` points *past* the last element, not at it. Never dereference `end()`!

## Iterator Categories

Different iterators support different operations, forming a hierarchy.

### Input Iterator (Read-Once, Forward)

Can read elements, move forward, single-pass.

```cpp showLineNumbers 
#include <iostream>
#include <iterator>

// Input iterator example: istream_iterator
std::istream_iterator<int> input(std::cin);
std::istream_iterator<int> eof;

while (input != eof) {
    int value = *input;  // Read
    ++input;             // Advance
    // Can't go back!
}

// Operations: *, ++, ==, !=
// Single-pass only
```

**Supports:**
- `*it` (read)
- `++it`, `it++` (advance)
- `==`, `!=` (compare)

**Cannot:**
- Write
- Go backward
- Multi-pass (use again after advancing)

### Output Iterator (Write-Once, Forward)

Can write elements, move forward, single-pass.

```cpp showLineNumbers 
#include <iostream>
#include <iterator>
#include <vector>

std::vector<int> vec;

// Output iterator example: back_insert_iterator
auto inserter = std::back_inserter(vec);

*inserter = 1;  // Write
*inserter = 2;  // Write
*inserter = 3;  // Write

// vec now contains {1, 2, 3}

// Operations: *, ++, =
```

**Supports:**
- `*it = value` (write)
- `++it`, `it++` (advance)

**Cannot:**
- Read
- Compare
- Multi-pass

### Forward Iterator (Read/Write, Forward, Multi-Pass)

Can read/write, move forward, multi-pass allowed.

```cpp showLineNumbers 
#include <forward_list>

std::forward_list<int> flist = {1, 2, 3, 4, 5};

auto it1 = flist.begin();
auto it2 = it1;  // Copy

++it1;
// it2 still points to first element (multi-pass)

*it1 = 10;  // Can write
int x = *it2;  // Can read
```

**Supports:**
- All Input operations
- Multi-pass (copy iterator, use both)
- Writing (if not const)

**Cannot:**
- Go backward
- Random access

### Bidirectional Iterator (Forward + Backward)

Can move both directions.

```cpp showLineNumbers 
#include <list>
#include <set>

std::list<int> lst = {1, 2, 3, 4, 5};

auto it = lst.end();
--it;  // Move backward
// Now points to last element

std::cout << *it;  // 5

++it;  // Forward
--it;  // Backward
--it;  // Backward again
std::cout << *it;  // 4

// std::set, std::map also provide bidirectional iterators
```

**Supports:**
- All Forward operations
- `--it`, `it--` (move backward)

**Cannot:**
- Random access (can't jump)

### Random Access Iterator (Full Control)

Can jump to any position instantly.

```cpp showLineNumbers 
#include <vector>
#include <array>

std::vector<int> vec = {1, 2, 3, 4, 5};

auto it = vec.begin();

it += 3;       // Jump forward 3
it -= 1;       // Jump back 1
it = it + 2;   // Arithmetic
it = it - 1;

std::cout << it[2];  // Subscript like array

// Comparison
if (it < vec.end()) {
    // ...
}

// Distance
auto diff = vec.end() - vec.begin();  // Number of elements
```

**Supports:**
- All Bidirectional operations
- `it += n`, `it -= n` (jump)
- `it + n`, `it - n` (arithmetic)
- `it[n]` (subscript)
- `<`, `>`, `<=`, `>=` (comparison)
- `it1 - it2` (distance)

**Containers:** `vector`, `deque`, `array`, C arrays

### Contiguous Iterator (C++17)

Guarantees contiguous memory (vector, array, string).

```cpp showLineNumbers 
std::vector<int> vec = {1, 2, 3, 4, 5};

int* ptr = &*vec.begin();  // Get raw pointer
// Can use pointer arithmetic
ptr[2];  // Same as vec[2]

// Guaranteed: &*(it + n) == (&*it) + n
```

## const_iterator

Prevents modification through the iterator.

```cpp showLineNumbers 
std::vector<int> vec = {1, 2, 3};

// Regular iterator (can modify)
std::vector<int>::iterator it = vec.begin();
*it = 10;  // ✅ OK

// const iterator (can't modify)
std::vector<int>::const_iterator cit = vec.cbegin();
// *cit = 10;  // ❌ Error

// const container gives const_iterator
const std::vector<int> cvec = {1, 2, 3};
auto it2 = cvec.begin();  // const_iterator
```

**Prefer:** Use `cbegin()` and `cend()` when you don't need to modify.

## Reverse Iterators

Iterate backward.

```cpp showLineNumbers 
#include <vector>

std::vector<int> vec = {1, 2, 3, 4, 5};

// Reverse iteration
for (auto it = vec.rbegin(); it != vec.rend(); ++it) {
    std::cout << *it << " ";  // 5 4 3 2 1
}

// Converting between normal and reverse
auto rit = vec.rbegin();
++rit;  // Points to 4
auto it = rit.base();  // Convert to normal iterator
// it points to 5 (one position forward!)
```

**Key:** `rbegin()` points to last element, `rend()` to before first.

## Iterator Operations

```cpp showLineNumbers 
#include <iterator>
#include <vector>

std::vector<int> vec = {1, 2, 3, 4, 5};

// Advance iterator
auto it = vec.begin();
std::advance(it, 3);  // Move 3 positions forward
// Works with any iterator (optimized per category)

// Distance between iterators
auto dist = std::distance(vec.begin(), vec.end());  // 5
// O(1) for random access, O(n) for others

// Next and prev (C++11)
auto it2 = std::next(vec.begin(), 2);  // Iterator at position 2
auto it3 = std::prev(vec.end(), 1);    // Iterator at last element

// These don't modify the original iterator
```

## Insert Iterators

Special output iterators that insert into containers.

```cpp showLineNumbers 
#include <iterator>
#include <vector>

std::vector<int> vec = {1, 2, 3};

// Back inserter (push_back)
auto back_it = std::back_inserter(vec);
*back_it = 4;  // Calls vec.push_back(4)
*back_it = 5;  // vec is now {1, 2, 3, 4, 5}

// Front inserter (push_front) - only for deque, list
std::list<int> lst = {1, 2, 3};
auto front_it = std::front_inserter(lst);
*front_it = 0;  // lst is now {0, 1, 2, 3}

// General inserter
std::vector<int> vec2 = {1, 5};
auto insert_it = std::inserter(vec2, vec2.begin() + 1);
*insert_it = 2;
*insert_it = 3;
*insert_it = 4;  // vec2 is {1, 2, 3, 4, 5}
```

## Stream Iterators

Read from or write to streams.

```cpp showLineNumbers 
#include <iterator>
#include <fstream>
#include <vector>

// Read from file
std::ifstream file("data.txt");
std::istream_iterator<int> file_it(file);
std::istream_iterator<int> eof;

std::vector<int> numbers(file_it, eof);  // Read all numbers

// Write to cout
std::vector<int> vec = {1, 2, 3, 4, 5};
std::ostream_iterator<int> out_it(std::cout, " ");
std::copy(vec.begin(), vec.end(), out_it);  // Prints: 1 2 3 4 5
```

## Iterator Traits

Query properties of iterators at compile-time.

```cpp showLineNumbers 
#include <iterator>
#include <vector>

using VecIter = std::vector<int>::iterator;

// Iterator category
using Category = std::iterator_traits<VecIter>::iterator_category;
// std::random_access_iterator_tag

// Value type
using Value = std::iterator_traits<VecIter>::value_type;
// int

// Difference type
using Diff = std::iterator_traits<VecIter>::difference_type;
// ptrdiff_t

// Pointer and reference types
using Ptr = std::iterator_traits<VecIter>::pointer;  // int*
using Ref = std::iterator_traits<VecIter>::reference;  // int&
```

## Custom Iterators

Create iterators for custom containers.

```cpp showLineNumbers 
class Range {
    int current;
    int end;
    
public:
    class Iterator {
        int value;
    public:
        using iterator_category = std::forward_iterator_tag;
        using value_type = int;
        using difference_type = std::ptrdiff_t;
        using pointer = int*;
        using reference = int&;
        
        Iterator(int v) : value(v) {}
        
        int operator*() const { return value; }
        Iterator& operator++() { ++value; return *this; }
        Iterator operator++(int) { Iterator tmp = *this; ++value; return tmp; }
        bool operator==(const Iterator& other) const { return value == other.value; }
        bool operator!=(const Iterator& other) const { return value != other.value; }
    };
    
    Range(int start, int end) : current(start), end(end) {}
    
    Iterator begin() const { return Iterator(current); }
    Iterator end() const { return Iterator(end); }
};

// Usage
for (int i : Range(0, 10)) {
    std::cout << i << " ";  // 0 1 2 3 4 5 6 7 8 9
}
```

## Iterator Invalidation

Iterators can become invalid after container modifications.

```cpp showLineNumbers 
std::vector<int> vec = {1, 2, 3, 4, 5};

auto it = vec.begin() + 2;  // Points to 3

vec.push_back(6);  // May reallocate
// it might be invalid now! (if reallocation happened)

// Safe approach
size_t index = std::distance(vec.begin(), it);
vec.push_back(6);
it = vec.begin() + index;  // Recalculate iterator

// Different containers, different rules:
// vector: invalidated by insert/erase/push_back (if realloc)
// list: only invalidated iterator at erased element
// set/map: only erased element's iterator invalidated
```

## Range-Based for Loop (Iterator Under the Hood)

```cpp showLineNumbers 
std::vector<int> vec = {1, 2, 3, 4, 5};

// Range-based for
for (int val : vec) {
    std::cout << val;
}

// Equivalent to
for (auto it = vec.begin(); it != vec.end(); ++it) {
    int val = *it;
    std::cout << val;
}

// With modification
for (int& val : vec) {  // Reference to modify
    val *= 2;
}

// const reference (efficient, no copy, no modify)
for (const auto& val : vec) {
    std::cout << val;
}
```

## Iterator Concepts (C++20)

```cpp showLineNumbers 
#include <iterator>

template<std::input_iterator Iter>
void process(Iter begin, Iter end) {
    // Guaranteed input iterator properties
}

template<std::random_access_iterator Iter>
void fast_access(Iter it) {
    it[5];  // Guaranteed to work
}

// Standard iterator concepts:
// std::input_iterator
// std::output_iterator
// std::forward_iterator
// std::bidirectional_iterator
// std::random_access_iterator
// std::contiguous_iterator
```

## Common Pitfalls

```cpp showLineNumbers 
// ❌ Dereferencing end()
auto it = vec.end();
*it;  // Undefined behavior!

// ❌ Incrementing end()
++vec.end();  // Undefined behavior!

// ❌ Using invalidated iterator
vec.push_back(10);
// old_iterator might be invalid

// ❌ Comparing iterators from different containers
vec1.begin() == vec2.begin();  // Undefined behavior!

// ✅ Always check before dereferencing
if (it != vec.end()) {
    *it;  // Safe
}
```

:::success Iterator Essentials

**Categories** = Input, Output, Forward, Bidirectional, Random Access  
**begin/end** = half-open range [begin, end)  
**const_iterator** = prevents modification  
**rbegin/rend** = reverse iteration  
**Invalidation** = modifications can invalidate iterators  
**Insert iterators** = back_inserter, front_inserter, inserter  
**Stream iterators** = istream_iterator, ostream_iterator  
**Range-for** = uses begin()/end() under the hood  
**C++20** = iterator concepts for constraints
:::