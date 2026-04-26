---
id: lighting-and-lumen-setup
title: Lighting and Lumen setup
sidebar_label: Lighting & Lumen
sidebar_position: 5
tags: [ unreal-engine, ue5, c++, lumen, lighting, ray-tracing ]
---

# Lighting and Lumen setup

## Why this matters

Lumen replaced the old choice between fully baked lighting (fast, static, breaks the moment something
moves) and fully dynamic ray-traced lighting (correct, expensive) with a single dynamic global illumination
and reflections system that's meant to just work. It doesn't fully "just work" for free, though — the
choice between hardware and software ray tracing, and a handful of quality knobs on the Post Process
Volume, are the difference between a scene that holds 60fps and one that doesn't, and between reflections
that look right and reflections that swim as the camera moves. Get the base setup wrong (no Sky Light, a
Stationary Directional Light instead of Movable) and Lumen silently falls back to worse-looking defaults
instead of failing loudly.

## Mental model

Lumen isn't a light — it's a lighting *solver* that consumes the scene you already built (meshes,
materials, lights) and traces against a representation of it to compute bounced light and reflections each
frame. Which representation it traces against is the whole configuration story: real triangles via
hardware ray tracing (accurate, expensive to keep updated as things move), or Distance Fields via software
ray tracing (cheaper, coarser). Everything else — Surface Cache vs Hit Lighting, Screen Traces, quality
sliders — is tuning how much of that trace's cost you're willing to pay in exchange for correctness, on a
per-project or per-area basis via the Post Process Volume.

## The mechanics

### Base scene setup

Lumen needs a light to bounce and a sky to gather ambient contribution from:

- **Directional Light** — set to **Movable**. Lumen's dynamic GI expects a fully dynamic key light; a
  Stationary or Static Directional Light doesn't participate in Lumen the same way.
- **Sky Light** — provides the ambient/sky contribution Lumen gathers into scenes; use Real Time Capture
  for a sky that changes (time of day, dynamic weather) or a captured cubemap for a static one.
- **Post Process Volume** — Lumen's per-view quality settings (reflection quality, ray lighting mode,
  ambient occlusion) live here, either on an unbound volume for a global default or a bounded one for a
  specific area's override.

### Hardware vs. software ray tracing

This is the single biggest Lumen decision, set in **Project Settings → Engine → Rendering**:

| Setting | What it does | Cost profile |
|---|---|---|
| Dynamic Global Illumination Method / Reflection Method | Selects Lumen as the GI/reflection method | — |
| Use Hardware Ray Tracing when available | Traces against actual scene geometry via RT hardware, falling back to software tracing when unavailable | Higher fidelity; scene update cost can be significant above roughly 100,000 instances |
| Ray Lighting Mode | **Surface Cache** (cheap, reuses cached lighting) vs **Hit Lighting for Reflections** (evaluates lighting at the actual ray hit, higher quality, higher cost) | Surface Cache for most content; Hit Lighting where mirror-quality reflections matter |

Software Ray Tracing (used when hardware RT is unavailable or disabled) traces against Distance Fields
instead of real geometry, with two tiers: **Detail Tracing** against per-mesh Distance Fields for higher
quality close up, and **Global Tracing** against a lower-detail Global Distance Field for cheaper,
longer-range tracing. If your project has hardware ray tracing available and enabled, you generally don't
want both systems paying their scene-update cost simultaneously — disable the software fallback's distance
field support explicitly:

```ini title="DefaultEngine.ini — avoid paying for both HWRT and software distance fields"
[/Script/Engine.RendererSettings]
r.DistanceFields.SupportEvenIfHardwareRayTracingSupported=0
```

### Post Process Volume quality knobs

Per-view overrides that matter most for Lumen reflections specifically:

- **Quality** — trades noise/detail for GPU cost; raise it for hero areas, leave default elsewhere.
- **Ray Lighting Mode** (per-view override of the project default) — set to Hit Lighting for Reflections
  on a bounded volume around, say, a mirror-heavy room, without paying that cost everywhere.
- **Screen Traces** — uses scene depth/color for cheap, high-quality traces where available, but bypasses
  the Lumen Scene, meaning Lumen-Scene-only contributions (some emissive setups) won't show up in
  screen-traced results. This is a correctness tradeoff, not just a quality slider.
- **High Quality Translucency Reflections** — improves mirror-like reflections on translucent surfaces at
  extra GPU cost; enable selectively rather than project-wide.

### Choosing per area, not per project

Because Ray Lighting Mode and reflection quality can be set on a bounded Post Process Volume, the practical
pattern is: cheap Surface Cache lighting and default quality as the project-wide baseline, with bounded
volumes raising quality (or switching to Hit Lighting) only around the specific rooms or set pieces where
it's visually load-bearing — a mirror, a highly reflective floor, a cutscene camera angle.

## Gotchas

:::warning A Stationary Directional Light silently degrades Lumen
If your key light isn't Movable, Lumen doesn't error — it just doesn't get the dynamic GI behavior you're
expecting from it. This is one of the most common "why does my scene look flat/wrong compared to the
Lumen demo" issues and it's a light property, not a Lumen setting.
:::

:::caution Hardware ray tracing cost scales with instance count, not just triangle count
Above roughly 100,000 instances, hardware ray tracing's scene update cost becomes significant regardless
of how simple each instance is. Dense instanced foliage or PCG-scattered content is exactly the case where
this bites — profile HWRT scene update cost on your actual dense scenes, not a test level.
:::

:::caution Screen Traces trade correctness for cost
Because screen traces bypass the Lumen Scene, effects that only exist there (certain emissive
contributions to reflections/GI) can be missing from a screen-traced result even though the setting is
purely a quality knob on paper. If something is invisible in reflections specifically, check whether
Screen Traces is masking a Lumen Scene contribution rather than assuming the emissive setup is broken.
:::

## See also

- [World Partition](./world-partition.md) — how large streamed worlds interact with Lumen's scene update
  cost as content streams in and out.
- [Landscape and foliage](./landscape-and-foliage.md) — dense foliage as a driver of Lumen/ray-tracing
  instance-count cost.
- [Streaming and budgets](./streaming-and-budgets.md) — frame budget context for where Lumen quality
  tradeoffs fit.
- [Epic — Lumen Global Illumination and Reflections](https://dev.epicgames.com/documentation/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine)
