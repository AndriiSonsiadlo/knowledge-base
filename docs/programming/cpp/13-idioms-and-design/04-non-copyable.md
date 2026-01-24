---
id: non-copyable
title: Non-Copyable Idiom
sidebar_label: Non-Copyable
sidebar_position: 4
tags: [cpp, non-copyable, idioms, raii, move-only]
---

# Non-Copyable Idiom

The non-copyable idiom prevents objects from being copied, ensuring unique ownership of resources. Essential for RAII types managing exclusive resources like file handles, mutexes, or database connections.

:::info Move-Only Types
Non-copyable types can still be moved, allowing transfer of ownership without duplication. Common pattern for resource-owning types.
:::

## Why Non-Copyable?

Some resources should not or cannot be copied:

```cpp showLineNumbers
// ❌ Copying these would be problematic
class FileHandle {
    int fd_;  // File descriptor
    // Copying fd_ would create two handles to same file!
};

class Mutex {
    pthread_mutex_t mutex_;
    // Copying mutex internals is nonsensical
};

class Database {
    ConnectionPtr conn_;
    // Two objects managing same connection = trouble
};
```

## Basic Non-Copyable Implementation

### C++11+ Way (Delete Functions)

```cpp showLineNumbers
class NonCopyable {
public:
    NonCopyable() = default;
    
    // Delete copy operations
    NonCopyable(const NonCopyable&) = delete;
    NonCopyable& operator=(const NonCopyable&) = delete;
    
    // Allow move operations (optional)
    NonCopyable(NonCopyable&&) = default;
    NonCopyable& operator=(NonCopyable&&) = default;
};

int main() {
    NonCopyable a;
    NonCopyable b = a;      // ❌ Error: deleted copy constructor
    NonCopyable c;
    c = a;                  // ❌ Error: deleted copy assignment
    
    NonCopyable d = std::move(a);  // ✅ OK: moved
}
```

**Explicit deletion** makes intent clear and provides better error messages.

### Pre-C++11 Way (Private Methods)

```cpp showLineNumbers
class NonCopyable {
public:
    NonCopyable() {}
    
private:
    // Private and unimplemented
    NonCopyable(const NonCopyable&);
    NonCopyable& operator=(const NonCopyable&);
};

// Attempting to copy gives linker error
```

This technique is obsolete; use `= delete` in modern C++.

## CRTP Non-Copyable Base

Reusable base class for making types non-copyable:

```cpp showLineNumbers
template<typename T>
class NonCopyable {
protected:
    NonCopyable() = default;
    ~NonCopyable() = default;
    
    NonCopyable(const NonCopyable&) = delete;
    NonCopyable& operator=(const NonCopyable&) = delete;
};

// Usage: inherit from NonCopyable<Derived>
class FileHandle : NonCopyable<FileHandle> {
    int fd_;
    
public:
    explicit FileHandle(const char* path) {
        fd_ = open(path, O_RDONLY);
    }
    
    ~FileHandle() {
        if (fd_ >= 0) close(fd_);
    }
    
    // Automatically non-copyable
};

// Boost style (no template parameter needed)
class NonCopyableBase {
protected:
    NonCopyableBase() = default;
    ~NonCopyableBase() = default;
    
private:
    NonCopyableBase(const NonCopyableBase&) = delete;
    NonCopyableBase& operator=(const NonCopyableBase&) = delete;
};

class MyClass : private NonCopyableBase {
    // Inheriting privately prevents copying
};
```

## Move-Only Types

Non-copyable but movable - common pattern for resource owners:

```cpp showLineNumbers
class UniqueResource {
    int* data_;
    
public:
    explicit UniqueResource(int value) 
        : data_(new int(value)) {}
    
    ~UniqueResource() {
        delete data_;
    }
    
    // Delete copy
    UniqueResource(const UniqueResource&) = delete;
    UniqueResource& operator=(const UniqueResource&) = delete;
    
    // Enable move
    UniqueResource(UniqueResource&& other) noexcept 
        : data_(other.data_) {
        other.data_ = nullptr;  // Steal resource
    }
    
    UniqueResource& operator=(UniqueResource&& other) noexcept {
        if (this != &other) {
            delete data_;           // Clean up our resource
            data_ = other.data_;    // Steal other's resource
            other.data_ = nullptr;  // Nullify other
        }
        return *this;
    }
    
    int get() const { return *data_; }
};

int main() {
    UniqueResource r1(42);
    
    UniqueResource r2 = r1;           // ❌ Error: deleted copy
    UniqueResource r3 = std::move(r1); // ✅ OK: moved
    
    // r1 is now in valid but unspecified state (data_ == nullptr)
    // r3 owns the resource
}
```

This is exactly how `std::unique_ptr` works.

## Real-World Examples

### File Handle Wrapper

```cpp showLineNumbers
class File {
    FILE* file_;
    
public:
    explicit File(const char* path, const char* mode) {
        file_ = fopen(path, mode);
        if (!file_) throw std::runtime_error("Failed to open file");
    }
    
    ~File() {
        if (file_) fclose(file_);
    }
    
    // Non-copyable
    File(const File&) = delete;
    File& operator=(const File&) = delete;
    
    // Movable
    File(File&& other) noexcept : file_(other.file_) {
        other.file_ = nullptr;
    }
    
    File& operator=(File&& other) noexcept {
        if (this != &other) {
            if (file_) fclose(file_);
            file_ = other.file_;
            other.file_ = nullptr;
        }
        return *this;
    }
    
    void write(const std::string& data) {
        fwrite(data.data(), 1, data.size(), file_);
    }
    
    FILE* get() const { return file_; }
};

// Usage
void writeLog(const std::string& message) {
    File log("app.log", "a");  // RAII
    log.write(message);
}  // Automatically closed
```

### Thread Wrapper

```cpp showLineNumbers
class Thread {
    std::thread thread_;
    
public:
    template<typename F, typename... Args>
    explicit Thread(F&& f, Args&&... args)
        : thread_(std::forward<F>(f), std::forward<Args>(args)...) {}
    
    ~Thread() {
        if (thread_.joinable()) {
            thread_.join();
        }
    }
    
    // Non-copyable (threads cannot be copied)
    Thread(const Thread&) = delete;
    Thread& operator=(const Thread&) = delete;
    
    // Movable
    Thread(Thread&&) = default;
    Thread& operator=(Thread&&) = default;
};

// Usage
Thread worker([]{ 
    std::cout << "Working...\n"; 
});  // Automatically joins on destruction
```

### Mutex Wrapper

```cpp showLineNumbers
class Mutex {
    std::mutex mutex_;
    
public:
    Mutex() = default;
    
    // Mutexes are fundamentally non-copyable
    Mutex(const Mutex&) = delete;
    Mutex& operator=(const Mutex&) = delete;
    
    // Also non-movable (moving a locked mutex is problematic)
    Mutex(Mutex&&) = delete;
    Mutex& operator=(Mutex&&) = delete;
    
    void lock() { mutex_.lock(); }
    void unlock() { mutex_.unlock(); }
    bool try_lock() { return mutex_.try_lock(); }
    
    std::mutex& get() { return mutex_; }
};
```

### Database Connection

```cpp showLineNumbers
class DatabaseConnection {
    void* connection_;  // Opaque handle
    
public:
    explicit DatabaseConnection(const std::string& connString) {
        connection_ = db_connect(connString.c_str());
        if (!connection_) {
            throw std::runtime_error("Connection failed");
        }
    }
    
    ~DatabaseConnection() {
        if (connection_) {
            db_disconnect(connection_);
        }
    }
    
    // Non-copyable: one connection per object
    DatabaseConnection(const DatabaseConnection&) = delete;
    DatabaseConnection& operator=(const DatabaseConnection&) = delete;
    
    // Movable: transfer connection ownership
    DatabaseConnection(DatabaseConnection&& other) noexcept 
        : connection_(other.connection_) {
        other.connection_ = nullptr;
    }
    
    DatabaseConnection& operator=(DatabaseConnection&& other) noexcept {
        if (this != &other) {
            if (connection_) db_disconnect(connection_);
            connection_ = other.connection_;
            other.connection_ = nullptr;
        }
        return *this;
    }
    
    void execute(const std::string& query) {
        db_execute(connection_, query.c_str());
    }
};

// Usage
DatabaseConnection getConnection() {
    return DatabaseConnection("host=localhost;db=mydb");
}

void processData() {
    auto conn = getConnection();  // Move from function return
    conn.execute("SELECT * FROM users");
}
```

## Standard Library Examples

Many standard library types are non-copyable:

```cpp showLineNumbers
#include <memory>
#include <thread>
#include <fstream>
#include <mutex>

// std::unique_ptr - move-only
std::unique_ptr<int> p1 = std::make_unique<int>(42);
std::unique_ptr<int> p2 = p1;            // ❌ Error
std::unique_ptr<int> p3 = std::move(p1); // ✅ OK

// std::thread - move-only
std::thread t1([]{ /* work */ });
std::thread t2 = t1;            // ❌ Error
std::thread t3 = std::move(t1); // ✅ OK

// std::ifstream - move-only (C++11+)
std::ifstream f1("file.txt");
std::ifstream f2 = f1;            // ❌ Error
std::ifstream f3 = std::move(f1); // ✅ OK

// std::mutex - non-copyable, non-movable
std::mutex m1;
std::mutex m2 = m1;            // ❌ Error
std::mutex m3 = std::move(m1); // ❌ Error
```

## Checking Copyability

```cpp showLineNumbers
#include <type_traits>

class Copyable {};

class NonCopyable {
public:
    NonCopyable(const NonCopyable&) = delete;
    NonCopyable& operator=(const NonCopyable&) = delete;
};

class MoveOnly {
public:
    MoveOnly(const MoveOnly&) = delete;
    MoveOnly& operator=(const MoveOnly&) = delete;
    MoveOnly(MoveOnly&&) = default;
    MoveOnly& operator=(MoveOnly&&) = default;
};

static_assert(std::is_copy_constructible_v<Copyable>);
static_assert(!std::is_copy_constructible_v<NonCopyable>);
static_assert(!std::is_copy_constructible_v<MoveOnly>);

static_assert(std::is_move_constructible_v<MoveOnly>);
static_assert(!std::is_move_constructible_v<std::mutex>);
```

## Rule of Five

Non-copyable types often implement the Rule of Five:

```cpp showLineNumbers
class Resource {
    int* data_;
    
public:
    // 1. Constructor
    explicit Resource(int value) : data_(new int(value)) {}
    
    // 2. Destructor
    ~Resource() { delete data_; }
    
    // 3. Copy constructor - DELETED
    Resource(const Resource&) = delete;
    
    // 4. Copy assignment - DELETED
    Resource& operator=(const Resource&) = delete;
    
    // 5. Move constructor
    Resource(Resource&& other) noexcept : data_(other.data_) {
        other.data_ = nullptr;
    }
    
    // 6. Move assignment
    Resource& operator=(Resource&& other) noexcept {
        if (this != &other) {
            delete data_;
            data_ = other.data_;
            other.data_ = nullptr;
        }
        return *this;
    }
};
```

## Design Considerations

### When to Make Non-Copyable

```cpp showLineNumbers
// ✅ SHOULD be non-copyable:
class FileDescriptor;     // System resource
class MutexLock;          // Lock state
class ThreadPool;         // Manages threads
class NetworkSocket;      // Network connection
class DatabaseTransaction; // Transaction state

// ❌ Should probably be copyable:
class Point { int x, y; };          // Simple value
class std::string;                  // Value semantics
class std::vector<int>;             // Container
class Color { int r, g, b, a; };    // Value type
```

**Rule of thumb:** If copying doesn't make semantic sense or would be expensive/dangerous, make it non-copyable.

### Composition with Non-Copyable Members

```cpp showLineNumbers
class Container {
    std::unique_ptr<Data> data_;  // Non-copyable member
    std::mutex mutex_;            // Non-copyable member
    
    // Container automatically becomes non-copyable!
    // Compiler implicitly deletes copy operations
};

// Equivalent to:
class Container {
    std::unique_ptr<Data> data_;
    std::mutex mutex_;
    
public:
    Container(const Container&) = delete;
    Container& operator=(const Container&) = delete;
};
```

If any member is non-copyable, the containing class automatically becomes non-copyable.

## Best Practices

:::success DO
- Delete copy operations explicitly for clarity
- Implement move operations for transferable resources
- Use `= default` for move when applicable
- Make resource-owning types non-copyable
- Document why a type is non-copyable
  :::

:::danger DON'T
- Make types non-copyable "just because"
- Forget to consider move semantics
- Inherit non-copyability in value-like types
- Mix copy and move semantics incorrectly
  :::

## Common Patterns

### Singleton (Non-Copyable)

```cpp showLineNumbers
class Singleton {
    static Singleton* instance_;
    
    // Private constructor
    Singleton() = default;
    
public:
    // Non-copyable
    Singleton(const Singleton&) = delete;
    Singleton& operator=(const Singleton&) = delete;
    
    static Singleton& getInstance() {
        if (!instance_) {
            instance_ = new Singleton();
        }
        return *instance_;
    }
};
```

### Scoped Lock (Non-Copyable, Non-Movable)

```cpp showLineNumbers
class ScopedLock {
    std::mutex& mutex_;
    
public:
    explicit ScopedLock(std::mutex& m) : mutex_(m) {
        mutex_.lock();
    }
    
    ~ScopedLock() {
        mutex_.unlock();
    }
    
    // Non-copyable, non-movable (holds active lock)
    ScopedLock(const ScopedLock&) = delete;
    ScopedLock& operator=(const ScopedLock&) = delete;
    ScopedLock(ScopedLock&&) = delete;
    ScopedLock& operator=(ScopedLock&&) = delete;
};
```

## Summary

Non-copyable idiom prevents object copying by deleting copy operations:

**Basic pattern:**
```cpp
class NonCopyable {
    NonCopyable(const NonCopyable&) = delete;
    NonCopyable& operator=(const NonCopyable&) = delete;
};
```

**Move-only pattern:**
```cpp
class MoveOnly {
    MoveOnly(const MoveOnly&) = delete;
    MoveOnly& operator=(const MoveOnly&) = delete;
    MoveOnly(MoveOnly&&) = default;
    MoveOnly& operator=(MoveOnly&&) = default;
};
```

**Use for:**
- Resource-owning types (files, connections, handles)
- RAII wrappers
- Unique ownership semantics
- Types where copying doesn't make sense

**Remember:**
- Explicitly delete copy operations for clarity
- Consider whether moving makes sense
- Compiler auto-deletes if member is non-copyable
- Standard library has many non-copyable types

```cpp
// Interview answer:
// "Non-copyable idiom prevents copying by deleting copy constructor
// and copy assignment. Common for resource-owning types like file
// handles or mutexes where copying doesn't make sense. Can still
// allow moving for ownership transfer. Use = delete to explicitly
// mark operations as deleted. If any member is non-copyable, the
// class automatically becomes non-copyable. Essential for RAII and
// unique ownership patterns."
```