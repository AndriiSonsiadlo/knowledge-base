---
id: aggregation-functions
title: Aggregation Functions
sidebar_label: Aggregation Functions
tags: [pandas, aggregation, groupby, agg, statistics]
---

# Aggregation Functions

## Overview

Aggregation combines multiple values into a single summary value. Common operations include sum, mean, count, min, max, and custom aggregations.

## Basic Aggregations

### Single Column Aggregation

```python title="Basic aggregation methods"
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'values': [10, 20, 30, 40, 50]
})

# Common aggregations
df['values'].sum()        # 150
df['values'].mean()       # 30.0
df['values'].median()     # 30.0
df['values'].std()        # 15.81
df['values'].var()        # 250.0
df['values'].min()        # 10
df['values'].max()        # 50
df['values'].count()      # 5
df['values'].nunique()    # 5 (unique values)
```

### DataFrame-Wide Aggregation

```python title="Aggregate entire DataFrame"
df = pd.DataFrame({
    'A': [1, 2, 3, 4],
    'B': [5, 6, 7, 8],
    'C': [9, 10, 11, 12]
})

# Sum of each column
df.sum()
# A    10
# B    26
# C    42

# Sum of each row
df.sum(axis=1)
# 0    15
# 1    18
# 2    21
# 3    24

# Multiple statistics
df.describe()
#          A    B     C
# count  4.0  4.0   4.0
# mean   2.5  6.5  10.5
# std    1.3  1.3   1.3
# min    1.0  5.0   9.0
# 25%    1.8  5.8   9.8
# 50%    2.5  6.5  10.5
# 75%    3.2  7.2  11.2
# max    4.0  8.0  12.0
```

## agg() Method

Apply one or more aggregations:

### Single Aggregation

```python title="Use agg() for aggregation"
df = pd.DataFrame({
    'values': [10, 20, 30, 40, 50]
})

# Single aggregation
df['values'].agg('sum')    # 150
df['values'].agg('mean')   # 30.0

# Built-in function
df['values'].agg(np.sum)   # 150
```

### Multiple Aggregations

```python title="Multiple aggregations on one column"
df = pd.DataFrame({
    'sales': [100, 200, 150, 300, 250]
})

# Multiple aggregations
result = df['sales'].agg(['sum', 'mean', 'std', 'min', 'max'])
# sum     1000.00
# mean     200.00
# std       79.06
# min      100.00
# max      300.00

# Custom names
result = df['sales'].agg([
    ('total', 'sum'),
    ('average', 'mean'),
    ('spread', 'std')
])
# total       1000.00
# average      200.00
# spread        79.06
```

### Different Aggregations per Column

```python title="Different functions for different columns"
df = pd.DataFrame({
    'product': ['A', 'B', 'A', 'B'],
    'quantity': [10, 20, 15, 25],
    'price': [100, 200, 150, 250]
})

# Different aggregation for each column
result = df.agg({
    'quantity': 'sum',
    'price': 'mean'
})
# quantity     70.0
# price       175.0

# Multiple aggregations per column
result = df.agg({
    'quantity': ['sum', 'mean'],
    'price': ['min', 'max']
})
#       quantity  price
# sum       70.0    NaN
# mean      17.5    NaN
# min        NaN  100.0
# max        NaN  250.0
```

## Custom Aggregation Functions

### Lambda Functions

```python title="Custom aggregation with lambda"
df = pd.DataFrame({
    'values': [10, 20, 30, 40, 50]
})

# Range (max - min)
df['values'].agg(lambda x: x.max() - x.min())  # 40

# Custom calculation
df['values'].agg(lambda x: x.sum() / len(x) * 2)  # 60.0
```

### Named Functions

```python title="Define custom aggregation functions"
def range_func(x):
    """Calculate range (max - min)"""
    return x.max() - x.min()

def custom_metric(x):
    """Custom business metric"""
    return x.sum() / x.count() * 1.1

df = pd.DataFrame({
    'values': [10, 20, 30, 40, 50]
})

# Use custom functions
df['values'].agg(range_func)        # 40
df['values'].agg(custom_metric)     # 33.0

# Multiple custom functions
df['values'].agg([range_func, custom_metric, 'mean'])
# range_func       40.0
# custom_metric    33.0
# mean             30.0
```

## Statistical Aggregations

### Descriptive Statistics

```python title="Statistical measures"
df = pd.DataFrame({
    'values': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
})

# Central tendency
df['values'].mean()        # 55.0
df['values'].median()      # 55.0
df['values'].mode()[0]     # First mode if multiple

# Dispersion
df['values'].std()         # 30.28 (sample std)
df['values'].var()         # 916.67 (sample variance)
df['values'].sem()         # Standard error of mean
df['values'].mad()         # Mean absolute deviation

# Distribution
df['values'].skew()        # Skewness
df['values'].kurt()        # Kurtosis

# Quantiles
df['values'].quantile(0.25)  # 25th percentile: 32.5
df['values'].quantile(0.75)  # 75th percentile: 77.5
df['values'].quantile([0.25, 0.5, 0.75])
```

### Cumulative Aggregations

```python title="Cumulative operations"
df = pd.DataFrame({
    'values': [10, 20, 30, 40, 50]
})

# Cumulative sum
df['cumsum'] = df['values'].cumsum()
#    values  cumsum
# 0      10      10
# 1      20      30
# 2      30      60
# 3      40     100
# 4      50     150

# Cumulative product
df['cumprod'] = df['values'].cumprod()

# Cumulative max/min
df['cummax'] = df['values'].cummax()
df['cummin'] = df['values'].cummin()
```

## Handling Missing Values

### Aggregation with NaN

```python title="NaN handling in aggregations"
df = pd.DataFrame({
    'values': [10, 20, np.nan, 40, 50]
})

# Default: skip NaN
df['values'].sum()      # 120.0 (ignores NaN)
df['values'].mean()     # 30.0

# Count non-NaN values
df['values'].count()    # 4

# Include NaN in count
len(df['values'])       # 5

# Minimum with NaN
df['values'].min()      # 10.0 (NaN ignored)

# Skip NaN parameter
df['values'].sum(skipna=True)   # 120.0 (default)
df['values'].sum(skipna=False)  # NaN
```

:::warning
Most aggregation functions skip NaN by default. Use `skipna=False` to propagate NaN values.
:::

## Conditional Aggregations

### Filter Then Aggregate

```python title="Aggregate with conditions"
df = pd.DataFrame({
    'category': ['A', 'B', 'A', 'B', 'A'],
    'value': [10, 20, 30, 40, 50]
})

# Sum only category A
df[df['category'] == 'A']['value'].sum()  # 90

# Mean of values > 25
df[df['value'] > 25]['value'].mean()  # 40.0

# Count by condition
(df['value'] > 25).sum()  # 3 (True counts as 1)
```

### Using np.where()

```python title="Conditional aggregation with np.where"
df = pd.DataFrame({
    'sales': [100, 200, 150, 300, 250]
})

# Sum of sales over 150
np.where(df['sales'] > 150, df['sales'], 0).sum()  # 750

# Count values in range
((df['sales'] >= 150) & (df['sales'] <= 250)).sum()  # 2
```

## Window Functions

### Rolling Aggregations

```python title="Moving window aggregations"
df = pd.DataFrame({
    'value': [10, 20, 30, 40, 50, 60]
})

# 3-period moving average
df['ma_3'] = df['value'].rolling(window=3).mean()
#    value   ma_3
# 0     10    NaN
# 1     20    NaN
# 2     30   20.0  # (10+20+30)/3
# 3     40   30.0  # (20+30+40)/3
# 4     50   40.0
# 5     60   50.0

# Rolling sum
df['rolling_sum'] = df['value'].rolling(window=3).sum()

# Multiple rolling aggregations
df['rolling_stats'] = df['value'].rolling(window=3).agg(['mean', 'std', 'min', 'max'])
```

### Expanding Aggregations

```python title="Cumulative expanding window"
df = pd.DataFrame({
    'value': [10, 20, 30, 40, 50]
})

# Expanding mean (cumulative average)
df['expanding_mean'] = df['value'].expanding().mean()
#    value  expanding_mean
# 0     10            10.0
# 1     20            15.0  # (10+20)/2
# 2     30            20.0  # (10+20+30)/3
# 3     40            25.0  # (10+20+30+40)/4
# 4     50            30.0  # All values

# Expanding sum
df['expanding_sum'] = df['value'].expanding().sum()
```

## Weighted Aggregations

### Weighted Average

```python title="Calculate weighted average"
df = pd.DataFrame({
    'value': [90, 85, 95],
    'weight': [0.3, 0.5, 0.2]
})

# Weighted average
weighted_avg = (df['value'] * df['weight']).sum() / df['weight'].sum()
# 87.5

# Or using np.average
weighted_avg = np.average(df['value'], weights=df['weight'])
# 87.5
```

## Aggregation with Multiple Columns

### Cross-Column Aggregations

```python title="Aggregate across columns"
df = pd.DataFrame({
    'q1': [100, 200, 150],
    'q2': [120, 180, 160],
    'q3': [110, 220, 170],
    'q4': [130, 210, 180]
})

# Row-wise sum
df['total'] = df[['q1', 'q2', 'q3', 'q4']].sum(axis=1)
#     q1   q2   q3   q4  total
# 0  100  120  110  130    460
# 1  200  180  220  210    810
# 2  150  160  170  180    660

# Row-wise mean
df['average'] = df[['q1', 'q2', 'q3', 'q4']].mean(axis=1)

# Row-wise max
df['best_quarter'] = df[['q1', 'q2', 'q3', 'q4']].max(axis=1)
```

## Performance Tips

### Vectorized Operations

```python title="Use vectorized operations"
df = pd.DataFrame({
    'value': range(1000000)
})

# Slow: apply with aggregation
# result = df['value'].apply(lambda x: x * 2).sum()

# Fast: vectorized
result = (df['value'] * 2).sum()

# Slow: loop aggregation
# total = 0
# for val in df['value']:
#     total += val

# Fast: built-in aggregation
total = df['value'].sum()
```

:::success
Always use built-in aggregation methods (sum, mean, etc.) instead of apply() or loops. They're optimized and much faster.
:::

### Efficient Multiple Aggregations

```python title="Optimize multiple aggregations"
df = pd.DataFrame({
    'values': range(10000)
})

# Less efficient: multiple passes
sum_val = df['values'].sum()
mean_val = df['values'].mean()
std_val = df['values'].std()

# More efficient: single pass with agg
stats = df['values'].agg(['sum', 'mean', 'std'])
sum_val = stats['sum']
mean_val = stats['mean']
std_val = stats['std']
```

## Common Aggregation Patterns

### Top N Summary

```python title="Aggregate top N values"
df = pd.DataFrame({
    'product': list('ABCDEFGH'),
    'sales': [100, 250, 150, 300, 200, 180, 220, 270]
})

# Top 3 products
top3 = df.nlargest(3, 'sales')

# Top 3 total sales
top3_total = df.nlargest(3, 'sales')['sales'].sum()  # 820

# Top 50% of sales
threshold = df['sales'].quantile(0.5)
top_half = df[df['sales'] >= threshold]['sales'].sum()
```

### Percentage Calculations

```python title="Calculate percentages"
df = pd.DataFrame({
    'category': ['A', 'B', 'C', 'D'],
    'value': [100, 200, 150, 50]
})

# Percentage of total
total = df['value'].sum()
df['percentage'] = (df['value'] / total * 100).round(2)
#   category  value  percentage
# 0        A    100       20.00
# 1        B    200       40.00
# 2        C    150       30.00
# 3        D     50       10.00

# Cumulative percentage
df['cumulative_pct'] = (df['value'].cumsum() / total * 100).round(2)
```

### Binned Aggregations

```python title="Aggregate by bins"
df = pd.DataFrame({
    'age': [15, 25, 35, 45, 55, 65, 75],
    'income': [20000, 35000, 50000, 65000, 70000, 45000, 30000]
})

# Create age groups
df['age_group'] = pd.cut(df['age'], bins=[0, 30, 50, 100])

# Aggregate by age group
df.groupby('age_group')['income'].agg(['mean', 'count'])
#               mean  count
# age_group                
# (0, 30]     27500      2
# (30, 50]    57500      2
# (50, 100]   48333      3
```

## String Aggregations

### Joining Strings

```python title="Aggregate text data"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B'],
    'item': ['apple', 'banana', 'carrot', 'date']
})

# Join strings
df.groupby('category')['item'].agg(lambda x: ', '.join(x))
# category
# A    apple, banana
# B    carrot, date

# Or using transform
df.groupby('category')['item'].transform(lambda x: ', '.join(x))
```

### First/Last Values

```python title="Get first or last values"
df = pd.DataFrame({
    'id': [1, 1, 2, 2],
    'value': [10, 20, 30, 40]
})

# First value per group
df.groupby('id')['value'].first()
# id
# 1    10
# 2    30

# Last value per group
df.groupby('id')['value'].last()
# id
# 1    20
# 2    40
```

## Common Mistakes

### Forgetting axis Parameter

```python title="Axis confusion in aggregations"
df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6]
})

# Sum columns (axis=0, default)
df.sum()
# A     6
# B    15

# Sum rows (axis=1)
df.sum(axis=1)
# 0    5
# 1    7
# 2    9

# Remember: axis=0 goes down, axis=1 goes across
```

### NaN Propagation

```python title="Understanding NaN in aggregations"
df = pd.DataFrame({
    'values': [10, 20, np.nan, 40]
})

# Default: skip NaN
df['values'].sum()  # 70.0

# This propagates NaN
df['values'].sum(skipna=False)  # NaN

# Product with NaN
df['values'].prod()  # 8000.0 (skips NaN)
df['values'].prod(skipna=False)  # NaN
```

## Quick Reference

**Basic aggregations:**

```python
df['col'].sum()                     # Total
df['col'].mean()                    # Average
df['col'].median()                  # Median
df['col'].std()                     # Standard deviation
df['col'].min()                     # Minimum
df['col'].max()                     # Maximum
df['col'].count()                   # Count non-NaN
df['col'].nunique()                 # Unique count
```

**Multiple aggregations:**

```python
df['col'].agg(['sum', 'mean', 'std'])
df.agg({'col1': 'sum', 'col2': 'mean'})
df['col'].agg([('total', 'sum'), ('avg', 'mean')])
```

**Custom aggregations:**

```python
df['col'].agg(lambda x: x.max() - x.min())
df['col'].agg(custom_function)
```

**Conditional:**

```python
df[df['col'] > 10]['col'].sum()
df['col'].where(df['col'] > 10).sum()
```

**Rolling:**

```python
df['col'].rolling(window=3).mean()
df['col'].expanding().sum()
df['col'].cumsum()
```

**Statistics:**

```python
df.describe()                       # Summary statistics
df['col'].quantile(0.75)           # 75th percentile
df['col'].value_counts()           # Frequency counts
```

**Common patterns:**

```python
# Percentage of total
df['pct'] = df['col'] / df['col'].sum() * 100

# Top N total
df.nlargest(5, 'col')['col'].sum()

# Weighted average
np.average(df['value'], weights=df['weight'])

# Row-wise aggregation
df[['col1', 'col2']].sum(axis=1)
```
