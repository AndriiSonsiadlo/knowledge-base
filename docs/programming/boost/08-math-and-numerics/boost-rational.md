---
id: boost-rational
title: Boost.Rational
sidebar_label: Boost.Rational
sidebar_position: 4
tags: [c++, boost, rational, fraction, exact-arithmetic]
---

# Boost.Rational

`boost::rational<T>` represents an **exact fraction** as a numerator/denominator pair. Every
operation automatically reduces the result to lowest terms using the GCD, so `6/4` becomes `3/2`
without any manual simplification. It gives you exact arithmetic where floating-point
representation error is unacceptable — financial calculations, symbolic computation, or any domain
where `0.1 + 0.2 != 0.3` is a problem.

:::info The problem it solves
Floating-point arithmetic introduces rounding at every step. When you need results that are *exactly*
correct — not approximately correct — you need a different representation. Rational numbers
(fractions of integers) are closed under addition, subtraction, multiplication, and division, and
Boost.Rational keeps them in canonical form automatically.
:::

## Basic usage

```cpp showLineNumbers title="rational_basics.cpp"
#include <boost/rational.hpp>
#include <iostream>

int main() {
    boost::rational<int> a(1, 3);   // 1/3
    boost::rational<int> b(1, 6);   // 1/6

    auto sum = a + b;               // 1/3 + 1/6 = 1/2 (auto-reduced)
    std::cout << sum << "\n";       // prints "1/2"

    auto product = a * b;           // 1/3 * 1/6 = 1/18
    std::cout << product << "\n";   // prints "1/18"

    // Comparison is exact
    boost::rational<int> half(1, 2);
    std::cout << std::boolalpha << (sum == half) << "\n";  // true
}
```

The denominator is always kept positive — `rational<int>(-3, 4)` and `rational<int>(3, -4)` both
normalise to `-3/4`.

## Arithmetic operations

All standard arithmetic operators work as expected. Division by a rational that is zero throws
`boost::bad_rational`.

```cpp showLineNumbers title="arithmetic.cpp"
#include <boost/rational.hpp>
#include <iostream>

int main() {
    using Q = boost::rational<long>;

    Q a(7, 3), b(2, 5);

    std::cout << "a + b = " << (a + b) << "\n";   // 41/15
    std::cout << "a - b = " << (a - b) << "\n";   // 29/15
    std::cout << "a * b = " << (a * b) << "\n";   // 14/15
    std::cout << "a / b = " << (a / b) << "\n";   // 35/6

    // Increment, compound assignment
    Q c(1, 2);
    c += Q(1, 3);
    std::cout << "1/2 + 1/3 = " << c << "\n";     // 5/6
}
```

:::danger Overflow with small integer types
`rational<int>` can overflow if the numerator or denominator grows beyond `INT_MAX` during
intermediate computations. For calculations involving large values, use `rational<long long>` or
combine with [Boost.Multiprecision](./boost-multiprecision.md)'s `cpp_int` for unbounded precision:
`boost::rational<boost::multiprecision::cpp_int>`.
:::

## Accessing components

```cpp showLineNumbers title="components.cpp"
#include <boost/rational.hpp>
#include <iostream>

int main() {
    boost::rational<int> r(22, 7);

    std::cout << "numerator:   " << r.numerator()   << "\n";  // 22
    std::cout << "denominator: " << r.denominator() << "\n";  // 7

    // Assign new value
    r.assign(355, 113);
    std::cout << "355/113 = " << r << "\n";  // already in lowest terms
}
```

## Conversion to and from floating point

```cpp showLineNumbers title="conversion.cpp"
#include <boost/rational.hpp>
#include <boost/rational/rational_io.hpp>
#include <iostream>

int main() {
    boost::rational<int> r(1, 3);

    // To floating point: exact division
    double d = boost::rational_cast<double>(r);
    std::cout << "1/3 as double = " << d << "\n";   // 0.333333...

    // From integer: implicitly wraps as n/1
    boost::rational<int> whole(5);
    std::cout << whole << "\n";   // "5/1"
}
```

:::note No implicit conversion to float
`rational_cast<double>(r)` is explicit by design. Implicit conversion would silently discard the
exactness that is the whole point of using rationals.
:::

## Comparison and ordering

Rationals compare by cross-multiplication, so ordering is exact and consistent. They work as map
keys and in sorted containers.

```cpp showLineNumbers title="comparison.cpp"
#include <boost/rational.hpp>
#include <cassert>
#include <set>

int main() {
    using Q = boost::rational<int>;

    assert(Q(1, 3) < Q(1, 2));
    assert(Q(2, 4) == Q(1, 2));   // auto-reduced, so equal
    assert(Q(-1, 3) < Q(0));

    // Usable as a set key
    std::set<Q> s;
    s.insert(Q(1, 3));
    s.insert(Q(2, 6));   // same as 1/3, not inserted again
    assert(s.size() == 1);
}
```

## Practical example: exact accumulation

```cpp showLineNumbers title="exact_sum.cpp"
#include <boost/rational.hpp>
#include <iostream>

int main() {
    using Q = boost::rational<long long>;

    // Sum 1/1 + 1/2 + 1/3 + ... + 1/10 exactly
    Q sum(0);
    for (int i = 1; i <= 10; ++i)
        sum += Q(1, i);

    std::cout << "H(10) = " << sum << "\n";   // 7381/2520
    std::cout << "     ~ " << boost::rational_cast<double>(sum) << "\n";
}
```

## See also

- <Icon icon="lucide:calculator" inline /> [Boost.Multiprecision](./boost-multiprecision.md) — use `cpp_int` as the underlying integer type for overflow-free rationals.
- <Icon icon="lucide:arrow-right-left" inline /> [Numeric Conversion](./numeric-conversion.md) — safe conversions between built-in numeric types.
- <Icon icon="lucide:calculator" inline /> [Boost.Math](./boost-math.md) — numerical functions that accept floating-point types.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
