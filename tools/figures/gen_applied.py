"""Figures for the time-series, interpretability and recommender sections."""

import numpy as np
from matplotlib.patches import Rectangle

from kbstyle import C, clean, fig, grid, save

rng = np.random.default_rng(11)


def _series(n=360, seed=0):
    r = np.random.default_rng(seed)
    t = np.arange(n)
    trend = 0.045 * t
    seasonal = 4.2 * np.sin(2 * np.pi * t / 52) + 1.4 * np.sin(2 * np.pi * t / 13)
    noise = r.normal(0, 1.05, n)
    return t, 20 + trend + seasonal + noise, trend, seasonal, noise


# ============================================================ time series
def decomposition():
    t, y, trend, seasonal, noise = _series()
    f, axes = grid(4, 1, 8.6, 7.0, sharex=True)
    for ax, series, name, col in [
        (axes[0], y, "observed", C.blue),
        (axes[1], 20 + trend, "trend", C.orange),
        (axes[2], seasonal, "seasonality", C.green),
        (axes[3], noise, "residual", C.grey),
    ]:
        ax.plot(t, series, color=col, lw=2.0)
        ax.set_ylabel(name, fontsize=11.5, fontweight="bold")
    axes[3].set_xlabel("time (weeks)")
    f.suptitle("Additive decomposition:  observed = trend + seasonality + residual",
               fontsize=13, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.95))
    save(f, "applied/ts-decomposition.png")


def stationarity():
    f, axes = grid(1, 3, 12.4, 3.9)
    n = 300
    t = np.arange(n)

    ax = axes[0]
    ax.plot(t, rng.normal(0, 1, n), color=C.green, lw=1.7)
    ax.axhline(0, color=C.black, lw=1.6)
    ax.set_title("Stationary\nconstant mean and variance", fontsize=12)

    ax = axes[1]
    ax.plot(t, 0.02 * t + rng.normal(0, 1, n), color=C.orange, lw=1.7)
    ax.set_title("Trend — mean drifts\nfix: difference the series", fontsize=12)

    ax = axes[2]
    ax.plot(t, rng.normal(0, 1, n) * (0.3 + t / 110), color=C.red, lw=1.7)
    ax.set_title("Changing variance\nfix: log or Box–Cox transform", fontsize=12)
    for ax in axes:
        ax.set_xlabel("time")
    axes[0].set_ylabel("value")
    f.suptitle("Classical forecasting models assume stationarity — check before fitting",
               fontsize=12.5, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.9))
    save(f, "applied/ts-stationarity.png")


def acf_plot():
    """ACF/PACF computed from a real AR(2) simulation, not sketched."""
    n = 1200
    e = rng.normal(0, 1, n)
    x = np.zeros(n)
    for i in range(2, n):
        x[i] = 0.62 * x[i - 1] - 0.34 * x[i - 2] + e[i]      # a genuine AR(2)
    x = x - x.mean()

    def acf(v, lags):
        c0 = (v * v).mean()
        return np.array([1.0 if k == 0 else (v[k:] * v[:-k]).mean() / c0 for k in range(lags + 1)])

    L = 24
    a = acf(x, L)
    # PACF via Durbin-Levinson.
    pac = [1.0]
    phi = np.zeros((L + 1, L + 1))
    for k in range(1, L + 1):
        if k == 1:
            phi[1, 1] = a[1]
        else:
            num = a[k] - sum(phi[k - 1, j] * a[k - j] for j in range(1, k))
            den = 1 - sum(phi[k - 1, j] * a[j] for j in range(1, k))
            phi[k, k] = num / den
            for j in range(1, k):
                phi[k, j] = phi[k - 1, j] - phi[k, k] * phi[k - 1, k - j]
        pac.append(phi[k, k])
    pac = np.array(pac)

    ci = 1.96 / np.sqrt(n)
    f, axes = grid(1, 2, 11.2, 4.0, sharey=True)
    for ax, vals, name, col in [(axes[0], a, "ACF", C.blue), (axes[1], pac, "PACF", C.orange)]:
        ax.bar(range(L + 1), vals, color=col, width=0.55)
        ax.axhspan(-ci, ci, color=C.grey, alpha=0.22)
        ax.axhline(0, color=C.black, lw=1.4)
        ax.set_xlabel("lag")
        ax.set_title(name, fontsize=13)
    axes[0].set_ylabel("correlation")
    axes[1].annotate("cuts off after lag 2\n→ AR(2)", xy=(2, pac[2]), xytext=(7, -0.45),
                     fontsize=11, color=C.red, fontweight="bold",
                     arrowprops=dict(arrowstyle="->", lw=2, color=C.red))
    f.suptitle("Simulated AR(2): the PACF cuts off at lag 2, the ACF decays — how order is chosen",
               fontsize=12.5, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.9))
    save(f, "applied/ts-acf-pacf.png")
    return pac


def backtesting():
    f, ax = fig(9.0, 4.4)
    rows = [("expanding\nwindow", True), ("rolling\nwindow", False)]
    y = 0.0
    for name, expanding in rows:
        group_top = y
        for i in range(4):
            tr_start = 0 if expanding else i * 1.4
            tr_end = 4.0 + i * 1.4
            ax.add_patch(Rectangle((tr_start, -y), tr_end - tr_start, 0.72, facecolor=C.blue,
                                   alpha=0.5, edgecolor="white", lw=2))
            ax.add_patch(Rectangle((tr_end + 0.05, -y), 1.3, 0.72, facecolor=C.orange,
                                   edgecolor="white", lw=2))
            y += 0.9
        # Label vertically centred on the four bars just drawn.
        ax.text(-0.45, -(group_top + (y - 0.9 - group_top) / 2) + 0.36, name,
                ha="right", va="center", fontsize=11.5, fontweight="bold")
        y += 0.7
    ax.annotate("", xy=(11.2, -y + 0.2), xytext=(0, -y + 0.2),
                arrowprops=dict(arrowstyle="->", lw=2.4, color=C.black))
    ax.text(5.6, -y - 0.25, "time →", ha="center", fontsize=11.5)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=C.blue, alpha=0.5, label="train"),
                       Patch(facecolor=C.orange, label="forecast horizon")],
              loc="lower right", fontsize=10.5, ncol=2)
    ax.set_xlim(-2.6, 12.0)
    ax.set_ylim(-y - 0.9, 1.15)
    clean(ax)
    ax.set_title("Backtesting: the model is only ever evaluated on data after its training window",
                 fontsize=12.5)
    f.tight_layout()
    save(f, "applied/ts-backtesting.png")


def forecast_intervals():
    t, y, *_ = _series(n=200, seed=4)
    split = 160
    f, ax = fig(8.6, 4.3)
    ax.plot(t[:split], y[:split], color=C.blue, lw=2.0, label="history")
    ax.plot(t[split:], y[split:], color=C.grey, lw=2.0, ls="--", label="actual (unseen)")

    h = np.arange(1, len(t) - split + 1)
    base = y[split - 1]
    drift = (y[split - 1] - y[0]) / split
    point = base + drift * h + 4.2 * np.sin(2 * np.pi * (t[split:]) / 52)
    ax.plot(t[split:], point, color=C.red, lw=2.6, label="forecast")
    for z, alpha in [(1.28, 0.22), (1.96, 0.14)]:
        band = z * 1.05 * np.sqrt(h)
        ax.fill_between(t[split:], point - band, point + band, color=C.red, alpha=alpha)
    ax.axvline(t[split], color=C.black, lw=2, ls=":")
    ax.text(t[split] + 1.5, y.min(), "forecast origin", fontsize=10.5)
    ax.set_xlabel("time (weeks)")
    ax.set_ylabel("value")
    ax.set_title("Uncertainty grows with the horizon — a point forecast alone hides that")
    ax.legend(fontsize=10, loc="upper left")
    f.tight_layout()
    save(f, "applied/ts-forecast-intervals.png")


def ts_features():
    f, ax = fig(9.4, 3.8)
    n = 14
    for i in range(n):
        col = C.blue if i < 8 else (C.orange if i < 10 else C.light)
        ax.add_patch(Rectangle((i * 0.72, 0), 0.62, 0.8, facecolor=col, alpha=0.9,
                               edgecolor="white", lw=1.8))
        ax.text(i * 0.72 + 0.31, 0.4, f"t{i-9}" if i < 10 else f"t+{i-9}", ha="center",
                va="center", color="white" if i < 10 else C.grey, fontsize=9.5, fontweight="bold")
    ax.text(2.9, 1.15, "lag features  (t−9 … t−2)", ha="center", fontsize=11.5, color=C.blue,
            fontweight="bold")
    ax.text(6.9, 1.15, "target", ha="center", fontsize=11.5, color=C.orange, fontweight="bold")
    ax.text(8.9, 1.15, "future — unavailable", ha="center", fontsize=11, color=C.grey)
    ax.annotate("", xy=(0, -0.28), xytext=(5.8, -0.28),
                arrowprops=dict(arrowstyle="<->", lw=2.2, color=C.blue))
    ax.text(2.9, -0.62, "rolling mean, std, min/max, diffs — all computed\nfrom this window only",
            ha="center", fontsize=10.5, color=C.blue)
    ax.text(6.9, -0.62, "Any feature touching the orange or grey\ncells is leakage.",
            ha="center", fontsize=10.5, color=C.red, fontweight="bold")
    ax.set_xlim(-0.6, 10.6)
    ax.set_ylim(-1.3, 1.7)
    clean(ax)
    ax.set_title("Turning a series into a supervised learning table", fontsize=13)
    f.tight_layout()
    save(f, "applied/ts-supervised-framing.png")


# ============================================================ interpretability
def feature_importance():
    f, axes = grid(1, 2, 11.4, 4.2)
    names = ["income", "age", "balance", "n_products", "tenure", "region", "channel", "is_active"]

    ax = axes[0]
    imp = np.array([0.31, 0.22, 0.17, 0.11, 0.08, 0.06, 0.03, 0.02])
    ax.barh(names[::-1], imp[::-1], color=C.blue)
    ax.set_xlabel("permutation importance (drop in score)")
    ax.set_title("Global: which features matter overall", fontsize=12.5)

    ax = axes[1]
    contrib = np.array([+0.28, -0.14, +0.19, -0.06, +0.03, -0.02, +0.01, -0.09])
    cols = [C.green if v > 0 else C.red for v in contrib]
    ax.barh(names[::-1], contrib[::-1], color=cols[::-1])
    ax.axvline(0, color=C.black, lw=1.8)
    ax.set_xlabel("SHAP value for ONE prediction")
    ax.set_title("Local: why *this* prediction came out as it did", fontsize=12.5)
    ax.text(0.97, 0.05, "green pushes the prediction up,\nred pushes it down",
            transform=ax.transAxes, ha="right", fontsize=10, color=C.grey)
    f.suptitle("Global and local explanations answer different questions",
               fontsize=13, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.9))
    save(f, "applied/interp-global-vs-local.png")


def partial_dependence():
    f, axes = grid(1, 2, 11.2, 4.1)
    x = np.linspace(20, 80, 200)

    ax = axes[0]
    pd_curve = 0.12 + 0.55 / (1 + np.exp(-(x - 48) / 5.5))
    ax.plot(x, pd_curve, color=C.blue, lw=3)
    ax.fill_between(x, pd_curve - 0.05, pd_curve + 0.05, color=C.blue, alpha=0.16)
    ax.set_xlabel("age")
    ax.set_ylabel("average predicted probability")
    ax.set_title("Partial dependence\nthe average effect of one feature", fontsize=12.5)

    ax = axes[1]
    for i in range(22):
        shift = rng.normal(0, 7)
        sign = 1 if i % 3 else -1
        ice = 0.12 + sign * 0.5 / (1 + np.exp(-(x - 48 - shift) / 5.5)) + (0.25 if sign < 0 else 0)
        ax.plot(x, ice, color=C.grey, lw=1.2, alpha=0.65)
    ax.plot(x, pd_curve, color=C.red, lw=3.4, label="PD (the average)")
    ax.set_xlabel("age")
    ax.set_title("Individual conditional expectation\nthe average hid two opposite subgroups",
                 fontsize=12)
    ax.legend(fontsize=10.5)
    f.tight_layout()
    save(f, "applied/interp-pdp-ice.png")


def interpretability_tradeoff():
    f, ax = fig(8.6, 4.6)
    models = {
        "Linear / logistic": (5.6, 1.8, C.green),
        "Decision tree (shallow)": (5.2, 2.2, C.green),
        "Generalised additive": (4.6, 3.0, C.blue),
        "Random forest": (2.6, 4.3, C.orange),
        "Gradient boosting": (2.2, 4.8, C.orange),
        "Deep network": (1.0, 5.4, C.red),
    }
    for name, (interp, acc, col) in models.items():
        ax.scatter([interp], [acc], s=260, c=col, zorder=5, edgecolors="white", linewidths=2)
        ax.annotate(name, xy=(interp, acc), xytext=(8, 10), textcoords="offset points",
                    fontsize=10.5, fontweight="bold")
    ax.set_xlabel("← harder to interpret        easier to interpret →")
    ax.set_ylabel("typical accuracy on complex tabular data →")
    ax.set_xlim(0.2, 7.4)
    ax.set_ylim(1.2, 6.2)
    ax.set_title("The usual trade-off — and post-hoc explanation is how you\nbuy back some interpretability without giving up the accuracy",
                 fontsize=12)
    f.tight_layout()
    save(f, "applied/interp-tradeoff.png")


# ============================================================ recommenders
def user_item_matrix():
    f, axes = grid(1, 2, 11.6, 4.4)
    n_u, n_i = 8, 10
    R = np.full((n_u, n_i), np.nan)
    r = np.random.default_rng(9)
    for u in range(n_u):
        for i in range(n_i):
            if r.random() < 0.34:
                R[u, i] = r.integers(1, 6)

    ax = axes[0]
    ax.imshow(np.where(np.isnan(R), 0, R), cmap="Blues", vmin=0, vmax=5)
    for u in range(n_u):
        for i in range(n_i):
            ax.text(i, u, "?" if np.isnan(R[u, i]) else f"{int(R[u,i])}", ha="center",
                    va="center", fontsize=11,
                    color=C.red if np.isnan(R[u, i]) else ("white" if R[u, i] > 3 else C.black),
                    fontweight="bold")
    ax.set_xlabel("items")
    ax.set_ylabel("users")
    filled = np.isfinite(R).mean()
    ax.set_title(f"The user–item matrix\n{filled*100:.0f} % observed — the rest is the task", fontsize=12)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)

    ax = axes[1]
    k = 3
    ax.add_patch(Rectangle((0, 0), 1.1, 3.2, facecolor=C.blue, alpha=0.8, edgecolor="white", lw=2))
    ax.text(0.55, 1.6, "U\nusers × k", ha="center", va="center", color="white", fontsize=11,
            fontweight="bold")
    ax.text(1.5, 1.6, "×", ha="center", va="center", fontsize=20, fontweight="bold")
    ax.add_patch(Rectangle((1.9, 2.1), 3.6, 1.1, facecolor=C.orange, edgecolor="white", lw=2))
    ax.text(3.7, 2.65, "Vᵀ   k × items", ha="center", va="center", color="white", fontsize=11,
            fontweight="bold")
    ax.text(5.9, 1.6, "≈", ha="center", va="center", fontsize=20, fontweight="bold")
    ax.add_patch(Rectangle((6.4, 0), 3.6, 3.2, facecolor=C.green, alpha=0.35,
                           edgecolor=C.green, lw=2.4))
    ax.text(8.2, 1.6, "R̂\nevery cell filled", ha="center", va="center", fontsize=11.5,
            fontweight="bold")
    ax.text(5.0, -0.6, f"k = {k} latent factors, learned only from the observed cells",
            ha="center", fontsize=11, color=C.grey)
    ax.set_xlim(-0.4, 10.4)
    ax.set_ylim(-1.2, 4.0)
    clean(ax)
    ax.set_title("Matrix factorisation fills the gaps", fontsize=12.5)
    f.tight_layout()
    save(f, "applied/rec-matrix-factorization.png")


def cf_types():
    f, axes = grid(1, 2, 11.0, 4.0)
    ax = axes[0]
    users = {"you": (1.0, 2.6), "A": (2.6, 3.3), "B": (2.6, 1.9)}
    items = {"film 1": (4.4, 3.5), "film 2": (4.4, 2.6), "film 3": (4.4, 1.7)}
    for name, (x, y) in users.items():
        ax.scatter([x], [y], s=340, c=C.blue if name == "you" else C.sky, zorder=5,
                   edgecolors="white", linewidths=2)
        ax.text(x, y - 0.42, name, ha="center", fontsize=11, fontweight="bold")
    for name, (x, y) in items.items():
        ax.scatter([x], [y], s=300, c=C.orange, marker="s", zorder=5, edgecolors="white",
                   linewidths=2)
        ax.text(x + 0.3, y, name, va="center", fontsize=10.5)
    for a, b, col, style in [("A", "film 1", C.grey, "-"), ("A", "film 2", C.grey, "-"),
                             ("B", "film 2", C.grey, "-"), ("B", "film 3", C.grey, "-"),
                             ("you", "film 2", C.grey, "-")]:
        p0 = users.get(a, items.get(a))
        p1 = items.get(b, users.get(b))
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=col, lw=1.8, ls=style, alpha=0.65, zorder=1)
    ax.plot([users["you"][0], items["film 1"][0]], [users["you"][1], items["film 1"][1]],
            color=C.red, lw=2.8, ls="--", zorder=4)
    ax.text(2.7, 3.9, "you and A both liked film 2,\nso A's film 1 is recommended", fontsize=10.5,
            color=C.red, fontweight="bold", ha="center")
    ax.set_xlim(0.2, 6.2)
    ax.set_ylim(1.0, 4.6)
    clean(ax)
    ax.set_title("Collaborative filtering\nuses who liked what — ignores content", fontsize=12)

    ax = axes[1]
    ax.text(0.5, 3.6, "Content-based", fontsize=12, fontweight="bold", color=C.green)
    feats = ["genre: sci-fi", "director: X", "length: 120 min", "era: 1990s"]
    for i, ft in enumerate(feats):
        ax.add_patch(Rectangle((0.4, 2.8 - i * 0.55), 3.0, 0.42, facecolor=C.green,
                               alpha=0.75, edgecolor="white", lw=1.6))
        ax.text(1.9, 3.01 - i * 0.55, ft, ha="center", va="center", color="white", fontsize=10)
    ax.annotate("", xy=(4.4, 2.2), xytext=(3.5, 2.2),
                arrowprops=dict(arrowstyle="->", lw=2.4, color=C.black))
    ax.text(5.0, 2.2, "match against\nwhat you liked\nbefore", ha="center", va="center",
            fontsize=10.5)
    ax.text(3.0, 0.55, "Works for brand-new items — the cold-start case\ncollaborative filtering cannot handle.",
            ha="center", fontsize=10.5, color=C.grey, style="italic")
    ax.set_xlim(0, 6.6)
    ax.set_ylim(0.1, 4.2)
    clean(ax)
    ax.set_title("Content-based\nuses item attributes", fontsize=12)
    f.tight_layout()
    save(f, "applied/rec-cf-vs-content.png")


def ranking_metrics():
    f, axes = grid(1, 2, 11.2, 4.0)
    ax = axes[0]
    rel = [1, 0, 1, 1, 0, 0, 1, 0, 0, 0]
    pos = np.arange(1, 11)
    ax.bar(pos, [1 / np.log2(p + 1) for p in pos], color=[C.green if r else C.light for r in rel])
    ax.set_xlabel("rank position")
    ax.set_ylabel("positional discount  1/log₂(rank+1)")
    ax.set_title("NDCG discounts by position\na hit at rank 1 is worth far more than at rank 10",
                 fontsize=11.5)
    ax.set_xticks(pos)

    ax = axes[1]
    k = np.arange(1, 21)
    prec = np.array([0.9, 0.85, 0.78, 0.72, 0.66, 0.62, 0.58, 0.55, 0.52, 0.50,
                     0.48, 0.46, 0.44, 0.43, 0.41, 0.40, 0.39, 0.38, 0.37, 0.36])
    rec = np.linspace(0.06, 0.62, 20)
    ax.plot(k, prec, "o-", color=C.blue, ms=5, label="precision@k")
    ax.plot(k, rec, "s-", color=C.orange, ms=5, label="recall@k")
    ax.set_xlabel("k (list length)")
    ax.set_title("Longer lists trade precision for recall\n— k is set by the UI, not the model",
                 fontsize=11.5)
    ax.legend(fontsize=10.5)
    f.tight_layout()
    save(f, "applied/rec-ranking-metrics.png")


def recsys_pipeline():
    f, ax = fig(10.6, 3.4)
    stages = [("Candidate\ngeneration", "millions → ~1000", C.blue),
              ("Scoring /\nranking", "~1000 → ~100", C.orange),
              ("Re-ranking\n(business rules,\ndiversity)", "~100 → ~10", C.green)]
    for i, (name, scale, col) in enumerate(stages):
        x = i * 3.4
        ax.add_patch(Rectangle((x, 0.7), 2.7, 1.5, facecolor=col, alpha=0.9,
                               edgecolor="white", lw=2))
        ax.text(x + 1.35, 1.45, name, ha="center", va="center", color="white", fontsize=11,
                fontweight="bold")
        ax.text(x + 1.35, 0.35, scale, ha="center", fontsize=10.5, color=C.grey)
        if i < 2:
            ax.annotate("", xy=(x + 3.38, 1.45), xytext=(x + 2.72, 1.45),
                        arrowprops=dict(arrowstyle="->", lw=2.4, color=C.black))
    ax.text(5.1, 2.72, "Cheap and approximate first, expensive and accurate last —\n"
                       "the only way to rank a catalogue of millions inside a latency budget.",
            ha="center", fontsize=11)
    ax.set_xlim(-0.3, 10.3)
    ax.set_ylim(-0.1, 3.5)
    clean(ax)
    f.tight_layout()
    save(f, "applied/rec-pipeline.png")


if __name__ == "__main__":
    print("applied:")
    decomposition()
    stationarity()
    pac = acf_plot()
    print(f"    PACF lags 1-4: {', '.join(f'{v:+.2f}' for v in pac[1:5])}  (AR(2): 3+ ≈ 0)")
    backtesting()
    forecast_intervals()
    ts_features()
    feature_importance()
    partial_dependence()
    interpretability_tradeoff()
    user_item_matrix()
    cf_types()
    ranking_metrics()
    recsys_pipeline()
