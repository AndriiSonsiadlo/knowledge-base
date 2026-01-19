---
id: pointer-arithmetic
title: Pointer Arithmetic
sidebar_label: Pointer Arithmetic
sidebar_position: 3
tags: [c++, pointers, arithmetic, arrays, memory]
---

# Pointer Arithmetic

Pointer arithmetic allows adding and subtracting integers from pointers to navigate through contiguous memory. The compiler automatically scales the arithmetic by the pointed-to type's size, making array traversal intuitive and efficient.

:::info Automatic Scaling
Adding 1 to a pointer moves it forward by `sizeof(type)` bytes, not 1 byte. The compiler handles the math so `ptr + 1` points to the next element, regardless of element size.
:::

## Basic Pointer Arithmetic

When you add an integer to a pointer, the pointer advances by that many elements of the pointed-to type. This makes array navigation natural.

```cpp
int arr[] = {10, 20, 30, 40, 50};
int* ptr = arr;  // Points to arr[0]

ptr + 0;  // Points to arr[0] (address: 0x1000)
ptr + 1;  // Points to arr[1] (address: 0x1004, not 0x1001!)
ptr + 2;  // Points to arr[2] (address: 0x1008)

// The actual address increases by sizeof(int) = 4 bytes each time
std::cout << ptr;       // 0x1000
std::cout << (ptr + 1); // 0x1004
std::cout << (ptr + 2); // 0x1008
```

The compiler multiplies the integer by `sizeof(int)` automatically. This is why pointer arithmetic "just works" for arrays: `ptr + 1` always means "the next element," regardless of whether elements are 1, 4, or 100 bytes.

### Dereferencing Arithmetic Results

You can combine pointer arithmetic with dereferencing to access elements at calculated positions.

```cpp
int arr[] = {10, 20, 30, 40, 50};
int* ptr = arr;

*(ptr + 0);  // 10 (arr[0])
*(ptr + 1);  // 20 (arr[1])
*(ptr + 2);  // 30 (arr[2])

// This is exactly what subscript notation does
ptr[0];  // 10 (same as *(ptr + 0))
ptr[1];  // 20 (same as *(ptr + 1))
ptr[2];  // 30 (same as *(ptr + 2))
```

The subscript operator `ptr[i]` is syntactic sugar for `*(ptr + i)`. Both forms are equivalent, but subscript notation is usually clearer. However, understanding the pointer arithmetic underneath helps when you need to manipulate addresses directly.

## Incrementing and Decrementing

Pointers support increment and decrement operators, which move the pointer forward or backward by one element.

```cpp
int arr[] = {10, 20, 30, 40, 50};
int* ptr = arr;

*ptr;      // 10 (arr[0])
ptr++;     // Move to next element
*ptr;      // 20 (arr[1])
ptr += 2;  // Move forward 2 elements
*ptr;      // 40 (arr[3])
ptr--;     // Move back 1 element
*ptr;      // 30 (arr[2])
```

These operators modify the pointer itself, changing what it points to. This is useful for iterating through arrays or linked structures. Post-increment (`ptr++`) and pre-increment (`++ptr`) both move the pointer but differ in what value they return.

### Pre vs Post Increment

The distinction between pre and post increment matters when the result is used in an expression.

```cpp
int arr[] = {10, 20, 30};
int* ptr = arr;

int x = *ptr++;   // Post-increment: dereferences, THEN increments
// x = 10 (dereferenced before increment)
// ptr now points to arr[1]

int y = *++ptr;   // Pre-increment: increments, THEN dereferences  
// ptr moves to arr[2] first
// y = 30 (dereferenced after increment)
```

Post-increment returns the old pointer value before incrementing, while pre-increment increments first then returns the new value. This is identical to how these operators work with integers but affects which memory location gets accessed.

## Pointer Subtraction

Subtracting two pointers gives the number of elements between them, not the byte difference. This only makes sense for pointers into the same array.

```cpp
int arr[] = {10, 20, 30, 40, 50};
int* start = arr;
int* end = arr + 5;

ptrdiff_t distance = end - start;  // 5 (elements, not bytes)

int* p1 = arr + 2;  // Points to arr[2]
int* p2 = arr + 0;  // Points to arr[0]
ptrdiff_t diff = p1 - p2;  // 2
```

The result type is `ptrdiff_t`, a signed integer type that can represent the difference between two pointers. The compiler automatically divides the byte difference by `sizeof(type)` to give you elements rather than bytes.

### Calculating Array Size with Pointers

Pointer subtraction enables computing array size when you have pointers to the beginning and end.

```cpp
int arr[] = {10, 20, 30, 40, 50};
int* begin = arr;
int* end = arr + 5;  // One past the last element

size_t size = end - begin;  // 5 elements

// Common pattern in C++ standard library
std::vector<int> vec = {1, 2, 3};
vec.end() - vec.begin();  // Vector size
```

This pattern is fundamental to C++ iterators. The "one past the end" pointer is valid for comparison and subtraction but must never be dereferenced. This convention allows natural loop conditions.

## Pointer Comparison

Pointers can be compared with relational operators when they point into the same array or object. Comparison checks addresses, not pointed-to values.

```cpp
int arr[] = {10, 20, 30, 40, 50};
int* p1 = arr;
int* p2 = arr + 2;
int* p3 = arr + 4;

if (p1 < p2) {  // ✅ True: p1 comes before p2
    std::cout << "p1 is earlier in memory\n";
}

if (p2 < p3) {  // ✅ True
    std::cout << "p2 comes before p3\n";
}

// Equality checks if they point to same location
if (p1 == arr) {  // ✅ True: both point to arr[0]
    std::cout << "Same location\n";
}
```

Relational comparison (`<`, `>`, `<=`, `>=`) only makes sense for pointers into the same array or object. Comparing unrelated pointers produces undefined behavior in some cases, though equality comparison is always safe.

## Iterating with Pointer Arithmetic

Pointer arithmetic is the foundation of array iteration. Modern C++ prefers iterators, but understanding pointer arithmetic helps with legacy code and manual memory management.

```cpp
int arr[] = {10, 20, 30, 40, 50};
int* end = arr + 5;  // One past last element

// Classic pointer iteration
for (int* ptr = arr; ptr != end; ++ptr) {
    std::cout << *ptr << " ";  // 10 20 30 40 50
}

// Backward iteration
for (int* ptr = end - 1; ptr >= arr; --ptr) {
    std::cout << *ptr << " ";  // 50 40 30 20 10
}
```

The loop continues while the pointer hasn't reached the end marker. Incrementing the pointer moves it to the next element. This pattern is common in C code and underlies how STL iterators work.

## Multi-Dimensional Arrays

Pointer arithmetic works with multi-dimensional arrays but requires understanding how they're laid out in memory as contiguous rows.

```cpp
int matrix[3][4] = {
    {1,  2,  3,  4},
    {5,  6,  7,  8},
    {9, 10, 11, 12}
};

int* ptr = &matrix[0][0];  // Pointer to first element

// Arrays are stored row-by-row in memory
*(ptr + 0);   // 1  (matrix[0][0])
*(ptr + 4);   // 5  (matrix[1][0])
*(ptr + 8);   // 9  (matrix[2][0])
*(ptr + 5);   // 6  (matrix[1][1])

// Calculating position: row * columns + col
int row = 1, col = 2;
*(ptr + row * 4 + col);  // 7 (matrix[1][2])
```

Multi-dimensional arrays are stored in row-major order. The compiler converts `matrix[i][j]` into pointer arithmetic: start address + i * row_size + j. Understanding this helps when working with dynamic 2D arrays or interfacing with C APIs.

## Dangers of Pointer Arithmetic

Pointer arithmetic has no bounds checking. Going beyond array boundaries causes undefined behavior.

```cpp
int arr[5] = {10, 20, 30, 40, 50};
int* ptr = arr;

*(ptr + 5);   // ❌ One past end (undefined to dereference)
*(ptr + 10);  // ❌ Way past end (undefined behavior)
*(ptr - 1);   // ❌ Before beginning (undefined behavior)

// The "one past end" pointer is valid for comparison
int* end = arr + 5;  // ✅ Valid (but don't dereference)
if (ptr != end) {    // ✅ Valid comparison
    *end;            // ❌ Invalid dereference
}
```

The compiler doesn't check if your pointer arithmetic stays within bounds. Accessing memory outside the array corrupts other variables, crashes the program, or appears to work but fails unpredictably. Always ensure your pointer arithmetic stays within valid ranges.

### Buffer Overflows

Unchecked pointer arithmetic is the root cause of buffer overflow vulnerabilities, where writing past array bounds corrupts adjacent memory.

```cpp
char buffer[10];
char* ptr = buffer;

for (int i = 0; i < 20; ++i) {  // ❌ Writes past buffer end
    *(ptr + i) = 'X';  // Undefined behavior after i >= 10
}

// Safe version
for (int i = 0; i < 10; ++i) {  // ✅ Stays within bounds
    *(ptr + i) = 'X';
}
```

Buffer overflows are dangerous security vulnerabilities. Attackers can exploit them to execute arbitrary code by carefully crafting input that overwrites critical memory. Modern C++ uses containers like `std::vector` and `std::array` which check bounds in debug mode and provide safer interfaces.

## Pointer Arithmetic with Structures

Pointer arithmetic works with any type, including structures. Adding 1 moves to the next structure in an array.

```cpp
struct Point {
    int x, y;
};

Point points[] = {{0, 0}, {1, 1}, {2, 2}};
Point* ptr = points;

ptr->x;           // 0 (first point's x)
(ptr + 1)->x;     // 1 (second point's x)
(ptr + 2)->y;     // 2 (third point's y)

// Iterating over array of structures
for (Point* p = points; p < points + 3; ++p) {
    std::cout << "(" << p->x << ", " << p->y << ")\n";
}
```

The compiler knows `sizeof(Point)` and moves the pointer by that amount. This works identically to fundamental types - the syntax and semantics are the same regardless of element size.

## Type Safety Considerations

Pointer arithmetic assumes all pointed-to memory has the same type. Treating memory as a different type breaks type safety and often causes undefined behavior.

```cpp
int arr[] = {10, 20, 30};
int* iptr = arr;

// ❌ Treating int array as char array
char* cptr = reinterpret_cast<char*>(arr);
cptr + 1;  // Moves 1 byte, not 1 int!
// This breaks the structure - now points into middle of an int

// Dereferencing produces garbage or crashes
int x = *(int*)(cptr + 1);  // ❌ Undefined behavior
```

When you reinterpret cast a pointer, arithmetic works in terms of the new type. This rarely does what you want and usually causes undefined behavior. Use pointer arithmetic only with the original pointed-to type.

:::warning Pointer Arithmetic Dangers

**No Bounds Checking**: Compiler won't stop you from going outside array bounds.

**Undefined Behavior**: Accessing memory outside valid range causes crashes or data corruption.

**Type Assumptions**: Arithmetic assumes memory is array of pointed-to type.

**Alignment Issues**: Casting between pointer types and using arithmetic can cause misalignment.

**One-Past-End**: Valid for comparison/subtraction but NOT for dereferencing.
:::

## Summary

Pointer arithmetic allows navigating contiguous memory by adding/subtracting integers from pointers. The compiler automatically scales arithmetic by `sizeof(type)`, so `ptr + 1` moves to the next element regardless of element size. Increment (`++`) and decrement (`--`) move pointers forward and backward by one element. Subscript notation `ptr[i]` is syntactic sugar for `*(ptr + i)`. Subtracting two pointers gives the number of elements between them (type `ptrdiff_t`). Pointer comparison (`<`, `>`, `==`) works for pointers into the same array. Iterating uses pointer arithmetic: `for (T* p = arr; p != end; ++p)`. Multi-dimensional arrays are stored row-major, enabling calculated access with `row * cols + col`. The "one past end" pointer is valid for comparison but never dereference it. Pointer arithmetic has no bounds checking - accessing outside array bounds is undefined behavior causing crashes or corruption. Buffer overflows from unchecked arithmetic are serious security vulnerabilities. Modern C++ prefers iterators and range-based for loops over raw pointer arithmetic. Use containers like `std::vector` and `std::array` which provide bounds-checked access. Pointer arithmetic is foundational to understanding arrays and iterators but should be used carefully, primarily for interfacing with C APIs or implementing low-level data structures. The key operations are addition (`ptr + n`), subtraction (`ptr - n`, `ptr1 - ptr2`), comparison (`ptr1 < ptr2`), increment/decrement (`ptr++`, `--ptr`), and understanding that arithmetic is scaled by type size automatically.

:::success Essential Concepts

**Automatic Scaling**: `ptr + 1` moves by `sizeof(*ptr)` bytes, not 1 byte.

**Subscript = Arithmetic**: `ptr[i]` is identical to `*(ptr + i)`.

**No Safety Net**: Compiler doesn't check bounds - your responsibility!

**One-Past-End Valid**: Can point one past end for loops, but never dereference.

**Same Array Only**: Arithmetic/comparison only meaningful for pointers into same array.

**Modern Alternative**: Use iterators and range-for instead of manual pointer arithmetic.
:::