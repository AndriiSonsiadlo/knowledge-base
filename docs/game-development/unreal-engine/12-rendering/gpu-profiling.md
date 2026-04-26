---
id: gpu-profiling
title: GPU profiling with in-engine tooling
sidebar_label: GPU profiling
sidebar_position: 8
tags: [ unreal-engine, ue5, c++, rendering, profiling, renderdoc ]
---

# GPU profiling with in-engine tooling

## Why this matters

"It's slow" is not a diagnosis until you know whether the frame is CPU-bound, GPU-bound, and if GPU-
bound, which pass is actually eating the milliseconds. Unreal ships several in-engine tools that answer
that at different levels of detail — a one-line `stat gpu` readout, a full hierarchical capture via
`ProfileGPU`, and RenderDoc integration for inspecting a single draw call's actual GPU state. Reaching
for full RenderDoc capture to answer "which pass is expensive" when `stat gpu` would have told you in
five seconds is a waste of time; reaching for `stat gpu` to answer "why does this exact draw call
produce the wrong pixel" is the wrong tool in the other direction.

## Mental model

Think of GPU profiling in Unreal as three zoom levels over the same frame, not three competing tools.
`stat gpu` is the widest zoom: a per-category summary (Base Pass, Shadows, Translucency, Post Process,
your own tagged passes) refreshed every frame, cheap enough to leave running. `profilegpu` zooms in one
level: a single captured frame broken into every individual pass and draw call with its own GPU time,
viewed in the GPU Visualizer. RenderDoc zooms in furthest: the actual GPU state — bound textures, shader
inputs and outputs, intermediate render targets — for a specific draw call inside a captured frame. The
right workflow moves from wide to narrow: confirm the category with `stat gpu`, find the offending pass
with `profilegpu`, and only reach for RenderDoc once you need to see inside that one draw call.

## The mechanics

### stat gpu — the always-available breakdown

The `stat gpu` console command shows a real-time, per-frame breakdown of GPU time by category (Base
Pass, Shadow Depths, Translucency, Post Process, and so on) directly in the running game or PIE
session. It's cheap to leave on while iterating, and it's the first thing to check before reaching for
a heavier tool — it tells you which broad category of rendering work is dominant. If you've tagged a
custom RDG pass with `RDG_GPU_STAT_SCOPE` (see [Render Dependency Graph](./render-dependency-graph.md)),
your custom pass shows up as its own line here instead of folding into a generic bucket.

```text title="Console command"
stat gpu
```

On mobile, the equivalent path is the on-device developer console (opened by a four-finger tap in
Development builds), where **Stat GPU** shows GPU time, **Stat Unit** shows CPU/thread time, and **Stat
UnitGraph** visualizes both over time — useful when you don't have a tethered profiling setup handy.

### ProfileGPU — a full hierarchical capture

The `profilegpu` console command captures one full GPU frame and opens it in the **GPU Visualizer**, a
hierarchical view of every pass and draw call in that frame with per-item GPU timing. This is the tool
for going from "Translucency is expensive this frame" (from `stat gpu`) to "which specific translucent
draw call is responsible" — including, for example, drilling into Skin Cache entries and their
associated Skeletal Meshes when investigating character rendering cost.

```text title="Console command"
profilegpu
```

### RDG's own profiling scopes

If you're authoring a custom render pass through RDG, tag it so it actually shows up in these tools
rather than appearing as unattributed time: `RDG_EVENT_SCOPE` feeds RenderDoc and RDG Insights,
`RDG_GPU_STAT_SCOPE` feeds `stat gpu`, and `RDG_CSV_STAT_EXCLUSIVE_SCOPE` feeds the CSV profiler. These
are three separate macros because the tools they feed are separate — using only one leaves your pass
invisible to the other two.

### RenderDoc integration

RenderDoc is a third-party GPU debugger Unreal integrates with for inspecting the actual GPU state of a
captured frame — individual draw calls, bound resources, shader inputs/outputs, and intermediate
render targets — at a level of detail neither `stat gpu` nor the GPU Visualizer provides. It's the
right tool once you've narrowed a problem down to "this specific draw call produces the wrong result"
or "I need to see the exact texture bound at this exact point," rather than a general performance
budget question.

:::note
Exact RenderDoc launch/attach steps (editor plugin vs. standalone capture, the specific menu path in
5.7) weren't independently re-verified against the 5.7 documentation in the sources consulted for this
doc — check the current RenderDoc integration entry point in your build before assuming a specific menu
location.
:::

### Where this fits relative to Unreal Insights

Unreal Insights is the engine's broader profiling and trace system, covering CPU, GPU, memory, and
networking traces over time rather than a single-frame breakdown. It's a substantially bigger topic
than the frame-level tools above and gets its own treatment separately — for GPU-specific,
single-frame investigation, `stat gpu`, `profilegpu`, and RenderDoc are the tools covered here.

## Gotchas

:::warning stat gpu numbers include CPU-side dispatch overhead alongside GPU time
Reading `stat gpu` categories as pure GPU execution time without cross-checking `stat unit` for CPU/GPU
balance can mislead you into optimizing the wrong side of a CPU-bound frame. Check both before deciding
where to spend optimization effort.
:::

:::caution An untagged custom RDG pass hides inside a generic bucket
If you added a custom pass through RDG without an `RDG_GPU_STAT_SCOPE`, it doesn't disappear from
`stat gpu` — it gets folded into whatever generic category it happens to fall under, which makes it
look like someone else's code is expensive. Tag your own passes before profiling them.
:::

:::warning ProfileGPU captures one frame — a spike you can't reliably reproduce won't show up
`profilegpu` is a single-frame snapshot triggered on demand. An intermittent frame spike needs to
actually be happening at the moment you trigger the capture, or a broader trace-based tool (Unreal
Insights) is the better fit than repeatedly guessing at the right frame to snapshot.
:::

## See also

- [Render Dependency Graph](./render-dependency-graph.md) — the `RDG_EVENT_SCOPE` /
  `RDG_GPU_STAT_SCOPE` / `RDG_CSV_STAT_EXCLUSIVE_SCOPE` macros these tools read from.
- [Render thread model](./render-thread-model.md) — why GPU time and CPU (game/render thread) time
  need to be read together, not in isolation.
- [Lumen](./lumen.md) — a common source of GPU cost worth checking with `stat gpu` before tuning its
  quality settings blind.
- [Epic — Introduction to Performance Profiling and Configuration](https://dev.epicgames.com/documentation/unreal-engine/introduction-to-performance-profiling-and-configuration-in-unreal-engine)
