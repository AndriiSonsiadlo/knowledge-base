---
id: core-concepts
title: Core Concepts
sidebar_label: Core Concepts
tags: [ pandas, data-analysis, python ]
---

# Core Concepts

## Overview

pandas has three fundamental data structures:

- **Series**: 1D labeled array
- **DataFrame**: 2D labeled table
- **Index**: Labels for rows and columns

## Series

A Series is a 1D array with labels (index).

### Creating Series

```python
import pandas as pd

# From list
s = pd.Series([10, 20, 30, 40])
# 0    10
# 1    20
# 2    30
# 3    40

# With custom index
s = pd.Series([10, 20, 30], index=['a', 'b', 'c'])
# a    10
# b    20
# c    30

# From dictionary
s = pd.Series({'a': 10, 'b': 20, 'c': 30})

# From scalar
s = pd.Series(5, index=['a', 'b', 'c'])
# a    5
# b    5
# c    5
```

### Accessing Series Data

```python
s = pd.Series([10, 20, 30], index=['a', 'b', 'c'])

# By label
s['a']  # 10
s[['a', 'c']]  # Multiple values

# By position
s.iloc[0]  # 10
s.iloc[0:2]  # First two

# Boolean indexing
s[s > 15]  # Values greater than 15
```

### Series Attributes

```python
s.values  # NumPy array of values
s.index  # Index object
s.dtype  # Data type
s.shape  # (3,)
s.size  # 3
s.name  # Series name (None by default)
```

### Common Series Operations

```python
s = pd.Series([10, 20, 30])

# Arithmetic
s + 5  # Add 5 to all
s * 2  # Multiply all by 2
s1 + s2  # Element-wise addition

# Statistics
s.mean()
s.sum()
s.std()
s.min()
s.max()

# Sorting
s.sort_values()  # By values
s.sort_index()  # By index

# Unique and counts
s.unique()
s.value_counts()
```

## DataFrame

A DataFrame is a 2D table with labeled rows and columns. Think of it as a dictionary of Series sharing the same index.

### Creating DataFrames

```python
# From dictionary
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['NYC', 'LA', 'Chicago']
})

# From list of lists
df = pd.DataFrame(
    [['Alice', 25], ['Bob', 30]],
    columns=['name', 'age']
)

# From list of dictionaries
df = pd.DataFrame([
    {'name': 'Alice', 'age': 25},
    {'name': 'Bob', 'age': 30}
])

# From NumPy array
import numpy as np

df = pd.DataFrame(
    np.random.randn(3, 2),
    columns=['A', 'B']
)
```

### DataFrame Structure

```python
df = pd.DataFrame({
    'name': ['Alice', 'Bob'],
    'age': [25, 30],
    'city': ['NYC', 'LA']
})

#      name  age  city
# 0   Alice   25   NYC
# 1     Bob   30    LA
```

Each column is a Series:

```python
df['age']  # Series
type(df['age'])  # pandas.core.series.Series
```

### DataFrame Attributes

```python
df.shape  # (rows, columns) e.g., (2, 3)
df.size  # Total elements: 6
df.columns  # Column names
df.index  # Row labels
df.dtypes  # Data type per column
df.info()  # Summary: types, non-null counts, memory
df.describe()  # Statistics for numeric columns
```

### Accessing DataFrame Data

```python
# Columns
df['age']  # Single column (Series)
df[['name', 'age']]  # Multiple columns (DataFrame)

# Rows by position
df.iloc[0]  # First row (Series)
df.iloc[0:2]  # First two rows (DataFrame)

# Rows by label
df.loc[0]  # Row with label 0
df.loc[0:1]  # Rows 0 to 1 (inclusive)

# Specific cells
df.loc[0, 'name']  # Row 0, column 'name'
df.iloc[0, 1]  # Row 0, column 1
```

### Adding and Removing Columns

```python
# Add column
df['country'] = 'USA'  # Scalar
df['age_doubled'] = df['age'] * 2  # From calculation

# Remove column
df.drop('age_doubled', axis=1)  # Returns new DataFrame
df.drop('age_doubled', axis=1, inplace=True)  # Modifies in place
del df['country']  # In-place deletion
```

### Common DataFrame Operations

```python
# Sorting
df.sort_values('age')  # By column
df.sort_values('age', ascending=False)  # Descending
df.sort_index()  # By index

# Filtering
df[df['age'] > 25]  # Boolean condition
df.query('age > 25')  # Query syntax

# Statistics
df.mean()  # Mean of numeric columns
df['age'].sum()  # Sum of one column
df.corr()  # Correlation matrix

# Info
df.head()  # First 5 rows
df.tail(3)  # Last 3 rows
df.sample(2)  # Random 2 rows
```

## Index

The Index is the label for rows (and columns). It enables fast lookups and alignment.

### Index Basics

```python
# Default numeric index
df = pd.DataFrame({'A': [1, 2, 3]})
# Index: RangeIndex(start=0, stop=3, step=1)

# Custom index
df = pd.DataFrame(
    {'A': [1, 2, 3]},
    index=['a', 'b', 'c']
)
# Index: Index(['a', 'b', 'c'], dtype='object')
```

### Setting and Resetting Index

```python
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35]
})

# Set column as index
df.set_index('name')
#          age
# name        
# Alice     25
# Bob       30
# Charlie   35

# Reset index (move index back to column)
df_indexed = df.set_index('name')
df_indexed.reset_index()
#       name  age
# 0    Alice   25
# 1      Bob   30
# 2  Charlie   35

# Drop index when resetting
df_indexed.reset_index(drop=True)
```

### Index Properties

```python
df.index.name  # Name of index
df.index.names  # Names (for MultiIndex)
df.index.is_unique  # Check if unique
df.index.dtype  # Data type
```

### Why Index Matters

**Fast lookups**

```python
df.set_index('name').loc['Alice']  # Fast label-based access
```

**Automatic alignment**

```python
s1 = pd.Series([1, 2], index=['a', 'b'])
s2 = pd.Series([3, 4], index=['b', 'c'])
s1 + s2
# a    NaN
# b    5.0
# c    NaN
```

**Time series indexing**

```python
df.index = pd.to_datetime(df['date'])
df['2024']  # All rows in 2024
df['2024-01']  # All rows in January 2024
```

## Relationship Between Series and DataFrame

A DataFrame is a collection of Series with a shared index:

```python
df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6]
})

# Each column is a Series
df['A']  # Series
df['B']  # Series

# Each row is also a Series
df.iloc[0]  # Series with index ['A', 'B']
```

Converting between them:

```python
# DataFrame to Series
s = df['A']  # Single column
s = df.iloc[0]  # Single row

# Series to DataFrame
df_new = s.to_frame()  # Single column
df_new = s.to_frame(name='column_name')
```

## Common Gotchas

**Views vs Copies**

```python
# This might be a view or a copy
df_subset = df[df['age'] > 25]
df_subset['age'] = 100  # May or may not modify df

# Explicit copy
df_subset = df[df['age'] > 25].copy()
df_subset['age'] = 100  # Won't affect df
```

**Chained Indexing**

```python
# Bad: chained indexing
df[df['age'] > 25]['age'] = 100  # Warning!

# Good: use loc
df.loc[df['age'] > 25, 'age'] = 100
```

**Column Names**

```python
# Avoid spaces in column names
df.columns = ['first name', 'age']  # Can't use df.first name
df.columns = ['first_name', 'age']  # Can use df.first_name
```

## Quick Reference

**Create**

```python
pd.Series([1, 2, 3])
pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
```

**Access**

```python
df['col']  # Column
df.loc[label]  # Row by label
df.iloc[position]  # Row by position
```

**Modify**

```python
df['new'] = values
df.drop('col', axis=1)
df.set_index('col')
df.reset_index()
```

**Info**

```python
df.shape
df.dtypes
df.info()
df.describe()
```
