---
id: storage-duration
title: Storage Duration
sidebar_label: Storage Duration
sidebar_position: 2
tags: [c++, storage-duration, lifetime, memory]
---

# Storage Duration

Storage duration defines when and where objects are created and destroyed. C++ has four storage durations: automatic, static, dynamic, and thread.

:::info Lifetime Determines Behavior
Storage duration affects performance, thread-safety, and memory management strategy.
:::

## Four Storage Durations

| Duration | When Created | When Destroyed | Location |
|----------|--------------|----------------|----------|
| **Automatic** | Block entry | Block exit | Stack |
| **Static** | Program start | Program end | Data segment |
| **Dynamic** | Explicit `new` | Explicit `delete` | Heap |
| **Thread** | Thread start | Thread end | Thread-local |

---

## Automatic Storage Duration

Default for local variables:

```cpp showLineNumbers 
void function() {
    int x = 42;        // Created
    Widget w;          // Constructor called
    
    if (condition) {
        int y = 10;    // Created inside if
    }                  // y destroyed
    
}  // x and w destroyed (destructor called for w)
```

**Characteristics**:
- Fast allocation (stack)
- LIFO destruction order
- Scope-based lifetime
- No memory leaks possible

### Destruction Order

```cpp showLineNumbers 
{
    Widget a;
    Widget b;
    Widget c;
}  // Destroyed in reverse: c, b, a
```

---

## Static Storage Duration

Exists for entire program:

```cpp showLineNumbers 
// Global scope
int global = 42;                    // Static duration

// File scope
static int file_scope = 100;        // Static duration

// Function scope
void function() {
    static int call_count = 0;      // Static duration
    call_count++;
}

// Class scope
class Widget {
    static int instance_count;      // Static duration (definition needed)
};
int Widget::instance_count = 0;
```

### Initialization

```cpp showLineNumbers 
// Zero-initialization first
int global_uninit;  // Zero before program starts

// Constant initialization (compile-time if possible)
constexpr int compile_time = 42;

// Dynamic initialization (runtime)
int runtime_init = getValue();  // Called before main()
```

### Initialization Order Issues

```cpp showLineNumbers 
// file1.cpp
int a = compute_a();

// file2.cpp
int b = compute_b();  // Uses 'a'

// ⚠️ Order undefined across translation units!
// b might initialize before a
```

**Solution**: Local static (lazy initialization):

```cpp showLineNumbers 
Widget& getInstance() {
    static Widget instance;  // Initialized on first call (thread-safe C++11+)
    return instance;
}
```

---

## Dynamic Storage Duration

Manual lifetime control:

```cpp showLineNumbers 
// Create
int* ptr = new int(42);
Widget* w = new Widget();

// Use...

// Destroy
delete ptr;
delete w;  // Calls destructor

// Array
int* arr = new int[10];
delete[] arr;  // Use delete[], not delete!
```

### Common Patterns

```cpp showLineNumbers 
// RAII wrapper (preferred)
std::unique_ptr<Widget> ptr = std::make_unique<Widget>();
// Automatic delete when ptr goes out of scope

// Shared ownership
std::shared_ptr<Widget> shared = std::make_shared<Widget>();
// Deleted when last shared_ptr destroyed
```

### Memory Management

```cpp showLineNumbers 
class Buffer {
    char* data;
    size_t size;
    
public:
    Buffer(size_t s) : size(s) {
        data = new char[size];  // Dynamic allocation
    }
    
    ~Buffer() {
        delete[] data;  // Manual cleanup
    }
    
    // Rule of Five for dynamic resources
    Buffer(const Buffer&);
    Buffer& operator=(const Buffer&);
    Buffer(Buffer&&) noexcept;
    Buffer& operator=(Buffer&&) noexcept;
};
```

---

## Thread Storage Duration (C++11)

One instance per thread:

```cpp showLineNumbers 
thread_local int tls_counter = 0;  // Separate for each thread

void thread_function() {
    tls_counter++;  // Each thread has own copy
    std::cout << tls_counter << "\n";
}

std::thread t1(thread_function);  // tls_counter = 1
std::thread t2(thread_function);  // Different tls_counter = 1
```

**Use cases**:
- Thread-specific caches
- Per-thread random number generators
- Thread-local error codes

---

## Storage Duration Examples

### Example 1: Mixing Durations

```cpp showLineNumbers 
int global = 10;  // Static

void function() {
    int local = 20;  // Automatic
    static int function_static = 30;  // Static
    
    int* dynamic = new int(40);  // Dynamic
    
    thread_local int tls = 50;  // Thread
    
    delete dynamic;
}  // local destroyed, others remain
```

### Example 2: Lifetime Demonstration

```cpp showLineNumbers 
class Logger {
public:
    Logger(const char* name) : name_(name) {
        std::cout << name_ << " created\n";
    }
    ~Logger() {
        std::cout << name_ << " destroyed\n";
    }
private:
    const char* name_;
};

Logger global("Global");  // Created before main

int main() {
    Logger local("Local");  // Created on entry
    
    static Logger static_obj("Static");  // Created on first encounter
    
    Logger* dynamic = new Logger("Dynamic");  // Created by new
    
    delete dynamic;  // Destroyed by delete
    
}  // local destroyed
  // static_obj destroyed
  // global destroyed
```

**Output**:
```
Global created
Local created
Static created
Dynamic created
Dynamic destroyed
Local destroyed
Static destroyed
Global destroyed
```

---

## Performance Comparison

```cpp showLineNumbers 
// Automatic (fastest)
void fast() {
    int arr[1000];  // Stack allocation
}  // Instant cleanup

// Static (once per program)
void lazy_init() {
    static ExpensiveObject obj;  // Only first call pays cost
}

// Dynamic (slowest)
void slow() {
    int* arr = new int[1000];  // Heap allocation
    delete[] arr;  // Explicit cleanup
}
```

**Benchmark** (typical):
- Automatic: ~1 ns
- Dynamic: ~50-100 ns (malloc/free overhead)
- Thread-local: ~5-10 ns (TLS access)

---

## Common Patterns

### Singleton (Static)

```cpp showLineNumbers 
class Singleton {
public:
    static Singleton& getInstance() {
        static Singleton instance;  // Thread-safe in C++11+
        return instance;
    }
    
private:
    Singleton() = default;
    Singleton(const Singleton&) = delete;
};
```

### Factory (Dynamic)

```cpp showLineNumbers 
std::unique_ptr<Widget> createWidget() {
    return std::make_unique<Widget>();  // Dynamic
}

auto widget = createWidget();
// Automatic cleanup when widget destroyed
```

### Thread Pool (Thread-local)

```cpp showLineNumbers 
thread_local std::vector<Task> local_queue;

void worker_thread() {
    // Each thread has own queue
    local_queue.push_back(task);
}
```

---

## Summary

**Storage durations**:
```cpp showLineNumbers 
// Automatic (default)
int local;          // Destroyed at scope end

// Static (program lifetime)
static int s;       // Destroyed at program end
int global;         // Destroyed at program end

// Dynamic (manual)
int* p = new int;   // Lives until delete
delete p;

// Thread (per-thread)
thread_local int t; // Destroyed when thread ends
```

**Choosing duration**:
- **Automatic**: Default choice, fast, safe
- **Static**: Singletons, config, program-wide state
- **Dynamic**: Variable size, runtime decisions, shared ownership
- **Thread**: Per-thread caches, thread-local state

**Best practices**:
- Prefer automatic (stack) when possible
- Use smart pointers for dynamic allocations
- Static for true program-wide state only
- Thread-local for thread-specific data

Understanding storage duration is fundamental to memory management, performance optimization, and preventing lifetime bugs.