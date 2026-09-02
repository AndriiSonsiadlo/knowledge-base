---
id: exported-symbols-and-the-module-abi
title: "Exported Symbols and the Non-Stable ABI"
sidebar_label: "Exported symbols"
sidebar_position: 5
tags: [linux, kernel]
prerequisites:
  - linux/kernel-architecture-and-idioms/modules-in-practice
draft: false
---

# Exported Symbols and the Non-Stable ABI

Why "never break user space" and "break modules freely" are a consistent pair of positions rather than hypocrisy.

A module can only call kernel functions that have been *exported* — the export list is a deliberate,
curated interface, not an accident of linkage. Understanding it explains both why some out-of-tree drivers
cannot be written at all, and why "Linux has no stable in-kernel ABI" is a maintenance policy, not a
technical shortcoming the project never got around to fixing.

## `EXPORT_SYMBOL` and `EXPORT_SYMBOL_GPL`

Every function a module is allowed to call must be marked exported at its definition site. Most kernel
functions are not — they are internal to their subsystem, and a module simply cannot see them, let alone
link against them. A function that should be callable from a module gets one of two macros immediately
after its definition:

- `EXPORT_SYMBOL(func)` exports it with no license restriction — any module can resolve it.
- `EXPORT_SYMBOL_GPL(func)` exports it only to modules whose declared `MODULE_LICENSE` the kernel recognises
  as GPL-compatible; a non-GPL module's attempt to resolve a `_GPL` symbol fails at load time, not at call
  time.

This is a technical mechanism carrying a legal intent, and it's worth being factual about both halves: the
check is a straightforward string comparison against the license a module declared, enforced by the module
loader before the module is allowed to run at all; the intent behind marking a given symbol `_GPL` is a
judgment call by that symbol's maintainers about how tightly they want to couple it to GPL-derived code.

## The export list is not the API

An exported symbol carries no compatibility promise. Its signature, its locking requirements, and its
existence at all can change in the very next release, and when that happens every in-tree caller is updated
in the same commit that changes the function — there is no deprecation period, because there is no external
contract to honour. `EXPORT_SYMBOL` answers "can a module call this at all"; it says nothing about whether
calling it will still work, or still mean the same thing, next kernel release.

## Symbol versioning (`modversions`)

`CONFIG_MODVERSIONS` adds a check that turns a silent ABI mismatch into a refused load instead of a
miscompiled call. For each exported symbol, the build computes a CRC over that symbol's *type signature* —
not its address, its shape: argument types, return type, and (transitively) the layout of any struct it
touches. That table of symbol-name-to-CRC pairs is written to `Module.symvers` at build time, and a module
built against one `Module.symvers` embeds the CRCs it was compiled against. At load time, the kernel
recomputes each symbol's current CRC and compares it against the value the module recorded; a mismatch means
the function's type signature moved in a way that would silently corrupt memory if the module were allowed
to call it with its old idea of the calling convention, and the module is refused before it can find out
the hard way.

## Version magic

Independent of modversions, every compiled module and every running kernel carry a `vermagic` string,
built from `UTS_RELEASE` plus a handful of concatenated config tokens: the kernel release, whether it's
SMP, the preemption model, whether module unloading is supported, whether modversions is enabled, and an
architecture-specific token (`MODULE_ARCH_VERMAGIC`) that's empty on x86-64 — there's no per-arch variant
to distinguish there. A module's `vermagic` must match the running kernel's exactly (module loading can
compare the two ignoring the leading version if the module carries CRCs; see `same_magic()`). This is a
coarser check than modversions: it doesn't reason about any individual symbol's type, and it says nothing
about which compiler built either side — it just refuses to link a module that was plainly configured
differently from the running kernel.

## What actually happens

An out-of-tree driver "breaks" on a kernel upgrade often enough to be a cliché. Nothing broke: an internal
interface the driver depended on changed, as it always may, and the driver was built against the old one.
`modinfo` on the module shows exactly what it was built against:

```text
$ modinfo hello.ko
filename:       /lib/modules/6.18.0/extra/hello.ko
license:        GPL
srcversion:     3F1A9C2B7E4D5A6F19203B4C
depends:
vermagic:       6.18.0 SMP preempt mod_unload modversions
```

Two distinct failures follow from two distinct checks, and they produce two distinct messages. A `vermagic`
mismatch is caught before the module is even parsed for symbols, and userspace's `insmod` reports it as a
generic format error:

```text
$ insmod hello.ko
insmod: ERROR: could not insert module hello.ko: Invalid module format
```

A modversions CRC mismatch on one specific symbol is caught later, while resolving that symbol, and is
reported by the kernel itself, in `dmesg`, naming the symbol:

```text
$ dmesg | tail -1
hello: disagrees about version of symbol some_exported_function
```

Both are the same underlying situation — the module and the running kernel disagree about an internal
interface — caught by two different checks at two different points in the load path.

## Why this is consistent with "we do not break user space"

Two different audiences, two different bargains. User-space programs are compiled once and run, unmodified,
against whatever kernel version they find — the kernel community cannot rebuild every program that ever
linked against a syscall, so the user-space ABI is held effectively fixed. In-tree kernel code is a
different situation entirely: every caller of an internal interface lives in the same tree as that
interface, and when the interface changes, every caller changes in the same commit, by the same person,
reviewed together. An out-of-tree module chose to be neither of those things — not user space, and not
in-tree code that gets updated alongside the interfaces it depends on — and modversions and vermagic are
what make that choice's actual cost visible at load time instead of as silent corruption at runtime.

## The three checks a module must pass to load

| Check | What it catches | What it produces | What to do |
|---|---|---|---|
| Version magic (`vermagic`) | Module built for a different kernel version, SMP/preemption configuration, or compiler | `insmod`/`modprobe`: `Invalid module format` | Rebuild the module against the running kernel's headers and build tree |
| Symbol resolution | Module calls a symbol that isn't exported at all, or isn't exported `EXPORT_SYMBOL_GPL` to a non-GPL module | `insmod`: `Unknown symbol in module`; `dmesg` names the missing symbol | Confirm the symbol is still exported in this kernel, and check the module's declared license |
| Symbol version (modversions CRC) | The symbol exists, but its type signature changed since the module was built | `dmesg`: `<module>: disagrees about version of symbol <name>` | Rebuild against the current `Module.symvers` — the interface itself moved |

## Misconceptions

**"The kernel has no ABI."** No — it has an extremely strict *user-space* ABI, held stable for decades
(`man 2 syscalls` from 1995 mostly still works). What it does not have is a stable *in-kernel* ABI between
subsystems and modules, which is the entire subject of this page.

**"`EXPORT_SYMBOL_GPL` is a licence check on your code."** No. It is a link-time check on your module's
*declared* `MODULE_LICENSE` string — a string you write yourself. It cannot verify that your source is
actually GPL-compatible; it only refuses to resolve the symbol for a module that didn't declare a
GPL-compatible license.

**"Modversions makes modules portable across kernel versions."** No — it makes an incompatibility
*detectable* at load time instead of silently corrupting memory at call time. That is closer to the
opposite of portability: it is precisely what stops an incompatible module from loading at all.

<KernelFacts
  structure={[["EXPORT_SYMBOL_GPL", "include/linux/export.h"], ["Module.symvers", "generated CRC table for exported symbols"]]}
  path="EXPORT_SYMBOL in kernel source → symbol table + CRC recorded at build time → checked when a module resolves the symbol at load → resolved or rejected"
  observe="modinfo <module.ko> | head"
  trap="'disagrees about version of symbol' is modversions working correctly. The module and the kernel have different ideas about a function's type, and loading it anyway would corrupt memory in a way no oops would explain." />

## References

- <Src file="include/linux/export.h" /> — the `EXPORT_SYMBOL`/`EXPORT_SYMBOL_GPL` macro definitions, shorter
  and clearer than any prose description of what they do.
- [Building external modules](https://docs.kernel.org/kbuild/modules.html) — symbol versioning,
  `Module.symvers`, and building against an installed kernel's headers.
- [Stable API nonsense](https://docs.kernel.org/process/stable-api-nonsense.html) — the kernel's own
  argument for why there is no stable in-kernel ABI, and the primary source for this page's "two audiences"
  framing.
