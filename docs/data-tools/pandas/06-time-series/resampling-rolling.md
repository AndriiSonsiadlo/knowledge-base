---
id: resampling-rolling
title: Resampling and Rolling Windows
sidebar_label: Resampling & Rolling
tags: [pandas, resampling, rolling, time-series, windows]
---

# Resampling and Rolling Windows

## Overview

Time series analysis often requires:

- **Resampling**: Change frequency (daily → monthly, hourly → daily)
- **Rolling**: Moving window calculations (moving average, rolling sum)
- **Expanding**: Cumulative calculations from the start
- **EWM**: Exponentially weighted moving calculations

## Resampling

Change the frequency of time series data.

### Downsampling (High to Low Frequency)

Aggregate to a lower frequency:

```python title="Downsample to lower frequency"
import pandas as pd
import numpy as np

# Daily data
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=31, freq='D'),
    'value': range(31)
})
df = df.set_index('date')

# Resample to weekly (sum)
weekly = df.resample('W').sum()
#             value
# date             
# 2024-01-07     21  # Sum of first 7 days
# 2024-01-14     77  # Sum of next 7 days
# 2024-01-21    133
# 2024-01-28    189
# 2024-02-04     30  # Last 2 days

# Resample to monthly (mean)
monthly = df.resample('M').mean()
#             value
# date             
# 2024-01-31   15.0  # Average of all January values
```

### Aggregation Functions

```python title="Different aggregation methods"
df = pd.DataFrame({
    'value': range(100)
}, index=pd.date_range('2024-01-01', periods=100, freq='D'))

# Weekly aggregations
weekly_sum = df.resample('W').sum()
weekly_mean = df.resample('W').mean()
weekly_min = df.resample('W').min()
weekly_max = df.resample('W').max()
weekly_count = df.resample('W').count()

# Multiple aggregations
weekly_stats = df.resample('W').agg(['sum', 'mean', 'min', 'max', 'count'])
```

### Upsampling (Low to High Frequency)

Increase frequency (creates missing values):

```python title="Upsample to higher frequency"
# Monthly data
df = pd.DataFrame({
    'value': [100, 200, 150]
}, index=pd.date_range('2024-01-01', periods=3, freq='M'))
#             value
# 2024-01-31    100
# 2024-02-29    200
# 2024-03-31    150

# Upsample to daily
daily = df.resample('D').asfreq()
# Creates daily index, values only on original dates
#             value
# 2024-01-01    NaN
# 2024-01-02    NaN
# ...
# 2024-01-31  100.0
# 2024-02-01    NaN
# ...

# Fill missing values
daily_ffill = df.resample('D').ffill()  # Forward fill
daily_bfill = df.resample('D').bfill()  # Backward fill
daily_interp = df.resample('D').interpolate()  # Interpolate
```

:::info
**Downsampling** aggregates data (many → few). **Upsampling** expands frequency (few → many) and creates NaN values that need to be filled.
:::

### Resampling Frequencies

```python title="Common resampling frequencies"
# Time-based
df.resample('D')      # Daily
df.resample('W')      # Weekly (Sunday)
df.resample('M')      # Month end
df.resample('MS')     # Month start
df.resample('Q')      # Quarter end
df.resample('Y')      # Year end
df.resample('H')      # Hourly
df.resample('T')      # Minutely
df.resample('S')      # Secondly

# Custom periods
df.resample('2D')     # Every 2 days
df.resample('3H')     # Every 3 hours
df.resample('15T')    # Every 15 minutes

# Business days
df.resample('B')      # Business days
df.resample('W-MON')  # Weekly on Monday
```

## Rolling Windows

Calculate statistics over a moving window:

### Basic Rolling

```python title="Simple rolling calculations"
df = pd.DataFrame({
    'value': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
}, index=pd.date_range('2024-01-01', periods=10, freq='D'))

# 3-day moving average
df['ma_3'] = df['value'].rolling(window=3).mean()
#             value  ma_3
# 2024-01-01     10   NaN
# 2024-01-02     20   NaN
# 2024-01-03     30  20.0  # (10+20+30)/3
# 2024-01-04     40  30.0  # (20+30+40)/3
# 2024-01-05     50  40.0
# ...

# 3-day rolling sum
df['sum_3'] = df['value'].rolling(window=3).sum()

# 3-day rolling max
df['max_3'] = df['value'].rolling(window=3).max()
```

### Window Size

```python title="Different window sizes"
df = pd.DataFrame({
    'price': [100, 102, 98, 105, 103, 107, 110, 108, 112, 115]
}, index=pd.date_range('2024-01-01', periods=10))

# Short-term trend (3 periods)
df['sma_3'] = df['price'].rolling(window=3).mean()

# Medium-term trend (5 periods)
df['sma_5'] = df['price'].rolling(window=5).mean()

# Long-term trend (10 periods)
df['sma_10'] = df['price'].rolling(window=10).mean()
```

### Minimum Periods

```python title="Handle incomplete windows"
df = pd.DataFrame({
    'value': [10, 20, 30, 40, 50]
})

# Default: NaN until window is full
df['rolling_3'] = df['value'].rolling(window=3).mean()
# 0    NaN
# 1    NaN
# 2   20.0

# min_periods: calculate with fewer values
df['rolling_min2'] = df['value'].rolling(window=3, min_periods=2).mean()
# 0    NaN
# 1   15.0  # (10+20)/2
# 2   20.0  # (10+20+30)/3
```

### Time-Based Windows

```python title="Rolling by time duration"
df = pd.DataFrame({
    'value': range(100)
}, index=pd.date_range('2024-01-01', periods=100, freq='H'))

# 24-hour rolling average
df['ma_24h'] = df['value'].rolling(window='24H').mean()

# 7-day rolling sum
df['sum_7d'] = df['value'].rolling(window='7D').sum()

# Works with irregular time series
df_irregular = df.sample(frac=0.8)  # 80% of data
df_irregular['ma'] = df_irregular['value'].rolling(window='24H').mean()
```

:::success
Use time-based windows (`window='7D'`) instead of count-based (`window=7`) for irregular time series or when frequency varies.
:::

### Rolling Aggregations

```python title="Multiple rolling statistics"
df = pd.DataFrame({
    'price': np.random.randn(100).cumsum() + 100
}, index=pd.date_range('2024-01-01', periods=100))

# Multiple aggregations
df['mean'] = df['price'].rolling(window=7).mean()
df['std'] = df['price'].rolling(window=7).std()
df['min'] = df['price'].rolling(window=7).min()
df['max'] = df['price'].rolling(window=7).max()

# All at once
rolling_stats = df['price'].rolling(window=7).agg(['mean', 'std', 'min', 'max'])
```

## Expanding Windows

Cumulative calculations from the start:

```python title="Expanding (cumulative) calculations"
df = pd.DataFrame({
    'value': [10, 20, 30, 40, 50]
})

# Expanding mean (cumulative average)
df['expanding_mean'] = df['value'].expanding().mean()
#    value  expanding_mean
# 0     10           10.0  # 10/1
# 1     20           15.0  # (10+20)/2
# 2     30           20.0  # (10+20+30)/3
# 3     40           25.0  # (10+20+30+40)/4
# 4     50           30.0  # All values

# Expanding sum
df['expanding_sum'] = df['value'].expanding().sum()
#    value  expanding_sum
# 0     10           10.0
# 1     20           30.0
# 2     30           60.0
# 3     40          100.0
# 4     50          150.0

# Expanding max (running maximum)
df['running_max'] = df['value'].expanding().max()
```

### Minimum Periods for Expanding

```python title="Start expanding after N periods"
df = pd.DataFrame({
    'value': [10, 20, 30, 40, 50]
})

# Don't calculate until we have at least 3 values
df['expanding_mean'] = df['value'].expanding(min_periods=3).mean()
#    value  expanding_mean
# 0     10             NaN
# 1     20             NaN
# 2     30            20.0  # (10+20+30)/3
# 3     40            25.0  # (10+20+30+40)/4
# 4     50            30.0
```

## Exponentially Weighted Moving (EWM)

Give more weight to recent values:

```python title="Exponentially weighted calculations"
df = pd.DataFrame({
    'price': [100, 102, 98, 105, 103, 107, 110, 108, 112, 115]
})

# EWM with span (like N-period moving average)
df['ewm_5'] = df['price'].ewm(span=5).mean()

# EWM with alpha (smoothing factor)
df['ewm_alpha'] = df['price'].ewm(alpha=0.3).mean()

# EWM with half-life
df['ewm_halflife'] = df['price'].ewm(halflife=3).mean()

# Recent values have more weight than old values
```

### EWM vs Simple Moving Average

```python title="Compare EWM and SMA"
df = pd.DataFrame({
    'value': [10, 10, 10, 10, 50]  # Sudden spike
})

# Simple moving average (equal weights)
df['sma_3'] = df['value'].rolling(window=3).mean()
# 0    NaN
# 1    NaN
# 2   10.0
# 3   10.0
# 4   23.3  # (10+10+50)/3

# EWM (recent values matter more)
df['ewm_3'] = df['value'].ewm(span=3).mean()
# 0   10.0
# 1   10.0
# 2   10.0
# 3   10.0
# 4   30.0  # Reacts faster to change
```

:::info
**EWM** reacts faster to recent changes than simple moving average. Use for trend detection in volatile data.
:::

## Combining Operations

### Resample Then Rolling

```python title="Resample first, then rolling"
# Hourly data
df = pd.DataFrame({
    'value': range(168)  # 1 week of hourly data
}, index=pd.date_range('2024-01-01', periods=168, freq='H'))

# Resample to daily, then 3-day moving average
daily = df.resample('D').mean()
daily['ma_3'] = daily['value'].rolling(window=3).mean()
#              value    ma_3
# 2024-01-01   11.5     NaN
# 2024-01-02   35.5     NaN
# 2024-01-03   59.5   35.5
# 2024-01-04   83.5   59.5
```

### Rolling with Groupby

```python title="Rolling within groups"
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=20).tolist() * 2,
    'category': ['A'] * 20 + ['B'] * 20,
    'value': range(40)
})
df = df.set_index('date')

# Rolling mean per category
df['rolling_mean'] = df.groupby('category')['value'].rolling(window=3).mean().reset_index(0, drop=True)
```

## Common Patterns

### Moving Average Crossover

```python title="Detect trend changes"
df = pd.DataFrame({
    'price': np.random.randn(100).cumsum() + 100
}, index=pd.date_range('2024-01-01', periods=100))

# Short and long moving averages
df['sma_5'] = df['price'].rolling(window=5).mean()
df['sma_20'] = df['price'].rolling(window=20).mean()

# Crossover signal
df['signal'] = np.where(df['sma_5'] > df['sma_20'], 1, -1)
# 1 = bullish (short-term > long-term)
# -1 = bearish (short-term < long-term)

# Detect crossover points
df['crossover'] = df['signal'].diff()
# 2 = bullish crossover (buy signal)
# -2 = bearish crossover (sell signal)
```

### Volatility Calculation

```python title="Rolling standard deviation"
df = pd.DataFrame({
    'price': np.random.randn(100).cumsum() + 100
}, index=pd.date_range('2024-01-01', periods=100))

# Calculate returns
df['returns'] = df['price'].pct_change()

# 20-day rolling volatility (annualized)
df['volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(252)
```

### Seasonal Decomposition

```python title="Weekly and monthly patterns"
df = pd.DataFrame({
    'value': np.random.randn(365).cumsum() + 100
}, index=pd.date_range('2024-01-01', periods=365))

# 7-day moving average (remove weekly noise)
df['weekly_ma'] = df['value'].rolling(window=7, center=True).mean()

# 30-day moving average (monthly trend)
df['monthly_ma'] = df['value'].rolling(window=30, center=True).mean()
```

### YTD Calculations

```python title="Year-to-date aggregations"
df = pd.DataFrame({
    'revenue': np.random.randint(1000, 5000, 365)
}, index=pd.date_range('2024-01-01', periods=365))

# Year-to-date sum
df['ytd_revenue'] = df.groupby(df.index.year)['revenue'].cumsum()

# Or using expanding with groupby
df['ytd_revenue'] = df.groupby(df.index.year)['revenue'].expanding().sum().reset_index(0, drop=True)
```

### Gap Detection

```python title="Find data gaps in time series"
df = pd.DataFrame({
    'value': range(10)
}, index=pd.to_datetime([
    '2024-01-01', '2024-01-02', '2024-01-03',
    '2024-01-10',  # Gap!
    '2024-01-11', '2024-01-12',
    '2024-01-20',  # Gap!
    '2024-01-21', '2024-01-22', '2024-01-23'
]))

# Calculate time difference
df['gap'] = df.index.to_series().diff()

# Find gaps > 1 day
gaps = df[df['gap'] > pd.Timedelta(days=1)]
```

## Advanced Techniques

### Custom Rolling Functions

```python title="Apply custom functions"
df = pd.DataFrame({
    'value': range(10)
})

# Custom function: range (max - min)
def range_calc(x):
    return x.max() - x.min()

df['rolling_range'] = df['value'].rolling(window=3).apply(range_calc)

# Custom function with arguments
def percentile(x, q):
    return x.quantile(q)

df['rolling_75th'] = df['value'].rolling(window=5).apply(
    lambda x: percentile(x, 0.75)
)
```

### Centered Windows

```python title="Center the window around each point"
df = pd.DataFrame({
    'value': [10, 20, 30, 40, 50]
})

# Default: window looks backward
df['rolling_back'] = df['value'].rolling(window=3).mean()
#    value  rolling_back
# 0     10           NaN
# 1     20           NaN
# 2     30          20.0  # (10+20+30)/3

# Centered: window around current point
df['rolling_center'] = df['value'].rolling(window=3, center=True).mean()
#    value  rolling_center
# 0     10             NaN
# 1     20            20.0  # (10+20+30)/3
# 2     30            30.0  # (20+30+40)/3
# 3     40            40.0  # (30+40+50)/3
# 4     50             NaN
```

### Multiple Columns Rolling

```python title="Rolling on multiple columns"
df = pd.DataFrame({
    'price': [100, 102, 98, 105, 103],
    'volume': [1000, 1200, 900, 1500, 1100]
})

# Apply rolling to multiple columns
rolling_stats = df[['price', 'volume']].rolling(window=3).mean()
#    price   volume
# 0    NaN      NaN
# 1    NaN      NaN
# 2  100.0   1033.3
# 3  101.7   1200.0
# 4  102.0   1166.7
```

## Performance Tips

```python title="Optimize rolling operations"
# Use numba engine for custom functions (faster)
df['rolling'] = df['value'].rolling(window=10).apply(
    custom_func,
    engine='numba',
    raw=True
)

# For large datasets, resample first
# Slow: rolling on hourly data
hourly_ma = df.rolling(window=168).mean()  # 168 hours = 1 week

# Faster: resample to daily first
daily = df.resample('D').mean()
daily_ma = daily.rolling(window=7).mean()

# Use built-in functions (faster than apply)
df['mean'] = df['value'].rolling(window=10).mean()  # Fast
# vs
df['mean'] = df['value'].rolling(window=10).apply(np.mean)  # Slower
```

:::warning
For large datasets with long rolling windows, consider resampling to lower frequency first. Rolling on 1 million hourly points with 7-day window is much slower than rolling on daily aggregated data.
:::

## Quick Reference

**Resampling:**

```python
df.resample('D').sum()               # Daily sum
df.resample('W').mean()              # Weekly average
df.resample('M').last()              # Last value per month
df.resample('H').ffill()             # Upsample and forward fill
df.resample('2D').agg(['sum', 'mean'])  # Multiple aggregations
```

**Rolling:**

```python
df['col'].rolling(window=7).mean()   # 7-period moving average
df['col'].rolling(window='7D').sum() # 7-day rolling sum
df['col'].rolling(window=7, min_periods=3).mean()  # Min 3 values
df['col'].rolling(window=7, center=True).mean()    # Centered window
```

**Expanding:**

```python
df['col'].expanding().mean()         # Cumulative average
df['col'].expanding().sum()          # Running total
df['col'].expanding(min_periods=3).std()  # Start after 3 values
```

**Exponentially weighted:**

```python
df['col'].ewm(span=10).mean()        # EWM with span
df['col'].ewm(alpha=0.3).mean()      # EWM with alpha
df['col'].ewm(halflife=5).mean()     # EWM with half-life
```

**Common patterns:**

```python
# Moving average
df['ma'] = df['price'].rolling(window=20).mean()

# Volatility
df['vol'] = df['returns'].rolling(window=20).std()

# YTD sum
df['ytd'] = df.groupby(df.index.year)['value'].cumsum()

# Resample then roll
df.resample('D').mean().rolling(window=7).mean()
```

**Frequencies:**

```python
'D' - Day, 'W' - Week, 'M' - Month end, 'MS' - Month start
'Q' - Quarter, 'Y' - Year, 'H' - Hour, 'T' - Minute, 'S' - Second
'B' - Business day, '2D' - Every 2 days, '3H' - Every 3 hours
```
