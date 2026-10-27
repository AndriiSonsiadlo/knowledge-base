// SPDX-License-Identifier: GPL-2.0
/*
 * chardrv: a 4 KiB scratch buffer behind /dev/chardrv.
 * read/write/llseek on the buffer, plus two ioctls: clear it, and get its length.
 */
#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt	/* prefix pr_*() output with "chardrv: " */

#include <linux/fs.h>
#include <linux/miscdevice.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/uaccess.h>

#include "chardrv.h"

static char buf[CHARDRV_BUF_SIZE];
static size_t buf_len;		/* bytes of buf currently holding data */
static DEFINE_MUTEX(buf_lock);	/* protects buf and buf_len */

static ssize_t chardrv_read(struct file *file, char __user *ubuf,
			    size_t count, loff_t *ppos)
{
	ssize_t ret;

	mutex_lock(&buf_lock);
	if (*ppos >= buf_len) {
		ret = 0;			/* end of data */
		goto out;
	}
	count = min_t(size_t, count, buf_len - *ppos);
	if (copy_to_user(ubuf, buf + *ppos, count)) {
		ret = -EFAULT;
		goto out;
	}
	*ppos += count;
	ret = count;
	pr_debug("read %zu bytes, pos now %lld\n", count, *ppos);
out:
	mutex_unlock(&buf_lock);
	return ret;
}

static ssize_t chardrv_write(struct file *file, const char __user *ubuf,
			     size_t count, loff_t *ppos)
{
	ssize_t ret;

	mutex_lock(&buf_lock);
	if (*ppos >= CHARDRV_BUF_SIZE) {
		ret = -ENOSPC;			/* buffer full */
		goto out;
	}
	count = min_t(size_t, count, CHARDRV_BUF_SIZE - *ppos);
	if (copy_from_user(buf + *ppos, ubuf, count)) {
		ret = -EFAULT;
		goto out;
	}
	*ppos += count;
	buf_len = max_t(size_t, buf_len, *ppos);
	ret = count;
	pr_debug("wrote %zu bytes, length now %zu\n", count, buf_len);
out:
	mutex_unlock(&buf_lock);
	return ret;
}

static long chardrv_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
	u32 len;

	switch (cmd) {
	case CHARDRV_CLEAR:
		mutex_lock(&buf_lock);
		buf_len = 0;
		mutex_unlock(&buf_lock);
		return 0;
	case CHARDRV_GET_LEN:
		mutex_lock(&buf_lock);
		len = buf_len;
		mutex_unlock(&buf_lock);
		return put_user(len, (u32 __user *)arg);
	default:
		return -ENOTTY;			/* "not supported", by convention */
	}
}

static loff_t chardrv_llseek(struct file *file, loff_t offset, int whence)
{
	return fixed_size_llseek(file, offset, whence, CHARDRV_BUF_SIZE);
}

static const struct file_operations chardrv_fops = {
	.owner		= THIS_MODULE,
	.read		= chardrv_read,
	.write		= chardrv_write,
	.unlocked_ioctl	= chardrv_ioctl,
	.llseek		= chardrv_llseek,
};

static struct miscdevice chardrv_dev = {
	.minor	= MISC_DYNAMIC_MINOR,
	.name	= "chardrv",
	.fops	= &chardrv_fops,
	.mode	= 0666,
};

/* Generates module init/exit that call misc_register()/misc_deregister(). */
module_misc_device(chardrv_dev);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("A 4 KiB scratch buffer behind /dev/chardrv");
