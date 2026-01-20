---
id: expressions-and-statements
title: Expressions and Statements
sidebar_label: Expressions
sidebar_position: 4
tags: [c++, expressions, statements, syntax, fundamentals]
---

# Expressions and Statements

Expressions produce values; statements perform actions. Understanding the distinction is fundamental to C++ programming.

:::info Key Difference
**Expression**: Evaluates to a value (`5 + 3`, `x > 0`)  
**Statement**: Complete instruction that executes (`int x = 5;`, `return 0;`)
:::

## Expressions

An expression is any code that produces a value and can be evaluated.

```cpp showLineNumbers 
// Simple expressions
42                  // Literal (value: 42)
x                   // Variable (value: contents of x)
x + 5               // Arithmetic (value: sum)
x > 10              // Comparison (value: true/false)
func()              // Function call (value: return value)

// Complex expressions
(x + y) * (z - 3)   // Nested expressions
x = y = 5           // Assignment chain (value: 5)
++x                 // Pre-increment (value: new x)
x++                 // Post-increment (value: old x)
```

Every expression has:
- **Type**: `int`, `double`, `bool`, etc.
- **Value**: Result of evaluation
- **Value category**: lvalue, rvalue, etc.

---

## Statements

A statement is a complete instruction that performs an action. Most statements end with `;`.

### Types of Statements

```cpp showLineNumbers 
// Expression statement (expression + semicolon)
x = 5;              // Assignment statement
func();             // Function call statement
x + 3;              // Valid but useless (value discarded)

// Declaration statement
int x;              // Variable declaration
int y = 10;         // Declaration with initialization

// Compound statement (block)
{
    int x = 5;
    std::cout << x;
}

// Control flow statements
if (x > 0) { }      // If statement
while (x > 0) { }   // While loop
for (;;) { }        // For loop
return 0;           // Return statement
break;              // Break statement
```

---

## Expression vs Statement Examples

```cpp showLineNumbers 
// Expression: produces value, no semicolon needed
int x = 5 + 3;      // '5 + 3' is expression
        ^^^^

// Statement: complete instruction with semicolon
int x = 5 + 3;      // Entire line is statement
^^^^^^^^^^^^^

// Expression used as statement
x + 3;              // Expression becomes statement (value discarded)

// Multiple expressions in one statement
x = (y = 5) + 3;    // y = 5 is expression (value: 5)
                    // (y = 5) + 3 is expression (value: 8)
                    // Entire line is statement
```

---

## Expression Categories

### Primary Expressions

The building blocks of all expressions:

```cpp showLineNumbers 
// Literals
42                  // Integer literal
3.14                // Floating-point literal
"hello"             // String literal
'A'                 // Character literal
true                // Boolean literal
nullptr             // Null pointer literal

// Identifiers
x                   // Variable
func                // Function

// this pointer (in member functions)
this->member        // Access to class member

// Lambda expression (C++11)
[](int x) { return x * 2; }
```

### Postfix Expressions

```cpp showLineNumbers 
arr[5]              // Array subscript
obj.member          // Member access
ptr->member         // Pointer member access
func(arg1, arg2)    // Function call
x++                 // Post-increment (returns old value)
x--                 // Post-decrement
type(value)         // Functional cast
```

### Unary Expressions

```cpp showLineNumbers 
++x                 // Pre-increment (returns new value)
--x                 // Pre-decrement
+x                  // Unary plus
-x                  // Unary minus (negation)
!x                  // Logical NOT
~x                  // Bitwise NOT
*ptr                // Dereference
&var                // Address-of
sizeof(x)           // Size in bytes
(type)x             // C-style cast
new int             // Dynamic allocation
delete ptr          // Deallocation
```

### Binary Expressions

```cpp showLineNumbers 
// Arithmetic
x + y               // Addition
x - y               // Subtraction
x * y               // Multiplication
x / y               // Division
x % y               // Modulus

// Comparison
x == y              // Equal
x != y              // Not equal
x < y               // Less than
x > y               // Greater than
x <= y              // Less or equal
x >= y              // Greater or equal

// Logical
x && y              // AND
x || y              // OR

// Bitwise
x & y               // Bitwise AND
x | y               // Bitwise OR
x ^ y               // Bitwise XOR
x << 2              // Left shift
x >> 2              // Right shift

// Assignment
x = y               // Assign
x += y              // x = x + y
x -= y              // x = x - y
x *= y              // x = x * y
```

### Ternary Expression

Only one ternary operator in C++:

```cpp showLineNumbers 
condition ? value_if_true : value_if_false

// Examples
int max = (x > y) ? x : y;
std::string msg = (count > 0) ? "Items found" : "No items";

// Can be nested (avoid for readability)
int sign = (x > 0) ? 1 : (x < 0) ? -1 : 0;
```

---

## Operator Precedence

Determines evaluation order when multiple operators present:

```cpp showLineNumbers 
// High to low precedence (simplified)
x++  x--                    // Postfix
++x  --x  !  ~  *  &        // Unary
*  /  %                     // Multiplicative
+  -                        // Additive
<<  >>                      // Shift
<  <=  >  >=                // Relational
==  !=                      // Equality
&                           // Bitwise AND
^                           // Bitwise XOR
|                           // Bitwise OR
&&                          // Logical AND
||                          // Logical OR
? :                         // Conditional
=  +=  -=  *=  /=           // Assignment
,                           // Comma (lowest)

// Examples
int result = 5 + 3 * 2;     // 11 (not 16): * before +
bool b = x > 5 && y < 10;   // Relational before logical
int x = y = 5;              // 5 (right-to-left)
```

Use parentheses for clarity:

```cpp showLineNumbers 
// Unclear
int result = x + y * z;

// Clear
int result = x + (y * z);   // Explicit intent
```

---

## Statement Types

### Null Statement

Empty statement (just semicolon):

```cpp showLineNumbers 
;                   // Null statement

// Used in loops with no body
while (getchar() != '\n')
    ;               // Empty body

// For loop with work in condition
for (int i = 0; i < n; ++i, sum += i)
    ;               // All work in for header
```

### Compound Statement (Block)

Groups multiple statements:

```cpp showLineNumbers 
{
    int x = 5;      // Local to block
    int y = 10;
    std::cout << x + y;
}                   // x and y destroyed here

// Creates scope
int x = 1;
{
    int x = 2;      // Different variable
    std::cout << x; // 2
}
std::cout << x;     // 1
```

### Declaration Statement

```cpp showLineNumbers 
int x;                      // Declaration
int y = 5;                  // Declaration with initialization
const double PI = 3.14;     // Constant declaration
auto value = compute();     // Type deduction

// Multiple declarations
int a, b, c;
int *ptr, arr[10];          // Pointer and array
```

### Selection Statements

```cpp showLineNumbers 
// If statement
if (x > 0) {
    std::cout << "Positive";
} else if (x < 0) {
    std::cout << "Negative";
} else {
    std::cout << "Zero";
}

// Switch statement
switch (value) {
    case 1:
        doOne();
        break;
    case 2:
        doTwo();
        break;
    default:
        doDefault();
}

// If with initializer (C++17)
if (auto result = compute(); result > 0) {
    use(result);
}
```

### Iteration Statements

```cpp showLineNumbers 
// While loop
while (condition) {
    // Body
}

// Do-while loop
do {
    // Body executes at least once
} while (condition);

// For loop
for (int i = 0; i < n; i++) {
    // Body
}

// Range-based for (C++11)
for (auto& elem : container) {
    // Process elem
}
```

### Jump Statements

```cpp showLineNumbers 
// Break: exit loop/switch
while (true) {
    if (done) break;
}

// Continue: skip to next iteration
for (int i = 0; i < n; i++) {
    if (skip_condition) continue;
    process(i);
}

// Return: exit function
int func() {
    return 42;
}

// Goto: jump to label (avoid!)
goto error_handler;
error_handler:
    cleanup();
```

---

## Expression Evaluation

### Order of Evaluation

```cpp showLineNumbers 
// Undefined order in most cases
int result = f() + g() + h();  // f, g, h can be called in any order

// Guaranteed left-to-right (C++17)
a.b              // a before b
a->b             // a before b
a[b]             // a before b
a << b           // a before b (streams)
a >> b           // a before b (streams)

// Short-circuit evaluation
x && y           // If x is false, y not evaluated
x || y           // If x is true, y not evaluated
```

### Sequence Points

Points where all previous evaluations complete:

```cpp showLineNumbers 
// Semicolon is sequence point
x = 1;
y = x + 1;       // x=1 completes before this

// Comma operator
x = (a = 1, b = 2, a + b);  // a=1, then b=2, then add

// Undefined behavior
i = i++;         // ❌ UB: modifies i twice
arr[i] = i++;    // ❌ UB: which i for index?

// Well-defined
i = 1;
arr[i++] = 5;    // OK: i evaluated before increment
```

---

## Common Pitfalls

### Assignment in Condition

```cpp showLineNumbers 
// ❌ Common mistake
if (x = 5) {     // Assignment, not comparison!
    // Always executes (5 is true)
}

// ✅ Intended comparison
if (x == 5) {
    // Executes when x equals 5
}

// ✅ Intentional assignment (rare)
if ((x = getValue()) != 0) {
    // Use x
}
```

### Expression as Statement

```cpp showLineNumbers 
x + 5;           // ⚠️ Legal but useless (value discarded)
x == 5;          // ⚠️ Legal but useless (comparison unused)

x = 5;           // ✅ Useful statement
```

---

## Summary

**Expressions**:
- Produce values
- Have types
- Can be nested
- `5 + 3`, `x > 0`, `func()`

**Statements**:
- Perform actions
- Usually end with `;`
- Control program flow
- `int x = 5;`, `if (x > 0) { }`

**Key points**:
- Expressions become statements by adding `;`
- Statements control execution flow
- Operator precedence determines evaluation order
- Short-circuit evaluation for `&&` and `||`

```cpp showLineNumbers 
// Expression
x + y

// Statement
x + y;

// Statement with expression
int result = x + y;
              ^^^^^ expression
^^^^^^^^^^^^^^^^^^ statement
```