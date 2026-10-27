---
id: apparmor
title: "AppArmor"
sidebar_label: "AppArmor"
sidebar_position: 6
tags: [linux, kernel, security]
prerequisites:
  - linux/security/the-lsm-framework
draft: false
---

# AppArmor

AppArmor confines programs by **path**. A profile for `/usr/sbin/nginx` lists the files,
capabilities and network access that program may use, and everything not listed is denied. It is
easier to read and write than SELinux policy, and less expressive. The choice is about which
trade-off fits.

## Profiles by path

A profile **attaches** to a program by its executable path. When an `execve()` matches a profile's
attachment, the new process runs confined by it. Profiles live in `/etc/apparmor.d/`, are compiled
by `apparmor_parser` into a DFA, and are loaded into the kernel. The language:

```text
abi <abi/4.0>,
include <tunables/global>

profile nginx /usr/sbin/nginx {
  include <abstractions/base>          # libc, locale, /dev/null, …
  include <abstractions/nameservice>   # DNS, /etc/passwd lookups

  capability net_bind_service,
  capability setuid,
  capability setgid,
  network inet stream,

  /etc/nginx/** r,
  /srv/www/** r,
  /var/log/nginx/*.log w,
  /run/nginx.pid rw,
  /usr/sbin/nginx mr,
}
```

File rules are a path glob and permissions: `r`, `w`, `a` (append), `l` (link), `k` (lock), `m`
(map as executable), and for execution `ix` (inherit this profile), `px` (switch to the target's
own profile), `cx` (a child profile) or `ux` (unconfined). Upper-case `Px`/`Ux` also scrub
dangerous environment variables. `capability` and `network` rules grant exactly what they name.
**Abstractions** are shared include files for common needs.

## Complain versus enforce

Each profile is in one of two modes:

- **enforce** — denials are refused and logged.
- **complain** — nothing is refused, but everything that *would* have been denied is logged.

`aa-complain /usr/sbin/nginx` and `aa-enforce /usr/sbin/nginx` switch. The usual way to build a
profile is to start in complain mode, exercise the program, then run **`aa-logprof`**, which reads
the log and proposes rules interactively. `aa-status` shows what is loaded. The VM has 109 profiles
loaded, 10 of them in enforce mode.

## Reading a denial

AppArmor logs through the audit subsystem. With `auditd` running, denials go to
`/var/log/audit/audit.log` as `type=AVC` records. Without it, they go to the kernel log. From the
lab below:

```text
type=AVC msg=audit(1793107046.273:2126): apparmor="DENIED" operation="open" class="file" profile="aacat" name="/srv/secret/key" pid=11395 comm="aacat" requested_mask="r" denied_mask="r" fsuid=1000 ouid=0FSUID="debian" OUID="root"
```

Read it as: profile **`aacat`** denied an **`open`** of the **file** at **`name`**. The program
asked for `r` (`requested_mask`), and `r` was what got denied (`denied_mask`). `fsuid` and `ouid`
are the caller's filesystem UID and the file owner's UID. The missing space before `FSUID` is
literal: auditd appends the translated names to the raw record.

## Containers

Docker and Podman confine every container with a generated profile, unless told otherwise:
**`docker-default`** for Docker, and `containers-default-<version>` for Podman. On the VM:

```text
$ sudo podman run --rm docker.io/library/alpine cat /proc/self/attr/current
containers-default-0.62.2 (enforce)
```

These profiles deny writes to most of `/proc` and `/sys`, `mount`, and `ptrace` of processes
outside the container. `--privileged` replaces them with `unconfined`
([Container Privilege](../15-containers-and-virtualization/capabilities-in-containers.md)).

Ubuntu 24.04's restriction on **unprivileged user namespaces** is also an AppArmor feature. An
unconfined program that creates a user namespace is moved into a profile that denies capabilities
inside it, unless a profile for that program allows `userns`
([User Namespaces](../15-containers-and-virtualization/user-namespaces.md)).

<Lab host="qemu" title="Confine a copy of cat, then walk around the profile with a hard link" time="10 min">

On the folder-01 Debian VM (AppArmor enabled by default; `auditd` installed). A copy of `cat` at
`/usr/local/bin/aacat` gets a profile allowing only reads under `/srv/www/`:

```bash
sudo cp /usr/bin/cat /usr/local/bin/aacat
sudo mkdir -p /srv/www /srv/secret
echo page | sudo tee /srv/www/index.html >/dev/null
echo key  | sudo tee /srv/secret/key >/dev/null
sudo tee /etc/apparmor.d/usr.local.bin.aacat >/dev/null <<'P'
abi <abi/4.0>,
include <tunables/global>

profile aacat /usr/local/bin/aacat {
  include <abstractions/base>
  /srv/www/** r,
}
P
sudo apparmor_parser -r /etc/apparmor.d/usr.local.bin.aacat
```

Measured (`uname -r`: `6.12.113+deb13-cloud-amd64`):

```text
$ aacat /srv/www/index.html
page
$ aacat /srv/secret/key
aacat: /srv/secret/key: Permission denied
$ aacat /etc/hostname
aacat: /etc/hostname: Permission denied
$ sudo ln /srv/secret/key /srv/www/key
$ aacat /srv/www/key
key
```

- **DAC said yes and AppArmor said no.** `/etc/hostname` is world-readable, and the profile doesn't
  list it. Same `EACCES` as a permission-bit failure, which is why the audit log is the place to
  look.
- **A hard link defeats the path rule.** `/srv/www/key` and `/srv/secret/key` are the same inode.
  The profile judges the *name* used to open it, so the second name is allowed. Creating that link
  needed root here. A confined program that can create links somewhere is a concern, which is why
  AppArmor has the `l` permission and checks a link's target against the source's permissions.

Cleanup:

```bash
sudo apparmor_parser -R /etc/apparmor.d/usr.local.bin.aacat
sudo rm -f /etc/apparmor.d/usr.local.bin.aacat /usr/local/bin/aacat
sudo rm -rf /srv/www /srv/secret
```

If it fails: `aacat` reads everything → the profile isn't loaded (`sudo aa-status | grep aacat`),
or the binary isn't at the attached path.

</Lab>

## SELinux versus AppArmor

The same intent, "nginx may read `/srv/www`", in each system:

<Tabs>
<TabItem value="selinux" label="SELinux">

```bash
# Label the content with the type the httpd_t domain is already allowed to read
sudo semanage fcontext -a -t httpd_sys_content_t '/srv/www(/.*)?'
sudo restorecon -Rv /srv/www
ls -Z /srv/www/index.html
# system_u:object_r:httpd_sys_content_t:s0 /srv/www/index.html
```

The policy already contains `allow httpd_t httpd_sys_content_t:file { read open getattr … };`.
Granting access means **labelling the files**, and the label is stored in each file's
`security.selinux` xattr.

</TabItem>
<TabItem value="apparmor" label="AppArmor">

```text
# /etc/apparmor.d/usr.sbin.nginx (excerpt)
profile nginx /usr/sbin/nginx {
  /srv/www/ r,
  /srv/www/** r,
}
```

Then `sudo apparmor_parser -r /etc/apparmor.d/usr.sbin.nginx`. Granting access means **adding a
path to the program's profile**. Nothing is stored on the files.

</TabItem>
</Tabs>

| | SELinux | AppArmor |
|---|---|---|
| Model | Type enforcement on labels: subject type × object type × class × permission | Per-program allow lists of paths, capabilities and network access |
| Label storage | `security.selinux` xattr on every file; contexts on processes, sockets, ports | None on files; the profile holds paths |
| Rename / hard link | Label follows the inode, whatever its name | Rules follow the name; another name can mean other rules |
| Expressiveness | Whole-system policy, MLS/MCS levels, role-based access | Confines chosen programs; everything else unconfined |
| Tooling | `semanage`, `restorecon`, `audit2allow`, `sesearch` | `aa-genprof`, `aa-logprof`, `aa-complain`, `aa-enforce` |
| Default on | Fedora, RHEL and derivatives, Android | Debian, Ubuntu, SUSE |

## Misconceptions

1. **"AppArmor and SELinux can't both protect a system, so the choice doesn't matter."** They are
   exclusive with each other today, but they protect different things. SELinux confines everything
   by label. AppArmor confines what has a profile, and nothing else.
2. **"An unconfined process under AppArmor is unrestricted."** It isn't confined by AppArmor. DAC,
   capabilities and the other stacked LSMs still apply.
3. **"Complain mode is a safe production setting."** It denies nothing. It's a tool for writing
   profiles.

<KernelFacts
  structure={[["struct aa_profile", "security/apparmor/include/policy.h"], ["struct aa_label", "security/apparmor/include/label.h"]]}
  path="security_file_open() → apparmor_file_open() → aa_path_perm() → profile DFA match"
  observe="sudo aa-status"
  trap="Path-based rules follow the name, not the object. A hard link or bind mount at a different path can be governed by different rules than the original." />

## References

- [AppArmor](https://docs.kernel.org/admin-guide/LSM/apparmor.html), kernel admin guide.
- AppArmor's [profile language reference](https://gitlab.com/apparmor/apparmor/-/wikis/AppArmor_Core_Policy_Reference)
  and `parser/techdoc.tex` — the file permissions and exec modes. Checked via context7
  (`/gitlab_apparmor/apparmor`) on 2026-10-27.
- [apparmor(7)](https://manpages.debian.org/trixie/apparmor/apparmor.7.en.html) and
  [apparmor.d(5)](https://manpages.debian.org/trixie/apparmor/apparmor.d.5.en.html).
- Ubuntu Server documentation, ["AppArmor"](https://documentation.ubuntu.com/server/how-to/security/apparmor/).
- <Src file="security/apparmor/lsm.c" symbol="apparmor_file_open" /> and
  <Src file="security/apparmor/file.c" symbol="aa_path_perm" />.
