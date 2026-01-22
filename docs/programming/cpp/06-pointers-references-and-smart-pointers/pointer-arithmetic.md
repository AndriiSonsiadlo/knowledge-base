---
id: pointer-arithmetic
title: Pointer Arithmetic
sidebar_label: Pointer Arithmetic
sidebar_position: 3
tags: [c++, pointers, arithmetic, arrays, memory]
---

# Pointer Arithmetic

Pointer arithmetic navigates contiguous memory with automatic scaling by type size. Essential for arrays but dangerous without bounds checking.

:::info Automatic Scaling
```cpp
int arr[5] = {10, 20, 30, 40, 50};
int* ptr = arr;

ptr + 1;  // Moves by sizeof(int) = 4 bytes, not 1 byte!
```

Compiler handles math: `ptr + n` → `ptr + (n * sizeof(type))`
:::

## Memory Layout
```
Address    Value    Pointer Position
0x1000     10       ptr + 0  (arr[0])
0x1004     20       ptr + 1  (arr[1])
0x1008     30       ptr + 2  (arr[2])
0x100C     40       ptr + 3  (arr[3])
0x1010     50       ptr + 4  (arr[4])
0x1014     ??       ptr + 5  (⚠️ out of bounds!)
```

## Basic Operations
```cpp showLineNumbers
int arr[] = {10, 20, 30, 40, 50};
int* ptr = arr;

// Addition
*(ptr + 0);  // 10
*(ptr + 1);  // 20
*(ptr + 2);  // 30

// Subscript notation (syntactic sugar)
ptr[0];      // 10 (same as *(ptr + 0))
ptr[1];      // 20 (same as *(ptr + 1))
ptr[2];      // 30 (same as *(ptr + 2))

// Increment/Decrement
ptr++;       // Move to next element
*ptr;        // 20
ptr += 2;    // Move forward 2 elements
*ptr;        // 40
```

:::warning No Bounds Checking
```cpp
int arr[5] = {10, 20, 30, 40, 50};
int* ptr = arr;

ptr[5];      // ❌ Undefined behavior
ptr[100];    // ❌ Undefined behavior
*(ptr - 1);  // ❌ Before array start
```

Compiler won't stop you - your responsibility!
:::

## Pointer Subtraction
```cpp showLineNumbers
int arr[] = {10, 20, 30, 40, 50};
int* start = arr;
int* end = arr + 5;

// Subtraction gives element count (not bytes)
ptrdiff_t count = end - start;  // 5 elements

int* p1 = arr + 2;  // Points to arr[2]
int* p2 = arr;      // Points to arr[0]
ptrdiff_t diff = p1 - p2;  // 2 elements
```

:::info Only Same Array
Subtraction only valid for pointers into same array!
```cpp
int arr1[5], arr2[5];
int* p1 = arr1;
int* p2 = arr2;
p1 - p2;  // ❌ Undefined behavior
```
:::

## Pointer Comparison
```cpp showLineNumbers
int arr[] = {10, 20, 30, 40, 50};
int* p1 = arr;
int* p2 = arr + 2;
int* end = arr + 5;

if (p1 < p2) {       // ✅ True: p1 comes before p2
    std::cout << "Earlier in memory\n";
}

if (p2 < end) {      // ✅ True: p2 before end
    std::cout << "Within bounds\n";
}

// One-past-end is valid for comparison
if (p1 != end) {     // ✅ Valid comparison
    // Don't dereference end!
}
```

Relational comparison (`<`, `>`, `<=`, `>=`) only makes sense for pointers into the same array or object.

## Array Iteration
```cpp showLineNumbers
int arr[] = {10, 20, 30, 40, 50};
int* end = arr + 5;  // One past last element

// Forward iteration
for (int* ptr = arr; ptr != end; ++ptr) {
    std::cout << *ptr << " ";  // 10 20 30 40 50
}

// Backward iteration
for (int* ptr = end - 1; ptr >= arr; --ptr) {
    std::cout << *ptr << " ";  // 50 40 30 20 10
}
```

:::success Modern Alternative
```cpp
// ✅ Prefer range-based for
for (int value : arr) {
    std::cout << value << " ";
}

// Or iterators
for (auto it = vec.begin(); it != vec.end(); ++it) {
    std::cout << *it << " ";
}
```
:::

## Multi-Dimensional Arrays
```cpp showLineNumbers
int matrix[3][4] = {
    {1,  2,  3,  4},
    {5,  6,  7,  8},
    {9, 10, 11, 12}
};

int* ptr = &matrix[0][0];

// Row-major storage (rows are contiguous)
*(ptr + 0);   // 1  (matrix[0][0])
*(ptr + 4);   // 5  (matrix[1][0])
*(ptr + 8);   // 9  (matrix[2][0])

// Calculate position: row * cols + col
int row = 1, col = 2;
*(ptr + row * 4 + col);  // 7 (matrix[1][2])
```

## Common Dangers

### Buffer Overflow
```cpp showLineNumbers
char buffer[10];
char* ptr = buffer;

// ❌ Writes past buffer
for (int i = 0; i < 20; ++i) {
    *(ptr + i) = 'X';  // Undefined after i >= 10
}

// ✅ Safe version
for (int i = 0; i < 10; ++i) {
    *(ptr + i) = 'X';
}
```

### One-Past-End Dereference
```cpp showLineNumbers
int arr[5] = {10, 20, 30, 40, 50};
int* end = arr + 5;

// ✅ Valid for comparison
if (ptr != end) { }

// ❌ Invalid to dereference
*end;  // Undefined behavior
```

### Type Punning
```cpp showLineNumbers
int arr[] = {10, 20, 30};
int* iptr = arr;

// ❌ Treating as different type
char* cptr = reinterpret_cast<char*>(arr);
cptr + 1;  // Moves 1 byte, not 1 int!

int x = *(int*)(cptr + 1);  // ❌ Undefined behavior
```

## Summary

:::info Core mechanics
- `ptr + n` moves by `n * sizeof(type)` bytes
- `ptr[i]` is syntactic sugar for `*(ptr + i)`
- Subtraction gives element count, not bytes
- Comparison works for same-array pointers
:::

:::info Valid operations
- Addition: `ptr + n`, `ptr++`, `ptr += n`
- Subtraction: `ptr - n`, `ptr--`, `ptr1 - ptr2`
- Comparison: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Dereference: `*ptr`, `ptr[i]`
:::

:::danger Dangers
- No bounds checking (compiler won't stop you)
- Buffer overflows (security vulnerabilities)
- One-past-end dereference (valid for comparison only)
- Type assumptions (arithmetic assumes correct type)
:::

:::success Modern practice
- Prefer iterators and range-based for
- Use `std::vector`/`std::array` (bounds checking)
- Pointer arithmetic for C API interop only
:::
