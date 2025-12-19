---
id: data-types
title: Data Types
sidebar_label: Data Types
tags: [pandas, dtypes, data-types, conversion, optimization]
---

# Data Types

## Overview

Understanding and managing data types is crucial for:

- **Memory efficiency**: Choosing the right type saves RAM
- **Performance**: Operations are faster with appropriate types
- **Correctness**: Prevent bugs from type mismatches
- **Functionality**: Some operations only work with specific types

**_pandas_** uses NumPy data types under the hood, with some pandas-specific additions.

## Common Data Types

### Numeric Types

Integer and floating-point numbers:

```python title="Numeric data types"
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'int_col': [1, 2, 3],
    'float_col': [1.5, 2.5, 3.5]
})

df.dtypes
# int_col      int64
# float_col    float64
```

**Integer types:**

- `int8`: -128 to 127
- `int16`: -32,768 to 32,767
- `int32`: -2.1B to 2.1B
- `int64`: Much larger range (default)
- `uint8`, `uint16`, `uint32`, `uint64`: Unsigned (positive only)

**Float types:**

- `float16`: Half precision (rarely used)
- `float32`: Single precision
- `float64`: Double precision (default)

### String/Object Type

Text and mixed data:

```python title="Object type for strings"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie']
})

df.dtypes
# name    object

# Object type can hold any Python object
df = pd.DataFrame({
    'mixed': ['text', 123, [1, 2, 3]]
})
df.dtypes
# mixed    object
```

The `object` dtype is memory-intensive and slow. For pure strings, consider the `string` dtype.

### String Type (pandas 1.0+)

Dedicated string type that's more memory-efficient:

```python title="Modern string type"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie']
})

# Convert to string dtype
df['name'] = df['name'].astype('string')

df.dtypes
# name    string

# Or specify when creating
df = pd.DataFrame({
    'name': pd.array(['Alice', 'Bob'], dtype='string')
})
```

Benefits: Better performance, clearer intent, future-proof.

### Boolean Type

True/False values:

```python title="Boolean data type"
df = pd.DataFrame({
    'is_active': [True, False, True],
    'has_discount': [1, 0, 1]  # This is int, not bool
})

df.dtypes
# is_active       bool
# has_discount    int64

# Convert integers to boolean
df['has_discount'] = df['has_discount'].astype(bool)
# has_discount    bool
```

Boolean columns are memory-efficient (1 byte per value).

### DateTime Type

Dates and times:

```python title="DateTime types"
df = pd.DataFrame({
    'date_str': ['2024-01-15', '2024-02-20', '2024-03-10']
})

# Initially stored as strings
df.dtypes
# date_str    object

# Convert to datetime
df['date'] = pd.to_datetime(df['date_str'])
df.dtypes
# date_str           object
# date       datetime64[ns]

# Datetime enables date operations
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day_name'] = df['date'].dt.day_name()
```

DateTime type unlocks time-based functionality and indexing.

### Categorical Type

For columns with limited unique values (like categories):

```python title="Categorical type for memory savings"
df = pd.DataFrame({
    'color': ['red', 'blue', 'red', 'green', 'blue', 'red'] * 1000
})

# As object type
print(df.memory_usage(deep=True)['color'])  # ~48000 bytes

# Convert to categorical
df['color'] = df['color'].astype('category')
print(df.memory_usage(deep=True)['color'])  # ~6000 bytes

df.dtypes
# color    category

# View categories
df['color'].cat.categories
# Index(['blue', 'green', 'red'], dtype='object')
```

Categorical is ideal for columns with repetitive values (status, region, grade, etc.).

### Timedelta Type

Duration/time differences:

```python title="Timedelta for durations"
df = pd.DataFrame({
    'start': pd.to_datetime(['2024-01-01', '2024-01-05']),
    'end': pd.to_datetime(['2024-01-10', '2024-01-15'])
})

# Calculate duration
df['duration'] = df['end'] - df['start']
df.dtypes
# start               datetime64[ns]
# end                 datetime64[ns]
# duration    timedelta64[ns]

# Access components
df['duration'].dt.days
# 0    9
# 1    10
```

## Checking Data Types

### View All Types

```python title="Inspecting data types"
df = pd.DataFrame({
    'name': ['Alice', 'Bob'],
    'age': [25, 30],
    'salary': [50000.0, 60000.0],
    'hired': pd.to_datetime(['2020-01-01', '2021-01-01'])
})

# See all column types
df.dtypes
# name               object
# age                 int64
# salary            float64
# hired      datetime64[ns]

# Get type of single column
df['age'].dtype  # dtype('int64')

# Detailed info including types
df.info()
# <class 'pandas.core.frame.DataFrame'>
# RangeIndex: 2 entries, 0 to 1
# Data columns (total 4 columns):
#  #   Column  Non-Null Count  Dtype         
# ---  ------  --------------  -----         
#  0   name    2 non-null      object        
#  1   age     2 non-null      int64         
#  2   salary  2 non-null      float64       
#  3   hired   2 non-null      datetime64[ns]
```

### Count Columns by Type

```python title="Summary of types in DataFrame"
# Number of columns per type
df.dtypes.value_counts()
# int64            1
# float64          1
# object           1
# datetime64[ns]   1

# Select columns by type
numeric_cols = df.select_dtypes(include=['number']).columns
date_cols = df.select_dtypes(include=['datetime']).columns
object_cols = df.select_dtypes(include=['object']).columns
```

## Type Conversion

### astype() - Explicit Conversion

The primary method for converting types:

```python title="Basic type conversion with astype"
df = pd.DataFrame({
    'age': ['25', '30', '35'],      # Strings
    'price': [100, 200, 150]        # Integers
})

# String to integer
df['age'] = df['age'].astype(int)

# Integer to float
df['price'] = df['price'].astype(float)

# To string
df['age'] = df['age'].astype(str)

df.dtypes
# age      object  (str)
# price    float64
```

### Convert Multiple Columns

```python title="Converting multiple columns at once"
df = pd.DataFrame({
    'A': ['1', '2', '3'],
    'B': ['4', '5', '6'],
    'C': ['7', '8', '9']
})

# Convert all to int
df = df.astype(int)

# Convert specific columns
df = df.astype({'A': int, 'B': float, 'C': str})

# Convert all object columns to string dtype
object_cols = df.select_dtypes(include=['object']).columns
df[object_cols] = df[object_cols].astype('string')
```

### Numeric Conversion with to_numeric()

More flexible numeric conversion with error handling:

```python title="Safe numeric conversion"
df = pd.DataFrame({
    'values': ['100', '200', 'invalid', '300']
})

# astype() would fail on 'invalid'
# df['values'].astype(int)  # ValueError!

# to_numeric() handles errors
df['values'] = pd.to_numeric(df['values'], errors='coerce')
# values
# 0    100.0
# 1    200.0
# 2      NaN  # Invalid became NaN
# 3    300.0

# errors parameter options:
# 'raise': Raise error (default)
# 'coerce': Convert invalid to NaN
# 'ignore': Return original if can't convert
```

This is safer when you're unsure about data quality.

### DateTime Conversion with to_datetime()

Convert to datetime with flexible parsing:

```python title="Converting to datetime"
df = pd.DataFrame({
    'date_str': ['2024-01-15', '01/15/2024', 'Jan 15, 2024']
})

# Automatic parsing
df['date'] = pd.to_datetime(df['date_str'])

# Specify format for speed
df['date'] = pd.to_datetime(df['date_str'], format='%Y-%m-%d')

# Handle invalid dates
df = pd.DataFrame({
    'dates': ['2024-01-15', 'invalid', '2024-02-20']
})
df['dates'] = pd.to_datetime(df['dates'], errors='coerce')
# 0   2024-01-15
# 1          NaT  # Not a Time
# 2   2024-02-20

# Parse from components
df = pd.DataFrame({
    'year': [2024, 2024],
    'month': [1, 2],
    'day': [15, 20]
})
df['date'] = pd.to_datetime(df[['year', 'month', 'day']])
```

### Categorical Conversion

```python title="Converting to categorical"
df = pd.DataFrame({
    'grade': ['A', 'B', 'A', 'C', 'B', 'A']
})

# Convert to categorical
df['grade'] = df['grade'].astype('category')

# With specific order (ordered categorical)
df['grade'] = pd.Categorical(
    df['grade'],
    categories=['C', 'B', 'A'],
    ordered=True
)

# Now comparisons work
df[df['grade'] > 'B']  # All A grades
```

Ordered categoricals enable meaningful comparisons.

### Downcast for Memory Savings

Reduce memory by using smaller integer/float types:

```python title="Downcasting to save memory"
df = pd.DataFrame({
    'small_ints': [1, 2, 3, 4, 5]
})

# Default is int64
df['small_ints'].dtype  # int64

# Downcast to smallest possible int
df['small_ints'] = pd.to_numeric(df['small_ints'], downcast='integer')
df['small_ints'].dtype  # int8 (1 byte instead of 8)

# Downcast floats
df = pd.DataFrame({
    'values': [1.5, 2.5, 3.5]
})
df['values'] = pd.to_numeric(df['values'], downcast='float')
df['values'].dtype  # float32 (4 bytes instead of 8)
```

## Handling Type Issues

### Mixed Types in Columns

When a column has mixed types, pandas defaults to object:

```python title="Dealing with mixed types"
df = pd.DataFrame({
    'mixed': [1, 2, 'three', 4]
})

df['mixed'].dtype  # object

# Find rows with non-numeric values
non_numeric = pd.to_numeric(df['mixed'], errors='coerce').isna()
problem_rows = df[non_numeric]
# 2    three

# Option 1: Convert invalid to NaN
df['mixed'] = pd.to_numeric(df['mixed'], errors='coerce')

# Option 2: Remove invalid rows
df = df[~non_numeric]

# Option 3: Replace invalid values
df['mixed'] = df['mixed'].replace('three', 3)
df['mixed'] = df['mixed'].astype(int)
```

### Leading Zeros in Strings

Numbers with leading zeros need special handling:

```python title="Preserving leading zeros"
df = pd.DataFrame({
    'zip_code': ['00501', '10001', '90210']
})

# As int, loses leading zeros
df['zip_code'].astype(int)  # 501, 10001, 90210

# Keep as string to preserve zeros
df['zip_code'] = df['zip_code'].astype('string')
# Or fill to specific length
df['zip_code'] = df['zip_code'].astype(int).astype(str).str.zfill(5)
```

### Nullable Integer Type

Regular int64 can't hold NaN. Use nullable integer:

```python title="Nullable integer types"
df = pd.DataFrame({
    'age': [25, None, 30]
})

# Regular int conversion fails with NaN
# df['age'].astype(int)  # Error!

# Nullable integer (pandas 1.0+)
df['age'] = df['age'].astype('Int64')  # Capital I
df.dtypes
# age    Int64

# Can now have missing values in integer column
df['age']
# 0      25
# 1    <NA>
# 2      30
```

Nullable types: `Int8`, `Int16`, `Int32`, `Int64`, `UInt8`, etc.

## Memory Optimization

### Check Memory Usage

```python title="Analyzing memory usage"
df = pd.DataFrame({
    'A': range(1000),
    'B': ['text'] * 1000,
    'C': [1.5] * 1000
})

# Memory per column
df.memory_usage()
# Index       128
# A          8000
# B          8000  # Doesn't show actual string size
# C          8000

# Deep=True for actual object size
df.memory_usage(deep=True)
# Index       128
# A          8000
# B         58000  # Actual string memory
# C          8000

# Total memory
total_mb = df.memory_usage(deep=True).sum() / 1024**2
print(f"Total: {total_mb:.2f} MB")
```

### Optimize Integer Columns

```python title="Optimizing integer memory"
df = pd.DataFrame({
    'small_numbers': [1, 2, 3, 4, 5],  # Values 1-5
    'ages': [25, 30, 35, 28, 42],       # Values 0-120
    'large_ids': [1000000, 2000000]     # Larger values
})

# Check current memory
print(df.memory_usage(deep=True))
# small_numbers    40  # int64 = 8 bytes × 5
# ages            40
# large_ids       16

# Optimize based on value ranges
df['small_numbers'] = df['small_numbers'].astype('int8')    # 1 byte
df['ages'] = df['ages'].astype('int8')                      # 1 byte
df['large_ids'] = df['large_ids'].astype('int32')           # 4 bytes

print(df.memory_usage(deep=True))
# small_numbers     5  # 1 byte × 5
# ages             5
# large_ids        8  # 4 bytes × 2

# Memory saved: ~60%
```

### Optimize Object Columns

```python title="Optimizing object/string columns"
df = pd.DataFrame({
    'status': ['active', 'inactive', 'active', 'pending'] * 250
})

# As object
print(df.memory_usage(deep=True)['status'])  # ~56000 bytes

# Convert to category
df['status'] = df['status'].astype('category')
print(df.memory_usage(deep=True)['status'])  # ~1200 bytes

# 97% memory reduction!
```

Use categorical for columns with \<50% unique values.

### Optimize Float Columns

```python title="Optimizing float precision"
df = pd.DataFrame({
    'measurements': [1.5, 2.5, 3.5, 4.5] * 1000
})

# float64 (default)
print(df.memory_usage()['measurements'])  # 32000 bytes

# float32 (enough precision for most cases)
df['measurements'] = df['measurements'].astype('float32')
print(df.memory_usage()['measurements'])  # 16000 bytes

# 50% memory reduction
```

### Optimize at Read Time

Set types when reading data to avoid conversion later:

```python title="Specify types when reading CSV"
# Inefficient: read then convert
df = pd.read_csv('data.csv')
df['age'] = df['age'].astype('int8')
df['status'] = df['status'].astype('category')

# Efficient: specify types directly
df = pd.read_csv('data.csv', dtype={
    'age': 'int8',
    'status': 'category',
    'price': 'float32'
})

# Save memory and time
```

## Type Coercion Behavior

### Automatic Type Promotion

pandas automatically promotes types when needed:

```python title="Automatic type promotion"
df = pd.DataFrame({
    'ints': [1, 2, 3]
})
df['ints'].dtype  # int64

# Add a float - promotes to float
df.loc[3, 'ints'] = 4.5
df['ints'].dtype  # float64

# Add NaN to int - promotes to float
df = pd.DataFrame({'ints': [1, 2, 3]})
df.loc[3, 'ints'] = np.nan
df['ints'].dtype  # float64

# Use nullable Int64 to avoid this
df = pd.DataFrame({'ints': pd.array([1, 2, 3], dtype='Int64')})
df.loc[3, 'ints'] = pd.NA
df['ints'].dtype  # Int64
```

### Division Behavior

```python title="Division type changes"
df = pd.DataFrame({
    'ints': [10, 20, 30]
})
df['ints'].dtype  # int64

# Division creates floats
result = df['ints'] / 2
result.dtype  # float64

# Integer division preserves int
result = df['ints'] // 2
result.dtype  # int64
```

## Best Practices

### Set Types Early

```python title="Define types when creating DataFrame"
# Don't do this:
df = pd.DataFrame({
    'id': [1, 2, 3],
    'status': ['active', 'pending', 'active']
})
df['id'] = df['id'].astype('int32')
df['status'] = df['status'].astype('category')

# Do this:
df = pd.DataFrame({
    'id': pd.array([1, 2, 3], dtype='int32'),
    'status': pd.Categorical(['active', 'pending', 'active'])
})
```

### Use Type-Specific Methods

```python title="Methods available per type"
# String methods (only work on object/string dtypes)
df['text'].str.upper()
df['text'].str.contains('pattern')

# DateTime methods (only work on datetime dtypes)
df['date'].dt.year
df['date'].dt.day_name()

# Categorical methods (only work on category dtypes)
df['category'].cat.categories
df['category'].cat.codes
```

### Validate Types

```python title="Type validation"
def validate_types(df, expected_types):
    """Check if DataFrame has expected types."""
    for col, expected in expected_types.items():
        actual = df[col].dtype
        if actual != expected:
            print(f"Warning: {col} is {actual}, expected {expected}")

expected = {
    'age': 'int64',
    'name': 'object',
    'hired': 'datetime64[ns]'
}
validate_types(df, expected)
```

### Document Type Choices

```python title="Document your type decisions"
# Good: Clear why each type was chosen
dtypes_config = {
    'customer_id': 'int32',      # Max 2B customers
    'status': 'category',        # Only 5 possible values
    'amount': 'float32',         # Precision to 2 decimals sufficient
    'created_at': 'datetime64[ns]'
}

df = pd.read_csv('data.csv', dtype=dtypes_config)
```

## Common Type Errors and Solutions

### Cannot Convert String to Numeric

```python title="Handling conversion errors"
df = pd.DataFrame({
    'price': ['$100', '$200', '$150']
})

# This fails
# df['price'].astype(float)  # ValueError!

# Solution: Clean then convert
df['price'] = df['price'].str.replace('$', '').astype(float)

# Or use to_numeric with coerce
df['price'] = pd.to_numeric(
    df['price'].str.replace('$', ''),
    errors='coerce'
)
```

### Cannot Add Column to Int DataFrame

```python title="Type compatibility issues"
df = pd.DataFrame({
    'value': [1, 2, 3]
})

# Adding NaN fails with int
# df.loc[3, 'value'] = np.nan  # Error!

# Solution: Use nullable Int64 from start
df = pd.DataFrame({
    'value': pd.array([1, 2, 3], dtype='Int64')
})
df.loc[3, 'value'] = pd.NA  # Works!
```

### Comparison Not Working

```python title="Type mismatch in comparisons"
df = pd.DataFrame({
    'age': ['25', '30', '35']  # Stored as strings
})

# This compares strings, not numbers
df[df['age'] > '28']  # Wrong results! '30' < '28' as strings

# Solution: Convert to numeric first
df['age'] = df['age'].astype(int)
df[df['age'] > 28]  # Correct
```

## Quick Reference

**Common types:**

```python
int64, int32, int16, int8          # Integers
float64, float32                   # Floats
object, string                     # Text
bool                               # True/False
datetime64[ns]                     # Dates/times
timedelta64[ns]                    # Durations
category                           # Categories
Int64, Int32, etc.                 # Nullable integers
```

**Check types:**

```python
df.dtypes                          # All columns
df['col'].dtype                    # Single column
df.info()                          # Detailed info
df.select_dtypes(include=['number'])  # By type
```

**Convert types:**

```python
df['col'].astype(int)              # Explicit conversion
pd.to_numeric(df['col'], errors='coerce')  # Safe numeric
pd.to_datetime(df['col'])          # To datetime
df['col'].astype('category')       # To category
```

**Memory optimization:**

```python
df.memory_usage(deep=True)         # Check usage
df['col'].astype('int8')           # Downcast integers
df['col'].astype('category')       # For repeated values
df['col'].astype('float32')        # Reduce float size
```

**Type-specific methods:**

```python
df['text'].str.method()            # String methods
df['date'].dt.method()             # DateTime methods
df['cat'].cat.method()             # Categorical methods
```
