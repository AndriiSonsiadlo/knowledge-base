---
id: policy-based-design
title: Policy-Based Design
sidebar_label: Policy-Based Design
sidebar_position: 7
tags: [c++, policy-based-design, templates, concepts, generic-programming]
---

# Policy-Based Design

**Policy-based design** builds a class from a few independent behaviors, each chosen by a template
parameter. The class (the **host**) implements the algorithm; each **policy** is a small type that
supplies one decision: how to check bounds, how to lock, how to allocate, how to compare. Because the
choice is made at compile time, an unused or empty policy costs nothing, and every combination is
its own concrete type.

It is the compile-time cousin of the Strategy pattern. The comparison with run-time and CRTP-based
polymorphism is on
[Dynamic vs Static Polymorphism](../07-classes-and-oop/dynamic-vs-static-polymorphism.md).

**Prerequisites:** [Class Templates](../08-templates-and-metaprogramming/class-templates.md),
[Concepts and requires](../08-templates-and-metaprogramming/concepts-and-requires.md).

## The problem

A container that might be checked or unchecked, locked or not, is awkward to write as one class.
Flags and `if`s add run-time cost and code to every instance. Inheritance hierarchies explode:
`CheckedArray`, `UncheckedArray`, `LockedCheckedArray`, and so on, one class per combination.
Policies make each decision a separate, reusable piece and let the host combine them.

## The idiom

```cpp title="policy.cpp" showLineNumbers
#include <concepts>
#include <cstddef>
#include <cstdio>
#include <mutex>
#include <stdexcept>
#include <thread>
#include <vector>

// --- Bounds policies: static functions, no state -------------------------------------
struct Unchecked {
    static void check(std::size_t, std::size_t) noexcept {}
};
struct Throwing {
    static void check(std::size_t i, std::size_t n) {
        if (i >= n) throw std::out_of_range("index out of range");
    }
};

template <typename P>
concept BoundsPolicy = requires(std::size_t i, std::size_t n) { P::check(i, n); };

template <typename T, std::size_t N, BoundsPolicy Bounds = Throwing>
class Array {
public:
    T& operator[](std::size_t i) { Bounds::check(i, N); return data_[i]; }
    const T& operator[](std::size_t i) const { Bounds::check(i, N); return data_[i]; }
private:
    T data_[N]{};
};

// --- Locking policies: may carry state, so the host stores one ------------------------
struct NoLock {
    void lock() noexcept {}
    void unlock() noexcept {}
};

template <typename L>
concept Lockable = requires(L l) { l.lock(); l.unlock(); };

template <Lockable Lock = std::mutex>
class Counter {
public:
    void increment() {
        std::lock_guard<Lock> g(lock_);
        ++value_;
    }
    long value() const { return value_; }
private:
    [[no_unique_address]] mutable Lock lock_;   // empty policies take no space
    long value_ = 0;
};

static_assert(sizeof(Counter<NoLock>) == sizeof(long));    // holds on Itanium ABI compilers tested

int main() {
    Array<int, 3> safe;
    try { safe[3] = 1; } catch (const std::out_of_range& e) { std::printf("caught: %s\n", e.what()); }

    Array<int, 3, Unchecked> fast;
    fast[2] = 7;
    std::printf("%d\n", fast[2]);

    Counter<std::mutex> shared;                 // safe to share between threads
    std::vector<std::thread> ts;
    for (int t = 0; t < 4; ++t)
        ts.emplace_back([&] { for (int i = 0; i < 1000; ++i) shared.increment(); });
    for (auto& t : ts) t.join();
    std::printf("%ld\n", shared.value());

    Counter<NoLock> local;                      // single-threaded: no locking cost, no mutex member
    for (int i = 0; i < 1000; ++i) local.increment();
    std::printf("%ld\n", local.value());
}
```

Output (g++ 15 and clang++ 21, `-std=c++20 -Wall -Wextra -pthread`, `-O0` and `-O2` identical):

```text
caught: index out of range
7
4000
1000
```

The `static_assert` on `sizeof` held with both compilers on x86-64 Linux (Itanium C++ ABI);
`[[no_unique_address]]` is an optimization the compiler may apply, not a guarantee of the standard, and
MSVC ignores the attribute (it provides `[[msvc::no_unique_address]]`).

<Diagram title="Host plus policies" caption="Array and Counter fix the algorithm; the policies supply the variable decision. Each combination is a separate type." accent="blue">
  <DiagramRow>
    <DiagramNode icon="settings" title="Host" accent>Array&lt;T, N, Bounds&gt;<br/>Counter&lt;Lock&gt;</DiagramNode>
    <DiagramNode icon="shield-check" title="Policy A">Throwing, std::mutex</DiagramNode>
    <DiagramNode icon="zap" title="Policy B">Unchecked, NoLock</DiagramNode>
  </DiagramRow>
</Diagram>

Parts of the idiom:

- **A policy has an interface, not a base class.** `Bounds::check(i, n)` and `lock()/unlock()` are the
  contracts. Any type that provides them works: `std::mutex` is a lock policy without knowing it.
  A concept (`BoundsPolicy`, `Lockable`) states the contract and turns a wrong policy into a short
  error at the host instead of a long one inside it.
- **Stateless policies use static functions** (`Bounds::check`), so the host stores nothing.
  **Stateful policies are stored as members** (`lock_`). Marking the member `[[no_unique_address]]`
  (C++20) lets an empty policy share storage with its neighbors.
- **Defaults** (`Bounds = Throwing`) make the common case a one-word type, `Array<int, 3>`.
- `Array<int, 3, Unchecked>` is a different type from `Array<int, 3>`: they cannot be assigned to
  each other or mixed in a container, and cost nothing at run time for being different.

### Policy as base class or as member

Older code inherits from policies (often privately) to get the empty base optimization and to let
the policy add members to the host's interface. In C++20, a `[[no_unique_address]]` member gives the same
space saving with composition and no name-lookup surprises, so prefer it. If you do inherit
from a policy, give the policy a `protected`, non-virtual destructor so no one can delete a host
through a policy pointer. Inheriting is still the right choice when the policy must contribute
public members, which a member cannot do; that mixin form is the [CRTP](./03-crtp.md) variant of the same idea.

### Template-template policies

A policy that is itself a template over the host's element type (`template <typename> class Check`)
can be passed as a template-template parameter, so the host writes `Check<T>`. This was common in early
policy libraries. It couples the host to a particular template shape: a policy with an extra
parameter does not fit. Passing the already-instantiated type (`Check<T>`) or a policy that takes
`T` in its member functions (as above) is more flexible.

## Policies in the standard library

The idiom is everywhere, mostly under other names:

| Class | Policy parameter | Decision |
|---|---|---|
| `std::vector<T, Alloc>`, `std::map<K, V, Cmp, Alloc>` | allocator ([Allocators](../09-standard-library/allocators.md)), comparator | memory source, ordering |
| `std::unique_ptr<T, D>` | deleter ([Custom Deleters](../06-pointers-references-and-smart-pointers/custom-deleters.md)) | how to release; stateless deleters add no size |
| `std::basic_string<C, Traits, Alloc>` | `char_traits` | character comparison and copying |
| `std::unordered_map<K, V, Hash, Eq, Alloc>` | hash, equality | key identity |
| `std::priority_queue<T, C, Cmp>` | container, comparator | storage and priority |

## Policies versus the alternatives

| Approach | When chosen | Switch at run time? | Cost |
|---|---|---|---|
| Policy (template parameter) | compile time | no | none for the choice itself; one instantiation per combination |
| Virtual strategy object | run time | yes | pointer, indirect call, usually allocation |
| Callable member (`std::function`) | run time | yes | [type-erased](./06-type-erasure.md) call |
| `if constexpr` on a flag | compile time | no | fine for one binary choice, not for open extension |
| Runtime flag | run time | yes | a branch per use and a field per object |

Pick a policy when the decision is known per use site and never changes during the program, when
you want zero overhead for the unused option, and when users should be able to add their own
policies. Pick a run-time strategy when the behavior must be chosen from configuration or changed
while the object lives.

## Pitfalls

- **Type explosion.** Each combination is a distinct type with its own code. Many policies with many
  values bloat compile time and the binary, and generic code that takes the host must be a template too.
- **Long error messages and type names.** Concepts on policies are the mitigation; a `using` alias
  gives the common configurations a name.
- **Policies that need to know the host.** If a policy must call back into the host, it becomes
  [CRTP](./03-crtp.md), with that pattern's incomplete-type rules.
- **Orthogonality is on you.** Policies that depend on each other (a lock policy that assumes a particular
  storage policy) are not independent; fold them into one policy or give the host a
  combined one.
- **Thread safety is the policy's, not the host's.** In the example, `Counter::value()` does not lock,
  and is only safe to call once the writers are finished; a locked policy protects the operations
  that use it, not the whole class.

## Related

- [CRTP](./03-crtp.md): policies that need the host type, and mixins.
- [Dynamic vs Static Polymorphism](../07-classes-and-oop/dynamic-vs-static-polymorphism.md): choosing between compile-time and run-time selection.
- [Type Erasure](./06-type-erasure.md): when the policy must change at run time without a hierarchy.
- [Concepts and requires](../08-templates-and-metaprogramming/concepts-and-requires.md): stating policy requirements.

## References

- [cppreference: `[[no_unique_address]]`](https://en.cppreference.com/w/cpp/language/attributes/no_unique_address)
- [cppreference: Concepts library](https://en.cppreference.com/w/cpp/concepts)
- [cppreference: `std::char_traits`](https://en.cppreference.com/w/cpp/string/char_traits)
