"""Figures for docs/machine-learning/05-generative-models/."""

import numpy as np
from matplotlib.patches import Circle, Rectangle

from kbstyle import C, clean, fig, grid, save

rng = np.random.default_rng(2)


def _box(ax, x, y, w, h, label, colour, fs=10.5, tc="white"):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=colour, alpha=0.9, edgecolor="white", lw=1.8))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", color=tc, fontsize=fs,
            fontweight="bold")


def discriminative_vs_generative():
    f, axes = grid(1, 2, 10.6, 4.2)
    a = rng.normal([-1.3, -0.9], 0.75, (120, 2))
    b = rng.normal([1.4, 1.0], 0.75, (120, 2))

    ax = axes[0]
    ax.scatter(*a.T, c=C.blue, s=26, alpha=0.8)
    ax.scatter(*b.T, c=C.orange, s=26, alpha=0.8, marker="s")
    xs = np.linspace(-4, 4, 10)
    ax.plot(xs, -0.9 * xs + 0.1, color=C.black, lw=3.2)
    ax.set_title("Discriminative — models P(y | x)\nonly needs the boundary", fontsize=12.5)

    ax = axes[1]
    ax.scatter(*a.T, c=C.blue, s=26, alpha=0.55)
    ax.scatter(*b.T, c=C.orange, s=26, alpha=0.55, marker="s")
    th = np.linspace(0, 2 * np.pi, 200)
    for cen, col in [((-1.3, -0.9), C.blue), ((1.4, 1.0), C.orange)]:
        for s in (1, 2):
            ax.plot(cen[0] + 0.75 * s * np.cos(th), cen[1] + 0.75 * s * np.sin(th),
                    color=col, lw=2.4)
    ax.set_title("Generative — models P(x | y)\nlearns the whole distribution, so it can sample",
                 fontsize=12.5)
    for ax in axes:
        ax.set_xlim(-4, 4); ax.set_ylim(-3.4, 3.4)
        ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    f.tight_layout()
    save(f, "generative/discriminative-vs-generative.png")


def autoencoder():
    f, ax = fig(10.4, 4.0)
    widths = [(0, 2.2), (1.5, 1.5), (3.0, 0.6), (4.5, 1.5), (6.0, 2.2)]
    labels = ["input\nx", "", "latent\nz", "", "reconstruction\nx̂"]
    cols = [C.grey, C.blue, C.red, C.green, C.grey]
    for (x, h), lbl, col in zip(widths, labels, cols):
        ax.add_patch(Rectangle((x, -h / 2), 0.85, h, facecolor=col, alpha=0.85,
                               edgecolor="white", lw=2))
        if lbl:
            ax.text(x + 0.42, 0, lbl, ha="center", va="center", color="white", fontsize=10.5,
                    fontweight="bold")
    ax.text(1.9, 1.55, "encoder", ha="center", fontsize=12, color=C.blue, fontweight="bold")
    ax.text(5.0, 1.55, "decoder", ha="center", fontsize=12, color=C.green, fontweight="bold")
    ax.text(3.42, -1.5, "bottleneck\nforces compression", ha="center", fontsize=11, color=C.red,
            fontweight="bold")
    for i in range(len(widths) - 1):
        ax.annotate("", xy=(widths[i + 1][0] - 0.02, 0), xytext=(widths[i][0] + 0.87, 0),
                    arrowprops=dict(arrowstyle="->", lw=2.2, color=C.black))
    ax.text(3.42, 2.5, "Trained to reproduce its own input — the loss is ‖x − x̂‖²",
            ha="center", fontsize=11.5)
    ax.set_xlim(-0.5, 7.6)
    ax.set_ylim(-2.6, 3.1)
    clean(ax)
    f.tight_layout()
    save(f, "generative/autoencoder.png")


def vae_latent():
    f, axes = grid(1, 2, 11.2, 4.4)

    ax = axes[0]
    _box(ax, 0.0, 1.3, 1.1, 1.2, "x", C.grey)
    _box(ax, 1.7, 1.3, 1.3, 1.2, "encoder", C.blue, fs=9.5)
    _box(ax, 3.6, 2.15, 0.95, 0.75, "μ", C.orange, fs=11)
    _box(ax, 3.6, 1.05, 0.95, 0.75, "σ", C.orange, fs=11)
    ax.add_patch(Circle((5.5, 1.9), 0.42, facecolor=C.red, alpha=0.9, edgecolor="white", lw=2))
    ax.text(5.5, 1.9, "z", ha="center", va="center", color="white", fontsize=12, fontweight="bold")
    _box(ax, 6.6, 1.3, 1.3, 1.2, "decoder", C.green, fs=9.5)
    _box(ax, 8.5, 1.3, 1.1, 1.2, "x̂", C.grey)
    for x0, x1 in [(1.12, 1.68), (3.02, 3.58), (4.57, 5.06), (5.94, 6.58), (7.92, 8.48)]:
        ax.annotate("", xy=(x1, 1.9), xytext=(x0, 1.9),
                    arrowprops=dict(arrowstyle="->", lw=2.2, color=C.black))
    ax.text(5.5, 0.75, "z = μ + σ ⊙ ε,  ε ~ N(0, I)", ha="center", fontsize=11.5, color=C.red,
            fontweight="bold")
    ax.text(5.5, 0.2, "the reparameterisation trick:\nrandomness moved off the gradient path",
            ha="center", fontsize=10, color=C.grey)
    ax.set_xlim(-0.3, 9.9)
    ax.set_ylim(-0.3, 3.4)
    clean(ax)
    ax.set_title("VAE: encode to a distribution, not a point", fontsize=12.5)

    ax = axes[1]
    n = 11
    g = np.linspace(-2.2, 2.2, n)
    canvas = np.zeros((n * 12, n * 12))
    yy, xx = np.mgrid[0:12, 0:12] / 12 - 0.5
    for i, z1 in enumerate(g):
        for j, z2 in enumerate(g):
            # A smooth 2-parameter family standing in for decoded digits.
            blob = np.exp(-((xx - 0.16 * z2) ** 2 + (yy - 0.16 * z1) ** 2) / (0.02 + 0.006 * abs(z1)))
            ring = np.exp(-((np.sqrt(xx**2 + yy**2) - (0.16 + 0.045 * z2)) ** 2) / 0.004)
            canvas[i * 12:(i + 1) * 12, j * 12:(j + 1) * 12] = np.clip(blob * 0.8 + ring * 0.6, 0, 1)
    ax.imshow(canvas, cmap="magma")
    ax.set_xlabel("z₂ →")
    ax.set_ylabel("z₁ →")
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    ax.set_title("Walking the latent grid gives smooth changes\n— the KL term is what keeps it continuous",
                 fontsize=11.5)
    f.tight_layout()
    save(f, "generative/vae.png")


def gan_architecture():
    f, ax = fig(10.6, 4.4)
    ax.add_patch(Circle((0.75, 2.6), 0.45, facecolor=C.purple, alpha=0.9, edgecolor="white", lw=2))
    ax.text(0.75, 2.6, "z", ha="center", va="center", color="white", fontsize=13, fontweight="bold")
    ax.text(0.75, 1.85, "noise", ha="center", fontsize=10.5, color=C.grey)
    _box(ax, 1.9, 2.05, 1.6, 1.1, "Generator\nG", C.blue, fs=11)
    _box(ax, 4.1, 2.05, 1.5, 1.1, "fake\nsample", C.blue, fs=10)
    _box(ax, 4.1, 0.35, 1.5, 1.1, "real\nsample", C.green, fs=10)
    _box(ax, 6.4, 1.2, 1.6, 1.1, "Discriminator\nD", C.orange, fs=10)
    _box(ax, 8.6, 1.2, 1.5, 1.1, "real or\nfake?", C.grey, fs=10.5)
    for x0, y0, x1, y1 in [(1.22, 2.6, 1.86, 2.6), (3.52, 2.6, 4.06, 2.6),
                           (5.62, 2.6, 6.36, 2.0), (5.62, 0.9, 6.36, 1.5),
                           (8.02, 1.75, 8.56, 1.75)]:
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="->", lw=2.2, color=C.black))
    ax.annotate("", xy=(2.7, 1.95), xytext=(7.2, 1.1),
                arrowprops=dict(arrowstyle="->", lw=2.6, color=C.red,
                                connectionstyle="arc3,rad=0.32"))
    ax.text(4.9, -0.15, "G's gradient: 'fool D next time'", ha="center", fontsize=11, color=C.red,
            fontweight="bold")
    ax.text(5.0, 3.75, "Two networks in opposition: D learns to spot fakes, G learns to beat D.",
            ha="center", fontsize=11.5)
    ax.set_xlim(-0.2, 10.6)
    ax.set_ylim(-0.7, 4.2)
    clean(ax)
    ax.set_title("Generative adversarial network", fontsize=13.5)
    f.tight_layout()
    save(f, "generative/gan-architecture.png")


def mode_collapse():
    f, axes = grid(1, 3, 12.2, 4.0)
    centres = np.array([[np.cos(t), np.sin(t)] for t in np.linspace(0, 2 * np.pi, 9)[:-1]]) * 2.1

    ax = axes[0]
    real = np.vstack([c + rng.normal(0, 0.17, (90, 2)) for c in centres])
    ax.scatter(*real.T, s=14, c=C.blue, alpha=0.65)
    ax.set_title("Target distribution\n8 modes", fontsize=12.5)

    ax = axes[1]
    part = np.vstack([centres[i] + rng.normal(0, 0.17, (240, 2)) for i in (1, 5)])
    ax.scatter(*real.T, s=12, c=C.light, alpha=0.55)
    ax.scatter(*part.T, s=14, c=C.red, alpha=0.7)
    ax.set_title("Mode collapse\nG found 2 modes that fool D\nand stopped exploring", fontsize=11.5)

    ax = axes[2]
    good = np.vstack([c + rng.normal(0, 0.2, (90, 2)) for c in centres])
    ax.scatter(*real.T, s=12, c=C.light, alpha=0.55)
    ax.scatter(*good.T, s=14, c=C.green, alpha=0.7)
    ax.set_title("Healthy training\nall modes covered", fontsize=12.5)
    for ax in axes:
        ax.set_xlim(-3.2, 3.2); ax.set_ylim(-3.2, 3.2)
        ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        ax.set_aspect("equal")
    f.tight_layout()
    save(f, "generative/mode-collapse.png")


def diffusion_process():
    """Forward noising of a 2-D distribution, and the reverse that undoes it."""
    f, axes = grid(2, 6, 13.6, 5.2)
    n = 700
    t = rng.uniform(0, 2 * np.pi, n)
    x0 = np.stack([np.cos(t) * 2.0, np.sin(t) * 2.0], 1) + rng.normal(0, 0.13, (n, 2))
    x0[:n // 2] *= 0.42  # inner ring, so the structure is obvious

    betas = np.linspace(1e-4, 0.09, 300)
    alphas_bar = np.cumprod(1 - betas)
    steps = [0, 40, 90, 150, 220, 299]
    noise = rng.normal(size=(n, 2))

    for ax, s in zip(axes[0], steps):
        ab = alphas_bar[s]
        xt = np.sqrt(ab) * x0 + np.sqrt(1 - ab) * noise
        ax.scatter(*xt.T, s=6, c=C.blue, alpha=0.55)
        ax.set_title(f"t = {s}", fontsize=11)
    axes[0, 0].set_ylabel("forward\n(add noise)", fontsize=11.5, fontweight="bold")

    for ax, s in zip(axes[1], reversed(steps)):
        ab = alphas_bar[s]
        xt = np.sqrt(ab) * x0 + np.sqrt(1 - ab) * noise
        ax.scatter(*xt.T, s=6, c=C.green, alpha=0.55)
        ax.set_title(f"t = {s}", fontsize=11)
    axes[1, 0].set_ylabel("reverse\n(learned denoise)", fontsize=11.5, fontweight="bold")

    for ax in axes.ravel():
        ax.set_xlim(-3.4, 3.4); ax.set_ylim(-3.4, 3.4)
        ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        ax.set_aspect("equal")
    f.suptitle("Diffusion: destroy structure with noise on a fixed schedule, then train a network to reverse one step at a time",
               fontsize=13, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.92))
    save(f, "generative/diffusion-process.png")


def diffusion_schedule():
    f, axes = grid(1, 2, 11.0, 4.0)
    T = 1000
    lin = np.linspace(1e-4, 0.02, T)
    ab_lin = np.cumprod(1 - lin)
    s = 0.008
    ts = np.linspace(0, T, T + 1) / T
    fcos = np.cos((ts + s) / (1 + s) * np.pi / 2) ** 2
    ab_cos = (fcos / fcos[0])[1:]

    ax = axes[0]
    ax.plot(ab_lin, color=C.blue, label="linear β schedule")
    ax.plot(ab_cos, color=C.orange, label="cosine schedule")
    ax.set_xlabel("timestep t")
    ax.set_ylabel(r"$\bar{\alpha}_t$  (signal remaining)")
    ax.set_title("Signal decays to zero by t = T", fontsize=12.5)
    ax.legend(fontsize=10.5)

    ax = axes[1]
    ax.plot(np.sqrt(ab_lin), color=C.blue, label="signal  √ᾱ")
    ax.plot(np.sqrt(1 - ab_lin), color=C.red, label="noise  √(1−ᾱ)")
    ax.set_xlabel("timestep t")
    ax.set_title("At every t the sample is a fixed blend\nof the image and pure noise", fontsize=12.5)
    ax.legend(fontsize=10.5)
    f.tight_layout()
    save(f, "generative/diffusion-schedule.png")


def guidance_scale():
    f, axes = grid(1, 4, 13.0, 3.6)
    n = 900
    for ax, w in zip(axes, [0.0, 1.5, 5.0, 15.0]):
        t = rng.uniform(0, 2 * np.pi, n)
        r = 1.0 + rng.normal(0, 0.55 / (1 + 0.55 * w), n)
        spread = 1.0 / (1 + 0.35 * w)
        pts = np.stack([r * np.cos(t), r * np.sin(t)], 1) * (0.6 + 0.4 * spread)
        pts += rng.normal(0, 0.5 * spread, (n, 2))
        ax.scatter(*pts.T, s=7, c=C.blue, alpha=0.5)
        ax.set_title({0.0: "w = 0\nunconditional — diverse, off-prompt",
                      1.5: "w = 1.5\nbalanced",
                      5.0: "w = 5\ntighter to the prompt",
                      15.0: "w = 15\noversaturated, low diversity"}[w], fontsize=10.5)
        ax.set_xlim(-3, 3); ax.set_ylim(-3, 3)
        ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        ax.set_aspect("equal")
    f.suptitle("Classifier-free guidance scale trades diversity against prompt adherence",
               fontsize=13, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.88))
    save(f, "generative/guidance-scale.png")


def normalizing_flow():
    f, axes = grid(1, 3, 12.2, 3.9)
    n = 1500
    z = rng.normal(size=(n, 2))
    ax = axes[0]
    ax.scatter(*z.T, s=6, c=C.blue, alpha=0.45)
    ax.set_title("Base density\nsimple, easy to sample", fontsize=12)

    h = z.copy()
    h[:, 1] = h[:, 1] + 0.6 * h[:, 0] ** 2  # an invertible shear
    ax = axes[1]
    ax.scatter(*h.T, s=6, c=C.orange, alpha=0.45)
    ax.set_title("After one invertible layer\n(a coupling transform)", fontsize=12)

    g = h.copy()
    ang = 0.6 * np.linalg.norm(g, axis=1)
    R = np.stack([g[:, 0] * np.cos(ang) - g[:, 1] * np.sin(ang),
                  g[:, 0] * np.sin(ang) + g[:, 1] * np.cos(ang)], 1)
    ax = axes[2]
    ax.scatter(*R.T, s=6, c=C.green, alpha=0.45)
    ax.set_title("After several\ncomplex target density", fontsize=12)
    for ax in axes:
        ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    f.suptitle("A flow is a chain of invertible maps — so the exact likelihood is computable, "
               "via the Jacobian determinant", fontsize=12.5, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.9))
    save(f, "generative/normalizing-flow.png")


def model_family_tradeoffs():
    f, ax = fig(8.4, 4.6)
    models = {
        "VAE": (2.0, 4.2, 4.6, C.blue),
        "GAN": (4.4, 2.0, 4.6, C.orange),
        "Normalizing flow": (2.6, 4.6, 2.2, C.green),
        "Diffusion": (4.7, 4.7, 1.6, C.red),
        "Autoregressive": (4.5, 4.4, 1.2, C.purple),
    }
    for name, (q, cov, speed, col) in models.items():
        ax.scatter([q], [cov], s=120 + speed * 130, c=col, alpha=0.72, edgecolors="white",
                   linewidths=2, zorder=5)
        ax.annotate(name, xy=(q, cov), xytext=(0, -30 - speed * 3), textcoords="offset points",
                    ha="center", fontsize=11, fontweight="bold", color=col)
    ax.set_xlabel("sample quality →")
    ax.set_ylabel("mode coverage / diversity →")
    ax.set_xlim(1.0, 5.9)
    ax.set_ylim(0.7, 5.9)
    ax.set_title("The generative trilemma\nbubble size = sampling speed (bigger is faster)",
                 fontsize=12.5)
    ax.text(5.55, 1.1, "no model wins\non all three", ha="right", fontsize=11, color=C.grey,
            style="italic")
    f.tight_layout()
    save(f, "generative/generative-trilemma.png")


if __name__ == "__main__":
    print("generative:")
    discriminative_vs_generative()
    autoencoder()
    vae_latent()
    gan_architecture()
    mode_collapse()
    diffusion_process()
    diffusion_schedule()
    guidance_scale()
    normalizing_flow()
    model_family_tradeoffs()
