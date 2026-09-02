---
id: systemd-in-practice-and-boot-debugging
title: "systemd in Practice, and Debugging a Broken Boot"
sidebar_label: "systemd and boot debugging"
sidebar_position: 12
tags: [linux, boot]
prerequisites:
  - linux/boot-and-init/systemd-the-model
  - linux/boot-and-init/the-kernel-command-line
  - linux/boot-and-init/initramfs-and-early-userspace
draft: false
---

# systemd in Practice, and Debugging a Broken Boot

Socket activation, journald, and unit supervision, then the playbook for a machine that will not finish booting.

This is the payoff page for the whole folder. A boot that fails is a boot that stopped at a *known*
stage, and every stage this folder has covered — firmware, boot loader, kernel image, `start_kernel()`,
initramfs, `switch_root`, systemd's own transaction — leaves evidence behind. This page is the playbook,
ordered by how far the machine actually got before it stopped.

## Socket and path activation

A `.service` doesn't have to start at boot at all. A `.socket` unit can own the listening socket a
service would normally bind itself, and systemd only starts the service the first time something actually
connects — the socket exists and queues the connection whether or not the service is running yet. A
`.path` unit does the same thing keyed on a filesystem event instead of a connection. Neither of these
*solves* the ordering problems the previous page described; what they do is remove a whole category of
them, because a client connecting to a socket-activated service no longer cares whether that service has
finished starting — the socket was already there to accept the connection, and the service starts (if it
hasn't already) as a side effect.

## journald

systemd's logging is structured, not line-oriented text files — every log entry is a set of key-value
fields (`MESSAGE=`, `_PID=`, `_SYSTEMD_UNIT=`, `PRIORITY=`, and dozens more), which is what makes
filtering by unit or boot or priority a query instead of a `grep`:

| Command | What it shows |
|---|---|
| `journalctl -b` | This boot's log, from the start |
| `journalctl -b -1` | The *previous* boot's log — the one you actually want after a crash, since the crashed boot's own log may be incomplete or never persisted |
| `journalctl -p err` | Only entries at priority `err` or worse, across every unit |
| `journalctl -u sshd` | Only entries tagged as belonging to `sshd.service` |
| `journalctl -u sshd -b -1 -p err` | Combine freely — the previous boot's error-or-worse entries from one unit |

Whether `-b -1` finds anything at all is a **configuration choice**, not a guarantee: `Storage=` in
`/etc/systemd/journald.conf` can be `volatile` (RAM-backed, gone on reboot — useless for exactly the boot
you most want to inspect), `persistent` (written to `/var/log/journal`, survives reboot), or `auto`
(persistent only if `/var/log/journal` already exists). A machine set to volatile storage loses the one
boot's log a debugging session needs most.

## A unit per cgroup

Every service systemd starts is placed in its own cgroup, not merely tracked by its main PID. This is why
`systemctl status` can list every process belonging to a unit even after that process has forked and the
child has forked again — a double-fork that would escape a naive "track the one PID I started" supervisor
doesn't escape a cgroup, because membership is inherited by every descendant regardless of how many times
it re-parents. Folder 15 covers cgroups themselves; the fact worth carrying forward here is narrower: a
unit's process accounting is exact because it's cgroup-based, not because systemd is watching PIDs.

## The playbook

Symptoms ordered by how far the machine got — each row names what reaching that symptom proves, the
first thing to try, and where in this folder (or this page) the underlying mechanism is explained:

| Symptom | Proves | Try first | See |
|---|---|---|---|
| No firmware output at all | Didn't even get through POST/UEFI init | Check the display cable/output, then the firmware's own boot-device order | [Firmware, BIOS, and UEFI](./firmware-bios-and-uefi.md) |
| Boot loader menu missing or wrong entry | Firmware ran and found *something* bootable, but not what you expected | Interrupt at the loader, check the entry list and default | [Boot Loaders](./bootloaders-grub-and-friends.md) |
| Kernel panic: "unable to mount root fs" | Kernel itself started and ran, but couldn't resolve or mount `root=` | Check `root=` against `blkid` output from a rescue/emergency shell | [The Kernel Command Line](./the-kernel-command-line.md) |
| Dropped to the initramfs emergency shell | Kernel and initramfs both ran; `/init` couldn't find or mount the real root | `cat /proc/cmdline` and `blkid` inside the emergency shell | [initramfs and Early User Space](./initramfs-and-early-userspace.md) |
| Boots to `emergency.target` | `switch_root` succeeded and systemd started, but a critical unit (often a filesystem mount) failed | `journalctl -xb` for the failing unit's error | This page, and [systemd: The Model](./systemd-the-model.md) |
| Boots, but one service fails | Everything through PID 1 and the transaction worked; one unit's own start command failed | `systemctl status <unit>` then `journalctl -u <unit> -b` | This page |
| Boots, but slowly | Everything works; something on (or off) the critical path is just slow | `systemd-analyze critical-chain`, not `blame` first | [Measuring a slow boot](#measuring-a-slow-boot) below |

*Ordered from "got almost nowhere" to "got everywhere, just imperfectly" — each row narrows down which
part of the boot chain is still a suspect.*

## The four parameters worth memorising

Of [the full command-line table](./the-kernel-command-line.md#the-parameters-worth-knowing), four earn a
place on a sticky note specifically for boot debugging:

- **`init=/bin/sh`** — skip the distribution's init entirely and land on a raw shell as PID 1. Works even
  when systemd itself, or every one of its unit files, is the thing that's broken.
- **`systemd.unit=rescue.target`** — let systemd start, but stop at a minimal single-user target instead
  of the normal default, useful when the kernel and initramfs are fine and the problem is somewhere in
  the unit graph.
- **`systemd.log_level=debug`** — raise systemd's own logging verbosity, independent of the kernel's
  `loglevel=`, for when the transaction itself is the mystery.
- **`earlyprintk=serial,ttyS0,115200`** — get kernel output onto a serial console before the normal
  console driver would otherwise be ready, for failures early enough that nothing else has a chance to
  print.

:::tip
`init=/bin/sh` is the escape hatch. When nothing else on this list gets you a prompt, this one still
might — it bypasses everything downstream of the kernel handing control to *something*, including
systemd itself.
:::

## Measuring a slow boot

`systemd-analyze` on its own reports one number: total time from kernel handoff to reaching the target,
split into firmware/loader/kernel/userspace phases. Two subcommands break that userspace figure down
further, and they answer different questions:

- **`systemd-analyze blame`** ranks every unit by how long *it individually* took to start, longest
  first.
- **`systemd-analyze critical-chain`** walks the actual dependency chain that determined when the target
  was reached — the path where each unit really was blocking the next one.

The honest caveat: `blame`'s ranking says nothing about whether anything was actually *waiting* on the
slow unit. A service that takes eight seconds to start but has nothing ordered after it costs the overall
boot time nothing at all — it just runs slowly, off to the side, in parallel with everything that does
matter. `critical-chain` is the one that answers "what do I actually have to make faster," and `blame`
alone routinely points at the wrong unit.

<Lab host="qemu" title="Break a boot, then diagnose it" time="15 min">

Using [the full-system Debian VM](../01-lab-and-toolchain/a-full-system-vm-and-wsl2.md), take a snapshot
before touching anything:

```bash
qemu-img snapshot -c before-boot-break debian-13-genericcloud-amd64.qcow2
```

Boot normally once to confirm the baseline works, then interrupt at the boot loader (or edit the kernel
command line for a single boot, the same way as [the kernel command-line lab](./the-kernel-command-line.md))
and change `root=` to a UUID that doesn't exist on this disk — a small edit, off by one character is
enough:

```text
root=UUID=00000000-0000-0000-0000-000000000000
```

Boot with that change. Expect the kernel to fail to mount root and the initramfs to drop to its emergency
shell rather than hang silently. From that shell, run the same two commands the initramfs page already
introduced:

```text
(initramfs)# cat /proc/cmdline
(initramfs)# blkid
```

`blkid`'s output includes the real UUID of the root filesystem — compare it against what `/proc/cmdline`
shows and the mismatch is the whole diagnosis. Reboot, correct `root=` back to the real UUID (or just
don't pass the override), and confirm the machine comes up clean again. Then restore the snapshot so the
qcow2 file itself is back to its pristine state regardless of anything left over inside the guest:

```bash
qemu-img snapshot -a before-boot-break debian-13-genericcloud-amd64.qcow2
```

:::danger
Do this against a single boot's command line (the loader menu edit, or a QEMU `-append` override), never
against a real machine's persistent boot configuration (`/etc/default/grub` followed by
`grub-mkconfig`/`update-grub`). Editing the persistent config with a broken UUID leaves the machine
unable to boot *at all*, every time, until someone fixes it from outside. The snapshot above is what
makes deliberately breaking a boot safe to repeat — it undoes damage a real machine's owner cannot undo
by simply rebooting.
:::

**If it fails:** the kernel boots straight through instead of dropping to the emergency shell — the disk
image uses `root=/dev/sdaN` or a label rather than a UUID, so a bogus UUID is simply never consulted.
Check the working command line first (`cat /proc/cmdline` on a normal boot) and edit whichever `root=`
form it actually uses.

</Lab>

<KernelFacts
  structure={[["journalctl -b", "this boot's structured log"], ["systemd-analyze critical-chain", "the ordering path that actually determined boot time"]]}
  path="symptom observed → the stage it proves was reached → the parameter or command for that stage → the page in this folder that explains the mechanism"
  observe="journalctl -b -p err"
  trap="systemd-analyze blame ranks services by how long they took, not by whether anything was waiting on them. A slow service off the critical chain costs nothing to boot time, and optimising it is wasted effort — critical-chain is the one that actually answers the question." />

## References

- [`journalctl(1)`](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html) — every flag
  this playbook leans on, especially `-b -1` for the previous boot's log.
- [`systemd-analyze(1)`](https://www.freedesktop.org/software/systemd/man/latest/systemd-analyze.html) —
  `blame` versus `critical-chain` in full, and why the distinction matters for where to spend effort.
- [systemd Debugging](https://freedesktop.org/wiki/Software/systemd/Debugging/) — the project's own
  debugging guide, and the source this page's four-parameter list is drawn from.
