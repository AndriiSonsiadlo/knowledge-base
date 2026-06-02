---
id: train-validation-test-splits
title: Train/Validation/Test Splits
sidebar_label: Train/Val/Test Splits
sidebar_position: 13
tags: [foundations, evaluation, methodology]
---

# Train/Validation/Test Splits

The test set is spent the moment you make a decision based on it. If you tune a hyperparameter, pick a model, or even decide "let's try one more architecture" after looking at test performance, that number is no longer an honest estimate of how the model will do on truly new data. The validation set exists specifically to absorb those decisions so the test set can stay clean.

:::info[Key idea]
The test set is spent the moment you make a decision based on it — the validation set exists to absorb those decisions.
:::

## The three splits and the job of each

- **Training set**: what the model's parameters are fit to.
- **Validation set**: used to make decisions — which hyperparameters, which model, when to stop training. You can look at this repeatedly.
- **Test set**: touched exactly once, at the very end, to report the number that will actually generalise to production. Every peek at it before that point degrades its honesty.

## Why a validation set is not optional

Without one, every hyperparameter decision has to be made against the test set — which means the test set has silently become a second training set, and the final reported number is optimistic in a way you can't measure.

## k-fold cross-validation

Split the data into $k$ folds; train on $k-1$, validate on the remaining one; rotate which fold is held out; average the $k$ validation scores. This uses every example for both training and validation (at different times) and gives a variance estimate on the metric, not just a point estimate — useful when the dataset is too small to afford a single held-out validation set.

## Stratified k-fold

Ordinary k-fold can, by chance, put almost all of a rare class into one fold. Stratified k-fold preserves the class proportions in every fold, which matters whenever classes are imbalanced (see [Imbalanced Data](../01-classical-ml/imbalanced-data.md)).

## Leave-one-out

The extreme case of k-fold with $k = n$ — every single example gets its own fold. Uses the maximum possible training data per fold, but costs $n$ full training runs, which is often computationally prohibitive.

## Grouped splits

When multiple rows share a subject (repeated measurements from the same patient, multiple images of the same object), a random split can put some of a subject's rows in training and others in validation — the model then partly "recognises" the subject rather than generalising, inflating the validation score. Grouped splits keep every row from a given subject in the same fold.

## Time-series splits

**Never shuffle time-series data.** A model must only ever be validated on data that comes *after* what it was trained on — shuffling lets it "see the future" during training, producing scores that look great and never reproduce in production. The correct scheme is an expanding or rolling window that always trains on the past and validates on the future.

## Nested cross-validation

Hyperparameter search on top of a single validation set still risks overfitting to that validation set if you try enough combinations. Nested CV wraps an inner cross-validation loop (for hyperparameter selection) inside an outer cross-validation loop (for an honest final performance estimate) — more expensive, but the only fully unbiased approach when the search space is large.

## Data leakage: six common forms

| Form | Symptom |
|---|---|
| Scaling/normalising before the split | validation score is optimistic, doesn't reproduce on new data |
| Target leakage (a feature that encodes the label) | suspiciously perfect validation score |
| Temporal leakage (future data leaking into training) | great backtest, poor live performance |
| Duplicate rows across split | inflated score from near-identical train/val examples |
| Group leakage (same subject in both splits) | model "recognises" subjects instead of generalising |
| Feature selection using the full dataset | overly optimistic score, understated true error |

The single most common leak is fitting a scaler (or any preprocessing step) on the full dataset before splitting — the scaler's mean and standard deviation then contain information from the validation set, which is exactly the leak the entire split discipline exists to prevent.

## The checklist

1. Split before any preprocessing that learns from the data.
2. Match the split strategy to the data's structure (grouped, stratified, or temporal, as appropriate).
3. Look at the test set exactly once.
4. Wrap preprocessing and modelling in a single `Pipeline` fitted only inside each training fold.

## Code: correct pipelines, and the leak that inflates a score

```python title="split_discipline_demo.py"
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import (
    train_test_split, StratifiedKFold, TimeSeriesSplit, cross_val_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

X, y = make_classification(n_samples=500, weights=[0.9, 0.1], random_state=0)

# --- Correct: scaler fitted only inside each training fold ---
correct_pipeline = Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression())])
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
correct_scores = cross_val_score(correct_pipeline, X, y, cv=skf, scoring="roc_auc")
print("correct (scaler inside CV):", correct_scores.mean())

# --- Leaky: scaler fitted on the FULL dataset before cross-validation ---
X_leaked = StandardScaler().fit_transform(X)  # sees validation folds too!
leaky_scores = cross_val_score(LogisticRegression(), X_leaked, y, cv=skf, scoring="roc_auc")
print("leaky (scaler fit on full data first):", leaky_scores.mean())

# --- Time-series split: never shuffle ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, shuffle=False)
tscv = TimeSeriesSplit(n_splits=5)
for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train)):
    print(f"fold {fold}: train size={len(train_idx)}, validates on the NEXT chunk, size={len(val_idx)}")
```

The leaky score is consistently higher than the correct one — small on this synthetic dataset, but the gap grows substantially with fewer samples or stronger scalers, and it never shows up until the model meets real production data.

## See also

- [The ML Workflow](./the-ml-workflow.md) — where splitting fits into the overall project loop.
- [Evaluation Metrics for Classification](./evaluation-metrics-classification.md) — what to measure once the splits are correct.
