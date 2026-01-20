---
id: fences
title: Memory Fences
sidebar_label: Fences
sidebar_position: 3
tags: [cpp, concurrency, fences, memory-barriers, synchronization]
---

# Memory Fences

**Fences** (memory barriers) are synchronization operations that establish ordering constraints between non-atomic and relaxed atomic operations.

## What are Fences?
```cpp
#include <atomic>

// Without fence
std::atomic<bool> ready{false};
int data = 0;

void writer() {
    data = 42;                                      // (1)
    ready.store(true, std::memory_order_relaxed);   // (2)
}

void reader() {
    while (!ready.load(std::memory_order_relaxed)); // (3)
    assert(data == 42);  // NOT GUARANTEED with relaxed!
}
```

### With Fence
```cpp
void writer() {
    data = 42;                                      // (1)
    std::atomic_thread_fence(std::memory_order_release);  // Fence!
    ready.store(true, std::memory_order_relaxed);   // (2)
}

void reader() {
    while (!ready.load(std::memory_order_relaxed)); // (3)
    std::atomic_thread_fence(std::memory_order_acquire);  // Fence!
    assert(data == 42);  // Now guaranteed!
}
```

## Fence Types
```cpp
#include <atomic>

// Acquire fence: prevents later reads/writes from moving before fence
std::atomic_thread_fence(std::memory_order_acquire);

// Release fence: prevents earlier reads/writes from moving after fence
std::atomic_thread_fence(std::memory_order_release);

// Full fence: both acquire and release
std::atomic_thread_fence(std::memory_order_acq_rel);

// Sequential consistency fence: strongest ordering
std::atomic_thread_fence(std::memory_order_seq_cst);
```

## When to Use Fences

### Pattern 1: Protecting Multiple Variables
```cpp
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

### Pattern 2: Relaxed Atomics with Ordering
```cpp
std::atomic<int> a{0}, b{0};

// Thread 1
a.store(1, std::memory_order_relaxed);
std::atomic_thread_fence(std::memory_order_release);
b.store(1, std::memory_order_relaxed);

// Thread 2
while (!b.load(std::memory_order_relaxed));
std::atomic_thread_fence(std::memory_order_acquire);
assert(a.load(std::memory_order_relaxed) == 1);  // Guaranteed
```

## Practical Example
```cpp
#include <atomic>
#include <thread>
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

## Fence vs Atomic Memory Order
```cpp
// Using atomic memory orders
ready.store(true, std::memory_order_release);
while (!ready.load(std::memory_order_acquire));

// Equivalent using fences
std::atomic_thread_fence(std::memory_order_release);
ready.store(true, std::memory_order_relaxed);

while (!ready.load(std::memory_order_relaxed));
std::atomic_thread_fence(std::memory_order_acquire);
```

:::info
Fences allow using **relaxed** atomic operations while still achieving synchronization, potentially improving performance.
:::

## Best Practices

:::success
**DO:**
- Use fences when protecting multiple non-atomic variables
- Use fences with relaxed atomics for fine-tuned performance
- Understand memory model before using fences
  :::

:::danger
**DON'T:**
- Use fences unless necessary (prefer atomic memory orders)
- Use fences without understanding happens-before relationships
- Mix fence-based and order-based synchronization carelessly
  :::

## Related Topics

- **[Atomics](02-atomics.md)** - Atomic operations
- **[C++ Memory Model](01-cpp-memory-model.md)** - Memory ordering
- **[Mutexes](06-mutexes.md)** - Higher-level synchronization