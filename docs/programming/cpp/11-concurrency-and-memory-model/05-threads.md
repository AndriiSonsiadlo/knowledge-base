---
id: threads
title: Thread Management
sidebar_label: Threads
sidebar_position: 5
tags: [cpp, concurrency, threads, threading, parallelism]
---

# Thread Management

**Threads** allow programs to perform multiple operations concurrently. C++11 introduced `std::thread` for portable threading.

## Basic Thread Creation
```cpp
#include <iostream>
#include <thread>

void hello() {
    std::cout << "Hello from thread!\n";
}

int main() {
    std::thread t(hello);  // Create and start thread
    t.join();              // Wait for thread to finish
    return 0;
}
```

## Thread Lifecycle
```mermaid
graph LR
    A[Created] --> B[Running]
    B --> C[join/detach]
    C --> D[Finished]
    
    style B fill:#90EE90
```
```cpp
#include <thread>

void task() {
    // Do work
}

int main() {
    std::thread t(task);
    
    // Must either join or detach before destruction!
    if (t.joinable()) {
        t.join();      // Wait for completion
        // OR
        // t.detach();  // Run independently
    }
    
    // t.~thread() would call std::terminate if not joined/detached
}
```

:::danger
A `std::thread` object must be either **joined** or **detached** before destruction, or `std::terminate()` is called!
:::

## Passing Arguments
```cpp
#include <thread>
#include <string>

void printMessage(int id, const std::string& msg) {
    std::cout << "Thread " << id << ": " << msg << '\n';
}

int main() {
    std::thread t1(printMessage, 1, "Hello");
    std::thread t2(printMessage, 2, "World");
    
    t1.join();
    t2.join();
}
```

### Passing by Reference
```cpp
#include <thread>

void increment(int& value) {
    ++value;
}

int main() {
    int counter = 0;
    
    // Must use std::ref for references
    std::thread t(increment, std::ref(counter));
    t.join();
    
    std::cout << counter << '\n';  // 1
}
```

### Passing Member Functions
```cpp
#include <thread>

class Worker {
public:
    void doWork(int param) {
        // Work
    }
};

int main() {
    Worker w;
    std::thread t(&Worker::doWork, &w, 42);
    t.join();
}
```

## Lambdas with Threads
```cpp
#include <thread>
#include <vector>

int main() {
    std::vector<std::thread> threads;
    
    for (int i = 0; i < 5; ++i) {
        threads.emplace_back([i]() {
            std::cout << "Thread " << i << '\n';
        });
    }
    
    for (auto& t : threads) {
        t.join();
    }
}
```

## Thread Management

### join() - Wait for Completion
```cpp
std::thread t(task);
t.join();  // Block until thread finishes
// Thread resources are cleaned up
```

### detach() - Independent Execution
```cpp
std::thread t(task);
t.detach();  // Thread runs independently
// Cannot join later, thread manages its own lifetime
```

### joinable() - Check State
```cpp
std::thread t(task);

if (t.joinable()) {
    t.join();  // Safe to join
}

// After join/detach, no longer joinable
assert(!t.joinable());
```

## Thread IDs
```cpp
#include <thread>
#include <iostream>

void printThreadId() {
    std::cout << "Thread ID: " << std::this_thread::get_id() << '\n';
}

int main() {
    std::thread t1(printThreadId);
    std::thread t2(printThreadId);
    
    std::cout << "Main thread ID: " << std::this_thread::get_id() << '\n';
    std::cout << "t1 ID: " << t1.get_id() << '\n';
    std::cout << "t2 ID: " << t2.get_id() << '\n';
    
    t1.join();
    t2.join();
}
```

## Thread-Local Storage
```cpp
#include <thread>
#include <iostream>

thread_local int counter = 0;  // Each thread has its own copy

void increment() {
    ++counter;
    std::cout << "Thread " << std::this_thread::get_id() 
              << ": counter = " << counter << '\n';
}

int main() {
    std::thread t1(increment);
    std::thread t2(increment);
    
    t1.join();
    t2.join();
    
    std::cout << "Main counter: " << counter << '\n';  // 0 (separate copy)
}
```

## Hardware Concurrency
```cpp
#include <thread>
#include <iostream>

int main() {
    unsigned int numThreads = std::thread::hardware_concurrency();
    std::cout << "Hardware threads: " << numThreads << '\n';
    
    // Create optimal number of threads
    std::vector<std::thread> workers;
    for (unsigned int i = 0; i < numThreads; ++i) {
        workers.emplace_back(doWork);
    }
    
    for (auto& t : workers) {
        t.join();
    }
}
```

## Practical Examples

### Example 1: Parallel Sum
```cpp
#include <thread>
#include <vector>
#include <numeric>

void partialSum(const std::vector<int>& data, size_t start, size_t end, 
                long long& result) {
    result = std::accumulate(data.begin() + start, 
                            data.begin() + end, 0LL);
}

long long parallelSum(const std::vector<int>& data) {
    size_t numThreads = std::thread::hardware_concurrency();
    size_t chunkSize = data.size() / numThreads;
    
    std::vector<std::thread> threads;
    std::vector<long long> results(numThreads);
    
    for (size_t i = 0; i < numThreads; ++i) {
        size_t start = i * chunkSize;
        size_t end = (i == numThreads - 1) ? data.size() : (i + 1) * chunkSize;
        
        threads.emplace_back(partialSum, std::cref(data), start, end, 
                            std::ref(results[i]));
    }
    
    for (auto& t : threads) {
        t.join();
    }
    
    return std::accumulate(results.begin(), results.end(), 0LL);
}
```

### Example 2: RAII Thread Wrapper
```cpp
#include <thread>

class ThreadGuard {
    std::thread& thread_;
    
public:
    explicit ThreadGuard(std::thread& t) : thread_(t) {}
    
    ~ThreadGuard() {
        if (thread_.joinable()) {
            thread_.join();
        }
    }
    
    ThreadGuard(const ThreadGuard&) = delete;
    ThreadGuard& operator=(const ThreadGuard&) = delete;
};

void usage() {
    std::thread t(task);
    ThreadGuard guard(t);
    
    // If exception thrown, guard ensures thread is joined
    riskyOperation();
    
}  // guard destructor joins thread
```

### Example 3: Scoped Thread (C++20)
```cpp
#include <thread>

class ScopedThread {
    std::thread thread_;
    
public:
    template<typename... Args>
    explicit ScopedThread(Args&&... args) 
        : thread_(std::forward<Args>(args)...) {}
    
    ~ScopedThread() {
        if (thread_.joinable()) {
            thread_.join();
        }
    }
    
    ScopedThread(const ScopedThread&) = delete;
    ScopedThread& operator=(const ScopedThread&) = delete;
};

void usage() {
    ScopedThread t(task);  // Automatically joined on scope exit
}
```

## Sleep and Yield
```cpp
#include <thread>
#include <chrono>

void sleepExample() {
    // Sleep for duration
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    
    // Sleep until time point
    auto wakeup = std::chrono::system_clock::now() + std::chrono::seconds(1);
    std::this_thread::sleep_until(wakeup);
    
    // Yield to other threads
    std::this_thread::yield();
}
```

## Exception Handling
```cpp
#include <thread>
#include <exception>

void riskyTask() {
    try {
        // May throw
        throw std::runtime_error("Error!");
    }
    catch (const std::exception& e) {
        // Handle in thread
        std::cerr << "Thread exception: " << e.what() << '\n';
    }
}

int main() {
    std::thread t(riskyTask);
    t.join();
    // Exception handled in thread, doesn't propagate to main
}
```

## Best Practices

:::success
**DO:**
- Always join or detach threads before destruction
- Use RAII wrappers for automatic joining
- Consider hardware_concurrency() for thread count
- Handle exceptions within threads
- Use thread-local storage for per-thread data
  :::

:::danger
**DON'T:**
- Create too many threads (use thread pools instead)
- Forget to join/detach (causes std::terminate)
- Share data without synchronization
- Assume thread execution order
- Ignore thread lifetime issues
  :::

## Common Patterns
```cpp
// Pattern 1: Fire and forget (detach)
std::thread([]{ logToFile("message"); }).detach();

// Pattern 2: Collect results with join
std::vector<std::thread> workers;
for (int i = 0; i < n; ++i) {
    workers.emplace_back(processChunk, i);
}
for (auto& t : workers) {
    t.join();
}

// Pattern 3: Move threads into containers
std::vector<std::thread> threads;
threads.push_back(std::thread(task));  // Move construction
```

## Related Topics

- **[Mutexes](06-mutexes.md)** - Thread synchronization
- **[Condition Variables](07-condition-variables.md)** - Thread coordination
- **[Thread Pools](09-thread-pools.md)** - Efficient thread management
- **[Data Races](04-data-races.md)** - Avoiding race conditions