---
id: selecting-columns
title: Selecting Columns
sidebar_label: Selecting Columns
tags: [ pandas, columns, selection, dataframe ]
---

# Selecting Columns

## Overview

Column selection is one of the most common operations in **_pandas_**. There are several ways to
select columns, each with different use cases and behaviors.

The main approaches:

- Bracket notation: `df['col']` or `df[['col1', 'col2']]`
- Dot notation: `df.col`
- loc/iloc: `df.loc[:, 'col']` or `df.iloc[:, 0]`
- Column methods: `filter()`, `select_dtypes()`

## Single Column Selection

### Bracket Notation (Recommended)

The most common way to select a single column:

```python title="Single column with brackets - returns Series"
import pandas as pd

df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['NYC', 'LA', 'Chicago']
})

# Returns a Series
column = df['age']
type(column)  # pandas.core.series.Series

print(column)
# 0    25
# 1    30
# 2    35
# Name: age, dtype: int64
```

A single bracket returns a Series, which is a 1D labeled array.

### Dot Notation (Convenient but Limited)

Access columns as attributes:

```python title="Dot notation - convenient for simple names"
# Same as df['age']
df.age

# Works for exploration and quick access
df.name
df.city
```

**Limitations of dot notation:**

```python title="When dot notation doesn't work"
# Column names with spaces
df['first name']  # Works
df.first
name  # SyntaxError!

# Column names that match DataFrame methods
df['count']  # Works
df.count  # Returns a method, not the column!

# Column names starting with numbers
df['2024_sales']  # Works
df
.2024
_sales  # SyntaxError!

# Setting new columns
df['new_col'] = 10  # Works
df.new_col = 10  # Creates an attribute, not a column!
```

Use dot notation for quick exploration, but stick to brackets for robust code.

### With loc

Select a column using loc (returns Series):

```python title="Single column with loc"
# All rows, single column
df.loc[:, 'age']

# This is equivalent to df['age']
# Use loc when you're also filtering rows:
df.loc[df['age'] > 28, 'name']
```

## Multiple Column Selection

### Double Brackets (Returns DataFrame)

Pass a list of column names to get a DataFrame:

```python title="Multiple columns - returns DataFrame"
# Select two columns
df[['name', 'city']]
#       name     city
# 0    Alice      NYC
# 1      Bob       LA
# 2  Charlie  Chicago

type(df[['name', 'city']])  # pandas.core.frame.DataFrame

# Even a single column in double brackets returns DataFrame
df[['name']]  # DataFrame with one column
df['name']  # Series
```

The double bracket returns a DataFrame, which maintains the 2D structure.

### Column Order

The order in the list determines the column order in the result:

```python title="Reordering columns during selection"
# Original order: name, age, city
df[['city', 'name', 'age']]
#       city     name  age
# 0      NYC    Alice   25
# 1       LA      Bob   30
# 2  Chicago  Charlie   35

# Useful for rearranging columns
df = df[['age', 'name', 'city']]  # Reorder permanently
```

### With loc

Select multiple columns using loc:

```python title="Multiple columns with loc"
# All rows, specific columns
df.loc[:, ['name', 'city']]

# Combined with row filtering
df.loc[df['age'] > 28, ['name', 'city']]
#       name     city
# 1      Bob       LA
# 2  Charlie  Chicago
```

## Column Slicing

### Slice by Label

Select a range of columns using slices:

```python title="Column slicing with loc (inclusive)"
df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'C': [7, 8, 9],
    'D': [10, 11, 12]
})

# Select columns from B to D (inclusive)
df.loc[:, 'B':'D']
#    B  C   D
# 0  4  7  10
# 1  5  8  11
# 2  6  9  12

# Note: This is inclusive on both ends
# df.loc[:, 'B':'D'] includes B, C, AND D
```

Remember: loc slicing is inclusive, unlike Python's standard slicing.

### Slice by Position

Use iloc to slice by column position:

```python title="Column slicing with iloc (exclusive)"
# First two columns (positions 0 and 1)
df.iloc[:, 0:2]
#    A  B
# 0  1  4
# 1  2  5
# 2  3  6

# Last two columns
df.iloc[:, -2:]

# Every other column
df.iloc[:, ::2]
#    A  C
# 0  1  7
# 1  2  8
# 2  3  9

# All except first column
df.iloc[:, 1:]
```

This follows Python's standard slicing rules (exclusive endpoint).

## Column Selection by Type

### select_dtypes()

Select columns based on their data type:

```python title="Select columns by data type"
df = pd.DataFrame({
    'name': ['Alice', 'Bob'],
    'age': [25, 30],
    'salary': [50000.0, 60000.0],
    'hired': pd.to_datetime(['2020-01-15', '2019-03-20']),
    'active': [True, False]
})

# Select numeric columns
df.select_dtypes(include=['number'])
#    age   salary
# 0   25  50000.0
# 1   30  60000.0

# Select only integers
df.select_dtypes(include=['int64'])
#    age
# 0   25
# 1   30

# Select only floats
df.select_dtypes(include=['float64'])
#     salary
# 0  50000.0
# 1  60000.0

# Select string columns
df.select_dtypes(include=['object'])
#     name
# 0  Alice
# 1    Bob

# Select datetime columns
df.select_dtypes(include=['datetime64'])
#        hired
# 0 2020-01-15
# 1 2019-03-20

# Select boolean columns
df.select_dtypes(include=['bool'])
#    active
# 0    True
# 1   False
```

This is extremely useful when you want to apply operations only to specific types.

### Exclude Data Types

```python title="Exclude columns by data type"
# Everything except numbers
df.select_dtypes(exclude=['number'])
#     name      hired  active
# 0  Alice 2020-01-15    True
# 1    Bob 2019-03-20   False

# Everything except strings
df.select_dtypes(exclude=['object'])
#    age   salary      hired  active
# 0   25  50000.0 2020-01-15    True
# 1   30  60000.0 2019-03-20   False
```

### Multiple Types

```python title="Select multiple data types"
# Select both integers and floats
df.select_dtypes(include=['int64', 'float64'])
#    age   salary
# 0   25  50000.0
# 1   30  60000.0

# Or use general category
df.select_dtypes(include=['number'])  # Same result
```

Common type categories:

- `'number'`: All numeric types (int, float)
- `'object'`: String/mixed types
- `'datetime64'`: Datetime types
- `'bool'`: Boolean
- `'category'`: Categorical

## Column Selection by Pattern

### filter() Method

Select columns using pattern matching:

```python title="Filter columns by name pattern"
df = pd.DataFrame({
    'sales_2023': [100, 200],
    'sales_2024': [150, 250],
    'cost_2023': [50, 80],
    'cost_2024': [60, 90],
    'profit': [50, 120]
})

# Columns containing 'sales'
df.filter(like='sales')
#    sales_2023  sales_2024
# 0         100         150
# 1         200         250

# Columns starting with 'cost'
df.filter(regex='^cost')
#    cost_2023  cost_2024
# 0         50         60
# 1         80         90

# Columns ending with '2024'
df.filter(regex='2024$')
#    sales_2024  cost_2024
# 0         150         60
# 1         250         90

# Exact match (using items parameter)
df.filter(items=['sales_2023', 'profit'])
#    sales_2023  profit
# 0         100      50
# 1         200     120
```

The regex parameter is powerful for complex patterns.

### List Comprehension

More flexible pattern matching:

```python title="Using list comprehension for column selection"
# Columns containing '2023'
cols_2023 = [col for col in df.columns if '2023' in col]
df[cols_2023]
#    sales_2023  cost_2023
# 0         100         50
# 1         200         80

# Columns starting with 's'
s_cols = [col for col in df.columns if col.startswith('s')]
df[s_cols]

# Columns with more than 10 characters
long_cols = [col for col in df.columns if len(col) > 10]
df[long_cols]

# Custom logic
numeric_name_cols = [col for col in df.columns if any(char.isdigit() for char in col)]
df[numeric_name_cols]
```

## Conditional Column Selection

### Select Based on Column Content

Choose columns based on their values:

```python title="Select columns with specific characteristics"
df = pd.DataFrame({
    'A': [1, 2, 3, 4, 5],
    'B': [0, 0, 0, 0, 0],
    'C': [10, 20, 30, 40, 50],
    'D': [1, 1, 1, 1, 1]
})

# Columns with any non-zero values
non_zero_cols = df.columns[(df != 0).any()]
df[non_zero_cols]
#    A   C  D
# 0  1  10  1
# 1  2  20  1
# 2  3  30  1

# Columns with variance > 0 (non-constant)
variable_cols = df.columns[df.var() > 0]
df[variable_cols]
#    A   C
# 0  1  10
# 1  2  20
# 2  3  30

# Columns with missing values
null_cols = df.columns[df.isnull().any()]
df[null_cols]

# Columns with all unique values
unique_cols = df.columns[df.nunique() == len(df)]
df[unique_cols]
```

This helps identify and select meaningful columns automatically.

### Select Based on Statistics

```python title="Select columns by statistical properties"
# Columns with mean > 10
high_mean_cols = df.columns[df.mean() > 10]
df[high_mean_cols]

# Columns with max value > 30
high_max_cols = df.columns[df.max() > 30]
df[high_max_cols]

# Columns with standard deviation > 5
high_std_cols = df.columns[df.std() > 5]
df[high_std_cols]
```

## Dropping Columns

### drop() Method

Remove columns by name:

```python title="Dropping columns"
df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'C': [7, 8, 9]
})

# Drop single column (returns new DataFrame)
df.drop('B', axis=1)
#    A  C
# 0  1  7
# 1  2  8
# 2  3  9

# Drop multiple columns
df.drop(['A', 'C'], axis=1)
#    B
# 0  4
# 1  5
# 2  6

# Drop in place (modifies original)
df.drop('B', axis=1, inplace=True)

# Using columns parameter (clearer)
df.drop(columns=['B', 'C'])
```

### Selecting What to Keep

Sometimes it's easier to select what you want to keep:

```python title="Keep vs drop approach"
df = pd.DataFrame({
    'A': [1, 2], 'B': [3, 4], 'C': [5, 6],
    'D': [7, 8], 'E': [9, 10]
})

# If you want to drop many columns, keeping is easier
# Drop A, B, C, D (keep only E)
df.drop(['A', 'B', 'C', 'D'], axis=1)  # Verbose

# Better: just select E
df[['E']]  # Clearer intent

# Keep A and E, drop the rest
df[['A', 'E']]
```

## Reordering Columns

### Explicit Order

Reorder columns by listing them in desired order:

```python title="Reordering columns"
df = pd.DataFrame({
    'age': [25, 30],
    'name': ['Alice', 'Bob'],
    'city': ['NYC', 'LA']
})

# Reorder to: name, age, city
df = df[['name', 'age', 'city']]
#     name  age city
# 0  Alice   25  NYC
# 1    Bob   30   LA
```

### Move Specific Column to Front

```python title="Move column to beginning"
# Move 'age' to first position
cols = ['age'] + [col for col in df.columns if col != 'age']
df = df[cols]


# Or using a function
def move_column_to_front(df, col_name):
    cols = [col_name] + [col for col in df.columns if col != col_name]
    return df[cols]


df = move_column_to_front(df, 'city')
```

### Sort Columns Alphabetically

```python title="Sort columns by name"
# Alphabetical order
df = df[sorted(df.columns)]

# Reverse alphabetical
df = df[sorted(df.columns, reverse=True)]
```

## Advanced Column Selection

### Dynamic Column Selection

Select columns programmatically:

```python title="Dynamic column selection based on logic"
df = pd.DataFrame({
    'id': [1, 2, 3],
    'user_name': ['Alice', 'Bob', 'Charlie'],
    'user_age': [25, 30, 35],
    'user_city': ['NYC', 'LA', 'Chicago'],
    'admin_role': ['yes', 'no', 'yes']
})

# All columns starting with 'user_'
user_cols = [col for col in df.columns if col.startswith('user_')]
df[user_cols]
#    user_name  user_age user_city
# 0      Alice        25       NYC
# 1        Bob        30        LA
# 2    Charlie        35   Chicago

# All columns except 'id'
non_id_cols = [col for col in df.columns if col != 'id']
df[non_id_cols]

# Columns with specific keywords
keywords = ['name', 'age']
relevant_cols = [col for col in df.columns if any(kw in col for kw in keywords)]
df[relevant_cols]
```

### Column Selection with Index

Sometimes you need to work with column positions:

```python title="Column selection by index position"
# Get column names by position
first_col = df.columns[0]
last_col = df.columns[-1]

# Select first 3 columns by position
first_three = df[df.columns[:3]]

# Select every other column
every_other = df[df.columns[::2]]

# Select specific positions
positions = [0, 2, 4]
selected = df[df.columns[positions]]
```

## Combining Selection Methods

### Filter Rows and Select Columns

Combine boolean filtering with column selection:

```python title="Combined row and column selection"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'David'],
    'age': [25, 30, 35, 28],
    'city': ['NYC', 'LA', 'NYC', 'Chicago'],
    'salary': [50000, 60000, 70000, 55000]
})

# Method 1: Using loc (recommended)
df.loc[df['age'] > 28, ['name', 'salary']]
#       name  salary
# 1      Bob   60000
# 2  Charlie   70000

# Method 2: Filter then select
filtered = df[df['age'] > 28]
result = filtered[['name', 'salary']]

# Method 3: Chain operations
result = df[df['age'] > 28][['name', 'salary']]
```

The loc approach is generally cleaner and more efficient.

### Type-Based Operations

```python title="Operations on specific column types"
df = pd.DataFrame({
    'name': ['Alice', 'Bob'],
    'age': [25, 30],
    'salary': [50000, 60000],
    'bonus': [5000, 6000]
})

# Apply operation only to numeric columns
numeric_cols = df.select_dtypes(include=['number'])
df[numeric_cols.columns] = numeric_cols * 1.1  # 10% increase

# Or more directly
df[df.select_dtypes(include=['number']).columns] *= 1.1
```

## Common Patterns

### Exclude Certain Columns

```python title="Exclude specific columns"
df = pd.DataFrame({
    'A': [1, 2], 'B': [3, 4], 'C': [5, 6], 'D': [7, 8]
})

# Keep everything except B and D
exclude = ['B', 'D']
keep_cols = [col for col in df.columns if col not in exclude]
df[keep_cols]
#    A  C
# 0  1  5
# 1  2  6

# Or use difference
keep_cols = df.columns.difference(exclude)
df[keep_cols]
```

### Select Columns Matching Multiple Patterns

```python title="OR pattern matching"
df = pd.DataFrame({
    'sales_q1': [100], 'sales_q2': [200],
    'cost_q1': [50], 'cost_q2': [80],
    'profit_q1': [50], 'profit_q2': [120]
})

# Columns containing 'sales' OR 'profit'
cols = [col for col in df.columns if 'sales' in col or 'profit' in col]
df[cols]
#    sales_q1  sales_q2  profit_q1  profit_q2
# 0       100       200         50        120

# Using regex with filter
df.filter(regex='sales|profit')  # Same result
```

### Rename While Selecting

```python title="Select and rename simultaneously"
# Using rename with column selection
df = df[['old_name1', 'old_name2']].rename(columns={
    'old_name1': 'new_name1',
    'old_name2': 'new_name2'
})

# Or select then rename
selected = df[['A', 'B']]
selected.columns = ['Column_A', 'Column_B']
```

## Performance Tips

### Column Access Performance

```python title="Performance considerations"
# For single value access in a column
# Fast: direct column access
df['col'].iloc[0]

# Slower: double indexing
df[['col']].iloc[0, 0]

# For repeated access, cache column reference
# Slow in loop:
for i in range(len(df)):
    value = df['expensive_column'][i]  # Repeated lookup

# Better:
col = df['expensive_column']  # Reference once
for i in range(len(col)):
    value = col[i]

# Best: avoid loops, use vectorized operations
values = df['expensive_column'].values  # NumPy array
```

### Minimize Column Selection Operations

```python title="Efficient column selection"
# Less efficient: Multiple selections
temp1 = df[['A', 'B']]
temp2 = temp1[temp1['A'] > 5]
result = temp2[['B']]

# More efficient: Single operation
result = df.loc[df['A'] > 5, ['B']]
```

## Common Mistakes

### Single vs Double Brackets

```python title="Bracket confusion"
df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})

# Single bracket - returns Series
s = df['A']
type(s)  # Series

# Double bracket - returns DataFrame
df_single = df[['A']]
type(df_single)  # DataFrame

# This matters for method chaining
df['A'].mean()  # Works - Series has mean()
df[['A']].mean()  # Also works - DataFrame has mean()

# But output differs
df['A'].mean()  # Returns scalar: 1.5
df[['A']].mean()  # Returns Series with one value: A  1.5
```

### Dot Notation Pitfalls

```python title="Dot notation problems"
# This doesn't create a column!
df.new_col = [1, 2, 3]  # Creates DataFrame attribute, not column

# This does:
df['new_col'] = [1, 2, 3]

# Can't use dot notation for assignment of new columns
# Always use brackets for setting columns
```

### Modifying Copies vs Views

```python title="Copy vs view issue"
# This might be a view or a copy
subset = df[['A', 'B']]
subset['A'] = 999  # Might trigger SettingWithCopyWarning

# Be explicit
subset = df[['A', 'B']].copy()
subset['A'] = 999  # Safe, won't affect df
```

## Quick Reference

**Single column (returns Series):**

```python
df['col']
df.col  # Dot notation (limited)
df.loc[:, 'col']
df.iloc[:, 0]
```

**Multiple columns (returns DataFrame):**

```python
df[['col1', 'col2']]
df.loc[:, ['col1', 'col2']]
df.iloc[:, [0, 1]]
```

**By type:**

```python
df.select_dtypes(include=['number'])
df.select_dtypes(exclude=['object'])
```

**By pattern:**

```python
df.filter(like='sales')
df.filter(regex='^cost_')
```

**Reorder:**

```python
df[['C', 'A', 'B']]  # Explicit order
df[sorted(df.columns)]  # Alphabetical
```

**Drop:**

```python
df.drop('col', axis=1)
df.drop(columns=['col1', 'col2'])
```

**Best practices:**

- Use `[]` brackets for robust code (not dot notation)
- Use `[[]]` double brackets to get DataFrame (not Series)
- Use `loc` when combining row filtering with column selection
- Use `select_dtypes()` for type-based operations
- Always use `.copy()` when modifying a subset
