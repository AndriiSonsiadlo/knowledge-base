---
id: local-methods
title: Local Methods — SHAP, LIME and Counterfactuals
sidebar_label: Local Methods
sidebar_position: 3
tags: [interpretability, shap, lime, counterfactuals]
---

# Local Methods — SHAP, LIME and Counterfactuals

Local methods explain a single prediction: not "what does this model rely on" but "why did *this* row come out the way it did". That is the question a declined applicant, a flagged transaction, or a debugging session actually asks.

:::info[Key idea]
SHAP distributes a prediction's deviation from the average across its features, with guarantees that the parts sum exactly to the whole. LIME fits a simple model in a small neighbourhood around one point. Counterfactuals skip attribution entirely and answer "what would have to change?" — usually the most actionable form.
:::

## SHAP

SHAP borrows the **Shapley value** from cooperative game theory: the features are players, the prediction is the payout, and each feature's attribution is its average marginal contribution across all possible orderings of the players.

That construction gives three properties no other attribution method has together:

| Property | Meaning |
|---|---|
| **Local accuracy** | Attributions sum exactly to prediction − baseline |
| **Missingness** | A feature absent from the model gets zero |
| **Consistency** | If a model changes so a feature contributes more, its SHAP value cannot decrease |

Consistency is the one that matters in practice, and it is exactly what impurity-based tree importance lacks — which is why SHAP replaced it for serious work.

$$
\phi_j = \sum_{S \subseteq F \setminus \{j\}} \frac{|S|!\,(|F| - |S| - 1)!}{|F|!}\left[f(S \cup \{j\}) - f(S)\right]
$$

That sum runs over every subset of features, so it is exponential — $2^{|F|}$ terms. Practical SHAP is entirely about approximating it:

| Variant | For | Cost |
|---|---|---|
| **TreeSHAP** | Tree ensembles | Polynomial — **exact** and fast |
| KernelSHAP | Any model | Slow; a weighted linear regression on sampled coalitions |
| DeepSHAP | Neural networks | Moderate; backprop-based approximation |
| LinearSHAP | Linear models | Trivial — it is just $\beta_j(x_j - \bar{x}_j)$ |

If you are explaining gradient boosting, TreeSHAP is exact and fast, which is a large part of why SHAP became the default in tabular ML.

### The baseline is a modelling choice

Every SHAP value is relative to a baseline — the expected prediction over some background dataset. Change the background and every attribution changes. Explaining a loan decision against "all applicants" answers a different question from explaining it against "all *approved* applicants". Neither is wrong; you must say which you used.

## LIME

LIME (Local Interpretable Model-agnostic Explanations) works by:

1. Perturbing the instance to generate a cloud of nearby synthetic points.
2. Getting the black box's predictions for them.
3. Weighting each by proximity to the original point.
4. Fitting a sparse linear model to that weighted sample.

The linear model's coefficients are the explanation. It is model-agnostic, intuitive, and works on text and images by perturbing words or superpixels rather than numeric features.

:::warning[LIME is unstable — run it twice]
Because the perturbations are random, LIME can give materially different explanations for the same instance on two consecutive runs. Reported feature rankings have been shown to flip entirely with a different random seed.

It is also sensitive to the kernel width defining "nearby", which has no principled default. Always run LIME several times with different seeds; if the explanation is not stable across runs, it is not an explanation.
:::

## SHAP or LIME

| | SHAP | LIME |
|---|---|---|
| Theoretical basis | Shapley values, with guarantees | Local surrogate, heuristic |
| Stability | Deterministic (TreeSHAP) | Varies run to run |
| Sums to the prediction | Yes | No |
| Speed on trees | Fast (TreeSHAP) | Slow — many model calls |
| Speed on arbitrary models | Slow (KernelSHAP) | Slow |
| Images and text | Workable | Often more natural |

For tabular models, especially tree ensembles, SHAP is the better default on every axis that matters. LIME retains an edge in intuitiveness and on unstructured data where superpixel or token perturbation is natural.

## Counterfactual explanations

A counterfactual answers a different and usually more useful question: **what is the smallest change that would flip the decision?**

> "Your loan was declined. Had your annual income been £4,000 higher, it would have been approved."

Compare that to a SHAP plot. The counterfactual is directly actionable, needs no statistical literacy, and maps naturally onto the legal requirement to give specific reasons for an adverse decision.

Good counterfactuals must be:

- **Valid** — actually flip the prediction
- **Minimal** — change as little as possible
- **Actionable** — never demand a change to age, race, or the past
- **Plausible** — respect feature correlations; "reduce your age by 10 years" and "double your income while halving your job tenure" are both useless

That last constraint is what makes counterfactual generation hard: naive optimisation happily produces off-manifold points that are minimal and completely impossible.

## Code: exact SHAP by enumeration, and a simple counterfactual search

```python title="local_methods.py"
import itertools

import numpy as np


def exact_shap(predict, x, background, feature_subsets=None):
    """Exact Shapley values by enumerating every coalition.

    Exponential in the number of features — fine for a demonstration with
    <= 10 features, hopeless beyond that. Real use calls TreeSHAP or KernelSHAP.
    """
    n = len(x)
    baseline = background.mean(axis=0)

    def value(subset):
        """Prediction with `subset` taken from x and the rest from the baseline."""
        row = baseline.copy()
        for j in subset:
            row[j] = x[j]
        return predict(row.reshape(1, -1))[0]

    phi = np.zeros(n)
    others = list(range(n))
    for j in range(n):
        rest = [k for k in others if k != j]
        for size in range(len(rest) + 1):
            weight = (np.math.factorial(size) *
                      np.math.factorial(n - size - 1) /
                      np.math.factorial(n))
            for S in itertools.combinations(rest, size):
                phi[j] += weight * (value(list(S) + [j]) - value(list(S)))
    return phi, value([]), value(others)


def counterfactual(predict, x, target, mutable, bounds, steps=4000, lr=0.05, seed=0):
    """Smallest change to `x` (in the mutable features) that reaches `target`.

    Immutable features — age, any protected attribute — are simply never
    touched, which is the only reliable way to keep a counterfactual actionable.
    """
    rng = np.random.default_rng(seed)
    cf = x.copy()
    for _ in range(steps):
        pred = predict(cf.reshape(1, -1))[0]
        if (target > 0 and pred >= target) or (target < 0 and pred <= target):
            break
        for j in mutable:
            probe = cf.copy()
            eps = 1e-3
            probe[j] += eps
            grad = (predict(probe.reshape(1, -1))[0] - pred) / eps
            direction = np.sign(target - pred)
            cf[j] = np.clip(cf[j] + lr * direction * grad, *bounds[j])
    return cf


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    n = 500
    X = np.column_stack([
        rng.normal(50_000, 15_000, n),      # income
        rng.normal(0.35, 0.12, n),          # debt ratio
        rng.integers(20, 70, n).astype(float),   # age (immutable)
    ])
    true_w = np.array([1.4e-5, -4.0, 0.004])
    predict = lambda A: A @ true_w - 0.4

    applicant = np.array([38_000.0, 0.52, 41.0])
    print(f"score {predict(applicant.reshape(1, -1))[0]:+.3f}  (approve if > 0)\n")

    phi, base, full = exact_shap(predict, applicant, X)
    names = ["income", "debt ratio", "age"]
    for name, v in zip(names, phi):
        print(f"  {name:>11}: {v:+.3f}")
    print(f"  {'sum':>11}: {phi.sum():+.3f}   vs  prediction − baseline = {full - base:+.3f}")
    print("  (local accuracy: these must match exactly)\n")

    cf = counterfactual(predict, applicant, target=0.02, mutable=[0, 1],
                        bounds={0: (0, 200_000), 1: (0.0, 1.0)})
    print("counterfactual — age deliberately held fixed:")
    for name, before, after in zip(names, applicant, cf):
        mark = "" if np.isclose(before, after) else "  ←"
        print(f"  {name:>11}: {before:>10,.2f}  →  {after:>10,.2f}{mark}")
    print(f"\n  new score {predict(cf.reshape(1, -1))[0]:+.3f}")
```

The check that `phi.sum()` equals `prediction − baseline` is the local-accuracy property, and it is worth asserting in any SHAP implementation you write — it catches baseline and indexing mistakes immediately.

## See also

- [Global Methods](./global-methods.md) — the model-wide view.
- [Pitfalls and Honest Practice](./pitfalls.md) — how to avoid over-reading these outputs.
- [Responsible AI and Failure Modes](../07-production-mlops/responsible-ai-and-failure-modes.md) — the fairness and governance context.
