---
id: loc-vs-iloc
title: loc vs iloc
sidebar_label: loc vs iloc
tags: [ pandas, indexing, loc, iloc, selection ]
---

# loc vs iloc

## Overview

**_pandas_** provides two main indexers for selecting data:

- **`loc`** : Label-based indexing (uses _row/column names_)
- **`iloc`** : Position-based indexing (uses _integer positions_)

The key difference: `loc` uses labels, `iloc` uses positions (like list indices).

## Basic Difference

```python title="The fundamental difference"
import pandas as pd

df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['NYC', 'LA', 'Chicago']
}, index=['a', 'b', 'c'])

#    name  age     city
# a  Alice   25      NYC
# b    Bob   30       LA
# c Charlie   35  Chicago

# loc uses labels
df.loc['a']  # Row with label 'a'
df.loc['a', 'name']  # Cell at row 'a', column 'name'

# iloc uses integer positions
df.iloc[0]  # First row (position 0)
df.iloc[0, 0]  # First row, first column
```

Think of `loc` as "location by name" and `iloc` as "location by position number".

## loc - Label-Based Indexing

### Single Row Selection

Access rows by their index labels:

```python title="Selecting single rows with loc"
df = pd.DataFrame({
    'product': ['A', 'B', 'C'],
    'price': [100, 200, 150]
}, index=['p1', 'p2', 'p3'])

# Get row with label 'p1'
df.loc['p1']
# product     A
# price     100

# Returns a Series with column names as index
```

### Multiple Row Selection

Select multiple rows using a list of labels:

```python title="Selecting multiple rows with loc"
# Multiple specific rows
df.loc[['p1', 'p3']]
#     product  price
# p1        A    100
# p3        C    150

# Returns a DataFrame
```

### Row Slicing

Slicing with `loc` is inclusive of both endpoints:

```python title="Slicing rows with loc (inclusive)"
df.loc['p1':'p3']  # Includes both 'p1' AND 'p3'
#     product  price
# p1        A    100
# p2        B    200
# p3        C    150

# This is different from Python's normal slicing!
# Normal Python: list[0:3] excludes index 3
# pandas loc: df.loc['p1':'p3'] includes 'p3'
```

### Column Selection with loc

Select specific columns:

```python title="Selecting columns with loc"
# All rows, single column
df.loc[:, 'product']  # Returns Series

# All rows, multiple columns
df.loc[:, ['product', 'price']]  # Returns DataFrame

# Slice columns (inclusive)
df.loc[:, 'product':'price']
```

### Rows and Columns Together

The power of `loc`: select rows AND columns simultaneously:

```python title="Selecting rows and columns together"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['NYC', 'LA', 'Chicago'],
    'salary': [50000, 60000, 70000]
}, index=['a', 'b', 'c'])

# Specific row and column
df.loc['a', 'name']  # 'Alice'

# Specific row, multiple columns
df.loc['a', ['name', 'age']]
# name     Alice
# age         25

# Multiple rows, specific column
df.loc[['a', 'c'], 'name']
# a      Alice
# c    Charlie

# Multiple rows and columns
df.loc[['a', 'b'], ['name', 'salary']]
#     name  salary
# a  Alice   50000
# b    Bob   60000

# Slicing both dimensions
df.loc['a':'b', 'name':'city']
```

### Boolean Indexing with loc

Combine conditions with column selection:

```python title="Boolean filtering with loc"
# Filter rows and select columns
df.loc[df['age'] > 28, ['name', 'city']]
#       name     city
# b      Bob       LA
# c  Charlie  Chicago

# Complex conditions
df.loc[
    (df['age'] > 25) & (df['city'] == 'NYC'),
    ['name', 'salary']
]

# Filter rows, get single column as Series
df.loc[df['age'] > 28, 'name']
# b        Bob
# c    Charlie
```

This is more efficient than filtering first and then selecting columns separately.

## iloc - Position-Based Indexing

### Single Row Selection

Access rows by integer position (0-indexed):

```python title="Selecting single rows with iloc"
df = pd.DataFrame({
    'product': ['A', 'B', 'C'],
    'price': [100, 200, 150]
}, index=['p1', 'p2', 'p3'])

# First row (position 0)
df.iloc[0]
# product     A
# price     100

# Last row
df.iloc[-1]
# product     C
# price     150

# Second row
df.iloc[1]
```

### Multiple Row Selection

Select multiple rows by position:

```python title="Selecting multiple rows with iloc"
# First and third rows
df.iloc[[0, 2]]
#     product  price
# p1        A    100
# p3        C    150

# First two rows
df.iloc[[0, 1]]
```

### Row Slicing

Slicing with `iloc` follows Python's standard slicing (exclusive endpoint):

```python title="Slicing rows with iloc (exclusive)"
# First 2 rows (0 and 1, excludes 2)
df.iloc[0:2]
#     product  price
# p1        A    100
# p2        B    200

# All rows except first
df.iloc[1:]

# All rows except last
df.iloc[:-1]

# Every other row
df.iloc[::2]
```

### Column Selection with iloc

Select columns by position:

```python title="Selecting columns with iloc"
# All rows, first column
df.iloc[:, 0]  # Returns Series

# All rows, first two columns
df.iloc[:, 0:2]  # Returns DataFrame

# All rows, last column
df.iloc[:, -1]

# Every other column
df.iloc[:, ::2]
```

### Rows and Columns Together

Select by position in both dimensions:

```python title="Selecting rows and columns by position"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['NYC', 'LA', 'Chicago']
})

# First row, second column
df.iloc[0, 1]  # 25

# First row, first two columns
df.iloc[0, 0:2]
# name     Alice
# age         25

# First two rows, all columns
df.iloc[0:2, :]

# First two rows, first two columns
df.iloc[0:2, 0:2]
#     name  age
# 0  Alice   25
# 1    Bob   30

# Last row, last column
df.iloc[-1, -1]  # 'Chicago'

# Specific positions
df.iloc[[0, 2], [0, 2]]  # Rows 0 and 2, columns 0 and 2
```

## Key Differences Summary

### Endpoint Inclusion

The most important difference in slicing behavior:

```python title="Slicing endpoint behavior"
df = pd.DataFrame({
    'value': [10, 20, 30, 40]
}, index=['a', 'b', 'c', 'd'])

# loc is INCLUSIVE of endpoint
df.loc['a':'c']  # Includes 'a', 'b', AND 'c'
#    value
# a     10
# b     20
# c     30

# iloc is EXCLUSIVE of endpoint (like Python lists)
df.iloc[0:3]  # Includes 0, 1, 2 (NOT 3)
#    value
# 0     10
# 1     20
# 2     30
```

### What They Accept

```python title="loc vs iloc acceptable inputs"
df = pd.DataFrame(
    {'A': [1, 2], 'B': [3, 4]},
    index=['x', 'y']
)

# loc accepts:
df.loc['x']  # Label
df.loc[['x', 'y']]  # List of labels
df.loc['x':'y']  # Label slice
df.loc[df['A'] > 1]  # Boolean array
df.loc['x', 'A']  # Label for row and column

# iloc accepts:
df.iloc[0]  # Integer position
df.iloc[[0, 1]]  # List of positions
df.iloc[0:2]  # Position slice
df.iloc[0, 0]  # Integer for row and column

# loc does NOT accept integer positions (with non-numeric index)
# iloc does NOT accept labels
```

### With Numeric Index

When your index is numeric, `loc` and `iloc` behave differently:

```python title="Numeric index - where confusion happens"
df = pd.DataFrame(
    {'value': [100, 200, 300]},
    index=[10, 20, 30]
)

#     value
# 10    100
# 20    200
# 30    300

# loc uses index labels (10, 20, 30)
df.loc[10]  # Row with label 10
# value    100

# iloc uses positions (0, 1, 2)
df.iloc[0]  # First row (happens to have label 10)
# value    100

# They give same result here, but for different reasons!

# Slicing shows the difference
df.loc[10:20]  # Labels 10 to 20 (inclusive)
#     value
# 10    100
# 20    200

df.iloc[0:2]  # Positions 0 to 2 (exclusive)
#     value
# 10    100
# 20    200
```

This is where many bugs happen - always be explicit about which you're using.

## Setting Values

Both `loc` and `iloc` can set values:

### Setting with loc

```python title="Setting values with loc"
df = pd.DataFrame({
    'name': ['Alice', 'Bob'],
    'age': [25, 30]
}, index=['a', 'b'])

# Set single value
df.loc['a', 'age'] = 26

# Set entire row
df.loc['a'] = ['Alice Smith', 27]

# Set entire column
df.loc[:, 'age'] = [28, 32]

# Set based on condition
df.loc[df['age'] > 26, 'age'] = 99

# Set multiple cells
df.loc['a', ['name', 'age']] = ['Alice', 30]
```

### Setting with iloc

```python title="Setting values with iloc"
# Set single value by position
df.iloc[0, 1] = 26

# Set entire row
df.iloc[0] = ['Alice Smith', 27]

# Set entire column
df.iloc[:, 1] = [28, 32]

# Set specific cells
df.iloc[0, [0, 1]] = ['Alice', 30]

# Set slice
df.iloc[0:2, 1] = [25, 30]
```

### Conditional Setting

```python title="Conditional value assignment"
df = pd.DataFrame({
    'score': [85, 92, 78, 95],
    'grade': ['', '', '', '']
})

# Assign grades based on scores
df.loc[df['score'] >= 90, 'grade'] = 'A'
df.loc[(df['score'] >= 80) & (df['score'] < 90), 'grade'] = 'B'
df.loc[df['score'] < 80, 'grade'] = 'C'

#    score grade
# 0     85     B
# 1     92     A
# 2     78     C
# 3     95     A
```

This is much cleaner than iterating through rows.

## Advanced Usage

### Boolean Arrays

Use boolean Series/arrays for conditional selection:

```python title="Using boolean masks"
df = pd.DataFrame({
    'product': ['A', 'B', 'C', 'D'],
    'price': [100, 200, 150, 300],
    'stock': [5, 0, 10, 2]
})

# Create boolean mask
in_stock = df['stock'] > 0
expensive = df['price'] > 150

# Use with loc
df.loc[in_stock & expensive, ['product', 'price']]
#   product  price
# 3       D    300

# Masks work with loc but not iloc
# df.iloc[in_stock]  # This won't work!
```

### Callable Selection

Pass functions to `loc` for dynamic selection:

```python title="Callable indexing (advanced)"
# Select using a function
df.loc[lambda x: x['price'] > 150]

# Useful in method chains
result = (df
          .loc[lambda x: x['stock'] > 0]  # Filter in stock
          .loc[:, ['product', 'price']]  # Select columns
          .sort_values('price')  # Sort
          )
```

### MultiIndex Selection

For DataFrames with multiple index levels:

```python title="MultiIndex selection"
# Create MultiIndex DataFrame
df = pd.DataFrame({
    'value': [1, 2, 3, 4]
}, index=pd.MultiIndex.from_tuples([
    ('A', 'x'), ('A', 'y'), ('B', 'x'), ('B', 'y')
], names=['letter', 'symbol']))

# Select by first level
df.loc['A']
#        value
# symbol      
# x          1
# y          2

# Select by both levels
df.loc[('A', 'x')]
# value    1

# Select using slice
df.loc[('A', 'x'):('B', 'x')]

# Cross-section (all 'x' regardless of first level)
df.xs('x', level='symbol')
```

## Common Patterns

### Get First/Last N Rows

```python title="Getting head and tail"
# First 3 rows
df.iloc[:3]  # or df.head(3)

# Last 3 rows  
df.iloc[-3:]  # or df.tail(3)

# All except first row
df.iloc[1:]

# All except last row
df.iloc[:-1]
```

### Get Specific Columns by Position

```python title="Column selection by position"
df = pd.DataFrame({
    'A': [1, 2], 'B': [3, 4], 'C': [5, 6], 'D': [7, 8]
})

# First and last columns
df.iloc[:, [0, -1]]
#    A  D
# 0  1  7
# 1  2  8

# Every other column
df.iloc[:, ::2]
#    A  C
# 0  1  5
# 1  2  6

# Middle columns
df.iloc[:, 1:3]
```

### Random Row Selection

```python title="Random sampling"
# Using iloc with random indices
import numpy as np

random_idx = np.random.choice(len(df), size=5, replace=False)
df.iloc[random_idx]

# Or use pandas sample method (easier)
df.sample(n=5)
```

### Selecting Diagonal Elements

```python title="Diagonal selection (square DataFrame)"
df = pd.DataFrame(np.arange(16).reshape(4, 4))

# Get diagonal using iloc
diagonal = [df.iloc[i, i] for i in range(len(df))]
# [0, 5, 10, 15]

# Or use numpy
np.diag(df.values)
```

## When to Use Which

### Use loc when

- Working with labeled indices (non-numeric or meaningful labels)
- Using boolean conditions to filter
- You want inclusive slicing
- Setting values based on conditions
- Code readability is important (labels are more descriptive)

```python title="Good use cases for loc"
# Meaningful labels
df.loc['2024-01-15', 'sales']

# Conditional filtering
df.loc[df['price'] > 100, 'discount'] = 0.1

# Clear intent
df.loc['Alice', 'age'] = 30
```

### Use iloc when

- Need to select by position (first N rows, last N rows)
- Working with position-based algorithms
- Index labels are arbitrary or don't matter
- Need Python-style slicing (exclusive endpoint)

```python title="Good use cases for iloc"
# Position-based operations
first_10 = df.iloc[:10]
last_row = df.iloc[-1]

# Splitting data
train = df.iloc[:800]
test = df.iloc[800:]

# Column reordering
df = df.iloc[:, [2, 0, 1, 3]]  # Reorder columns by position
```

## Common Mistakes

### Confusing loc and iloc

```python title="Common error - mixing loc and iloc"
df = pd.DataFrame(
    {'value': [1, 2, 3]},
    index=['a', 'b', 'c']
)

# WRONG - using position with loc on non-numeric index
df.loc[0]  # KeyError! No label '0'

# CORRECT
df.iloc[0]  # First row by position
df.loc['a']  # Row with label 'a'
```

### Forgetting Inclusive vs Exclusive

```python title="Common error - slicing confusion"
df = pd.DataFrame({'value': range(10)})

# Expecting 5 rows but getting 6 with loc
df.loc[0:5]  # Returns rows 0, 1, 2, 3, 4, 5 (6 rows!)

# Getting 5 rows with iloc
df.iloc[0:5]  # Returns rows 0, 1, 2, 3, 4 (5 rows)
```

### Chained Indexing

```python title="Common error - chained indexing"
# BAD - might not work as expected
df[df['age'] > 25]['salary'] = 50000  # Warning!

# GOOD - use loc
df.loc[df['age'] > 25, 'salary'] = 50000
```

Chained indexing can create a copy instead of a view, so assignments might not work.

### Not Using Copy

```python title="Common error - modifying views"
# This might modify original df or might not
subset = df.iloc[:5]
subset['new_col'] = 10  # Warning about SettingWithCopyWarning

# BETTER - be explicit
subset = df.iloc[:5].copy()
subset['new_col'] = 10  # Safe, won't affect df
```

## Performance Considerations

```python title="Performance tips"
# For single value access, at[] and iat[] are faster
# (but less flexible)
value = df.at['a', 'age']  # Faster than df.loc['a', 'age']
value = df.iat[0, 1]  # Faster than df.iloc[0, 1]

# For multiple operations, stick with loc/iloc
# The speedup is negligible for most use cases

# Avoid repeatedly calling loc in loops
# BAD
for i in range(len(df)):
    df.loc[i, 'new'] = df.loc[i, 'col1'] * 2  # Slow

# GOOD
df['new'] = df['col1'] * 2  # Vectorized
```

## Quick Reference

**loc - Label-based:**

```python
df.loc['row_label']  # Single row
df.loc['row_label', 'col_label']  # Single cell
df.loc['start':'end']  # Slice (inclusive)
df.loc[['r1', 'r2'], ['c1', 'c2']]  # Multiple rows/cols
df.loc[df['col'] > 5]  # Boolean filter
df.loc[df['col'] > 5, 'other_col']  # Filter + column
```

**`iloc` - Position-based:**

```python
df.iloc[0]  # First row
df.iloc[0, 1]  # First row, second column
df.iloc[0:3]  # Slice (exclusive)
df.iloc[[0, 2], [1, 3]]  # Multiple positions
df.iloc[:, -1]  # Last column
df.iloc[-1, :]  # Last row
```

**Key differences:**

- `loc`: inclusive slicing, uses labels, works with boolean arrays
- `iloc`: exclusive slicing, uses positions, Python-style indexing
- Both can set values and select rows/columns simultaneously
