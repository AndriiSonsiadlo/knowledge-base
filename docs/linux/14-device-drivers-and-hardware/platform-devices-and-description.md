---
id: platform-devices-and-description
title: "Platform Devices, Device Tree, and ACPI"
sidebar_label: "Platform devices"
sidebar_position: 2
tags: [linux, kernel, drivers]
prerequisites:
  - linux/device-drivers-and-hardware/the-linux-device-model
draft: false
---

# Platform Devices, Device Tree, and ACPI

PCI and USB devices announce themselves. The bus can be asked what is attached, and each device
answers with its vendor and device IDs. A UART at a fixed address on an SoC, an interrupt
controller, or QEMU's firmware-configuration port cannot be asked anything. There is no protocol
for discovering them, so the kernel has to be told they exist: where their registers are, which
interrupt they use, and what kind of device they are. Two description formats do the telling:
**device tree** on arm64 and most embedded systems, and **ACPI** tables on x86-64 PCs and servers.
**Platform devices** are the driver-side abstraction that hides which one was used.

## Enumerable versus described hardware

| | Enumerable | Described |
|---|---|---|
| Examples | PCI/PCIe, USB, virtio over PCI | SoC peripherals, legacy PC devices, on-board sensors on I²C |
| How the kernel learns of them | Asks the bus: reads configuration space, or a USB descriptor | Reads a description supplied by firmware or the bootloader |
| Identity comes from | The device itself (vendor/device IDs) | The description (`compatible`, `_HID`) |
| Resources (addresses, IRQs) come from | The device's BARs, assigned at enumeration | The description, fixed by the board's design |
| What happens if the description is wrong | Nothing: there is no description | The device is never found, or a driver writes to the wrong address |

On x86-64, PCIe covers most devices and ACPI describes the rest. On an arm64 SoC it is often the
other way round: most peripherals sit directly on the chip's internal interconnect at fixed
addresses, and nothing can enumerate them.

## Device tree

A **device tree** is a data structure describing the hardware, written as source (`.dts`),
compiled to a binary blob (a `.dtb`, or *flattened device tree*), and handed to the kernel by the
bootloader. Each **node** describes one device. The properties that matter to a driver are:

- **`compatible`** — a list of strings, most specific first, naming what the device is (for example
  `"qemu,fw-cfg-mmio"`). This is what drivers match on.
- **`reg`** — the register ranges, as address/size pairs in the parent bus's address format.
- **`interrupts`** — which interrupt line or lines, in the format the interrupt controller's node
  defines.
- **phandles** — references to other nodes: this device's clock, its regulator, its interrupt
  controller. These are the supplier links fw_devlink turns into probe ordering (see
  [The Linux Device Model](./the-linux-device-model.md)).

A device tree is pure data: it describes the hardware and cannot run code. The kernel unpacks it at
boot and exposes it read-only at `/proc/device-tree` (a link into `/sys/firmware/devicetree/base`).
Device tree also carries the bindings for buses that *are* simple but not self-describing, such as
I²C, SPI and GPIO. This repository's embedded section will cover device-tree authoring for boards
in depth; it is named here in prose because that page is not yet written.

## ACPI

**ACPI** tables are built by the platform firmware and found through a pointer the firmware leaves
for the OS. The one that describes devices is the **DSDT** (Differentiated System Description
Table), plus optional **SSDT**s. Inside them, each device is an object with methods and named
values:

- **`_HID`** (Hardware ID) — what the device is, such as `"QEMU0002"` or `"PNP0501"` (a 16550
  UART). Drivers match on it. **`_CID`** gives compatible IDs as a fallback.
- **`_CRS`** (Current Resource Settings) — its I/O ports, memory ranges and interrupts.
- **`_STA`** — whether the device is present and enabled.

Unlike a device tree, ACPI tables contain **AML**: bytecode the kernel's ACPI interpreter executes.
A `_CRS` can be a method that computes its answer, and `_PS0`/`_PS3` methods switch the device's
power state by running firmware-supplied code. That flexibility lets one OS image run on hardware
it has never seen, at the cost of trusting firmware code. The raw tables are visible at
`/sys/firmware/acpi/tables/`.

ACPI can also carry device-tree-style properties. The special `_HID` **`PRP0001`** tells the kernel
to match the device using a `compatible` property inside the ACPI `_DSD` object, so a driver with
only an `of_match_table` can bind on an ACPI system.

## The platform bus

Whatever described a device, Linux turns most described, non-enumerable devices into a
<Src file="include/linux/platform_device.h" symbol="platform_device" /> on the **platform bus**. A
<Src file="include/linux/platform_device.h" symbol="platform_driver" /> registers against that bus
with whatever match tables it supports, and the bus's match function tries each in turn.
<Src file="drivers/base/platform.c" symbol="platform_match" /> in v6.18 checks, in order:

1. `driver_override`, if set (only that driver may bind);
2. a device-tree match against the driver's `of_match_table`;
3. an ACPI match against its `acpi_match_table`;
4. the driver's `id_table` of plain platform device names;
5. finally, the driver's name against the device's name.

Resources arrive the same way regardless of source. The firmware description is translated into
`struct resource` entries on the device, which the driver reads with `platform_get_resource()`, or
more often maps directly with `devm_platform_ioremap_resource()` and `platform_get_irq()`.

## One driver, both descriptions

QEMU's firmware-configuration device, `fw_cfg`, is a real example. The emulated machine describes
it whichever way the guest architecture expects, and one driver,
`drivers/firmware/qemu_fw_cfg.c`, handles both:

```c
static const struct of_device_id fw_cfg_sysfs_mmio_match[] = {
	{ .compatible = "qemu,fw-cfg-mmio", },
	{},
};
MODULE_DEVICE_TABLE(of, fw_cfg_sysfs_mmio_match);

#ifdef CONFIG_ACPI
static const struct acpi_device_id fw_cfg_sysfs_acpi_match[] = {
	{ FW_CFG_ACPI_DEVICE_ID, },		/* "QEMU0002" */
	{},
};
MODULE_DEVICE_TABLE(acpi, fw_cfg_sysfs_acpi_match);
#endif

static struct platform_driver fw_cfg_sysfs_driver = {
	.probe = fw_cfg_sysfs_probe,
	.remove = fw_cfg_sysfs_remove,
	.driver = {
		.name = "fw_cfg",
		.of_match_table = fw_cfg_sysfs_mmio_match,
		.acpi_match_table = ACPI_PTR(fw_cfg_sysfs_acpi_match),
	},
};
```

Here are the two descriptions of that device. The ACPI one was decompiled with `iasl -d` from the
DSDT of the folder-01 Debian VM (x86-64). The device-tree node is the example from the kernel's
binding document for the device, as QEMU's arm64 `virt` machine presents it:

<Tabs>
<TabItem value="dt" label="Device tree (arm64 virt machine)">

```text
fw-cfg@9020000 {
    compatible = "qemu,fw-cfg-mmio";
    reg = <0x9020000 0xa>;
};
```

</TabItem>
<TabItem value="acpi" label="ACPI (x86-64 PC machine)">

```text
Device (FWCF)
{
    Name (_HID, "QEMU0002")  // _HID: Hardware ID
    Name (_STA, 0x0B)  // _STA: Status
    Name (_CRS, ResourceTemplate ()  // _CRS: Current Resource Settings
    {
        IO (Decode16,
            0x0510,             // Range Minimum
            0x0510,             // Range Maximum
            0x01,               // Alignment
            0x0C,               // Length
            )
    })
}
```

</TabItem>
</Tabs>

| Question | Device tree | ACPI |
|---|---|---|
| What is it? | `compatible = "qemu,fw-cfg-mmio"` | `_HID "QEMU0002"` |
| Where are its registers? | `reg = <0x9020000 0xa>`: 10 bytes of **MMIO** | `_CRS` → `IO(…0x0510…, 0x0C)`: 12 **I/O ports** |
| Is it present? | Node exists (or `status = "okay"`) | `_STA = 0x0B` |
| Interrupts | `interrupts = <…>` (none for this device) | An `Interrupt` entry inside `_CRS` (none here) |

The same driver ends up with a `struct resource` in both cases. On x86-64 that resource is
`IORESOURCE_IO` and on arm64 it is `IORESOURCE_MEM`, and the driver checks which kind it got.

:::note[arm64]
Device tree is the norm on arm64 embedded and mobile systems, and the whole of the SoC is usually
described that way. arm64 *servers*, however, typically boot with ACPI under Arm's SBSA/BSA and
SBBR/BBR standards, so the same distribution kernel can boot them the way it boots an x86-64
server. The register window differs too: x86-64 has a separate I/O-port address space (the `IO`
resource above), while arm64 has none, so QEMU's arm64 machine puts the same device in MMIO. See
[MMIO, `ioremap`, and Accessors](./mmio-and-port-io.md).
:::

On the x86-64 VM, the device-tree side is simply absent, and the ACPI-described device shows up as
a platform device bound to `fw_cfg`:

```text
$ uname -r
6.12.113+deb13-cloud-amd64
$ ls /sys/firmware/acpi/tables/
APIC  DSDT  FACP  FACS  HPET  WAET  data  dynamic
$ ls /proc/device-tree
ls: cannot access '/proc/device-tree': No such file or directory
$ cat /sys/bus/acpi/devices/QEMU0002:00/path
\_SB_.PCI0.FWCF
$ cat /sys/bus/platform/devices/QEMU0002:00/modalias
acpi:QEMU0002:
$ readlink -f /sys/bus/platform/devices/QEMU0002:00/driver
/sys/bus/platform/drivers/fw_cfg
```

The platform device is named after its ACPI device (`QEMU0002:00`). Its `modalias`, `acpi:QEMU0002:`,
is what lets `udev` load `qemu_fw_cfg.ko` automatically: `MODULE_DEVICE_TABLE(acpi, …)` above
recorded that same alias in the module.

## Choosing and reading

You rarely choose between the two. The platform's firmware decides, and a driver for hardware that
can appear on both kinds of system supplies both match tables. Inside the driver, the
**unified device property API** reads properties without caring where they came from:
`device_property_read_u32()`, `device_property_read_string()` and
`device_get_match_data()` work against a device-tree node or an ACPI `_DSD` alike. New drivers
should use it rather than the `of_`-prefixed calls, so that they also work on ACPI systems.

When a described device is not being detected, check in this order:

1. Is it in the description at all? Look under `/proc/device-tree/` or in an `iasl -d` dump.
2. Is it present as a platform device? Check `ls /sys/bus/platform/devices/`.
3. Does its `modalias` match an alias of the driver you expect? Compare
   `cat …/modalias` with `modinfo <driver> | grep alias`.
4. Did it bind? Check the `driver` symlink, then `devices_deferred` (see
   [Debugging Drivers](./debugging-drivers.md)).

<KernelFacts
  structure={[["struct platform_driver", "include/linux/platform_device.h"], ["struct of_device_id", "include/linux/mod_devicetable.h"]]}
  path="platform_driver_register() → driver_register() → platform_match(): driver_override → of_driver_match_device() → acpi_driver_match_device() → id_table → name → probe()"
  observe="ls /sys/bus/platform/devices; ls /proc/device-tree 2>/dev/null || ls /sys/firmware/acpi/tables"
  trap="A `compatible` string or `_HID` that differs from the driver's table by one character never matches, and nothing reports an error. The device simply sits on the platform bus unbound." />

## References

- [Linux and the Devicetree](https://docs.kernel.org/devicetree/usage-model.html) — how the kernel
  uses device tree: matching, platform-device creation, and what a `.dtb` contains.
- [ACPI Based Device Enumeration](https://docs.kernel.org/firmware-guide/acpi/enumeration.html) —
  how ACPI-described devices become platform, I²C and SPI devices, including `PRP0001` and `_DSD`
  properties.
- [Devicetree Specification](https://www.devicetree.org/specifications/) — the format itself:
  nodes, standard properties, and the `.dtb` layout.
- <Src file="drivers/base/platform.c" symbol="platform_match" /> — the five-step matching order
  above, in about twenty lines.
- <Src file="drivers/firmware/qemu_fw_cfg.c" /> — the `fw_cfg` driver used as this page's example;
  a short, real driver with both match tables.
