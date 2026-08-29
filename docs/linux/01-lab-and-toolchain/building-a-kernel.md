---
id: building-a-kernel
title: "Building a Kernel"
sidebar_label: "Building a kernel"
sidebar_position: 3
tags: [linux, kernel, lab]
prerequisites:
  - linux/lab-and-toolchain/getting-and-navigating-the-source
draft: false
---

# Building a Kernel

From defconfig to a bootable image, including the debug options that make the rest of this section's labs possible.

The build itself is not the interesting part — `make -j$(nproc)` is one command, and a machine with
enough cores finishes it before you've read this sentence twice. The interesting part is `.config`:
a plain text file that decides which of the kernel's roughly 20,000 `Kconfig` options are compiled
into the kernel you end up running. Almost every "why doesn't my system have X" question — a missing
filesystem, a driver that isn't there, a debugger that can't resolve a symbol — is a config question,
not a code question. Building a kernel once, deliberately, with a config you chose on purpose, makes
that concrete instead of theoretical.

## What a build produces

A single build run leaves several files behind, and they get confused constantly because they all
come from the same source tree and the same command. They are not interchangeable — each one has
exactly one job.

| Artefact | What it is | Used by |
|---|---|---|
| `vmlinux` | The uncompressed ELF kernel image, with full debug symbols if `CONFIG_DEBUG_INFO` is on. **Not bootable on its own.** | GDB (folder 01's next-but-one page) loads this |
| `arch/x86/boot/bzImage` | `vmlinux`, stripped and compressed, with a small real-mode boot stub prepended. **This is what actually boots.** | QEMU's `-kernel` flag, and every real bootloader |
| `vmlinuz` | A distribution's installed *name* for a `bzImage` — usually `/boot/vmlinuz-$(uname -r)`, copied there by `make install`. Same file, different name and location. | GRUB and friends, on an installed system |
| `System.map` | A plain-text symbol-to-address table for this exact build, generated alongside `vmlinux`. | Tools that need symbol lookups without loading the full ELF |
| `modules` (in `INSTALL_MOD_PATH`) | Every `CONFIG_*=m` piece, built as separate `.ko` files instead of linked into `vmlinux` | `insmod`/`modprobe` at runtime |

Approximate sizes from a real `defconfig` build on x86-64, debug info on, to put the two most-confused
artefacts side by side:

| File | Approximate size |
|---|---|
| `vmlinux` | 150–250 MB (uncompressed, full DWARF debug info) |
| `arch/x86/boot/bzImage` | 10–14 MB (stripped and compressed) |

Exact numbers depend on compiler version, config, and kernel version — treat these as "same order of
magnitude," not a spec.

:::note
`vmlinux` being ten to twenty times larger than `bzImage` is not a bug and not a compression failure —
it's almost entirely debug info that `bzImage` never carries. GDB needs that information; a booting
kernel does not.
:::

## Starting from a config

You never write a `.config` by hand from nothing. Kbuild ships several starting points, and which one
you pick trades completeness for speed:

- **`make defconfig`** — sane, complete x86-64 defaults. This is what most of this section's labs use:
  a config close to what a real distribution ships, minus distro-specific patches.
- **`make tinyconfig`** — the smallest kernel that will still boot. Most drivers, filesystems, and
  optional subsystems compiled out. Builds in well under five minutes on a modern machine, at the cost
  of a kernel that can do almost nothing beyond boot and run a shell — useful precisely because a lab
  kernel usually doesn't need to do more.
- **`make olddefconfig`** — takes an *existing* `.config` (from an older kernel version, or one you
  hand-edited) and fills in anything new with its default value, without prompting. This is how you
  carry a config forward across a version bump, or apply the `./scripts/config` edits below without
  Kconfig re-asking questions you've already answered.
- **Copying a running system's config** — most distributions ship the config their own kernel was built
  with, at `/boot/config-$(uname -r)` or compressed at `/proc/config.gz` if `CONFIG_IKCONFIG_PROC` is
  on. `zcat /proc/config.gz > .config` (or a plain copy of the `/boot/` file) gives you a config that
  matches hardware you already know works, as a starting point for `make olddefconfig`.

## The options that matter for a debuggable lab kernel

`defconfig` alone does not give you a kernel GDB can usefully attach to. These are the options this
section's labs assume are on, what each one buys you, and what it costs. Every symbol below was
checked against `lib/Kconfig.debug`, `lib/Kconfig.kasan`, and `init/Kconfig` at the pinned v6.18 tag.

| Symbol | Gives you | Cost |
|---|---|---|
| `CONFIG_DEBUG_INFO_DWARF_TOOLCHAIN_DEFAULT` | Selects `CONFIG_DEBUG_INFO` — `vmlinux` carries full DWARF debug symbols (`gcc -g`), which is what GDB needs to resolve a variable, a struct field, or a line number at all. | A much larger, slower-to-link `vmlinux`. No effect on `bzImage` size or boot behavior. |
| `CONFIG_GDB_SCRIPTS` | Generates the GDB helper scripts (`vmlinux-gdb.py` and friends) alongside the build, auto-loaded when you `gdb vmlinux` — the `lx-*` commands (`lx-dmesg`, `lx-ps`, task/struct walkers) this section's GDB page relies on. | None beyond `CONFIG_DEBUG_INFO` already being on; `depends on` chain requires it. |
| `CONFIG_KALLSYMS_ALL` | Keeps *every* symbol in `kallsyms`, not just function/text symbols. Without it, GDB and `/proc/kallsyms` can resolve function names but not most data symbols. | Slightly larger kernel image; negligible next to `DEBUG_INFO`. |
| `CONFIG_DEBUG_KERNEL` | The umbrella "I am developing/debugging the kernel" switch — several of the options above `depends on` it and stay hidden in `menuconfig` until it's on. | None by itself. |
| `CONFIG_DEBUG_INFO_REDUCED` — **leave off** | Would strip macro/typedef/variable debug info to shrink the build, trading away exactly the information a debugging lab exists to have. | Not a cost to pay — this is the one row in this table you turn *off*. |
| `CONFIG_KASAN` — **leave off by default** | Runtime memory-error detection: catches out-of-bounds and use-after-free the moment they happen, not later as a mystery crash. Genuinely useful — deliberately, on its own lab. | 1.5–3× slower kernel and noticeably larger image. Turn it on when you're hunting a memory bug, not as a default. |

The one-liners below apply every row except the two marked "leave off," directly against `.config`,
without opening `menuconfig` at all:

```text
$ ./scripts/config --enable CONFIG_DEBUG_KERNEL
$ ./scripts/config --enable CONFIG_DEBUG_INFO_DWARF_TOOLCHAIN_DEFAULT
$ ./scripts/config --enable CONFIG_GDB_SCRIPTS
$ ./scripts/config --enable CONFIG_KALLSYMS_ALL
$ ./scripts/config --disable CONFIG_DEBUG_INFO_REDUCED
$ make olddefconfig
```

`make olddefconfig` at the end is not optional — `./scripts/config` edits the file directly, and
`olddefconfig` is what resolves any options those edits now imply (or make unavailable) without
stopping to ask.

## `menuconfig` in practice

`make menuconfig` is the interactive alternative to hand-editing `.config` or scripting
`./scripts/config` calls — a curses UI over the same `Kconfig` tree. Three things make it usable rather
than a maze:

- **`/` searches.** Type `/` then a symbol name (with or without the `CONFIG_` prefix) and it lists
  every matching option, its location in the menu tree, its current value, and — critically — its
  `Depends on:` line.
- **The help text names the real symbol.** Every option's help screen (`?` or Enter on a highlighted
  item) starts by restating the exact `CONFIG_` name, so what you read in the UI and what you'd write
  in `.config` or a `./scripts/config` call are never in doubt.
- **`y`, `m`, `n` — and what `m` means.** `y` links the code into `vmlinux` permanently; `n` compiles it
  out entirely; `m` builds it as a separate loadable module (a `.ko` file) instead — present on the
  system, but not resident in the kernel image until something `insmod`s or `modprobe`s it.

:::tip
Search for `FRAME_POINTER` and read its `Depends on:` line: on x86-64 it depends on
`ARCH_WANT_FRAME_POINTERS`, which nothing selects by default — the arch's default unwinder is `ORC`, not
frame pointers. That line is the actual answer to "why won't this turn on": you're not missing a step,
the option genuinely isn't reachable until something upstream selects its dependency. On x86-64 that
means switching the kernel unwinder choice to `CONFIG_UNWINDER_FRAME_POINTER` first — a real trade
(~3% larger text, 5–10% slower) that this section's labs don't ask you to make, since `ORC` already
gives GDB everything it needs.
:::

## Running the build

```text
$ make -j$(nproc)
```

`-j$(nproc)` runs one compile job per CPU thread — the standard way to use every core you have. Realistic
wall-clock time on a modern 8-core machine: a couple of minutes for `tinyconfig`, ten to forty minutes
for a full `defconfig` build, depending on how many of those ~20,000 options ended up `y` rather than `n`.

To install any `CONFIG_*=m` modules into a staging tree instead of the live system — the right thing to
do for a lab kernel you don't want touching your host's `/lib/modules`:

```text
$ make modules_install INSTALL_MOD_PATH=~/kernel-lab/boot/modules
```

**When it fails**, the overwhelming majority of the time it is a missing host package, not a bug in your
config — `flex`, `bison`, and `libelf`/`libssl` headers are the three that come up most often, because
they're needed by Kconfig's own parser and by tools invoked partway through the build rather than by
the compiler itself. [The Lab Machine](./the-lab-machine.md#what-to-install) has the exact package list
per distribution.

## Rebuilding

Kbuild tracks dependencies per translation unit, down to which headers and which `CONFIG_*` values each
`.o` file actually used — which is why editing one `.c` file triggers a fast, single-file rebuild, but
flipping one `CONFIG_` symbol can trigger a much larger one: any file whose compiled output depends on
that symbol (an `#ifdef`, a different code path entirely) is now stale and gets rebuilt, sometimes half
the tree, even though you didn't touch a single line of source.

Three levels of "start clean," each throwing away more:

| Command | Removes |
|---|---|
| `make clean` | Most build products (`.o`, `.ko`, generated files) — keeps `.config` and the external module symbol table |
| `make mrproper` | Everything `clean` removes, plus `.config` itself and backups — this is "as if freshly checked out" |
| `make distclean` | Everything `mrproper` removes, plus editor backup files and patch leftovers — the deepest clean, rarely needed |

<Lab host="any-linux" title="Build a debuggable lab kernel" time="20–40 min">

1. From your kernel source tree, start from a full defconfig:

   ```text
   $ cd ~/kernel-lab/linux
   $ make defconfig
   ```

2. Apply the debug options from the table above:

   ```text
   $ ./scripts/config --enable CONFIG_DEBUG_KERNEL
   $ ./scripts/config --enable CONFIG_DEBUG_INFO_DWARF_TOOLCHAIN_DEFAULT
   $ ./scripts/config --enable CONFIG_GDB_SCRIPTS
   $ ./scripts/config --enable CONFIG_KALLSYMS_ALL
   $ ./scripts/config --disable CONFIG_DEBUG_INFO_REDUCED
   $ make olddefconfig
   ```

3. Build:

   ```text
   $ make -j$(nproc)
   ```

4. Confirm both artefacts exist and are the right shape:

   ```text
   $ ls -lh vmlinux arch/x86/boot/bzImage
   -rwxr-xr-x 1 you you 187M ... vmlinux
   -rw-r--r-- 1 you you  12M ... arch/x86/boot/bzImage

   $ file vmlinux
   vmlinux: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), statically linked,
   BuildID[sha1]=..., with debug_info, not stripped
   ```

   Sizes will differ from the ones shown — what matters is `file vmlinux` saying **`with debug_info,
   not stripped`**. If it says `stripped`, one of step 2's options didn't take; rerun `make olddefconfig`
   and check `.config` for `CONFIG_DEBUG_INFO=y`.

**If it fails:** a build that dies early, complaining about `flex`, `bison`, or a missing `libelf.h` /
`openssl/opensslv.h`, means a host package from [The Lab Machine](./the-lab-machine.md#what-to-install)
didn't land — reinstall from your distribution's tab there and rerun `make -j$(nproc)`; Kbuild resumes
from wherever it stopped.

</Lab>

<KernelFacts
  structure={[[".config", "the generated single source of truth for the build"], ["System.map", "symbol-to-address table for the built kernel"]]}
  path="make defconfig → .config → make -j → vmlinux → objcopy/compression → arch/x86/boot/bzImage"
  observe="ls -lh vmlinux arch/x86/boot/bzImage && file vmlinux"
  trap="`vmlinux` is not bootable and `bzImage` has no symbols. GDB needs the first, QEMU needs the second, and you need both from the *same* build or every breakpoint lands in the wrong place." />

## References

- [Kernel documentation — Kconfig language](https://docs.kernel.org/kbuild/kconfig.html)
  — what `menuconfig`, `defconfig`, `olddefconfig`, and the rest of the `make *config` targets actually
  do to `.config`, straight from the build system's own docs.
- [Kernel documentation — README (build instructions)](https://docs.kernel.org/admin-guide/README.html)
  — the kernel's own build instructions: short, authoritative, and the first place to check when a
  build behaves unexpectedly.
- [Kernel documentation — Kernel debugging with GDB](https://docs.kernel.org/dev-tools/gdb-kernel-debugging.html)
  — the exact config symbols the GDB helper scripts require; the reason this page turns them on before
  you ever attach a debugger.
