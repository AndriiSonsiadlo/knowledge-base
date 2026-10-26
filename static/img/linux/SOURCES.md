# Image Sources

Every image referenced from `docs/linux/` is tracked here so it can be re-sourced or replaced later without losing the citation trail.

Images are referenced as `/img/linux/...` (no `/knowledge-base` prefix; Docusaurus prepends `baseUrl` itself).

| file | source_url | publisher | retrieved | notes |
|---|---|---|---|---|
| `kernel-architecture-and-idioms/linux-kernel-diagram.svg` | https://graphviz.org/Gallery/directed/Linux_kernel_diagram.svg | Graphviz gallery | 2026-08-29 | Whole-kernel subsystem map, rendered from the gallery's DOT source. Far too dense to read inline — used zoomable. Vector, unmodified. |
| `overview/privilege-rings.svg` | https://upload.wikimedia.org/wikipedia/commons/2/2f/Priv_rings.svg | Wikimedia Commons | 2026-08-29 | x86 protection rings 0–3 as concentric circles. Vector, unmodified. |
| `memory-management/x86-64-paging.png` | https://commons.wikimedia.org/wiki/File:X86_Paging_64bit.svg | Wikimedia Commons | 2026-09-11 | Four-level x86-64 page walk (PML4/PDP/PD/PT + 4K page) from CR3, with the 9-9-9-9-12 bit split. 1280px PNG rendering of the source SVG, unmodified content. |
| `block-layer-and-storage/linux-storage-stack-v6.18.png` | https://www.thomas-krenn.com/en/wikiEN/images/d/d1/Linux-storage-stack-diagram_v6.18.png | Thomas-Krenn wiki (Werner Fischer) | 2026-10-26 | "Linux Storage Stack Diagram" revision for Linux 6.18 (dated 2026-01-22), CC BY-SA 4.0 per the wiki page. The published 1160×1644 PNG, flattened onto white and quantised to 256 colours (590 KB → 108 KB, mean per-channel error 0.09); content unmodified. The page also offers an SVG (inside the ZIP), not used because it is a draw.io export. |
| `networking-stack/netfilter-packet-flow.svg` | https://upload.wikimedia.org/wikipedia/commons/3/37/Netfilter-packet-flow.svg | Wikimedia Commons (Jan Engelhardt) | 2026-10-26 | Netfilter packet flow through every hook, including the bridge path, labelled with the legacy xtables table names (raw, mangle, nat, filter, security). CC BY-SA 3.0; file version of 2021-04-21. Original SVG, unmodified. |

## Policy

All images in this section are chosen for how well they teach their topic. Provenance is recorded here so any figure can be replaced later without guessing where it came from. Every figure used on a page carries an italic source credit directly beneath it via `<Figure source= href= />`.
