"""Figures for docs/computer-science/algorithms/.

Run from the repository root, with the venv created by the plan's Task 3:

    .venv/bin/python tools/figures/gen_algorithms.py                 # all figures
    .venv/bin/python tools/figures/gen_algorithms.py recursion_tree  # one figure

kbstyle's output root points at static/img/ml, so it is redirected here rather
than edited — every other generator in this directory still wants the ML path.
"""

import pathlib
import sys

import kbstyle
from kbstyle import C, clean, fig, save
from matplotlib import pyplot as plt  # noqa: E402  (kbstyle selects the Agg backend first)

kbstyle.OUT_ROOT = pathlib.Path(__file__).resolve().parents[2] / "static" / "img" / "cs"


def amortized_push_cost():
    """Cost of each individual append into a doubling dynamic array."""
    f, ax = fig(7.2, 3.4)
    n = 33
    costs = [1 + (i if i > 0 and (i & (i - 1)) == 0 else 0) for i in range(n)]
    ax.bar(range(n), costs, color=C.blue, width=0.7)
    ax.axhline(3, color=C.red, lw=2.2, ls="--")
    ax.text(n - 0.5, 3.4, "amortized cost = 3", color=C.red, ha="right", fontsize=11,
            fontweight="bold")
    ax.set_xlabel("append number")
    ax.set_ylabel("element copies")
    ax.set_title("Doubling growth: rare expensive appends, cheap on average")
    save(f, "algorithms/amortized-push-cost.png")


def _node(ax, x, y, label, r=0.30, face="white", edge=C.black, lw=2.0):
    ax.add_patch(plt.Circle((x, y), r, facecolor=face, edgecolor=edge, lw=lw, zorder=3))
    ax.text(x, y, label, ha="center", va="center", fontsize=13, fontweight="bold",
            color=C.black, zorder=4)


def _parent_edge(ax, child, parent, color=C.blue, r=0.30):
    """Arrow from a child node to its parent, trimmed to both circle edges."""
    ax.annotate("", xy=parent, xytext=child, zorder=2,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=2.2,
                                shrinkA=r * 46, shrinkB=r * 46))


def dsu_forest():
    """A disjoint-set forest before and after path compression."""
    f, axes = kbstyle.grid(1, 2, 8.4, 3.4)
    layouts = [
        (
            "after the three unions",
            {0: (1.0, 2.0), 1: (0.2, 1.0), 2: (1.8, 1.0), 3: (1.8, 0.0),
             4: (3.2, 2.0), 5: (4.0, 2.0)},
            [(1, 0), (2, 0), (3, 2)],
        ),
        (
            "after find(3): path compressed",
            {0: (1.0, 2.0), 1: (0.1, 1.0), 2: (1.0, 1.0), 3: (1.9, 1.0),
             4: (3.2, 2.0), 5: (4.0, 2.0)},
            [(1, 0), (2, 0), (3, 0)],
        ),
    ]
    for ax, (title, pos, edges) in zip(axes, layouts):
        clean(ax)
        ax.set_xlim(-0.6, 4.6)
        ax.set_ylim(-0.7, 2.8)
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=12)
        for child, parent in edges:
            _parent_edge(ax, pos[child], pos[parent],
                         color=C.red if (child, parent) == (3, 0) and "find" in title else C.blue)
        for name, (x, y) in pos.items():
            root = name in (0, 4, 5)
            _node(ax, x, y, str(name), face=C.yellow if root else "white")
    f.suptitle("Disjoint-set forest: only the root names the set", fontsize=15,
               fontweight="bold")
    save(f, "algorithms/dsu-forest.png")


def prefix_sum_bands():
    """Values, their running prefix sums, and one range answered by subtraction."""
    a = [3, 1, 4, 1, 5, 9, 2, 6]
    p = [0]
    for v in a:
        p.append(p[-1] + v)
    lo, hi = 2, 5

    f, (top, bot) = kbstyle.grid(2, 1, 7.6, 4.8, sharex=True,
                                 gridspec_kw={"height_ratios": [1, 1.25]})
    colors = [C.orange if lo <= i <= hi else C.blue for i in range(len(a))]
    top.bar(range(len(a)), a, color=colors, width=0.72)
    for i, v in enumerate(a):
        top.text(i, v + 0.35, str(v), ha="center", fontsize=11, fontweight="bold")
    top.set_ylim(0, 11)
    top.set_ylabel("a[i]")
    top.set_title("Prefix sums: one subtraction answers any range")

    xs = [i - 0.5 for i in range(len(p))]
    bot.plot(xs, p, color=C.black, marker="o", lw=2.4, zorder=3)
    marked = {lo, hi + 1}
    for i, (x, v) in enumerate(zip(xs, p)):
        if i not in marked:
            bot.annotate(str(v), (x, v), textcoords="offset points", xytext=(0, 9),
                         ha="center", fontsize=11)
    for x, label, value, side in ((lo - 0.5, f"P[{lo}] = {p[lo]}", p[lo], "right"),
                                  (hi + 0.5, f"P[{hi + 1}] = {p[hi + 1]}", p[hi + 1], "left")):
        bot.plot([x], [value], marker="o", color=C.red, markersize=11, zorder=4)
        top.axvline(x, color=C.red, ls="--", lw=1.8)
        bot.axvline(x, color=C.red, ls="--", lw=1.8)
        bot.annotate(label, (x, value), textcoords="offset points",
                     xytext=(-9 if side == "right" else 11, -22),
                     ha=side, color=C.red, fontsize=12, fontweight="bold", zorder=5,
                     bbox=dict(facecolor="white", edgecolor="none", pad=1.0))
    bot.set_ylim(-4, 46)
    bot.set_xlim(-1.1, 7.9)
    bot.set_xticks(range(len(a)))
    bot.set_xlabel("index i")
    bot.set_ylabel("P[i]")
    bot.text(3.5, 41, f"sum(2, 5) = P[6] − P[2] = {p[hi + 1]} − {p[lo]} = {p[hi + 1] - p[lo]}",
             ha="center", va="center", color=C.red, fontsize=12.5, fontweight="bold",
             zorder=5, bbox=dict(facecolor="white", edgecolor="none", pad=2.0))
    save(f, "algorithms/prefix-sum-bands.png")


def kmp_failure_table():
    """The failure function of `abacaba`, and the slide it licenses."""
    pattern = "abacaba"
    fail = [0, 0, 1, 0, 1, 2, 3]
    f, ax = fig(7.6, 3.6)
    clean(ax)
    ax.set_xlim(-1.9, len(pattern) + 0.3)
    ax.set_ylim(-2.1, 2.15)
    ax.set_aspect("equal")

    for i, ch in enumerate(pattern):
        ax.add_patch(plt.Rectangle((i, 0.5), 0.9, 0.9, facecolor="white",
                                   edgecolor=C.black, lw=1.8))
        ax.text(i + 0.45, 0.95, ch, ha="center", va="center", fontsize=15,
                fontweight="bold")
        ax.add_patch(plt.Rectangle((i, -0.5), 0.9, 0.9,
                                   facecolor=C.sky if fail[i] else "white",
                                   edgecolor=C.grey, lw=1.4))
        ax.text(i + 0.45, -0.05, str(fail[i]), ha="center", va="center", fontsize=14,
                color=C.black)
    ax.text(-0.25, 0.95, "pattern", ha="right", va="center", fontsize=12.5,
            fontweight="bold")
    ax.text(-0.25, -0.05, "fail[i]", ha="right", va="center", fontsize=12.5,
            color=C.grey)

    for start, color, label in ((0, C.green, "prefix «aba»"), (4, C.orange, "suffix «aba»")):
        ax.plot([start + 0.05, start + 2.85], [1.5, 1.5], color=color, lw=4,
                solid_capstyle="butt")
        ax.text(start + 1.45, 1.65, label, ha="center", fontsize=11.5, color=color,
                fontweight="bold")

    ax.annotate("", xy=(3.45, -0.75), xytext=(6.45, -0.75), zorder=2,
                arrowprops=dict(arrowstyle="-|>", color=C.red, lw=2.4,
                                connectionstyle="arc3,rad=0.35"))
    ax.text(2.9, -1.6, "mismatch after pattern[6] → resume at pattern[fail[6]] = pattern[3];\n"
                       "the text pointer does not move back",
            ha="center", va="center", fontsize=12, color=C.red)
    ax.set_title("fail[i]: the longest proper prefix of pattern[0..i] that is also a suffix")
    save(f, "algorithms/kmp-failure-table.png")


FIGURES = {
    "amortized_push_cost": amortized_push_cost,
    "dsu_forest": dsu_forest,
    "prefix_sum_bands": prefix_sum_bands,
    "kmp_failure_table": kmp_failure_table,
}

if __name__ == "__main__":
    names = sys.argv[1:] or list(FIGURES)
    for name in names:
        print(f"{name}:")
        FIGURES[name]()
