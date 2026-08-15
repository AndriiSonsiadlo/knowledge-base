"""Figures for docs/machine-learning/07-production-mlops/."""

import numpy as np
from matplotlib.patches import Rectangle

from kbstyle import C, clean, fig, grid, save

rng = np.random.default_rng(5)


def drift_types():
    f, axes = grid(1, 3, 12.4, 4.0)
    x = np.linspace(-4, 8, 500)

    def norm(mu, s):
        return np.exp(-0.5 * ((x - mu) / s) ** 2) / (s * np.sqrt(2 * np.pi))

    ax = axes[0]
    ax.fill_between(x, norm(1.0, 1.0), color=C.blue, alpha=0.45, label="training")
    ax.fill_between(x, norm(1.0, 1.0), color=C.blue, alpha=0.0)
    ax.plot(x, norm(1.0, 1.0), color=C.blue, lw=2.6)
    ax.plot(x, norm(1.0, 1.0), color=C.orange, lw=2.6, ls="--", label="production")
    ax.set_title("No drift\ninputs and labels unchanged", fontsize=12)
    ax.legend(fontsize=9.5)

    ax = axes[1]
    ax.fill_between(x, norm(1.0, 1.0), color=C.blue, alpha=0.4, label="training P(x)")
    ax.fill_between(x, norm(3.6, 1.2), color=C.orange, alpha=0.4, label="production P(x)")
    ax.set_title("Covariate drift\nP(x) moved, P(y|x) did not", fontsize=12)
    ax.legend(fontsize=9.5)

    ax = axes[2]
    ax.fill_between(x, norm(1.0, 1.0), color=C.blue, alpha=0.4, label="P(x) unchanged")
    ax.plot(x, 1 / (1 + np.exp(-(x - 1.0))) * 0.42, color=C.blue, lw=2.8, label="old P(y|x)")
    ax.plot(x, 1 / (1 + np.exp(-(x - 4.2))) * 0.42, color=C.red, lw=2.8, ls="--", label="new P(y|x)")
    ax.set_title("Concept drift\nthe relationship itself changed", fontsize=12)
    ax.legend(fontsize=9)

    for ax in axes:
        ax.set_yticks([])
        ax.set_xlabel("feature value")
    f.suptitle("Only one of these is visible without labels — which is why input monitoring is not enough",
               fontsize=12.5, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.9))
    save(f, "mlops/drift-types.png")


def drift_detection():
    f, ax = fig(8.0, 4.3)
    days = np.arange(0, 120)
    psi = 0.02 + 0.004 * days * (days > 55) * 0.9 + rng.normal(0, 0.012, days.size).clip(-0.02, 0.02)
    psi = np.clip(psi, 0.005, None)
    acc = 0.91 - 0.0022 * np.clip(days - 62, 0, None) + rng.normal(0, 0.006, days.size)

    ax.plot(days, psi, color=C.blue, lw=2.6, label="PSI on a key feature")
    ax.axhline(0.1, color=C.orange, ls="--", lw=2.2)
    ax.axhline(0.25, color=C.red, ls="--", lw=2.2)
    ax.text(1, 0.108, "0.1 — investigate", fontsize=10, color=C.orange, fontweight="bold")
    ax.text(1, 0.258, "0.25 — act", fontsize=10, color=C.red, fontweight="bold")
    ax.set_xlabel("days since deployment")
    ax.set_ylabel("population stability index", color=C.blue)
    ax.tick_params(axis="y", labelcolor=C.blue)

    ax2 = ax.twinx()
    ax2.plot(days, acc, color=C.green, lw=2.6, label="accuracy (labels arrive late)")
    ax2.set_ylabel("accuracy", color=C.green)
    ax2.tick_params(axis="y", labelcolor=C.green)
    ax2.grid(False)
    ax2.set_ylim(0.78, 0.95)

    ax.axvline(55, color=C.grey, ls=":", lw=2)
    ax.annotate("input drift detectable here", xy=(55, 0.20), xytext=(14, 0.30),
                fontsize=10.5, arrowprops=dict(arrowstyle="->", lw=1.8, color=C.grey))
    ax.annotate("accuracy only confirms it weeks later", xy=(95, 0.34), xytext=(40, 0.40),
                fontsize=10.5, color=C.green,
                arrowprops=dict(arrowstyle="->", lw=1.8, color=C.green))
    ax.set_title("Input drift is an early warning; label-based metrics lag")
    f.tight_layout()
    save(f, "mlops/drift-detection.png")


def deployment_strategies():
    f, axes = grid(1, 3, 12.6, 3.8)

    def draw(ax, title, bars, note):
        for i, (label, frac_old, colr) in enumerate(bars):
            y = -i * 0.85
            ax.add_patch(Rectangle((0, y), 6 * frac_old, 0.62, facecolor=C.blue, alpha=0.75,
                                   edgecolor="white", lw=1.8))
            if frac_old < 1:
                ax.add_patch(Rectangle((6 * frac_old, y), 6 * (1 - frac_old), 0.62,
                                       facecolor=colr, edgecolor="white", lw=1.8))
            ax.text(-0.25, y + 0.31, label, ha="right", va="center", fontsize=10.5)
        ax.text(3, -len(bars) * 0.85 - 0.15, note, ha="center", fontsize=10.5, color=C.grey)
        ax.set_xlim(-2.0, 6.4)
        ax.set_ylim(-len(bars) * 0.85 - 0.75, 0.95)
        clean(ax)
        ax.set_title(title, fontsize=12.5)

    draw(axes[0], "Blue–green",
         [("before", 1.0, C.green), ("cutover", 0.0, C.green)],
         "instant switch, instant rollback\n(needs 2× capacity)")
    draw(axes[1], "Canary",
         [("t₀", 0.95, C.green), ("t₁", 0.75, C.green), ("t₂", 0.5, C.green), ("t₃", 0.0, C.green)],
         "ramp slowly, watch metrics,\nroll back on any regression")
    draw(axes[2], "Shadow",
         [("live", 1.0, C.orange), ("mirror", 0.0, C.orange)],
         "new model scores real traffic\nbut its output is discarded")
    from matplotlib.patches import Patch
    f.legend(handles=[Patch(facecolor=C.blue, alpha=0.75, label="current model"),
                      Patch(facecolor=C.green, label="new model"),
                      Patch(facecolor=C.orange, label="new model (no user impact)")],
             loc="lower center", ncol=3, fontsize=10.5, frameon=False, bbox_to_anchor=(0.5, -0.04))
    f.tight_layout(rect=(0, 0.08, 1, 1))
    save(f, "mlops/deployment-strategies.png")


def latency_percentiles():
    f, ax = fig(7.6, 4.3)
    base = rng.lognormal(np.log(42), 0.42, 60000)
    tail = rng.lognormal(np.log(260), 0.55, 1400)
    lat = np.concatenate([base, tail])
    ax.hist(lat, bins=np.linspace(0, 700, 160), color=C.blue, alpha=0.75)
    for q, col, lbl in [(50, C.green, "p50"), (95, C.orange, "p95"), (99, C.red, "p99")]:
        v = np.percentile(lat, q)
        ax.axvline(v, color=col, lw=2.8)
        ax.text(v + 8, ax.get_ylim()[1] * (0.92 - 0.13 * [50, 95, 99].index(q)),
                f"{lbl} = {v:.0f} ms", color=col, fontsize=11.5, fontweight="bold")
    ax.text(0.98, 0.42, f"mean = {lat.mean():.0f} ms\n— hides the tail entirely",
            transform=ax.transAxes, ha="right", fontsize=11, color=C.grey,
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=C.light))
    ax.set_xlabel("inference latency (ms)")
    ax.set_ylabel("requests")
    ax.set_title("Serving latency is long-tailed — always report percentiles")
    f.tight_layout()
    save(f, "mlops/latency-percentiles.png")


def batching_throughput():
    f, axes = grid(1, 2, 11.0, 4.2)
    bs = np.array([1, 2, 4, 8, 16, 32, 64, 128, 256])
    per_item = 9.0 / bs + 0.55          # fixed overhead amortised across the batch
    latency = per_item * bs
    throughput = 1000 / per_item

    ax = axes[0]
    ax.plot(bs, throughput, "o-", color=C.blue, ms=8)
    ax.set_xscale("log", base=2)
    ax.set_xlabel("batch size")
    ax.set_ylabel("throughput (requests/s)")
    ax.set_title("Batching amortises fixed overhead", fontsize=12.5)

    ax = axes[1]
    ax.plot(bs, latency, "o-", color=C.red, ms=8)
    ax.set_xscale("log", base=2)
    ax.axhline(100, color=C.grey, ls="--", lw=2.2)
    ax.text(1.1, 106, "SLA budget: 100 ms", fontsize=10.5, color=C.grey)
    ok = bs[latency <= 100].max()
    ax.axvline(ok, color=C.green, lw=2.4)
    ax.text(ok * 1.15, latency.max() * 0.55, f"largest batch\nwithin SLA: {ok}",
            fontsize=10.5, color=C.green, fontweight="bold")
    ax.set_xlabel("batch size")
    ax.set_ylabel("per-request latency (ms)")
    ax.set_title("…but latency rises with it", fontsize=12.5)
    f.suptitle("Throughput and latency pull in opposite directions — the SLA picks the batch size",
               fontsize=12.5, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.9))
    save(f, "mlops/batching-tradeoff.png")


def quantization():
    f, axes = grid(1, 2, 11.0, 4.0)
    ax = axes[0]
    fmts = ["FP32", "FP16", "INT8", "INT4"]
    size = np.array([26.0, 13.0, 6.5, 3.25])   # a 6.5 B-parameter model
    ax.bar(fmts, size, color=[C.grey, C.blue, C.green, C.orange])
    for i, v in enumerate(size):
        ax.text(i, v + 0.6, f"{v:.1f} GB", ha="center", fontsize=11.5, fontweight="bold")
    ax.set_ylabel("memory for a 6.5 B-parameter model")
    ax.set_title("Quantization is mostly a memory win", fontsize=12.5)
    ax.set_ylim(0, 31)

    ax = axes[1]
    quality = np.array([100.0, 99.9, 99.1, 95.4])
    ax.plot(fmts, quality, "o-", color=C.red, ms=10)
    ax.axhline(99, color=C.grey, ls="--", lw=2)
    ax.text(0.05, 99.15, "1 % quality budget", fontsize=10.5, color=C.grey)
    ax.set_ylabel("relative task quality (%)")
    ax.set_ylim(93, 101)
    ax.set_title("Quality holds to INT8, then falls away", fontsize=12.5)
    f.tight_layout()
    save(f, "mlops/quantization.png")


def ab_test_power():
    f, axes = grid(1, 2, 11.0, 4.2)
    ax = axes[0]
    n = np.logspace(2, 5.6, 200)
    for mde, col in [(0.01, C.red), (0.02, C.orange), (0.05, C.blue)]:
        p = 0.10
        se = np.sqrt(2 * p * (1 - p) / n)
        z = mde * p / se
        from math import erf
        power = np.array([0.5 * (1 + erf((zi - 1.96) / np.sqrt(2))) for zi in z])
        ax.semilogx(n, power, color=col, lw=2.8, label=f"detect a {mde*100:.0f} % relative lift")
    ax.axhline(0.8, color=C.grey, ls="--", lw=2.2)
    ax.text(120, 0.82, "80 % power", fontsize=10.5, color=C.grey)
    ax.set_xlabel("users per arm (log scale)")
    ax.set_ylabel("power")
    ax.set_title("Smaller effects need far more traffic\n(baseline conversion 10 %)", fontsize=12)
    ax.legend(fontsize=10, loc="lower right")

    ax = axes[1]
    days = np.arange(1, 29)
    r = np.random.default_rng(11)
    obs = 0.001 + np.cumsum(r.normal(0, 0.004, 28)) / np.sqrt(np.arange(1, 29))
    ci = 1.96 * 0.02 / np.sqrt(days * 900)
    ax.plot(days, obs, color=C.blue, lw=2.6, label="observed lift")
    ax.fill_between(days, obs - ci, obs + ci, color=C.blue, alpha=0.18, label="95 % CI")
    ax.axhline(0, color=C.black, lw=2)
    sig = np.flatnonzero((obs - ci > 0) | (obs + ci < 0))
    if len(sig):
        for d in sig[:4]:
            ax.scatter([days[d]], [obs[d]], s=110, c=C.red, zorder=6)
    ax.set_xlabel("day")
    ax.set_ylabel("lift vs. control")
    ax.set_title("Peeking daily manufactures false positives\n(red = would have 'won' if you stopped there)",
                 fontsize=11.5)
    ax.legend(fontsize=10)
    f.tight_layout()
    save(f, "mlops/ab-testing.png")


def training_serving_skew():
    f, ax = fig(9.8, 4.2)
    ax.add_patch(Rectangle((0.2, 2.2), 3.6, 1.2, facecolor=C.blue, alpha=0.85, edgecolor="white", lw=2))
    ax.text(2.0, 2.8, "Training pipeline\npandas, batch, full history", ha="center", va="center",
            color="white", fontsize=11, fontweight="bold")
    ax.add_patch(Rectangle((0.2, 0.4), 3.6, 1.2, facecolor=C.orange, alpha=0.9, edgecolor="white", lw=2))
    ax.text(2.0, 1.0, "Serving pipeline\nJava/Go, per-request, live data", ha="center", va="center",
            color="white", fontsize=11, fontweight="bold")
    ax.annotate("", xy=(5.4, 2.8), xytext=(3.85, 2.8), arrowprops=dict(arrowstyle="->", lw=2.4, color=C.black))
    ax.annotate("", xy=(5.4, 1.0), xytext=(3.85, 1.0), arrowprops=dict(arrowstyle="->", lw=2.4, color=C.black))
    ax.add_patch(Rectangle((5.5, 1.3), 2.0, 1.2, facecolor=C.grey, alpha=0.85, edgecolor="white", lw=2))
    ax.text(6.5, 1.9, "same model", ha="center", va="center", color="white", fontsize=11,
            fontweight="bold")
    ax.text(8.9, 1.9, "different\nfeatures\n→ silent\nquality loss", ha="center", va="center",
            fontsize=11, color=C.red, fontweight="bold")
    ax.annotate("", xy=(8.0, 1.9), xytext=(7.55, 1.9), arrowprops=dict(arrowstyle="->", lw=2.4, color=C.red))
    ax.text(4.9, 3.75, "Two implementations of 'the same' feature logic is the classic MLOps bug.",
            ha="center", fontsize=11.5)
    ax.text(4.9, -0.1, "A feature store fixes it by making both paths read one definition.",
            ha="center", fontsize=11, color=C.green, fontweight="bold")
    ax.set_xlim(0, 10.6)
    ax.set_ylim(-0.5, 4.2)
    clean(ax)
    ax.set_title("Training–serving skew", fontsize=13.5)
    f.tight_layout()
    save(f, "mlops/training-serving-skew.png")


def ml_test_pyramid():
    f, ax = fig(8.4, 4.4)
    tiers = [
        ("Model quality gates\n(offline eval, fairness slices)", 2.0, C.red),
        ("Integration tests\n(pipeline end-to-end, serving parity)", 3.6, C.orange),
        ("Data validation\n(schema, ranges, nulls, distributions)", 5.2, C.blue),
        ("Unit tests\n(feature transforms, deterministic code)", 6.8, C.green),
    ]
    y = 0
    for label, w, col in tiers:
        ax.add_patch(Rectangle((-w / 2, y), w, 1.0, facecolor=col, alpha=0.85,
                               edgecolor="white", lw=2.5))
        ax.text(0, y + 0.5, label, ha="center", va="center", color="white", fontsize=10.5,
                fontweight="bold")
        y += 1.05
    ax.text(0, y + 0.35, "fewer, slower, higher-level →", ha="center", fontsize=10.5, color=C.grey)
    ax.text(4.6, 2.1, "ML adds a whole\nlayer classical\nsoftware doesn't\nhave: the data",
            ha="center", fontsize=11, color=C.blue, fontweight="bold")
    ax.set_xlim(-5.0, 7.0)
    ax.set_ylim(-0.4, 5.2)
    clean(ax)
    ax.set_title("The ML test pyramid", fontsize=13.5)
    f.tight_layout()
    save(f, "mlops/ml-test-pyramid.png")


def cost_breakdown():
    f, axes = grid(1, 2, 11.0, 4.2)
    ax = axes[0]
    labels = ["Training\n(one-off)", "Inference\n(every request, forever)"]
    vals = [15, 85]
    ax.barh(labels, vals, color=[C.blue, C.orange])
    for i, v in enumerate(vals):
        ax.text(v + 1.5, i, f"{v} %", va="center", fontsize=13, fontweight="bold")
    ax.set_xlim(0, 100)
    ax.set_xlabel("share of total lifetime compute spend")
    ax.set_title("Where the money actually goes\n(typical production model)", fontsize=12)

    ax = axes[1]
    months = np.arange(1, 25)
    train_cost = np.where(months == 1, 40000, 0)
    infer = 3500 * 1.09 ** (months - 1)
    ax.plot(months, np.cumsum(train_cost), color=C.blue, lw=2.8, label="cumulative training")
    ax.plot(months, np.cumsum(infer), color=C.orange, lw=2.8, label="cumulative inference")
    cross = months[np.cumsum(infer) > np.cumsum(train_cost)][0]
    ax.axvline(cross, color=C.grey, ls="--", lw=2)
    ax.text(cross + 0.4, 20000, f"inference overtakes\ntraining in month {cross}", fontsize=10.5,
            color=C.grey)
    ax.set_xlabel("month")
    ax.set_ylabel("cumulative cost ($)")
    ax.set_title("Inference compounds with traffic", fontsize=12)
    ax.legend(fontsize=10.5)
    f.tight_layout()
    save(f, "mlops/cost-breakdown.png")


if __name__ == "__main__":
    print("mlops:")
    drift_types()
    drift_detection()
    deployment_strategies()
    latency_percentiles()
    batching_throughput()
    quantization()
    ab_test_power()
    training_serving_skew()
    ml_test_pyramid()
    cost_breakdown()
