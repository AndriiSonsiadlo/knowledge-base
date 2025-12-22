---
id: interview-snippets
title: Interview Snippets
sidebar_label: Interview Snippets
tags: [pandas, interview, coding, questions]
---

# Interview Snippets

## Overview

Common pandas questions asked in data science and analytics interviews. Each snippet includes the problem, solution, and explanation.

## Data Manipulation

### Find Duplicate Rows

**Question:** Find all duplicate rows in a DataFrame.

```python title="Find duplicates"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Alice', 'Charlie'],
    'age': [25, 30, 25, 35]
})

# Find duplicates
duplicates = df[df.duplicated(keep=False)]
#     name  age
# 0  Alice   25
# 2  Alice   25

# Find first duplicate only
duplicates = df[df.duplicated(keep='first')]
#     name  age
# 2  Alice   25

# Count duplicates per combination
dup_counts = df.groupby(df.columns.tolist()).size().reset_index(name='count')
dup_counts = dup_counts[dup_counts['count'] > 1]
```

### Top N per Group

**Question:** Get top 3 highest values per category.

```python title="Top N per group"
df = pd.DataFrame({
    'category': ['A', 'A', 'A', 'B', 'B', 'B', 'A', 'B'],
    'value': [10, 20, 15, 25, 30, 22, 18, 28]
})

# Method 1: Using groupby + nlargest
top3 = df.groupby('category').apply(
    lambda x: x.nlargest(3, 'value')
).reset_index(drop=True)

# Method 2: Using sort + groupby + head
top3 = (df.sort_values('value', ascending=False)
          .groupby('category')
          .head(3))

# Method 3: Using rank
df['rank'] = df.groupby('category')['value'].rank(ascending=False)
top3 = df[df['rank'] <= 3]
```

### Second Highest Value

**Question:** Find the second highest salary per department.

```python title="Second highest value"
df = pd.DataFrame({
    'department': ['Sales', 'Sales', 'IT', 'IT', 'Sales'],
    'salary': [50000, 60000, 70000, 65000, 55000]
})

# Method 1: Using nlargest
second_highest = df.groupby('department')['salary'].nlargest(2).groupby('department').last()

# Method 2: Using rank
df['rank'] = df.groupby('department')['salary'].rank(ascending=False, method='dense')
second_highest = df[df['rank'] == 2]

# Method 3: Using sort
second_highest = (df.sort_values('salary', ascending=False)
                    .groupby('department')
                    .nth(1))
```

### Pivot with Aggregation

**Question:** Create a pivot table showing average sales by product and region.

```python title="Pivot table with aggregation"
df = pd.DataFrame({
    'product': ['A', 'B', 'A', 'B', 'A', 'B'],
    'region': ['East', 'East', 'West', 'West', 'East', 'West'],
    'sales': [100, 150, 120, 180, 110, 170]
})

# Pivot table
result = df.pivot_table(
    index='product',
    columns='region',
    values='sales',
    aggfunc='mean'
)
# region   East  West
# product            
# A       105.0   120
# B       150.0   175

# With multiple aggregations
result = df.pivot_table(
    index='product',
    columns='region',
    values='sales',
    aggfunc=['mean', 'sum', 'count']
)
```

## String Operations

### Extract from String

**Question:** Extract domain from email addresses.

```python title="Extract domain from email"
df = pd.DataFrame({
    'email': ['alice@gmail.com', 'bob@yahoo.com', 'charlie@gmail.com']
})

# Extract domain
df['domain'] = df['email'].str.split('@').str[1]
# Or using extract
df['domain'] = df['email'].str.extract(r'@(.+)')

#              email      domain
# 0  alice@gmail.com   gmail.com
# 1   bob@yahoo.com   yahoo.com
# 2  charlie@gmail.com  gmail.com
```

### Clean Phone Numbers

**Question:** Standardize phone numbers to XXX-XXX-XXXX format.

```python title="Standardize phone numbers"
df = pd.DataFrame({
    'phone': ['(123) 456-7890', '555.123.4567', '9998887777']
})

# Remove all non-digits
df['cleaned'] = df['phone'].str.replace(r'\D', '', regex=True)

# Format as XXX-XXX-XXXX
df['formatted'] = df['cleaned'].str.replace(
    r'(\d{3})(\d{3})(\d{4})',
    r'\1-\2-\3',
    regex=True
)
#             phone     cleaned     formatted
# 0  (123) 456-7890  1234567890  123-456-7890
# 1   555.123.4567  5551234567  555-123-4567
# 2      9998887777  9998887777  999-888-7777
```

## Missing Data

### Fill Missing with Group Mean

**Question:** Fill missing values with the mean of their group.

```python title="Fill NaN with group mean"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B', 'A'],
    'value': [10, np.nan, 15, 25, 20]
})

# Fill with group mean
df['value'] = df.groupby('category')['value'].transform(
    lambda x: x.fillna(x.mean())
)
#   category  value
# 0        A   10.0
# 1        A   15.0  # Filled with mean of A: (10+20)/2
# 2        B   15.0
# 3        B   25.0
# 4        A   20.0
```

### Forward Fill by Group

**Question:** Forward fill missing values within each group.

```python title="Forward fill within groups"
df = pd.DataFrame({
    'id': [1, 1, 1, 2, 2, 2],
    'value': [10, np.nan, np.nan, 20, np.nan, 30]
})

# Forward fill per group
df['filled'] = df.groupby('id')['value'].ffill()
#    id  value  filled
# 0   1   10.0    10.0
# 1   1    NaN    10.0
# 2   1    NaN    10.0
# 3   2   20.0    20.0
# 4   2    NaN    20.0
# 5   2   30.0    30.0
```

## DateTime Operations

### Calculate Age from Birthdate

**Question:** Calculate age from birthdate.

```python title="Calculate age"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'birthdate': pd.to_datetime(['1990-05-15', '1985-08-20', '1995-12-10'])
})

today = pd.Timestamp('2024-01-15')
df['age'] = ((today - df['birthdate']).dt.days / 365.25).astype(int)
#       name  birthdate  age
# 0    Alice 1990-05-15   33
# 1      Bob 1985-08-20   38
# 2  Charlie 1995-12-10   28
```

### Business Days Between Dates

**Question:** Calculate business days between two dates.

```python title="Count business days"
df = pd.DataFrame({
    'start': pd.to_datetime(['2024-01-01', '2024-02-01']),
    'end': pd.to_datetime(['2024-01-15', '2024-02-15'])
})

# Count business days
df['business_days'] = df.apply(
    lambda row: len(pd.bdate_range(row['start'], row['end'])),
    axis=1
)
#        start        end  business_days
# 0 2024-01-01 2024-01-15             11
# 1 2024-02-01 2024-02-15             11
```

### Filter Last N Days

**Question:** Get records from the last 30 days.

```python title="Filter recent records"
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=100),
    'value': range(100)
})

# Last 30 days from most recent date
end_date = df['date'].max()
start_date = end_date - pd.Timedelta(days=30)
recent = df[df['date'] >= start_date]

# Alternative
recent = df[df['date'] >= df['date'].max() - pd.Timedelta(days=30)]
```

## Aggregation & GroupBy

### Running Total by Group

**Question:** Calculate cumulative sum per category.

```python title="Cumulative sum per group"
df = pd.DataFrame({
    'category': ['A', 'A', 'A', 'B', 'B', 'B'],
    'value': [10, 20, 15, 25, 30, 22]
})

df['cumsum'] = df.groupby('category')['value'].cumsum()
#   category  value  cumsum
# 0        A     10      10
# 1        A     20      30
# 2        A     15      45
# 3        B     25      25
# 4        B     30      55
# 5        B     22      77
```

### Percentage of Total per Group

**Question:** Calculate each value as percentage of group total.

```python title="Percentage within groups"
df = pd.DataFrame({
    'category': ['A', 'A', 'B', 'B'],
    'value': [100, 150, 200, 250]
})

df['pct_of_group'] = df.groupby('category')['value'].transform(
    lambda x: x / x.sum() * 100
)
#   category  value  pct_of_group
# 0        A    100          40.0
# 1        A    150          60.0
# 2        B    200          44.44
# 3        B    250          55.56
```

### Rank Within Groups

**Question:** Rank values within each group.

```python title="Rank within groups"
df = pd.DataFrame({
    'department': ['Sales', 'Sales', 'IT', 'IT', 'Sales'],
    'salary': [50000, 60000, 70000, 65000, 55000]
})

df['rank'] = df.groupby('department')['salary'].rank(ascending=False)
#   department  salary  rank
# 0      Sales   50000   3.0
# 1      Sales   60000   1.0
# 2         IT   70000   1.0
# 3         IT   65000   2.0
# 4      Sales   55000   2.0
```

## Merging & Joining

### Find Unmatched Records

**Question:** Find records in left DataFrame that don't have a match in right.

```python title="Find unmatched records"
left = pd.DataFrame({
    'id': [1, 2, 3, 4],
    'name': ['Alice', 'Bob', 'Charlie', 'David']
})

right = pd.DataFrame({
    'id': [1, 2, 5],
    'value': [100, 200, 300]
})

# Find unmatched
merged = pd.merge(left, right, on='id', how='left', indicator=True)
unmatched = merged[merged['_merge'] == 'left_only']
#    id     name  value      _merge
# 2   3  Charlie    NaN   left_only
# 3   4    David    NaN   left_only
```

### Merge Multiple DataFrames

**Question:** Merge three DataFrames on a common key.

```python title="Merge multiple DataFrames"
df1 = pd.DataFrame({'id': [1, 2], 'a': [10, 20]})
df2 = pd.DataFrame({'id': [1, 2], 'b': [30, 40]})
df3 = pd.DataFrame({'id': [1, 2], 'c': [50, 60]})

# Method 1: Chain merges
result = df1.merge(df2, on='id').merge(df3, on='id')

# Method 2: Using reduce
from functools import reduce
dfs = [df1, df2, df3]
result = reduce(lambda left, right: pd.merge(left, right, on='id'), dfs)
#    id   a   b   c
# 0   1  10  30  50
# 1   2  20  40  60
```

## Performance & Optimization

### Optimize Data Types

**Question:** Reduce memory usage of a DataFrame.

```python title="Optimize memory usage"
df = pd.DataFrame({
    'category': ['A', 'B', 'A', 'B'] * 1000,
    'value': range(4000)
})

# Check memory
print(df.memory_usage(deep=True))

# Optimize
df['category'] = df['category'].astype('category')
df['value'] = pd.to_numeric(df['value'], downcast='integer')

# Memory reduced significantly
print(df.memory_usage(deep=True))
```

### Vectorized vs Loop

**Question:** Calculate a new column efficiently.

```python title="Vectorization vs loops"
df = pd.DataFrame({
    'a': range(10000),
    'b': range(10000)
})

# Bad: Loop (slow)
result = []
for i in range(len(df)):
    result.append(df.loc[i, 'a'] + df.loc[i, 'b'])
df['sum'] = result

# Good: Vectorized (fast)
df['sum'] = df['a'] + df['b']

# Bad: Apply with simple operation
df['sum'] = df.apply(lambda row: row['a'] + row['b'], axis=1)

# Good: Vectorized
df['sum'] = df['a'] + df['b']
```

## Complex Queries

### Consecutive Days

**Question:** Find records with 3 or more consecutive days of data.

```python title="Find consecutive sequences"
df = pd.DataFrame({
    'date': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03', 
                            '2024-01-05', '2024-01-06', '2024-01-10'])
})

# Calculate day differences
df['day_diff'] = df['date'].diff().dt.days

# Mark new sequences
df['new_seq'] = (df['day_diff'] != 1) | (df['day_diff'].isna())
df['seq_id'] = df['new_seq'].cumsum()

# Count sequence lengths
seq_lengths = df.groupby('seq_id').size()

# Filter sequences with 3+ days
long_sequences = seq_lengths[seq_lengths >= 3]
result = df[df['seq_id'].isin(long_sequences.index)]
```

### Remove Outliers by Group

**Question:** Remove outliers using IQR method per category.

```python title="Remove outliers per group"
df = pd.DataFrame({
    'category': ['A'] * 10 + ['B'] * 10,
    'value': [1, 2, 3, 4, 5, 100, 7, 8, 9, 10,  # 100 is outlier in A
              20, 22, 24, 26, 28, 30, 32, 34, 200, 38]  # 200 is outlier in B
})

def remove_outliers(group):
    Q1 = group['value'].quantile(0.25)
    Q3 = group['value'].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return group[(group['value'] >= lower) & (group['value'] <= upper)]

cleaned = df.groupby('category').apply(remove_outliers).reset_index(drop=True)
```

### Transpose with Aggregation

**Question:** Reshape data from long to wide with multiple value columns.

```python title="Complex pivot"
df = pd.DataFrame({
    'date': ['2024-01-01', '2024-01-01', '2024-01-02', '2024-01-02'],
    'metric': ['sales', 'profit', 'sales', 'profit'],
    'value': [100, 20, 120, 25]
})

# Pivot to wide format
wide = df.pivot(index='date', columns='metric', values='value')
# metric      profit  sales
# date                     
# 2024-01-01      20    100
# 2024-01-02      25    120

# Calculate margin
wide['margin'] = (wide['profit'] / wide['sales'] * 100).round(2)
```

## SQL-Like Operations

### Window Functions

**Question:** Calculate difference from previous row per group.

```python title="Lag/Lead calculations"
df = pd.DataFrame({
    'id': [1, 1, 1, 2, 2, 2],
    'date': pd.date_range('2024-01-01', periods=6),
    'value': [10, 15, 20, 30, 35, 40]
})

# Lag (previous value)
df['prev_value'] = df.groupby('id')['value'].shift(1)

# Calculate change
df['change'] = df['value'] - df['prev_value']

# Percentage change
df['pct_change'] = df.groupby('id')['value'].pct_change() * 100
```

### Self Join

**Question:** Find pairs of records that meet a condition.

```python title="Self join pattern"
df = pd.DataFrame({
    'employee': ['Alice', 'Bob', 'Charlie'],
    'manager': ['Bob', 'Charlie', None]
})

# Find employee-manager pairs
result = pd.merge(
    df,
    df,
    left_on='manager',
    right_on='employee',
    suffixes=('_emp', '_mgr')
)
#   employee_emp manager_emp employee_mgr manager_mgr
# 0        Alice         Bob          Bob     Charlie
# 1          Bob     Charlie      Charlie        None
```

## Quick Tips

**Common mistakes to avoid:**

```python
# Don't: Chained indexing
df[df['col'] > 5]['new_col'] = 10  # Warning!

# Do: Use loc
df.loc[df['col'] > 5, 'new_col'] = 10

# Don't: Loop through rows
for i in range(len(df)):
    df.loc[i, 'new'] = df.loc[i, 'a'] + df.loc[i, 'b']

# Do: Vectorize
df['new'] = df['a'] + df['b']

# Don't: Repeated concatenation
result = pd.DataFrame()
for chunk in chunks:
    result = pd.concat([result, chunk])

# Do: Collect then concat once
results = []
for chunk in chunks:
    results.append(chunk)
result = pd.concat(results)
```

**One-liners:**

```python
# Top 3 per group
df.sort_values('val', ascending=False).groupby('cat').head(3)

# Remove duplicates keeping last
df.drop_duplicates(subset=['id'], keep='last')

# Fill forward then backward
df['col'].ffill().bfill()

# Conditional column
df['label'] = np.where(df['val'] > 100, 'high', 'low')

# Multiple conditions
df['label'] = np.select(
    [df['val'] < 50, df['val'] < 100],
    ['low', 'medium'],
    default='high'
)

# Percentage change
df['pct_change'] = df['value'].pct_change() * 100

# Rank with ties
df['rank'] = df['score'].rank(method='dense', ascending=False)

# Group and get first/last
df.groupby('id').first()
df.groupby('id').last()
```

**Interview preparation checklist:**

- Know difference between loc and iloc
- Understand merge types (inner, left, right, outer)
- Master groupby operations
- Handle missing data appropriately
- Use vectorized operations over loops
- Know when to use apply vs vectorization
- Understand datetime operations
- Practice reshaping (pivot, melt)
- Optimize data types for memory
- Write readable, efficient code
