---
id: boost-phoenix
title: Boost.Phoenix
sidebar_label: Boost.Phoenix
sidebar_position: 3
tags: [c++, boost, phoenix, lambda, functional]
---

# Boost.Phoenix

Boost.Phoenix is a **functional-programming toolkit** for C++ that lets you build function objects
inline using expression templates. Before C++11 lambdas existed, Phoenix provided the closest thing
the language had to anonymous functions — lazy expressions composed from placeholders, operators, and
higher-order combinators. Today it remains relevant as the expression layer behind
[Boost.Spirit](../05-strings-and-text/boost-spirit.md) semantic actions.

:::info The problem it solves
Pre-C++11 C++ had no lambdas. Writing a one-off functor for `std::for_each` or a Spirit semantic
action meant declaring a whole class. Phoenix lets you write `_1 * _1 + 1` directly in the
algorithm call, producing a function object at compile time through expression templates.
:::

## Lazy expressions with placeholders

Phoenix placeholders (`arg1`, `arg2`, ...) build callable expression trees that are evaluated later,
when the resulting function object is invoked.

```cpp showLineNumbers title="phoenix_basics.cpp"
#include <boost/phoenix.hpp>
#include <algorithm>
#include <vector>
#include <iostream>

int main() {
    using namespace boost::phoenix;
    using namespace boost::phoenix::placeholders;

    std::vector<int> v{1, 2, 3, 4, 5};

    // Square each element — _1 * _1 builds a lazy function object
    std::vector<int> result;
    std::transform(v.begin(), v.end(), std::back_inserter(result),
                   arg1 * arg1);

    for (int x : result) std::cout << x << " ";
    // 1 4 9 16 25
}
```

## Lazy values and references

`val()` wraps a constant into a lazy expression; `ref()` wraps a reference so that the expression
can read or mutate external state.

```cpp showLineNumbers title="phoenix_val_ref.cpp"
#include <boost/phoenix.hpp>
#include <algorithm>
#include <vector>
#include <iostream>

int main() {
    using namespace boost::phoenix;
    using namespace boost::phoenix::placeholders;

    std::vector<int> v{1, 2, 3, 4, 5};

    int total = 0;
    std::for_each(v.begin(), v.end(), ref(total) += arg1);
    std::cout << "sum = " << total << "\n";   // 15
}
```

## Control-flow expressions

Phoenix provides lazy versions of `if_else_`, `while_`, `for_`, and `switch_` for building complex
inline expressions.

```cpp showLineNumbers title="phoenix_control.cpp"
#include <boost/phoenix.hpp>
#include <algorithm>
#include <vector>
#include <iostream>

int main() {
    using namespace boost::phoenix;
    using namespace boost::phoenix::placeholders;

    std::vector<int> v{-2, 5, -1, 3, 0};

    // Clamp negatives to zero
    std::transform(v.begin(), v.end(), v.begin(),
                   if_else_(arg1 < val(0), val(0), arg1));

    for (int x : v) std::cout << x << " ";
    // 0 5 0 3 0
}
```

## Phoenix with Boost.Spirit

Phoenix's main modern use case is as the semantic-action engine for Spirit parsers. Spirit rules
produce attributes; Phoenix expressions transform them inline.

```cpp showLineNumbers title="phoenix_spirit.cpp"
#include <boost/spirit/include/qi.hpp>
#include <boost/phoenix.hpp>
#include <iostream>
#include <string>

int main() {
    namespace qi = boost::spirit::qi;
    using boost::phoenix::ref;

    std::string input = "42";
    int result = 0;

    qi::parse(input.begin(), input.end(),
              qi::int_[ref(result) = qi::_1]);

    std::cout << result << "\n";   // 42
}
```

:::tip When Phoenix still matters
If you use Boost.Spirit, you will encounter Phoenix — it is the standard way to write semantic
actions. Outside of Spirit, C++11 lambdas are almost always a better choice.
:::

## Phoenix versus lambdas

| Feature | Boost.Phoenix | C++ Lambdas |
|---------|---------------|-------------|
| Available | pre-C++11 | C++11+ |
| Syntax | expression templates (`arg1 * arg1`) | `[](auto x) { return x * x; }` |
| Composability | very high (expression trees) | moderate (nesting) |
| Debuggability | poor (deep template errors) | good |
| Spirit integration | native | works but more verbose |
| Learning curve | steep | low |

:::note Legacy status
Phoenix was essential before C++11. In modern C++ it is a niche tool — reach for it when working
with Spirit, and prefer lambdas everywhere else.
:::

## See also

- <Icon icon="lucide:link" inline /> [Boost.Bind](./boost-bind.md) — simpler partial application, also superseded by lambdas.
- <Icon icon="lucide:link" inline /> [Boost.Function](./boost-function.md) — polymorphic wrapper for the callables Phoenix produces.
- <Icon icon="lucide:type" inline /> [Boost.Spirit](../05-strings-and-text/boost-spirit.md) — the parser framework that uses Phoenix for semantic actions.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
