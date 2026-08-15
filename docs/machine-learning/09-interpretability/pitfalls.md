---
id: pitfalls
title: Pitfalls and Honest Practice
sidebar_label: Pitfalls
sidebar_position: 4
tags: [interpretability, pitfalls, causality, fairness]
---

# Pitfalls and Honest Practice

Explanation methods produce a plot for any model, on any data, whether or not the result means anything. Knowing when the plot is lying is most of the skill.

:::info[Key idea]
Attribution is not causation, correlated features scramble every attribution method, and different methods disagree with no ground truth to settle it. Explanations are evidence to reason with, not answers to report.
:::

## Attribution is not causation

This is the error that produces bad decisions rather than merely bad slides.

A SHAP value says: *within this model*, the output moves with this feature. It says nothing about what happens if you change the feature in the world. If ice-cream sales predict drownings, ice cream gets a large SHAP value — and banning ice cream saves nobody.

Worse, the model may have learned a **reversed** relationship that is genuine in the data and catastrophic as a policy. The pneumonia model that scored asthmatics as low-risk was correct about the historical data and would have killed people if used to make the triage decision that had produced the pattern in the first place.

:::danger[Never plan an intervention from a feature-attribution plot]
"Feature X has the highest SHAP value, so let's increase X" is unsound. The model captures association; interventions require causal structure. If you need to know the effect of *doing* something, you need a randomised experiment or an explicit causal model — see [Online Evaluation and A/B Testing](../07-production-mlops/online-evaluation-and-ab-testing.md).
:::

## Correlated features break everything

When two features carry overlapping information, every attribution method has to decide how to split the credit, and they make different arbitrary choices.

| Method | Behaviour with correlated features |
|---|---|
| Permutation importance | **Understates both** — shuffle one, the model reads the other |
| Impurity importance | Splits credit arbitrarily by which was chosen first |
| SHAP (interventional) | Splits credit, may evaluate impossible feature combinations |
| SHAP (conditional / TreeSHAP path-dependent) | Respects correlations, but attributes to features the model never used |
| PDP | Extrapolates off-manifold; use ALE instead |

There is no correct answer here — it is a genuine ambiguity about what "this feature's contribution" means when two features are near-copies. The practical response:

- **Group** correlated features and attribute to the group.
- Report the correlation structure alongside any importance ranking.
- Say which SHAP variant you used; interventional and conditional answer different questions.

## Explanations of a bad model explain nothing

If a model is overfitted, mis-specified, or trained on leaked data, its explanations faithfully describe a broken object. A SHAP plot of a model that learned a leak will confidently show the leaking feature as most important — which is useful for *finding* the leak, and worthless as domain insight.

Always establish that the model generalises before interpreting it. Interpretability is a step after validation, not a substitute for it.

## Methods disagree, and there is no referee

Run permutation importance, impurity importance, and mean-absolute SHAP on the same model and you will typically get three different rankings. There is no ground-truth attribution to check them against, because "how much did this feature contribute" is not a uniquely defined quantity.

What to do:

1. Use more than one method and treat **agreement** as the signal.
2. Where they disagree, investigate rather than pick the flattering one.
3. Report the method, its parameters, and its background dataset — an unlabelled SHAP plot is not reproducible.

## Human factors

- **Plausible explanations increase trust regardless of correctness.** A convincing-looking attribution makes people trust a model *more* even when the model is wrong. Explanations can manufacture unwarranted confidence.
- **Confirmation bias.** Given several methods, people report the one matching their prior. Pre-register which method you will use.
- **Feature names are not concepts.** `f_47_norm` explains nothing to a domain expert; explanations must be translated into their vocabulary to be useful.

## Fairness needs its own tooling

A model can produce entirely reasonable explanations and still discriminate — through proxies (postcode for ethnicity, purchase history for pregnancy) that look innocuous in an attribution plot.

Fairness requires measuring **outcomes** sliced by group, not inspecting attributions:

| Criterion | Requires |
|---|---|
| Demographic parity | Equal positive rate across groups |
| Equalised odds | Equal TPR **and** FPR across groups |
| Calibration within groups | A predicted 0.7 means 0.7 in every group |

These are mathematically incompatible except in degenerate cases — you cannot satisfy all three at once, so which one you choose is an explicit, documented, value-laden decision. Removing the protected attribute from the features does not achieve fairness; it just hides the proxy.

## A checklist

Before presenting an explanation:

- [ ] The model generalises — validated on held-out data, no leakage
- [ ] Importance computed on **held-out** data, not training data
- [ ] Correlated features grouped, or the correlation reported
- [ ] At least two methods agree, or the disagreement is explained
- [ ] ICE plotted alongside every PDP
- [ ] The SHAP background dataset is stated
- [ ] LIME run with several seeds and shown to be stable
- [ ] No causal claim is being made from an associational method
- [ ] Fairness assessed by sliced outcome metrics, not attributions
- [ ] Explanation phrased in the audience's vocabulary

## Code: demonstrating the correlation trap and method disagreement

```python title="pitfalls.py"
import numpy as np


def permutation_importance(predict, X, y, n_repeats=20, seed=0):
    rng = np.random.default_rng(seed)
    r2 = lambda a, p: 1 - ((a - p) ** 2).sum() / ((a - a.mean()) ** 2).sum()
    baseline = r2(y, predict(X))
    out = np.zeros(X.shape[1])
    for j in range(X.shape[1]):
        drops = []
        for _ in range(n_repeats):
            Xp = X.copy()
            rng.shuffle(Xp[:, j])
            drops.append(baseline - r2(y, predict(Xp)))
        out[j] = np.mean(drops)
    return out


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    n = 4000

    signal = rng.normal(size=n)
    X = np.column_stack([
        signal,                              # x0: the real driver
        signal + rng.normal(0, 0.03, n),     # x1: a near-copy of x0
        rng.normal(size=n),                  # x2: independent, weaker driver
    ])
    y = 2.0 * signal + 0.8 * X[:, 2] + rng.normal(0, 0.3, n)

    Xd = np.column_stack([np.ones(n), X])
    coefs, *_ = np.linalg.lstsq(Xd, y, rcond=None)
    predict = lambda A: np.column_stack([np.ones(len(A)), A]) @ coefs

    print("fitted coefficients (note how the shared signal is split arbitrarily):")
    for j, name in enumerate(["x0", "x1 (copy of x0)", "x2"]):
        print(f"  {name:>16}: {coefs[j + 1]:+.3f}")

    imp = permutation_importance(predict, X, y)
    print("\npermutation importance:")
    for j, name in enumerate(["x0", "x1 (copy of x0)", "x2"]):
        print(f"  {name:>16}: {imp[j]:+.4f}")

    print("\nx0 and x1 jointly carry ~2.0 of signal — far more than x2's 0.8 —")
    print("yet both score near zero because each covers for the other.")
    print("Permuting them together tells the truth:")

    r2 = lambda a, p: 1 - ((a - p) ** 2).sum() / ((a - a.mean()) ** 2).sum()
    base = r2(y, predict(X))
    Xg = X.copy()
    rng.shuffle(Xg[:, 0])
    rng.shuffle(Xg[:, 1])
    print(f"  group (x0, x1)  : {base - r2(y, predict(Xg)):+.4f}")
```

The final number is several times either individual score. Any importance ranking computed feature-by-feature on correlated inputs is telling you something other than what it appears to.

## See also

- [Global Methods](./global-methods.md) and [Local Methods](./local-methods.md) — the methods this page qualifies.
- [Responsible AI and Failure Modes](../07-production-mlops/responsible-ai-and-failure-modes.md) — fairness metrics in depth.
- [Online Evaluation and A/B Testing](../07-production-mlops/online-evaluation-and-ab-testing.md) — how to actually establish a causal effect.
