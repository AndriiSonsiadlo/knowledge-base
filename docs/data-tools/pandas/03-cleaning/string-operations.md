---
id: string-operations
title: String Operations
sidebar_label: String Operations
tags: [pandas, strings, text, data-cleaning]
---

# String Operations

## Overview

pandas provides string methods through the `.str` accessor. These methods work on Series containing strings and are essential for text data cleaning.

## Basic String Methods

### Case Conversion

```python title="Change text case"
import pandas as pd

df = pd.DataFrame({
    'name': ['Alice Smith', 'BOB JONES', 'charlie Brown']
})

# Convert to lowercase
df['name'].str.lower()
# 0     alice smith
# 1       bob jones
# 2    charlie brown

# Convert to uppercase
df['name'].str.upper()
# 0     ALICE SMITH
# 1       BOB JONES
# 2    CHARLIE BROWN

# Title case (capitalize first letter of each word)
df['name'].str.title()
# 0     Alice Smith
# 1       Bob Jones
# 2    Charlie Brown

# Capitalize (only first letter)
df['name'].str.capitalize()
# 0     Alice smith
# 1       Bob jones
# 2    Charlie brown
```

### Strip Whitespace

```python title="Remove leading/trailing whitespace"
df = pd.DataFrame({
    'text': ['  hello  ', 'world  ', '  test']
})

# Remove both sides
df['text'].str.strip()
# 0    hello
# 1    world
# 2     test

# Remove left side only
df['text'].str.lstrip()
# 0    hello  
# 1    world  
# 2    test

# Remove right side only
df['text'].str.rstrip()
# 0      hello
# 1    world
# 2      test
```

Always strip whitespace when cleaning user input.

### String Length

```python title="Get string length"
df = pd.DataFrame({
    'text': ['hello', 'world', 'test']
})

df['text'].str.len()
# 0    5
# 1    5
# 2    4

# Filter by length
df[df['text'].str.len() > 4]
#     text
# 0  hello
# 1  world
```

## Finding and Replacing

### Contains

Check if string contains a pattern:

```python title="Check if strings contain pattern"
df = pd.DataFrame({
    'email': ['alice@gmail.com', 'bob@yahoo.com', 'charlie@gmail.com']
})

# Check if contains 'gmail'
df['email'].str.contains('gmail')
# 0     True
# 1    False
# 2     True

# Use in filtering
gmail_users = df[df['email'].str.contains('gmail')]
#              email
# 0  alice@gmail.com
# 2  charlie@gmail.com

# Case-insensitive search
df['email'].str.contains('GMAIL', case=False)

# Check for missing values (na=False to handle NaN)
df['email'].str.contains('gmail', na=False)
```

### Starts With / Ends With

```python title="Check string start or end"
df = pd.DataFrame({
    'filename': ['report.pdf', 'data.csv', 'image.png', 'notes.txt']
})

# Files ending with .pdf
df['filename'].str.endswith('.pdf')
# 0     True
# 1    False
# 2    False
# 3    False

# Files starting with 'data'
df['filename'].str.startswith('data')
# 0    False
# 1     True
# 2    False
# 3    False

# Filter PDF files
pdf_files = df[df['filename'].str.endswith('.pdf')]
```

### Replace

```python title="Replace substrings"
df = pd.DataFrame({
    'phone': ['123-456-7890', '555-123-4567', '999-888-7777']
})

# Replace hyphens with spaces
df['phone'].str.replace('-', ' ')
# 0    123 456 7890
# 1    555 123 4567
# 2    999 888 7777

# Remove all hyphens
df['phone'].str.replace('-', '')
# 0    1234567890
# 1    5551234567
# 2    9998887777

# Regex replacement (remove all non-digits)
df['phone'].str.replace(r'\D', '', regex=True)
# 0    1234567890
# 1    5551234567
# 2    9998887777

# Multiple replacements
df['phone'].str.replace('-', '').str.replace(' ', '')
```

## Splitting and Joining

### Split Strings

```python title="Split strings into parts"
df = pd.DataFrame({
    'name': ['Alice Smith', 'Bob Jones', 'Charlie Brown']
})

# Split into list
df['name'].str.split()
# 0     [Alice, Smith]
# 1       [Bob, Jones]
# 2    [Charlie, Brown]

# Split into separate columns
df[['first_name', 'last_name']] = df['name'].str.split(expand=True)
#       name first_name last_name
# 0   Alice Smith      Alice     Smith
# 1     Bob Jones        Bob     Jones
# 2  Charlie Brown    Charlie     Brown

# Split on specific delimiter
df = pd.DataFrame({
    'email': ['alice@gmail.com', 'bob@yahoo.com']
})
df[['username', 'domain']] = df['email'].str.split('@', expand=True)
#             email username     domain
# 0  alice@gmail.com    alice  gmail.com
# 1   bob@yahoo.com      bob  yahoo.com

# Get specific part
df['email'].str.split('@').str[0]  # Username
# 0    alice
# 1      bob
```

### Join Strings

```python title="Combine strings"
df = pd.DataFrame({
    'first': ['Alice', 'Bob'],
    'last': ['Smith', 'Jones']
})

# Concatenate columns
df['full_name'] = df['first'] + ' ' + df['last']
#   first   last      full_name
# 0 Alice  Smith    Alice Smith
# 1   Bob  Jones      Bob Jones

# Join with separator
df['full_name'] = df['first'].str.cat(df['last'], sep=' ')

# Join multiple columns
df['full'] = df['first'].str.cat([df['last']], sep=' ')
```

## Extracting Substrings

### Slicing

```python title="Extract parts of string"
df = pd.DataFrame({
    'code': ['ABC123', 'DEF456', 'GHI789']
})

# First 3 characters
df['code'].str[:3]
# 0    ABC
# 1    DEF
# 2    GHI

# Last 3 characters
df['code'].str[-3:]
# 0    123
# 1    456
# 2    789

# Characters 2-4
df['code'].str[2:4]
# 0    C1
# 1    F4
# 2    I7
```

### Extract with Regex

```python title="Extract patterns with regex"
df = pd.DataFrame({
    'text': ['Price: $100', 'Cost: $250', 'Value: $75']
})

# Extract numbers
df['text'].str.extract(r'(\d+)')
#      0
# 0  100
# 1  250
# 2   75

# Extract with named groups
df['text'].str.extract(r'(?P<label>\w+): \$(?P<amount>\d+)')
#     label amount
# 0   Price    100
# 1    Cost    250
# 2   Value     75

# Extract all occurrences
df = pd.DataFrame({
    'text': ['ID: 123, 456', 'ID: 789']
})
df['text'].str.extractall(r'(\d+)')
#        0
#   match
# 0 0      123
#   1      456
# 1 0      789
```

## Pattern Matching

### Match

```python title="Check if pattern matches from start"
df = pd.DataFrame({
    'code': ['ABC123', 'XYZ456', 'ABC789']
})

# Match codes starting with ABC
df['code'].str.match(r'^ABC')
# 0     True
# 1    False
# 2     True

# Use in filtering
abc_codes = df[df['code'].str.match(r'^ABC')]
#     code
# 0  ABC123
# 2  ABC789
```

### Find Position

```python title="Find substring position"
df = pd.DataFrame({
    'text': ['hello world', 'test hello', 'hello']
})

# Find position of 'hello'
df['text'].str.find('hello')
# 0    0  # Found at position 0
# 1    5  # Found at position 5
# 2    0  # Found at position 0

# Returns -1 if not found
df['text'].str.find('xyz')
# 0   -1
# 1   -1
# 2   -1
```

## Cleaning Operations

### Remove Special Characters

```python title="Clean special characters"
df = pd.DataFrame({
    'text': ['hello!', 'world?', 'test@123']
})

# Remove punctuation
df['text'].str.replace(r'[^\w\s]', '', regex=True)
# 0       hello
# 1       world
# 2    test123

# Keep only letters
df['text'].str.replace(r'[^a-zA-Z]', '', regex=True)
# 0    hello
# 1    world
# 2     test

# Keep only digits
df['text'].str.replace(r'\D', '', regex=True)
# 0       
# 1       
# 2    123
```

### Normalize Text

```python title="Standardize text format"
df = pd.DataFrame({
    'name': ['  ALICE  ', 'bob', 'Charlie  ']
})

# Clean and standardize
df['name_clean'] = (df['name']
    .str.strip()      # Remove whitespace
    .str.lower()      # Lowercase
    .str.title()      # Title case
)
#        name name_clean
# 0    ALICE      Alice
# 1      bob        Bob
# 2  Charlie    Charlie
```

### Remove Extra Spaces

```python title="Remove multiple spaces"
df = pd.DataFrame({
    'text': ['hello  world', 'test   data', 'a    b    c']
})

# Replace multiple spaces with single space
df['text'].str.replace(r'\s+', ' ', regex=True)
# 0    hello world
# 1      test data
# 2        a b c
```

## Padding and Alignment

### Pad Strings

```python title="Add padding to strings"
df = pd.DataFrame({
    'code': ['1', '42', '999']
})

# Pad with zeros (left)
df['code'].str.zfill(5)
# 0    00001
# 1    00042
# 2    00999

# Pad left with any character
df['code'].str.pad(5, side='left', fillchar='0')
# 0    00001
# 1    00042
# 2    00999

# Pad right
df['code'].str.pad(5, side='right', fillchar='X')
# 0    1XXXX
# 1    42XXX
# 2    999XX

# Center
df['code'].str.center(5, fillchar='-')
# 0    --1--
# 1    -42--
# 2    -999-
```

## Working with Dates in Strings

### Parse Date Components

```python title="Extract date parts from strings"
df = pd.DataFrame({
    'date_str': ['2024-01-15', '2024-02-20', '2024-03-10']
})

# Extract year, month, day
df['year'] = df['date_str'].str[:4]
df['month'] = df['date_str'].str[5:7]
df['day'] = df['date_str'].str[8:10]

# Or split
df[['year', 'month', 'day']] = df['date_str'].str.split('-', expand=True)
#     date_str  year month day
# 0  2024-01-15  2024    01  15
# 1  2024-02-20  2024    02  20
# 2  2024-03-10  2024    03  10

# Better: convert to datetime
df['date'] = pd.to_datetime(df['date_str'])
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
```

## Handling Missing Values

### String Operations with NaN

```python title="Handle NaN in string operations"
import numpy as np

df = pd.DataFrame({
    'text': ['hello', None, 'world', np.nan]
})

# String methods skip NaN by default
df['text'].str.upper()
# 0    HELLO
# 1     None
# 2    WORLD
# 3      NaN

# Fill NaN before operations
df['text'].fillna('').str.upper()
# 0    HELLO
# 1         
# 2    WORLD
# 3         

# Check for NaN-safe operations
df['text'].str.contains('hello', na=False)
# 0     True
# 1    False
# 2    False
# 3    False
```

## Common Cleaning Patterns

### Email Cleaning

```python title="Standardize email addresses"
df = pd.DataFrame({
    'email': ['  ALICE@Gmail.COM  ', 'bob@YAHOO.com', 'Charlie@Test.Com']
})

df['email_clean'] = (df['email']
    .str.strip()           # Remove whitespace
    .str.lower()           # Lowercase
)
#                 email         email_clean
# 0   ALICE@Gmail.COM    alice@gmail.com
# 1     bob@YAHOO.com     bob@yahoo.com
# 2  Charlie@Test.Com  charlie@test.com
```

### Phone Number Cleaning

```python title="Standardize phone numbers"
df = pd.DataFrame({
    'phone': ['(123) 456-7890', '555.123.4567', '999-888-7777']
})

# Remove all non-digits
df['phone_clean'] = df['phone'].str.replace(r'\D', '', regex=True)
#             phone phone_clean
# 0  (123) 456-7890  1234567890
# 1   555.123.4567  5551234567
# 2   999-888-7777  9998887777

# Format consistently
df['phone_formatted'] = df['phone_clean'].str.replace(
    r'(\d{3})(\d{3})(\d{4})',
    r'\1-\2-\3',
    regex=True
)
#             phone phone_clean phone_formatted
# 0  (123) 456-7890  1234567890   123-456-7890
# 1   555.123.4567  5551234567   555-123-4567
# 2   999-888-7777  9998887777   999-888-7777
```

### Name Cleaning

```python title="Clean and standardize names"
df = pd.DataFrame({
    'name': ['  alice smith  ', 'BOB JONES', 'charlie-brown']
})

df['name_clean'] = (df['name']
    .str.strip()                          # Remove whitespace
    .str.replace('-', ' ')                # Replace hyphens
    .str.replace(r'\s+', ' ', regex=True) # Remove extra spaces
    .str.title()                          # Title case
)
#               name      name_clean
# 0    alice smith     Alice Smith
# 1       BOB JONES       Bob Jones
# 2  charlie-brown  Charlie Brown
```

### URL/Domain Extraction

```python title="Extract domain from URLs"
df = pd.DataFrame({
    'url': ['https://www.example.com/page', 'http://test.org', 'www.site.com']
})

# Extract domain
df['domain'] = (df['url']
    .str.replace(r'https?://', '', regex=True)  # Remove protocol
    .str.replace('www.', '')                     # Remove www
    .str.split('/').str[0]                       # Get domain only
)
#                           url      domain
# 0  https://www.example.com/page  example.com
# 1             http://test.org     test.org
# 2                www.site.com     site.com
```

## Performance Tips

### Vectorized Operations

```python title="Efficient string operations"
# Slow: iterating
result = []
for val in df['text']:
    result.append(val.upper() if val else '')
df['upper'] = result

# Fast: vectorized
df['upper'] = df['text'].str.upper()

# Chain operations efficiently
df['clean'] = (df['text']
    .str.strip()
    .str.lower()
    .str.replace(r'\s+', ' ', regex=True)
)
```

## Quick Reference

**Case conversion:**

```python
df['col'].str.lower()              # Lowercase
df['col'].str.upper()              # Uppercase
df['col'].str.title()              # Title case
df['col'].str.capitalize()         # Capitalize first
```

**Whitespace:**

```python
df['col'].str.strip()              # Remove both sides
df['col'].str.lstrip()             # Remove left
df['col'].str.rstrip()             # Remove right
```

**Find/replace:**

```python
df['col'].str.contains('text')     # Check contains
df['col'].str.startswith('text')   # Check starts
df['col'].str.endswith('text')     # Check ends
df['col'].str.replace('old', 'new') # Replace
```

**Split/join:**

```python
df['col'].str.split()              # Split to list
df['col'].str.split(expand=True)   # Split to columns
df['col1'].str.cat(df['col2'], sep=' ') # Join
```

**Extract:**

```python
df['col'].str[:3]                  # First 3 chars
df['col'].str[-3:]                 # Last 3 chars
df['col'].str.extract(r'(\d+)')    # Extract pattern
```

**Clean:**

```python
df['col'].str.replace(r'[^\w\s]', '', regex=True)  # Remove special chars
df['col'].str.replace(r'\s+', ' ', regex=True)     # Remove extra spaces
df['col'].str.zfill(5)                             # Pad with zeros
```

**Common pattern:**

```python
# Clean text column
df['col_clean'] = (df['col']
    .str.strip()                       # Remove whitespace
    .str.lower()                       # Lowercase
    .str.replace(r'\s+', ' ', regex=True)  # Remove extra spaces
)
```
