---
id: lumen
title: Lumen global illumination and reflections
sidebar_label: Lumen
sidebar_position: 3
tags: [ unreal-engine, ue5, c++, rendering, lumen, lighting ]
---

# Lumen global illumination and reflections

## Why this matters

Lumen replaces the bake-lightmaps-and-hope workflow with fully dynamic global illumination and
reflections, which is exactly why its cost model is less intuitive than a static lightmap's: there's
no "bake time" to absorb the cost, it's all paid per frame, and the two ray tracing paths underneath it
(software and hardware) have sharply different cost profiles depending on scene composition. Treating
Lumen as a single on/off toggle means missing the settings that actually determine whether it costs
2ms or 12ms in your scene — and missing the case where enabling both ray tracing paths at once pays
for each of them separately instead of picking one.

## Mental model

Lumen splits into two mostly-independent problems that happen to share infrastructure: **Global
Illumination** (indirect diffuse lighting bouncing off the scene) and **Reflections** (specular
bounces). Both are ultimately answered by tracing rays out from a surface and asking "what does this
ray hit, and what does that surface look like lit?" — the two implementations of "trace a ray" are
Software Ray Tracing (against Signed Distance Fields, no special GPU hardware required) and Hardware
Ray Tracing (against the GPU's dedicated ray tracing units, higher quality, higher per-instance scene
maintenance cost). To make "what does that surface look like lit" cheap, Lumen doesn't re-shade the
full material at the hit point by default — it samples a **Surface Cache**, a low-resolution, cached
material representation of the scene precomputed for exactly this purpose. Every scalability knob in
Lumen is really tuning one of three things: which ray tracing implementation does the tracing, how
faithfully the Surface Cache approximates the real material, and how far/wide the trace is allowed to
search.

## The mechanics

### Two independent choices: GI method and reflection method

Lumen is configured in Project Settings under Engine > Rendering, where **Dynamic Global
Illumination Method** and **Reflection Method** are set independently — both can point at Lumen, or
you can mix Lumen GI with a different reflection approach depending on the project. Within Lumen
itself, **Ray Lighting Mode** picks how a traced hit gets its lighting: **Surface Cache** reuses
Lumen's cached, low-cost material representation of the scene (cheaper, standard choice), while **Hit
Lighting for Reflections** re-shades the actual hit material at full cost for higher-quality
reflections at a higher GPU price.

### Software vs. hardware ray tracing

Lumen's tracing has two implementations:

- **Software Ray Tracing** traces against Signed Distance Fields — either **Detail Tracing** against
  each mesh's own distance field (higher quality, more expensive) or **Global Tracing** against a
  merged, lower-resolution Global Distance Field (cheaper, coarser). This runs on any GPU regardless
  of ray tracing hardware support.
- **Hardware Ray Tracing** uses the GPU's ray tracing units, enabled via "Use Hardware Ray Tracing
  when available" with Software Ray Tracing as the fallback where hardware support is absent. Hardware
  Ray Tracing can produce noticeably better quality on complex geometry, but its scene update cost
  becomes significant with scenes above roughly 100,000 instances — it's not free just because the
  hardware supports it.

```ini title="DefaultEngine.ini — avoid paying for both ray tracing scene representations"
[SystemSettings]
; When Hardware Ray Tracing is used, this stops Lumen from also maintaining the
; Software Ray Tracing distance field representation for the same scene, which
; would otherwise cost extra memory and per-frame scene update time.
r.DistanceFields.SupportEvenIfHardwareRayTracingSupported=0
```

### Far Field tracing

Lumen Hardware Ray Tracing's **Far Field** extends GI and reflections out to roughly a kilometer,
useful for open-world scenes where the normal Lumen Scene radius isn't enough. It depends on World
Partition's Hierarchical Level of Detail (HLOD) being built for the level, since Far Field traces
against that HLOD representation rather than full-detail geometry at range.

```ini title="DefaultEngine.ini — enabling Lumen Far Field"
[SystemSettings]
r.LumenScene.FarField=1
```

### Translucency

**High Quality Translucency Reflections** improves mirror-like reflections on translucent surfaces
(glass, water) when enabled, at an increased GPU cost — it's an explicit opt-in rather than the
default translucency reflection behavior.

## Gotchas

:::warning High instance counts and Hardware Ray Tracing don't mix well by default
Scenes with more than roughly 100,000 instances can see a significant Hardware Ray Tracing scene
update cost. If a level is instance-heavy (dense foliage, large-scale procedural placement), profile
GI cost with Hardware Ray Tracing on before shipping it as the default — Software Ray Tracing's Global
Tracing mode may be the cheaper and more predictable choice at that scale.
:::

:::caution Don't leave both ray tracing representations resident by accident
If your project enables Hardware Ray Tracing, explicitly setting
`r.DistanceFields.SupportEvenIfHardwareRayTracingSupported=0` avoids silently paying the memory and
scene update cost of the Software Ray Tracing distance field representation you're not using for
Lumen's primary path.
:::

:::warning Far Field needs HLOD, not just World Partition
Enabling `r.LumenScene.FarField` without building World Partition HLODs for the level won't give you
the extended range you're expecting — Far Field traces specifically against the HLOD representation.
:::

:::note
Exact default values, additional scalability CVars (per-platform Lumen quality presets, Surface Cache
resolution controls, and so on) are extensive and version-sensitive. This doc covers the settings
confirmed for 5.7 above; verify any additional `r.Lumen.*` CVar you plan to rely on against your engine
version before shipping a tuned config.
:::

## See also

- [Nanite](./nanite.md) — the geometry pipeline Lumen's Surface Cache is built to sample efficiently.
- [Lighting and Lumen setup](../11-world-building/lighting-and-lumen-setup.md) — level-side setup
  (Lumen Scene, placement, HLOD) that this doc assumes as context.
- [GPU profiling](./gpu-profiling.md) — where to actually see Lumen's GI/reflection cost broken out
  per frame.
- [Epic — Lumen Global Illumination and Reflections](https://dev.epicgames.com/documentation/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine)
