# Image Sources

Every image referenced from `docs/linux/` is tracked here so it can be re-sourced or replaced later without losing the citation trail.

Images are referenced as `/img/linux/...` (no `/knowledge-base` prefix; Docusaurus prepends `baseUrl` itself).

| file | source_url | publisher | retrieved | notes |
|---|---|---|---|---|
| `kernel-architecture-and-idioms/linux-kernel-diagram.svg` | https://graphviz.org/Gallery/directed/Linux_kernel_diagram.svg | Graphviz gallery | 2026-08-29 | Whole-kernel subsystem map, rendered from the gallery's DOT source. Far too dense to read inline — used zoomable. Vector, unmodified. |
| `overview/privilege-rings.svg` | https://upload.wikimedia.org/wikipedia/commons/2/2f/Priv_rings.svg | Wikimedia Commons | 2026-08-29 | x86 protection rings 0–3 as concentric circles. Vector, unmodified. |
| `memory-management/x86-64-paging.png` | https://commons.wikimedia.org/wiki/File:X86_Paging_64bit.svg | Wikimedia Commons | 2026-09-11 | Four-level x86-64 page walk (PML4/PDP/PD/PT + 4K page) from CR3, with the 9-9-9-9-12 bit split. 1280px PNG rendering of the source SVG, unmodified content. |

## Policy

All images in this section are chosen for how well they teach their topic. Provenance is recorded here so any figure can be replaced later without guessing where it came from. Every figure used on a page carries an italic source credit directly beneath it via `<Figure source= href= />`.
