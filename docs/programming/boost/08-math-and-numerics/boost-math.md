---
id: boost-math
title: Boost.Math
sidebar_label: Boost.Math
sidebar_position: 1
tags: [c++, boost, math, special-functions, statistics]
---

# Boost.Math

`Boost.Math` is a comprehensive mathematics library that goes far beyond what `<cmath>` provides.
It ships **special functions** (gamma, beta, Bessel, error functions, elliptic integrals), a full
suite of **statistical distributions** with PDF/CDF/quantile support, **root-finding** algorithms,
and **numerical integration** (quadrature) — all as header-only, precision-aware templates.

:::info The problem it solves
The C++ standard library gives you `sin`, `cos`, `exp`, and a handful of others. Real numerical
work — hypothesis testing, signal processing, computational physics — needs functions like the
incomplete beta, Bessel functions of the first kind, or the quantile of a chi-squared distribution.
Boost.Math fills that gap with tested, portable implementations that work with any floating-point
type, including arbitrary-precision types from [Boost.Multiprecision](./boost-multiprecision.md).
:::

## Special functions

Boost.Math provides over 100 special mathematical functions. They live in `<boost/math/special_functions/*.hpp>`
or in the convenience header `<boost/math/special_functions.hpp>`.

```cpp showLineNumbers title="special_functions.cpp"
#include <boost/math/special_functions/gamma.hpp>
#include <boost/math/special_functions/bessel.hpp>
#include <boost/math/special_functions/erf.hpp>
#include <iostream>

int main() {
    // Gamma function: generalisation of factorial to real/complex numbers
    double g = boost::math::tgamma(5.0);   // 4! = 24
    std::cout << "tgamma(5) = " << g << "\n";

    // Bessel function of the first kind, order 0
    double j0 = boost::math::cyl_bessel_j(0, 1.5);
    std::cout << "J0(1.5) = " << j0 << "\n";

    // Error function
    double e = boost::math::erf(1.0);
    std::cout << "erf(1) = " << e << "\n";
}
```

:::tip C++17 added some of these
C++17 brought `std::beta`, `std::tgamma`, `std::cyl_bessel_j`, and a few others. Boost.Math
still covers far more functions and works on pre-C++17 compilers. It also provides error-handling
policies that the standard versions lack.
:::

## Statistical distributions

Every distribution is a type. You query it with free functions: `pdf`, `cdf`, `quantile`, `mean`,
`variance`, `skewness`, and more.

```cpp showLineNumbers title="distributions.cpp"
#include <boost/math/distributions/normal.hpp>
#include <boost/math/distributions/chi_squared.hpp>
#include <iostream>

int main() {
    using boost::math::normal;
    using boost::math::chi_squared;

    normal std_normal(0.0, 1.0);   // mean=0, stddev=1
    std::cout << "P(X < 1.96) = " << cdf(std_normal, 1.96) << "\n";    // ~0.975
    std::cout << "z for 95%  = " << quantile(std_normal, 0.975) << "\n"; // ~1.96

    chi_squared chi2(10);          // 10 degrees of freedom
    std::cout << "chi2 mean  = " << mean(chi2) << "\n";                 // 10
    std::cout << "chi2 p=0.05= " << quantile(chi2, 0.95) << "\n";      // ~18.307
}
```

| Distribution | Constructor | Typical use |
|-------------|-------------|-------------|
| `normal` | `normal(mean, sd)` | General statistics, z-tests |
| `students_t` | `students_t(df)` | Small-sample hypothesis testing |
| `chi_squared` | `chi_squared(df)` | Goodness-of-fit tests |
| `fisher_f` | `fisher_f(df1, df2)` | ANOVA, variance comparison |
| `binomial` | `binomial(n, p)` | Discrete success/failure trials |
| `poisson` | `poisson(lambda)` | Rare-event counting |

## Root finding

Boost.Math provides bracket-and-bisect, Newton-Raphson, and Halley's method for finding roots
of functions. These live in `<boost/math/tools/roots.hpp>`.

```cpp showLineNumbers title="root_finding.cpp"
#include <boost/math/tools/roots.hpp>
#include <cmath>
#include <iostream>

int main() {
    // Find x such that x^2 - 2 = 0  (i.e. sqrt(2))
    auto f = [](double x) { return x * x - 2.0; };

    // bisect needs a bracket [a, b] where f(a) and f(b) have opposite signs
    auto result = boost::math::tools::bisect(
        f, 1.0, 2.0,
        boost::math::tools::eps_tolerance<double>(52)  // 52-bit precision
    );

    double root = (result.first + result.second) / 2.0;
    std::cout << "sqrt(2) ~ " << root << "\n";
}
```

:::note Newton-Raphson needs derivatives
`newton_raphson_iterate` converges quadratically but requires the first derivative. `halley_iterate`
needs first and second derivatives for cubic convergence. If you only have `f(x)`, use `bisect` or
`bracket_and_solve_root`.
:::

## Numerical integration (quadrature)

For definite integrals where no closed-form solution exists, Boost.Math offers adaptive quadrature
routines.

```cpp showLineNumbers title="quadrature.cpp"
#include <boost/math/quadrature/gauss_kronrod.hpp>
#include <cmath>
#include <iostream>

int main() {
    using boost::math::quadrature::gauss_kronrod;

    // Integrate sin(x)/x from 0 to pi  (the sine integral Si(pi) ~ 1.8519)
    auto f = [](double x) { return x == 0.0 ? 1.0 : std::sin(x) / x; };

    double error;
    double result = gauss_kronrod<double, 15>::integrate(f, 0.0, M_PI, 5, 1e-9, &error);
    std::cout << "Si(pi) ~ " << result << ", error ~ " << error << "\n";
}
```

## Error-handling policies

Boost.Math lets you control what happens on domain errors, overflow, and underflow through
**policies**. The default throws on domain errors; you can switch to returning NaN, errno-based
handling, or ignoring.

```cpp showLineNumbers title="policies.cpp"
#include <boost/math/special_functions/gamma.hpp>
#include <boost/math/policies/error_handling.hpp>
#include <iostream>

using namespace boost::math::policies;

// Policy: return NaN on domain error instead of throwing
typedef policy<domain_error<ignore_error>> my_policy;

int main() {
    // tgamma(-1) is a pole — default would throw
    double g = boost::math::tgamma(-1.0, my_policy());
    std::cout << "tgamma(-1) = " << g << "\n";  // NaN, no exception
}
```

:::warning Performance consideration
Boost.Math is header-only and template-heavy. Instantiating many distributions or special functions
across different types will increase compile times. Consider using explicit instantiation in a `.cpp`
file if build times become a problem.
:::

## Boost.Math versus the standard library

| Feature | `<cmath>` / C++17 special functions | `Boost.Math` |
|---------|-------------------------------------|-------------|
| Basic functions (`sin`, `exp`, ...) | yes | yes (plus many more) |
| Special functions | partial (C++17) | 100+ functions |
| Statistical distributions | no | 30+ distributions |
| Root finding | no | bisect, Newton, Halley |
| Quadrature | no | Gauss-Kronrod, tanh-sinh, ... |
| Error policies | errno only | configurable policy system |
| Arbitrary-precision support | no | works with Multiprecision types |

## See also

- <Icon icon="lucide:calculator" inline /> [Boost.Multiprecision](./boost-multiprecision.md) — use with Boost.Math for high-precision calculations.
- <Icon icon="lucide:dice" inline /> [Boost.Random](./boost-random.md) — random number generation and distributions.
- <Icon icon="lucide:sigma" inline /> [Boost.Accumulators](./boost-accumulators.md) — streaming statistical computations.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) — the standardisation lineage.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
