---
id: the-kernel-command-line
title: "The Kernel Command Line"
sidebar_label: "Kernel command line"
sidebar_position: 4
tags: [linux, boot]
prerequisites:
  - linux/boot-and-init/bootloaders-grub-and-friends
draft: false
---

# The Kernel Command Line

How parameters reach the kernel, how they are parsed, and the dozen worth knowing — the most useful boot debugging tool there is.

The command line is the only channel through which you can change kernel behaviour *before* any user
space exists. Every other lever — a sysctl, a module option loaded after boot, a config file under
`/etc` — requires something to already be running to read it. The command line requires nothing: it is
text handed over at the same instant the kernel itself is handed over, which makes it the most useful
debugging tool in this folder and the only one that still works when the machine will not boot far
enough to log in.

## How it reaches the kernel

The [boot loader](./bootloaders-grub-and-friends.md) builds the command line as one of its four jobs —
concatenating whatever `linux`/`linuxefi` line arguments the menu entry carries — and places it where the
[boot protocol](./the-kernel-image.md) says a command line goes: at the physical address written into the
setup header's `cmd_line_ptr` field. The kernel does not go looking for it; the loader is obligated to
fill that field in, and the kernel trusts it.

Once the kernel is running, it keeps its own copy. `/proc/cmdline` is not a live view of firmware or
loader state — it is `fs/proc/cmdline.c` printing back
<Src file="init/main.c" symbol="saved_command_line" /> exactly as the kernel saved it once, early in boot.
Nothing after that point can change what `/proc/cmdline` reports, including anything the kernel itself
does while parsing the string.

## How it is parsed

Parsing happens in two passes, and the difference between them is *when* each runs, not *what* they
parse:

- **`early_param()`** registers a handler for a parameter that must be acted on before most of the
  kernel is up — before memory management, before most subsystems have even been initialised. Only a
  short list of parameters qualify: things like early console selection, KASLR disabling, or memory-map
  overrides that later init code already depends on. <Src file="include/linux/init.h" symbol="early_param" />
  is the registration macro; <Src file="init/main.c" symbol="parse_early_param" /> is what walks the
  command line against every handler registered this way, and it runs first.
- **`__setup()`** registers a handler for everything else — the ordinary case. <Src file="include/linux/init.h" symbol="__setup" />
  is the macro; <Src file="kernel/params.c" symbol="parse_args" /> is what walks the command line against
  every `__setup` handler, later in `start_kernel()`, after `parse_early_param()` has already run.

What happens to a `key=value` pair that matches *no* handler at all is where the interesting behaviour
lives, and it is not "ignored." `parse_args()` is called with
<Src file="init/main.c" symbol="unknown_bootoption" /> as its fallback, and that function makes a
decision per unrecognised parameter:

- A well-known boot loader identifier (`BOOT_IMAGE=`, `kexec`) is dropped silently.
- A parameter **whose name contains a `.`** — `systemd.unit=`, `usbcore.autosuspend=`, any
  `modulename.param=value` shape — is left alone entirely. The kernel does not act on it and does not
  hand it to anything; it simply stays present, unmodified, in the full command line for a later consumer
  to find on its own. This is why `systemd.*` options work: systemd, once it becomes PID 1, reads
  `/proc/cmdline` itself and picks out anything prefixed `systemd.` — the kernel's own parser plays no
  part in that handoff.
- Everything else — a bare `key=value` pair with no dot — becomes an entry in the environment or argument
  list the kernel will hand to whatever it execs as init.

Separately from all of this, anything after a literal `--` on the command line is *always* handed to init
as arguments, via a second, dedicated `parse_args()` pass — the mechanism
[the kernel's own admin guide to `init`](https://docs.kernel.org/admin-guide/init.html) documents as
"everything after `--` is passed as an argument to init." That pass is unconditional; it does not depend
on anything being unrecognised first.

## The parameters worth knowing

| Parameter | What it does | Reach for it when |
|---|---|---|
| `root=` | Names the device to mount as the real root — a path, a `UUID=`, or a `LABEL=` | Always present on a working system; the first thing to check when boot stalls with "unable to mount root fs" |
| `rootfstype=` | Overrides filesystem-type autodetection for `root=` | Autodetection guesses wrong, or the filesystem needs a hint the superblock doesn't carry |
| `init=` | Runs the named program as PID 1 instead of the distribution's normal init | User space is broken but the kernel boots fine — the single most useful recovery parameter in this folder |
| `console=` | Selects and configures a console device (`ttyS0`, `tty0`, with baud rate for serial) | No output is reaching the display or terminal you expect |
| `quiet` | Raises the console log level so only high-priority messages print | Normal, quiet boots; the opposite of what you want while debugging |
| `loglevel=` | Sets the console log level numerically (`0`–`7`, higher is more verbose) | You need messages a default level suppresses — `loglevel=8` shows everything, including `KERN_DEBUG` |
| `nokaslr` | Disables kernel address space layout randomisation | Addresses need to be reproducible across boots for debugging, or a crash dump needs stable offsets |
| `maxcpus=` | Caps the number of CPUs brought online at boot | Isolating whether a bug is SMP-related, without physically removing cores |
| `nosmp` | Boots with a single CPU, equivalent to `maxcpus=0` | The most aggressive version of the same isolation |
| `initcall_debug` | Traces every initcall's entry, return value, and duration | An initcall is hanging or a driver's probe order matters to a bug |
| `earlyprintk=` | Enables kernel output before the normal console driver is ready | The machine hangs or panics before `console=` would even be in effect |
| `systemd.unit=` | Tells systemd which target to boot into, overriding the default | Booting straight to `rescue.target` or `multi-user.target` instead of the graphical default |
| `single` / `emergency` | Boots to a single-user or emergency shell, bypassing most units | Diagnosing a broken boot from as close to PID 1 as possible without hand-editing `init=` |

*The kernel command-line parameters worth knowing, and the situation each one is for. The complete,
authoritative list is [`Documentation/admin-guide/kernel-parameters.txt`](https://docs.kernel.org/admin-guide/kernel-parameters.html).*

## Module parameters on the command line

A parameter shaped `modulename.param=value` — `usbcore.autosuspend=-1`, for instance — is exactly the
"contains a dot, left untouched" case from the parsing section above. If the module is already built into
the kernel, its parameter is registered through the same `__setup`/`module_param` machinery and gets
picked up during the normal parsing pass. If the module is instead loaded later, the untouched text is
still sitting in `/proc/cmdline`, and `modprobe` consults it (per the comment in `unknown_bootoption()`:
*"unused parameters — modprobe will find them in `/proc/cmdline`"*) so a parameter for a module that
doesn't exist yet at boot still reaches it once it loads.

## Setting one for a single boot

Two routes reach the same place — appending text to the string the kernel receives — from two different
starting points:

- **At the GRUB menu**, press `e` on the entry, find the `linux`/`linuxefi` line, and append the
  parameter before booting with `Ctrl+X`. This is exactly the [recovery trick already covered](./bootloaders-grub-and-friends.md#what-actually-happens)
  in this folder's boot loader page — the edit lives for one boot only, and `grub.cfg` is never touched.
- **At a QEMU invocation**, the `-append` flag *is* the command line, passed directly with no loader in
  between at all: `-append "console=ttyS0 init=/bin/sh"`.

Both routes hand the kernel the same kind of string through the same `cmd_line_ptr` field; only how that
string gets assembled differs.

<Lab host="qemu" title="Change kernel behaviour without rebuilding" time="10 min">

Using the canonical invocation from [Booting Your Kernel in QEMU](../01-lab-and-toolchain/booting-your-kernel-in-qemu.md),
change only the `-append` value across three boots and watch the same kernel behave differently each time.

1. **Plain boot** — establish the baseline:

   ```text
   $ qemu-system-x86_64 \
       -kernel arch/x86/boot/bzImage \
       -initrd ../initramfs.cpio.gz \
       -append "console=ttyS0" \
       -nographic -m 2G -smp 2 -enable-kvm -no-reboot
   ```

   Expect the usual banner, a normal-length scroll of boot messages, then:

   ```text
   [initramfs] mounted proc, sysfs, devtmpfs — dropping to shell
   / #
   ```

2. **Add `initcall_debug loglevel=8`** — nothing about the kernel changed, only what it's told to report:

   ```text
   $ qemu-system-x86_64 \
       -kernel arch/x86/boot/bzImage \
       -initrd ../initramfs.cpio.gz \
       -append "console=ttyS0 initcall_debug loglevel=8" \
       -nographic -m 2G -smp 2 -enable-kvm -no-reboot
   ```

   The distinguishing output: a line per initcall, at `KERN_DEBUG` — invisible at the default log level,
   which is why `loglevel=8` has to ride along with `initcall_debug` rather than being optional:

   ```text
   [    0.041203] calling  migration_init+0x0/0x20 @ 1
   [    0.041215] initcall migration_init+0x0/0x20 returned 0 after 3 usecs
   [    0.041980] entering initcall level: device
   ...
   ```

   (Exact function names and timings vary by build — the shape of the output, one `calling`/`initcall
   ... returned` pair per initcall, is the thing to look for.)

3. **Add `init=/bin/sh`** — skip the initramfs's own `/init` entirely:

   ```text
   $ qemu-system-x86_64 \
       -kernel arch/x86/boot/bzImage \
       -initrd ../initramfs.cpio.gz \
       -append "console=ttyS0 init=/bin/sh" \
       -nographic -m 2G -smp 2 -enable-kvm -no-reboot
   ```

   The distinguishing output is an *absence*: no `"[initramfs] mounted proc, sysfs, devtmpfs"` line, no
   `exec /bin/sh` from the script — because the script never ran. The kernel `exec`s `/bin/sh` directly as
   PID 1, and you land straight on a bare prompt:

   ```text
   #
   ```

   Nothing is mounted yet, because the code that would have mounted it — `/init` — is the thing you just
   skipped:

   ```text
   # cat /proc/cmdline
   cat: can't open '/proc/cmdline': No such file or directory
   # mount -t proc none /proc
   # cat /proc/cmdline
   console=ttyS0 init=/bin/sh
   ```

Confirming `/proc/cmdline` at the end of each run is the same check every time — it is the ground truth
for what the loader actually passed, independent of what any of the three boots did with it afterward.

</Lab>

<KernelFacts
  structure={[["saved_command_line", "init/main.c — the kernel's own copy of what it was given"]]}
  path="loader fills cmd_line_ptr → parse_early_param() → parse_args() → unknown_bootoption() → leftovers stay in /proc/cmdline or reach init"
  observe="cat /proc/cmdline"
  trap="An unrecognised parameter is not an error. A dotted key like `nokalsr` (typo for `nokaslr`) is left completely untouched by the kernel — no warning, no effect, just silently present in /proc/cmdline for nothing in particular to read." />

## References

- [The kernel's complete parameter list](https://docs.kernel.org/admin-guide/kernel-parameters.html) —
  every parameter this page's table only samples; the reference to actually keep open while debugging.
- [`man 7 kernel-command-line`](https://www.freedesktop.org/software/systemd/man/latest/kernel-command-line.html) —
  systemd's own account of the parameters it consumes directly from `/proc/cmdline`, including every
  `systemd.*` and `rd.*` option.
- [The kernel's admin guide to `init`](https://docs.kernel.org/admin-guide/init.html) — the `init=`
  escape hatch this page's lab uses, and the failures it exists to diagnose.
