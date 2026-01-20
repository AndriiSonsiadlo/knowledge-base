---
id: references
title: References
sidebar_label: References
sidebar_position: 2
tags: [c++, references, aliases, pointers]
---

# References

A reference is an alias for an existing object - another name for the same memory location. Unlike pointers, references cannot be null, must be initialized when declared, and cannot be reseated to refer to a different object.

:::info Reference = Alias
A reference is NOT a new variable - it's just another name for an existing object. Modifying the reference modifies the original object directly.
:::

## Basic References

References create an alternate name for an existing variable. All operations on the reference affect the original variable because they're the same thing.

```cpp showLineNumbers 
int x = 42;
int& ref = x;  // ref is an alias for x

ref = 100;            // Modifies x
std::cout << x;       // 100
std::cout << ref;     // 100
std::cout << &ref;    // Same address as &x

x = 200;              // Modifying x
std::cout << ref;     // 200 (ref sees the change)
```

The reference `ref` doesn't create new storage - it's just another way to access `x`. Taking the address of a reference gives you the address of the original object. This is fundamentally different from pointers, which are separate variables storing addresses.

### References Must Be Initialized

Unlike pointers, references cannot exist without referring to something. They must be bound to an object at declaration.

```cpp showLineNumbers 
int& bad_ref;  // ❌ Error: references must be initialized

int x = 42;
int& good_ref = x;  // ✅ OK: bound to x

int* ptr;  // ✅ OK: pointers can be uninitialized (though dangerous)
```

This requirement eliminates null reference bugs. There's no way to create a reference that doesn't refer to a valid object, making references safer than pointers in this respect. The compiler enforces the initialization requirement.

## References Cannot Be Reseated

Once initialized, a reference always refers to the same object. Assignment through a reference modifies the referred-to object, it doesn't change what the reference refers to.

```cpp showLineNumbers 
int x = 10;
int y = 20;
int& ref = x;  // ref refers to x

ref = y;       // ❌ Does NOT make ref refer to y!
               // ✅ Copies y's value into x

std::cout << x;    // 20 (x was modified)
std::cout << ref;  // 20 (still refers to x)
std::cout << y;    // 20 (y unchanged)
```

This is a critical difference from pointers. With pointers, `ptr = &y` changes where the pointer points. With references, `ref = y` is value assignment to the referred-to object. You cannot make a reference "point" elsewhere after initialization.

### References vs Pointers

The choice between references and pointers depends on whether you need nullable, reassignable behavior or guaranteed valid aliases.

```cpp showLineNumbers 
int x = 42;

// Pointer (nullable, reassignable)
int* ptr = &x;
ptr = nullptr;  // ✅ Can be null
*ptr = 10;      // ❌ Must check first!

int y = 100;
ptr = &y;       // ✅ Can point elsewhere

// Reference (never null, not reassignable)
int& ref = x;
// ref = nullptr;  // ❌ Error: can't "nullify" a reference
ref = 10;       // ✅ Always safe (guaranteed valid)

// ref = y;     // ✅ Copies y into x (doesn't reseat)
```

Use references when you need a guaranteed-valid alias (function parameters, return values). Use pointers when you need nullable or reassignable behavior (optional values, polymorphism, data structures).

## Function Parameters

References enable efficient pass-by-reference semantics, allowing functions to modify caller's variables without copying.

```cpp showLineNumbers 
void increment(int& x) {  // Pass by reference
    x++;                  // Modifies caller's variable
}

int value = 10;
increment(value);
std::cout << value;  // 11 (modified)

// Compare to pass-by-value
void bad_increment(int x) {  // Copy
    x++;  // Modifies copy, not original
}

bad_increment(value);
std::cout << value;  // Still 11 (unchanged by bad_increment)
```

Pass-by-reference avoids copying large objects and allows functions to modify arguments. This is more efficient than pass-by-value for large types like containers and enables functions to return multiple values through reference parameters.

### const References

Const references allow reading but prevent modification, making them ideal for passing large objects efficiently without allowing changes.

```cpp showLineNumbers 
void print(const std::string& s) {  // No copy, can't modify
    std::cout << s;
    // s[0] = 'X';  // ❌ Error: s is const
}

std::string str = "Hello";
print(str);  // ✅ No copy (efficient)

print("World");  // ✅ Can bind to temporary

// Without const, temporaries don't bind
void modify(std::string& s) { s += "!"; }
// modify("Hello");  // ❌ Error: can't bind non-const ref to temporary
```

Const references can bind to temporaries, extending their lifetime. This makes `const std::string&` the idiomatic way to pass strings to functions: no copy overhead, clear intent that the function won't modify the argument.

## Return by Reference

Functions can return references to allow modification of class members or avoid copying large objects.

```cpp showLineNumbers 
class Widget {
    std::string name;
public:
    std::string& getName() {  // Return reference
        return name;  // Return reference to member
    }
    
    const std::string& getName() const {  // const version
        return name;  // Can't modify through returned reference
    }
};

Widget w;
w.getName() = "New Name";  // ✅ OK: modifies through reference

const Widget cw;
// cw.getName() = "X";  // ❌ Error: const version returns const ref
```

Returning non-const references enables chaining and direct modification of internals. Returning const references provides efficient read access without allowing modification. This pattern is common for container element access (`vector::operator[]`) and getter methods.

### Danger: Dangling References

Never return references to local variables. Locals are destroyed when the function returns, creating dangling references.

```cpp showLineNumbers 
int& dangerous() {
    int x = 42;
    return x;  // ❌ Dangling: x destroyed at return
}

int& ref = dangerous();
ref = 100;  // ❌ Undefined behavior: x doesn't exist

// ✅ Correct: return reference to member or parameter
class Safe {
    int data;
public:
    int& getData() { return data; }  // ✅ Member outlives call
};

int& choose(int& a, int& b, bool flag) {
    return flag ? a : b;  // ✅ Parameter outlives call
}
```

References don't extend object lifetimes. Returning a reference to a local creates the same problem as returning a pointer to a local - undefined behavior. Only return references to objects that outlive the function call.

## Rvalue References (C++11)

Rvalue references (using `&&`) bind to temporaries and enable move semantics, allowing efficient transfer of resources.

```cpp showLineNumbers 
void process(int& x) {       // Lvalue reference
    std::cout << "lvalue\n";
}

void process(int&& x) {      // Rvalue reference
    std::cout << "rvalue\n";
}

int a = 10;
process(a);       // Calls lvalue version
process(10);      // Calls rvalue version (temporary)
process(std::move(a));  // Calls rvalue version (cast to rvalue)
```

Rvalue references enable distinguishing between objects you can modify in-place (lvalues) versus temporaries you can "steal" from (rvalues). This distinction is fundamental to move semantics and perfect forwarding.

### Move Semantics

Move operations transfer ownership of resources from source to destination, avoiding expensive copying.

```cpp showLineNumbers 
class Buffer {
    char* data;
    size_t size;
public:
    // Copy constructor - expensive
    Buffer(const Buffer& other) {
        size = other.size;
        data = new char[size];
        std::copy(other.data, other.data + size, data);
    }
    
    // Move constructor - cheap
    Buffer(Buffer&& other) noexcept {
        data = other.data;      // Steal pointer
        size = other.size;
        other.data = nullptr;   // Leave other valid but empty
        other.size = 0;
    }
};

Buffer create() { return Buffer(1000); }

Buffer b = create();  // Move constructor called (not copy!)
```

The move constructor transfers ownership by stealing the source's pointer instead of allocating new memory and copying. The source object is left in a valid but empty state. This optimization is transparent when returning by value due to move semantics.

## Reference Wrappers

`std::reference_wrapper` allows storing references in containers, which normally can't hold references directly.

```cpp showLineNumbers 
int x = 10, y = 20, z = 30;

// ❌ Can't store references in vector
// std::vector<int&> refs;  // Error

// ✅ Can store reference_wrappers
std::vector<std::reference_wrapper<int>> refs;
refs.push_back(std::ref(x));
refs.push_back(std::ref(y));
refs.push_back(std::ref(z));

refs[0].get()++;  // Increments x
std::cout << x;   // 11
```

References can't be stored in containers because they're not regular objects (can't be reassigned, no default construction). `std::reference_wrapper` wraps a reference in a copyable, assignable object that acts like a reference.

## Forwarding References

Template parameters with `&&` create forwarding references (universal references) that preserve value categories.

```cpp showLineNumbers 
template<typename T>
void wrapper(T&& arg) {  // Forwarding reference
    process(std::forward<T>(arg));  // Perfect forwarding
}

int x = 10;
wrapper(x);      // T deduced as int&, arg is lvalue ref
wrapper(10);     // T deduced as int, arg is rvalue ref
wrapper(std::move(x));  // T deduced as int, arg is rvalue ref
```

Forwarding references enable perfect forwarding: passing arguments to another function while preserving whether they were lvalues or rvalues. This is fundamental to writing generic wrapper functions that don't affect move/copy semantics.

:::warning Common Mistakes

**Dangling Reference**: Returning reference to local variable causes undefined behavior.

**Reference to Temporary**: Binding non-const reference to temporary is illegal.

**Thinking References are Pointers**: `ref = other` copies value, doesn't reseat reference.

**Null References**: Impossible by design, but taking address of dereferenced null pointer creates one.
:::

## Summary

References are aliases for existing objects, providing alternative names for the same memory location. Unlike pointers, references must be initialized at declaration and cannot be null or reseated. All operations on a reference affect the original object because they're identical. Assignment through a reference copies values, it doesn't change what the reference refers to. References are ideal for function parameters to avoid copying and enable modification of caller's variables. Const references (`const T&`) allow efficient read-only access and bind to temporaries. Functions can return references for efficient access to members, but never return references to local variables as they create dangling references. Rvalue references (`T&&`) bind to temporaries and enable move semantics for efficient resource transfer. Forwarding references in templates (`T&&`) preserve value categories for perfect forwarding. `std::reference_wrapper` enables storing references in containers. The key differences from pointers: references can't be null (always valid), can't be reseated (always refer to same object), don't require dereferencing (transparent access), and must be initialized. Use references for guaranteed-valid aliases and efficient parameter passing. Use pointers when you need nullable, reassignable, or optional semantics. The syntax is cleaner than pointers (`ref` vs `*ptr`), the compiler guarantees validity, and the semantics are closer to normal variable usage, making references the preferred choice when their constraints (non-null, non-reassignable) fit your needs.

:::success Key Takeaways

**Alias Not Copy**: References are alternate names, not new storage.

**Guaranteed Valid**: No null references possible - always safe to use.

**No Reseating**: `ref = x` copies value into referred object, doesn't change reference binding.

**Perfect for Parameters**: `const T&` for efficiency without copying or modification.

**No Dereferencing Needed**: Use references like normal variables, not `*ptr` syntax.

**Lifetime Matters**: References don't extend object lifetime - returning refs to locals is undefined behavior.
:::