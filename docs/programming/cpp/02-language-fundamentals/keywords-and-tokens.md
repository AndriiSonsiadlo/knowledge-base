---
id: keywords-and-tokens
title: Keywords and Tokens
sidebar_label: Keywords & Tokens
sidebar_position: 3
tags: [c++, keywords, tokens, identifiers, literals]
---

# Keywords and Tokens

Before the compiler can understand `int count = 42;`, it splits the text into **tokens**: the
smallest meaningful pieces, here `int`, `count`, `=`, `42` and `;`. Every C++ program is a sequence
of tokens of five kinds. Knowing them explains which names you may use, what type a literal like
`42` or `"hi"` has, and why `x+++y` means what it does.

**Prerequisites:** [Basic Syntax](./basic-syntax.md). Where tokenisation sits in the build is
covered in [Preprocessing](../01-toolchain-and-build/preprocessing.md).

## The five kinds of token

<Diagram title="int count = 42;  as tokens" accent="violet">
  <DiagramRow>
    <DiagramNode title="Keyword">`int`: reserved word with fixed meaning</DiagramNode>
    <DiagramNode title="Identifier" accent>`count`: a name you choose</DiagramNode>
    <DiagramNode title="Operator">`=`: acts on operands</DiagramNode>
    <DiagramNode title="Literal">`42`: a value written in the source</DiagramNode>
    <DiagramNode title="Punctuator">`;`: structure (ends the statement)</DiagramNode>
  </DiagramRow>
</Diagram>

Whitespace and comments separate tokens but are not tokens themselves: early in translation, each
comment is replaced by a single space. So `int/*x*/a;` is `int a;`, but `in/**/t` is two tokens
`in` and `t`, not `int`.

### Longest match ("maximal munch")

The tokenizer always takes the **longest** sequence of characters that forms a valid token, without
looking at what makes sense afterwards:

```cpp
int z = x+++y;     // tokens: x ++ + y   → (x++) + y
int w = x+++++y;   // tokens: x ++ ++ + y → does not compile (x++ is not an lvalue)
```

Add spaces when operators touch. C++11 made one deliberate exception: in `std::vector<std::vector<int>>`
the closing `>>` is split into two `>` to end both template argument lists; in C++03 you had to
write `> >`.

## Keywords

Keywords are reserved: you cannot use them as names. Grouped by job (versions marked where a word
was added later):

| Purpose | Keywords |
|---|---|
| Fundamental types | `bool` `char` `char8_t`*(C++20)* `char16_t`*(C++11)* `char32_t`*(C++11)* `wchar_t` `short` `int` `long` `signed` `unsigned` `float` `double` `void` `auto` |
| Values | `true` `false` `nullptr`*(C++11)* `this` |
| Declarations and qualifiers | `const` `volatile` `static` `extern` `inline` `mutable` `thread_local`*(C++11)* `constexpr`*(C++11)* `consteval`*(C++20)* `constinit`*(C++20)* `typedef` `using` `namespace` `register` `export` `friend` `explicit` `virtual` |
| Classes and enums | `class` `struct` `union` `enum` `public` `protected` `private` `operator` |
| Control flow | `if` `else` `switch` `case` `default` `for` `while` `do` `break` `continue` `return` `goto` |
| Templates and concepts | `template` `typename` `concept`*(C++20)* `requires`*(C++20)* |
| Type queries and casts | `sizeof` `alignof`*(C++11)* `alignas`*(C++11)* `decltype`*(C++11)* `typeid` `static_cast` `dynamic_cast` `const_cast` `reinterpret_cast` |
| Memory | `new` `delete` |
| Errors and checks | `try` `catch` `throw` `noexcept`*(C++11)* `static_assert`*(C++11)* |
| Coroutines *(C++20)* | `co_await` `co_yield` `co_return` |
| Other | `asm` |

Notes on the odd ones:

- `register` lost its meaning in C++17 and `export` was unused from C++11 until modules reused it
  in C++20. Both stay reserved.
- `override`, `final`, `import` and `module` are **not** keywords. They are identifiers with special
  meaning only in specific positions, so `int final = 3;` compiles. This let C++11 and C++20 add
  them without breaking existing code that used those names.
- `and`, `or`, `not`, `bitand`, `bitor`, `xor`, `compl`, `and_eq`, `or_eq`, `xor_eq`, `not_eq` are
  **alternative tokens**: exact synonyms for `&&`, `||`, `!`, `&`, `|`, `^`, `~`, `&=`, `|=`, `^=`,
  `!=`. `if (a and not b)` is valid C++. They are rarely used.

The complete list, with every version's additions, is on
[cppreference: C++ keywords](https://en.cppreference.com/w/cpp/keyword).

## Identifiers

An identifier names a variable, function, type, namespace and so on.

- Allowed characters: letters, digits and `_`; it may not start with a digit.
- Case-sensitive: `value`, `Value` and `VALUE` are three names.
- It may not be a keyword.

```cpp
int count, _tmp, value2, snake_case, camelCase;   // valid
int 2nd;        // error: starts with a digit
int my-var;     // error: parsed as my - var
int class;      // error: keyword
```

**Reserved identifiers.** Some valid-looking names belong to the compiler and standard library;
using them is undefined behaviour, even if it usually compiles:

- any name containing a double underscore `__`, anywhere;
- any name starting with `_` followed by an uppercase letter (`_Value`);
- in the global namespace, any name starting with `_` (`_count` at file scope).

A trailing underscore (`size_`) and `m_` prefixes are safe, which is why both are common for member
variables.

## Literals

A literal writes a value directly in the source. Every literal has a type, decided by its spelling.

### Integer literals

| Spelling | Meaning |
|---|---|
| `42` | decimal |
| `0x2A` | hexadecimal |
| `052` | **octal**: a leading `0` means base 8, so `010 == 8` |
| `0b101010` | binary *(C++14)* |
| `1'000'000` | digit separators *(C++14)*, ignored by the compiler |
| `42u`, `42l`, `42ul`, `42ll`, `42ull` | suffixes: `unsigned`, `long`, `long long` |
| `42z`, `42uz` | `std::size_t`'s signed counterpart and `std::size_t` *(C++23)* |

Without a suffix, a decimal literal gets the first of `int`, `long`, `long long` that can hold it.
So `3000000000` is `long` on 64-bit Linux, where `int` is 32 bits. The leading-zero octal rule is a
real trap when padding numbers: `int code = 0755;` is 493.

### Floating-point literals

`3.14` is a `double`; `3.14f` is a `float`; `3.14L` is a `long double`. `1.5e-3` is
scientific notation (1.5 × 10⁻³). Hexadecimal floats *(C++17)* give exact binary values:
`0x1.2p3` is 1.125 × 2³ = 9.0.

### Character and string literals

```cpp
'A'        // char
u8'A'      // char8_t (C++20)
u'A'       // char16_t      U'A'  // char32_t      L'A'  // wchar_t
'\n' '\t' '\\' '\'' '\0' '\x41'   // escape sequences: newline, tab, backslash, quote, NUL, hex

"Hello"    // type const char[6]: five characters plus the terminating '\0'
u8"Hi"     // const char8_t[3] (C++20; was const char[] before)
"Hello, " "World"                 // adjacent literals are joined: "Hello, World"
R"(C:\path\no "escapes" needed)"  // raw string (C++11): backslashes and quotes taken literally
```

A string literal is an **array**, not a pointer, although it converts to `const char*` when passed
to a function. Writing to it is undefined behaviour. For a real string object use `std::string`
([Strings](../09-standard-library/strings.md)) or the `s` suffix below.

### `bool`, pointer and user-defined literals

`true` and `false` are the `bool` literals; `nullptr` *(C++11)* is the null pointer literal (prefer
it to `NULL` or `0`). Since C++11 types can define their own literal suffixes:

```cpp title="literals.cpp" showLineNumbers
#include <chrono>
#include <iostream>
#include <string>

constexpr long long operator""_km(unsigned long long x) { return x * 1000; }   // no space before _km

int main() {
    using namespace std::literals;
    auto name = "hi"s;     // std::string
    auto wait = 100ms;     // std::chrono::milliseconds
    std::cout << 5_km << ' ' << name.size() << ' ' << wait.count() << '\n';   // 5000 2 100
}
```

User-defined suffixes must start with `_`; those without are reserved for the standard library. The
older spelling with a space, `operator"" _km`, is deprecated since C++23.

## Operators and punctuators

The operators are listed in [Operator Precedence](./operators/operator-precedence.md) and explained
in the [Operators](./operators/arithmetic.md) pages. Punctuators give the program its shape: `;`
ends a statement, `{ }` delimit blocks and initialisers, `( )` group and call, `[ ]` subscript and
introduce lambdas, `,` separates, `:` and `::` appear in labels, base-class lists and qualified
names, `...` marks variadics, and `#` starts a preprocessor directive. Several symbols have more
than one job (`*` multiplies or dereferences, `&` is bitwise AND, address-of or a reference); the
surrounding grammar decides which.

## Key points

- Tokenisation takes the longest valid token: `x+++y` is `x++ + y`.
- `override`, `final`, `import`, `module` are not keywords; `and`/`or`/`not` are spellings of operators.
- Avoid `__` anywhere and a leading `_` + capital; prefer a trailing `_` for members.
- A leading `0` makes an integer literal octal.
- `"Hello"` is a `const char[6]`, not a `std::string`; use `"Hello"s` or `std::string`.

## Related

- [Basic Syntax](./basic-syntax.md) — how these tokens combine into a program
- [Fundamental Types](../03-types-and-values/fundamental-types.md) — the types that literals produce
- [Preprocessing](../01-toolchain-and-build/preprocessing.md) — the phase that runs on these tokens
