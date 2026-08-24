---
id: register-level-programming
title: Register-Level Programming
sidebar_label: Register-Level Programming
sidebar_position: 2
tags: [embedded, bare-metal, registers, mmio, volatile, bitwise, stm32]
---

# Register-Level Programming

A peripheral is a piece of digital logic sitting on the same bus as your RAM. It has no API, no calling convention and no way to be invoked. The only interface it exposes is a small block of addresses: write a word to one of them and some flip-flops change state; read from another and you get the current state of some wires. That is the whole model.

The mental model worth internalising: **a register is not a variable.** It happens to be reachable through a pointer, and C will happily let you treat it like storage, but almost every intuition you have about storage is wrong here. Reading it twice can give different answers. Writing it can have effects far away and no effect on what you read back. Some registers clear a bit when you write a `1` to it; some clear when you *read* them; some are write-only and read as zero. The compiler knows none of this, which is why the pointer must be `volatile` and why you must think about the exact sequence of accesses in a way you never do for ordinary C.

:::info[Prerequisites]
[Bit Manipulation Techniques](../../computer-science/bit-manipulation/techniques.md) owns masking, shifting, and the bitwise idioms themselves — this page assumes them and only covers what changes when the target is hardware. [The Cortex-M Memory Map](../02-processor-architecture/memory-map-and-bit-banding.md) establishes why the peripheral region behaves differently from SRAM. [Your First Bare-Metal Blink](./your-first-bare-metal-blink.md) is the working program this page generalises.
:::

## Where peripherals live

On Cortex-M the address space is architecturally partitioned, and the partition is what gives peripheral accesses their behaviour. The `0x4000_0000`–`0x5FFF_FFFF` region is *Device* memory: accesses to it are not cached, not speculated, not merged, and not reordered with respect to each other by the processor. That is exactly what a peripheral needs, and you get it for free by virtue of the address — no MPU configuration required.

Within that region each vendor lays out its own map. On the STM32F411RE (RM0383 Rev 4, Table 1 "Register boundary addresses"):

| Base address | Bus | Peripheral |
|---|---|---|
| `0x4000 0000` | APB1 | TIM2 — and TIM3/4/5, RTC, I²C, USART2, SPI2/3 above it |
| `0x4001 0000` | APB2 | TIM1, USART1, USART6, ADC1, SPI1, SYSCFG, EXTI |
| `0x4002 0000` | AHB1 | **GPIOA** |
| `0x4002 0400` | AHB1 | GPIOB — each port is `0x400` further on |
| `0x4002 3800` | AHB1 | **RCC** |
| `0x4002 3C00` | AHB1 | FLASH interface |
| `0x4002 6000` | AHB1 | DMA1 |
| `0x4002 6400` | AHB1 | DMA2 |
| `0xE000 E000` | — | Cortex-M core peripherals: SysTick, NVIC, SCB |

Two structural facts fall out of that table and both matter in practice.

**Ports are evenly spaced.** GPIOA at `0x4002 0000`, GPIOB at `0x4002 0400`, and so on in `0x400` steps. This is deliberate and universal across vendors, and it is what makes a driver that takes a "port" argument possible at all — the port *is* the base address.

**Which bus a peripheral is on decides which `RCC_*ENR` register enables it.** GPIO is AHB1, so `RCC_AHB1ENR`. USART2 is APB1, so `RCC_APB1ENR`. USART1 is APB2, so `RCC_APB2ENR`. Enabling the right bit in the wrong register compiles, runs, and silently does nothing.

The `0xE000_E000` block is different in kind: it is part of the processor, identical on every Cortex-M4 from any vendor, and documented in PM0214 rather than RM0383. [SysTick and the Core Peripherals](../02-processor-architecture/systick-and-core-peripherals.md) covers it.

## The two ways to name a register

### Individual macros

```c
#define GPIOA_BASE   0x40020000u
#define GPIOA_MODER  (*(volatile uint32_t *)(GPIOA_BASE + 0x00u))
#define GPIOA_ODR    (*(volatile uint32_t *)(GPIOA_BASE + 0x14u))
```

Unpack the cast from the inside out: `GPIOA_BASE + 0x00u` is an integer; `(volatile uint32_t *)` reinterprets it as a pointer to a volatile 32-bit object; the leading `*` dereferences it, so the macro expands to an lvalue you can read and assign. `GPIOA_MODER |= 1;` compiles to a load, an orr and a store against that address.

This is honest and dependency-free, and it is what the blink page uses to keep the first program self-contained. It scales badly: every register needs its own line, the offsets are repeated, and nothing stops you writing `GPIOA_BASE + 0x14` where you meant `+ 0x18`.

### A struct overlay

```c
typedef struct {
    volatile uint32_t MODER;    /* 0x00 */
    volatile uint32_t OTYPER;   /* 0x04 */
    volatile uint32_t OSPEEDR;  /* 0x08 */
    volatile uint32_t PUPDR;    /* 0x0C */
    volatile uint32_t IDR;      /* 0x10 */
    volatile uint32_t ODR;      /* 0x14 */
    volatile uint32_t BSRR;     /* 0x18 */
    volatile uint32_t LCKR;     /* 0x1C */
    volatile uint32_t AFR[2];   /* 0x20, 0x24 — AFRL and AFRH */
} GPIO_TypeDef;

#define GPIOA  ((GPIO_TypeDef *)0x40020000u)
#define GPIOB  ((GPIO_TypeDef *)0x40020400u)
#define GPIOC  ((GPIO_TypeDef *)0x40020800u)
```

Now `GPIOA->MODER` is the register, `GPIOB->MODER` is the same register on another port, and a function can take a `GPIO_TypeDef *` and work on any of them. The offsets are stated once, by the layout of the struct, and the compiler computes them. This is the pattern every vendor header uses and the one [CMSIS and Vendor HALs](./cmsis-and-vendor-hals.md) formalises.

It relies on the struct's layout matching the hardware exactly, which on this target it does: `uint32_t` members with 4-byte alignment and no padding, in a compiler where `sizeof(uint32_t) == 4`. Gaps in the register map are represented by explicit reserved members, never by leaving them out:

```c
typedef struct {
    volatile uint32_t CR;          /* 0x00 */
    volatile uint32_t PLLCFGR;     /* 0x04 */
    volatile uint32_t CFGR;        /* 0x08 */
    volatile uint32_t CIR;         /* 0x0C */
    volatile uint32_t AHB1RSTR;    /* 0x10 */
    volatile uint32_t AHB2RSTR;    /* 0x14 */
    uint32_t          RESERVED0[2];/* 0x18, 0x1C — not implemented */
    volatile uint32_t APB1RSTR;    /* 0x20 */
    volatile uint32_t APB2RSTR;    /* 0x24 */
    uint32_t          RESERVED1[2];/* 0x28, 0x2C */
    volatile uint32_t AHB1ENR;     /* 0x30 */
    /* ... */
} RCC_TypeDef;
```

Note that the reserved members are deliberately *not* `volatile`: nothing may touch them, and dropping the qualifier makes an accidental access easier to spot in a review. Do not be tempted to compress a run of reserved words — every offset after the gap depends on it being the right size, and an off-by-one there produces a driver that writes to a plausible-looking wrong register.

## Read-modify-write, and the field idioms

Almost every register write is a read-modify-write, because a register holds unrelated fields and you must preserve the ones you are not changing. Three idioms cover nearly everything.

```c
/* Set bits: leave everything else alone. */
RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;

/* Clear bits. */
RCC->AHB1ENR &= ~RCC_AHB1ENR_GPIOAEN;

/* Replace a multi-bit field: CLEAR the field, THEN set the new value. */
GPIOA->MODER = (GPIOA->MODER & ~MODER_MASK(5)) | MODER_OUTPUT(5);
```

The third is the one that is not obvious, and getting it wrong is the subject of the next section. A useful pair of helpers, given a mask and its lowest bit:

```c
/* Field helpers. `mask` is the field in place; the shift is derived from it,
   so there is one source of truth per field instead of a mask and a shift
   that can drift apart. */
#define FIELD_PREP(mask, value)  (((value) << (__builtin_ctz(mask))) & (mask))
#define FIELD_GET(mask, reg)     (((reg) & (mask)) >> (__builtin_ctz(mask)))

#define GPIO_MODER_Msk(pin)  (3u << ((pin) * 2u))

/* PA5 = 01 (general purpose output) */
GPIOA->MODER = (GPIOA->MODER & ~GPIO_MODER_Msk(5))
             |  FIELD_PREP(GPIO_MODER_Msk(5), 1u);
```

`__builtin_ctz` — count trailing zeros — is a GCC and Clang builtin that folds to a constant at compile time whenever the mask is a constant, so this costs nothing at runtime. The same trick is how the Linux kernel's `FIELD_PREP`/`FIELD_GET` macros work, and it removes an entire class of "the mask and the shift disagree" defect.

## The two-bit-field bug, worked

Here is the failure, on real hardware, with real reset values.

You want `PA5` as an output and you write the obvious thing:

```c
GPIOA->MODER |= (1u << (5 * 2));   /* looks right — and is, by luck */
```

It works. `MODER5` reset to `00`, `00 | 01` is `01`, the LED blinks, and you conclude the idiom is fine. Then you use it on `PA13` — say to repurpose the SWDIO pin on a production board where debug is not fitted:

```c
GPIOA->MODER |= (1u << (13 * 2));  /* the same line. Now broken. */
```

`GPIOA_MODER` resets to `0xA800 0000` (RM0383 Rev 4 §8.4.1), so `MODER13` — bits 27:26 — starts at `10`, alternate function, because that pin is SWDIO out of reset. Watch the field:

| | Bits 27:26 | Meaning |
|---|---|---|
| Reset value | `10` | Alternate function (SWDIO) |
| You OR in | `01` | intending "general purpose output" |
| Result | `11` | **Analog mode** |

Analog mode disconnects the pin's digital output driver and its Schmitt trigger entirely. The pin does not drive, does not read, and draws almost no current. Every subsequent `BSRR` write is accepted by the GPIO block and simply has no electrical effect. There is no fault and no status bit — the peripheral is doing precisely what you asked.

What makes this expensive is that the debugger agrees with you. `MODER` reads `0xAC00 0000`; you check bit 26, it is set, "output bit is on", and you go looking at the wiring. The mistake is that a two-bit field has four values and you only checked one bit of it.

```c
/* The idiom that is correct on every field, including ones that reset to 00. */
GPIOA->MODER = (GPIOA->MODER & ~(3u << (13 * 2)))   /* clear the field  */
             |  (1u << (13 * 2));                    /* then set it      */
```

The rule generalises: **`|=` is only ever correct for a single-bit flag.** For anything two bits or wider, clear then set — even when the field currently reads zero, because "currently" is a property of program history, not of the code in front of you.

```wavedrom title="GPIOA_MODER bits 31:16 at reset — the debug pins are not zero" alt="Bit-field strip of the upper half of GPIOA_MODER showing MODER13, MODER14 and MODER15 in alternate-function mode at reset"
{ reg: [
    { bits: 2, name: "MODER8", type: 4 },
    { bits: 2, name: "MODER9", type: 4 },
    { bits: 2, name: "MODER10", type: 4 },
    { bits: 2, name: "MODER11", type: 4 },
    { bits: 2, name: "MODER12", type: 4 },
    { bits: 2, name: "MODER13", type: 2 },
    { bits: 2, name: "MODER14", type: 2 },
    { bits: 2, name: "MODER15", type: 2 }
  ],
  config: { hspace: 1000, bits: 16 }
}
```

| Field | Bits | Reset (port A) | Pin function at reset |
|---|---|---|---|
| `MODER8`…`MODER12` | 25:16 | `00` | Input |
| `MODER13` | 27:26 | `10` | **Alternate function** — `SWDIO` |
| `MODER14` | 29:28 | `10` | **Alternate function** — `SWCLK` |
| `MODER15` | 31:30 | `10` | **Alternate function** — `JTDI` |

Whole-register reset value `0xA800 0000`. The companion registers carry the same fingerprint: `GPIOA_PUPDR` resets to `0x6400 0000` — pull-up on `PA13` and `PA15`, pull-down on `PA14` — which is the board's SWD idle state, and `GPIOA_OSPEEDR` and `GPIOA_OTYPER` reset to `0x0000 0000`.

## Access width and access side effects

Two more ways a register differs from a variable, both of which bite eventually.

**Some registers must be accessed at a specific width.** A 32-bit register that only supports word access will ignore or corrupt a byte write. On the STM32F4 the GPIO and RCC registers accept byte, half-word and word access, but that is a property of these peripherals and not a general rule — RM0383 states the supported width per peripheral, and other families are stricter. Declaring the struct member `uint32_t` and assigning a `uint32_t` gets it right by construction; casting a register pointer to `uint8_t *` to poke one byte is how you find out that it did not.

**Reads and writes can have side effects.** Three patterns that recur across every vendor:

- **Read-to-clear.** Reading a status register clears its flags. A debugger's register view that reads every peripheral register on halt will clear them out from under you — which is why an interrupt flag can be "already gone" the moment you single-step. Not a bug in your code.
- **Write-1-to-clear (`rc_w1`).** Writing a `1` clears the flag; writing a `0` does nothing. So the correct code is `TIMx->SR = ~TIM_SR_UIF;` or `TIMx->SR = TIM_SR_UIF;` depending on the register's convention — but *never* `TIMx->SR &= ~TIM_SR_UIF`, which reads the whole register and writes back ones for every other flag that happened to be set, clearing them all.
- **Write-only.** `BSRR` reads as `0x0000 0000`. `GPIOA->BSRR |= x` therefore does exactly the same thing as `GPIOA->BSRR = x` on this part, but the read is meaningless and the habit will be wrong on the next register.

The reference manual states which of these applies per bit, in a column usually labelled "Type" or in the register's access legend: `rw`, `r`, `w`, `rc_w1`, `rc_r`, `t`. Reading that column is not optional detail work; it is where the semantics live.

:::warning[`SR &= ~FLAG` on a write-one-to-clear register clears every other flag too]
This is the interrupt bug that presents as "we lose events under load", and it survives code review because the line looks like careful, minimal bit clearing.

Take a timer status register with several flags — update, and four capture/compare channels. You want to acknowledge only the update event, so you write what looks like the conservative thing:

```c
TIM2->SR &= ~TIM_SR_UIF;    /* WRONG on a write-1-to-clear register */
```

The compiler emits a load, an `and`, and a store. Suppose at the moment of the load `UIF` and `CC1IF` are both set. The value read is `0b0011`; after `& ~UIF` it is `0b0010`; and that is what gets stored. On a `rc_w1` register, storing a `1` into `CC1IF` **clears** `CC1IF`. You have just acknowledged an interrupt you never handled. The capture value sits in the register unread, the handler for it never runs, and the symptom is an event that goes missing occasionally — more often as the interrupt rate rises, because the window in which a second flag can be set is what decides how often it happens.

The correct forms depend on the convention the peripheral uses, and both appear in ST's own drivers:

```c
TIM2->SR = ~TIM_SR_UIF;   /* write 0 to UIF (clears it), 1 elsewhere (no effect) */
TIM2->SR = TIM_SR_UIF;    /* on a plain rc_w1 register: write 1 to the bit to clear */
```

Note that the first is correct for the STM32 timer `SR`, whose flags are cleared by writing **zero** — the opposite of the more common `rc_w1`. There is no substitute for reading the access column for the specific register. The rule that always holds: **never read-modify-write a status register.** A single store, with a constant, is both correct and atomic.

The same shape appears in `EXTI->PR`, `DMA->LIFCR`/`HIFCR`, and every peripheral's interrupt-flag register. If you find `&= ~` applied to anything named `SR`, `PR`, `ISR` or `IFCR`, treat it as a defect until you have checked the manual.
:::

## See also

- [Your First Bare-Metal Blink](./your-first-bare-metal-blink.md) — the complete program these idioms were extracted from.
- [What `volatile` Does and Does Not Do](./volatile-and-the-compiler.md) — why every pointer above is `volatile`, and the guarantees that qualifier does not give.
- [CMSIS and Vendor HALs](./cmsis-and-vendor-hals.md) — the struct-overlay pattern above, standardised, plus the layers vendors build on top of it.
- [The Cortex-M Memory Map](../02-processor-architecture/memory-map-and-bit-banding.md) — why the peripheral region is Device memory and what bit-banding offers instead of read-modify-write.
- [Bit Manipulation Techniques](../../computer-science/bit-manipulation/techniques.md) — masking, shifting and the bitwise vocabulary this page assumes.

## References

- STMicroelectronics — [**RM0383**, *STM32F411xC/E advanced Arm-based 32-bit MCUs reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), consulted at **Rev 4** (May 2025). §1.1 "List of abbreviations for registers" for the `rw`/`r`/`w`/`rc_w1`/`rc_r`/`t` access legend that this page's side-effect section depends on; Table 1 "Register boundary addresses" for the base-address table; §8.4 for the GPIO register map, offsets and reset values including the `0xA800 0000` `MODER` and `0x6400 0000` `PUPDR` on port A; §6.3 for the RCC map and its reserved gaps.
- STMicroelectronics — [**PM0214**, *STM32 Cortex-M4 MCUs and MPUs programming manual*](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf), consulted at **Rev 10** (March 2020). §2.2 "Memory model" for the architectural memory regions and the Device-memory ordering rules that make peripheral accesses behave; §4 for the `0xE000 E000` core-peripheral block.
- Arm — [**Armv7-M Architecture Reference Manual**](https://developer.arm.com/documentation/ddi0403/latest/). §A3.5 "Memory access order" and the Device memory type: the normative statement that accesses to Device memory are not merged, reordered or speculated, which is what makes a `volatile` store to a peripheral do what you meant.
- ISO/IEC — **9899:2018** (C17), §6.7.3 "Type qualifiers" and §6.3.2.3 "Pointers". The standard's rules for `volatile`-qualified access and for converting an integer to a pointer — the operation every macro on this page performs, and one the standard describes as implementation-defined. The freely available [N2310 working draft](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n2310.pdf) tracks C17 closely.
