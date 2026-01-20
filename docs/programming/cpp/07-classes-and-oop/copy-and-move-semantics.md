---
id: copy-and-move
title: Copy and Move Semantics
sidebar_label: Copy & Move
sidebar_position: 5
tags: [c++, copy, move, semantics, performance]
---

# Copy and Move Semantics

Copy creates a duplicate of an object. Move transfers ownership of resources from one object to another. Understanding when each happens is crucial for performance and correctness.

:::info Copy vs Move
**Copy** = Duplicate the data (can be expensive)  
**Move** = Transfer ownership (cheap, just pointer swap)
:::

## Copy Operations

Copying creates an independent duplicate with its own resources.

```cpp showLineNumbers 
std::vector<int> v1 = {1, 2, 3, 4, 5};
std::vector<int> v2 = v1;  // Copy: v2 gets its own array

v2[0] = 100;  // Doesn't affect v1
std::cout << v1[0];  // Still 1
```

**When copying happens:**
- Initialization: `Type obj2 = obj1;`
- Assignment: `obj2 = obj1;`
- Pass by value: `func(obj);`
- Return by value: `return obj;`

## Move Operations (C++11)

Moving transfers resources without copying the actual data.

```cpp showLineNumbers 
std::vector<int> v1 = {1, 2, 3, 4, 5};
std::vector<int> v2 = std::move(v1);  // Move: v2 steals v1's array

// v1 is now empty (moved-from state)
// v2 has the data (no copying happened!)
```

**When moving happens:**
- `std::move()`: Explicit move
- Return temporary: `return std::vector<int>{1,2,3};`
- Pass rvalue: `func(getTempObject());`

## Performance Difference

Moving is dramatically faster for resource-owning types:

```cpp showLineNumbers 
class BigData {
    int* data;
    size_t size;
    
public:
    // Copy: allocate + copy all elements (SLOW)
    BigData(const BigData& other) {
        size = other.size;
        data = new int[size];
        std::copy(other.data, other.data + size, data);
    }
    
    // Move: just steal pointer (FAST)
    BigData(BigData&& other) noexcept {
        data = other.data;      // Steal pointer
        size = other.size;
        other.data = nullptr;   // Leave valid
        other.size = 0;
    }
};
```

**Benchmark example:**
```cpp showLineNumbers 
std::vector<std::string> vec(1000000);  // 1 million strings

auto copy = vec;              // ~50ms (copies all strings)
auto moved = std::move(vec);  // ~0.001ms (just pointer swap)
```

## Value Categories

Understanding lvalues and rvalues helps predict when moves happen:

```cpp showLineNumbers 
int x = 10;           // x is lvalue (has name, address)
int y = x + 5;        // x+5 is rvalue (temporary)

std::string s1 = "hello";
std::string s2 = s1;           // Copy (s1 is lvalue)
std::string s3 = std::move(s1); // Move (std::move makes lvalue into rvalue)
std::string s4 = s1 + s2;      // Move (s1+s2 is temporary rvalue)
```

**Simple rule:**
- Has a name? It's an lvalue → copy
- Temporary or `std::move()`? It's an rvalue → move

## Implementing Move

Move operations should be `noexcept` and leave source in valid state:

```cpp showLineNumbers 
class Resource {
    int* data;
    
public:
    // Move constructor
    Resource(Resource&& other) noexcept {
        data = other.data;      // Steal
        other.data = nullptr;   // Nullify source
    }
    
    // Move assignment
    Resource& operator=(Resource&& other) noexcept {
        if (this != &other) {
            delete data;           // Free our old resource
            data = other.data;     // Steal other's resource  
            other.data = nullptr;  // Nullify source
        }
        return *this;
    }
    
    ~Resource() { delete data; }
};
```

**Critical points:**
- Mark `noexcept` (enables optimizations)
- Check self-assignment in move assignment
- Leave source valid but unspecified (usually empty/null)

## Copy Elision and RVO

Compilers optimize away unnecessary copies/moves:

```cpp showLineNumbers 
Widget createWidget() {
    Widget w(42);
    return w;  // No copy! No move! (RVO)
}

Widget w = createWidget();  // Direct construction in w's memory
```

**Return Value Optimization (RVO):** Compiler constructs return value directly in caller's memory. Named Return Value Optimization (NRVO) does same for named variables.

**Guaranteed since C++17** for temporaries, optional for named variables.

## When to Use std::move

```cpp showLineNumbers 
std::vector<int> v1 = {1, 2, 3};

// ✅ Good: Moving from local about to die
std::vector<int> v2 = std::move(v1);
// Don't use v1 after this!

// ✅ Good: Moving into function
processData(std::move(v2));

// ❌ Bad: Don't move and then use
auto v3 = std::move(v1);
v1.push_back(4);  // ⚠️ Undefined behavior!

// ❌ Bad: Don't move from const
const std::vector<int> cv = {1,2,3};
auto v4 = std::move(cv);  // Copies anyway! const can't be moved-from
```

## Perfect Forwarding

Templates can forward arguments preserving their value category:

```cpp showLineNumbers 
template<typename T>
void wrapper(T&& arg) {
    // std::forward preserves lvalue/rvalue-ness
    actualFunction(std::forward<T>(arg));
}

Widget w;
wrapper(w);              // Forwards as lvalue (copy)
wrapper(Widget());       // Forwards as rvalue (move)
wrapper(std::move(w));   // Forwards as rvalue (move)
```

:::success Quick Reference

**Copy = Duplicate**, Move = Transfer  
**lvalue = named**, rvalue = temporary  
**std::move = cast to rvalue** (doesn't actually move!)  
**noexcept on moves** = essential for performance  
**Don't use after move** = left in valid-but-empty state  
**RVO = free optimization** = no copy, no move  
**const can't move** = always copies
:::