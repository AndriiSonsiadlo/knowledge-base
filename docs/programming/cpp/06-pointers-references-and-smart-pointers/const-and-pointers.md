---
id: const-pointers
title: const Pointers
sidebar_label: const Pointers
sidebar_position: 4
tags: [c++, pointers, const, immutability]
---

# const Pointers

`const` with pointers creates three distinct scenarios. Understanding the difference prevents bugs and documents intent.

:::info Reading Rule
**Read declarations right-to-left:**
- `const int* ptr` = "ptr is a pointer to const int"
- `int* const ptr` = "ptr is a const pointer to int"
- `const int* const ptr` = "ptr is a const pointer to const int"
:::


## Use Cases

`type* const ptr` pointers are useful when you want a pointer with reference-like "cannot be reseated" semantics but need actual pointer behavior.

Permanent reference to specific object:

```cpp showLineNumbers 
class Widget {
    int* const internal_ptr;  // Always points to same allocation
public:
    Widget(int* p) : internal_ptr(p) {
        // internal_ptr cannot be changed after initialization
    }
    void modify() {
        *internal_ptr = 100;  // Can modify pointed-to value
    }
};
```

## Three Forms
```cpp showLineNumbers
int x = 10, y = 20;

// 1. Pointer to const (can't modify data)
const int* ptr1 = &x;
// *ptr1 = 30;  // ❌ Error
ptr1 = &y;      // ✅ OK: can point elsewhere

// 2. const pointer (can't change pointer)
int* const ptr2 = &x;
*ptr2 = 30;     // ✅ OK: can modify data
// ptr2 = &y;   // ❌ Error: can't point elsewhere

// 3. const pointer to const (can't change either)
const int* const ptr3 = &x;
// *ptr3 = 30;  // ❌ Error
// ptr3 = &y;   // ❌ Error
```

## Visual Guide
```
┌─────────────────────────────────────────────┐
│  const int* ptr                             │
│  ─────────►  const data, mutable pointer    │
│                                             │
│  int* const ptr                             │
│  ─────────►  mutable data, const pointer    │
│                                             │
│  const int* const ptr                       │
│  ─────────►  const data, const pointer      │
└─────────────────────────────────────────────┘
```

### Reading Complex Declarations

The right-to-left reading rule helps parse complex const declarations correctly.

```cpp showLineNumbers 
const int* const ptr;
// Read right-to-left: "ptr is a const pointer to const int"

int const* const ptr;  
// Read right-to-left: "ptr is a const pointer to const int"

const int* ptr;
// Read right-to-left: "ptr is a pointer to const int"

int* const ptr;
// Read right-to-left: "ptr is a const pointer to int"
```

The position of `const` relative to `*` determines what's const. Before `*` (or after type) = data is const. After `*` = pointer is const.

## Function Parameters

`const` pointers in function signatures communicate intent and enable compiler optimizations.

```cpp showLineNumbers 
// Pointer to const - can't modify through pointer
void read_data(const int* data, size_t size) {
    for (size_t i = 0; i < size; ++i) {
        std::cout << data[i];  // ✅ Can read
        // data[i] = 0;        // ❌ Cannot modify
    }
}

// const pointer - pointer itself won't change
void process(int* const ptr) {
    *ptr = 42;          // ✅ Can modify data
    // ptr = nullptr;   // ❌ Cannot change pointer
}

// Both const
void display(const int* const ptr) {
    std::cout << *ptr;  // ✅ Can read
    // *ptr = 10;       // ❌ Cannot modify
    // ptr = nullptr;   // ❌ Cannot change pointer
}
```

Most commonly, functions take `pointer-to-const` to indicate they won't modify the argument. The `const pointer` (second case) is rare for parameters since local copies of pointers can freely be reassigned without affecting the caller.

## Arrays and const

Pointer-to-const works naturally with arrays, preventing modification of array elements.

```cpp showLineNumbers 
int arr[] = {1, 2, 3, 4, 5};
const int* ptr = arr;

// Can read through pointer
std::cout << ptr[2];  // 3

// Cannot modify through pointer
// ptr[2] = 10;       // ❌ Error

// Array itself still modifiable
arr[2] = 10;          // ✅ OK
std::cout << ptr[2];  // 10
```

Array subscripting works through pointer-to-const because it's syntactic sugar for pointer arithmetic and dereferencing. The const prevents modification but allows navigation.

## Casting Away const

You can remove const with `const_cast`, but modifying originally-const data is undefined behavior.

```cpp showLineNumbers 
int x = 10;
const int* cptr = &x;

// Remove const with const_cast
int* ptr = const_cast<int*>(cptr);
*ptr = 20;  // ✅ OK: x wasn't originally const

// Dangerous with originally const data
const int y = 30;
const int* cptr2 = &y;
int* ptr2 = const_cast<int*>(cptr2);
*ptr2 = 40;  // ❌ Undefined behavior: y was const!
```

:::danger const_cast Rules
- ✅ Safe: removing const from non-const data
- ❌ Unsafe: modifying originally const data = UB
- Use only when interfacing with badly-designed APIs
:::
 
## const with Dynamic Memory

const affects what you can do with dynamically allocated memory through the pointer.

```cpp showLineNumbers 
// Pointer to const on heap
const int* ptr1 = new int(42);
// *ptr1 = 10;  // ❌ Cannot modify
delete ptr1;  // ✅ Can still delete

// const pointer to heap memory
int* const ptr2 = new int(42);
*ptr2 = 10;  // ✅ Can modify
delete ptr2;  // ✅ Can delete

// Both const
const int* const ptr3 = new int(42);
// *ptr3 = 10;  // ❌ Cannot modify
delete ptr3;  // ✅ Can delete
```

The const qualifiers don't prevent deleting the memory, only modification through the pointer. Deletion is a memory management operation, not data modification.

## const Correctness

Using const correctly throughout your code catches bugs at compile-time and documents intent.

```cpp showLineNumbers 
class Buffer {
    int* data;
    size_t size;
    
public:
    // const accessor - can't modify
    const int* getData() const {
        return data;
    }
    
    // Non-const accessor - can modify
    int* getData() {
        return data;
    }
    
    // const parameter
    void copy(const int* source, size_t count) {
        // source won't be modified
        std::copy(source, source + count, data);
    }
};

const Buffer cb;
const int* data = cb.getData();  // ✅ Calls const version

Buffer b;
int* data2 = b.getData();  // ✅ Calls non-const version
```

## Summary

:::info Three forms
- `const T*` → can't modify data, can move pointer
- `T* const` → can modify data, can't move pointer  
- `const T* const` → can't modify data or pointer
:::

:::info Reading guide
- Read right-to-left
- Before `*` → data is const
- After `*` → pointer is const
:::

:::info Common patterns
- `const T*` for function parameters (read-only)
- `T* const` for member pointers (fixed location)
- `const T* const` for maximum protection
:::

:::info Type conversions
- Non-const → const: implicit (safe)
- const → non-const: requires `const_cast` (dangerous)
:::

:::success Best practices
- Use `const` everywhere possible
- Function parameters: prefer `const T*` for read-only
- Document intent through const-correctness
- Never modify originally-const data
:::
