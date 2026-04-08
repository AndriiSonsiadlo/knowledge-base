---
id: boost-random
title: Boost.Random
sidebar_label: Boost.Random
sidebar_position: 3
tags: [c++, boost, random, rng, distribution]
---

# Boost.Random

`Boost.Random` provides a framework of **random number engines** and **distributions** that separate
the source of randomness from the shape of the output. It is the direct ancestor of C++11's
`<random>` — the API was adopted almost verbatim into the standard. Boost.Random remains useful
for its extra engines, extra distributions, and for codebases that need to support pre-C++11
compilers.

:::info The problem it solves
`rand()` is global state, low quality, and gives you only uniform integers in `[0, RAND_MAX]`.
Real applications need different distributions (normal, Poisson, Bernoulli), reproducible seeding,
and independent generator instances. Boost.Random — and later `<random>` — formalise the separation
between *engines* (raw bits) and *distributions* (shaped output).
:::

## Engines and distributions

An **engine** produces a stream of uniformly distributed unsigned integers. A **distribution** maps
that stream into a specific shape (uniform real, normal, binomial, etc.).

```cpp showLineNumbers title="basic_usage.cpp"
#include <boost/random/mersenne_twister.hpp>
#include <boost/random/uniform_int_distribution.hpp>
#include <boost/random/normal_distribution.hpp>
#include <iostream>

int main() {
    boost::random::mt19937 rng(42);  // Mersenne Twister, seeded with 42

    // Uniform integer in [1, 6]
    boost::random::uniform_int_distribution<> die(1, 6);
    std::cout << "die roll: " << die(rng) << "\n";

    // Normal distribution: mean=0, stddev=1
    boost::random::normal_distribution<> gauss(0.0, 1.0);
    std::cout << "normal sample: " << gauss(rng) << "\n";
}
```

```mermaid
flowchart LR
    SEED[Seed] --> ENG[Engine -- mt19937, ranlux, ...]
    ENG --> |uniform bits| DIST[Distribution -- uniform, normal, ...]
    DIST --> OUT[Shaped random values]
```

## Available engines

| Engine | Quality | Speed | State size | Notes |
|--------|---------|-------|------------|-------|
| `mt19937` | excellent | fast | 2.5 KB | Default choice, period 2^19937-1 |
| `mt19937_64` | excellent | fast | 5 KB | 64-bit variant |
| `ranlux24` | high | slow | small | Luxury level random numbers |
| `lagged_fibonacci607` | good | very fast | ~4.8 KB | Long period, large state |
| `taus88` | acceptable | very fast | 12 bytes | Minimal state, short period |
| `random_device` | crypto-quality | varies | none | Non-deterministic, OS entropy |

:::note random_device for seeding
`boost::random::random_device` reads from the operating system's entropy pool (`/dev/urandom` on
Linux, `CryptGenRandom` on Windows). Use it to **seed** a fast engine like `mt19937`, not as the
engine itself — it is slow and may block.
:::

## Common distributions

```cpp showLineNumbers title="distributions.cpp"
#include <boost/random.hpp>
#include <iostream>

int main() {
    boost::random::mt19937 rng(12345);

    // Uniform real in [0.0, 1.0)
    boost::random::uniform_real_distribution<> uniform(0.0, 1.0);

    // Bernoulli: true with probability 0.3
    boost::random::bernoulli_distribution<> coin(0.3);

    // Poisson: mean = 4.0
    boost::random::poisson_distribution<> poisson(4.0);

    // Binomial: 10 trials, p = 0.5
    boost::random::binomial_distribution<> binom(10, 0.5);

    for (int i = 0; i < 5; ++i) {
        std::cout << "uniform=" << uniform(rng)
                  << " coin=" << coin(rng)
                  << " poisson=" << poisson(rng)
                  << " binom=" << binom(rng) << "\n";
    }
}
```

## Reproducibility

Given the same engine type and seed, the sequence is identical across runs and platforms. This is
essential for simulations, testing, and debugging.

```cpp showLineNumbers title="reproducible.cpp"
#include <boost/random/mersenne_twister.hpp>
#include <boost/random/uniform_int_distribution.hpp>
#include <cassert>

int main() {
    boost::random::mt19937 rng1(42);
    boost::random::mt19937 rng2(42);

    boost::random::uniform_int_distribution<> dist(1, 100);

    for (int i = 0; i < 1000; ++i) {
        assert(dist(rng1) == dist(rng2));  // always identical
    }
}
```

:::warning Do not use for cryptography
Engines like `mt19937` are **not** cryptographically secure — their internal state can be
reconstructed from 624 consecutive outputs. For security-sensitive randomness, use
`boost::random::random_device` directly or a dedicated crypto library.
:::

## Seeding from random_device

```cpp showLineNumbers title="proper_seeding.cpp"
#include <boost/random/mersenne_twister.hpp>
#include <boost/random/random_device.hpp>
#include <boost/random/uniform_int_distribution.hpp>
#include <iostream>

int main() {
    boost::random::random_device entropy;
    boost::random::mt19937 rng(entropy());  // non-deterministic seed

    boost::random::uniform_int_distribution<> dist(1, 1000);
    std::cout << dist(rng) << "\n";   // different every run
}
```

## Boost.Random versus std::random

| Feature | `boost::random` | `<random>` (C++11) |
|---------|-----------------|---------------------|
| Core API | engine + distribution | identical design |
| `mt19937` | yes | yes |
| `random_device` | yes | yes |
| Extra engines | `lagged_fibonacci`, `taus88`, more | fewer |
| Extra distributions | more variants | standard set |
| Serialization of engine state | `operator<<` / `operator>>` | same |
| Header-only | yes | yes (standard) |
| Pre-C++11 support | yes | no |

:::note Which to choose
On C++11 and later, `<random>` is fine for most use cases — the API is the same because it came
from Boost. Reach for Boost.Random when you need an engine or distribution not in `<random>`, or
when targeting a pre-C++11 toolchain.
:::

## See also

- <Icon icon="lucide:calculator" inline /> [Boost.Math](./boost-math.md) — statistical distributions for analytical work (PDF, CDF, quantiles).
- <Icon icon="lucide:sigma" inline /> [Boost.Accumulators](./boost-accumulators.md) — compute statistics over generated samples.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the C++ Standard](../00-overview/boost-and-the-standard.md) — the `<random>` lineage.
- <Icon icon="lucide:book-open" inline /> [Boost overview](../readme.md).
