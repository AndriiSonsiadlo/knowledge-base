---
id: initramfs-and-early-userspace
title: "initramfs and Early User Space"
sidebar_label: "initramfs"
sidebar_position: 9
tags: [linux, kernel, boot]
prerequisites:
  - linux/boot-and-init/start-kernel-and-initcalls
draft: false
---

# initramfs and Early User Space

Why a root filesystem needs a root filesystem, and how the chicken-and-egg is broken.

To mount the real root filesystem you need a driver for whatever controller it's attached to — a NVMe
queue, a SATA AHCI controller, an encrypted LVM stack — and on many systems that driver is a module that
itself lives *on* the root filesystem you can't mount yet. The kernel breaks this circularity with a tiny
filesystem it already has in memory before any disk is touched at all: the initramfs.

## rootfs, ramfs, initramfs — three words, one mechanism

These three names get used interchangeably, and collapsing them loses the detail that makes the rest of
this page make sense:

- **rootfs** is a `tmpfs`-family instance the kernel always creates during boot, mounted at `/` before
  anything else exists to mount there. Every kernel has one, whether or not it's ever handed a cpio
  archive to unpack into it.
- **ramfs** is the underlying mechanism: a filesystem that stores everything directly in page cache, with
  no backing block device at all. `tmpfs` (rootfs's actual implementation) adds size limits and swap
  support on top of the same idea.
- **initramfs** is a cpio archive — the *contents* the kernel unpacks into rootfs, not a filesystem type
  of its own.

The detail worth sitting with: there is no block device and no filesystem image involved in any of this.
"Mounting the initramfs" is really "unpacking a cpio archive's files directly into an already-mounted
in-memory filesystem." Nothing is mounted from the initrd; the initrd's *contents* are copied in.

## The cpio format

The archive format is `cpio`'s `newc` variant — not `tar`, and the reason is almost entirely historical
simplicity: `newc` headers are fixed-size ASCII hex fields with no alignment padding tricks or
GNU/POSIX-tar-variant ambiguity to handle, which keeps the kernel's own unpacker small and dependency-free.
The kernel's unpacker, <Src file="init/initramfs.c" symbol="do_populate_rootfs" />, is deliberately
minimal — it understands exactly enough of `newc` to place files, directories, device nodes, and symlinks
into rootfs, and nothing more; it is not a general-purpose archive tool.

## What `/init` in a distribution's initramfs actually does

The kernel's job ends once the archive is unpacked and `/init` inside it is running as PID 1. Everything
after that is ordinary (if minimal) user-space code, and on a real distribution it does, in rough order:

1. Load kernel modules for whatever storage controller the root filesystem needs, and for networking too
   if root is reached over the network.
2. Assemble any layered storage the root sits on top of — software RAID (`md`), LVM volume groups, or an
   encrypted volume (LUKS) that needs a passphrase or key before it can be opened.
3. Resolve `root=` from the kernel command line — which may name a device directly, a UUID, or an LVM
   logical volume — to an actual block device node.
4. Mount that device as the real root, conventionally at `/sysroot`.
5. Hand over via `switch_root` — the mechanics of that handoff, and of PID 1 continuing on the other side
   of it, belong to a later part of this section.

None of this is kernel behaviour — it's policy encoded in a shell script and a handful of binaries that
happen to ship inside the cpio archive.

## How yours is generated

No two distributions build their initramfs the same way, though all of them produce the same kind of
artefact:

| Distribution family | Generator | Config |
|---|---|---|
| Fedora / RHEL | `dracut` | `/etc/dracut.conf`, `/etc/dracut.conf.d/*.conf` |
| Arch | `mkinitcpio` | `/etc/mkinitcpio.conf` |
| Debian / Ubuntu | `initramfs-tools` (`update-initramfs`) | `/etc/initramfs-tools/initramfs.conf` |

The more consequential distinction is not which tool but which **mode** it ran in:

- A **host-only** (or "host-specific") image includes drivers only for hardware the generator detected
  on the machine it ran on. It's smaller and faster to build, and it is the default on most
  installations — because most installations never move their disk to different hardware.
- A **generic** image includes a much broader set of storage and filesystem drivers, so it boots on
  hardware the generator never saw. It's what installer media ships with, and what you'd want if you
  plan to move a disk between machines.

An initramfs generated in host-only mode on one machine can fail to boot the exact same installed
distribution on different hardware — not because anything is corrupt, but because the driver the new
hardware needs was never included in the first place.

## Opening one up

Modern installed images are frequently not a single compressed cpio archive but a **concatenation**: an
uncompressed early-microcode cpio segment (for early CPU microcode loading, which has to happen before
the main archive is even parsed) followed by the real, compressed main archive. A bare `zcat` or `cpio
-idv` run against the whole file can silently only see the first segment, which is why the
distribution-provided tools — `lsinitrd` (dracut-based systems) and `lsinitramfs`
(`initramfs-tools`-based systems) — are the right way to inspect one: they already know about the
microcode-plus-archive layout and unpack accordingly, instead of assuming one cpio stream.

## What actually happens

**"The initramfs boots the system."** It doesn't — it prepares the conditions under which the real root
can be mounted, and then it is discarded entirely. Its whole reason to exist is the module list it
carries; everything else in it exists to load and use those modules.

```text
$ lsinitrd | head -20
Version: dracut-060+1-1.fc41
Arguments: --no-hostonly --no-hostonly-cmdline
dracut modules:
bash
systemd
systemd-initrd
i18n
...
====================
/init -> usr/lib/systemd/systemd
drwxr-xr-x   1 root     root            0 Jan  1  1970 .
drwxr-xr-x   1 root     root            0 Jan  1  1970 dev
drwxr-xr-x   1 root     root            0 Jan  1  1970 etc
lrwxr-xr-x   1 root     root            0 Jan  1  1970 usr/lib/modules/6.18.0/kernel/drivers/nvme
...
```

The `lrwxr-xr-x`/directory entries under `usr/lib/modules/.../kernel/drivers/` are the point of the whole
exercise — the exact set of drivers this image decided the machine needs before it can reach the real
root. Once `switch_root` runs, the memory this cpio was unpacked into is reclaimed — an initramfs that
"boots the system" would have no reason to ever be freed.

```mermaid
flowchart LR
    A["cpio archive<br/>in memory, loaded by the loader/-initrd"] -->|"do_populate_rootfs() unpacks"| B["rootfs (tmpfs)<br/>files placed, no block device"]
    B -->|"kernel execs"| C["/init runs<br/>loads storage/network modules"]
    C -->|"assembles md/LVM/LUKS, resolves root=, mounts"| D["Real root<br/>mounted at /sysroot"]
    D -->|"switch_root"| E["Real init<br/>PID 1 continues as /sbin/init"]
    E -->|"initramfs memory freed"| F["Reclaimed"]
```

*The initramfs's whole life, from a cpio in RAM to the memory being reclaimed.*

## When it goes wrong

When `/init` cannot find or mount the real root, most initramfs implementations drop to an **emergency
shell** rather than panicking silently — a minimal prompt running inside the still-unpacked initramfs,
with none of the real system mounted. Two commands are worth running there before anything else:

- `cat /proc/cmdline` — confirms what `root=` (and everything else) the kernel actually received; a typo
  or a stale `root=` after a disk was replaced is one of the most common reasons to land here at all.
- `blkid` — lists every block device the kernel can currently see along with its filesystem type and
  UUID, which is the fastest way to check whether the UUID `root=` names still exists on this machine.

<Lab host="any-linux" title="Look inside your distribution's initramfs" time="10 min">

On Fedora/RHEL:

```text
$ lsinitrd /boot/initramfs-$(uname -r).img | head -40
```

On Debian/Ubuntu:

```text
$ lsinitramfs /boot/initrd.img-$(uname -r) | head -40
```

Expect `/init` (or a symlink to it) near the top of the listing, and a
`usr/lib/modules/.../kernel/drivers/` tree further down. Then compare the module count the image carries
against what's actually loaded on the running system:

```text
$ lsinitrd /boot/initramfs-$(uname -r).img | grep -c '\.ko'
$ lsmod | wc -l
```

The two numbers won't match — the initramfs carries every driver it *might* need at early boot, not only
the ones this particular boot used.

**If it fails:** on a machine with no `/boot` directory at all — a WSL2 install is the clearest example —
there is no distribution-generated initramfs to inspect, because WSL2 boots through Microsoft's own Linux
kernel and init path rather than a normal distribution boot chain. That gap is itself the point: it's the
same "not every capability exists on every host" lesson the lab-machine capability table already made.

</Lab>

<KernelFacts
  structure={[["populate_rootfs()", "init/initramfs.c"], ["do_populate_rootfs()", "init/initramfs.c"]]}
  path="kernel unpacks cpio into rootfs (do_populate_rootfs, via a rootfs_initcall) → runs /init → modules loaded → real root mounted → switch_root"
  observe="lsinitrd (dracut) or lsinitramfs (initramfs-tools) on your own image"
  trap="An initramfs built on your machine is often built *for* your machine. A host-only image is small but can fail to boot the same distribution on different hardware; a generic image boots anywhere and is larger." />

## References

- [`Documentation/filesystems/ramfs-rootfs-initramfs.rst`](https://docs.kernel.org/filesystems/ramfs-rootfs-initramfs.html) —
  the kernel's own three-way distinction between rootfs, ramfs, and initramfs that this page's first
  section follows directly.
- `man 8 dracut` and `man 8 mkinitcpio` — the two generators most readers actually have installed, and
  where their host-only-versus-generic build modes are documented in full.
- [`Documentation/driver-api/early-userspace/early_userspace_support.rst`](https://docs.kernel.org/driver-api/early-userspace/early_userspace_support.html) —
  the cpio contract the kernel's unpacker enforces, for anyone building a custom initramfs by hand.
