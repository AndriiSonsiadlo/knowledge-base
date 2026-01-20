---
id: containers
title: STL Containers
sidebar_label: Containers
sidebar_position: 1
tags: [c++, stl, containers, vector, map, set, data-structures]
---

# Standard Library Containers

Containers store collections of objects. The STL provides optimized, well-tested containers for different access patterns and performance needs. Choose the right container for your use case.

:::info Container Categories
**Sequence**: ordered by insertion (vector, deque, list)  
**Associative**: sorted by key (set, map)  
**Unordered**: hash-based (unordered_set, unordered_map)  
**Adapters**: interfaces built on other containers (stack, queue, priority_queue)
:::

## std::vector - Dynamic Array

The most commonly used container. Contiguous memory, fast random access, efficient end insertion.

```cpp showLineNumbers 
#include <vector>

std::vector<int> vec;         // Empty vector
std::vector<int> vec2(10);    // 10 elements (value-initialized to 0)
std::vector<int> vec3(10, 42); // 10 elements, all 42
std::vector<int> vec4{1, 2, 3}; // Initializer list

// Adding elements
vec.push_back(10);      // Add to end O(1) amortized
vec.emplace_back(20);   // Construct in-place
vec.insert(vec.begin(), 5);  // Insert at beginning O(n)

// Accessing
int x = vec[0];         // No bounds check
int y = vec.at(1);      // Bounds checked (throws)
int& first = vec.front();
int& last = vec.back();

// Size and capacity
vec.size();             // Number of elements
vec.capacity();         // Allocated space
vec.empty();            // Is empty?
vec.reserve(100);       // Pre-allocate space
vec.shrink_to_fit();    // Reduce capacity to size

// Removing
vec.pop_back();         // Remove last O(1)
vec.erase(vec.begin()); // Remove first O(n)
vec.clear();            // Remove all

// Iteration
for (int val : vec) {
    std::cout << val << " ";
}
```

**When to use:**
- Default choice for sequences
- Need random access
- Mostly add/remove at end
- Memory efficiency important

**Performance:**
- Random access: O(1)
- End insertion: O(1) amortized
- Middle insertion: O(n)
- Search: O(n) unsorted, O(log n) if sorted

## std::array - Fixed-Size Array

Stack-allocated, fixed-size array wrapper with STL interface.

```cpp showLineNumbers 
#include <array>

std::array<int, 5> arr = {1, 2, 3, 4, 5};

arr[0] = 10;
arr.at(1) = 20;  // Bounds checked
arr.fill(0);     // Fill all with value

// Size is compile-time constant
constexpr size_t size = arr.size();  // 5

// No dynamic allocation
// Stack allocated, no overhead
```

**When to use:**
- Size known at compile-time
- Need stack allocation
- Want STL algorithms with C arrays
- Performance critical (no heap allocation)

## std::deque - Double-Ended Queue

Fast insertion/removal at both ends. Not contiguous.

```cpp showLineNumbers 
#include <deque>

std::deque<int> deq;

// Fast operations at both ends
deq.push_front(10);   // O(1)
deq.push_back(20);    // O(1)
deq.pop_front();      // O(1)
deq.pop_back();       // O(1)

// Random access still O(1) (but slower than vector)
int x = deq[0];
```

**When to use:**
- Need fast insertion at both ends
- Don't need contiguous memory
- Random access still needed

**Performance:**
- Front/back insertion: O(1)
- Random access: O(1) but slower than vector
- Middle insertion: O(n)

## std::list - Doubly Linked List

Efficient insertion/removal anywhere, but no random access.

```cpp showLineNumbers 
#include <list>

std::list<int> lst = {1, 2, 3, 4, 5};

// Fast insertion anywhere (if you have iterator)
auto it = lst.begin();
++it;
lst.insert(it, 10);  // O(1) at iterator position

// Splice - move elements from another list
std::list<int> other = {6, 7, 8};
lst.splice(lst.end(), other);  // Constant time!

// Remove elements
lst.remove(3);       // Remove all 3's
lst.remove_if([](int x) { return x % 2 == 0; });  // Remove even

// Unique - remove consecutive duplicates
lst.sort();
lst.unique();
```

**When to use:**
- Frequent insertion/removal in middle
- Don't need random access
- Splice operations
- Iterator stability (iterators not invalidated)

**Performance:**
- Insertion/removal at position: O(1)
- Access element: O(n)
- Higher memory overhead (2 pointers per element)

## std::forward_list - Singly Linked List

Like list but single links. More memory efficient.

```cpp showLineNumbers 
#include <forward_list>

std::forward_list<int> fwd = {1, 2, 3};

fwd.push_front(0);   // Only push_front (no push_back)
fwd.insert_after(fwd.begin(), 5);

// Can't go backward
// No size() method (would be O(n))
```

**When to use:**
- Need linked list but memory constrained
- Only forward iteration needed
- Rarely used in practice

## std::set - Ordered Set (Red-Black Tree)

Sorted unique elements, typically implemented as red-black tree.

```cpp showLineNumbers 
#include <set>

std::set<int> s = {3, 1, 4, 1, 5};  // Duplicates ignored
// s contains: {1, 3, 4, 5} (sorted!)

// Insertion
s.insert(2);          // O(log n)
s.emplace(6);         // Construct in-place

// Search
bool found = s.count(3);  // Returns 0 or 1
auto it = s.find(4);      // Returns iterator or end()
if (it != s.end()) {
    std::cout << "Found: " << *it;
}

// Removal
s.erase(3);           // Remove by value
s.erase(s.begin());   // Remove by iterator

// Range operations
auto lower = s.lower_bound(3);  // First >= 3
auto upper = s.upper_bound(3);  // First > 3

// Always sorted
for (int val : s) {
    std::cout << val << " ";  // Prints in order
}
```

**When to use:**
- Need sorted unique elements
- Frequent search operations
- Need range queries

**Performance:**
- Search: O(log n)
- Insert: O(log n)
- Remove: O(log n)
- Iteration: sorted order

## std::multiset - Ordered Multiset

Like set but allows duplicates.

```cpp showLineNumbers 
#include <set>

std::multiset<int> ms = {1, 2, 2, 3, 3, 3};

// All 2's and 3's are stored
ms.count(3);  // Returns 3

// Equal range - all elements with value
auto range = ms.equal_range(3);
for (auto it = range.first; it != range.second; ++it) {
    std::cout << *it;  // Prints all 3's
}
```

## std::map - Ordered Key-Value Pairs

Associates keys with values, sorted by key.

```cpp showLineNumbers 
#include <map>

std::map<std::string, int> ages;

// Insertion
ages["Alice"] = 30;           // Insert or update
ages.insert({"Bob", 25});     // Insert pair
ages.emplace("Charlie", 35);  // Construct in-place

// Access
int age = ages["Alice"];      // Creates entry if not exists!
int age2 = ages.at("Bob");    // Throws if not exists

// Check existence
if (ages.count("David")) {    // Returns 0 or 1
    std::cout << "Found";
}

auto it = ages.find("Alice");
if (it != ages.end()) {
    std::cout << it->first << ": " << it->second;
}

// Iteration (sorted by key)
for (const auto& [name, age] : ages) {  // C++17 structured bindings
    std::cout << name << " is " << age << "\n";
}

// Remove
ages.erase("Alice");
```

**When to use:**
- Need key-value mapping
- Keys should be sorted
- Frequent lookups by key

**Performance:**
- Lookup: O(log n)
- Insert: O(log n)
- Delete: O(log n)

## std::multimap - Multiple Values Per Key

```cpp showLineNumbers 
#include <map>

std::multimap<std::string, int> scores;

scores.insert({"Alice", 90});
scores.insert({"Alice", 85});  // Multiple values for Alice

// Get all values for key
auto range = scores.equal_range("Alice");
for (auto it = range.first; it != range.second; ++it) {
    std::cout << it->second << " ";  // 85 90
}
```

## std::unordered_set - Hash Set

Unordered unique elements using hash table.

```cpp showLineNumbers 
#include <unordered_set>

std::unordered_set<int> us = {3, 1, 4, 1, 5};

// Fast lookup
us.insert(2);         // Average O(1)
bool found = us.count(3);  // Average O(1)

// Not sorted!
for (int val : us) {
    // Order is unspecified
}

// Custom hash for user types
struct Point {
    int x, y;
    bool operator==(const Point& other) const {
        return x == other.x && y == other.y;
    }
};

struct PointHash {
    size_t operator()(const Point& p) const {
        return std::hash<int>()(p.x) ^ (std::hash<int>()( p.y) << 1);
    }
};

std::unordered_set<Point, PointHash> points;
```

**When to use:**
- Need fast lookup
- Don't need sorted order
- Have good hash function

**Performance:**
- Lookup: O(1) average, O(n) worst
- Insert: O(1) average
- More memory than set

## std::unordered_map - Hash Map

Fast key-value lookup using hash table.

```cpp showLineNumbers 
#include <unordered_map>

std::unordered_map<std::string, int> counts;

// Fast operations
counts["word"]++;         // O(1) average
counts.emplace("key", 42);

// Iteration order unspecified
for (const auto& [key, value] : counts) {
    std::cout << key << ": " << value << "\n";
}

// Bucket information (advanced)
counts.bucket_count();    // Number of buckets
counts.load_factor();     // Elements per bucket
counts.rehash(100);       // Set minimum bucket count
```

**When to use:**
- Need fastest lookup
- Don't care about order
- Default choice for key-value if order not needed

## std::stack - LIFO Adapter

Stack interface built on top of another container (default: deque).

```cpp showLineNumbers 
#include <stack>

std::stack<int> stk;

stk.push(1);
stk.push(2);
stk.push(3);

stk.top();    // 3 (peek)
stk.pop();    // Remove top
stk.size();   // 2
stk.empty();  // false

// Underlying container
std::stack<int, std::vector<int>> vecStack;  // Use vector
```

**Use for:** LIFO operations, recursion emulation, DFS

## std::queue - FIFO Adapter

Queue interface built on deque.

```cpp showLineNumbers 
#include <queue>

std::queue<int> q;

q.push(1);
q.push(2);
q.push(3);

q.front();    // 1
q.back();     // 3
q.pop();      // Remove front
```

**Use for:** FIFO operations, BFS, task queues

## std::priority_queue - Heap

Max-heap by default.

```cpp showLineNumbers 
#include <queue>

std::priority_queue<int> pq;

pq.push(3);
pq.push(1);
pq.push(4);

pq.top();     // 4 (largest)
pq.pop();     // Remove largest

// Min-heap
std::priority_queue<int, std::vector<int>, std::greater<int>> minHeap;
minHeap.push(3);
minHeap.push(1);
minHeap.top();  // 1 (smallest)

// Custom comparator
auto cmp = [](int a, int b) { return a > b; };
std::priority_queue<int, std::vector<int>, decltype(cmp)> customPQ(cmp);
```

**Use for:** Priority-based processing, Dijkstra's algorithm, scheduling

## Container Selection Guide

```cpp showLineNumbers 
// Need random access? → vector or array
// Add/remove at ends? → deque
// Add/remove anywhere? → list
// Unique sorted elements? → set
// Key-value sorted? → map
// Fast lookup, any order? → unordered_set/map
// Duplicates allowed? → multiset/multimap
// LIFO? → stack
// FIFO? → queue
// Priority-based? → priority_queue
```

## Common Operations Across Containers

```cpp showLineNumbers 
// All containers support
c.size();
c.empty();
c.clear();

// Most support
c.begin(), c.end();  // Iterators
c.insert(value);
c.erase(iterator);

// Sequence containers
c.push_back(value);
c.pop_back();
c.front(), c.back();

// Associative containers
c.find(key);
c.count(key);
```

:::success Container Quick Reference

**vector** = dynamic array, default choice  
**array** = fixed size, stack allocated  
**deque** = fast both ends  
**list** = linked, fast insert/remove anywhere  
**set** = sorted unique, O(log n) operations  
**map** = sorted key-value, O(log n) operations  
**unordered_set/map** = hash-based, O(1) average  
**stack/queue** = adapters for specific patterns  
**priority_queue** = heap for priority operations
:::