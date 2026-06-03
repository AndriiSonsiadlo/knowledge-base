---
id: feature-stores
title: Feature Stores
sidebar_label: Feature Stores
sidebar_position: 4
tags: [mlops, features, feature-store, serving]
---

# Feature Stores

The same feature, computed two different ways in two different places, gives two different answers — training pipeline code and serving pipeline code drift apart, quietly, until a model that scored well offline behaves differently in production for no reason anyone can immediately find.

:::info[Key idea]
A feature store exists to guarantee that training and serving compute a feature identically - everything else it does is convenience.
:::

## Training/serving skew, defined and illustrated

**Training/serving skew** is any difference between how a feature is computed at training time versus at serving time — a different aggregation window, a subtly different join, a rounding difference. A concrete example: training computes "average purchase amount over the last 30 days" using a batch job with full historical data; serving computes it with a slightly different window boundary due to timezone handling — the model was trained on one distribution of that feature and is being fed a subtly different one at inference time, with no error raised anywhere.

## The offline store and the online store

**Offline store**: holds historical feature values, optimised for large-scale batch reads — what training reads from. **Online store**: holds only the *current* value of each feature, optimised for low-latency single-row lookups — what serving reads from at inference time. A feature store's core job is keeping these two representations of the same underlying feature definition consistent with each other.

## Point-in-time correctness, and the label-leakage bug it prevents

When assembling a training set, each row needs the feature values *as they were at the time the label was generated* — not the feature's current (possibly later-updated) value. Using a feature's future value to train on a past label is a form of [Curse of Dimensionality](../00-foundations/curse-of-dimensionality.md)-adjacent leakage — the model learns from information it wouldn't have had at prediction time, and the resulting offline metric is inflated in a way that never appears in true serving.

$$
\text{feature}(entity, t) = \text{value of the feature for } entity \text{ as of exactly time } t, \text{ not later}
$$

## Feature definitions as versioned code

A feature's *definition* — the transformation logic that produces it — should be versioned exactly like model code, not left as an ad-hoc SQL query someone wrote once. This is what makes it possible to know, later, exactly what "average purchase amount" meant for any given historical training run, even after the definition has since been refined.

## Backfilling a new feature

When a new feature definition is added, historical training data needs that feature computed retroactively across past time periods — a **backfill**, exactly analogous to [Data Pipelines and Contracts](./data-pipelines-and-contracts.md)'s backfill concept, applied specifically to feature computation rather than raw ingestion.

## Feature reuse across models, and its real organisational value

Once a feature is defined and materialised once, any model can reuse it — avoiding every team independently reimplementing "average purchase amount" slightly differently, each with its own subtle bugs and its own skew risk. This reuse, more than any individual technical capability, is often the actual organisational payoff of a shared feature store.

## Freshness and TTL

Each online feature has a **freshness** requirement (how recently must it have been updated to be usable) and often a **TTL** (time-to-live, after which a stale value is treated as missing rather than served as if current) — both need to be explicit, since silently serving a stale feature value is a quieter version of the same training/serving skew problem.

## The latency budget for online lookups

Online feature lookups happen inside the request path of a real-time prediction — every millisecond spent looking up features directly extends end-to-end latency, connecting directly to [Serving Patterns](./serving-patterns.md)'s latency budget. This is why the online store is architecturally distinct from (and much faster, for single-row lookups, than) the offline store.

## When a feature store is overkill

For a single model doing batch scoring, with no real-time serving requirement and no feature reuse across other models, a full feature store is often unnecessary infrastructure — the skew and reuse problems it solves don't yet exist in that setup, and the operational cost of running the infrastructure isn't earning its keep.

## The lightweight alternative: shared transformation code plus a scheduled materialisation job

A simpler pattern that solves the *core* skew problem without a dedicated feature-store platform: put the feature transformation logic in one shared module, imported by both training and serving code paths directly, and run a scheduled job that materialises the current values wherever serving needs to read them — the same guarantee (one definition, two consumers) with far less infrastructure.

| Symbol | Meaning |
|---|---|
| offline store | historical feature values, for training |
| online store | current feature values, low-latency, for serving |

## Code: point-in-time correct join vs. a naive join, and the leakage it prevents

```python title="feature_store_demo.py"
import pandas as pd

events = pd.DataFrame({
    "user_id": [1, 1, 1, 2, 2],
    "event_time": pd.to_datetime(["2026-01-01", "2026-01-05", "2026-01-10", "2026-01-02", "2026-01-08"]),
    "purchase_amount": [50.0, 30.0, 100.0, 20.0, 40.0],
})

labels = pd.DataFrame({
    "user_id": [1, 2],
    "label_time": pd.to_datetime(["2026-01-06", "2026-01-05"]),
    "churned": [0, 1],
})

def naive_join(labels: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """WRONG: uses ALL events per user, including ones after the label was generated."""
    agg = events.groupby("user_id")["purchase_amount"].mean().rename("avg_purchase")
    return labels.merge(agg, on="user_id")

def point_in_time_join(labels: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """CORRECT: only uses events that happened before each row's label_time."""
    rows = []
    for _, label_row in labels.iterrows():
        valid_events = events[
            (events["user_id"] == label_row["user_id"])
            & (events["event_time"] < label_row["label_time"])  # strictly before the label
        ]
        avg_purchase = valid_events["purchase_amount"].mean() if len(valid_events) else None
        rows.append({**label_row.to_dict(), "avg_purchase": avg_purchase})
    return pd.DataFrame(rows)

naive_result = naive_join(labels, events)
correct_result = point_in_time_join(labels, events)

print("naive join (LEAKS future purchases into avg_purchase):")
print(naive_result[["user_id", "avg_purchase", "churned"]])
print("\npoint-in-time correct join (only purchases known before the label):")
print(correct_result[["user_id", "avg_purchase", "churned"]])
print(f"\nuser 1's avg_purchase differs: naive={naive_result.iloc[0]['avg_purchase']:.1f} "
      f"vs correct={correct_result.iloc[0]['avg_purchase']:.1f} — the naive version leaked the Jan-10 purchase")
```

## See also

- [Data Pipelines and Contracts](./data-pipelines-and-contracts.md) — the validated pipelines that feed a feature store's raw inputs.
- [Serving Patterns](./serving-patterns.md) — where the online store's latency budget becomes a hard production constraint.
