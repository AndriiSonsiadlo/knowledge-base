---
id: overview
title: Pandas Overview
sidebar_label: Overview
tags: [ pandas, data-analysis, python ]
---

# Pandas Overview

## What is Pandas?

**_pandas_** is the most-used Python library for data manipulation and analysis. It provides DataFrames (2D tables) and
Series (1D arrays) that make working with structured data intuitive and powerful.

## When to Use Pandas

Use **_pandas_** for:

- Exploratory data analysis
- Data cleaning and preprocessing
- Datasets under ~10GB that fit in memory
- Time series analysis
- Structured/tabular data

Consider alternatives when:

- Data exceeds RAM (use _Dask_, _Polars_, or _PySpark_)
- Need maximum performance (try _Polars_)
- Working with streaming data

## Quick Example

```python title="Example"
import pandas as pd

# Read and explore
df = pd.read_csv('sales.csv')
print(df.head())
print(df.info())

# Clean and transform
df_clean = (df
            .dropna(subset=['revenue'])
            .query('revenue > 0')
            .assign(profit_margin=lambda x: x['profit'] / x['revenue'])
            )

# Aggregate
summary = (df_clean
           .groupby('category')['revenue']
           .agg(['sum', 'mean', 'count'])
           .sort_values('sum', ascending=False)
           )

# Export
summary.to_excel('summary.xlsx')
```

## Key Concepts

**Data Structures**

- Series: 1D labeled array
- DataFrame: 2D table
- Index: Row and column labels

**Selection**

- Column: `df['col']` or `df[['col1', 'col2']]`
- Position: `df.iloc[0:5, 0:3]`
- Label: `df.loc[rows, cols]`
- Filter: `df[df['col'] > 5]`

**Cleaning**

- Missing: `dropna()`, `fillna()`
- Types: `astype()`
- Strings: `.str` accessor
- Duplicates: `drop_duplicates()`

**Aggregation**

- Group: `groupby()`
- Combine: `merge()`, `join()`, `concat()`
- Reshape: `pivot_table()`, `melt()`

**Time Series**

- DateTime operations
- Resampling (daily → monthly)
- Rolling windows

## Typical Workflow

```
Import → Explore → Clean → Transform → Aggregate → Export
```

## Common Operations

| Task           | Command                   |
|----------------|---------------------------|
| Read CSV       | `pd.read_csv('file.csv')` |
| First 5 rows   | `df.head()`               |
| Data info      | `df.info()`               |
| Statistics     | `df.describe()`           |
| Select column  | `df['col']` or `df.col`   |
| Filter rows    | `df[df['col'] > 5]`       |
| Group by       | `df.groupby('col').sum()` |
| Missing values | `df.isnull().sum()`       |
| Sort           | `df.sort_values('col')`   |
| Save CSV       | `df.to_csv('file.csv')`   |

## Installation

Install `pandas` package with `pip`:

```bash title="Terminal"
pip install pandas
```

Verify installed package:

```python title="Python"
import pandas as pd

print(pd.__version__)
```

## Resources

- [Official pandas docs](https://pandas.pydata.org/docs/)
- [10 Minutes to pandas](https://pandas.pydata.org/docs/user_guide/10min.html)
