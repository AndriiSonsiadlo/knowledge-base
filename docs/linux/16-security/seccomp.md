---
id: seccomp
title: "seccomp and Syscall Filtering"
sidebar_label: "seccomp"
sidebar_position: 7
tags: [linux, kernel, security]
prerequisites:
  - linux/security/capabilities
  - linux/syscalls-and-the-boundary/the-syscall-table-and-dispatch
related:
  - linux/containers-and-virtualization/building-a-container-from-scratch
  - linux/syscalls-and-the-boundary/tracing-and-intercepting-syscalls
draft: false
---

# seccomp and Syscall Filtering

seccomp shrinks the kernel a process can reach. A small classic-BPF program runs on every system
call. It sees the syscall number, the architecture and the raw arguments, and returns one of a few
verdicts: allow, fail with an errno, kill, trap, or ask a supervisor. Every container runtime
installs one. The details that matter are the ones people get wrong: check the architecture first,
and filter pointer arguments by value only, never by what they point to.

## Strict mode

The original seccomp (2005), `prctl(PR_SET_SECCOMP, SECCOMP_MODE_STRICT)`, allows exactly four
system calls: `read`, `write`, `_exit` and `sigreturn`. Anything else kills the process. It suits
a process that receives already-open file descriptors and only computes. Almost nothing else can
live with it, which is why filter mode exists. `Seccomp: 1` in `/proc/<pid>/status` means strict
mode, and `2` means filter mode.

## Filter mode

`seccomp(SECCOMP_SET_MODE_FILTER, flags, &prog)` installs a classic BPF program. At each syscall
entry, `__secure_computing()` runs every filter attached to the thread over a `struct seccomp_data`:

```c
struct seccomp_data {
	int   nr;                    /* syscall number */
	__u32 arch;                  /* AUDIT_ARCH_* of the calling convention */
	__u64 instruction_pointer;
	__u64 args[6];               /* raw register values */
};
```

The program returns a 32-bit value. The top 16 bits are the action, and the low 16 bits are data:
the errno for `ERRNO`, or a value passed to a tracer.

```wavedrom title="A seccomp filter's 32-bit return value" alt="Bit-field strip: low 16 bits SECCOMP_RET_DATA, high 16 bits SECCOMP_RET_ACTION_FULL"
{ reg: [
  { bits: 16, name: "SECCOMP_RET_DATA (errno, trace value)", type: 3 },
  { bits: 16, name: "SECCOMP_RET_ACTION_FULL", type: 2 }
], config: { hspace: 700 } }
```

Filters stack. A process can add more, but never remove one, and each `fork()` and `execve()`
inherits them. When several filters are attached, all of them run, and the **most restrictive**
result wins. The action values are ordered so that a numeric comparison selects it:

| Action | Value | Effect | Precedence |
|---|---|---|---|
| `SECCOMP_RET_KILL_PROCESS` | `0x80000000` | Kill the whole process (core dump) | 1 (most restrictive) |
| `SECCOMP_RET_KILL_THREAD` | `0x00000000` | Kill the calling thread | 2 |
| `SECCOMP_RET_TRAP` | `0x00030000` | Don't run it; deliver `SIGSYS` | 3 |
| `SECCOMP_RET_ERRNO` | `0x00050000` | Don't run it; return `-data` | 4 |
| `SECCOMP_RET_USER_NOTIF` | `0x7fc00000` | Suspend and ask a supervisor process | 5 |
| `SECCOMP_RET_TRACE` | `0x7ff00000` | Hand to a `ptrace` tracer, or fail with `ENOSYS` if none | 6 |
| `SECCOMP_RET_LOG` | `0x7ffc0000` | Run it, and log it | 7 |
| `SECCOMP_RET_ALLOW` | `0x7fff0000` | Run it | 8 |

A filter applies to the thread that installed it, and to its descendants.
**`SECCOMP_FILTER_FLAG_TSYNC`** applies it to every thread of the process at once, or fails if any
thread can't take it. That matters for a multithreaded runtime that installs the filter late.

## Check the architecture first

`nr` means nothing without `arch`. One x86-64 machine accepts system calls through three ABIs with
three different numbering schemes: native 64-bit, 32-bit i386 (through `int 0x80`), and x32 (64-bit
registers with 32-bit pointers, numbered with bit 30 set). A filter that compares `nr` against
x86-64 numbers without first checking `arch` applies its rules to the wrong syscalls when a process
enters through another ABI. Number 165 means `mount` in one table and something unrelated in
another.

So every filter starts the same way: load `arch`, compare it to the expected `AUDIT_ARCH_*`, and
kill the process if it doesn't match. On x86-64, a second check rejects numbers with
`__X32_SYSCALL_BIT` set, because x32 shares `AUDIT_ARCH_X86_64`. libseccomp generates both checks
automatically, which is one good reason to use it.

## Arguments are values, not memory

`args[]` holds raw register values. For `openat`, `args[1]` is the *address* of the path string,
not the path. A filter can't read user memory. Even if it could, the result would be useless: once
the filter has said yes, another thread can rewrite the string before the kernel copies it in
(time-of-check to time-of-use, the same race as a [double fetch](./vulnerability-classes.md#double-fetch)).
So seccomp can filter on flags and integers (`clone` flags, `socket` families, `ioctl` numbers), but
it can't filter by path. Access to files is the job of [Landlock](./the-lsm-framework.md#the-modules-today),
[AppArmor](./apparmor.md) or [SELinux](./selinux.md), which run after the kernel has copied the
path and resolved it.

## no_new_privs

An unprivileged process can install a filter only after setting `no_new_privs`
(`prctl(PR_SET_NO_NEW_PRIVS, 1)`). Otherwise `seccomp()` fails with `EACCES`. Without that rule,
an unprivileged process could install a filter that makes some syscall fail, then `execve()` a
setuid-root program, which would run as root with an unexpected failure the attacker chose, for
example in a `setuid()` call meant to drop privilege. With `no_new_privs` set, `execve()` can't
gain privilege, so the filter can't be turned against a privileged program. A process with
`CAP_SYS_ADMIN` in its user namespace is exempt. See
[Container Privilege](../15-containers-and-virtualization/capabilities-in-containers.md#no_new_privs)
for the container side.

## User notification

`SECCOMP_RET_USER_NOTIF` (Linux 5.0) moves the decision out of BPF into a **supervisor** process.
Installing the filter with `SECCOMP_FILTER_FLAG_NEW_LISTENER` returns a **listener file
descriptor**, which the installer passes to the supervisor, usually over a UNIX socket. When the
action fires, the calling thread blocks, and the supervisor:

1. reads the request with `ioctl(SECCOMP_IOCTL_NOTIF_RECV)`: the `seccomp_data` plus a cookie;
2. inspects the target as needed, for example through `/proc/<pid>/mem`, checking the cookie with
   `SECCOMP_IOCTL_NOTIF_ID_VALID` so it isn't fooled by a recycled PID;
3. performs the operation on the target's behalf if it chooses, and can install a file descriptor
   in the target with **`SECCOMP_IOCTL_NOTIF_ADDFD`**;
4. answers with `SECCOMP_IOCTL_NOTIF_SEND`: a return value, or `SECCOMP_USER_NOTIF_FLAG_CONTINUE`
   to let the kernel run the syscall as normal.

This is how LXD and Incus let unprivileged containers do selected `mknod` and `mount` operations
that the host vets. The TOCTOU warning above still applies: `CONTINUE` must never be the answer to
a security decision based on reading the target's memory.

## Runtime default profiles

Docker's default profile is an **allowlist**: a JSON document listing over 300 syscalls with
`SCMP_ACT_ALLOW`, with a default action of `SCMP_ACT_ERRNO`. Some entries are conditional on
argument values (`clone` without namespace flags, `personality` with specific values) or on the
container's capabilities: `mount` and the namespace calls are allowed only when `CAP_SYS_ADMIN` was
added. The daemon compiles it with libseccomp. Podman and CRI-O ship the same profile through
`containers/common`. `--security-opt seccomp=profile.json` replaces it, and
`--security-opt seccomp=unconfined` removes it. On the VM, `Seccomp: 2` with one filter inside a
default Podman container is that profile.

<Lab host="qemu" title="Make uname fail with EPERM" time="10 min">

`deny_uname` installs a filter that makes `uname(2)` fail, then runs a command under it:

```c title="deny_uname.c"
// SPDX-License-Identifier: GPL-2.0
/*
 * Install a seccomp filter that makes uname(2) fail with EPERM, then run
 * a command under it: ./deny_uname uname -a
 */
#define _GNU_SOURCE
#include <errno.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <stddef.h>
#include <stdio.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(int argc, char **argv)
{
	struct sock_filter filter[] = {
		/* Wrong architecture: kill, since the numbers below would be wrong. */
		BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
		BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
		/* x32 numbers have bit 30 set and share AUDIT_ARCH_X86_64. */
		BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
		BPF_JUMP(BPF_JMP | BPF_JGE | BPF_K, __X32_SYSCALL_BIT, 0, 1),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
		/* uname → EPERM; everything else allowed. */
		BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_uname, 0, 1),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
	};
	struct sock_fprog prog = {
		.len = sizeof(filter) / sizeof(filter[0]),
		.filter = filter,
	};

	if (argc < 2) {
		fprintf(stderr, "usage: %s <cmd> [args...]\n", argv[0]);
		return 2;
	}
	if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
		perror("PR_SET_NO_NEW_PRIVS");
		return 1;
	}
	if (syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER, 0, &prog) < 0) {
		perror("seccomp");
		return 1;
	}
	execvp(argv[1], &argv[1]);
	perror("execvp");
	return 1;
}
```

```make title="Makefile"
CFLAGS ?= -O2 -Wall -Wextra

deny_uname: deny_uname.c
	$(CC) $(CFLAGS) -o $@ deny_uname.c

clean:
	rm -f deny_uname
```

Files: [`deny_uname.c`](pathname:///code/linux/seccomp-uname/deny_uname.c),
[`Makefile`](pathname:///code/linux/seccomp-uname/Makefile). Measured on the folder-01 Debian VM as
the user `debian`:

```text
$ uname -sr
Linux 6.12.113+deb13-cloud-amd64
$ ./deny_uname uname -sr
uname: cannot get system name: Operation not permitted
$ strace -f -e trace=uname ./deny_uname uname -sr 2>&1 | tail -3
uname(0x7ffe4646f750)                   = -1 EPERM (Operation not permitted)
uname: cannot get system name: Operation not permitted
+++ exited with 1 +++
$ ./deny_uname grep -E '^(Seccomp|NoNewPrivs)' /proc/self/status
NoNewPrivs:	1
Seccomp:	2
Seccomp_filters:	1
$ grep Seccomp /proc/1/status
Seccomp:	0
Seccomp_filters:	0
```

- **The syscall never ran.** `strace` shows `uname` returning `EPERM` straight away. The filter's
  `SECCOMP_RET_ERRNO | EPERM` became the return value.
- **The filter survived `execve()`.** `deny_uname` installed it, then exec'd `uname` and `grep`,
  which both run under it. That inheritance is what makes seccomp usable by a runtime.
- **No root was needed**, because the program sets `no_new_privs` first.
- **systemd (PID 1) has no filter**, while many of the services it starts do (`SystemCallFilter=`).

The [container lab](../15-containers-and-virtualization/building-a-container-from-scratch.md)'s
filter is the larger example: the same arch and x32 checks with an eleven-syscall denylist.

If it fails: `seccomp: Permission denied` (`EACCES`) → `no_new_privs` wasn't set and the process
lacks `CAP_SYS_ADMIN`. `seccomp: Invalid argument` → a jump offset in the BPF program is wrong;
the kernel validates the program before accepting it.

</Lab>

## Misconceptions

1. **"seccomp can block access to a file path."** It sees only the pointer to the path. Filtering
   paths needs an LSM, which checks after the kernel has copied and resolved the name.
2. **"A denylist is as good as an allowlist."** A denylist allows every syscall it doesn't name,
   including those added in later kernels and older equivalents of the ones it does name
   (`open` next to `openat`). Runtimes ship allowlists.
3. **"seccomp filters are eBPF."** They are classic BPF: no maps, no helpers, no loops, a limited
   instruction set, and the kernel translates them internally. An eBPF-based seccomp has been
   proposed and not merged.

<KernelFacts
  structure={[["struct seccomp_data", "include/uapi/linux/seccomp.h"], ["struct seccomp_filter", "kernel/seccomp.c"]]}
  path="syscall entry → syscall_trace_enter() → __secure_computing() → seccomp_run_filters() → action"
  observe="grep Seccomp /proc/self/status; grep Seccomp /proc/1/status"
  trap="A filter written for x86-64 numbers that does not first check `arch == AUDIT_ARCH_X86_64` can be sidestepped through another syscall ABI on the same machine." />

## References

- [Seccomp BPF (SECure COMPuting with filters)](https://docs.kernel.org/userspace-api/seccomp_filter.html)
  — actions, precedence, user notification, and the architecture warning.
- [seccomp(2)](https://man7.org/linux/man-pages/man2/seccomp.2.html) and
  [seccomp_unotify(2)](https://man7.org/linux/man-pages/man2/seccomp_unotify.2.html).
- [libseccomp](https://github.com/seccomp/libseccomp) — `seccomp_init`, `seccomp_rule_add`,
  `seccomp_arch_add`; it generates the architecture checks. Checked via context7
  (`/seccomp/libseccomp`) on 2026-10-27.
- Docker, ["Seccomp security profiles for Docker"](https://docs.docker.com/engine/security/seccomp/)
  — the default allowlist and `--security-opt seccomp=`.
- <Src file="kernel/seccomp.c" symbol="__secure_computing" /> and `seccomp_run_filters()` beside it.
