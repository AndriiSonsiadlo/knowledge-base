---
id: gcd-and-modular-arithmetic
title: GCD & Modular Arithmetic
sidebar_label: GCD & Modular Arithmetic
sidebar_position: 2
tags: [computer-science, algorithms, math, number-theory, modular-arithmetic]
---

# GCD & Modular Arithmetic

The greatest common divisor looks like a problem for factoring both numbers and comparing their
prime factorizations — and that works, but it costs as much as factoring, which for large numbers is
expensive. Euclid's algorithm answers the same question without ever finding a single factor, using
one observation instead: `gcd(a, b) = gcd(b, a mod b)`. Repeatedly replacing the pair `(a, b)` with
`(b, a mod b)` shrinks the numbers every step and always reaches `(g, 0)`, at which point `g` is the
answer. No factoring, no primality testing, just repeated remainders — and it is fast for a reason
this page derives rather than asserts.

Fast exponentiation solves a different-looking problem the same way: computing `a^b mod m` by
squaring is not a modular-arithmetic trick bolted onto ordinary exponentiation, it *is* what
exponentiation becomes once every intermediate result is kept small by reducing modulo `m` at every
step, rather than only once at the very end. That single habit — reduce early, reduce often — is the
one idea underlying every use of modular arithmetic this section's other pages lean on, from a
rolling hash's window update to a cryptographic key exchange's repeated squaring.

## Core Concepts

| Term | Meaning |
|---|---|
| **GCD** | `gcd(a, b)`: the largest integer dividing both `a` and `b` with no remainder |
| **Extended Euclid** | Alongside `gcd(a, b)`, finds integers `x, y` such that `a*x + b*y = gcd(a, b)` (Bezout's identity) |
| **Modular inverse** | `a⁻¹ mod m`: the value `x` with `a*x ≡ 1 (mod m)`; exists exactly when `gcd(a, m) = 1` |
| **Fast exponentiation** | Computing `a^b mod m` in O(log b) multiplications by repeated squaring, instead of O(b) sequential ones |
| **Modular multiply identity** | `(a * b) mod m = ((a mod m) * (b mod m)) mod m` — the identity that lets every intermediate stay bounded |

## Mechanism

Trace input — `gcd(252, 198)` by Euclid's algorithm, and `3^13 mod 7` by fast exponentiation.

<Figure src="/img/cs/algorithms/euclid-steps.png"
        alt="A sequence of shrinking rectangles illustrating Euclid's algorithm on gcd(252, 198), each rectangle's long side replaced by the remainder of the previous division"
        caption="Euclid's algorithm as shrinking rectangles: a 252x198 rectangle, then 198x54, then 54x36, then 36x18 -- an 18x18 square tiles the last one exactly, so 18 is the GCD."
        source="Generated for this page" href="" license="" />

```text
gcd(252, 198):
  252 = 1*198 + 54      gcd(252, 198) = gcd(198, 54)
  198 = 3*54  + 36      gcd(198, 54)  = gcd(54, 36)
   54 = 1*36  + 18      gcd(54, 36)   = gcd(36, 18)
   36 = 2*18  +  0      gcd(36, 18)   = gcd(18, 0) = 18

gcd(252, 198) = 18
```

Every step replaces the pair with strictly smaller numbers, and the sequence of remainders it
produces is at its slowest exactly when consecutive Fibonacci numbers are fed in — Lame's theorem
(cited in CLRS 4th ed. §31.2 and Knuth's *TAOCP* Vol. 2) shows the number of division steps is
O(log min(a, b)), with the Fibonacci pair as the adversarial input that makes every quotient equal
to 1 and forces the maximum number of steps for a given size.

```text
3^13 mod 7 by squaring -- the algorithm below reads the exponent's bits low to high (bit 0
first), squaring the base at every step and folding it into the result only where the bit is 1.
13 in binary is 1101, so bit 0 = 1, bit 1 = 0, bit 2 = 1, bit 3 = 1:

  result = 1, base = 3
  bit 0 (=1): result = 1*3       mod 7 = 3         base = 3^2  mod 7 = 2
  bit 1 (=0): result unchanged = 3                 base = 2^2  mod 7 = 4
  bit 2 (=1): result = 3*4       mod 7 = 5         base = 4^2  mod 7 = 2
  bit 3 (=1): result = 5*2       mod 7 = 3         base = 2^2  mod 7 = 4 (unused, loop ends)

3^13 mod 7 = 3      (check: 3 has order 6 mod 7 -- 3^6 = 729 = 104*7 + 1 -- and 13 mod 6 = 1,
                     so 3^13 = 3^(6*2+1) = (3^6)^2 * 3^1 = 1^2 * 3 = 3 mod 7)
```

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
def gcd(a, b):
    """O(log min(a, b)) worst case -- the Fibonacci pair realizes it (CLRS 4/e s31.2)."""
    while b:
        a, b = b, a % b
    return a


def extended_gcd(a, b):
    """Returns (g, x, y) with a*x + b*y = g = gcd(a, b). Same O(log min(a, b)) bound."""
    old_r, r = a, b
    old_x, x = 1, 0
    old_y, y = 0, 1
    while r:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_x, x = x, old_x - q * x
        old_y, y = y, old_y - q * y
    return old_r, old_x, old_y


def mod_inverse(a, m):
    """a^-1 mod m, via extended Euclid. Exists iff gcd(a, m) == 1."""
    g, x, _ = extended_gcd(a, m)
    if g != 1:
        raise ValueError(f"no modular inverse: gcd({a}, {m}) = {g} != 1")
    return x % m


def mod_pow(base, exp, mod):
    """a^b mod m in O(log b) multiplications: reduce after every squaring, never wait."""
    result = 1 % mod
    base %= mod
    while exp > 0:
        if exp & 1:
            result = (result * base) % mod
        base = (base * base) % mod
        exp >>= 1
    return result
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
#include <cassert>
#include <cstdint>
#include <stdexcept>
#include <tuple>

long long gcd_fn(long long a, long long b) {
    while (b) { long long t = a % b; a = b; b = t; }
    return a;
}

std::tuple<long long, long long, long long> extended_gcd(long long a, long long b) {
    long long old_r = a, r = b, old_x = 1, x = 0, old_y = 0, y = 1;
    while (r) {
        long long q = old_r / r;
        long long tmp_r = old_r - q * r; old_r = r; r = tmp_r;
        long long tmp_x = old_x - q * x; old_x = x; x = tmp_x;
        long long tmp_y = old_y - q * y; old_y = y; y = tmp_y;
    }
    return {old_r, old_x, old_y};
}

long long mod_inverse(long long a, long long m) {
    auto [g, x, y] = extended_gcd(a, m);
    if (g != 1) throw std::domain_error("no modular inverse");
    return ((x % m) + m) % m;                 // C++'s % can return negative -- see Edge Cases
}

// Note: uses __int128 internally to avoid overflow on the intermediate product --
// see "overflow in the modular multiply" below.
long long mod_pow(long long base, long long exp, long long mod) {
    long long result = 1 % mod;
    base %= mod;
    while (exp > 0) {
        if (exp & 1) result = static_cast<long long>((__int128)result * base % mod);
        base = static_cast<long long>((__int128)base * base % mod);
        exp >>= 1;
    }
    return result;
}
```

</TabItem>
</Tabs>

## Practical Usage

- **Python's [`math.gcd`](https://docs.python.org/3/library/math.html#math.gcd)** is implemented in C
  and should be preferred over a hand-written loop in production code; the loop above exists to show
  the O(log min(a, b)) mechanism, not to be re-implemented.
- **`pow(base, exp, mod)`** — Python's three-argument built-in `pow` performs fast modular
  exponentiation natively (see the
  [built-in functions docs](https://docs.python.org/3/library/functions.html#pow)); it is the
  standard library's version of `mod_pow` above and should be used directly rather than
  hand-rolled, except when the goal is to show the squaring mechanism itself.
- **Cryptography.** RSA key generation needs a modular inverse (extended Euclid) to compute the
  private exponent from the public one, and RSA encryption/decryption is fast exponentiation modulo
  a large composite — both are exactly the two functions on this page, at much larger bit widths.
- **[Naive Matching & Rabin-Karp](../strings-and-text/naive-matching-and-rabin-karp.md)'s rolling
  hash** precomputes `pow(BASE, m - 1, MOD)` once with fast exponentiation, then updates its window
  hash with one modular multiply per slide — the identity this page opened with, applied directly.

<Tabs groupId="code-lang">
<TabItem value="python" label="Python">

```python showLineNumbers
# gcd, extended Euclid, modular inverse, and fast exponentiation, checked on the traced inputs
assert gcd(252, 198) == 18
g, x, y = extended_gcd(252, 198)
assert g == 18 and 252 * x + 198 * y == 18          # Bezout's identity holds exactly
assert mod_inverse(3, 11) == 4                       # 3*4 = 12 = 1 (mod 11)
assert (3 * mod_inverse(3, 11)) % 11 == 1
assert mod_pow(3, 13, 7) == 3                        # matches the traced squaring above
assert mod_pow(3, 13, 7) == pow(3, 13, 7)            # cross-checked against the stdlib
```

</TabItem>
<TabItem value="cpp" label="C++">

```cpp showLineNumbers
int main() {
    assert(gcd_fn(252, 198) == 18);
    auto [g, x, y] = extended_gcd(252, 198);
    assert(g == 18 && 252 * x + 198 * y == 18);
    assert(mod_inverse(3, 11) == 4);
    assert(mod_pow(3, 13, 7) == 3);
}
```

</TabItem>
</Tabs>

## Edge Cases & Pitfalls

- **Overflow in the modular multiply.** `(a * b) % m` overflows a 64-bit `long long` the moment `a`
  and `b` are both close to 2^63 -- the product itself, not the final residue, is what overflows.
  C++ code that will run with `m` near the limit of a 64-bit type needs a widening multiply
  (`__int128`, shown above) or a "Russian peasant" modular multiply that never forms the full
  product. See [Integers & Two's Complement](../../bit-manipulation/integers-and-twos-complement.md)
  for what silently wrapping around actually looks like. Python has no such trap: its `int` is
  arbitrary precision, so `(a * b) % m` is always exact regardless of magnitude.
- **Negative results from C++'s `%`.** C++'s `%` can return a negative value when its left operand
  is negative — `(-7) % 3 == -1` in C++, not `2`. `mod_inverse` above adds `m` and takes `% m` again
  specifically to normalize this. Python's `%` always returns a result with the sign of the divisor,
  so this trap is language-specific to C++ and similar languages, not universal.
- **Assuming a modular inverse always exists.** `mod_inverse(a, m)` is only defined when
  `gcd(a, m) = 1`; calling it with, say, `a = 4, m = 8` has no solution (`gcd(4, 8) = 4 != 1`) and
  the function above correctly raises rather than returning a wrong number.
- **Sequential multiplication instead of squaring.** Computing `a^b mod m` with a loop that
  multiplies by `a` exactly `b` times is O(b), not O(log b) -- correct, but for cryptographic-sized
  exponents (hundreds of bits) the difference is the difference between instant and never finishing.

## Comparisons

| | Cost | What it computes |
|---|---|---|
| Euclid's algorithm | O(log min(a, b)) worst | `gcd(a, b)` |
| Extended Euclid | O(log min(a, b)) worst | `gcd(a, b)` plus Bezout coefficients `x, y` |
| Modular inverse via extended Euclid | O(log m) worst | `a⁻¹ mod m`, when it exists |
| Modular inverse via Fermat's little theorem | O(log m) worst | `a⁻¹ mod m`, but only when `m` is prime (`a^(m-2) mod m`) |
| Fast exponentiation (squaring) | O(log b) worst | `a^b mod m` |
| Sequential exponentiation | O(b) worst | `a^b mod m` |

Fermat's-little-theorem inverses avoid extended Euclid entirely when the modulus is prime — one call
to `mod_pow` instead — but silently give a wrong answer if `m` is composite, since the theorem's
precondition simply does not hold; extended Euclid works for any modulus and detects the
no-inverse case explicitly instead of failing silently.

## Recall

<Recall
  invariant="gcd(a, b) = gcd(b, a mod b), and reducing modulo m after every multiplication instead of once at the end keeps every intermediate value bounded -- both are the same idea of never letting a computation's size grow past what the final answer needs."
  costs={[
    ["Euclid's algorithm, gcd(a, b) (worst)", "O(log min(a, b))"],
    ["extended Euclid (worst)", "O(log min(a, b))"],
    ["modular inverse via extended Euclid (worst)", "O(log m)"],
    ["fast exponentiation, a^b mod m (worst)", "O(log b)"],
    ["sequential exponentiation, a^b mod m (worst)", "O(b)"],
  ]}
  reachFor="Any computation that chains multiplications under a fixed modulus -- rolling hashes, modular inverses, or exponentiation with a large exponent -- where reducing early keeps every step cheap."
  trap="Forming the full product before taking the modulus in a fixed-width language -- the product overflows even when the final residue would have fit comfortably."
/>

## References

- Cormen, Leiserson, Rivest & Stein, *Introduction to Algorithms*, 4th ed., §31.2 "Greatest common
  divisor" — Euclid's algorithm, its running time, and the Fibonacci worst case.
- Sedgewick & Wayne, *Algorithms*, 4th ed., §1.1 "Basic Programming Model" — GCD as a canonical
  worked example of a while-loop algorithm's correctness argument.
- [`math.gcd`](https://docs.python.org/3/library/math.html#math.gcd) and the three-argument
  [`pow(base, exp, mod)`](https://docs.python.org/3/library/functions.html#pow) — CPython's own
  documentation for both operations this page derives by hand.

## Related Pages

- [Math & Number Theory](./intro.md) — the folder's map of where this arithmetic surfaces elsewhere.
- [Primes & Sieves](./primes-and-sieves.md) — the previous page's sieve, and where fast exponentiation
  reappears inside probabilistic primality tests.
- [Integers & Two's Complement](../../bit-manipulation/integers-and-twos-complement.md) — the
  overflow behavior this page's modular-multiply warning depends on.
- [Naive Matching & Rabin-Karp](../strings-and-text/naive-matching-and-rabin-karp.md) — the rolling
  hash that applies this page's modular multiply once per slide.
