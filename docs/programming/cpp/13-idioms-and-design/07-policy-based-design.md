---
id: policy-based-design
title: Policy-Based Design
sidebar_label: Policy-Based Design
sidebar_position: 7
tags: [cpp, policy-based-design, templates, design-patterns, generic-programming]
---

# Policy-Based Design

Policy-based design decomposes complex behaviors into independent policy classes combined through templates. Each policy defines one aspect of behavior, and policies are mixed together to create flexible, reusable components.

:::info Compile-Time Strategy Pattern
Think of policies as compile-time strategy patterns. Instead of runtime polymorphism with virtual functions, policies provide compile-time composition of behaviors with zero runtime overhead.
:::

## The Problem

```cpp showLineNumbers
// Traditional approach: inheritance explosion
class SmartPtr { /* ... */ };
class SmartPtrWithRefCounting : public SmartPtr { /* ... */ };
class SmartPtrWithCopyCounting : public SmartPtr { /* ... */ };
class SmartPtrWithThreadSafe : public SmartPtr { /* ... */ };
class SmartPtrWithRefCountingAndThreadSafe : public SmartPtr { /* ... */ };
// Combinatorial explosion of classes!

// Policy-based approach: compose behaviors
template<typename T, 
         typename OwnershipPolicy,
         typename CheckingPolicy,
         typename StoragePolicy>
class SmartPtr { /* ... */ };
// Policies combine independently!
```

## Basic Policy Pattern

```cpp showLineNumbers
// Policy 1: Storage policy
template<typename T>
struct DefaultStorage {
    using PointerType = T*;
    using ReferenceType = T&;
    
protected:
    PointerType ptr_ = nullptr;
    
    PointerType get() const { return ptr_; }
    void set(PointerType p) { ptr_ = p; }
};

// Policy 2: Checking policy
struct NoChecking {
    template<typename T>
    static void check(T*) { }  // No-op
};

struct EnforceNotNull {
    template<typename T>
    static void check(T* ptr) {
        if (!ptr) throw std::runtime_error("Null pointer!");
    }
};

// Smart pointer using policies
template<typename T,
         template<typename> class CheckingPolicy = NoChecking,
         template<typename> class StoragePolicy = DefaultStorage>
class SmartPtr : private StoragePolicy<T> {
    using Storage = StoragePolicy<T>;
    using Checker = CheckingPolicy<T>;
    
public:
    explicit SmartPtr(T* ptr = nullptr) {
        Storage::set(ptr);
    }
    
    T& operator*() const {
        Checker::check(Storage::get());
        return *Storage::get();
    }
    
    T* operator->() const {
        Checker::check(Storage::get());
        return Storage::get();
    }
};

// Usage
SmartPtr<int> p1(new int(42));  // No checking
SmartPtr<int, EnforceNotNull> p2(new int(42));  // With null check

*p1;  // OK
*p2;  // Throws if null
```

## Real-World Example: Thread-Safe Container

```cpp showLineNumbers
// Locking policies
struct NoLock {
    void lock() { }
    void unlock() { }
};

struct MutexLock {
    std::mutex mutex_;
    
    void lock() { mutex_.lock(); }
    void unlock() { mutex_.unlock(); }
};

struct SpinLock {
    std::atomic_flag flag_ = ATOMIC_FLAG_INIT;
    
    void lock() {
        while (flag_.test_and_set(std::memory_order_acquire));
    }
    
    void unlock() {
        flag_.clear(std::memory_order_release);
    }
};

// Container with locking policy
template<typename T, typename LockingPolicy = NoLock>
class ThreadSafeContainer : private LockingPolicy {
    std::vector<T> data_;
    
public:
    void push(T value) {
        this->lock();
        data_.push_back(std::move(value));
        this->unlock();
    }
    
    T pop() {
        this->lock();
        T value = std::move(data_.back());
        data_.pop_back();
        this->unlock();
        return value;
    }
    
    size_t size() const {
        this->lock();
        size_t result = data_.size();
        this->unlock();
        return result;
    }
};

// Usage
ThreadSafeContainer<int, NoLock> singleThreaded;  // No overhead
ThreadSafeContainer<int, MutexLock> multiThreaded;  // With mutex
ThreadSafeContainer<int, SpinLock> lowContention;  // With spinlock
```

Each variant compiled optimally - no virtual function overhead!

## Multiple Policies Example

```cpp showLineNumbers
// Allocation policies
template<typename T>
struct NewAllocator {
    static T* allocate() {
        return new T();
    }
    
    static void deallocate(T* ptr) {
        delete ptr;
    }
};

template<typename T>
struct MallocAllocator {
    static T* allocate() {
        void* p = std::malloc(sizeof(T));
        return new (p) T();  // Placement new
    }
    
    static void deallocate(T* ptr) {
        ptr->~T();
        std::free(ptr);
    }
};

// Ownership policies
template<typename T>
struct RefCounted {
    int* count_;
    
    RefCounted() : count_(new int(1)) {}
    
    void acquire(T*) {
        ++(*count_);
    }
    
    bool release(T*) {
        return --(*count_) == 0;
    }
    
    ~RefCounted() {
        if (count_ && *count_ == 0) {
            delete count_;
        }
    }
};

template<typename T>
struct Unique {
    void acquire(T*) { }
    
    bool release(T*) {
        return true;  // Always delete
    }
};

// Smart pointer with multiple policies
template<typename T,
         template<typename> class OwnershipPolicy,
         template<typename> class AllocationPolicy>
class CustomPtr : private OwnershipPolicy<T> {
    using Ownership = OwnershipPolicy<T>;
    using Allocator = AllocationPolicy<T>;
    
    T* ptr_;
    
public:
    CustomPtr() : ptr_(Allocator::allocate()) {
        Ownership::acquire(ptr_);
    }
    
    ~CustomPtr() {
        if (Ownership::release(ptr_)) {
            Allocator::deallocate(ptr_);
        }
    }
    
    T& operator*() { return *ptr_; }
    T* operator->() { return ptr_; }
};

// Usage - mix and match policies
using UniqueNew = CustomPtr<Widget, Unique, NewAllocator>;
using SharedNew = CustomPtr<Widget, RefCounted, NewAllocator>;
using UniqueMalloc = CustomPtr<Widget, Unique, MallocAllocator>;
```

## Policy Classes vs Policy Templates

### Policy Classes

```cpp showLineNumbers
// Policy is a complete class
struct UpperCase {
    static std::string transform(const std::string& s) {
        std::string result = s;
        std::transform(result.begin(), result.end(), 
                      result.begin(), ::toupper);
        return result;
    }
};

template<typename TransformPolicy>
class StringProcessor {
public:
    std::string process(const std::string& input) {
        return TransformPolicy::transform(input);
    }
};

StringProcessor<UpperCase> processor;
```

### Policy Templates

```cpp showLineNumbers
// Policy is a template
template<typename T>
struct DefaultDeleter {
    void operator()(T* ptr) const {
        delete ptr;
    }
};

template<typename T, template<typename> class DeleterPolicy>
class SmartPtr {
    T* ptr_;
    DeleterPolicy<T> deleter_;
    
public:
    ~SmartPtr() {
        deleter_(ptr_);
    }
};
```

## Policy Inheritance vs Composition

### Private Inheritance (Empty Base Optimization)

```cpp showLineNumbers
template<typename LockingPolicy>
class Container : private LockingPolicy {  // EBO applies
    std::vector<int> data_;
    
public:
    void push(int value) {
        this->lock();  // From LockingPolicy
        data_.push_back(value);
        this->unlock();
    }
};

// If LockingPolicy is NoLock (empty class), no storage overhead
```

### Composition

```cpp showLineNumbers
template<typename LockingPolicy>
class Container {
    std::vector<int> data_;
    LockingPolicy lock_;  // Member variable
    
public:
    void push(int value) {
        lock_.lock();
        data_.push_back(value);
        lock_.unlock();
    }
};
```

Private inheritance preferred for empty policies (saves space via EBO).

## Destructors in Policies

```cpp showLineNumbers
// Non-virtual destructor (OK for policies used as base classes)
template<typename T>
struct RefCounted {
    int* count_;
    
    RefCounted() : count_(new int(1)) {}
    
    // No virtual destructor - policy never deleted polymorphically
    ~RefCounted() {
        if (count_ && --(*count_) == 0) {
            delete count_;
        }
    }
};

template<typename T, typename OwnershipPolicy>
class SmartPtr : private OwnershipPolicy {  // Private inheritance
    T* ptr_;
    
public:
    ~SmartPtr() {
        // OwnershipPolicy::~OwnershipPolicy() called automatically
        // No polymorphic deletion, so no virtual destructor needed
    }
};
```

## Policy Constraints (C++20 Concepts)

```cpp showLineNumbers
#include <concepts>

// Define requirements for a locking policy
template<typename T>
concept LockingPolicy = requires(T lock) {
    { lock.lock() } -> std::same_as<void>;
    { lock.unlock() } -> std::same_as<void>;
};

// Define requirements for allocator policy
template<typename T, typename U>
concept AllocatorPolicy = requires(T alloc, U* ptr) {
    { T::allocate() } -> std::same_as<U*>;
    { T::deallocate(ptr) } -> std::same_as<void>;
};

// Container with constrained policy
template<typename T, LockingPolicy Lock = NoLock>
class Container : private Lock {
    std::vector<T> data_;
    
public:
    void push(T value) {
        this->lock();
        data_.push_back(std::move(value));
        this->unlock();
    }
};

// Compile error if policy doesn't satisfy concept
Container<int, int> bad;  // Error: int doesn't satisfy LockingPolicy
```

## Logger Example

```cpp showLineNumbers
// Output policies
struct ConsoleOutput {
    void write(const std::string& msg) {
        std::cout << msg << std::endl;
    }
};

struct FileOutput {
    std::ofstream file_;
    
    FileOutput() : file_("log.txt", std::ios::app) {}
    
    void write(const std::string& msg) {
        file_ << msg << std::endl;
    }
};

// Timestamp policies
struct NoTimestamp {
    std::string format(const std::string& msg) {
        return msg;
    }
};

struct ISOTimestamp {
    std::string format(const std::string& msg) {
        auto now = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        std::stringstream ss;
        ss << std::put_time(std::localtime(&time), "[%Y-%m-%d %H:%M:%S] ");
        ss << msg;
        return ss.str();
    }
};

// Logger combining policies
template<typename OutputPolicy, typename TimestampPolicy>
class Logger : private OutputPolicy, private TimestampPolicy {
public:
    void log(const std::string& message) {
        std::string formatted = TimestampPolicy::format(message);
        OutputPolicy::write(formatted);
    }
};

// Usage
Logger<ConsoleOutput, NoTimestamp> simpleLogger;
simpleLogger.log("Simple message");
// Output: Simple message

Logger<FileOutput, ISOTimestamp> fileLogger;
fileLogger.log("Timestamped message");
// Output to file: [2024-02-28 10:30:45] Timestamped message
```

## Policy-Based Smart Pointer

Complete example combining multiple policies:

```cpp showLineNumbers
// Storage policy
template<typename T>
struct DefaultStorage {
    using PointerType = T*;
    using ReferenceType = T&;
    
protected:
    PointerType ptr_;
    
    DefaultStorage(PointerType p = nullptr) : ptr_(p) {}
    PointerType get() const { return ptr_; }
    void set(PointerType p) { ptr_ = p; }
};

// Checking policy
template<typename T>
struct AssertCheck {
    static void check(T* ptr) {
        assert(ptr != nullptr && "Null pointer dereference");
    }
};

template<typename T>
struct NoCheck {
    static void check(T*) { }
};

// Ownership policy
template<typename T>
struct DeepCopy {
    static T* clone(const T* ptr) {
        return ptr ? new T(*ptr) : nullptr;
    }
};

template<typename T>
struct NoCopy {
    static T* clone(const T*) = delete;
};

// Complete smart pointer
template<typename T,
         template<typename> class StoragePolicy = DefaultStorage,
         template<typename> class CheckingPolicy = NoCheck,
         template<typename> class OwnershipPolicy = DeepCopy>
class SmartPointer : private StoragePolicy<T> {
    using Storage = StoragePolicy<T>;
    using Checker = CheckingPolicy<T>;
    using Owner = OwnershipPolicy<T>;
    
public:
    explicit SmartPointer(T* p = nullptr) {
        Storage::set(p);
    }
    
    ~SmartPointer() {
        delete Storage::get();
    }
    
    // Copy (uses OwnershipPolicy)
    SmartPointer(const SmartPointer& other) {
        Storage::set(Owner::clone(other.get()));
    }
    
    // Dereference (uses CheckingPolicy)
    T& operator*() const {
        Checker::check(Storage::get());
        return *Storage::get();
    }
    
    T* operator->() const {
        Checker::check(Storage::get());
        return Storage::get();
    }
    
    T* get() const {
        return Storage::get();
    }
};

// Usage with different policy combinations
SmartPointer<int> ptr1(new int(42));  // Default: no check, deep copy
SmartPointer<int, DefaultStorage, AssertCheck> ptr2(new int(42));  // With assert
```

## Host Class Pattern

Policy classes can be templated on the host:

```cpp showLineNumbers
template<typename Host>
struct ThreadSafePolicy {
    void operation() {
        mutex_.lock();
        static_cast<Host*>(this)->do_operation();
        mutex_.unlock();
    }
    
private:
    std::mutex mutex_;
};

template<typename ThreadingPolicy>
class MyClass : private ThreadingPolicy<MyClass<ThreadingPolicy>> {
    using Base = ThreadingPolicy<MyClass>;
    
public:
    void public_operation() {
        Base::operation();
    }
    
private:
    friend ThreadingPolicy<MyClass>;
    
    void do_operation() {
        // Actual work
    }
};
```

## Performance Comparison

```cpp showLineNumbers
// Virtual functions (runtime polymorphism)
class Base {
public:
    virtual void operation() = 0;
    virtual ~Base() = default;
};

class Derived : public Base {
public:
    void operation() override { /* ... */ }
};

void use_virtual(Base* ptr) {
    ptr->operation();  // Virtual dispatch: ~5-10ns overhead
}

// Policy-based (compile-time polymorphism)
template<typename Policy>
class PolicyBased : private Policy {
public:
    void operation() {
        Policy::operation();  // Inlined: 0ns overhead
    }
};

template<typename T>
void use_policy(PolicyBased<T>& obj) {
    obj.operation();  // Direct call, fully optimized
}

// Policy-based is faster but less flexible
```

## Best Practices

:::success DO
- Use policies for orthogonal concerns
- Name policies clearly (e.g., `LockingPolicy`, `StoragePolicy`)
- Use private inheritance with EBO for empty policies
- Document policy requirements clearly
- Use concepts (C++20) to constrain policies
  :::

:::danger DON'T
- Over-engineer with too many policies
- Mix policies with runtime polymorphism unnecessarily
- Forget to document policy interfaces
- Make policies stateful without clear reason
- Use policies for tightly coupled behaviors
  :::

## When to Use Policy-Based Design

**Use when:**
- Behaviors are orthogonal and independent
- Need compile-time polymorphism
- Performance critical (no virtual overhead)
- Want to avoid inheritance explosion
- Building generic libraries

**Don't use when:**
- Need runtime type switching
- Behaviors are tightly coupled
- Simple inheritance suffices
- Compile time doesn't matter

## Summary

Policy-based design decomposes behaviors into independent policy classes:

**Pattern:**
```cpp
template<typename Policy1, typename Policy2>
class Host : private Policy1, private Policy2 {
    void operation() {
        Policy1::do_something();
        Policy2::do_something_else();
    }
};
```

**Benefits:**
- Compile-time composition
- Zero runtime overhead
- Highly configurable
- Avoids inheritance explosion
- Excellent performance

**Trade-offs:**
- More complex than inheritance
- Compile-time only (no runtime flexibility)
- Can lead to long template names
- Increased compile time

**Use cases:**
- Smart pointers (ownership, checking, storage)
- Containers (locking, allocation)
- Loggers (output, formatting)
- Generic algorithms

```cpp
// Interview answer:
// "Policy-based design uses template parameters to compose
// behaviors from independent policy classes. Each policy defines
// one aspect of behavior, and the host class combines them.
// Provides compile-time polymorphism with zero overhead - policies
// are inlined and optimized away. Better than inheritance for
// orthogonal concerns because it avoids combinatorial explosion
// and enables better performance. Used in STL (allocators,
// iterators) and smart pointers. Trade-off: less flexible than
// runtime polymorphism but much faster."
```