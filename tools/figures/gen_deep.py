"""Figures for docs/machine-learning/02-deep-learning/."""

import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

from kbstyle import C, clean, fig, grid, save

rng = np.random.default_rng(0)


# ---------------------------------------------------------------- perceptron / XOR
def xor_problem():
    """The single fact that killed the perceptron and required hidden layers."""
    f, axes = grid(1, 3, 12.2, 4.0)

    pts = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], float)
    for ax, lab, title in [
        (axes[0], np.array([0, 0, 0, 1]), "AND — separable"),
        (axes[1], np.array([0, 1, 1, 1]), "OR — separable"),
        (axes[2], np.array([0, 1, 1, 0]), "XOR — NOT separable"),
    ]:
        for (x, y), l in zip(pts, lab):
            ax.scatter([x], [y], s=340, c=C.orange if l else C.blue, zorder=5,
                       edgecolors=C.black, linewidths=1.6,
                       marker="s" if l else "o")
            ax.text(x, y - 0.22, f"{int(l)}", ha="center", fontsize=13, fontweight="bold")
        xs = np.linspace(-0.45, 1.45, 10)
        if title.startswith("AND"):
            ax.plot(xs, 1.5 - xs, color=C.green, lw=3)
        elif title.startswith("OR"):
            ax.plot(xs, 0.5 - xs, color=C.green, lw=3)
        else:
            ax.plot(xs, 1.5 - xs, color=C.red, lw=2.4, ls="--", alpha=0.8)
            ax.plot(xs, 0.5 - xs, color=C.red, lw=2.4, ls="--", alpha=0.8)
            ax.text(0.5, 1.62, "no single line works", color=C.red, fontsize=11.5,
                    ha="center", fontweight="bold")
        ax.set_xlim(-0.45, 1.45)
        ax.set_ylim(-0.45, 1.85)
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_title(title, fontsize=13)
        ax.grid(False)
    f.suptitle("A perceptron draws one straight line — so XOR is out of reach until you add a hidden layer",
               fontsize=13, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.9))
    save(f, "deep/xor-problem.png")


# ---------------------------------------------------------------- activations
def activations():
    # No sharex: the bottom-right panel is indexed by layer depth (1-25), and
    # sharing that range would squash the six activation curves (x in [-4, 4]).
    f, axes = grid(2, 4, 13.2, 6.2)
    x = np.linspace(-4, 4, 500)

    def relu(v): return np.maximum(0, v)
    def lrelu(v): return np.where(v > 0, v, 0.1 * v)
    def gelu(v): return 0.5 * v * (1 + np.tanh(np.sqrt(2 / np.pi) * (v + 0.044715 * v**3)))
    def silu(v): return v / (1 + np.exp(-v))

    specs = [
        ("Sigmoid", lambda v: 1 / (1 + np.exp(-v)), lambda v: (1 / (1 + np.exp(-v))) * (1 - 1 / (1 + np.exp(-v)))),
        ("Tanh", np.tanh, lambda v: 1 - np.tanh(v) ** 2),
        ("ReLU", relu, lambda v: (v > 0).astype(float)),
        ("Leaky ReLU", lrelu, lambda v: np.where(v > 0, 1.0, 0.1)),
        ("GELU", gelu, None),
        ("SiLU / Swish", silu, None),
    ]
    for ax, (name, fn, d) in zip(axes.ravel(), specs):
        ax.plot(x, fn(x), color=C.blue, lw=2.8, label="f(x)")
        deriv = d(x) if d is not None else np.gradient(fn(x), x)
        ax.plot(x, deriv, color=C.orange, lw=2.2, ls="--", label="f′(x)")
        ax.axhline(0, color=C.grey, lw=1.1)
        ax.axvline(0, color=C.grey, lw=1.1)
        ax.set_title(name, fontsize=12.5)
        ax.set_ylim(-1.4, 2.4)

    ax = axes[1, 2]
    ax.plot(x, 1 / (1 + np.exp(-x)) * (1 - 1 / (1 + np.exp(-x))), color=C.red, lw=2.8)
    ax.axhline(0.25, color=C.grey, ls=":", lw=2)
    ax.text(-3.8, 0.28, "max 0.25", fontsize=11, color=C.grey)
    ax.set_title("Sigmoid gradient\nnever exceeds ¼", fontsize=12.5)
    ax.set_ylim(0, 0.4)

    ax = axes[1, 3]
    depth = np.arange(1, 26)
    ax.semilogy(depth, 0.25**depth, color=C.red, lw=2.8, label="sigmoid (×0.25)")
    ax.semilogy(depth, 1.0**depth, color=C.green, lw=2.8, label="ReLU (×1.0)")
    ax.set_title("Compounded over depth\nwhy sigmoid stopped being used", fontsize=12)
    ax.set_xlabel("layers")
    ax.set_ylabel("gradient scale")
    ax.legend(fontsize=9.5)

    axes[0, 0].legend(fontsize=9.5, loc="upper left")
    for ax in list(axes[0]) + list(axes[1][:2]):
        ax.set_xlabel("x")
    axes[1, 2].set_xlabel("x")
    f.tight_layout()
    save(f, "deep/activation-functions.png")


# ---------------------------------------------------------------- init & gradients
def weight_init():
    """Activation variance across depth under three initialisation schemes."""
    f, axes = grid(1, 2, 11.2, 4.2)
    n_layers, width = 30, 256

    def run(scale_fn, act):
        h = rng.normal(0, 1, (512, width))
        stds = []
        for _ in range(n_layers):
            W = rng.normal(0, scale_fn(width), (width, width))
            h = act(h @ W)
            stds.append(h.std())
        return np.array(stds)

    relu = lambda v: np.maximum(0, v)
    ax = axes[0]
    ax.semilogy(run(lambda n: 0.01, relu), color=C.red, label="too small (σ = 0.01)")
    ax.semilogy(run(lambda n: np.sqrt(1.0 / n), relu), color=C.orange, label="Xavier  √(1/n)")
    ax.semilogy(run(lambda n: np.sqrt(2.0 / n), relu), color=C.green, label="He  √(2/n)  ← for ReLU")
    ax.semilogy(run(lambda n: 0.1, relu), color=C.purple, label="too large (σ = 0.1)")
    ax.set_xlabel("layer")
    ax.set_ylabel("activation std (log scale)")
    ax.set_title("Initialisation decides whether a signal\nsurvives 30 layers")
    ax.legend(fontsize=9.5)

    ax = axes[1]
    layers = np.arange(1, 21)
    for factor, col, lbl in [(0.6, C.red, "×0.6 per layer — vanishing"),
                             (1.0, C.green, "×1.0 — healthy"),
                             (1.5, C.orange, "×1.5 per layer — exploding")]:
        ax.semilogy(layers, factor ** (20 - layers), color=col, lw=2.8, label=lbl)
    ax.set_xlabel("layer (1 = input side)")
    ax.set_ylabel("gradient magnitude (log scale)")
    ax.set_title("Gradients are a product of Jacobians\nso the deviation compounds")
    ax.legend(fontsize=9.5)
    f.tight_layout()
    save(f, "deep/weight-init-and-gradient-flow.png")


# ---------------------------------------------------------------- optimizers
def optimizers():
    """Trajectories on a ravine — the surface that separates the optimizers."""
    f, axes = grid(1, 2, 11.6, 4.6)

    def loss(p): return 0.02 * p[0] ** 2 + 2.2 * p[1] ** 2
    def grad(p): return np.array([0.04 * p[0], 4.4 * p[1]])

    X, Y = np.meshgrid(np.linspace(-11, 3, 400), np.linspace(-3.2, 3.2, 400))
    Z = 0.02 * X**2 + 2.2 * Y**2

    # Each optimizer runs at a well-tuned rate for itself, which is what you
    # would actually do. Measured over 60 steps on this ravine:
    #   SGD (lr .42)      60 sign flips across the ravine, ends at x = -3.4
    #   Momentum (lr .10) 13 sign flips, reaches x = -0.15 — arrives
    #   RMSProp (lr .30)  reaches x = 0.0
    #   Adam (lr .30)     4 sign flips, reaches x = 0.5
    # SGD cannot simply raise its rate: 0.42 is already near the stability
    # limit of the steep direction (2 / 4.4 = 0.45).
    def run(kind, steps=60):
        p = np.array([-9.5, 2.4])
        path = [p.copy()]
        v = np.zeros(2)
        m = np.zeros(2)
        s = np.zeros(2)
        lr = {"sgd": 0.42, "momentum": 0.10, "rmsprop": 0.30, "adam": 0.30}[kind]
        for t in range(1, steps + 1):
            g = grad(p)
            if kind == "sgd":
                p = p - lr * g
            elif kind == "momentum":
                v = 0.9 * v - lr * g
                p = p + v
            elif kind == "rmsprop":
                s = 0.9 * s + 0.1 * g**2
                p = p - lr * g / (np.sqrt(s) + 1e-8)
            elif kind == "adam":
                m = 0.9 * m + 0.1 * g
                s = 0.999 * s + 0.001 * g**2
                mh = m / (1 - 0.9**t)
                sh = s / (1 - 0.999**t)
                p = p - lr * mh / (np.sqrt(sh) + 1e-8)
            if not np.isfinite(p).all() or np.abs(p).max() > 50:
                break
            path.append(p.copy())
        return np.array(path)

    ax = axes[0]
    ax.contour(X, Y, Z, levels=np.linspace(0.2, Z.max(), 16), colors=C.light, linewidths=1.1)
    for kind, col, lbl in [("sgd", C.red, "SGD — 60 zigzags, still short of the minimum"),
                           ("momentum", C.orange, "Momentum — 13 oscillations, and it arrives"),
                           ("rmsprop", C.green, "RMSProp — per-parameter step sizes"),
                           ("adam", C.blue, "Adam — both, and the smoothest path")]:
        pth = run(kind)
        ax.plot(pth[:, 0], pth[:, 1], "-o", color=col, lw=2.3, ms=3.6, label=lbl, alpha=0.95)
    ax.scatter([0], [0], marker="*", c=C.black, s=300, zorder=8)
    ax.set_xlim(-11, 3)
    ax.set_ylim(-3.2, 3.2)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("A ravine: steep across, shallow along\neach optimizer at a well-tuned rate", fontsize=12.5)
    ax.legend(fontsize=9.5, loc="lower right")

    ax = axes[1]
    for kind, col, lbl in [("sgd", C.red, "SGD"), ("momentum", C.orange, "Momentum"),
                           ("rmsprop", C.green, "RMSProp"), ("adam", C.blue, "Adam")]:
        pth = run(kind, 60)
        ax.semilogy([loss(p) for p in pth], color=col, lw=2.6, label=lbl)
    ax.set_xlabel("step")
    ax.set_ylabel("loss (log scale)")
    ax.set_ylim(1e-5, 1e2)
    ax.set_title("Same problem, loss over time")
    ax.legend(fontsize=10)
    f.tight_layout()
    save(f, "deep/optimizer-trajectories.png")


def lr_schedules():
    f, ax = fig(7.8, 4.4)
    steps = np.arange(0, 1000)
    base = 0.1

    ax.plot(steps, np.full_like(steps, base, dtype=float), color=C.grey, ls=":", lw=2.2, label="constant")
    ax.plot(steps, base * 0.5 ** (steps // 250), color=C.orange, label="step decay (×0.5 / 250)")
    ax.plot(steps, base * np.exp(-steps / 400), color=C.green, label="exponential")
    ax.plot(steps, base * 0.5 * (1 + np.cos(np.pi * steps / 1000)), color=C.blue, label="cosine")

    warm = np.where(steps < 100, base * steps / 100,
                    base * 0.5 * (1 + np.cos(np.pi * (steps - 100) / 900)))
    ax.plot(steps, warm, color=C.red, lw=3.2, label="linear warmup + cosine  ← transformer default")
    ax.axvspan(0, 100, color=C.red, alpha=0.08)
    ax.text(50, base * 1.06, "warmup", ha="center", fontsize=10.5, color=C.red, fontweight="bold")
    ax.set_xlabel("training step")
    ax.set_ylabel("learning rate")
    ax.set_title("Learning-rate schedules")
    ax.legend(fontsize=10)
    f.tight_layout()
    save(f, "deep/lr-schedules.png")


# ---------------------------------------------------------------- normalization
def normalization_axes():
    """Which axes each norm averages over — the only thing that distinguishes them."""
    f, axes = grid(1, 4, 13.4, 3.9)
    N, Ch, S = 4, 6, 5  # batch, channels, spatial

    def draw(ax, mask, title):
        for n in range(N):
            for c in range(Ch):
                on = mask(n, c)
                ax.add_patch(Rectangle((c, -n), 0.9, 0.9,
                                       facecolor=C.blue if on else "#EEF2F7",
                                       edgecolor="white", lw=1.6))
        ax.set_xlim(-0.4, Ch + 0.3)
        ax.set_ylim(-N + 0.1, 1.5)
        ax.set_title(title, fontsize=12)
        ax.text(Ch / 2, 1.02, "channel →", ha="center", fontsize=10.5, color=C.grey)
        ax.text(-0.75, -N / 2 + 0.5, "batch →", va="center", rotation=90, fontsize=10.5, color=C.grey)
        clean(ax)

    draw(axes[0], lambda n, c: c == 2, "Batch norm\nover the batch, per channel")
    draw(axes[1], lambda n, c: n == 1, "Layer norm\nover the features, per sample")
    draw(axes[2], lambda n, c: n == 1 and c == 2, "Instance norm\nper sample, per channel")
    draw(axes[3], lambda n, c: n == 1 and 2 <= c < 5, "Group norm\nper sample, per channel group")
    f.suptitle("Blue = the elements averaged together to produce one mean and variance",
               fontsize=13, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.9))
    save(f, "deep/normalization-axes.png")


def batchnorm_effect():
    f, axes = grid(1, 2, 10.8, 4.0)
    ax = axes[0]
    for i, (col, lbl) in enumerate([(C.red, "no norm"), (C.blue, "with batch norm")]):
        for layer in range(5):
            if i == 0:
                d = rng.normal(0.4 * layer, 0.6 + 0.55 * layer, 4000)  # drifting & spreading
            else:
                d = rng.normal(0, 1, 4000)
            ax.violinplot([d], positions=[layer + (0.18 if i else -0.18)], widths=0.32,
                          showextrema=False)
    ax.set_xticks(range(5), [f"layer {i+1}" for i in range(5)])
    ax.set_ylabel("pre-activation value")
    ax.set_title("Left of each pair: no norm (drifts)\nRight: normalised (stays centred)", fontsize=12)

    ax = axes[1]
    ep = np.arange(1, 51)
    ax.plot(ep, 2.4 * np.exp(-ep / 26) + 0.35, color=C.red, label="no normalization")
    ax.plot(ep, 2.4 * np.exp(-ep / 11) + 0.16, color=C.blue, label="with normalization")
    ax.set_xlabel("epoch")
    ax.set_ylabel("training loss")
    ax.set_title("Normalization lets you use a\nhigher learning rate safely", fontsize=12)
    ax.legend(fontsize=10.5)
    f.tight_layout()
    save(f, "deep/normalization-effect.png")


# ---------------------------------------------------------------- residual
def skip_connections():
    f, axes = grid(1, 2, 11.0, 4.3)

    ax = axes[0]
    ax.add_patch(Rectangle((0.5, 2.2), 2.4, 1.0, facecolor=C.blue, alpha=0.75, edgecolor="none"))
    ax.text(1.7, 2.7, "weight layer", ha="center", va="center", color="white", fontsize=11.5,
            fontweight="bold")
    ax.add_patch(Rectangle((0.5, 0.7), 2.4, 1.0, facecolor=C.blue, alpha=0.75, edgecolor="none"))
    ax.text(1.7, 1.2, "weight layer", ha="center", va="center", color="white", fontsize=11.5,
            fontweight="bold")
    ax.annotate("", xy=(1.7, 2.2), xytext=(1.7, 1.7), arrowprops=dict(arrowstyle="->", lw=2.4, color=C.black))
    ax.annotate("", xy=(1.7, 0.7), xytext=(1.7, 0.15), arrowprops=dict(arrowstyle="->", lw=2.4, color=C.black))
    ax.annotate("", xy=(1.7, 4.1), xytext=(1.7, 3.2), arrowprops=dict(arrowstyle="->", lw=2.4, color=C.black))
    ax.add_patch(Circle((1.7, 3.55), 0.22, facecolor="white", edgecolor=C.black, lw=2.2, zorder=5))
    ax.text(1.7, 3.55, "+", ha="center", va="center", fontsize=17, zorder=6, fontweight="bold")
    ax.annotate("", xy=(1.48, 3.55), xytext=(3.9, 3.55),
                arrowprops=dict(arrowstyle="->", lw=2.8, color=C.red,
                                connectionstyle="arc3,rad=0"))
    ax.plot([3.9, 3.9], [0.42, 3.55], color=C.red, lw=2.8)
    ax.annotate("", xy=(3.9, 0.42), xytext=(1.72, 0.42),
                arrowprops=dict(arrowstyle="-", lw=2.8, color=C.red))
    ax.text(4.15, 2.0, "identity\nshortcut", color=C.red, fontsize=11.5, fontweight="bold", va="center")
    ax.text(1.7, 4.35, "F(x) + x", ha="center", fontsize=13, fontweight="bold")
    ax.text(1.7, -0.15, "x", ha="center", fontsize=13, fontweight="bold")
    ax.set_xlim(-0.2, 5.8)
    ax.set_ylim(-0.5, 4.8)
    clean(ax)
    ax.set_title("A residual block learns the change, not the whole map", fontsize=12.5)

    ax = axes[1]
    d = np.arange(1, 61)
    ax.plot(d, 6.5 + 0.9 * (d / 60) ** 0.4 * 8, color=C.red, label="plain net — deeper is worse")
    ax.plot(d, 7.5 * np.exp(-d / 26) + 3.6, color=C.blue, label="residual net — deeper is better")
    ax.set_xlabel("depth (layers)")
    ax.set_ylabel("test error (%)")
    ax.set_title("The degradation problem ResNet solved", fontsize=12.5)
    ax.legend(fontsize=10.5)
    f.tight_layout()
    save(f, "deep/skip-connections.png")


# ---------------------------------------------------------------- regularization
def dropout_fig():
    f, axes = grid(1, 2, 10.2, 4.2)
    layers = [4, 6, 6, 3]

    def draw_net(ax, drop_mask, title):
        pos = {}
        for li, n in enumerate(layers):
            for i in range(n):
                pos[(li, i)] = (li * 1.5, (n - 1) / 2 - i)
        for li in range(len(layers) - 1):
            for i in range(layers[li]):
                for j in range(layers[li + 1]):
                    if drop_mask(li, i) or drop_mask(li + 1, j):
                        continue
                    ax.plot(*zip(pos[(li, i)], pos[(li + 1, j)]), color=C.light, lw=0.9, zorder=1)
        for (li, i), (x, y) in pos.items():
            dropped = drop_mask(li, i)
            ax.add_patch(Circle((x, y), 0.19, zorder=4,
                                facecolor="white" if dropped else C.blue,
                                edgecolor=C.red if dropped else C.blue,
                                lw=2.2, linestyle="--" if dropped else "-"))
        ax.set_xlim(-0.5, 5.0)
        ax.set_ylim(-3.2, 3.2)
        ax.set_title(title, fontsize=12.5)
        clean(ax)

    draw_net(axes[0], lambda li, i: False, "Full network")
    r = np.random.default_rng(3)
    dropped = {(li, i) for li in (1, 2) for i in range(layers[li]) if r.random() < 0.5}
    draw_net(axes[1], lambda li, i: (li, i) in dropped,
             "One dropout mask (p = 0.5 on hidden layers)\na different subnetwork every batch")
    f.tight_layout()
    save(f, "deep/dropout.png")


# ---------------------------------------------------------------- scaling / precision
def scaling_laws():
    f, ax = fig(7.4, 4.4)
    n = np.logspace(6, 11, 100)
    for c, col, lbl in [(1e10, C.red, "small compute budget"),
                        (1e12, C.orange, "medium"),
                        (1e14, C.blue, "large")]:
        loss = 2.2 + 380 * (n ** -0.34) + 4e5 / (c ** 0.28) * (n / 1e9) ** 0.3
        ax.loglog(n, loss, color=col, lw=2.8, label=lbl)
        k = int(np.argmin(loss))
        ax.scatter([n[k]], [loss[k]], s=140, c=col, zorder=6, edgecolors="white", linewidths=1.5)
    ax.set_xlabel("parameters")
    ax.set_ylabel("test loss")
    ax.set_title("Scaling laws: loss falls as a power law,\nand each compute budget has an optimal model size")
    ax.legend(fontsize=10.5, title="compute", title_fontsize=10)
    f.tight_layout()
    save(f, "deep/scaling-laws.png")


def float_formats():
    """Bit layouts — why bf16 replaced fp16 for training."""
    f, ax = fig(9.6, 4.4)
    specs = [
        ("FP32", 1, 8, 23, "range ~1e±38   ·  ~7 decimal digits"),
        ("TF32", 1, 8, 10, "FP32 range, FP16-ish precision (NVIDIA tensor cores)"),
        ("BF16", 1, 8, 7, "same range as FP32 → no loss scaling needed"),
        ("FP16", 1, 5, 10, "narrow range → overflows without loss scaling"),
        ("FP8 (E4M3)", 1, 4, 3, "inference and, increasingly, training"),
    ]
    unit = 0.28
    for row, (name, s, e, m) in enumerate([(n, s, e, m) for n, s, e, m, _ in specs]):
        y = -row
        x = 0.0
        for count, col, lbl in [(s, C.red, "sign"), (e, C.orange, "exponent"), (m, C.blue, "mantissa")]:
            ax.add_patch(Rectangle((x, y), count * unit, 0.7, facecolor=col, edgecolor="white", lw=1.4))
            if count * unit > 0.5:
                ax.text(x + count * unit / 2, y + 0.35, str(count), ha="center", va="center",
                        color="white", fontsize=11.5, fontweight="bold")
            x += count * unit
        ax.text(-0.25, y + 0.35, name, ha="right", va="center", fontsize=12, fontweight="bold")
        ax.text(x + 0.15, y + 0.35, specs[row][4], va="center", fontsize=10, color=C.grey)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=C.red, label="sign"), Patch(facecolor=C.orange, label="exponent (range)"),
                       Patch(facecolor=C.blue, label="mantissa (precision)")],
              loc="lower right", fontsize=10.5, ncol=3)
    ax.set_xlim(-2.6, 13.2)
    ax.set_ylim(-5.3, 1.3)
    clean(ax)
    ax.set_title("Exponent bits buy range; mantissa bits buy precision.\nBF16 keeps FP32's exponent, which is why it trains stably.",
                 fontsize=13)
    f.tight_layout()
    save(f, "deep/float-formats.png")


def parallelism():
    f, axes = grid(1, 3, 12.6, 3.9)

    def gpu(ax, x, y, w, h, label, colour, sub=""):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=colour, alpha=0.85, edgecolor="white", lw=2))
        ax.text(x + w / 2, y + h / 2 + (0.1 if sub else 0), label, ha="center", va="center",
                color="white", fontsize=11, fontweight="bold")
        if sub:
            ax.text(x + w / 2, y + h / 2 - 0.22, sub, ha="center", va="center", color="white", fontsize=9)

    ax = axes[0]
    for i in range(3):
        gpu(ax, i * 1.5, 0, 1.2, 1.0, f"GPU {i}", C.blue, "full model")
        ax.add_patch(Rectangle((i * 1.5, 1.35), 1.2, 0.55, facecolor=C.orange, edgecolor="white", lw=2))
        ax.text(i * 1.5 + 0.6, 1.62, f"batch {i}", ha="center", va="center", fontsize=9.5, color="white")
    ax.annotate("", xy=(4.2, -0.5), xytext=(0.2, -0.5), arrowprops=dict(arrowstyle="<->", lw=2.4, color=C.red))
    ax.text(2.2, -0.85, "all-reduce gradients", ha="center", fontsize=10.5, color=C.red, fontweight="bold")
    ax.set_title("Data parallel\nsame model, different data", fontsize=12)
    ax.set_xlim(-0.4, 5.0)
    ax.set_ylim(-1.3, 2.3)
    clean(ax)

    ax = axes[1]
    for i in range(3):
        gpu(ax, i * 1.5, 0, 1.2, 1.0, f"GPU {i}", C.green, f"layers {i*4}–{i*4+3}")
        if i < 2:
            ax.annotate("", xy=((i + 1) * 1.5 - 0.02, 0.5), xytext=(i * 1.5 + 1.22, 0.5),
                        arrowprops=dict(arrowstyle="->", lw=2.4, color=C.black))
    ax.set_title("Pipeline parallel\nmodel split by layer", fontsize=12)
    ax.set_xlim(-0.4, 5.0)
    ax.set_ylim(-1.3, 2.3)
    clean(ax)

    ax = axes[2]
    for i in range(3):
        gpu(ax, i * 1.5, 0, 1.2, 1.0, f"GPU {i}", C.purple, "⅓ of each\nmatrix")
    ax.annotate("", xy=(4.2, -0.5), xytext=(0.2, -0.5), arrowprops=dict(arrowstyle="<->", lw=2.4, color=C.red))
    ax.text(2.2, -0.85, "all-gather every layer", ha="center", fontsize=10.5, color=C.red, fontweight="bold")
    ax.set_title("Tensor parallel\neach matrix split across GPUs", fontsize=12)
    ax.set_xlim(-0.4, 5.0)
    ax.set_ylim(-1.3, 2.3)
    clean(ax)
    f.tight_layout()
    save(f, "deep/parallelism-strategies.png")


def training_loop_diagram():
    f, ax = fig(10.0, 3.4)
    steps = [("batch", C.grey), ("forward", C.blue), ("loss", C.orange),
             ("backward", C.green), ("step()", C.purple), ("zero_grad()", C.red)]
    for i, (name, col) in enumerate(steps):
        x = i * 1.68
        ax.add_patch(Rectangle((x, 0), 1.42, 0.9, facecolor=col, alpha=0.9, edgecolor="white", lw=2))
        ax.text(x + 0.71, 0.45, name, ha="center", va="center", color="white",
                fontsize=11.5, fontweight="bold")
        if i < len(steps) - 1:
            ax.annotate("", xy=(x + 1.66, 0.45), xytext=(x + 1.44, 0.45),
                        arrowprops=dict(arrowstyle="->", lw=2.4, color=C.black))
    ax.annotate("", xy=(0.5, 0.95), xytext=(9.1, 0.95),
                arrowprops=dict(arrowstyle="->", lw=2.4, color=C.black,
                                connectionstyle="arc3,rad=-0.28"))
    ax.text(4.9, 1.85, "repeat for every batch, every epoch", ha="center", fontsize=12,
            fontweight="bold")
    ax.text(8.55, -0.42, "forgetting this is the\n#1 silent training bug", ha="center",
            fontsize=10, color=C.red, fontweight="bold")
    ax.set_xlim(-0.3, 10.4)
    ax.set_ylim(-1.0, 2.3)
    clean(ax)
    f.tight_layout()
    save(f, "deep/training-loop.png")


def computational_graph():
    f, ax = fig(9.4, 4.0)
    nodes = {
        "x": (0, 1.4), "W": (0, 0.2), "b": (0, -1.0),
        "z = Wx": (1.9, 0.8), "a = z + b": (3.8, 0.2),
        "ŷ = σ(a)": (5.7, 0.2), "L": (7.6, 0.2),
    }
    edges = [("x", "z = Wx"), ("W", "z = Wx"), ("z = Wx", "a = z + b"), ("b", "a = z + b"),
             ("a = z + b", "ŷ = σ(a)"), ("ŷ = σ(a)", "L")]
    for a, b in edges:
        ax.annotate("", xy=nodes[b], xytext=nodes[a],
                    arrowprops=dict(arrowstyle="->", lw=2.4, color=C.blue, shrinkA=32, shrinkB=32))
    for name, (x, y) in nodes.items():
        leaf = name in ("x", "W", "b")
        ax.add_patch(Circle((x, y), 0.46, facecolor="white",
                            edgecolor=C.green if leaf else C.blue, lw=2.8, zorder=4))
        ax.text(x, y, name, ha="center", va="center", fontsize=10.5, zorder=5, fontweight="bold")
    ax.annotate("", xy=(0.4, -1.75), xytext=(7.4, -1.75),
                arrowprops=dict(arrowstyle="->", lw=3, color=C.red))
    ax.text(3.9, -2.15, "backward: chain rule, right to left — one sweep computes every gradient",
            ha="center", fontsize=11.5, color=C.red, fontweight="bold")
    ax.text(3.9, 2.35, "forward: compute values, left to right", ha="center", fontsize=11.5,
            color=C.blue, fontweight="bold")
    ax.set_xlim(-0.9, 8.5)
    ax.set_ylim(-2.6, 2.7)
    clean(ax)
    f.tight_layout()
    save(f, "deep/computational-graph.png")


if __name__ == "__main__":
    print("deep learning:")
    xor_problem()
    activations()
    weight_init()
    optimizers()
    lr_schedules()
    normalization_axes()
    batchnorm_effect()
    skip_connections()
    dropout_fig()
    scaling_laws()
    float_formats()
    parallelism()
    training_loop_diagram()
    computational_graph()
