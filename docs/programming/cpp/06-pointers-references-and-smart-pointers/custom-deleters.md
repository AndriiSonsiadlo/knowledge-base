---
id: custom-deleters
title: Custom Deleters
sidebar_label: Custom Deleters
sidebar_position: 8
tags: [c++, smart-pointers, deleters, resource-management, raii]
---

# Custom Deleters

Custom deleters allow smart pointers to manage resources that require cleanup beyond simple `delete`. They enable RAII for file handles, database connections, system resources, and any object with special cleanup requirements.

:::info Beyond delete
Default deleters call `delete` or `delete[]`. Custom deleters can close files, unlock mutexes, release system handles, or perform any cleanup operation.
:::

## The Concept

Smart pointers call a deleter function when the managed object should be destroyed. By default, this is `delete`, but you can provide custom cleanup logic.

```cpp
// Default deleter uses delete
auto ptr1 = std::make_unique<int>(42);
// Equivalent to: delete ptr;

// Custom deleter for FILE*
auto deleter = [](FILE* f) {
    if (f) {
        std::cout << "Closing file\n";
        fclose(f);
    }
};

std::unique_ptr<FILE, decltype(deleter)> file(
    fopen("data.txt", "r"),
    deleter
);
// Calls deleter when file goes out of scope
```

The deleter is called when the smart pointer is destroyed, providing automatic cleanup even if exceptions occur. This extends RAII to resources that aren't heap-allocated objects.

## unique_ptr with Custom Deleters

For unique_ptr, the deleter type is part of the type signature, affecting the size and interface.

```cpp
// Deleter type is template parameter
auto deleter = [](int* p) {
    std::cout << "Custom delete\n";
    delete p;
};

std::unique_ptr<int, decltype(deleter)> ptr(new int(42), deleter);

// Without deleter
std::unique_ptr<int> ptr2(new int(100));

// These are different types!
// decltype(ptr) != decltype(ptr2)
```

The deleter type must be specified in the template parameters. Lambda deleters require `decltype` to capture their type. This makes unique_ptr with custom deleters less convenient than shared_ptr, but it maintains zero-overhead principle.

### Function Pointer Deleters

Function pointers as deleters are simpler but less flexible than lambdas.

```cpp
void customDelete(int* p) {
    std::cout << "Function delete\n";
    delete p;
}

// Specify deleter type explicitly
std::unique_ptr<int, void(*)(int*)> ptr(new int(42), customDelete);

// Or use decltype
std::unique_ptr<int, decltype(&customDelete)> ptr2(new int(100), customDelete);
```

Function pointer deleters don't increase the size of unique_ptr beyond a single function pointer. They're appropriate for stateless cleanup operations.

### Lambda Deleters

Lambdas are more flexible, allowing capture of state needed for cleanup.

```cpp
std::string filename = "data.txt";

auto deleter = [filename](FILE* f) {
    if (f) {
        std::cout << "Closing " << filename << "\n";
        fclose(f);
    }
};

std::unique_ptr<FILE, decltype(deleter)> file(
    fopen(filename.c_str(), "r"),
    deleter
);
```

Capturing lambdas increase unique_ptr's size by the capture size. Stateless lambdas (no captures) are as efficient as function pointers and can often be optimized to zero size.

## shared_ptr with Custom Deleters

shared_ptr handles custom deleters more elegantly - the deleter type is not part of the type signature.

```cpp
auto deleter = [](int* p) {
    std::cout << "Custom delete\n";
    delete p;
};

std::shared_ptr<int> ptr1(new int(42), deleter);
std::shared_ptr<int> ptr2(new int(100), deleter);

// Same type! Can assign, compare, store in containers
ptr1 = ptr2;  // ✅ Works because both are shared_ptr<int>
```

The deleter is stored in the control block, not the shared_ptr itself. This means all shared_ptrs to the same type are interchangeable regardless of deleter. This is more convenient but has a small memory cost (deleter stored in control block).

### Type Erasure

shared_ptr uses type erasure for deleters, enabling mixing different deleters of the same type.

```cpp
void deleter1(int* p) { delete p; }
auto deleter2 = [](int* p) { delete p; };

std::shared_ptr<int> ptr1(new int(1), deleter1);
std::shared_ptr<int> ptr2(new int(2), deleter2);

std::vector<std::shared_ptr<int>> vec;
vec.push_back(ptr1);  // ✅ Function pointer deleter
vec.push_back(ptr2);  // ✅ Lambda deleter
// Both work because they're both shared_ptr<int>
```

This flexibility makes shared_ptr easier to use with custom deleters than unique_ptr, at the cost of always storing the deleter in the control block (small memory overhead).

## Common Use Cases

### File Handles

Managing C file handles with RAII using smart pointers.

```cpp
auto fileDeleter = [](FILE* f) {
    if (f) {
        std::cout << "Closing file\n";
        fclose(f);
    }
};

std::shared_ptr<FILE> openFile(const char* path, const char* mode) {
    return std::shared_ptr<FILE>(fopen(path, mode), fileDeleter);
}

auto file = openFile("data.txt", "r");
if (file) {
    char buffer[256];
    fgets(buffer, sizeof(buffer), file.get());
}
// File automatically closed
```

The file is automatically closed when the last shared_ptr is destroyed, even if exceptions occur. This is much safer than manual fclose calls.

### Mutex Unlocking

Custom deleters can unlock mutexes, though std::lock_guard is usually better.

```cpp
std::mutex mtx;

void process() {
    // Custom deleter unlocks mutex
    std::unique_ptr<std::mutex, void(*)(std::mutex*)> lock(
        &mtx,
        [](std::mutex* m) { m->unlock(); }
    );
    
    mtx.lock();
    
    // Work with protected data
    
    // Mutex automatically unlocked when lock destroyed
}

// Better: use std::lock_guard
void better_process() {
    std::lock_guard<std::mutex> lock(mtx);
    // Automatically unlocked
}
```

While this demonstrates custom deleters, standard lock management facilities (lock_guard, unique_lock) are better for mutexes. Use custom deleters for resources without standard RAII wrappers.

### System Resources

Managing operating system resources like file descriptors or handles.

```cpp
#include <unistd.h>  // Unix file descriptors

auto fdDeleter = [](int* fd) {
    if (fd && *fd != -1) {
        std::cout << "Closing fd " << *fd << "\n";
        close(*fd);
    }
    delete fd;
};

std::shared_ptr<int> openSocket(int domain, int type, int protocol) {
    int fd = socket(domain, type, protocol);
    if (fd == -1) {
        return nullptr;
    }
    return std::shared_ptr<int>(new int(fd), fdDeleter);
}

auto sock = openSocket(AF_INET, SOCK_STREAM, 0);
// Socket automatically closed
```

System resources often use integers as handles. Wrapping them in smart pointers with custom deleters provides automatic cleanup and prevents resource leaks.

### Database Connections

Custom deleters work well for managing database connections or transactions.

```cpp
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

```cpp
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

```cpp
int global = 42;

// No-op deleter - doesn't delete
auto noopDeleter = [](int*) { /* do nothing */ };

std::shared_ptr<int> ptr(&global, noopDeleter);

// ptr observes global but won't delete it
*ptr = 100;
std::cout << global;  // 100

// Safe: no-op deleter called, nothing happens
```

This is useful when you need to store both owned and non-owned pointers in the same container using smart pointers.

## Deleter with State

Capturing state in lambda deleters enables context-aware cleanup.

```cpp
class Logger {
public:
    void log(const std::string& msg) {
        std::cout << "[LOG] " << msg << "\n";
    }
};

std::shared_ptr<Logger> logger = std::make_shared<Logger>();

auto deleter = [logger](int* p) {
    logger->log("Deleting resource");
    delete p;
};

std::shared_ptr<int> resource(new int(42), deleter);
// When resource destroyed, logs the deletion
```

The captured logger keeps the logger alive as long as any resources with this deleter exist. This enables logging, statistics, or notifications during cleanup.

## std::default_delete

The default deleter used by unique_ptr is available as `std::default_delete` for explicit use.

```cpp
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

You rarely need to use default_delete explicitly, but it's useful for template code that needs a consistent deleter interface.

## Performance Considerations

Custom deleters have different performance implications for unique_ptr and shared_ptr.

```cpp
// unique_ptr: deleter type affects size
auto lambda = [](int* p) { delete p; };
sizeof(std::unique_ptr<int, decltype(lambda)>);  
// Size includes lambda (+ captured state)

sizeof(std::unique_ptr<int>);  
// Just pointer size (8 bytes on 64-bit)

// shared_ptr: deleter in control block
sizeof(std::shared_ptr<int>);  
// Always 16 bytes regardless of deleter
// But control block is larger with custom deleter
```

For unique_ptr, stateless lambdas or function pointers don't increase size. Capturing lambdas do. For shared_ptr, the smart pointer size is constant but the control block grows.

:::warning Common Pitfalls

**Deleting Non-Owned Memory**: No-op deleters for non-owned pointers, or crashes result.

**Forgetting to Check nullptr**: Always check if pointer is valid before cleanup operations.

**Deleter Exceptions**: Deleters should be noexcept - exceptions during cleanup are dangerous.

**unique_ptr Type Complexity**: Custom deleters make unique_ptr types complex - use auto.

**Circular References**: Deleter capturing shared_ptr can create cycles - use weak_ptr.
:::

## Summary

Custom deleters extend smart pointers to manage any resource requiring cleanup beyond `delete`. For unique_ptr, the deleter type is a template parameter affecting the type signature and potentially size. Use lambdas with `decltype` or function pointers as deleters. For shared_ptr, deleters use type erasure and are stored in the control block, keeping all shared_ptrs of the same type compatible regardless of deleter. Common use cases include file handles (fclose), system resources (close file descriptors), database connections, mutex unlocking, and any resource needing special cleanup. Lambdas can capture state for context-aware cleanup like logging. No-op deleters enable smart pointers to non-owned memory. Deleters should be noexcept to prevent exceptions during cleanup. Always check pointer validity before cleanup operations. shared_ptr deleters are more convenient (type-erased) but have small memory overhead. unique_ptr deleters have zero overhead if stateless but complicate types. Prefer standard RAII wrappers (lock_guard, fstream) when available, use custom deleters for resources without standard wrappers. Custom deleters enable the RAII pattern for any resource: files, handles, connections, transactions, locks - anything that needs cleanup. This makes C++ resource management automatic and exception-safe across all resource types, not just heap memory.

:::success Key Takeaways

**Beyond delete**: Manage any resource - files, handles, connections, locks.

**unique_ptr**: Deleter type is template parameter, affects type signature.

**shared_ptr**: Deleter type-erased in control block, more convenient.

**RAII for Everything**: Extend automatic cleanup to all resource types.

**Exception Safety**: Cleanup happens automatically even during exceptions.

**Lambda Capture**: Enable context-aware cleanup with captured state.

**No-op Deleter**: Use for non-owned memory that shouldn't be deleted.

**Always noexcept**: Deleters should never throw exceptions.
:::