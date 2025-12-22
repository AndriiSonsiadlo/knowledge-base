---
id: pivot-melt
title: Pivot Tables and Melt
sidebar_label: Pivot & Melt
tags: [pandas, pivot, melt, reshape, pivot-table]
---

# Pivot Tables and Melt

## Overview

Pivot tables and melt are powerful reshaping tools:

- **pivot()**: Reshape long to wide (unique index/column combinations)
- **pivot_table()**: Pivot with aggregation (handles duplicates)
- **melt()**: Reshape wide to long (unpivot)
- **crosstab()**: Create cross-tabulations

## pivot() - Basic Reshaping

Convert rows into columns when data has unique combinations:

```python title="Basic pivot operation"
import pandas as pd

df = pd.DataFrame({
    'date': ['2024-01-01', '2024-01-01', '2024-01-02', '2024-01-02'],
    'product': ['A', 'B', 'A', 'B'],
    'sales': [100, 150, 120, 160]
})

# Pivot: dates as rows, products as columns
result = df.pivot(index='date', columns='product', values='sales')
# product      A    B
# date              
# 2024-01-01  100  150
# 2024-01-02  120  160

# Reset index to make date a regular column
result = result.reset_index()
# product       date    A    B
# 0      2024-01-01  100  150
# 1      2024-01-02  120  160
```

:::warning
`pivot()` requires unique combinations of index and columns. For duplicates, use `pivot_table()` instead.
:::

### Multiple Values

```python title="Pivot multiple value columns"
df = pd.DataFrame({
    'date': ['2024-01-01', '2024-01-02'],
    'product': ['A', 'A'],
    'sales': [100, 120],
    'profit': [20, 25]
})

# Pivot both sales and profit
result = df.pivot(index='date', columns='product', values=['sales', 'profit'])
#            sales profit
# product        A      A
# date                   
# 2024-01-01   100     20
# 2024-01-02   120     25

# Flatten multi-level columns
result.columns = ['_'.join(col) for col in result.columns]
result = result.reset_index()
#          date  sales_A  profit_A
# 0  2024-01-01      100        20
# 1  2024-01-02      120        25
```

## pivot_table() - Aggregating Pivot

Pivot with aggregation for handling duplicate combinations:

```python title="Pivot table with aggregation"
df = pd.DataFrame({
    'date': ['2024-01-01', '2024-01-01', '2024-01-01', '2024-01-02'],
    'product': ['A', 'B', 'A', 'B'],  # 'A' appears twice on 2024-01-01
    'sales': [100, 150, 110, 160]
})

# pivot() would fail due to duplicate (2024-01-01, A)
# Use pivot_table with aggregation
result = pd.pivot_table(
    df,
    index='date',
    columns='product',
    values='sales',
    aggfunc='sum'  # How to handle duplicates
)
# product      A    B
# date              
# 2024-01-01  210  150  # Sum of 100 + 110
# 2024-01-02  NaN  160
```

### Aggregation Functions

```python title="Different aggregation methods"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B', 'A', 'B'],
    'type': ['X', 'Y', 'X', 'Y', 'X', 'Y'],
    'value': [10, 20, 30, 40, 15, 35]
})

# Sum
result = pd.pivot_table(df, index='category', columns='type', 
                        values='value', aggfunc='sum')
# type    X   Y
# category      
# A      25  20
# B      30  75

# Mean
result = pd.pivot_table(df, index='category', columns='type',
                        values='value', aggfunc='mean')

# Count
result = pd.pivot_table(df, index='category', columns='type',
                        values='value', aggfunc='count')

# Multiple aggregations
result = pd.pivot_table(df, index='category', columns='type',
                        values='value', aggfunc=['sum', 'mean', 'count'])
```

### Fill Missing Values

```python title="Handle missing values in pivot"
df = pd.DataFrame({
    'A': ['foo', 'foo', 'bar'],
    'B': ['one', 'two', 'one'],
    'C': [1, 2, 3]
})

# Missing combinations become NaN
result = pd.pivot_table(df, index='A', columns='B', values='C')
# B    one  two
# A            
# bar  3.0  NaN
# foo  1.0  2.0

# Fill NaN with 0
result = pd.pivot_table(df, index='A', columns='B', values='C', fill_value=0)
# B    one  two
# A            
# bar    3    0
# foo    1    2
```

### Margins (Subtotals)

```python title="Add row and column totals"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B'],
    'region': ['East', 'West', 'East', 'West'],
    'sales': [100, 150, 200, 250]
})

result = pd.pivot_table(
    df,
    index='category',
    columns='region',
    values='sales',
    aggfunc='sum',
    margins=True,        # Add totals
    margins_name='Total' # Label for totals row/column
)
# region   East  West  Total
# category                  
# A         100   150    250
# B         200   250    450
# Total     300   400    700
```

:::info
Use `margins=True` to add subtotals and grand totals to your pivot table, similar to Excel pivot tables.
:::

### Multiple Index/Columns

```python title="Hierarchical pivot table"
df = pd.DataFrame({
    'year': [2023, 2023, 2024, 2024],
    'quarter': ['Q1', 'Q2', 'Q1', 'Q2'],
    'region': ['East', 'West', 'East', 'West'],
    'sales': [100, 150, 120, 160]
})

# Multiple row indices
result = pd.pivot_table(
    df,
    index=['year', 'quarter'],
    columns='region',
    values='sales'
)
# region        East  West
# year quarter            
# 2023 Q1        100   NaN
#      Q2        NaN   150
# 2024 Q1        120   NaN
#      Q2        NaN   160
```

## melt() - Wide to Long

Unpivot data from wide to long format:

```python title="Basic melt operation"
df = pd.DataFrame({
    'name': ['Alice', 'Bob'],
    'math': [90, 85],
    'english': [88, 92],
    'science': [95, 87]
})
#     name  math  english  science
# 0  Alice    90       88       95
# 1    Bob    85       92       87

# Melt all columns except name
melted = df.melt(id_vars=['name'])
#     name variable  value
# 0  Alice     math     90
# 1    Bob     math     85
# 2  Alice  english     88
# 3    Bob  english     92
# 4  Alice  science     95
# 5    Bob  science     87
```

### Custom Column Names

```python title="Rename melted columns"
melted = df.melt(
    id_vars=['name'],
    var_name='subject',   # Name for variable column
    value_name='score'    # Name for value column
)
#     name  subject  score
# 0  Alice     math     90
# 1    Bob     math     85
# 2  Alice  english     88
# 3    Bob  english     92
# 4  Alice  science     95
# 5    Bob  science     87
```

### Selective Melting

```python title="Melt specific columns only"
df = pd.DataFrame({
    'student': ['Alice', 'Bob'],
    'class': ['A', 'B'],
    'math': [90, 85],
    'english': [88, 92],
    'science': [95, 87]
})

# Melt only math and english
melted = df.melt(
    id_vars=['student', 'class'],
    value_vars=['math', 'english'],  # Only these columns
    var_name='subject',
    value_name='score'
)
#   student class  subject  score
# 0   Alice     A     math     90
# 1     Bob     B     math     85
# 2   Alice     A  english     88
# 3     Bob     B  english     92
```

## Pivot and Melt Together

### Round Trip Transformation

```python title="Pivot then melt back"
# Start with long format
long = pd.DataFrame({
    'name': ['Alice', 'Alice', 'Bob', 'Bob'],
    'subject': ['math', 'english', 'math', 'english'],
    'score': [90, 88, 85, 92]
})

# Convert to wide
wide = long.pivot(index='name', columns='subject', values='score')
# subject  english  math
# name                  
# Alice         88    90
# Bob           92    85

# Convert back to long
long_again = wide.reset_index().melt(
    id_vars=['name'],
    var_name='subject',
    value_name='score'
)
#     name  subject  score
# 0  Alice  english     88
# 1    Bob  english     92
# 2  Alice     math     90
# 3    Bob     math     85
```

## crosstab() - Frequency Tables

Create cross-tabulation of two or more factors:

```python title="Basic crosstab"
df = pd.DataFrame({
    'gender': ['M', 'F', 'M', 'F', 'M', 'F'],
    'handed': ['R', 'R', 'L', 'R', 'R', 'L'],
    'age': [25, 30, 28, 35, 22, 27]
})

# Count combinations
result = pd.crosstab(df['gender'], df['handed'])
# handed  L  R
# gender      
# F       1  2
# M       1  2

# With margins (totals)
result = pd.crosstab(df['gender'], df['handed'], margins=True)
# handed  L  R  All
# gender          
# F       1  2    3
# M       1  2    3
# All     2  4    6
```

### Crosstab with Values

```python title="Crosstab with aggregation"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B', 'A', 'B'],
    'region': ['East', 'West', 'East', 'West', 'East', 'West'],
    'sales': [100, 150, 200, 250, 120, 280]
})

# Sum sales by category and region
result = pd.crosstab(
    df['category'],
    df['region'],
    values=df['sales'],
    aggfunc='sum'
)
# region   East  West
# category           
# A         220   150
# B         200   530

# Normalize to show percentages
result = pd.crosstab(
    df['category'],
    df['region'],
    normalize='all'  # 'all', 'index', or 'columns'
)
# region      East      West
# category                  
# A       0.333333  0.166667
# B       0.166667  0.333333
```

## Common Patterns

### Sales by Product and Month

```python title="Reshape sales data"
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=60, freq='D'),
    'product': ['A', 'B'] * 30,
    'sales': range(60)
})

# Add month column
df['month'] = df['date'].dt.to_period('M')

# Pivot to see products by month
result = pd.pivot_table(
    df,
    index='month',
    columns='product',
    values='sales',
    aggfunc='sum'
)
# product    A    B
# month           
# 2024-01  465  496
# 2024-02  899  928
```

### Survey Data Transformation

```python title="Reshape survey responses"
# Wide format survey
survey = pd.DataFrame({
    'respondent': [1, 2, 3],
    'q1_rating': [5, 4, 3],
    'q2_rating': [4, 5, 4],
    'q3_rating': [3, 4, 5]
})

# Convert to long format for analysis
long = survey.melt(
    id_vars=['respondent'],
    var_name='question',
    value_name='rating'
)

# Clean question names
long['question'] = long['question'].str.replace('_rating', '')
#    respondent question  rating
# 0           1       q1       5
# 1           2       q1       4
# 2           3       q1       3
# 3           1       q2       4
# 4           2       q2       5
# 5           3       q2       4

# Analyze
long.groupby('question')['rating'].mean()
# question
# q1    4.0
# q2    4.333333
# q3    4.0
```

### Time Series Pivoting

```python title="Pivot time series data"
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=12, freq='M'),
    'metric': ['revenue', 'cost'] * 6,
    'value': [100, 80, 110, 85, 120, 90, 115, 88, 125, 92, 130, 95]
})

# Pivot to have metrics as columns
result = df.pivot(index='date', columns='metric', values='value')
result['profit'] = result['revenue'] - result['cost']

# result:
# metric      cost  revenue  profit
# date                            
# 2024-01-31    80      100      20
# 2024-02-29    85      110      25
# 2024-03-31    90      120      30
```

## Advanced Techniques

### Multi-Level Melt

```python title="Melt with multiple value columns"
df = pd.DataFrame({
    'student': ['Alice', 'Bob'],
    'math_score': [90, 85],
    'math_grade': ['A', 'B'],
    'english_score': [88, 92],
    'english_grade': ['B', 'A']
})

# Melt keeping score and grade together
# First melt scores
scores = df.melt(
    id_vars=['student'],
    value_vars=['math_score', 'english_score'],
    var_name='subject_score',
    value_name='score'
)
scores['subject'] = scores['subject_score'].str.replace('_score', '')

# Then melt grades
grades = df.melt(
    id_vars=['student'],
    value_vars=['math_grade', 'english_grade'],
    var_name='subject_grade',
    value_name='grade'
)
grades['subject'] = grades['subject_grade'].str.replace('_grade', '')

# Merge back together
result = pd.merge(scores[['student', 'subject', 'score']], 
                  grades[['student', 'subject', 'grade']], 
                  on=['student', 'subject'])
```

### Conditional Pivot

```python title="Pivot with conditional values"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B'],
    'metric': ['sales', 'profit', 'sales', 'profit'],
    'value': [100, 20, 200, 40]
})

# Pivot
result = df.pivot(index='category', columns='metric', values='value')

# Calculate profit margin
result['margin'] = (result['profit'] / result['sales'] * 100).round(2)
# metric      profit  sales  margin
# category                         
# A               20    100    20.0
# B               40    200    20.0
```

## Performance Tips

```python title="Optimize pivot operations"
# For large DataFrames, use categorical for repeated values
df['category'] = df['category'].astype('category')
df['region'] = df['region'].astype('category')

# Then pivot
result = pd.pivot_table(df, index='category', columns='region', values='sales')

# Use observed=True in groupby before pivot
# (Faster with categorical data)
```

:::success
Convert columns to categorical before pivoting if they have many repeated values. This significantly improves performance and reduces memory usage.
:::

## Common Mistakes

### Pivot with Duplicates

```python title="Handle duplicate index-column combinations"
df = pd.DataFrame({
    'A': ['foo', 'foo', 'foo'],
    'B': ['one', 'one', 'two'],
    'C': [1, 2, 3]
})

# This fails - duplicate (foo, one)
# df.pivot(index='A', columns='B', values='C')  # ValueError!

# Use pivot_table instead
result = pd.pivot_table(df, index='A', columns='B', values='C', aggfunc='sum')
# B    one  two
# A            
# foo    3    3
```

### Forgetting reset_index()

```python title="Reset index after pivot"
# Pivot creates index
result = df.pivot(index='date', columns='product', values='sales')
# product  A    B
# date          
# 2024-01  100  150

# Index makes filtering harder
# result[result['date'] == '2024-01']  # Error! date is index

# Reset to make date a column
result = result.reset_index()
# Now can filter: result[result['date'] == '2024-01']
```

### Column Name Confusion

```python title="Handle multi-level column names"
df = pd.DataFrame({
    'date': ['2024-01-01', '2024-01-02'],
    'product': ['A', 'A'],
    'sales': [100, 120],
    'profit': [20, 25]
})

result = df.pivot(index='date', columns='product', values=['sales', 'profit'])
# Multi-level columns: ('sales', 'A'), ('profit', 'A')

# Flatten column names
result.columns = ['_'.join(col) for col in result.columns]
# Now: sales_A, profit_A
```

## Quick Reference

**Pivot (unique combinations):**

```python
df.pivot(index='row', columns='col', values='val')
df.pivot(index='row', columns='col', values=['val1', 'val2'])
```

**Pivot table (with aggregation):**

```python
pd.pivot_table(df, index='row', columns='col', values='val', aggfunc='sum')
pd.pivot_table(df, index='row', columns='col', aggfunc=['sum', 'mean'])
pd.pivot_table(df, index='row', columns='col', fill_value=0)
pd.pivot_table(df, index='row', columns='col', margins=True)
```

**Melt (wide to long):**

```python
df.melt(id_vars=['id'])
df.melt(id_vars=['id'], value_vars=['col1', 'col2'])
df.melt(id_vars=['id'], var_name='variable', value_name='value')
```

**Crosstab:**

```python
pd.crosstab(df['row'], df['col'])
pd.crosstab(df['row'], df['col'], values=df['val'], aggfunc='sum')
pd.crosstab(df['row'], df['col'], normalize='all')
pd.crosstab(df['row'], df['col'], margins=True)
```

**Common patterns:**

```python
# Pivot then calculate
wide = df.pivot(index='date', columns='product', values='sales')
wide['total'] = wide.sum(axis=1)

# Melt then aggregate
long = df.melt(id_vars=['id'])
long.groupby('variable')['value'].mean()

# Round trip
wide = long.pivot(index='id', columns='var', values='val')
long = wide.reset_index().melt(id_vars=['id'])

# Flatten multi-level columns
df.columns = ['_'.join(col) for col in df.columns]
```
