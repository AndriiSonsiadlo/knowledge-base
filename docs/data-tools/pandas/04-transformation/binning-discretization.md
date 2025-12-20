---
id: binning-categorical
title: Binning and Categorical Data
sidebar_label: Binning & Categorical
tags: [pandas, binning, categorical, discretization]
---

# Binning and Categorical Data

## Overview

**Binning** converts continuous data into discrete intervals (bins). **Categorical data** represents discrete categories with limited unique values. Both are essential for analysis and visualization.

## Binning Continuous Data

### cut() - Equal-Width Bins

Divide data into bins of equal width:

```python title="Create equal-width bins"
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'age': [5, 15, 25, 35, 45, 55, 65, 75]
})

# Create 4 equal-width bins
df['age_group'] = pd.cut(df['age'], bins=4)
#    age       age_group
# 0    5   (4.93, 22.5]
# 1   15   (4.93, 22.5]
# 2   25  (22.5, 40.0]
# 3   35  (22.5, 40.0]
# 4   45  (40.0, 57.5]
# 5   55  (40.0, 57.5]
# 6   65  (57.5, 75.0]
# 7   75  (57.5, 75.0]

# With custom labels
df['age_group'] = pd.cut(
    df['age'],
    bins=4,
    labels=['Child', 'Adult', 'Middle-aged', 'Senior']
)
#    age   age_group
# 0    5       Child
# 1   15       Child
# 2   25       Adult
# 3   35       Adult
# 4   45  Middle-aged
# 5   55  Middle-aged
# 6   65      Senior
# 7   75      Senior
```

### Custom Bin Edges

```python title="Define specific bin boundaries"
df = pd.DataFrame({
    'age': [5, 15, 25, 35, 45, 55, 65, 75]
})

# Specify exact bin edges
bins = [0, 18, 35, 60, 100]
labels = ['Child', 'Young Adult', 'Adult', 'Senior']

df['age_group'] = pd.cut(df['age'], bins=bins, labels=labels)
#    age    age_group
# 0    5        Child
# 1   15        Child
# 2   25  Young Adult
# 3   35  Young Adult
# 4   45        Adult
# 5   55        Adult
# 6   65       Senior
# 7   75       Senior
```

:::info
Intervals are **right-inclusive** by default: (0, 18] means 0 < x ≤ 18. Use `right=False` for left-inclusive.
:::

### Include Edge Cases

```python title="Handle values at boundaries"
df = pd.DataFrame({
    'value': [0, 25, 50, 75, 100]
})

# Right-inclusive (default)
pd.cut(df['value'], bins=[0, 50, 100])
# 0         NaN  # 0 not included!
# 1    (0, 50]
# 2    (0, 50]
# 3   (50, 100]
# 4   (50, 100]

# Include lowest value
pd.cut(df['value'], bins=[0, 50, 100], include_lowest=True)
# 0    [0, 50]   # Now 0 is included
# 1    (0, 50]
# 2    (0, 50]
# 3   (50, 100]
# 4   (50, 100]
```

### qcut() - Equal-Frequency Bins

Create bins with approximately equal number of observations:

```python title="Create quantile-based bins"
df = pd.DataFrame({
    'income': [20000, 25000, 30000, 35000, 40000, 
               50000, 60000, 80000, 100000, 150000]
})

# 4 bins with equal counts
df['income_quartile'] = pd.qcut(df['income'], q=4)
#     income income_quartile
# 0    20000  [20000, 32500]
# 1    25000  [20000, 32500]
# 2    30000  [20000, 32500]
# 3    35000  (32500, 45000]
# 4    40000  (32500, 45000]
# 5    50000  (45000, 70000]
# 6    60000  (45000, 70000]
# 7    80000  (70000, 150000]
# 8   100000  (70000, 150000]
# 9   150000  (70000, 150000]

# With labels
df['income_quartile'] = pd.qcut(
    df['income'],
    q=4,
    labels=['Q1', 'Q2', 'Q3', 'Q4']
)
```

:::success
Use `qcut()` when you want balanced groups. Use `cut()` when bin boundaries are meaningful (e.g., age groups).
:::

### Percentile-Based Bins

```python title="Bin by specific percentiles"
df = pd.DataFrame({
    'score': np.random.randint(0, 100, 100)
})

# Create bins at 25th, 50th, 75th percentiles
df['score_group'] = pd.qcut(
    df['score'],
    q=[0, 0.25, 0.5, 0.75, 1.0],
    labels=['Bottom 25%', 'Lower-middle', 'Upper-middle', 'Top 25%']
)

# Count per group
df['score_group'].value_counts()
```

## Working with Categorical Data

### Creating Categories

```python title="Create categorical dtype"
df = pd.DataFrame({
    'color': ['red', 'blue', 'red', 'green', 'blue']
})

# Convert to categorical
df['color'] = df['color'].astype('category')
df['color'].dtype
# CategoricalDtype(categories=['blue', 'green', 'red'], ordered=False)

# Create with specific categories
df['color'] = pd.Categorical(
    df['color'],
    categories=['red', 'blue', 'green', 'yellow'],  # yellow not in data
    ordered=False
)
```

### Ordered Categories

```python title="Create ordered categorical"
df = pd.DataFrame({
    'size': ['M', 'L', 'S', 'M', 'S', 'L']
})

# Create ordered categories
df['size'] = pd.Categorical(
    df['size'],
    categories=['S', 'M', 'L'],
    ordered=True
)

# Now comparisons work
df[df['size'] > 'S']  # Returns M and L
#   size
# 0    M
# 1    L
# 3    M
# 5    L
```

:::info
Ordered categoricals enable meaningful comparisons (\>, \<, \>=, \<=). Useful for ordinal data like ratings, sizes, or education levels.
:::

### Categorical Properties

```python title="Access categorical information"
df = pd.DataFrame({
    'grade': pd.Categorical(['A', 'B', 'A', 'C', 'B'],
                            categories=['A', 'B', 'C', 'D'],
                            ordered=True)
})

# View categories
df['grade'].cat.categories
# Index(['A', 'B', 'C', 'D'], dtype='object')

# Check if ordered
df['grade'].cat.ordered  # True

# Get codes (integer representation)
df['grade'].cat.codes
# 0    0  # A
# 1    1  # B
# 2    0  # A
# 3    2  # C
# 4    1  # B

# Count per category (including unused)
df['grade'].value_counts()
# A    2
# B    2
# C    1
# D    0  # Unused category still shown
```

### Add/Remove Categories

```python title="Modify categories"
df = pd.DataFrame({
    'status': pd.Categorical(['active', 'pending', 'active'])
})

# Add new category
df['status'] = df['status'].cat.add_categories(['archived'])
df['status'].cat.categories
# Index(['active', 'pending', 'archived'], dtype='object')

# Remove unused categories
df['status'] = df['status'].cat.remove_unused_categories()

# Remove specific category
df['status'] = df['status'].cat.remove_categories(['archived'])

# Rename categories
df['status'] = df['status'].cat.rename_categories({
    'active': 'Active',
    'pending': 'Pending'
})
```

### Reorder Categories

```python title="Change category order"
df = pd.DataFrame({
    'priority': pd.Categorical(['high', 'low', 'medium', 'low'],
                               ordered=True)
})

# Reorder categories
df['priority'] = df['priority'].cat.reorder_categories(
    ['low', 'medium', 'high'],
    ordered=True
)

# Now sorting works as expected
df.sort_values('priority')
#   priority
# 1      low
# 3      low
# 2   medium
# 0     high
```

## Memory Benefits

### Categorical vs Object

```python title="Memory savings with categorical"
df = pd.DataFrame({
    'status': ['active'] * 1000 + ['inactive'] * 1000
})

# As object (string)
df['status'].memory_usage(deep=True)
# ~112000 bytes

# As categorical
df['status'] = df['status'].astype('category')
df['status'].memory_usage(deep=True)
# ~2000 bytes (98% reduction!)
```

:::success
Convert to categorical when:

- Column has \<50% unique values
- Values repeat frequently
- Need to save memory
- Want to preserve unused categories

  :::

## Binning Strategies

### Age Groups

```python title="Common age binning"
df = pd.DataFrame({
    'age': [5, 12, 18, 25, 35, 45, 55, 65, 75]
})

# Standard age groups
bins = [0, 18, 35, 50, 65, 100]
labels = ['Child', 'Young Adult', 'Adult', 'Middle-aged', 'Senior']
df['age_group'] = pd.cut(df['age'], bins=bins, labels=labels)

# Or generations
bins = [0, 25, 40, 56, 75, 100]
labels = ['Gen Z', 'Millennial', 'Gen X', 'Boomer', 'Silent']
df['generation'] = pd.cut(df['age'], bins=bins, labels=labels)
```

### Income Brackets

```python title="Income binning"
df = pd.DataFrame({
    'income': [25000, 35000, 50000, 75000, 125000, 250000]
})

# Income brackets
bins = [0, 30000, 60000, 100000, 200000, np.inf]
labels = ['Low', 'Lower-middle', 'Middle', 'Upper-middle', 'High']
df['income_bracket'] = pd.cut(df['income'], bins=bins, labels=labels)
```

### Grade Ranges

```python title="Score to grade conversion"
df = pd.DataFrame({
    'score': [95, 85, 75, 65, 55, 45]
})

# Letter grades
bins = [0, 60, 70, 80, 90, 100]
labels = ['F', 'D', 'C', 'B', 'A']
df['grade'] = pd.cut(
    df['score'],
    bins=bins,
    labels=labels,
    include_lowest=True
)
#    score grade
# 0     95     A
# 1     85     B
# 2     75     C
# 3     65     D
# 4     55     F
# 5     45     F
```

### Time-Based Bins

```python title="Time period binning"
df = pd.DataFrame({
    'hour': range(24)
})

# Time of day
bins = [0, 6, 12, 18, 24]
labels = ['Night', 'Morning', 'Afternoon', 'Evening']
df['period'] = pd.cut(
    df['hour'],
    bins=bins,
    labels=labels,
    right=False,  # [0, 6) instead of (0, 6]
    include_lowest=True
)
```

## Advanced Binning

### Custom Binning Function

```python title="Apply custom binning logic"
df = pd.DataFrame({
    'value': [10, 25, 50, 75, 100, 150, 200]
})

def custom_bin(value):
    if value < 50:
        return 'Small'
    elif value < 100:
        return 'Medium'
    else:
        return 'Large'

df['size'] = df['value'].apply(custom_bin)
#    value    size
# 0     10   Small
# 1     25   Small
# 2     50  Medium
# 3     75  Medium
# 4    100   Large
# 5    150   Large
# 6    200   Large
```

### Binning with NaN Handling

```python title="Handle missing values in binning"
df = pd.DataFrame({
    'value': [10, np.nan, 30, 40, np.nan, 60]
})

# NaN values are excluded from bins
df['bin'] = pd.cut(df['value'], bins=3)
#    value          bin
# 0   10.0  (9.95, 26.67]
# 1    NaN           NaN
# 2   30.0  (26.67, 43.33]
# 3   40.0  (26.67, 43.33]
# 4    NaN           NaN
# 5   60.0  (43.33, 60.0]

# Fill NaN bins
df['bin'] = df['bin'].cat.add_categories(['Unknown'])
df['bin'].fillna('Unknown', inplace=True)
```

### Duplicate Edges in qcut

```python title="Handle duplicate edges in quantiles"
df = pd.DataFrame({
    'value': [1, 1, 1, 1, 2, 2, 3, 3, 4, 5]
})

# duplicates='drop' removes duplicate edges
df['quartile'] = pd.qcut(df['value'], q=4, duplicates='drop')

# Or use duplicates='raise' to see the error
# pd.qcut(df['value'], q=4, duplicates='raise')  # ValueError!
```

:::warning
`qcut()` fails if there aren't enough unique values to create distinct bins. Use `duplicates='drop'` to handle this.
:::

## Categorical Operations

### Group by Category

```python title="Aggregate by categorical"
df = pd.DataFrame({
    'category': pd.Categorical(['A', 'B', 'A', 'B', 'C']),
    'value': [10, 20, 15, 25, 30]
})

# GroupBy includes all categories (even unused)
result = df.groupby('category', observed=False)['value'].sum()
# A    25
# B    45
# C    30

# observed=True: only include categories present in data
result = df.groupby('category', observed=True)['value'].sum()
```

### Dummy Variables (One-Hot Encoding)

```python title="Convert categorical to dummy variables"
df = pd.DataFrame({
    'color': pd.Categorical(['red', 'blue', 'red', 'green'])
})

# Create dummy variables
dummies = pd.get_dummies(df['color'])
#    blue  green  red
# 0     0      0    1
# 1     1      0    0
# 2     0      0    1
# 3     0      1    0

# Drop first category (avoid multicollinearity)
dummies = pd.get_dummies(df['color'], drop_first=True)
#    green  red
# 0      0    1
# 1      0    0
# 2      0    1
# 3      1    0

# Add prefix
dummies = pd.get_dummies(df['color'], prefix='color')
#    color_blue  color_green  color_red
# 0           0            0          1
# 1           1            0          0
# 2           0            0          1
# 3           0            1          0
```

### Map Categories

```python title="Map categorical values"
df = pd.DataFrame({
    'size': pd.Categorical(['S', 'M', 'L', 'S', 'M'])
})

# Map to numeric
size_map = {'S': 1, 'M': 2, 'L': 3}
df['size_num'] = df['size'].map(size_map)
#   size  size_num
# 0    S         1
# 1    M         2
# 2    L         3
# 3    S         1
# 4    M         2

# Or use cat.codes (automatic)
df['size_code'] = df['size'].cat.codes
#   size  size_code
# 0    S          2  # Based on alphabetical order
# 1    M          1
# 2    L          0
```

## Practical Examples

### Customer Segmentation

```python title="Segment customers by behavior"
df = pd.DataFrame({
    'customer_id': range(100),
    'total_spent': np.random.uniform(100, 5000, 100),
    'visits': np.random.randint(1, 50, 100)
})

# Spending tier
df['spending_tier'] = pd.qcut(
    df['total_spent'],
    q=4,
    labels=['Bronze', 'Silver', 'Gold', 'Platinum']
)

# Engagement level
df['engagement'] = pd.cut(
    df['visits'],
    bins=[0, 5, 15, 50],
    labels=['Low', 'Medium', 'High']
)

# Segment (combination)
df['segment'] = df['spending_tier'].astype(str) + '-' + df['engagement'].astype(str)
```

### Risk Scoring

```python title="Create risk categories"
df = pd.DataFrame({
    'credit_score': np.random.randint(300, 850, 1000)
})

# Risk levels
bins = [300, 580, 670, 740, 850]
labels = ['Very High Risk', 'High Risk', 'Medium Risk', 'Low Risk']
df['risk_level'] = pd.cut(
    df['credit_score'],
    bins=bins,
    labels=labels
)

# Count by risk
df['risk_level'].value_counts().sort_index()
```

## Performance Tips

```python title="Optimize categorical operations"
# Convert to categorical once, not repeatedly
df['status'] = df['status'].astype('category')  # Do this once

# Not this (slow)
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].astype('category')  # Repeated conversion

# Better: convert all object columns at once
object_cols = df.select_dtypes(include=['object']).columns
df[object_cols] = df[object_cols].astype('category')
```

## Quick Reference

**Binning:**

```python
pd.cut(series, bins=4)                   # Equal-width bins
pd.cut(series, bins=[0, 10, 20])        # Custom edges
pd.qcut(series, q=4)                     # Equal-frequency bins
pd.qcut(series, q=[0, 0.25, 0.5, 1])    # Custom percentiles
```

**Categorical:**

```python
series.astype('category')                # Convert to categorical
pd.Categorical(series, ordered=True)    # Create ordered
series.cat.categories                    # View categories
series.cat.codes                         # Get numeric codes
series.cat.add_categories(['new'])      # Add category
series.cat.remove_unused_categories()   # Remove unused
```

**Operations:**

```python
pd.get_dummies(series)                   # One-hot encoding
series.cat.reorder_categories([...])    # Change order
df.groupby('cat', observed=False)       # Include all categories
series.cat.rename_categories({...})     # Rename
```

**Common patterns:**

```python
# Age groups
pd.cut(df['age'], bins=[0, 18, 35, 50, 65, 100])

# Quartiles
pd.qcut(df['value'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])

# Custom binning
df['value'].apply(lambda x: 'high' if x > 100 else 'low')

# Memory optimization
df['col'].astype('category')  # For repeated values
```
