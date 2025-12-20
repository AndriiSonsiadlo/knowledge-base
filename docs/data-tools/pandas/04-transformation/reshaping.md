---
id: reshaping
title: Reshaping Data
sidebar_label: Reshaping
tags: [pandas, reshape, pivot, melt, stack, unstack]
---

# Reshaping Data

## Overview

Reshaping transforms data between wide and long formats. Common operations:

- **Wide to Long**: `melt()`, `stack()`
- **Long to Wide**: `pivot()`, `pivot_table()`, `unstack()`
- **Other**: `transpose()`, `explode()`

## Wide vs Long Format

```python title="Wide vs Long format examples"
import pandas as pd

# Wide format (each variable is a column)
wide = pd.DataFrame({
    'name': ['Alice', 'Bob'],
    'math': [90, 85],
    'english': [88, 92]
})
#     name  math  english
# 0  Alice    90       88
# 1    Bob    85       92

# Long format (one row per observation)
long = pd.DataFrame({
    'name': ['Alice', 'Alice', 'Bob', 'Bob'],
    'subject': ['math', 'english', 'math', 'english'],
    'score': [90, 88, 85, 92]
})
#     name  subject  score
# 0  Alice     math     90
# 1  Alice  english     88
# 2    Bob     math     85
# 3    Bob  english     92
```

:::info
**Wide format**: Easy to read, good for display
**Long format**: Better for analysis, required by many plotting libraries
:::

## melt() - Wide to Long

Convert columns into rows:

```python title="Basic melt"
df = pd.DataFrame({
    'name': ['Alice', 'Bob'],
    'math': [90, 85],
    'english': [88, 92],
    'science': [95, 87]
})

# Melt all columns except 'name'
melted = df.melt(id_vars=['name'])
#     name variable  value
# 0  Alice     math     90
# 1    Bob     math     85
# 2  Alice  english     88
# 3    Bob  english     92
# 4  Alice  science     95
# 5    Bob  science     87

# Melt specific columns
melted = df.melt(
    id_vars=['name'],
    value_vars=['math', 'english']  # Only these columns
)
```

### Custom Column Names

```python title="Rename melt output columns"
df = pd.DataFrame({
    'student': ['Alice', 'Bob'],
    'q1': [90, 85],
    'q2': [88, 92],
    'q3': [95, 87]
})

melted = df.melt(
    id_vars=['student'],
    var_name='quarter',      # Name for the variable column
    value_name='score'       # Name for the value column
)
#   student quarter  score
# 0   Alice      q1     90
# 1     Bob      q1     85
# 2   Alice      q2     88
# 3     Bob      q2     92
# 4   Alice      q3     95
# 5     Bob      q3     87
```

### Multiple ID Variables

```python title="Melt with multiple identifier columns"
df = pd.DataFrame({
    'name': ['Alice', 'Bob'],
    'class': ['A', 'B'],
    'math': [90, 85],
    'english': [88, 92]
})

melted = df.melt(
    id_vars=['name', 'class'],  # Keep both as identifiers
    var_name='subject',
    value_name='score'
)
#     name class  subject  score
# 0  Alice     A     math     90
# 1    Bob     B     math     85
# 2  Alice     A  english     88
# 3    Bob     B  english     92
```

## pivot() - Long to Wide

Convert rows into columns (inverse of melt):

```python title="Basic pivot"
df = pd.DataFrame({
    'name': ['Alice', 'Alice', 'Bob', 'Bob'],
    'subject': ['math', 'english', 'math', 'english'],
    'score': [90, 88, 85, 92]
})

# Pivot to wide format
wide = df.pivot(
    index='name',         # Rows
    columns='subject',    # New columns
    values='score'        # Values to fill
)
# subject  english  math
# name                  
# Alice         88    90
# Bob           92    85

# Reset index to make 'name' a column again
wide = wide.reset_index()
# subject    name  english  math
# 0         Alice       88    90
# 1           Bob       92    85
```

:::warning
`pivot()` requires unique combinations of index and columns. Use `pivot_table()` for duplicate combinations.
:::

### Pivot with Multiple Values

```python title="Pivot multiple value columns"
df = pd.DataFrame({
    'student': ['Alice', 'Alice', 'Bob', 'Bob'],
    'subject': ['math', 'english', 'math', 'english'],
    'score': [90, 88, 85, 92],
    'grade': ['A', 'B', 'B', 'A']
})

# Pivot both score and grade
wide = df.pivot(
    index='student',
    columns='subject',
    values=['score', 'grade']
)
#         score       grade      
# subject english math english math
# student                         
# Alice        88   90       B    A
# Bob          92   85       A    B
```

## pivot_table() - Aggregating Pivot

Like pivot but handles duplicates by aggregating:

```python title="Pivot with aggregation"
df = pd.DataFrame({
    'date': ['2024-01-01', '2024-01-01', '2024-01-02', '2024-01-02'],
    'product': ['A', 'A', 'A', 'B'],
    'sales': [100, 150, 200, 300]
})

# Duplicate combinations exist (2024-01-01, A appears twice)
# pivot() would fail, use pivot_table()
result = df.pivot_table(
    index='date',
    columns='product',
    values='sales',
    aggfunc='sum'  # How to aggregate duplicates
)
# product      A      B
# date                 
# 2024-01-01 250.0    NaN
# 2024-01-02 200.0  300.0
```

### Aggregation Functions

```python title="Different aggregation functions"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B', 'A', 'B'],
    'type': ['X', 'Y', 'X', 'Y', 'X', 'Y'],
    'value': [10, 20, 30, 40, 15, 35]
})

# Sum
result = df.pivot_table(
    index='category',
    columns='type',
    values='value',
    aggfunc='sum'
)
# type    X   Y
# category      
# A      25  20
# B      30  75

# Mean
result = df.pivot_table(
    index='category',
    columns='type',
    values='value',
    aggfunc='mean'
)

# Multiple aggregations
result = df.pivot_table(
    index='category',
    columns='type',
    values='value',
    aggfunc=['sum', 'mean', 'count']
)
```

### Fill Missing Values

```python title="Handle missing values in pivot"
df = pd.DataFrame({
    'A': ['foo', 'foo', 'bar'],
    'B': ['one', 'two', 'one'],
    'C': [1, 2, 3]
})

result = df.pivot_table(
    index='A',
    columns='B',
    values='C',
    fill_value=0  # Replace NaN with 0
)
# B    one  two
# A            
# bar    3    0
# foo    1    2
```

### Margins (Totals)

```python title="Add row and column totals"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B'],
    'type': ['X', 'Y', 'X', 'Y'],
    'value': [10, 20, 30, 40]
})

result = df.pivot_table(
    index='category',
    columns='type',
    values='value',
    aggfunc='sum',
    margins=True,      # Add totals
    margins_name='Total'  # Label for totals
)
# type      X   Y  Total
# category              
# A        10  20     30
# B        30  40     70
# Total    40  60    100
```

## stack() and unstack()

Work with MultiIndex DataFrames:

### stack() - Columns to Rows

```python title="Stack columns into rows"
df = pd.DataFrame({
    'math': [90, 85],
    'english': [88, 92]
}, index=['Alice', 'Bob'])
#        math  english
# Alice    90       88
# Bob      85       92

# Stack columns into index
stacked = df.stack()
# Alice  math       90
#        english    88
# Bob    math       85
#        english    92
# dtype: int64

# Result is a Series with MultiIndex
type(stacked)  # Series
```

### unstack() - Rows to Columns

```python title="Unstack index into columns"
df = pd.DataFrame({
    'value': [90, 88, 85, 92]
}, index=pd.MultiIndex.from_tuples([
    ('Alice', 'math'),
    ('Alice', 'english'),
    ('Bob', 'math'),
    ('Bob', 'english')
]))

# Unstack inner level
unstacked = df.unstack()
#        value          
#       english math
# Alice      88   90
# Bob        92   85

# Unstack specific level
unstacked = df.unstack(level=0)
#            value        
#            Alice   Bob
# english       88    92
# math          90    85
```

### Stack/Unstack Levels

```python title="Control which level to stack/unstack"
df = pd.DataFrame({
    'A': [1, 2],
    'B': [3, 4],
    'C': [5, 6]
}, index=pd.Index(['X', 'Y'], name='idx'))

# Stack (default: last level)
stacked = df.stack()
# idx   
# X    A    1
#      B    3
#      C    5
# Y    A    2
#      B    4
#      C    6

# Unstack to get back
stacked.unstack()
#      A  B  C
# idx         
# X    1  3  5
# Y    2  4  6
```

## transpose()

Swap rows and columns:

```python title="Transpose DataFrame"
df = pd.DataFrame({
    'Alice': [90, 88],
    'Bob': [85, 92]
}, index=['math', 'english'])
#         Alice  Bob
# math       90   85
# english    88   92

# Transpose
df_t = df.T
#        math  english
# Alice    90       88
# Bob      85       92

# Shorthand
df_t = df.transpose()
```

:::info
Transpose is useful for switching between student-as-columns and subject-as-columns formats.
:::

## explode()

Expand lists in cells into separate rows:

```python title="Explode lists into rows"
df = pd.DataFrame({
    'name': ['Alice', 'Bob'],
    'hobbies': [['reading', 'swimming'], ['gaming', 'cooking', 'hiking']]
})
#     name                   hobbies
# 0  Alice      [reading, swimming]
# 1    Bob  [gaming, cooking, hiking]

# Explode hobbies into separate rows
exploded = df.explode('hobbies')
#     name   hobbies
# 0  Alice   reading
# 0  Alice  swimming
# 1    Bob    gaming
# 1    Bob   cooking
# 1    Bob    hiking

# Reset index
exploded = exploded.reset_index(drop=True)
```

### Explode Multiple Columns

```python title="Explode multiple columns simultaneously"
df = pd.DataFrame({
    'name': ['Alice', 'Bob'],
    'scores': [[90, 88], [85, 92]],
    'subjects': [['math', 'english'], ['math', 'english']]
})

# Explode both columns together
exploded = df.explode(['scores', 'subjects'])
#     name scores subjects
# 0  Alice     90     math
# 0  Alice     88  english
# 1    Bob     85     math
# 1    Bob     92  english
```

## Common Reshaping Patterns

### Sales Data: Wide to Long

```python title="Reshape sales data for analysis"
df = pd.DataFrame({
    'product': ['A', 'B', 'C'],
    'Q1': [100, 200, 150],
    'Q2': [120, 180, 160],
    'Q3': [110, 220, 170],
    'Q4': [130, 210, 180]
})

# Melt quarters into single column
sales_long = df.melt(
    id_vars=['product'],
    var_name='quarter',
    value_name='sales'
)
#   product quarter  sales
# 0       A      Q1    100
# 1       B      Q1    200
# 2       C      Q1    150
# ...

# Now easy to plot or analyze by quarter
sales_long.groupby('quarter')['sales'].sum()
```

### Survey Data: Long to Wide

```python title="Pivot survey responses"
df = pd.DataFrame({
    'respondent': [1, 1, 1, 2, 2, 2],
    'question': ['Q1', 'Q2', 'Q3', 'Q1', 'Q2', 'Q3'],
    'answer': [5, 4, 3, 4, 5, 4]
})

# One column per question
survey_wide = df.pivot(
    index='respondent',
    columns='question',
    values='answer'
)
# question  Q1  Q2  Q3
# respondent            
# 1          5   4   3
# 2          4   5   4
```

### Time Series: Unstacking

```python title="Reshape time series data"
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=6, freq='D'),
    'metric': ['sales', 'costs'] * 3,
    'value': [100, 80, 120, 85, 110, 90]
})

# Pivot to have metrics as columns
ts_wide = df.pivot(
    index='date',
    columns='metric',
    values='value'
)
# metric      costs  sales
# date                    
# 2024-01-01     80    100
# 2024-01-02     85    120
# 2024-01-03     90    110

# Now can easily calculate profit
ts_wide['profit'] = ts_wide['sales'] - ts_wide['costs']
```

### Combining Reshaping Operations

```python title="Chain reshaping operations"
df = pd.DataFrame({
    'id': [1, 2],
    'name': ['Alice', 'Bob'],
    'scores': [[90, 88, 95], [85, 92, 87]]
})

# Explode then separate
result = (df
    .explode('scores')
    .reset_index(drop=True)
    .assign(subject=['math', 'english', 'science'] * 2)
)
#    id   name scores  subject
# 0   1  Alice     90     math
# 1   1  Alice     88  english
# 2   1  Alice     95  science
# 3   2    Bob     85     math
# 4   2    Bob     92  english
# 5   2    Bob     87  science
```

## MultiIndex Reshaping

### Creating MultiIndex

```python title="Reshape with MultiIndex"
df = pd.DataFrame({
    'year': [2023, 2023, 2024, 2024],
    'quarter': ['Q1', 'Q2', 'Q1', 'Q2'],
    'sales': [100, 120, 110, 130]
})

# Set MultiIndex
df = df.set_index(['year', 'quarter'])
#              sales
# year quarter      
# 2023 Q1        100
#      Q2        120
# 2024 Q1        110
#      Q2        130

# Unstack quarter
wide = df.unstack('quarter')
#       sales    
# quarter   Q1   Q2
# year            
# 2023     100  120
# 2024     110  130
```

### Working with MultiIndex Columns

```python title="Flatten MultiIndex columns"
df = pd.DataFrame({
    ('A', 'x'): [1, 2],
    ('A', 'y'): [3, 4],
    ('B', 'x'): [5, 6],
    ('B', 'y'): [7, 8]
})

# Flatten column names
df.columns = ['_'.join(col) for col in df.columns]
#    A_x  A_y  B_x  B_y
# 0    1    3    5    7
# 1    2    4    6    8
```

## Performance Tips

```python title="Efficient reshaping"
# For large DataFrames, avoid repeated melts
# Bad
for col in columns:
    df_temp = df.melt(id_vars=['id'], value_vars=[col])
    # Process each

# Good
df_long = df.melt(id_vars=['id'], value_vars=columns)
# Process once

# Use categorical for repeated values after melt
df_long['variable'] = df_long['variable'].astype('category')
```

:::success
After melting, convert the 'variable' column to categorical to save memory if you have many rows.
:::

## Common Mistakes

### Pivot with Duplicates

```python title="Handling duplicate index-column combinations"
df = pd.DataFrame({
    'A': ['foo', 'foo', 'foo'],
    'B': ['one', 'one', 'two'],
    'C': [1, 2, 3]
})

# This fails - duplicate (foo, one)
# df.pivot(index='A', columns='B', values='C')  # ValueError!

# Use pivot_table instead
df.pivot_table(index='A', columns='B', values='C', aggfunc='sum')
# B    one  two
# A            
# foo    3    3
```

### Forgetting to Reset Index

```python title="Reset index after pivot"
# Pivot creates index from 'name'
pivoted = df.pivot(index='name', columns='subject', values='score')
# subject  english  math
# name                  
# Alice         88    90
# Bob           92    85

# Reset to make 'name' a regular column
pivoted = pivoted.reset_index()
# subject    name  english  math
# 0         Alice       88    90
# 1           Bob       92    85
```

### Column Name Conflicts

```python title="Handle column name collisions"
df = pd.DataFrame({
    'name': ['Alice', 'Bob'],
    'variable': ['math', 'english'],
    'value': [90, 85]
})

# Melt creates 'variable' and 'value' columns
# But 'variable' already exists!
melted = df.melt(
    id_vars=['name'],
    var_name='metric',      # Use different name
    value_name='score'      # Use different name
)
```

## Quick Reference

**Wide to Long:**

```python
df.melt(id_vars=['id'], var_name='var', value_name='val')
df.stack()                          # Columns to index
```

**Long to Wide:**

```python
df.pivot(index='row', columns='col', values='val')
df.pivot_table(index='row', columns='col', aggfunc='sum')
df.unstack()                        # Index to columns
```

**Other:**

```python
df.T                                # Transpose
df.transpose()                      # Transpose
df.explode('col')                   # Lists to rows
```

**Common patterns:**

```python
# Melt all except ID columns
df.melt(id_vars=['id'])

# Pivot with aggregation
df.pivot_table(index='A', columns='B', values='C', aggfunc='mean')

# Stack/unstack MultiIndex
df.stack(level=-1)
df.unstack(level=0)

# Explode and reshape
df.explode('list_col').pivot(...)

# Reset index after pivot
df.pivot(...).reset_index()
```

**Memory optimization:**

```python
# After melt, convert to category
df_long['variable'] = df_long['variable'].astype('category')
```
