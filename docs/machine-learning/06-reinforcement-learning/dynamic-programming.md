---
id: dynamic-programming
title: Dynamic Programming
sidebar_label: Dynamic Programming
sidebar_position: 4
tags: [reinforcement-learning, dynamic-programming, planning]
---

# Dynamic Programming

If you already know exactly how the environment works — every transition probability, every reward — you don't need to act, explore, or learn from experience at all. You can compute the optimal policy directly, by repeatedly applying the Bellman equations from [Value Functions and Bellman Equations](./value-functions-and-bellman-equations.md) until they converge.

:::info[Key idea]
With a known model you never need to act at all - you can compute the optimal policy by repeatedly applying the Bellman equations.
:::

## The assumption: full knowledge of P and R

Every method on this page assumes the transition function $P$ and reward function $R$ are fully known in advance — a strong assumption that real environments rarely satisfy, but one that makes dynamic programming (DP) the exact, correctness-baseline case every later, model-free method ([Monte Carlo and TD Learning](./monte-carlo-and-td-learning.md) onward) approximates without that assumption.

## Iterative policy evaluation

Starting from an arbitrary $V_0$, repeatedly apply the Bellman expectation equation as an update rule:

$$
V_{k+1}(s) \leftarrow \sum_a \pi(a \mid s) \sum_{s'} P(s' \mid s, a) \left[ R(s,a,s') + \gamma V_k(s') \right]
$$

Each sweep over all states pushes $V_k$ closer to the true $V^\pi$; repeated indefinitely (or until the change per sweep is negligible), it converges — the direct iterative analogue of the linear-system solve from the previous page.

## Policy improvement, and the policy improvement theorem

Given $V^\pi$, construct a new policy $\pi'$ by acting greedily with respect to it: $\pi'(s) = \arg\max_a Q^\pi(s, a)$. The **policy improvement theorem** guarantees $\pi'$ is at least as good as $\pi$ everywhere — $V^{\pi'}(s) \geq V^\pi(s)$ for every state — and strictly better somewhere unless $\pi$ was already optimal. This is the theoretical guarantee that makes "evaluate, then greedily improve" a sound strategy at all, rather than just a plausible heuristic.

## Policy iteration, and why it terminates

**Policy iteration** alternates full policy evaluation (run to convergence) with a full greedy policy improvement step, repeating until the policy stops changing. Because there are only finitely many deterministic policies for a finite MDP, and the policy improvement theorem guarantees each iteration either strictly improves or has already reached the optimum, the process is guaranteed to terminate in a finite number of iterations, at the optimal policy.

## Value iteration as a truncated variant

**Value iteration** collapses evaluation and improvement into a single update, applying the Bellman *optimality* equation directly instead of running evaluation to convergence first:

$$
V_{k+1}(s) \leftarrow \max_a \sum_{s'} P(s' \mid s, a) \left[ R(s,a,s') + \gamma V_k(s') \right]
$$

Equivalent to policy iteration with policy evaluation truncated to a single sweep — cheaper per full "iteration," at the cost of more total sweeps needed for convergence.

## The connection between them

Both are instances of [Value Functions and Bellman Equations](./value-functions-and-bellman-equations.md)'s **generalised policy iteration** — the only real difference is *how much* evaluation happens between improvement steps: policy iteration runs evaluation all the way to convergence; value iteration runs exactly one step. Every point in between (partial evaluation, then improve) is also a valid, convergent variant.

## Asynchronous and in-place variants

Standard ("synchronous") sweeps update every state using the *previous* sweep's values throughout. **In-place** updates instead use newly-updated values immediately within the same sweep — often converges faster in practice, with the same convergence guarantee. **Asynchronous** DP goes further: update states in any order, even skipping some indefinitely, as long as every state keeps getting updated infinitely often eventually — useful when some states matter more than others and deserve more frequent updates.

## Convergence guarantees and the contraction-mapping argument

Both policy evaluation and value iteration's updates are **contraction mappings** under the Bellman operator, with contraction factor $\gamma < 1$ — meaning each application strictly shrinks the maximum distance between the current estimate and the true value function by at least a factor of $\gamma$. This is the mathematical fact that guarantees convergence to a *unique* fixed point, regardless of the (finite) starting values.

## Computational cost, and why this does not scale

Each sweep costs $O(|\mathcal{S}|^2 |\mathcal{A}|)$ in the worst case (every state, every action, every possible next state) — and this is *before* accounting for needing a known, tabular model of $P$ and $R$ in the first place. For any real-world state space (images, continuous sensors, large combinatorial spaces), both the memory to store a full transition model and the computation to sweep it are completely infeasible — the direct motivation for every model-free method that follows.

## Why DP still matters

Despite being impractical at scale, DP is the **correctness baseline** the entire rest of this section is measured against: every model-free algorithm ([Monte Carlo and TD Learning](./monte-carlo-and-td-learning.md), [Q-Learning and SARSA](./q-learning-and-sarsa.md)) is trying to approximate what DP would compute exactly, given a known model, using only sampled experience instead. Understanding DP's exact answer on a small problem (this section's grid world) is what makes it possible to verify whether a model-free method is learning something correct.

## Generalised policy iteration, restated

Every algorithm in the rest of this section — tabular or deep, on-policy or off — can be understood as some particular trade-off within the same evaluate/improve loop introduced here: how much evaluation happens per improvement step, how it's estimated (exactly, from full sweeps, vs. approximately, from sampled experience), and how greedy the improvement step is.

| Symbol | Meaning |
|---|---|
| $V_k$ | the value-function estimate after $k$ sweeps |
| $\pi'$ | the greedily-improved policy |
| $\gamma$ | the discount factor, also the Bellman operator's contraction factor |

## Code: policy iteration and value iteration on the grid world, compared

```python title="dynamic_programming_demo.py"
import numpy as np
import time
from mdp_demo import P, R, n_states, n_actions

gamma = 0.95

def policy_evaluation(policy, theta=1e-6):
    V = np.zeros(n_states)
    while True:
        R_pi = np.sum(policy * R, axis=1)
        P_pi = np.einsum("sa,sat->st", policy, P)
        V_new = R_pi + gamma * P_pi @ V
        if np.abs(V_new - V).max() < theta:
            return V_new
        V = V_new

def policy_iteration():
    policy = np.ones((n_states, n_actions)) / n_actions
    for iteration in range(100):
        V = policy_evaluation(policy)
        Q = R + gamma * np.einsum("sat,t->sa", P, V)
        new_policy = np.zeros_like(policy)
        new_policy[np.arange(n_states), np.argmax(Q, axis=1)] = 1.0
        if np.array_equal(new_policy, policy):
            return new_policy, V, iteration + 1
        policy = new_policy
    return policy, V, 100

def value_iteration(theta=1e-6):
    V = np.zeros(n_states)
    for iteration in range(1000):
        Q = R + gamma * np.einsum("sat,t->sa", P, V)
        V_new = np.max(Q, axis=1)
        if np.abs(V_new - V).max() < theta:
            policy = np.zeros((n_states, n_actions))
            policy[np.arange(n_states), np.argmax(Q, axis=1)] = 1.0
            return policy, V_new, iteration + 1
        V = V_new

start = time.perf_counter()
pi_policy, pi_V, pi_iters = policy_iteration()
pi_time = time.perf_counter() - start

start = time.perf_counter()
vi_policy, vi_V, vi_iters = value_iteration()
vi_time = time.perf_counter() - start

print(f"policy iteration: {pi_iters} iterations, {pi_time*1000:.2f}ms")
print(f"value iteration:  {vi_iters} iterations, {vi_time*1000:.2f}ms")
print("both converge to the same V:", np.allclose(pi_V, vi_V, atol=1e-3))
print("both converge to the same policy:", np.array_equal(pi_policy, vi_policy))
```

## See also

- [Monte Carlo and TD Learning](./monte-carlo-and-td-learning.md) — the model-free approximation of this exact recursion.
- [Value Functions and Bellman Equations](./value-functions-and-bellman-equations.md) — the equations these algorithms iterate.
