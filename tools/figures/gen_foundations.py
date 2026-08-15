"""Figures for docs/machine-learning/00-foundations/."""

import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

from kbstyle import C, clean, fig, grid, save

rng = np.random.default_rng(0)


# --------------------------------------------------------------------------
# learning-paradigms.md
# --------------------------------------------------------------------------
def learning_paradigms():
    f, axes = grid(1, 3, 11.5, 3.8)

    # Supervised: labelled points with a decision boundary.
    ax = axes[0]
    a = rng.normal([-1.1, -0.8], 0.62, (45, 2))
    b = rng.normal([1.2, 1.0], 0.62, (45, 2))
    ax.scatter(*a.T, c=C.blue, s=42, edgecolors="white", linewidths=0.8, label="class A")
    ax.scatter(*b.T, c=C.orange, s=42, marker="s", edgecolors="white", linewidths=0.8, label="class B")
    xs = np.linspace(-3.2, 3.2, 10)
    ax.plot(xs, -0.85 * xs + 0.15, color=C.black, lw=2.6, ls="--")
    ax.set_title("Supervised\nlabels given")
    ax.legend(loc="upper left", fontsize=10)

    # Unsupervised: same points, no labels, discovered groups.
    ax = axes[1]
    allpts = np.vstack([a, b])
    ax.scatter(*allpts.T, c=C.grey, s=42, edgecolors="white", linewidths=0.8)
    for cx, cy, col in [(-1.1, -0.8, C.blue), (1.2, 1.0, C.orange)]:
        ax.add_patch(Circle((cx, cy), 1.5, fill=False, ec=col, lw=2.6, ls="--"))
    ax.set_title("Unsupervised\nstructure discovered")

    # Reinforcement: a trajectory collecting reward.
    ax = axes[2]
    t = np.linspace(0, 1, 40)
    px = -2.6 + 5.0 * t + 0.5 * np.sin(7 * t)
    py = -2.2 + 4.2 * t + 0.7 * np.sin(5 * t)
    ax.plot(px, py, color=C.green, lw=2.8)
    ax.scatter([px[0]], [py[0]], c=C.green, s=110, zorder=5, label="start")
    ax.scatter([px[-1]], [py[-1]], c=C.red, s=190, marker="*", zorder=5, label="goal")
    for gx, gy in [(-0.9, 0.3), (0.7, 1.2)]:
        ax.scatter([gx], [gy], c=C.yellow, s=95, marker="D", edgecolors=C.black, linewidths=1.0, zorder=4)
    ax.set_title("Reinforcement\nreward along the way")
    ax.legend(loc="upper left", fontsize=10)

    for ax in axes:
        ax.set_xlim(-3.2, 3.2)
        ax.set_ylim(-3.0, 3.0)
        ax.set_xticks([])
        ax.set_yticks([])
    f.tight_layout()
    save(f, "foundations/learning-paradigms.png")


# --------------------------------------------------------------------------
# gradient-descent.md
# --------------------------------------------------------------------------
def gradient_descent_lr():
    """The three learning-rate regimes on one elongated quadratic bowl."""
    f, axes = grid(1, 3, 12.0, 4.1)

    def loss(x, y):
        return 0.16 * x**2 + y**2

    def gradient(p):
        return np.array([0.32 * p[0], 2.0 * p[1]])

    X, Y = np.meshgrid(np.linspace(-5.4, 5.4, 320), np.linspace(-3.0, 3.0, 320))
    Z = loss(X, Y)
    levels = np.linspace(0.15, Z.max(), 14)

    for ax, lr, title in [
        (axes[0], 0.06, "Too small\ncrawls, never arrives"),
        (axes[1], 0.42, "Well chosen\nsteady descent"),
        (axes[2], 1.02, "Too large\noscillates and diverges"),
    ]:
        ax.contour(X, Y, Z, levels=levels, colors=C.light, linewidths=1.1)
        p = np.array([-4.8, 2.4])
        path = [p.copy()]
        for _ in range(28):
            p = p - lr * gradient(p)
            if not np.isfinite(p).all() or np.abs(p).max() > 40:
                break
            path.append(p.copy())
        path = np.array(path)
        inside = (np.abs(path[:, 0]) <= 5.4) & (np.abs(path[:, 1]) <= 3.0)
        ax.plot(path[inside, 0], path[inside, 1], "-o", color=C.blue, lw=2.4, ms=5.5, zorder=4)
        ax.scatter([path[0, 0]], [path[0, 1]], c=C.green, s=120, zorder=6, label="start")
        ax.scatter([0], [0], marker="*", c=C.red, s=250, zorder=6, label="minimum")
        ax.set_title(title)
        ax.set_xlim(-5.4, 5.4)
        ax.set_ylim(-3.0, 3.0)
        ax.set_xticks([])
        ax.set_yticks([])
    axes[0].legend(loc="lower right", fontsize=10)
    f.tight_layout()
    save(f, "foundations/learning-rate-regimes.png")


def gradient_descent_variants():
    """Batch vs mini-batch vs stochastic: the noise/step-count trade-off."""
    f, ax = fig(7.0, 4.4)

    def curve(noise, steps, seed):
        r = np.random.default_rng(seed)
        loss = 2.6
        out = [loss]
        for _ in range(steps):
            loss = max(0.06, loss * 0.965 + r.normal(0, noise))
            out.append(loss)
        return np.array(out)

    ax.plot(curve(0.0, 200, 1), color=C.blue, label="Batch — every example per step")
    ax.plot(curve(0.035, 200, 2), color=C.orange, label="Mini-batch — a sample per step")
    ax.plot(curve(0.13, 200, 3), color=C.red, alpha=0.85, label="Stochastic — one example per step")
    ax.set_xlabel("update step")
    ax.set_ylabel("loss")
    ax.set_title("Gradient noise rises as the batch shrinks")
    ax.legend()
    f.tight_layout()
    save(f, "foundations/gradient-descent-variants.png")


# --------------------------------------------------------------------------
# bias-variance-tradeoff.md
# --------------------------------------------------------------------------
def bias_variance():
    f, axes = grid(1, 2, 11.4, 4.3)

    # Left: polynomial fits at three capacities.
    ax = axes[0]
    xs = np.linspace(0, 1, 14)
    truth = lambda t: np.sin(2 * np.pi * t)
    ys = truth(xs) + rng.normal(0, 0.22, xs.size)
    fine = np.linspace(0, 1, 300)
    ax.plot(fine, truth(fine), color=C.grey, lw=2.2, ls="--", label="true function")
    ax.scatter(xs, ys, c=C.black, s=48, zorder=5, label="training data")
    for deg, col, lbl in [(1, C.red, "degree 1 — underfit"), (3, C.green, "degree 3 — good"), (12, C.orange, "degree 12 — overfit")]:
        coef = np.polyfit(xs, ys, deg)
        ax.plot(fine, np.polyval(coef, fine), color=col, lw=2.5, label=lbl)
    ax.set_ylim(-2.1, 2.1)
    ax.set_title("Model capacity, three ways")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend(fontsize=9.5, loc="lower left")

    # Right: the canonical decomposition.
    ax = axes[1]
    cap = np.linspace(0.35, 10, 300)
    bias2 = 3.4 / cap**1.35
    var = 0.045 * cap**1.5
    noise = np.full_like(cap, 0.35)
    total = bias2 + var + noise
    ax.plot(cap, bias2, color=C.blue, label="bias²")
    ax.plot(cap, var, color=C.orange, label="variance")
    ax.plot(cap, noise, color=C.grey, ls=":", lw=2.2, label="irreducible noise")
    ax.plot(cap, total, color=C.red, lw=3.2, label="total error")
    best = cap[np.argmin(total)]
    ax.axvline(best, color=C.black, ls="--", lw=1.8)
    ax.annotate("sweet spot", xy=(best, np.min(total)), xytext=(best + 1.5, np.min(total) + 1.5),
                fontsize=11, arrowprops=dict(arrowstyle="->", lw=1.8, color=C.black))
    ax.set_xlabel("model capacity →")
    ax.set_ylabel("expected test error")
    ax.set_title("The trade-off")
    ax.set_ylim(0, 4.2)
    ax.legend(fontsize=10)
    f.tight_layout()
    save(f, "foundations/bias-variance-tradeoff.png")


# --------------------------------------------------------------------------
# overfitting-and-regularization.md
# --------------------------------------------------------------------------
def learning_curves():
    f, ax = fig(7.2, 4.4)
    ep = np.arange(1, 81)
    train = 1.9 * np.exp(-ep / 16) + 0.06
    val = 1.9 * np.exp(-ep / 13) + 0.20 + 0.0016 * np.clip(ep - 26, 0, None) ** 1.55
    ax.plot(ep, train, color=C.blue, label="training loss")
    ax.plot(ep, val, color=C.orange, label="validation loss")
    k = int(np.argmin(val))
    ax.scatter([ep[k]], [val[k]], s=150, c=C.red, zorder=6)
    ax.axvline(ep[k], color=C.red, ls="--", lw=1.8)
    ax.annotate("early-stopping point\n(validation minimum)", xy=(ep[k], val[k]),
                xytext=(ep[k] + 12, val[k] + 0.75), fontsize=11,
                arrowprops=dict(arrowstyle="->", lw=1.8, color=C.red))
    ax.axvspan(ep[k], ep[-1], color=C.red, alpha=0.07)
    ax.text(ep[k] + 24, 0.13, "overfitting:\ntrain ↓  val ↑", fontsize=11, color=C.red, ha="center")
    ax.set_xlabel("epoch")
    ax.set_ylabel("loss")
    ax.set_title("The gap between the curves is the overfit")
    ax.legend()
    f.tight_layout()
    save(f, "foundations/learning-curves-overfitting.png")


def regularization_paths():
    """Ridge vs lasso coefficient paths — lasso zeroes, ridge only shrinks."""
    f, axes = grid(1, 2, 11.4, 4.2, sharey=True)
    n, p = 60, 8
    X = rng.normal(size=(n, p))
    beta = np.array([3.0, -2.2, 1.5, 0.0, 0.0, 0.0, 0.0, 0.0])
    y = X @ beta + rng.normal(0, 0.6, n)
    alphas = np.logspace(-2, 2.2, 60)

    ridge = np.array([np.linalg.solve(X.T @ X + a * np.eye(p), X.T @ y) for a in alphas])

    def lasso(Xm, yv, a, iters=400):
        b = np.zeros(Xm.shape[1])
        norms = (Xm**2).sum(0)
        for _ in range(iters):
            for j in range(Xm.shape[1]):
                r = yv - Xm @ b + Xm[:, j] * b[j]
                rho = Xm[:, j] @ r
                b[j] = np.sign(rho) * max(abs(rho) - a, 0) / norms[j]
        return b

    las = np.array([lasso(X, y, a) for a in alphas])

    for ax, paths, title in [(axes[0], ridge, "Ridge (L2) — shrinks toward zero"),
                             (axes[1], las, "Lasso (L1) — sets coefficients to zero")]:
        for j in range(p):
            ax.plot(alphas, paths[:, j], color=C.cycle[j % len(C.cycle)], lw=2.3)
        ax.set_xscale("log")
        ax.axhline(0, color=C.black, lw=1.4)
        ax.set_xlabel("regularization strength α  (log scale)")
        ax.set_title(title, fontsize=13)
    axes[0].set_ylabel("coefficient value")
    f.tight_layout()
    save(f, "foundations/ridge-vs-lasso-paths.png")


def l1_l2_geometry():
    """Why L1 produces exact zeros: the constraint region has corners.

    The constrained optimum is *solved for* rather than placed by eye, so the
    drawn contour is genuinely tangent to the constraint boundary — that
    tangency is the whole argument the figure is making.
    """
    # Elongated, correlated quadratic loss: (b - bhat)' A (b - bhat).
    # Chosen so the L1 optimum lands exactly on the corner (0, t) while the L2
    # optimum lands off-axis — the contrast the figure exists to show.
    bhat = np.array([2.0, 3.0])
    A = np.array([[1.0, 0.8], [0.8, 1.0]])
    t = 1.0  # constraint budget

    def loss(b1, b2):
        d1, d2 = b1 - bhat[0], b2 - bhat[1]
        return A[0, 0] * d1**2 + 2 * A[0, 1] * d1 * d2 + A[1, 1] * d2**2

    th = np.linspace(0, 2 * np.pi, 2001)
    # Boundary parametrisations, then an argmin over a dense sample of each.
    l2_pts = np.stack([t * np.cos(th), t * np.sin(th)])
    s = np.linspace(-1, 1, 2001)
    l1_pts = np.concatenate(
        [np.stack([t * s, t * (1 - np.abs(s))]), np.stack([t * s, -t * (1 - np.abs(s))])], axis=1
    )

    X, Y = np.meshgrid(np.linspace(-2.2, 4.4, 600), np.linspace(-2.2, 4.4, 600))
    Z = loss(X, Y)

    f, axes = grid(1, 2, 10.4, 5.0)
    panels = [
        (axes[0], l2_pts, l2_pts, "L2 (ridge): round boundary\ntangency lands off the axes"),
        (axes[1], l1_pts, np.stack([[t, 0, -t, 0, t], [0, t, 0, -t, 0.0]]),
         "L1 (lasso): corners sit on the axes\ntangency lands on one — β₁ = 0 exactly"),
    ]

    for ax, cand, poly, title in panels:
        sol = cand[:, np.argmin(loss(cand[0], cand[1]))]
        lvl = loss(sol[0], sol[1])

        ax.fill(poly[0], poly[1], color=C.blue, alpha=0.22)
        ax.plot(poly[0], poly[1], color=C.blue, lw=2.8)

        # Interior contours, plus the tangent one through the solution.
        ax.contour(X, Y, Z, levels=[lvl * 0.18, lvl * 0.55], colors=[C.orange], linewidths=1.8, alpha=0.75)
        ax.contour(X, Y, Z, levels=[lvl], colors=[C.orange], linewidths=3.0)

        ax.scatter(*bhat, c=C.orange, s=130, zorder=6, edgecolors="white", linewidths=1.5)
        ax.annotate("unconstrained\noptimum  β̂", xy=bhat, xytext=(bhat[0] - 0.05, bhat[1] + 0.45),
                    fontsize=10.5, ha="center", color="#B07500")
        ax.scatter(*sol, c=C.red, s=200, zorder=7, edgecolors="white", linewidths=1.5)
        ax.annotate("solution", xy=sol, xytext=(sol[0] - 1.35, sol[1] - 1.15),
                    fontsize=11.5, fontweight="bold", color=C.red,
                    arrowprops=dict(arrowstyle="->", lw=2.0, color=C.red))

        ax.axhline(0, color=C.black, lw=1.4, zorder=1)
        ax.axvline(0, color=C.black, lw=1.4, zorder=1)
        ax.set_xlim(-1.8, 3.7)
        ax.set_ylim(-1.8, 3.9)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        ax.set_title(title, fontsize=12.5)
        ax.set_xlabel("β₁")
        ax.set_ylabel("β₂")
        print(f"    solution = ({sol[0]:+.3f}, {sol[1]:+.3f})")

    f.tight_layout()
    save(f, "foundations/l1-l2-constraint-geometry.png")


# --------------------------------------------------------------------------
# loss-functions.md
# --------------------------------------------------------------------------
def loss_functions():
    f, axes = grid(1, 2, 11.4, 4.2)

    ax = axes[0]
    r = np.linspace(-3, 3, 400)
    ax.plot(r, r**2, color=C.blue, label="squared error (MSE)")
    ax.plot(r, np.abs(r), color=C.orange, label="absolute error (MAE)")
    d = 1.0
    huber = np.where(np.abs(r) <= d, 0.5 * r**2, d * (np.abs(r) - 0.5 * d))
    ax.plot(r, huber, color=C.green, label="Huber (δ = 1)")
    ax.axvspan(-1, 1, color=C.green, alpha=0.07)
    ax.set_xlabel("residual  (prediction − target)")
    ax.set_ylabel("loss")
    ax.set_title("Regression losses")
    ax.set_ylim(0, 5)
    ax.legend(fontsize=10.5)

    ax = axes[1]
    p = np.linspace(0.001, 0.999, 400)
    ax.plot(p, -np.log(p), color=C.blue, label="−log p   (true class = 1)")
    ax.plot(p, -np.log(1 - p), color=C.orange, label="−log(1−p)  (true class = 0)")
    m = np.linspace(-2, 3, 400)
    ax.plot((m + 2) / 5, np.clip(1 - m, 0, None), color=C.green, ls="--", label="hinge (SVM), rescaled x")
    ax.set_xlabel("predicted probability p")
    ax.set_ylabel("loss")
    ax.set_title("Classification losses")
    ax.set_ylim(0, 6)
    ax.legend(fontsize=10)
    ax.annotate("confident and wrong\n→ unbounded penalty", xy=(0.03, 3.5), xytext=(0.33, 4.6),
                fontsize=10, arrowprops=dict(arrowstyle="->", lw=1.6, color=C.black))
    f.tight_layout()
    save(f, "foundations/loss-functions.png")


# --------------------------------------------------------------------------
# evaluation-metrics-classification.md
# --------------------------------------------------------------------------
def confusion_matrix_fig():
    f, ax = fig(5.8, 4.8)
    cm = np.array([[850, 50], [30, 70]])
    ax.imshow(cm, cmap="Blues", vmin=0, vmax=cm.max() * 1.15)
    names = [["True negative\n850", "False positive\n50\n(Type I)"],
             ["False negative\n30\n(Type II)", "True positive\n70"]]
    for i in range(2):
        for j in range(2):
            ax.text(j, i, names[i][j], ha="center", va="center", fontsize=11.5,
                    color="white" if cm[i, j] > cm.max() * 0.5 else C.black, fontweight="bold")
    ax.set_xticks([0, 1], ["predicted\nnegative", "predicted\npositive"])
    ax.set_yticks([0, 1], ["actual\nnegative", "actual\npositive"])
    ax.set_title("Confusion matrix\n1000 samples, 10 % positive")
    ax.grid(False)
    f.tight_layout()
    save(f, "foundations/confusion-matrix.png")


def roc_and_pr():
    """ROC looks great on imbalanced data; PR tells the truth."""
    n_neg, n_pos = 2000, 100
    s_neg = rng.beta(2, 5, n_neg)
    s_pos = rng.beta(5, 2.2, n_pos)
    scores = np.concatenate([s_neg, s_pos])
    labels = np.concatenate([np.zeros(n_neg), np.ones(n_pos)])
    order = np.argsort(-scores)
    lab = labels[order]
    tp = np.cumsum(lab)
    fp = np.cumsum(1 - lab)
    tpr = tp / n_pos
    fpr = fp / n_neg
    precision = tp / (tp + fp)

    f, axes = grid(1, 2, 11.0, 4.4)
    ax = axes[0]
    ax.plot(fpr, tpr, color=C.blue, lw=3)
    ax.plot([0, 1], [0, 1], color=C.grey, ls="--", lw=2)
    auc = np.trapezoid(tpr, fpr)
    ax.fill_between(fpr, tpr, alpha=0.15, color=C.blue)
    ax.set_xlabel("false positive rate")
    ax.set_ylabel("true positive rate (recall)")
    ax.set_title(f"ROC curve — AUC ≈ {auc:.2f}\nlooks excellent")
    ax.text(0.55, 0.15, "chance", color=C.grey, fontsize=11, rotation=32)

    ax = axes[1]
    ax.plot(tpr, precision, color=C.orange, lw=3)
    base = n_pos / (n_pos + n_neg)
    ax.axhline(base, color=C.grey, ls="--", lw=2)
    ax.text(0.42, base + 0.03, f"chance = {base:.2f} (positive rate)", color=C.grey, fontsize=10.5)
    ax.set_xlabel("recall")
    ax.set_ylabel("precision")
    ax.set_ylim(0, 1.02)
    ax.set_title("Precision–recall — same model\nthe weakness is visible")
    for a in axes:
        a.set_xlim(0, 1)
    f.tight_layout()
    save(f, "foundations/roc-vs-precision-recall.png")


def threshold_tradeoff():
    f, ax = fig(7.2, 4.3)
    x = np.linspace(-4, 6, 500)
    neg = np.exp(-0.5 * ((x - 0.0) / 1.0) ** 2)
    pos = np.exp(-0.5 * ((x - 2.6) / 1.0) ** 2)
    ax.fill_between(x, neg, color=C.blue, alpha=0.35, label="actual negatives")
    ax.fill_between(x, pos, color=C.orange, alpha=0.35, label="actual positives")
    t = 1.55
    ax.axvline(t, color=C.black, lw=2.6)
    ax.text(t + 0.1, 1.05, "threshold", fontsize=11.5, fontweight="bold")
    ax.fill_between(x, neg, where=(x > t), color=C.red, alpha=0.55)
    ax.fill_between(x, pos, where=(x <= t), color=C.purple, alpha=0.55)
    ax.annotate("false positives", xy=(2.0, 0.16), xytext=(3.3, 0.62), fontsize=11,
                color=C.red, arrowprops=dict(arrowstyle="->", lw=1.8, color=C.red))
    ax.annotate("false negatives", xy=(1.15, 0.16), xytext=(-3.7, 0.62), fontsize=11,
                color=C.purple, arrowprops=dict(arrowstyle="->", lw=1.8, color=C.purple))
    ax.set_xlabel("model score")
    ax.set_ylabel("density")
    ax.set_title("Moving the threshold trades one error type for the other")
    ax.set_ylim(0, 1.25)
    ax.legend(loc="upper left", fontsize=10.5)
    f.tight_layout()
    save(f, "foundations/threshold-tradeoff.png")


# --------------------------------------------------------------------------
# evaluation-metrics-regression.md
# --------------------------------------------------------------------------
def residual_diagnostics():
    f, axes = grid(1, 3, 12.0, 3.9)
    n = 140
    xp = rng.uniform(0, 10, n)

    ax = axes[0]
    ax.scatter(xp, rng.normal(0, 1, n), c=C.blue, s=32, alpha=0.8)
    ax.set_title("Healthy\nno pattern, constant spread", fontsize=12)

    ax = axes[1]
    ax.scatter(xp, 0.9 * (xp - 5) ** 2 / 5 - 2 + rng.normal(0, 0.5, n), c=C.orange, s=32, alpha=0.8)
    ax.set_title("Curvature\nmissing a non-linear term", fontsize=12)

    ax = axes[2]
    ax.scatter(xp, rng.normal(0, 1, n) * (0.25 + xp / 4), c=C.red, s=32, alpha=0.8)
    ax.set_title("Heteroscedastic\nvariance grows with x", fontsize=12)

    for ax in axes:
        ax.axhline(0, color=C.black, lw=2)
        ax.set_xlabel("predicted value")
    axes[0].set_ylabel("residual")
    f.tight_layout()
    save(f, "foundations/residual-diagnostics.png")


# --------------------------------------------------------------------------
# train-validation-test-splits.md
# --------------------------------------------------------------------------
def cv_schemes():
    f, axes = grid(2, 1, 8.6, 5.6)

    ax = axes[0]
    k = 5
    for i in range(k):
        for j in range(k):
            is_val = i == j
            ax.add_patch(Rectangle((j, -i), 0.94, 0.86,
                                   facecolor=C.orange if is_val else C.blue,
                                   alpha=0.95 if is_val else 0.45, edgecolor="white", lw=2))
        ax.text(-0.25, -i + 0.43, f"fold {i+1}", ha="right", va="center", fontsize=11)
    ax.set_xlim(-1.6, k + 0.4)
    ax.set_ylim(-k + 0.05, 1.5)
    ax.text(k / 2, 0.95, "k-fold cross-validation — every block is validated exactly once",
            ha="center", fontsize=12.5, fontweight="bold")
    clean(ax)

    ax = axes[1]
    for i in range(4):
        n_train = i + 2
        ax.add_patch(Rectangle((0, -i), n_train - 0.06, 0.86, facecolor=C.blue, alpha=0.45,
                               edgecolor="white", lw=2))
        ax.add_patch(Rectangle((n_train, -i), 0.94, 0.86, facecolor=C.orange, edgecolor="white", lw=2))
        ax.add_patch(Rectangle((n_train + 1, -i), max(0.01, 5 - n_train - 1), 0.86,
                               facecolor=C.light, alpha=0.5, edgecolor="white", lw=2))
        ax.text(-0.25, -i + 0.43, f"split {i+1}", ha="right", va="center", fontsize=11)
    ax.set_xlim(-1.6, 6.4)
    ax.set_ylim(-3.95, 1.5)
    ax.text(3, 0.95, "Time-series split — validation is always in the future",
            ha="center", fontsize=12.5, fontweight="bold")
    ax.annotate("", xy=(6.2, -3.6), xytext=(0, -3.6),
                arrowprops=dict(arrowstyle="->", lw=2.2, color=C.black))
    ax.text(3.1, -3.95, "time →", ha="center", fontsize=11.5)
    clean(ax)

    from matplotlib.patches import Patch
    f.legend(handles=[Patch(facecolor=C.blue, alpha=0.45, label="train"),
                      Patch(facecolor=C.orange, label="validate"),
                      Patch(facecolor=C.light, alpha=0.5, label="unused (future)")],
             loc="lower center", ncol=3, fontsize=11, frameon=False, bbox_to_anchor=(0.5, -0.02))
    f.tight_layout(rect=(0, 0.06, 1, 1))
    save(f, "foundations/cross-validation-schemes.png")


def data_leakage():
    """Why the scaler must be fitted inside the fold."""
    f, axes = grid(1, 2, 10.4, 3.6)
    for ax, title, ok in [(axes[0], "Wrong — scale, then split", False),
                          (axes[1], "Right — split, then scale in-fold", True)]:
        ax.add_patch(Rectangle((0, 1.1), 7.4, 0.85, facecolor=C.purple if not ok else C.light,
                               alpha=0.5 if not ok else 0.45, edgecolor="white", lw=2))
        ax.text(3.7, 1.52, "fit scaler on ALL data" if not ok else "raw data",
                ha="center", va="center", fontsize=11.5, fontweight="bold")
        ax.add_patch(Rectangle((0, 0), 5.2, 0.85, facecolor=C.blue, alpha=0.5, edgecolor="white", lw=2))
        ax.text(2.6, 0.42, "train", ha="center", va="center", fontsize=11.5)
        ax.add_patch(Rectangle((5.35, 0), 2.05, 0.85, facecolor=C.orange, edgecolor="white", lw=2))
        ax.text(6.37, 0.42, "test", ha="center", va="center", fontsize=11.5)
        ax.annotate("", xy=(3.7, 0.95), xytext=(3.7, 1.05),
                    arrowprops=dict(arrowstyle="->", lw=2.2, color=C.black))
        if not ok:
            ax.text(6.37, -0.42, "test statistics\nleaked into training", ha="center",
                    fontsize=10.5, color=C.red, fontweight="bold")
        else:
            ax.text(2.6, -0.42, "fit scaler here only,\nthen apply to test", ha="center",
                    fontsize=10.5, color=C.green, fontweight="bold")
        ax.set_xlim(-0.3, 7.7)
        ax.set_ylim(-0.95, 2.2)
        clean(ax)
        ax.set_title(title, fontsize=12.5, color=C.red if not ok else C.green)
    f.tight_layout()
    save(f, "foundations/preprocessing-leakage.png")


# --------------------------------------------------------------------------
# curse-of-dimensionality.md
# --------------------------------------------------------------------------
def curse_of_dimensionality():
    f, axes = grid(1, 2, 11.2, 4.2)

    ax = axes[0]
    dims = np.arange(1, 101)
    ratios = []
    for d in dims:
        pts = rng.normal(size=(400, d))
        q = np.zeros(d)
        dist = np.linalg.norm(pts - q, axis=1)
        ratios.append((dist.max() - dist.min()) / dist.min())
    ax.plot(dims, ratios, color=C.blue)
    ax.set_xlabel("dimensions")
    ax.set_ylabel("(farthest − nearest) / nearest")
    ax.set_title("Distances concentrate\n'nearest neighbour' stops meaning anything")

    ax = axes[1]
    d = np.arange(1, 21)
    ax.plot(d, 0.5**d, color=C.orange, marker="o")
    ax.set_yscale("log")
    ax.set_xlabel("dimensions")
    ax.set_ylabel("fraction of the cube within 0.5 of centre")
    ax.set_title("Volume flees to the corners\nthe centre of a cube is empty")
    f.tight_layout()
    save(f, "foundations/curse-of-dimensionality.png")


# --------------------------------------------------------------------------
# probability-and-distributions.md
# --------------------------------------------------------------------------
def distributions():
    f, axes = grid(2, 3, 11.6, 6.0)

    x = np.linspace(-4, 4, 400)
    ax = axes[0, 0]
    for s, col in [(0.6, C.blue), (1.0, C.orange), (2.0, C.green)]:
        ax.plot(x, np.exp(-0.5 * (x / s) ** 2) / (s * np.sqrt(2 * np.pi)), color=col, label=f"σ = {s}")
    ax.set_title("Normal")
    ax.legend(fontsize=9.5)

    ax = axes[0, 1]
    k = np.arange(0, 16)
    for n_, p_, col in [(15, 0.25, C.blue), (15, 0.5, C.orange), (15, 0.75, C.green)]:
        from math import comb
        pmf = [comb(n_, int(i)) * p_**i * (1 - p_) ** (n_ - i) for i in k]
        ax.plot(k, pmf, "o-", color=col, ms=5, label=f"p = {p_}")
    ax.set_title("Binomial (n = 15)")
    ax.legend(fontsize=9.5)

    ax = axes[0, 2]
    from math import factorial
    for lam, col in [(1, C.blue), (4, C.orange), (9, C.green)]:
        pmf = [np.exp(-lam) * lam**i / factorial(int(i)) for i in k]
        ax.plot(k, pmf, "o-", color=col, ms=5, label=f"λ = {lam}")
    ax.set_title("Poisson")
    ax.legend(fontsize=9.5)

    ax = axes[1, 0]
    xe = np.linspace(0, 5, 300)
    for lam, col in [(0.5, C.blue), (1.0, C.orange), (2.0, C.green)]:
        ax.plot(xe, lam * np.exp(-lam * xe), color=col, label=f"λ = {lam}")
    ax.set_title("Exponential")
    ax.legend(fontsize=9.5)

    ax = axes[1, 1]
    xb = np.linspace(0.001, 0.999, 300)
    from math import gamma
    for a, b, col in [(0.5, 0.5, C.blue), (2, 5, C.orange), (5, 2, C.green)]:
        B = gamma(a) * gamma(b) / gamma(a + b)
        ax.plot(xb, xb ** (a - 1) * (1 - xb) ** (b - 1) / B, color=col, label=f"α={a}, β={b}")
    ax.set_ylim(0, 3.2)
    ax.set_title("Beta")
    ax.legend(fontsize=9.5)

    ax = axes[1, 2]
    for n_, col in [(1, C.blue), (2, C.orange), (30, C.green)]:
        means = rng.uniform(0, 1, (20000, n_)).mean(axis=1)
        ax.hist(means, bins=45, density=True, color=col, alpha=0.55, label=f"n = {n_}")
    ax.set_title("CLT: means of uniforms")
    ax.legend(fontsize=9.5)

    for ax in axes.ravel():
        ax.set_yticks([])
    f.tight_layout()
    save(f, "foundations/common-distributions.png")


# --------------------------------------------------------------------------
# information-theory.md
# --------------------------------------------------------------------------
def information_theory():
    f, axes = grid(1, 3, 12.0, 3.9)

    ax = axes[0]
    p = np.linspace(0.001, 0.999, 400)
    H = -(p * np.log2(p) + (1 - p) * np.log2(1 - p))
    ax.plot(p, H, color=C.blue)
    ax.scatter([0.5], [1.0], c=C.red, s=110, zorder=5)
    ax.annotate("maximum uncertainty\n1 bit", xy=(0.5, 1.0), xytext=(0.5, 0.45),
                ha="center", fontsize=10.5, arrowprops=dict(arrowstyle="->", lw=1.7, color=C.black))
    ax.set_xlabel("p")
    ax.set_ylabel("entropy H(p)  [bits]")
    ax.set_title("Binary entropy", fontsize=12.5)

    ax = axes[1]
    ax.plot(p, -np.log2(p), color=C.orange)
    ax.set_ylim(0, 7)
    ax.set_xlabel("probability of the observed event")
    ax.set_ylabel("surprisal −log₂ p  [bits]")
    ax.set_title("Surprisal\nrare events carry more information", fontsize=12.5)

    ax = axes[2]
    xs = np.arange(6)
    P = np.array([0.05, 0.10, 0.35, 0.30, 0.15, 0.05])
    Q = np.array([0.20, 0.20, 0.20, 0.15, 0.15, 0.10])
    w = 0.4
    ax.bar(xs - w / 2, P, w, color=C.blue, label="P (true)")
    ax.bar(xs + w / 2, Q, w, color=C.orange, label="Q (model)")
    kl = np.sum(P * np.log2(P / Q))
    ax.set_title(f"KL(P ‖ Q) = {kl:.3f} bits\nextra cost of coding P with Q", fontsize=12.5)
    ax.set_xlabel("outcome")
    ax.legend(fontsize=10)
    f.tight_layout()
    save(f, "foundations/information-theory.png")


# --------------------------------------------------------------------------
# linear-algebra.md
# --------------------------------------------------------------------------
def linear_algebra():
    f, axes = grid(1, 3, 12.0, 4.1)

    A = np.array([[1.4, 0.75], [0.35, 1.1]])
    th = np.linspace(0, 2 * np.pi, 200)
    circ = np.stack([np.cos(th), np.sin(th)])

    ax = axes[0]
    ax.plot(*circ, color=C.blue, lw=2.6, label="unit circle")
    tc = A @ circ
    ax.plot(*tc, color=C.orange, lw=2.6, label="after A")
    evals, evecs = np.linalg.eig(A)
    for i in range(2):
        v = evecs[:, i].real
        ax.annotate("", xy=v * 1.8, xytext=(0, 0),
                    arrowprops=dict(arrowstyle="->", lw=2.8, color=C.red))
        ax.text(*(v * 2.05), f"λ={evals[i].real:.2f}", fontsize=10.5, color=C.red, ha="center")
    ax.set_title("A matrix is a transformation\neigenvectors keep their direction", fontsize=12)
    ax.legend(fontsize=9.5, loc="lower right")
    ax.set_aspect("equal")

    ax = axes[1]
    a = np.array([2.2, 0.6])
    b = np.array([1.0, 1.9])
    proj = (a @ b) / (a @ a) * a
    for v, col, lbl in [(a, C.blue, "a"), (b, C.orange, "b")]:
        ax.annotate("", xy=v, xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=3, color=col))
        ax.text(*(v * 1.12), lbl, fontsize=13, color=col, fontweight="bold")
    ax.annotate("", xy=proj, xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=3, color=C.green))
    ax.plot([b[0], proj[0]], [b[1], proj[1]], ls="--", color=C.grey, lw=2)
    ax.text(proj[0] + 0.06, proj[1] - 0.32, "proj$_a$ b", fontsize=11.5, color=C.green)
    ax.set_title("Dot product = projection\nthe basis of every similarity score", fontsize=12)
    ax.set_aspect("equal")

    ax = axes[2]
    M = np.array([[3.0, 1.2], [1.2, 1.0]])
    U, S, Vt = np.linalg.svd(M)
    ax.plot(*circ, color=C.light, lw=2.2)
    ax.plot(*(M @ circ), color=C.blue, lw=2.6)
    for i in range(2):
        d = U[:, i] * S[i]
        ax.annotate("", xy=d, xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=3, color=C.orange))
        ax.text(*(d * 1.14), f"σ{i+1}={S[i]:.2f}", fontsize=10.5, color=C.orange, ha="center")
    ax.set_title("SVD: any matrix is\nrotate → stretch → rotate", fontsize=12)
    ax.set_aspect("equal")

    for ax in axes:
        ax.axhline(0, color=C.black, lw=1.2)
        ax.axvline(0, color=C.black, lw=1.2)
    f.tight_layout()
    save(f, "foundations/linear-algebra-geometry.png")


# --------------------------------------------------------------------------
# calculus-and-gradients.md
# --------------------------------------------------------------------------
def gradients():
    f, axes = grid(1, 2, 11.0, 4.3)

    ax = axes[0]
    x = np.linspace(-2.4, 2.4, 400)
    fx = 0.35 * x**3 - x + 0.4
    ax.plot(x, fx, color=C.blue, lw=3)
    for x0, col in [(-1.7, C.orange), (0.0, C.green), (1.5, C.red)]:
        y0 = 0.35 * x0**3 - x0 + 0.4
        slope = 1.05 * x0**2 - 1
        tx = np.linspace(x0 - 0.75, x0 + 0.75, 10)
        ax.plot(tx, y0 + slope * (tx - x0), color=col, lw=2.4, ls="--")
        ax.scatter([x0], [y0], color=col, s=95, zorder=5)
        ax.text(x0, y0 + 0.55, f"f′ = {slope:+.2f}", color=col, fontsize=10.5, ha="center")
    ax.set_title("The derivative is the local slope", fontsize=12.5)
    ax.set_xlabel("x")
    ax.set_ylabel("f(x)")

    ax = axes[1]
    gx, gy = np.meshgrid(np.linspace(-2.2, 2.2, 220), np.linspace(-2.2, 2.2, 220))
    Z = gx**2 + 2.2 * gy**2
    ax.contour(gx, gy, Z, levels=12, colors=C.light, linewidths=1.2)
    qx, qy = np.meshgrid(np.linspace(-2, 2, 9), np.linspace(-2, 2, 9))
    ax.quiver(qx, qy, -2 * qx, -4.4 * qy, color=C.blue, alpha=0.75, width=0.005)
    ax.scatter([0], [0], marker="*", c=C.red, s=280, zorder=6)
    ax.set_title("The gradient points uphill\n(descent goes the other way)", fontsize=12.5)
    ax.set_xlabel("θ₁")
    ax.set_ylabel("θ₂")
    ax.set_aspect("equal")
    f.tight_layout()
    save(f, "foundations/derivatives-and-gradients.png")


# --------------------------------------------------------------------------
# statistics-and-estimation.md
# --------------------------------------------------------------------------
def estimation():
    f, axes = grid(1, 2, 11.0, 4.2)

    ax = axes[0]
    for n, col in [(5, C.red), (20, C.orange), (100, C.blue)]:
        means = rng.normal(0, 1, (20000, n)).mean(axis=1)
        ax.hist(means, bins=60, density=True, alpha=0.5, color=col, label=f"n = {n}  (SE = {1/np.sqrt(n):.2f})")
    ax.set_xlim(-1.5, 1.5)
    ax.set_xlabel("sample mean")
    ax.set_ylabel("density")
    ax.set_title("Standard error shrinks as 1/√n\nfour times the data halves the error", fontsize=12.5)
    ax.legend(fontsize=10)

    ax = axes[1]
    n_int = 25
    covered = 0
    for i in range(n_int):
        s = rng.normal(0, 1, 30)
        m, se = s.mean(), s.std(ddof=1) / np.sqrt(30)
        lo, hi = m - 1.96 * se, m + 1.96 * se
        ok = lo <= 0 <= hi
        covered += ok
        col = C.blue if ok else C.red
        ax.plot([lo, hi], [i, i], color=col, lw=2.6)
        ax.scatter([m], [i], color=col, s=30, zorder=5)
    ax.axvline(0, color=C.black, lw=2.2)
    ax.text(0.05, n_int - 0.5, "true value", fontsize=11)
    ax.set_yticks([])
    ax.set_xlabel("estimate ± 95 % interval")
    ax.set_title(f"{covered} of {n_int} intervals contain the truth\n'95 % confident' is a statement about the procedure", fontsize=12)
    f.tight_layout()
    save(f, "foundations/sampling-and-confidence.png")


# --------------------------------------------------------------------------
# data-preprocessing-and-features.md
# --------------------------------------------------------------------------
def scaling():
    f, axes = grid(1, 3, 12.0, 3.9)
    raw = np.stack([rng.normal(50, 12, 220), rng.normal(0.5, 0.11, 220)], axis=1)

    ax = axes[0]
    ax.scatter(*raw.T, s=26, c=C.grey, alpha=0.75)
    ax.set_title("Raw\naxes differ by 100×", fontsize=12)

    ax = axes[1]
    std = (raw - raw.mean(0)) / raw.std(0)
    ax.scatter(*std.T, s=26, c=C.blue, alpha=0.75)
    ax.set_title("Standardised\nmean 0, std 1", fontsize=12)

    ax = axes[2]
    mm = (raw - raw.min(0)) / (raw.max(0) - raw.min(0))
    ax.scatter(*mm.T, s=26, c=C.orange, alpha=0.75)
    ax.set_title("Min–max\nsqueezed into [0, 1]", fontsize=12)

    for ax, lbl in zip(axes, ["feature 2 (0–1 scale)", "", ""]):
        ax.set_xlabel("feature 1 (0–100 scale)")
    axes[0].set_ylabel("feature 2 (0–1 scale)")
    f.tight_layout()
    save(f, "foundations/feature-scaling.png")


if __name__ == "__main__":
    print("foundations:")
    learning_paradigms()
    gradient_descent_lr()
    gradient_descent_variants()
    bias_variance()
    learning_curves()
    regularization_paths()
    l1_l2_geometry()
    loss_functions()
    confusion_matrix_fig()
    roc_and_pr()
    threshold_tradeoff()
    residual_diagnostics()
    cv_schemes()
    data_leakage()
    curse_of_dimensionality()
    distributions()
    information_theory()
    linear_algebra()
    gradients()
    estimation()
    scaling()
