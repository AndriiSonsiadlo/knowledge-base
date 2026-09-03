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


def recursion_tree():
    """Mergesort's recursion tree for n = 8: work per node, and the level sum on the right."""
    f, ax = fig(8.4, 5.2)
    clean(ax)
    ax.set_xlim(-0.5, 9.6)
    ax.set_ylim(-0.6, 4.3)

    # (label, x, level) for each node, level 0 at the top (root)
    levels = [
        [("n=8", 4.0)],
        [("n=4", 1.8), ("n=4", 6.2)],
        [("n=2", 0.8), ("n=2", 2.8), ("n=2", 5.2), ("n=2", 7.2)],
        [("n=1", 0.3), ("n=1", 1.3), ("n=1", 2.3), ("n=1", 3.3),
         ("n=1", 4.7), ("n=1", 5.7), ("n=1", 6.7), ("n=1", 7.7)],
    ]
    ys = [4.0, 2.8, 1.6, 0.4]
    positions = {}
    for depth, (row, y) in enumerate(zip(levels, ys)):
        for i, (label, x) in enumerate(row):
            positions[(depth, i)] = (x, y)

    # edges: each node at depth d, index i has two children at depth d+1, index 2i, 2i+1
    for depth in range(len(levels) - 1):
        for i in range(len(levels[depth])):
            x0, y0 = positions[(depth, i)]
            for child in (2 * i, 2 * i + 1):
                if (depth + 1, child) in positions:
                    x1, y1 = positions[(depth + 1, child)]
                    ax.plot([x0, x1], [y0 - 0.28, y1 + 0.28], color=C.grey, lw=1.6, zorder=1)

    for depth, row in enumerate(levels):
        for i, (label, x) in enumerate(row):
            y = ys[depth]
            ax.add_patch(plt.Circle((x, y), 0.30, facecolor="white", edgecolor=C.blue,
                                    lw=2.0, zorder=3))
            ax.text(x, y, label, ha="center", va="center", fontsize=10.5, fontweight="bold",
                    color=C.black, zorder=4)

    # level work, and the running total on the right
    work = ["cn (1 subproblem × cn)", "2 · c(n/2) = cn", "4 · c(n/4) = cn", "8 · c(n/8) = cn"]
    for y, label in zip(ys, work):
        ax.text(9.5, y, label, ha="right", va="center", fontsize=11, color=C.red,
                fontweight="bold")

    ax.text(9.5, 4.6, "work per level", ha="right", va="center", fontsize=11.5,
            color=C.grey, fontweight="bold")
    ax.axhline(-0.15, color=C.light, lw=1.2)
    ax.text(4.0, -0.5, "log₂8 = 3 levels below the root, each costing Θ(n) → Θ(n log n) total",
            ha="center", va="center", fontsize=11.5, color=C.black)
    ax.set_title("Mergesort's recursion tree, n = 8: Θ(n) work at every one of the log n levels",
                 fontsize=13.5)
    save(f, "algorithms/recursion-tree.png")


def fenwick_tree():
    """The Fenwick/BIT responsibility ranges over 8 elements, plus one update path.

    Index i (1-based) stores the sum of the range (i - lowbit(i), i]. Ranges of
    equal length never overlap, so stacking rows by length (= lowbit(i)) draws
    the classic pyramid with no crossing labels. The arrows trace update(3):
    every ancestor reached by repeatedly adding lowbit(i).
    """
    n = 8

    def lowbit(i):
        return i & (-i)

    update_path = []
    i = 3
    while i <= n:
        update_path.append(i)
        i += lowbit(i)

    row_of = {1: 0, 2: 1, 4: 2, 8: 3}  # length -> row (taller ranges sit higher)
    f, ax = fig(8.6, 5.6)
    clean(ax)
    ax.set_xlim(0.3, n + 0.7)
    ax.set_ylim(-0.6, 5.1)

    for i in range(1, n + 1):
        ax.add_patch(plt.Rectangle((i - 0.4, 4.3), 0.8, 0.7, facecolor="white",
                                   edgecolor=C.black, lw=1.8))
        ax.text(i, 4.65, f"a[{i}]", ha="center", va="center", fontsize=11, fontweight="bold")

    centers = {}
    for i in range(1, n + 1):
        length = lowbit(i)
        lo = i - length + 1
        y = 0.4 + row_of[length] * 1.15
        on_path = i in update_path
        color = C.orange if on_path else C.blue
        ax.plot([lo, i], [y, y], color=color, lw=5, solid_capstyle="round",
                 zorder=2 + on_path, alpha=1.0 if on_path else 0.85)
        ax.plot([lo, lo], [y - 0.1, y + 0.1], color=color, lw=2)
        ax.plot([i, i], [y - 0.1, y + 0.1], color=color, lw=2)
        ax.text((lo + i) / 2, y + 0.28, f"tree[{i}]=sum({lo}..{i})",
                ha="center", fontsize=9.5, color=color, fontweight="bold" if on_path else "normal")
        centers[i] = ((lo + i) / 2, y)

    for a, b in zip(update_path, update_path[1:]):
        ax.annotate("", xy=centers[b], xytext=centers[a], zorder=4,
                    arrowprops=dict(arrowstyle="-|>", color=C.red, lw=2.4,
                                    connectionstyle="arc3,rad=0.15"))
    ax.text(4.5, -0.45, "update(3): 3 → 3+lowbit(3)=4 → 4+lowbit(4)=8, stop (>8)",
            ha="center", fontsize=12, color=C.red, fontweight="bold")
    ax.set_title("Fenwick tree: each index owns a range fixed by its low bit", fontsize=14)
    save(f, "algorithms/fenwick-tree.png")


def ring_buffer_states():
    """An 8-slot ring buffer at four points in a push/pop/push sequence."""
    slots = 8
    states = [
        ("empty: head = tail = 0", [None] * 8, 0, 0),
        ("after push ×5", [10, 20, 30, 40, 50, None, None, None], 0, 5),
        ("after pop ×2", [None, None, 30, 40, 50, None, None, None], 2, 5),
        ("after push ×4 (tail wraps)", [90, None, 30, 40, 50, 60, 70, 80], 2, 1),
    ]
    f, axes = kbstyle.grid(2, 2, 9.0, 6.0)
    for ax, (title, values, head, tail) in zip(axes.flat, states):
        clean(ax)
        ax.set_xlim(-0.7, slots - 0.3)
        ax.set_ylim(-1.3, 1.5)
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=12.5)
        for i in range(slots):
            occupied = values[i] is not None
            ax.add_patch(plt.Rectangle((i - 0.42, -0.42), 0.84, 0.84,
                                       facecolor=C.sky if occupied else "white",
                                       edgecolor=C.black, lw=1.6))
            if occupied:
                ax.text(i, 0.0, str(values[i]), ha="center", va="center",
                        fontsize=11.5, fontweight="bold")
            ax.text(i, -0.95, str(i), ha="center", va="center", fontsize=9.5, color=C.grey)
        ax.annotate("head", (head, 0.55), xytext=(head, 1.15), ha="center",
                    fontsize=10.5, color=C.blue, fontweight="bold",
                    arrowprops=dict(arrowstyle="-|>", color=C.blue, lw=1.8))
        ax.annotate("tail", (tail % slots, 0.55), xytext=(tail % slots, 1.15), ha="center",
                    fontsize=10.5, color=C.red, fontweight="bold",
                    arrowprops=dict(arrowstyle="-|>", color=C.red, lw=1.8))
    f.suptitle("Ring buffer: tail wraps past index 7 back to index 0", fontsize=15,
               fontweight="bold")
    save(f, "algorithms/ring-buffer-states.png")


def bloom_false_positive_rate():
    """False-positive rate vs bits per element, for k = 3, 5, 7 hash functions."""
    import math

    bits_per_element = [b / 2 for b in range(2, 41)]
    f, ax = fig(7.4, 4.4)
    for k, color in ((3, C.blue), (5, C.orange), (7, C.red)):
        rates = [(1 - math.exp(-k / b)) ** k for b in bits_per_element]
        ax.plot(bits_per_element, rates, color=color, label=f"k = {k}", lw=2.4)
    ax.set_yscale("log")
    ax.set_xlabel("bits per element (m / n)")
    ax.set_ylabel("false-positive rate p (log scale)")
    ax.set_title("Bloom filter: p ≈ (1 − e^(−k/b))^k, lower is better")
    ax.legend()
    save(f, "algorithms/bloom-false-positive-rate.png")


def radix_sort_passes():
    """LSD radix sort of [170, 45, 75, 90, 802, 24, 2, 66]: buckets after each digit pass."""
    passes = [
        ("pass 1 — units digit", {0: [170, 90], 2: [802, 2], 4: [24], 5: [45, 75], 6: [66]},
         [170, 90, 802, 2, 24, 45, 75, 66]),
        ("pass 2 — tens digit", {0: [802, 2], 2: [24], 4: [45], 6: [66], 7: [170, 75], 9: [90]},
         [802, 2, 24, 45, 66, 170, 75, 90]),
        ("pass 3 — hundreds digit", {0: [2, 24, 45, 66, 75, 90], 1: [170], 8: [802]},
         [2, 24, 45, 66, 75, 90, 170, 802]),
    ]
    f, axes = kbstyle.grid(3, 1, 7.6, 8.4)
    for ax, (title, buckets, output) in zip(axes, passes):
        clean(ax)
        ax.set_xlim(-0.6, 9.6)
        ax.set_ylim(-1.1, 3.3)
        ax.set_title(title, fontsize=12.5)
        for d in range(10):
            ax.add_patch(plt.Rectangle((d - 0.42, -0.5), 0.84, 0.5, facecolor="white",
                                       edgecolor=C.grey, lw=1.2))
            ax.text(d, -0.25, str(d), ha="center", va="center", fontsize=10, color=C.grey)
            for k, v in enumerate(buckets.get(d, [])):
                ax.add_patch(plt.Rectangle((d - 0.42, 0.05 + k * 0.62), 0.84, 0.52,
                                           facecolor=C.sky, edgecolor=C.black, lw=1.2, zorder=2))
                ax.text(d, 0.31 + k * 0.62, str(v), ha="center", va="center", fontsize=9.5,
                        fontweight="bold", zorder=3)
        ax.text(4.5, 3.05, "output (buckets 0→9, left to right within a bucket): "
                            + ", ".join(str(v) for v in output),
                ha="center", va="center", fontsize=10, color=C.red)
    f.suptitle("LSD radix sort: three stable passes, least significant digit first", fontsize=15,
               fontweight="bold")
    save(f, "algorithms/radix-sort-passes.png")


def _qs_panel(ax, values, active_lo, active_hi, dead, pivot_idx, found_idx, title):
    clean(ax)
    ax.set_xlim(-0.6, len(values) - 0.4)
    ax.set_ylim(-0.9, 1.1)
    ax.set_title(title, fontsize=11.5)
    for i, v in enumerate(values):
        if found_idx == i:
            face = C.green
        elif i == pivot_idx:
            face = C.orange
        elif dead[0] <= i <= dead[1]:
            face = C.light
        elif active_lo <= i <= active_hi:
            face = "white"
        else:
            face = C.light
        edge = C.blue if active_lo <= i <= active_hi else C.grey
        ax.add_patch(plt.Rectangle((i - 0.42, -0.42), 0.84, 0.84, facecolor=face,
                                   edgecolor=edge, lw=2.2 if active_lo <= i <= active_hi else 1.2))
        ax.text(i, 0.0, str(v), ha="center", va="center", fontsize=12, fontweight="bold")


def quickselect_shrink():
    """Finding the 3rd smallest of [5, 1, 8, 3, 9, 2, 7, 4]: the searched region per level."""
    f, axes = kbstyle.grid(3, 1, 7.4, 6.6)
    _qs_panel(axes[0], [5, 1, 8, 3, 9, 2, 7, 4], 0, 7, (8, -1), 7, None,
              "level 0: pivot = arr[7] = 4, whole array searched")
    _qs_panel(axes[1], [1, 3, 2, 4, 9, 8, 7, 5], 0, 2, (3, 7), None, None,
              "after partition: pivotIndex 3 > k=2 → recurse left, indices 0–2 only")
    _qs_panel(axes[2], [1, 2, 3, 4, 9, 8, 7, 5], 2, 2, (0, 1), None, 2,
              "level 1 partitions [1,3,2]→[1,2,3], pivotIndex 1 < k=2 → index 2 is the answer: 3")
    f.suptitle("Quickselect: only the side containing k is ever recursed into", fontsize=15,
               fontweight="bold")
    save(f, "algorithms/quickselect-shrink.png")


FIGURES = {
    "amortized_push_cost": amortized_push_cost,
    "dsu_forest": dsu_forest,
    "prefix_sum_bands": prefix_sum_bands,
    "kmp_failure_table": kmp_failure_table,
    "recursion_tree": recursion_tree,
    "fenwick_tree": fenwick_tree,
    "ring_buffer_states": ring_buffer_states,
    "bloom_false_positive_rate": bloom_false_positive_rate,
    "radix_sort_passes": radix_sort_passes,
    "quickselect_shrink": quickselect_shrink,
}

if __name__ == "__main__":
    names = sys.argv[1:] or list(FIGURES)
    for name in names:
        print(f"{name}:")
        FIGURES[name]()
