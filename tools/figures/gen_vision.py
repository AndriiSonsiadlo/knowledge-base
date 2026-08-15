"""Figures for docs/machine-learning/04-computer-vision/."""

import numpy as np
from matplotlib.patches import Circle, Rectangle

from kbstyle import C, clean, fig, grid, save

rng = np.random.default_rng(1)


def sample_image(n=64):
    """A synthetic but structured greyscale image: disc, bar, gradient, noise."""
    y, x = np.mgrid[0:n, 0:n] / n
    img = 0.28 + 0.45 * x
    img += 0.42 * (((x - 0.34) ** 2 + (y - 0.36) ** 2) < 0.028)
    img[int(0.62 * n):int(0.72 * n), int(0.18 * n):int(0.86 * n)] = 0.06
    img += rng.normal(0, 0.022, (n, n))
    return np.clip(img, 0, 1)


def conv2d(img, k):
    kh, kw = k.shape
    pad = kh // 2
    p = np.pad(img, pad, mode="edge")
    out = np.zeros_like(img)
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            out[i, j] = (p[i:i + kh, j:j + kw] * k).sum()
    return out


# ---------------------------------------------------------------- images as tensors
def images_as_tensors():
    f, axes = grid(1, 4, 13.0, 3.5)
    n = 48
    y, x = np.mgrid[0:n, 0:n] / n
    r = np.clip(0.85 - 0.7 * y, 0, 1)
    g = np.clip(0.25 + 0.65 * x, 0, 1)
    b = np.clip(0.9 - 0.8 * x * y * 2, 0, 1)
    rgb = np.stack([r, g, b], -1)
    axes[0].imshow(rgb)
    axes[0].set_title("RGB image\nshape (48, 48, 3)", fontsize=12)
    for ax, ch, name, cmap in [(axes[1], r, "Red", "Reds"), (axes[2], g, "Green", "Greens"),
                               (axes[3], b, "Blue", "Blues")]:
        ax.imshow(ch, cmap=cmap, vmin=0, vmax=1)
        ax.set_title(f"{name} channel\nshape (48, 48)", fontsize=12)
    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
    f.suptitle("An image is a tensor: every pixel is a number per channel",
               fontsize=13.5, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.9))
    save(f, "vision/images-as-tensors.png")


# ---------------------------------------------------------------- convolution
def convolution_kernels():
    img = sample_image()
    kernels = {
        "Identity": np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]], float),
        "Blur (box)": np.ones((3, 3)) / 9,
        "Sobel — vertical edges": np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], float),
        "Sobel — horizontal edges": np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], float),
        "Sharpen": np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], float),
    }
    f, axes = grid(1, 6, 14.0, 3.0)
    axes[0].imshow(img, cmap="gray", vmin=0, vmax=1)
    axes[0].set_title("input", fontsize=11.5)
    for ax, (name, k) in zip(axes[1:], kernels.items()):
        out = conv2d(img, k)
        ax.imshow(out, cmap="gray")
        ax.set_title(name, fontsize=10.5)
    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
    f.suptitle("The same convolution, different kernels — a CNN learns these numbers itself",
               fontsize=13, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.88))
    save(f, "vision/convolution-kernels.png")


def convolution_mechanics():
    """One 3×3 kernel stepping over a 5×5 input, with the arithmetic shown."""
    f, axes = grid(1, 3, 12.4, 4.0)
    inp = np.array([[3, 1, 0, 2, 4], [1, 5, 2, 1, 0], [0, 2, 7, 3, 1],
                    [4, 1, 3, 6, 2], [2, 0, 1, 4, 5]], float)
    k = np.array([[1, 0, -1], [1, 0, -1], [1, 0, -1]], float)

    def draw_grid(ax, M, title, highlight=None, fmt="{:.0f}", cmap="Blues"):
        ax.imshow(M, cmap=cmap, alpha=0.55)
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                ax.text(j, i, fmt.format(M[i, j]), ha="center", va="center", fontsize=12,
                        fontweight="bold")
        if highlight:
            i0, j0, h, w = highlight
            ax.add_patch(Rectangle((j0 - 0.5, i0 - 0.5), w, h, fill=False, edgecolor=C.red, lw=3.5))
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        ax.set_title(title, fontsize=12.5)

    draw_grid(axes[0], inp, "Input 5×5", highlight=(0, 0, 3, 3))
    draw_grid(axes[1], k, "Kernel 3×3\n(vertical edge detector)", cmap="Oranges")
    out = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            out[i, j] = (inp[i:i + 3, j:j + 3] * k).sum()
    draw_grid(axes[2], out, "Output 3×3\n(no padding, stride 1)", highlight=(0, 0, 1, 1), cmap="Greens")
    val = (inp[0:3, 0:3] * k).sum()
    axes[2].text(1.0, 3.05, f"top-left = Σ(patch × kernel) = {val:.0f}", ha="center", fontsize=11.5,
                 color=C.red, fontweight="bold")
    f.tight_layout()
    save(f, "vision/convolution-mechanics.png")


def receptive_field():
    f, ax = fig(9.0, 4.0)
    sizes = [(9, "input"), (7, "conv 3×3"), (5, "conv 3×3"), (3, "conv 3×3"), (1, "conv 3×3")]
    for li, (s, name) in enumerate(sizes):
        x0 = li * 2.05
        for i in range(s):
            for j in range(s):
                shade = 1.0 if (li == 0 and 0 <= i < 9 and 0 <= j < 9) else 1.0
                ax.add_patch(Rectangle((x0 + j * 0.16, -i * 0.16), 0.14, 0.14,
                                       facecolor=C.blue, alpha=0.22 + 0.12 * li,
                                       edgecolor="white", lw=0.5))
        ax.text(x0 + s * 0.08, 0.42, f"{s}×{s}", ha="center", fontsize=11.5, fontweight="bold")
        ax.text(x0 + s * 0.08, -s * 0.16 - 0.28, name, ha="center", fontsize=10, color=C.grey)
    ax.text(4.1, -1.9, "Each 3×3 conv adds 2 to the receptive field.\n"
                       "Stacking small kernels is cheaper than one big one — and adds a non-linearity each time.",
            ha="center", fontsize=11.5)
    ax.set_xlim(-0.4, 9.6)
    ax.set_ylim(-2.5, 0.9)
    clean(ax)
    ax.set_title("Receptive field grows with depth", fontsize=13)
    f.tight_layout()
    save(f, "vision/receptive-field.png")


def pooling():
    f, axes = grid(1, 3, 11.6, 3.6)
    M = np.array([[1, 3, 2, 4], [5, 6, 1, 2], [7, 2, 8, 3], [1, 4, 2, 9]], float)

    def show(ax, A, title, cmap):
        ax.imshow(A, cmap=cmap, alpha=0.55)
        for i in range(A.shape[0]):
            for j in range(A.shape[1]):
                ax.text(j, i, f"{A[i,j]:.1f}".rstrip("0").rstrip("."), ha="center", va="center",
                        fontsize=13, fontweight="bold")
        ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        ax.set_title(title, fontsize=12.5)

    show(axes[0], M, "Input 4×4", "Blues")
    for (i0, j0), col in [((0, 0), C.red), ((0, 2), C.green), ((2, 0), C.orange), ((2, 2), C.purple)]:
        axes[0].add_patch(Rectangle((j0 - 0.5, i0 - 0.5), 2, 2, fill=False, edgecolor=col, lw=3))
    mx = np.array([[M[i:i+2, j:j+2].max() for j in (0, 2)] for i in (0, 2)])
    av = np.array([[M[i:i+2, j:j+2].mean() for j in (0, 2)] for i in (0, 2)])
    show(axes[1], mx, "Max pool 2×2\nkeeps the strongest response", "Reds")
    show(axes[2], av, "Average pool 2×2\nsmooths the region", "Greens")
    f.tight_layout()
    save(f, "vision/pooling.png")


def augmentation():
    f, axes = grid(2, 4, 12.0, 6.0)
    base = sample_image(56)
    ops = [
        ("original", lambda a: a),
        ("horizontal flip", lambda a: a[:, ::-1]),
        ("rotate 90°", lambda a: np.rot90(a)),
        ("crop + resize", lambda a: np.kron(a[10:38, 10:38], np.ones((2, 2)))),
        ("brightness", lambda a: np.clip(a * 1.5, 0, 1)),
        ("contrast", lambda a: np.clip((a - 0.5) * 1.9 + 0.5, 0, 1)),
        ("gaussian noise", lambda a: np.clip(a + rng.normal(0, 0.11, a.shape), 0, 1)),
        ("cutout", None),
    ]
    for ax, (name, fn) in zip(axes.ravel(), ops):
        if name == "cutout":
            out = base.copy()
            out[14:34, 26:46] = 0.0
        else:
            out = fn(base)
        ax.imshow(out, cmap="gray", vmin=0, vmax=1)
        ax.set_title(name, fontsize=11.5)
        ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    f.suptitle("Augmentation: same label, more variation — the cheapest regularizer in vision",
               fontsize=13.5, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.93))
    save(f, "vision/data-augmentation.png")


def iou():
    f, axes = grid(1, 4, 12.8, 3.5)
    cases = [(0.05, "0.05 — miss"), (0.35, "0.35 — poor"), (0.62, "0.62 — usable"), (0.88, "0.88 — good")]
    for ax, (target, label) in zip(axes, cases):
        gt = (1.0, 1.0, 3.0, 2.4)
        # Solve for the horizontal offset that yields the target IoU.
        best, bo = None, 0
        for off in np.linspace(0, 3.0, 3000):
            px, py, pw, ph = 1.0 + off, 1.0, 3.0, 2.4
            ix = max(0, min(gt[0] + gt[2], px + pw) - max(gt[0], px))
            iy = max(0, min(gt[1] + gt[3], py + ph) - max(gt[1], py))
            inter = ix * iy
            union = gt[2] * gt[3] + pw * ph - inter
            v = inter / union
            if best is None or abs(v - target) < abs(best - target):
                best, bo = v, off
        px = 1.0 + bo
        ax.add_patch(Rectangle(gt[:2], gt[2], gt[3], facecolor=C.blue, alpha=0.35,
                               edgecolor=C.blue, lw=3, label="ground truth"))
        ax.add_patch(Rectangle((px, 1.0), 3.0, 2.4, facecolor=C.orange, alpha=0.35,
                               edgecolor=C.orange, lw=3, label="prediction"))
        ax.set_xlim(0.4, 7.4)
        ax.set_ylim(0.3, 4.3)
        ax.set_title(f"IoU = {best:.2f}\n{label.split('—')[1].strip()}", fontsize=12)
        clean(ax)
    axes[0].legend(fontsize=9.5, loc="upper right")
    f.suptitle("Intersection over Union — the threshold (usually 0.5) decides what counts as a detection",
               fontsize=13, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.88))
    save(f, "vision/iou.png")


def detection_vs_segmentation():
    f, axes = grid(1, 4, 13.0, 3.6)
    n = 64
    img = np.full((n, n), 0.82)
    yy, xx = np.mgrid[0:n, 0:n]
    cat = ((xx - 20) ** 2 / 90 + (yy - 34) ** 2 / 150) < 1
    dog = ((xx - 44) ** 2 / 110 + (yy - 32) ** 2 / 190) < 1
    img[cat] = 0.42
    img[dog] = 0.24

    axes[0].imshow(img, cmap="gray", vmin=0, vmax=1)
    axes[0].set_title("Classification\n'contains: cat, dog'", fontsize=11.5)

    axes[1].imshow(img, cmap="gray", vmin=0, vmax=1)
    for (x0, y0, w, h), col, lbl in [((9, 20, 22, 28), C.blue, "cat"), ((31, 17, 26, 32), C.orange, "dog")]:
        axes[1].add_patch(Rectangle((x0, y0), w, h, fill=False, edgecolor=col, lw=3))
        axes[1].text(x0, y0 - 2, lbl, color=col, fontsize=11, fontweight="bold")
    axes[1].set_title("Object detection\nbox + label per object", fontsize=11.5)

    sem = np.zeros((n, n, 3))
    sem[:] = (0.93, 0.93, 0.93)
    sem[cat | dog] = (0.0, 0.45, 0.70)
    axes[2].imshow(sem)
    axes[2].set_title("Semantic segmentation\nper-pixel class — both are 'animal'", fontsize=11.5)

    inst = np.zeros((n, n, 3))
    inst[:] = (0.93, 0.93, 0.93)
    inst[cat] = (0.0, 0.45, 0.70)
    inst[dog] = (0.90, 0.62, 0.0)
    axes[3].imshow(inst)
    axes[3].set_title("Instance segmentation\nper-pixel, and the two are distinct", fontsize=11.5)

    for ax in axes:
        ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    f.tight_layout()
    save(f, "vision/vision-task-types.png")


def vit_patches():
    """Two panels on top, then the flattened patch sequence as a wide strip."""
    import matplotlib.pyplot as plt

    img = sample_image(64)
    f = plt.figure(figsize=(11.0, 6.2))
    gs = f.add_gridspec(2, 2, height_ratios=[2.5, 1.0], hspace=0.42, wspace=0.15)

    ax = f.add_subplot(gs[0, 0])
    ax.imshow(img, cmap="gray", vmin=0, vmax=1)
    ax.set_title("Input 64×64", fontsize=12.5)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)

    ax = f.add_subplot(gs[0, 1])
    ax.imshow(img, cmap="gray", vmin=0, vmax=1)
    for i in range(0, 65, 16):
        ax.axhline(i - 0.5, color=C.red, lw=2.4)
        ax.axvline(i - 0.5, color=C.red, lw=2.4)
    ax.set_title("Split into 16×16 patches → 16 patches", fontsize=12.5)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)

    # The sequence strip: one axes, patches drawn side by side in image coords.
    ax = f.add_subplot(gs[1, :])
    gap = 3
    strip = np.ones((16, 16 * 16 + gap * 15))
    for idx in range(16):
        r, c = divmod(idx, 4)
        strip[:, idx * (16 + gap):idx * (16 + gap) + 16] = img[r * 16:(r + 1) * 16,
                                                               c * 16:(c + 1) * 16]
    ax.imshow(strip, cmap="gray", vmin=0, vmax=1, aspect="equal")
    for idx in range(16):
        ax.text(idx * (16 + gap) + 8, 19.5, str(idx + 1), ha="center", fontsize=9, color=C.grey)
    ax.set_title("Flattened into a sequence of 16 tokens — then fed to a standard transformer",
                 fontsize=12.5)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    save(f, "vision/vit-patches.png")


def transfer_learning():
    f, ax = fig(10.4, 4.0)
    stages = [("conv 1\nedges", C.blue), ("conv 2\ntextures", C.blue), ("conv 3\nparts", C.blue),
              ("conv 4\nobjects", C.orange), ("classifier\nhead", C.red)]
    for i, (name, col) in enumerate(stages):
        x = i * 2.0
        frozen = i < 3
        ax.add_patch(Rectangle((x, 0.6), 1.65, 1.4, facecolor=col,
                               alpha=0.35 if frozen else 0.92, edgecolor=col, lw=2.6,
                               linestyle="--" if frozen else "-"))
        ax.text(x + 0.82, 1.3, name, ha="center", va="center", fontsize=10.5,
                fontweight="bold", color=C.black if frozen else "white")
        ax.text(x + 0.82, 0.25, "frozen" if frozen else "re-trained", ha="center",
                fontsize=10, color=C.grey if frozen else C.red, fontweight="bold")
        if i < len(stages) - 1:
            ax.annotate("", xy=(x + 1.98, 1.3), xytext=(x + 1.67, 1.3),
                        arrowprops=dict(arrowstyle="->", lw=2.2, color=C.black))
    ax.text(5.0, 2.55, "Early layers learn generic features that transfer.\n"
                       "Later layers are task-specific — those are the ones you retrain.",
            ha="center", fontsize=11.5)
    ax.set_xlim(-0.4, 10.4)
    ax.set_ylim(-0.3, 3.3)
    clean(ax)
    ax.set_title("Transfer learning: freeze the general, retrain the specific", fontsize=13)
    f.tight_layout()
    save(f, "vision/transfer-learning.png")


def cnn_architectures():
    f, ax = fig(10.6, 4.4)
    nets = [
        ("LeNet-5", 1998, 0.06, 5, C.grey),
        ("AlexNet", 2012, 60, 8, C.blue),
        ("VGG-16", 2014, 138, 16, C.green),
        ("GoogLeNet", 2014, 6.8, 22, C.purple),
        ("ResNet-50", 2015, 25.6, 50, C.orange),
        ("ResNet-152", 2015, 60, 152, C.red),
    ]
    for name, year, params, depth, col in nets:
        ax.scatter([depth], [params], s=230, c=col, zorder=5, edgecolors="white", linewidths=2)
        ax.annotate(f"{name}\n({year})", xy=(depth, params), xytext=(0, 16),
                    textcoords="offset points", ha="center", fontsize=10, fontweight="bold")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("depth (layers, log scale)")
    ax.set_ylabel("parameters, millions (log scale)")
    ax.set_title("Depth rose sharply; parameter count did not.\nSkip connections and 1×1 bottlenecks are why.",
                 fontsize=12.5)
    ax.set_ylim(0.03, 400)
    f.tight_layout()
    save(f, "vision/cnn-architectures.png")


def gradcam():
    f, axes = grid(1, 3, 11.6, 3.7)
    n = 72
    img = sample_image(n)
    axes[0].imshow(img, cmap="gray", vmin=0, vmax=1)
    axes[0].set_title("Input", fontsize=12.5)

    yy, xx = np.mgrid[0:n, 0:n]
    heat = np.exp(-(((xx - 0.34 * n) ** 2 + (yy - 0.36 * n) ** 2) / (2 * (0.13 * n) ** 2)))
    axes[1].imshow(heat, cmap="jet")
    axes[1].set_title("Grad-CAM heatmap\nwhere the gradient says the class lives", fontsize=11.5)

    axes[2].imshow(img, cmap="gray", vmin=0, vmax=1)
    axes[2].imshow(heat, cmap="jet", alpha=0.5)
    axes[2].set_title("Overlaid\nthe model looked at the disc", fontsize=11.5)
    for ax in axes:
        ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    f.tight_layout()
    save(f, "vision/gradcam.png")


if __name__ == "__main__":
    print("vision:")
    images_as_tensors()
    convolution_kernels()
    convolution_mechanics()
    receptive_field()
    pooling()
    augmentation()
    iou()
    detection_vs_segmentation()
    vit_patches()
    transfer_learning()
    cnn_architectures()
    gradcam()
