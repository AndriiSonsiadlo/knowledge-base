---
id: pointer-arithmetic
title: Pointer Arithmetic
sidebar_label: Pointer Arithmetic
sidebar_position: 3
tags: [c++, pointers, arithmetic, arrays, undefined-behavior, ptrdiff_t]
---

# Pointer Arithmetic

Adding an integer to a pointer moves it by that many **elements**, not bytes: for `T* p`, `p + n`
is the address of the element `n` places further along, which is `n * sizeof(T)` bytes away. This
is what lets pointers walk arrays, and it is also what the subscript operator is defined in terms
of. The catch is that the language only defines the arithmetic *inside one array object*. Step
outside and the behavior is undefined, even if you never read the result.

**Prerequisites:** [Raw pointers](./raw-pointers.md) (including array-to-pointer conversion).

## Scaling by element size

```cpp title="scaling.cpp" showLineNumbers
#include <cstdio>

int main() {
    int arr[5] = {10, 20, 30, 40, 50};
    int* p = arr;

    std::printf("%d %d\n", *(p + 1), p[2]);      // p[2] is defined as *(p + 2)
    ++p;                                          // now &arr[1]
    p += 2;                                       // now &arr[3]
    std::printf("%d\n", *p);

    // The byte distance is a multiple of sizeof(int):
    std::printf("%zu\n", reinterpret_cast<const char*>(&arr[1]) - reinterpret_cast<const char*>(&arr[0]));
}
```

```text
20 30
40
4
```

The last line prints 4 on every mainstream platform, but it is `sizeof(int)`, which is
implementation-defined. The built-in `a[i]` is *defined* as `*(a + i)`, so `2[arr]` also compiles
and is equal to `arr[2]`; nobody should write it.

<Diagram title="int arr[5], p = arr" caption="Valid positions are 0 to 4 for dereferencing, and 5 (one past the end) for forming and comparing only." accent="blue">
  <DiagramRow>
    <DiagramNode title="arr[0]" accent>p + 0</DiagramNode>
    <DiagramNode title="arr[1]">p + 1</DiagramNode>
    <DiagramNode title="arr[2]">p + 2</DiagramNode>
    <DiagramNode title="arr[3]">p + 3</DiagramNode>
    <DiagramNode title="arr[4]">p + 4</DiagramNode>
    <DiagramNode title="end" dashed>p + 5, never dereference</DiagramNode>
  </DiagramRow>
</Diagram>

## What is defined

For a pointer `p` to element `i` of an array of `N` elements (a single object counts as an array of
one), the standard defines:

| Expression | Result | Condition |
|---|---|---|
| `p + n`, `p - n`, `p += n`, `++p`, `--p` | pointer to element `i ± n` | the new index is in `[0, N]` |
| `p - q` | `std::ptrdiff_t` count of elements between | both point into (or one past) the same array |
| `p == q`, `p != q` | whether they point at the same place | any two pointers of compatible type |
| `p < q`, `<=`, `>`, `>=` | position order | same array; otherwise unspecified (use `std::less`) |
| `*p`, `p[k]` | the element | the index is in `[0, N-1]` |

Index `N` (**one past the end**) may be formed, compared and subtracted, but not dereferenced. It is
what makes the half-open range `[begin, end)` loop work. Any other result, such as `arr - 1` or
`arr + 6`, is undefined behavior **at the moment of the computation**. Hardware that doesn't wrap
is no excuse: a compiler may assume the arithmetic stayed in bounds and fold a later comparison to a
constant.

Three smaller rules:

- Adding `0` to a null pointer yields null, and `nullptr - nullptr` is `0`. Both are defined in C++
  (they are not in C before C23).
- `p - q` has type `std::ptrdiff_t` (signed). The count can be negative. Mixing it with `std::size_t`
  silently converts a negative number to a huge unsigned one.
- Arithmetic needs a **complete object type**. `void*` and function pointers have no element size,
  so `p + 1` is ill-formed. GCC and Clang accept it on `void*` as an extension that treats
  `sizeof(void)` as 1; `-Wpointer-arith` (part of `-pedantic`) warns. Cast to `std::byte*` or
  `unsigned char*` for explicit byte offsets.

## Iterating a range

A pair of pointers `[first, last)` is the original form of the iterator range every standard
algorithm accepts. Pointers into an array or a `std::vector`'s buffer are valid iterators.

```cpp title="range.cpp" showLineNumbers
#include <algorithm>
#include <cstddef>
#include <cstdio>
#include <iterator>

int main() {
    int arr[] = {3, 1, 4, 1, 5, 9};
    const int* first = std::begin(arr);
    const int* last  = std::end(arr);            // one past the end

    std::ptrdiff_t n = last - first;             // element count, signed
    std::printf("%td elements\n", n);

    for (const int* p = first; p != last; ++p)   // != rather than <, works for any iterator
        std::printf("%d ", *p);
    std::puts("");

    const int* where = std::find(first, last, 4);
    std::printf("4 is at index %td\n", where - first);

    // Walking backwards: stop BEFORE decrementing past the start.
    for (const int* p = last; p != first;) {
        --p;
        std::printf("%d ", *p);
    }
    std::puts("");
}
```

```text
6 elements
3 1 4 1 5 9 
4 is at index 2
9 5 1 4 1 3 
```

The reverse loop shows the one-past-the-start trap. `for (p = last - 1; p >= first; --p)` ends by
computing `first - 1`, which is undefined, and the `>=` test never fails on an unsigned or wrapped
value. Decrement first, then use.

For new code, prefer a range-`for`, a standard algorithm, or `std::span` *(C++20)*, which keeps the
pointer and length together and gives bounds-checkable `operator[]` in hardened library modes.

## Multidimensional arrays

`int m[2][3]` is an array of 2 elements, each an `int[3]`. So `m[i]` decays to `int*` for row `i`,
and `m + 1` is a `int (*)[3]` that skips a whole row (3 ints at once).

```cpp title="rows.cpp" showLineNumbers
#include <cstdio>

int main() {
    int m[2][3] = {{1, 2, 3}, {4, 5, 6}};

    int (*row)[3] = m;                  // pointer to a row of 3 ints
    ++row;                              // advances by 3 * sizeof(int)
    std::printf("%d\n", (*row)[1]);     // 5

    int* r1 = m[1];                     // pointer to the first int of row 1
    std::printf("%d\n", r1[2]);         // 6, still inside row 1

    // m[0][4] would read "through" row 0 into row 1. Formally undefined (index 4 of an int[3]),
    // though it works with every compiler at -O0. Don't rely on it.
}
```

```text
5
6
```

Treating the whole 2D array as a flat `int[6]` through `&m[0][0] + k` for `k >= 3` has the same
formal problem, because the pointer started inside a 3-element array. It works in practice, and
sanitizers do not flag it, but it is the kind of code that stops working when an optimizer starts
exploiting bounds. If you need a flat view, store a `std::vector<int>` or `int[6]` and compute
`i * cols + j` yourself.

## Bytes and unrelated objects

Moving by a byte offset is legitimate for the object representation of any object: convert to
`unsigned char*`, `char*` or `std::byte*` (an allowed aliasing exception, see
[strict aliasing](../05-memory-and-object-lifetime/strict-aliasing.md)) and do arithmetic there. That
is how `std::memcpy`-style code and serializers inspect an object.

What is not allowed is arithmetic that jumps between unrelated objects: `&a + (&b - &a)` is undefined
even when `a` and `b` are adjacent locals, because they are not elements of one array. Converting
pointers to `std::uintptr_t` and doing integer arithmetic is the only way to reason about raw
addresses, and the result converts back to a usable pointer only if it is a value you obtained from
that conversion in the first place. (Optimizers track *pointer provenance*, which integers don't
carry; the exact C++ rules are still evolving.)

## Common mistakes

- **Loop bound off by one.** `i <= n` or `p <= last` reads one past the end.
- **Pointer to a vector element kept across `push_back`.** Reallocation invalidates every pointer
  into the old buffer.
- **Adding to the wrong type.** `char*` steps by 1, `int*` by 4: cast carefully when parsing
  buffers, and mind [alignment](../05-memory-and-object-lifetime/alignment.md) when you reinterpret
  the result.
- **Subtracting pointers into different arrays** to find a "distance".
- **Mixing signed and unsigned** counts, so that `p - n` becomes `p + huge`.

## Key points

- `p + n` moves `n` elements; `p[i]` is `*(p + i)`.
- Defined only within an array plus one past the end; forming anything else is already undefined.
- Subtraction gives a signed `std::ptrdiff_t` and requires the same array.
- Use `[first, last)` ranges, algorithms, or `std::span` instead of hand-rolled bounds.

## Related

- [Raw pointers](./raw-pointers.md): where array decay and dangling pointers are covered.
- [const and pointers](./const-and-pointers.md): `const int*` as the read-only cursor type.
- [Iterators](../09-standard-library/iterators.md): the generalization of pointer arithmetic.
