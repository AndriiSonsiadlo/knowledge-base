---
id: capabilities-in-containers
title: "Capabilities and Container Privilege"
sidebar_label: "Container privilege"
sidebar_position: 7
tags: [linux, kernel, containers]
prerequisites:
  - linux/containers-and-virtualization/user-namespaces
  - linux/security/capabilities
related:
  - linux/security/seccomp
draft: false
---

# Capabilities and Container Privilege

A container started by root runs as root. `id` inside prints `uid=0`, and on a rootful runtime that
UID 0 is the host's UID 0. So what stops it doing everything root can? Mostly the **capability
set**. Runtimes keep 11 to 14 of root's 41 capabilities by default. `--privileged` puts all of them
back and turns off most of the other guards too. This page covers what the default keeps, what
`--privileged` actually disables, and which capabilities are root by another name.
[Capabilities](../16-security/capabilities.md) owns the model itself: the five sets and the
`execve()` transformation. Here we look only at how containers use it.

## The default set

Measured, not quoted: `grep Cap /proc/self/status` in an Alpine container, decoded with
`capsh --decode`. Docker's list matches its documentation and moby's `oci/caps/defaults.go`.
Podman 5 dropped three more from its default.

| Capability | Bit | Docker 29.8 | Podman 5.4 (crun) | What it allows |
|---|---|---|---|---|
| `CAP_CHOWN` | 0 | ✓ | ✓ | Change any file's owner |
| `CAP_DAC_OVERRIDE` | 1 | ✓ | ✓ | Bypass read/write/execute permission checks |
| `CAP_FOWNER` | 3 | ✓ | ✓ | Act as the owner of any file (chmod, utime) |
| `CAP_FSETID` | 4 | ✓ | ✓ | Keep setuid/setgid bits when modifying a file |
| `CAP_KILL` | 5 | ✓ | ✓ | Signal any process (in the container's PID namespace) |
| `CAP_SETGID` | 6 | ✓ | ✓ | Set arbitrary GIDs |
| `CAP_SETUID` | 7 | ✓ | ✓ | Set arbitrary UIDs |
| `CAP_SETPCAP` | 8 | ✓ | ✓ | Drop bounding-set bits; grant inheritable caps |
| `CAP_NET_BIND_SERVICE` | 10 | ✓ | ✓ | Bind ports below 1024 |
| `CAP_NET_RAW` | 13 | ✓ | — | Raw and packet sockets (classic `ping`, packet spoofing) |
| `CAP_SYS_CHROOT` | 18 | ✓ | ✓ | `chroot()` |
| `CAP_MKNOD` | 27 | ✓ | — | Create device nodes (opening them is still up to the device cgroup) |
| `CAP_AUDIT_WRITE` | 29 | ✓ | — | Write to the kernel audit log |
| `CAP_SETFCAP` | 31 | ✓ | ✓ | Set file capabilities |
| **Bitmask** | | `a80425fb` | `800405fb` | |

Everything else is gone, including `CAP_SYS_ADMIN`, `CAP_NET_ADMIN`, `CAP_SYS_MODULE`,
`CAP_SYS_PTRACE`, `CAP_SYS_TIME`, `CAP_SYS_BOOT`, `CAP_DAC_READ_SEARCH` and `CAP_BPF`. They are
dropped from the **bounding set**, not just the effective set, so no `execve()` of a setuid or
file-capability binary inside the container can bring them back.

```wavedrom title="The low 32 bits of the effective set in a default Docker container (a80425fb). Kept bits in colour; bits 32–40 are all dropped" alt="Bit-field strip of capability bits 0 to 31, with CHOWN, DAC_OVERRIDE, FOWNER, FSETID, KILL, SETGID, SETUID, SETPCAP, NET_BIND_SERVICE, NET_RAW, SYS_CHROOT, MKNOD, AUDIT_WRITE and SETFCAP highlighted as kept"
{ reg: [
  { bits: 1, name: "CHOWN", type: 2 },
  { bits: 1, name: "DAC_OVR", type: 2 },
  { bits: 1, name: "DAC_RS" },
  { bits: 1, name: "FOWNER", type: 2 },
  { bits: 1, name: "FSETID", type: 2 },
  { bits: 1, name: "KILL", type: 2 },
  { bits: 1, name: "SETGID", type: 2 },
  { bits: 1, name: "SETUID", type: 2 },
  { bits: 1, name: "SETPCAP", type: 2 },
  { bits: 1, name: "IMMUT" },
  { bits: 1, name: "NET_BIND", type: 2 },
  { bits: 2, name: "BCAST ADMIN" },
  { bits: 1, name: "NET_RAW", type: 2 },
  { bits: 4, name: "IPC SYS_MODULE RAWIO" },
  { bits: 1, name: "CHROOT", type: 2 },
  { bits: 8, name: "PTRACE … SYS_ADMIN … TTY_CONFIG" },
  { bits: 1, name: "MKNOD", type: 2 },
  { bits: 1, name: "LEASE" },
  { bits: 1, name: "AUDIT_W", type: 2 },
  { bits: 1, name: "AUDIT_C" },
  { bits: 1, name: "SETFCAP", type: 2 }
], config: { hspace: 900, lanes: 2 } }
```

## What `--privileged` turns off

`--privileged` is not "a few more capabilities". It switches off nearly every guard the runtime
applies. Measured with `podman run --privileged` on the Debian VM; the device and LSM items are also
stated in Docker's `run` reference:

| Guard | Default container | `--privileged` |
|---|---|---|
| Capabilities | 11 (Podman) / 14 (Docker) | All 41: `CapEff: 000001ffffffffff` |
| seccomp | Runtime's filter (`Seccomp: 2`) | None (`Seccomp: 0`) |
| AppArmor / SELinux | `containers-default-0.62.2 (enforce)` | `crun (unconfined)` |
| `/dev` | 15 entries: a minimal tmpfs | 139 entries: every host device node |
| Device cgroup | Only the minimal devices are allowed | All devices allowed |
| `/sys`, `/sys/fs/cgroup` | Mounted `ro` | Mounted `rw` |
| `/proc/kcore`, `/proc/sys`, … | Masked or read-only | Visible and writable |

Each row on its own is a way out. All of them together leave a container that differs from a host
root shell mostly in its namespaces, and a root process with every capability can enter or undo
those too. Use `--cap-add` with the one capability you need, or `--device` for one device, instead.

:::note[Docker Desktop's seccomp counts]
On Docker Desktop (WSL 2) the same measurement shows `Seccomp_filters: 3` by default and `2` with
`--privileged`, not `1` and `0`. The Docker engine itself runs inside a filtered environment, and
seccomp filters are inherited and can't be removed. `--privileged` removes only the filter Docker
added. A Docker engine running directly on a Linux host shows `0`.
:::

## `no_new_privs`

The bounding set stops a capability coming back through `execve()`. `no_new_privs`
(`prctl(PR_SET_NO_NEW_PRIVS, 1)`) closes the rest of that door. Once it is set, which is
irreversible and inherited across `fork` and `execve`, setuid and setgid bits and file capabilities
are ignored at exec time: `execve()` can only keep or reduce privilege. That is what
`--security-opt no-new-privileges` sets, and Kubernetes' `allowPrivilegeEscalation: false`. Neither
Docker nor Podman sets it by default (`NoNewPrivs: 0` above), because some images rely on `su` or
`sudo` inside.

Its second job is seccomp's precondition. An unprivileged process may install a seccomp filter
only if `no_new_privs` is set. Otherwise it could filter a setuid binary's syscalls and make that
binary misbehave in a privileged context. With `CAP_SYS_ADMIN` the requirement is lifted, which is
why runtimes running as root can apply a filter without setting it. The
[container lab](./building-a-container-from-scratch.md) drops `CAP_SYS_ADMIN` first, so it has to
set `no_new_privs` before installing its filter.

## Capabilities that are root

Some capabilities are narrow. Others give enough control over the kernel that the holder can turn
them into all the others. Granting one of these is granting root:

- **`CAP_SYS_ADMIN`** — the catch-all. It covers `mount`, namespace creation, `setns`, many device
  `ioctl`s and dozens of other operations. Mounting alone lets a process reshape what every program
  in its mount namespace sees, including the files it executes.
- **`CAP_SYS_MODULE`** — loads kernel modules. Kernel code runs with no boundary at all.
- **`CAP_BPF`** with **`CAP_PERFMON`** — loads tracing BPF programs that can read any kernel memory.
  Together with `CAP_NET_ADMIN` they also allow networking programs. (Before 5.8 all of this was
  under `CAP_SYS_ADMIN`.)
- **`CAP_SYS_PTRACE`** — attaches to any process the holder can see and rewrites its memory and
  registers. So the holder acts with that process's privileges. With `--pid=host` that means the
  host's processes.
- **`CAP_DAC_READ_SEARCH`** — besides bypassing read checks, it allows `open_by_handle_at()`, which
  opens a file by an opaque handle without walking a path. In 2014 the "shocker" exploit used this to
  guess handles on the host filesystem and read host files from inside a Docker container. This is
  why Docker removed the capability from its default.
- **`CAP_SYS_RAWIO`** and **`CAP_NET_ADMIN`** come close: raw I/O ports and `/dev/mem` for the
  first, and for the second, full control of the network namespace's firewall, routing and
  interfaces. With `--net=host`, that means the host's network.

## Rootless changes the question

Everything above assumes the container's root is the host's root. In a
[user namespace](./user-namespaces.md) the capabilities are real, but only over resources the
namespace owns. `CAP_SYS_ADMIN` there allows mounting a tmpfs in the container's own mount
namespace, but not loading a module or touching the host's network. Rootless Podman is
`--privileged`-shaped inside and unprivileged outside. The cost is the extra kernel surface a user
namespace exposes to unprivileged code (see [User Namespaces](./user-namespaces.md)).

<Lab host="qemu" title="Decode a container's capabilities, default and privileged" time="5 min">

On the folder-01 Debian VM with rootful Podman 5.4.2 (`sudo apt install podman libcap2-bin`):

```bash
for f in "" --privileged; do
  echo "=== podman run $f"
  sudo podman run --rm $f docker.io/library/alpine grep -E 'Cap|Seccomp|NoNewPrivs' /proc/self/status
done
/usr/sbin/capsh --decode=00000000800405fb
```

Measured (`uname -r`: `6.12.113+deb13-cloud-amd64`):

```text
=== podman run
CapInh:	0000000000000000
CapPrm:	00000000800405fb
CapEff:	00000000800405fb
CapBnd:	00000000800405fb
CapAmb:	0000000000000000
NoNewPrivs:	0
Seccomp:	2
Seccomp_filters:	1
=== podman run --privileged
CapInh:	0000000000000000
CapPrm:	000001ffffffffff
CapEff:	000001ffffffffff
CapBnd:	000001ffffffffff
CapAmb:	0000000000000000
NoNewPrivs:	0
Seccomp:	0
Seccomp_filters:	0
0x00000000800405fb=cap_chown,cap_dac_override,cap_fowner,cap_fsetid,cap_kill,cap_setgid,cap_setuid,cap_setpcap,cap_net_bind_service,cap_sys_chroot,cap_setfcap
```

- **The bounding set equals the effective set** in both runs. Dropping from the bounding set is what
  makes the default permanent for every process in the container.
- **`000001ffffffffff` is 41 bits**, capabilities 0 to 40 (`CAP_CHECKPOINT_RESTORE`), which matches
  `/proc/sys/kernel/cap_last_cap` (`40`) on this kernel.
- **`Seccomp: 2`** is filter mode. `--privileged` removed it as well, which is the less visible half
  of what the flag does.

The same loop with `docker run` on Docker 29.8.2 prints `a80425fb`: the three extra bits are
`CAP_NET_RAW`, `CAP_MKNOD` and `CAP_AUDIT_WRITE`.

If it fails: `capsh: command not found` as a normal user → it is in `/usr/sbin`, which is not on a
non-root user's `PATH` on Debian.

</Lab>

## Misconceptions

1. **"`--privileged` just grants extra capabilities."** It also removes the seccomp filter and the
   LSM profile, exposes every host device, and mounts `/sys` and the cgroup tree read-write. The
   capabilities are the smallest part of it.
2. **"Dropping `CAP_SYS_ADMIN` is enough."** Several other capabilities are root by another name
   (`CAP_SYS_MODULE`, `CAP_SYS_PTRACE`, `CAP_DAC_READ_SEARCH`, `CAP_BPF`). And capabilities are only
   one layer: seccomp and the LSM are what stop a kernel bug from being reached at all.
3. **"Capabilities inside a user namespace are real capabilities."** They are checked against the
   namespace that owns the resource. `CAP_NET_ADMIN` in a rootless container administers that
   container's network namespace and nothing of the host's.

<KernelFacts
  structure={[["kernel_cap_t", "include/linux/capability.h"], ["struct cred (cap_* fields)", "include/linux/cred.h"]]}
  path="execve() → bprm_creds_from_file() → cap_bprm_creds_from_file() → new effective = f(permitted, bounding, file caps, no_new_privs)"
  observe="grep Cap /proc/self/status; capsh --decode=$(awk '/CapEff/{print $2}' /proc/self/status)"
  trap="A container granted `CAP_SYS_ADMIN` 'just to mount something' has been granted most of root. Grant the narrowest capability or mount from outside." />

## References

- [capabilities(7)](https://man7.org/linux/man-pages/man7/capabilities.7.html) — every capability,
  the five sets, and the `execve()` transformation rules.
- Docker, ["Runtime privilege and Linux capabilities"](https://docs.docker.com/reference/cli/docker/container/run/#privileged)
  in the `docker run` reference — the default list and what `--privileged` grants. Checked via
  context7 (`/docker/docs`) on 2026-10-27, and measured against Docker 29.8.2.
- [moby `daemon/pkg/oci/caps/defaults.go`](https://github.com/moby/moby/blob/master/daemon/pkg/oci/caps/defaults.go)
  — the source of Docker's default list, linked from Docker's security documentation.
- `crun spec` and `podman run` output on the Debian VM — Podman's default, measured on 2026-10-27.
- [prctl(2)](https://man7.org/linux/man-pages/man2/prctl.2.html), `PR_SET_NO_NEW_PRIVS`, and the
  kernel's [No New Privileges Flag](https://docs.kernel.org/userspace-api/no_new_privs.html) document.
- <Src file="security/commoncap.c" symbol="cap_bprm_creds_from_file" /> — where exec computes the
  new capability sets.
