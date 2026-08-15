"""Shared house style for generated knowledge-base figures.

Every figure in `static/img/ml/` is produced by a script in this directory that
imports this module. The style targets *legibility first*: large type, thick
strokes, high contrast, and a colour-blind-safe palette (Okabe-Ito), rendered on
an opaque white canvas because the `<Figure>` component places figures on a
permanently light plate in both site themes.

Usage:

    from kbstyle import fig, save, C

    f, ax = fig(6, 4)
    ax.plot(x, y, color=C.blue)
    save(f, "foundations/gradient-descent-paths.png")
"""

from __future__ import annotations

import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_ROOT = pathlib.Path(__file__).resolve().parents[2] / "static" / "img" / "ml"

# Export at 2x so the figures stay sharp on HiDPI displays; `save()` halves the
# apparent size by writing at dpi=200 for a figure measured in inches.
DPI = 200


class C:
    """Okabe-Ito, the standard colour-blind-safe qualitative palette.

    Safe for deuteranopia, protanopia and tritanopia. Used everywhere so that a
    colour means the same thing across figures: `blue` is the primary series,
    `orange` the contrasting one, `red` the failure case.
    """

    blue = "#0072B2"
    orange = "#E69F00"
    green = "#009E73"
    red = "#D55E00"
    purple = "#CC79A7"
    sky = "#56B4E9"
    yellow = "#F0E442"
    black = "#111827"
    grey = "#6B7280"
    light = "#D1D5DB"

    # Ordered cycle for multi-series plots.
    cycle = [blue, orange, green, red, purple, sky, black]


plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.25,
        # Type sizes are deliberately large: these are read at ~700px wide
        # inside a docs column, not at full figure size.
        "font.size": 13,
        "axes.titlesize": 15,
        "axes.labelsize": 13,
        "xtick.labelsize": 11.5,
        "ytick.labelsize": 11.5,
        "legend.fontsize": 11.5,
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans"],
        "axes.titleweight": "bold",
        "axes.titlepad": 12,
        # Thick strokes and de-emphasised chrome.
        "lines.linewidth": 2.6,
        "lines.markersize": 7,
        "axes.linewidth": 1.3,
        "axes.edgecolor": "#374151",
        "axes.labelcolor": "#111827",
        "text.color": "#111827",
        "xtick.color": "#374151",
        "ytick.color": "#374151",
        "xtick.major.width": 1.3,
        "ytick.major.width": 1.3,
        "axes.grid": True,
        "grid.color": "#E5E7EB",
        "grid.linewidth": 1.0,
        "axes.axisbelow": True,
        "legend.frameon": True,
        "legend.framealpha": 0.95,
        "legend.edgecolor": "#D1D5DB",
        "figure.autolayout": False,
    }
)


def fig(w: float = 6.4, h: float = 4.2, **kw):
    """A single-axes figure at the house default aspect."""
    f, ax = plt.subplots(figsize=(w, h), **kw)
    return f, ax


def grid(rows: int, cols: int, w: float = 6.4, h: float = 4.2, **kw):
    """A multi-panel figure; returns (figure, axes-array)."""
    f, axes = plt.subplots(rows, cols, figsize=(w, h), **kw)
    return f, axes


def despine(ax, keep=("left", "bottom")):
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(side in keep)


def nogrid(ax):
    ax.grid(False)


def clean(ax):
    """Strip an axes down to a bare drawing surface (for schematic figures)."""
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)


def save(f, relpath: str) -> pathlib.Path:
    """Write `f` to static/img/ml/<relpath> and close it."""
    out = OUT_ROOT / relpath
    out.parent.mkdir(parents=True, exist_ok=True)
    f.savefig(out, dpi=DPI)
    plt.close(f)
    print(f"  wrote {relpath}")
    return out
