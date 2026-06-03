---
id: rlhf-and-preference-optimization
title: RLHF and Preference Optimization
sidebar_label: RLHF & Preference Optimization
sidebar_position: 12
tags: [reinforcement-learning, rlhf, dpo, alignment]
---

# RLHF and Preference Optimization

Everything in this section so far assumed a reward function already exists. For "write a helpful, harmless response" — the actual goal behind training a modern chat model — no programmable reward function exists at all. RLHF is the answer: learn a reward function from human comparisons, then optimise against it. This is also, for most readers, where reinforcement learning actually shows up in practice.

:::info[Key idea]
When you cannot write down a reward function, learn one from human comparisons, then optimise against it - carefully, because the learned reward can be gamed.
:::

## The problem: "be helpful" has no programmable reward

Unlike this section's grid world or CartPole, there's no simple scalar function of a language model's output that captures "helpful and harmless" — the goal is inherently subjective, contextual, and resistant to hand-coding, exactly the kind of goal [RL Problem Setup](./rl-problem-setup.md) flagged the reward hypothesis as struggling with.

## The three-stage pipeline (SFT, reward model, RL)

**Stage 1 — SFT** (Supervised Fine-Tuning): fine-tune a pretrained language model on high-quality human-written examples of desired behaviour, exactly [Fine-tuning and Instruction Tuning](../03-sequence-and-nlp/finetuning-and-instruction-tuning.md)'s standard supervised recipe. **Stage 2 — reward model**: train a separate model to predict which of two responses a human would prefer. **Stage 3 — RL**: use that learned reward model as the reward signal to further optimise the SFT model via [PPO and Trust Regions](./ppo-and-trust-regions.md).

## Collecting preference data, and why pairwise comparison beats absolute rating

Asking a human to rate a response "7 out of 10" is unreliable — different raters use the scale differently, and the same rater is inconsistent across sessions. Asking "which of these two responses is better" is a far more reliable signal humans can give consistently — comparative judgments are simply easier and more reliable for people to make than absolute ones, which is why essentially all RLHF pipelines collect *pairwise* preferences rather than absolute scores.

## The reward model and the Bradley-Terry objective

$$
P(y_1 \succ y_2 \mid x) = \frac{\exp(r_\phi(x, y_1))}{\exp(r_\phi(x, y_1)) + \exp(r_\phi(x, y_2))}
$$

The **Bradley-Terry model** converts pairwise preference probabilities into a single scalar reward $r_\phi$ per response — the reward model is trained to make its scalar outputs consistent with the observed human preference, via a standard classification-style loss (maximum likelihood on the observed comparisons) on top of this formula.

## The RL stage with PPO, treating the language model as the policy

The language model itself becomes the **policy** $\pi_\theta$ — each generated token is an "action," the full generated response is a "trajectory," and the reward model's scalar output for the completed response is the (delayed, terminal-only) reward. [PPO and Trust Regions](./ppo-and-trust-regions.md)'s clipped objective and trust-region machinery apply here essentially unchanged from the CartPole setting, just at a vastly larger scale.

## The KL penalty against the reference model, and what happens without it

$$
r_{\text{total}} = r_\phi(x, y) - \beta \, D_{KL}\big(\pi_\theta(\cdot \mid x) \,\|\, \pi_{\text{ref}}(\cdot \mid x)\big)
$$

A penalty term is added, discouraging the policy from drifting too far (in KL divergence) from a fixed **reference model** (typically the SFT checkpoint) — directly analogous to [PPO and Trust Regions](./ppo-and-trust-regions.md)'s trust-region idea, but applied against a fixed anchor rather than just the previous iteration. Without this penalty, the policy can drift arbitrarily far while still increasing the learned reward model's score — exactly the reward-hacking risk described next, with nothing anchoring it to remain a coherent language model at all.

## Reward hacking and over-optimisation, with the characteristic symptoms

Because $r_\phi$ is only a learned *approximation* of true human preference, optimising it too hard eventually exploits its imperfections rather than genuinely improving quality — the characteristic symptom is a policy that keeps scoring higher on the *reward model* while a human rater would judge its actual outputs as getting worse (repetitive, sycophantic, evasive, or exploiting quirks specific to the reward model's training distribution). This is [RL Problem Setup](./rl-problem-setup.md)'s reward hacking, playing out at the scale of a full language model.

## DPO: skipping the reward model by reparameterising the objective

**Direct Preference Optimization (DPO)** observes that, under the Bradley-Terry model, the optimal policy for the full KL-regularised RLHF objective has a closed-form relationship to the reward function — which means the reward model can be substituted out algebraically, leaving an objective expressed directly in terms of the policy's own log-probabilities on preferred vs. dispreferred responses. No separate reward model, no RL loop (no PPO, no rollouts, no reward hacking against a proxy model) — just a supervised-learning-style loss on preference pairs.

## The DPO objective explained

$$
\mathcal{L}_{\text{DPO}} = -\log \sigma\left( \beta \log \frac{\pi_\theta(y_w \mid x)}{\pi_{\text{ref}}(y_w \mid x)} - \beta \log \frac{\pi_\theta(y_l \mid x)}{\pi_{\text{ref}}(y_l \mid x)} \right)
$$

where $y_w$ is the preferred ("winning") response and $y_l$ the dispreferred ("losing") one. This is directly a supervised classification-style loss — simpler to implement, more stable to train (no RL instability, no separate reward model to overfit against), and has become the standard first choice for preference-based fine-tuning specifically because of that simplicity.

## RLAIF and constitutional approaches, briefly

**RLAIF** (RL from AI Feedback) replaces human preference labels with another (typically larger or more capable) model's judgments — trading label cost for a dependency on the judge model's own reliability. **Constitutional AI** approaches use an explicit written set of principles, with a model critiquing and revising its own outputs against those principles, reducing (but not eliminating) the need for large-scale human preference labelling.

## What alignment training does and does not fix

RLHF/DPO-style training shapes a model's *surface behaviour* toward what raters preferred — it does not guarantee the model has internalised the underlying values in any deeper sense, nor does it fix factual errors, reasoning failures, or capability gaps the base model already had. It is best understood as steering an existing capability distribution toward preferred outputs, not as installing new capabilities or genuine understanding.

## Evaluating an aligned model

Standard held-out accuracy metrics don't capture "helpfulness" or "harmlessness" directly — evaluation typically combines human (or AI-judge) pairwise preference comparisons against a reference model, red-teaming for adversarial failure modes, and benchmark suites targeting specific known failure categories (refusals, sycophancy, factuality) — inheriting much of the same fundamental difficulty [Evaluating Generative Models](../05-generative-models/evaluating-generative-models.md) described for generation quality generally: there is no single ground-truth answer key.

| Symbol | Meaning |
|---|---|
| $r_\phi(x, y)$ | the learned reward model's score |
| $\pi_\theta, \pi_{\text{ref}}$ | the policy being trained and the fixed reference (SFT) model |
| $\beta$ | the KL-penalty (or DPO temperature) coefficient |

## Code: a reward model on synthetic preferences, then DPO on a tiny policy

```python title="rlhf_dpo_demo.py"
import torch
import torch.nn as nn
import numpy as np

vocab_size, seq_len, hidden_dim = 20, 6, 32
rng = np.random.default_rng(0)

class TinyLM(nn.Module):
    """A minimal token-scoring model standing in for a language model's log-probabilities."""
    def __init__(self):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, hidden_dim)
        self.net = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, vocab_size))
    def token_logprobs(self, sequence):
        h = self.embed(sequence[:-1]).mean(dim=0, keepdim=True).expand(len(sequence) - 1, -1)
        logits = self.net(h)
        log_probs = torch.log_softmax(logits, dim=-1)
        return log_probs.gather(1, sequence[1:].unsqueeze(1)).sum()  # sum log-prob of the sequence

class RewardModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, hidden_dim)
        self.net = nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, 1))
    def forward(self, sequence):
        h = self.embed(sequence).mean(dim=0)
        return self.net(h).squeeze(-1)

def synthetic_pair():
    """Preference ground truth: sequences with a higher token sum are 'preferred' (a synthetic proxy)."""
    seq_a = torch.randint(0, vocab_size, (seq_len,))
    seq_b = torch.randint(0, vocab_size, (seq_len,))
    return (seq_a, seq_b) if seq_a.sum() > seq_b.sum() else (seq_b, seq_a)  # (preferred, dispreferred)

# --- Stage 2: train the reward model on pairwise preferences via the Bradley-Terry loss ---
reward_model = RewardModel()
reward_opt = torch.optim.Adam(reward_model.parameters(), lr=0.005)
for step in range(500):
    y_w, y_l = synthetic_pair()
    r_w, r_l = reward_model(y_w), reward_model(y_l)
    loss = -torch.log(torch.sigmoid(r_w - r_l) + 1e-8)  # Bradley-Terry pairwise loss
    reward_opt.zero_grad(); loss.backward(); reward_opt.step()

# --- Stage 3 (DPO variant): skip the reward model, optimise the policy directly on preferences ---
policy = TinyLM()
ref_model = TinyLM()
ref_model.load_state_dict(policy.state_dict())
for p in ref_model.parameters():
    p.requires_grad = False
policy_opt = torch.optim.Adam(policy.parameters(), lr=0.005)
beta = 0.1
kl_log = []

for step in range(300):
    y_w, y_l = synthetic_pair()
    logp_w, logp_l = policy.token_logprobs(y_w), policy.token_logprobs(y_l)
    with torch.no_grad():
        ref_logp_w, ref_logp_l = ref_model.token_logprobs(y_w), ref_model.token_logprobs(y_l)

    dpo_loss = -torch.log(torch.sigmoid(
        beta * (logp_w - ref_logp_w) - beta * (logp_l - ref_logp_l)
    ) + 1e-8)
    policy_opt.zero_grad(); dpo_loss.backward(); policy_opt.step()

    with torch.no_grad():
        kl_estimate = (logp_w - ref_logp_w).item()  # tracked to make the regularisation visible
        kl_log.append(kl_estimate)

print(f"final DPO loss: {dpo_loss.item():.3f}")
print(f"policy log-prob drift from reference (last 10 steps): {np.mean(kl_log[-10:]):.3f}")
```

## See also

- [PPO and Trust Regions](./ppo-and-trust-regions.md) — the RL algorithm the classic RLHF pipeline's third stage runs.
- [Fine-tuning and Instruction Tuning](../03-sequence-and-nlp/finetuning-and-instruction-tuning.md) — the SFT stage this pipeline builds on.
