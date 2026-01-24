---
id: type-erasure
title: Type Erasure
sidebar_label: Type Erasure
sidebar_position: 6
tags: [cpp, type-erasure, templates, polymorphism, design-patterns]
---

# Type Erasure

Type erasure hides the concrete type behind a common interface, allowing different types to be treated uniformly without inheritance. Combines the flexibility of runtime polymorphism with the performance benefits of templates.

:::info Polymorphism Without Inheritance
Type erasure lets unrelated types work through a common interface without requiring them to inherit from a base class. The canonical example is `std::function` which can store any callable.
:::

## The Problem

```cpp showLineNumbers
// Need to store different callables
void callback1() { std::cout << "Callback 1\n"; }

struct Functor {
    void operator()() { std::cout << "Functor\n"; }
};

// How to store both?
// ❌ Can't use common base class - they're unrelated types
// ❌ Templates require knowing exact type at compile-time
// ✅ Type erasure!
```

## Basic Type Erasure Pattern

```cpp showLineNumbers
class Function {
    // Internal interface
    struct Concept {
        virtual void call() = 0;
        virtual ~Concept() = default;
    };
    
    // Wrapper for specific types
    template<typename F>
    struct Model : Concept {
        F func_;
        
        Model(F func) : func_(std::move(func)) {}
        
        void call() override {
            func_();
        }
    };
    
    std::unique_ptr<Concept> impl_;
    
public:
    // Constructor - type erased here
    template<typename F>
    Function(F func) 
        : impl_(std::make_unique<Model<F>>(std::move(func))) {}
    
    // Common interface
    void operator()() {
        impl_->call();
    }
};

// Usage
void func() { std::cout << "Free function\n"; }

struct Functor {
    void operator()() { std::cout << "Functor\n"; }
};

int main() {
    Function f1 = func;              // Stores function pointer
    Function f2 = Functor();         // Stores functor
    Function f3 = []{ std::cout << "Lambda\n"; };  // Stores lambda
    
    f1();  // "Free function"
    f2();  // "Functor"
    f3();  // "Lambda"
    
    // All have same type: Function
    // Original types erased!
}
```

**How it works:**
1. Template constructor accepts any type `F`
2. Wraps `F` in `Model<F>` which implements `Concept`
3. Stores `Model<F>` as pointer to `Concept` (type erased)
4. Calls forward through `Concept` interface

## std::function Implementation

Simplified version of the standard library:

```cpp showLineNumbers
template<typename>
class Function;  // Primary template (undefined)

// Partial specialization for function signatures
template<typename R, typename... Args>
class Function<R(Args...)> {
    struct Concept {
        virtual R invoke(Args... args) = 0;
        virtual ~Concept() = default;
        virtual Concept* clone() const = 0;
    };
    
    template<typename F>
    struct Model : Concept {
        F func_;
        
        Model(F f) : func_(std::move(f)) {}
        
        R invoke(Args... args) override {
            return func_(std::forward<Args>(args)...);
        }
        
        Concept* clone() const override {
            return new Model(func_);
        }
    };
    
    Concept* impl_ = nullptr;
    
public:
    Function() = default;
    
    template<typename F>
    Function(F func) 
        : impl_(new Model<F>(std::move(func))) {}
    
    ~Function() {
        delete impl_;
    }
    
    // Copy
    Function(const Function& other)
        : impl_(other.impl_ ? other.impl_->clone() : nullptr) {}
    
    Function& operator=(const Function& other) {
        if (this != &other) {
            delete impl_;
            impl_ = other.impl_ ? other.impl_->clone() : nullptr;
        }
        return *this;
    }
    
    // Move
    Function(Function&& other) noexcept
        : impl_(other.impl_) {
        other.impl_ = nullptr;
    }
    
    Function& operator=(Function&& other) noexcept {
        if (this != &other) {
            delete impl_;
            impl_ = other.impl_;
            other.impl_ = nullptr;
        }
        return *this;
    }
    
    // Invoke
    R operator()(Args... args) {
        if (!impl_) throw std::bad_function_call();
        return impl_->invoke(std::forward<Args>(args)...);
    }
    
    explicit operator bool() const {
        return impl_ != nullptr;
    }
};

// Usage
Function<int(int, int)> add = [](int a, int b) { return a + b; };
Function<void()> print = []{ std::cout << "Hello\n"; };

int result = add(3, 4);  // 7
print();                 // "Hello"
```

## Drawable Example

Type-erased drawing interface:

```cpp showLineNumbers
class Drawable {
    struct Concept {
        virtual void draw() const = 0;
        virtual ~Concept() = default;
        virtual Concept* clone() const = 0;
    };
    
    template<typename T>
    struct Model : Concept {
        T object_;
        
        Model(T obj) : object_(std::move(obj)) {}
        
        void draw() const override {
            object_.draw();  // Calls T::draw()
        }
        
        Concept* clone() const override {
            return new Model(object_);
        }
    };
    
    std::unique_ptr<Concept> impl_;
    
public:
    template<typename T>
    Drawable(T obj) 
        : impl_(std::make_unique<Model<T>>(std::move(obj))) {}
    
    // Copy
    Drawable(const Drawable& other)
        : impl_(other.impl_->clone()) {}
    
    Drawable& operator=(const Drawable& other) {
        impl_.reset(other.impl_->clone());
        return *this;
    }
    
    // Move
    Drawable(Drawable&&) = default;
    Drawable& operator=(Drawable&&) = default;
    
    void draw() const {
        impl_->draw();
    }
};

// Usage - no inheritance needed!
struct Circle {
    void draw() const { std::cout << "Circle\n"; }
};

struct Square {
    void draw() const { std::cout << "Square\n"; }
};

int main() {
    std::vector<Drawable> shapes;
    shapes.push_back(Circle());
    shapes.push_back(Square());
    
    for (const auto& shape : shapes) {
        shape.draw();
    }
    // Output:
    // Circle
    // Square
}
```

No common base class needed for `Circle` and `Square`!

## Small Buffer Optimization (SBO)

Avoid heap allocation for small types:

```cpp showLineNumbers
template<typename R, typename... Args>
class Function {
    static constexpr size_t BUFFER_SIZE = 32;
    
    struct Concept {
        virtual R invoke(Args...) = 0;
        virtual ~Concept() = default;
        virtual void clone_to(void* buffer) const = 0;
        virtual void move_to(void* buffer) = 0;
    };
    
    template<typename F>
    struct Model : Concept {
        F func_;
        
        Model(F f) : func_(std::move(f)) {}
        
        R invoke(Args... args) override {
            return func_(std::forward<Args>(args)...);
        }
        
        void clone_to(void* buffer) const override {
            new (buffer) Model(func_);
        }
        
        void move_to(void* buffer) override {
            new (buffer) Model(std::move(func_));
        }
    };
    
    alignas(std::max_align_t) char buffer_[BUFFER_SIZE];
    Concept* impl_ = nullptr;
    bool is_heap_ = false;
    
public:
    template<typename F>
    Function(F func) {
        using ModelType = Model<F>;
        
        if constexpr (sizeof(ModelType) <= BUFFER_SIZE) {
            // Small: use buffer
            impl_ = new (buffer_) ModelType(std::move(func));
            is_heap_ = false;
        } else {
            // Large: use heap
            impl_ = new ModelType(std::move(func));
            is_heap_ = true;
        }
    }
    
    ~Function() {
        if (impl_) {
            if (is_heap_) {
                delete impl_;
            } else {
                impl_->~Concept();
            }
        }
    }
    
    R operator()(Args... args) {
        return impl_->invoke(std::forward<Args>(args)...);
    }
};
```

Small callables stored in buffer (no allocation), large ones use heap.

## std::any Implementation

Type-erased container for any value:

```cpp showLineNumbers
class Any {
    struct Concept {
        virtual ~Concept() = default;
        virtual Concept* clone() const = 0;
        virtual const std::type_info& type() const = 0;
    };
    
    template<typename T>
    struct Model : Concept {
        T value_;
        
        Model(T value) : value_(std::move(value)) {}
        
        Concept* clone() const override {
            return new Model(value_);
        }
        
        const std::type_info& type() const override {
            return typeid(T);
        }
    };
    
    std::unique_ptr<Concept> impl_;
    
public:
    Any() = default;
    
    template<typename T>
    Any(T value) 
        : impl_(std::make_unique<Model<T>>(std::move(value))) {}
    
    // Copy/move
    Any(const Any& other) 
        : impl_(other.impl_ ? other.impl_->clone() : nullptr) {}
    
    Any(Any&&) = default;
    Any& operator=(const Any&);
    Any& operator=(Any&&) = default;
    
    // Type checking
    const std::type_info& type() const {
        return impl_ ? impl_->type() : typeid(void);
    }
    
    // Access
    template<typename T>
    T* cast() {
        if (type() == typeid(T)) {
            return &static_cast<Model<T>*>(impl_.get())->value_;
        }
        return nullptr;
    }
    
    template<typename T>
    const T* cast() const {
        if (type() == typeid(T)) {
            return &static_cast<const Model<T>*>(impl_.get())->value_;
        }
        return nullptr;
    }
};

// Usage
Any a = 42;
Any b = std::string("hello");
Any c = 3.14;

int* pi = a.cast<int>();
if (pi) std::cout << *pi << "\n";  // 42

std::string* ps = b.cast<std::string>();
if (ps) std::cout << *ps << "\n";  // "hello"
```

## Iterator Type Erasure

Abstract over different iterator types:

```cpp showLineNumbers
template<typename T>
class AnyIterator {
    struct Concept {
        virtual void advance() = 0;
        virtual T& dereference() = 0;
        virtual bool equal(const Concept* other) const = 0;
        virtual Concept* clone() const = 0;
        virtual ~Concept() = default;
    };
    
    template<typename Iter>
    struct Model : Concept {
        Iter iter_;
        
        Model(Iter it) : iter_(it) {}
        
        void advance() override {
            ++iter_;
        }
        
        T& dereference() override {
            return *iter_;
        }
        
        bool equal(const Concept* other) const override {
            auto* p = dynamic_cast<const Model*>(other);
            return p && iter_ == p->iter_;
        }
        
        Concept* clone() const override {
            return new Model(iter_);
        }
    };
    
    std::unique_ptr<Concept> impl_;
    
public:
    template<typename Iter>
    AnyIterator(Iter it) 
        : impl_(std::make_unique<Model<Iter>>(it)) {}
    
    AnyIterator(const AnyIterator& other)
        : impl_(other.impl_->clone()) {}
    
    AnyIterator& operator++() {
        impl_->advance();
        return *this;
    }
    
    T& operator*() {
        return impl_->dereference();
    }
    
    bool operator==(const AnyIterator& other) const {
        return impl_->equal(other.impl_.get());
    }
};

// Usage with different container types
std::vector<int> vec = {1, 2, 3};
std::list<int> lst = {4, 5, 6};

AnyIterator<int> it1 = vec.begin();
AnyIterator<int> it2 = lst.begin();

// Both have same type, but wrap different iterators
```

## Performance Considerations

```cpp showLineNumbers
// Virtual dispatch overhead
struct WithTypeErasure {
    std::function<int(int)> func;  // Virtual dispatch
    
    int call(int x) {
        return func(x);  // ~5-10 ns overhead
    }
};

// Template - no overhead
template<typename F>
struct WithTemplate {
    F func;
    
    int call(int x) {
        return func(x);  // Inlined, ~1 ns
    }
};

// Trade-off: Flexibility vs Performance
// Type erasure: flexible, small overhead
// Templates: fast, compile-time only
```

## Comparison with Alternatives

| Approach | Type Info | Runtime Flexibility | Performance | Code Size |
|----------|-----------|---------------------|-------------|-----------|
| **Type Erasure** | Erased | High | ~5-10ns overhead | Small |
| **Virtual Functions** | Known | High | ~5-10ns overhead | Small |
| **Templates** | Known | None | Zero overhead | Large (bloat) |
| **Variants** | Known (closed set) | Medium | Zero overhead | Medium |

## Best Practices

:::success DO
- Use for unknown types at compile-time
- Implement clone for copy support
- Consider small buffer optimization
- Use for plugin systems
- Leverage for callback storage
  :::

:::danger DON'T
- Use when templates suffice
- Ignore performance implications
- Forget to handle copy/move properly
- Use excessively (compile-time is often better)
  :::

## Advanced: External Polymorphism

Type erasure enables external polymorphism pattern:

```cpp showLineNumbers
// External interface
struct DrawingDevice {
    virtual void draw_circle(int x, int y, int r) = 0;
    virtual void draw_rect(int x, int y, int w, int h) = 0;
    virtual ~DrawingDevice() = default;
};

// Type-erased wrapper
template<typename Device>
struct DeviceModel : DrawingDevice {
    Device device_;
    
    DeviceModel(Device d) : device_(std::move(d)) {}
    
    void draw_circle(int x, int y, int r) override {
        device_.draw_circle(x, y, r);
    }
    
    void draw_rect(int x, int y, int w, int h) override {
        device_.draw_rect(x, y, w, h);
    }
};

// Client code
class Shape {
    std::unique_ptr<DrawingDevice> device_;
    
public:
    template<typename Device>
    void set_device(Device device) {
        device_ = std::make_unique<DeviceModel<Device>>(
            std::move(device));
    }
    
    virtual void draw(DrawingDevice& device) = 0;
};
```

## Summary

Type erasure hides concrete types behind a common interface:

**Pattern:**
```cpp
class TypeErased {
    struct Concept {
        virtual void operation() = 0;
        virtual ~Concept() = default;
    };
    
    template<typename T>
    struct Model : Concept {
        T obj_;
        void operation() override { obj_.operation(); }
    };
    
    std::unique_ptr<Concept> impl_;
    
public:
    template<typename T>
    TypeErased(T obj) : impl_(new Model<T>(std::move(obj))) {}
    
    void operation() { impl_->operation(); }
};
```

**Use cases:**
- Callback storage (`std::function`)
- Heterogeneous containers
- Plugin systems
- Runtime polymorphism without inheritance
- `std::any` for arbitrary value storage

**Trade-offs:**
- Adds virtual dispatch overhead
- Enables runtime flexibility
- No template bloat
- Slightly more complex than templates

```cpp
// Interview answer:
// "Type erasure uses templates + virtual functions to hide concrete
// types behind a common interface. Template constructor accepts any
// type T, wraps it in a Model<T> implementing an abstract Concept,
// stores as pointer to Concept. This erases the type while preserving
// behavior. Used in std::function and std::any. Enables runtime
// polymorphism without requiring inheritance. Trade-off: virtual
// dispatch overhead for flexibility. Great for callbacks and
// heterogeneous collections of unrelated types."
```