---
id: memory-map-and-bit-banding
title: The Cortex-M Memory Map
sidebar_label: The Memory Map and Bit-Banding
sidebar_position: 5
tags: [embedded, cortex-m, arm, memory, bit-banding, stm32]
---

# The Cortex-M Memory Map

A microcontroller has one 4 GB address space and everything lives in it: flash, RAM, every peripheral register, the interrupt controller, the debug hardware. There is no MMU, so what you write in a pointer is the physical address the bus sees. That is the simplification that makes bare-metal firmware tractable — and it means the *layout* of that space is not a vendor's private business but part of the architecture you program against.

Arm fixed the layout. Armv7-M divides the 4 GB into eight 0.5 GB partitions with fixed names, fixed default memory *types* and fixed execute-never attributes, and a silicon vendor populates those partitions rather than rearranging them (*Armv7-M ARM*, DDI 0403E.e §B3.1). The practical consequence is the one worth carrying: **the address alone tells you how the processor will treat an access.** An access at `0x2000_0400` may be reordered, cached and speculatively prefetched. An access at `0x4002_0014` may not be reordered relative to other peripheral accesses, must not be cached, and cannot be executed. You do not configure that; it is a property of the address.

This page covers what that map is, what "Normal", "Device" and "Strongly-ordered" actually promise, how ST populates the map on the STM32F411, and bit-banding — a Cortex-M3 and Cortex-M4 feature that is very commonly, and wrongly, described as a Cortex-M feature.

:::info[Prerequisites]
[Reading a Datasheet](../01-hardware-foundations/reading-a-datasheet.md) explains the division of labour between a datasheet, a reference manual and a programming manual, which is exactly the division this page's citations follow. [CPU Caches](../../computer-science/memory-hierarchy/cpu-caches.md) owns cache theory; the memory *types* below are the mechanism a Cortex-M uses instead of leaving that to a cache controller.
:::

## The architectural address map

Every row here is *Armv7-M ARM* DDI 0403E.e, **Table B3-1 "Armv7-M address map"**, with the System region expanded from **Table B3-2**.

| Address range | Name | Memory type | XN? | Cache attribute | What it is for |
|---|---|---|---|---|---|
| `0x0000_0000`–`0x1FFF_FFFF` | Code | Normal | — | WT | "Typically ROM or flash memory." |
| `0x2000_0000`–`0x3FFF_FFFF` | SRAM | Normal | — | WBWA | "SRAM region typically used for on-chip RAM." |
| `0x4000_0000`–`0x5FFF_FFFF` | Peripheral | Device | **XN** | — | "On-chip peripheral address space." |
| `0x6000_0000`–`0x7FFF_FFFF` | RAM | Normal | — | WBWA | Off-chip memory, write-back write-allocate. |
| `0x8000_0000`–`0x9FFF_FFFF` | RAM | Normal | — | WT | Off-chip memory, write-through. |
| `0xA000_0000`–`0xBFFF_FFFF` | Device | Device, shareable | **XN** | — | "Shared device space." |
| `0xC000_0000`–`0xDFFF_FFFF` | Device | Device, non-shareable | **XN** | — | "Non-shared device space." |
| `0xE000_0000`–`0xE00F_FFFF` | **PPB** | **Strongly-ordered** | **XN** | — | "1MB region reserved as the PPB. This supports key resources, including the System Control Space, and debug features." |
| `0xE010_0000`–`0xFFFF_FFFF` | Vendor_SYS | Device | **XN** | — | "Vendor system region." |

Five things follow directly.

**The Peripheral region and everything from `0xA000_0000` upward is execute-never.** The `DefaultPermissions()` pseudocode in *Armv7-M ARM* §B3.5 enumerates it one region at a time, keyed on address bits `[31:29]`:

```text
case address<31:29> of
  when '000' perms.xn = '0';   /* 0x00000000  Code               */
  when '001' perms.xn = '0';   /* 0x20000000  SRAM               */
  when '010' perms.xn = '1';   /* 0x40000000  Peripheral         */
  when '011' perms.xn = '0';   /* 0x60000000  RAM                */
  when '100' perms.xn = '0';   /* 0x80000000  RAM                */
  when '101' perms.xn = '1';   /* 0xA0000000  Device, shareable  */
  when '110' perms.xn = '1';   /* 0xC0000000  Device, non-shar.  */
  when '111' perms.xn = '1';   /* 0xE0000000  System             */
```

So XN covers exactly four of the eight partitions — `010`, `101`, `110` and `111` — and this matches the XN column of the table above, including the two blanks: **the external RAM regions `0x6000_0000`–`0x9FFF_FFFF` are Normal memory and are executable.** That is not a curiosity; running code out of external RAM is a real technique on parts that have an external memory controller.

Any attempt to fetch an instruction from one of the four XN partitions raises a MemManage fault, which is why a corrupted function pointer landing in peripheral space produces a fault rather than executing garbage.

**Of those four, only the System region's XN is beyond an enabled MPU's reach.** *Armv7-M ARM* §B3.1 carries the note "An enabled MPU cannot change the XN property of the System memory region", and §B3.5 states the rule and its scope: "The MPU is restricted in how it can change the default memory map attributes associated with System space, that is, for addresses `0xE0000000` and higher. System space is always marked as XN, Execute Never." The `CheckPermission` path enforces it unconditionally — `if address<31:29> == '111' then // enforce System space execute never; perms.xn = '1';`. For the Peripheral and Device regions the default XN is a *default*: an MPU region covering them can clear it.

**The Private Peripheral Bus is where Arm's own hardware lives.** Inside it, `0xE000_E000`–`0xE000_EFFF` is the System Control Space, holding the NVIC, SysTick, the SCB, the MPU registers, and the fault status registers (*Armv7-M ARM* §B1.3). Those addresses are identical on every Cortex-M, which is exactly why CMSIS core code is portable and vendor peripheral code is not.

**The PPB has stricter access rules than ordinary memory.** *Armv7-M ARM* §B3.1.1: "Register accesses are always little endian, regardless of the endian state of the processor. In general and unless otherwise stated, registers support word accesses only, with byte and halfword access UNPREDICTABLE." A byte write to an NVIC register is not a clever optimisation; it is undefined behaviour with an exception carved out for the byte-aligned priority and fault-status fields.

**Code should live in the Code region even though SRAM is executable.** PM0214 Rev 10 §2.2.3 gives the reason and it is about buses, not permissions: "The Code, SRAM, and external RAM regions can hold programs. However, it is recommended that programs always use the Code region. The reason of this is that the processor has separate buses that enable instruction fetches and data accesses to occur simultaneously."

## Memory types: what the processor promises

The type column above is not documentation. It changes what the hardware is allowed to do to your accesses.

| Type | What the processor may do (PM0214 Rev 10 §2.2.1) |
|---|---|
| **Normal** | "The processor can re-order transactions for efficiency, or perform speculative reads." |
| **Device** | "The processor preserves transaction order relative to other transactions to Device or Strongly-ordered memory." |
| **Strongly-ordered** | "The processor preserves transaction order relative to all other transactions." |

PM0214 §2.2.1 draws the Device/Strongly-ordered line precisely: "the memory system can buffer a write to Device memory, but must not buffer a write to Strongly-ordered memory."

That distinction is worth holding, because it explains something people often attribute to `volatile`. `volatile` is a *compiler* keyword: it stops the compiler eliding or reordering an access. It says nothing about what the *bus* does. The reason a sequence of writes to two different peripherals arrives in program order is that both live in Device memory and the architecture orders Device accesses relative to each other — not because you wrote `volatile`. And the reason two accesses to *different* memory types can still be reordered is Table 12 "Ordering of memory accesses", which shows that a Normal access and a Device access have no guaranteed relative order in either direction.

So peripheral registers need `volatile` **and** the ordering guarantee, for different reasons and against different opponents. Where the guarantee is not enough — a write to a peripheral that must land before a DMA controller reads a buffer in Normal memory, for instance — you need an explicit barrier. PM0214 §2.2.4 lists the three (`DMB`, `DSB`, `ISB`) and, usefully, names five situations that require one, including one that belongs to the next page: "Vector table. If the program changes an entry in the vector table, and then enables the corresponding exception, use a DMB instruction between the operations."

The full treatment of `volatile` and of barriers belongs to the bare-metal folder; what belongs here is the reason the memory *map* is doing part of that job for you.

## How ST populates the map on the STM32F411

The architecture reserves the space; RM0383 says what is actually in it. The concrete picture for the NUCLEO-F411RE's STM32F411RE, from RM0383 Rev 4:

| Address range | Contents | Source |
|---|---|---|
| `0x0000_0000`–`0x0007_FFFF` | **Alias** of whichever memory the boot pins selected | Table 3 |
| `0x0800_0000`–`0x0807_FFFF` | Flash memory, 512 KB | Table 3 |
| `0x1FFF_0000`–`0x1FFF_77FF` | System memory (ST's factory bootloader) | Table 3 |
| `0x2000_0000`–`0x2002_0000` | SRAM1, 128 KB | Table 3, §2.3.1 |
| `0x2200_0000`–`0x23FF_FFFF` | SRAM bit-band alias | PM0214 Table 14 |
| `0x4000_0000`–`0x4000_73FF` | APB1 peripherals — TIM2–TIM5, RTC, watchdogs, SPI2/3, USART2, I2C1–3, PWR | Table 1 |
| `0x4001_0000`–`0x4001_53FF` | APB2 peripherals — TIM1, USART1/6, ADC1, SDIO, SPI1/4/5, SYSCFG, EXTI, TIM9–11 | Table 1 |
| `0x4002_0000`–`0x4002_67FF` | AHB1 peripherals — GPIOA–GPIOE, GPIOH, CRC, RCC, flash interface, DMA1/2 | Table 1 |
| `0x4200_0000`–`0x43FF_FFFF` | Peripheral bit-band alias | PM0214 Table 15 |
| `0x5000_0000`–`0x5003_FFFF` | USB OTG FS (AHB2) | Table 1 |
| `0xE000_0000`–`0xE00F_FFFF` | PPB — NVIC, SysTick, SCB, MPU | *Armv7-M ARM* Table B3-2 |

Note the alias at address zero. RM0383 Rev 4 §2.4 explains why it has to exist: "The Cortex-M4 with FPU CPU always fetches the reset vector on the ICode bus, which implies to have the boot space available only in the code area (typically, flash memory)." The `BOOT[1:0]` pins choose which memory is aliased there — main flash, system memory, or embedded SRAM (Table 2) — and Table 3's footnote adds the detail that saves confusion later: "Even when aliased in the boot memory space, the related memory is still accessible at its original memory space." Flash appears at both `0x0000_0000` and `0x0800_0000`, simultaneously, and linker scripts conventionally use the latter because it is unambiguous. [Reset and Boot Configuration](../01-hardware-foundations/reset-and-boot-configuration.md) covers the boot-pin side.

## Bit-banding

### What it is

Bit-banding maps one bit of memory to one whole word of a separate *alias* address range, so that a single load or store to the alias reads or writes one bit — no read-modify-write in your instruction stream, and therefore nothing an interrupt can land in the middle of.

There are two banded areas, and both are the *lowest 1 MB* of their region. From PM0214 Rev 10 §2.2.5, Tables 14 and 15:

| Bit-band region (1 MB) | Alias region (32 MB) | Covers |
|---|---|---|
| `0x2000_0000`–`0x200F_FFFF` | `0x2200_0000`–`0x23FF_FFFF` | The bottom 1 MB of SRAM |
| `0x4000_0000`–`0x400F_FFFF` | `0x4200_0000`–`0x43FF_FFFF` | The bottom 1 MB of peripheral space |

32 MB of alias for 1 MB of region is exactly the 32× expansion you would expect: one 32-bit word per bit, and 1 MB × 8 bits × 4 bytes = 32 MB.

The mapping formula, verbatim from PM0214 Rev 10 §2.2.5:

```text
bit_word_offset = (byte_offset x 32) + (bit_number x 4)
bit_word_addr   = bit_band_base + bit_word_offset
```

where `bit_band_base` is the start of the *alias* region, `byte_offset` is the byte's offset within the bit-band region, and `bit_number` is 0–7 within that byte.

RM0383 Rev 4 §2.3.3 works an example that is worth reproducing because it is the arithmetic you will actually do:

> The following example shows how to map bit 2 of the byte located at SRAM address `0x20000300` to the alias region: `0x22006008 = 0x22000000 + (0x300*32) + (2*4)`. Writing to address `0x22006008` has the same effect as a read-modify-write operation on bit 2 of the byte at SRAM address `0x20000300`.

Reads and writes both behave sensibly. PM0214 §2.2.5: writing a word to the alias sets the target bit from **bit 0 of the value written** — "Writing `0x01` has the same effect as writing `0xFF`. Writing `0x00` has the same effect as writing `0x0E`" — and reading returns `0x00000000` or `0x00000001`.

In C the idiom is a macro:

```c
/* PM0214 Rev 10, section 2.2.5. addr must be in 0x20000000-0x200FFFFF
   (SRAM) or 0x40000000-0x400FFFFF (peripheral); bit is 0-31 within
   the word at addr, which the formula turns into a byte plus a bit. */
#define BITBAND_SRAM(addr, bit) \
    (*(volatile uint32_t *)(0x22000000u + (((uint32_t)(addr) - 0x20000000u) * 32u) + ((bit) * 4u)))
#define BITBAND_PERIPH(addr, bit) \
    (*(volatile uint32_t *)(0x42000000u + (((uint32_t)(addr) - 0x40000000u) * 32u) + ((bit) * 4u)))
```

### Where it exists, and where it does not

This is the part that gets stated wrongly more often than any other fact in this folder.

| Core | Architecture | Bit-banding | Evidence |
|---|---|---|---|
| Cortex-M0, M0+ | Armv6-M | **No** | Arm's product pages list no Bit Manipulation feature; ST's Cortex-M0+ programming manual PM0223 contains no bit-band section, region or alias. |
| **Cortex-M3** | Armv7-M | **Yes** | Arm's Cortex-M3 page, Bit Manipulation row: "Integrated Bit-field Processing Instructions and Bus Level Bit Banding". |
| **Cortex-M4** | Armv7E-M | **Yes** | Arm's Cortex-M4 page, Bit Manipulation row: "Integrated Bit Field Processing Instructions & Bus Level Bit Banding". PM0214 §2.2.5. |
| Cortex-M7 | Armv7E-M | **No** | Arm's Cortex-M7 page, Bit Manipulation row: "Integrated Bit-Field Processing Instructions" — and nothing more. ST's PM0253 states the consequence outright, below. |
| Cortex-M23, M33, M55 | Armv8-M / v8.1-M | **No** | ST's Cortex-M33 programming manual PM0264 contains no bit-band section, region or alias. |

Two independent pieces of evidence make this solid rather than a claim from memory.

First, **bit-banding does not appear in the Armv7-M Architecture Reference Manual at all** — not the term, not the alias base addresses, not the mapping formula. It is documented in the *processor* manuals (Arm's Cortex-M3 and Cortex-M4 device generic user guides, and vendor manuals derived from them) because it is a property of those cores' bus interconnect, not of the instruction set architecture. That is why an Armv7E-M core, the Cortex-M7, can lack a feature that another Armv7E-M core, the Cortex-M4, has.

Second, ST says so directly. PM0253 Rev 6 §3.1.1, "Binary compatibility with other Cortex processors": **"The code designed for other Cortex-M processors is compatible with Cortex-M7 as long as it does not rely on bit-banding."**

So the accurate statement is: **bit-banding is a Cortex-M3 and Cortex-M4 feature. It is absent from M0 and M0+, absent from M7, and absent from the Armv8-M cores.** Writing it as "a Cortex-M feature" is the error, and it is the kind that survives review because it sounds right.

### Is it worth using?

Honestly: usually not, and the reasons are worth knowing before you build a driver on it.

It buys you a genuinely uninterruptible single-bit update. PM0214 Rev 10 §2.2 says bit-banding "provides atomic operations to bit data" — the read-modify-write happens inside the bus fabric rather than as three instructions in your program, so no interrupt can preempt it halfway. That is a real property, and the alternative (`reg |= mask`) is a real bug when an ISR touches the same register.

Against that:

- **It is not portable.** Everything in the table above. Code built on bit-banding does not move to an M0+, an M7 or an M33.
- **The atomicity is against interrupts, not against other bus masters.** RM0383 Rev 4 §2.3.3 is explicit that on this family "The operations are only available for Cortex-M4 with FPU accesses, and not from other bus masters (e.g. DMA)." A DMA controller cannot use the alias, and a bit-band write is still a read-modify-write on the bus that a concurrent master could interleave with.
- **It only covers the bottom 1 MB of each region.** On the STM32F411 that is enough for all of SRAM and for the APB and AHB1 peripheral blocks, but not for anything above `0x400F_FFFF` — USB OTG FS at `0x5000_0000`, for example, is outside it entirely.
- **Better tools exist for the common cases.** Many STM32 peripherals provide a dedicated atomic set/reset register — `GPIOx_BSRR` being the canonical one — which needs no aliasing and works everywhere. For general read-modify-write atomicity, `LDREX`/`STREX` are architectural (PM0214 §2.2.7) and portable across every Cortex-M3 and later.

The honest recommendation: know it exists, recognise it when you see it in vendor code, use `BSRR`-style registers and `LDREX`/`STREX` when you need atomicity, and reach for bit-banding only when it is clearly the simplest thing and you have accepted that the code is M3/M4-only.

:::warning[Three ways the memory map produces a fault that reads as a compiler bug]
**Reading a peripheral without `volatile`.** The compiler sees a load from a constant address, no writes in between, and caches the value in a register. Your polling loop spins forever on a status bit that changed three microseconds ago. Nothing in the memory map protects you here — Device memory constrains the *bus*, not the compiler — and the failure only appears at `-O2`, which is why "it works in the debug build" is the classic symptom.

**Assuming `volatile` gives you ordering across memory types.** It does not. PM0214 Rev 10, Table 12 shows that a Normal access and a Device access have no guaranteed order relative to each other in either direction. Fill a buffer in SRAM, then write the DMA enable bit, and the architecture does not promise the buffer writes have landed. You need a `DMB`. This one is genuinely dangerous because it works almost always — the reordering window is small — and fails under load or after a compiler upgrade.

**Byte- or halfword-accessing a PPB register.** "In general and unless otherwise stated, registers support word accesses only, with byte and halfword access UNPREDICTABLE" (*Armv7-M ARM* §B3.1.1). The exceptions are real and useful — priority registers and fault status registers are explicitly byte-addressable — but they are exceptions. A halfword write to `SysTick->CTRL` is not a smaller version of a word write; it is undefined.

And the one that is not a fault at all, which makes it the worst: **bit-banding an address outside the banded 1 MB**. The macros above compute an alias address by arithmetic and cannot tell that the input was out of range — and the arithmetic is a 32× multiply, so it overflows. Feed `BITBAND_PERIPH` the USB OTG FS base at `0x5000_0000`: the subtraction gives `0x1000_0000`, multiplying by 32 gives `0x2_0000_0000`, and truncating to 32 bits gives **zero**. The macro returns `0x4200_0000` plus your bit offset — a perfectly legal alias address that points at the bottom of the *peripheral* bit-band region, i.e. at `TIM2_CR1`. Your write silently modifies a timer you were not thinking about, at the moment you thought you were configuring USB, with no fault and no clue. Check that the address is inside `0x2000_0000`–`0x200F_FFFF` or `0x4000_0000`–`0x400F_FFFF` before aliasing it — or use `BSRR` and sidestep the whole thing.
:::

## See also

- [The Register Model](./cortex-m-register-model.md) — the special registers that live in the core rather than in the address space, and why they need `MRS`/`MSR`.
- [Exceptions and the Vector Table](./exceptions-and-the-vector-table.md) — the one structure the hardware reads out of the Code region without being told to.
- [The Cortex-M Family](./arm-cortex-m-profiles.md) — the per-core feature table this page's bit-banding row comes from.
- [Reset and Boot Configuration](../01-hardware-foundations/reset-and-boot-configuration.md) — the `BOOT[1:0]` pins that decide what is aliased at address zero.
- [CPU Caches](../../computer-science/memory-hierarchy/cpu-caches.md) — the cache behaviour the memory-type column is standing in for, and which becomes a real concern on Cortex-M7.

## References

- Arm — [***Armv7-M Architecture Reference Manual***](https://developer.arm.com/documentation/ddi0403/latest/), consulted at **DDI 0403E.e (ID021621)**. §B3.1 "The system address map" with **Table B3-1** (the eight partitions, their memory types, XN and cache attributes) and **Table B3-2** (the PPB/Vendor_SYS split of the System region); §B3.1.1 "General rules for PPB register accesses" for the word-access rule and little-endian requirement; §B1.3 for the System Control Space at `0xE000_E000`; §B3.5 "Protected Memory System Architecture, PMSAv7" for the `DefaultPermissions()` per-region XN assignment quoted above (XN on address bits `[31:29]` of `010`, `101`, `110` and `111` — note that the two RAM partitions `011` and `100` are **not** XN), for the "System space is always marked as XN" restriction on an enabled MPU, and for the `address<31:29> == '111'` enforcement in the permission-check pseudocode. Bit-banding is **not** described anywhere in this manual, which is the evidence for it being a processor rather than an architecture feature.
- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), consulted at **Rev 10** (March 2020). §2.2 "Memory model" and Figure 8 for the map as ST states it; §2.2.1 for the Normal/Device/Strongly-ordered definitions and the write-buffering distinction; §2.2.2 and **Table 12** for the ordering guarantees between types; §2.2.3 and Table 13 for per-region access behaviour and the Code-region recommendation; §2.2.4 for the barrier instructions and when to use them; §2.2.5 with **Tables 14 and 15** for the bit-band regions, aliases and mapping formula; §2.2.7 for `LDREX`/`STREX`. Note that Table 13's PPB row prints its address range inconsistently with Figure 8 in the version consulted — Figure 8 and the *Armv7-M ARM* agree on `0xE000_0000`–`0xE00F_FFFF`, which is the value used above.
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). §2.2–§2.3 with **Table 1** "STM32F411xC/E register boundary addresses" for every peripheral base address quoted; §2.3.1 for the 128 KB of SRAM; §2.3.3 "Bit banding" for the worked `0x22006008` example and the statement that bit-band operations are unavailable to DMA and other bus masters; §2.4 with **Table 2** (boot modes) and **Table 3** (memory mapping versus boot mode) for the alias at address zero.
- STMicroelectronics — [**PM0253**, *STM32F7 and STM32H7 series Cortex-M7 processor programming manual*](https://www.st.com/resource/en/programming_manual/pm0253-stm32f7-series-and-stm32h7-series-cortexm7-processor-programming-manual-stmicroelectronics.pdf), consulted at **Rev 6** (May 2026). §3.1.1 for the quoted bit-banding compatibility statement, and its §2.2 memory-model chapter — which describes the same eight regions as PM0214 but contains no bit-band region, alias or formula.
- STMicroelectronics — [**PM0223**, *STM32 Cortex-M0+ MCUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0223-stm32-cortexm0-mcus-programming-manual-stmicroelectronics.pdf) and [**PM0264**, *STM32 Cortex-M33 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0264-stm32-cortexm33-mcus-programming-manual-stmicroelectronics.pdf). Consulted specifically to confirm the negative: neither document contains the terms "bit-band", "bit band" or "bit-banding" anywhere, on any revision retrieved 2026-08-19.
- Arm — [**Cortex-M3**](https://developer.arm.com/Processors/Cortex-M3), [**Cortex-M4**](https://developer.arm.com/Processors/Cortex-M4) and [**Cortex-M7**](https://developer.arm.com/Processors/Cortex-M7) product-support pages, retrieved 2026-08-19. The Bit Manipulation row of each, which names "Bus Level Bit Banding" on the first two and omits it on the third.
