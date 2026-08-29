---
id: a-minimal-rootfs
title: "A Minimal Root Filesystem"
sidebar_label: "A minimal rootfs"
sidebar_position: 4
tags: [linux, kernel, lab]
prerequisites:
  - linux/lab-and-toolchain/building-a-kernel
draft: false
---

# A Minimal Root Filesystem

A static BusyBox, a directory skeleton, and an /init packed into an initramfs — early user space made concrete instead of magical.

A kernel that boots with no root filesystem panics — it has a CPU, memory, and a scheduler, and
nothing to run. Every distribution hides how thin the contract actually is behind `dracut`, `systemd`,
and hundreds of megabytes of tooling, so it's easy to end up believing early user space is inherently
complicated. It isn't. Building the smallest possible userland by hand — one static binary, a handful
of empty directories, and a ten-line shell script — takes about twenty minutes and permanently removes
the magic: `/init` is just a program the kernel happens to run first, and PID 1 is just whichever
process that program becomes.

## What the kernel needs

The contract is small enough to state in full. An **initramfs** is a `cpio` archive, optionally
gzip-compressed, that the kernel unpacks directly into an in-memory `tmpfs` mounted as `/` — before any
real block device, filesystem driver, or disk has been touched. Once unpacking finishes, the kernel
looks for one file, `/init`, and executes it as PID 1. <Src file="init/initramfs.c" symbol="unpack_to_rootfs" />
is the function that does the unpacking; <Src file="init/main.c" symbol="kernel_init" /> is what runs
afterward and, through <Src file="init/main.c" symbol="run_init_process" />, `exec`s whatever `/init`
turns out to be. That's the entire contract — no filesystem type detection, no hardware probing, no
service manager. Everything past this point is userland choosing to do more with it.

## BusyBox, statically linked

A normal Linux binary is dynamically linked: it lists the shared libraries it needs, and the kernel's
`ELF` loader hands off to a dynamic linker (`ld.so`) to find and map them before `main()` runs. That
dynamic linker has to exist somewhere the new root filesystem can find it — which means installing a
working libc into an initramfs that currently has nothing. **BusyBox built statically** sidesteps the
entire problem: one self-contained ELF binary, every applet (`sh`, `ls`, `mount`, `mkdir`, `cat`, and
dozens more) linked directly into it, nothing to install, nothing for the loader to fail to find.

```text
$ cd ~/kernel-lab
$ curl -LO https://busybox.net/downloads/busybox-1.36.1.tar.bz2
$ tar xf busybox-1.36.1.tar.bz2 && cd busybox-1.36.1
$ make defconfig
$ ./scripts/config --enable CONFIG_STATIC
$ make -j$(nproc)
$ make install CONFIG_PREFIX=~/kernel-lab/initramfs
```

`make install` populates `~/kernel-lab/initramfs/bin/busybox` and symlinks every enabled applet
(`~/kernel-lab/initramfs/bin/sh`, `.../ls`, and so on) back to that one binary — BusyBox inspects
`argv[0]` at runtime to decide which applet it's being invoked as.

## The directory skeleton

Nothing creates these for you — a bare initramfs is not a partial Linux install, it's an empty `tmpfs`
plus whatever you packed into the archive. The minimum skeleton a shell needs to do anything useful:

```text
$ cd ~/kernel-lab/initramfs
$ mkdir -p bin sbin etc proc sys dev usr/bin usr/sbin
```

`proc`, `sys`, and `dev` matter for a specific reason: they must exist as **empty directories in the
archive itself**, because a mount point has to already exist before anything can be mounted onto it.
The kernel doesn't create mount points on demand — `mount -t proc none /proc` fails outright if `/proc`
isn't there first. `bin`, `sbin`, and the `usr/` equivalents just need to exist for BusyBox's installed
symlinks to land somewhere.

## Writing `/init`

`/init` is not a special file format or a kernel-recognized binary — it is any executable at that exact
path, and the simplest version is just a shell script that mounts the three pseudo-filesystems every
later lab in this section assumes are present, then hands control to an interactive shell:

```bash
#!/bin/sh
mount -t proc none /proc
mount -t sysfs none /sys
mount -t devtmpfs none /dev

echo "[initramfs] mounted proc, sysfs, devtmpfs — dropping to shell"

exec /bin/sh
```

Two details break this in ways that look nothing like their actual cause. First, `/init` must be
**executable** — `chmod +x init` — or the kernel's attempt to run it fails and produces a kernel panic
that reads like the kernel itself is broken, not like a file permission problem. Second, `exec /bin/sh`
at the end, not a plain `/bin/sh`: `exec` replaces PID 1 with the shell instead of spawning a child of
it, and PID 1 exiting is a fatal, unrecoverable event in Linux's process model — plain `/bin/sh` would
leave the script itself as PID 1, and the moment that script ends, so does the entire machine.

## Packing it

```text
$ cd ~/kernel-lab/initramfs
$ find . | cpio -H newc -o | gzip > ../initramfs.cpio.gz
```

Each piece does one job: `find .` lists every file and directory in the tree, in an order `cpio` can
walk; `cpio -H newc -o` reads that file list on stdin and writes a `newc`-format archive to stdout —
`newc` is the portable, kernel-supported `cpio` variant, as opposed to the older binary or POSIX `ustar`
formats the kernel's initramfs unpacker doesn't accept; and `gzip` compresses the result, which the
kernel decompresses transparently on unpack. The output — `~/kernel-lab/initramfs.cpio.gz` — is the
exact artefact [Booting Your Kernel in QEMU](./booting-your-kernel-in-qemu.md)'s `-initrd` flag takes by name.

## What you have just built

This is not a simplified stand-in for what a real distribution does at boot — it is the same mechanism,
with the hardware-detection layer removed. `dracut` (Fedora/RHEL) and `mkinitcpio` (Arch) both produce a
`cpio` archive that a kernel unpacks into a `tmpfs` and executes `/init` from, exactly as above; the
difference is that their generated `/init` (often a small script that then hands off to `systemd` as
PID 1) spends most of its logic probing for the real root device, loading the right disk and filesystem
drivers, and only then switching over to it — none of which this lab's fixed, known VM needs. Folder
03's initramfs page covers that real-world version, including the root-device handoff this one skips
entirely.

```mermaid
flowchart LR
    A["initramfs.cpio.gz"] --> B["kernel unpacks into rootfs (tmpfs)"]
    B --> C["kernel executes /init"]
    C --> D["/init mounts proc, sysfs, devtmpfs"]
    D --> E["exec /bin/sh"]
```

*From a cpio archive to a shell prompt, which is everything early user space does.*

<Lab host="any-linux" title="Build a BusyBox initramfs" time="20 min">

1. Build static BusyBox and stage it:

   ```text
   $ cd ~/kernel-lab
   $ curl -LO https://busybox.net/downloads/busybox-1.36.1.tar.bz2
   $ tar xf busybox-1.36.1.tar.bz2 && cd busybox-1.36.1
   $ make defconfig
   $ ./scripts/config --enable CONFIG_STATIC
   $ make -j$(nproc)
   $ make install CONFIG_PREFIX=~/kernel-lab/initramfs
   ```

2. Build the directory skeleton:

   ```text
   $ cd ~/kernel-lab/initramfs
   $ mkdir -p proc sys dev
   ```

3. Write `/init` (the script from above) and make it executable:

   ```text
   $ chmod +x init
   ```

4. Pack it:

   ```text
   $ find . | cpio -H newc -o | gzip > ../initramfs.cpio.gz
   6474 blocks
   ```

   Expect a line like `NNNNN blocks` on stderr — the block count `cpio` reports for what it just wrote.
   The exact number depends on which BusyBox applets you enabled.

5. Confirm the archive:

   ```text
   $ ls -lh ~/kernel-lab/initramfs.cpio.gz
   -rw-r--r-- 1 you you 1.8M ... initramfs.cpio.gz
   ```

   A few megabytes is normal for a `defconfig`-built static BusyBox; an archive under a few hundred
   kilobytes usually means `CONFIG_STATIC` didn't take and you packed a dynamically linked binary instead.

**If it fails:** a boot that reaches `Run /init as init process` and then immediately panics with
`/init: not found`, even though the file is clearly there, means BusyBox is dynamically linked — the
kernel can find `/init`, but `/init` itself can't find its linker, since this rootfs has none installed.
Rerun BusyBox's build with `CONFIG_STATIC=y` confirmed (`./scripts/config --state CONFIG_STATIC`) and
verify with `file bin/busybox`, which should say `statically linked`, not `dynamically linked`.

</Lab>

<KernelFacts
  structure={[["initramfs.cpio.gz", "a cpio newc archive, gzip-compressed"], ["/init", "the first user-space program the kernel executes"]]}
  path="kernel unpacks cpio into rootfs (tmpfs) → executes /init → /init execs a shell"
  observe="zcat initramfs.cpio.gz | cpio -t | head"
  trap="`/init` missing, not executable, or dynamically linked all produce the same kernel panic. The panic says the kernel could not run init; it does not say which of the three is wrong." />

## References

- [Kernel documentation — ramfs, rootfs, and initramfs](https://docs.kernel.org/filesystems/ramfs-rootfs-initramfs.html)
  — the kernel's own explanation of the three layers, and the distinction ("rootfs is a ramfs mount that
  can never be unmounted") readers most often get wrong.
- [BusyBox — downloads and applet list](https://www.busybox.net/downloads/BusyBox.html)
  — what a single BusyBox binary can actually do; worth a skim before assuming an applet you want is
  (or isn't) included.
- [Kernel documentation — early userspace support](https://docs.kernel.org/driver-api/early-userspace/early_userspace_support.html)
  — the `cpio` format contract the kernel's initramfs unpacker enforces, straight from the source.
