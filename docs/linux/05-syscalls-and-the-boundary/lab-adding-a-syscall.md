---
id: lab-adding-a-syscall
title: "Lab: Add a System Call"
sidebar_label: "Lab: add a syscall"
sidebar_position: 10
tags: [linux, kernel, syscalls]
prerequisites:
  - linux/syscalls-and-the-boundary/the-syscall-table-and-dispatch
  - linux/lab-and-toolchain/building-a-kernel
draft: false
---

# Lab: Add a System Call

End to end in the QEMU lab: define it, wire the table, rebuild, boot, call it, and watch it in
`strace`. Every abstraction in this folder becomes concrete the moment you own both sides of the
boundary — you choose a number, write a handler, rebuild, boot, and call it from C, and afterwards the
dispatch table in [The Table and the Dispatch](./the-syscall-table-and-dispatch.md) is no longer a
diagram, it is a file you edited yourself.

:::note[What was actually executed in this environment]
This page's C code and every kernel-source detail (the `.tbl` line format, the syscall number chosen,
`SYSCALL_DEFINE1`'s expansion, the `obj-y` line) were verified against Elixir/raw GitHub for the pinned
v6.18 tag, and the reader-facing C caller was actually compiled and run — see
[What was verified and what was not](#what-was-verified-and-what-was-not) at the end. What was **not**
done is the full lab: this environment has no `qemu-system-x86_64` binary, no cloned kernel source tree
(a full clone or even a shallow `torvalds/linux` checkout is multiple gigabytes, impractical to fetch
here just to prove a build succeeds), and no toolchain for cross-building a bootable kernel image. The
step-by-step instructions and their expected output below are written from verified source facts, not
captured from a real boot — where that matters, it is called out inline rather than presented as a
transcript.
:::

## What you are about to do

Four edits, in order:

1. **A table entry** — one line in `arch/x86/entry/syscalls/syscall_64.tbl`, giving your syscall a
   number and naming its entry point.
2. **A `SYSCALL_DEFINE`** — the handler itself, in a new file under `kernel/`.
3. **A rebuild** — the same `make -j$(nproc)` from [Building a Kernel](../01-lab-and-toolchain/building-a-kernel.md).
4. **A caller** — a small, statically linked C program that calls your syscall by number.

Say this plainly before you start: in real kernel development, adding a syscall is a heavyweight act.
It needs a justification an existing interface can't satisfy, an architecture-independent design (the
number and the handler have to make sense on arm64 and every other architecture the kernel supports,
not just x86-64), a man page, and a kernel selftest, and it has to survive review from people whose job
is specifically to say no to new syscalls when an existing one could be extended instead. This lab skips
every one of those requirements on purpose. [Why upstream would reject
this](#why-upstream-would-reject-this) below says so again, at the end, so the shortcut doesn't read as
a template for real work.

<Lab host="qemu" title="Add a syscall and call it" time="60 min, most of it the rebuild">

### 1. Pick a number and add the table line

<Src file="arch/x86/entry/syscalls/syscall_64.tbl" /> is a plain text file, one syscall per line, in the
format its own header comment states: `<number> <abi> <name> <entry point>`. As of the v6.18 tag, the
highest `common`/`64` (native x86-64) syscall number in use is 469 (`file_setattr`); the range from 512
onward is reserved for the legacy `x32` ABI and is a different numbering track entirely. **470** is the
next free native number:

```text
470	common	hello_kernel		sys_hello_kernel
```

:::warning
Pick a number **above** everything currently in use — do not reuse or guess at a gap, because a
"gap" in this file is very likely a removed syscall's number that must never be reassigned (see
[Numbers are frozen forever](./the-syscall-table-and-dispatch.md#numbers-are-frozen-forever)). This
kernel's numbering past 469 is now **local to you** — a binary built against it, calling syscall 470,
means nothing on anyone else's kernel, upstream or otherwise, and would call whatever upstream syscall
that number is eventually assigned to instead.
:::

### 2. Write the handler

A new file, `kernel/hello_syscall.c` — a one-argument `SYSCALL_DEFINE1`, taking a user pointer, copying
a fixed string into it with `copy_to_user`, and returning `0` on success or `-EFAULT` on a bad pointer,
exactly the convention [Copying Data Across the
Boundary](./copying-data-across-the-boundary.md#copy_from_user-and-copy_to_user) already covered:

```c
// kernel/hello_syscall.c
#include <linux/syscalls.h>
#include <linux/uaccess.h>
#include <linux/kernel.h>

SYSCALL_DEFINE1(hello_kernel, char __user *, buf)
{
	const char msg[] = "hello from the kernel you built\n";

	if (copy_to_user(buf, msg, sizeof(msg)))
		return -EFAULT;

	return 0;
}
```

Then wire it into the build — Kbuild does not compile a file just because it exists under `kernel/`, it
compiles what `kernel/Makefile`'s `obj-y` list names. Add one line, following the same
`obj-y = a.o b.o c.o \` continuation style already in that file:

```text
obj-y += hello_syscall.o
```

This is also the point at which the reader touches Kbuild directly rather than through `make defconfig`
or `menuconfig` — see [Kconfig and
Kbuild](../04-kernel-architecture-and-idioms/kconfig-and-kbuild.md) for what `obj-y` means to the build
system underneath this one line.

### 3. Rebuild

The same invocation [Building a Kernel](../01-lab-and-toolchain/building-a-kernel.md#running-the-build)
established:

```text
$ make -j$(nproc)
```

Editing the `.tbl` file regenerates the syscall headers Kbuild derives from it (a fast, whole-tree-wide
dependency, since every translation unit that includes the syscall table transitively depends on it),
and the new `.o` from `obj-y` is a single new compile unit — realistically a couple of minutes on a
modern multi-core machine for the incremental parts, not the ten-to-forty-minute full `defconfig` build
[Building a Kernel](../01-lab-and-toolchain/building-a-kernel.md#running-the-build) quotes for a clean
tree, because only the syscall table's dependents and the one new file actually need recompiling.

### 4. Boot in QEMU

The canonical invocation from [Booting Your Kernel in
QEMU](../01-lab-and-toolchain/booting-your-kernel-in-qemu.md#the-canonical-invocation), verbatim — this
lab adds nothing to it:

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

Expect the same banner and BusyBox prompt that page describes, with nothing different in the boot log —
a new syscall does not announce itself at boot; it is silent until something calls it.

### 5. Call it from C — statically linked

```c
// caller.c
#define _GNU_SOURCE
#include <stdio.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <errno.h>
#include <string.h>

int main(void)
{
	char buf[64];
	long ret = syscall(470, buf);

	if (ret < 0) {
		printf("syscall(470) failed: %s\n", strerror(errno));
		return 1;
	}

	printf("kernel said: %s", buf);
	return 0;
}
```

```text
$ gcc -static -O0 -o caller caller.c
```

This is the step that catches people, so it is said before you hit it rather than in the failure list
below: **it must be `-static`.** The BusyBox initramfs this lab's kernel boots into
([A Minimal Root Filesystem](../01-lab-and-toolchain/a-minimal-rootfs.md)) has no dynamic loader for a
glibc binary — no `/lib64/ld-linux-x86-64.so.2`, nothing NSS or `ld.so` could resolve at runtime.
A dynamically linked test binary copied into that initramfs is not a syscall problem at all, it never
gets that far.

Copy `caller` into the initramfs root before repacking it (the same `cpio` packing [A Minimal Root
Filesystem](../01-lab-and-toolchain/a-minimal-rootfs.md) describes), rebuild the initramfs archive, and
boot again with the same QEMU invocation as step 4.

Inside the guest:

```text
/ # ./caller
kernel said: hello from the kernel you built
```

### 6. Watch it in `strace`

```text
/ # strace ./caller
...
syscall_0x1d6(0x... /* 64-byte buffer */) = 0
kernel said: hello from the kernel you built
+++ exited with 0 +++
```

`0x1d6` is 470 in hex. `strace` renders it as `syscall_0x1d6` — an unrecognised-syscall placeholder —
rather than `hello_kernel`, because `strace`'s syscall-name tables are compiled from the *upstream*
`.tbl` files at `strace`'s own build time. Your kernel knows the name `hello_kernel`; `strace`, running
unmodified userspace tooling built against mainline's numbering, has never heard of it. This is itself
the lesson [libc is not the kernel](./libc-is-not-the-kernel.md) already made from the other direction:
syscall *names* are a userspace convention layered on top of numbers the kernel actually dispatches on,
and a name that only your kernel knows is invisible to every tool that wasn't built against your kernel.

**If it fails:**

- **The symbol is missing at link time, not at boot.** Forgetting the `obj-y` line in step 2 does not
  fail silently and does not fail at boot — it fails while linking `vmlinux` in step 3, with an
  undefined-reference error naming `__x64_sys_hello_kernel` (or a similar mangled name the
  `SYSCALL_DEFINE1` macro generates). The `.tbl` entry references an entry point that Kbuild never
  compiled a definition for.
- **"No such file or directory" for a binary that plainly exists.** This is step 5's dynamic-linking
  trap arriving as a confusing kernel-side error rather than a clear one: the initramfs kernel tries to
  `execve` your test binary, finds it, and then tries to find *its interpreter* —
  `/lib64/ld-linux-x86-64.so.2` — which does not exist in a BusyBox initramfs. The missing file is the
  interpreter, not the binary you copied in; `file caller` (showing `dynamically linked` instead of
  `statically linked`) confirms it before you even boot.

</Lab>

## What you just proved

Each step maps back to a page this folder already wrote:

- The table entry in step 1 is the same mechanism [The Table and the
  Dispatch](./the-syscall-table-and-dispatch.md) described from the read-only side — you just added a
  row to the file that page only quoted from.
- The `copy_to_user` call in step 2 is the exact interface [Copying Data Across the
  Boundary](./copying-data-across-the-boundary.md#copy_from_user-and-copy_to_user) covered — the same
  return-value convention (zero means success) applies to the handler you wrote as to every syscall in
  the tree.
- The `-EFAULT` return on a bad pointer is the same negative-errno convention [Arguments, Return
  Values, and errno](./arguments-return-values-and-errno.md#negative-errno-and-the-sign-trick) derived
  from first principles — your handler participates in it by returning a small negative number, exactly
  like every syscall around it.
- The unrecognised `syscall_0x1d6` name in `strace` is [libc is not the
  kernel](./libc-is-not-the-kernel.md)'s point from a new angle: a syscall's *name*, as far as any
  userspace tool is concerned, is metadata that tool shipped with, not something the kernel transmits at
  call time. The kernel only ever sees and returns a number.

## Why upstream would reject this

A real new syscall needs, at minimum: a concrete justification that an existing syscall or `ioctl`
genuinely cannot be extended to cover the need; a design that makes sense identically across every
architecture the kernel supports, not just the one you tested on; a man page describing the new
interface's contract; and a kernel selftest under `tools/testing/selftests/` exercising it, because a
syscall number, once released, is a permanent commitment — it cannot be renumbered or reclaimed even if
the interface turns out to be a mistake. None of that happened here. This lab exists to make the
mechanics concrete, not to teach the habit of reaching for a new syscall number as a first move — in
practice, the answer upstream gives most often is "extend an existing interface instead," and that
answer is usually right.

## What was verified and what was not

Everything about the *shape* of this lab was checked against the pinned v6.18 source rather than
assumed:

- The `.tbl` file's format and the highest in-use native (`common`/`64`) syscall number (469, making 470
  the next free one) were read directly from
  `arch/x86/entry/syscalls/syscall_64.tbl` at the v6.18 tag — not guessed.
- `SYSCALL_DEFINE1`'s definition (`include/linux/syscalls.h`) and `kernel/Makefile`'s `obj-y` line
  format were both read from the pinned tag, not recalled from memory.
- The C caller program above was actually compiled in this environment with `gcc -static -O0` and
  produced a genuine, statically linked ELF binary (confirmed with `file`, which reported `statically
  linked`, no interpreter). It was also actually *run* — against this environment's real host kernel,
  which is a real, unmodified v6.18-family build, not the custom lab kernel this page describes building.
  Since that host kernel has no syscall 470, the honest, actually-observed result was:

  ```text
  $ ./caller
  syscall(470) failed: Function not implemented
  ```

  `Function not implemented` is `strerror(ENOSYS)` — exactly the failure a correctly-written raw
  `syscall()` call produces against a kernel that has no such syscall, which is a genuine data point
  confirming the C source and the raw-syscall mechanism both work correctly. It is **not** a
  demonstration of the lab succeeding — that requires the custom-built kernel from steps 1–4 actually
  booted, which this environment cannot do.
- `strace` and `qemu-system-x86_64` are not installed in this sandbox, and there is no
  package-manager access to add them. The `strace` output in step 6 and the QEMU boot log in step 4 are
  therefore written as accurate descriptions of what the verified mechanism produces, not captured
  transcripts, and are presented that way rather than as invented terminal sessions passed off as real
  ones.

<KernelFacts
  structure={[["SYSCALL_DEFINE1", "include/linux/syscalls.h"], ["sys_call_table", "arch/x86/entry/syscall_64.c"]]}
  path="syscall_64.tbl → generated syscall headers → x64_sys_call() switch case → __x64_sys_hello_kernel() → __do_sys_hello_kernel()"
  observe="strace ./caller 2>&1 | grep syscall_"
  trap="Adding a syscall is the easy part; keeping it is the hard part. A syscall number is a permanent commitment, which is why upstream asks whether an existing interface can be extended before it will consider a new one." />

## References

- <Src file="arch/x86/entry/syscalls/syscall_64.tbl" /> — the file you are editing, and the format is
  documented in its own header comment.
- [Adding a new system call](https://docs.kernel.org/process/adding-syscalls.html) — the kernel's own
  guide to doing this for real, including everything this lab skips.
- [`syscall(2)`](https://man7.org/linux/man-pages/man2/syscall.2.html) — the caller side, and the reason
  the test program uses `syscall()` rather than a wrapper.
- [Linux Kernel Selftests](https://docs.kernel.org/dev-tools/kselftest.html) — what a real new syscall
  must ship with, which is the point of the closing section above.
