---
id: kvm-and-hardware-virtualization
title: "KVM"
sidebar_label: "KVM"
sidebar_position: 11
tags: [linux, kernel, containers]
prerequisites:
  - computer-science/cpu-architecture/hardware-virtualization
  - linux/containers-and-virtualization/what-a-container-actually-is
  - linux/device-drivers-and-hardware/talking-to-user-space
draft: false
---

# KVM

KVM turns the kernel into a hypervisor with surprisingly little new machinery. A VM is a process.
Each virtual CPU is a thread, guest memory is ordinary process memory, and the whole interface is
`ioctl()`s on file descriptors from `/dev/kvm`. The hardware support described in
[Hardware Virtualization](../../computer-science/cpu-architecture/hardware-virtualization.md) does
the hard part. KVM's job is the loop around `VMRUN` (AMD) or `VMRESUME` (Intel), and QEMU's job is
everything that loop hands back to user space.

## The file-descriptor hierarchy

Three levels of file descriptor, each created by an `ioctl` on the one above:

| fd | Created by | Represents | Typical `ioctl`s |
|---|---|---|---|
| `/dev/kvm` | `open()` | The KVM subsystem | `KVM_GET_API_VERSION`, `KVM_CHECK_EXTENSION`, `KVM_CREATE_VM`, `KVM_GET_VCPU_MMAP_SIZE` |
| VM fd | `KVM_CREATE_VM` | One guest: its memory map, interrupt controllers, devices | `KVM_SET_USER_MEMORY_REGION`, `KVM_CREATE_VCPU`, `KVM_CREATE_IRQCHIP`, `KVM_IOEVENTFD`, `KVM_IRQFD` |
| vCPU fd | `KVM_CREATE_VCPU` | One virtual CPU | `KVM_GET/SET_REGS`, `KVM_GET/SET_SREGS`, `KVM_RUN` |

Each vCPU fd can be `mmap`ed to give a `struct kvm_run`. This page of shared memory is how the
kernel tells user space why `KVM_RUN` returned, without another syscall to ask. The parts that
matter:

| `struct kvm_run` field | Direction | Meaning |
|---|---|---|
| `exit_reason` | kernel → user | `KVM_EXIT_IO` (2), `KVM_EXIT_HLT` (5), `KVM_EXIT_MMIO` (6), `KVM_EXIT_SHUTDOWN` (8), `KVM_EXIT_INTERNAL_ERROR` (17), … |
| `io` | kernel → user | `direction`, `size`, `port`, `count`, `data_offset` (where in this page the data is) |
| `mmio` | both | `phys_addr`, `data[8]`, `len`, `is_write` |
| `request_interrupt_window` | user → kernel | Exit as soon as the guest can take an interrupt |
| `ready_for_interrupt_injection`, `if_flag` | kernel → user | Whether an interrupt can be injected now |
| `immediate_exit` | user → kernel | Return from `KVM_RUN` without entering the guest (used to kick a vCPU thread) |
| `cr8`, `apic_base` | both | Task priority and APIC base when the APIC is in user space |
| `kvm_valid_regs`, `kvm_dirty_regs`, `s.regs` | both | Registers synced through this page, saving `KVM_GET/SET_REGS` calls |

## Guest memory is process memory

`KVM_SET_USER_MEMORY_REGION` says: guest physical addresses `guest_phys_addr` to
`guest_phys_addr + memory_size` are backed by this range of *my* virtual address space. The memory
is ordinary anonymous memory (or a file, or hugetlbfs), so it can be swapped, shared or migrated
like any other memory. On an EPT/NPT violation, KVM resolves the guest physical address to a host
virtual address through the memslot, then to a host physical page by faulting it in through the
normal `get_user_pages` path, and installs a second-level (guest physical → host physical) entry.
The guest's own page tables translate guest virtual to guest physical, and the hardware walks both
levels. See [TLB and Address Translation Hardware](../../computer-science/memory-hierarchy/tlb-and-address-translation-hardware.md).

`KVM_SET_USER_MEMORY_REGION2` (Linux 6.8+) is the extended form. Its main addition is a
`guest_memfd` file descriptor for memory the host can't map: the basis for confidential guests
(AMD SEV-SNP, Intel TDX). Plain VMs still use the original call.

## The run loop

`ioctl(vcpu_fd, KVM_RUN)` enters the guest and doesn't return until something needs user space.
Inside the kernel:

1. Load the guest state and enter the guest (`VMRUN` / `VMRESUME`).
2. The guest runs at native speed until a **VM exit**: an instruction or event the hardware is
   configured to intercept.
3. KVM's exit handler runs. If the kernel can handle the exit (a `CPUID`, most MSR accesses, an
   EPT fault, a timer interrupt, an I/O port registered with an in-kernel device), it does, and
   re-enters the guest **without returning to user space**.
4. Otherwise, it fills in `kvm_run` and returns from the `ioctl`. User space emulates the access
   and calls `KVM_RUN` again.

Most exits never leave the kernel. The ones that reach QEMU are mostly device accesses for devices
QEMU emulates.

```mermaid
sequenceDiagram
    participant Q as QEMU vCPU thread
    participant K as KVM (kernel)
    participant G as guest
    Q->>K: ioctl(KVM_RUN)
    K->>G: VM entry (VMRUN / VMRESUME)
    Note over G: runs natively
    G->>K: VM exit (out to port 0x3f8)
    alt handled in the kernel
        K->>G: re-enter
    else needs user space
        K-->>Q: return; kvm_run.exit_reason = KVM_EXIT_IO
        Note over Q: emulate the serial port
        Q->>K: ioctl(KVM_RUN)
    end
```

*The run loop. The `alt` branch is the whole performance story: an exit handled in the kernel costs
a world switch; one handed to QEMU adds two syscall-boundary crossings and a thread wake-up.*

## VM exits and where they are handled

| Exit (Intel name) | Handled in | Typical cause |
|---|---|---|
| `EXTERNAL_INTERRUPT` | KVM | A host interrupt arrived while the guest ran; the host handles it, then re-enters |
| `EPT_VIOLATION` | KVM | First touch of a guest page, or a write to a write-protected one |
| `EPT_MISCONFIG` | KVM, or QEMU as `KVM_EXIT_MMIO` | MMIO to an emulated device's registers |
| `CPUID` | KVM | The guest asks what CPU it has; KVM answers from the table QEMU set |
| `MSR_READ` / `MSR_WRITE` | KVM (most), QEMU for filtered MSRs | Timer, APIC and power-management registers |
| `HLT` | KVM with an in-kernel APIC; QEMU (`KVM_EXIT_HLT`) without | Idle guest |
| `IO_INSTRUCTION` | KVM for in-kernel devices and `ioeventfd`s; QEMU (`KVM_EXIT_IO`) otherwise | Legacy devices, the serial port, virtio notifications |

The handler table is `kvm_vmx_exit_handlers[]` in `arch/x86/kvm/vmx/vmx.c`, with an equivalent in
`svm.c`.

## Where QEMU fits

QEMU provides everything that isn't a CPU: the **machine model** (chipset, firmware, memory map),
**device emulation** (disks, NICs, the serial port), and the management interfaces. With
`-accel kvm` (`-enable-kvm` in folder 01's
[command line](../01-lab-and-toolchain/a-full-system-vm-and-wsl2.md)), each vCPU is a QEMU thread
looping on `KVM_RUN`. With `-accel tcg`, QEMU translates guest instructions itself instead, which
is portable and much slower. The [virtio page](./virtio-and-paravirtualization.md) covers how
devices avoid most of the exits that reach QEMU.

## What actually happens

A 90-line program creates a VM, gives it one page of memory with seven bytes of real-mode code
(load `0x3f8` into `dx`, `'A'` into `al`, `out`, `hlt`), and runs it. It follows LWN's 2015
"Using the KVM API" article, the canonical minimal example.

```c title="kvm_hello.c"
// SPDX-License-Identifier: GPL-2.0
/*
 * The smallest useful KVM program: one VM, one vCPU, one page of real-mode
 * code that writes a byte to port 0x3f8 and halts. Follows LWN's
 * "Using the KVM API" (2015).
 */
#include <err.h>
#include <fcntl.h>
#include <linux/kvm.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>

int main(void)
{
	/* mov $0x3f8, %dx; mov $'A', %al; out %al, (%dx); hlt */
	const uint8_t code[] = { 0xba, 0xf8, 0x03, 0xb0, 'A', 0xee, 0xf4 };
	struct kvm_sregs sregs;
	struct kvm_regs regs;
	struct kvm_run *run;
	int kvm, vm, vcpu, ret;
	size_t run_size;
	uint8_t *mem;

	kvm = open("/dev/kvm", O_RDWR | O_CLOEXEC);
	if (kvm < 0)
		err(1, "/dev/kvm");
	ret = ioctl(kvm, KVM_GET_API_VERSION, NULL);
	if (ret != KVM_API_VERSION)
		errx(1, "KVM_GET_API_VERSION %d, expected %d", ret, KVM_API_VERSION);

	vm = ioctl(kvm, KVM_CREATE_VM, 0UL);
	if (vm < 0)
		err(1, "KVM_CREATE_VM");

	/* One page of ordinary process memory becomes guest physical 0x1000. */
	mem = mmap(NULL, 0x1000, PROT_READ | PROT_WRITE,
		   MAP_SHARED | MAP_ANONYMOUS, -1, 0);
	if (mem == MAP_FAILED)
		err(1, "mmap");
	memcpy(mem, code, sizeof(code));
	struct kvm_userspace_memory_region region = {
		.slot = 0,
		.guest_phys_addr = 0x1000,
		.memory_size = 0x1000,
		.userspace_addr = (uintptr_t)mem,
	};
	if (ioctl(vm, KVM_SET_USER_MEMORY_REGION, &region) < 0)
		err(1, "KVM_SET_USER_MEMORY_REGION");

	vcpu = ioctl(vm, KVM_CREATE_VCPU, 0UL);
	if (vcpu < 0)
		err(1, "KVM_CREATE_VCPU");
	run_size = ioctl(kvm, KVM_GET_VCPU_MMAP_SIZE, NULL);
	run = mmap(NULL, run_size, PROT_READ | PROT_WRITE, MAP_SHARED, vcpu, 0);
	if (run == MAP_FAILED)
		err(1, "mmap kvm_run");

	/* Real mode, flat: CS base 0, start executing at 0x1000. */
	if (ioctl(vcpu, KVM_GET_SREGS, &sregs) < 0)
		err(1, "KVM_GET_SREGS");
	sregs.cs.base = 0;
	sregs.cs.selector = 0;
	if (ioctl(vcpu, KVM_SET_SREGS, &sregs) < 0)
		err(1, "KVM_SET_SREGS");
	regs = (struct kvm_regs){ .rip = 0x1000, .rflags = 0x2 };
	if (ioctl(vcpu, KVM_SET_REGS, &regs) < 0)
		err(1, "KVM_SET_REGS");

	for (;;) {
		if (ioctl(vcpu, KVM_RUN, NULL) < 0)
			err(1, "KVM_RUN");
		switch (run->exit_reason) {
		case KVM_EXIT_IO:
			printf("KVM_EXIT_IO: port 0x%x, %s, size %d, byte '%c'\n",
			       run->io.port,
			       run->io.direction == KVM_EXIT_IO_OUT ? "out" : "in",
			       run->io.size,
			       *((char *)run + run->io.data_offset));
			break;
		case KVM_EXIT_HLT:
			puts("KVM_EXIT_HLT");
			return 0;
		default:
			errx(1, "unexpected exit_reason %d", run->exit_reason);
		}
	}
}
```

```make title="Makefile"
CFLAGS ?= -O2 -Wall -Wextra

kvm_hello: kvm_hello.c
	$(CC) $(CFLAGS) -o $@ kvm_hello.c

clean:
	rm -f kvm_hello
```

Files: [`kvm_hello.c`](pathname:///code/linux/kvm-hello/kvm_hello.c),
[`Makefile`](pathname:///code/linux/kvm-hello/Makefile). Measured on the folder-01 Debian VM:

```text
$ make && sudo ./kvm_hello
cc -O2 -Wall -Wextra -o kvm_hello kvm_hello.c
KVM_EXIT_IO: port 0x3f8, out, size 1, byte 'A'
KVM_EXIT_HLT
$ grep -o -m1 -E 'vmx|svm' /proc/cpuinfo; lsmod | grep kvm
svm
kvm_amd               147456  0
kvm                  1380352  1 kvm_amd
irqbypass              12288  1 kvm
```

- **Both exits reached user space** because the program created no in-kernel devices. There's no
  `KVM_CREATE_IRQCHIP`, so KVM has no APIC to wait on for `hlt` and returns `KVM_EXIT_HLT`. No
  device is registered at port `0x3f8`, so the `out` comes back as `KVM_EXIT_IO`. QEMU's real
  serial port takes exactly the same path.
- **The byte is in the shared page**, at `run->io.data_offset`. No copy and no extra syscall.
- **This was nested virtualization.** The VM runs under QEMU's TCG with `-cpu max`, which emulates
  AMD SVM, so `kvm_amd` loaded inside the VM and ran this guest on emulated hardware. It works, but
  every number here is meaningless as a performance measurement. Exit counts per second (from
  `perf kvm stat` or `/sys/kernel/debug/kvm/`) were not measured for the same reason.

If it fails: `/dev/kvm: Permission denied` → run with `sudo` or join the `kvm` group.
`/dev/kvm: No such file or directory` → no hardware virtualization exposed (`grep -c -E 'vmx|svm'
/proc/cpuinfo` is 0), or the `kvm_intel`/`kvm_amd` module isn't loaded. `KVM_EXIT_SHUTDOWN` → the
guest triple-faulted, usually from a wrong `rip` or `cs.base`.

## Misconceptions

1. **"KVM is a type-2 hypervisor because it runs inside Linux."** The type-1/type-2 taxonomy fits
   poorly. KVM is part of the kernel running directly on the hardware, which is type-1 in shape. But
   that kernel also runs ordinary processes, and the VMs are among them, which is type-2 in shape.
   The useful questions are which component handles each exit, and what runs in the most privileged
   mode.
2. **"QEMU is slow emulation."** With KVM, QEMU doesn't execute guest instructions at all. It runs
   device models and handles the exits that reach user space. TCG, its emulator, is slow, and that
   is the mode this lab's VM uses.
3. **"Every guest instruction is trapped."** Guest code runs natively, ring 3 and ring 0 alike.
   Only the instructions and events configured as intercepts cause exits, and with EPT/NPT even
   page-table updates don't.

<KernelFacts
  structure={[["struct kvm_run", "include/uapi/linux/kvm.h"], ["struct kvm_vcpu", "include/linux/kvm_host.h"]]}
  path="ioctl(vcpu_fd, KVM_RUN) → kvm_vcpu_ioctl() → kvm_arch_vcpu_ioctl_run() → vcpu_run() → vmx_vcpu_run() | svm_vcpu_run() → exit handler"
  observe="ls -l /dev/kvm; grep -c -E 'vmx|svm' /proc/cpuinfo"
  trap="Nested virtualization (KVM inside a VM) works, but every L2 exit costs several L1 exits. Benchmarks taken inside a cloud VM's nested guest say little about bare-metal KVM." />

## References

- [The Definitive KVM API Documentation](https://docs.kernel.org/virt/kvm/api.html) — every
  `ioctl`, `struct kvm_run`, and `KVM_SET_USER_MEMORY_REGION2`.
- Josh Triplett, ["Using the KVM API"](https://lwn.net/Articles/658511/), LWN, 2015 — the
  annotated minimal example this page's program follows.
- <Src file="virt/kvm/kvm_main.c" symbol="kvm_vcpu_ioctl" /> and
  <Src file="arch/x86/kvm/x86.c" symbol="vcpu_run" /> — the vCPU `ioctl` dispatch and the x86
  run loop; `kvm_vmx_exit_handlers` in <Src file="arch/x86/kvm/vmx/vmx.c" />.
- [QEMU accelerators](https://www.qemu.org/docs/master/system/introduction.html#virtualisation-accelerators)
  — KVM, TCG and the others.
