---
id: noexcept-and-strong-guarantee
title: Exception Safety and the Strong Guarantee
sidebar_label: Exception Safety
sidebar_position: 2
tags: [cpp, noexcept, exception-safety, strong-guarantee, basic-guarantee]
---

# Exception Safety and the Strong Guarantee

**Exception safety** is the promise a function makes about program state when an exception leaves it.
There are four standard levels. Most code should aim for the **strong guarantee** (all or nothing)
where it is affordable, and the tool that makes it possible is an operation that cannot throw, which is
what [`noexcept`](../04-functions-and-call-mechanics/noexcept.md) expresses. This page owns the
guarantee levels and the techniques for reaching them. The `noexcept` specifier and operator
themselves are on the linked page.

**Prerequisites:** [Exceptions](./01-exceptions.md),
[Copy and Move Semantics](../07-classes-and-oop/copy-and-move-semantics.md).

## The four levels

| Guarantee | If an exception escapes | Typical example |
|---|---|---|
| **No guarantee** | Anything: leaks, broken invariants | Raw `new`/`delete` with no cleanup |
| **Basic** | No leaks, all invariants hold, but the state may have changed | `vector::insert` in the middle |
| **Strong** | Program state is exactly as before the call (commit or rollback) | `vector::push_back`, `std::swap`-based assignment |
| **No-throw** | The function never throws | Destructors, `swap`, most moves of standard types, `size()` |

The levels are cumulative: strong implies basic. Only the strong guarantee requires the original
value to be preserved. "Basic" never means "leak or corrupt": a basic-guarantee function
that leaks is not exception-safe at all.

## Basic versus strong, measured

The program below inserts four elements whose copy constructor throws on the third copy, once with
element-by-element insertion and once with the copy-and-commit shape.

```cpp title="levels.cpp" showLineNumbers
#include <cstdio>
#include <stdexcept>
#include <vector>

struct Bomb {                       // the 3rd copy throws
    static inline int copies = 0;
    int v;
    explicit Bomb(int x) : v(x) {}
    Bomb(const Bomb& o) : v(o.v) { if (++copies == 3) throw std::runtime_error("copy failed"); }
    Bomb& operator=(const Bomb&) = default;     // keep clang -Wextra quiet (deprecated-copy)
};

class Bag {
    std::vector<Bomb> data_;
public:
    std::size_t size() const noexcept { return data_.size(); }
    void add_basic(const std::vector<Bomb>& xs) {      // prefix stays inserted
        for (const Bomb& b : xs) data_.push_back(b);
    }
    void add_strong(const std::vector<Bomb>& xs) {     // prepare on a copy, then commit
        std::vector<Bomb> tmp = data_;
        tmp.insert(tmp.end(), xs.begin(), xs.end());
        data_.swap(tmp);                               // noexcept
    }
};

int main() {
    std::vector<Bomb> xs;
    xs.reserve(4);
    for (int i = 0; i < 4; ++i) xs.emplace_back(i);

    Bag a;
    try { a.add_basic(xs); }
    catch (const std::exception& e) { std::printf("basic: %s, size=%zu\n", e.what(), a.size()); }

    Bomb::copies = 0;
    Bag b;
    try { b.add_strong(xs); }
    catch (const std::exception& e) { std::printf("strong: %s, size=%zu\n", e.what(), b.size()); }
}
```

```text
basic: copy failed, size=1
strong: copy failed, size=0
```

Same output on g++ 15.2 and clang++ 21.1 (libstdc++), `-std=c++20`, `-O0` and `-O2`. The exact size
in the basic case depends on when the vector reallocates, so it is a property of the implementation;
what the guarantee fixes is that `Bag` holds a *valid prefix* in one case and the original (empty)
state in the other.

## The shape of a strong-guarantee operation

<Diagram title="Prepare, then commit" caption="Everything that can throw happens before the commit; the commit cannot throw." accent="green">
  <DiagramRow>
    <DiagramNode title="1. Prepare">Copy or build the new state on the side. May throw; the original is untouched.</DiagramNode>
    <DiagramArrow direction="right" label="success" />
    <DiagramNode title="2. Commit" accent>Swap or move into place with a noexcept operation.</DiagramNode>
    <DiagramArrow direction="right" />
    <DiagramNode title="3. Cleanup">Old state is destroyed by the temporary's destructor.</DiagramNode>
  </DiagramRow>
</Diagram>

If step 1 throws, the temporary's destructor releases whatever it built and the object is unchanged.
This is why `swap` and move assignment need to be `noexcept`: a commit that can throw leaves the
object half-changed. It is also why `std::vector` reallocation uses `std::move_if_noexcept`: moving
elements one at a time into new storage with a throwing move constructor cannot be undone, so the
library copies instead unless the move is `noexcept` or the type is not copyable. The measured effect
is shown in
[Why move operations should be noexcept](../04-functions-and-call-mechanics/noexcept.md#move-semantics-and-noexcept).

The [copy-and-swap idiom](../13-idioms-and-design/05-copy-and-swap.md) packages this shape for
assignment, and [PIMPL](../13-idioms-and-design/02-pimpl.md) can make the commit a single pointer swap.

## Rollback when copying is too expensive

Copying the whole object may cost too much. Then save just enough to undo, and restore it in a
`catch`. The restore step itself must not throw.

```cpp showLineNumbers
// ...  (fragment: `names_` is a std::vector<std::string>, `index_` an int)
void rename_first(std::string s) {
    std::string old = std::move(names_.front());   // move-from: noexcept for std::string
    try {
        names_.front() = std::move(s);
        index_ = compute_index(names_);            // may throw
    } catch (...) {
        names_.front() = std::move(old);           // restore, no-throw move assignment
        throw;
    }
}
```

This is more fragile than prepare-and-commit: every added step needs its own undo. For several
resources, a small scope guard (run a lambda on scope exit unless dismissed) keeps rollback next to the
action; `scope_fail` and friends exist only as `std::experimental` facilities in the Library Fundamentals TS v3, not in the standard.

## Choosing a level

- **No-throw** for destructors, `swap`, move operations, deallocation, and simple observers. Mark them
  `noexcept`.
- **Strong** for operations callers will retry, or that must not corrupt shared state: assignment,
  bulk updates, transactions.
- **Basic** when strong costs a copy you cannot afford and callers can cope with a valid-but-changed
  object (inserting in the middle of a `vector` gives only the basic guarantee when element copy or move
  can throw).
- Document which one you provide. A reader cannot infer it from the signature.

Standard containers and smart pointers already give you these guarantees per operation, so building
on them and on [RAII](../13-idioms-and-design/01-raii.md) means few explicit `try`/`catch` blocks.

## Common mistakes

- **A "strong" function that mutates before the last throwing step.** The commit has to be the only
  mutation of the visible state.
- **Returning a large object by value from a mutator**, such as `T pop()`. If copying the result
  throws after the element was removed, the element is lost. This is why `std::stack::pop()` returns
  `void` and `top()` is separate.
- **Assuming self-assignment and aliasing cannot happen** in the prepare phase (`v.insert(v.end(),
  v.begin(), v.end())`).
- **Marking a function `noexcept` to "get" the no-throw guarantee** when it can still allocate: the
  program terminates instead of recovering.

## Key points

- Four levels: no guarantee, basic, strong, no-throw. Name the one you provide.
- Strong guarantee = do the throwing work on the side, commit with a non-throwing swap or move.
- Move assignment and `swap` must not throw, which is why containers only move on reallocation when the
  move is `noexcept`.
- Build on RAII and the standard containers; they supply most guarantees without extra code.
