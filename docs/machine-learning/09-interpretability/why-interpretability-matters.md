---
id: why-interpretability-matters
title: Why Interpretability Matters
sidebar_label: Why It Matters
sidebar_position: 1
tags: [interpretability, explainability, responsible-ai]
---

# Why Interpretability Matters

A model that is accurate on your test set can still be unusable — because it is illegal to deploy without an explanation, because it is right for a reason that will not survive next quarter, or because nobody will act on a number they cannot interrogate.

:::info[Key idea]
"Why did the model say that?" is a different question from "is the model accurate?", and a good answer to the second does not supply the first. Interpretability is how you check that a model is right *for the right reasons* — which is the only kind of correctness that generalises.
:::

## Four distinct reasons, with different requirements

| Reason | Who asks | What satisfies them |
|---|---|---|
| **Debugging** | You | Any method that reveals what the model keyed on |
| **Trust and adoption** | Domain experts, users | Explanations in their vocabulary, not features |
| **Regulation** | Legal, compliance | Documented, reproducible, often model-specific |
| **Fairness auditing** | Everyone | Behaviour sliced by protected group |

These pull in different directions. A SHAP plot is excellent for debugging and useless for a customer told their loan was declined. Under the GDPR and the US Equal Credit Opportunity Act, "adverse action" notices must give specific principal reasons — a requirement that post-hoc attribution satisfies awkwardly at best.

## The famous failure modes

Every one of these was a model with excellent test-set metrics.

- **The husky and the wolf.** A classifier separating huskies from wolves turned out to be detecting **snow** in the background. It scored well because wolf photos happened to be taken in snow. This is the canonical demonstration of a right answer for a wrong reason.
- **Pneumonia and asthma.** A model predicting pneumonia mortality learned that asthmatic patients had *lower* risk — true in the data, because asthmatics were routed straight to intensive care. Deployed as a triage tool it would have sent exactly the highest-risk patients home.
- **Rulers in dermatology images.** Skin-lesion classifiers picked up on the surgical rulers that clinicians place beside lesions they already suspect are malignant.
- **Hospital tokens in chest X-rays.** Models learned to identify which hospital took the scan from metadata burned into the image, and used base rates rather than pathology.

The pattern is identical each time: a shortcut correlated with the label in training, absent or reversed in deployment. **No accuracy metric can detect this.** Only looking at what the model used can.

## Interpretable by design, or explained afterwards

<Figure
  src="/img/ml/applied/interp-tradeoff.png"
  alt="A scatter of model families positioned by how interpretable they are against typical accuracy on complex tabular data"
  caption="The usual trade-off. Post-hoc explanation is the attempt to buy back some interpretability without giving up accuracy — but an explanation of a black box is an approximation of it, never the thing itself."
/>

| | Intrinsically interpretable | Post-hoc explained |
|---|---|---|
| Examples | Linear/logistic, shallow trees, GAMs, rule lists | Any model + SHAP, LIME, PDP |
| Explanation is | The model itself | An approximation of the model |
| Faithfulness | Exact by construction | Approximate, sometimes badly |
| Accuracy ceiling | Lower on complex data | Whatever the model achieves |

:::warning[Prefer an interpretable model when one is good enough]
The reflex to fit gradient boosting and explain it afterwards is often the wrong move. On many tabular problems a well-specified logistic regression or a small GAM loses very little accuracy and gives an explanation that is exact rather than approximate.

Rudin's argument is worth taking seriously: for high-stakes decisions, explaining a black box is a worse answer than not using a black box. The burden should be on demonstrating that the extra accuracy is real, material, and worth the loss of a faithful explanation.
:::

## The axes to keep straight

**Global vs. local.** Global explanations describe the model's overall behaviour ("income is the most important feature"). Local explanations describe one prediction ("*this* applicant was declined mainly because of their debt ratio"). They answer different questions and can genuinely disagree — a feature can be globally unimportant but decisive for a particular case.

**Model-specific vs. model-agnostic.** Model-specific methods exploit internal structure (tree split gains, linear coefficients, attention weights) and are usually faster and more faithful. Model-agnostic methods (permutation importance, LIME, KernelSHAP) treat the model as a black box and work on anything, at higher cost.

## What an explanation is not

- **It is not causal.** A SHAP value says the model's output moves with this feature, not that changing the feature in the world changes the outcome. Confusing the two leads directly to bad interventions.
- **It is not necessarily faithful.** A surrogate model can approximate a black box well on average and badly exactly where you are looking.
- **It is not unique.** Different methods routinely produce different — occasionally contradictory — attributions for the same prediction, and there is no ground truth to arbitrate.
- **It is not a fairness guarantee.** A model can produce reasonable-looking explanations and still be discriminatory through proxy variables.

## See also

- [Global Methods](./global-methods.md) — feature importance, PDP and ICE.
- [Local Methods](./local-methods.md) — SHAP, LIME and counterfactuals.
- [Pitfalls and Honest Practice](./pitfalls.md) — how these methods mislead.
- [Responsible AI and Failure Modes](../07-production-mlops/responsible-ai-and-failure-modes.md) — the broader governance picture.
