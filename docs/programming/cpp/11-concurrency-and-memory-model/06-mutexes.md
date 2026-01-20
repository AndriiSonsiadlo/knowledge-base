---
id: mutexes
title: Mutexes and Locks
sidebar_label: Mutexes
sidebar_position: 6
tags: [cpp, concurrency, mutexes, locks, synchronization]
---

# Mutexes and Locks

A **mutex** (mutual exclusion) is a synchronization primitive that protects shared data by allowing only one thread to access it at a time.

## std::mutex
```cpp
#include <mutex>
#include <thread>

std::mutex mtx;
int counter = 0;

void increment() {
    mtx.lock();
    ++counter;
    mtx.unlock();
}
```

:::warning
Manual `lock()`/`unlock()` is error-prone. Always use RAII lock guards!
:::

## Lock Guards (RAII)

### std::lock_guard
```cpp
#include <mutex>

std::mutex mtx;
int counter = 0;

void increment() {
    std::lock_guard<std::mutex> lock(mtx);
    ++counter;
    // Automatically unlocks when lock goes out of scope
}
```

### std::unique_lock

More flexible than `lock_guard`:
```cpp
#include <mutex>

std::mutex mtx;

void flexibleLocking() {
    std::unique_lock<std::mutex> lock(mtx);
    
    // Can unlock early
    lock.unlock();
    doNonCriticalWork();
    
    // Can relock
    lock.lock();
    accessSharedData();
    
    // Can transfer ownership
    std::unique_lock<std::mutex> lock2 = std::move(lock);
}
```

### std::scoped_lock (C++17)

Lock multiple mutexes without deadlock:
```cpp
#include <mutex>

std::mutex mtx1, mtx2;

void transfer() {
    std::scoped_lock lock(mtx1, mtx2);  // Locks both atomically
    // Transfer data between resources
}  // Both unlocked automatically
```

## Mutex Types

### std::mutex

Basic mutual exclusion:
```cpp
std::mutex mtx;

void critical_section() {
    std::lock_guard<std::mutex> lock(mtx);
    // Protected code
}
```

### std::recursive_mutex

Allows same thread to lock multiple times:
```cpp
#include <mutex>

std::recursive_mutex rmtx;

void f() {
    std::lock_guard<std::recursive_mutex> lock(rmtx);
    // ...
}

void g() {
    std::lock_guard<std::recursive_mutex> lock(rmtx);
    f();  // OK: same thread can lock again
}
```

### std::timed_mutex

Supports timeout on lock attempts:
```cpp
#include <mutex>
#include <chrono>

std::timed_mutex tmtx;

void tryLockWithTimeout() {
    if (tmtx.try_lock_for(std::chrono::milliseconds(100))) {
        // Got lock within 100ms
        doWork();
        tmtx.unlock();
    } else {
        // Timeout
        handleTimeout();
    }
}
```

### std::shared_mutex (C++17)

Reader-writer lock:
```cpp
#include <shared_mutex>

std::shared_mutex smtx;
int data = 0;

void reader() {
    std::shared_lock lock(smtx);  // Multiple readers
    int value = data;
}

void writer() {
    std::unique_lock lock(smtx);  // Exclusive writer
    data = 42;
}
```

## Deadlock Prevention

### Problem: Deadlock
```cpp
// DEADLOCK!
std::mutex mtx1, mtx2;

void thread1() {
    std::lock_guard<std::mutex> lock1(mtx1);
    std::lock_guard<std::mutex> lock2(mtx2);  // Waits for mtx2
}

void thread2() {
    std::lock_guard<std::mutex> lock2(mtx2);
    std::lock_guard<std::mutex> lock1(mtx1);  // Waits for mtx1
}
// Both threads wait forever!
```

### Solution 1: Lock Order
```cpp
void thread1() {
    std::lock_guard<std::mutex> lock1(mtx1);  // Always lock mtx1 first
    std::lock_guard<std::mutex> lock2(mtx2);
}

void thread2() {
    std::lock_guard<std::mutex> lock1(mtx1);  // Same order
    std::lock_guard<std::mutex> lock2(mtx2);
}
```

### Solution 2: std::lock (Atomic)
```cpp
void thread1() {
    std::unique_lock<std::mutex> lock1(mtx1, std::defer_lock);
    std::unique_lock<std::mutex> lock2(mtx2, std::defer_lock);
    
    std::lock(lock1, lock2);  // Locks both atomically, no deadlock
    // Work with both locked
}
```

### Solution 3: std::scoped_lock (C++17)
```cpp
void thread1() {
    std::scoped_lock lock(mtx1, mtx2);  // Deadlock-free
    // Work with both locked
}
```

## try_lock

Non-blocking lock attempt:
```cpp
#include <mutex>

std::mutex mtx;

void tryLockExample() {
    if (mtx.try_lock()) {
        // Got the lock
        doWork();
        mtx.unlock();
    } else {
        // Lock not available, do something else
        doAlternativeWork();
    }
}
```

## Practical Examples

### Example 1: Thread-Safe Counter
```cpp
#include <mutex>

class Counter {
    mutable std::mutex mutex_;
    int value_ = 0;
    
public:
    void increment() {
        std::lock_guard<std::mutex> lock(mutex_);
        ++value_;
    }
    
    int get() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return value_;
    }
};
```

### Example 2: Thread-Safe Queue
```cpp
#include <queue>
#include <mutex>
#include <optional>

template<typename T>
class ThreadSafeQueue {
    std::queue<T> queue_;
    mutable std::mutex mutex_;
    
public:
    void push(T value) {
        std::lock_guard<std::mutex> lock(mutex_);
        queue_.push(std::move(value));
    }
    
    std::optional<T> pop() {
        std::lock_guard<std::mutex> lock(mutex_);
        if (queue_.empty()) {
            return std::nullopt;
        }
        T value = std::move(queue_.front());
        queue_.pop();
        return value;
    }
    
    bool empty() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return queue_.empty();
    }
};
```

### Example 3: Lazy Initialization
```cpp
#include <mutex>
#include <memory>

class Singleton {
    static std::unique_ptr<Singleton> instance_;
    static std::mutex mutex_;
    
    Singleton() = default;
    
public:
    static Singleton& getInstance() {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!instance_) {
            instance_ = std::unique_ptr<Singleton>(new Singleton());
        }
        return *instance_;
    }
};

// Better: use std::call_once
std::once_flag flag;
std::unique_ptr<Singleton> instance;

Singleton& getInstance() {
    std::call_once(flag, []() {
        instance = std::make_unique<Singleton>();
    });
    return *instance;
}
```

## Performance Considerations
```cpp
// Minimize critical section size
std::mutex mtx;

void inefficient() {
    std::lock_guard<std::mutex> lock(mtx);
    expensiveComputation();  // Should be outside lock!
    sharedData = result;
}

void efficient() {
    auto result = expensiveComputation();  // Outside lock
    {
        std::lock_guard<std::mutex> lock(mtx);
        sharedData = result;  // Minimal critical section
    }
}
```

## Best Practices

:::success
**DO:**
- Always use RAII locks (lock_guard, unique_lock)
- Keep critical sections small
- Use scoped_lock for multiple mutexes
- Use shared_mutex for read-heavy workloads
- Consider std::call_once for one-time initialization
  :::

:::danger
**DON'T:**
- Manually lock/unlock (error-prone)
- Lock in inconsistent order (causes deadlock)
- Hold locks longer than necessary
- Nest locks carelessly
- Use mutexes for simple counters (use atomics)
  :::

## Mutex Comparison

| Type                   | Use Case            | Multiple Locks |
|------------------------|---------------------|----------------|
| `std::mutex`           | Basic protection    | No             |
| `std::recursive_mutex` | Recursive functions | No             |
| `std::timed_mutex`     | With timeout        | No             |
| `std::shared_mutex`    | Reader-writer       | Yes (shared)   |

## Related Topics

- **[Threads](05-threads.md)** - Thread basics
- **[Condition Variables](07-condition-variables.md)** - Thread coordination
- **[Data Races](04-data-races.md)** - Avoiding races
- **[Atomics](02-atomics.md)** - Lock-free alternative