---
id: groupby
title: GroupBy Operations
sidebar_label: GroupBy
tags: [pandas, groupby, aggregation, split-apply-combine]
---

# GroupBy Operations

## Overview

GroupBy implements the **split-apply-combine** pattern:

1. **Split**: Divide data into groups based on criteria
2. **Apply**: Apply a function to each group independently
3. **Combine**: Combine results into a data structure

This is one of the most powerful features in pandas.

## Basic GroupBy

### Single Column Grouping

```python title="Group by single column"
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'category': ['A', 'B', 'A', 'B', 'A', 'B'],
    'value': [10, 20, 15, 25, 12, 30]
})

# Group by category and sum
result = df.groupby('category')['value'].sum()
# category
# A    37
# B    75

# Group and aggregate entire DataFrame
result = df.groupby('category').sum()
#          value
# category      
# A           37
# B           75
```

### Multiple Column Grouping

```python title="Group by multiple columns"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B', 'A', 'B'],
    'region': ['East', 'West', 'East', 'West', 'East', 'West'],
    'sales': [100, 150, 200, 250, 120, 280]
})

# Group by category and region
result = df.groupby(['category', 'region'])['sales'].sum()
# category  region
# A         East      220
#           West      150
# B         East      200
#           West      530

# Reset index to get DataFrame
result = result.reset_index()
#   category region  sales
# 0        A   East    220
# 1        A   West    150
# 2        B   East    200
# 3        B   West    530
```

:::info
GroupBy with multiple columns creates a MultiIndex. Use `reset_index()` to convert it back to regular columns.
:::

## Common Aggregations

### Built-in Aggregations

```python title="Standard aggregation methods"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B'],
    'value': [10, 20, 15, 25]
})

# Sum
df.groupby('category')['value'].sum()

# Mean
df.groupby('category')['value'].mean()
# category
# A    15.0
# B    20.0

# Count
df.groupby('category')['value'].count()

# Min/Max
df.groupby('category')['value'].min()
df.groupby('category')['value'].max()

# Standard deviation
df.groupby('category')['value'].std()

# Multiple statistics
df.groupby('category')['value'].describe()
```

### agg() - Multiple Aggregations

```python title="Apply multiple aggregations"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B'],
    'sales': [100, 150, 200, 250],
    'quantity': [10, 15, 20, 25]
})

# Multiple aggregations on one column
result = df.groupby('category')['sales'].agg(['sum', 'mean', 'count'])
#          sum   mean  count
# category                  
# A        250  125.0      2
# B        450  225.0      2

# Different aggregations per column
result = df.groupby('category').agg({
    'sales': ['sum', 'mean'],
    'quantity': ['min', 'max']
})
#          sales       quantity    
#            sum  mean      min max
# category                         
# A          250 125.0       10  15
# B          450 225.0       20  25

# Custom names
result = df.groupby('category').agg(
    total_sales=('sales', 'sum'),
    avg_sales=('sales', 'mean'),
    total_qty=('quantity', 'sum')
)
#          total_sales  avg_sales  total_qty
# category                                   
# A                250      125.0         25
# B                450      225.0         45
```

:::success
Use named aggregations (pandas 0.25+) for cleaner column names: `agg(name=('column', 'function'))`
:::

## GroupBy Selection

### Select Columns After Grouping

```python title="Select specific columns"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B'],
    'product': ['X', 'Y', 'X', 'Y'],
    'sales': [100, 150, 200, 250],
    'profit': [20, 30, 40, 50]
})

# Group by category, aggregate sales only
df.groupby('category')['sales'].sum()

# Group by category, aggregate multiple columns
df.groupby('category')[['sales', 'profit']].sum()
#          sales  profit
# category              
# A          250      50
# B          450      90

# All columns except grouping column
df.groupby('category').sum()
```

### Iterate Through Groups

```python title="Loop through groups"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B'],
    'value': [10, 20, 15, 25]
})

# Iterate through groups
for name, group in df.groupby('category'):
    print(f"Category: {name}")
    print(group)
    print()

# Category: A
#   category  value
# 0        A     10
# 1        A     20
# 
# Category: B
#   category  value
# 2        B     15
# 3        B     25
```

### Get Specific Group

```python title="Access a specific group"
grouped = df.groupby('category')

# Get group 'A'
group_a = grouped.get_group('A')
#   category  value
# 0        A     10
# 1        A     20

# Get multiple groups
for cat in ['A', 'B']:
    group = grouped.get_group(cat)
    print(f"Group {cat}:")
    print(group)
```

## Transform and Filter

### transform() - Same Shape Output

Add aggregated values back to original DataFrame:

```python title="Transform adds group statistics"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B'],
    'value': [10, 20, 15, 25]
})

# Add group mean to each row
df['group_mean'] = df.groupby('category')['value'].transform('mean')
#   category  value  group_mean
# 0        A     10        15.0
# 1        A     20        15.0
# 2        B     15        20.0
# 3        B     25        20.0

# Add group sum
df['group_sum'] = df.groupby('category')['value'].transform('sum')

# Custom transform
df['diff_from_mean'] = df.groupby('category')['value'].transform(
    lambda x: x - x.mean()
)
#   category  value  diff_from_mean
# 0        A     10            -5.0
# 1        A     20             5.0
# 2        B     15            -5.0
# 3        B     25             5.0
```

### filter() - Keep/Remove Groups

Filter entire groups based on group properties:

```python title="Filter groups by condition"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B', 'C'],
    'value': [10, 20, 15, 25, 30]
})

# Keep groups where sum > 30
result = df.groupby('category').filter(lambda x: x['value'].sum() > 30)
#   category  value
# 1        A     20
# 0        A     10
# 3        B     25
# 2        B     15

# Keep groups with more than 1 member
result = df.groupby('category').filter(lambda x: len(x) > 1)

# Remove outliers within groups
def remove_outliers(group):
    return group[np.abs(group['value'] - group['value'].mean()) < 2 * group['value'].std()]

result = df.groupby('category').filter(remove_outliers)
```

:::warning
`filter()` returns entire groups (all rows), not individual rows. Use boolean indexing for row-level filtering.
:::

## Advanced GroupBy

### apply() - Flexible Operations

Most flexible GroupBy method:

```python title="Custom operations with apply"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B'],
    'value': [10, 20, 15, 25]
})

# Custom function per group
def custom_function(group):
    return pd.Series({
        'sum': group['value'].sum(),
        'count': len(group),
        'max_minus_min': group['value'].max() - group['value'].min()
    })

result = df.groupby('category').apply(custom_function)
#          sum  count  max_minus_min
# category                           
# A         30      2             10
# B         40      2             10

# Return modified DataFrame
def normalize(group):
    group['normalized'] = (group['value'] - group['value'].mean()) / group['value'].std()
    return group

result = df.groupby('category').apply(normalize)
```

### GroupBy with Custom Keys

```python title="Group by computed values"
df = pd.DataFrame({
    'value': [10, 20, 30, 40, 50]
})

# Group by even/odd
df.groupby(df['value'] % 2 == 0)['value'].sum()
# value
# False    90  # Odd values: 10+30+50
# True     60  # Even values: 20+40

# Group by value ranges
df.groupby(pd.cut(df['value'], bins=[0, 25, 50]))['value'].sum()

# Group by custom function
def classify(value):
    return 'low' if value < 30 else 'high'

df.groupby(df['value'].apply(classify))['value'].mean()
```

### Multiple Aggregations with Different Functions

```python title="Complex aggregations"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B'],
    'sales': [100, 150, 200, 250],
    'quantity': [10, 15, 20, 25],
    'profit': [20, 30, 40, 50]
})

# Different functions for different columns
result = df.groupby('category').agg({
    'sales': ['sum', 'mean'],
    'quantity': 'sum',
    'profit': lambda x: x.max() - x.min()
})

# With custom names
result = df.groupby('category').agg(
    total_sales=('sales', 'sum'),
    avg_sales=('sales', 'mean'),
    total_qty=('quantity', 'sum'),
    profit_range=('profit', lambda x: x.max() - x.min())
)
```

## Handling Missing Values

### Groups with NaN

```python title="NaN in groupby keys"
df = pd.DataFrame({
    'category': ['A', 'B', np.nan, 'A', np.nan],
    'value': [10, 20, 30, 40, 50]
})

# NaN creates its own group by default
df.groupby('category')['value'].sum()
# category
# A      50
# B      20
# NaN    80

# Exclude NaN groups
df.groupby('category', dropna=True)['value'].sum()
# category
# A    50
# B    20

# NaN in values (not keys) are ignored in aggregations
df['value'] = [10, np.nan, 30, 40, 50]
df.groupby('category')['value'].sum()  # Skips NaN in sum
```

## GroupBy with Dates

### Grouping by Time Periods

```python title="Group by date components"
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=100),
    'value': range(100)
})

# Group by month
df['month'] = df['date'].dt.month
df.groupby('month')['value'].sum()

# Group by year-month
df.groupby(df['date'].dt.to_period('M'))['value'].sum()

# Group by day of week
df.groupby(df['date'].dt.day_name())['value'].mean()

# Group by custom period
df.groupby(pd.Grouper(key='date', freq='W'))['value'].sum()
```

### Resample vs GroupBy

```python title="Resample for time series"
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=30, freq='D'),
    'value': range(30)
})
df = df.set_index('date')

# Resample (better for time series)
df.resample('W')['value'].sum()

# GroupBy with Grouper (more flexible)
df.groupby(pd.Grouper(freq='W'))['value'].sum()
```

## Top N per Group

### Get Top N in Each Group

```python title="Top N rows per group"
df = pd.DataFrame({
    'category': ['A', 'A', 'A', 'B', 'B', 'B'],
    'value': [10, 20, 15, 25, 30, 22]
})

# Top 2 per category
result = df.groupby('category').apply(
    lambda x: x.nlargest(2, 'value')
).reset_index(drop=True)
#   category  value
# 0        A     20
# 1        A     15
# 2        B     30
# 3        B     25

# Using head() for first N
result = df.sort_values('value', ascending=False).groupby('category').head(2)

# Bottom 1 per group
result = df.groupby('category').apply(
    lambda x: x.nsmallest(1, 'value')
)
```

## Cumulative Operations within Groups

```python title="Cumulative calculations per group"
df = pd.DataFrame({
    'category': ['A', 'A', 'A', 'B', 'B', 'B'],
    'value': [10, 20, 15, 25, 30, 22]
})

# Cumulative sum within each group
df['cumsum'] = df.groupby('category')['value'].cumsum()
#   category  value  cumsum
# 0        A     10      10
# 1        A     20      30
# 2        A     15      45
# 3        B     25      25
# 4        B     30      55
# 5        B     22      77

# Rank within group
df['rank'] = df.groupby('category')['value'].rank(ascending=False)

# Percentage of group total
df['pct_of_group'] = df.groupby('category')['value'].transform(
    lambda x: x / x.sum() * 100
)
```

## Performance Tips

### Optimize GroupBy Operations

```python title="Performance optimization"
df = pd.DataFrame({
    'category': ['A'] * 10000 + ['B'] * 10000,
    'value': range(20000)
})

# Slow: Multiple separate groupby calls
sum_a = df[df['category'] == 'A']['value'].sum()
sum_b = df[df['category'] == 'B']['value'].sum()

# Fast: Single groupby
result = df.groupby('category')['value'].sum()

# Use as_index=False to avoid reset_index
result = df.groupby('category', as_index=False)['value'].sum()
#   category      value
# 0        A   49995000
# 1        B  149995000

# Faster aggregations with numba (if installed)
result = df.groupby('category')['value'].agg('sum', engine='numba')
```

:::success
Avoid multiple groupby calls. Combine all aggregations in a single `agg()` call for better performance.
:::

### Sort Parameter

```python title="Control sorting in groupby"
df = pd.DataFrame({
    'category': ['B', 'A', 'C', 'B', 'A', 'C'],
    'value': [10, 20, 15, 25, 30, 22]
})

# GroupBy sorts by default (can be slow)
df.groupby('category')['value'].sum()
# category
# A    50
# B    35
# C    37

# Disable sorting for speed (if order doesn't matter)
df.groupby('category', sort=False)['value'].sum()
# category
# B    35  # First category in data
# A    50
# C    37
```

## Common Patterns

### Percentage of Total per Group

```python title="Calculate group percentages"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B'],
    'product': ['X', 'Y', 'X', 'Y'],
    'sales': [100, 150, 200, 250]
})

# Sales as % of category total
df['pct_of_category'] = df.groupby('category')['sales'].transform(
    lambda x: x / x.sum() * 100
)
#   category product  sales  pct_of_category
# 0        A       X    100             40.0
# 1        A       Y    150             60.0
# 2        B       X    200             44.44
# 3        B       Y    250             55.56

# Sales as % of grand total
df['pct_of_total'] = df['sales'] / df['sales'].sum() * 100
```

### Compare to Group Average

```python title="Deviation from group mean"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B'],
    'value': [10, 20, 15, 25]
})

# Difference from group mean
df['diff_from_mean'] = df.groupby('category')['value'].transform(
    lambda x: x - x.mean()
)

# Standardize within groups (z-score)
df['z_score'] = df.groupby('category')['value'].transform(
    lambda x: (x - x.mean()) / x.std()
)
```

### Fill Missing with Group Mean

```python title="Impute missing values by group"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B', 'A'],
    'value': [10, np.nan, 15, 25, 20]
})

# Fill NaN with group mean
df['value'] = df.groupby('category')['value'].transform(
    lambda x: x.fillna(x.mean())
)
#   category  value
# 0        A   10.0
# 1        A   15.0  # Filled with A's mean (10+20)/2
# 2        B   15.0
# 3        B   25.0
# 4        A   20.0
```

## Common Mistakes

### Forgetting reset_index()

```python title="GroupBy creates index from groups"
df = pd.DataFrame({
    'category': ['A', 'B', 'A', 'B'],
    'value': [10, 20, 15, 25]
})

# Result has category as index
result = df.groupby('category')['value'].sum()
# category
# A    25
# B    45

# Need reset_index for regular DataFrame
result = df.groupby('category')['value'].sum().reset_index()
#   category  value
# 0        A     25
# 1        B     45

# Or use as_index=False
result = df.groupby('category', as_index=False)['value'].sum()
```

### transform() vs agg() Confusion

```python title="Understanding transform vs agg"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B'],
    'value': [10, 20, 15, 25]
})

# agg() reduces to one row per group
df.groupby('category')['value'].agg('mean')
# category
# A    15.0
# B    20.0

# transform() keeps original shape
df.groupby('category')['value'].transform('mean')
# 0    15.0  # Mean of A
# 1    15.0  # Mean of A
# 2    20.0  # Mean of B
# 3    20.0  # Mean of B
```

### Column Name Conflicts

```python title="Avoid naming conflicts"
df = pd.DataFrame({
    'category': ['A', 'B', 'A', 'B'],
    'sum': [10, 20, 15, 25]  # 'sum' is also a method name
})

# This can be confusing
df.groupby('category')['sum'].sum()  # Works but confusing

# Better: use clear column names
df.rename(columns={'sum': 'total'}, inplace=True)
df.groupby('category')['total'].sum()
```

## Quick Reference

**Basic groupby:**

```python
df.groupby('col')['value'].sum()
df.groupby(['col1', 'col2'])['value'].mean()
df.groupby('col', as_index=False)['value'].sum()
```

**Aggregations:**

```python
grouped.agg(['sum', 'mean', 'count'])
grouped.agg({'col1': 'sum', 'col2': 'mean'})
grouped.agg(total=('sales', 'sum'))
```

**Transform and filter:**

```python
grouped.transform('mean')           # Add group stat to each row
grouped.filter(lambda x: len(x) > 2)  # Keep groups with >2 rows
grouped.apply(custom_func)          # Custom operation
```

**Common patterns:**

```python
# Top N per group
df.groupby('group').head(n)
df.groupby('group').nlargest(n, 'col')

# Cumulative within group
df.groupby('group')['col'].cumsum()

# Percentage of group
df.groupby('group')['col'].transform(lambda x: x / x.sum() * 100)

# Fill NaN with group mean
df.groupby('group')['col'].transform(lambda x: x.fillna(x.mean()))

# Compare to group mean
df.groupby('group')['col'].transform(lambda x: x - x.mean())
```

**Performance:**

```python
df.groupby('col', sort=False)       # Disable sorting
df.groupby('col').agg(['sum', 'mean'])  # Combine aggregations
```
