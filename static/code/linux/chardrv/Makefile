obj-m += chardrv.o

KDIR ?= $(HOME)/kernel-lab/linux

all:
	$(MAKE) -C $(KDIR) M=$(CURDIR) modules

test_chardrv: test_chardrv.c chardrv.h
	$(CC) -static -Wall -o $@ test_chardrv.c

clean:
	$(MAKE) -C $(KDIR) M=$(CURDIR) clean
	rm -f test_chardrv
