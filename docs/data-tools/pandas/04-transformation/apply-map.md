---
id: apply-map
title: Apply and Map
sidebar_label: Apply & Map
tags: [pandas, apply, map, transform, functions]
---

# Apply and Map

## Overview

pandas provides several methods to apply custom functions to data:

- **`apply()`**: Apply function along axis (rows/columns)
- **`map()`**: Element-wise mapping for Series
- **`applymap()`**: Element-wise for entire DataFrame (deprecated, use `map()`)
- **`transform()`**: Apply function and return same-shaped result

## apply() - Series

Apply a function to each element in a Series:

```python title="Apply function to Series"
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'price': [100, 200, 150, 300]
})

# Apply built-in function
df['price'].apply(np.sqrt)
# 0    10.000000
# 1    14.142136
# 2    12.247449
# 3    17.320508

# Apply custom function
def add_tax(price):
    return price * 1.1

df['price'].apply(add_tax)
# 0    110.0
# 1    220.0
# 2    165.0
# 3    330.0

# Apply lambda
df['price'].apply(lambda x: x * 1.1)
# Same result
```

## apply() - DataFrame

Apply function along rows or columns:

```python title="Apply to DataFrame rows/columns"
df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'C': [7, 8, 9]
})

# Apply to each column (axis=0, default)
df.apply(np.sum)
# A     6
# B    15
# C    24

# Apply to each row (axis=1)
df.apply(np.sum, axis=1)
# 0    12
# 1    15
# 2    18

# Custom function on columns
def get_range(col):
    return col.max() - col.min()

df.apply(get_range)
# A    2
# B    2
# C    2

# Custom function on rows
def row_max_min_diff(row):
    return row.max() - row.min()

df.apply(row_max_min_diff, axis=1)
# 0    6
# 1    6
# 2    6
```

### Apply with Multiple Columns

```python title="Apply function using multiple columns"
df = pd.DataFrame({
    'quantity': [10, 20, 15],
    'price': [100, 50, 75]
})

# Calculate total using row data
def calculate_total(row):
    return row['quantity'] * row['price']

df['total'] = df.apply(calculate_total, axis=1)
#    quantity  price  total
# 0        10    100   1000
# 1        20     50   1000
# 2        15     75   1125

# Or with lambda
df['total'] = df.apply(lambda row: row['quantity'] * row['price'], axis=1)
```

### Apply Returning Multiple Values

```python title="Return multiple values from apply"
df = pd.DataFrame({
    'name': ['Alice Smith', 'Bob Jones', 'Charlie Brown']
})

# Return Series (creates new columns)
def split_name(name):
    parts = name.split()
    return pd.Series({
        'first_name': parts[0],
        'last_name': parts[1]
    })

df[['first_name', 'last_name']] = df['name'].apply(split_name)
#            name first_name last_name
# 0   Alice Smith      Alice     Smith
# 1     Bob Jones        Bob     Jones
# 2  Charlie Brown    Charlie     Brown
```

## map() - Series Mapping

Map values using a dictionary or function:

```python title="Map values in Series"
df = pd.DataFrame({
    'grade': ['A', 'B', 'A', 'C', 'B']
})

# Map with dictionary
grade_map = {'A': 90, 'B': 80, 'C': 70}
df['score'] = df['grade'].map(grade_map)
#   grade  score
# 0     A     90
# 1     B     80
# 2     A     90
# 3     C     70
# 4     B     80

# Map with function
df['grade'].map(lambda x: x.lower())
# 0    a
# 1    b
# 2    a
# 3    c
# 4    b

# Map with Series
mapping = pd.Series({
    'A': 'Excellent',
    'B': 'Good',
    'C': 'Average'
})
df['grade'].map(mapping)
# 0    Excellent
# 1         Good
# 2    Excellent
# 3      Average
# 4         Good
```

### Handling Missing Mappings

```python title="Handle unmapped values"
df = pd.DataFrame({
    'code': ['A', 'B', 'X', 'C']  # 'X' not in mapping
})

mapping = {'A': 1, 'B': 2, 'C': 3}

# map() returns NaN for missing
df['code'].map(mapping)
# 0    1.0
# 1    2.0
# 2    NaN  # 'X' not found
# 3    3.0

# Fill missing with default
df['code'].map(mapping).fillna(0)
# 0    1.0
# 1    2.0
# 2    0.0
# 3    3.0
```

## replace() - Value Replacement

Similar to map but keeps unmatched values:

```python title="Replace specific values"
df = pd.DataFrame({
    'status': ['active', 'inactive', 'active', 'pending']
})

# Replace with dictionary
df['status'].replace({
    'active': 1,
    'inactive': 0,
    'pending': 2
})
# 0    1
# 1    0
# 2    1
# 3    2

# Replace multiple values with one
df['status'].replace(['active', 'pending'], 'open')
# 0      open
# 1  inactive
# 2      open
# 3      open
```

Difference: `map()` returns NaN for unmapped, `replace()` keeps original value.

## applymap() / map() - Element-wise DataFrame

Apply function to every element in DataFrame:

```python title="Element-wise operations on DataFrame"
df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6]
})

# Deprecated: applymap()
# df.applymap(lambda x: x * 2)

# Use map() instead (pandas 2.1+)
df.map(lambda x: x * 2)
#    A   B
# 0  2   8
# 1  4  10
# 2  6  12

# Apply to numeric columns only
numeric_cols = df.select_dtypes(include=['number']).columns
df[numeric_cols] = df[numeric_cols].map(lambda x: x * 2)
```

## transform() - Same Shape Output

Apply function but always return same shape as input:

```python title="Transform with same-shaped output"
df = pd.DataFrame({
    'A': [1, 2, 3, 4],
    'B': [5, 6, 7, 8]
})

# Normalize columns (subtract mean, divide by std)
df.transform(lambda x: (x - x.mean()) / x.std())
#           A         B
# 0 -1.341641 -1.341641
# 1 -0.447214 -0.447214
# 2  0.447214  0.447214
# 3  1.341641  1.341641

# Multiple functions
df['A'].transform(['sqrt', 'square'])
#        sqrt  square
# 0  1.000000       1
# 1  1.414214       4
# 2  1.732051       9
# 3  2.000000      16
```

transform() is useful with groupby for adding aggregated values back to original rows.

## Common Patterns

### Conditional Logic

```python title="Apply conditional transformations"
df = pd.DataFrame({
    'age': [15, 25, 35, 45, 55]
})

# Categorize ages
def categorize_age(age):
    if age < 18:
        return 'Minor'
    elif age < 65:
        return 'Adult'
    else:
        return 'Senior'

df['category'] = df['age'].apply(categorize_age)
#    age category
# 0   15    Minor
# 1   25    Adult
# 2   35    Adult
# 3   45    Adult
# 4   55    Adult

# Or with lambda and np.where
df['category'] = df['age'].apply(
    lambda x: 'Minor' if x < 18 else ('Senior' if x >= 65 else 'Adult')
)
```

### String Manipulation

```python title="Apply string operations"
df = pd.DataFrame({
    'email': ['ALICE@TEST.COM', 'bob@test.com', 'CHARLIE@TEST.COM']
})

# Clean emails
def clean_email(email):
    return email.lower().strip()

df['email_clean'] = df['email'].apply(clean_email)
#             email     email_clean
# 0  ALICE@TEST.COM  alice@test.com
# 1    bob@test.com    bob@test.com
# 2  CHARLIE@TEST.COM  charlie@test.com

# Extract domain
df['domain'] = df['email_clean'].apply(lambda x: x.split('@')[1])
#             email     email_clean     domain
# 0  ALICE@TEST.COM  alice@test.com  test.com
# 1    bob@test.com    bob@test.com  test.com
# 2  CHARLIE@TEST.COM  charlie@test.com  test.com
```

### Calculating Derived Columns

```python title="Create calculated columns"
df = pd.DataFrame({
    'purchase_date': pd.to_datetime(['2024-01-15', '2024-02-20', '2024-01-10']),
    'amount': [100, 200, 150]
})

# Days since purchase
from datetime import datetime
today = datetime(2024, 3, 1)

df['days_since'] = df['purchase_date'].apply(lambda x: (today - x).days)
#   purchase_date  amount  days_since
# 0    2024-01-15     100          46
# 1    2024-02-20     200          10
# 2    2024-01-10     150          51

# Better: use vectorized operations
df['days_since'] = (today - df['purchase_date']).dt.days
```

### Working with Lists/Dicts

```python title="Apply to complex data types"
df = pd.DataFrame({
    'scores': [[85, 90, 88], [92, 95, 89], [78, 82, 85]]
})

# Calculate average of lists
df['avg_score'] = df['scores'].apply(np.mean)
#         scores  avg_score
# 0  [85, 90, 88]       87.666667
# 1  [92, 95, 89]       92.000000
# 2  [78, 82, 85]       81.666667

# Work with dictionaries
df = pd.DataFrame({
    'data': [
        {'a': 1, 'b': 2},
        {'a': 3, 'b': 4},
        {'a': 5, 'b': 6}
    ]
})

df['sum'] = df['data'].apply(lambda x: sum(x.values()))
#                 data  sum
# 0  {'a': 1, 'b': 2}    3
# 1  {'a': 3, 'b': 4}    7
# 2  {'a': 5, 'b': 6}   11
```

## Performance Considerations

### Vectorization vs Apply

```python title="Vectorized operations are faster"
df = pd.DataFrame({
    'A': range(10000),
    'B': range(10000)
})

# Slow: apply with row-wise operation
df['C'] = df.apply(lambda row: row['A'] + row['B'], axis=1)

# Fast: vectorized operation
df['C'] = df['A'] + df['B']

# Slow: apply for simple math
df['squared'] = df['A'].apply(lambda x: x ** 2)

# Fast: vectorized
df['squared'] = df['A'] ** 2
```

Use vectorized operations when possible. Reserve apply() for complex logic.

### When to Use Each Method

```python title="Choosing the right method"
# Use vectorized operations (fastest)
df['total'] = df['price'] * df['quantity']

# Use apply() when:
# - Need row-wise operations with multiple columns
# - Complex logic that can't be vectorized
def complex_calculation(row):
    if row['type'] == 'A':
        return row['value'] * 1.5
    elif row['type'] == 'B':
        return row['value'] * 0.8
    else:
        return row['value']

df['result'] = df.apply(complex_calculation, axis=1)

# Use map() when:
# - Simple value mapping/replacement
df['status_code'] = df['status'].map({'active': 1, 'inactive': 0})

# Use np.where() for simple conditions (fastest)
df['label'] = np.where(df['value'] > 100, 'high', 'low')
```

## Advanced Examples

### Progress Tracking

```python title="Track progress with apply"
from tqdm import tqdm
tqdm.pandas()

# Use progress_apply instead of apply
df['result'] = df['column'].progress_apply(slow_function)
```

### Error Handling

```python title="Handle errors in apply"
def safe_divide(row):
    try:
        return row['numerator'] / row['denominator']
    except ZeroDivisionError:
        return np.nan
    except Exception as e:
        return np.nan

df['result'] = df.apply(safe_divide, axis=1)

# Or with specific error handling
df['result'] = df.apply(
    lambda row: row['a'] / row['b'] if row['b'] != 0 else np.nan,
    axis=1
)
```

### Chaining Operations

```python title="Chain apply operations"
df = pd.DataFrame({
    'text': ['  HELLO  ', 'world', '  TEST  ']
})

# Chain multiple operations
df['clean'] = (df['text']
    .apply(str.strip)       # Remove whitespace
    .apply(str.lower)       # Lowercase
    .apply(str.title)       # Title case
)
#        text  clean
# 0    HELLO   Hello
# 1    world   World
# 2     TEST    Test
```

## Common Mistakes

### Using apply() When Not Needed

```python title="Don't use apply for simple operations"
# Bad: slow
df['doubled'] = df['value'].apply(lambda x: x * 2)

# Good: fast
df['doubled'] = df['value'] * 2

# Bad: slow
df['is_high'] = df['price'].apply(lambda x: x > 100)

# Good: fast
df['is_high'] = df['price'] > 100
```

### Axis Confusion

```python title="Understanding axis parameter"
df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6]
})

# axis=0: apply to each column (down)
df.apply(sum, axis=0)
# A    6
# B    15

# axis=1: apply to each row (across)
df.apply(sum, axis=1)
# 0    5
# 1    7
# 2    9
```

### map() vs apply() Confusion

```python title="When to use map vs apply"
df = pd.DataFrame({
    'grade': ['A', 'B', 'C']
})

# Use map() for simple value replacement
df['grade'].map({'A': 90, 'B': 80, 'C': 70})  # Correct

# Don't use apply() for this
df['grade'].apply(lambda x: {'A': 90, 'B': 80, 'C': 70}[x])  # Overkill
```

## Quick Reference

**Series operations:**

```python
series.apply(func)                 # Apply function to each element
series.map(dict_or_func)          # Map values
series.replace(old, new)          # Replace values
```

**DataFrame operations:**

```python
df.apply(func, axis=0)            # Apply to columns
df.apply(func, axis=1)            # Apply to rows
df.map(func)                      # Element-wise (all values)
df.transform(func)                # Transform with same shape
```

**Common patterns:**

```python
# Value mapping
df['col'].map({'A': 1, 'B': 2})

# Row-wise calculation
df.apply(lambda row: row['a'] + row['b'], axis=1)

# Conditional logic
df['col'].apply(lambda x: 'high' if x > 100 else 'low')

# Multiple outputs
df['col'].apply(lambda x: pd.Series({'a': x*2, 'b': x*3}))
```

**Performance tips:**

1. Use vectorized operations when possible
2. Use `np.where()` for simple conditions
3. Use `map()` for value mapping
4. Reserve `apply()` for complex logic
5. Avoid `apply()` with `axis=1` on large DataFrames

**Alternatives (faster):**

```python
# Instead of apply
df['result'] = df['a'] + df['b']              # Vectorized
df['result'] = np.where(condition, a, b)      # np.where
df['result'] = df['col'].map(mapping_dict)    # map
```
