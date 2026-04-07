---
id: versioning-and-releases
title: Versioning and Releases
sidebar_label: Versioning and Releases
sidebar_position: 6
tags: [ c++, boost, versioning, releases ]
---

# Versioning and Releases

Boost ships as one coordinated release with one version number, even though it is really ~160
[independent libraries](./what-is-boost.md). That single number — something like **1.85.0** — tells you
which snapshot of every library you have, which is what makes "I'm on Boost 1.85" a meaningful statement.
This page covers the versioning scheme, the release cadence, how to read the version from code, and how
the project is structured behind the scenes.

:::info The one number you quote
When you report a Boost version, you give the umbrella release number (for example `1.85.0`), not a
per-library version. Every library in that release is whatever revision shipped in `1.85.0`.
:::

## The versioning scheme

Boost versions look like **`1.XX.0`**:

- The leading **`1`** has been constant since 1999 and effectively never changes — do not read SemVer
  "major version" meaning into it.
- The **`XX`** is the part that actually moves: `1.82`, `1.83`, `1.84`, `1.85`, and so on. This is the
  number people mean when they say "Boost 1.85."
- The trailing **`0`** is a point/patch slot. It is almost always `0`; Boost occasionally issues a
  point release (for example a `1.XX.1`) to fix a serious problem, but routine work goes into the next
  `XX`.

So the *minor* field carries the real version progression. Treat `1.84` to `1.85` the way you would treat
a normal minor version bump elsewhere: mostly additive, occasionally with deprecations or breaking
changes in specific libraries.

## Release cadence

Boost ships on a **time-based schedule of roughly three releases per year** — historically in the spring,
summer, and around the end of the year. Releases are not gated on any single feature; whatever is ready by
the cut-off goes out, and the rest waits for the next train.

```mermaid
flowchart LR
    DEV[Ongoing development in per-library repos] --> BETA[Beta build for the release]
    BETA --> RC[Release candidate and testing]
    RC --> REL[Numbered release 1.XX.0]
    REL --> NEXT[Next cycle begins]
```

:::tip Pin your version
Because three releases a year means the landscape shifts steadily, pin a specific Boost version in your
build (via your [package manager](../01-build-and-integration/package-managers.md) or a fixed download)
rather than tracking "latest." Upgrade deliberately and re-run your tests.
:::

## Reading the version from code: BOOST_VERSION

Boost exposes its version to the preprocessor through `<boost/version.hpp>`, which defines two macros:

- **`BOOST_VERSION`** — a single integer encoding the version as `MAJOR * 100000 + MINOR * 100 + PATCH`.
  For Boost 1.85.0 that is `108500`.
- **`BOOST_LIB_VERSION`** — a string like `"1_85"`, the form used inside auto-link library filenames on
  MSVC (see [header-only vs compiled](./header-only-vs-compiled.md)).

```cpp showLineNumbers title="print_version.cpp"
#include <boost/version.hpp>
#include <iostream>

int main() {
    // Decode the packed integer back into its parts
    std::cout << "Boost "
              << BOOST_VERSION / 100000 << '.'        // major -> 1
              << BOOST_VERSION / 100 % 1000 << '.'    // minor -> 85
              << BOOST_VERSION % 100 << '\n';         // patch -> 0

    std::cout << "Lib tag: " << BOOST_LIB_VERSION << '\n';  // "1_85"
}
```

Because `BOOST_VERSION` is a plain integer, you can guard code on it at compile time — useful when a
feature or fix landed in a known release:

```cpp showLineNumbers title="version_guard.cpp"
#include <boost/version.hpp>

#if BOOST_VERSION >= 108300        // 1.83.0 or newer
    // use the newer API path
#else
    // fall back for older Boost
#endif
```

:::note Why the packed integer
The single-integer form makes version comparisons trivial in the preprocessor — `BOOST_VERSION >= 108300`
is one clean comparison, whereas comparing separate major/minor/patch macros would need nested checks.
:::

## Deprecation policy

Boost's general approach is to **warn before it breaks**. When a library deprecates an interface, it
typically keeps the old path working for a transition period and emits a deprecation warning, often
controllable through a macro so you can silence it or opt into the new behaviour early. Some libraries
expose macros such as `BOOST_<LIB>_NO_DEPRECATED` to compile out the legacy surface entirely.

That said, deprecation timelines are decided **per library**, not centrally — there is no single
project-wide guarantee of how many releases an old API survives. Always read a library's own changelog
before assuming an upgrade is transparent.

:::warning Read the release notes before upgrading
Each release ships notes describing per-library changes, deprecations, and removals. Skipping several
versions at once compounds the risk: a quietly deprecated API in `1.81` may be *gone* by `1.85`. Upgrade
in steps when you can, and rebuild against your test suite.
:::

## Modularization: the superproject and per-library repos

Although users consume Boost as one tarball, development is **modular**. Each library lives in its own Git
repository (for example a repo for Filesystem, another for Asio), and these are stitched together by a
**superproject** that references them as Git submodules. A release is essentially a coordinated snapshot of
all those submodules at compatible commits.

```bash
# Clone the superproject and all library submodules
git clone --recursive https://github.com/boostorg/boost.git
cd boost

# Check out a specific release and sync submodules to it
git checkout boost-1.85.0
git submodule update --init --recursive
```

This structure has practical consequences:

- You can track or contribute to a single library's repo without dealing with the whole tree.
- Tooling can, in principle, fetch just the libraries you depend on plus their internal dependencies.
- The unified release still gives you one tested, mutually-compatible set — you are not responsible for
  matching individual library versions yourself.

## Reading release notes

When a new version lands, the release notes are your map. A useful reading order:

1. **Scan for "Breaking changes" and "Removed"** across the libraries you actually use — these are what
   can stop your build.
2. **Check deprecations** so you can migrate ahead of an eventual removal.
3. **Note new libraries and features** that might let you drop a workaround or a third-party dependency.
4. **Confirm toolchain/standard requirements** — Boost periodically raises its minimum compiler and C++
   standard, which can affect whether a version even builds for you.

## Where to go next

- <Icon icon="lucide:git-fork" inline /> [History and philosophy](./history-and-philosophy.md) — the review culture behind each release.
- <Icon icon="lucide:package" inline /> [Boost via vcpkg and Conan](../01-build-and-integration/package-managers.md) — pin and install a specific version.
- <Icon icon="lucide:puzzle" inline /> [Header-only vs compiled](./header-only-vs-compiled.md) — where `BOOST_LIB_VERSION` shows up.
- <Icon icon="lucide:arrow-left-right" inline /> [Boost and the C++ standard](./boost-and-the-standard.md) — track which version gained which feature.
