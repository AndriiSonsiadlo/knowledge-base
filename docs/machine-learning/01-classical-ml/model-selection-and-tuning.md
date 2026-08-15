---
id: model-selection-and-tuning
title: Model Selection and Tuning
sidebar_label: Model Selection & Tuning
sidebar_position: 20
tags: [classical-ml, hyperparameters, tuning, methodology]
---

# Model Selection and Tuning

Every hyperparameter search is a way of spending a limited resource: the information in your validation set. Search too aggressively, over too many combinations, and you'll quietly overfit to the validation set itself — the exact failure the validation set was supposed to prevent in the first place.

:::info[Key idea]
Every hyperparameter decision spends some of your validation set — budget it like a finite resource.
:::

<Figure
  src="/img/ml/classical/grid-vs-random-search.png"
  alt="Grid search covering only five distinct values of the important parameter, versus random search covering twenty-five"
  caption="With the same 25 trials, grid search tests only 5 distinct values of the parameter that actually matters, because it spends the rest varying one that does not. Random search tests 25 — which is why it wins whenever some parameters matter far more than others."
/>

## Parameters vs. hyperparameters

**Parameters** are learned by the training objective (weights, tree splits). **Hyperparameters** are chosen before training and held fixed (learning rate, tree depth, regularisation strength) — the training loss can never be used to choose them, since the training loss is always minimised by the least-regularised, most-flexible setting, which is precisely the overfitting direction.

## Grid search and its combinatorial cost

Enumerate every combination of a fixed set of values per hyperparameter. Cost grows multiplicatively — 5 values for each of 4 hyperparameters is $5^4 = 625$ combinations, each requiring a full training run (or cross-validation fold set).

## Random search, and why it beats grid search on the same budget

Sampling hyperparameter combinations randomly, rather than exhaustively, tends to find better configurations for the same total number of trials — because in most problems only a few hyperparameters actually matter much, and grid search wastes trials varying unimportant ones on a fixed grid while barely varying the important ones. Random search explores every hyperparameter's full range on every trial, so it's far more likely to hit a good value for the hyperparameters that matter, even at the same trial budget.

## Coarse-to-fine search

<Figure
  src="/img/ml/classical/validation-curve.png"
  alt="Training error falling monotonically while validation error forms a U, with the minimum marked"
  caption="Sweeping one hyperparameter while holding the rest fixed. The gap between the curves is overfitting; the validation minimum is the setting to keep."
/>

Start with a wide, coarse random search to identify a promising region of hyperparameter space, then run a narrower, finer search (grid or random) within that region — more efficient than a single very fine search across the entire original space.

## Bayesian optimisation / TPE, conceptually

Instead of choosing the next trial randomly or exhaustively, Bayesian optimisation builds a probabilistic model of "which hyperparameter regions tend to score well" from trials already run, and uses that model to choose the next, most-promising trial — more sample-efficient than random search, at the cost of being sequential (harder to parallelise) and adding its own complexity.

## Successive halving and Hyperband

Instead of running every candidate configuration to full completion, allocate a small budget (e.g. few training epochs, small data subset) to many candidates, discard the worst-performing half, and give the survivors a larger budget — repeating until one (or a few) configurations remain, which have received the largest budget. This exploits the empirical observation that poor configurations are usually identifiable early, without needing to train them to completion.

## What to tune first, per model family

| Model | Tune first |
|---|---|
| Linear/logistic regression | regularisation strength $\lambda$ |
| SVM | $C$, then kernel `gamma` |
| Decision tree | `max_depth`, `min_samples_leaf` |
| Random forest | `n_estimators` (large), `max_features` |
| Gradient boosting | `learning_rate` and `n_estimators` together, then `max_depth` |
| kNN | $k$ |

## Nested cross-validation for an unbiased estimate

Hyperparameter search on top of a single validation set can itself overfit that validation set given enough trials. Nested CV wraps an inner CV loop (for hyperparameter selection) inside an outer CV loop (for a final, unbiased performance estimate) — the outer loop's test folds are never used in any hyperparameter decision, giving an honest number at the cost of $\text{outer folds} \times \text{inner search cost}$ total training runs.

## The validation-set overfitting trap

Running many hyperparameter trials and picking the single best validation score is itself a form of multiple-comparisons overfitting: with enough trials, some configuration will score well on the validation set purely by chance. The symptom: the gap between validation-set performance and true held-out test-set performance grows with the number of trials attempted.

## Reproducibility: seeds and reporting variance

A single training run's score is itself noisy (depending on random initialisation, data shuffling). Report mean and standard deviation across multiple seeds rather than a single number, especially when comparing two configurations whose scores are close — the full treatment is in [Reproducibility](../07-production-mlops/reproducibility.md).

## Knowing when to stop tuning

Diminishing returns set in quickly: the jump from a default configuration to a lightly-tuned one is usually large; the jump from a lightly-tuned configuration to an exhaustively-tuned one is usually small. Past a certain point, more data, better features, or a different model family will move the needle further than continued hyperparameter search.

## Code: grid vs. random vs. halving search, and nested CV

```python title="model_selection_demo.py"
import time
import numpy as np
from scipy.stats import loguniform, randint
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import (
    GridSearchCV, RandomizedSearchCV, HalvingRandomSearchCV,
    cross_val_score, StratifiedKFold,
)
from sklearn.experimental import enable_halving_search_cv  # noqa: F401, required to unlock HalvingRandomSearchCV

X, y = make_classification(n_samples=1000, n_features=20, random_state=0)

param_grid = {"n_estimators": [50, 100, 200], "max_depth": [3, 5, 10], "max_features": ["sqrt", "log2"]}
param_dist = {"n_estimators": randint(50, 300), "max_depth": randint(2, 15), "max_features": ["sqrt", "log2"]}

for name, search in [
    ("GridSearchCV", GridSearchCV(RandomForestClassifier(random_state=0), param_grid, cv=3)),
    ("RandomizedSearchCV", RandomizedSearchCV(RandomForestClassifier(random_state=0), param_dist, n_iter=18, cv=3, random_state=0)),
    ("HalvingRandomSearchCV", HalvingRandomSearchCV(RandomForestClassifier(random_state=0), param_dist, cv=3, random_state=0)),
]:
    start = time.perf_counter()
    search.fit(X, y)
    elapsed = time.perf_counter() - start
    print(f"{name:22s}: best_score={search.best_score_:.4f}  time={elapsed:.2f}s")

# --- Nested CV: the naive single-split estimate is optimistic ---
inner_cv, outer_cv = StratifiedKFold(3), StratifiedKFold(3)
nested_search = RandomizedSearchCV(RandomForestClassifier(random_state=0), param_dist, n_iter=10, cv=inner_cv, random_state=0)
nested_scores = cross_val_score(nested_search, X, y, cv=outer_cv)
print(f"\nnested CV (unbiased) score:      {nested_scores.mean():.4f}")

naive_search = RandomizedSearchCV(RandomForestClassifier(random_state=0), param_dist, n_iter=10, cv=inner_cv, random_state=0)
naive_search.fit(X, y)
print(f"naive single-search best_score (optimistic): {naive_search.best_score_:.4f}")
```

## See also

- [Train/Validation/Test Splits](../00-foundations/train-validation-test-splits.md) — the split discipline every search strategy here depends on.
- [Boosting Libraries: XGBoost, LightGBM, CatBoost](./boosting-libraries.md) — a concrete example of hyperparameters worth tuning in this order.
