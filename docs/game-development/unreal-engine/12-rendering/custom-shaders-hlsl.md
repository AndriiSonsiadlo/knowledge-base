---
id: custom-shaders-hlsl
title: Custom shaders and HLSL in Unreal
sidebar_label: Custom shaders & HLSL
sidebar_position: 5
tags: [ unreal-engine, ue5, c++, rendering, hlsl, shaders ]
---

# Custom shaders and HLSL in Unreal

## Why this matters

The material graph's **Custom** node feels like a universal escape hatch for "just write the HLSL" —
and it is one, but it's the most limited of three distinct ways to get hand-written shader code into
the engine, and reaching for it when you actually need a compute shader or a full render pass leads to
code crammed into a string literal with no debugging, no reuse, and no access to RDG. Knowing the three
tiers — Custom node, Custom HLSL with attribute sets, and a real `FGlobalShader` backed by a `.usf`
file — and when each is the right tool is what keeps a rendering feature maintainable instead of
becoming an unreadable inline string nobody wants to touch again.

## Mental model

Think of the three tiers as a ladder of "how much of the engine's shader machinery do I actually need":
a Custom node is HLSL glued into a material graph's *existing* generated shader, with no file of its
own and no life outside that one material. A global shader is the opposite end — a real, independently
compiled shader with its own `.usf` source file, C++ parameter binding, and full access to RDG for
dispatching compute or custom passes. Nothing routes through the material graph at all in that path;
you're writing and scheduling a shader the same way the engine's own passes are written. Picking a tier
is really answering one question: does this shader logic belong to one material's look, or does it need
to exist and be dispatched independently of any specific material?

## The mechanics

### Tier 1 — the Custom material expression node

The Custom node inside a material graph takes a block of HLSL as a string property on the node,
compiles it as part of the material's generated shader, and exposes typed inputs/outputs you wire up
in the graph like any other node. It's the right tool for a small, self-contained expression — a
custom noise function, a bespoke UV distortion — that doesn't need to exist outside this one material.
It has no separate file, no `#include`, and no source control diff friendlier than "the string inside
this node changed."

A related but distinct capability: the **Custom HLSL** node (as used in newer procedural/PCG-facing
contexts) supports an **Attribute Set Generator** mode, letting a Custom HLSL block generate structured
attribute data rather than just a scalar/vector expression output.

:::note
The Attribute Set Generator mode is a recent addition and its exact scope (which graph contexts expose
it) should be checked against your 5.7 build rather than assumed to be universally available wherever
a Custom node exists.
:::

### Tier 2 — global shaders and .usf/.ush files

A **global shader** is a real C++ shader class — deriving from `FGlobalShader` — backed by an actual
HLSL source file (`.usf` for a shader, `.ush` for a header meant to be `#include`d). This is the tier
you reach for when you need a compute shader, a full custom render pass, or shader code you want to
unit-reason-about and diff normally instead of reading out of a string property.

```cpp title="MyGlobalShader.h — a compute shader class"
class FMyComputeShaderCS : public FGlobalShader
{
    DECLARE_GLOBAL_SHADER(FMyComputeShaderCS);
    SHADER_USE_PARAMETER_STRUCT(FMyComputeShaderCS, FGlobalShader);

    BEGIN_SHADER_PARAMETER_STRUCT(FParameters, )
        SHADER_PARAMETER_RDG_TEXTURE_SRV(Texture2D, InputTexture)
        SHADER_PARAMETER_RDG_TEXTURE_UAV(RWTexture2D<float4>, OutputTexture)
        SHADER_PARAMETER(FVector2f, InvTextureSize)
    END_SHADER_PARAMETER_STRUCT()

    static bool ShouldCompilePermutation(const FGlobalShaderPermutationParameters& Parameters)
    {
        return IsFeatureLevelSupported(Parameters.Platform, ERHIFeatureLevel::SM5);
    }
};
```

```text title="MyComputeShader.usf — the HLSL body, referenced by virtual path from C++"
#include "/Engine/Private/Common.ush"

Texture2D InputTexture;
RWTexture2D<float4> OutputTexture;
float2 InvTextureSize;

[numthreads(8, 8, 1)]
void MainCS(uint3 DispatchThreadId : SV_DispatchThreadID)
{
    float4 Sample = InputTexture.Load(int3(DispatchThreadId.xy, 0));
    OutputTexture[DispatchThreadId.xy] = Sample;
}
```

```cpp title="Registering the shader against its virtual source path"
IMPLEMENT_GLOBAL_SHADER(FMyComputeShaderCS, "/Plugin/MyPlugin/Private/MyComputeShader.usf", "MainCS", SF_Compute);
```

### Where shader files live: virtual shader source directories

Shader files aren't referenced by real filesystem path from C++ or from `#include` directives inside
`.usf`/`.ush` files — they're referenced by a **virtual shader source directory** mapping. The engine's
own shaders live under the virtual root `/Engine/Shaders/`. A plugin that ships a `Shaders/Private/`
folder gets an automatic virtual mapping to `/Plugin/<PluginName>/Private/...` with no extra
registration — that's why the example above references `/Plugin/MyPlugin/Private/MyComputeShader.usf`
rather than a disk path. A module that isn't a plugin (or needs a custom virtual root) registers its
own mapping explicitly, typically in the module's startup:

```cpp title="MyModule.cpp — mapping a non-plugin module's shader directory"
void FMyModule::StartupModule()
{
    const FString ShaderDirectory = FPaths::Combine(FPaths::ProjectDir(), TEXT("Source/MyModule/Shaders"));
    AddShaderSourceDirectoryMapping(TEXT("/MyModule"), ShaderDirectory);
}
```

:::note
`AddShaderSourceDirectoryMapping` is a long-standing, stable engine API for this purpose, but its exact
signature and header should be confirmed against your 5.7 engine sources if you're wiring this up for
the first time — this doc did not independently re-verify it against the 5.7 API reference in the
sources consulted.
:::

## Gotchas

:::warning[Custom node HLSL isn't reusable or debuggable the way a .usf file is]
There's no `#include`, no shared header, and no source-level shader debugging for a Custom node's
string body. Once the same HLSL snippet is copy-pasted into a second Custom node, move it to a real
global shader or a shared `.ush` include instead.
:::

:::caution[Virtual paths, not disk paths]
`IMPLEMENT_GLOBAL_SHADER` and `#include` inside shader files both take virtual paths
(`/Engine/...`, `/Plugin/<Name>/...`, or your own registered root), never a real filesystem path. A
typo in the virtual root is a shader compile failure that reads like a missing file, because it is one
— just not at the path you're looking at on disk.
:::

:::warning[Plugin shader folders map automatically; module folders don't]
Don't assume a game module's `Shaders/` folder is visible to shader compilation just because a
plugin's would be — a plugin's `Shaders/` directory gets its virtual mapping for free, a bare module
does not and needs an explicit `AddShaderSourceDirectoryMapping` call.
:::

## See also

- [Materials and the material graph](./materials-and-material-graph.md) — where the Custom node lives
  and what it competes with for simpler cases.
- [Render Dependency Graph](./render-dependency-graph.md) — how a global shader's compute/raster pass
  actually gets scheduled and given resources once it exists.
- [Post process and view extensions](./post-process-and-view-extensions.md) — a common consumer of a
  hand-written global shader.
- [Epic — Overview of Shaders in Plugins](https://dev.epicgames.com/documentation/unreal-engine/overview-of-shaders-in-plugins-unreal-engine)
