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
