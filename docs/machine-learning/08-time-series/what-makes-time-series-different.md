---
id: what-makes-time-series-different
title: What Makes Time Series Different
sidebar_label: What Makes It Different
sidebar_position: 1
tags: [time-series, forecasting, foundations]
---

# What Makes Time Series Different

Almost everything in [Foundations](../00-foundations/what-is-machine-learning.md) assumes your observations are independent and identically distributed — that shuffling the rows changes nothing. Time series violates that assumption in the first sentence: the order *is* the signal. Every technique in this section exists because that one assumption fails.

:::info[Key idea]
i.i.d. is the assumption that breaks. Once observations are ordered and correlated with their own past, random splits leak the future into training, cross-validation becomes invalid, and the error of a forecast grows with how far ahead you look.
:::

## The three things that change

| | Ordinary supervised learning | Time series |
|---|---|---|
| Row order | Irrelevant — shuffle freely | Carries the signal |
| Observations | Independent | Correlated with their own past |
| Splitting | Random | Must respect chronology |
| Error | Roughly constant across the test set | Grows with the forecast horizon |
| Target at prediction time | Unknown, unrelated to inputs | Often a future value of the input itself |

## Autocorrelation: the defining property

In a time series, a value is correlated with its own earlier values. Yesterday's temperature is the single best predictor of today's. That correlation is the thing you are exploiting — and also the thing that invalidates the standard statistical machinery, which assumes independent errors.

Two consequences follow immediately:

- **Effective sample size is smaller than the row count.** A thousand highly autocorrelated hourly readings carry far less information than a thousand independent samples. Confidence intervals computed as if they were independent will be far too narrow.
- **A naive baseline is unusually strong.** Predicting "tomorrow equals today" — the *persistence* or *random-walk* forecast — beats a surprising number of models on a surprising number of series. It is the baseline any real model must beat, and the one most often skipped.

:::warning[Beating the persistence baseline is the bar]
A model with 3 % error sounds good until you compute that predicting "same as yesterday" gets 2.8 %. Always compute the naive forecast first. On financial series in particular it is very hard to beat, and a model that appears to do so is usually leaking.
:::

## The vocabulary

| Term | Meaning |
|---|---|
| **Trend** | Long-run movement of the level |
| **Seasonality** | A pattern repeating on a *fixed, known* period — daily, weekly, yearly |
| **Cycle** | A repeating pattern with no fixed period (business cycles) |
| **Residual / noise** | What is left after removing the above |
| **Lag** | A previous value: lag-1 is the prior observation |
| **Horizon (h)** | How many steps ahead you forecast |
| **Frequency** | The sampling interval — hourly, daily, monthly |
| **Stationarity** | Statistical properties do not change over time |

Seasonality and cycles are worth keeping distinct: seasonality has a known fixed period you can encode directly, cycles do not and are much harder.

## Univariate, multivariate, and panel

- **Univariate** — one series, predicted from its own history. `sales`.
- **Multivariate** — several series that interact and are forecast jointly. `sales`, `price`, `stock`.
- **Panel / longitudinal** — many related series sharing structure, forecast together. Sales for 10,000 products across 200 stores.

Panel data is what most industrial forecasting actually looks like, and it is where machine-learning approaches decisively beat per-series classical models: one gradient-boosted model trained across all series learns patterns that a series with twelve observations could never support alone.

## Forecasting is not the only task

| Task | Question |
|---|---|
| **Forecasting** | What comes next? |
| **Anomaly detection** | Is this point abnormal *given the pattern*? |
| **Classification** | What kind of series is this? (ECG diagnosis, device identification) |
| **Segmentation / changepoint detection** | When did the behaviour change? |
| **Imputation** | What was the missing value? |

The rest of this section is about forecasting, which is the most common and the one whose pitfalls generalise best. [Anomaly detection](../01-classical-ml/anomaly-detection.md) covers the second in a non-temporal setting.

## Why random splitting is fatal

This deserves stating explicitly because it is the single most common mistake:

```python
# WRONG — for a time series this is meaningless
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=True)
```

With shuffling, the test set contains points from *before* some training points. The model is being asked to interpolate inside a period it has already seen, not to predict the future. Reported error can be several times lower than the model's real forecasting error — and the gap only shows up in production.

The fix is chronological splitting, covered in [Validation and Backtesting](./validation-and-backtesting.md).

## Code: the naive baselines every project should start with

```python title="baselines.py"
import numpy as np


def naive_forecast(y, h=1):
    """Persistence: tomorrow equals today. The bar to beat."""
    return np.repeat(y[-1], h)


def seasonal_naive_forecast(y, season_length, h=1):
    """This period equals the same period last cycle. Strong on seasonal data."""
    return np.array([y[-season_length + (i % season_length)] for i in range(h)])


def drift_forecast(y, h=1):
    """Extrapolate the average slope of the whole history."""
    slope = (y[-1] - y[0]) / (len(y) - 1)
    return y[-1] + slope * np.arange(1, h + 1)


def mae(actual, predicted):
    return np.mean(np.abs(np.asarray(actual) - np.asarray(predicted)))


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    t = np.arange(200)
    series = 50 + 0.08 * t + 6 * np.sin(2 * np.pi * t / 12) + rng.normal(0, 1.5, 200)

    train, test = series[:-12], series[-12:]
    h = len(test)

    results = {
        "naive": naive_forecast(train, h),
        "seasonal naive": seasonal_naive_forecast(train, 12, h),
        "drift": drift_forecast(train, h),
    }
    for name, forecast in results.items():
        print(f"{name:>16}: MAE = {mae(test, forecast):.2f}")

    # Any model you build must beat the best of these, or it is not earning its cost.
    print(f"\nbar to beat: {min(mae(test, f) for f in results.values()):.2f}")
```

On a series with strong seasonality the seasonal naive forecast is usually far ahead of plain persistence — which is itself a useful diagnostic, because it tells you the seasonal period is real and worth modelling.

## See also

- [Decomposition and Stationarity](./decomposition-and-stationarity.md) — separating trend, seasonality and noise.
- [Validation and Backtesting](./validation-and-backtesting.md) — how to split and evaluate without leaking.
- [Train/Validation/Test Splits](../00-foundations/train-validation-test-splits.md) — the general splitting rules this section specialises.
