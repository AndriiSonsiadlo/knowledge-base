---
id: stack-vs-heap
title: Stack vs Heap Memory
sidebar_label: Stack vs Heap
sidebar_position: 3
tags: [c++, stack, heap, memory, performance]
---

# Stack vs Heap Memory

Stack and heap are the two primary memory regions for storing variables. Understanding their differences is crucial for performance and memory management.

:::info Key Difference
**Stack**: Fast, automatic, limited size  
**Heap**: Flexible, manual, large size
:::

## Stack Memory

### Characteristics

```cpp
void function() {
    int x = 42;           // Stack allocation
    char buffer[1024];    // Stack array
    Widget w;             // Stack object
}  // All destroyed automatically
```

**Properties**:
- **Speed**: Extremely fast (~1 ns)
- **Size**: Limited (1-8 MB typical)
- **Lifetime**: Scope-based (automatic)
- **Management**: Automatic (RAII)
- **Allocation**: Pointer bump (O(1))
- **Deallocation**: Pointer bump (O(1))
- **Fragmentation**: None
- **Thread-safety**: Each thread has own stack

### How Stack Works

```
High Address
│
├─────────────┐
│   x = 42    │ ← Stack pointer (SP)
├─────────────┤
│  buffer[0]  │
│  buffer[1]  │
│     ...     │
│ buffer[1023]│
├─────────────┤
│   Widget w  │
├─────────────┤
│   (free)    │
│             │
Low Address

// Function returns: SP moves up, deallocating all
```

**Stack overflow**: Exceeding stack size causes crash:

```cpp
void recursive() {
    int large[100000];  // Each call allocates 400KB
    recursive();        // ❌ Stack overflow after ~10 calls
}
```

---

## Heap Memory

### Characteristics

```cpp
void function() {
    int* ptr = new int(42);        // Heap allocation
    char* buffer = new char[1024]; // Heap array
    Widget* w = new Widget();      // Heap object
    
    delete ptr;
    delete[] buffer;
    delete w;  // Manual cleanup required
}
```

**Properties**:
- **Speed**: Slower (~50-100 ns)
- **Size**: Large (GBs available)
- **Lifetime**: Explicit (new/delete)
- **Management**: Manual
- **Allocation**: Complex (O(1) to O(log n))
- **Deallocation**: Complex
- **Fragmentation**: Possible
- **Thread-safety**: Requires synchronization

### How Heap Works

```
Memory allocator maintains free lists:

Free blocks:
[16 bytes] → [32 bytes] → [1024 bytes] → ...

Allocation:
- Find suitable block (best-fit, first-fit, etc.)
- Split if too large
- Return pointer

Deallocation:
- Mark block as free
- Coalesce with neighbors
```

**Fragmentation**:

```cpp
char* a = new char[100];  // [100]
char* b = new char[100];  // [100][100]
delete a;                 // [free][100]
char* c = new char[150];  // ❌ Can't fit! Fragmented

// Heap: [free:100][used:100][free:elsewhere:150]
```

---

## Comparison

| Aspect | Stack | Heap |
|--------|-------|------|
| **Speed** | Very fast | Slower |
| **Size** | Limited (~1-8 MB) | Large (~GBs) |
| **Lifetime** | Automatic | Manual |
| **Allocation** | O(1), trivial | O(1) to O(log n) |
| **Deallocation** | O(1), automatic | Manual, can leak |
| **Fragmentation** | None | Possible |
| **Cache locality** | Excellent | Variable |
| **Thread-safe** | Per-thread | Requires sync |

---

## When to Use Each

### Use Stack When

```cpp
// Small objects
int x = 42;
std::array<int, 100> arr;

// Scope-limited lifetime
{
    Widget w;
}  // Destroyed automatically

// Hot path performance
void fast_function() {
    int temp[16];  // Stack is faster
    process(temp);
}
```

### Use Heap When

```cpp
// Large objects
int* huge = new int[1000000];  // 4 MB, too big for stack

// Runtime-determined size
int* arr = new int[user_input];

// Lifetime beyond scope
Widget* create() {
    return new Widget();  // Outlives function
}

// Polymorphism
Base* ptr = new Derived();  // Dynamic type
```

---

## Performance Impact

```cpp
// Stack allocation benchmark
void stack_test() {
    for (int i = 0; i < 1000000; ++i) {
        int arr[10];  // ~1 ns per allocation
    }
}

// Heap allocation benchmark
void heap_test() {
    for (int i = 0; i < 1000000; ++i) {
        int* arr = new int[10];  // ~50-100 ns per allocation
        delete[] arr;
    }
}

// Stack is 50-100x faster!
```

---

## Stack Overflow

```cpp
// ❌ Stack overflow causes
void recursive_bomb() {
    recursive_bomb();  // Infinite recursion
}

void large_locals() {
    int huge[1000000];  // 4 MB, exceeds stack
}

void deep_nesting() {
    int a[10000];
    another_function();  // Each call adds to stack
}
```

**Detection**:
```bash
# Increase stack size (temporary fix)
ulimit -s unlimited  # Linux

# Compile with stack checking
g++ -fstack-protector-all program.cpp
```

---

## Memory Leaks (Heap Problem)

```cpp
// ❌ Leak
void leak() {
    int* ptr = new int(42);
    // Never deleted!
}

// ✅ RAII solution
void no_leak() {
    std::unique_ptr<int> ptr = std::make_unique<int>(42);
    // Automatically deleted
}

// ✅ Smart pointer for dynamic arrays
void array_safe() {
    std::vector<int> vec(1000);  // Manages heap internally
    // Automatic cleanup
}
```

---

## Practical Examples

### Example 1: Factory Function

```cpp
// ❌ Cannot return stack object
Widget create() {
    Widget w;
    return w;  // ⚠️ Copy/move, but OK with RVO
}

// ✅ Return by value (RVO)
Widget create() {
    return Widget();  // No copy with optimization
}

// ✅ Return heap object (manual management)
Widget* create() {
    return new Widget();  // Caller owns
}

// ✅ Return smart pointer (automatic management)
std::unique_ptr<Widget> create() {
    return std::make_unique<Widget>();  // Best!
}
```

### Example 2: Large Data

```cpp
// ❌ Stack overflow
void process_data() {
    double matrix[10000][10000];  // 800 MB!
    // ❌ Stack overflow
}

// ✅ Heap allocation
void process_data() {
    std::vector<std::vector<double>> matrix(10000, 
        std::vector<double>(10000));  // Heap
}
```

### Example 3: Variable Size

```cpp
// ❌ Can't do variable-length arrays on stack (non-standard)
void process(int n) {
    int arr[n];  // ❌ VLA (not standard C++)
}

// ✅ Heap via vector
void process(int n) {
    std::vector<int> arr(n);  // ✅ Standard, heap
}
```

---

## Cache Performance

```cpp
// Stack (good cache locality)
void stack_access() {
    int arr[1000];
    for (int i = 0; i < 1000; ++i) {
        arr[i] = i;  // Sequential, cache-friendly
    }
}

// Heap (potential cache misses)
void heap_access() {
    int* arr = new int[1000];
    for (int i = 0; i < 1000; ++i) {
        arr[i] = i;  // May miss cache if fragmented
    }
    delete[] arr;
}

// Stack is typically 2-10x faster due to cache
```

---

## Best Practices

:::success DO
- Default to stack allocation
- Use stack for small, scope-limited objects
- Use `std::vector`, `std::string` for dynamic sizes
- Use smart pointers for heap objects
- Profile before optimizing
  :::

:::danger DON'T
- Put large arrays on stack
- Forget to delete heap allocations
- Use `new`/`delete` when stack works
- Assume heap is always bad (sometimes necessary)
  :::

---

## Summary

**Stack**:
- Fast, automatic, limited
- Default choice for local variables
- Excellent cache locality
- No memory leaks possible

**Heap**:
- Flexible, manual, large
- Use for: large objects, dynamic sizes, shared ownership
- Requires explicit management
- Slower, but necessary for many cases

**Decision guide**:
```cpp
// Stack (default)
int x = 42;
Widget w;
std::array<int, 100> arr;

// Heap (when needed)
std::vector<int> dynamic_arr;           // Dynamic size
std::unique_ptr<Widget> ptr;            // Shared beyond scope
std::shared_ptr<Resource> shared;       // Multiple owners
```

**Golden rule**: Use stack unless you have a specific reason for heap. When using heap, prefer smart pointers over raw `new`/`delete`.