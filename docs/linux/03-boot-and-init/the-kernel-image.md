---
id: the-kernel-image
title: "Inside `bzImage`"
sidebar_label: "Inside bzImage"
sidebar_position: 6
tags: [linux, kernel, boot]
prerequisites:
  - linux/boot-and-init/the-boot-chain
draft: false
---

# Inside `bzImage`

The layout of a compressed kernel image, and why vmlinux, vmlinuz, and bzImage are three different things.

`vmlinux`, `vmlinuz`, and `bzImage` are three names people use interchangeably, and they name three
different files with three different jobs. Confusing them costs people hours — pointing GDB at the wrong
one, or trying to `objdump` a file that was never meant to be read as one. This page opens the actual
file up: what's inside it, who is responsible for filling in each part, and how a boot loader's few bytes
of trust turn into a running kernel.

## The three names

| Name | What it is | Bootable? | Used for |
|---|---|---|---|
| `vmlinux` | An uncompressed ELF binary, with full debug symbols if built with them | No — nothing in the boot chain knows how to load a bare ELF this way | GDB, `objdump`, `nm` — anything that needs symbol information |
| `bzImage` | Real-mode setup code, plus a setup header, plus a *compressed* payload with its own self-extracting decompressor | Yes — this is what `arch/x86/boot/` actually produces and what a boot loader loads | Booting the machine |
| `vmlinuz` | A distribution's installed copy of a `bzImage`, under a conventional name in `/boot` | Yes — it's the same file, just installed and renamed | Same as `bzImage` — the `z` is a hint that it's compressed, nothing more |

*Three names for kernel output, and why only one of them is safe to load into a debugger.*

## The layout of a bzImage

A `bzImage` is not "a compressed `vmlinux`" — it's a small, self-sufficient program with the compressed
kernel riding along as data:

1. **Real-mode setup code** — the part of the file that still runs in 16-bit real mode, the same
   constraint [legacy BIOS](./firmware-bios-and-uefi.md) imposes on anything it loads directly. This code
   does minimal hardware setup and reads the setup header the loader filled in.
2. **The setup header** — a fixed-layout block of fields, described below, that is the entire contract
   between whatever loaded this file and the kernel about to run.
3. **The compressed payload** — the actual kernel, compressed with whatever algorithm the build chose,
   plus a small decompressor stub that runs once the setup code hands off. The decompressor is not the
   boot loader's job and not the setup code's job — it's part of the payload itself.

## The setup header

The setup header is <Src file="arch/x86/include/uapi/asm/bootparam.h" symbol="setup_header" /> — a
packed struct with no padding, because its layout is a binary ABI, not an internal kernel detail. The
fields a boot loader actually has to care about:

```wavedrom title="The setup_header fields a boot loader has to fill in or check — gaps compressed, not to scale" alt="Bit-field strip of eight setup_header fields: boot_flag, header, version, loadflags, code32_start, ramdisk_image, ramdisk_size, and cmd_line_ptr, with the untouched fields between them shown as compressed gray gaps"
{ reg: [
    { bits: 8, type: 1 },
    { bits: 16, name: "boot_flag", type: 2 },
    { bits: 8, type: 1 },
    { bits: 32, name: "header", type: 2 },
    { bits: 16, name: "version", type: 2 },
    { bits: 8, type: 1 },
    { bits: 8, name: "loadflags", type: 2 },
    { bits: 8, type: 1 },
    { bits: 32, name: "code32_start", type: 2 },
    { bits: 32, name: "ramdisk_image", type: 2 },
    { bits: 32, name: "ramdisk_size", type: 2 },
    { bits: 8, type: 1 },
    { bits: 32, name: "cmd_line_ptr", type: 2 }
  ],
  config: { hspace: 1400, bits: 240, lanes: 1 }
}
```

*The gray blocks are the fields between the named ones — `root_flags`, `syssize`, `jump`,
`realmode_swtch`, `setup_move_size`, and others — compressed to a fixed width purely so the fields that
matter stay readable. Real offsets, from [`Documentation/arch/x86/boot.rst`](https://docs.kernel.org/arch/x86/boot.html):*

| Field | Offset | Size | Meaning |
|---|---|---|---|
| `boot_flag` | `0x1FE` | 2 bytes | Must contain `0xAA55` — the closest thing this format has to a magic number |
| `header` | `0x202` | 4 bytes | Must contain `"HdrS"` (`0x53726448`) — confirms this is a real boot-protocol header, not an old-format image |
| `version` | `0x206` | 2 bytes | Boot protocol version, as `(major << 8) + minor` |
| `loadflags` | `0x211` | 1 byte | Bitmask — includes `CAN_USE_HEAP`, `QUIET_FLAG`, and a bit the decompressor uses internally to signal KASLR status to the kernel proper |
| `code32_start` | `0x214` | 4 bytes | Protected-mode entry address; defaults to the kernel's own load address |
| `ramdisk_image` | `0x218` | 4 bytes | Linear address of the initramfs, once loaded |
| `ramdisk_size` | `0x21C` | 4 bytes | Size of the initramfs at that address |
| `cmd_line_ptr` | `0x228` | 4 bytes | Linear address of the kernel command line string |

## Who fills the header in

This table *is* the loader/kernel contract — every field is one of three kinds, and getting the kind
wrong is a real class of boot-loader bug:

| Kind | Meaning | Example fields |
|---|---|---|
| **read** | The kernel reads this; a loader must never modify it | `boot_flag`, `header`, `version` |
| **write (obligatory)** | The loader *must* fill this in correctly, or the kernel gets garbage | `ramdisk_image`, `ramdisk_size`, `cmd_line_ptr`, `loadflags` |
| **modify (optional)** | The loader may override the kernel's own default, but doesn't have to | `code32_start` |

A loader that gets an obligatory `write` field wrong doesn't fail cleanly — `ramdisk_size` set to zero
when an initramfs really was loaded, for instance, means the kernel proceeds believing there is no
initramfs at all, which looks like an early-user-space failure with no boot-loader-shaped explanation
anywhere in the trail.

## Decompression

The payload can be compressed with any of several algorithms the build selects — `CONFIG_KERNEL_GZIP`,
`CONFIG_KERNEL_XZ`, and `CONFIG_KERNEL_ZSTD` are the common choices, alongside less common ones the same
`init/Kconfig` menu offers. Whichever one is chosen, the decompressor built into the payload is the only
thing that knows how to undo it — nothing outside the `bzImage` needs to know or care which compression
scheme it is. The decompressor runs, relocates the now-uncompressed kernel to its final address, and
jumps into the kernel proper's own <Src file="arch/x86/kernel/head_64.S" symbol="startup_64" /> — a
*different* symbol of the same name from the one inside the decompressor's own
<Src file="arch/x86/boot/compressed/head_64.S" symbol="startup_64" /> entry point, since the decompressor
and the kernel it unpacks are two separate compiled programs that happen to share an entry-point name.
From there, [early boot](./early-boot-and-arch-setup.md) is architecture setup in C, culminating in
`start_kernel()`.

## What actually happens

Getting from an installed image back to something GDB can use is one command, not archaeology:

```text
$ file /boot/vmlinuz-6.18.0
/boot/vmlinuz-6.18.0: Linux kernel x86 boot executable bzImage, version 6.18.0 (build@host) ...,
RO-rootFS, swap_dev 0x0, Normal VGA
```

`file` already recognises the format — that's the "three names" table's `bzImage` row, confirmed on a
real installed file. Getting the ELF back out:

```text
$ scripts/extract-vmlinux /boot/vmlinuz-6.18.0 > /tmp/vmlinux
extract-vmlinux: Extracted vmlinux using 'unxz' from offset 12345
$ file /tmp/vmlinux
/tmp/vmlinux: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), statically linked, ...
```

<Src file="scripts/extract-vmlinux" /> tries each supported decompressor's magic bytes against the file
in turn until one of them produces something `file` or `readelf` recognises as an ELF binary — it doesn't
need to be told which algorithm was used, because it just tries all of them. The output is a real,
symbol-bearing ELF — usable for `objdump -d`, but only fully useful in GDB if it's from the *same build*
as the running kernel, since a rebuild can change addresses and inlining even with identical source.

## Misconceptions

- **"`bzImage` means bzip2."** It means *big zImage*. The original `zImage` format had a hard 512 KB size
  limit; `bzImage` is the format that lifted it. The name predates bzip2 support in the kernel build and
  has nothing to do with that compression algorithm.
- **"`vmlinuz` can be loaded into GDB."** Not usefully. `vmlinuz` is a `bzImage` — setup code plus a
  compressed payload — not an ELF file with symbols. GDB needs `vmlinux` from the exact same build.
- **"The boot loader decompresses the kernel."** It doesn't. The boot loader's job ends at handoff; the
  compressed payload carries its own decompressor and extracts itself once running.

<KernelFacts
  structure={[["struct setup_header", "arch/x86/include/uapi/asm/bootparam.h"]]}
  path="loader fills setup_header → jumps to code32_start → decompressor runs → relocation → startup_64() → start_kernel()"
  observe="file /boot/vmlinuz-$(uname -r)"
  trap="bzImage is not bzip2-compressed and never was. The 'bz' is 'big zImage' — the format that lifted the old 512 KB size limit, nothing to do with the compression algorithm of the same two letters." />

## References

- [The x86 boot protocol](https://docs.kernel.org/arch/x86/boot.html) — the primary source for every
  setup-header field, its offset, and whether the loader must read, write, or may optionally modify it.
- [The zero-page layout](https://docs.kernel.org/arch/x86/zero-page.html) — `struct boot_params`, the
  larger structure the setup header lives inside once the kernel is running.
- [`scripts/extract-vmlinux`](https://elixir.bootlin.com/linux/v6.18/source/scripts/extract-vmlinux) via
  <Src file="scripts/extract-vmlinux" /> — the tool this page's "What actually happens" section uses to
  recover an ELF `vmlinux` from an installed `bzImage`.
