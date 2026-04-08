---
id: boost-ublas
title: Boost.uBLAS
sidebar_label: Boost.uBLAS
sidebar_position: 7
tags: [c++, boost, ublas, linear-algebra, matrix]
---

# Boost.uBLAS

`Boost.uBLAS` (micro Basic Linear Algebra Subprograms) provides **vector and matrix types** with
standard linear-algebra operations: addition, scalar multiplication, inner/outer products, matrix
multiplication, and element access. It uses **expression templates** for lazy evaluation, avoiding
temporaries in compound expressions. uBLAS is header-only and requires no external BLAS library.

:::info The problem it solves
The C++ standard library has no vector/matrix types for linear algebra. Writing your own risks
bugs in indexing, memory layout, and operator overloading. uBLAS gives you correct, tested
containers with natural mathematical syntax (`A * x + b`) and support for dense, sparse, banded,
and triangular storage.
:::

## Vectors

```cpp showLineNumbers title="vectors.cpp"
#include <boost/numeric/ublas/vector.hpp>
#include <boost/numeric/ublas/io.hpp>
#include <iostream>

namespace ublas = boost::numeric::ublas;

int main() {
    ublas::vector<double> v(3);
    v(0) = 1.0; v(1) = 2.0; v(2) = 3.0;

    ublas::vector<double> w(3);
    w(0) = 4.0; w(1) = 5.0; w(2) = 6.0;

    // Element-wise addition
    ublas::vector<double> sum = v + w;
    std::cout << "v + w = " << sum << "\n";   // [3](5,7,9)

    // Scalar multiplication
    ublas::vector<double> scaled = 2.0 * v;
    std::cout << "2*v   = " << scaled << "\n"; // [3](2,4,6)

    // Inner (dot) product
    double dot = ublas::inner_prod(v, w);
    std::cout << "v . w = " << dot << "\n";    // 32
}
```

:::note Indexing starts at 0
uBLAS uses `operator()` for element access, not `operator[]`. Indexing is zero-based:
`v(0)` is the first element, `A(0, 1)` is row 0, column 1.
:::

## Dense matrices

```cpp showLineNumbers title="matrices.cpp"
#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/io.hpp>
#include <iostream>

namespace ublas = boost::numeric::ublas;

int main() {
    ublas::matrix<double> A(2, 3);  // 2 rows, 3 columns
    A(0,0) = 1; A(0,1) = 2; A(0,2) = 3;
    A(1,0) = 4; A(1,1) = 5; A(1,2) = 6;

    ublas::matrix<double> B(3, 2);
    B(0,0) = 7; B(0,1) = 8;
    B(1,0) = 9; B(1,1) = 10;
    B(2,0) = 11; B(2,1) = 12;

    // Matrix multiplication: (2x3) * (3x2) = (2x2)
    ublas::matrix<double> C = ublas::prod(A, B);
    std::cout << "A * B =\n" << C << "\n";
    // [2,2]((58,64),(139,154))
}
```

## Matrix-vector product

```cpp showLineNumbers title="matvec.cpp"
#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/vector.hpp>
#include <boost/numeric/ublas/io.hpp>
#include <iostream>

namespace ublas = boost::numeric::ublas;

int main() {
    ublas::matrix<double> A(2, 2);
    A(0,0) = 1; A(0,1) = 2;
    A(1,0) = 3; A(1,1) = 4;

    ublas::vector<double> x(2);
    x(0) = 5; x(1) = 6;

    ublas::vector<double> b = ublas::prod(A, x);
    std::cout << "A*x = " << b << "\n";  // [2](17,39)
}
```

## Special matrix types

uBLAS provides storage-optimised types for common matrix structures:

| Type | Header | Storage | Use case |
|------|--------|---------|----------|
| `matrix<T>` | `matrix.hpp` | dense, row-major | general purpose |
| `identity_matrix<T>` | `matrix.hpp` | implicit | identity operations |
| `zero_matrix<T>` | `matrix.hpp` | implicit | zero-initialisation |
| `triangular_matrix<T>` | `triangular.hpp` | half the elements | LU decomposition |
| `banded_matrix<T>` | `banded.hpp` | diagonals only | tridiagonal systems |
| `symmetric_matrix<T>` | `symmetric.hpp` | half + mirror | covariance matrices |
| `mapped_matrix<T>` | `mapped_matrix.hpp` | hash map | sparse, random access |
| `compressed_matrix<T>` | `compressed_matrix.hpp` | CSR/CSC | sparse, sequential |

```cpp showLineNumbers title="sparse.cpp"
#include <boost/numeric/ublas/mapped_matrix.hpp>
#include <boost/numeric/ublas/io.hpp>
#include <iostream>

namespace ublas = boost::numeric::ublas;

int main() {
    // Sparse matrix: only non-zero entries stored
    ublas::mapped_matrix<double> S(1000, 1000);
    S(0, 0) = 1.0;
    S(500, 500) = 2.0;
    S(999, 999) = 3.0;

    std::cout << "S(500,500) = " << S(500, 500) << "\n";  // 2
    std::cout << "S(1,1) = " << S(1, 1) << "\n";          // 0 (not stored)
}
```

## Expression templates

uBLAS evaluates compound expressions lazily. `A + B` does not create a temporary matrix — it
creates a lightweight proxy that computes elements on demand when assigned.

```cpp showLineNumbers title="expression_templates.cpp"
#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/io.hpp>

namespace ublas = boost::numeric::ublas;

int main() {
    ublas::matrix<double> A(2, 2), B(2, 2), C(2, 2);
    A(0,0) = 1; A(0,1) = 2; A(1,0) = 3; A(1,1) = 4;
    B(0,0) = 5; B(0,1) = 6; B(1,0) = 7; B(1,1) = 8;

    // No temporary for A + B; the sum is evaluated directly into C
    C = A + B;

    // Chained: also no temporaries for (2*A + B)
    C = 2.0 * A + B;
}
```

:::warning uBLAS is not a high-performance BLAS
uBLAS provides correct, portable linear algebra with a clean C++ API, but it does **not** match
the performance of optimised BLAS implementations (OpenBLAS, MKL, ATLAS) or modern C++ libraries
like Eigen. For performance-critical numerical code — large matrix decompositions, iterative
solvers, machine learning — prefer Eigen or link against an optimised BLAS. uBLAS is best suited
for moderate-size problems where API convenience and portability outweigh raw speed.
:::

## Subranges and slicing

```cpp showLineNumbers title="slicing.cpp"
#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/matrix_proxy.hpp>
#include <boost/numeric/ublas/io.hpp>
#include <iostream>

namespace ublas = boost::numeric::ublas;

int main() {
    ublas::matrix<double> A(4, 4);
    for (unsigned i = 0; i < 4; ++i)
        for (unsigned j = 0; j < 4; ++j)
            A(i, j) = i * 4 + j;

    // Extract a 2x2 submatrix starting at (1,1)
    ublas::matrix_range<ublas::matrix<double>> sub(
        A, ublas::range(1, 3), ublas::range(1, 3)
    );
    std::cout << "submatrix:\n" << sub << "\n";
    // [2,2]((5,6),(9,10))
}
```

## See also

- <Icon icon="lucide:calculator" inline /> [Boost.Math](./boost-math.md) — mathematical functions to complement linear algebra.
- <Icon icon="lucide:sigma" inline /> [Boost.Accumulators](./boost-accumulators.md) — streaming statistics without full matrix storage.
- <Icon icon="lucide:calculator" inline /> [Boost.Multiprecision](./boost-multiprecision.md) — use as the element type for high-precision matrices.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
