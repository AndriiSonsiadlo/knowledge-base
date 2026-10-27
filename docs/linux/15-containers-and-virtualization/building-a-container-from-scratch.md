---
id: building-a-container-from-scratch
title: "Lab: Build a Container from Scratch"
sidebar_label: "Lab: a container"
sidebar_position: 8
tags: [linux, kernel, containers]
prerequisites:
  - linux/containers-and-virtualization/mount-and-pid-namespaces
  - linux/containers-and-virtualization/user-namespaces
  - linux/containers-and-virtualization/cgroup-v2-architecture
  - linux/networking-stack/network-namespaces-and-virtual-devices
related:
  - linux/security/seccomp
draft: false
---

# Lab: Build a Container from Scratch

Each earlier page in this folder described one ingredient. This lab puts them together in
192 lines of C, in the same order a real runtime applies them. It ends with a shell that `ps`,
`hostname`, `ip` and `mount` all agree is inside a container. Nothing here is a toy version of the
mechanism. It *is* the mechanism, without the robustness.

## What you will build

`minicontainer <rootfs> <cmd> [args…]`, run as root, does six things, in order, and stops with
`perror` at the first failure:

1. **A cgroup** — `/sys/fs/cgroup/minicontainer-<pid>` with `memory.max=64M`, `memory.swap.max=0`
   and `pids.max=64` ([cgroup v2 Architecture](./cgroup-v2-architecture.md)).
2. **Namespaces** — `clone()` with new mount, PID, UTS, IPC and network namespaces. The parent puts
   the child into the cgroup and gives it one end of a veth pair while the child waits on a pipe
   ([Namespaces Overview](./namespaces-overview.md),
   [Network Namespaces and Virtual Devices](../13-networking-stack/network-namespaces-and-virtual-devices.md)).
3. **A root filesystem** — a hostname, a private mount tree, `pivot_root` into the rootfs, and fresh
   `/proc` and `/dev` ([Mount and PID Namespaces](./mount-and-pid-namespaces.md)).
4. **Fewer capabilities** — Docker's default 14, in the bounding, permitted and effective sets
   ([Container Privilege](./capabilities-in-containers.md)).
5. **A seccomp filter** — `no_new_privs`, then a BPF filter that returns `EPERM` for eleven
   syscalls ([seccomp](../16-security/seccomp.md)).
6. **`execvp()`** of the command.

```mermaid
sequenceDiagram
    participant P as parent (host namespaces)
    participant K as kernel
    participant C as child
    P->>K: mkdir cgroup; write memory.max, pids.max
    P->>K: clone(CLONE_NEWNS|NEWPID|NEWUTS|NEWIPC|NEWNET)
    K-->>C: PID 1 in new namespaces
    Note over C: read(pipe) blocks
    P->>K: write child PID to cgroup.procs
    P->>K: ip link add veth, move one end to child netns, addresses
    P->>C: write(pipe)
    C->>K: sethostname, MS_PRIVATE, bind rootfs, pivot_root, umount old root
    C->>K: mount /proc, tmpfs /dev, mknod null and zero
    C->>K: PR_CAPBSET_DROP ×27, capset
    C->>K: PR_SET_NO_NEW_PRIVS, seccomp(SET_MODE_FILTER)
    C->>K: execvp(cmd)
    P->>K: waitpid, rmdir cgroup
```

*The pipe is the synchronisation point. The child must not configure anything until the parent has
put it in the cgroup and given it a network interface.*

| File | What it is |
|---|---|
| [`minicontainer.c`](pathname:///code/linux/minicontainer/minicontainer.c) | The runtime: 192 lines, no dependencies beyond libc and kernel headers |
| [`setup-rootfs.sh`](pathname:///code/linux/minicontainer/setup-rootfs.sh) | Downloads, checks and extracts an Alpine minirootfs |
| [`Makefile`](pathname:///code/linux/minicontainer/Makefile) | One target |

## Prepare a root filesystem

Any directory with a userland works as a rootfs. Alpine's minirootfs is 8.7 MiB unpacked and has BusyBox,
so `ps`, `ip`, `ping` and `mount` are all there. The script pins the version and checks the SHA-256
before extracting. A downloaded archive is untrusted input, so it is unpacked into a new directory
and never over existing files.

```bash title="setup-rootfs.sh"
#!/bin/sh
# Download the Alpine minirootfs, check its SHA-256, and extract it into
# ./rootfs. The archive is untrusted input, so it goes into a fresh directory.
set -eu

VERSION=3.24.3
FILE=alpine-minirootfs-$VERSION-x86_64.tar.gz
URL=https://dl-cdn.alpinelinux.org/alpine/v${VERSION%.*}/releases/x86_64/$FILE
SHA256=f8e1cafba9b1b283b5d30d06f9885c8d2bc161ffe9083ade8e2e157813a53407

[ -e rootfs ] && { echo "rootfs/ already exists; remove it first" >&2; exit 1; }
curl -fsSLo "$FILE" "$URL"
echo "$SHA256  $FILE" | sha256sum -c -
mkdir rootfs
tar -xzf "$FILE" -C rootfs --no-same-owner
rm "$FILE"
```

## The code

```c title="minicontainer.c"
// SPDX-License-Identifier: GPL-2.0
/*
 * minicontainer: namespaces, a cgroup, pivot_root, a capability drop and a
 * seccomp filter, in the order a real runtime applies them.
 *
 *   sudo ./minicontainer <rootfs> <cmd> [args...]
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/audit.h>
#include <linux/capability.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <sched.h>
#include <signal.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/sysmacros.h>
#include <sys/wait.h>
#include <unistd.h>

#define DIE(what) do { perror(what); exit(1); } while (0)
#define CHECK(call) do { if ((call) < 0) DIE(#call); } while (0)

static char **child_argv;
static int sync_pipe[2];

/* Docker's default capability set (moby daemon/pkg/oci/caps/defaults.go). */
static const int keep_caps[] = {
	CAP_CHOWN, CAP_DAC_OVERRIDE, CAP_FOWNER, CAP_FSETID, CAP_KILL,
	CAP_SETGID, CAP_SETUID, CAP_SETPCAP, CAP_NET_BIND_SERVICE, CAP_NET_RAW,
	CAP_SYS_CHROOT, CAP_MKNOD, CAP_AUDIT_WRITE, CAP_SETFCAP,
};

static void write_file(const char *path, const char *val)
{
	int fd = open(path, O_WRONLY);

	if (fd < 0 || write(fd, val, strlen(val)) < 0)
		DIE(path);
	close(fd);
}

static void run(const char *fmt, ...)
{
	char cmd[256];
	va_list ap;

	va_start(ap, fmt);
	vsnprintf(cmd, sizeof(cmd), fmt, ap);
	va_end(ap);
	if (system(cmd) != 0) {
		fprintf(stderr, "failed: %s\n", cmd);
		exit(1);
	}
}

/* Step 3: a private mount tree, the rootfs as /, and fresh /proc and /dev. */
static void enter_rootfs(const char *rootfs)
{
	CHECK(mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL));
	CHECK(mount(rootfs, rootfs, NULL, MS_BIND | MS_REC, NULL));
	CHECK(chdir(rootfs));
	if (mkdir(".oldroot", 0700) < 0 && errno != EEXIST)
		DIE("mkdir .oldroot");
	CHECK(syscall(SYS_pivot_root, ".", ".oldroot"));
	CHECK(chdir("/"));
	CHECK(umount2("/.oldroot", MNT_DETACH));
	CHECK(rmdir("/.oldroot"));
	CHECK(mount("proc", "/proc", "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC, NULL));
	CHECK(mount("tmpfs", "/dev", "tmpfs", MS_NOSUID, "mode=755"));
	CHECK(mknod("/dev/null", S_IFCHR | 0666, makedev(1, 3)));
	CHECK(mknod("/dev/zero", S_IFCHR | 0666, makedev(1, 5)));
}

/* Step 4: shrink the bounding set, then the effective/permitted sets. */
static void drop_caps(void)
{
	struct __user_cap_header_struct hdr = { _LINUX_CAPABILITY_VERSION_3, 0 };
	struct __user_cap_data_struct data[2] = { 0 };
	unsigned long long keep = 0;

	for (size_t i = 0; i < sizeof(keep_caps) / sizeof(keep_caps[0]); i++)
		keep |= 1ULL << keep_caps[i];
	for (int cap = 0; prctl(PR_CAPBSET_READ, cap) >= 0; cap++)
		if (!(keep & (1ULL << cap)))
			CHECK(prctl(PR_CAPBSET_DROP, cap));
	data[0].effective = data[0].permitted = data[0].inheritable = keep;
	data[1].effective = data[1].permitted = data[1].inheritable = keep >> 32;
	CHECK(syscall(SYS_capset, &hdr, data));
}

/* Step 5: a teaching denylist. Real runtimes ship an allowlist. */
#define DENY(nr) \
	BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, (nr), 0, 1), \
	BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM)

static void install_seccomp(void)
{
	struct sock_filter filter[] = {
		BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
		BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
		BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
		/* x32 ABI numbers carry bit 30 and would dodge the checks below. */
		BPF_JUMP(BPF_JMP | BPF_JGE | BPF_K, 0x40000000, 0, 1),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
		DENY(__NR_keyctl), DENY(__NR_add_key), DENY(__NR_request_key),
		DENY(__NR_unshare), DENY(__NR_mount), DENY(__NR_umount2),
		DENY(__NR_ptrace), DENY(__NR_kexec_load), DENY(__NR_init_module),
		DENY(__NR_finit_module), DENY(__NR_bpf),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
	};
	struct sock_fprog prog = { sizeof(filter) / sizeof(filter[0]), filter };

	CHECK(prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0));
	CHECK(syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER, 0, &prog));
}

static int child(void *rootfs)
{
	char c;

	close(sync_pipe[1]);
	if (read(sync_pipe[0], &c, 1) != 1)
		DIE("wait for parent");
	CHECK(sethostname("minicontainer", 13));
	enter_rootfs(rootfs);
	drop_caps();
	install_seccomp();
	execvp(child_argv[0], child_argv); /* Step 6 */
	DIE("execvp");
}

int main(int argc, char **argv)
{
	static char stack[1 << 20];
	char cg[64], path[96], pid_s[16];
	int status;
	pid_t pid;

	if (argc < 3) {
		fprintf(stderr, "usage: %s <rootfs> <cmd> [args...]\n", argv[0]);
		return 2;
	}
	child_argv = &argv[2];

	/* Step 1: a cgroup with memory and pid limits. */
	snprintf(cg, sizeof(cg), "/sys/fs/cgroup/minicontainer-%d", getpid());
	CHECK(mkdir(cg, 0755));
	snprintf(path, sizeof(path), "%s/memory.max", cg);
	write_file(path, "64M");
	snprintf(path, sizeof(path), "%s/memory.swap.max", cg);
	write_file(path, "0");
	snprintf(path, sizeof(path), "%s/pids.max", cg);
	write_file(path, "64");

	/* Step 2: new namespaces; the child blocks until the pipe is written. */
	CHECK(pipe(sync_pipe));
	pid = clone(child, stack + sizeof(stack),
		    CLONE_NEWNS | CLONE_NEWPID | CLONE_NEWUTS | CLONE_NEWIPC |
		    CLONE_NEWNET | SIGCHLD, argv[1]);
	CHECK(pid);
	close(sync_pipe[0]);

	snprintf(path, sizeof(path), "%s/cgroup.procs", cg);
	snprintf(pid_s, sizeof(pid_s), "%d", pid);
	write_file(path, pid_s);

	/* A real runtime does this over netlink; ip(8) keeps it readable. */
	run("ip link add mc-host type veth peer name mc-guest");
	run("ip link set mc-guest netns %d", pid);
	run("ip addr add 10.200.0.1/24 dev mc-host && ip link set mc-host up");
	run("nsenter -t %d -n sh -c 'ip addr add 10.200.0.2/24 dev mc-guest &&"
	    " ip link set mc-guest up && ip link set lo up'", pid);

	CHECK(write(sync_pipe[1], "x", 1));
	close(sync_pipe[1]);
	CHECK(waitpid(pid, &status, 0));

	/* Cleanup: the veth pair died with the netns; the cgroup is now empty. */
	CHECK(rmdir(cg));
	return WIFEXITED(status) ? WEXITSTATUS(status) : 128 + WTERMSIG(status);
}
```

```make title="Makefile"
CFLAGS ?= -O2 -Wall -Wextra

minicontainer: minicontainer.c
	$(CC) $(CFLAGS) -o $@ minicontainer.c

clean:
	rm -f minicontainer
```

### Step 1: the cgroup

`main()` creates the cgroup directory directly under `/sys/fs/cgroup` and writes three limits.
`memory.swap.max=0` is not in the original plan. It makes the memory limit a real limit: without
it, on a host with swap, the memory hog below would be swapped out instead of killed. The VM has no
swap, but the program should not depend on that.

On a systemd host the cgroup tree belongs to systemd. Writing directly under the root works, and
systemd left this cgroup alone for the few seconds it existed. But a long-lived runtime asks systemd
for a delegated subtree instead (a transient scope with `Delegate=yes`), which is what runc's
systemd cgroup driver does.

### Step 2: namespaces and the network

`clone()` with five `CLONE_NEW*` flags creates the child already inside its new namespaces. The
child is PID 1 in its PID namespace, but the parent sees its host PID. The parent then uses that PID
twice: it writes it to `cgroup.procs`, and it passes it to `ip link set … netns <pid>`, which moves
the veth end into the namespace the process belongs to.

The network setup calls `ip` through `system()`, plus `nsenter -n` to configure the child's end from
inside its namespace. That keeps the program readable. A real runtime builds the same netlink
messages itself, or hands the job to a CNI plugin.

### Step 3: the root filesystem

The order is forced by `pivot_root(2)`'s `EINVAL` conditions:

- `mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL)` first. `pivot_root` refuses if the current
  root or the new root's parent mount is **shared**, and systemd makes `/` shared. Without this line,
  mounts and unmounts in the container would also propagate to the host.
- Then **bind-mount the rootfs onto itself**. `pivot_root` needs the new root to be a mount point,
  and a plain directory is not.
- `pivot_root(".", ".oldroot")` swaps the roots. `umount2("/.oldroot", MNT_DETACH)` then drops the
  host's whole tree from this namespace. Until that line runs, the host filesystem is still reachable
  at `/.oldroot`.

glibc has no `pivot_root()` wrapper, so the code calls `syscall(SYS_pivot_root, …)`.

### Step 4: capabilities

`drop_caps()` builds a 64-bit mask of the 14 kept capabilities. It calls `PR_CAPBSET_DROP` for every
other capability the kernel knows about. The loop stops where `PR_CAPBSET_READ` fails, so it adapts
to the running kernel's `cap_last_cap`. Then a single `capset` sets the permitted, effective and
inheritable sets to the mask.

The code uses the raw `capset` syscall and not libcap. With `_LINUX_CAPABILITY_VERSION_3`, the
syscall takes two 32-bit halves of each set. That is the only awkward part, and it is two lines. In
return the lab needs nothing beyond kernel headers.

The bounding set is the one that matters for `execve()`. For a root process, exec recomputes the new
permitted set as roughly "everything, limited by the bounding set". So setting only the effective
set would be undone at the next exec. That is why `CapBnd` in the transcript equals `CapEff`.

### Step 5: seccomp

`install_seccomp()` loads a classic BPF program that runs on every syscall:

1. Check `seccomp_data.arch` is `AUDIT_ARCH_X86_64`, and kill the process otherwise. Syscall numbers
   differ per architecture, so a filter that skipped this check could be bypassed through the
   32-bit `int 0x80` entry, where number 165 means something else.
2. Return `EPERM` for any number with bit 30 set: the **x32 ABI**, which shares `AUDIT_ARCH_X86_64`
   but has its own numbers. This is not in the original plan. It is the hole an arch-only check
   leaves open.
3. Compare the number against eleven denied syscalls, and return `SECCOMP_RET_ERRNO | EPERM` on a
   match. Everything else gets `SECCOMP_RET_ALLOW`.

This is a **denylist**, small enough to read. Docker's and Podman's default profiles are allowlists
of over 300 syscalls with argument checks, because a denylist fails open for every syscall added
in later kernels.

The filter needs `no_new_privs` because Step 4 has already dropped `CAP_SYS_ADMIN`. Without that
capability the kernel refuses `SECCOMP_SET_MODE_FILTER` with `EACCES` unless `no_new_privs` is set.

### Step 6: exec

`execvp()` replaces the child with the command. The new program starts with the cgroup, namespaces,
root, capability sets and filter already in place, and it can't undo any of them: the filter denies
`mount` and `unshare`, and the capabilities that would allow the rest are gone from the bounding set.

## Run it

<Lab host="qemu" title="Build minicontainer, run a shell in it, and check every layer" time="20 min">

:::warning
This runs as root and changes host state while it runs: a cgroup under `/sys/fs/cgroup` and a veth
interface. Both go away when the container exits. Nothing is lost if it fails halfway, but see
[Clean up](#clean-up).
:::

On the folder-01 Debian VM (Debian 13, `gcc`, `iproute2`). Copy `static/code/linux/minicontainer/`
into the VM, then:

```bash
./setup-rootfs.sh && make
sudo ./minicontainer ./rootfs /bin/sh
```

Inside, run the checks. The transcript below ran them in one `/bin/sh -c` script with `set -x`.
From a second shell on the host, read the cgroup while the container is still running. The host
`ip link` before and after shows the cleanup.

```text
--- host before:
lo               UNKNOWN        00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP> 
ens3             UP             52:54:00:12:34:56 <BROADCAST,MULTICAST,UP,LOWER_UP> 
--- container:
+ hostname
minicontainer
+ ps
PID   USER     TIME  COMMAND
    1 root      0:00 /bin/sh -c set -x hostname ps …
    3 root      0:00 ps
+ grep -E 'Cap|Seccomp|NoNewPrivs' /proc/self/status
CapInh:	00000000a80425fb
CapPrm:	00000000a80425fb
CapEff:	00000000a80425fb
CapBnd:	00000000a80425fb
CapAmb:	0000000000000000
NoNewPrivs:	1
Seccomp:	2
Seccomp_filters:	1
+ ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
29: mc-guest@if30: <BROADCAST,MULTICAST,UP,LOWER_UP,M-DOWN> mtu 1500 qdisc noqueue state UP qlen 1000
    link/ether a2:33:a3:87:50:88 brd ff:ff:ff:ff:ff:ff
    inet 10.200.0.2/24 scope global mc-guest
       valid_lft forever preferred_lft forever
    inet6 fe80::a033:a3ff:fe87:5088/64 scope link tentative 
       valid_lft forever preferred_lft forever
+ ping -c1 10.200.0.1
PING 10.200.0.1 (10.200.0.1): 56 data bytes
64 bytes from 10.200.0.1: seq=0 ttl=64 time=1.060 ms

--- 10.200.0.1 ping statistics ---
1 packets transmitted, 1 packets received, 0% packet loss
round-trip min/avg/max = 1.060/1.060/1.060 ms
+ mount -t tmpfs x /mnt
mount: permission denied (are you root?)
+ head -c 209715200 /dev/zero
+ tail
Killed
+ echo 137
137
+ sleep 8
--- host, while it runs:
mc-host@if29     UP             42:fe:49:f6:e8:cf <BROADCAST,MULTICAST,UP,LOWER_UP> 
low 0
high 0
max 70
oom 3
oom_kill 1
oom_group_kill 0
--- host after:
lo               UNKNOWN        00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP> 
ens3             UP             52:54:00:12:34:56 <BROADCAST,MULTICAST,UP,LOWER_UP> 
(no cgroup)
```

`ps`'s long command line is cut at `…`. Everything else is verbatim, from
`uname -r` `6.12.113+deb13-cloud-amd64` and BusyBox 1.37.0.

Read it layer by layer:

- **UTS and PID namespaces.** `hostname` is `minicontainer`. `ps` shows two processes: the shell as
  PID 1 and `ps` itself as PID 3. PID 2 was `hostname`, which ran and exited. The plan expected PIDs
  1 and 2; BusyBox's `hostname` runs as a separate process, not inside the shell.
- **Capabilities.** All four sets are `a80425fb`, which is exactly Docker's default. `NoNewPrivs: 1`
  and `Seccomp: 2` (filter mode) show Step 5.
- **The network namespace.** Only `lo` and `mc-guest` exist inside. The host side, `mc-host`, shows
  up on the host only while the container runs. `ping` reaches the host end of the pair.
- **seccomp.** `mount -t tmpfs x /mnt` fails with "permission denied". The filter returned `EPERM`
  before the kernel's capability check could. (`CAP_SYS_ADMIN` is gone too, so either layer alone
  would have refused.)
- **The memory cgroup.** `tail` buffers its input looking for the last lines, so 200 MiB with no
  newline grows its memory without bound. At 64 MiB the OOM killer killed it (exit status 137 is
  128 + `SIGKILL`). On the host, `memory.events` counted the allocations that hit `max` and one
  `oom_kill`. The shell survived because the kill is targeted.

If it fails:

- `pivot_root: Invalid argument` → the new root is not a mount point, or `/` is still shared. The
  bind-mount and `MS_PRIVATE` lines exist for exactly this.
- `mkdir(cg, 0755): Permission denied` → not run as root.
- `/sys/fs/cgroup/.../memory.max: No such file or directory` → the `memory` controller is not
  enabled in `/sys/fs/cgroup/cgroup.subtree_control`.
- `RTNETLINK answers: File exists` → a veth called `mc-host` survived a crashed run. Delete it with
  `sudo ip link del mc-host`.

</Lab>

:::note[What the lab needed that the plan did not foresee]
- **An empty `/dev`.** The minirootfs ships `/dev` with no nodes, and `head` needs `/dev/zero`. The
  code mounts a tmpfs on `/dev` and creates `null` and `zero` with `mknod`. runc creates a dozen
  nodes plus `/dev/pts`, `/dev/shm` and the standard symlinks.
- **No `/sys` inside.** Reading `/sys/fs/cgroup/memory.max` in the container fails with "No such
  file". This runtime never mounts sysfs, and with no cgroup namespace the container would see the
  host's whole cgroup tree if it did. runc mounts sysfs read-only and unshares the cgroup namespace.
- **BusyBox's `head` wants bytes.** `head -c 200M` is "invalid number". Use `head -c 209715200`.
- **TCG is slow.** Under software emulation the OOM kill took several seconds, so the host-side read
  of `memory.events` happens 9 seconds in. An earlier read at 3 seconds showed all zeros.
:::

## What runc does that this does not

The six steps are the whole mechanism, but runc wraps them in a great deal of robustness:

- **User namespaces** for rootless mode, with the UID/GID maps written by the parent before the
  child continues. The same pipe handshake, one more step ([User Namespaces](./user-namespaces.md)).
- **cgroups through systemd** when the systemd driver is chosen, a cgroup namespace, and a read-only
  cgroup mount.
- **An allowlist seccomp profile** with per-argument rules (for example, `clone` allowed only
  without namespace flags), from the OCI config.
- **A complete `/dev`**, `/dev/pts` with a new `devpts` instance, and `/dev/console` for a TTY.
- **Masked and read-only paths.** `/proc/kcore`, `/proc/keys`, `/proc/sys` and others are
  over-mounted so the container can't read or write host state through them.
- **rlimits, an AppArmor or SELinux label, `no_new_privs` on request, OCI hooks**, and the
  `create`/`start` split that lets a caller set up networking between the two.
- **Reading all of this from a `config.json`** in an OCI bundle, which is what
  [Images, Layers, and OCI](./images-layers-and-oci.md) covers.

## Clean up

The program cleans up after itself. When the child exits:

- **The veth pair is already gone.** When a network namespace is destroyed, its interfaces are
  destroyed, and deleting one end of a veth pair deletes the other. The program has no code for
  this, and the host `ip link` after the run shows that none is needed.
- **The cgroup is removed by `rmdir`.** A cgroup can be removed only when it has no processes, and
  once the container's PID 1 has exited the kernel has killed everything else in its PID namespace.

After a crash (or a `kill -9` of `minicontainer` itself), remove both by hand:

```bash
sudo ip link del mc-host 2>/dev/null
sudo rmdir /sys/fs/cgroup/minicontainer-*
ls /sys/fs/cgroup | grep minicontainer   # expect no output
```

Delete the rootfs with `rm -rf rootfs`.

<KernelFacts
  structure={[["struct nsproxy", "include/linux/nsproxy.h"], ["struct seccomp_filter", "kernel/seccomp.c"]]}
  path="clone(CLONE_NEW*) → [parent: cgroup.procs, veth] → pivot_root() → capset() → prctl(NO_NEW_PRIVS) → seccomp(SET_MODE_FILTER) → execvp()"
  observe="sudo ./minicontainer ./rootfs /bin/grep -E 'Cap|Seccomp' /proc/self/status"
  trap="Order matters. Install the seccomp filter after `pivot_root` and the mounts, because the filter denies `mount`. Drop capabilities before `exec`, because a capability dropped after `exec` was never dropped for the new program's first instructions." />

## References

- [clone(2)](https://man7.org/linux/man-pages/man2/clone.2.html),
  [pivot_root(2)](https://man7.org/linux/man-pages/man2/pivot_root.2.html) (the `EINVAL` list and
  the `pivot_root(".", ".")` idiom), [seccomp(2)](https://man7.org/linux/man-pages/man2/seccomp.2.html)
  (the architecture check, and why the x32 bit matters).
- <Src file="fs/namespace.c" symbol="pivot_root" /> — the `EINVAL` checks in order;
  <Src file="kernel/seccomp.c" symbol="seccomp_prepare_filter" /> — the `no_new_privs` or
  `CAP_SYS_ADMIN` precondition.
- Liz Rice, *Container Security* (O'Reilly, 2020), ch. 4 — the same construction, in Go.
- runc's [`libcontainer/nsenter/nsexec.c`](https://github.com/opencontainers/runc/blob/main/libcontainer/nsenter/nsexec.c)
  and [`libcontainer/standard_init_linux.go`](https://github.com/opencontainers/runc/blob/main/libcontainer/standard_init_linux.go)
  — the production version of this lab.
- [Alpine Linux downloads](https://alpinelinux.org/downloads/) — the minirootfs and its checksums
  (`latest-releases.yaml`).
