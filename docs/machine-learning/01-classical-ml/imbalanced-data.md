---
id: imbalanced-data
title: Imbalanced Data
sidebar_label: Imbalanced Data
sidebar_position: 19
tags: [classical-ml, imbalance, evaluation]
---

# Imbalanced Data

99% of your rows are one class, and accuracy just became a lie. Imbalance is best understood as a metric-and-threshold problem before it's a sampling problem — fixing evaluation costs nothing and should always come first, and often it turns out to be the only fix actually needed.

:::info[Key idea]
Imbalance is a metric-and-threshold problem before it is a sampling problem — fix the evaluation first, then decide whether to touch the data.
:::

## Where imbalance comes from

Rare-event prediction (fraud, disease, equipment failure), where the rare class is inherently uncommon in the real world — not a data-collection mistake to be "fixed" by resampling, but a genuine property of the problem the model must be evaluated against honestly.

## Why accuracy and even ROC-AUC mislead at extreme ratios

Accuracy on a 99:1 dataset is trivially high for a model that predicts the majority class always — covered in [Evaluation Metrics for Classification](../00-foundations/evaluation-metrics-classification.md). ROC-AUC is more robust but still misleading at extreme ratios: its false-positive rate is normalised by the (huge) number of true negatives, so even a poor classifier with many false positives relative to the tiny number of true positives can still show a deceptively high AUC. **PR-AUC does not have this problem** — precision is computed relative to *predicted* positives, which stays sensitive to false positives regardless of how many true negatives exist.

## Threshold moving as the cheapest fix

Most classifiers default to a 0.5 decision threshold, which is simply the wrong choice when classes are imbalanced and error costs differ. Moving the threshold based on the actual cost of false positives versus false negatives ([Evaluation Metrics for Classification](../00-foundations/evaluation-metrics-classification.md)) costs nothing computationally and is often the single most effective imbalance fix — it requires no retraining.

## Class weights in the loss

Multiply each class's loss contribution by a weight inversely proportional to its frequency (the formula from [Loss Functions](../00-foundations/loss-functions.md)), forcing the optimiser to treat minority-class mistakes as costing more — available as a simple parameter (`class_weight="balanced"`) in most sklearn models.

## Random undersampling and what it discards

Randomly remove majority-class examples until classes are balanced — cheap, but discards potentially useful information, and with severe imbalance can throw away the vast majority of the dataset.

## Random oversampling and the overfitting it invites

Randomly duplicate minority-class examples until classes are balanced — preserves all data, but duplicated points give the model exact repeats to memorise, increasing overfitting risk on the minority class specifically.

## SMOTE and the honest evidence

:::note[Outside the master library whitelist]
The code example below uses `imbalanced-learn` (`imblearn`), not in the default library set. Install with `pip install imbalanced-learn`.
:::

SMOTE (Synthetic Minority Oversampling Technique) generates *synthetic* minority examples by interpolating between existing minority points and their nearest minority neighbours, rather than exact duplicates — a more sophisticated alternative to naive oversampling. The honest caveat, backed by several published benchmarking studies: SMOTE often does **not** outperform simple class weighting or threshold tuning in practice, despite being the most commonly reached-for imbalance technique — try the cheaper fixes first and measure whether SMOTE actually helps on your specific data before assuming it will.

## Resampling belongs inside the cross-validation fold

Applying SMOTE (or any resampling) to the *full* dataset before splitting leaks synthetic points derived from what will become validation data back into training — the same leakage class covered in [Train/Validation/Test Splits](../00-foundations/train-validation-test-splits.md). Resampling must happen only on the training portion of each fold, never before the split.

## Ensemble approaches

**Balanced bagging**: each bootstrap sample in a bagging ensemble is drawn to be class-balanced, rather than reflecting the original imbalanced proportions — combines [Random Forests and Bagging](./random-forests-and-bagging.md)'s variance reduction with a built-in resampling step.

## Anomaly detection as the alternative framing

At extreme imbalance ratios (far fewer than 1% positive), there may be too few positive examples for a classifier to learn stable patterns at all — [Anomaly Detection](./anomaly-detection.md)'s "model normal, flag deviation" framing can work better than trying to force a supervised classifier to learn from a handful of positive examples.

## Decision table by imbalance ratio

| Ratio | Reach for |
|---|---|
| Mild (up to ~9:1) | class weights, threshold tuning — often sufficient alone |
| Moderate (10:1 to 100:1) | class weights + threshold tuning; consider SMOTE if those aren't enough |
| Severe (100:1 to 1000:1) | balanced bagging, careful threshold tuning, PR-AUC as the primary metric |
| Extreme (beyond 1000:1, very few positives) | anomaly detection framing instead of supervised classification |

## Code: accuracy vs. ROC-AUC vs. PR-AUC divergence, and the SMOTE leak

```python title="imbalanced_data_demo.py"
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, average_precision_score

X, y = make_classification(n_samples=2000, weights=[0.99, 0.01], random_state=0)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, stratify=y, random_state=0)

# --- Baseline: predict majority class always ---
majority_preds = np.zeros(len(y_test))
print(f"majority-class accuracy: {accuracy_score(y_test, majority_preds):.4f}  <- looks great, catches zero positives")

model = LogisticRegression(class_weight="balanced", max_iter=500).fit(X_train, y_train)
probs = model.predict_proba(X_test)[:, 1]
preds = (probs >= 0.5).astype(int)

print(f"model accuracy:  {accuracy_score(y_test, preds):.4f}")
print(f"model ROC-AUC:    {roc_auc_score(y_test, probs):.4f}")
print(f"model PR-AUC:     {average_precision_score(y_test, probs):.4f}  <- the honest number here")

# --- SMOTE inside vs. outside the CV fold ---
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)

correct_pipeline = ImbPipeline([("smote", SMOTE(random_state=0)), ("clf", LogisticRegression(max_iter=500))])
correct_scores = cross_val_score(correct_pipeline, X, y, cv=skf, scoring="average_precision")
print(f"\ncorrect (SMOTE inside CV): {correct_scores.mean():.4f}")

X_smote_leaked, y_smote_leaked = SMOTE(random_state=0).fit_resample(X, y)  # sees all data first
leaky_scores = cross_val_score(LogisticRegression(max_iter=500), X_smote_leaked, y_smote_leaked, cv=5, scoring="average_precision")
print(f"leaky (SMOTE before split):  {leaky_scores.mean():.4f}")
```

## See also

- [Evaluation Metrics for Classification](../00-foundations/evaluation-metrics-classification.md) — the metric and threshold discipline this page depends on.
- [Anomaly Detection](./anomaly-detection.md) — the alternative framing at extreme imbalance ratios.
