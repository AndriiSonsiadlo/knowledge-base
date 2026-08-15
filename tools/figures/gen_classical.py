"""Figures for docs/machine-learning/01-classical-ml/.

Everything here is hand-rolled in numpy rather than pulled from scikit-learn, so
the figures depend only on numpy + matplotlib and the exact algorithm being
drawn is visible in this file.
"""

import numpy as np
from matplotlib.colors import ListedColormap

from kbstyle import C, clean, fig, grid, save

rng = np.random.default_rng(7)
CMAP = ListedColormap([C.blue, C.orange])
BG = ListedColormap(["#CFE3F3", "#FBE7C4"])


# ---------------------------------------------------------------- datasets
def two_blobs(n=90, sep=2.4, seed=1):
    r = np.random.default_rng(seed)
    a = r.normal([-sep / 2, -sep / 2 * 0.6], 0.85, (n, 2))
    b = r.normal([sep / 2, sep / 2 * 0.6], 0.85, (n, 2))
    return np.vstack([a, b]), np.r_[np.zeros(n), np.ones(n)].astype(int)


def moons(n=110, noise=0.19, seed=3):
    r = np.random.default_rng(seed)
    t = np.linspace(0, np.pi, n)
    x1 = np.stack([np.cos(t), np.sin(t)], 1)
    x2 = np.stack([1 - np.cos(t), 0.5 - np.sin(t)], 1)
    X = np.vstack([x1, x2]) + r.normal(0, noise, (2 * n, 2))
    return X, np.r_[np.zeros(n), np.ones(n)].astype(int)


def circles(n=130, seed=5):
    r = np.random.default_rng(seed)
    t = r.uniform(0, 2 * np.pi, n)
    inner = np.stack([0.45 * np.cos(t), 0.45 * np.sin(t)], 1) + r.normal(0, 0.09, (n, 2))
    t2 = r.uniform(0, 2 * np.pi, n)
    outer = np.stack([1.15 * np.cos(t2), 1.15 * np.sin(t2)], 1) + r.normal(0, 0.11, (n, 2))
    return np.vstack([inner, outer]), np.r_[np.zeros(n), np.ones(n)].astype(int)


def mesh(X, pad=0.6, steps=320):
    x0, x1 = X[:, 0].min() - pad, X[:, 0].max() + pad
    y0, y1 = X[:, 1].min() - pad, X[:, 1].max() + pad
    xx, yy = np.meshgrid(np.linspace(x0, x1, steps), np.linspace(y0, y1, steps))
    return xx, yy


def draw_points(ax, X, y, s=34):
    ax.scatter(X[:, 0], X[:, 1], c=y, cmap=CMAP, s=s, edgecolors="white", linewidths=0.7, zorder=4)


def boundary(ax, xx, yy, Z):
    ax.contourf(xx, yy, Z, levels=[-0.5, 0.5, 1.5], cmap=BG, alpha=0.85)
    ax.contour(xx, yy, Z, levels=[0.5], colors=[C.black], linewidths=2.4)


def bare(ax):
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)


# ---------------------------------------------------------------- linear regression
def linear_regression():
    f, axes = grid(1, 2, 11.2, 4.2)
    n = 60
    x = rng.uniform(0, 10, n)
    y = 2.1 * x + 4 + rng.normal(0, 3.2, n)
    b1, b0 = np.polyfit(x, y, 1)
    fit = b0 + b1 * x

    ax = axes[0]
    ax.scatter(x, y, c=C.blue, s=42, zorder=4, edgecolors="white", linewidths=0.7)
    xs = np.linspace(0, 10, 10)
    ax.plot(xs, b0 + b1 * xs, color=C.red, lw=3, zorder=5, label=f"fit:  y = {b0:.1f} + {b1:.2f}x")
    for xi, yi, fi in zip(x, y, fit):
        ax.plot([xi, xi], [yi, fi], color=C.grey, lw=1.2, alpha=0.75, zorder=3)
    ax.set_title("Least squares minimises the\nsum of squared vertical distances")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend(fontsize=10.5, loc="upper left")

    ax = axes[1]
    ax.scatter(fit, y - fit, c=C.blue, s=42, edgecolors="white", linewidths=0.7)
    ax.axhline(0, color=C.red, lw=2.6)
    ax.set_title("Residuals show no pattern\n— the linear model fits")
    ax.set_xlabel("fitted value")
    ax.set_ylabel("residual")
    f.tight_layout()
    save(f, "classical/linear-regression-fit.png")


def anscombe():
    """Four datasets, identical regression statistics, four different stories."""
    x = np.array([10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5], float)
    sets = {
        "I": (x, np.array([8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68])),
        "II": (x, np.array([9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10, 9.13, 7.26, 4.74])),
        "III": (x, np.array([7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39, 8.15, 6.42, 5.73])),
        "IV": (np.array([8, 8, 8, 8, 8, 8, 8, 19, 8, 8, 8], float),
               np.array([6.58, 5.76, 7.71, 8.84, 8.47, 7.04, 5.25, 12.50, 5.56, 7.91, 6.89])),
    }
    f, axes = grid(1, 4, 13.0, 3.5, sharex=True, sharey=True)
    for ax, (name, (xv, yv)) in zip(axes, sets.items()):
        m, c = np.polyfit(xv, yv, 1)
        ax.scatter(xv, yv, c=C.blue, s=46, zorder=4, edgecolors="white", linewidths=0.7)
        xs = np.linspace(3, 20, 10)
        ax.plot(xs, c + m * xs, color=C.red, lw=2.4)
        ax.set_title(f"{name}:  y = {c:.2f} + {m:.2f}x", fontsize=12)
        ax.set_xlim(2, 20)
        ax.set_ylim(2, 14)
    axes[0].set_ylabel("y")
    f.suptitle("Anscombe's quartet — same fit, same R², same correlation. Always plot the data.",
               fontsize=13.5, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.93))
    save(f, "classical/anscombe-quartet.png")


# ---------------------------------------------------------------- logistic regression
def logistic_regression():
    f, axes = grid(1, 2, 11.2, 4.2)

    ax = axes[0]
    z = np.linspace(-8, 8, 400)
    ax.plot(z, 1 / (1 + np.exp(-z)), color=C.blue, lw=3.2)
    ax.axhline(0.5, color=C.grey, ls="--", lw=2)
    ax.axvline(0, color=C.grey, ls="--", lw=2)
    ax.set_xlabel("z = wᵀx + b   (log-odds)")
    ax.set_ylabel("σ(z) = P(y = 1)")
    ax.set_title("The sigmoid maps any real number\ninto a probability")
    ax.annotate("decision threshold", xy=(0, 0.5), xytext=(2.0, 0.22), fontsize=10.5,
                arrowprops=dict(arrowstyle="->", lw=1.7, color=C.black))

    ax = axes[1]
    X, y = two_blobs(seed=11)
    Xb = np.c_[np.ones(len(X)), X]
    w = np.zeros(3)
    for _ in range(3000):
        p = 1 / (1 + np.exp(-Xb @ w))
        w -= 0.06 * (Xb.T @ (p - y)) / len(X)
    xx, yy = mesh(X)
    P = 1 / (1 + np.exp(-(w[0] + w[1] * xx + w[2] * yy)))
    boundary(ax, xx, yy, (P > 0.5).astype(int))
    ax.contour(xx, yy, P, levels=[0.25, 0.75], colors=[C.grey], linewidths=1.6, linestyles="--")
    draw_points(ax, X, y)
    ax.set_title("A linear decision boundary\ndashed: p = 0.25 and 0.75")
    bare(ax)
    f.tight_layout()
    save(f, "classical/logistic-regression.png")


# ---------------------------------------------------------------- k-NN
def knn():
    """The k knob is the bias-variance knob, made visible."""
    X, y = moons(seed=13)
    xx, yy = mesh(X)
    grid_pts = np.c_[xx.ravel(), yy.ravel()]
    d = np.linalg.norm(grid_pts[:, None, :] - X[None, :, :], axis=2)
    order = np.argsort(d, axis=1)

    f, axes = grid(1, 3, 12.0, 4.0)
    for ax, k in zip(axes, [1, 15, 75]):
        vote = y[order[:, :k]].mean(axis=1)
        boundary(ax, xx, yy, (vote > 0.5).astype(int).reshape(xx.shape))
        draw_points(ax, X, y, s=26)
        label = {1: "k = 1 — every island is noise\n(high variance)",
                 15: "k = 15 — smooth, sensible",
                 75: "k = 75 — nearly linear\n(high bias)"}[k]
        ax.set_title(label, fontsize=12)
        bare(ax)
    f.tight_layout()
    save(f, "classical/knn-k-effect.png")


# ---------------------------------------------------------------- SVM
def svm_margin():
    """Hard-margin SVM by hand: the maximum-margin separator and its support vectors."""
    # Deliberately linearly separable, so this is a genuine *hard*-margin
    # picture: no point violates the margin, and the support vectors are
    # exactly the points sitting on it.
    r = np.random.default_rng(21)
    a = r.normal([-1.9, -1.2], 0.62, (35, 2))
    b = r.normal([2.0, 1.5], 0.62, (35, 2))
    X = np.vstack([a, b])
    y = np.r_[np.zeros(35), np.ones(35)].astype(int)
    ysign = np.where(y == 1, 1.0, -1.0)

    # Projected-gradient on the primal hinge objective with a tiny C penalty.
    w = np.zeros(2)
    b = 0.0
    lr, lam = 0.02, 0.02
    for _ in range(20000):
        marg = ysign * (X @ w + b)
        viol = marg < 1
        gw = lam * w - (ysign[viol, None] * X[viol]).sum(0) / len(X)
        gb = -(ysign[viol]).sum() / len(X)
        w -= lr * gw
        b -= lr * gb

    f, ax = fig(6.6, 5.2)
    xx, yy = mesh(X, pad=0.9)
    Z = (xx * w[0] + yy * w[1] + b)
    ax.contourf(xx, yy, (Z > 0).astype(int), levels=[-0.5, 0.5, 1.5], cmap=BG, alpha=0.8)
    ax.contour(xx, yy, Z, levels=[0], colors=[C.black], linewidths=3)
    ax.contour(xx, yy, Z, levels=[-1, 1], colors=[C.grey], linewidths=2, linestyles="--")

    sv = np.abs(ysign * (X @ w + b) - 1) < 0.12
    draw_points(ax, X, y, s=52)
    ax.scatter(X[sv, 0], X[sv, 1], s=280, facecolors="none", edgecolors=C.red, linewidths=3, zorder=6)
    margin = 2 / np.linalg.norm(w)
    ax.set_title(f"Maximum-margin separator\ncircled = support vectors; margin width ≈ {margin:.2f}")
    ax.text(0.02, 0.02, "Only the circled points define the boundary.\nDelete any other point and nothing moves.",
            transform=ax.transAxes, fontsize=10.5, va="bottom",
            bbox=dict(boxstyle="round,pad=0.45", fc="white", ec=C.light))
    bare(ax)
    f.tight_layout()
    save(f, "classical/svm-margin.png")


def kernel_trick():
    """Not separable in 2-D; separable in 3-D after a radial lift."""
    X, y = circles(n=110)
    f = __import__("matplotlib.pyplot", fromlist=["x"]).figure(figsize=(11.2, 4.4))

    ax = f.add_subplot(1, 2, 1)
    draw_points(ax, X, y, s=34)
    ax.set_title("Input space\nno straight line can separate these", fontsize=12.5)
    ax.set_aspect("equal")
    bare(ax)

    ax = f.add_subplot(1, 2, 2, projection="3d")
    z = np.exp(-(X**2).sum(1))  # the RBF-style lift
    ax.scatter(X[:, 0], X[:, 1], z, c=y, cmap=CMAP, s=32, edgecolors="white", linewidths=0.5)
    gx, gy = np.meshgrid(np.linspace(-1.6, 1.6, 12), np.linspace(-1.6, 1.6, 12))
    ax.plot_surface(gx, gy, np.full_like(gx, 0.62), color=C.grey, alpha=0.32)
    ax.set_title("Lifted by z = e^(−‖x‖²)\na flat plane now separates them", fontsize=12.5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.grid(False)
    f.tight_layout()
    save(f, "classical/kernel-trick.png")


# ---------------------------------------------------------------- trees & ensembles
def _fit_stump_tree(X, y, depth, max_depth):
    """Tiny CART on Gini, returning a nested dict."""
    if depth >= max_depth or len(np.unique(y)) == 1 or len(y) < 5:
        return {"leaf": float(y.mean())}
    best = None
    for feat in (0, 1):
        for thr in np.quantile(X[:, feat], np.linspace(0.08, 0.92, 24)):
            m = X[:, feat] <= thr
            if m.sum() < 3 or (~m).sum() < 3:
                continue
            def gini(v):
                if len(v) == 0:
                    return 0.0
                p = v.mean()
                return 1 - p**2 - (1 - p) ** 2
            score = (m.sum() * gini(y[m]) + (~m).sum() * gini(y[~m])) / len(y)
            if best is None or score < best[0]:
                best = (score, feat, thr, m)
    if best is None:
        return {"leaf": float(y.mean())}
    _, feat, thr, m = best
    return {"feat": feat, "thr": thr,
            "l": _fit_stump_tree(X[m], y[m], depth + 1, max_depth),
            "r": _fit_stump_tree(X[~m], y[~m], depth + 1, max_depth)}


def _pred_tree(node, P):
    if "leaf" in node:
        return np.full(len(P), node["leaf"])
    m = P[:, node["feat"]] <= node["thr"]
    out = np.empty(len(P))
    if m.any():
        out[m] = _pred_tree(node["l"], P[m])
    if (~m).any():
        out[~m] = _pred_tree(node["r"], P[~m])
    return out


def decision_trees():
    X, y = moons(seed=17)
    xx, yy = mesh(X)
    P = np.c_[xx.ravel(), yy.ravel()]
    f, axes = grid(1, 3, 12.0, 4.0)
    for ax, d in zip(axes, [1, 3, 12]):
        t = _fit_stump_tree(X, y.astype(float), 0, d)
        Z = (_pred_tree(t, P) > 0.5).astype(int).reshape(xx.shape)
        boundary(ax, xx, yy, Z)
        draw_points(ax, X, y, s=26)
        ax.set_title({1: "depth 1 — a single split",
                      3: "depth 3 — coarse but sane",
                      12: "depth 12 — memorising noise"}[d], fontsize=12.5)
        bare(ax)
    f.suptitle("Trees carve the space into axis-aligned rectangles — always",
               fontsize=13.5, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.92))
    save(f, "classical/decision-tree-depth.png")


def random_forest():
    X, y = moons(seed=19)
    xx, yy = mesh(X)
    P = np.c_[xx.ravel(), yy.ravel()]

    f, axes = grid(1, 2, 10.6, 4.3)
    t = _fit_stump_tree(X, y.astype(float), 0, 12)
    boundary(axes[0], xx, yy, (_pred_tree(t, P) > 0.5).astype(int).reshape(xx.shape))
    draw_points(axes[0], X, y, s=26)
    axes[0].set_title("One deep tree\njagged, overfit", fontsize=12.5)

    acc = np.zeros(len(P))
    n_trees = 60
    for i in range(n_trees):
        r = np.random.default_rng(100 + i)
        idx = r.integers(0, len(X), len(X))  # bootstrap sample
        acc += _pred_tree(_fit_stump_tree(X[idx], y[idx].astype(float), 0, 8), P)
    Z = (acc / n_trees > 0.5).astype(int).reshape(xx.shape)
    boundary(axes[1], xx, yy, Z)
    draw_points(axes[1], X, y, s=26)
    axes[1].set_title(f"{n_trees} bootstrapped trees, averaged\nsmooth, generalises", fontsize=12.5)
    for ax in axes:
        bare(ax)
    f.tight_layout()
    save(f, "classical/random-forest-smoothing.png")


def boosting_stages():
    """Boosting fits the residual left by the ensemble so far."""
    n = 70
    x = np.sort(rng.uniform(0, 10, n))
    truth = np.sin(x) * 2 + 0.3 * x
    y = truth + rng.normal(0, 0.35, n)

    def stump_fit(xv, resid):
        best = None
        for thr in np.linspace(xv.min() + 0.3, xv.max() - 0.3, 60):
            m = xv <= thr
            if m.sum() < 3 or (~m).sum() < 3:
                continue
            l, r = resid[m].mean(), resid[~m].mean()
            err = ((resid[m] - l) ** 2).sum() + ((resid[~m] - r) ** 2).sum()
            if best is None or err < best[0]:
                best = (err, thr, l, r)
        return best[1:]

    f, axes = grid(1, 4, 13.2, 3.6, sharey=True)
    pred = np.full(n, y.mean())
    lr = 0.5
    stages = {1: axes[1], 5: axes[2], 40: axes[3]}
    axes[0].scatter(x, y, c=C.grey, s=28)
    axes[0].plot(x, truth, color=C.green, lw=2.4, ls="--")
    axes[0].set_title("data + truth", fontsize=12)
    for m in range(1, 41):
        thr, l, r = stump_fit(x, y - pred)
        pred = pred + lr * np.where(x <= thr, l, r)
        if m in stages:
            ax = stages[m]
            ax.scatter(x, y, c=C.grey, s=28)
            ax.plot(x, truth, color=C.green, lw=2.0, ls="--")
            ax.plot(x, pred, color=C.red, lw=2.8)
            ax.set_title(f"after {m} stump{'s' if m > 1 else ''}", fontsize=12)
    for ax in axes:
        ax.set_xlabel("x")
    axes[0].set_ylabel("y")
    f.suptitle("Gradient boosting: each shallow tree corrects what the ensemble still gets wrong",
               fontsize=13.5, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.9))
    save(f, "classical/boosting-stages.png")


def bagging_vs_boosting():
    f, axes = grid(1, 2, 10.6, 3.9)
    ax = axes[0]
    for i in range(5):
        ax.add_patch(__import__("matplotlib.patches", fromlist=["x"]).Rectangle(
            (i * 1.5, 0), 1.15, 0.8, facecolor=C.blue, alpha=0.55, edgecolor="white", lw=2))
        ax.text(i * 1.5 + 0.58, 0.4, f"T{i+1}", ha="center", va="center", fontsize=11, color="white",
                fontweight="bold")
        ax.annotate("", xy=(i * 1.5 + 0.58, -0.15), xytext=(i * 1.5 + 0.58, 0.0),
                    arrowprops=dict(arrowstyle="->", lw=2, color=C.grey))
    ax.text(3.6, -0.62, "average / vote", ha="center", fontsize=12, fontweight="bold")
    ax.set_title("Bagging — independent, parallel\nreduces variance", fontsize=12.5)
    ax.set_xlim(-0.5, 8.0)
    ax.set_ylim(-1.1, 1.3)
    clean(ax)

    ax = axes[1]
    for i in range(5):
        ax.add_patch(__import__("matplotlib.patches", fromlist=["x"]).Rectangle(
            (i * 1.5, 0), 1.15, 0.8, facecolor=C.orange, edgecolor="white", lw=2))
        ax.text(i * 1.5 + 0.58, 0.4, f"T{i+1}", ha="center", va="center", fontsize=11, color="white",
                fontweight="bold")
        if i < 4:
            ax.annotate("", xy=((i + 1) * 1.5 - 0.02, 0.4), xytext=(i * 1.5 + 1.17, 0.4),
                        arrowprops=dict(arrowstyle="->", lw=2.4, color=C.black))
    ax.text(3.6, -0.62, "each fits the previous one's residual", ha="center", fontsize=12,
            fontweight="bold")
    ax.set_title("Boosting — sequential, dependent\nreduces bias", fontsize=12.5)
    ax.set_xlim(-0.5, 8.0)
    ax.set_ylim(-1.1, 1.3)
    clean(ax)
    f.tight_layout()
    save(f, "classical/bagging-vs-boosting.png")


# ---------------------------------------------------------------- clustering
def kmeans_steps():
    r = np.random.default_rng(4)
    cent_true = np.array([[-2.2, -1.6], [2.4, -1.0], [0.2, 2.6]])
    X = np.vstack([c + r.normal(0, 0.75, (55, 2)) for c in cent_true])
    cent = np.array([[-3.4, 2.6], [-3.0, 2.0], [-2.6, 2.9]])  # deliberately bad init

    f, axes = grid(1, 4, 13.2, 3.6)
    snaps = {0: axes[0], 1: axes[1], 3: axes[2], 12: axes[3]}
    for it in range(13):
        d = np.linalg.norm(X[:, None] - cent[None], axis=2)
        lab = d.argmin(1)
        if it in snaps:
            ax = snaps[it]
            ax.scatter(X[:, 0], X[:, 1], c=lab, cmap=ListedColormap([C.blue, C.orange, C.green]),
                       s=26, alpha=0.85)
            ax.scatter(cent[:, 0], cent[:, 1], marker="X", s=260, c=C.red, edgecolors="white",
                       linewidths=2, zorder=6)
            ax.set_title(f"iteration {it}", fontsize=12)
            bare(ax)
        for k in range(3):
            if (lab == k).any():
                cent[k] = X[lab == k].mean(0)
    f.suptitle("k-means: assign to nearest centroid, move centroid to the mean, repeat",
               fontsize=13.5, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.9))
    save(f, "classical/kmeans-iterations.png")


def kmeans_limits():
    """Where k-means fails, and the elbow that picks k."""
    f, axes = grid(1, 3, 12.2, 4.0)

    def run(X, k, seed=0):
        r = np.random.default_rng(seed)
        cent = X[r.choice(len(X), k, replace=False)]
        for _ in range(60):
            lab = np.linalg.norm(X[:, None] - cent[None], axis=2).argmin(1)
            for j in range(k):
                if (lab == j).any():
                    cent[j] = X[lab == j].mean(0)
        return lab, cent

    Xm, _ = moons(n=140, noise=0.08, seed=31)
    lab, cent = run(Xm, 2, seed=2)
    axes[0].scatter(Xm[:, 0], Xm[:, 1], c=lab, cmap=CMAP, s=26)
    axes[0].scatter(cent[:, 0], cent[:, 1], marker="X", s=240, c=C.red, edgecolors="white", linewidths=2)
    axes[0].set_title("k-means assumes round blobs\nso it splits the moons wrongly", fontsize=12)
    bare(axes[0])

    r = np.random.default_rng(9)
    A = r.normal([-1, 0], [2.4, 0.35], (150, 2))
    B = r.normal([3, 0], [0.4, 0.4], (60, 2))
    Xe = np.vstack([A, B])
    lab, cent = run(Xe, 2, seed=1)
    axes[1].scatter(Xe[:, 0], Xe[:, 1], c=lab, cmap=CMAP, s=26)
    axes[1].scatter(cent[:, 0], cent[:, 1], marker="X", s=240, c=C.red, edgecolors="white", linewidths=2)
    axes[1].set_title("Unequal spread breaks it too\nthe wide cluster gets cut in half", fontsize=12)
    bare(axes[1])

    cent_true = np.array([[-3, -2], [3, -2], [0, 3], [5, 3.5]])
    Xb = np.vstack([c + r.normal(0, 0.7, (60, 2)) for c in cent_true])
    ks = range(1, 9)
    inertias = []
    for k in ks:
        lab, cent = run(Xb, k, seed=3)
        inertias.append(((Xb - cent[lab]) ** 2).sum())
    axes[2].plot(list(ks), inertias, "o-", color=C.blue, ms=8)
    axes[2].scatter([4], [inertias[3]], s=280, facecolors="none", edgecolors=C.red, linewidths=3, zorder=6)
    axes[2].annotate("elbow — 4 true clusters", xy=(4, inertias[3]), xytext=(4.9, inertias[3] + inertias[0] * 0.28),
                     fontsize=11, arrowprops=dict(arrowstyle="->", lw=1.9, color=C.red))
    axes[2].set_xlabel("k")
    axes[2].set_ylabel("inertia (within-cluster SS)")
    axes[2].set_title("The elbow method picks k", fontsize=12)
    f.tight_layout()
    save(f, "classical/kmeans-limitations.png")


def dbscan_vs_kmeans():
    X, _ = moons(n=150, noise=0.07, seed=41)
    X = np.vstack([X, rng.uniform([-1.6, -1.2], [2.6, 1.6], (14, 2))])  # noise points

    def dbscan(Xd, eps, min_pts):
        n = len(Xd)
        D = np.linalg.norm(Xd[:, None] - Xd[None], axis=2)
        nbr = [np.flatnonzero(D[i] <= eps) for i in range(n)]
        lab = np.full(n, -1)
        cid = 0
        for i in range(n):
            if lab[i] != -1 or len(nbr[i]) < min_pts:
                continue
            stack, lab[i] = [i], cid
            while stack:
                j = stack.pop()
                if len(nbr[j]) >= min_pts:
                    for q in nbr[j]:
                        if lab[q] == -1:
                            lab[q] = cid
                            stack.append(q)
            cid += 1
        return lab

    f, axes = grid(1, 2, 10.6, 4.3)
    r = np.random.default_rng(2)
    cent = X[r.choice(len(X), 2, replace=False)]
    for _ in range(60):
        lab = np.linalg.norm(X[:, None] - cent[None], axis=2).argmin(1)
        for j in range(2):
            cent[j] = X[lab == j].mean(0)
    axes[0].scatter(X[:, 0], X[:, 1], c=lab, cmap=CMAP, s=30)
    axes[0].set_title("k-means (k = 2)\ncuts straight through both moons", fontsize=12.5)

    lab2 = dbscan(X, 0.26, 5)
    noise = lab2 == -1
    axes[1].scatter(X[~noise, 0], X[~noise, 1], c=lab2[~noise], cmap=CMAP, s=30)
    axes[1].scatter(X[noise, 0], X[noise, 1], c=C.grey, s=44, marker="x", linewidths=2.2)
    axes[1].set_title(f"DBSCAN\nfollows density, and labels {noise.sum()} points as noise (×)", fontsize=12.5)
    for ax in axes:
        bare(ax)
    f.tight_layout()
    save(f, "classical/dbscan-vs-kmeans.png")


def dendrogram():
    r = np.random.default_rng(12)
    pts = np.vstack([r.normal([0, 0], 0.35, (4, 2)), r.normal([3, 1], 0.35, (4, 2))])
    n = len(pts)
    clusters = {i: [i] for i in range(n)}
    heights = {}
    pos = {i: float(i) for i in range(n)}
    order = list(range(n))
    nxt = n
    active = dict(clusters)
    coords = {i: (float(i), 0.0) for i in range(n)}
    f, ax = fig(7.2, 4.4)
    while len(active) > 1:
        best = None
        for a in active:
            for b in active:
                if a >= b:
                    continue
                d = max(np.linalg.norm(pts[i] - pts[j]) for i in active[a] for j in active[b])
                if best is None or d < best[0]:
                    best = (d, a, b)
        d, a, b = best
        xa, ya = coords[a]
        xb, yb = coords[b]
        ax.plot([xa, xa, xb, xb], [ya, d, d, yb], color=C.blue, lw=2.4)
        coords[nxt] = ((xa + xb) / 2, d)
        active[nxt] = active[a] + active[b]
        del active[a], active[b]
        nxt += 1
    ax.axhline(2.0, color=C.red, ls="--", lw=2.4)
    ax.text(0.1, 2.12, "cut here → 2 clusters", color=C.red, fontsize=11.5, fontweight="bold")
    ax.set_xticks(range(n), [f"p{i}" for i in range(n)])
    ax.set_ylabel("merge distance")
    ax.set_title("Hierarchical clustering: the cut height chooses k\n(no need to fix k in advance)")
    f.tight_layout()
    save(f, "classical/dendrogram.png")


def gmm_vs_kmeans():
    r = np.random.default_rng(6)
    A = r.multivariate_normal([-1.2, 0], [[2.2, 1.2], [1.2, 0.9]], 180)
    B = r.multivariate_normal([2.4, 1.2], [[0.6, -0.35], [-0.35, 1.4]], 180)
    X = np.vstack([A, B])

    f, axes = grid(1, 2, 10.6, 4.3)
    cent = X[r.choice(len(X), 2, replace=False)]
    for _ in range(60):
        lab = np.linalg.norm(X[:, None] - cent[None], axis=2).argmin(1)
        for j in range(2):
            cent[j] = X[lab == j].mean(0)
    axes[0].scatter(X[:, 0], X[:, 1], c=lab, cmap=CMAP, s=20, alpha=0.8)
    axes[0].set_title("k-means — hard, spherical\nassignments", fontsize=12.5)

    # EM for a 2-component GMM.
    mu = X[r.choice(len(X), 2, replace=False)].astype(float)
    cov = np.array([np.cov(X.T)] * 2)
    pi = np.array([0.5, 0.5])
    for _ in range(120):
        dens = np.zeros((len(X), 2))
        for k in range(2):
            diff = X - mu[k]
            inv = np.linalg.inv(cov[k])
            dens[:, k] = pi[k] * np.exp(-0.5 * np.einsum("ij,jk,ik->i", diff, inv, diff)) / np.sqrt(
                np.linalg.det(cov[k]))
        resp = dens / dens.sum(1, keepdims=True)
        Nk = resp.sum(0)
        pi = Nk / len(X)
        for k in range(2):
            mu[k] = (resp[:, k, None] * X).sum(0) / Nk[k]
            diff = X - mu[k]
            cov[k] = (resp[:, k, None, None] * np.einsum("ij,ik->ijk", diff, diff)).sum(0) / Nk[k]

    axes[1].scatter(X[:, 0], X[:, 1], c=resp[:, 0], cmap="coolwarm", s=20, alpha=0.85)
    th = np.linspace(0, 2 * np.pi, 200)
    for k in range(2):
        vals, vecs = np.linalg.eigh(cov[k])
        for scale in (1.0, 2.0):
            ell = (vecs @ (np.sqrt(vals)[:, None] * np.stack([np.cos(th), np.sin(th)])) * scale).T + mu[k]
            axes[1].plot(ell[:, 0], ell[:, 1], color=C.black, lw=2.2)
    axes[1].set_title("GMM — soft, elliptical\ncolour = P(component 1)", fontsize=12.5)
    for ax in axes:
        bare(ax)
    f.tight_layout()
    save(f, "classical/gmm-vs-kmeans.png")


# ---------------------------------------------------------------- PCA
def pca():
    r = np.random.default_rng(3)
    X = r.multivariate_normal([0, 0], [[3.2, 2.1], [2.1, 1.9]], 260)
    Xc = X - X.mean(0)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)

    f, axes = grid(1, 3, 12.4, 4.0)
    ax = axes[0]
    ax.scatter(*Xc.T, s=22, c=C.grey, alpha=0.7)
    for i in range(2):
        v = Vt[i] * S[i] / np.sqrt(len(Xc)) * 2.2
        ax.annotate("", xy=v, xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=3.4,
                                                             color=[C.blue, C.orange][i]))
        ax.text(*(v * 1.16), f"PC{i+1}", fontsize=12.5, fontweight="bold",
                color=[C.blue, C.orange][i], ha="center")
    ax.set_title("PC1 is the direction of\nmaximum variance", fontsize=12.5)
    ax.set_aspect("equal")

    ax = axes[1]
    proj = Xc @ Vt.T
    ax.scatter(*proj.T, s=22, c=C.blue, alpha=0.7)
    ax.axhline(0, color=C.black, lw=1.4)
    ax.axvline(0, color=C.black, lw=1.4)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title("Rotated into the PC basis\nnow uncorrelated", fontsize=12.5)
    ax.set_aspect("equal")

    ax = axes[2]
    var = S**2 / (S**2).sum()
    many = np.array([0.42, 0.23, 0.13, 0.08, 0.055, 0.035, 0.02, 0.015, 0.008, 0.007])
    ax.bar(range(1, 11), many, color=C.blue, alpha=0.85, label="individual")
    ax.plot(range(1, 11), np.cumsum(many), "o-", color=C.red, label="cumulative")
    ax.axhline(0.9, color=C.grey, ls="--", lw=2)
    ax.text(5.4, 0.92, "90 % of variance", fontsize=10.5, color=C.grey)
    ax.set_xlabel("component")
    ax.set_ylabel("fraction of variance")
    ax.set_title("Scree plot chooses the\nnumber of components", fontsize=12.5)
    ax.legend(fontsize=10)
    f.tight_layout()
    save(f, "classical/pca-explained.png")


# ---------------------------------------------------------------- imbalance
def imbalanced():
    f, axes = grid(1, 3, 12.2, 3.8)
    r = np.random.default_rng(8)
    maj = r.normal([0, 0], 1.0, (400, 2))
    minr = r.normal([1.9, 1.7], 0.6, (25, 2))

    axes[0].scatter(*maj.T, s=18, c=C.blue, alpha=0.55, label="majority (400)")
    axes[0].scatter(*minr.T, s=52, c=C.orange, edgecolors=C.black, linewidths=0.8, label="minority (25)")
    axes[0].set_title("Original — 94 % / 6 %\naccuracy 94 % by always saying 'majority'", fontsize=11.5)
    axes[0].legend(fontsize=9.5, loc="lower right")

    keep = maj[r.choice(len(maj), 60, replace=False)]
    axes[1].scatter(*keep.T, s=18, c=C.blue, alpha=0.55)
    axes[1].scatter(*minr.T, s=52, c=C.orange, edgecolors=C.black, linewidths=0.8)
    axes[1].set_title("Undersample majority\ncheap, but throws away data", fontsize=11.5)

    synth = []
    for _ in range(120):
        i, j = r.choice(len(minr), 2, replace=False)
        lam = r.uniform(0, 1)
        synth.append(minr[i] + lam * (minr[j] - minr[i]))  # SMOTE interpolation
    synth = np.array(synth)
    axes[2].scatter(*maj.T, s=18, c=C.blue, alpha=0.55)
    axes[2].scatter(*synth.T, s=30, c=C.green, alpha=0.75, marker="^", label="synthetic")
    axes[2].scatter(*minr.T, s=52, c=C.orange, edgecolors=C.black, linewidths=0.8, label="real")
    axes[2].set_title("SMOTE — interpolate new minority\npoints between real ones", fontsize=11.5)
    axes[2].legend(fontsize=9.5, loc="lower right")
    for ax in axes:
        bare(ax)
    f.tight_layout()
    save(f, "classical/imbalanced-resampling.png")


# ---------------------------------------------------------------- tuning
def search_strategies():
    """Bergstra & Bengio's point: random search wins when only one axis matters."""
    f, axes = grid(1, 2, 10.6, 4.6)
    important = lambda v: np.exp(-((v - 0.62) ** 2) / 0.02)

    for ax, kind in [(axes[0], "grid"), (axes[1], "random")]:
        if kind == "grid":
            g = np.linspace(0.1, 0.9, 5)
            px, py = np.meshgrid(g, g)
            px, py = px.ravel(), py.ravel()
        else:
            r = np.random.default_rng(11)
            px, py = r.uniform(0.05, 0.95, 25), r.uniform(0.05, 0.95, 25)
        ax.scatter(px, py, s=80, c=C.blue, zorder=5, edgecolors="white", linewidths=1)
        xs = np.linspace(0, 1, 300)
        ax.plot(xs, 0.06 + 0.16 * important(xs), color=C.orange, lw=2.6, transform=ax.transAxes)
        ax.axvline(0.62, color=C.red, ls="--", lw=2.2)
        tried = len(np.unique(np.round(px, 6)))
        ax.set_title(f"{'Grid' if kind=='grid' else 'Random'} search — 25 trials\n"
                     f"{tried} distinct values of the parameter that matters",
                     fontsize=12.5)
        ax.set_xlabel("parameter that matters")
        ax.set_ylabel("parameter that doesn't")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
    f.tight_layout()
    save(f, "classical/grid-vs-random-search.png")


def validation_curve():
    f, ax = fig(7.2, 4.3)
    c = np.logspace(-3, 3, 40)
    train = 0.06 + 0.62 * np.exp(-((np.log10(c) + 3) / 1.7))
    val = train + 0.05 + 0.055 * np.clip(np.log10(c) + 0.4, 0, None) ** 1.9
    ax.plot(c, train, color=C.blue, label="training error")
    ax.plot(c, val, color=C.orange, label="validation error")
    ax.set_xscale("log")
    k = int(np.argmin(val))
    ax.axvline(c[k], color=C.red, ls="--", lw=2.2)
    ax.scatter([c[k]], [val[k]], s=150, c=C.red, zorder=6)
    ax.text(c[k] * 1.3, val[k] + 0.14, "best setting", color=C.red, fontsize=11, fontweight="bold")
    ax.annotate("underfit", xy=(2e-3, 0.55), fontsize=12, color=C.grey)
    ax.annotate("overfit", xy=(2e2, 0.55), fontsize=12, color=C.grey)
    ax.set_xlabel("model complexity  (e.g. SVM C, tree depth)")
    ax.set_ylabel("error")
    ax.set_title("A validation curve locates the complexity sweet spot")
    ax.legend()
    f.tight_layout()
    save(f, "classical/validation-curve.png")


def anomaly_detection():
    f, axes = grid(1, 2, 10.6, 4.2)
    r = np.random.default_rng(15)
    inl = r.normal([0, 0], 0.85, (280, 2))
    out = r.uniform(-4, 4, (18, 2))
    X = np.vstack([inl, out])

    xx, yy = np.meshgrid(np.linspace(-4.5, 4.5, 260), np.linspace(-4.5, 4.5, 260))
    mu, cov = inl.mean(0), np.cov(inl.T)
    inv = np.linalg.inv(cov)
    P = np.stack([xx.ravel(), yy.ravel()], 1) - mu
    md = np.einsum("ij,jk,ik->i", P, inv, P).reshape(xx.shape)

    ax = axes[0]
    ax.scatter(*X.T, s=22, c=C.grey, alpha=0.8)
    ax.contour(xx, yy, md, levels=[4, 9, 16], colors=[C.blue], linewidths=2)
    ax.set_title("Density model of 'normal'\ncontours = Mahalanobis distance", fontsize=12.5)

    ax = axes[1]
    score = np.einsum("ij,jk,ik->i", X - mu, inv, X - mu)
    flag = score > 9
    ax.scatter(X[~flag, 0], X[~flag, 1], s=22, c=C.blue, alpha=0.7, label="inlier")
    ax.scatter(X[flag, 0], X[flag, 1], s=95, c=C.red, marker="X", label=f"flagged ({flag.sum()})")
    ax.contour(xx, yy, md, levels=[9], colors=[C.black], linewidths=2.6)
    ax.set_title("Threshold the score\nthe threshold is a business decision", fontsize=12.5)
    ax.legend(fontsize=10, loc="upper left")
    for ax in axes:
        bare(ax)
    f.tight_layout()
    save(f, "classical/anomaly-detection.png")


def manifold_learning():
    f = __import__("matplotlib.pyplot", fromlist=["x"]).figure(figsize=(11.4, 4.2))
    r = np.random.default_rng(21)
    t = 1.5 * np.pi * (1 + 2 * r.uniform(size=700))
    h = 21 * r.uniform(size=700)
    X = np.stack([t * np.cos(t), h, t * np.sin(t)], 1)

    ax = f.add_subplot(1, 2, 1, projection="3d")
    ax.scatter(X[:, 0], X[:, 1], X[:, 2], c=t, cmap="viridis", s=14)
    ax.set_title("Swiss roll in 3-D\nEuclidean distance is misleading", fontsize=12.5)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])
    ax.grid(False)

    ax = f.add_subplot(1, 2, 2)
    ax.scatter(t, h, c=t, cmap="viridis", s=14)
    ax.set_title("Unrolled: the true 2-D structure\nwhat manifold learning recovers", fontsize=12.5)
    bare(ax)
    f.tight_layout()
    save(f, "classical/manifold-swiss-roll.png")


def naive_bayes():
    f, axes = grid(1, 2, 10.6, 4.2)
    x = np.linspace(-4, 8, 400)
    for mu, s, col, lbl in [(0.6, 1.0, C.blue, "P(x | spam)"), (3.4, 1.3, C.orange, "P(x | ham)")]:
        ax = axes[0]
        ax.plot(x, np.exp(-0.5 * ((x - mu) / s) ** 2) / (s * np.sqrt(2 * np.pi)), color=col, label=lbl)
        ax.fill_between(x, np.exp(-0.5 * ((x - mu) / s) ** 2) / (s * np.sqrt(2 * np.pi)),
                        color=col, alpha=0.18)
    axes[0].set_title("Class-conditional densities\nmodelled per feature, independently", fontsize=12.5)
    axes[0].set_xlabel("feature value")
    axes[0].legend(fontsize=10.5)

    ax = axes[1]
    r = np.random.default_rng(5)
    X = np.vstack([r.multivariate_normal([-1, -1], [[1.4, 1.1], [1.1, 1.4]], 160),
                   r.multivariate_normal([2, 2], [[1.4, 1.1], [1.1, 1.4]], 160)])
    y = np.r_[np.zeros(160), np.ones(160)].astype(int)
    xx, yy = mesh(X)
    logp = []
    for k in (0, 1):
        Xi = X[y == k]
        m, v = Xi.mean(0), Xi.var(0)  # diagonal covariance — the naive assumption
        lp = -0.5 * ((xx - m[0]) ** 2 / v[0] + (yy - m[1]) ** 2 / v[1]) - 0.5 * np.log(v.prod())
        logp.append(lp)
    boundary(ax, xx, yy, (logp[1] > logp[0]).astype(int))
    draw_points(ax, X, y, s=22)
    ax.set_title("The 'naive' independence assumption\nignores the visible correlation — and still works",
                 fontsize=12)
    bare(ax)
    f.tight_layout()
    save(f, "classical/naive-bayes.png")


if __name__ == "__main__":
    print("classical:")
    linear_regression()
    anscombe()
    logistic_regression()
    knn()
    svm_margin()
    kernel_trick()
    decision_trees()
    random_forest()
    boosting_stages()
    bagging_vs_boosting()
    kmeans_steps()
    kmeans_limits()
    dbscan_vs_kmeans()
    dendrogram()
    gmm_vs_kmeans()
    pca()
    imbalanced()
    search_strategies()
    validation_curve()
    anomaly_detection()
    manifold_learning()
    naive_bayes()
