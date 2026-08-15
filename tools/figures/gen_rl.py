"""Figures for docs/machine-learning/06-reinforcement-learning/.

The gridworld and cliff-walking figures run real value iteration / Q-learning,
so the numbers and arrows shown are the actual converged results.
"""

import numpy as np
from matplotlib.patches import Circle, FancyArrow, Rectangle

from kbstyle import C, clean, fig, grid, save

rng = np.random.default_rng(3)


def agent_env_loop():
    f, ax = fig(8.6, 3.9)
    ax.add_patch(Rectangle((0.4, 1.2), 2.3, 1.4, facecolor=C.blue, alpha=0.9,
                           edgecolor="white", lw=2))
    ax.text(1.55, 1.9, "Agent", ha="center", va="center", color="white", fontsize=14,
            fontweight="bold")
    ax.add_patch(Rectangle((5.4, 1.2), 2.6, 1.4, facecolor=C.green, alpha=0.9,
                           edgecolor="white", lw=2))
    ax.text(6.7, 1.9, "Environment", ha="center", va="center", color="white", fontsize=14,
            fontweight="bold")
    ax.annotate("", xy=(5.35, 2.35), xytext=(2.75, 2.35),
                arrowprops=dict(arrowstyle="->", lw=2.8, color=C.black))
    ax.text(4.05, 2.5, "action  aₜ", ha="center", fontsize=12, fontweight="bold")
    ax.annotate("", xy=(2.75, 1.75), xytext=(5.35, 1.75),
                arrowprops=dict(arrowstyle="->", lw=2.8, color=C.orange))
    ax.text(4.05, 1.42, "state  sₜ₊₁", ha="center", fontsize=12, fontweight="bold", color=C.orange)
    ax.annotate("", xy=(2.75, 1.05), xytext=(5.35, 1.05),
                arrowprops=dict(arrowstyle="->", lw=2.8, color=C.red))
    ax.text(4.05, 0.72, "reward  rₜ₊₁", ha="center", fontsize=12, fontweight="bold", color=C.red)
    ax.text(4.2, 3.15, "The agent is not told the right action — only how good the outcome was.",
            ha="center", fontsize=11.5)
    ax.set_xlim(0, 8.6)
    ax.set_ylim(0.3, 3.6)
    clean(ax)
    f.tight_layout()
    save(f, "rl/agent-environment-loop.png")


# ---------------------------------------------------------------- gridworld
GRID_H, GRID_W = 4, 4
WALLS = {(1, 1), (2, 2)}
GOAL = (0, 3)
TRAP = (1, 3)


def _gridworld_value_iteration(gamma=0.9, step_cost=-0.04):
    """Standard 4×4 gridworld, deterministic moves, solved by value iteration."""
    V = np.zeros((GRID_H, GRID_W))
    acts = {"↑": (-1, 0), "↓": (1, 0), "←": (0, -1), "→": (0, 1)}
    terminal = {GOAL: 1.0, TRAP: -1.0}
    for s, r in terminal.items():
        V[s] = r
    for _ in range(400):
        newV = V.copy()
        for i in range(GRID_H):
            for j in range(GRID_W):
                if (i, j) in WALLS or (i, j) in terminal:
                    continue
                best = -1e9
                for di, dj in acts.values():
                    ni, nj = i + di, j + dj
                    if not (0 <= ni < GRID_H and 0 <= nj < GRID_W) or (ni, nj) in WALLS:
                        ni, nj = i, j
                    best = max(best, step_cost + gamma * V[ni, nj])
                newV[i, j] = best
        V = newV
    policy = {}
    for i in range(GRID_H):
        for j in range(GRID_W):
            if (i, j) in WALLS or (i, j) in terminal:
                continue
            best, ba = -1e9, None
            for a, (di, dj) in acts.items():
                ni, nj = i + di, j + dj
                if not (0 <= ni < GRID_H and 0 <= nj < GRID_W) or (ni, nj) in WALLS:
                    ni, nj = i, j
                v = step_cost + gamma * V[ni, nj]
                if v > best:
                    best, ba = v, a
            policy[(i, j)] = ba
    return V, policy


def gridworld_mdp():
    V, policy = _gridworld_value_iteration()
    f, axes = grid(1, 3, 12.4, 4.2)

    def base(ax):
        for i in range(GRID_H):
            for j in range(GRID_W):
                if (i, j) in WALLS:
                    fc = C.black
                elif (i, j) == GOAL:
                    fc = C.green
                elif (i, j) == TRAP:
                    fc = C.red
                else:
                    fc = "#F3F4F6"
                ax.add_patch(Rectangle((j, -i), 0.96, 0.96, facecolor=fc, edgecolor="white", lw=2.5))
        ax.set_xlim(-0.15, GRID_W + 0.1)
        ax.set_ylim(-GRID_H + 0.85, 1.1)
        clean(ax)
        ax.set_aspect("equal")

    ax = axes[0]
    base(ax)
    ax.text(GOAL[1] + 0.48, -GOAL[0] + 0.48, "+1", ha="center", va="center", fontsize=15,
            color="white", fontweight="bold")
    ax.text(TRAP[1] + 0.48, -TRAP[0] + 0.48, "−1", ha="center", va="center", fontsize=15,
            color="white", fontweight="bold")
    ax.text(0.48, -3 + 0.48, "start", ha="center", va="center", fontsize=11, fontweight="bold")
    ax.set_title("The MDP\nstates, two terminal rewards,\nstep cost −0.04", fontsize=12)

    ax = axes[1]
    base(ax)
    for i in range(GRID_H):
        for j in range(GRID_W):
            if (i, j) in WALLS:
                continue
            col = "white" if (i, j) in (GOAL, TRAP) else C.black
            ax.text(j + 0.48, -i + 0.48, f"{V[i, j]:.2f}", ha="center", va="center",
                    fontsize=12, fontweight="bold", color=col)
    ax.set_title("V*(s) after value iteration\nγ = 0.9", fontsize=12)

    ax = axes[2]
    base(ax)
    arrows = {"↑": (0, 0.3), "↓": (0, -0.3), "←": (-0.3, 0), "→": (0.3, 0)}
    for (i, j), a in policy.items():
        dx, dy = arrows[a]
        ax.annotate("", xy=(j + 0.48 + dx, -i + 0.48 + dy), xytext=(j + 0.48 - dx, -i + 0.48 - dy),
                    arrowprops=dict(arrowstyle="->", lw=3.2, color=C.blue))
    ax.text(GOAL[1] + 0.48, -GOAL[0] + 0.48, "+1", ha="center", va="center", fontsize=14,
            color="white", fontweight="bold")
    ax.text(TRAP[1] + 0.48, -TRAP[0] + 0.48, "−1", ha="center", va="center", fontsize=14,
            color="white", fontweight="bold")
    ax.set_title("The greedy policy π*(s)\nread straight off V*", fontsize=12)
    f.tight_layout()
    save(f, "rl/gridworld-value-iteration.png")


def discount_factor():
    f, ax = fig(7.4, 4.2)
    t = np.arange(0, 61)
    for g, col in [(0.5, C.red), (0.9, C.orange), (0.99, C.blue), (0.999, C.green)]:
        ax.plot(t, g**t, color=col, lw=2.8, label=f"γ = {g}   (horizon ≈ {1/(1-g):.0f} steps)")
    ax.set_xlabel("steps into the future")
    ax.set_ylabel("weight on that reward")
    ax.set_title("The discount factor sets the effective planning horizon\n1/(1−γ)")
    ax.legend(fontsize=10.5)
    f.tight_layout()
    save(f, "rl/discount-factor.png")


# ---------------------------------------------------------------- cliff walking
def cliff_walking():
    """The canonical Sutton & Barto example separating Q-learning from SARSA."""
    H, W = 4, 12
    start, goal = (3, 0), (3, 11)
    cliff = {(3, j) for j in range(1, 11)}
    acts = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def step(s, a):
        i, j = s
        di, dj = acts[a]
        ni, nj = min(max(i + di, 0), H - 1), min(max(j + dj, 0), W - 1)
        if (ni, nj) in cliff:
            return start, -100.0, False
        return (ni, nj), -1.0, (ni, nj) == goal

    def train(kind, episodes=2500, eps=0.1, alpha=0.5, gamma=1.0, seed=0):
        r = np.random.default_rng(seed)
        Q = np.zeros((H, W, 4))
        returns = []
        for _ in range(episodes):
            s = start
            total = 0.0
            a = r.integers(4) if r.random() < eps else int(np.argmax(Q[s]))
            for _ in range(400):
                s2, rew, done = step(s, a)
                total += rew
                a2 = r.integers(4) if r.random() < eps else int(np.argmax(Q[s2]))
                target = rew + gamma * (0 if done else
                                        (Q[s2].max() if kind == "q" else Q[s2][a2]))
                Q[s][a] += alpha * (target - Q[s][a])
                s, a = s2, a2
                if done:
                    break
            returns.append(total)
        return Q, np.array(returns)

    Qq, rq = train("q")
    Qs, rs = train("sarsa")

    f, axes = grid(2, 1, 9.2, 7.0)

    ax = axes[0]
    for i in range(H):
        for j in range(W):
            fc = C.red if (i, j) in cliff else ("#F3F4F6")
            if (i, j) == start:
                fc = C.blue
            if (i, j) == goal:
                fc = C.green
            ax.add_patch(Rectangle((j, -i), 0.94, 0.94, facecolor=fc, edgecolor="white", lw=1.8))
    ax.text(0.47, -3 + 0.47, "S", ha="center", va="center", fontsize=12, color="white",
            fontweight="bold")
    ax.text(11.47, -3 + 0.47, "G", ha="center", va="center", fontsize=12, color="white",
            fontweight="bold")
    ax.text(6, -3 + 0.47, "THE CLIFF — reward −100", ha="center", va="center",
            fontsize=10.5, color="white", fontweight="bold")

    def draw_path(Q, col, label, dashed=False):
        s = start
        pts = [(s[1] + 0.47, -s[0] + 0.47)]
        for _ in range(60):
            a = int(np.argmax(Q[s]))
            s2, _, done = step(s, a)
            if s2 == s:
                break
            s = s2
            pts.append((s[1] + 0.47, -s[0] + 0.47))
            if done:
                break
        pts = np.array(pts)
        ax.plot(pts[:, 0], pts[:, 1], color=col, lw=3.4, label=label,
                ls="--" if dashed else "-", zorder=6)

    draw_path(Qq, C.orange, "Q-learning — optimal path, hugs the cliff")
    draw_path(Qs, C.purple, "SARSA — safer path, stays clear", dashed=True)
    ax.set_xlim(-0.2, W + 0.1)
    ax.set_ylim(-H + 0.85, 1.05)
    ax.legend(fontsize=10.5, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.30))
    clean(ax)
    ax.set_aspect("equal")
    ax.set_title("Cliff walking: the greedy path and the safe path differ", fontsize=12.5)

    ax = axes[1]
    k = 50
    smooth = lambda v: np.convolve(v, np.ones(k) / k, mode="valid")
    ax.plot(smooth(rq), color=C.orange, label=f"Q-learning (off-policy), final ≈ {rq[-200:].mean():.0f}")
    ax.plot(smooth(rs), color=C.purple, label=f"SARSA (on-policy), final ≈ {rs[-200:].mean():.0f}")
    ax.set_ylim(-140, 0)
    ax.set_xlabel("episode")
    ax.set_ylabel("return per episode (smoothed)")
    ax.set_title("With ε-greedy exploration, SARSA earns more —\nit learns the value of the policy it actually follows",
                 fontsize=12)
    ax.legend(fontsize=10.5, loc="lower right")
    f.tight_layout()
    save(f, "rl/cliff-walking.png")
    return rq, rs


def exploration_strategies():
    """ε-greedy vs decaying ε vs UCB on a 10-armed bandit, averaged over runs."""
    k, steps, runs = 10, 1200, 300

    def bandit(strategy, seed_base=0):
        rewards = np.zeros(steps)
        optimal = np.zeros(steps)
        for run in range(runs):
            r = np.random.default_rng(seed_base + run)
            true_q = r.normal(0, 1, k)
            best_a = int(np.argmax(true_q))
            Q = np.zeros(k)
            N = np.zeros(k)
            for t in range(steps):
                if strategy == "greedy":
                    a = int(np.argmax(Q))
                elif strategy == "eps":
                    a = r.integers(k) if r.random() < 0.1 else int(np.argmax(Q))
                elif strategy == "decay":
                    e = 1.0 / (1 + t / 60)
                    a = r.integers(k) if r.random() < e else int(np.argmax(Q))
                else:  # ucb
                    with np.errstate(divide="ignore", invalid="ignore"):
                        bonus = np.where(N > 0, 2.0 * np.sqrt(np.log(t + 1) / np.maximum(N, 1)), 1e9)
                    a = int(np.argmax(Q + bonus))
                rew = r.normal(true_q[a], 1)
                N[a] += 1
                Q[a] += (rew - Q[a]) / N[a]
                rewards[t] += rew
                optimal[t] += a == best_a
        return rewards / runs, optimal / runs * 100

    f, axes = grid(1, 2, 11.4, 4.2)
    for name, col, lbl in [("greedy", C.red, "greedy (ε = 0) — gets stuck"),
                           ("eps", C.orange, "ε-greedy (ε = 0.1)"),
                           ("decay", C.blue, "ε decaying from 1.0"),
                           ("ucb", C.green, "UCB — optimism under uncertainty")]:
        rew, opt = bandit(name)
        sm = lambda v: np.convolve(v, np.ones(25) / 25, mode="valid")
        axes[0].plot(sm(rew), color=col, lw=2.4, label=lbl)
        axes[1].plot(sm(opt), color=col, lw=2.4, label=lbl)
    axes[0].set_xlabel("step")
    axes[0].set_ylabel("average reward")
    axes[0].set_title("10-armed bandit, averaged over 300 runs", fontsize=12.5)
    axes[0].legend(fontsize=9.5, loc="lower right")
    axes[1].set_xlabel("step")
    axes[1].set_ylabel("% of steps taking the best arm")
    axes[1].set_title("Pure greedy plateaus far below optimal", fontsize=12.5)
    axes[1].legend(fontsize=9.5, loc="lower right")
    f.tight_layout()
    save(f, "rl/exploration-strategies.png")


def ppo_clipping():
    f, axes = grid(1, 2, 11.0, 4.2)
    r = np.linspace(0, 2.2, 400)
    eps = 0.2
    for ax, A, title in [(axes[0], 1.0, "Positive advantage (A > 0)\nthe gain is capped at 1 + ε"),
                         (axes[1], -1.0, "Negative advantage (A < 0)\nthe push-down is capped at 1 − ε")]:
        unclipped = r * A
        clipped = np.clip(r, 1 - eps, 1 + eps) * A
        obj = np.minimum(unclipped, clipped)
        ax.plot(r, unclipped, color=C.light, lw=2.4, ls="--", label="unclipped  r·A")
        ax.plot(r, obj, color=C.blue, lw=3.4, label="PPO objective  min(r·A, clip(r)·A)")
        ax.axvline(1 - eps, color=C.grey, ls=":", lw=2)
        ax.axvline(1 + eps, color=C.grey, ls=":", lw=2)
        ax.axvspan(1 - eps, 1 + eps, color=C.green, alpha=0.09)
        ax.text(1.0, ax.get_ylim()[0] * 0.85 if A < 0 else 1.9, "trust region", ha="center",
                fontsize=10.5, color=C.green, fontweight="bold")
        ax.set_xlabel("probability ratio  r = π_new / π_old")
        ax.set_title(title, fontsize=12)
        ax.legend(fontsize=9.5, loc="lower right" if A > 0 else "upper right")
    axes[0].set_ylabel("objective")
    f.suptitle("PPO clipping removes the incentive to move the policy far in one update",
               fontsize=13, fontweight="bold")
    f.tight_layout(rect=(0, 0, 1, 0.9))
    save(f, "rl/ppo-clipping.png")


def rl_algorithm_map():
    f, ax = fig(9.6, 5.0)
    groups = {
        "Value-based": (1.6, 3.6, C.blue, ["Q-learning", "SARSA", "DQN", "Double DQN"]),
        "Policy-based": (5.0, 4.4, C.orange, ["REINFORCE", "PPO", "TRPO"]),
        "Actor–critic": (8.0, 3.6, C.green, ["A2C / A3C", "DDPG", "SAC", "TD3"]),
        "Model-based": (5.0, 1.2, C.purple, ["Dyna-Q", "MuZero", "World models"]),
    }
    for name, (x, y, col, members) in groups.items():
        ax.add_patch(Rectangle((x - 1.35, y - 0.95), 2.7, 1.9, facecolor=col, alpha=0.16,
                               edgecolor=col, lw=2.6))
        ax.text(x, y + 0.68, name, ha="center", fontsize=12.5, fontweight="bold", color=col)
        for i, m in enumerate(members):
            ax.text(x, y + 0.28 - i * 0.36, m, ha="center", fontsize=10.5)
    ax.annotate("", xy=(6.6, 3.9), xytext=(3.0, 3.9),
                arrowprops=dict(arrowstyle="<->", lw=2.4, color=C.grey))
    ax.text(4.8, 2.55, "actor–critic combines both:\na policy (actor) + a value estimate (critic)",
            ha="center", fontsize=10.5, color=C.grey, style="italic")
    ax.set_xlim(0, 9.8)
    ax.set_ylim(0, 5.8)
    clean(ax)
    ax.set_title("The RL algorithm landscape", fontsize=13.5)
    f.tight_layout()
    save(f, "rl/algorithm-map.png")


def rlhf_pipeline():
    f, ax = fig(11.0, 3.6)
    stages = [
        ("1. Pretrain\nnext-token on\nweb text", C.grey),
        ("2. SFT\nfine-tune on\ndemonstrations", C.blue),
        ("3. Reward model\ntrained on human\npreference pairs", C.orange),
        ("4. RL (PPO/DPO)\noptimise policy\nagainst the reward", C.green),
    ]
    for i, (label, col) in enumerate(stages):
        x = i * 2.75
        ax.add_patch(Rectangle((x, 0.5), 2.4, 1.7, facecolor=col, alpha=0.88,
                               edgecolor="white", lw=2))
        ax.text(x + 1.2, 1.35, label, ha="center", va="center", color="white", fontsize=10.5,
                fontweight="bold")
        if i < 3:
            ax.annotate("", xy=(x + 2.72, 1.35), xytext=(x + 2.42, 1.35),
                        arrowprops=dict(arrowstyle="->", lw=2.6, color=C.black))
    ax.text(5.5, 0.05, "A KL penalty against the SFT model stops step 4 drifting into reward hacking.",
            ha="center", fontsize=11, color=C.red, fontweight="bold")
    ax.set_xlim(-0.3, 11.3)
    ax.set_ylim(-0.4, 2.7)
    clean(ax)
    ax.set_title("RLHF: four stages, each with a different objective", fontsize=13)
    f.tight_layout()
    save(f, "rl/rlhf-pipeline.png")


if __name__ == "__main__":
    print("rl:")
    agent_env_loop()
    gridworld_mdp()
    discount_factor()
    rq, rs = cliff_walking()
    print(f"    cliff: Q-learning final {rq[-200:].mean():.1f}, SARSA final {rs[-200:].mean():.1f}")
    exploration_strategies()
    ppo_clipping()
    rl_algorithm_map()
    rlhf_pipeline()
