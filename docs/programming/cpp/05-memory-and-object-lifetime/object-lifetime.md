---
id: object-lifetime
title: Object Lifetime
sidebar_label: Object Lifetime
sidebar_position: 4
tags: [c++, lifetime, construction, destruction, raii]
---

# Object Lifetime

Object lifetime spans from construction to destruction. Understanding lifetime is critical for memory safety, RAII, and avoiding undefined behavior.

:::info Construction to Destruction
An object's lifetime begins when its constructor completes and ends when its destructor begins.
:::

## Lifetime Phases

```mermaid
graph LR
    A[Memory Allocated] --> B[Constructor Called]
    B --> C[Object Lifetime BEGINS]
    C --> D[Object Usage]
    D --> E[Destructor Called]
    E --> F[Object Lifetime ENDS]
    F --> G[Memory Deallocated]
    
    style C fill:#90EE90
    style F fill:#FFB6C1
```

---

## Automatic Objects

```cpp showLineNumbers 
{
    Widget w;  // 1. Memory allocated on stack
               // 2. Constructor called
               // 3. Lifetime begins
    
    w.use();   // Object valid
    
}              // 4. Destructor called
               // 5. Lifetime ends
               // 6. Memory deallocated (stack pointer moves)
```

### Construction Order

```cpp showLineNumbers 
{
    Widget a;
    Widget b;
    Widget c;
}  // Destroyed in reverse: c → b → a
```

**Rule**: Objects destroyed in reverse order of construction.

---

## Dynamic Objects

```cpp showLineNumbers 
Widget* ptr = new Widget();  // 1. Allocate heap memory
                             // 2. Call constructor
                             // 3. Lifetime begins

ptr->use();  // Object valid

delete ptr;  // 4. Call destructor
             // 5. Lifetime ends
             // 6. Free heap memory
             // ptr is now dangling!
```

### Dangling Pointers

```cpp showLineNumbers 
Widget* ptr = new Widget();
delete ptr;  // Object destroyed

ptr->use();  // ❌ Undefined behavior! Lifetime ended
*ptr = Widget();  // ❌ UB
```

---

## Member Object Lifetimes

```cpp showLineNumbers 
class Container {
    Widget member;  // Member object
public:
    Container() {
        // member constructed BEFORE Container body
    }
    
    ~Container() {
        // Container body completes
        // member destroyed AFTER
    }
};
```

**Order**:
1. Base class constructors (if any)
2. Member constructors (declaration order)
3. Container constructor body
4. Container destructor body
5. Member destructors (reverse order)
6. Base class destructors (if any)

```cpp showLineNumbers 
class Example {
    Widget a;
    Widget b;
public:
    Example() : a(), b() {  // a then b constructed
        std::cout << "Example constructed\n";
    }
    
    ~Example() {
        std::cout << "Example destroyed\n";
        // b then a destroyed
    }
};
```

---

## Temporary Object Lifetimes

```cpp showLineNumbers 
std::string getString() { return "hello"; }

// Temporary destroyed at end of statement
getString().size();  // OK: temporary lives for statement

// Reference extends lifetime
const std::string& ref = getString();  // Temporary lives until ref destroyed
std::cout << ref;  // ✅ OK

// ❌ Dangling reference
const std::string& bad() {
    return std::string("temp");  // Temporary destroyed!
}
// Caller gets dangling reference
```

**Rule**: Binding temporary to const reference extends its lifetime to reference's scope.

---

## Lifetime Extension

### Const Reference

```cpp showLineNumbers 
const Widget& ref = Widget();  // Temporary lifetime extended
// Widget lives as long as ref

{
    const Widget& ref = Widget();
    // Use ref
}  // Temporary destroyed here
```

### Not Extended

```cpp showLineNumbers 
Widget&& rref = Widget();  // Lifetime extended (rvalue reference)

void func(const Widget& w);
func(Widget());  // Temporary destroyed after func returns
```

---

## Placement New

Separate allocation from construction:

```cpp showLineNumbers 
alignas(Widget) char buffer[sizeof(Widget)];  // Raw memory

// Construct in pre-allocated memory
Widget* w = new (buffer) Widget();  // Placement new

w->use();  // OK

w->~Widget();  // Explicit destructor call
// Don't delete w! We didn't allocate with new
```

---

## Static Initialization

```cpp showLineNumbers 
Widget global;  // Constructed before main()

int main() {
    static Widget local_static;  // Constructed on first encounter
    
    std::cout << "In main\n";
}

// Destroyed after main() returns:
// 1. local_static
// 2. global
```

**Order fiasco**:

```cpp showLineNumbers 
// file1.cpp
int a = compute_a();

// file2.cpp
int b = compute_b();  // Uses 'a'
// ⚠️ Order undefined! b might initialize before a
```

**Solution**: Function-local static (lazy initialization):

```cpp showLineNumbers 
Widget& getWidget() {
    static Widget w;  // Constructed on first call
    return w;
}
```

---

## Lifetime and RAII

```cpp showLineNumbers 
class File {
    FILE* handle;
public:
    File(const char* name) {
        handle = fopen(name, "r");
        // Lifetime begins
    }
    
    ~File() {
        if (handle) {
            fclose(handle);  // Cleanup before lifetime ends
        }
        // Lifetime ends
    }
};

{
    File f("data.txt");  // Opens file
    // Use file
}  // Closes file automatically
```

**RAII**: Resource Acquisition Is Initialization - resource lifetime tied to object lifetime.

---

## Moved-From Objects

```cpp showLineNumbers 
std::vector<int> v1 = {1, 2, 3};
std::vector<int> v2 = std::move(v1);

// v1 is still alive (lifetime continues)
// But in valid-but-unspecified state

// ✅ Can assign or destroy
v1 = {4, 5, 6};  // OK
// v1 destroyed normally

// ⚠️ Don't use without reassigning
std::cout << v1.size();  // Technically OK but don't rely on value
```

---

## Common Lifetime Bugs

### Use After Free

```cpp showLineNumbers 
Widget* ptr = new Widget();
delete ptr;
ptr->method();  // ❌ Lifetime ended
```

### Dangling Reference

```cpp showLineNumbers 
Widget& getRef() {
    Widget w;
    return w;  // ❌ Returns reference to destroyed object
}
```

### Double Delete

```cpp showLineNumbers 
Widget* ptr = new Widget();
delete ptr;
delete ptr;  // ❌ Lifetime already ended
```

### Accessing Before Construction

```cpp showLineNumbers 
class Bad {
    Widget& ref;
public:
    Bad() : ref(*new Widget()) {
        // Member init happens BEFORE body
    }
    
    ~Bad() {
        // ref is member, can't delete properly!
    }
};
```

---

## Lifetime-Dependent Objects

```cpp showLineNumbers 
class View {
    const std::string& data;  // References another object
public:
    View(const std::string& s) : data(s) {}
    
    void print() { std::cout << data; }
};

void example() {
    std::string s = "hello";
    View v(s);  // v depends on s
    
    v.print();  // ✅ OK
}  // s destroyed AFTER v (reverse construction order)

void broken() {
    View v(std::string("temp"));  // ❌ Temporary destroyed!
    v.print();  // ❌ data dangles
}
```

---

## Perfect Forwarding and Lifetime

```cpp showLineNumbers 
template<typename T>
void wrapper(T&& arg) {
    process(std::forward<T>(arg));  // Preserves value category
}

std::string s = "hello";
wrapper(s);                  // Forwards lvalue
wrapper(std::string("temp")); // Forwards rvalue
```

---

## Summary

**Lifetime = Construction → Destruction**:
```cpp showLineNumbers 
{
    Widget w;  // Construction (lifetime begins)
    w.use();   // Usage (lifetime active)
}              // Destruction (lifetime ends)
```

**Key rules**:
- Destroyed in reverse construction order
- Temporaries destroyed at statement end (unless bound to const&)
- Members constructed before body, destroyed after
- Static objects: program lifetime
- Dynamic objects: manual lifetime (new/delete)

**Lifetime bugs**:
```cpp showLineNumbers 
delete ptr; ptr->use();  // ❌ Use after free
return local;            // ❌ Return local by reference
delete p; delete p;      // ❌ Double delete
```

**Best practices**:
- Use RAII for resource management
- Prefer automatic (stack) objects
- Use smart pointers for dynamic objects
- Avoid returning references to locals
- Don't access moved-from objects without reassigning

Understanding object lifetime is fundamental to writing correct C++ code and avoiding undefined behavior.