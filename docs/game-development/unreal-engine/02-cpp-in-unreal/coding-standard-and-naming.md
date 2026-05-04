---
id: coding-standard-and-naming
title: Epic's coding standard and naming rules
sidebar_label: Coding standard & naming
sidebar_position: 10
tags: [ unreal-engine, ue5, c++, coding-standard, naming ]
---

# Epic's coding standard and naming rules

Unreal C++ has a house style, and it's more than cosmetic: the type-prefix convention (`U`, `A`, `F`,
`E`, and the rest) is load-bearing information — you can tell whether a type is a `UObject`, an
`AActor`, a plain struct, or an enum from its name alone, before opening the header. Departing from it
doesn't just look wrong in review; it removes information every other Unreal developer (and some
tooling) expects to read off the type name directly.

## Why this matters

The prefix convention substitutes for information C++ doesn't otherwise surface at a glance — is this
pointer GC-tracked, is this class Blueprint-subclassable, is this an interface I need to inherit the
`I`-half of. A codebase that follows the convention lets you answer those questions by reading a
variable declaration; one that doesn't forces a header lookup every time.

## Mental model

Every reflected (and most non-reflected) type gets a single-letter prefix that encodes its role:

| Prefix | Meaning | Example |
|---|---|---|
| `U` | `UObject`-derived class | `UHealthComponent` |
| `A` | `AActor`-derived class | `AEnemyCharacter` |
| `F` | Plain struct/class (most non-`UObject` types) | `FDamageInfo` |
| `E` | Enum | `EMatchState` |
| `S` | `SWidget`-derived (Slate) class | `SCombatHUD` |
| `I` | Abstract interface | `IDamageableInterface` |
| `T` | Template class | `TArray`, `TSharedPtr` |
| `C` | Concept-alike struct types | (rare in gameplay code) |
| `b` (variable prefix, not a class prefix) | Boolean | `bIsAlive` |

Most non-`UObject` classes default to `F`, even ones that aren't strictly "plain data" — the
convention is about what the type *is*, not about giving every non-`UObject` type its own unique
letter.

## The mechanics

### Applying the prefixes

```cpp title="Prefix usage together"
UENUM(BlueprintType)
enum class EMatchState : uint8
{
    Warmup,
    InProgress
};

USTRUCT(BlueprintType)
struct FDamageInfo
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere)
    float Amount = 0.0f;
};

UCLASS()
class MYGAME_API AEnemyCharacter : public ACharacter, public IDamageableInterface
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, Category = "Health")
    bool bIsElite = false;

private:
    UPROPERTY()
    EMatchState CurrentState = EMatchState::Warmup;
};
```

### TEXT() and avoiding redundant work in loops

Epic's style guide calls out two related habits: always wrap string literals in `TEXT()` when
constructing `FString`s, to avoid an undesirable conversion cost on every use of the literal; and hoist
common subexpressions — including `FName` construction from a literal — out of loops and into
`static` locals, since building an `FName` from a string is a string-table lookup, not a free
operation.

```cpp title="Hoisting FName construction"
void TickHandler()
{
    static const FName HandlerTag(TEXT("DamageTick")); // built once
    // ... use HandlerTag every tick without re-building it
}
```

### File naming

Class headers are named after the class with the type prefix dropped — `AEnemyCharacter` lives in
`EnemyCharacter.h`, not `AEnemyCharacter.h`. This matches Unreal's own engine source layout
(`Actor.h` for `AActor`, `Object.h` for `UObject`).

### Preferring the standard library where it's better

The coding standard is explicit that Unreal's historical avoidance of `std` was a product of its era
— early C++ standard libraries were inconsistent across platforms, and Unreal needed tighter control
over allocation. Where the modern standard library offers a genuinely better result than Unreal's own
type, Epic's own guidance says to prefer it, provided you don't mix idioms within the same API.

## Gotchas

:::warning[A missing type prefix isn't a compile error, just a readability regression]
Nothing stops you from naming a `UObject`-derived class `HealthComponent` instead of
`UHealthComponent`. It compiles fine and immediately reads as inconsistent with the rest of the
codebase and the engine's own source.
:::

:::caution[Don't mix Unreal idioms and STL idioms in the same API surface]
Taking a `TArray` parameter and internally converting to `std::vector` (or vice versa) inside one
function is exactly the mixing Epic's own guidance warns against — pick one per API boundary.
:::

:::note
The full Epic coding standard covers a great deal more than naming — brace style, header organization,
`const`-correctness rules, and more. This page covers the naming and prefix conventions specifically;
consult the full standard document for the rest before writing engine-contribution-quality code.
:::

## See also

- [UObject and reflection](./uobject-and-reflection.md) — the macros (`UCLASS`, `USTRUCT`, `UENUM`)
  the prefix convention exists to support.
- [Strings and text](./strings-and-text.md) — the `TEXT()`/`FName` guidance referenced above, in full.
- [Unreal C++ vs standard C++](./unreal-cpp-vs-standard-cpp.md) — the broader std-vs-Unreal-types
  trade-off this page touches on.
- [Epic — Epic C++ Coding Standard for Unreal Engine](https://dev.epicgames.com/documentation/unreal-engine/epic-cplusplus-coding-standard-for-unreal-engine)
