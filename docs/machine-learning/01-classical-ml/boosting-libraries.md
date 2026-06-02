---
id: boosting-libraries
title: "Boosting Libraries: XGBoost, LightGBM, CatBoost"
sidebar_label: XGBoost, LightGBM, CatBoost
sidebar_position: 11
tags: [classical-ml, boosting, xgboost, lightgbm, catboost]
---

# Boosting Libraries: XGBoost, LightGBM, CatBoost

:::note[Outside the master library whitelist]
This page uses `xgboost`, `lightgbm`, and `catboost` — none is in the knowledge base's default library set (`numpy`, `scipy`, `pandas`, `matplotlib`, `scikit-learn`, `torch`, `torchvision`, `transformers`, `datasets`). They are the industry-standard implementations of [Gradient Boosting](./gradient-boosting.md) and this page cannot honestly cover the topic without them. Install with `pip install xgboost lightgbm catboost`.
:::

The textbook gradient boosting algorithm from the previous page is simple; three competing libraries have spent a decade optimising and extending it, and they now disagree about nearly everything except the core idea. Knowing what each one actually does differently — not just which one "wins" a given benchmark — is what lets you pick correctly for a new problem.

:::info[Key idea]
XGBoost, LightGBM, and CatBoost differ in how they grow trees and how they handle categories — those two choices drive nearly every practical difference.
:::

## What the libraries add over textbook gradient boosting

Second-order loss approximation, sophisticated regularisation, native missing-value handling, GPU support, and — critically — very different strategies for *how* a tree is grown, which turns out to matter more than any other single design choice.

## XGBoost: regularised objective, second-order approximation, level-wise growth

XGBoost approximates the loss with a second-order (Newton) expansion, using both gradient and Hessian information per split, and adds an explicit regularisation term over tree complexity (number of leaves, leaf weight magnitude) directly into the split-selection objective — not just as external hyperparameters. Trees grow **level-wise**: every node at a given depth is split before moving to the next depth, producing balanced trees.

## LightGBM: leaf-wise growth, histogram binning, GOSS

LightGBM grows trees **leaf-wise**: at each step it splits whichever leaf gives the largest loss reduction, regardless of depth — this can produce much better loss reduction per tree than level-wise growth, but the resulting trees are unbalanced and prone to overfitting on small datasets (since leaf-wise growth aggressively deepens whichever branch looks best on the training data, which is more susceptible to noise on small samples). Histogram-based binning discretises continuous features into buckets before searching for splits, dramatically speeding up split-finding. **GOSS** (Gradient-based One-Side Sampling) keeps all high-gradient (poorly-fit) examples but subsamples low-gradient (well-fit) ones, speeding up training with minimal accuracy loss.

## CatBoost: ordered boosting, native categorical handling, target-leakage avoidance

CatBoost's signature feature is native handling of categorical features via **ordered target statistics** — computing a category's encoded value using only the examples that came before it in a randomly permuted order, which prevents the target leakage that naive target-mean encoding introduces ([Data Preprocessing and Features](../00-foundations/data-preprocessing-and-features.md)). **Ordered boosting** applies the same before-only-what-came-earlier discipline to the boosting process itself, further reducing overfitting from target leakage.

## Comparison table

| | XGBoost | LightGBM | CatBoost |
|---|---|---|---|
| Growth strategy | level-wise | leaf-wise | level-wise (symmetric) |
| Categorical handling | manual encoding needed | some native support | best-in-class native support |
| Missing values | native | native | native |
| Speed | good | fastest, especially on large data | slower, but often needs less tuning |
| Default overfitting risk | moderate | higher on small data | lower, due to ordered boosting |
| GPU support | yes | yes | yes |

## Hyperparameters that actually matter, ranked

1. `n_estimators` / `num_boost_round` and `learning_rate` — the fundamental boosting trade.
2. `max_depth` (XGBoost/CatBoost) or `num_leaves` (LightGBM) — controls overfitting risk directly.
3. `subsample` and `colsample_bytree` — bagging-style randomness layered on top of boosting.
4. Regularisation terms (`reg_alpha`/`reg_lambda` in XGBoost, `l2_leaf_reg` in CatBoost).

## A sane tuning order

Fix a small learning rate and a generous `n_estimators` with early stopping; tune tree complexity (`max_depth`/`num_leaves`) first, since it has the largest effect on the bias/variance balance; then tune subsampling and regularisation; only then, if needed, fine-tune the learning rate itself.

## When a random forest or a linear model is the better answer

If the dataset is small and noisy, a [Random Forest](./random-forests-and-bagging.md)'s robustness to overfitting may beat a carefully-tuned boosted model with less effort. If the relationship is genuinely close to linear, [Linear Regression](./linear-regression.md) or [Logistic Regression](./logistic-regression.md) will be faster, more interpretable, and just as accurate — boosting's flexibility is wasted effort when the true function doesn't need it.

## Code: identical task, all three libraries, score and timing

```python title="boosting_libraries_demo.py"
import time
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import xgboost as xgb
import lightgbm as lgb
import catboost as cb

X, y = make_classification(n_samples=5000, n_features=20, random_state=0)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

models = {
    "XGBoost": xgb.XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.1, eval_metric="logloss"),
    "LightGBM": lgb.LGBMClassifier(n_estimators=200, num_leaves=15, learning_rate=0.1, verbose=-1),
    "CatBoost": cb.CatBoostClassifier(n_estimators=200, depth=4, learning_rate=0.1, verbose=False),
}

print(f"{'model':10s} | {'AUC':>6s} | {'fit time (s)':>12s}")
for name, model in models.items():
    start = time.perf_counter()
    model.fit(X_train, y_train)
    elapsed = time.perf_counter() - start
    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    print(f"{name:10s} | {auc:.4f} | {elapsed:12.3f}")

# --- LightGBM native categorical handling vs manual one-hot ---
categories = np.random.default_rng(0).choice(["A", "B", "C", "D"], size=len(X))
import pandas as pd
df = pd.DataFrame(X, columns=[f"f{i}" for i in range(X.shape[1])])
df["cat"] = pd.Categorical(categories)  # LightGBM reads pandas categorical dtype natively
lgb_native = lgb.LGBMClassifier(n_estimators=100, verbose=-1).fit(df, y, categorical_feature=["cat"])
print("LightGBM with native categorical handling trained successfully, no manual encoding required")
```

## See also

- [Gradient Boosting](./gradient-boosting.md) — the textbook algorithm all three libraries extend.
- [Model Selection and Tuning](./model-selection-and-tuning.md) — the search strategy for the hyperparameters listed above.
