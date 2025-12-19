---
id: outliers-validation
title: Outliers and Data Validation
sidebar_label: Outliers & Validation
tags: [pandas, outliers, validation, data-quality]
---

# Outliers and Data Validation

## Overview

Outliers are data points that differ significantly from other observations. Data validation ensures your data meets expected criteria before analysis.

## Detecting Outliers

### Statistical Methods

#### Z-Score Method

Identify values that are many standard deviations from the mean:

```python title="Z-score outlier detection"
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'value': [10, 12, 11, 13, 100, 14, 12, 11]
})

# Calculate z-scores
mean = df['value'].mean()
std = df['value'].std()
df['z_score'] = (df['value'] - mean) / std

# Outliers: |z-score| > 3 (common threshold)
outliers = df[np.abs(df['z_score']) > 3]
#    value   z_score
# 4    100  2.89...

# Or use scipy
from scipy import stats
df['z_score'] = np.abs(stats.zscore(df['value']))
outliers = df[df['z_score'] > 3]
```

Z-score works well for normally distributed data.

#### IQR Method (Interquartile Range)

More robust to extreme values:

```python title="IQR outlier detection"
df = pd.DataFrame({
    'price': [100, 110, 105, 115, 1000, 108, 112, 107]
})

# Calculate IQR
Q1 = df['price'].quantile(0.25)
Q3 = df['price'].quantile(0.75)
IQR = Q3 - Q1

# Define outlier bounds
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

# Find outliers
outliers = df[(df['price'] < lower_bound) | (df['price'] > upper_bound)]
#    price
# 4   1000

# Filter out outliers
df_clean = df[(df['price'] >= lower_bound) & (df['price'] <= upper_bound)]
```

IQR method is the basis for box plots and works for skewed data.

### Percentile Method

Simple approach using percentiles:

```python title="Percentile-based outlier detection"
df = pd.DataFrame({
    'value': range(100) + [1000, 2000]  # Two outliers
})

# Remove top/bottom 1%
lower = df['value'].quantile(0.01)
upper = df['value'].quantile(0.99)

df_clean = df[(df['value'] >= lower) & (df['value'] <= upper)]

# Or remove values beyond 95th percentile
threshold = df['value'].quantile(0.95)
df[df['value'] <= threshold]
```

### Visual Detection

```python title="Visual outlier detection"
import matplotlib.pyplot as plt

df = pd.DataFrame({
    'value': [10, 12, 11, 13, 100, 14, 12, 11]
})

# Box plot (shows outliers as points)
df.boxplot(column='value')

# Histogram
df['value'].hist(bins=20)

# Scatter plot for relationships
df.plot.scatter(x='col1', y='col2')
```

Visual inspection helps identify outliers that statistics might miss.

## Handling Outliers

### Remove Outliers

```python title="Removing outliers"
df = pd.DataFrame({
    'age': [25, 30, 28, 150, 35, 29],  # 150 is outlier
    'salary': [50000, 60000, 55000, 58000, 1000000, 52000]  # 1M is outlier
})

# Remove using IQR for each column
def remove_outliers_iqr(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return df[(df[column] >= lower) & (df[column] <= upper)]

df_clean = remove_outliers_iqr(df, 'age')
df_clean = remove_outliers_iqr(df_clean, 'salary')
```

### Cap Outliers (Winsorization)

Replace extreme values with threshold values:

```python title="Cap outliers instead of removing"
df = pd.DataFrame({
    'value': [1, 2, 3, 100, 4, 5, 200]
})

# Cap at 5th and 95th percentiles
lower = df['value'].quantile(0.05)
upper = df['value'].quantile(0.95)

df['value_capped'] = df['value'].clip(lower=lower, upper=upper)
#    value  value_capped
# 0      1             1
# 1      2             2
# 2      3             3
# 3    100             5  # Capped
# 4      4             4
# 5      5             5
# 6    200             5  # Capped

# Or manually
df['value_capped'] = np.where(df['value'] > upper, upper,
                              np.where(df['value'] < lower, lower, df['value']))
```

Capping preserves row count while limiting outlier impact.

### Transform Data

```python title="Transform to reduce outlier impact"
df = pd.DataFrame({
    'value': [1, 10, 100, 1000, 10000]
})

# Log transformation (for right-skewed data)
df['log_value'] = np.log(df['value'])

# Square root transformation
df['sqrt_value'] = np.sqrt(df['value'])

# Box-Cox transformation (requires positive values)
from scipy import stats
df['boxcox_value'], _ = stats.boxcox(df['value'])
```

Transformations make outliers less extreme without removing data.

## Data Validation

### Range Validation

Check if values fall within expected ranges:

```python title="Validate value ranges"
df = pd.DataFrame({
    'age': [25, 30, 150, 28],  # 150 is invalid
    'score': [85, 92, 105, 78]  # 105 is invalid (max 100)
})

# Check for invalid ages
invalid_age = df[(df['age'] < 0) | (df['age'] > 120)]
#    age  score
# 2  150    105

# Check for invalid scores
invalid_score = df[(df['score'] < 0) | (df['score'] > 100)]
#    age  score
# 2  150    105

# Validate and mark
df['age_valid'] = df['age'].between(0, 120)
df['score_valid'] = df['score'].between(0, 100)

# Keep only valid rows
df_valid = df[df['age_valid'] & df['score_valid']]
```

### Type Validation

```python title="Validate data types"
df = pd.DataFrame({
    'id': ['1', '2', 'ABC', '4'],  # ABC is invalid
    'email': ['a@test.com', 'invalid', 'b@test.com', 'c@test.com']
})

# Check if id is numeric
df['id_valid'] = pd.to_numeric(df['id'], errors='coerce').notna()
#    id         email  id_valid
# 0   1    a@test.com      True
# 1   2       invalid      True
# 2 ABC    b@test.com     False
# 3   4    c@test.com      True

# Validate email format (basic)
df['email_valid'] = df['email'].str.contains('@', na=False)

# Filter valid rows
df_valid = df[df['id_valid'] & df['email_valid']]
```

### Pattern Validation

```python title="Validate with regex patterns"
df = pd.DataFrame({
    'phone': ['123-456-7890', '555-1234', '999-888-7777'],
    'zip': ['12345', '123', '54321']
})

# Validate phone format (XXX-XXX-XXXX)
df['phone_valid'] = df['phone'].str.match(r'^\d{3}-\d{3}-\d{4}$')
#          phone  phone_valid
# 0  123-456-7890         True
# 1      555-1234        False
# 2  999-888-7777         True

# Validate zip code (5 digits)
df['zip_valid'] = df['zip'].str.match(r'^\d{5}$')
#     zip  zip_valid
# 0  12345       True
# 1    123      False
# 2  54321       True
```

### Uniqueness Validation

```python title="Check for required uniqueness"
df = pd.DataFrame({
    'user_id': [1, 2, 3, 2, 4],  # 2 is duplicate
    'email': ['a@test.com', 'b@test.com', 'c@test.com', 'b@test.com', 'd@test.com']
})

# Check if user_id is unique
is_unique = df['user_id'].is_unique  # False

# Find duplicates
duplicates = df[df.duplicated(subset=['user_id'], keep=False)]
#    user_id        email
# 1        2  b@test.com
# 3        2  b@test.com

# Validate uniqueness per row
df['id_is_unique'] = ~df.duplicated(subset=['user_id'], keep=False)
```

### Completeness Validation

```python title="Check for required fields"
df = pd.DataFrame({
    'id': [1, 2, 3, 4],
    'name': ['Alice', None, 'Charlie', 'David'],
    'email': ['a@test.com', 'b@test.com', None, 'd@test.com']
})

# Check required fields
required_fields = ['id', 'name', 'email']
df['is_complete'] = df[required_fields].notna().all(axis=1)
#    id     name        email  is_complete
# 0   1    Alice   a@test.com         True
# 1   2     None   b@test.com        False
# 2   3  Charlie         None        False
# 3   4    David   d@test.com         True

# Get incomplete rows
incomplete = df[~df['is_complete']]
```

### Cross-Field Validation

```python title="Validate relationships between fields"
df = pd.DataFrame({
    'start_date': pd.to_datetime(['2024-01-01', '2024-02-01', '2024-03-01']),
    'end_date': pd.to_datetime(['2024-01-15', '2024-01-20', '2024-03-10'])
})

# End date should be after start date
df['date_valid'] = df['end_date'] > df['start_date']
#   start_date   end_date  date_valid
# 0 2024-01-01 2024-01-15        True
# 1 2024-02-01 2024-01-20       False
# 2 2024-03-01 2024-03-10        True

# Another example: discount <= price
df = pd.DataFrame({
    'price': [100, 200, 150],
    'discount': [10, 250, 20]  # 250 is invalid
})
df['discount_valid'] = df['discount'] <= df['price']
```

## Building Validation Functions

### Create Validation Pipeline

```python title="Reusable validation function"
def validate_dataframe(df):
    """Validate DataFrame and return issues."""
    issues = []
    
    # Check for missing values in required columns
    required = ['id', 'name', 'email']
    for col in required:
        if col in df.columns:
            missing_count = df[col].isnull().sum()
            if missing_count > 0:
                issues.append(f"{col}: {missing_count} missing values")
    
    # Check age range
    if 'age' in df.columns:
        invalid_age = df[(df['age'] < 0) | (df['age'] > 120)]
        if len(invalid_age) > 0:
            issues.append(f"age: {len(invalid_age)} invalid values")
    
    # Check for duplicates
    if 'id' in df.columns:
        dup_count = df['id'].duplicated().sum()
        if dup_count > 0:
            issues.append(f"id: {dup_count} duplicates")
    
    return issues

# Use it
issues = validate_dataframe(df)
if issues:
    print("Validation issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("All validations passed!")
```

### Validation Report

```python title="Generate validation report"
def validation_report(df):
    """Create comprehensive validation report."""
    report = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'missing_values': df.isnull().sum().to_dict(),
        'duplicate_rows': df.duplicated().sum(),
        'dtypes': df.dtypes.astype(str).to_dict()
    }
    
    # Numeric columns statistics
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        report['numeric_summary'] = df[numeric_cols].describe().to_dict()
    
    return report

# Generate report
report = validation_report(df)
print(f"Total rows: {report['total_rows']}")
print(f"Duplicates: {report['duplicate_rows']}")
print(f"Missing values: {report['missing_values']}")
```

## Common Validation Patterns

### Email Validation

```python title="Validate email addresses"
df = pd.DataFrame({
    'email': ['user@example.com', 'invalid', 'test@domain.co.uk', '@missing.com']
})

# Basic validation
df['email_valid'] = df['email'].str.contains(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    na=False,
    regex=True
)

# Get invalid emails
invalid_emails = df[~df['email_valid']]
```

### Date Validation

```python title="Validate dates"
df = pd.DataFrame({
    'date_str': ['2024-01-01', '2024-13-01', '2024-02-30', '2024-03-15']
})

# Try to parse, invalid become NaT
df['date'] = pd.to_datetime(df['date_str'], errors='coerce')
df['date_valid'] = df['date'].notna()
#     date_str       date  date_valid
# 0 2024-01-01 2024-01-01        True
# 1 2024-13-01        NaT       False
# 2 2024-02-30        NaT       False
# 3 2024-03-15 2024-03-15        True
```

### Numeric Range Validation

```python title="Validate numeric ranges"
df = pd.DataFrame({
    'temperature': [-300, 25, 30, 500],  # -300 and 500 invalid
    'humidity': [45, 60, 105, 80]  # 105 invalid (0-100)
})

# Define valid ranges
ranges = {
    'temperature': (-100, 100),
    'humidity': (0, 100)
}

# Validate
for col, (min_val, max_val) in ranges.items():
    df[f'{col}_valid'] = df[col].between(min_val, max_val)

# Get all invalid rows
is_valid = df[[c for c in df.columns if c.endswith('_valid')]].all(axis=1)
invalid_rows = df[~is_valid]
```

## Handling Invalid Data

### Flag and Keep

```python title="Mark invalid data without removing"
df = pd.DataFrame({
    'value': [10, -5, 20, 1000, 30]
})

# Flag outliers
Q1 = df['value'].quantile(0.25)
Q3 = df['value'].quantile(0.75)
IQR = Q3 - Q1
df['is_outlier'] = (df['value'] < Q1 - 1.5*IQR) | (df['value'] > Q3 + 1.5*IQR)

# Analyze with and without outliers
print(f"Mean with outliers: {df['value'].mean()}")
print(f"Mean without: {df[~df['is_outlier']]['value'].mean()}")
```

### Separate Invalid Records

```python title="Split valid and invalid data"
df = pd.DataFrame({
    'id': [1, 2, 3, 4],
    'age': [25, -5, 30, 150]
})

# Separate valid and invalid
valid_mask = df['age'].between(0, 120)
df_valid = df[valid_mask]
df_invalid = df[~valid_mask]

# Save for review
df_invalid.to_csv('invalid_records.csv', index=False)
df_valid.to_csv('valid_records.csv', index=False)
```

### Apply Corrections

```python title="Auto-correct common issues"
df = pd.DataFrame({
    'email': ['USER@TEST.COM', ' user@test.com ', 'user@TEST.com']
})

# Standardize emails
df['email_clean'] = (df['email']
    .str.strip()           # Remove whitespace
    .str.lower()           # Lowercase
)
#               email     email_clean
# 0   USER@TEST.COM   user@test.com
# 1  user@test.com    user@test.com
# 2   user@TEST.com   user@test.com
```

## Quick Reference

**Detect outliers:**

```python
# Z-score method
z_scores = np.abs((df['col'] - df['col'].mean()) / df['col'].std())
outliers = df[z_scores > 3]

# IQR method
Q1, Q3 = df['col'].quantile([0.25, 0.75])
IQR = Q3 - Q1
outliers = df[(df['col'] < Q1-1.5*IQR) | (df['col'] > Q3+1.5*IQR)]

# Percentile method
upper = df['col'].quantile(0.99)
outliers = df[df['col'] > upper]
```

**Handle outliers:**

```python
df_clean = df[~outliers_mask]           # Remove
df['col_capped'] = df['col'].clip(lower, upper)  # Cap
df['col_log'] = np.log(df['col'])       # Transform
```

**Validate:**

```python
df['valid'] = df['col'].between(min, max)  # Range
df['valid'] = df['col'].str.match(pattern)  # Pattern
df['valid'] = df['col'].notna()         # Not null
df['valid'] = ~df.duplicated(subset=['col'])  # Unique
```

**Common validations:**

```python
# Email
df['col'].str.contains(r'^[\w\.-]+@[\w\.-]+\.\w+$')

# Phone (US)
df['col'].str.match(r'^\d{3}-\d{3}-\d{4}$')

# Zip code (US)
df['col'].str.match(r'^\d{5}$')

# Date
pd.to_datetime(df['col'], errors='coerce').notna()
```
