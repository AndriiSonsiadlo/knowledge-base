---
id: deep-q-networks
title: Deep Q-Networks
sidebar_label: Deep Q-Networks
sidebar_position: 7
tags: [reinforcement-learning, dqn, deep-rl]
---

# Deep Q-Networks

[Q-Learning and SARSA](./q-learning-and-sarsa.md) hit a hard ceiling: a table indexed by state doesn't scale past small, discrete state spaces. Swap the table for a neural network and the state-space problem disappears — but a new one appears immediately, because naive function approximation in RL is unstable in ways tabular methods never are.

:::info[Key idea]
Naive function approximation in RL diverges - DQN works because of two stabilisers, the replay buffer and the target network, not because of the network itself.
:::

## Why tabular Q-learning cannot scale

A Q-table requires one entry per state-action pair, and stores nothing shared between similar states — an image-based state space has no usable tabular representation at all. A function approximator, in contrast, can *generalise*: learning about one state informs the value estimate for similar, even never-visited, states.

## Q-function approximation

Replace the table $Q(s, a)$ with a parameterised function $Q_\theta(s, a)$ (a neural network), trained to minimise the same TD error from [Q-Learning and SARSA](./q-learning-and-sarsa.md) via gradient descent, instead of updating a table entry directly.

## The deadly triad, and why it destabilises training

Three ingredients, each individually reasonable, combine to make training provably unstable: **function approximation** (values for different states are no longer independent — updating one changes others), **bootstrapping** (the update target itself depends on the same changing estimates), and **off-policy learning** (Q-learning's max-based target, learning about a policy different from the one generating data). Any two of the three are usually manageable; all three together (exactly DQN's situation) is the **deadly triad**, and it is a documented source of divergence, not just slow convergence.

## Experience replay: breaking correlation between consecutive samples

Standard supervised training assumes independent, identically-distributed samples — but consecutive states visited by an agent are highly correlated (each state is reached from the previous one). **Experience replay** stores past transitions $(s, a, r, s')$ in a buffer and trains on randomly-sampled minibatches from it, rather than on the most recent transition directly — breaking the correlation and letting each transition be reused multiple times, improving sample efficiency as a side benefit.

## The target network: freezing the bootstrap target

Using the same, constantly-updating network for both the current estimate $Q_\theta(s,a)$ and the bootstrap target $\max_{a'} Q_\theta(s',a')$ means the target moves every single gradient step — chasing a moving target destabilises training directly. DQN keeps a separate **target network** $Q_{\theta^-}$, a periodically-synced (frozen-in-between) copy of the main network, used only to compute the bootstrap target — holding the target still for many updates at a time.

## The DQN loss

$$
L(\theta) = \mathbb{E}_{(s,a,r,s') \sim \text{replay}} \left[ \left( r + \gamma \max_{a'} Q_{\theta^-}(s', a') - Q_\theta(s, a) \right)^2 \right]
$$

Exactly the squared TD error from [Q-Learning and SARSA](./q-learning-and-sarsa.md), but averaged over a random replay-buffer minibatch, with the target computed by the frozen target network $\theta^-$ rather than the live network $\theta$.

## The full algorithm

1. Take an ε-greedy action, observe the transition, store it in the replay buffer.
2. Sample a random minibatch of past transitions from the buffer.
3. Compute the DQN loss using the target network, take a gradient step on $\theta$.
4. Periodically copy $\theta \to \theta^-$ to update the target network.

## Preprocessing and frame stacking for pixel inputs

For pixel-based environments, standard preprocessing includes grayscaling, resizing, and — because a single frame reveals no velocity information — stacking several consecutive frames as the network's input, which is exactly [Markov Decision Processes](./markov-decision-processes.md)'s frame-stacking workaround for partial observability, applied concretely.

## Double DQN and maximisation bias

[Q-Learning and SARSA](./q-learning-and-sarsa.md)'s maximisation-bias problem carries over directly to DQN. **Double DQN** applies the same fix using the two networks already available: use the *live* network $\theta$ to select the best action, but the *target* network $\theta^-$ to evaluate it — $r + \gamma Q_{\theta^-}(s', \arg\max_{a'} Q_\theta(s', a'))$ — decoupling selection from evaluation without needing a genuinely separate second network.

## Duelling architectures

Split the network's final layers into two streams — a state-value stream $V(s)$ and an advantage stream $A(s,a)$ — recombined as $Q(s,a) = V(s) + (A(s,a) - \text{mean}_a A(s,a))$. Useful specifically when many actions have similar values in a given state (the network can learn "this state is good" once, in $V$, without separately re-learning it for every action in $A$).

## Prioritised replay

Rather than sampling uniformly from the replay buffer, sample transitions with probability proportional to their TD error magnitude — prioritising transitions the network is currently getting most wrong, learning more from surprising experience and less from already-well-predicted transitions.

## Rainbow as the combination

**Rainbow DQN** combines Double DQN, duelling architectures, prioritised replay, and several further improvements (multi-step returns, distributional RL, noisy exploration) into a single agent — an empirical demonstration that these individually-motivated fixes are largely complementary rather than redundant.

## Sample efficiency as deep RL's defining weakness

Even with all these stabilisers, DQN-family algorithms typically require millions of environment steps to reach strong performance on non-trivial tasks — a stark contrast to supervised learning's typically much better data efficiency, and a direct consequence of learning purely from trial-and-error feedback rather than labelled examples.

## What a healthy DQN training curve looks like, and what the broken ones look like

**Healthy**: episode return rises steadily (with noise) and plateaus near the environment's achievable maximum; the loss may not monotonically decrease (it's chasing a periodically-updated target) but stays bounded. **Broken — no replay buffer**: high correlation between consecutive updates causes the loss to spike and the policy to oscillate or collapse. **Broken — no target network**: the bootstrap target chases the live network, often causing runaway value overestimation and diverging Q-values, visible directly in the code below.

| Symbol | Meaning |
|---|---|
| $\theta, \theta^-$ | the live network's parameters and the frozen target network's parameters |
| replay buffer | the stored pool of past transitions sampled for training |

## Code: DQN on CartPole, with the replay buffer and target network each removed to show failure

```python title="deep_q_network_demo.py"
import torch
import torch.nn as nn
import numpy as np
import random
from collections import deque

class QNetwork(nn.Module):
    def __init__(self, state_dim=4, action_dim=2):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(state_dim, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, action_dim))
    def forward(self, x):
        return self.net(x)

class TinyCartPole:
    """A minimal CartPole-style dynamics stand-in, avoiding a gymnasium dependency."""
    def reset(self):
        self.state = np.random.default_rng().uniform(-0.05, 0.05, 4)
        self.steps = 0
        return self.state
    def step(self, action):
        x, x_dot, theta, theta_dot = self.state
        force = 10.0 if action == 1 else -10.0
        theta_dot += 0.02 * (force + 10 * np.sin(theta))
        theta += 0.02 * theta_dot
        x_dot += 0.02 * force * 0.1
        x += 0.02 * x_dot
        self.state = np.array([x, x_dot, theta, theta_dot])
        self.steps += 1
        done = abs(theta) > 0.5 or abs(x) > 2.0 or self.steps >= 200
        return self.state, 1.0, done

def train_dqn(use_replay=True, use_target_network=True, n_episodes=150):
    env = TinyCartPole()
    q_net = QNetwork()
    target_net = QNetwork()
    target_net.load_state_dict(q_net.state_dict())
    optimizer = torch.optim.Adam(q_net.parameters(), lr=0.001)
    buffer = deque(maxlen=5000)
    rng = np.random.default_rng(0)
    episode_returns, q_value_log = [], []

    for episode in range(n_episodes):
        state = env.reset()
        epsilon = max(0.05, 1.0 - episode / 100)
        total_reward = 0.0
        for step in range(200):
            if rng.random() < epsilon:
                action = rng.integers(2)
            else:
                with torch.no_grad():
                    action = q_net(torch.tensor(state, dtype=torch.float32)).argmax().item()
            next_state, reward, done = env.step(action)
            buffer.append((state, action, reward, next_state, done))
            state = next_state
            total_reward += reward

            batch = random.sample(buffer, min(32, len(buffer))) if use_replay else [buffer[-1]]
            states, actions, rewards, next_states, dones = zip(*batch)
            states = torch.tensor(np.array(states), dtype=torch.float32)
            actions = torch.tensor(actions)
            rewards = torch.tensor(rewards, dtype=torch.float32)
            next_states = torch.tensor(np.array(next_states), dtype=torch.float32)
            dones = torch.tensor(dones, dtype=torch.float32)

            target_source = target_net if use_target_network else q_net
            with torch.no_grad():
                target_q = rewards + 0.99 * target_source(next_states).max(1).values * (1 - dones)
            current_q = q_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)
            loss = nn.functional.mse_loss(current_q, target_q)
            optimizer.zero_grad(); loss.backward(); optimizer.step()

            if done:
                break
        if use_target_network and episode % 10 == 0:
            target_net.load_state_dict(q_net.state_dict())
        episode_returns.append(total_reward)
        with torch.no_grad():
            q_value_log.append(q_net(torch.tensor(state, dtype=torch.float32)).max().item())

    return episode_returns, q_value_log

full_returns, full_q = train_dqn(use_replay=True, use_target_network=True)
no_replay_returns, no_replay_q = train_dqn(use_replay=False, use_target_network=True)
no_target_returns, no_target_q = train_dqn(use_replay=True, use_target_network=False)

print(f"full DQN:        mean last-20 return = {np.mean(full_returns[-20:]):.1f}")
print(f"no replay buffer: mean last-20 return = {np.mean(no_replay_returns[-20:]):.1f}  (correlated updates destabilise)")
print(f"no target network: max |Q| reached    = {max(abs(q) for q in no_target_q):.1f}  (values often diverge without freezing the target)")
```

## See also

- [Q-Learning and SARSA](./q-learning-and-sarsa.md) — the tabular algorithm DQN generalises via function approximation.
- [Policy Gradient Methods](./policy-gradient-methods.md) — the alternative family that optimises the policy directly instead of a value function.
