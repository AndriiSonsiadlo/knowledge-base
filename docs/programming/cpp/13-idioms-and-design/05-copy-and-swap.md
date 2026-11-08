---
id: copy-and-swap
title: Copy-and-Swap
sidebar_label: Copy-and-Swap
sidebar_position: 5
tags: [c++, copy-and-swap, idioms, exception-safety, assignment-operator]
---

# Copy-and-Swap

**Copy-and-swap** writes an assignment operator in two steps: build a copy of the source (which may
throw), then swap it with `*this` (which cannot). If the copy fails, `*this` was never touched. The
old state ends up in the copy, whose destructor releases it. One function gives you the strong
exception guarantee, self-assignment safety, and (with a by-value parameter) both copy and move
assignment.

What the copy and move operations must do is owned by
[Copy and Move Semantics](../07-classes-and-oop/copy-and-move-semantics.md), and which of them to
declare by [Rule of 0/3/5](../07-classes-and-oop/rule-of-zero-three-five.md). The exception
guarantee levels are defined on
[noexcept and the strong guarantee](../10-error-handling-and-safety/02-noexcept-and-strong-guarantee.md).
This page is the idiom itself.

**Prerequisites:** [Copy and Move Semantics](../07-classes-and-oop/copy-and-move-semantics.md),
[`noexcept`](../04-functions-and-call-mechanics/noexcept.md), [RAII](./01-raii.md).

## The problem with the obvious operator

```cpp title="Fragment: naive copy assignment"
Buffer& Buffer::operator=(const Buffer& o) {
    delete[] data_;                          // old state destroyed first
    size_ = o.size_;
    data_ = new int[size_];                  // may throw: *this now points at freed memory
    std::copy(o.data_, o.data_ + size_, data_);
    return *this;
}
```

If `new` throws, `data_` dangles (and `size_` is already updated), so the object is not even valid.
`b = b` is worse: it frees the data and then copies from the freed array. Fixing these with an
`if (this == &o)` test and reordering is possible, but each fix is another thing to get right in
every class. Copy-and-swap makes the correct order the only order.

## The idiom

```cpp title="cas.cpp" showLineNumbers
#include <algorithm>
#include <cstddef>
#include <cstdio>
#include <utility>

class Buffer {
public:
    explicit Buffer(std::size_t n = 0) : size_(n), data_(n ? new int[n]() : nullptr) {}
    Buffer(const Buffer& o) : size_(o.size_), data_(o.size_ ? new int[o.size_] : nullptr) {
        std::copy(o.data_, o.data_ + size_, data_);
    }
    Buffer(Buffer&& o) noexcept : Buffer() { swap(*this, o); }   // move = default-construct + swap
    ~Buffer() { delete[] data_; }

    Buffer& operator=(Buffer other) noexcept {   // by value: the copy (or move) happens here
        swap(*this, other);
        return *this;                             // other's destructor frees the old state
    }

    friend void swap(Buffer& a, Buffer& b) noexcept {
        using std::swap;
        swap(a.size_, b.size_);
        swap(a.data_, b.data_);
    }

    std::size_t size() const { return size_; }
    int& operator[](std::size_t i) { return data_[i]; }

private:
    std::size_t size_;
    int* data_;
};

int main() {
    Buffer a(3), b(5);
    a[0] = 42;
    b = a;                                       // copy assignment: copy a into the parameter
    std::printf("%zu %d\n", b.size(), b[0]);

    b = Buffer(10);                              // rvalue: parameter is move-constructed (or elided)
    std::printf("%zu\n", b.size());

    Buffer& alias = b;
    b = alias;                                   // self-assignment: correct, one needless copy
    std::printf("%zu\n", b.size());
}
```

Output (g++ 15 and clang++ 21, `-std=c++20 -Wall -Wextra`, `-O0` and `-O2`):

```text
3 42
10
10
```

Reading `operator=(Buffer other)`:

1. **The parameter is the copy.** For `b = a`, `a` is an lvalue, so `other` is copy-constructed from it.
   That is the only step that can throw, and it happens before the function body, so `*this`
   is untouched on failure.
2. **`swap` commits.** It exchanges the two pointers and sizes: no allocation, no throw, so it is
   `noexcept`. After it, `*this` has the new state and `other` has the old one.
3. **The destructor of `other` releases the old state** at the closing brace. There is no
   explicit cleanup code, which is [RAII](./01-raii.md) doing the work.

The failure case, run (g++ 15 and clang++ 21, same flags):

```cpp title="strong.cpp" showLineNumbers
#include <cstdio>
#include <stdexcept>
#include <string>
#include <utility>

struct Bomb {
    static inline bool armed = false;
    Bomb() = default;
    Bomb(const Bomb&) { if (armed) throw std::runtime_error("copy failed"); }
};

struct Pair {
    std::string name;
    Bomb b;
    Pair() = default;
    Pair(const Pair&) = default;
    Pair& operator=(Pair other) noexcept { name.swap(other.name); return *this; }
};

int main() {
    Pair x; x.name = "x";
    Pair y; y.name = "y";
    Bomb::armed = true;
    try { y = x; } catch (const std::exception& e) { std::printf("%s, y=%s\n", e.what(), y.name.c_str()); }
}
```

```text
copy failed, y=y
```

`y` keeps its previous contents. That is the strong guarantee, and `Pair` got it without
a single `try`.

### One operator for copy and move assignment

Because the parameter is taken by value, an rvalue source is **move**-constructed into it (or
constructed in place, with elision): `b = Buffer(10)` allocates once and swaps. One operator therefore
covers both assignments, and the move assignment is as cheap as a move constructor plus a swap. The
move constructor above is written as "default-construct, then swap", which keeps it
`noexcept` and reuses the swap.

Do not also declare `operator=(Buffer&&)` next to `operator=(Buffer)`: a call with an rvalue is
ambiguous (checked with g++ 15 and clang++ 21):

```text
error: ambiguous overload for 'operator=' (operand types are 'T' and 'T')
```

### Writing `swap`

Provide a non-member `swap` found by argument-dependent lookup, written as a hidden friend as above.
Inside it, `using std::swap;` followed by an unqualified call lets each member use its own `swap`
if one exists and fall back to `std::swap` otherwise. Callers should do the same (or use
`std::ranges::swap`, C++20) so that your overload is found. Specializing `std::swap` for your own type is unnecessary: the generic version works for any
move-constructible, move-assignable type, and a hidden friend is found first by ADL. The `swap` must be `noexcept`; if a member's swap can throw, the
idiom no longer gives the strong guarantee.

## Trade-offs

Copy-and-swap optimizes for correctness and brevity, not for every case:

- **It always allocates on copy assignment.** The by-value parameter builds a fresh copy even when
  `*this` already has enough capacity that an element-wise copy would reuse. `std::vector`'s own
  assignment reuses capacity for exactly this reason. If assignment is hot and sizes are
  similar, write the two assignments by hand and keep copy-and-swap for the rest.
- **Self-assignment does a needless copy** (correctly, as `alias` in the example shows). Adding a
  self-test would slow every other assignment, so the usual advice is not to.
- **It needs a cheap, `noexcept` swap.** A type with no non-throwing swap (for example one whose
  members include a throwing-move type) cannot give the strong guarantee this way.
- **It covers only `*this`.** It guarantees "all or nothing" for the object,
  not for other objects the assignment might touch.
- **It is the wrong tool for a class that follows the rule of zero.** If every member already
  manages itself, the compiler-generated assignment is already correct; do not write one.

For a handle class that owns a single raw resource, prefer wrapping the resource in `unique_ptr` (move-only) or
a container (copy and move) over hand-writing any of this; see [RAII](./01-raii.md).

## Related

- [Copy and Move Semantics](../07-classes-and-oop/copy-and-move-semantics.md): the four operations and what a moved-from object holds.
- [noexcept and the strong guarantee](../10-error-handling-and-safety/02-noexcept-and-strong-guarantee.md): why "prepare, then commit with a non-throwing step" works.
- [Pimpl](./02-pimpl.md): the same commit step applied to a single pointer.

## References

- [cppreference: Copy assignment operator](https://en.cppreference.com/w/cpp/language/copy_assignment)
- [cppreference: `std::swap`](https://en.cppreference.com/w/cpp/algorithm/swap)
- [cppreference: `std::ranges::swap`](https://en.cppreference.com/w/cpp/utility/ranges/swap)
