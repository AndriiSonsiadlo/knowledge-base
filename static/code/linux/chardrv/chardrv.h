/* SPDX-License-Identifier: GPL-2.0 */
/* ioctl interface shared by chardrv.ko and its user-space test program. */
#ifndef CHARDRV_H
#define CHARDRV_H

#include <linux/ioctl.h>
#include <linux/types.h>

#define CHARDRV_BUF_SIZE 4096

#define CHARDRV_CLEAR   _IO('c', 1)
#define CHARDRV_GET_LEN _IOR('c', 2, __u32)

#endif
