---
id: policy-gradient-methods
title: Policy Gradient Methods
sidebar_label: Policy Gradient Methods
sidebar_position: 8
tags: [reinforcement-learning, policy-gradient, reinforce]
---

# Policy Gradient Methods

Every algorithm so far learns a value function first, and derives a policy from it only indirectly (act greedily with respect to the values). Policy gradient methods skip the middleman entirely — parameterise the policy directly, and take gradients of expected return with respect to those parameters.

:::info[Key idea]
You can take gradients of expected return with respect to policy parameters without ever differentiating through the environment, using the log-derivative trick.
:::

## Why value-based methods struggle with continuous actions and stochastic optima

[Deep Q-Networks](./deep-q-networks.md)'s $\max_{a'} Q(s',a')$ requires enumerating every action to find the best one — trivial for a handful of discrete actions, intractable for continuous action spaces (an infinite set to maximise over). Value-based methods also struggle to represent a genuinely *stochastic* optimal policy directly, which some problems (games with hidden information, certain safety-critical settings) actually require.

## Parameterising a policy directly

Let $\pi_\theta(a \mid s)$ be a policy directly parameterised by $\theta$ (a neural network's weights) — for discrete actions, typically a softmax over action logits; for continuous actions, typically the parameters of a Gaussian distribution. This sidesteps value-based methods' action-enumeration problem entirely: sampling from $\pi_\theta$ works identically regardless of whether the action space is discrete or continuous.

## The objective: expected return

$$
J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta} \left[ G_0 \right]
$$

Directly [Markov Decision Processes](./markov-decision-processes.md)'s expected-return objective, now written explicitly as a function of the policy's parameters $\theta$ — the quantity policy gradient methods differentiate and ascend.

## The policy gradient theorem, derived via the log-derivative trick

The obstacle: $J(\theta)$ is an expectation over trajectories whose *probability itself* depends on $\theta$ — naively differentiating through that would require differentiating through the environment's dynamics, which is generally impossible (unknown, non-differentiable). The **log-derivative trick** sidesteps this:

$$
\nabla_\theta \mathbb{E}_{x \sim p_\theta}[f(x)] = \mathbb{E}_{x \sim p_\theta}\left[ f(x) \nabla_\theta \log p_\theta(x) \right]
$$

Applied to trajectories, and using the fact that the environment's transition probabilities don't depend on $\theta$ at all (only the policy's action probabilities do), this yields the **policy gradient theorem**:

$$
\nabla_\theta J(\theta) = \mathbb{E}_{\tau \sim \pi_\theta} \left[ \sum_t \nabla_\theta \log \pi_\theta(a_t \mid s_t) \, G_t \right]
$$

The environment's (possibly unknown, non-differentiable) dynamics have vanished from the gradient entirely — only the *policy's own* log-probability needs to be differentiated, something a neural network handles trivially.

## REINFORCE

The direct algorithm implementing this gradient: run an episode, compute the actual return $G_t$ following each action, and take a gradient step in the direction $\nabla_\theta \log \pi_\theta(a_t \mid s_t) \, G_t$ for every timestep — increasing the probability of actions that led to high return, decreasing it for actions that led to low return.

## Why the gradient estimate has enormous variance

$G_t$ is a single Monte Carlo sample of the return — exactly [Monte Carlo and TD Learning](./monte-carlo-and-td-learning.md)'s high-variance estimator, now used directly inside a gradient. A single lucky (or unlucky) episode can produce a wildly noisy gradient estimate, making raw REINFORCE slow and unstable to train in practice.

## Baselines, and the proof that subtracting a state-dependent baseline leaves the estimator unbiased

Subtracting any function $b(s_t)$ that does **not** depend on the action from $G_t$ leaves the gradient's expectation unchanged:

$$
\mathbb{E}_{a \sim \pi_\theta}\left[ \nabla_\theta \log \pi_\theta(a \mid s) \, b(s) \right] = b(s) \, \nabla_\theta \sum_a \pi_\theta(a \mid s) = b(s) \, \nabla_\theta 1 = 0
$$

Since $\sum_a \pi_\theta(a \mid s) = 1$ for any $\theta$, its gradient is exactly zero — so subtracting any state-only baseline adds zero in expectation, while (with a well-chosen baseline) substantially reducing variance in practice.

## The value function as the natural baseline

Using $V(s_t)$ (an estimate of the *average* return from that state) as the baseline turns $G_t - V(s_t)$ into an estimate of the **advantage** $A(s_t, a_t)$ from [Value Functions and Bellman Equations](./value-functions-and-bellman-equations.md) — "was this specific action better than typical for this state," a much lower-variance signal than the raw return, and the direct bridge to [Actor-Critic Methods](./actor-critic-methods.md).

## Reward-to-go instead of the full episode return

Using the *full* episode return $G_0$ for every timestep's update credits early actions with rewards that happened before they could possibly have caused them. Using **reward-to-go** — $G_t$, only the return from timestep $t$ onward — instead removes this non-causal credit assignment, reducing variance further with no change to the estimator's expectation (rewards from before time $t$ don't depend on $a_t$, so including them only adds zero-mean noise).

## Entropy regularisation for exploration

Adding a bonus term proportional to the policy's entropy $\mathcal{H}(\pi_\theta(\cdot \mid s))$ to the objective discourages the policy from collapsing to a single deterministic action too early, encouraging continued exploration during training — a soft, differentiable alternative to ε-greedy's hard random-action switching.

## Continuous action spaces via Gaussian policies

For continuous actions, parameterise $\pi_\theta(a \mid s)$ as a Gaussian $\mathcal{N}(\mu_\theta(s), \sigma_\theta(s))$, with the network outputting the mean (and optionally the standard deviation) — sampling and computing $\log \pi_\theta(a \mid s)$ both have simple closed forms for a Gaussian, making the policy gradient theorem directly applicable with no discretisation needed.

## The on-policy sample-efficiency cost

Every gradient in this page requires trajectories sampled from the *current* policy $\pi_\theta$ — once $\theta$ updates, old trajectories are (in principle) no longer valid samples of the new policy's distribution and must be discarded. This on-policy requirement is a genuine sample-efficiency cost relative to off-policy methods like [Deep Q-Networks](./deep-q-networks.md), which can reuse arbitrarily old experience via the replay buffer.

| Symbol | Meaning |
|---|---|
| $\pi_\theta(a \mid s)$ | the directly-parameterised policy |
| $J(\theta)$ | the expected-return objective |
| $b(s)$ | a state-dependent baseline |

## Code: REINFORCE with and without a baseline, variance measured directly

```python title="policy_gradient_demo.py"
import torch
import torch.nn as nn
import numpy as np
from deep_q_network_demo import TinyCartPole

class PolicyNetwork(nn.Module):
    def __init__(self, state_dim=4, action_dim=2):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(state_dim, 64), nn.ReLU(), nn.Linear(64, action_dim))
    def forward(self, x):
        return torch.softmax(self.net(x), dim=-1)

class ValueNetwork(nn.Module):
    def __init__(self, state_dim=4):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(state_dim, 64), nn.ReLU(), nn.Linear(64, 1))
    def forward(self, x):
        return self.net(x).squeeze(-1)

def run_episode(env, policy):
    states, actions, rewards = [], [], []
    state = env.reset()
    for _ in range(200):
        probs = policy(torch.tensor(state, dtype=torch.float32))
        action = torch.multinomial(probs, 1).item()
        next_state, reward, done = env.step(action)
        states.append(state); actions.append(action); rewards.append(reward)
        state = next_state
        if done:
            break
    return states, actions, rewards

def reward_to_go(rewards, gamma=0.99):
    result, running = [0.0] * len(rewards), 0.0
    for t in reversed(range(len(rewards))):
        running = rewards[t] + gamma * running
        result[t] = running
    return result

def train_reinforce(use_baseline, n_episodes=300):
    env = TinyCartPole()
    policy = PolicyNetwork()
    value_net = ValueNetwork() if use_baseline else None
    policy_opt = torch.optim.Adam(policy.parameters(), lr=0.01)
    value_opt = torch.optim.Adam(value_net.parameters(), lr=0.01) if use_baseline else None
    returns_log, grad_variance_log = [], []

    for episode in range(n_episodes):
        states, actions, rewards = run_episode(env, policy)
        returns = torch.tensor(reward_to_go(rewards), dtype=torch.float32)
        states_t = torch.tensor(np.array(states), dtype=torch.float32)
        actions_t = torch.tensor(actions)

        if use_baseline:
            values = value_net(states_t)
            advantages = returns - values.detach()
            value_loss = nn.functional.mse_loss(values, returns)
            value_opt.zero_grad(); value_loss.backward(); value_opt.step()
        else:
            advantages = returns

        log_probs = torch.log(policy(states_t).gather(1, actions_t.unsqueeze(1)).squeeze(1))
        per_step_terms = -log_probs * advantages
        policy_loss = per_step_terms.mean()
        policy_opt.zero_grad(); policy_loss.backward(); policy_opt.step()

        returns_log.append(sum(rewards))
        grad_variance_log.append(per_step_terms.detach().var().item())

    return returns_log, grad_variance_log

returns_no_baseline, var_no_baseline = train_reinforce(use_baseline=False)
returns_baseline, var_baseline = train_reinforce(use_baseline=True)

print(f"no baseline: mean last-20 return = {np.mean(returns_no_baseline[-20:]):.1f}, "
      f"mean gradient-term variance = {np.mean(var_no_baseline[-20:]):.2f}")
print(f"with baseline: mean last-20 return = {np.mean(returns_baseline[-20:]):.1f}, "
      f"mean gradient-term variance = {np.mean(var_baseline[-20:]):.2f}  (should be lower)")
```

## See also

- [Actor-Critic Methods](./actor-critic-methods.md) — replacing the Monte Carlo return with a learned, lower-variance critic.
- [Deep Q-Networks](./deep-q-networks.md) — the value-based alternative this page's on-policy sample cost trades against.
