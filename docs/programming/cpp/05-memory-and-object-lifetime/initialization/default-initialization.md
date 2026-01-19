---
id: default-initialization
title: Default Initialization
sidebar_label: Default Initialization
sidebar_position: 1
tags: [c++, initialization, default-init, undefined-behavior]
---

# Default Initialization

Default initialization occurs when an object is created without an explicit initializer. The behavior depends on the object's type and storage duration, and for fundamental types, it often leaves the value indeterminate.

:::warning Undefined Values
Default initialization of fundamental types (int, double, pointers) in automatic storage leaves them with indeterminate values. Reading these values before assignment causes undefined behavior.
:::

## Fundamental Types

When you declare a fundamental type variable without providing an initial value, the compiler performs default initialization. For automatic (local) variables, this means the memory is not cleared and contains whatever garbage values were previously there.

```cpp
void function() {
    int x;        // Default-initialized to indeterminate value
    double d;     // Indeterminate value
    int* ptr;     // Indeterminate pointer (dangerous!)
    
    std::cout << x;    // ❌ Undefined behavior - reading indeterminate value
    std::cout << d;    // ❌ Undefined behavior
    *ptr = 42;         // ❌ Undefined behavior - pointer points nowhere
}
```

The reason for this behavior is performance: zeroing memory on every variable declaration would add unnecessary overhead when the programmer intends to immediately assign a value. However, this creates a dangerous situation where forgetting to initialize can lead to unpredictable program behavior.

### Static Storage Duration

For variables with static storage duration (globals and static locals), default initialization actually does provide a predictable value: zero. This is part of the C++ standard's guarantee that all static storage is zero-initialized before any other initialization occurs.

```cpp
int global;              // Default-initialized to 0
static int file_static;  // Default-initialized to 0

void function() {
    static int func_static;  // Default-initialized to 0 (on first call)
    
    std::cout << global;       // ✅ Safe: 0
    std::cout << file_static;  // ✅ Safe: 0
    std::cout << func_static;  // ✅ Safe: 0
}
```

This difference between automatic and static storage is a source of subtle bugs. Code that works correctly with global variables might fail when those variables are converted to local variables, because the implicit zero-initialization is lost.

## Class Types with Default Constructors

When a class defines a default constructor (one that takes no arguments), default initialization calls that constructor. This provides a way to ensure objects are always in a valid state, even when no explicit initializer is provided.

```cpp
class Widget {
    int value;
public:
    Widget() : value(42) {  // Default constructor
        std::cout << "Widget constructed\n";
    }
};

void function() {
    Widget w;  // Default-initialized: calls Widget()
    // w.value is guaranteed to be 42
}
```

The default constructor is called automatically, ensuring the object is properly initialized. This is a key advantage of classes over fundamental types: they can enforce initialization invariants. Even if the programmer forgets to provide an initializer, the class can ensure it's in a valid state.

### Implicit Default Constructor

If a class doesn't declare any constructors at all, the compiler generates an implicit default constructor. However, this generated constructor performs member-wise default initialization, which means fundamental type members are left uninitialized.

```cpp
class Point {
    int x, y;  // No constructor defined
};

Point p;  // Default-initialized
// p.x and p.y have indeterminate values! ❌

// Better: Provide a constructor
class SafePoint {
    int x, y;
public:
    SafePoint() : x(0), y(0) {}  // Explicitly initialize
};

SafePoint sp;  // sp.x and sp.y are guaranteed to be 0 ✅
```

The compiler-generated default constructor does what you tell it to do, but for fundamental types, that means doing nothing. This is why it's considered good practice to always provide initializers for member variables, either in the constructor's initializer list or with in-class initializers.

### Deleted Default Constructor

Some classes explicitly delete their default constructor to prevent default initialization. This is useful when an object only makes sense with certain parameters.

```cpp
class File {
    FILE* handle;
public:
    File() = delete;  // No default construction allowed
    File(const char* filename) {
        handle = fopen(filename, "r");
    }
};

// File f;  // ❌ Error: default constructor deleted
File f("data.txt");  // ✅ Must provide filename
```

By deleting the default constructor, the class designer forces users to provide necessary information (like a filename) at construction time. This prevents the existence of "invalid" objects that haven't been properly configured.

## Arrays

Arrays of fundamental types follow the same rules as scalar variables. Local arrays are left with indeterminate values, while static arrays are zero-initialized.

```cpp
void function() {
    int arr[10];  // Each element has indeterminate value ❌
    
    for (int i = 0; i < 10; ++i) {
        std::cout << arr[i];  // ❌ Undefined behavior
    }
}

static int global_arr[10];  // All elements initialized to 0 ✅

void safe_function() {
    std::cout << global_arr[0];  // ✅ Safe: 0
}
```

This behavior extends to multi-dimensional arrays as well. The important principle is that automatic storage gets no implicit initialization, while static storage is always zero-initialized. Understanding this distinction is crucial for writing correct C++ code.

### Class Type Arrays

When an array contains objects of a class type, each element is default-initialized by calling the class's default constructor. This ensures that all array elements are properly constructed.

```cpp
class Widget {
public:
    Widget() { std::cout << "Constructed\n"; }
};

Widget arr[3];  // Calls Widget() three times
// Each array element is properly initialized
```

The default constructor is called for each array element in order, from index 0 to n-1. This guarantees that every object in the array exists in a valid state, assuming the default constructor properly initializes all members.

## Member Variables

Class member variables are default-initialized when the constructor doesn't explicitly initialize them. For fundamental types in members, this means they have indeterminate values unless the class is stored in static storage.

```cpp
class Bad {
    int value;  // Not initialized in constructor
public:
    Bad() {}  // Default constructor doesn't initialize value
    
    int getValue() { return value; }  // ❌ Returns indeterminate value
};

class Good {
    int value;
public:
    Good() : value(0) {}  // Explicitly initialize in initializer list
    
    int getValue() { return value; }  // ✅ Returns 0
};

void test() {
    Bad b;
    std::cout << b.getValue();  // ❌ Undefined behavior
    
    Good g;
    std::cout << g.getValue();  // ✅ Safe: 0
}
```

Always initialize member variables in the constructor's initializer list or use in-class initializers (C++11) to avoid this problem. The compiler won't warn you about uninitialized members in many cases, so this is a common source of bugs.

### In-Class Initializers (C++11)

Modern C++ allows you to provide default values directly in the class definition. These initializers are used when the constructor doesn't explicitly initialize the member.

```cpp
class Widget {
    int value = 42;      // In-class initializer
    std::string name = "default";
    
public:
    Widget() {}  // value and name get default values
    Widget(int v) : value(v) {}  // name gets default, value from parameter
};
```

In-class initializers provide a fallback value that's used unless the constructor overrides it. This is safer than leaving members uninitialized and clearer than having to repeat the same initialization in every constructor.

## Summary

Default initialization behavior depends critically on both the type being initialized and where the object is stored. For fundamental types in automatic storage, default initialization is effectively no initialization at all, leaving dangerous indeterminate values. For class types, default initialization calls the default constructor, which should establish a valid object state. Static storage duration objects are always zero-initialized before any other initialization occurs. Understanding these distinctions is essential for writing correct and safe C++ code, and it's generally best practice to always provide explicit initializers rather than relying on default initialization for fundamental types.