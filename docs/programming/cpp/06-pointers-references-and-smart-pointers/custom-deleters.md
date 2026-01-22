---
id: custom-deleters
title: Custom Deleters
sidebar_label: Custom Deleters
sidebar_position: 8
tags: [c++, smart-pointers, deleters, resource-management, raii]
---

# Custom Deleters

Extend smart pointers to manage any resource requiring special cleanup beyond `delete`. Enable RAII for files, handles, connections, locks - anything needing cleanup.

:::info Beyond delete
**Default:** `delete` or `delete[]`  
**Custom:** Close files, unlock mutexes, release handles, any cleanup

Smart pointers + custom deleters = RAII for everything
:::

## The Concept
```cpp showLineNumbers
// Default deleter
auto ptr1 = std::make_unique<int>(42);
// Calls: delete ptr

// Custom deleter
auto deleter = [](FILE* f) {
    if (f) fclose(f);
};

std::unique_ptr<FILE, decltype(deleter)> file(
    fopen("data.txt", "r"),
    deleter
);
// Calls: deleter(file) → fclose
```

The deleter is called when the smart pointer is destroyed, providing automatic cleanup even if exceptions occur. This extends RAII to resources that aren't heap-allocated objects.

## unique_ptr with Custom Deleters

For `unique_ptr`, the deleter type is part of the type signature, affecting the size and interface.

```cpp showLineNumbers 
// Lambda deleter
auto deleter = [](int* p) {
    std::cout << "Custom delete\n";
    delete p;
};

std::unique_ptr<int, decltype(deleter)> ptr(new int(42), deleter);

// Function pointer deleter
void customDelete(int* p) {
    std::cout << "Function delete\n";
    delete p;
}

std::unique_ptr<int, decltype(&customDelete)> ptr2(
    new int(100),
    customDelete
);

// These are DIFFERENT types
// decltype(ptr) != decltype(ptr2)
```

:::warning Type Signature
```cpp showLineNumbers
std::unique_ptr<int, Deleter1> p1;
std::unique_ptr<int, Deleter2> p2;

// ❌ Different types - cannot assign
// p1 = std::move(p2);  // Error

// Size depends on deleter
sizeof(p1);  // Varies based on Deleter1
```
:::

## shared_ptr with Custom Deleters

Deleter is type-erased, not part of type signature.
```cpp showLineNumbers
auto d1 = [](int* p) { delete p; };
auto d2 = [](int* p) { delete p; };

std::shared_ptr<int> ptr1(new int(1), d1);
std::shared_ptr<int> ptr2(new int(2), d2);

// ✅ Same type despite different deleters
ptr1 = ptr2;

std::vector<std::shared_ptr<int>> vec = {ptr1, ptr2};
```


The deleter is stored in the control block, not the `shared_ptr` itself. This means all `shared_ptr`s to the same type are interchangeable regardless of deleter. This is more convenient but has a small memory cost (deleter stored in control block).

:::success Type Erasure Advantage

`shared_ptr` uses type erasure for deleters, enabling mixing different deleters of the same type.

```cpp showLineNumbers
// All shared_ptr<T> are same type
void process(std::shared_ptr<Widget> w) {
    // Works with any deleter
}

// Can store in same container
std::vector<std::shared_ptr<Resource>> resources;
// Each can have different deleter
```
:::

This flexibility makes `shared_ptr` easier to use with custom deleters than `unique_ptr`, at the cost of always storing the deleter in the control block (small memory overhead).

## Common Use Cases

### File Handles

Managing C file handles with RAII using smart pointers.

```cpp showLineNumbers 
auto fileDeleter = [](FILE* f) {
    if (f) {
        std::cout << "Closing file\n";
        fclose(f);
    }
};

std::shared_ptr<FILE> openFile(const char* path, const char* mode) {
    FILE* f = fopen(path, mode);
    if (!f) return nullptr;
    
    return std::shared_ptr<FILE>(f, fileDeleter);
}

// Usage
auto file = openFile("data.txt", "r");
if (file) {
    char buffer[256];
    fgets(buffer, sizeof(buffer), file.get());
}
// File automatically closed
```

The file is automatically closed when the last `shared_ptr` is destroyed, even if exceptions occur. This is much safer than manual `fclose` calls.

### Mutex Unlocking

Custom deleters can unlock mutexes, though `std::lock_guard` is usually better.

```cpp showLineNumbers 
std::mutex mtx;

void process() {
    auto unlock = [](std::mutex* m) { m->unlock(); };
    
    std::unique_ptr<std::mutex, decltype(unlock)> lock(
        &mtx,
        unlock
    );
    
    mtx.lock();
    
    // Work with protected data
    
    // Mutex automatically unlocked when lock destroyed
}

// Better: use std::lock_guard
void better() {
    std::lock_guard<std::mutex> lock(mtx);
    // Automatically unlocked
}
```

While this demonstrates custom deleters, standard lock management facilities (`lock_guard`, `unique_lock`) are better for mutexes. Use custom deleters for resources without standard RAII wrappers.

### System Resources

Managing operating system resources like file descriptors or handles.

```cpp showLineNumbers 
#include <unistd.h>  // Unix file descriptors

auto fdDeleter = [](int* fd) {
    if (fd && *fd != -1) {
        std::cout << "Closing fd " << *fd << "\n";
        close(*fd);
        delete fd;
    }
};

std::shared_ptr<int> openSocket() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd == -1) return nullptr;
    
    return std::shared_ptr<int>(new int(fd), fdDeleter);
}

auto sock = openSocket();
// Socket automatically closed
```

System resources often use integers as handles. Wrapping them in smart pointers with custom deleters provides automatic cleanup and prevents resource leaks.

### Database Connections

Custom deleters work well for managing database connections or transactions.

```cpp showLineNumbers 
struct Connection {
    // Database connection handle
    void* handle;
    
    void close() {
        std::cout << "Closing connection\n";
        // Close database connection
    }
};

auto connectionDeleter = [](Connection* conn) {
    if (conn) {
        conn->close();
        delete conn;
    }
};

std::shared_ptr<Connection> openConnection(const std::string& connString) {
    auto conn = new Connection();
    // Open connection with connString
    return std::shared_ptr<Connection>(conn, connectionDeleter);
}
```

### Arrays with Custom Deletion

When managing arrays allocated with custom allocators.

```cpp showLineNumbers 
// Array with custom allocator
int* allocateArray(size_t size) {
    std::cout << "Custom allocate " << size << " ints\n";
    return static_cast<int*>(std::malloc(size * sizeof(int)));
}

void deallocateArray(int* arr) {
    std::cout << "Custom deallocate\n";
    std::free(arr);
}

std::unique_ptr<int[], void(*)(int*)> arr(
    allocateArray(10),
    deallocateArray
);

arr[0] = 42;
// Custom deallocate called automatically
```

## No-op Deleters

Sometimes you need a smart pointer to non-owned memory that shouldn't be deleted.

```cpp showLineNumbers 
int global = 42;

// No-op deleter - doesn't delete
auto noopDeleter = [](int*) { /* do nothing */ };

std::shared_ptr<int> ptr(&global, noopDeleter);

// ptr observes global but won't delete it
*ptr = 100;
std::cout << global;  // 100

// Safe: no-op deleter called, nothing happens
```

**Use case:** Mix owned/non-owned pointers in same container
```cpp showLineNumbers
std::vector<std::shared_ptr<Widget>> widgets;

auto owned = std::make_shared<Widget>();
Widget stack_widget;

widgets.push_back(owned);
widgets.push_back(std::shared_ptr<Widget>(&stack_widget, [](Widget*){}));
```

## Deleter with State

Capturing state in lambda deleters enables context-aware cleanup.

```cpp showLineNumbers 
class Logger {
public:
    void log(const std::string& msg) {
        std::cout << "[LOG] " << msg << "\n";
    }
};

auto logger = std::make_shared<Logger>();

auto deleter = [logger](int* p) {
    logger->log("Deleting resource");
    delete p;
};

std::shared_ptr<int> resource(new int(42), deleter);
// When resource destroyed, logs the deletion
```

The captured logger keeps the logger alive as long as any resources with this deleter exist. This enables logging, statistics, or notifications during cleanup.

## Deleter Comparison

| Feature | unique_ptr | shared_ptr |
|---------|-----------|------------|
| **Type signature** | Part of type | Type-erased |
| **Storage** | Inline (size varies) | Control block (size constant) |
| **Overhead** | Zero if stateless | Always stored |
| **Flexibility** | Less (type matters) | More (same type) |
| **Performance** | Better (no indirection) | Slight overhead |
```cpp showLineNumbers
// unique_ptr
auto d1 = [](int* p) { delete p; };
sizeof(std::unique_ptr<int, decltype(d1)>);  // 8 (stateless)

auto d2 = [x=42](int* p) { delete p; };
sizeof(std::unique_ptr<int, decltype(d2)>);  // 12 (captures int)

// shared_ptr
sizeof(std::shared_ptr<int>);  // Always 16
```

## std::default_delete

The default deleter used by `unique_ptr` is available as `std::default_delete` for explicit use.

```cpp showLineNumbers 
std::default_delete<int> deleter;

int* p = new int(42);
deleter(p);  // Equivalent to: delete p;

// Array specialization
std::default_delete<int[]> arrayDeleter;

int* arr = new int[10];
arrayDeleter(arr);  // Equivalent to: delete[] arr;

// Used implicitly by unique_ptr
std::unique_ptr<int> ptr(new int(42));
// Uses std::default_delete<int> internally
```

You rarely need to use `default_delete` explicitly, but it's useful for template code that needs a consistent deleter interface.

## Best Practices

:::success DO
- **Check null** before cleanup operations
- **Make deleters noexcept** - no exceptions during cleanup
- **Capture by value** for lambda deleters (avoid dangling refs)
- **Use shared_ptr** when deleter type flexibility needed
- **Prefer standard RAII** (fstream, lock_guard) when available
:::

:::danger DON'T
- **Delete non-owned memory** - use no-op deleter
- **Throw from deleters** - can terminate program
- **Forget null checks** - validate pointer before operations
- **Create circular deps** - captured shared_ptrs can leak
:::

## Performance Considerations

Custom deleters have different performance implications for `unique_ptr` and `shared_ptr`.

```cpp showLineNumbers 
// unique_ptr with stateless lambda
auto d1 = [](int* p) { delete p; };
sizeof(std::unique_ptr<int, decltype(d1)>);  // 8 bytes

// unique_ptr with capturing lambda
auto d2 = [logger](int* p) { delete p; };
sizeof(std::unique_ptr<int, decltype(d2)>);  // 8 + sizeof(logger)

// shared_ptr (always same)
sizeof(std::shared_ptr<int>);  // 16 bytes
// Deleter in control block
```

## Summary

:::info Core concept:
- Extend smart pointers to any resource
- Not just heap memory (files, handles, locks)
- RAII for everything
:::

:::info `unique_ptr` deleters:
- Type part of signature
- Zero overhead if stateless
- Requires `decltype` for lambdas
- Different deleters = different types
:::

:::info `shared_ptr` deleters:
- Type-erased (stored in control block)
- All `shared_ptr<T>` same type
- Small overhead (always stored)
- More flexible for heterogeneous collections
:::

:::info Common patterns:
- File handles (fclose)
- System resources (close fd)
- Database connections
- No-op for non-owned memory
- Stateful deleters (logging, metrics)
:::

:::info Guidelines:
- Always check null in deleter
- Make deleters noexcept
- Prefer standard RAII when available
- Use `shared_ptr` for deleter flexibility
- Use `unique_ptr` for zero overhead
:::
