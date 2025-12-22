---
id: datetime-basics
title: DateTime Basics
sidebar_label: DateTime Basics
tags: [pandas, datetime, time-series, dates]
---

# DateTime Basics

## Overview

Working with dates and times is essential for time series analysis. pandas provides powerful datetime functionality through:

- **Parsing**: Convert strings to datetime
- **Components**: Extract year, month, day, etc.
- **Arithmetic**: Calculate differences and offsets
- **Formatting**: Convert datetime to strings

## Creating DateTime Objects

### to_datetime() - Parse Dates

```python title="Convert strings to datetime"
import pandas as pd

df = pd.DataFrame({
    'date_str': ['2024-01-15', '2024-02-20', '2024-03-10']
})

# Convert to datetime
df['date'] = pd.to_datetime(df['date_str'])
df['date'].dtype  # datetime64[ns]

#     date_str       date
# 0  2024-01-15 2024-01-15
# 1  2024-02-20 2024-02-20
# 2  2024-03-10 2024-03-10
```

### Different Date Formats

```python title="Parse various date formats"
dates = pd.Series([
    '2024-01-15',      # ISO format
    '01/15/2024',      # US format
    '15-Jan-2024',     # Month name
    'January 15, 2024' # Full text
])

# Auto-detect format
parsed = pd.to_datetime(dates)

# Specify format for speed
df['date'] = pd.to_datetime(df['date_str'], format='%Y-%m-%d')

# Common format codes:
# %Y - 4-digit year (2024)
# %y - 2-digit year (24)
# %m - Month as number (01-12)
# %d - Day of month (01-31)
# %H - Hour 24-hour (00-23)
# %M - Minute (00-59)
# %S - Second (00-59)
```

:::info
Specify the format with `format` parameter for 10-50x faster parsing on large datasets when all dates follow the same pattern.
:::

### Handle Invalid Dates

```python title="Deal with invalid date strings"
dates = pd.Series(['2024-01-15', 'invalid', '2024-02-30'])

# errors='raise' - raise exception (default)
# pd.to_datetime(dates)  # ValueError!

# errors='coerce' - invalid becomes NaT (Not a Time)
parsed = pd.to_datetime(dates, errors='coerce')
# 0   2024-01-15
# 1          NaT
# 2          NaT

# errors='ignore' - leave invalid as-is
parsed = pd.to_datetime(dates, errors='ignore')
# 0    2024-01-15
# 1       invalid
# 2    2024-02-30
```

### Parse from Components

```python title="Create datetime from separate columns"
df = pd.DataFrame({
    'year': [2024, 2024, 2024],
    'month': [1, 2, 3],
    'day': [15, 20, 10]
})

# Combine into datetime
df['date'] = pd.to_datetime(df[['year', 'month', 'day']])
#    year  month  day       date
# 0  2024      1   15 2024-01-15
# 1  2024      2   20 2024-02-20
# 2  2024      3   10 2024-03-10

# With time components
df = pd.DataFrame({
    'year': [2024], 'month': [1], 'day': [15],
    'hour': [14], 'minute': [30], 'second': [45]
})
df['datetime'] = pd.to_datetime(df)
# 0   2024-01-15 14:30:45
```

## DateTime Components (dt accessor)

Extract parts from datetime using `.dt` accessor:

```python title="Extract datetime components"
df = pd.DataFrame({
    'date': pd.to_datetime(['2024-01-15', '2024-02-20', '2024-03-10'])
})

# Date components
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day'] = df['date'].dt.day
df['day_of_week'] = df['date'].dt.dayofweek  # 0=Monday, 6=Sunday
df['day_of_year'] = df['date'].dt.dayofyear
df['quarter'] = df['date'].dt.quarter
df['week'] = df['date'].dt.isocalendar().week

#         date  year  month  day  day_of_week  day_of_year  quarter  week
# 0 2024-01-15  2024      1   15            0           15        1     3
# 1 2024-02-20  2024      2   20            1           51        1     8
# 2 2024-03-10  2024      3   10            6           70        1    10
```

### Named Components

```python title="Get text representations"
df = pd.DataFrame({
    'date': pd.to_datetime(['2024-01-15', '2024-02-20', '2024-03-10'])
})

# Month and day names
df['month_name'] = df['date'].dt.month_name()
df['day_name'] = df['date'].dt.day_name()

#         date   month_name   day_name
# 0 2024-01-15      January     Monday
# 1 2024-02-20     February    Tuesday
# 2 2024-03-10        March     Sunday

# Abbreviated
df['month_abbr'] = df['date'].dt.month_name().str[:3]
df['day_abbr'] = df['date'].dt.day_name().str[:3]
```

### Time Components

```python title="Extract time parts"
df = pd.DataFrame({
    'datetime': pd.to_datetime([
        '2024-01-15 14:30:45',
        '2024-02-20 09:15:30'
    ])
})

df['hour'] = df['datetime'].dt.hour
df['minute'] = df['datetime'].dt.minute
df['second'] = df['datetime'].dt.second
df['time'] = df['datetime'].dt.time  # Time only (no date)

#               datetime  hour  minute  second      time
# 0  2024-01-15 14:30:45    14      30      45  14:30:45
# 1  2024-02-20 09:15:30     9      15      30  09:15:30
```

## Date Arithmetic

### Date Differences

```python title="Calculate time differences"
df = pd.DataFrame({
    'start': pd.to_datetime(['2024-01-01', '2024-02-01']),
    'end': pd.to_datetime(['2024-01-15', '2024-02-20'])
})

# Calculate difference (returns Timedelta)
df['duration'] = df['end'] - df['start']
#        start        end   duration
# 0 2024-01-01 2024-01-15   14 days
# 1 2024-02-01 2024-02-20   19 days

# Extract days
df['days'] = (df['end'] - df['start']).dt.days
#        start        end   duration  days
# 0 2024-01-01 2024-01-15   14 days    14
# 1 2024-02-01 2024-02-20   19 days    19

# Total seconds
df['seconds'] = (df['end'] - df['start']).dt.total_seconds()
```

### Adding/Subtracting Time

```python title="Add or subtract time periods"
df = pd.DataFrame({
    'date': pd.to_datetime(['2024-01-15', '2024-02-20'])
})

# Add days
df['plus_7_days'] = df['date'] + pd.Timedelta(days=7)
#         date plus_7_days
# 0 2024-01-15  2024-01-22
# 1 2024-02-20  2024-02-27

# Subtract days
df['minus_3_days'] = df['date'] - pd.Timedelta(days=3)

# Add weeks
df['plus_2_weeks'] = df['date'] + pd.Timedelta(weeks=2)

# Add hours, minutes
df['plus_time'] = df['date'] + pd.Timedelta(hours=5, minutes=30)
```

### Date Offsets

```python title="Use DateOffset for business logic"
df = pd.DataFrame({
    'date': pd.to_datetime(['2024-01-15', '2024-02-20'])
})

# Add months (handles month-end properly)
df['plus_1_month'] = df['date'] + pd.DateOffset(months=1)
#         date plus_1_month
# 0 2024-01-15   2024-02-15
# 1 2024-02-20   2024-03-20

# Add years
df['plus_1_year'] = df['date'] + pd.DateOffset(years=1)

# Business day offset (skip weekends)
df['plus_5_bdays'] = df['date'] + pd.offsets.BDay(5)

# Month end
df['month_end'] = df['date'] + pd.offsets.MonthEnd(0)  # 0 = this month
```

:::success
Use `pd.DateOffset` for month/year arithmetic as it handles varying month lengths correctly. Use `pd.Timedelta` for fixed durations (days, hours).
:::

## Date Ranges

### date_range() - Generate Sequences

```python title="Create date sequences"
# Daily dates
dates = pd.date_range(start='2024-01-01', end='2024-01-10')
# DatetimeIndex(['2024-01-01', '2024-01-02', ..., '2024-01-10'])

# With periods instead of end
dates = pd.date_range(start='2024-01-01', periods=10)

# Different frequencies
daily = pd.date_range('2024-01-01', periods=7, freq='D')
weekly = pd.date_range('2024-01-01', periods=5, freq='W')
monthly = pd.date_range('2024-01-01', periods=12, freq='M')
quarterly = pd.date_range('2024-01-01', periods=4, freq='Q')

# Business days (Mon-Fri)
bdays = pd.date_range('2024-01-01', periods=10, freq='B')

# Hourly
hourly = pd.date_range('2024-01-01', periods=24, freq='H')
```

### Common Frequencies

```python title="Date range frequency codes"
# D - Calendar day
# B - Business day
# W - Weekly
# M - Month end
# MS - Month start
# Q - Quarter end
# QS - Quarter start
# Y - Year end
# YS - Year start
# H - Hourly
# T or min - Minutely
# S - Secondly

# Custom frequencies
every_3_days = pd.date_range('2024-01-01', periods=10, freq='3D')
every_2_hours = pd.date_range('2024-01-01 00:00', periods=12, freq='2H')
```

## Filtering by Dates

### Date Comparison

```python title="Filter by date conditions"
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=100),
    'value': range(100)
})

# Filter by date range
filtered = df[df['date'] >= '2024-02-01']
filtered = df[(df['date'] >= '2024-02-01') & (df['date'] <= '2024-02-29')]

# Filter by year
filtered = df[df['date'].dt.year == 2024]

# Filter by month
filtered = df[df['date'].dt.month == 2]  # February

# Filter by day of week
filtered = df[df['date'].dt.dayofweek == 0]  # Mondays only

# Filter by quarter
filtered = df[df['date'].dt.quarter == 1]  # Q1 only
```

### Date Range Filtering

```python title="Between dates"
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=365),
    'value': range(365)
})

# Between specific dates
mask = df['date'].between('2024-02-01', '2024-02-29')
february = df[mask]

# Last 30 days
from datetime import datetime, timedelta
end_date = datetime(2024, 3, 1)
start_date = end_date - timedelta(days=30)
recent = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
```

## DateTime Index

### Setting DateTime Index

```python title="Use datetime as index"
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=10),
    'value': range(10)
})

# Set date as index
df = df.set_index('date')
#             value
# date             
# 2024-01-01      0
# 2024-01-02      1
# 2024-01-03      2

# Benefits: can use date-based indexing
df.loc['2024-01-05']         # Single date
df.loc['2024-01-05':'2024-01-07']  # Date range
df.loc['2024-01']            # Entire month (if available)
```

### Partial String Indexing

```python title="Index by year, month, or day"
df = pd.DataFrame({
    'value': range(365)
}, index=pd.date_range('2024-01-01', periods=365))

# Select by year
df.loc['2024']

# Select by month
df.loc['2024-02']

# Select by specific date
df.loc['2024-02-15']

# Slice
df.loc['2024-01-15':'2024-01-20']
```

## Formatting DateTime

### Convert to String

```python title="Format datetime as string"
df = pd.DataFrame({
    'date': pd.to_datetime(['2024-01-15', '2024-02-20'])
})

# Default string conversion
df['date_str'] = df['date'].astype(str)
# '2024-01-15'

# Custom format
df['formatted'] = df['date'].dt.strftime('%Y-%m-%d')      # '2024-01-15'
df['formatted'] = df['date'].dt.strftime('%m/%d/%Y')      # '01/15/2024'
df['formatted'] = df['date'].dt.strftime('%B %d, %Y')     # 'January 15, 2024'
df['formatted'] = df['date'].dt.strftime('%Y-%m')         # '2024-01'

# Common formats:
# %Y-%m-%d        # 2024-01-15
# %m/%d/%Y        # 01/15/2024
# %d-%b-%Y        # 15-Jan-2024
# %B %d, %Y       # January 15, 2024
# %Y-%m-%d %H:%M  # 2024-01-15 14:30
```

## Common Patterns

### Age Calculation

```python title="Calculate age from birthdate"
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'birthdate': pd.to_datetime(['1990-05-15', '1985-08-20', '1995-12-10'])
})

# Calculate age
today = pd.Timestamp('2024-01-15')
df['age'] = ((today - df['birthdate']).dt.days / 365.25).astype(int)
#       name  birthdate  age
# 0    Alice 1990-05-15   33
# 1      Bob 1985-08-20   38
# 2  Charlie 1995-12-10   28
```

### Business Days Between Dates

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
```

### Extract Time Period

```python title="Group by time period"
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=100),
    'value': range(100)
})

# Add period columns for grouping
df['year_month'] = df['date'].dt.to_period('M')
df['year_quarter'] = df['date'].dt.to_period('Q')
df['year_week'] = df['date'].dt.to_period('W')

# Group and aggregate
monthly_sum = df.groupby('year_month')['value'].sum()
# year_month
# 2024-01    465
# 2024-02    899
# 2024-03    ...
```

### Days Until Event

```python title="Calculate days remaining"
df = pd.DataFrame({
    'event': ['Conference', 'Deadline', 'Meeting'],
    'date': pd.to_datetime(['2024-06-15', '2024-03-01', '2024-02-10'])
})

today = pd.Timestamp('2024-01-15')
df['days_until'] = (df['date'] - today).dt.days
df['status'] = df['days_until'].apply(
    lambda x: 'Past' if x < 0 else f'{x} days'
)
```

## Timezones

### Working with Timezones

```python title="Handle timezone-aware datetimes"
# Create timezone-aware dates
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=5, tz='UTC')
})

# Convert timezone
df['date_eastern'] = df['date'].dt.tz_convert('America/New_York')
df['date_pacific'] = df['date'].dt.tz_convert('America/Los_Angeles')

# Localize (add timezone to naive datetime)
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=5)
})
df['date_utc'] = df['date'].dt.tz_localize('UTC')

# Remove timezone
df['date_naive'] = df['date_utc'].dt.tz_localize(None)
```

## Performance Tips

```python title="Optimize datetime operations"
# Specify format for faster parsing
df['date'] = pd.to_datetime(df['date_str'], format='%Y-%m-%d')

# Use infer_datetime_format for mixed formats (slower but flexible)
df['date'] = pd.to_datetime(df['date_str'], infer_datetime_format=True)

# Cache datetime conversions
# Bad: repeated conversion
for i in range(1000):
    pd.to_datetime('2024-01-15')

# Good: convert once
date = pd.to_datetime('2024-01-15')
for i in range(1000):
    use(date)
```

:::warning
Always specify the `format` parameter in `pd.to_datetime()` when parsing large datasets with consistent date formats. It's 10-50x faster than auto-detection.
:::

## Common Mistakes

### String vs DateTime Comparison

```python title="Compare datetime objects correctly"
df = pd.DataFrame({
    'date_str': ['2024-01-15', '2024-02-20']
})

# Wrong: comparing strings
# df[df['date_str'] > '2024-02-01']  # String comparison!

# Correct: convert to datetime first
df['date'] = pd.to_datetime(df['date_str'])
df[df['date'] > '2024-02-01']  # DateTime comparison
```

### Month Arithmetic

```python title="Use DateOffset for months"
df = pd.DataFrame({
    'date': pd.to_datetime(['2024-01-31'])
})

# Wrong: Timedelta doesn't work for months
# df['date'] + pd.Timedelta(days=30)  # Not always 1 month

# Correct: use DateOffset
df['next_month'] = df['date'] + pd.DateOffset(months=1)
# 2024-02-29 (handles month-end correctly)
```

## Quick Reference

**Parsing:**

```python
pd.to_datetime(series)
pd.to_datetime(series, format='%Y-%m-%d')
pd.to_datetime(series, errors='coerce')
pd.to_datetime(df[['year', 'month', 'day']])
```

**Components (dt accessor):**

```python
df['date'].dt.year
df['date'].dt.month
df['date'].dt.day
df['date'].dt.dayofweek
df['date'].dt.month_name()
df['date'].dt.day_name()
```

**Arithmetic:**

```python
df['end'] - df['start']              # Difference
df['date'] + pd.Timedelta(days=7)    # Add days
df['date'] + pd.DateOffset(months=1) # Add months
(end - start).dt.days                # Extract days
```

**Date ranges:**

```python
pd.date_range('2024-01-01', '2024-12-31', freq='D')
pd.date_range('2024-01-01', periods=10, freq='B')
pd.bdate_range('2024-01-01', '2024-01-31')
```

**Filtering:**

```python
df[df['date'] > '2024-01-01']
df[df['date'].dt.month == 2]
df[df['date'].dt.dayofweek == 0]
df['date'].between('2024-01-01', '2024-01-31')
```

**Formatting:**

```python
df['date'].dt.strftime('%Y-%m-%d')
df['date'].dt.strftime('%m/%d/%Y')
df['date'].astype(str)
```
