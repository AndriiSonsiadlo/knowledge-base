---
id: atomics
title: Atomic Operations
sidebar_label: Atomics
sidebar_position: 2
tags: [cpp, concurrency, atomics, threading, lock-free]
---

# Atomic Operations

**Atomic operations** execute as a single, indivisible step with no possibility of interference from other threads.

## std::atomic
```cpp
#include <atomic>

std::atomic<int> counter{0};

void increment() {
    ++counter;  // Atomic increment
}

void read() {
    int value = counter;  // Atomic read
}
```

### Non-Atomic Problem
```cpp
// WITHOUT atomics - DATA RACE!
int counter = 0;

// Thread 1          Thread 2
counter++;           counter++;
// Load: 0           Load: 0
// Add: 1            Add: 1  
// Store: 1          Store: 1
// Result: counter = 1 (should be 2!)
```

## Basic Operations
```cpp
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
```cpp
#include <atomic>

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

### Weak vs Strong CAS
```cpp
// Strong: only fails if value != expected
value.compare_exchange_strong(expected, desired);

// Weak: may spuriously fail even if value == expected
// Faster on some architectures
value.compare_exchange_weak(expected, desired);

// Typical usage of weak in loop
while (!value.compare_exchange_weak(expected, desired)) {
    // Retry
}
```

## Lock-Free Data Structures

### Lock-Free Stack
```cpp
#include <atomic>

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
        
        while (!head_.compare_exchange_weak(newNode->next, newNode)) {
            // Retry if head changed
        }
    }
    
    bool pop(T& result) {
        Node* oldHead = head_.load();
        
        while (oldHead && !head_.compare_exchange_weak(oldHead, oldHead->next)) {
            // Retry
        }
        
        if (oldHead) {
            result = oldHead->data;
            delete oldHead;
            return true;
        }
        return false;
    }
};
```

### Atomic Counter
```cpp
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

## std::atomic_flag

The only guaranteed lock-free atomic:
```cpp
#include <atomic>

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

## Practical Examples

### Example 1: Shared Counter
```cpp
#include <atomic>
#include <thread>
#include <vector>

std::atomic<int> sharedCounter{0};

void worker() {
    for (int i = 0; i < 1000; ++i) {
        sharedCounter.fetch_add(1, std::memory_order_relaxed);
    }
}

int main() {
    std::vector<std::thread> threads;
    for (int i = 0; i < 10; ++i) {
        threads.emplace_back(worker);
    }
    
    for (auto& t : threads) {
        t.join();
    }
    
    std::cout << sharedCounter << '\n';  // 10000
}
```

### Example 2: Producer-Consumer
```cpp
#include <atomic>
#include <thread>

std::atomic<bool> dataReady{false};
int data = 0;

void producer() {
    data = 42;  // Prepare data
    dataReady.store(true, std::memory_order_release);
}

void consumer() {
    while (!dataReady.load(std::memory_order_acquire)) {
        // Wait
    }
    assert(data == 42);  // Guaranteed
}
```

## Performance Considerations
```cpp
// Relaxed: fastest, no ordering
counter.fetch_add(1, std::memory_order_relaxed);

// Acquire/Release: medium, synchronization
flag.store(true, std::memory_order_release);

// Sequential: slowest, full ordering
flag.store(true, std::memory_order_seq_cst);  // Default
```

## Best Practices

:::success
**DO:**
- Use atomics for simple shared counters
- Use relaxed ordering for independent operations
- Check `is_lock_free()` for performance-critical code
- Prefer high-level primitives (mutex) when possible
  :::

:::danger
**DON'T:**
- Use atomics for complex data structures (use mutexes)
- Assume all atomic operations are lock-free
- Use relaxed ordering without understanding memory model
- Mix atomic and non-atomic access
  :::

## Related Topics

- **[C++ Memory Model](01-cpp-memory-model.md)** - Memory ordering
- **[Fences](03-fences.md)** - Memory barriers
- **[Mutexes](06-mutexes.md)** - Higher-level synchronization