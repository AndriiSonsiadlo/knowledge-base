---
id: sorting-ranking
title: Sorting and Ranking
sidebar_label: Sorting & Ranking
tags: [pandas, sorting, ranking, ordering]
---

# Sorting and Ranking

## Overview

Sorting organizes data by values. Ranking assigns positions based on values. Both are essential for analysis and presentation.

## Sorting by Values

### sort_values() - Basic Sorting

```python title="Sort by column values"
import pandas as pd

df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'David'],
    'age': [25, 30, 25, 28],
    'salary': [50000, 60000, 55000, 58000]
})

# Sort by single column (ascending)
df.sort_values('age')
#       name  age  salary
# 0    Alice   25   50000
# 2  Charlie   25   55000
# 3    David   28   58000
# 1      Bob   30   60000

# Sort descending
df.sort_values('salary', ascending=False)
#       name  age  salary
# 1      Bob   30   60000
# 3    David   28   58000
# 2  Charlie   25   55000
# 0    Alice   25   50000
```

:::warning
`sort_values()` returns a new DataFrame by default. Use `inplace=True` to modify the original, or assign the result.
:::

### Sort by Multiple Columns

```python title="Multi-column sorting"
df = pd.DataFrame({
    'category': ['A', 'B', 'A', 'B', 'A'],
    'priority': [1, 2, 1, 1, 2],
    'value': [100, 200, 150, 180, 120]
})

# Sort by category, then by priority
df.sort_values(['category', 'priority'])
#   category  priority  value
# 0        A         1    100
# 2        A         1    150
# 4        A         2    120
# 3        B         1    180
# 1        B         2    200

# Different directions for each column
df.sort_values(
    ['category', 'value'],
    ascending=[True, False]  # category asc, value desc
)
#   category  priority  value
# 2        A         1    150
# 4        A         2    120
# 0        A         1    100
# 1        B         2    200
# 3        B         1    180
```

### Sort with Missing Values

```python title="Handle NaN in sorting"
import numpy as np

df = pd.DataFrame({
    'value': [3, 1, np.nan, 2, np.nan]
})

# NaN at the end (default)
df.sort_values('value')
#    value
# 1    1.0
# 3    2.0
# 0    3.0
# 2    NaN
# 4    NaN

# NaN at the beginning
df.sort_values('value', na_position='first')
#    value
# 2    NaN
# 4    NaN
# 1    1.0
# 3    2.0
# 0    3.0
```

## Sorting by Index

### sort_index()

```python title="Sort by index labels"
df = pd.DataFrame({
    'value': [10, 20, 30]
}, index=['c', 'a', 'b'])

# Sort by index
df.sort_index()
#    value
# a     20
# b     30
# c     10

# Sort descending
df.sort_index(ascending=False)
#    value
# c     10
# b     30
# a     20

# Sort columns
df = pd.DataFrame({
    'z': [1, 2],
    'a': [3, 4],
    'c': [5, 6]
})
df.sort_index(axis=1)  # Sort column names
#    a  c  z
# 0  3  5  1
# 1  4  6  2
```

## Ranking

### rank() - Assign Ranks

```python title="Basic ranking"
df = pd.DataFrame({
    'score': [85, 92, 85, 78, 95]
})

# Assign ranks (highest value = highest rank)
df['rank'] = df['score'].rank(ascending=False)
#    score  rank
# 0     85   3.5  # Tied, gets average rank
# 1     92   2.0
# 2     85   3.5  # Tied, gets average rank
# 3     78   5.0
# 4     95   1.0
```

:::info
By default, `rank()` uses average method for ties. Both tied values get rank 3.5 (average of 3 and 4).
:::

### Rank Methods for Ties

```python title="Different tie-breaking methods"
df = pd.DataFrame({
    'score': [85, 92, 85, 78, 95]
})

# Average (default): tied values get average rank
df['rank_avg'] = df['score'].rank(ascending=False, method='average')

# Min: tied values get minimum rank
df['rank_min'] = df['score'].rank(ascending=False, method='min')

# Max: tied values get maximum rank  
df['rank_max'] = df['score'].rank(ascending=False, method='max')

# First: ranks assigned in order of appearance
df['rank_first'] = df['score'].rank(ascending=False, method='first')

# Dense: like min, but no gaps in ranking
df['rank_dense'] = df['score'].rank(ascending=False, method='dense')

#    score  rank_avg  rank_min  rank_max  rank_first  rank_dense
# 0     85       3.5       3.0       4.0         3.0         3.0
# 1     92       2.0       2.0       2.0         2.0         2.0
# 2     85       3.5       3.0       4.0         4.0         3.0
# 3     78       5.0       5.0       5.0         5.0         4.0
# 4     95       1.0       1.0       1.0         1.0         1.0
```

### Rank by Groups

```python title="Ranking within groups"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B', 'A'],
    'score': [85, 92, 78, 88, 90]
})

# Rank within each category
df['rank'] = df.groupby('category')['score'].rank(ascending=False)
#   category  score  rank
# 0        A     85   3.0
# 1        A     92   1.0
# 2        B     78   2.0
# 3        B     88   1.0
# 4        A     90   2.0
```

This is useful for "top N per group" queries.

### Percentile Rank

```python title="Rank as percentile"
df = pd.DataFrame({
    'score': [50, 75, 100, 80, 60]
})

# Rank as percentile (0-1)
df['percentile'] = df['score'].rank(pct=True)
#    score  percentile
# 0     50         0.2  # 20th percentile
# 1     75         0.6  # 60th percentile
# 2    100         1.0  # 100th percentile
# 3     80         0.8  # 80th percentile
# 4     60         0.4  # 40th percentile

# Convert to percentage
df['percentile_pct'] = df['percentile'] * 100
```

## Top N and Bottom N

### nlargest() and nsmallest()

```python title="Get top/bottom N rows"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    'score': [85, 92, 78, 95, 88]
})

# Top 3 scores
df.nlargest(3, 'score')
#      name  score
# 3   David     95
# 1     Bob     92
# 4     Eve     88

# Bottom 2 scores
df.nsmallest(2, 'score')
#       name  score
# 2  Charlie     78
# 0    Alice     85

# Top N by multiple columns
df.nlargest(2, ['score', 'name'])
```

:::success
`nlargest()` and `nsmallest()` are faster than sorting when you only need top/bottom N rows.
:::

## Sorting Performance

### Sort Algorithms

```python title="Choose sort algorithm"
df = pd.DataFrame({
    'value': range(100000, 0, -1)
})

# Default: quicksort
df.sort_values('value', kind='quicksort')

# Stable sort (preserves order of equal elements)
df.sort_values('value', kind='stable')

# Merge sort (always stable but slower)
df.sort_values('value', kind='mergesort')

# Heap sort
df.sort_values('value', kind='heapsort')
```

:::info
Use `kind='stable'` when the order of equal elements matters. Default quicksort is fastest but not stable.
:::

### Sort in Place

```python title="Modify original DataFrame"
df = pd.DataFrame({
    'value': [3, 1, 2]
})

# Returns new DataFrame (default)
df_sorted = df.sort_values('value')

# Modify original
df.sort_values('value', inplace=True)
# df is now sorted
```

## Common Patterns

### Sort and Reset Index

```python title="Reset index after sorting"
df = pd.DataFrame({
    'value': [30, 10, 20]
}, index=['a', 'b', 'c'])

# Sort and keep original index
df.sort_values('value')
#    value
# b     10
# c     20
# a     30

# Sort and reset to 0, 1, 2
df.sort_values('value').reset_index(drop=True)
#    value
# 0     10
# 1     20
# 2     30
```

### Sort by Computed Column

```python title="Sort by calculated values"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'score1': [85, 90, 78],
    'score2': [92, 88, 95]
})

# Sort by average score
df['avg'] = (df['score1'] + df['score2']) / 2
df.sort_values('avg', ascending=False)
#       name  score1  score2    avg
# 1      Bob      90      88   89.0
# 0    Alice      85      92   88.5
# 2  Charlie      78      95   86.5

# Or without creating column
df.loc[((df['score1'] + df['score2']) / 2).sort_values(ascending=False).index]
```

### Top N per Group

```python title="Get top N within each group"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B', 'A', 'B'],
    'value': [10, 15, 20, 25, 12, 22]
})

# Top 2 per category
df.groupby('category').apply(
    lambda x: x.nlargest(2, 'value')
).reset_index(drop=True)
#   category  value
# 0        A     15
# 1        A     12
# 2        B     25
# 3        B     22

# Or with sorting
df.sort_values('value', ascending=False).groupby('category').head(2)
```

### Rank with Custom Function

```python title="Apply custom ranking logic"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'David'],
    'score': [85, 92, 85, 78]
})

# Assign letter grades based on rank
def assign_grade(rank):
    if rank <= 2:
        return 'A'
    elif rank <= 4:
        return 'B'
    else:
        return 'C'

df['rank'] = df['score'].rank(ascending=False, method='min')
df['grade'] = df['rank'].apply(assign_grade)
#       name  score  rank grade
# 0    Alice     85   3.0     B
# 1      Bob     92   1.0     A
# 2  Charlie     85   3.0     B
# 3    David     78   5.0     C
```

## Sorting Dates

### Sort DateTime Columns

```python title="Sort by dates"
df = pd.DataFrame({
    'date': pd.to_datetime(['2024-03-01', '2024-01-15', '2024-02-20']),
    'value': [100, 200, 150]
})

# Sort by date (oldest first)
df.sort_values('date')
#         date  value
# 1 2024-01-15    200
# 2 2024-02-20    150
# 0 2024-03-01    100

# Most recent first
df.sort_values('date', ascending=False)
#         date  value
# 0 2024-03-01    100
# 2 2024-02-20    150
# 1 2024-01-15    200
```

### Sort by Date Components

```python title="Sort by year, month, day separately"
df = pd.DataFrame({
    'date': pd.to_datetime(['2024-01-15', '2023-12-20', '2024-01-10'])
})

# Extract components
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day'] = df['date'].dt.day

# Sort by month, then day (ignoring year)
df.sort_values(['month', 'day'])
```

## Sorting Strings

### Natural Sort (Human Sort)

```python title="Sort strings naturally"
df = pd.DataFrame({
    'version': ['1.10', '1.2', '1.9', '1.20', '1.1']
})

# Regular sort (lexicographic)
df.sort_values('version')
#   version
# 4     1.1
# 3    1.10
# 1     1.2
# 0    1.20
# 2     1.9

# Natural sort using key parameter
from natsort import natsorted
df['sort_key'] = df['version'].apply(lambda x: natsorted([x])[0])
df.sort_values('sort_key')

# Or use natsort directly
df_sorted = df.iloc[natsorted(range(len(df)), key=lambda i: df.loc[i, 'version'])]
```

### Case-Insensitive Sort

```python title="Sort strings ignoring case"
df = pd.DataFrame({
    'name': ['alice', 'Bob', 'CHARLIE', 'david']
})

# Case-sensitive (default)
df.sort_values('name')
# Bob, CHARLIE, alice, david (capitals first)

# Case-insensitive
df.sort_values('name', key=lambda x: x.str.lower())
#       name
# 0    alice
# 1      Bob
# 2  CHARLIE
# 3    david
```

## Combining Sort and Filter

### Filter Then Sort

```python title="Filter and sort together"
df = pd.DataFrame({
    'category': ['A', 'B', 'A', 'B', 'A'],
    'value': [10, 20, 15, 25, 12]
})

# Filter category A, then sort by value
result = df[df['category'] == 'A'].sort_values('value', ascending=False)
#   category  value
# 2        A     15
# 4        A     12
# 0        A     10

# Or with query
result = df.query('category == "A"').sort_values('value', ascending=False)
```

## Performance Tips

```python title="Sorting optimization"
# For large DataFrames, specify columns to sort
df.sort_values(['col1', 'col2'])  # Only sort by needed columns

# Use nlargest/nsmallest instead of sort + head
# Slow
df.sort_values('value', ascending=False).head(10)

# Fast
df.nlargest(10, 'value')

# Sort index is faster than sort values
# If you need to sort frequently, set as index
df.set_index('id').sort_index()  # Fast
```

:::warning
Sorting large DataFrames can be slow. Consider:

1. Using `nlargest()`/`nsmallest()` for top/bottom N
2. Filtering before sorting to reduce data size
3. Setting frequently sorted columns as index

   :::

## Common Mistakes

### Forgetting to Assign Result

```python title="Sort doesn't modify by default"
df = pd.DataFrame({'value': [3, 1, 2]})

# This doesn't change df
df.sort_values('value')

# Need to assign
df = df.sort_values('value')
# Or use inplace
df.sort_values('value', inplace=True)
```

### Mixing Sort Directions

```python title="Specify ascending per column"
# Wrong: only applies to first column
df.sort_values(['col1', 'col2'], ascending=False)

# Right: specify for each
df.sort_values(['col1', 'col2'], ascending=[True, False])
```

### Rank Direction Confusion

```python title="Rank ascending vs descending"
df = pd.DataFrame({'score': [85, 92, 78]})

# ascending=True: lower value = lower rank
df['score'].rank(ascending=True)
# 0    2.0  (85)
# 1    3.0  (92)
# 2    1.0  (78)

# ascending=False: higher value = lower rank  
df['score'].rank(ascending=False)
# 0    2.0  (85)
# 1    1.0  (92)
# 2    3.0  (78)
```

## Quick Reference

**Sort by values:**

```python
df.sort_values('col')                    # Ascending
df.sort_values('col', ascending=False)   # Descending
df.sort_values(['c1', 'c2'])            # Multiple columns
df.sort_values('col', na_position='first') # NaN handling
```

**Sort by index:**

```python
df.sort_index()                          # Sort by row index
df.sort_index(axis=1)                   # Sort by column names
```

**Ranking:**

```python
df['col'].rank()                         # Rank (average for ties)
df['col'].rank(method='min')            # Min rank for ties
df['col'].rank(ascending=False)         # Higher value = rank 1
df['col'].rank(pct=True)                # Percentile rank
df.groupby('group')['col'].rank()       # Rank within groups
```

**Top/Bottom N:**

```python
df.nlargest(n, 'col')                   # Top N
df.nsmallest(n, 'col')                  # Bottom N
df.groupby('group').head(n)             # Top N per group
```

**Common patterns:**

```python
# Sort and reset index
df.sort_values('col').reset_index(drop=True)

# Top N per group
df.groupby('group').apply(lambda x: x.nlargest(2, 'value'))

# Rank and filter top ranks
df[df['col'].rank(ascending=False) <= 3]
```
