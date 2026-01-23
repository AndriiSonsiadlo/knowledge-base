---
id: atomics-and-fences
title: Atomics and Memory Fences
sidebar_label: Atomics & Fences
sidebar_position: 2
tags: [cpp, concurrency, atomics, fences, memory-barriers, lock-free]
---

# Atomics and Memory Fences

Atomic operations execute as single, indivisible steps with no interference from other threads. Memory fences (barriers) establish ordering constraints between operations.

:::info Lock-Free Synchronization
**Atomics** = indivisible operations (read/write/modify)  
**Fences** = ordering guarantees for surrounding operations  
Together they enable lock-free programming and fine-grained synchronization
:::

## Atomic Operations

Atomic operations are indivisible - no other thread can observe them half-complete.
```cpp showLineNumbers
#include <atomic>

std::atomic<int> counter{0};

void increment() {
    ++counter;  // Atomic: read-modify-write as one operation
}

void read() {
    int value = counter;  // Atomic read
}
```

### The Non-Atomic Problem
```cpp showLineNumbers
// WITHOUT atomics - DATA RACE!
int counter = 0;

// Thread 1          Thread 2
counter++;           counter++;
// Load: 0           Load: 0
// Add: 1            Add: 1  
// Store: 1          Store: 1
// Result: counter = 1 (should be 2!)
```

Without atomics, the three operations (load, add, store) can interleave, causing lost updates.

## Basic Atomic Operations
```cpp showLineNumbers
#include <atomic>

std::atomic<int> x{0};

// Read
int val = x.load();         // Explicit load
int val2 = x;               // Implicit load

// Write
x.store(42);                // Explicit store
x = 42;                     // Implicit store

// Read-modify-write
int old = x.exchange(10);   // Swap value, return old

// Increment/decrement
x++;                        // Atomic increment
++x;                        // Atomic increment
x--;                        // Atomic decrement
int prev = x.fetch_add(5);  // Add 5, return old value
int prev2 = x.fetch_sub(3); // Subtract 3, return old value
```

## Compare-and-Swap (CAS)

The fundamental operation for lock-free algorithms.
```cpp showLineNumbers
std::atomic<int> value{10};

int expected = 10;
int desired = 20;

// If value==expected, set value=desired; return true
// Otherwise, set expected=value; return false
bool success = value.compare_exchange_strong(expected, desired);

if (success) {
    // value is now 20
} else {
    // value was not 10, expected now contains actual value
}
```

### Strong vs Weak CAS
```cpp showLineNumbers
// Strong: only fails if value != expected
value.compare_exchange_strong(expected, desired);

// Weak: may spuriously fail even if value == expected
// Faster on some architectures
value.compare_exchange_weak(expected, desired);

// Typical usage of weak in loop
while (!value.compare_exchange_weak(expected, desired)) {
    // Retry if spurious failure
}
```

Weak CAS is faster but can fail spuriously. Use in loops where retry is acceptable.

## Lock-Free Stack Example
```cpp showLineNumbers
template<typename T>
class LockFreeStack {
    struct Node {
        T data;
        Node* next;
    };
    
    std::atomic<Node*> head_{nullptr};
    
public:
    void push(T value) {
        Node* newNode = new Node{value, nullptr};
        newNode->next = head_.load();
        
        // Keep trying until successful
        while (!head_.compare_exchange_weak(newNode->next, newNode)) {
            // If head changed, newNode->next updated automatically
        }
    }
    
    bool pop(T& result) {
        Node* oldHead = head_.load();
        
        while (oldHead && 
               !head_.compare_exchange_weak(oldHead, oldHead->next)) {
            // Retry if head changed
        }
        
        if (oldHead) {
            result = oldHead->data;
            delete oldHead;  // ⚠️ Unsafe - ABA problem!
            return true;
        }
        return false;
    }
};
```

## Memory Fences

Fences establish ordering constraints between non-atomic and relaxed atomic operations.

### Without Fences - Problem
```cpp showLineNumbers
std::atomic<bool> ready{false};
int data = 0;

void writer() {
    data = 42;                                      // (1)
    ready.store(true, std::memory_order_relaxed);   // (2)
}

void reader() {
    while (!ready.load(std::memory_order_relaxed)); // (3)
    assert(data == 42);  // ⚠️ NOT GUARANTEED with relaxed!
}
```

With relaxed ordering, there's no guarantee `data = 42` happens before `ready = true`.

### With Fences - Solution
```cpp showLineNumbers
void writer() {
    data = 42;                                      // (1)
    std::atomic_thread_fence(std::memory_order_release);  // Fence!
    ready.store(true, std::memory_order_relaxed);   // (2)
}

void reader() {
    while (!ready.load(std::memory_order_relaxed)); // (3)
    std::atomic_thread_fence(std::memory_order_acquire);  // Fence!
    assert(data == 42);  // ✅ Now guaranteed!
}
```

The release fence ensures all prior writes complete before the store. The acquire fence ensures all subsequent reads see those writes.

## Fence Types
```cpp showLineNumbers
// Acquire fence: prevents later reads/writes from moving before
std::atomic_thread_fence(std::memory_order_acquire);

// Release fence: prevents earlier reads/writes from moving after
std::atomic_thread_fence(std::memory_order_release);

// Full fence: both acquire and release
std::atomic_thread_fence(std::memory_order_acq_rel);

// Sequential consistency fence: strongest ordering
std::atomic_thread_fence(std::memory_order_seq_cst);
```

## Fence Usage Pattern

Protecting multiple variables with relaxed atomics:
```cpp showLineNumbers
std::atomic<bool> ready{false};
int x = 0, y = 0, z = 0;

void producer() {
    x = 1;
    y = 2;
    z = 3;
    std::atomic_thread_fence(std::memory_order_release);
    ready.store(true, std::memory_order_relaxed);
}

void consumer() {
    while (!ready.load(std::memory_order_relaxed));
    std::atomic_thread_fence(std::memory_order_acquire);
    // All writes to x, y, z are visible
    assert(x == 1 && y == 2 && z == 3);
}
```

## Atomic Counter Example
```cpp showLineNumbers
#include <atomic>

class AtomicCounter {
    std::atomic<int> count_{0};
    
public:
    void increment() {
        count_.fetch_add(1, std::memory_order_relaxed);
    }
    
    int get() const {
        return count_.load(std::memory_order_relaxed);
    }
};
```

Relaxed ordering is sufficient for simple counters where exact ordering doesn't matter.

## std::atomic_flag

The only guaranteed lock-free atomic type.
```cpp showLineNumbers
std::atomic_flag flag = ATOMIC_FLAG_INIT;

// Test and set
if (!flag.test_and_set()) {
    // First time, flag is now set
}

// Clear
flag.clear();

// Simple spinlock
class Spinlock {
    std::atomic_flag locked_ = ATOMIC_FLAG_INIT;
    
public:
    void lock() {
        while (locked_.test_and_set(std::memory_order_acquire)) {
            // Spin
        }
    }
    
    void unlock() {
        locked_.clear(std::memory_order_release);
    }
};
```

## Checking Lock-Free Support
```cpp showLineNumbers
std::atomic<int> x;
std::atomic<double> y;
std::atomic<MyLargeStruct> z;

// Check if lock-free at compile-time
static_assert(std::atomic<int>::is_always_lock_free);

// Check at runtime
if (x.is_lock_free()) {
    std::cout << "int atomic is lock-free\n";
}

if (y.is_lock_free()) {
    std::cout << "double atomic is lock-free\n";
}

// Large types might not be lock-free
if (!z.is_lock_free()) {
    std::cout << "MyLargeStruct uses locks\n";
}
```

## Performance Comparison
```cpp showLineNumbers
// Relaxed: fastest, no ordering
counter.fetch_add(1, std::memory_order_relaxed);

// Acquire/Release: medium, synchronization
flag.store(true, std::memory_order_release);

// Sequential: slowest, full ordering
flag.store(true, std::memory_order_seq_cst);  // Default
```

**Typical latency:**
- Relaxed: ~1-2 cycles
- Acquire/Release: ~5-10 cycles
- Sequential consistency: ~10-20 cycles

## Producer-Consumer with Fences
```cpp showLineNumbers
#include <atomic>
#include <vector>

class MessageQueue {
    std::vector<int> buffer_;
    std::atomic<size_t> writePos_{0};
    std::atomic<size_t> readPos_{0};
    
public:
    void push(int value) {
        size_t pos = writePos_.load(std::memory_order_relaxed);
        buffer_[pos] = value;
        
        std::atomic_thread_fence(std::memory_order_release);
        writePos_.store(pos + 1, std::memory_order_relaxed);
    }
    
    bool pop(int& result) {
        size_t pos = readPos_.load(std::memory_order_relaxed);
        if (pos >= writePos_.load(std::memory_order_relaxed)) {
            return false;
        }
        
        std::atomic_thread_fence(std::memory_order_acquire);
        result = buffer_[pos];
        readPos_.store(pos + 1, std::memory_order_relaxed);
        return true;
    }
};
```

## Best Practices

:::success DO
- Use atomics for simple shared counters/flags
- Use relaxed ordering for independent operations
- Check `is_lock_free()` for critical paths
- Profile before optimizing memory orders
- Start with sequential consistency, optimize if needed
  :::

:::danger DON'T
- Use atomics for complex data structures (use mutexes)
- Mix atomic and non-atomic access to same variable
- Assume all atomic operations are lock-free
- Use relaxed ordering without understanding memory model
- Over-optimize memory ordering prematurely
  :::

## Summary

**Atomic operations:**
- Indivisible read/write/modify operations
- No data races, no torn reads/writes
- Support lock-free algorithms
- `load()`, `store()`, `exchange()`, CAS

**Memory fences:**
- Establish ordering between operations
- Release fence: prior writes complete before fence
- Acquire fence: subsequent reads see prior writes
- Allow relaxed atomics with ordering guarantees

**Use cases:**
- **Atomics:** Simple counters, flags, lock-free structures
- **Fences:** Protecting multiple variables with relaxed atomics
- **Sequential consistency:** When in doubt (default, safe)
- **Relaxed:** Independent counters, statistics
