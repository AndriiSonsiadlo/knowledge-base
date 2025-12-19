---
id: missing-data
title: Missing Data
sidebar_label: Missing Data
tags: [pandas, missing-data, data-cleaning]
---

# Missing Data

## Overview

Missing data appears as `NaN` (Not a Number), `None`, or `NaT` (Not a Time) in pandas. Handling it correctly is crucial for data analysis.

## Detecting Missing Data

### Check for Missing Values

```python title="Find missing values"
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'name': ['Alice', 'Bob', None, 'David'],
    'age': [25, np.nan, 35, 28],
    'city': ['NYC', 'LA', 'Chicago', None]
})

# Check which values are missing
df.isnull()  # or df.isna()
#     name    age   city
# 0  False  False  False
# 1  False   True  False
# 2   True  False  False
# 3  False  False   True

# Check which values are NOT missing
df.notnull()  # or df.notna()
```

`isnull()` and `isna()` are identical. Use whichever you prefer.

### Count Missing Values

```python title="Count missing values per column"
# Missing values per column
df.isnull().sum()
# name    1
# age     1
# city    1

# Total missing values
df.isnull().sum().sum()  # 3

# Percentage missing per column
(df.isnull().sum() / len(df) * 100).round(2)
# name    25.0
# age     25.0
# city    25.0
```

### Find Rows with Missing Data

```python title="Get rows with missing values"
# Rows with any missing value
df[df.isnull().any(axis=1)]
#     name   age     city
# 1    Bob   NaN       LA
# 2   None  35.0  Chicago
# 3  David  28.0     None

# Rows with all values missing
df[df.isnull().all(axis=1)]

# Rows with specific column missing
df[df['age'].isnull()]
#    name  age city
# 1   Bob  NaN   LA

# Rows with multiple columns missing
df[df['name'].isnull() | df['city'].isnull()]
```

### Summary of Missing Data

```python title="Missing data summary"
# Create summary DataFrame
missing_summary = pd.DataFrame({
    'missing_count': df.isnull().sum(),
    'missing_pct': (df.isnull().sum() / len(df) * 100).round(2)
})
print(missing_summary)
#       missing_count  missing_pct
# name              1        25.00
# age               1        25.00
# city              1        25.00
```

## Removing Missing Data

### dropna() - Remove Rows/Columns

```python title="Drop rows with missing values"
df = pd.DataFrame({
    'A': [1, 2, np.nan, 4],
    'B': [5, np.nan, np.nan, 8],
    'C': [9, 10, 11, 12]
})

# Drop rows with any missing value (default)
df.dropna()
#      A    B   C
# 0  1.0  5.0   9
# 3  4.0  8.0  12

# Original df unchanged unless inplace=True
df.dropna(inplace=True)
```

### Drop Based on Thresholds

```python title="Drop with conditions"
df = pd.DataFrame({
    'A': [1, np.nan, np.nan, 4],
    'B': [5, 6, np.nan, 8],
    'C': [9, 10, 11, 12]
})

# Drop rows with ALL values missing
df.dropna(how='all')
#      A    B   C
# 0  1.0  5.0   9
# 1  NaN  6.0  10
# 2  NaN  NaN  11
# 3  4.0  8.0  12

# Drop rows with at least N non-null values
df.dropna(thresh=2)  # Keep rows with at least 2 non-null
#      A    B   C
# 0  1.0  5.0   9
# 1  NaN  6.0  10
# 3  4.0  8.0  12
```

### Drop Columns with Missing Data

```python title="Drop columns instead of rows"
# Drop columns with any missing value
df.dropna(axis=1)
#     C
# 0   9
# 1  10
# 2  11
# 3  12

# Drop columns with all missing values
df.dropna(axis=1, how='all')

# Drop columns with too many missing values
threshold = len(df) * 0.5  # More than 50% missing
df.dropna(axis=1, thresh=threshold)
```

### Drop Based on Specific Columns

```python title="Drop based on subset of columns"
df = pd.DataFrame({
    'id': [1, 2, 3, 4],
    'value': [100, np.nan, 300, np.nan],
    'optional': [np.nan, np.nan, np.nan, np.nan]
})

# Drop only if 'value' is missing (ignore 'optional')
df.dropna(subset=['value'])
#    id  value  optional
# 0   1  100.0       NaN
# 2   3  300.0       NaN

# Drop if either id or value is missing
df.dropna(subset=['id', 'value'])
```

## Filling Missing Data

### fillna() - Replace Missing Values

```python title="Fill with constant value"
df = pd.DataFrame({
    'A': [1, np.nan, 3],
    'B': [4, 5, np.nan]
})

# Fill all missing with 0
df.fillna(0)
#      A    B
# 0  1.0  4.0
# 1  0.0  5.0
# 2  3.0  0.0

# Fill with specific values per column
df.fillna({'A': 0, 'B': 999})
#      A      B
# 0  1.0    4.0
# 1  0.0    5.0
# 2  3.0  999.0
```

### Fill with Statistics

```python title="Fill with mean, median, mode"
df = pd.DataFrame({
    'price': [100, 200, np.nan, 400, np.nan],
    'quantity': [1, np.nan, 3, 4, 5]
})

# Fill with mean
df['price'].fillna(df['price'].mean())
# 0    100.0
# 1    200.0
# 2    233.33
# 3    400.0
# 4    233.33

# Fill with median (more robust to outliers)
df['price'].fillna(df['price'].median())

# Fill with mode (most common value)
df['quantity'].fillna(df['quantity'].mode()[0])

# Fill all numeric columns with mean
numeric_cols = df.select_dtypes(include=['number']).columns
df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
```

### Forward Fill and Backward Fill

```python title="Fill with adjacent values"
df = pd.DataFrame({
    'value': [1, np.nan, np.nan, 4, np.nan]
})

# Forward fill (use previous value)
df['value'].fillna(method='ffill')  # or method='pad'
# 0    1.0
# 1    1.0  # Filled from row 0
# 2    1.0  # Filled from row 1
# 3    4.0
# 4    4.0  # Filled from row 3

# Backward fill (use next value)
df['value'].fillna(method='bfill')  # or method='backfill'
# 0    1.0
# 1    4.0  # Filled from row 3
# 2    4.0  # Filled from row 3
# 3    4.0
# 4    NaN  # No value after this

# Limit number of consecutive fills
df['value'].fillna(method='ffill', limit=1)
# Only fills 1 consecutive NaN
```

Forward/backward fill is useful for time series data.

### Fill with Interpolation

```python title="Interpolate missing values"
df = pd.DataFrame({
    'value': [1, np.nan, np.nan, 4, np.nan, 6]
})

# Linear interpolation
df['value'].interpolate()
# 0    1.0
# 1    2.0  # Interpolated
# 2    3.0  # Interpolated
# 3    4.0
# 4    5.0  # Interpolated
# 5    6.0

# Different interpolation methods
df['value'].interpolate(method='polynomial', order=2)
df['value'].interpolate(method='spline', order=2)
```

Interpolation estimates values based on surrounding data.

## Replacing Values with NaN

### Replace Specific Values

```python title="Convert values to NaN"
df = pd.DataFrame({
    'age': [25, -999, 30, 0, 35],
    'income': [50000, 0, 60000, 'N/A', 70000]
})

# Replace specific value with NaN
df['age'].replace(-999, np.nan)
# 0    25.0
# 1     NaN
# 2    30.0

# Replace multiple values
df['age'].replace([0, -999], np.nan)

# Replace in entire DataFrame
df.replace('N/A', np.nan)

# Replace using dictionary
df.replace({'age': {0: np.nan}, 'income': {'N/A': np.nan}})
```

Common placeholders: -999, 0, 'N/A', 'NULL', '', '?'

## Group-Based Filling

### Fill with Group Statistics

```python title="Fill missing values by group"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B', 'A'],
    'value': [10, np.nan, 20, np.nan, 30]
})

# Fill with group mean
df['value'] = df.groupby('category')['value'].transform(
    lambda x: x.fillna(x.mean())
)
#   category  value
# 0        A   10.0
# 1        A   20.0  # Filled with mean of A (10+30)/2
# 2        B   20.0
# 3        B   20.0  # Filled with mean of B (20)
# 4        A   30.0

# Fill with group median
df['value'] = df.groupby('category')['value'].transform(
    lambda x: x.fillna(x.median())
)
```

This preserves group-level patterns in the data.

## Handling Special Cases

### NaT (Not a Time) for Dates

```python title="Missing datetime values"
df = pd.DataFrame({
    'date': pd.to_datetime(['2024-01-01', None, '2024-01-03'])
})

# Check for missing dates
df['date'].isnull()
# 0    False
# 1     True
# 2    False

# Fill with specific date
df['date'].fillna(pd.to_datetime('2024-01-01'))

# Forward fill dates
df['date'].fillna(method='ffill')
```

### Empty Strings vs NaN

```python title="Distinguish between empty and NaN"
df = pd.DataFrame({
    'text': ['hello', '', None, 'world']
})

# Empty string is not NaN
df['text'].isnull()
# 0    False
# 1    False  # Empty string is not null
# 2     True
# 3    False

# Convert empty strings to NaN
df['text'].replace('', np.nan)

# Or during read
df = pd.read_csv('data.csv', na_values=['', 'NA', 'NULL'])
```

## Checking for Missing After Operations

### Verify Cleaning Results

```python title="Validate missing data handling"
# Before cleaning
print(f"Missing before: {df.isnull().sum().sum()}")

# Clean data
df_clean = df.fillna(df.mean())

# After cleaning
print(f"Missing after: {df_clean.isnull().sum().sum()}")

# Ensure no missing values remain
assert df_clean.isnull().sum().sum() == 0, "Still have missing values!"
```

## Common Patterns

### Strategy: Drop vs Fill

```python title="Decision framework for handling missing data"
df = pd.DataFrame({
    'critical': [1, 2, np.nan, 4],  # Can't proceed without this
    'optional': [5, np.nan, np.nan, 8],  # Can fill or ignore
    'metadata': [np.nan] * 4  # All missing, can drop
})

# Drop rows where critical column is missing
df = df.dropna(subset=['critical'])

# Fill optional column
df['optional'] = df['optional'].fillna(df['optional'].median())

# Drop entirely missing columns
df = df.dropna(axis=1, how='all')
```

### Time Series Missing Data

```python title="Handle missing in time series"
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=5),
    'value': [100, np.nan, np.nan, 400, 500]
})

# Forward fill (carry last observation forward)
df['value_ffill'] = df['value'].fillna(method='ffill')

# Interpolate (smooth transition)
df['value_interp'] = df['value'].interpolate()

# Both approaches common in time series
```

### Conditional Filling

```python title="Fill based on conditions"
df = pd.DataFrame({
    'type': ['A', 'A', 'B', 'B'],
    'value': [10, np.nan, np.nan, 40]
})

# Fill only for specific type
df.loc[df['type'] == 'A', 'value'] = df.loc[df['type'] == 'A', 'value'].fillna(0)

# Or use np.where
df['value'] = np.where(
    df['value'].isnull() & (df['type'] == 'A'),
    0,
    df['value']
)
```

## Performance Tips

### Efficient Missing Value Operations

```python title="Performance considerations"
# Slow: Check each column separately
for col in df.columns:
    if df[col].isnull().any():
        df[col].fillna(0, inplace=True)

# Fast: Vectorized operation
df.fillna(0, inplace=True)

# For large DataFrames, check if filling is needed first
if df.isnull().any().any():
    df.fillna(0, inplace=True)
```

## Common Mistakes

### Comparing NaN

```python title="NaN comparison behavior"
# NaN != NaN (always)
np.nan == np.nan  # False!

# Use pandas methods to check
pd.isna(np.nan)   # True
pd.isna(None)     # True

# Don't do this:
# df[df['col'] == np.nan]  # Returns empty!

# Do this:
df[df['col'].isna()]  # Correct
```

### Modifying Copies

```python title="Copy vs view warning"
# This might not work
subset = df[df['A'] > 5]
subset['B'].fillna(0)  # Warning!

# Do this instead
subset = df[df['A'] > 5].copy()
subset['B'].fillna(0, inplace=True)

# Or use loc
df.loc[df['A'] > 5, 'B'] = df.loc[df['A'] > 5, 'B'].fillna(0)
```

### Forgetting inplace=False

```python title="fillna doesn't modify by default"
df = pd.DataFrame({'A': [1, np.nan, 3]})

# This doesn't change df
df['A'].fillna(0)  # Returns new Series

# Need to assign or use inplace
df['A'] = df['A'].fillna(0)  # Assign result
# or
df['A'].fillna(0, inplace=True)  # Modify in place
```

## Quick Reference

**Detect missing:**

```python
df.isnull()                    # Boolean mask
df.isnull().sum()              # Count per column
df.isnull().any()              # Any missing per column
df[df['col'].isnull()]         # Rows where col is null
```

**Remove missing:**

```python
df.dropna()                    # Drop rows with any NaN
df.dropna(how='all')           # Drop if all values NaN
df.dropna(subset=['col'])      # Drop based on specific column
df.dropna(axis=1)              # Drop columns with NaN
df.dropna(thresh=2)            # Keep rows with 2+ non-null
```

**Fill missing:**

```python
df.fillna(0)                   # Fill with constant
df.fillna(df.mean())           # Fill with mean
df.fillna(method='ffill')      # Forward fill
df.fillna(method='bfill')      # Backward fill
df.interpolate()               # Interpolate
df.fillna({'A': 0, 'B': 999})  # Different values per column
```

**Replace with NaN:**

```python
df.replace(-999, np.nan)       # Replace specific value
df.replace(['NA', '?'], np.nan) # Replace multiple values
```

**Common workflow:**

```python
# 1. Check missing data
df.isnull().sum()

# 2. Decide strategy per column
df.dropna(subset=['critical_col'])
df['optional_col'].fillna(df['optional_col'].median())

# 3. Verify
assert df.isnull().sum().sum() == 0
```
