---
id: containers
title: TArray, TMap, and TSet
sidebar_label: Containers
sidebar_position: 4
tags: [ unreal-engine, ue5, c++, tarray, tmap, tset, containers ]
---

# TArray, TMap, and TSet

Unreal ships its own container library instead of using `std::vector`, `std::unordered_map`, and
`std::unordered_set`. The API differs enough from the STL that muscle memory misleads you — `Num()`
not `size()`, `Add()` not `push_back()`, iteration order guarantees that don't match what you'd expect
from a hash map — and these are the containers you'll use in nearly every function you write, so
getting comfortable with their actual behaviour (not their STL-shaped assumptions) pays off constantly.

## Why this matters

`UPROPERTY`-reflected containers are how Unreal exposes arrays, maps, and sets to the Details panel
and to Blueprint. Using `std::vector` in a `UPROPERTY` member simply doesn't work — the reflection
system doesn't know about it. Beyond reflection, Unreal's containers integrate with the engine's own
allocators and memory tracking, which is why the engine's own code — and consequently most examples
you'll read — uses them everywhere, including in code that never touches Blueprint or the editor.

## Mental model

- **`TArray<T>`** — a contiguous, dynamically-growing array. Same mental model as `std::vector`:
  amortized O(1) append, O(n) insert/remove in the middle, random access by index.
- **`TMap<K, V>`** — a hash-keyed associative container, key to value. Comparable to
  `std::unordered_map`, but unordered *and* the iteration order is not contractually stable across
  insert/remove.
- **`TSet<T>`** — a hash-keyed container of unique elements, comparable to `std::unordered_set`.

`TMap` and `TSet` both require their key/element type to be hashable via a `GetTypeHash` overload —
Unreal's containers rely on free-function `GetTypeHash`, not a `std::hash` specialization, so a custom
key type needs its own `GetTypeHash` overload before it can go in a `TMap` or `TSet`.

## The mechanics

### TArray

```cpp title="TArray basics"
TArray<AActor*> NearbyActors;
NearbyActors.Add(SomeActor);
NearbyActors.Reserve(64);          // pre-size to avoid reallocation churn

for (AActor* Actor : NearbyActors)
{
    // ranged-for works exactly as you'd expect
}

NearbyActors.RemoveSwap(SomeActor); // O(1) removal, doesn't preserve order
```

As a `UPROPERTY`:

```cpp title="Reflected array member"
UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Loadout")
TArray<TSubclassOf<AWeapon>> AvailableWeapons;
```

`TArray` uses a configurable allocator (`FDefaultAllocator` by default) — the same template accepts a
custom allocator for fixed-capacity or inline-storage variants, which is how the engine avoids heap
allocation for small, short-lived arrays in hot code paths.

### TMap

```cpp title="TMap basics"
TMap<FName, int32> ScoreByPlayer;
ScoreByPlayer.Add(TEXT("Player1"), 100);

if (int32* Score = ScoreByPlayer.Find(PlayerName))
{
    *Score += 10;
}
```

`Find` returns a pointer (`nullptr` if absent) rather than throwing or default-constructing on lookup
— there's no `operator[]`-inserts-a-default-value trap like `std::map`.

### TSet

```cpp title="TSet basics"
TSet<AActor*> VisitedActors;
VisitedActors.Add(Actor);

if (VisitedActors.Contains(Actor))
{
    // already visited
}
```

### Move semantics

`TArray`, `TMap`, `TSet`, and `FString` all support move construction and move assignment, and the
engine leans on this — returning a `TArray` by value from a function is idiomatic Unreal C++, not a
performance smell, because the move happens instead of a copy. Use `MoveTemp(x)` (Unreal's equivalent
of `std::move`) to force a move where the compiler can't infer one, such as moving into a container
element.

```cpp title="Explicit move"
TArray<FString> Names = BuildNames();
Cache.Add(MoveTemp(Names));   // moves instead of copying the array
```

## Gotchas

:::warning[A custom struct in a TMap/TSet needs GetTypeHash]
Forgetting to define `GetTypeHash` for a struct used as a `TMap` key or `TSet` element is a compile
error, not a silent bug — but the error message points at container internals, not your struct, which
makes it look scarier than it is.
:::

:::warning[TArray iterators invalidate on reallocation]
Adding to a `TArray` while holding a pointer or iterator into it (including a range-based `for` over
the same array) is the same class of bug as with `std::vector` — the backing buffer can move.
:::

:::caution[TMap/TSet iteration order is not insertion order]
Don't rely on it for anything user-visible or replicated; if order matters, use a `TArray` or sort
explicitly.
:::

## See also

- [Strings and text](./strings-and-text.md) — `FString` is itself built on `TArray<TCHAR>`.
- [UObject and reflection](./uobject-and-reflection.md) — why `UPROPERTY` containers must be Unreal's
  own types, not STL equivalents.
- [Unreal C++ vs standard C++](./unreal-cpp-vs-standard-cpp.md) — the broader case for and against
  reaching for the STL instead.
- [Epic — Epic C++ Coding Standard for Unreal Engine](https://dev.epicgames.com/documentation/unreal-engine/epic-cplusplus-coding-standard-for-unreal-engine)
