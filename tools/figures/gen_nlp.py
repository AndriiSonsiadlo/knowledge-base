"""Figures for docs/machine-learning/03-sequence-and-nlp/."""

import numpy as np
from matplotlib.patches import Circle, Rectangle

from kbstyle import C, clean, fig, grid, save

rng = np.random.default_rng(0)


def _box(ax, x, y, w, h, label, colour, fs=10.5, alpha=0.9, tc="white"):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=colour, alpha=alpha, edgecolor="white", lw=1.8))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", color=tc, fontsize=fs,
            fontweight="bold")


# ---------------------------------------------------------------- RNN
def rnn_unrolled():
    f, ax = fig(11.0, 3.9)
    T = 5
    for t in range(T):
        x = t * 2.1
        _box(ax, x, 0.9, 1.25, 0.95, "RNN\ncell", C.blue)
        ax.annotate("", xy=(x + 0.62, 0.85), xytext=(x + 0.62, 0.2),
                    arrowprops=dict(arrowstyle="->", lw=2.2, color=C.black))
        ax.text(x + 0.62, -0.05, f"x{t+1}", ha="center", fontsize=12, fontweight="bold")
        ax.annotate("", xy=(x + 0.62, 2.55), xytext=(x + 0.62, 1.88),
                    arrowprops=dict(arrowstyle="->", lw=2.2, color=C.black))
        ax.text(x + 0.62, 2.7, f"h{t+1}", ha="center", fontsize=12, fontweight="bold", color=C.green)
        if t < T - 1:
            ax.annotate("", xy=(x + 2.08, 1.38), xytext=(x + 1.27, 1.38),
                        arrowprops=dict(arrowstyle="->", lw=2.6, color=C.green))
    ax.text(9.9, 1.38, "same weights\nat every step", fontsize=11, color=C.green, va="center",
            fontweight="bold")
    ax.annotate("", xy=(0.62, 3.35), xytext=(9.0, 3.35),
                arrowprops=dict(arrowstyle="->", lw=2.6, color=C.red))
    ax.text(4.8, 3.55, "backpropagation through time — the gradient path that vanishes",
            ha="center", fontsize=11, color=C.red, fontweight="bold")
    ax.set_xlim(-0.6, 12.0)
    ax.set_ylim(-0.5, 4.1)
    clean(ax)
    f.tight_layout()
    save(f, "nlp/rnn-unrolled.png")


def lstm_cell():
    f, axes = grid(1, 2, 11.6, 4.4)

    ax = axes[0]
    _box(ax, 0.6, 0.5, 6.6, 3.0, "", C.light, alpha=0.35, tc=C.black)
    ax.plot([0.2, 7.8], [3.05, 3.05], color=C.green, lw=4)
    ax.text(4.0, 3.28, "cell state  C  — the uninterrupted highway", ha="center", fontsize=11,
            color=C.green, fontweight="bold")
    for i, (name, col, x) in enumerate([("forget\ngate", C.red, 1.4),
                                        ("input\ngate", C.orange, 3.2),
                                        ("output\ngate", C.blue, 5.6)]):
        _box(ax, x, 1.1, 1.3, 1.0, name, col, fs=10)
        ax.add_patch(Circle((x + 0.65, 3.05), 0.19, facecolor="white", edgecolor=C.black, lw=2, zorder=6))
        ax.text(x + 0.65, 3.05, "×" if i != 1 else "+", ha="center", va="center", fontsize=13, zorder=7)
        ax.annotate("", xy=(x + 0.65, 2.86), xytext=(x + 0.65, 2.12),
                    arrowprops=dict(arrowstyle="->", lw=2, color=col))
    ax.text(4.0, 0.15, "gates are sigmoids: 0 = block, 1 = pass", ha="center", fontsize=10.5,
            color=C.grey)
    ax.set_xlim(0, 8.4)
    ax.set_ylim(-0.2, 3.9)
    clean(ax)
    ax.set_title("LSTM: gates decide what the cell state keeps", fontsize=12.5)

    ax = axes[1]
    steps = np.arange(1, 61)
    ax.semilogy(steps, 0.82**steps, color=C.red, lw=2.8, label="vanilla RNN — gradient dies")
    ax.semilogy(steps, 0.995**steps, color=C.green, lw=2.8, label="LSTM — additive path survives")
    ax.axhline(1e-6, color=C.grey, ls=":", lw=2)
    ax.text(2, 1.6e-6, "effectively zero", fontsize=10.5, color=C.grey)
    ax.set_xlabel("timesteps back")
    ax.set_ylabel("gradient magnitude (log scale)")
    ax.set_title("Why the gating matters", fontsize=12.5)
    ax.legend(fontsize=10)
    f.tight_layout()
    save(f, "nlp/lstm-cell.png")


# ---------------------------------------------------------------- attention
def attention_heatmap():
    """A causal self-attention pattern over a real sentence."""
    toks = ["The", "cat", "that", "chased", "the", "mouse", "was", "hungry"]
    n = len(toks)
    A = np.zeros((n, n))
    # Hand-built to show a plausible dependency: "was" attends to "cat".
    links = {0: {0: 1.0}, 1: {0: 0.6, 1: 0.4}, 2: {1: 0.7, 2: 0.3},
             3: {1: 0.5, 2: 0.2, 3: 0.3}, 4: {4: 0.6, 3: 0.4},
             5: {3: 0.4, 4: 0.3, 5: 0.3}, 6: {1: 0.65, 5: 0.15, 6: 0.2},
             7: {1: 0.45, 6: 0.3, 7: 0.25}}
    for i, row in links.items():
        for j, v in row.items():
            A[i, j] = v

    f, axes = grid(1, 2, 11.8, 4.8)
    ax = axes[0]
    im = ax.imshow(A, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(n), toks, rotation=45, ha="right")
    ax.set_yticks(range(n), toks)
    ax.set_xlabel("attending to (keys)")
    ax.set_ylabel("query token")
    ax.set_title("Attention weights\n'was' looks back at 'cat', not 'mouse'", fontsize=12.5)
    ax.grid(False)
    for i in range(n):
        for j in range(n):
            if A[i, j] > 0.05:
                ax.text(j, i, f"{A[i,j]:.1f}", ha="center", va="center", fontsize=8.5,
                        color="white" if A[i, j] > 0.5 else C.black)
    f.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[1]
    mask = np.tril(np.ones((n, n)))
    ax.imshow(mask, cmap="Greys", vmin=0, vmax=1.6)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, "✓" if mask[i, j] else "−∞", ha="center", va="center",
                    fontsize=10, color=C.black if mask[i, j] else C.red, fontweight="bold")
    ax.set_xticks(range(n), toks, rotation=45, ha="right")
    ax.set_yticks(range(n), toks)
    ax.set_title("Causal mask\nfuture positions set to −∞ before softmax", fontsize=12.5)
    ax.grid(False)
    f.tight_layout()
    save(f, "nlp/attention-weights.png")


def qkv_mechanism():
    f, ax = fig(10.6, 4.4)
    _box(ax, 0.2, 1.6, 1.5, 1.0, "X\n(tokens)", C.grey)
    for i, (name, col, y) in enumerate([("Q", C.blue, 3.1), ("K", C.orange, 1.6), ("V", C.green, 0.1)]):
        _box(ax, 2.5, y, 1.1, 1.0, name, col)
        ax.annotate("", xy=(2.45, y + 0.5), xytext=(1.75, 2.1),
                    arrowprops=dict(arrowstyle="->", lw=2.2, color=col))
        ax.text(2.05, y + 0.62 if i != 1 else y + 1.15, f"W{name}", fontsize=9.5, color=col,
                fontweight="bold")
    _box(ax, 4.6, 2.35, 1.9, 1.0, "QKᵀ / √d", C.purple)
    ax.annotate("", xy=(4.55, 2.85), xytext=(3.65, 3.6), arrowprops=dict(arrowstyle="->", lw=2.2, color=C.blue))
    ax.annotate("", xy=(4.55, 2.7), xytext=(3.65, 2.1), arrowprops=dict(arrowstyle="->", lw=2.2, color=C.orange))
    _box(ax, 7.0, 2.35, 1.6, 1.0, "softmax", C.red)
    ax.annotate("", xy=(6.95, 2.85), xytext=(6.55, 2.85), arrowprops=dict(arrowstyle="->", lw=2.2, color=C.black))
    _box(ax, 9.0, 1.3, 1.5, 1.0, "output", C.blue)
    ax.annotate("", xy=(8.95, 1.9), xytext=(8.65, 2.7), arrowprops=dict(arrowstyle="->", lw=2.2, color=C.red))
    ax.annotate("", xy=(8.95, 1.7), xytext=(5.75, 0.6), arrowprops=dict(arrowstyle="->", lw=2.2, color=C.green))
    ax.text(6.0, 3.75, "scores: how much each token\nshould attend to each other token",
            ha="center", fontsize=10, color=C.purple)
    ax.text(5.4, 0.05, "weighted sum of values", ha="center", fontsize=10, color=C.green)
    ax.text(5.6, -0.7, "√d keeps the dot products from saturating the softmax as d grows",
            ha="center", fontsize=10.5, color=C.grey, style="italic")
    ax.set_xlim(-0.2, 11.2)
    ax.set_ylim(-1.1, 4.4)
    clean(ax)
    ax.set_title("Scaled dot-product attention", fontsize=13.5)
    f.tight_layout()
    save(f, "nlp/qkv-attention.png")


def transformer_block():
    f, axes = grid(1, 2, 10.4, 6.0)
    variants = [
        (axes[0], False, "Post-LN (original, 2017)\nLayerNorm(x + Sublayer(x))\nneeds warmup to train"),
        (axes[1], True, "Pre-LN (modern default)\nx + Sublayer(LayerNorm(x))\ntrains stably without warmup"),
    ]
    for ax, pre, title in variants:
        y = 0.0
        ax.text(1.75, y - 0.5, "input", ha="center", fontsize=11.5, fontweight="bold")
        for name, col in [("Multi-head\nattention", C.blue), ("Feed-forward\n(MLP)", C.green)]:
            branch_start = y  # where the residual tap leaves the trunk
            if pre:
                # LayerNorm -> sublayer -> add
                _box(ax, 0.9, y + 0.35, 1.7, 0.5, "LayerNorm", C.orange, fs=9.5)
                _box(ax, 0.9, y + 1.05, 1.7, 0.95, name, col, fs=9.5)
                add_y = y + 2.35
                block_top = y + 2.0
            else:
                # sublayer -> add -> LayerNorm
                _box(ax, 0.9, y + 0.35, 1.7, 0.95, name, col, fs=9.5)
                add_y = y + 1.62
                block_top = y + 1.30
            ax.annotate("", xy=(1.75, add_y - 0.2), xytext=(1.75, block_top),
                        arrowprops=dict(arrowstyle="->", lw=2, color=C.black))
            ax.add_patch(Circle((1.75, add_y), 0.19, facecolor="white", edgecolor=C.black,
                                lw=2, zorder=6))
            ax.text(1.75, add_y, "+", ha="center", va="center", fontsize=14, zorder=7)

            # Residual: taps the trunk below the sublayer, rejoins at the add.
            ax.plot([1.75, 3.15], [branch_start + 0.05, branch_start + 0.05], color=C.red, lw=2.4)
            ax.plot([3.15, 3.15], [branch_start + 0.05, add_y], color=C.red, lw=2.4)
            ax.annotate("", xy=(1.95, add_y), xytext=(3.15, add_y),
                        arrowprops=dict(arrowstyle="->", lw=2.4, color=C.red))

            if pre:
                y = add_y + 0.45
            else:
                # In Post-LN the norm sits AFTER the add, on the trunk itself.
                ax.annotate("", xy=(1.75, add_y + 0.42), xytext=(1.75, add_y + 0.2),
                            arrowprops=dict(arrowstyle="->", lw=2, color=C.black))
                _box(ax, 0.9, add_y + 0.42, 1.7, 0.5, "LayerNorm", C.orange, fs=9.5)
                y = add_y + 1.35
        if pre:
            _box(ax, 0.9, y + 0.1, 1.7, 0.5, "final LayerNorm", C.orange, fs=9)
            y += 0.9
        ax.text(3.42, 1.5, "residual", color=C.red, fontsize=10, rotation=90, va="center")
        ax.set_xlim(0.2, 4.3)
        ax.set_ylim(-1.0, y + 0.4)
        clean(ax)
        ax.set_title(title, fontsize=11.5)
    f.tight_layout()
    save(f, "nlp/transformer-block.png")


def positional_encoding():
    f, axes = grid(1, 3, 12.6, 3.9)
    L, D = 64, 64
    pos = np.arange(L)[:, None]
    i = np.arange(D)[None, :]
    angle = pos / np.power(10000, (2 * (i // 2)) / D)
    PE = np.where(i % 2 == 0, np.sin(angle), np.cos(angle))

    ax = axes[0]
    im = ax.imshow(PE, cmap="RdBu", aspect="auto", vmin=-1, vmax=1)
    ax.set_xlabel("embedding dimension")
    ax.set_ylabel("position")
    ax.set_title("Sinusoidal encoding\nlow dims wiggle fast, high dims slow", fontsize=12)
    ax.grid(False)
    f.colorbar(im, ax=ax, fraction=0.046)

    ax = axes[1]
    for d, col in [(0, C.blue), (4, C.orange), (16, C.green), (32, C.red)]:
        ax.plot(PE[:, d], color=col, lw=2.2, label=f"dim {d}")
    ax.set_xlabel("position")
    ax.set_title("Each dimension is a\ndifferent-frequency wave", fontsize=12)
    ax.legend(fontsize=9.5, ncol=2)

    ax = axes[2]
    sim = PE @ PE.T / D
    im = ax.imshow(sim, cmap="viridis", aspect="auto")
    ax.set_xlabel("position")
    ax.set_ylabel("position")
    ax.set_title("Similarity depends on distance\n— relative position is recoverable", fontsize=12)
    ax.grid(False)
    f.colorbar(im, ax=ax, fraction=0.046)
    f.tight_layout()
    save(f, "nlp/positional-encoding.png")


def decoding_strategies():
    """How temperature and truncation reshape the next-token distribution."""
    logits = np.array([3.2, 2.6, 2.1, 1.4, 1.0, 0.6, 0.2, -0.3, -0.8, -1.5])
    words = ["the", "a", "this", "my", "our", "his", "its", "one", "some", "any"]

    def softmax(v):
        e = np.exp(v - v.max())
        return e / e.sum()

    f, axes = grid(1, 4, 13.4, 3.7, sharey=True)
    for ax, (T, title) in zip(axes[:2], [(0.5, "Temperature 0.5\nsharper — safer, repetitive"),
                                         (1.5, "Temperature 1.5\nflatter — creative, riskier")]):
        p = softmax(logits / T)
        ax.bar(range(10), p, color=C.blue)
        ax.set_title(title, fontsize=11.5)
        ax.set_xticks(range(10), words, rotation=60, fontsize=9)

    p = softmax(logits)
    ax = axes[2]
    k = 4
    cols = [C.blue if i < k else C.light for i in range(10)]
    ax.bar(range(10), p, color=cols)
    ax.set_title(f"Top-k (k = {k})\nkeep k, renormalise", fontsize=11.5)
    ax.set_xticks(range(10), words, rotation=60, fontsize=9)

    ax = axes[3]
    cum = np.cumsum(p)
    keep = cum <= 0.9
    keep[np.argmax(cum > 0.9)] = True
    ax.bar(range(10), p, color=[C.blue if keep[i] else C.light for i in range(10)])
    ax.set_title(f"Top-p / nucleus (p = 0.9)\nkeep the smallest set summing to 0.9\n→ {keep.sum()} tokens here",
                 fontsize=11)
    ax.set_xticks(range(10), words, rotation=60, fontsize=9)
    axes[0].set_ylabel("probability")
    f.tight_layout()
    save(f, "nlp/decoding-strategies.png")


def tokenization():
    f, ax = fig(10.4, 3.6)
    rows = [
        ("Characters", ["t", "o", "k", "e", "n", "i", "z", "a", "t", "i", "o", "n"], C.red,
         "tiny vocab, very long sequences"),
        ("Subwords (BPE)", ["token", "ization"], C.green, "the practical middle ground"),
        ("Words", ["tokenization"], C.blue, "huge vocab, and unknown words break it"),
    ]
    for r, (name, pieces, col, note) in enumerate(rows):
        y = -r * 1.15
        ax.text(-0.35, y + 0.32, name, ha="right", va="center", fontsize=12, fontweight="bold")
        x = 0.0
        for p in pieces:
            w = max(0.42, len(p) * 0.29)
            ax.add_patch(Rectangle((x, y), w - 0.06, 0.64, facecolor=col, alpha=0.85,
                                   edgecolor="white", lw=2))
            ax.text(x + (w - 0.06) / 2, y + 0.32, p, ha="center", va="center", color="white",
                    fontsize=11, fontweight="bold")
            x += w
        ax.text(x + 0.25, y + 0.32, f"{len(pieces)} token{'s' if len(pieces)!=1 else ''} — {note}",
                va="center", fontsize=10.5, color=C.grey)
    ax.set_xlim(-2.6, 9.4)
    ax.set_ylim(-2.7, 1.0)
    clean(ax)
    ax.set_title("Three granularities for the same word", fontsize=13)
    f.tight_layout()
    save(f, "nlp/tokenization-granularity.png")


def lora():
    f, ax = fig(10.0, 4.2)
    ax.add_patch(Rectangle((0.3, 0.4), 2.6, 2.6, facecolor=C.blue, alpha=0.35, edgecolor=C.blue, lw=2.6))
    ax.text(1.6, 1.7, "W₀\nd × d\nFROZEN", ha="center", va="center", fontsize=12, fontweight="bold")
    ax.text(1.6, 3.25, "e.g. 4096 × 4096 = 16.7 M params", ha="center", fontsize=10, color=C.grey)

    ax.text(3.4, 1.7, "+", ha="center", va="center", fontsize=26, fontweight="bold")

    ax.add_patch(Rectangle((4.0, 0.4), 0.55, 2.6, facecolor=C.orange, edgecolor="white", lw=2))
    ax.text(4.28, 1.7, "B\nd×r", ha="center", va="center", fontsize=10.5, color="white",
            fontweight="bold", rotation=90)
    ax.add_patch(Rectangle((4.75, 2.45), 2.6, 0.55, facecolor=C.green, edgecolor="white", lw=2))
    ax.text(6.05, 2.72, "A   r×d", ha="center", va="center", fontsize=10.5, color="white",
            fontweight="bold")
    ax.text(5.7, 0.05, "rank r = 8  →  2 × 4096 × 8 = 65 k params\n≈ 0.4 % of the frozen matrix",
            ha="center", fontsize=11, color=C.red, fontweight="bold")
    ax.annotate("", xy=(8.2, 1.7), xytext=(7.5, 1.7), arrowprops=dict(arrowstyle="->", lw=2.6, color=C.black))
    ax.add_patch(Rectangle((8.4, 0.4), 2.6, 2.6, facecolor=C.purple, alpha=0.35, edgecolor=C.purple, lw=2.6))
    ax.text(9.7, 1.7, "W₀ + BA\nused at\ninference", ha="center", va="center", fontsize=11.5,
            fontweight="bold")
    ax.set_xlim(0, 11.4)
    ax.set_ylim(-0.7, 3.8)
    clean(ax)
    ax.set_title("LoRA: freeze the big matrix, train a low-rank update beside it", fontsize=13.5)
    f.tight_layout()
    save(f, "nlp/lora.png")


def embeddings():
    f, axes = grid(1, 2, 11.0, 4.2)
    ax = axes[0]
    words = {"king": (2.4, 2.2), "queen": (2.0, 0.7), "man": (0.6, 2.0), "woman": (0.2, 0.5),
             "prince": (3.3, 2.6), "princess": (2.9, 1.1)}
    for w, (x, y) in words.items():
        ax.scatter([x], [y], s=110, c=C.blue, zorder=5)
        ax.text(x + 0.09, y + 0.12, w, fontsize=12, fontweight="bold")
    for a, b in [("king", "queen"), ("man", "woman"), ("prince", "princess")]:
        ax.annotate("", xy=words[b], xytext=words[a],
                    arrowprops=dict(arrowstyle="->", lw=2.4, color=C.red, alpha=0.85))
    ax.text(1.5, -0.15, "the same offset ≈ 'gender'", fontsize=11, color=C.red, fontweight="bold")
    ax.set_title("Directions carry meaning\nking − man + woman ≈ queen", fontsize=12.5)
    ax.set_xlim(-0.5, 4.4)
    ax.set_ylim(-0.5, 3.2)
    clean(ax)

    ax = axes[1]
    r = np.random.default_rng(4)
    groups = {"animals": ((-1.6, 1.2), C.blue), "countries": ((1.7, 1.4), C.orange),
              "verbs": ((0.2, -1.5), C.green)}
    for name, ((cx, cy), col) in groups.items():
        pts = r.normal([cx, cy], 0.5, (26, 2))
        ax.scatter(*pts.T, s=38, c=col, alpha=0.8, label=name)
    ax.set_title("Similar words cluster\n(2-D projection of a 300-D space)", fontsize=12.5)
    ax.legend(fontsize=10.5)
    clean(ax)
    f.tight_layout()
    save(f, "nlp/word-embeddings.png")


def seq2seq():
    f, ax = fig(11.0, 4.0)
    src = ["Le", "chat", "noir"]
    tgt = ["The", "black", "cat"]
    for i, w in enumerate(src):
        _box(ax, i * 1.5, 2.2, 1.25, 0.85, w, C.blue)
        ax.text(i * 1.5 + 0.62, 1.95, "↑", ha="center", fontsize=13)
    ax.text(2.2, 3.4, "Encoder", ha="center", fontsize=12.5, fontweight="bold", color=C.blue)
    _box(ax, 5.0, 2.2, 1.5, 0.85, "context", C.purple)
    ax.annotate("", xy=(4.95, 2.62), xytext=(4.3, 2.62), arrowprops=dict(arrowstyle="->", lw=2.6, color=C.black))
    for i, w in enumerate(tgt):
        _box(ax, 7.2 + i * 1.5, 2.2, 1.25, 0.85, w, C.green)
        if i < len(tgt) - 1:
            ax.annotate("", xy=(7.2 + (i + 1) * 1.5 - 0.02, 2.62), xytext=(7.2 + i * 1.5 + 1.27, 2.62),
                        arrowprops=dict(arrowstyle="->", lw=2.2, color=C.green))
    ax.annotate("", xy=(7.15, 2.62), xytext=(6.55, 2.62), arrowprops=dict(arrowstyle="->", lw=2.6, color=C.black))
    ax.text(9.0, 3.4, "Decoder", ha="center", fontsize=12.5, fontweight="bold", color=C.green)
    ax.text(5.75, 1.55, "the bottleneck:\none fixed vector for the whole sentence", ha="center",
            fontsize=10.5, color=C.red, fontweight="bold")
    for i in range(3):
        for j in range(3):
            ax.plot([i * 1.5 + 0.62, 7.2 + j * 1.5 + 0.62], [2.15, 2.15], color=C.orange,
                    lw=1.1, alpha=0.35)
    ax.text(5.75, 0.75, "attention (added later) reconnects every output to every input,\nremoving that bottleneck",
            ha="center", fontsize=10.5, color=C.orange, fontweight="bold")
    ax.set_xlim(-0.4, 12.2)
    ax.set_ylim(0.3, 3.9)
    clean(ax)
    f.tight_layout()
    save(f, "nlp/seq2seq-bottleneck.png")


def attention_cost():
    f, ax = fig(7.4, 4.3)
    n = np.arange(128, 32769, 128)
    ax.loglog(n, n**2 * 2e-9, color=C.red, lw=2.8, label="attention — O(n²)")
    ax.loglog(n, n * 4096 * 2e-9, color=C.blue, lw=2.8, label="feed-forward — O(n·d)")
    cross = 4096
    ax.axvline(cross, color=C.grey, ls="--", lw=2)
    ax.text(cross * 1.1, 1e-3, "beyond ~4 k tokens attention\ndominates the cost", fontsize=10.5,
            color=C.grey)
    ax.set_xlabel("sequence length (tokens)")
    ax.set_ylabel("relative cost")
    ax.set_title("Why long context is expensive")
    ax.legend(fontsize=10.5)
    f.tight_layout()
    save(f, "nlp/attention-quadratic-cost.png")


if __name__ == "__main__":
    print("nlp:")
    rnn_unrolled()
    lstm_cell()
    attention_heatmap()
    qkv_mechanism()
    transformer_block()
    positional_encoding()
    decoding_strategies()
    tokenization()
    lora()
    embeddings()
    seq2seq()
    attention_cost()
