---
id: asset-manager-and-soft-references
title: AssetManager, PrimaryAssetId, and async loading with StreamableManager
sidebar_label: AssetManager & soft references
sidebar_position: 5
tags: [ unreal-engine, ue5, c++, asset-manager, primary-asset-id, streamable-manager, async-loading, memory-budget ]
---

# AssetManager, PrimaryAssetId, and async loading with StreamableManager

This is the difference between a game that loads what it needs and a game that loads everything it
might ever need, all at once. Two projects with an identical amount of content can differ by 6x in peak
memory usage depending entirely on whether that content is registered with `UAssetManager` and streamed
in through `FStreamableManager`, or sitting behind `TObjectPtr` hard references from a handful of
always-loaded classes. This doc is the one to read closely if you only read one in this section.

## Why this matters

Every `TObjectPtr` hard reference chain (see
[Asset types and references](./asset-types-and-references.md)) that reaches from an always-loaded class
— your `AGameModeBase` subclass, your `UGameInstance`, a singleton data table — down to a specific
weapon skin, a rare enemy's skeletal mesh, or a cinematic's assets means that skin, mesh, or cinematic
is resident in memory for the entire session, whether or not the player ever encounters it. On a
project with a few hundred cosmetic variants or a large open world's worth of enemy types, that
difference is routinely the gap between a 2 GB memory footprint and a 12 GB one — and it's not a
performance bug you fix later, it's an architecture decision you either made on day one or are now
retrofitting across hundreds of assets.

`UAssetManager` and `FStreamableManager` are Epic's answer to "how do I load only what I need, when I
need it, without hand-rolling a loading system." AssetManager is the registry and policy layer
(what counts as a loadable unit, what rules govern it); StreamableManager is the actual async loader.

## Mental model

```mermaid
flowchart TD
    subgraph Registry["UAssetManager — registry + policy"]
        Scan["ScanPathsForPrimaryAssets /\nScanPrimaryAssetTypesFromConfig"]
        Scan --> Registered["Registered Primary Assets\n(FPrimaryAssetId -> FAssetData)"]
        Registered --> Rules["PrimaryAssetRules\n(Priority, ChunkId, CookRule)"]
    end

    subgraph Loader["FStreamableManager — actual loading"]
        Request["RequestAsyncLoad(FSoftObjectPath / TArray)"]
        Request --> Handle["FStreamableHandle"]
        Handle -->|OnComplete| Callback["FStreamableDelegate callback"]
        Handle --> Memory["Loaded UObject in memory"]
    end

    Registered -->|"LoadPrimaryAsset() / ChangeBundleStateForPrimaryAssets()"| Loader

    subgraph Bundles["Asset Bundles — partial loading of a Primary Asset's content"]
        PDA["UPrimaryDataAsset instance"]
        PDA -->|"meta=(AssetBundles=\"Client\")"| ClientBundle["Client bundle: UI icon, small preview mesh"]
        PDA -->|"meta=(AssetBundles=\"Game\")"| GameBundle["Game bundle: full mesh, textures, VFX"]
    end
```

A **Primary Asset** is a unit the AssetManager knows about by a stable `FPrimaryAssetId` and can
load/unload as a whole. A **Secondary Asset** — everything a Primary Asset references — loads
automatically as a side effect of loading the Primary Asset that references it, the same as any other
hard reference, *unless* that reference is soft and behind a bundle you haven't requested.
**Asset Bundles** are the mechanism that lets you load only *part* of a Primary Asset's soft-referenced
content — the small UI icon without the full-resolution mesh, for instance — which is what actually
produces the 2 GB vs 12 GB gap in practice.

## The mechanics

### Primary vs secondary assets, and FPrimaryAssetId

By default, only `UWorld` assets (levels) are Primary Assets. Everything else is Secondary — loaded
automatically whenever something that references it loads. To make your own class a Primary Asset
type, derive it from `UPrimaryDataAsset` (or override `GetPrimaryAssetId` on any `UObject` subclass) so
the AssetManager can address, load, and unload it independently by ID rather than only as a side effect
of something else loading it.

An `FPrimaryAssetId` is a pair: an `FPrimaryAssetType` (a logical category, usually named after the
base class) and an asset name (usually the asset's Content Browser name). `UPrimaryDataAsset`
automatically provides `GetPrimaryAssetId()` built from the asset's short name and native class — a
`UWeaponDefinition` asset named `"PlasmaRifle"` gets a Primary Asset ID of `WeaponDefinition:PlasmaRifle`
without you writing anything.

```cpp title="WeaponDefinition.h — a Primary Asset with bundled content"
UCLASS()
class MYGAME_API UWeaponDefinition : public UPrimaryDataAsset
{
    GENERATED_BODY()

public:
    // Always loaded whenever this Primary Asset loads at all: identity, gameplay stats.
    UPROPERTY(EditDefaultsOnly, Category = "Weapon")
    FText DisplayName;

    UPROPERTY(EditDefaultsOnly, Category = "Weapon")
    float BaseDamage = 10.f;

    // Bundled: only pulled into memory when the "UI" bundle is explicitly requested —
    // e.g. for an inventory screen that only needs icons, not full meshes.
    UPROPERTY(EditDefaultsOnly, Category = "Weapon|UI", meta = (AssetBundles = "UI"))
    TSoftObjectPtr<UTexture2D> InventoryIcon;

    // Bundled separately: only loaded when the weapon is actually equipped/spawned.
    UPROPERTY(EditDefaultsOnly, Category = "Weapon|Game", meta = (AssetBundles = "Game"))
    TSoftObjectPtr<USkeletalMesh> WeaponMesh;

    UPROPERTY(EditDefaultsOnly, Category = "Weapon|Game", meta = (AssetBundles = "Game"))
    TSoftObjectPtr<UNiagaraSystem> MuzzleFlashVFX;
};
```

The `meta = (AssetBundles = "...")` tag on a `TSoftObjectPtr`/`TSoftClassPtr` property is what feeds the
asset's `AssetBundleData` — updated automatically when the `UPrimaryDataAsset` is saved. This is the
mechanism, not an incidental detail: it's how a single data asset can represent "the inventory-list
version of this weapon" and "the fully-equipped, in-world version of this weapon" as two independently
loadable slices of the same object.

### Registering primary asset types

You tell the AssetManager which classes and directories to scan for Primary Assets in
`DefaultGame.ini`, under `[/Script/Engine.AssetManagerSettings]`:

```ini title="DefaultGame.ini"
[/Script/Engine.AssetManagerSettings]
+PrimaryAssetTypesToScan=(PrimaryAssetType="WeaponDefinition",AssetBaseClass="/Script/MyGame.WeaponDefinition",bHasBlueprintClasses=False,bIsEditorOnly=False,Directories=((Path="/Game/Weapons")),Rules=(Priority=0,ChunkId=-1,CookRule=Unknown))

+PrimaryAssetRules=(PrimaryAssetId="Map:/Game/Maps/Sanctuary",Rules=(Priority=-1,ChunkId=1,CookRule=Unknown))
+PrimaryAssetRules=(PrimaryAssetId="Map:/Game/Maps/ShooterEntry",Rules=(Priority=-1,ChunkId=0,CookRule=AlwaysCook))
```

`PrimaryAssetRules` overrides let you set `Priority` (load ordering / eviction priority when multiple
assets compete), `ChunkId` (which downloadable content chunk an asset cooks into — relevant for
chunked/patchable installs), and `CookRule` (e.g. force always-cook for a startup map's references, so
it can't be accidentally stripped by other rules).

If you need registration logic more dynamic than a static directory scan — for instance, primary assets
generated or organized at runtime rather than as static content — override `StartInitialLoading` in a
custom `UAssetManager` subclass and call `ScanPathsForPrimaryAssets` yourself; Epic's own guidance
recommends grouping assets of the same type into a single subfolder when you do this, for scan
efficiency. To point the engine at your custom subclass instead of the default `UAssetManager`, set
`AssetManagerClassName` in `DefaultEngine.ini`:

```ini title="DefaultEngine.ini"
[/Script/Engine.Engine]
AssetManagerClassName=/Script/MyGame.MyGameAssetManager
```

```cpp title="MyGameAssetManager.h"
UCLASS()
class MYGAME_API UMyGameAssetManager : public UAssetManager
{
    GENERATED_BODY()

protected:
    virtual void StartInitialLoading() override;
};
```

```cpp title="MyGameAssetManager.cpp"
void UMyGameAssetManager::StartInitialLoading()
{
    Super::StartInitialLoading();          // Runs ScanPrimaryAssetTypesFromConfig() for you
    // Add any programmatic ScanPathsForPrimaryAssets() calls here for dynamically-discovered types.
}
```

### Loading a Primary Asset, and loading only some of its bundles

```cpp title="Loading a weapon's UI bundle for an inventory screen"
void UInventoryWidget::ShowWeapon(FPrimaryAssetId WeaponId)
{
    UAssetManager& Manager = UAssetManager::Get();

    TArray<FName> BundlesToLoad = { TEXT("UI") };
    FStreamableDelegate OnLoaded = FStreamableDelegate::CreateUObject(this, &UInventoryWidget::OnWeaponUILoaded, WeaponId);

    Manager.LoadPrimaryAsset(WeaponId, BundlesToLoad, OnLoaded);
}

void UInventoryWidget::OnWeaponUILoaded(FPrimaryAssetId WeaponId)
{
    if (UWeaponDefinition* Weapon = Cast<UWeaponDefinition>(UAssetManager::Get().GetPrimaryAssetObject(WeaponId)))
    {
        // Only InventoryIcon is guaranteed resolvable here — WeaponMesh's "Game" bundle was never requested.
        SetIconTexture(Weapon->InventoryIcon.Get());
    }
}
```

```cpp title="Later: player actually equips the weapon — load the Game bundle too"
void AMyCharacter::EquipWeapon(FPrimaryAssetId WeaponId)
{
    TArray<FName> BundlesToLoad = { TEXT("Game") };
    UAssetManager::Get().LoadPrimaryAsset(WeaponId, BundlesToLoad,
        FStreamableDelegate::CreateUObject(this, &AMyCharacter::OnWeaponGameAssetsLoaded, WeaponId));
}
```

`ChangeBundleStateForPrimaryAssets` (and its async counterpart) is the API for updating which bundles
are loaded for a *set* of already-registered primary assets at once — useful for "everything on this
loot table should now have its Game bundle loaded" style bulk transitions, rather than looping
`LoadPrimaryAsset` calls per asset.

When you're done with content — the player un-equips, backs out of the inventory screen — call
`UAssetManager::Get().UnloadPrimaryAsset(WeaponId)` (or the bundle-specific unload) so the loaded
assets become eligible for garbage collection again. Loading without a matching unload is how a
StreamableManager-based system still leaks memory over a long session; the API doesn't unload for you.

### Async loading assets that aren't Primary Assets

Not everything needs the full Primary Asset/bundle machinery — sometimes you just have a
`TSoftObjectPtr` on a regular `UObject` and want it loaded asynchronously. That's what
`FStreamableManager::RequestAsyncLoad` is for directly, without going through Primary Asset
registration at all:

```cpp title="Direct StreamableManager usage for a one-off soft reference"
void AWeaponSpawner::SpawnRareVariantAsync(UWeaponDefinition* Definition)
{
    if (Definition->RareVariantMesh.IsNull())
    {
        return;
    }

    FStreamableManager& Streamable = UAssetManager::Get().GetStreamableManager();

    FSoftObjectPath MeshPath = Definition->RareVariantMesh.ToSoftObjectPath();
    Streamable.RequestAsyncLoad(
        MeshPath,
        FStreamableDelegate::CreateUObject(this, &AWeaponSpawner::OnRareVariantLoaded)
    );
}

void AWeaponSpawner::OnRareVariantLoaded()
{
    // Re-resolve now that the package has loaded; the TSoftObjectPtr's cached weak pointer is valid again.
    if (UStaticMesh* Mesh = RareVariantMesh.Get())
    {
        MeshComponent->SetStaticMesh(Mesh);
    }
}
```

`RequestAsyncLoad` returns a `TSharedPtr<FStreamableHandle>` you should generally hold onto (as a member,
not a throwaway local) for the duration you care about the load:

- `Handle->IsActive()` — still tracked, not canceled/released.
- `Handle->HasLoadCompleted()` — finished (assets that failed to load are still null, check for that
  separately rather than assuming completion means success).
- `Handle->WaitUntilComplete(Timeout, bStartStalledHandles)` — blocks synchronously; use only where a
  stall is acceptable (a loading screen), same caveat as `TSoftObjectPtr::LoadSynchronous`.
- `Handle->ReleaseHandle()` — releases the handle's hold; combined with no other references, this is
  what lets the loaded assets become collectible.

For simply loading a whole top-level asset and its immediate sub-objects with no need for a persistent
handle, `LoadAssetAsync` (from `CoreUObject`, non-blocking, built on `LoadPackageAsync` internally) is a
lighter-weight alternative; for a batch of several soft paths at once, `UAssetManager::LoadAssetList`
loads a list of non-Primary assets through the manager's shared streamable manager in one call.

### Dynamically-registered Primary Assets

Some content isn't known at cook time — dynamically spawned/generated data. The AssetManager supports
registering these too: `ExtractSoftObjectPaths` walks a `UStruct` instance and collects the soft
references it finds (for building bundle data on the fly), and `RecursivelyExpandBundleData` expands a
dynamic asset's bundle dependencies, registers it, and kicks off loading — the mechanism behind
"Registering and Loading Dynamically-Created Primary Assets" for content that doesn't live as static
`.uasset` files.

## Gotchas

:::warning Bundles only gate *soft* references
Tagging a `TObjectPtr` hard reference with `meta = (AssetBundles = "Game")` does nothing — hard
references are not bundle-gated, they load unconditionally the instant the owning object loads. Bundles
only defer properties that are already `TSoftObjectPtr`/`TSoftClassPtr`. If a "Game"-bundled property
still shows up loaded when only the "UI" bundle was requested, check whether it's actually declared as
a soft pointer in the header.
:::

:::caution `GetPrimaryAssetObject` returns null until the relevant bundle is loaded
Calling `GetPrimaryAssetObject(WeaponId)` before any `LoadPrimaryAsset` call for that ID returns the
Primary Asset itself only if something else already caused it to load — its bundled soft references
are not resolved just because the data asset object exists. Always request the bundle you need and load
off the completion delegate rather than assuming the object graph is fully populated on first access.
:::

:::warning Forgetting to unload leaks exactly like forgetting to `delete`
`LoadPrimaryAsset`/`ChangeBundleStateForPrimaryAssets` increment a reference the AssetManager holds
against the loaded content. There's no automatic timeout or scope-based release — if your code path
that loads a bundle doesn't have a matching unload on the corresponding transition (level exit, weapon
unequip, screen close), that memory stays resident for the rest of the session, same failure mode as a
missed `TSharedPtr` release.
:::

:::caution `RequestAsyncLoad` callbacks can fire on a differently-ordered path than you assume
Multiple in-flight `RequestAsyncLoad` calls for overlapping soft paths do not guarantee callback
ordering matches request ordering, and a released/canceled handle's delegate may never fire. Don't
build gameplay logic that depends on load-completion order across separate handles; if ordering
matters, load as one batch (`LoadAssetList` / a single `RequestAsyncLoad` with the full array) instead
of separate sequential calls.
:::

:::note
`FStreamableDownloadParams` and the download-specific fields (`bInstallSoftReferences`, `CachePin`,
`Priority`) are marked experimental in the engine source at the time these docs were consulted — treat
that download-oriented surface (relevant mainly to platforms with installable/downloadable content
chunks) as subject to change, separate from the stable core `RequestAsyncLoad`/`FStreamableHandle` API
described above.
:::

## See also

- [Asset types and references](./asset-types-and-references.md) — the `TObjectPtr` vs `TSoftObjectPtr`
  distinction that AssetManager and bundles build on top of.
- [Asset naming and organization](./asset-naming-and-organization.md) — folder conventions that keep
  `ScanPathsForPrimaryAssets` and directory-based scanning cheap and unambiguous.
- [Cooking and the derived data cache](./cooking-and-derived-data-cache.md) — how `ChunkId`/`CookRule`
  primary asset rules interact with what actually gets cooked into a build.
- [Subsystems](../02-cpp-in-unreal/subsystems.md) — where a game-specific loading-screen manager built
  on top of StreamableManager typically lives.
- [Epic — Asset Management in Unreal Engine](https://dev.epicgames.com/documentation/unreal-engine/asset-management-in-unreal-engine)
