---
id: pimpl
title: Pimpl (Pointer to Implementation)
sidebar_label: Pimpl
sidebar_position: 2
tags: [cpp, pimpl, idioms, design-patterns, compilation, encapsulation]
---

# Pimpl (Pointer to Implementation)

**Pimpl** (Pointer to Implementation) separates a class's interface from its implementation by moving private members into a separate implementation class. This reduces compilation dependencies and provides better encapsulation.

## The Problem

Without Pimpl, changing private members forces recompilation of all files that include the header, even though they can't access those members.
```cpp
// widget.h - WITHOUT Pimpl
#include "detail.h"        // Implementation dependency
#include "helper.h"        // Leaked to users
#include <vector>

class Widget {
public:
    void doSomething();
    
private:
    Detail detail_;         // Exposes Detail to users
    Helper helper_;         // Exposes Helper to users
    std::vector<int> data_; // Forces vector recompilation
};

// Any change to private members requires recompiling all users!
```

## The Solution

Pimpl hides implementation details behind an opaque pointer, making the interface header independent of implementation changes.
```cpp
// widget.h - WITH Pimpl
#include <memory>

class Widget {
public:
    Widget();
    ~Widget();
    
    // Rule of Five needed with Pimpl
    Widget(Widget&&) noexcept;
    Widget& operator=(Widget&&) noexcept;
    Widget(const Widget&);
    Widget& operator=(const Widget&);
    
    void doSomething();
    
private:
    struct Impl;  // Forward declaration
    std::unique_ptr<Impl> pImpl_;
};

// widget.cpp
#include "widget.h"
#include "detail.h"   // Only needed in .cpp
#include "helper.h"   // Only needed in .cpp
#include <vector>

struct Widget::Impl {
    Detail detail;
    Helper helper;
    std::vector<int> data;
};

Widget::Widget() : pImpl_(std::make_unique<Impl>()) {}
Widget::~Widget() = default;
Widget::Widget(Widget&&) noexcept = default;
Widget& Widget::operator=(Widget&&) noexcept = default;

Widget::Widget(const Widget& other)
    : pImpl_(std::make_unique<Impl>(*other.pImpl_)) {}

Widget& Widget::operator=(const Widget& other) {
    *pImpl_ = *other.pImpl_;
    return *this;
}

void Widget::doSomething() {
    pImpl_->helper.help();
    pImpl_->data.push_back(42);
}
```

:::info
The destructor must be defined in the `.cpp` file where `Impl` is complete, otherwise `unique_ptr` can't delete it.
:::

## Benefits

Pimpl provides several compile-time and design advantages.

### Faster Compilation

Only the implementation file needs recompilation when private members change, not all users of the class.
```cpp
// Changing Widget::Impl only requires recompiling widget.cpp
// All files that include widget.h don't need recompilation
```

### Better Encapsulation

Implementation details are completely hidden from users - they can't even see the types used internally.
```cpp
// widget.h - users can't see Detail, Helper, or vector
class Widget {
    struct Impl;
    std::unique_ptr<Impl> pImpl_;
};
```

### ABI Stability

The class layout doesn't change when private members change, maintaining binary compatibility across library versions.
```cpp
// Adding members to Impl doesn't break ABI
// Widget's memory layout stays the same
```

### Reduced Header Dependencies

Implementation headers are only included in `.cpp` files, reducing transitive includes for users.
```cpp
// widget.h - minimal includes
#include <memory>  // Only this needed

// widget.cpp - heavy includes hidden
#include "complex_implementation.h"
#include "third_party_library.h"
```

## Implementation Patterns

Different use cases require different Pimpl implementations.

### Basic Pimpl (Move-Only)

Simplest form - no copying, only moving, reduces boilerplate code.
```cpp
// widget.h
class Widget {
public:
    Widget();
    ~Widget();
    Widget(Widget&&) noexcept;
    Widget& operator=(Widget&&) noexcept;
    
private:
    struct Impl;
    std::unique_ptr<Impl> pImpl_;
};

// widget.cpp
struct Widget::Impl {
    // Implementation members
};

Widget::Widget() : pImpl_(std::make_unique<Impl>()) {}
Widget::~Widget() = default;
Widget::Widget(Widget&&) noexcept = default;
Widget& Widget::operator=(Widget&&) noexcept = default;
```

### Copyable Pimpl

Enables copying by implementing copy constructor and assignment with deep copy.
```cpp
// widget.h
class Widget {
public:
    Widget();
    ~Widget();
    
    Widget(const Widget& other);
    Widget& operator=(const Widget& other);
    
    Widget(Widget&&) noexcept;
    Widget& operator=(Widget&&) noexcept;
    
private:
    struct Impl;
    std::unique_ptr<Impl> pImpl_;
};

// widget.cpp
Widget::Widget(const Widget& other)
    : pImpl_(std::make_unique<Impl>(*other.pImpl_)) {}

Widget& Widget::operator=(const Widget& other) {
    if (this != &other) {
        *pImpl_ = *other.pImpl_;
    }
    return *this;
}
```

### Shared Pimpl

Multiple objects can share the same implementation using reference counting.
```cpp
// widget.h
class Widget {
public:
    Widget();
    // Compiler-generated copy/move work correctly
    
private:
    struct Impl;
    std::shared_ptr<Impl> pImpl_;
};

// widget.cpp
Widget::Widget() : pImpl_(std::make_shared<Impl>()) {}
```

### Fast Pimpl (Inline Storage)

Avoids heap allocation by using inline storage, trading header changes for performance.
```cpp
// widget.h
class Widget {
public:
    Widget();
    ~Widget();
    
private:
    static constexpr size_t STORAGE_SIZE = 64;
    alignas(std::max_align_t) std::byte storage_[STORAGE_SIZE];
    
    struct Impl;
    Impl* pImpl_;
};

// widget.cpp
struct Widget::Impl {
    // Must fit in STORAGE_SIZE
};

Widget::Widget() {
    static_assert(sizeof(Impl) <= STORAGE_SIZE);
    pImpl_ = new(storage_) Impl();
}

Widget::~Widget() {
    pImpl_->~Impl();
}
```

## Practical Examples

### Example 1: Network Client

Network implementation details are hidden, allowing protocol changes without recompiling users.
```cpp
// client.h
#include <memory>
#include <string>

class NetworkClient {
public:
    NetworkClient(const std::string& host, int port);
    ~NetworkClient();
    
    NetworkClient(NetworkClient&&) noexcept;
    NetworkClient& operator=(NetworkClient&&) noexcept;
    
    bool connect();
    void send(const std::string& data);
    std::string receive();
    
private:
    struct Impl;
    std::unique_ptr<Impl> pImpl_;
};

// client.cpp
#include "client.h"
#include <sys/socket.h>  // Not leaked to users
#include <netinet/in.h>  // Not leaked to users
#include <vector>

struct NetworkClient::Impl {
    int sockfd;
    sockaddr_in serverAddr;
    std::vector<char> buffer;
    
    Impl(const std::string& host, int port);
    ~Impl();
};

NetworkClient::NetworkClient(const std::string& host, int port)
    : pImpl_(std::make_unique<Impl>(host, port)) {}

NetworkClient::~NetworkClient() = default;
NetworkClient::NetworkClient(NetworkClient&&) noexcept = default;
NetworkClient& NetworkClient::operator=(NetworkClient&&) noexcept = default;

bool NetworkClient::connect() {
    return ::connect(pImpl_->sockfd, 
                    (sockaddr*)&pImpl_->serverAddr,
                    sizeof(pImpl_->serverAddr)) == 0;
}
```

### Example 2: Database Connection

Database-specific headers are isolated, preventing pollution of user code with database types.
```cpp
// database.h
#include <memory>
#include <string>
#include <vector>

class Database {
public:
    Database(const std::string& connectionString);
    ~Database();
    
    bool connect();
    void execute(const std::string& query);
    std::vector<std::string> fetchResults();
    
private:
    struct Impl;
    std::unique_ptr<Impl> pImpl_;
};

// database.cpp
#include "database.h"
#include <libpq-fe.h>  // PostgreSQL - not leaked

struct Database::Impl {
    PGconn* conn;
    PGresult* result;
    std::string connString;
    
    Impl(const std::string& cs) : conn(nullptr), result(nullptr), connString(cs) {}
    
    ~Impl() {
        if (result) PQclear(result);
        if (conn) PQfinish(conn);
    }
};

Database::Database(const std::string& connectionString)
    : pImpl_(std::make_unique<Impl>(connectionString)) {}

Database::~Database() = default;

bool Database::connect() {
    pImpl_->conn = PQconnectdb(pImpl_->connString.c_str());
    return PQstatus(pImpl_->conn) == CONNECTION_OK;
}
```

### Example 3: GUI Widget

Platform-specific GUI code is hidden, enabling cross-platform interfaces without exposing platform details.
```cpp
// button.h
#include <memory>
#include <string>
#include <functional>

class Button {
public:
    Button(const std::string& text);
    ~Button();
    
    void setText(const std::string& text);
    void setOnClick(std::function<void()> callback);
    void show();
    
private:
    struct Impl;
    std::unique_ptr<Impl> pImpl_;
};

// button_windows.cpp (Windows platform)
#include "button.h"
#include <windows.h>  // Not leaked to users

struct Button::Impl {
    HWND hwnd;
    std::function<void()> onClick;
    
    Impl(const std::string& text) {
        hwnd = CreateWindow("BUTTON", text.c_str(), 
                           WS_VISIBLE | WS_CHILD,
                           10, 10, 100, 30, NULL, NULL, NULL, NULL);
    }
    
    ~Impl() {
        DestroyWindow(hwnd);
    }
};

// button_linux.cpp (Linux platform)
#include "button.h"
#include <gtk/gtk.h>  // Not leaked to users

struct Button::Impl {
    GtkWidget* widget;
    std::function<void()> onClick;
    
    Impl(const std::string& text) {
        widget = gtk_button_new_with_label(text.c_str());
    }
    
    ~Impl() {
        gtk_widget_destroy(widget);
    }
};
```

## Performance Considerations

Pimpl has trade-offs between compilation time and runtime performance.

### Extra Indirection

Every access through pImpl requires pointer dereference, adding slight overhead.
```cpp
// One extra indirection
void Widget::doSomething() {
    pImpl_->data.push_back(42);  // pImpl_ -> data -> push_back
}

// vs direct access
void Widget::doSomething() {
    data_.push_back(42);  // data_ -> push_back
}
```

### Heap Allocation

Creating a Pimpl object requires heap allocation, which is slower than stack allocation.
```cpp
// Heap allocation
Widget w;  // Allocates Impl on heap

// Can be mitigated with inline storage
// or object pools
```

### Cache Locality

Implementation data is not contiguous with the object, potentially affecting cache performance.
```cpp
// Poor cache locality
std::vector<Widget> widgets(1000);
for (auto& w : widgets) {
    w.doSomething();  // Each access jumps to different heap location
}
```

## When to Use Pimpl

Pimpl is most beneficial in specific scenarios, not everywhere.

:::success
**Use Pimpl When:**
- Class has complex private implementation
- Reducing compilation dependencies is important
- Providing stable ABI for library interface
- Hiding platform-specific implementation
- Private members change frequently
  :::

:::warning
**Avoid Pimpl When:**
- Performance is critical (hot path code)
- Class is header-only template
- Implementation is simple (few dependencies)
- Creating many short-lived objects
- Overhead outweighs compilation benefits
  :::

## Best Practices

Follow these guidelines for effective Pimpl usage.

:::success
**DO:**
- Define destructor in `.cpp` file
- Use `unique_ptr` for exclusive ownership
- Forward declare Impl in header
- Include Impl definition only in `.cpp`
- Implement Rule of Five if needed
  :::

:::danger
**DON'T:**
- Define destructor inline in header
- Use Pimpl for every class
- Expose Impl pointer to users
- Forget to implement copy operations
- Mix Pimpl and inline implementations
  :::

## Pimpl Variants

Different pointer types provide different semantics and performance characteristics.

| Variant | Pointer Type   | Semantics           | Copy Behavior          |
|---------|----------------|---------------------|------------------------|
| Unique  | `unique_ptr`   | Exclusive ownership | Move-only or deep copy |
| Shared  | `shared_ptr`   | Shared ownership    | Shallow copy           |
| Fast    | Inline storage | No allocation       | Complex copy           |

## Related Topics

- **[Smart Pointers](../06-pointers-references-and-smart-pointers/unique-ptr.md)** - Ownership management
- **[Rule of Five](../07-classes-and-oop/rule-of-zero-three-five.md)** - Special members
- **[Forward Declarations](../01-toolchain-and-build/headers-and-includes.md)** - Compilation dependencies