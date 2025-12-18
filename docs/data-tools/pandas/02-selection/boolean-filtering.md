---
id: boolean-filtering
title: Boolean Filtering
sidebar_label: Boolean Filtering
tags: [ pandas, filtering, boolean, conditions, query ]
---

# Boolean Filtering

## Overview

Boolean filtering selects rows based on conditions. It's one of the most common operations in data
analysis - filtering data to find what you need.

The basic pattern: `df[condition]` where condition evaluates to `True/False` for _each row_.

## Basic Boolean Filtering

### Single Condition

Filter rows where a condition is `True`:

```python title="Simple comparison"
import pandas as pd

df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'David'],
    'age': [25, 30, 35, 28],
    'city': ['NYC', 'LA', 'NYC', 'Chicago']
})

# Get rows where age is greater than 28
df[df['age'] > 28]
#       name  age city
# 1      Bob   30   LA
# 2  Charlie   35  NYC
```

The condition `df['age'] > 28` creates a _boolean_ `Series` that's used to filter:

```python title="Understanding the boolean mask"
# The condition returns True/False for each row
mask = df['age'] > 28
print(mask)
# 0    False
# 1     True
# 2     True
# 3    False

# Use the mask to filter
df[mask]  # Same as df[df['age'] > 28]
```

### Comparison Operators

All standard comparison operators work:

```python title="All comparison operators"
df[df['age'] == 30]  # Equal to
df[df['age'] != 30]  # Not equal to
df[df['age'] > 28]  # Greater than
df[df['age'] >= 30]  # Greater than or equal
df[df['age'] < 30]  # Less than
df[df['age'] <= 28]  # Less than or equal
```

### String Conditions

Filter based on text values:

```python title="String comparisons"
# Exact match
df[df['city'] == 'NYC']

# Case-sensitive comparison
df[df['name'] == 'alice']  # Returns empty (no match)

# String methods (case-insensitive)
df[df['city'].str.lower() == 'nyc']

# Contains substring
df[df['name'].str.contains('a')]  # Names containing 'a'

# Starts with
df[df['city'].str.startswith('N')]

# Ends with
df[df['name'].str.endswith('e')]
```

The `.str` accessor gives you access to string methods for filtering.

## Multiple Conditions

### AND Conditions

Use `&` to combine conditions (both must be True):

```python title="AND - both conditions must be True"
# Age > 25 AND city is NYC
df[(df['age'] > 25) & (df['city'] == 'NYC')]

# Parentheses are required around each condition
# This won't work: df[df['age'] > 25 & df['city'] == 'NYC']
```

Real example - find active high-value customers:

```python title="Business logic with AND"
customers = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'status': ['active', 'inactive', 'active'],
    'lifetime_value': [5000, 2000, 8000]
})

# Active customers with high lifetime value
high_value = customers[
    (customers['status'] == 'active') &
    (customers['lifetime_value'] > 4000)
    ]
```

### OR Conditions

Use `|` for OR (at least one condition must be True):

```python title="OR - at least one condition must be True"
# Age > 30 OR city is Chicago
df[(df['age'] > 30) | (df['city'] == 'Chicago')]

# Multiple OR conditions
df[(df['city'] == 'NYC') | (df['city'] == 'LA') | (df['city'] == 'Chicago')]
```

### NOT Conditions

Use `~` to negate a condition:

```python title="NOT - inverse the condition"
# NOT NYC (everyone except NYC)
df[~(df['city'] == 'NYC')]

# NOT (age > 30) is the same as age <= 30
df[~(df['age'] > 30)]
```

### Complex Conditions

Combine AND, OR, and NOT:

```python title="Complex multi-condition filter"
# (Age > 28 AND city NYC) OR (age < 27)
df[((df['age'] > 28) & (df['city'] == 'NYC')) | (df['age'] < 27)]

# Not in NYC AND (age > 25 OR name starts with 'D')
df[
    ~(df['city'] == 'NYC') &
    ((df['age'] > 25) | (df['name'].str.startswith('D')))
    ]
```

**_Remember_**: Use `&` for AND, `|` for OR, `~` for NOT. Always **use parentheses** around each condition.

## Special Filtering Methods

### isin() - Multiple Values

Check if values are in a list:

```python title="Filter for multiple specific values"
# City is NYC or LA
df[df['city'].isin(['NYC', 'LA'])]

# More readable than: df[(df['city'] == 'NYC') | (df['city'] == 'LA')]

# Numeric values
ages_to_find = [25, 30, 35]
df[df['age'].isin(ages_to_find)]

# Negate with ~
df[~df['city'].isin(['NYC', 'LA'])]  # Everyone NOT in NYC or LA
```

### between() - Range Checks

Check if values fall within a range:

```python title="Filter for values in a range"
# Age between 26 and 32 (inclusive)
df[df['age'].between(26, 32)]

# Same as: df[(df['age'] >= 26) & (df['age'] <= 32)]

# Exclusive bounds
df[df['age'].between(26, 32, inclusive='neither')]  # 26 < age < 32
df[df['age'].between(26, 32, inclusive='left')]  # 26 <= age < 32
df[df['age'].between(26, 32, inclusive='right')]  # 26 < age <= 32
```

### String Pattern Matching

More advanced string filtering:

```python title="Pattern matching in strings"
df = pd.DataFrame({
    'email': ['alice@gmail.com', 'bob@yahoo.com', 'charlie@gmail.com']
})

# Contains pattern
df[df['email'].str.contains('gmail')]

# Regex pattern (starts with 'a' or 'c')
df[df['email'].str.contains('^[ac]', regex=True)]

# Case-insensitive search
df[df['email'].str.contains('GMAIL', case=False)]

# Match exact pattern
df[df['email'].str.match(r'\w+@gmail\.com')]
```

## Handling Missing Values

Boolean operations with `NaN` values require special care:

```python title="Filtering with missing values"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'David'],
    'age': [25, None, 35, 28],
    'city': ['NYC', 'LA', None, 'Chicago']
})

# This excludes NaN rows
df[df['age'] > 28]

# Check for missing values
df[df['age'].isnull()]  # Rows where age is missing
df[df['age'].notna()]  # Rows where age is NOT missing

# Combine with other conditions
df[(df['age'].notna()) & (df['age'] > 28)]

# Filter where any column is null
df[df.isnull().any(axis=1)]

# Filter where all columns are non-null
df[df.notna().all(axis=1)]
```

## Query Method

The `query()` method provides a more readable way to filter using string expressions:

```python title="Query method for readable filtering"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'salary': [50000, 60000, 70000]
})

# Standard boolean filtering
df[(df['age'] > 25) & (df['salary'] < 65000)]

# Same with query (more readable)
df.query('age > 25 and salary < 65000')

# Or conditions
df.query('age > 30 or salary > 65000')

# Not operator
df.query('not (age > 30)')
```

### Query with Variables

Reference Python variables using `@`:

```python title="Using variables in query"
min_age = 28
max_salary = 65000

# Reference external variables with @
df.query('age > @min_age and salary < @max_salary')

# List membership
cities = ['NYC', 'LA']
df.query('city in @cities')

# String variables
target_city = 'NYC'
df.query('city == @target_city')
```

### Query Advantages

```python title="Why use query"
# Cleaner for complex conditions
df.query('(age > 25 and city == "NYC") or (age < 27 and salary > 55000)')

# vs boolean indexing (harder to read)
df[
    ((df['age'] > 25) & (df['city'] == 'NYC')) |
    ((df['age'] < 27) & (df['salary'] > 55000))
    ]

# Can reference column names with spaces (if backticked in DataFrame)
df.query('`first name` == "Alice"')
```

## Filter by Index

Filter based on index labels or positions:

```python title="Index-based filtering"
df = pd.DataFrame(
    {'value': [10, 20, 30, 40]},
    index=['a', 'b', 'c', 'd']
)

# Filter by index values
df[df.index.isin(['a', 'c'])]

# Filter by index conditions
df[df.index.str.startswith('a')]

# Numeric index filtering
df_numeric = pd.DataFrame({'value': [10, 20, 30]})
df_numeric[df_numeric.index > 0]  # All rows except first
```

## Filtering with loc

While `df[condition]` works for rows, `loc` allows filtering rows AND selecting columns:

```python title="Filter rows and select columns with loc"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['NYC', 'LA', 'NYC'],
    'salary': [50000, 60000, 70000]
})

# Filter rows, return all columns
df.loc[df['age'] > 28]

# Filter rows, select specific columns
df.loc[df['age'] > 28, ['name', 'salary']]

# Filter rows, select single column (returns Series)
df.loc[df['age'] > 28, 'name']

# Multiple conditions with column selection
df.loc[(df['age'] > 25) & (df['city'] == 'NYC'), ['name', 'age']]
```

This is particularly useful when you want to filter and immediately work with specific columns.

## Practical Examples

### Business Analytics

```python title="Finding high-value customers"
customers = pd.DataFrame({
    'customer_id': [1, 2, 3, 4, 5],
    'orders': [5, 12, 3, 20, 8],
    'total_spent': [500, 2000, 200, 5000, 1200],
    'status': ['active', 'active', 'churned', 'active', 'active']
})

# High-value active customers
high_value = customers[
    (customers['status'] == 'active') &
    (customers['total_spent'] > 1000) &
    (customers['orders'] > 10)
    ]

# At-risk customers (low recent orders)
at_risk = customers[
    (customers['status'] == 'active') &
    (customers['orders'] < 5)
    ]
```

### Data Quality Checks

```python title="Finding data quality issues"
sales = pd.DataFrame({
    'product': ['A', 'B', 'C', 'D'],
    'quantity': [10, -5, 0, 15],
    'price': [100, 200, 0, 150]
})

# Find invalid records
invalid = sales[
    (sales['quantity'] <= 0) |  # Invalid quantity
    (sales['price'] <= 0)  # Invalid price
    ]

# Find potential outliers
mean_price = sales['price'].mean()
std_price = sales['price'].std()
outliers = sales[
    (sales['price'] > mean_price + 3 * std_price) |
    (sales['price'] < mean_price - 3 * std_price)
    ]
```

### Date Filtering

```python title="Time-based filtering"
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=100),
    'sales': range(100)
})

# Filter by date range
df[df['date'] > '2024-02-01']
df[df['date'].between('2024-01-15', '2024-02-15')]

# Filter by date components
df[df['date'].dt.month == 1]  # January only
df[df['date'].dt.dayofweek == 0]  # Mondays only
df[df['date'].dt.year == 2024]  # Year 2024
```

## Performance Tips

For large DataFrames, consider these optimizations:

```python title="Performance optimization"
# Bad: Multiple separate filters (creates intermediate DataFrames)
df_temp = df[df['age'] > 25]
df_temp = df_temp[df_temp['city'] == 'NYC']
result = df_temp[df_temp['salary'] > 50000]

# Good: Single combined filter
result = df[
    (df['age'] > 25) &
    (df['city'] == 'NYC') &
    (df['salary'] > 50000)
    ]

# For very large DataFrames, query can be faster
result = df.query('age > 25 and city == "NYC" and salary > 50000')

# Store reusable masks
high_age = df['age'] > 25
nyc = df['city'] == 'NYC'
high_salary = df['salary'] > 50000
result = df[high_age & nyc & high_salary]
```

## Common Mistakes

### Missing Parentheses

```python title="Common error - missing parentheses"
# WRONG - will raise error
df[df['age'] > 25 & df['city'] == 'NYC']

# CORRECT - parentheses around each condition
df[(df['age'] > 25) & (df['city'] == 'NYC')]
```

The error occurs because Python evaluates `25 & df['city']` first, which doesn't make sense.

### Using 'and' Instead of '&'

```python title="Common error - using 'and' instead of '&'"
# WRONG - 'and' doesn't work with Series
df[df['age'] > 25 and df['city'] == 'NYC']  # Error!

# CORRECT - use &
df[(df['age'] > 25) & (df['city'] == 'NYC')]

# Exception: 'and' works in query strings
df.query('age > 25 and city == "NYC"')  # This is fine
```

### Chained Comparisons

```python title="Common error - chained comparisons"
# WRONG - doesn't work as expected
df[25 < df['age'] < 35]

# CORRECT - use between or explicit conditions
df[df['age'].between(25, 35, inclusive='neither')]
# or
df[(df['age'] > 25) & (df['age'] < 35)]
```

## Quick Reference

**Basic filtering:**

```python
df[df['col'] > 5]  # Single condition
df[(df['col1'] > 5) & (df['col2'] == 'A')]  # AND
df[(df['col1'] > 5) | (df['col2'] == 'A')]  # OR
df[~(df['col'] > 5)]  # NOT
```

**Special methods:**

```python
df[df['col'].isin([1, 2, 3])]  # Multiple values
df[df['col'].between(5, 10)]  # Range
df[df['col'].str.contains('text')]  # String pattern
df[df['col'].isnull()]  # Missing values
```

**Query method:**

```python
df.query('col > 5')
df.query('col > 5 and col2 == "A"')
df.query('col in @my_list')
```

**With loc:**

```python
df.loc[df['col'] > 5, ['col1', 'col2']]
```

**Operators:**

- `&` = AND
- `|` = OR
- `~` = NOT
- Always use parentheses around conditions!
