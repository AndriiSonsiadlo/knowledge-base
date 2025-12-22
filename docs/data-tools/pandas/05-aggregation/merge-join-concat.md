---
id: merge-join-concat
title: Merge, Join, and Concat
sidebar_label: Merge, Join & Concat
tags: [ pandas, merge, join, concat, combine, dataframes ]
---

# Merge, Join, and Concat

## Overview

pandas provides several methods to combine DataFrames:

- **merge()**: SQL-style joins based on common columns/indices
- **join()**: Join on indices (or column to index)
- **concat()**: Stack DataFrames vertically or horizontally
- **append()**: Add rows (deprecated, use concat)

## merge() - SQL-Style Joins

### Inner Join (Default)

Keep only rows with matching keys in both DataFrames:

```python title="Inner join - intersection"
import pandas as pd

left = pd.DataFrame({
    'key': ['A', 'B', 'C'],
    'left_value': [1, 2, 3]
})

right = pd.DataFrame({
    'key': ['A', 'B', 'D'],
    'right_value': [4, 5, 6]
})

# Inner join (only A and B match)
result = pd.merge(left, right, on='key', how='inner')
#   key  left_value  right_value
# 0   A           1            4
# 1   B           2            5

# Or use DataFrame method
result = left.merge(right, on='key', how='inner')
```

:::info
**Inner join** keeps only matching rows. This is the default behavior when `how` is not specified.
:::

### Left Join

Keep all rows from left DataFrame:

```python title="Left join - keep all left rows"
result = pd.merge(left, right, on='key', how='left')
#   key  left_value  right_value
# 0   A           1          4.0
# 1   B           2          5.0
# 2   C           3          NaN  # No match in right, filled with NaN
```

### Right Join

Keep all rows from right DataFrame:

```python title="Right join - keep all right rows"
result = pd.merge(left, right, on='key', how='right')
#   key  left_value  right_value
# 0   A         1.0            4
# 1   B         2.0            5
# 2   D         NaN            6  # No match in left
```

### Outer Join

Keep all rows from both DataFrames:

```python title="Outer join - union"
result = pd.merge(left, right, on='key', how='outer')
#   key  left_value  right_value
# 0   A         1.0          4.0
# 1   B         2.0          5.0
# 2   C         3.0          NaN
# 3   D         NaN          6.0
```

### Join Type Comparison

```python title="All join types visualized"
left = pd.DataFrame({
    'key': ['A', 'B', 'C'],
    'val': [1, 2, 3]
})
right = pd.DataFrame({
    'key': ['B', 'C', 'D'],
    'val': [4, 5, 6]
})

# Inner: B, C (intersection)
# Left: A, B, C (all from left)
# Right: B, C, D (all from right)
# Outer: A, B, C, D (union)
```

:::warning
Be careful with join types:

- **Inner**: May lose data (only matches)
- **Left**: Preserves left data, adds right where possible
- **Right**: Preserves right data, adds left where possible
- **Outer**: Keeps everything, but creates many NaN values

  :::

## Merge on Different Columns

### Different Column Names

```python title="Merge when columns have different names"
left = pd.DataFrame({
    'employee_id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie']
})

right = pd.DataFrame({
    'emp_id': [1, 2, 4],
    'salary': [50000, 60000, 55000]
})

# Specify which columns to join on
result = pd.merge(
    left,
    right,
    left_on='employee_id',
    right_on='emp_id',
    how='inner'
)
#    employee_id     name  emp_id  salary
# 0            1    Alice       1   50000
# 1            2      Bob       2   60000
```

### Multiple Columns

```python title="Merge on multiple columns"
left = pd.DataFrame({
    'year': [2023, 2023, 2024],
    'quarter': ['Q1', 'Q2', 'Q1'],
    'sales': [100, 120, 110]
})

right = pd.DataFrame({
    'year': [2023, 2023, 2024],
    'quarter': ['Q1', 'Q2', 'Q2'],
    'costs': [80, 90, 85]
})

# Join on both year and quarter
result = pd.merge(left, right, on=['year', 'quarter'], how='inner')
#    year quarter  sales  costs
# 0  2023      Q1    100     80
# 1  2023      Q2    120     90
```

### Merge with Index

```python title="Merge on index"
left = pd.DataFrame({
    'value': [1, 2, 3]
}, index=['A', 'B', 'C'])

right = pd.DataFrame({
    'value': [4, 5, 6]
}, index=['A', 'B', 'D'])

# Merge on indices
result = pd.merge(
    left,
    right,
    left_index=True,
    right_index=True,
    how='inner'
)
#    value_x  value_y
# A        1        4
# B        2        5

# Or use suffixes to rename columns
result = pd.merge(
    left,
    right,
    left_index=True,
    right_index=True,
    how='inner',
    suffixes=('_left', '_right')
)
#    value_left  value_right
# A           1            4
# B           2            5
```

## Handling Duplicate Keys

### One-to-Many Merge

```python title="One-to-many relationship"
customers = pd.DataFrame({
    'customer_id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie']
})

orders = pd.DataFrame({
    'customer_id': [1, 1, 2, 3, 3],
    'order_id': [101, 102, 103, 104, 105],
    'amount': [100, 150, 200, 120, 180]
})

# One customer can have many orders
result = pd.merge(customers, orders, on='customer_id', how='left')
#    customer_id     name  order_id  amount
# 0            1    Alice     101.0   100.0
# 1            1    Alice     102.0   150.0
# 2            2      Bob     103.0   200.0
# 3            3  Charlie     104.0   120.0
# 4            3  Charlie     105.0   180.0
```

### Many-to-Many Merge

```python title="Many-to-many creates cartesian product"
students = pd.DataFrame({
    'class': ['Math', 'Math', 'Science'],
    'student': ['Alice', 'Bob', 'Charlie']
})

classes = pd.DataFrame({
    'class': ['Math', 'Math', 'Science'],
    'room': ['101', '102', '201']
})

# Each Math student matches both Math rooms (2x2 = 4 rows)
result = pd.merge(students, classes, on='class')
#      class  student room
# 0     Math    Alice  101
# 1     Math    Alice  102
# 2     Math      Bob  101
# 3     Math      Bob  102
# 4  Science  Charlie  201
```

:::warning
Many-to-many merges can explode the number of rows. Check if this is expected or indicates a data
issue.
:::

### Indicator Column

Track which DataFrame each row came from:

```python title="Add merge indicator"
left = pd.DataFrame({'key': ['A', 'B', 'C'], 'val': [1, 2, 3]})
right = pd.DataFrame({'key': ['B', 'C', 'D'], 'val': [4, 5, 6]})

result = pd.merge(left, right, on='key', how='outer', indicator=True)
#   key  val_x  val_y      _merge
# 0   A    1.0    NaN   left_only
# 1   B    2.0    4.0        both
# 2   C    3.0    5.0        both
# 3   D    NaN    6.0  right_only

# Custom indicator name
result = pd.merge(left, right, on='key', how='outer', indicator='source')
```

## join() Method

Simpler syntax for index-based joins:

```python title="Join on indices"
left = pd.DataFrame({
    'A': [1, 2, 3]
}, index=['a', 'b', 'c'])

right = pd.DataFrame({
    'B': [4, 5, 6]
}, index=['a', 'b', 'd'])

# Join (left join by default)
result = left.join(right, how='inner')
#    A  B
# a  1  4
# b  2  5

# Outer join
result = left.join(right, how='outer')
#      A    B
# a  1.0  4.0
# b  2.0  5.0
# c  3.0  NaN
# d  NaN  6.0
```

### Join Multiple DataFrames

```python title="Join multiple DataFrames at once"
df1 = pd.DataFrame({'A': [1, 2]}, index=['a', 'b'])
df2 = pd.DataFrame({'B': [3, 4]}, index=['a', 'b'])
df3 = pd.DataFrame({'C': [5, 6]}, index=['a', 'b'])

# Join all at once
result = df1.join([df2, df3])
#    A  B  C
# a  1  3  5
# b  2  4  6
```

### Join Column to Index

```python title="Join DataFrame column to another's index"
left = pd.DataFrame({
    'key': ['a', 'b', 'c'],
    'value': [1, 2, 3]
})

right = pd.DataFrame({
    'data': [4, 5, 6]
}, index=['a', 'b', 'd'])

# Join left's 'key' column to right's index
result = left.join(right, on='key')
#   key  value  data
# 0   a      1   4.0
# 1   b      2   5.0
# 2   c      3   NaN
```

## concat() - Concatenation

### Vertical Concatenation (Stack Rows)

```python title="Concatenate along rows (axis=0)"
df1 = pd.DataFrame({
    'A': [1, 2],
    'B': [3, 4]
})

df2 = pd.DataFrame({
    'A': [5, 6],
    'B': [7, 8]
})

# Stack vertically (default axis=0)
result = pd.concat([df1, df2])
#    A  B
# 0  1  3
# 1  2  4
# 0  5  7  # Index repeats!
# 1  6  8

# Reset index
result = pd.concat([df1, df2], ignore_index=True)
#    A  B
# 0  1  3
# 1  2  4
# 2  5  7
# 3  6  8
```

### Horizontal Concatenation (Stack Columns)

```python title="Concatenate along columns (axis=1)"
df1 = pd.DataFrame({
    'A': [1, 2, 3]
})

df2 = pd.DataFrame({
    'B': [4, 5, 6]
})

# Stack horizontally
result = pd.concat([df1, df2], axis=1)
#    A  B
# 0  1  4
# 1  2  5
# 2  3  6
```

### Concat with Different Columns

```python title="Handle mismatched columns"
df1 = pd.DataFrame({
    'A': [1, 2],
    'B': [3, 4]
})

df2 = pd.DataFrame({
    'B': [5, 6],
    'C': [7, 8]
})

# Union of columns (default)
result = pd.concat([df1, df2], ignore_index=True)
#      A  B    C
# 0  1.0  3  NaN
# 1  2.0  4  NaN
# 2  NaN  5  7.0
# 3  NaN  6  8.0

# Intersection of columns only
result = pd.concat([df1, df2], join='inner', ignore_index=True)
#    B
# 0  3
# 1  4
# 2  5
# 3  6
```

### Concat with Keys

Add multi-level index to track source:

```python title="Track source DataFrame with keys"
df1 = pd.DataFrame({'value': [1, 2]})
df2 = pd.DataFrame({'value': [3, 4]})

result = pd.concat([df1, df2], keys=['df1', 'df2'])
#        value
# df1 0      1
#     1      2
# df2 0      3
#     1      4

# Reset to make keys a column
result = result.reset_index(level=0).rename(columns={'level_0': 'source'})
#   source  value
# 0    df1      1
# 1    df1      2
# 0    df2      3
# 1    df2      4
```

## Combining Operations

### Merge Multiple DataFrames

```python title="Chain multiple merges"
df1 = pd.DataFrame({'key': ['A', 'B'], 'val1': [1, 2]})
df2 = pd.DataFrame({'key': ['A', 'B'], 'val2': [3, 4]})
df3 = pd.DataFrame({'key': ['A', 'B'], 'val3': [5, 6]})

# Chain merges
result = (df1
          .merge(df2, on='key')
          .merge(df3, on='key')
          )
#   key  val1  val2  val3
# 0   A     1     3     5
# 1   B     2     4     6

# Or use reduce
from functools import reduce

dfs = [df1, df2, df3]
result = reduce(lambda left, right: pd.merge(left, right, on='key'), dfs)
```

### Merge Then Concat

```python title="Combine merge and concat"
# Merge data for 2023
df_2023_sales = pd.DataFrame({'product': ['A', 'B'], 'sales': [100, 200]})
df_2023_costs = pd.DataFrame({'product': ['A', 'B'], 'costs': [80, 150]})
df_2023 = pd.merge(df_2023_sales, df_2023_costs, on='product')
df_2023['year'] = 2023

# Merge data for 2024
df_2024_sales = pd.DataFrame({'product': ['A', 'B'], 'sales': [120, 220]})
df_2024_costs = pd.DataFrame({'product': ['A', 'B'], 'costs': [85, 160]})
df_2024 = pd.merge(df_2024_sales, df_2024_costs, on='product')
df_2024['year'] = 2024

# Concat both years
result = pd.concat([df_2023, df_2024], ignore_index=True)
```

## Common Patterns

### Add Lookup Data

```python title="Enrich data with lookup table"
transactions = pd.DataFrame({
    'product_id': [1, 2, 1, 3],
    'quantity': [10, 5, 8, 12]
})

product_info = pd.DataFrame({
    'product_id': [1, 2, 3],
    'name': ['Widget', 'Gadget', 'Tool'],
    'price': [10.0, 20.0, 15.0]
})

# Add product info to transactions
result = pd.merge(transactions, product_info, on='product_id', how='left')
result['total'] = result['quantity'] * result['price']
#    product_id  quantity     name  price  total
# 0           1        10   Widget   10.0  100.0
# 1           2         5   Gadget   20.0  100.0
# 2           1         8   Widget   10.0   80.0
# 3           3        12     Tool   15.0  180.0
```

### Combine Regional Data

```python title="Combine data from multiple sources"
north = pd.DataFrame({
    'product': ['A', 'B'],
    'sales': [100, 200],
    'region': 'North'
})

south = pd.DataFrame({
    'product': ['A', 'B'],
    'sales': [150, 180],
    'region': 'South'
})

# Combine all regions
all_regions = pd.concat([north, south], ignore_index=True)
#   product  sales region
# 0       A    100  North
# 1       B    200  North
# 2       A    150  South
# 3       B    180  South
```

### Update DataFrame

```python title="Update values from another DataFrame"
main = pd.DataFrame({
    'id': [1, 2, 3],
    'value': [10, 20, 30]
})

updates = pd.DataFrame({
    'id': [2, 3],
    'value': [25, 35]  # New values
})

# Update by merging and combining
result = main.merge(updates, on='id', how='left', suffixes=('', '_new'))
result['value'] = result['value_new'].fillna(result['value'])
result = result.drop('value_new', axis=1)
#    id  value
# 0   1   10.0
# 1   2   25.0  # Updated
# 2   3   35.0  # Updated
```

## Performance Tips

### Merge Performance

```python title="Optimize merge operations"
# Index merge is faster
left = df1.set_index('key')
right = df2.set_index('key')
result = left.join(right)  # Faster than merge on column

# Sort before merge for large DataFrames
left = left.sort_values('key')
right = right.sort_values('key')
result = pd.merge(left, right, on='key')

# Use categorical for repeated merge keys
df['key'] = df['key'].astype('category')
```

:::success
For repeated merges on the same column, convert it to categorical dtype or set it as the index for
better performance.
:::

## Common Mistakes

### Duplicate Column Names

```python title="Handle duplicate column names"
left = pd.DataFrame({'key': ['A'], 'value': [1]})
right = pd.DataFrame({'key': ['A'], 'value': [2]})

# Creates value_x and value_y (confusing!)
result = pd.merge(left, right, on='key')
#   key  value_x  value_y
# 0   A        1        2

# Better: use descriptive suffixes
result = pd.merge(left, right, on='key', suffixes=('_left', '_right'))
#   key  value_left  value_right
# 0   A           1            2

# Or rename before merge
left = left.rename(columns={'value': 'left_value'})
right = right.rename(columns={'value': 'right_value'})
result = pd.merge(left, right, on='key')
```

### Forgetting ignore_index

```python title="Reset index after concat"
df1 = pd.DataFrame({'A': [1, 2]})
df2 = pd.DataFrame({'A': [3, 4]})

# Index repeats (confusing)
result = pd.concat([df1, df2])
#    A
# 0  1
# 1  2
# 0  3  # Index 0 again!
# 1  4

# Better: reset index
result = pd.concat([df1, df2], ignore_index=True)
#    A
# 0  1
# 1  2
# 2  3
# 3  4
```

### Wrong Join Type

```python title="Choose correct join type"
left = pd.DataFrame({'key': ['A', 'B', 'C'], 'val': [1, 2, 3]})
right = pd.DataFrame({'key': ['A', 'B'], 'val': [4, 5]})

# Inner join loses 'C'
inner = pd.merge(left, right, on='key', how='inner')  # Only A, B

# Left join keeps all left data
left_join = pd.merge(left, right, on='key', how='left')  # A, B, C
```

## Quick Reference

**Merge (SQL-style joins):**

```python
pd.merge(left, right, on='key', how='inner')  # Inner join
pd.merge(left, right, on='key', how='left')  # Left join
pd.merge(left, right, on='key', how='right')  # Right join
pd.merge(left, right, on='key', how='outer')  # Outer join
pd.merge(left, right, left_on='k1', right_on='k2')  # Different names
pd.merge(left, right, left_index=True, right_index=True)  # On index
```

**Join (index-based):**

```python
left.join(right, how='inner')
left.join(right, how='left')
left.join([df2, df3])  # Join multiple
left.join(right, on='key')  # Column to index
```

**Concat (stack):**

```python
pd.concat([df1, df2])  # Stack rows (axis=0)
pd.concat([df1, df2], axis=1)  # Stack columns
pd.concat([df1, df2], ignore_index=True)  # Reset index
pd.concat([df1, df2], keys=['a', 'b'])  # Add multi-level index
pd.concat([df1, df2], join='inner')  # Only common columns
```

**Common patterns:**

```python
# Merge multiple DataFrames
df1.merge(df2, on='key').merge(df3, on='key')

# Add lookup data
transactions.merge(product_info, on='product_id', how='left')

# Combine and track source
pd.concat([df1, df2], keys=['source1', 'source2'])

# Update values
main.merge(updates, on='id', how='left', suffixes=('', '_new'))
```

**Tips:**

- Use `merge()` for column-based joins
- Use `join()` for index-based joins
- Use `concat()` for stacking DataFrames
- Always check result size to catch unexpected many-to-many joins
- Use `indicator=True` to track merge sources
