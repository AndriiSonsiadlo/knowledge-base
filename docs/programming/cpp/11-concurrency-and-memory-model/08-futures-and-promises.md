---
id: futures-and-promises
title: Futures and Promises
sidebar_label: Futures & Promises
sidebar_position: 8
tags: [cpp, concurrency, futures, promises, async, threading]
---

# Futures and Promises

**Futures** and **promises** provide a mechanism for asynchronous computation: one thread computes a value and another retrieves it later.

## Basic Concepts
```mermaid
graph LR
    A[Promise] -->|set_value| B[Shared State]
    B -->|get| C[Future]
    
    D[Producer Thread] --> A
    C --> E[Consumer Thread]
```
```cpp
#include <future>

void producer(std::promise<int> prom) {
    // Compute value
    int result = 42;
    prom.set_value(result);  // Make available to future
}

void consumer() {
    std::promise<int> prom;
    std::future<int> fut = prom.get_future();
    
    std::thread t(producer, std::move(prom));
    
    int value = fut.get();  // Blocks until value available
    std::cout << "Result: " << value << '\n';
    
    t.join();
}
```

## std::async

Easier way to run async tasks:
```cpp
#include <future>

int compute() {
    return 42;
}

int main() {
    // Launch async task
    std::future<int> result = std::async(std::launch::async, compute);
    
    // Do other work...
    
    // Get result (blocks if not ready)
    std::cout << "Result: " << result.get() << '\n';
}
```

### Launch Policies
```cpp
#include <future>

// async: definitely runs in separate thread
auto fut1 = std::async(std::launch::async, compute);

// deferred: runs in calling thread when get() called
auto fut2 = std::async(std::launch::deferred, compute);

// async | deferred: implementation chooses (default)
auto fut3 = std::async(std::launch::async | std::launch::deferred, compute);
auto fut4 = std::async(compute);  // Same as above
```

## std::promise and std::future

### Basic Promise/Future
```cpp
#include <future>
#include <thread>

void asyncTask(std::promise<std::string> prom) {
    try {
        // Do work
        std::string result = "Success!";
        prom.set_value(result);
    }
    catch (...) {
        // Communicate exception
        prom.set_exception(std::current_exception());
    }
}

int main() {
    std::promise<std::string> prom;
    std::future<std::string> fut = prom.get_future();
    
    std::thread t(asyncTask, std::move(prom));
    
    try {
        std::string result = fut.get();
        std::cout << result << '\n';
    }
    catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << '\n';
    }
    
    t.join();
}
```

### Promise Operations
```cpp
std::promise<int> prom;

// Set value (can only be called once)
prom.set_value(42);

// Set exception
prom.set_exception(std::make_exception_ptr(std::runtime_error("Error")));

// Set value at thread exit
prom.set_value_at_thread_exit(42);

// Get future
std::future<int> fut = prom.get_future();
```

### Future Operations
```cpp
std::future<int> fut = std::async(compute);

// Get value (blocks, can only call once)
int value = fut.get();

// Check if ready (non-blocking)
if (fut.valid()) {
    // Future has shared state
}

// Wait for result
fut.wait();

// Wait with timeout
if (fut.wait_for(std::chrono::seconds(1)) == std::future_status::ready) {
    int value = fut.get();
}

// Wait until time point
auto deadline = std::chrono::system_clock::now() + std::chrono::seconds(5);
fut.wait_until(deadline);
```

## std::shared_future

Multiple threads can wait on same result:
```cpp
#include <future>

int compute() {
    return 42;
}

int main() {
    std::shared_future<int> shared = std::async(compute).share();
    
    // Multiple threads can call get()
    std::thread t1([shared] {
        std::cout << "T1: " << shared.get() << '\n';
    });
    
    std::thread t2([shared] {
        std::cout << "T2: " << shared.get() << '\n';
    });
    
    t1.join();
    t2.join();
}
```

## std::packaged_task

Wraps callable object with future:
```cpp
#include <future>

int multiply(int a, int b) {
    return a * b;
}

int main() {
    std::packaged_task<int(int, int)> task(multiply);
    std::future<int> result = task.get_future();
    
    // Run task (can be in another thread)
    task(6, 7);
    
    std::cout << "Result: " << result.get() << '\n';  // 42
}
```

### Packaged Task with Thread
```cpp
std::packaged_task<int()> task([]{ return 42; });
std::future<int> result = task.get_future();

std::thread t(std::move(task));  // Run in thread

std::cout << result.get() << '\n';
t.join();
```

## Practical Examples

### Example 1: Parallel Computation
```cpp
#include <future>
#include <vector>
#include <numeric>

long long parallelSum(const std::vector<int>& data) {
    size_t mid = data.size() / 2;
    
    // Compute first half async
    auto fut = std::async(std::launch::async, [&] {
        return std::accumulate(data.begin(), data.begin() + mid, 0LL);
    });
    
    // Compute second half in current thread
    long long sum2 = std::accumulate(data.begin() + mid, data.end(), 0LL);
    
    // Get first half result
    long long sum1 = fut.get();
    
    return sum1 + sum2;
}
```

### Example 2: Timeout Pattern
```cpp
#include <future>
#include <chrono>

template<typename F>
auto withTimeout(F func, std::chrono::seconds timeout) {
    auto fut = std::async(std::launch::async, func);
    
    if (fut.wait_for(timeout) == std::future_status::timeout) {
        throw std::runtime_error("Operation timed out");
    }
    
    return fut.get();
}

// Usage
try {
    auto result = withTimeout(expensiveComputation, std::chrono::seconds(5));
}
catch (const std::runtime_error& e) {
    std::cerr << e.what() << '\n';
}
```

### Example 3: Pipeline Pattern
```cpp
#include <future>

int stage1(int input) {
    return input * 2;
}

int stage2(int input) {
    return input + 10;
}

int stage3(int input) {
    return input * input;
}

int pipeline(int input) {
    auto fut1 = std::async(std::launch::async, stage1, input);
    auto fut2 = std::async(std::launch::async, stage2, fut1.get());
    auto fut3 = std::async(std::launch::async, stage3, fut2.get());
    
    return fut3.get();
}
```

### Example 4: Exception Propagation
```cpp
#include <future>

int riskyComputation() {
    if (/* error condition */) {
        throw std::runtime_error("Computation failed");
    }
    return 42;
}

int main() {
    auto fut = std::async(std::launch::async, riskyComputation);
    
    try {
        int result = fut.get();  // Exception propagated here
        std::cout << "Result: " << result << '\n';
    }
    catch (const std::exception& e) {
        std::cerr << "Caught: " << e.what() << '\n';
    }
}
```

## std::async vs std::thread

| `std::async` | `std::thread` |
|-------------|---------------|
| Returns future with result | No return value |
| Automatic exception propagation | Manual exception handling |
| Can defer execution | Always runs immediately |
| Easier to use | More control |
```cpp
// async: automatic result handling
auto result = std::async(compute).get();

// thread: manual result handling
int result;
std::thread t([&result] { result = compute(); });
t.join();
```

## Waiting Strategies
```cpp
std::future<int> fut = std::async(compute);

// 1. Blocking wait
int result = fut.get();

// 2. Check if ready
if (fut.wait_for(std::chrono::seconds(0)) == std::future_status::ready) {
    int result = fut.get();
}

// 3. Timed wait
auto status = fut.wait_for(std::chrono::seconds(1));
if (status == std::future_status::ready) {
    // Ready
} else if (status == std::future_status::timeout) {
    // Not ready yet
}
```

## Best Practices

:::success
**DO:**
- Use `std::async` for simple async operations
- Handle exceptions from futures
- Check `valid()` before calling `get()`
- Use `shared_future` for multiple waiters
- Consider timeouts for long operations
  :::

:::danger
**DON'T:**
- Call `get()` multiple times (only once!)
- Forget to call `get()` or `wait()` on futures from `async`
- Assume `async` always creates new thread
- Ignore exceptions from futures
- Use promise after calling `set_value()`
  :::

## Common Patterns
```cpp
// Pattern 1: Fire-and-forget with error handling
auto fut = std::async(std::launch::async, riskyTask);
// Later: check for errors
try { fut.get(); } catch (...) { }

// Pattern 2: Multiple async tasks
std::vector<std::future<int>> futures;
for (int i = 0; i < 10; ++i) {
    futures.push_back(std::async(compute, i));
}
for (auto& f : futures) {
    results.push_back(f.get());
}

// Pattern 3: Promise for one-time notification
std::promise<void> signal;
auto fut = signal.get_future();
// In another thread:
signal.set_value();  // Signal ready
```

## Related Topics

- **[Threads](05-threads.md)** - Thread basics
- **[Thread Pools](09-thread-pools.md)** - Managed async execution
- **[Condition Variables](07-condition-variables.md)** - Thread coordination
- **[std::async](https://en.cppreference.com/w/cpp/thread/async)** - Reference