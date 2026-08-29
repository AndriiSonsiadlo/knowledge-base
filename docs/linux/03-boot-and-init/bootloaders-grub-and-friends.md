---
id: bootloaders-grub-and-friends
title: "Boot Loaders"
sidebar_label: "Boot loaders"
sidebar_position: 3
tags: [linux, boot]
prerequisites:
  - linux/boot-and-init/the-boot-chain
draft: false
---

# Boot Loaders

GRUB 2, systemd-boot, and direct EFI stub boot — and the four things any boot loader must do.

A boot loader has four jobs and no more: find a kernel, find an initramfs, build a command line, hand
over. Everything else a real boot loader ships with — menus, themes, filesystem drivers, a scripting
language — exists only to make those four things possible on a machine whose exact disk layout, kernel
version, and partition UUIDs it cannot know in advance. The three tools on this page sit at three very
different points on that spectrum, from "does everything itself" to "does almost nothing," and the
right one for a given machine depends on how much of that uncertainty actually needs solving at boot
time.

## The four jobs

1. **Find a kernel** — locate a `vmlinuz` file (or, with an EFI stub, treat the kernel itself as the
   thing to find) on some filesystem the loader can read.
2. **Find an initramfs** — locate the matching `initrd.img`, so early user space has the drivers and
   tools it needs to reach the real root.
3. **Build a command line** — assemble the text the kernel will parse at boot: `root=`, console settings,
   and anything else this specific machine needs.
4. **Hand over** — load both files into memory and jump into the kernel's entry point. From this instant
   the loader is gone; it is not resident, and it does not get control back.

Everything downstream of the jump is [The Boot Chain](./the-boot-chain.md)'s territory, not the loader's.

## GRUB 2's structure

GRUB 2 handles uncertainty by carrying its own filesystem drivers, so it can read `/boot` on whatever
filesystem it turns out to be, even ones the firmware itself cannot read:

- On legacy BIOS, a tiny **first-stage image** lives in the MBR's 446 usable bytes — barely enough code
  to locate and load the next stage. On UEFI, this stage is unnecessary; firmware loads `grubx64.efi`
  from the ESP directly.
- **`core.img`** is the real second stage: just enough filesystem support (and nothing else) to find and
  read `/boot/grub`.
- From there GRUB loads **modules** out of `/boot/grub` as needed — additional filesystem drivers,
  graphics support, cryptography for an encrypted `/boot` — before finally reading its configuration and
  presenting the menu.

This is why GRUB works almost anywhere: it doesn't depend on firmware understanding the filesystem
`/boot` lives on, because GRUB brought its own driver for it.

## Why you never edit `grub.cfg`

`/boot/grub/grub.cfg` is **generated**, not authored. It's produced by `grub-mkconfig` (or its distro
wrapper) from two inputs: `/etc/default/grub`, which holds the settings you actually want to change, and
the scripts in `/etc/grub.d/`, which scan the system — installed kernels, other detected operating
systems — and emit the menu entries. Hand-editing `grub.cfg` works exactly until the next kernel install
regenerates it and silently discards the edit.

The two commands that regenerate it correctly:

```bash
# Debian / Ubuntu
sudo update-grub

# Fedora / RHEL (UEFI)
sudo grub2-mkconfig -o /boot/efi/EFI/fedora/grub.cfg
```

:::note
Those two commands are not equally routine. Debian/Ubuntu still regenerates `grub.cfg` on every kernel
install — that's what `update-grub` (wrapping `grub-mkconfig`) is for. Fedora and RHEL 8+ default to the
**Boot Loader Specification (BLS)** instead (Fedora, since Fedora 30): `grub.cfg` becomes essentially
static, holding little more than a `blscfg` directive, and each kernel install drops its own snippet
under `/boot/loader/entries/*.conf` via `kernel-install`/`grubby` — no `grub.cfg` regeneration involved.
`grub2-mkconfig` still exists on those systems, but it's closer to an emergency-repair command than
something a normal kernel install runs.
:::

## `systemd-boot`

`systemd-boot` takes the opposite approach from GRUB: instead of carrying its own filesystem drivers, it
relies on UEFI already being able to read FAT, and does nothing GRUB does that FAT-plus-UEFI can't cover
on its own. The result is much smaller and correspondingly less flexible:

- **UEFI only** — there is no legacy-BIOS mode, because the whole design leans on services only UEFI
  provides.
- **One config file per boot entry**, under `$ESP/loader/entries/*.conf`, each naming a `linux` line, an
  `initrd` line, and boot options — no scripting language, no generation step.
- **No filesystem drivers of its own** — it only ever reads the ESP, and UEFI already knows how to read
  FAT, so there's nothing left for `systemd-boot` to bring.

## EFI stub: no loader at all

The Linux kernel binary is, on UEFI, itself a valid `.efi` executable —
<Src file="drivers/firmware/efi/libstub/efi-stub-entry.c" symbol="efi_pe_entry" /> is the entry point
firmware calls if it loads `vmlinuz` directly. Firmware doesn't need to understand "kernel" as a concept;
it just runs a PE32+ file like any other, and that file happens to be a Linux kernel that knows how to
finish booting itself. The command line comes from an NVRAM boot variable (set with `efibootmgr`) or from
a `systemd-boot` entry that names the kernel as its `linux` line — either way, no separate loader program
ever runs.

Set beside each other, the three trade "how much a machine's uncertainty gets solved by the loader"
against "how much the loader itself has to carry":

| | GRUB 2 | `systemd-boot` | EFI stub |
|---|---|---|---|
| Firmware support | legacy BIOS and UEFI | UEFI only | UEFI only |
| Config location | `/boot/grub/grub.cfg`, regenerated per install (Debian/Ubuntu) or `/boot/loader/entries/*.conf`, static `grub.cfg` (Fedora/RHEL 8+, BLS) | `$ESP/loader/entries/*.conf` | an NVRAM boot variable |
| Filesystem knowledge required | its own drivers for whatever `/boot` is on | none — relies on UEFI's FAT support | none — relies on UEFI's FAT support |
| Size | large — carries drivers, a menu, a scripting language | small — one binary, no scripting | none — no loader binary at all |
| What you give up | nothing filesystem-wise, but more surface to configure wrong | any filesystem but FAT, any firmware but UEFI | a menu, and any per-boot choice beyond what NVRAM holds |

*GRUB 2, `systemd-boot`, and EFI stub boot, compared across what each one needs from firmware and what it costs to use.*

## What actually happens

Press `e` at the GRUB menu on any entry, and you're looking at that entry's actual `linux` and `initrd`
lines — the exact text GRUB is about to load and hand off — not the config file itself. Edit them, and
the change applies to *this one boot only*; GRUB never writes anything back to `grub.cfg`, so the next
boot starts from the unedited entry again.

This is the single most useful recovery trick in this folder. The keys, on a stock GRUB 2 menu:

1. Highlight the entry you want to boot (usually the default, highest-numbered kernel) and press `e`.
2. Find the line starting with `linux` (or `linuxefi`) — this is the kernel command line the entry is
   about to use.
3. Move to the end of that line and append the option you need — most commonly `init=/bin/sh`, which
   tells the kernel to run a shell directly as PID 1 instead of the normal init, skipping every unit and
   service that might be the reason the system won't boot.
4. Press `Ctrl+X` (or `F10`) to boot with the edited line.

:::tip
`init=/bin/sh` at this prompt rescues most broken systems that boot the kernel fine but fail somewhere
in user space — a bad fstab entry, a broken systemd unit, a forgotten root password. It drops you
straight into a root shell with no service ever having started, so use it as a diagnostic vantage point,
not an assumption that everything else is fine: filesystems may still be mounted read-only, and
`/`, `/usr`, and friends may not be the layout a normal login shell would expect.
:::

## Misconceptions

- **"GRUB boots Linux."** GRUB loads a file into memory and jumps to it. It never runs Linux code, never
  understands processes or system calls, and is not present in memory in any meaningful sense the moment
  after that jump. "Boots Linux" credits the loader with work the kernel does entirely on its own, once
  handed off to.
- **"Editing `grub.cfg` fixes it."** On a system that still regenerates it per kernel install
  (Debian/Ubuntu), the edit survives only until the next kernel update silently discards it — the
  durable fix is `/etc/default/grub` or `/etc/grub.d/`, followed by re-running `grub-mkconfig`. On BLS
  systems (Fedora/RHEL 8+) it's worse than temporary: `grub.cfg` is closer to a static launcher, so an
  edit there may not even be read at all (see
  [Why you never edit `grub.cfg`](#why-you-never-edit-grubcfg) above).
- **"You need a boot loader."** You need something to find a kernel, find an initramfs, build a command
  line, and hand over — but on UEFI, the kernel can do all four of those for itself as an EFI stub. A
  boot loader is the common answer, not the only possible one.

<KernelFacts
  structure={[["/boot/grub/grub.cfg", "generated — never hand-edited"], ["/etc/default/grub", "the input you actually edit"]]}
  path="firmware → loader image → menu entry → linux/initrd lines → kernel handoff with a command line"
  observe="cat /proc/cmdline"
  trap="`/proc/cmdline` is the truth about what the loader passed, and `grub.cfg` is only what it intended to. When they disagree, the boot used a different entry than you think." />

## References

- [GRUB manual](https://www.gnu.org/software/grub/manual/grub/grub.html) — the configuration model this
  page insists on: `/etc/default/grub` and `/etc/grub.d/` as input, `grub-mkconfig` as the only correct
  way to produce `grub.cfg`.
- [`systemd-boot` manual](https://www.freedesktop.org/software/systemd/man/latest/systemd-boot.html) —
  the minimal alternative to GRUB, and its per-entry config file format.
- [The kernel's EFI stub documentation](https://docs.kernel.org/admin-guide/efi-stub.html) — booting
  with no loader at all, and exactly what firmware must provide instead of a separate program.
