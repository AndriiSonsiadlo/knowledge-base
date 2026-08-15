---
id: classical-forecasting-models
title: Classical Forecasting Models
sidebar_label: Classical Models
sidebar_position: 3
tags: [time-series, arima, exponential-smoothing, forecasting]
---

# Classical Forecasting Models

Exponential smoothing and ARIMA predate machine learning by decades and still win a great many forecasting competitions — particularly on short, clean, single series where a gradient-boosted model has nothing to learn from.

:::info[Key idea]
Exponential smoothing forecasts from weighted averages of past *values*, with weights decaying geometrically. ARIMA forecasts from past values **and past errors**, after differencing to stationarity. On short univariate series these remain extremely hard to beat.
:::

## Exponential smoothing

### Simple (no trend, no seasonality)

$$
\hat{y}_{t+1} = \alpha y_t + (1 - \alpha)\hat{y}_t
$$

Every forecast is a weighted average of the last observation and the previous forecast. Unrolling shows the weight on an observation $k$ steps back is $\alpha(1-\alpha)^k$ — geometric decay, so the whole history contributes but the recent past dominates.

$\alpha$ controls the trade directly: near 1 the model tracks noise, near 0 it barely responds to real change. It is fitted by minimising in-sample squared error rather than chosen by hand.

### Holt and Holt–Winters

| Model | Adds | Components tracked |
|---|---|---|
| Simple | — | level |
| **Holt's linear** | Trend | level, trend |
| **Holt–Winters** | Seasonality | level, trend, seasonal |

Holt–Winters keeps a separate smoothing parameter for each component ($\alpha$, $\beta$, $\gamma$) and comes in additive and multiplicative seasonal forms — the same choice discussed in [Decomposition and Stationarity](./decomposition-and-stationarity.md).

:::tip[Damped trend is almost always better]
Holt's linear trend extrapolates the current slope forever, which over long horizons produces absurd forecasts. The *damped* variant multiplies the trend by $\phi < 1$ at each step so it flattens out. Empirically the damped version beats the undamped one so consistently that it is a reasonable default.
:::

## ARIMA

**ARIMA(p, d, q)** has three integer parameters:

| Symbol | Name | Meaning |
|---|---|---|
| **p** | AutoRegressive | How many past *values* enter the equation |
| **d** | Integrated | How many times the series was differenced |
| **q** | Moving Average | How many past *errors* enter the equation |

$$
y'_t = c + \underbrace{\phi_1 y'_{t-1} + \dots + \phi_p y'_{t-p}}_{\text{AR: past values}} + \underbrace{\theta_1 \varepsilon_{t-1} + \dots + \theta_q \varepsilon_{t-q}}_{\text{MA: past errors}} + \varepsilon_t
$$

where $y'$ is the series after $d$ differences.

The MA part is the less intuitive half. It says: when the model was wrong last period, part of that error carries forward. This is what lets ARIMA absorb one-off shocks that an AR model would either ignore or over-react to.

**SARIMA(p, d, q)(P, D, Q)ₘ** adds the same three terms again at the seasonal lag $m$ — so a monthly series with annual seasonality uses $m = 12$ and gets terms at lags 12, 24, and so on.

### Choosing the orders

Two routes, and in practice you use both:

1. **Read the ACF/PACF**, following the identification table in [Decomposition and Stationarity](./decomposition-and-stationarity.md).
2. **Search and score** with AIC or BIC, which is what `auto_arima` and `statsmodels` do. AIC tends to pick slightly larger models; BIC penalises parameters harder and is the safer choice when you care about forecasting rather than fit.

Compare information criteria only across models fitted to the **same** $d$. Differencing changes the data being modelled, so the likelihoods are not comparable across different $d$ — a genuinely common and silent mistake.

## Which to reach for

| Situation | Model |
|---|---|
| Short series (< 50 points) | Exponential smoothing |
| Clear trend and fixed seasonality | Holt–Winters, or SARIMA |
| Need interpretable coefficients | ARIMA |
| Need external drivers (price, weather, promotions) | SARIMAX, or move to [ML approaches](./machine-learning-for-forecasting.md) |
| Many related series | [ML approaches](./machine-learning-for-forecasting.md) — classical models fit each series alone |
| Multiple seasonalities (daily *and* weekly *and* yearly) | Prophet, TBATS, or ML with calendar features |

That last row is a real limitation: ARIMA handles one seasonal period. Hourly electricity demand has daily, weekly and annual cycles simultaneously, and SARIMA cannot represent all three.

## Prophet, briefly

Prophet fits a decomposable model — trend + seasonality + holidays — as a curve-fitting problem rather than a stochastic process. It handles multiple seasonalities and missing data, needs almost no tuning, and is genuinely useful for business series with strong calendar effects.

It is also frequently beaten by a well-tuned seasonal naive baseline, and its confidence intervals are known to be poorly calibrated. Treat it as a strong, convenient baseline rather than a finishing move.

## Code: exponential smoothing and AR from scratch

```python title="classical_forecasting.py"
import numpy as np


def simple_exponential_smoothing(y, alpha):
    """Returns the fitted one-step-ahead forecasts."""
    fitted = np.empty(len(y))
    fitted[0] = y[0]
    for t in range(1, len(y)):
        fitted[t] = alpha * y[t - 1] + (1 - alpha) * fitted[t - 1]
    return fitted


def holt_linear(y, alpha, beta, damping=1.0):
    """Holt's linear trend, with optional damping (phi < 1 flattens the trend)."""
    level, trend = y[0], y[1] - y[0]
    fitted = np.empty(len(y))
    fitted[0] = level
    for t in range(1, len(y)):
        fitted[t] = level + damping * trend
        prev_level = level
        level = alpha * y[t] + (1 - alpha) * (level + damping * trend)
        trend = beta * (level - prev_level) + (1 - beta) * damping * trend
    return fitted, level, trend


def holt_forecast(level, trend, h, damping=1.0):
    """h-step forecast. With damping the trend contribution converges."""
    return np.array([level + trend * sum(damping ** j for j in range(1, i + 1))
                     for i in range(1, h + 1)])


def fit_ar(y, p):
    """AR(p) by ordinary least squares on lagged columns."""
    X = np.column_stack([y[p - i - 1:len(y) - i - 1] for i in range(p)])
    X = np.column_stack([np.ones(len(X)), X])
    target = y[p:]
    coefs, *_ = np.linalg.lstsq(X, target, rcond=None)
    return coefs


def forecast_ar(y, coefs, h):
    p = len(coefs) - 1
    history = list(y)
    out = []
    for _ in range(h):
        window = [history[-i - 1] for i in range(p)]
        nxt = coefs[0] + np.dot(coefs[1:], window)
        history.append(nxt)
        out.append(nxt)
    return np.array(out)


if __name__ == "__main__":
    rng = np.random.default_rng(3)
    t = np.arange(150)
    y = 40 + 0.25 * t + rng.normal(0, 2.0, 150)
    train, test = y[:-10], y[-10:]

    def mae(a, b):
        return np.mean(np.abs(np.asarray(a) - np.asarray(b)))

    # Naive baseline, first — always.
    print(f"{'naive':>26}: MAE {mae(test, np.repeat(train[-1], 10)):.2f}")

    _, level, trend = holt_linear(train, alpha=0.6, beta=0.15)
    print(f"{'Holt (undamped)':>26}: MAE {mae(test, holt_forecast(level, trend, 10)):.2f}")
    print(f"{'Holt (damped, phi=0.9)':>26}: MAE "
          f"{mae(test, holt_forecast(level, trend, 10, damping=0.9)):.2f}")

    coefs = fit_ar(train, p=3)
    print(f"{'AR(3)':>26}: MAE {mae(test, forecast_ar(train, coefs, 10)):.2f}")
```

On a trending series Holt beats persistence comfortably, because persistence has no mechanism for extrapolating a slope at all — which is precisely the gap the trend component exists to fill.

## See also

- [Decomposition and Stationarity](./decomposition-and-stationarity.md) — the differencing and ACF reading these models depend on.
- [Machine Learning for Forecasting](./machine-learning-for-forecasting.md) — when tree ensembles and neural nets overtake these.
- [Validation and Backtesting](./validation-and-backtesting.md) — evaluating any of them honestly.
