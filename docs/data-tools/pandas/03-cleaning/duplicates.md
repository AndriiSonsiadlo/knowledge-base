---
id: duplicates
title: Handling Duplicates
sidebar_label: Duplicates
tags: [pandas, duplicates, data-cleaning]
---

# Handling Duplicates

## Overview

Duplicate rows are common in real-world data. **_pandas_** provides simple methods to find and remove them.

## Finding Duplicates

### Check for Any Duplicates

```python title="Check if duplicates exist"
import pandas as pd

df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Alice', 'Charlie'],
    'age': [25, 30, 25, 35]
})

# Check if any duplicates exist
df.duplicated().any()  # True

# Count duplicate rows
df.duplicated().sum()  # 1
```

### Identify Duplicate Rows

```python title="Find which rows are duplicates"
# Boolean mask of duplicate rows
df.duplicated()
# 0    False  # First occurrence
# 1    False
# 2     True  # Duplicate of row 0
# 3    False

# Get the actual duplicate rows
duplicates = df[df.duplicated()]
#     name  age
# 2  Alice   25
```

By default, the first occurrence is marked as non-duplicate.

### Mark First vs Last Occurrence

```python title="Control which occurrence to mark"
# Mark first occurrence as duplicate (keep last)
df.duplicated(keep='last')
# 0     True  # Now row 0 is marked as duplicate
# 1    False
# 2    False  # Last occurrence not marked
# 3    False

# Mark all occurrences as duplicates
df.duplicated(keep=False)
# 0     True  # All duplicates marked
# 1    False
# 2     True
# 3    False
```

## Duplicates Based on Specific Columns

### Check Duplicates in Subset of Columns

Often you want to find duplicates based on specific columns only:

```python title="Duplicates based on specific columns"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Alice'],
    'age': [25, 30, 28],
    'city': ['NYC', 'LA', 'NYC']
})

# Duplicate based on 'name' only
df.duplicated(subset=['name'])
# 0    False
# 1    False
# 2     True  # Same name as row 0

# View duplicate names
df[df.duplicated(subset=['name'], keep=False)]
#     name  age city
# 0  Alice   25  NYC
# 2  Alice   28  NYC

# Duplicate based on multiple columns
df.duplicated(subset=['name', 'city'])
# 0    False
# 1    False
# 2     True  # Same name AND city as row 0
```

### Find Duplicate Values in Single Column

```python title="Find duplicate values in one column"
df = pd.DataFrame({
    'email': ['a@test.com', 'b@test.com', 'a@test.com', 'c@test.com']
})

# Find duplicate emails
duplicate_emails = df[df.duplicated(subset=['email'], keep=False)]
#          email
# 0  a@test.com
# 2  a@test.com

# Count occurrences
df['email'].value_counts()
# a@test.com    2
# b@test.com    1
# c@test.com    1
```

## Removing Duplicates

### drop_duplicates()

The main method for removing duplicates:

```python title="Basic duplicate removal"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Alice', 'Charlie'],
    'age': [25, 30, 25, 35]
})

# Remove duplicates (keeps first occurrence)
df_clean = df.drop_duplicates()
#       name  age
# 0    Alice   25
# 1      Bob   30
# 3  Charlie   35

# Original df unchanged unless inplace=True
df.drop_duplicates(inplace=True)
```

### Keep First, Last, or Remove All

```python title="Control which duplicates to keep"
df = pd.DataFrame({
    'id': [1, 2, 1, 3],
    'value': [100, 200, 150, 300]
})

# Keep first occurrence (default)
df.drop_duplicates(subset=['id'], keep='first')
#    id  value
# 0   1    100  # First occurrence of id=1
# 1   2    200
# 3   3    300

# Keep last occurrence
df.drop_duplicates(subset=['id'], keep='last')
#    id  value
# 1   2    200
# 2   1    150  # Last occurrence of id=1
# 3   3    300

# Remove all duplicates (keep none)
df.drop_duplicates(subset=['id'], keep=False)
#    id  value
# 1   2    200  # Only unique ids remain
# 3   3    300
```

### Drop Duplicates by Specific Columns

```python title="Remove duplicates based on subset"
df = pd.DataFrame({
    'user_id': [1, 2, 1, 3],
    'timestamp': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04'],
    'action': ['login', 'login', 'logout', 'login']
})

# Keep only first action per user
df.drop_duplicates(subset=['user_id'], keep='first')
#    user_id   timestamp  action
# 0        1  2024-01-01   login
# 1        2  2024-01-02   login
# 3        3  2024-01-04   login

# Multiple columns
df.drop_duplicates(subset=['user_id', 'action'])
```

## Common Patterns

### Keep Latest Record per ID

```python title="Keep most recent record for each ID"
df = pd.DataFrame({
    'customer_id': [1, 1, 2, 2, 3],
    'date': pd.to_datetime(['2024-01-01', '2024-01-15', '2024-01-10', '2024-01-20', '2024-01-05']),
    'purchase': [100, 150, 200, 250, 300]
})

# Sort by date, then keep last occurrence per customer
df_latest = (df
    .sort_values('date')
    .drop_duplicates(subset=['customer_id'], keep='last')
)
#    customer_id       date  purchase
# 1            1 2024-01-15       150
# 3            2 2024-01-20       250
# 4            3 2024-01-05       300
```

:::warning
Always sort before `drop_duplicates` when order matters.
:::

### Keep Record with Highest/Lowest Value

```python title="Keep record with max/min value per group"
df = pd.DataFrame({
    'product': ['A', 'A', 'B', 'B'],
    'price': [100, 150, 200, 180],
    'store': ['S1', 'S2', 'S3', 'S4']
})

# Keep lowest price per product
df_cheapest = (df
    .sort_values('price')
    .drop_duplicates(subset=['product'], keep='first')
)
#   product  price store
# 0       A    100    S1
# 3       B    180    S4
```

### Remove Exact Duplicate Rows

```python title="Remove completely identical rows"
df = pd.DataFrame({
    'A': [1, 1, 2, 3],
    'B': [4, 4, 5, 6]
})

# Rows 0 and 1 are identical
df.drop_duplicates()
#    A  B
# 0  1  4
# 2  2  5
# 3  3  6
```

This checks all columns by default.

## Analyzing Duplicates Before Removal

### Count Duplicates per Group

```python title="How many duplicates exist per group"
df = pd.DataFrame({
    'email': ['a@test.com', 'b@test.com', 'a@test.com', 'a@test.com', 'c@test.com']
})

# Count occurrences
duplicate_counts = df['email'].value_counts()
# a@test.com    3
# b@test.com    1
# c@test.com    1

# Filter to only duplicates
duplicates_only = duplicate_counts[duplicate_counts > 1]
# a@test.com    3
```

### Compare Duplicate Groups

```python title="Examine differences within duplicate groups"
df = pd.DataFrame({
    'id': [1, 1, 2, 2],
    'value': [100, 150, 200, 200],
    'status': ['active', 'inactive', 'pending', 'pending']
})

# Group by id and compare
for id_val, group in df.groupby('id'):
    if len(group) > 1:
        print(f"ID {id_val}:")
        print(group)
        print()
```

Useful to understand why duplicates exist before removing them.

## Index Duplicates

### Check for Duplicate Index Values

```python title="Find duplicate index values"
df = pd.DataFrame(
    {'value': [1, 2, 3, 4]},
    index=['a', 'b', 'a', 'c']
)

# Check if index has duplicates
df.index.duplicated().any()  # True

# Find duplicate index values
df.index.duplicated()
# [False, False,  True, False]

# Remove duplicate index (keeps first)
df = df[~df.index.duplicated()]
#    value
# a      1
# b      2
# c      4
```

### Reset Index to Remove Index Duplicates

```python title="Reset index to handle duplicates"
df = pd.DataFrame(
    {'value': [1, 2, 3]},
    index=['a', 'a', 'b']
)

# Reset to integer index
df_reset = df.reset_index()
#   index  value
# 0     a      1
# 1     a      2
# 2     b      3

# Now can handle 'a' duplicates in column
df_reset.drop_duplicates(subset=['index'], keep='first')
```

## Edge Cases

### Empty DataFrame

```python title="Duplicates in empty DataFrame"
df = pd.DataFrame()
df.duplicated().any()  # False
df.drop_duplicates()   # Returns empty DataFrame
```

### All Rows Are Duplicates

```python title="When all rows are identical"
df = pd.DataFrame({
    'A': [1, 1, 1],
    'B': [2, 2, 2]
})

df.drop_duplicates()
#    A  B
# 0  1  2  # Only first row kept
```

### NaN Values in Duplicates

```python title="How NaN is handled in duplicates"
import numpy as np

df = pd.DataFrame({
    'A': [1, 1, np.nan, np.nan],
    'B': [2, 2, 3, 3]
})

# NaN values are considered equal
df.duplicated()
# 0    False
# 1     True  # Duplicate of row 0
# 2    False
# 3     True  # Duplicate of row 2 (NaN == NaN for duplicates)

df.drop_duplicates()
#      A  B
# 0  1.0  2
# 2  NaN  3
```

## Best Practices

**Always check before removing:**

```python
# See what you're removing
print(f"Rows before: {len(df)}")
print(f"Duplicates: {df.duplicated().sum()}")
df_clean = df.drop_duplicates()
print(f"Rows after: {len(df_clean)}")
```

**Specify subset explicitly:**

```python
# Clear what defines a duplicate
df.drop_duplicates(subset=['email'])  # Good

# Not clear what's being checked
df.drop_duplicates()  # Less clear
```

**Sort before dropping when order matters:**

```python
# Keep most recent per ID
df.sort_values('date').drop_duplicates(subset=['id'], keep='last')
```

**Save removed duplicates for review:**

```python
# Keep duplicates for analysis
duplicates = df[df.duplicated(keep=False)]
duplicates.to_csv('duplicates_for_review.csv')

# Then remove
df_clean = df.drop_duplicates()
```

## Quick Reference

**Find duplicates:**

```python
df.duplicated()                      # Boolean mask
df.duplicated().sum()                # Count
df[df.duplicated()]                  # Get duplicate rows
df.duplicated(subset=['col'])        # Based on column
df.duplicated(keep=False)            # Mark all occurrences
```

**Remove duplicates:**

```python
df.drop_duplicates()                 # Keep first
df.drop_duplicates(keep='last')      # Keep last
df.drop_duplicates(keep=False)       # Remove all
df.drop_duplicates(subset=['col'])   # Based on column
df.drop_duplicates(inplace=True)     # Modify in place
```

**Common workflow:**

```python
# 1. Check for duplicates
df.duplicated().sum()

# 2. Investigate duplicates
df[df.duplicated(subset=['id'], keep=False)]

# 3. Sort if needed
df = df.sort_values('date')

# 4. Remove duplicates
df = df.drop_duplicates(subset=['id'], keep='last')
```
