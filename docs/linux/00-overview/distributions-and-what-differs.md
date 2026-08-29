---
id: distributions-and-what-differs
title: "Distributions and What Actually Differs"
sidebar_label: "Distributions"
sidebar_position: 5
tags: [linux]
prerequisites:
  - linux/overview/what-linux-actually-is
draft: false
---

# Distributions and What Actually Differs

Same kernel, different packaging: what genuinely varies between distributions and the much longer list of things that do not.

The interesting question about distributions is not what they differ on — that list is short and
mostly cosmetic. It is the far longer list of what they *cannot* differ on, because every distribution
ships the same kernel interface: the same syscalls, the same `/proc`, the same ELF format. That
constancy is not an accident of convention; it is why a statically linked binary built on any one
distribution runs, unmodified, on every other one. Anything that varies has to vary somewhere other
than the kernel interface — and finding where is what this page is about.

## What genuinely differs

| | Debian | Fedora | Arch | Alpine | Android |
|---|---|---|---|---|---|
| Init system | systemd | systemd | systemd | OpenRC | Android `init` (its own `init.rc` language, not systemd) |
| C library | glibc | glibc | glibc | musl | Bionic |
| Package manager | APT / dpkg | DNF / RPM | pacman | apk | Package Manager Service (APK files, no general-purpose package manager) |
| Kernel config & patch set | Debian's own `.config` + conservative patch set | Fedora's own `.config`, tracks upstream closely | Arch's own `.config`, minimal patching | Alpine's own `.config`, hardening-leaning | Vendor/OEM `.config` + vendor patches, often heavily forked |
| Default filesystem | ext4 | Btrfs | ext4 (installer default; user-chosen) | ext4 | ext4 or F2FS, device-dependent |
| Security module | AppArmor | SELinux (enforcing by default) | None by default | None by default | SELinux (mandatory, enforcing since Android 9) |
| Release model | Fixed release (stable/testing/unstable) | Fixed release, ~6 months | Rolling release | Fixed release, ~6 months, plus a rolling `edge` branch | Tied to AOSP + vendor image releases, OEM-controlled |

*What five representative Linux distributions actually vary: packaging, defaults, and policy —
never the kernel interface itself.*

## The kernel config is the biggest real difference

Every distribution in that table builds from the same upstream source, but not the same `.config`.
A feature that is compiled out of a kernel is not merely disabled by default — it is genuinely absent:
no code for it exists in the running kernel image, and no runtime setting brings it back. This is a
bigger source of real behavioral difference between distributions than any userland tool, because it
determines which subsystems, filesystems, and security features can possibly exist on that machine at
all. It is also the reason two people running "the same kernel version" from two different
distributions can observe genuinely different capabilities. How a `Kconfig` symbol becomes a compiled
object — and how to read a kernel's actual configuration back out — is covered in
[Kconfig and Kbuild](../04-kernel-architecture-and-idioms/kconfig-and-kbuild.md); the running kernel's
own config is queryable directly:

```text
$ zcat /proc/config.gz | grep CONFIG_IKCONFIG
CONFIG_IKCONFIG=y
CONFIG_IKCONFIG_PROC=y
```

That `/proc/config.gz` file only exists when the kernel was built with
<Src file="kernel/configs.c" symbol="CONFIG_IKCONFIG_PROC" /> — it is itself a config option, and a
distribution that omits it makes its own kernel's configuration unqueryable from the running system.

## libc is the second

The C library is the second-biggest real difference, and the one most often blamed on the wrong layer.
glibc and musl both implement the C standard library and the userland side of the syscall ABI, but they
are not interchangeable at the binary level: a binary dynamically linked against glibc does not run on
Alpine without extra work, because Alpine ships musl and no glibc-compatible dynamic loader. People
routinely describe this as "Alpine's kernel doesn't support X" — it is not a kernel problem at all.
The kernel underneath both distributions accepts the identical set of syscalls; the failure happens
entirely in userland, when the dynamic loader can't find symbols the binary expects.

## What does not differ

This is the section that makes the rest of the page worth reading, because it is the longer list:

- **Syscall numbers and semantics** — the same syscall number means the same operation, with the same
  arguments and the same error codes, on every distribution running the same architecture.
- **`/proc` and `/sys` layout** — both are kernel-generated, not distribution-generated; their
  structure comes from the kernel's own code, not a distribution's packaging choices.
- **The ELF ABI** — the executable and shared-library format, and how the dynamic loader resolves
  symbols, is a kernel-and-toolchain contract, not a distribution one.
- **Signal semantics** — signal numbers, default dispositions, and delivery semantics are kernel
  behavior, identical everywhere.
- **The VFS interface** — the system calls a userland program uses to interact with any filesystem are
  the same regardless of which filesystem a distribution defaults to.
- **Page size and address-space layout**, on the same architecture — these come from the kernel and the
  hardware it runs on, not from packaging decisions.

## What actually happens

"The package manager installed a kernel" hides a sequence that is worth having in mind, because the
last step of it is the one people forget:

1. The package unpacks a compressed kernel image and a matching tree of modules to
   `/boot` and `/lib/modules/$(uname -r)`.
2. `depmod` runs, rebuilding the module dependency index against the newly installed module tree.
3. An initramfs is generated fresh, against *this specific machine's* hardware and installed modules —
   not shipped pre-built, because a generic one couldn't know in advance which storage controller or
   filesystem driver this machine's boot needs.
4. A boot-loader entry is added pointing at the new kernel, and the previous kernel is normally left
   installed as a fallback rather than removed.

None of that changes what is actually running. The kernel currently executing is whatever was loaded
at the last boot, and it stays that way regardless of what a package manager just wrote to `/boot` —
which is exactly why `uname -r` can disagree with the newest kernel sitting in `/boot`: the update took
effect on disk, not in memory, and nothing takes effect in memory until the next reboot.

## Android is Linux

The one distribution that surprises people the most: Android runs the Linux kernel, full stop — the
same kernel this section is about, with vendor and Android-specific patches layered on top. But it
carries almost none of the userland most people associate with "Linux." There is no GNU userland: the
C library is Bionic, not glibc. There is no systemd, or any conventional Linux init system — Android's
`init` process reads its own `init.rc` configuration language and has no relationship to the init
systems in the table above. There is no general-purpose package manager in the APT/DNF/pacman sense;
applications install as signed APK bundles through the Package Manager Service. And its security model
goes further than any desktop distribution's default: SELinux has been mandatory and enforcing since
Android 9, applied per-app through a much more granular policy than a typical Linux desktop uses. Same
kernel; almost nothing else in common with Debian.

## Misconceptions

1. **"Distributions ship different kernels."** They ship different *configurations and patch sets* of
   the same upstream kernel, not different kernels in any architectural sense. The syscall interface,
   the VFS, and the rest of the mechanism described in this section are the same code everywhere.
2. **"Alpine is small because its kernel is small."** Alpine's install footprint is small because of
   its userland choices — musl instead of glibc, BusyBox instead of GNU coreutils — not because its
   kernel is a stripped-down or different kernel. The kernel itself is ordinary upstream Linux with
   Alpine's own config.
3. **"The distribution decides how memory management works."** A distribution decides *defaults* — the
   `sysctl` values a fresh install ships with, things like swappiness or overcommit policy — not the
   underlying mechanism. The memory-management code itself is the same kernel code, unaffected by which
   distribution is running it.

<KernelFacts
  structure={[["/proc/config.gz", "kernel/configs.c (CONFIG_IKCONFIG_PROC)"]]}
  path="distribution package → /boot/vmlinuz-$VER + /lib/modules/$VER → depmod → initramfs generation → boot-loader entry"
  observe="ls /boot && ls /lib/modules && uname -r"
  trap="The newest kernel in `/boot` is not the running kernel. Nothing about a kernel install takes effect until the next boot, and `kexec` is the only exception." />

## References

- [Alpine Wiki — Comparison with other distros](https://wiki.alpinelinux.org/wiki/Comparison_with_other_distros)
  — a concrete, honest account of what changing libc and userland actually breaks, from the distribution
  that changes both.
- [The Linux kernel user's and administrator's guide — README](https://docs.kernel.org/admin-guide/README.html)
  — what a plain kernel build actually produces, which is exactly what a distribution's package then
  wraps and installs.
- [Android Open Source Project — Kernel architecture](https://source.android.com/docs/core/architecture/kernel)
  — how far a vendor kernel can diverge from upstream while still being Linux underneath.
