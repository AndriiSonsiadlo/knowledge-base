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
