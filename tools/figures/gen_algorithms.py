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


FIGURES = {
    "amortized_push_cost": amortized_push_cost,
}

if __name__ == "__main__":
    names = sys.argv[1:] or list(FIGURES)
    for name in names:
        print(f"{name}:")
        FIGURES[name]()
