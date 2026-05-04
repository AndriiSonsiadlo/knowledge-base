---
id: uobject-and-reflection
title: UObject and the reflection system
sidebar_label: UObject & reflection
sidebar_position: 1
tags: [ unreal-engine, ue5, c++, uobject, reflection, uht ]
---

# UObject and the reflection system

Every gameplay class you write in Unreal — `AActor`, `UActorComponent`, your own `UMyGameSubsystem`
— ultimately derives from `UObject`. `UObject` isn't just a base class for shared behaviour; it's the
hook into a second type system layered on top of C++'s own. Miss that, and you'll fight the engine:
properties that silently don't serialize, Blueprint nodes that never appear, objects that vanish
under garbage collection for no visible reason. All of that traces back to whether a type and its
members are *reflected*.

## Why this matters

Standard C++ has no runtime type information beyond what RTTI grudgingly offers, and no built-in way
to ask "what fields does this class have" or "call this method by name." Unreal needs both — for the
Blueprint visual scripting bridge, for the property editor in the Details panel, for automatic
serialization to disk and over the network, and for garbage collection to know which pointers are
live references. The reflection system is what supplies that missing runtime metadata, and it is
opt-in: a class, struct, enum, property, or function only exists to the engine's tools if you mark it.

## Mental model: two type systems, one build step

C++ compiles your class as an ordinary type. Separately, **Unreal Header Tool (UHT)** parses the same
header, looking specifically for `UCLASS()`, `USTRUCT()`, `UENUM()`, `UPROPERTY()`, and `UFUNCTION()`
macros. For everything it finds, UHT generates additional C++ — a `.generated.h` file — containing the
plumbing that registers the type with Unreal's reflection database at startup: an `FProperty` per
reflected member, a `UFunction` per reflected method, and a `UClass` object that describes the type
itself.

```mermaid
flowchart LR
    H["MyActor.h<br/>(UCLASS / UPROPERTY / UFUNCTION)"] --> UHT[Unreal Header Tool]
    UHT --> G["MyActor.generated.h"]
    H --> CPP[Your compiler]
    G --> CPP
    CPP --> BIN[Compiled binary]
    BIN --> RT["Reflection database<br/>(UClass / FProperty / UFunction)"]
    RT --> Uses["Blueprint · Details panel ·<br/>Serialization · GC · Replication"]
```

This is why every reflected header must `#include "MyActor.generated.h"` as its **last** include, and
why `GENERATED_BODY()` has to be the first line inside the class body — that macro expands to code UHT
generated specifically for that class, in that position.

## The mechanics

### UCLASS — reflecting a class

Any `UObject`-derived class you want the engine to know about needs `UCLASS()` above it and
`GENERATED_BODY()` inside it:

```cpp title="MyGameSubsystem.h"
UCLASS()
class MYGAME_API UMyGameSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float RespawnDelaySeconds = 3.0f;
};
```

`UCLASS` itself takes class specifiers — `Abstract` (no instances), `Blueprintable` (can be
subclassed in Blueprint), `NotBlueprintable`, and others — that control how the type behaves in the
editor and reflection database.

### USTRUCT — reflecting a data-only struct

Structs get the same treatment through `USTRUCT()` and `GENERATED_BODY()`, but they are value types,
not `UObject`s — no reflection-driven lifetime, no GC tracking of the struct itself (its `UPROPERTY`
members are still tracked if the struct is embedded in something GC tracks).

```cpp title="FDamageInfo"
USTRUCT(BlueprintType)
struct FDamageInfo
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Amount = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TSubclassOf<UDamageType> DamageType;
};
```

### UENUM — reflecting an enum

```cpp title="EMatchState"
UENUM(BlueprintType)
enum class EMatchState : uint8
{
    Warmup,
    InProgress,
    PostMatch
};
```

`enum class : uint8` is the expected form for a Blueprint-exposed enum; UHT reflects each enumerator
so it appears as a dropdown option in the editor.

### UPROPERTY — reflecting a member

`UPROPERTY` is what makes a member visible to serialization, the Details panel, Blueprint, and garbage
collection. Specifiers control exposure and behaviour:

| Specifier | Effect |
|---|---|
| `EditAnywhere` / `EditDefaultsOnly` / `EditInstanceOnly` | Editable in the Details panel (and where) |
| `BlueprintReadWrite` / `BlueprintReadOnly` | Exposed to Blueprint graphs |
| `VisibleAnywhere` | Shown but not editable |
| `Category = "..."` | Grouping in the Details panel |
| `meta = (ClampMin = "0.0"))` | Editor-only metadata — never read by game logic |

A `UPROPERTY` pointer to a `UObject` also becomes a **strong garbage-collection reference** — see
[Garbage collection](./garbage-collection.md) for why that matters more than it sounds like it should.

### UFUNCTION — reflecting a method

```cpp title="Exposing a method"
UFUNCTION(BlueprintCallable, Category = "Match")
void StartNextRound();
```

`UFUNCTION` registers a `UFunction` for the method, letting it be called from Blueprint
(`BlueprintCallable`), overridden in Blueprint (`BlueprintImplementableEvent`,
`BlueprintNativeEvent`), or bound as a dynamic delegate target — a dynamic delegate can only bind to a
`UFUNCTION`, never a plain C++ method. See
[Blueprint interop](../04-blueprint-interop/exposing-cpp-to-blueprint.md) for the full specifier set.

## Gotchas

:::warning[GENERATED_BODY() position and the last-include rule]
`GENERATED_BODY()` must be the first line in the class/struct body, and `#include "ClassName.generated.h"`
must be the last include in the header. Violating either produces UHT errors that look nothing like
the actual mistake.
:::

:::warning[meta specifiers are editor-only]
Metadata (`meta = (...)`) is stripped from cooked builds and is never visible to running game code.
Don't read it back at runtime — it isn't there.
:::

:::caution[A non-reflected member is invisible to the engine, silently]
A plain `float Speed;` with no `UPROPERTY` compiles fine — and then never serializes, never shows in
the Details panel, and is never GC-tracked if it's a pointer. There's no warning; it just behaves like
ordinary C++, which is exactly the trap, because everything around it doesn't.
:::

## See also

- [Garbage collection](./garbage-collection.md) — why `UPROPERTY` pointers are the difference between
  a live object and a dangling one.
- [Interfaces](./interfaces.md) — the `UINTERFACE`/`IInterface` pair, reflection's other two-class
  pattern.
- [Coding standard and naming](./coding-standard-and-naming.md) — the `U`/`A`/`F`/`E` prefixes this
  system relies on.
- [Exposing C++ to Blueprint](../04-blueprint-interop/exposing-cpp-to-blueprint.md) — the specifiers
  that matter most for the Blueprint bridge.
- [Epic — Reflection System in Unreal Engine](https://dev.epicgames.com/documentation/unreal-engine/reflection-system-in-unreal-engine)

