---
id: if-switch
title: Conditional Statements (if, switch)
sidebar_label: if & switch
sidebar_position: 1
tags: [c++, control-flow, conditionals]
---

# Conditional Statements (`if`, `switch`)

A conditional statement runs one piece of code or another depending on a value. C++ has two:
`if` tests any condition, and `switch` jumps to one of several labelled cases for a single integer
or enum value. Beyond the basic forms, modern C++ adds **init-statements** *(C++17)*, which scope a
variable to the conditional, and **`if constexpr`** *(C++17)*, which chooses a branch at compile
time.

**Prerequisites:** [Expressions and Statements](../expressions-and-statements.md),
[Logical Operators](../operators/logical.md).

## `if` / `else`

```cpp
if (score >= 90) {
    grade = 'A';
} else if (score >= 80) {   // tested only when the first condition was false
    grade = 'B';
} else {
    grade = 'C';            // none matched
}
```

The condition is converted to `bool` (zero and null pointers are false). There is no special
`else if` keyword: it is an `else` whose body is another `if`.

**Brace every branch**, even one-liners. Without braces only the next statement belongs to the
`if`, so a line added later runs unconditionally. A duplicated unbraced `goto fail;` line caused
Apple's 2014 TLS certificate-check bug. `-Wall` includes `-Wmisleading-indentation`, which catches
some of these.

### Init-statement *(C++17)*

`if (init; condition)` declares a variable visible in the condition and in **both** branches, but
not after the statement. Short-lived results (a lookup, an error code, a lock) then cannot leak into
the surrounding code:

```cpp
if (auto it = cache.find(key); it != cache.end()) {
    use(it->second);         // it is visible here...
} else {
    cache.emplace(key, compute(key));   // ...and here
}
// it is out of scope here
```

### `if constexpr` *(C++17)*

With `if constexpr` the condition must be a compile-time constant, and inside a template the branch
not taken is **discarded**: it is not instantiated, so it may contain code that would not compile
for this type.

```cpp title="describe.cpp" showLineNumbers
#include <iostream>
#include <string>
#include <type_traits>

template <class T>
std::string describe(const T& v) {
    if constexpr (std::is_arithmetic_v<T>)
        return "number " + std::to_string(v);   // std::to_string(std::string) would not compile
    else
        return "text " + std::string(v);
}

int main() { std::cout << describe(42) << ", " << describe("hi") << '\n'; }   // number 42, text hi
```

With a plain `if`, both branches would be compiled for every `T` and `describe("hi")` would fail.
Templates are introduced in [Function Templates](../../08-templates-and-metaprogramming/function-templates.md).

## `switch`

`switch` evaluates one value of integer, character or enum type and **jumps** to the matching
`case` label. The labels must be constant expressions with distinct values. If nothing matches,
control goes to `default`, or skips the whole `switch` if there is no `default`.

```cpp
switch (op) {
    case '+':
    case '-':                 // two labels, one body
        additive(op);
        break;                // leave the switch
    case '*':
        multiply();
        break;
    default:                  // everything else
        unknown(op);
}
```

### Fall-through

A `case` label is only a jump target, not a boundary. After the matching case's statements run,
execution **continues into the next case** until it reaches `break` (or `return`, or the end of the
`switch`). This is called fall-through.

<Walkthrough title="switch (n) with n == 1, missing one break" caption="case 1 forgot its break; case 2 has one." accent="amber">
  <Step title="Jump to the matching label">

```cpp
switch (n) {
    // highlight-next-line
    case 1: std::cout << "one ";
    case 2: std::cout << "two ";  break;
    case 3: std::cout << "three ";
}
```

`n == 1`, so control jumps straight to `case 1:`. Output: <StepChange>`one `</StepChange>

  </Step>
  <Step title="No break: fall into case 2">

```cpp
switch (n) {
    case 1: std::cout << "one ";
    // highlight-next-line
    case 2: std::cout << "two ";  break;
    case 3: std::cout << "three ";
}
```

Labels do not stop execution, so the next line runs too. Output: `one `<StepChange>`two `</StepChange>

  </Step>
  <Step title="break leaves the switch">

`break` jumps past the closing brace. `case 3` never runs. Final output: `one two `.
With `n == 2` you would get `two `; with `n == 3`, `three `; with `n == 7`, nothing.

  </Step>
</Walkthrough>

Fall-through is occasionally what you want. Mark it with `[[fallthrough]];` *(C++17)*. It documents
the intent, and silences `-Wimplicit-fallthrough` (enabled by `-Wextra` in GCC), which otherwise
warns about the missing `break`:

```cpp
case Level::Verbose:
    log_details();
    [[fallthrough]];          // deliberately continue into Normal
case Level::Normal:
    log_summary();
    break;
```

### Variables inside cases

All cases share one scope, and jumping past an initialised variable into its scope is an error.
Give a case its own block when it declares something:

```cpp
switch (kind) {
    case 0: {
        std::string name = read_name();   // scoped to this block
        greet(name);
        break;
    }
    case 1:                               // without the braces above: "jump to case label
        bye();                            // crosses initialization of name"
        break;
}
```

### Enums and exhaustiveness

When you switch over an enum and list every enumerator **without** a `default`, `-Wall`
(`-Wswitch`) warns if someone later adds an enumerator you did not handle. A `default` would hide
that. `switch` also accepts a C++17 init-statement:

```cpp
enum class State { Idle, Active, Faulted };

switch (auto s = device.poll(); s) {
    case State::Idle:    spin();  break;
    case State::Active:  work();  break;
    case State::Faulted: reset(); break;
}
```

## Choosing between them

<Diagram title="if or switch?" accent="green">
  <DiagramNode variant="pill">What are you testing?</DiagramNode>
  <DiagramRow>
    <DiagramNode title="One integer, char or enum value against fixed constants" accent>`switch`: each case is visible at a glance, enum coverage is checked</DiagramNode>
    <DiagramNode title="Ranges, several variables, strings, or any other predicate">`if` / `else if`: `switch` cannot test `x > 10` or a `std::string`</DiagramNode>
  </DiagramRow>
</Diagram>

Choose for readability, not speed. Compilers can turn a dense `switch` into a jump table, but they
also optimise `if` chains, and either may become the other.

## Key points

- Brace every branch.
- Use `if (init; cond)` to keep helper variables out of the surrounding scope.
- `if constexpr` discards the untaken branch in templates.
- `switch` cases fall through until `break`; mark intentional fall-through with `[[fallthrough]]`.
- Give a case braces if it declares a variable; omit `default` on enum switches to keep `-Wswitch`.

## Related

- [Loops](./loops.md) — the other half of control flow
- [goto and Labels](./goto-and-labels.md) — the jump rules `switch` shares
- [Logical Operators](../operators/logical.md) — combining conditions
