---
id: the-lab-machine
title: "The Lab Machine"
sidebar_label: "The lab machine"
sidebar_position: 1
tags: [linux, kernel, lab]
prerequisites: []
draft: false
---

# The Lab Machine

Why QEMU is the spine of every lab here, what to install on the host, and what each lab host badge means.

Every hands-on exercise in this section runs inside a virtual machine, never on your laptop directly,
and that is not caution for its own sake. A kernel panic in a VM costs you a QEMU process you can
restart in seconds; a kernel panic on bare metal costs you a reboot, and sometimes a filesystem check.
A VM lets you attach a debugger to the CPU itself and single-step kernel code the way you would
single-step a userspace program — something no amount of `printk` gets you on real hardware without a
serial cable and a second machine. And a VM lets you pin the exact kernel version you are running, which
is the whole reason a claim on this page or any later one is checkable rather than merely believable:
every `<Src>` link, every command's expected output, every walk through kernel code assumes the same
pinned tag you built yourself, not whatever your distribution happened to ship.

## What the lab is

For most of this section, "the lab" means one thing: a QEMU/x86-64 virtual machine, booting a kernel
you built from source, with a minimal BusyBox initramfs as its root filesystem. That combination is
small, fast to boot, and disposable — you can break it on purpose, dozens of times a day, and rebuild
it in seconds. It is enough to watch scheduling, memory management, and syscall handling happen for
real, because those mechanisms don't care whether `/sbin/init` is BusyBox or systemd.

It is not enough for everything. Some later labs need systemd, a real block device and filesystem, or
a working network stack — things a BusyBox initramfs deliberately does not have. For those, folder 01
also covers a full-system VM built from a Debian cloud image, which trades the initramfs lab's speed
for a machine that behaves like a real installed distribution. Which one a given lab needs is called
out at the top of that lab, not left for you to guess.

## The host badges

Every `<Lab>` in this section carries a host badge, and the badge is a promise about what the lab
needs before you start — never something you discover four steps in. This table is the reference for
the whole section; later folders link back to it instead of re-explaining the badges.

| Badge | Promises |
|---|---|
| `qemu` | Runs inside this section's QEMU/x86-64 VM, booting a kernel you built. Nothing on your host is touched beyond the VM process itself. |
| `qemu-gdb` | The same QEMU VM, plus a live GDB session attached to the guest kernel over QEMU's `-s -S` stub. Needs everything `qemu` needs, plus `gdb`. |
| `any-linux` | Runs directly on your host shell — cloning, building, `git grep`, reading files. No VM, no `root`, works the same on a bare-metal Linux box or inside WSL2. |
| `wsl2-ok` | Verified to also work, unmodified, inside WSL2. A narrower claim than `any-linux`: some `qemu`/`qemu-gdb` labs additionally earn this badge once nested virtualization is confirmed working; most do not. |
| `root-required` | Needs `root`/`sudo` on the host itself — not inside a disposable guest. Used sparingly, and never casually. |

:::warning
A lab marked `:::danger` never carries the `any-linux` badge. Irreversible, host-level damage and "runs
directly on your shell with no isolation" is a combination this section refuses to ship.
:::

## What to install

Install the same toolchain regardless of which distribution you develop on — building a kernel and
running QEMU need the same handful of packages everywhere, only the package manager and exact names
change. Pick your host.

<Tabs>
<TabItem value="debian" label="Debian / Ubuntu" default>

```text
sudo apt update
sudo apt install -y build-essential flex bison libelf-dev libssl-dev bc \
  libncurses-dev qemu-system-x86 gdb cpio git
```

</TabItem>
<TabItem value="fedora" label="Fedora">

```text
sudo dnf install -y gcc make flex bison elfutils-libelf-devel openssl-devel bc \
  ncurses-devel qemu-system-x86 gdb cpio git
```

</TabItem>
<TabItem value="arch" label="Arch">

```text
sudo pacman -S --needed base-devel flex bison libelf openssl bc ncurses \
  qemu-desktop gdb cpio git
```

</TabItem>
<TabItem value="wsl2" label="WSL2 (Ubuntu)">

```text
sudo apt update
sudo apt install -y build-essential flex bison libelf-dev libssl-dev bc \
  libncurses-dev qemu-system-x86 gdb cpio git
```

Identical to the Debian/Ubuntu tab — WSL2's Ubuntu userland takes the same packages. What differs is
whether `/dev/kvm` shows up at all; see [KVM, and when you cannot have it](#kvm-and-when-you-cannot-have-it) below.

</TabItem>
</Tabs>

:::note
Package names drift between distribution releases, most often around the OpenSSL and `ncurses`
development packages. If a package above 404s on your system, search your distribution's package
index for the `-dev`/`-devel` package that ships `libelf.h`, `openssl/opensslv.h`, or `ncurses.h` —
the kernel build only cares that the headers exist, not what the package happens to be called this year.
:::

## The directory convention

Every lab in this section — not just this folder's — assumes one fixed layout on your host:

```text
~/kernel-lab/
├── linux/               # the kernel source tree (Getting the Source, next page)
│   └── arch/x86/boot/bzImage   # built in place — never moved out of the tree
├── initramfs/           # the BusyBox rootfs tree you build and pack
├── initramfs.cpio.gz    # the packed initramfs, written one level up from initramfs/
└── boot/
    └── modules/         # `make modules_install` output
```

Commands throughout this section are written assuming you `cd ~/kernel-lab/linux` before running them,
that a built kernel stays where the build leaves it (`arch/x86/boot/bzImage`, in-tree), and that the
packed initramfs lands one directory up, at `~/kernel-lab/initramfs.cpio.gz`. Using a different path
works fine — this is a convention, not a requirement the tooling enforces — but every copy-pasted
command in a later lab assumes this one, so deviating means translating every path by hand.

## Disk, memory, and time budget

The single biggest reason people abandon a hands-on kernel exercise is that the cost was a surprise
partway through. It isn't small, and it's worth knowing up front.

| Item | Cost |
|---|---|
| Source checkout, full clone | ~5 GB, with full history |
| Source checkout, shallow clone (`--depth 1`) | ~1.5 GB, no history |
| A full `defconfig`-class build | ~20–30 GB of build output, 10–40 minutes on 8 cores |
| A `tinyconfig`-based lab kernel | A few hundred MB and well under 5 minutes on the same machine |
| RAM to build comfortably | 8 GB minimum; the linker and `LTO`-enabled builds want more |
| RAM to run the QEMU lab VM | 512 MB–1 GB is plenty for the BusyBox initramfs lab |

The gap between a `tinyconfig` build and a `defconfig` build is not a rounding error — it is most
driver code, most filesystems, and most of the kernel's optional subsystems, all compiled out. Labs in
this section default to the smallest config that exercises what they're teaching, precisely to keep
that 10–40 minute number from being the common case.

## KVM, and when you cannot have it

`-enable-kvm` is the single QEMU flag that decides whether your guest kernel runs on real hardware
virtualization or is fully emulated in software, and the difference is roughly an order of magnitude.
It needs two things to be true: `/dev/kvm` must exist and be accessible, and the host CPU must have
virtualization extensions enabled (`Intel VT-x` or `AMD-V`, usually a BIOS/UEFI setting, occasionally
disabled by a hypervisor underneath you).

Three situations are worth knowing in advance:

- **Bare-metal Linux, virtualization enabled in firmware.** The common case. `/dev/kvm` exists,
  `-enable-kvm` works, and the lab VM is fast.
- **Inside a cloud VM or another hypervisor.** Nested virtualization is frequently disabled by the
  outer hypervisor, even when the underlying physical CPU supports it — a cloud instance you did not
  provision specifically for nested virt very often has no `/dev/kvm` at all.
- **WSL2.** Recent Windows builds expose `/dev/kvm` inside WSL2 when the host CPU and Windows's own
  Hyper-V layer both support nested virtualization; older builds do not expose it at all. Check, don't
  assume.

Without KVM, everything in this section still works — QEMU falls back to its software emulator (TCG)
— just roughly 5–10× slower. That is a real cost for a full-system VM boot, and a barely noticeable one
for the small `tinyconfig` lab kernel this folder mostly uses. Missing `/dev/kvm` is a slowdown, not a
blocker; nothing in this section requires it.

## What runs where

A quick map of this folder's labs to what they need, so a WSL2-only or KVM-less reader knows
immediately what they can run today without reading every page first.

| Page | Lab host | Needs |
|---|---|---|
| The Lab Machine (this page) | `any-linux` | Just a shell and the packages above |
| Getting the Source | `any-linux` | A shell, `git`, network access to `git.kernel.org` or GitHub |
| Building a Kernel | `any-linux` | The toolchain above; no VM yet |
| A Minimal Root Filesystem | `any-linux` | BusyBox and `cpio`; no VM yet |
| Booting Your Kernel in QEMU | `qemu` | Everything above, plus a working `qemu-system-x86_64` |
| Debugging the Kernel with GDB | `qemu-gdb` | Everything `qemu` needs, plus `gdb` |
| A Full-System VM, and What WSL2 Can Do | — (no lab; capability tables) | Reading only |

<Lab host="any-linux" title="Confirm your host can run the lab" time="5 min">

1. Check QEMU is installed and runnable:

   ```text
   $ qemu-system-x86_64 --version
   QEMU emulator version 8.2.2
   ```

2. Check your compiler:

   ```text
   $ gcc --version
   gcc (Ubuntu 13.2.0-23ubuntu4) 13.2.0
   ```

3. Check GDB:

   ```text
   $ gdb --version
   GNU gdb (Ubuntu 12.1-0ubuntu1~22.04) 12.1
   ```

4. Check for KVM:

   ```text
   $ ls -l /dev/kvm
   crw-rw---- 1 root kvm 10, 232 Aug 29 09:00 /dev/kvm
   ```

Exact version numbers will differ from the ones shown above — what matters is that all four commands
print something, and that step 4 shows a device node rather than "No such file or directory".

**If it fails:** a missing command means a package from the install tabs above didn't land — reinstall
using your distribution's tab. A missing `/dev/kvm` is not a failure to fix before continuing; it means
this folder's labs will run slower, and that's the end of the consequence.

</Lab>

<KernelFacts
  structure={[["~/kernel-lab/", "the working directory every lab in this section assumes"]]}
  path="host packages → source checkout → kernel build → initramfs → QEMU boot → GDB attach"
  observe="qemu-system-x86_64 --version && ls -l /dev/kvm"
  trap="Building a kernel on the host and booting it on the host are two different risks. This section only ever boots what you built inside QEMU, and that is the point." />

## References

- [QEMU documentation — `x86_64` System Emulator target](https://www.qemu.org/docs/master/system/target-i386.html)
  — the machine options every later lab's QEMU invocation in this section is drawn from.
- [Kernel documentation — Minimal requirements to compile the Kernel](https://docs.kernel.org/process/changes.html)
  — the kernel's own minimum tool versions; the authoritative answer to "is my toolchain new enough."
- [Microsoft — Windows Subsystem for Linux FAQ](https://learn.microsoft.com/en-us/windows/wsl/faq)
  — what WSL2 does and does not provide, worth checking whenever a lab in this section is marked `wsl2-ok`.
