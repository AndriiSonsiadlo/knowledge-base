---
id: signedness
title: Signed and Unsigned Types
sidebar_label: Signedness
sidebar_position: 3
tags: [c++, signed, unsigned, types, overflow]
---

# Signed and Unsigned Types

Integer types can be signed (negative and positive) or unsigned (only positive). Understanding signedness prevents bugs and overflow issues.

## Signed Types (Default)

```cpp showLineNumbers 
int x = -42;        // Signed by default
signed int y = -42; // Explicitly signed (same)

short s = -100;
long l = -1000;
```

**Range** (n bits): -2^(n-1) to 2^(n-1)-1

## Unsigned Types

```cpp showLineNumbers 
unsigned int count = 42;
unsigned char byte = 255;
unsigned long size = 1000000;

// Shorter form
unsigned x = 42;  // unsigned int
```

**Range** (n bits): 0 to 2^n-1

---

## char is Special

```cpp showLineNumbers 
char c;           // Implementation-defined: signed or unsigned
signed char sc;   // Guaranteed signed (-128 to 127)
unsigned char uc; // Guaranteed unsigned (0 to 255)

// For character data: use char
// For small integers: use signed/unsigned char
```

---

## Mixing Signed and Unsigned

```cpp showLineNumbers 
int x = -1;
unsigned int y = 1;

if (x < y) {  // ⚠️ Danger! x converts to large unsigned
    // This doesn't execute! -1 becomes 4294967295
}

// x (signed) converted to unsigned before comparison
// -1 → 4294967295 (wraps around)
```

**Rule**: When mixing, signed converts to unsigned.

---

## Overflow Behavior

### Signed Overflow (Undefined)

```cpp showLineNumbers 
int x = INT_MAX;  // 2147483647
x++;  // ❌ Undefined behavior!
```

### Unsigned Overflow (Well-Defined)

```cpp showLineNumbers 
unsigned int x = UINT_MAX;  // 4294967295
x++;  // ✅ Wraps to 0 (modulo arithmetic)

unsigned int y = 0;
y--;  // Wraps to UINT_MAX
```

Unsigned wraps around: 0 - 1 = 2^32 - 1

---

## Common Pitfalls

### Negative Loop

```cpp showLineNumbers 
// ❌ Infinite loop!
for (unsigned int i = 10; i >= 0; i--) {
    // i never < 0 (unsigned!)
}

// ✅ Fix: use signed
for (int i = 10; i >= 0; i--) {
    // Works correctly
}
```

### Subtraction

```cpp showLineNumbers 
unsigned int a = 5;
unsigned int b = 10;

unsigned int diff = a - b;  // ⚠️ Wraps! diff = huge number
int diff = a - b;           // Still wrong: computes unsigned then converts

// ✅ Fix: cast before subtraction
int diff = static_cast<int>(a) - static_cast<int>(b);  // -5
```

---

## When to Use Each

**Signed** (default choice):
- General integers
- Can be negative
- Math operations

**Unsigned**:
- Bit manipulation
- Sizes, counts (when > 0 guaranteed)
- Interfacing with C APIs
- Wrap-around behavior desired

```cpp showLineNumbers 
// Typical usage
int temperature = -5;           // Can be negative
unsigned int flags = 0xFF00;    // Bit flags
size_t size = vec.size();       // Size (unsigned)
```

---

## Summary

- **Signed**: Can be negative, overflow is UB
- **Unsigned**: 0+, overflow wraps (modulo)
- **Mixing**: Signed converts to unsigned
- **Default**: Use signed unless specific reason

```cpp showLineNumbers 
// Generally prefer
int x = 10;  // Signed by default

// Use unsigned for
unsigned int flags = 0;     // Bit operations
size_t size = data.size();  // Sizes/counts
```