---
id: namespaces-overview
title: "Namespaces"
sidebar_label: "Namespaces"
sidebar_position: 2
tags: [linux, kernel, containers]
prerequisites:
  - linux/containers-and-virtualization/what-a-container-actually-is
  - linux/processes-and-threads/task-struct-the-anatomy-of-a-task
draft: false
---

# Namespaces

A namespace wraps one kind of global resource so that a group of processes gets its own copy of
it: its own hostname, its own PID numbers, its own mount table, its own network stack. Linux has
eight kinds. All of them work the same way:

- **create** one with a `CLONE_NEW*` flag;
- **join** one through a file descriptor, with `setns()`;
- **inspect** one through `/proc/PID/ns`.

This page covers the common machinery. The two namespaces with the most surprising semantics, mount
and PID, get [their own page](./mount-and-pid-namespaces.md), and so does the user namespace,
which changes what privilege means ([User Namespaces](./user-namespaces.md)).

## The eight namespaces

| Namespace | Flag | Isolates | Since | Covered in |
|---|---|---|---|---|
| Mount | `CLONE_NEWNS` | The mount table: which filesystems are mounted where | 2.4.19 | [Mounts and Mount Namespaces](../11-vfs-and-filesystems/mounts-and-mount-namespaces.md), [Mount and PID Namespaces](./mount-and-pid-namespaces.md) |
| UTS | `CLONE_NEWUTS` | Hostname and NIS domain name | 2.6.19 | this page |
| IPC | `CLONE_NEWIPC` | System V IPC objects and POSIX message queues | 2.6.19 | this page |
| PID | `CLONE_NEWPID` | Process ID numbers | 2.6.24 | [Mount and PID Namespaces](./mount-and-pid-namespaces.md) |
| Network | `CLONE_NEWNET` | Interfaces, addresses, routes, firewall rules, sockets, `/proc/sys/net` | 2.6.24 | [Network Namespaces and Virtual Devices](../13-networking-stack/network-namespaces-and-virtual-devices.md) |
| User | `CLONE_NEWUSER` | UIDs, GIDs, and capabilities relative to them | 3.8 (usable) | [User Namespaces](./user-namespaces.md) |
| Cgroup | `CLONE_NEWCGROUP` | The view of the cgroup hierarchy: which cgroup appears as root | 4.6 | [cgroup v2](./cgroup-v2-architecture.md) |
| Time | `CLONE_NEWTIME` | Offsets for `CLOCK_MONOTONIC` and `CLOCK_BOOTTIME` (not the wall clock) | 5.6 | this page |

The user namespace flag existed from 2.6.23, but the namespace became complete and safe to use only
in 3.8.

The UTS, IPC and time namespaces need no page of their own. A **UTS namespace** gives a container
its own hostname (`sethostname()` changes only its copy). An **IPC namespace** gives it a private
set of System V shared memory segments, semaphores and message queues, plus its own POSIX message
queue filesystem. A **time namespace** lets a process see a different "time since boot", which is
mostly useful for checkpointing a container on one machine and restoring it on another; it cannot
change the wall-clock time.

## Creating: `clone`, `clone3`, `unshare`

Three system calls create namespaces:

- **`clone()` and `clone3()`** with `CLONE_NEW*` flags create the namespaces *and* a new process
  inside them, in one step. Runtimes use this.
- **`unshare(flags)`** moves the *calling* process into new namespaces, except for PID and time
  namespaces, where it applies only to the caller's future children. The `unshare(1)` command wraps
  it.

Creating any namespace except a user namespace requires `CAP_SYS_ADMIN` in the user namespace that
will own it. A process that first creates a user namespace gains a full capability set inside it,
and can then create the others: that is how rootless containers start.

The flags are bits in the clone-flags word:

```wavedrom title="The CLONE_NEW* bits in the clone flags word (from include/uapi/linux/sched.h). CLONE_NEWTIME sits inside the low byte, which clone() reserves for the exit signal" alt="Bit-field strip of the low 32 bits of the clone flags: bits 0-7 CSIGNAL with CLONE_NEWTIME at bit 7, bit 17 CLONE_NEWNS, bits 25 to 30 CLONE_NEWCGROUP, NEWUTS, NEWIPC, NEWUSER, NEWPID, NEWNET"
{ reg: [
    { bits: 7, name: "CSIGNAL (exit signal)", type: 5 },
    { bits: 1, name: "NEWTIME", type: 4 },
    { bits: 9, name: "other CLONE_* flags" },
    { bits: 1, name: "NEWNS", type: 2 },
    { bits: 7, name: "other CLONE_* flags" },
    { bits: 1, name: "NEWCGROUP", type: 2 },
    { bits: 1, name: "NEWUTS", type: 2 },
    { bits: 1, name: "NEWIPC", type: 2 },
    { bits: 1, name: "NEWUSER", type: 3 },
    { bits: 1, name: "NEWPID", type: 2 },
    { bits: 1, name: "NEWNET", type: 2 },
    { bits: 1, name: "" }
  ],
  config: { hspace: 1000, bits: 32, lanes: 1 }
}
```

The odd one out is `CLONE_NEWTIME` (`0x80`). By the time it was added, every high bit of the
32-bit word was taken, so it reused a bit inside `CSIGNAL`, the byte that `clone()` uses for the
child's exit signal. The header says so directly: those flags "intersect with CSIGNAL so can be used
with unshare and clone3 syscalls only". `clone3()` takes a structure with the exit signal in its
own field, which is one reason it exists.

## Joining: `setns` and `nsenter`

`setns(fd, nstype)` moves the caller into the namespace `fd` refers to. The descriptor comes from
opening a `/proc/PID/ns/*` file, or, since 5.8, it can be a **pidfd**: `setns(pidfd, CLONE_NEWNET |
CLONE_NEWUTS)` joins several of that process's namespaces atomically. `nsenter(1)` wraps it:
`nsenter -t <pid> -n ip addr` runs `ip addr` inside a container's network namespace using the
host's `ip` binary. That is the standard way to debug container networking from the host.

## `/proc/PID/ns` as the handle

Each process has one symbolic link per namespace type in `/proc/PID/ns/`. The link target,
`net:[4026532276]`, is the namespace's **identity**: two processes are in the same namespace if and
only if their links show the same inode number. Two extra links, `pid_for_children` and
`time_for_children`, show where the process's *future* children will go, which differs from `pid`
and `time` right after an `unshare`.

Opening the file gives a descriptor that keeps the namespace alive. Bind-mounting it does the same,
without any process holding it open. `ip netns add` is exactly that: it creates a network namespace
and bind-mounts its handle at `/run/netns/<name>`.

## Ownership: every namespace has a user namespace

Every non-user namespace is **owned by** the user namespace that was current when it was created.
Capability checks for operations on a namespace's resources are made against that owning user
namespace. For example, `CAP_NET_ADMIN` is checked against the user namespace that owns the network
namespace. That rule is what makes rootless containers possible without making them root;
[User Namespaces](./user-namespaces.md) explains it.

## Lifetime

A namespace lives as long as anything references it: a process inside it, an open
`/proc/PID/ns/*` descriptor, a bind mount of its handle, or a child namespace. When the last
reference goes, the kernel tears it down. For a network namespace, that means destroying its
interfaces and closing its sockets. A namespace whose last process exited but whose handle is
still bind-mounted therefore stays alive, invisible to `ps`.

<Lab host="qemu" title="Create UTS and PID namespaces with unshare, then look in from outside" time="10 min">

On the folder-01 Debian VM. Start a shell in new UTS and PID namespaces, change its hostname, and
leave it running for 30 seconds while you inspect it from the host:

```bash
sudo unshare --uts --pid --fork --mount-proc \
    sh -c 'hostname lab; hostname; echo $$; ps -o pid,cmd; sleep 30' &
sleep 3
hostname
P=$(pgrep -f '^sleep 30'); grep NSpid /proc/$P/status
sudo nsenter -t $P -u hostname
sudo lsns -t uts -t pid -o NS,TYPE,NPROCS,PID,COMMAND
```

Measured (`uname -r`: `6.12.113+deb13-cloud-amd64`; long command lines trimmed with `…`):

```text
lab
1
    PID CMD
      1 sh -c hostname lab; hostname; echo $$; ps -o pid,cmd; sleep 30
      4 ps -o pid,cmd
$ hostname
kblab
$ grep NSpid /proc/$P/status
NSpid:	7018	6
$ sudo nsenter -t $P -u hostname
lab
$ sudo lsns -t uts -t pid -o NS,TYPE,NPROCS,PID,COMMAND
        NS TYPE NPROCS   PID COMMAND
4026531836 pid     116     1 /sbin/init
4026531838 uts     112     1 /sbin/init
4026532271 uts       1   394 ├─/usr/lib/systemd/systemd-udevd
4026532272 uts       1   384 ├─/usr/lib/systemd/systemd-timesyncd
4026532274 uts       1   822 └─/usr/lib/systemd/systemd-logind
4026532277 uts       3  7012 unshare --uts --pid --fork --mount-proc sh -c hostname lab; …
4026532278 pid       2  7013 └─sh -c hostname lab; …
```

What each part shows:

- **Inside**, the hostname is `lab`, the shell is PID 1, and `ps` sees only two processes:
  `--mount-proc` mounted a fresh `/proc` for the new PID namespace.
- **Outside**, the hostname is unchanged (`kblab`). The `sleep` is PID 7018 on the host and PID 6
  inside: `NSpid` lists its number in every PID namespace it belongs to, outermost first.
- **`nsenter -u`** joined only the UTS namespace and saw `lab`.
- **The new UTS namespace has three processes, the new PID namespace two.** `unshare` itself moved
  into the new UTS namespace, but *not* into the new PID namespace. It forked (`--fork`), and only
  the child, the `sh`, became PID 1 there. That is the `unshare(CLONE_NEWPID)` rule in action.
- **systemd services already use namespaces.** `systemd-udevd`, `systemd-timesyncd` and
  `systemd-logind` each run in a private UTS namespace, from their units' `ProtectHostname=yes`.
  Namespaces are not only a container feature.

Cleanup: none needed. The namespaces disappear when the `sleep` finishes and its shell exits.

If it fails: `unshare: unshare failed: Operation not permitted` means the command ran without
`sudo`. Without a user namespace, creating these namespaces needs `CAP_SYS_ADMIN`.

</Lab>

<KernelFacts
  structure={[["struct nsproxy", "include/linux/nsproxy.h"], ["struct ns_common", "include/linux/ns_common.h"]]}
  path="unshare(CLONE_NEWUTS) → ksys_unshare() → unshare_nsproxy_namespaces() → create_new_namespaces() → switch_task_namespaces()"
  observe="lsns; ls -l /proc/self/ns"
  trap="`unshare(CLONE_NEWPID)` does not move the caller. Only its *next child* becomes PID 1 in the new namespace, which is why `unshare --pid` needs `--fork`, and why the `unshare` process itself stays outside." />

## References

- [namespaces(7)](https://man7.org/linux/man-pages/man7/namespaces.7.html) — the namespace types,
  `/proc/PID/ns`, and the lifetime rules.
- [clone(2)](https://man7.org/linux/man-pages/man2/clone.2.html),
  [unshare(2)](https://man7.org/linux/man-pages/man2/unshare.2.html) and
  [setns(2)](https://man7.org/linux/man-pages/man2/setns.2.html) — creating and joining namespaces,
  including the kernel version each flag appeared in and pidfd-based `setns`.
- Kerrisk, ["Namespaces in operation, part 1: namespaces overview"](https://lwn.net/Articles/531114/)
  (LWN, 2013) — the series that introduced most readers to namespaces. It predates the cgroup and
  time namespaces.
- <Src file="kernel/nsproxy.c" symbol="create_new_namespaces" /> — where a task's namespace set is
  copied with selected members replaced.
