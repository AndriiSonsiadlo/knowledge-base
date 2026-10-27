// SPDX-License-Identifier: GPL-2.0
/* Exercise /dev/chardrv: write, seek, read back, and both ioctls. */
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

#include "chardrv.h"

#define CHECK(cond, what) \
	do { if (!(cond)) { printf("FAIL: %s (errno %d: %s)\n", what, errno, strerror(errno)); return 1; } } while (0)

int main(void)
{
	char out[16] = { 0 };
	__u32 len;
	int fd = open("/dev/chardrv", O_RDWR);

	CHECK(fd >= 0, "open /dev/chardrv");
	CHECK(write(fd, "hello", 5) == 5, "write 5 bytes");
	CHECK(lseek(fd, 0, SEEK_SET) == 0, "seek to 0");
	CHECK(read(fd, out, sizeof(out)) == 5, "read back 5 bytes");
	CHECK(memcmp(out, "hello", 5) == 0, "data matches");
	CHECK(ioctl(fd, CHARDRV_GET_LEN, &len) == 0 && len == 5, "GET_LEN == 5");
	CHECK(ioctl(fd, CHARDRV_CLEAR) == 0, "CLEAR");
	CHECK(ioctl(fd, CHARDRV_GET_LEN, &len) == 0 && len == 0, "GET_LEN == 0 after CLEAR");
	CHECK(ioctl(fd, _IO('c', 99)) == -1 && errno == ENOTTY, "unknown ioctl -> ENOTTY");
	close(fd);
	printf("PASS\n");
	return 0;
}
