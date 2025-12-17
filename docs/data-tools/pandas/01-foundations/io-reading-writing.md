---
id: io-reading-writing
title: Reading and Writing Data
sidebar_label: I/O Operations
tags: [ pandas, data-analysis, python ]
---

# Reading and Writing Data

## Overview

**_pandas_** can read from and write to many file formats. The most common pattern is `pd.read_*()`
for reading and `df.to_*()` for writing.

**Common formats:**

- CSV: `read_csv()`, `to_csv()`
- Excel: `read_excel()`, `to_excel()`
- JSON: `read_json()`, `to_json()`
- SQL: `read_sql()`, `to_sql()`
- Parquet: `read_parquet()`, `to_parquet()`

## CSV Files

CSV is the most common format. It's plain text, human-readable, and
universally supported.

### Reading CSV

**Basic usage:**

```python
import pandas as pd

df = pd.read_csv('data.csv')
```

**Common parameters:**

```python
# Custom delimiter
df = pd.read_csv('data.tsv', sep='\t')  # Tab-separated
df = pd.read_csv('data.txt', sep='|')  # Pipe-separated

# Specify column names if file has no header
df = pd.read_csv('data.csv', header=None)
df = pd.read_csv('data.csv', names=['A', 'B', 'C'])

# Skip rows
df = pd.read_csv('data.csv', skiprows=3)  # Skip first 3 rows
df = pd.read_csv('data.csv', skiprows=[0, 2, 5])  # Skip specific rows

# Use specific column as index
df = pd.read_csv('data.csv', index_col=0)  # First column
df = pd.read_csv('data.csv', index_col='id')  # Column named 'id'

# Select specific columns
df = pd.read_csv('data.csv', usecols=['name', 'age'])
df = pd.read_csv('data.csv', usecols=[0, 1, 3])  # By position
```

**Data types:**

By default, **_pandas_** infers types, but you can be explicit:

```python
# Specify dtypes
df = pd.read_csv('data.csv', dtype={
    'age': int,
    'price': float,
    'category': 'category'  # Saves memory for repeated values
})

# Parse dates automatically
df = pd.read_csv('data.csv', parse_dates=['date_column'])

# Parse dates from multiple columns
df = pd.read_csv('data.csv', parse_dates=[['year', 'month', 'day']])
```

**Missing values:**

```python
# Recognize custom NA values
df = pd.read_csv('data.csv', na_values=['NA', 'missing', '?'])

# Different NA values per column
df = pd.read_csv('data.csv', na_values={
    'age': ['?', 'unknown'],
    'price': [0, -999]
})

# Keep default NA values
df = pd.read_csv('data.csv', keep_default_na=True)
```

**Large files:**

For files that don't fit in memory:

```python
# Read in chunks
chunk_size = 10000
chunks = []
for chunk in pd.read_csv('large.csv', chunksize=chunk_size):
    # Process each chunk
    processed = chunk[chunk['value'] > 0]
    chunks.append(processed)

df = pd.concat(chunks, ignore_index=True)

# Or read only n rows
df = pd.read_csv('large.csv', nrows=1000)  # First 1000 rows
```

**Encoding:**

If you see strange characters, check the encoding:

```python
# Common encodings
df = pd.read_csv('data.csv', encoding='utf-8')  # Default
df = pd.read_csv('data.csv', encoding='latin-1')  # Western European
df = pd.read_csv('data.csv', encoding='cp1252')  # Windows

# Let pandas guess
df = pd.read_csv('data.csv', encoding_errors='ignore')
```

### Writing CSV

```python
# Basic write
df.to_csv('output.csv')

# Without row index
df.to_csv('output.csv', index=False)

# Custom separator
df.to_csv('output.tsv', sep='\t')

# Select columns
df.to_csv('output.csv', columns=['name', 'age'])

# Custom NA representation
df.to_csv('output.csv', na_rep='NULL')

# Append to existing file
df.to_csv('output.csv', mode='a', header=False)

# Compression
df.to_csv('output.csv.gz', compression='gzip')
df.to_csv('output.csv.zip', compression='zip')
```

## Excel Files

Excel files (.xlsx, .xls) can contain multiple sheets and formatting. Reading Excel requires the
`openpyxl` or `xlrd` library.

```shell
# Install if needed
pip install openpyxl
```

### Reading Excel

```python
# Read first sheet
df = pd.read_excel('data.xlsx')

# Specific sheet by name
df = pd.read_excel('data.xlsx', sheet_name='Sheet1')

# Specific sheet by position
df = pd.read_excel('data.xlsx', sheet_name=0)  # First sheet

# Read all sheets into dictionary
dfs = pd.read_excel('data.xlsx', sheet_name=None)
# dfs = {'Sheet1': df1, 'Sheet2': df2, ...}

# Multiple specific sheets
dfs = pd.read_excel('data.xlsx', sheet_name=['Sheet1', 'Sheet3'])
```

**Other parameters work like CSV:**

```python
df = pd.read_excel(
    'data.xlsx',
    sheet_name='Data',
    skiprows=2,  # Skip first 2 rows
    usecols='A:D',  # Columns A through D
    nrows=100,  # Read only 100 rows
    dtype={'age': int},
    na_values=['N/A']
)

# Column range by position
df = pd.read_excel('data.xlsx', usecols=[0, 1, 2])

# Named ranges (if defined in Excel)
df = pd.read_excel('data.xlsx', usecols='SalesData')
```

### Writing Excel

```python
# Basic write
df.to_excel('output.xlsx', index=False)

# Specific sheet name
df.to_excel('output.xlsx', sheet_name='MyData', index=False)

# Multiple sheets
with pd.ExcelWriter('output.xlsx') as writer:
    df1.to_excel(writer, sheet_name='Sales', index=False)
    df2.to_excel(writer, sheet_name='Customers', index=False)
    df3.to_excel(writer, sheet_name='Products', index=False)

# Append to existing file (requires openpyxl)
with pd.ExcelWriter('existing.xlsx', mode='a') as writer:
    df.to_excel(writer, sheet_name='NewSheet')
```

**Formatting (requires openpyxl):**

```python
with pd.ExcelWriter('formatted.xlsx', engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Data', index=False)

    # Access worksheet for formatting
    worksheet = writer.sheets['Data']
    worksheet.column_dimensions['A'].width = 20
```

## JSON Files

JSON is common for web APIs and nested data structures.

### Reading JSON

```python
# From file
df = pd.read_json('data.json')

# From string
json_str = '{"name": ["Alice", "Bob"], "age": [25, 30]}'
df = pd.read_json(json_str)

# Orientation matters
# records: [{col: val}, {col: val}]
df = pd.read_json('data.json', orient='records')

# columns: {col: {index: val}}
df = pd.read_json('data.json', orient='columns')

# index: {index: {col: val}}
df = pd.read_json('data.json', orient='index')
```

**Common JSON structures:**

```python
# Array of objects (most common from APIs)
# [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
df = pd.read_json('data.json', orient='records')

# Nested JSON requires normalization
import json

with open('nested.json') as f:
    data = json.load(f)
df = pd.json_normalize(data)

# Example: API response with nested data
# {"users": [{"name": "Alice", "address": {"city": "NYC"}}]}
df = pd.json_normalize(data['users'])
# Columns: name, address.city
```

### Writing JSON

```python
# Default orientation
df.to_json('output.json')

# Records format (array of objects)
df.to_json('output.json', orient='records')

# Pretty print with indentation
df.to_json('output.json', orient='records', indent=2)

# Specific date format
df.to_json('output.json', date_format='iso')

# Split format (useful for archiving)
df.to_json('output.json', orient='split')
```

## SQL Databases

**_pandas_** can read from and write to SQL databases. Requires `sqlalchemy` or database-specific driver.

```shell
pip install sqlalchemy psycopg2-binary  # For PostgreSQL
pip install sqlalchemy pymysql          # For MySQL
```

### Reading from SQL

```python
from sqlalchemy import create_engine

# Create connection
engine = create_engine('postgresql://user:password@localhost:5432/dbname')
# or: sqlite:///path/to/database.db
# or: mysql+pymysql://user:password@localhost/dbname

# Read entire table
df = pd.read_sql_table('table_name', engine)

# Execute query
query = "SELECT * FROM users WHERE age > 25"
df = pd.read_sql_query(query, engine)

# Auto-detect (table or query)
df = pd.read_sql("SELECT * FROM users", engine)

# With parameters (prevents SQL injection)
query = "SELECT * FROM users WHERE age > %(min_age)s"
df = pd.read_sql_query(query, engine, params={'min_age': 25})

# Parse dates
df = pd.read_sql_query(
    "SELECT * FROM events",
    engine,
    parse_dates=['created_at', 'updated_at']
)
```

**Reading in chunks:**

```python
# For large tables
for chunk in pd.read_sql_query(query, engine, chunksize=10000):
    # Process each chunk
    process(chunk)
```

### Writing to SQL

```python
# Write DataFrame to SQL
df.to_sql('table_name', engine, if_exists='replace', index=False)

# if_exists options:
# 'fail': Raise error if table exists (default)
# 'replace': Drop table and recreate
# 'append': Add data to existing table

# Append data
df.to_sql('logs', engine, if_exists='append', index=False)

# Specify data types
from sqlalchemy.types import Integer, String, Float

df.to_sql('table_name', engine, dtype={
    'id': Integer,
    'name': String(50),
    'price': Float
})

# Write in chunks (for large DataFrames)
df.to_sql('table_name', engine, chunksize=1000)
```

## Parquet Files

Parquet is a columnar storage format that's fast and efficient. Excellent for large datasets.

```shell
pip install pyarrow
# or: 
pip install fastparquet
```

### Why Parquet?

- **Fast**: Much faster than CSV for reading/writing
- **Compact**: Compressed by default, smaller file sizes
- **Type-safe**: Preserves data types exactly
- **Columnar**: Efficient for selecting specific columns

```python
# Write parquet
df.to_parquet('data.parquet')

# With specific engine
df.to_parquet('data.parquet', engine='pyarrow')

# Compression options
df.to_parquet('data.parquet', compression='gzip')
df.to_parquet('data.parquet', compression='snappy')  # Faster
df.to_parquet('data.parquet', compression='brotli')  # Better compression

# Read parquet
df = pd.read_parquet('data.parquet')

# Read specific columns only
df = pd.read_parquet('data.parquet', columns=['name', 'age'])

# Read with filters (requires pyarrow)
df = pd.read_parquet(
    'data.parquet',
    filters=[('age', '>', 25)]
)
```

**When to use Parquet:**

- Storing intermediate analysis results
- Archiving processed data
- Sharing data between Python and other tools (Spark, R)
- Need to preserve exact data types

## Other Formats

### HTML Tables

```python
# Read tables from HTML
dfs = pd.read_html('https://example.com/data.html')  # Returns list of DataFrames
df = dfs[0]  # First table

# Read from local file
dfs = pd.read_html('file.html')

# Write HTML table
df.to_html('output.html', index=False)
```

### Clipboard

Useful for quick copy-paste:

```python
# Copy from clipboard (e.g., Excel selection)
df = pd.read_clipboard()

# Copy to clipboard
df.to_clipboard(index=False)
```

### Pickle (Python-specific)

Preserves pandas objects exactly, but only for Python:

```python
# Save
df.to_pickle('data.pkl')

# Load
df = pd.read_pickle('data.pkl')
```

Warning: Pickle files can execute arbitrary code. Only use with trusted sources.

### Feather

Fast binary format, interoperable with R and other languages:

```shell
pip install pyarrow
```

```python
df.to_feather('data.feather')
df = pd.read_feather('data.feather')
```

## Best Practices

**Choosing a format:**

- **CSV**: Human-readable, universal compatibility, simple data
- **Excel**: Sharing with non-programmers, multiple sheets, small datasets
- **Parquet**: Large datasets, preserving types, archiving, performance
- **JSON**: Web APIs, nested structures, configuration
- **SQL**: Centralized data, complex queries, multi-user access

**Performance tips:**

```python
# For large CSVs, specify dtypes upfront
df = pd.read_csv('large.csv', dtype={
    'id': 'int32',  # Instead of int64
    'category': 'category',  # Instead of object
    'price': 'float32'  # Instead of float64
})

# Use chunksize for files larger than RAM
for chunk in pd.read_csv('huge.csv', chunksize=50000):
    process(chunk)

# Use Parquet for repeated reads
df = pd.read_csv('data.csv')
df.to_parquet('data.parquet')  # One-time conversion
df = pd.read_parquet('data.parquet')  # Much faster subsequent reads
```

**Data integrity:**

```python
# Always check data after reading
df.info()  # Types, non-null counts
df.head()  # First few rows
df.describe()  # Statistics
df.isnull().sum()  # Missing values per column

# Verify critical columns
assert df['id'].is_unique
assert df['price'].min() >= 0
```

**Memory management:**

```python
# Check memory usage
df.memory_usage(deep=True).sum() / 1024 ** 2  # MB

# Optimize dtypes after reading
df['category'] = df['category'].astype('category')
df['year'] = df['year'].astype('int16')  # If values fit

# Read only needed columns
df = pd.read_csv('data.csv', usecols=['id', 'name', 'price'])
```

## Quick Reference

**Reading:**

```python
pd.read_csv('file.csv')
pd.read_excel('file.xlsx', sheet_name='Sheet1')
pd.read_json('file.json', orient='records')
pd.read_sql('SELECT * FROM table', engine)
pd.read_parquet('file.parquet')
```

**Writing:**

```python
df.to_csv('file.csv', index=False)
df.to_excel('file.xlsx', sheet_name='Data', index=False)
df.to_json('file.json', orient='records')
df.to_sql('table', engine, if_exists='replace')
df.to_parquet('file.parquet')
```

**Common parameters:**

```python
index = False  # Don't write index
usecols = ['A', 'B']  # Read specific columns
dtype = {'col': int}  # Specify types
parse_dates = ['date']  # Parse as datetime
na_values = ['?', 'NA']  # Recognize missing values
chunksize = 10000  # Read in chunks
```
