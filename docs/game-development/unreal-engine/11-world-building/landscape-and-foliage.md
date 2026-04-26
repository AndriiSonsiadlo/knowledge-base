---
id: landscape-and-foliage
title: Landscape and foliage
sidebar_label: Landscape & Foliage
sidebar_position: 3
tags: [ unreal-engine, ue5, c++, landscape, foliage, terrain ]
---

# Landscape and foliage

## Why this matters

Landscape and foliage look like separate editor modes but they're the same performance conversation: both
exist to put enormous amounts of visual detail on screen without paying per-object cost for it. A
landscape is one deformable heightfield rendered efficiently at scale; foliage is thousands of repeated
meshes rendered as instance batches instead of individual actors. Get either wrong — too many landscape
components, foliage instanced per-actor instead of batched — and you've built a scene that looks fine in
the viewport and chokes the frame budget the moment it's built for shipping.

## Mental model

A landscape isn't one mesh — it's a grid of `ALandscapeProxy` components (in World Partition maps,
`ALandscapeStreamingProxy`), each covering a section of the heightfield so the engine can cull, LOD, and
stream them independently. Foliage similarly isn't "many actors" — it's `UFoliageType` assets, each
describing a mesh and its scatter rules, whose instances are batched into
`UHierarchicalInstancedStaticMeshComponent`s (HISM) so the renderer draws one batched call per foliage
type per landscape section instead of one draw call per tree.

## The mechanics

### Sculpting and components

Landscape sculpting (raise/lower, smooth, erosion tools, and importing a heightmap) edits the heightfield
data stored per landscape component. Component size and section size are set at landscape creation time
and are expensive to change afterward — they determine how the terrain is subdivided for LOD and
streaming, the same tradeoff World Partition's cell size makes for actors: coarser components mean fewer
streaming units and coarser LOD transitions; finer components mean tighter culling at the cost of more
components to manage.

### Landscape materials and layers

A landscape's surface look comes from **layers** — named paint channels (grass, rock, snow, mud) each
backed by a `ULandscapeLayerInfoObject` asset, painted with weight per vertex. The landscape material
reads those weights through a `LandscapeLayerBlend` material node: add a layer entry per paint channel,
give it a blend type, and feed it a texture sample.

- **LB Alpha Blend** — blends by the painted weight directly, good for most surface transitions.
- **LB Height Blend** — blends using the input texture's alpha as a height mask, so a transition (snow
  catching on the high points of rock) reads as more physically plausible than a flat alpha blend.

```text title="Building a layered landscape material (editor steps)"
1. Add a LandscapeLayerBlend node in the Material Editor.
2. Click + next to Layers, name the entry to match your Layer Info asset (e.g. "Snow").
3. Set Blend Type per entry (LB Alpha Blend or LB Height Blend).
4. Feed each layer entry a Texture Sample; for height-blended layers, also feed the
   texture's alpha into the LandscapeLayerBlend node's Height input.
5. Connect the LandscapeLayerBlend output to Base Color (or wherever the layered look is consumed).
```

Layer Info assets are shared, not per-landscape — reusing the same "Rock" layer across multiple
landscapes keeps their paint weights compatible if you ever merge or retile terrain.

### Foliage and instancing

Foliage Mode paints instances of a `UFoliageType` (wrapping a static mesh and its scatter parameters:
density, scale range, alignment to normal, random seed) directly onto landscape or static mesh surfaces.
Painted instances aren't individual actors — they're entries in an `AInstancedFoliageActor`'s
`UHierarchicalInstancedStaticMeshComponent`, which culls and LODs per-instance without the overhead of
per-actor tick, physics, or replication. Landscape Grass Type takes this further for the densest layer
(grass, small rocks): grass instances are derived procedurally from a landscape layer weight at runtime
rather than hand-painted, so density can scale with view distance without an artist placing every blade.

Where you need runtime-driven scattering instead of hand-painted foliage — spawning debris after an
event, populating a procedurally generated area — you drive an HISM component directly:

```cpp title="RuntimeDebrisScatter.h — scattering instances at runtime without the Foliage Editor"
UCLASS()
class MYGAME_API ARuntimeDebrisScatter : public AActor
{
    GENERATED_BODY()

public:
    ARuntimeDebrisScatter();

    UFUNCTION(BlueprintCallable, Category = "Debris")
    void ScatterAroundLocation(const FVector& Center, int32 InstanceCount, float Radius);

protected:
    UPROPERTY(VisibleAnywhere, Category = "Components")
    TObjectPtr<class UHierarchicalInstancedStaticMeshComponent> DebrisMeshes;
};
```

```cpp title="RuntimeDebrisScatter.cpp"
ARuntimeDebrisScatter::ARuntimeDebrisScatter()
{
    DebrisMeshes = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("DebrisMeshes"));
    RootComponent = DebrisMeshes;
}

void ARuntimeDebrisScatter::ScatterAroundLocation(const FVector& Center, int32 InstanceCount, float Radius)
{
    for (int32 Index = 0; Index < InstanceCount; ++Index)
    {
        const FVector2D Offset = FMath::RandPointInCircle(Radius);
        const FVector InstanceLocation = Center + FVector(Offset.X, Offset.Y, 0.f);
        const FTransform InstanceTransform(FRotator(0.f, FMath::FRandRange(0.f, 360.f), 0.f), InstanceLocation);
        DebrisMeshes->AddInstance(InstanceTransform, /*bWorldSpace=*/true);
    }
}
```

### Nanite interaction

Static meshes used as foliage, landscape grass, and the landscape itself can all be Nanite meshes —
Instanced Static Mesh, Hierarchical Instanced Static Mesh, Foliage, and Landscape Grass components are all
listed as supported Nanite component types. That means dense, high-poly foliage no longer has to rely on
aggressive LOD swaps to stay cheap; the tradeoff moves toward instance count and overdraw rather than
per-instance triangle budget.

## Gotchas

:::warning Component/section size decided once, painfully changed later
Reflowing an existing landscape's component or section size effectively means re-tiling the whole
heightfield and re-painting layer weights. Pick sizes based on your target world scale and streaming
strategy up front rather than adjusting mid-production.
:::

:::caution Foliage density is a runtime cost, not just an editor slider
High-density foliage painted for a "looks good in this one screenshot" moment is easy to forget about;
audit density and culling distance per foliage type against your actual frame budget, not just visually in
the editor viewport.
:::

:::caution Shared Layer Info assets mean shared weight semantics
Because a `ULandscapeLayerInfoObject` is a shared asset, changing its properties (like whether it's a
weight-blended layer) affects every landscape that paints with it — don't duplicate landscapes without
checking whether they're meant to diverge on layer setup too.
:::

## See also

- [World Partition](./world-partition.md) — how `ALandscapeStreamingProxy` and dense foliage participate
  in grid streaming.
- [Procedural content generation](./procedural-content-generation.md) — scattering foliage and set
  dressing through PCG graphs instead of hand-painting.
- [Streaming and budgets](./streaming-and-budgets.md) — landscape and foliage as streaming/memory cost
  centers.
- [Epic — Landscape materials](https://dev.epicgames.com/documentation/unreal-engine/landscape-materials-in-unreal-engine)
