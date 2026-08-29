---
id: a-full-system-vm-and-wsl2
title: "A Full-System VM, and What WSL2 Can Do"
sidebar_label: "Full VM and WSL2"
sidebar_position: 7
tags: [linux, kernel, lab]
prerequisites:
  - linux/lab-and-toolchain/booting-your-kernel-in-qemu
draft: false
---

# A Full-System VM, and What WSL2 Can Do

A Debian VM for the labs that need systemd and real block devices, then an honest account of which labs WSL2 can and cannot run.

The BusyBox initramfs lab that carried this folder so far is deliberately thin: no systemd, no real
block device, no network stack, because none of that is needed to watch scheduling, memory management,
or a syscall happen. That thinness runs out the moment a later lab needs any of those three things for
real, and rebuilding them by hand inside an initramfs would just be reinventing a distribution one
directory at a time. A Debian cloud image under QEMU is the second machine this section keeps around for
exactly that reason — slower to boot, but a real installed system with real services. And because a
sizeable share of readers are doing all of this from Windows, the second half of this page turns the
same honesty this section applies everywhere else onto WSL2 itself: what it actually runs, what it
fakes, and where it will teach you something wrong if you don't already know better.

## When the initramfs lab is not enough

| Need | Folder | Why the initramfs lab can't cover it |
|---|---|---|
| A running init system, units, and service dependencies | 03 | BusyBox's `/init` is a shell script, not `systemd` — there is nothing to introspect with `systemctl`. |
| A real block device and an on-disk filesystem | 11–12 | The initramfs lab's root is `tmpfs`, unpacked entirely into RAM; nothing here ever calls into a block layer or a filesystem driver. |
| A working network stack | 13 | The canonical invocation configures no NIC; anything below the socket layer is simply absent. |
| Containers | 15 | Namespaces and cgroups work in principle inside the initramfs lab, but a container runtime expects a real root filesystem, `systemd` (or an init that fakes enough of it), and a network stack to attach to. |

Each row names the folder where that lab actually lives; this page just builds the machine that makes it possible.

## A Debian cloud image under QEMU

Debian publishes ready-to-boot cloud images per release, and the `genericcloud` variant — a smaller
hardware-driver set than `generic`, built for exactly this kind of VM use — is the one to grab. The path
below is current for Debian 13 ("trixie") as of this writing; **check
[cloud.debian.org/images/cloud](https://cloud.debian.org/images/cloud/) before you run it**, since the
release name in the path changes every time Debian ships a new stable version:

```bash
curl -LO https://cloud.debian.org/images/cloud/trixie/latest/debian-13-genericcloud-amd64.qcow2
```

A cloud image has no root password and no user account baked in on purpose — it expects to be
provisioned on first boot by **cloud-init**, reading configuration from a small ISO it looks for at
every boot. `cloud-localds` (Debian/Ubuntu package `cloud-image-utils`) builds that ISO from two YAML
files:

```bash
cat > user-data <<'EOF'
#cloud-config
users:
  - name: debian
    ssh_authorized_keys:
      - ssh-ed25519 AAAA...your-public-key...
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
EOF
touch meta-data

sudo apt install --yes cloud-image-utils
cloud-localds seed.iso user-data meta-data
```

Boot the image with the seed attached as a second drive, the cloud image as a `virtio` block device, and
a forwarded port standing in for a real network:

```bash
qemu-system-x86_64 \
    -drive file=debian-13-genericcloud-amd64.qcow2,if=virtio \
    -drive file=seed.iso,if=virtio,format=raw \
    -netdev user,id=n0,hostfwd=tcp::2222-:22 \
    -device virtio-net-pci,netdev=n0 \
    -m 2G \
    -smp 2 \
    -enable-kvm \
    -nographic
```

Give cloud-init a few seconds to run on first boot, then reach the guest over the forwarded port instead
of the serial console:

```bash
ssh -p 2222 debian@localhost
```

Everything from here — `apt`, `systemctl`, a real `/etc/fstab` — behaves exactly like an installed
Debian machine, because it is one.

## Snapshots are the point

A machine with real state is a machine you can break in a way that sticks, which is exactly what some
later labs need to demonstrate — and exactly what makes doing it carelessly expensive. `qemu-img`
snapshots make the qcow2 disk itself revertible, independent of anything happening inside the guest:

```bash
qemu-img snapshot -c before debian-13-genericcloud-amd64.qcow2
```

Then break the machine deliberately — corrupt a filesystem, `rm -rf` something a service depends on,
whatever the lab in question calls for — and when it's time to start clean again:

```bash
qemu-img snapshot -l debian-13-genericcloud-amd64.qcow2   # list snapshots
qemu-img snapshot -a before debian-13-genericcloud-amd64.qcow2   # roll back to "before"
```

This is what makes the destructive labs later in this section safe to run at all: a `:::danger` lab is
one whose damage is real and does not undo itself, and a snapshot taken first is what turns "real and
permanent" into "real and free to repeat." [The Lab Machine](./the-lab-machine.md#the-host-badges)
covers the badge; this is the mechanism that backs it for anything running on this full-system VM.

## Sharing files with the guest

Two ways to move a file across the host/guest boundary, with a real trade-off between them. **`scp`
over the forwarded port** (`scp -P 2222 file debian@localhost:`) needs nothing beyond what the invocation
above already sets up, but it's a copy — the guest gets its own point-in-time version, and a host-side
edit after the fact does not appear on the other end without copying again. **`virtiofs`** shares a host
directory live instead: run `virtiofsd --socket-path=/tmp/vhostqemu -o source=/path/on/host` on the
host, add `-chardev socket,id=char0,path=/tmp/vhostqemu -device vhost-user-fs-pci,chardev=char0,tag=hostshare -object memory-backend-memfd,id=mem,size=2G,share=on -numa node,memdev=mem`
to the QEMU invocation (the shared memory object has to match `-m`), then `mount -t virtiofs hostshare
/mnt` inside the guest — after which both sides see the same files, no copying, no staleness. `scp` is
the simpler tool for "get this one file across once"; `virtiofs` is worth the extra setup only when the
guest needs to keep working against files the host is actively editing.

## WSL2, honestly

WSL2 is not a compatibility shim and it is not bare metal either — it's a Microsoft-built Linux kernel,
compiled from [a public fork Microsoft maintains](https://github.com/microsoft/WSL2-Linux-Kernel),
booted inside a lightweight Hyper-V VM with a curated set of virtio drivers and Hyper-V-specific
integration. That kernel is real: it runs real syscalls, a real scheduler, a real VFS. What's missing is
everything upstream of the kernel — there is no firmware, no boot loader, no discovered hardware,
because Hyper-V hands the VM a kernel image directly the same way `-kernel` does in the canonical QEMU
invocation from [Booting Your Kernel in QEMU](./booting-your-kernel-in-qemu.md#the-canonical-invocation).
That single fact — a real kernel, with the entire boot chain in front of it replaced — is what makes the
table below need three columns instead of two.

| Capability | Works | Partly | Does not |
|---|---|---|---|
| Building a kernel | Yes | | |
| Most userspace tooling (`gcc`, `git`, editors, containers via WSL's own runtime) | Yes | | |
| `strace` | | Depends on the shipped kernel's `CONFIG_` set for the tracee's syscalls | |
| `perf` | | Hardware PMU counters are Hyper-V's to grant, not guaranteed on every host | |
| `/proc` and `/sys` | | Populated by the real kernel, but for a synthetic Hyper-V machine, not your physical one | |
| Running a custom kernel | Yes — via `kernel=` in `.wslconfig` | | |
| UEFI/GRUB boot chain | | | Hyper-V hands the VM a kernel image directly; nothing here ever boots |
| `kexec` / `kdump` | | | Absent — no boot chain to hand off to |
| `systemd` | Yes on current WSL, opt-in via `wsl.conf`'s `[boot]` section on older ones | | |
| Loading arbitrary out-of-tree modules | | Only against a matching custom kernel you built yourself (`kernelModules=` in `.wslconfig`) | |
| Nested QEMU with KVM acceleration | Yes on recent Windows 11 builds, via `nestedVirtualization` in `.wslconfig` | | |

The "partly" rows share a cause: WSL2's kernel is a real kernel, so `/proc/cpuinfo`, `/sys`, `strace`,
and `perf` all return *something* — the trap is that "something" describes the Hyper-V VM Microsoft
built, filtered through whatever that kernel's `CONFIG_` set enables, not the physical machine sitting
under your hands.

## Which folders' labs run on WSL2

| Folder | Runs on WSL2? | Why |
|---|---|---|
| 00 — Overview | Yes | No lab content; reading only. |
| 01 — Lab and Toolchain | Partly | Building a kernel and `any-linux` labs run fine; QEMU labs need `nestedVirtualization` on and a recent Windows 11 build, and GDB against `-s -S` works the same way once that's true. |
| 02 — Guided Traces | Partly | Traces that run inside this section's own QEMU lab inherit folder 01's nested-virtualization requirement; traces read directly off WSL2's own kernel are not the same kernel this section pins and built against. |
| 03 — systemd and Init | Partly | Current WSL2 ships `systemd` (opt-in on older versions), so `systemctl`-level exploration works; anything that needs to watch the actual boot handoff from firmware does not, because WSL2 has no boot chain to watch. |
| 04 — Kernel Architecture and Idioms | Partly | Reading source and building are `any-linux` work and run anywhere; anything that depends on this section's QEMU/GDB lab inherits the same nested-virtualization requirement as folder 01. |

This is the table the `wsl2-ok` badge means: a lab earns it only once nested virtualization has been
confirmed working, and most `qemu`/`qemu-gdb` labs in folders 05 and later have not been re-verified
against it, which is why this table stops at folder 04.

## The honest summary

WSL2 is a Microsoft-built Linux kernel running inside a Hyper-V VM, with a heavily customised init and
filesystem path in front of it. It is a genuinely good place to *read* kernel source and to *build* a
kernel — both are ordinary userspace work that doesn't care what's underneath it. It is a bad place to
learn how a machine boots, because the entire boot chain this section spends folder 03 on simply isn't
there to observe. And it will teach you something wrong about `/proc` and `/sys` if you trust their
contents uncritically, because what they describe is real, but it's a description of the synthetic
Hyper-V machine, not of the laptop or desktop those files seem to be talking about.

<KernelFacts
  structure={[["/proc/version", "identifies a WSL2 kernel by its version string"], [".wslconfig", "Windows-side config; `kernel=` under `[wsl2]` points WSL2 at a kernel image you built"]]}
  path="Windows → Hyper-V → Microsoft WSL2 kernel → your distribution's userland"
  observe="cat /proc/version && ls /sys/firmware"
  trap="WSL2 runs a real Linux kernel, so most things work — which is exactly why the things that do not work are so confusing. There is no firmware, no boot loader, and no `/sys/firmware/efi`, because nothing booted." />

## References

- [WSL — Advanced settings configuration](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)
  — the `kernel=`, `kernelModules=`, and `nestedVirtualization` keys under `[wsl2]` in `.wslconfig`, straight from Microsoft's own docs.
- [microsoft/WSL2-Linux-Kernel](https://github.com/microsoft/WSL2-Linux-Kernel)
  — the actual kernel source and `.config` Microsoft ships with WSL2; the answer to "is this feature compiled in" for anything in the capability table above.
- [Debian Cloud Images](https://cloud.debian.org/images/cloud/)
  — the `genericcloud` images this page's lab uses, and where the release-name path changes on every new stable release.
- [QEMU documentation — vhost-user back ends](https://www.qemu.org/docs/master/system/devices/virtio/vhost-user.html)
  — the `virtiofsd`/`vhost-user-fs-pci`/`memory-backend-memfd` combination behind the `virtiofs` share above.
- [QEMU documentation — Invocation](https://www.qemu.org/docs/master/system/invocation.html)
  — `-drive`, `-netdev`, and `hostfwd` syntax for the full-system boot command.
