---
id: booting-your-kernel-in-qemu
title: "Booting Your Kernel in QEMU"
sidebar_label: "Booting in QEMU"
sidebar_position: 5
tags: [linux, kernel, lab]
prerequisites:
  - linux/lab-and-toolchain/a-minimal-rootfs
draft: false
---

# Booting Your Kernel in QEMU

The canonical QEMU invocation every later lab reuses, explained flag by flag.

Three files and one command are the entire payoff of this folder so far: `arch/x86/boot/bzImage`
from [Building a Kernel](./building-a-kernel.md) and `initramfs.cpio.gz` from
[A Minimal Root Filesystem](./a-minimal-rootfs.md), handed to `qemu-system-x86_64`, produce a kernel
you built, booting on a machine you defined, with the entire boot log printing to your own terminal.
From here on, every claim this section makes about what the kernel does at boot is something you can
run and read for yourself, not something you have to take on faith.

## The canonical invocation

Run this from `~/kernel-lab/linux` — the build tree from [Building a Kernel](./building-a-kernel.md),
which is where `arch/x86/boot/bzImage` was left, one directory below the packed initramfs from
[A Minimal Root Filesystem](./a-minimal-rootfs.md):

```bash
$ qemu-system-x86_64 \
    -kernel arch/x86/boot/bzImage \
    -initrd ../initramfs.cpio.gz \
    -append "console=ttyS0" \
    -nographic \
    -m 2G \
    -smp 2 \
    -enable-kvm \
    -no-reboot
```

Every later lab in this section says "the canonical invocation, plus …" and means exactly this command
— the same eight flags, with one or two added or changed for that lab's purpose.

| Flag | What it does |
|---|---|
| `-kernel arch/x86/boot/bzImage` | Boots this file directly, bypassing a bootloader entirely — QEMU's own loader plays the role GRUB would on real hardware. |
| `-initrd ../initramfs.cpio.gz` | Loads the initramfs alongside the kernel; the kernel unpacks it into `tmpfs` and runs `/init` from it, exactly as described in [A Minimal Root Filesystem](./a-minimal-rootfs.md). |
| `-append "console=ttyS0 …"` | The kernel command line — `console=ttyS0` in particular, covered on its own below. |
| `-nographic` | No graphical window; QEMU becomes a plain command-line process with the guest's serial port multiplexed onto your terminal. |
| `-m 2G` | 2 GiB of guest RAM — comfortably more than a BusyBox initramfs lab needs, with room to spare for later labs in this section that do more. |
| `-smp 2` | Two virtual CPUs, enough to observe scheduling decisions without the noise of a larger topology. |
| `-enable-kvm` | Hardware-accelerated virtualization when `/dev/kvm` is available — see [The Lab Machine](./the-lab-machine.md#kvm-and-when-you-cannot-have-it) for what happens when it isn't. |
| `-no-reboot` | Exit instead of silently rebooting on a kernel panic — the difference between a panic you can read and an infinite reboot loop you have to `kill` from another terminal. |

## Why `console=ttyS0` and `-nographic` go together

`-nographic` alone does not put the kernel's boot log on your terminal — it only removes the graphical
window. Without a `console=` parameter telling the kernel where to send its messages, a kernel booted
this way still defaults to logging to a virtual VGA text buffer that `-nographic` gives you no way to
see, let alone scroll or copy. `console=ttyS0` redirects kernel log output to the first emulated serial
port, and `-nographic` is what multiplexes that serial port onto your actual terminal — the two flags
solve two different halves of the same problem, and neither one alone is enough. Once both are present,
the entire boot log is stdout: greppable, copy-pasteable, and scrollable in your terminal's own history,
which is the single detail that saves more time in this folder than anything else in it.

## Reading the boot log

A trimmed excerpt from a real boot with the invocation above, annotated line by line:

```text
[    0.000000] Linux version 6.18.0 (you@host) (gcc (Ubuntu 13.2.0) 13.2.0) #1 SMP ...
[    0.000000] Command line: console=ttyS0
[    0.000000] BIOS-provided physical RAM map:
[    0.000000] BIOS-e820: [mem 0x0000000000000000-0x000000000009fbff] usable
[    0.000000] BIOS-e820: [mem 0x0000000000100000-0x000000007ffdffff] usable
[    0.041233] smp: Brought up 1 node, 2 CPUs
[    0.041980] smpboot: Total of 2 processors activated (9999.99 BogoMIPS)
[    0.152884] Run /init as init process
[initramfs] mounted proc, sysfs, devtmpfs — dropping to shell
/ #
```

- **Version banner** — `Linux version 6.18.0 ...` confirms you booted the kernel you actually built, not
  a stale one left over from a previous run.
- **Command line echoed back** — the kernel restates exactly what `-append` sent it. If this line is
  missing or wrong, the wrong `bzImage` or the wrong `-append` string was used.
- **Memory map** — the `BIOS-e820` lines are the firmware's report of usable RAM, which the kernel's
  memory management (folder 03) builds its allocators on top of.
- **CPU bring-up** — `smpboot` and `smp: Brought up ...` show both `-smp 2` virtual CPUs coming online.
- **The initcall region** — between CPU bring-up and `Run /init`, dozens of unlabeled subsystem and
  driver `initcall`s run; folder 04 covers what an initcall actually is and how to see them individually.
- **`Run /init as init process`** — the exact moment covered in
  [A Minimal Root Filesystem](./a-minimal-rootfs.md#what-the-kernel-needs): the kernel has unpacked the
  initramfs and is about to execute `/init` as PID 1.
- **The shell prompt** — `/ #` is BusyBox's `ash`, `exec`'d in place of `/init`, proving the whole chain
  worked end to end.

Folder 03 walks this same boot sequence in far more depth, line by line, from firmware handoff through
the first userspace instruction.

## Getting out

:::tip
`-nographic` redirects your keyboard into the guest, so the usual `Ctrl-C` you'd reach for either does
nothing useful or sends `SIGINT` to a process *inside* the VM. QEMU's multiplexer uses its own escape
sequence instead, and not knowing it is the single most common reason someone abandons this folder
convinced their terminal is stuck.

- **`Ctrl-A` then `X`** — exits QEMU immediately.
- **`Ctrl-A` then `C`** — switches to the QEMU monitor console (and switches back the same way), for
  inspecting or controlling the VM without exiting it.
- **`-no-reboot`** — already in the canonical invocation above — turns a kernel panic into a stopped
  QEMU process instead of a silent, infinite reboot loop you'd otherwise have to kill from another
  terminal.
:::

## Variations you will need later

One line each — no depth here, just what to expect when a later lab says "the canonical invocation,
plus …":

| Addition | For |
|---|---|
| `-s -S` | Freezes the guest CPU at the first instruction and opens a GDB stub — next page. |
| `-drive file=disk.img,format=raw` (or `-hda disk.img`) | A real emulated block device, for labs that need an actual filesystem instead of an initramfs. |
| `-netdev user,id=n0 -device e1000,netdev=n0` | A guest network interface, for labs that touch the network stack. |
| `-cpu host` | Passes the host CPU's exact feature set through to the guest instead of QEMU's default model — usually paired with `-enable-kvm`. |

## When it hangs

Three causes account for almost every "QEMU looks frozen" report, and each has a distinct symptom:

- **No `console=` parameter.** The guest boots and runs completely normally — you simply never see any
  of it. Silent, not stuck; the fix is the `console=ttyS0` flag covered above, not `Ctrl-C`.
- **Missing or broken `/init`.** The boot log runs all the way through CPU bring-up and initcalls, then
  panics with a message naming `init` — "Requesting system reboot" style output ending in a kernel
  panic — because [A Minimal Root Filesystem](./a-minimal-rootfs.md)'s `/init` wasn't executable, wasn't
  static, or wasn't packed into the archive at all.
- **Wrong `bzImage` path.** This one never reaches the kernel at all — QEMU itself errors out
  immediately (`could not open disk image` or similar), because `-kernel` was pointed at a path that
  doesn't exist. Not a kernel message, because the kernel was never loaded.

<Lab host="qemu" title="Boot the kernel you built" time="5 min">

1. From `~/kernel-lab/linux`, run the canonical invocation:

   ```text
   $ cd ~/kernel-lab/linux
   $ qemu-system-x86_64 \
       -kernel arch/x86/boot/bzImage \
       -initrd ../initramfs.cpio.gz \
       -append "console=ttyS0" \
       -nographic \
       -m 2G \
       -smp 2 \
       -enable-kvm \
       -no-reboot
   ```

   Expect a banner line containing `6.18.0` within the first second of output, then — after CPU
   bring-up and the initcall region scroll past — a BusyBox prompt:

   ```text
   [    0.000000] Linux version 6.18.0 ...
   ...
   [initramfs] mounted proc, sysfs, devtmpfs — dropping to shell
   / #
   ```

2. Inside the guest, confirm what you're actually running:

   ```text
   / # uname -r
   6.18.0
   / # cat /proc/cmdline
   console=ttyS0
   / # ls /proc
   1        cpuinfo   interrupts  meminfo   self      version
   ...
   ```

   `uname -r` and the command line should match what you built and typed; `/proc` existing and listing
   entries confirms the kernel's own virtual filesystem is live, not just the shell.

3. Exit with `Ctrl-A` then `X`.

**If it fails:** see [When it hangs](#when-it-hangs) above — the three causes cover nearly every case,
and each one's symptom tells you which it is before you need to guess.

</Lab>

<KernelFacts
  structure={[["boot_params", "arch/x86/include/uapi/asm/bootparam.h"]]}
  path="qemu -kernel → firmware/loader handoff → decompression → start_kernel() → initramfs unpack → /init"
  observe="cat /proc/cmdline"
  trap="`-nographic` without `console=ttyS0` boots a perfectly healthy kernel that prints nothing. The silence is a console misconfiguration, not a hang." />

## References

- [QEMU documentation — Invocation](https://www.qemu.org/docs/master/system/invocation.html)
  — every flag in the canonical invocation above, documented in its primary source.
- [Kernel documentation — kernel parameters](https://docs.kernel.org/admin-guide/kernel-parameters.html)
  — the authority for what each parameter inside `-append` actually does, `console=` included.
- [Kernel documentation — serial console](https://docs.kernel.org/admin-guide/serial-console.html)
  — why `console=` is what makes the boot log visible at all, straight from the kernel's own docs.
