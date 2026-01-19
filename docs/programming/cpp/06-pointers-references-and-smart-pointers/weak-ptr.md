---
id: weak-ptr
title: std::weak_ptr
sidebar_label: weak_ptr
sidebar_position: 7
tags: [c++, smart-pointers, weak-ptr, reference-counting, cpp11]
---

# std::weak_ptr

`std::weak_ptr` is a smart pointer that holds a non-owning ("weak") reference to an object managed by `shared_ptr`. It must be converted to a `shared_ptr` to access the object, and this conversion fails if the object has been deleted.

:::info Non-Owning Observer
`weak_ptr` observes an object without keeping it alive. It breaks circular reference cycles and enables checking if an object still exists before accessing it.
:::

## Basic Concept

A weak_ptr doesn't increase the reference count of the object it observes. The object can be deleted even if weak_ptrs still exist.

```cpp
#include <memory>

std::weak_ptr<int> weak;

{
    auto shared = std::make_shared<int>(42);
    weak = shared;  // weak observes the int
    
    std::cout << shared.use_count();  // 1 (weak_ptr doesn't count)
    std::cout << weak.use_count();    // 1 (reports shared count)
}  // shared destroyed, int deleted

// weak now refers to deleted object
if (weak.expired()) {
    std::cout << "Object is gone\n";  // This executes
}
```

The weak_ptr watches the shared_ptr but doesn't participate in ownership. When all shared_ptrs are destroyed, the object is deleted even if weak_ptrs remain. The weak_ptr then becomes "expired."

## Creating weak_ptr

You create weak_ptrs from shared_ptrs, never from raw pointers or unique_ptrs.

```cpp
auto shared = std::make_shared<int>(42);

// Create weak_ptr from shared_ptr
std::weak_ptr<int> weak1 = shared;
std::weak_ptr<int> weak2(shared);
auto weak3 = std::weak_ptr<int>(shared);

// Copy weak_ptr
std::weak_ptr<int> weak4 = weak1;

std::cout << shared.use_count();  // 1 (weak_ptrs don't increase count)
```

All these weak_ptrs observe the same object but don't own it. The shared_ptr's reference count remains 1 because weak ownership doesn't count toward keeping the object alive.

## Checking Validity

Before accessing an object through weak_ptr, you must check if it still exists.

```cpp
std::weak_ptr<int> weak;

{
    auto shared = std::make_shared<int>(42);
    weak = shared;
    
    // Check if object still exists
    if (!weak.expired()) {
        std::cout << "Object exists\n";
    }
}

// Object deleted
if (weak.expired()) {
    std::cout << "Object is gone\n";
}

// Alternatively, check use_count
if (weak.use_count() == 0) {
    std::cout << "No owners left\n";
}
```

The `expired()` method checks if the object has been deleted (equivalent to `use_count() == 0`). You must check before attempting to access the object because the shared_ptrs might have been destroyed.

## Locking: Converting to shared_ptr

To access the object, convert the weak_ptr to shared_ptr using `lock()`. This fails safely if the object has been deleted.

```cpp
std::weak_ptr<int> weak;

{
    auto shared = std::make_shared<int>(42);
    weak = shared;
    
    // Lock creates temporary shared_ptr
    if (auto locked = weak.lock()) {
        std::cout << *locked;  // 42
        // locked keeps object alive in this scope
    } else {
        std::cout << "Object gone\n";
    }
}

// Try to lock after object deleted
if (auto locked = weak.lock()) {
    // Won't execute - lock() returns empty shared_ptr
} else {
    std::cout << "Lock failed\n";  // This executes
}
```

`lock()` returns a shared_ptr that either owns the object (if it still exists) or is empty (if object was deleted). This is the safe way to access the object - it's atomic, preventing the object from being deleted between checking and accessing.

### Why lock() Instead of Direct Access

Directly checking and then accessing would have a race condition in multithreaded code.

```cpp
// ❌ Race condition (don't do this)
if (!weak.expired()) {
    // Another thread might destroy last shared_ptr here!
    auto shared = weak.lock();  // Might return empty
}

// ✅ Safe: atomic check-and-lock
if (auto shared = weak.lock()) {
    // Guaranteed to have valid shared_ptr here
    *shared = 100;
}
```

`lock()` atomically checks if the object exists and creates a shared_ptr if it does. This prevents the object from being deleted after checking but before accessing.

## Breaking Circular References

The primary use case for weak_ptr is breaking circular references that would prevent shared_ptr from deleting objects.

```cpp
class Node {
public:
    std::string data;
    std::shared_ptr<Node> next;     // Strong reference forward
    std::weak_ptr<Node> prev;       // Weak reference back (breaks cycle)
    
    Node(std::string d) : data(d) {}
    ~Node() { std::cout << "~Node(" << data << ")\n"; }
};

auto node1 = std::make_shared<Node>("first");
auto node2 = std::make_shared<Node>("second");
auto node3 = std::make_shared<Node>("third");

// Build doubly-linked list
node1->next = node2;
node2->prev = node1;  // Weak - doesn't create cycle

node2->next = node3;
node3->prev = node2;  // Weak - doesn't create cycle

// All destructors called correctly when nodes go out of scope!
```

Without weak_ptr, the `prev` pointers would be shared_ptrs, creating reference cycles where each node keeps the previous one alive, and nothing ever gets deleted. weak_ptr allows traversal in both directions without ownership cycles.

### Parent-Child Relationships

Parent-child relationships typically use shared_ptr from parent to child and weak_ptr from child to parent.

```cpp
class Child;

class Parent {
public:
    std::vector<std::shared_ptr<Child>> children;  // Owns children
    ~Parent() { std::cout << "~Parent\n"; }
};

class Child {
public:
    std::weak_ptr<Parent> parent;  // Observes parent, doesn't own
    ~Child() { std::cout << "~Child\n"; }
    
    void notifyParent() {
        if (auto p = parent.lock()) {
            std::cout << "Parent exists\n";
            // Use p safely
        } else {
            std::cout << "Parent is gone\n";
        }
    }
};

{
    auto parent = std::make_shared<Parent>();
    auto child = std::make_shared<Child>();
    
    parent->children.push_back(child);
    child->parent = parent;
    
    child->notifyParent();  // "Parent exists"
}  // ~Parent, ~Child (correct order)
```

The parent owns the children (strong references), and children observe the parent (weak reference). This prevents cycles: when the parent is destroyed, it releases its children, and the children can detect that their parent is gone.

## Observer Pattern

weak_ptr is ideal for implementing observers that should not keep observed objects alive.

```cpp
class Subject {
    std::vector<std::weak_ptr<Observer>> observers;
    
public:
    void attach(std::shared_ptr<Observer> obs) {
        observers.push_back(obs);  // Weak reference
    }
    
    void notify() {
        // Remove expired observers
        observers.erase(
            std::remove_if(observers.begin(), observers.end(),
                [](auto& weak) { return weak.expired(); }),
            observers.end()
        );
        
        // Notify remaining observers
        for (auto& weak : observers) {
            if (auto obs = weak.lock()) {
                obs->update();
            }
        }
    }
};
```

Observers can be destroyed without notifying the subject. The subject doesn't keep observers alive - they're held weakly. When notifying, expired observers are skipped or removed automatically.

## Caching

weak_ptr enables caches that don't prevent cached objects from being deleted.

```cpp
class ResourceManager {
    std::map<std::string, std::weak_ptr<Resource>> cache;
    
public:
    std::shared_ptr<Resource> getResource(const std::string& name) {
        // Check cache
        auto it = cache.find(name);
        if (it != cache.end()) {
            if (auto resource = it->second.lock()) {
                std::cout << "Cache hit\n";
                return resource;  // Return cached resource
            }
        }
        
        // Create new resource
        std::cout << "Cache miss\n";
        auto resource = std::make_shared<Resource>(name);
        cache[name] = resource;  // Store weak reference
        return resource;
    }
};
```

The cache stores weak_ptrs, so it doesn't prevent resources from being deleted when no longer needed. If a resource is still in use elsewhere (has active shared_ptrs), the cache can return it. Otherwise, the cache entry is expired and a new resource is created.

## weak_ptr Operations

weak_ptr provides several operations for observation and conversion.

```cpp
auto shared = std::make_shared<int>(42);
std::weak_ptr<int> weak = shared;

// Check if expired
bool gone = weak.expired();  // false

// Get owner count
long count = weak.use_count();  // 1

// Lock to shared_ptr
if (auto locked = weak.lock()) {
    std::cout << *locked;
}

// Reset (stop observing)
weak.reset();
// weak is now empty

// Check if empty
if (weak.expired()) {
    std::cout << "Empty or expired\n";
}
```

## Thread Safety

Like shared_ptr, weak_ptr's control block operations are thread-safe, but the observed object isn't automatically protected.

```cpp
std::shared_ptr<int> shared = std::make_shared<int>(42);
std::weak_ptr<int> weak = shared;

void thread1() {
    auto locked = weak.lock();  // ✅ Thread-safe lock
    if (locked) {
        *locked = 100;  // ❌ Data race if thread2 also modifies
    }
}

void thread2() {
    auto locked = weak.lock();  // ✅ Thread-safe lock
    if (locked) {
        *locked = 200;  // ❌ Data race with thread1
    }
}
```

Creating and destroying weak_ptrs, copying them, and calling `lock()` are all thread-safe. However, if multiple threads lock and access the object simultaneously, you need additional synchronization.

## enable_shared_from_this

When you need to create a shared_ptr or weak_ptr to `this` inside a member function, inherit from `enable_shared_from_this`.

```cpp
class Widget : public std::enable_shared_from_this<Widget> {
public:
    std::weak_ptr<Widget> getWeakPtr() {
        return weak_from_this();  // ✅ Safe
    }
    
    std::shared_ptr<Widget> getSharedPtr() {
        return shared_from_this();  // ✅ Safe
    }
    
    void registerCallback() {
        auto self = weak_from_this();
        callbacks.push_back([self]() {
            if (auto locked = self.lock()) {
                locked->doWork();
            }
        });
    }
};

auto widget = std::make_shared<Widget>();
auto weak = widget->getWeakPtr();  // ✅ Correctly shares control block
```

Never create a shared_ptr directly from `this` - it creates a second control block, causing double-delete. `enable_shared_from_this` provides the correct way to get shared ownership of `this`.

### Common Mistake: Creating from this

```cpp
class Bad {
public:
    std::shared_ptr<Bad> getPtr() {
        return std::shared_ptr<Bad>(this);  // ❌ Second control block!
    }
};

auto ptr1 = std::make_shared<Bad>();  // Control block 1
auto ptr2 = ptr1->getPtr();            // Control block 2 (disaster!)
// Object will be double-deleted!
```

## Performance

weak_ptr has minimal overhead - it's essentially a pointer plus a pointer to the control block.

```cpp
sizeof(std::weak_ptr<int>) == sizeof(std::shared_ptr<int>)
// Both: 16 bytes (2 pointers)

// No atomic operations when checking/locking
// Only when creating/destroying weak_ptr
```

Checking `expired()` and calling `lock()` are fast operations. The atomic overhead only occurs when creating, copying, or destroying weak_ptrs, not when using them.

:::warning Common Mistakes

**Accessing Without lock()**: Cannot dereference weak_ptr directly - must lock first.

**Assuming Object Exists**: Always check `lock()` result - object might be deleted.

**Race Conditions**: Don't check `expired()` separately - use `lock()` for atomic check-and-access.

**Creating from this**: Use `enable_shared_from_this`, never `shared_ptr(this)`.

**Forgetting to Break Cycles**: Shared_ptr cycles cause leaks - identify and use weak_ptr to break them.
:::

## Summary

`std::weak_ptr` is a non-owning observer of objects managed by `shared_ptr`, not increasing reference count and allowing objects to be deleted. It must be converted to `shared_ptr` using `lock()` to access the object, returning empty shared_ptr if object was deleted. Check validity with `expired()` or by testing `lock()` result. The primary use case is breaking circular references that would prevent shared_ptr from deleting objects - use weak_ptr for backward references in linked structures and child-to-parent references. weak_ptr enables the observer pattern where observers shouldn't keep subjects alive, and caching where cache doesn't prevent deletion. Always use `lock()` for atomic check-and-access, never check `expired()` separately in multithreaded code. Inherit from `enable_shared_from_this<T>` to safely create shared/weak pointers to `this` in member functions. weak_ptr control block operations are thread-safe but the observed object needs separate synchronization. Never create multiple shared_ptrs from the same raw pointer - use `shared_from_this()` or `weak_from_this()` instead. Performance overhead is minimal - same size as shared_ptr with fast `lock()` operations. Use weak_ptr when you need to observe without owning, break ownership cycles, or implement caches and observers. It solves the "how do I point to something that might go away" problem elegantly and safely.

:::success Essential Concepts

**Non-Owning**: Observes without keeping object alive - doesn't increase reference count.

**Breaking Cycles**: Essential for preventing shared_ptr circular reference memory leaks.

**lock() Required**: Convert to shared_ptr before accessing - fails safely if object deleted.

**Atomic Check**: `lock()` atomically checks and accesses - prevents race conditions.

**Observer Pattern**: Perfect for observers that shouldn't keep subjects alive.

**enable_shared_from_this**: Use this to create weak_ptr to `this` safely.

**Parent-Child**: Strong reference down (parent→child), weak reference up (child→parent).
:::