---
id: firmware-bios-and-uefi
title: "Firmware: BIOS and UEFI"
sidebar_label: "BIOS and UEFI"
sidebar_position: 1
tags: [linux, boot]
prerequisites:
  - linux/guided-traces/from-power-on-to-login-prompt
draft: false
---

# Firmware: BIOS and UEFI

What the firmware does before anything Linux exists, and why UEFI made boot loaders simpler and boot debugging harder.

Before any Linux code exists anywhere in memory, something has to bring RAM up, work out what hardware
is actually present, and decide what to execute first. That something is firmware — code baked into
flash on the motherboard, running before there is a filesystem, a scheduler, or even reliable memory to
lean on. It is a full software stack in its own right, not a thin prelude to Linux, and the two models in
production use today — legacy BIOS and UEFI — differ enough in what they leave behind that "what does
the firmware do here" changes which commands actually answer a failed-boot question.

## What firmware must do

Every firmware, legacy or UEFI, does the same handful of things before handing off, regardless of how it
does them:

- **POST** (power-on self-test) — confirm the CPU, RAM, and buses actually work before trusting them.
- **Memory training and mapping** — initialise the memory controller, then build a map of which physical
  address ranges are usable RAM, which are reserved for hardware, and which are unusable.
- **Bus and device enumeration** — find what's attached (storage controllers, network adapters, the
  boot device itself) well enough to hand a device list to whatever runs next.
- **Publish tables the OS will read** — most importantly the ACPI tables, which describe the machine's
  power management, interrupt routing, and hardware topology in a form an OS can parse without knowing
  the specific board.
- **Decide what to execute next** — following its own configuration, pick a device and a piece of code
  to load into memory and jump to.

Firmware doesn't know what Linux is. It only knows which sector or file to read and where to jump
afterward — the [chain of handoffs](./the-boot-chain.md) starts here, and firmware's job ends the
instant it jumps.

## Legacy BIOS, as a model

Legacy BIOS is the older of the two models, and its constraints still shape how people talk about
booting even on machines that no longer run it:

- The CPU starts in **16-bit real mode** — a mode with no memory protection and a 1 MiB address space,
  a holdover from the original IBM PC.
- BIOS looks for a boot device with a valid **MBR** (Master Boot Record) — the disk's first 512 bytes,
  ending in the two-byte signature `0x55AA`. Only 446 of those bytes are available for actual code; the
  rest is the partition table and the signature.
- 446 bytes is nowhere near enough to load a kernel, so the MBR's job is narrower than "boot Linux": it
  loads a second-stage loader (GRUB's `core.img`, in the common case), which loads the rest. This
  **chainloading** — one small piece of code loading a slightly less small piece of code — is how BIOS
  boot loaders get around the 446-byte ceiling.
- BIOS exposes hardware through **interrupt-based services** — `int 0x13` for disk reads,
  `int 0x10` for video, and so on — callable only from real mode. Once the kernel switches the CPU into
  protected or long mode, those interrupts stop working; the kernel brings up its own drivers for
  everything BIOS used to do on its behalf.

## UEFI, as a model

UEFI is not a firmware tweak on top of BIOS — it's a different model, closer to a small operating system
than to a boot ROM:

- The boot device carries a normal filesystem: a FAT32 **EFI System Partition** (ESP), readable by
  firmware without any chainloading trick.
- What firmware loads is a `.efi` file — a **PE32+ executable**, the same binary format Windows uses,
  not a hand-assembled 512-byte blob.
- Which `.efi` file to run, and in what order, is recorded as **NVRAM boot variables** — `Boot0000`,
  `Boot0001`, and so on, plus a `BootOrder` variable listing which to try and in what sequence. This
  state lives in firmware, not on any disk partition.
- UEFI splits what it offers into **boot services** (available only before an OS takes over — file and
  disk access, console I/O, memory allocation) and **runtime services** (still callable after boot, for
  things like reading/writing NVRAM variables or triggering a reboot from a running OS).
- Instead of a BIOS memory map, UEFI hands the OS an **EFI memory map** — a richer structure with
  per-region attributes (cacheability, whether it's runtime-services memory that must stay mapped forever,
  and more) rather than BIOS's simple usable/reserved split.

:::note
This section describes UEFI on x86-64, the architecture this section is pinned to. On arm64, UEFI plays
an even larger role: there is no legacy-BIOS equivalent to fall back to, so arm64 servers and most arm64
Linux distributions assume UEFI (or U-Boot presenting a UEFI-compatible interface) as the only supported
firmware model.
:::

## What the kernel is handed

Whichever model booted the machine, the kernel's first job is to read back what firmware already
figured out rather than rediscover it:

- **The memory map.** On legacy BIOS this is the **e820 map** — named after the BIOS interrupt call,
  `int 0x15, ax=0xE820`, used to build it — represented in the kernel as
  <Src file="arch/x86/include/asm/e820/types.h" symbol="e820_table" />. On UEFI it's the **EFI memory
  map** instead, an array of <Src file="include/linux/efi.h" symbol="efi_memory_desc_t" /> entries. Both
  answer the same question — which physical addresses are safe to allocate from — in different shapes.
- **ACPI tables.** Firmware built them; the kernel parses them to learn about CPUs, interrupt routing,
  and power management without needing board-specific code.

This is where `dmesg`'s very first lines come from. A machine booted through the legacy path opens with
`BIOS-e820:` lines; a machine booted through UEFI opens with `efi:` lines describing the EFI memory map
instead — the same information, in the two different shapes above.

## Why UEFI made boot simpler and debugging harder

UEFI's ESP-and-`.efi`-executable model is a real simplification: a boot loader is now a normal program on
a normal, readable filesystem, built with a normal toolchain, instead of hand-assembled code shoehorned
into 446 bytes with chainloading bolted on to get past that limit. `grubx64.efi` can be inspected, copied,
and rebuilt like any other file.

The cost moved rather than disappeared. Boot *selection* — which entry runs, and in what order — now
lives in firmware NVRAM, a place Linux cannot inspect by just reading a file on disk. A machine that
boots the wrong thing, or nothing, might have a perfectly intact ESP and a perfectly intact `grub.cfg`
and still fail, because the boot-order variable pointing at them is missing, corrupted, or was
overwritten by another OS's installer. Debugging that failure means reaching for a tool that talks to
firmware directly — `efibootmgr` — rather than just reading files, which is a step BIOS boot debugging
never needed because BIOS kept no equivalent state to go missing.

## Evidence on a running system

Three checks, cheapest first, that establish which model booted the machine and what firmware handed it:

```text
$ ls /sys/firmware/efi
config_table  efivars  fw_platform_size  esrt  runtime  runtime-map  systab  ...
```

If `/sys/firmware/efi` exists, this boot went through UEFI. If it doesn't, this boot went through the
legacy path — see the trap below before concluding anything about the *machine*.

```text
$ efibootmgr -v
BootCurrent: 0002
BootOrder: 0002,0000,0001
Boot0000* Windows Boot Manager  HD(1,GPT,...)/File(\EFI\Microsoft\Boot\bootmgfw.efi)
Boot0001* UEFI: Built-in EFI Shell
Boot0002* ubuntu   HD(1,GPT,...)/File(\EFI\ubuntu\grubx64.efi)
```

`BootCurrent` names the NVRAM entry this boot actually used; `BootOrder` is the sequence firmware tries.
This is the tool for the failure mode above — it reads the state a broken ESP-and-config alone can't
explain.

```text
$ dmesg | grep -i efi
[    0.000000] efi: EFI v2.70 by American Megatrends
[    0.000000] efi: ACPI=0x... ACPI 2.0=0x... SMBIOS=0x... SMBIOS 3.0=0x... MEMATTR=0x...
```

`dmesg` confirms the same thing from the kernel's side: an `efi:` block this early means the kernel
received an EFI memory map and the table pointers UEFI publishes, not a BIOS `e820` map.

Put side by side, the two models diverge on every axis that matters for debugging a boot from Linux:

| | Legacy BIOS | UEFI |
|---|---|---|
| Where the loader lives | MBR (446 usable bytes) + chainloaded second stage | `.efi` file on a FAT32 ESP |
| Executable format | hand-assembled real-mode code | PE32+ executable |
| Partition scheme | MBR, or GPT with a BIOS boot partition | GPT with an ESP |
| Boot selection | fixed device-scan order, no per-entry state | NVRAM `BootOrder` / `Boot####` variables |
| Services offered to the OS | `int` calls, real-mode only, gone once the CPU leaves real mode | boot services (pre-OS) + runtime services (persist after boot) |
| How you inspect it from Linux | indirectly — read the MBR bytes, or trust `dmesg`'s `BIOS-e820` lines | directly — `/sys/firmware/efi`, `efibootmgr -v` |

*Legacy BIOS and UEFI, compared across where the loader lives, what it is, and how Linux can see into it.*

<KernelFacts
  structure={[["efi_memory_desc_t", "include/linux/efi.h"]]}
  path="firmware POST → memory map + ACPI tables → boot variable selects a loader → loader executes"
  observe="ls /sys/firmware/efi && efibootmgr -v"
  trap="`/sys/firmware/efi` absent does not mean the machine lacks UEFI; it means *this* kernel was booted through the legacy path. Dual-mode firmware makes this a per-boot fact, not a per-machine one." />

## References

- [UEFI Specifications](https://uefi.org/specifications) — the primary source for boot variables, the
  ESP layout, and the boot-services/runtime-services split described above.
- [The x86 boot protocol](https://docs.kernel.org/arch/x86/boot.html) — what the kernel requires from
  whatever loads it, on both legacy BIOS and UEFI paths.
- [`man 8 efibootmgr`](https://man.archlinux.org/man/efibootmgr.8.en) — how boot variables are read and
  changed from a running Linux system, the tool this page's evidence section relies on.
