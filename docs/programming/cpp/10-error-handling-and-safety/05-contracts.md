---
id: contracts
title: Contracts (C++26)
sidebar_label: Contracts
sidebar_position: 5
tags: [cpp, contracts, preconditions, postconditions, cpp26, contract-assert, p2900]
---

# Contracts (C++26)

A **contract** is the written agreement between a function and its callers: what the caller must
provide (**preconditions**), what the function guarantees in return (**postconditions**), and what must
hold inside the body (assertions). Until C++26 that agreement lives in comments and
[`assert`](./04-assertions.md) macros. C++26 adds **contract assertions** to the language itself, so
the compiler sees them, tools can reason about them, and the project controls what happens on a
violation. This page explains that design and, more importantly, states carefully where it stands,
because as of this page's date (November 2026) its standardization status is unsettled.

**Prerequisites:** [Assertions](./04-assertions.md) (what a precondition or invariant check is),
[Exceptions](./01-exceptions.md) (contrast with recoverable errors).

## Status: what is and is not settled \{#status\}

:::warning[As of 2026-11-11]
Do not treat contracts as a shipped feature of an ISO-published C++26. The facts below are from
WG21 papers and trip reports. Items marked *reported* come from secondary sources, because the
National Body comments were not public when this page was written.
:::

| Fact | Status | Source |
|---|---|---|
| Contract assertions (`pre`, `post`, `contract_assert`), proposal **P2900**, were adopted into the C++26 working draft at the February 2025 meeting (Hagenberg), plenary vote 100 for, 14 against, 12 abstaining | Adopted into the draft | [Sutter, Mar 2026 trip report](https://herbsutter.com/2026/03/29/c26-is-done-trip-report-march-2026-iso-c-standards-meeting-london-croydon-uk/) |
| At the March 2026 meeting (Croydon) WG21 finished C++26's technical work and sent it to the DIS (international) ballot, 114 for, 12 against, 3 abstaining. The trip report attributes the dissent mainly to contracts, and says the committee kept them | Retained | same |
| Feature-test macro `__cpp_contracts` is `202502L` for C++26. Contracts on virtual functions are listed under a later value (`202606L`, C++29), so they are **not** part of C++26 | Specified | [cppreference: contract assertions](https://en.cppreference.com/w/cpp/language/contracts) |
| The ISO DIS ballot for C++26 closed in October 2026 and was reported as **not approved**, with contracts named as the main cause. WG21 meets in Búzios, 16 to 21 November 2026, to choose the next step | *Reported*. Outcome of that meeting unknown | [P4433R0, "Do not remove Contracts from C++26"](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/p4433r0.pdf) (title and context); [Fertig, Nov 2026](https://andreasfertig.com/blog/2026/11/cpp26-dis-failed-how-does-cpp-survive/); [Wikipedia: C++26](https://en.wikipedia.org/wiki/C%2B%2B26) |
| Competing positions exist: P4334R0 argues the design has fundamental flaws; P4433R0 argues contracts should stay | Open | [open-std.org 2026 papers](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2026/) |

What this means in practice:

- The syntax and semantics below are those of P2900 as described on cppreference. They **may change**
  before C++26 is published, or the feature could be removed from it.
- Compiler support is early. GCC 16 implements P2900R14 (listed as "Contracts (PR119061)" on
  [gcc.gnu.org/gcc-16/changes.html](https://gcc.gnu.org/gcc-16/changes.html)). The flag to enable
  it is reportedly `-fcontracts` with `-std=c++26`, which that page does not confirm. Clang had no upstream support at the
  time of writing. Flag names and behaviour are implementation-specific; read your compiler's
  documentation. The snippets on this page were **not compiled**, because the toolchains available when
  this page was written (g++ 15.2, clang++ 21.1) do not implement contracts.
- Nothing here is needed to write correct code today. Section "Until then" lists what to use.

## The three constructs \{#syntax\}

`pre` and `post` are *identifiers with special meaning*, not reserved words; `contract_assert` is a
keyword.

```cpp showLineNumbers
// ...  (C++26 syntax, not compiled: see Status)
int divide(int dividend, int divisor)
    pre(divisor != 0);                       // precondition: checked on entry

int absolute_value(int n)
    post(r : r >= 0);                        // postcondition, "r" names the returned object

void push_checked(std::vector<int>& v, int x)
    pre(v.size() < v.max_size())
    post(v.size() > 0)                       // postcondition without a result binding
{
    v.push_back(x);
    contract_assert(v.back() == x);          // assertion statement inside the body
}
```

- `pre(cond)` is checked when the function is entered, `post(cond)` when it returns **normally**. A function
  that exits by exception never violates a postcondition.
- `post(r : cond)` binds `r` to the returned object; it is ill-formed on a `void` function. For a
  function whose return type is a deduced `auto`, the binding is allowed only on a definition.
- The predicate is an ordinary `bool` expression (no unparenthesized comma).
- A redeclaration must repeat the same specifiers or omit them.
- Not allowed on **virtual**, **deleted**, or first-declaration-defaulted functions (cppreference).
  Lambdas can carry them.

## Evaluation semantics \{#semantics\}

Writing a contract does not say what happens when it fails. The standard defines four **evaluation
semantics** and leaves **the choice implementation-defined**, per evaluation (typically a compiler
flag).

| Semantic | Predicate checked? | On violation |
|---|---|---|
| **ignore** | No | Nothing. The predicate is not evaluated |
| **observe** | Yes | Calls the violation handler, then **continues** |
| **enforce** | Yes | Calls the violation handler, then terminates the program |
| **quick-enforce** | Yes | Terminates immediately, without calling the handler |

A **contract violation** under a checking semantic means the predicate was false, evaluating it threw
an exception, or (in a constant expression) it was not a constant expression. "Terminates" means
`std::terminate`, `std::abort`, or just stopping; the implementation picks. During constant
evaluation, a violation under *observe* produces a diagnostic and under *enforce* makes the program
ill-formed.

<Diagram title="What happens at a contract check" caption="The handler is the extension point; the semantic decides whether the program continues." accent="violet">
  <DiagramRow>
    <DiagramNode title="Predicate">evaluates to false, throws, or is not constant</DiagramNode>
    <DiagramArrow direction="right" label="violation" />
    <DiagramNode title="Semantic" accent>ignore, observe, enforce or quick-enforce</DiagramNode>
    <DiagramArrow direction="right" label="observe, enforce" />
    <DiagramNode title="handle_contract_violation">receives std::contracts::contract_violation</DiagramNode>
  </DiagramRow>
</Diagram>

The handler is a function `void handle_contract_violation(const std::contracts::contract_violation&)`
(optionally `noexcept`). The implementation supplies a default, which the standard recommends should print a diagnostic; whether a
program may replace it is implementation-defined. The `contract_violation` object (header
`<contracts>`) carries details such as the kind of assertion, the source location and the evaluation
semantic (member names per the standard, not verified against a release here).

Because the semantic is a build-time choice, **the predicate must not have side effects the program
relies on**. It is unspecified whether the predicate runs at all, and the implementation may evaluate
it more than once. That is the same trap as `assert` under `NDEBUG`, now made unavoidable by design.

## What contracts are not

- **Not error handling.** They state bugs. A violated precondition means the *caller* is wrong, and the
  library should not promise a particular recovery. For input that can legitimately be bad, use
  [exceptions](./01-exceptions.md) or [`expected`](./03-error-codes.md#stdexpected).
- **Not optimization hints.** A failed check under *ignore* means the program continues with the
  condition false. If you want the compiler to assume something, that is a different feature
  (`[[assume]]`, C++23).
- **Not a replacement for `static_assert`.** Compile-time properties of types still use
  [`static_assert`](./04-assertions.md#static_assert-compile-time-checks).
- **Not undefined behavior by themselves.** A checked violation is defined (handler, then
  continue or terminate); what happens if you continue after *ignoring* one depends on the code that follows.
  See [Undefined Behavior](./06-undefined-behavior.md).

## Until then: what to use today \{#until-then\}

- **`assert`** for internal invariants, keeping the `NDEBUG` caveat in mind.
- **Library hardening** (`-D_GLIBCXX_ASSERTIONS`, libc++ hardening modes) to turn standard-library
  precondition violations (such as `operator[]` out of range) into aborts. Coverage is
  implementation-specific.
- **Throwing** for preconditions on a *public* API where a recoverable failure is wanted, at the cost of
  making the function non-`noexcept` (see the narrow-contract guideline in
  [noexcept](../04-functions-and-call-mechanics/noexcept.md#where-to-put-noexcept)).
- **Documented contracts** in comments or Doxygen-style `@pre` / `@post`, and project-level macros such
  as `MY_ASSERT` ([custom assertion macros](./04-assertions.md#custom-assertion-macros)).
- Guideline libraries provide `Expects(cond)` and `Ensures(cond)` macros (for example Microsoft GSL).
  They are macros, not language features, but they match the pre/postcondition vocabulary and are easy
  to replace with `pre`/`post` later.

## Key points

- Contract assertions are `pre(...)`, `post(...)` and `contract_assert(...)`, proposed as P2900 for
  C++26. Contracts on virtual functions are not part of C++26.
- Whether a check runs, and what a violation does, is chosen by the implementation: ignore, observe,
  enforce or quick-enforce.
- Predicates must be side-effect free in effect: they may run zero, one or many times.
- As of 2026-11-11 the C++26 DIS ballot was reported failed with contracts as the main dispute, and WG21
  had not yet decided the way forward. Check [isocpp.org](https://isocpp.org/) and the WG21 papers
  index before relying on this feature.
- Use `assert`, hardening and documented preconditions today.
