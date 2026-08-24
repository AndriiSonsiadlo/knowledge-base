---
id: embedded-c-idioms
title: Embedded C Idioms
sidebar_label: Embedded C Idioms
sidebar_position: 12
tags: [embedded, bare-metal, c, idioms, packed, endianness, bitfields, cert-c, misra]
---

# Embedded C Idioms

Embedded C is the same language as any other C. What differs is which of its underspecified corners you are standing on. On a desktop, `int` is 32 bits, structs are laid out the way you expect, unaligned access works, and the byte order matches whatever produced the file. In firmware you are parsing a protocol written by someone else's compiler, laying a struct over a hardware register, and running on a part where `int` might be 16 bits and an unaligned load might be a fault.

The mental model: **an embedded idiom is a way of writing something so that the thing the standard leaves open cannot hurt you.** Every entry below is a small piece of syntax that trades a little verbosity for the removal of an entire failure mode — usually one that is invisible until the code is ported, the compiler is upgraded, or the optimiser gets smarter.

:::info[Prerequisites]
[Register-Level Programming](./register-level-programming.md) covers memory-mapped I/O and the field-clear-then-set idiom, which the bitfield section here argues against replacing with language features. [Integers and Two's Complement](../../computer-science/bit-manipulation/integers-and-twos-complement.md) owns integer representation, promotion and overflow — the mechanics under several of the traps below. [What `volatile` Does and Does Not Do](./volatile-and-the-compiler.md) is a prerequisite for anything touching hardware.
:::

## The idioms and what each one prevents

| Idiom | Instead of | The mistake it prevents |
|---|---|---|
| `uint32_t`, `int16_t` from `<stdint.h>` | `int`, `long`, `unsigned` | A type whose width changes with the target. `int` is 16 bits on many compilers for 8- and 16-bit parts; `long` is 32 on ARM and 64 on x86-64 |
| `static` on every non-exported function and file-scope variable | External linkage by default | Name collisions at link time, and an optimiser that cannot prove a function is only called from one place |
| `const` after the thing it protects: `uint32_t * const p` | Guessing which side | Making the *pointer* read-only when you meant the *target*, or vice versa |
| `sizeof x` / `sizeof arr / sizeof arr[0]` | A hardcoded length | The buffer overrun that appears the day someone changes the array size and misses one of the two places |
| Designated initialisers: `.baud = 115200` | Positional initialisation | Silently shifting every field when a member is inserted into the struct |
| `_Static_assert` on every layout assumption | A comment | Discovering at runtime, on hardware, that the struct is not the size the protocol says |
| `memcpy` into a local, or byte-wise assembly, for wire data | Casting a pointer to a packed struct | An unaligned or wrong-endian read that works on one target and faults or corrupts on another |
| Explicit shift-and-mask for hardware registers | Bitfield structs | The compiler choosing a byte-wide access to a 32-bit register, or ordering fields the other way round |
| `U` suffix on unsigned constants: `1U << 31` | `1 << 31` | Undefined behaviour — shifting into the sign bit of a signed `int` |
| Braces on every `if`/`while`, even one-liners | Bare statements | The second statement someone adds later that is not actually in the branch |
| `enum` for state, `switch` with no `default` that falls off | Magic numbers | An unhandled state that the compiler could have warned about under `-Wswitch` |

The rest of this page is the four that are genuinely subtle.

## Packed structs and alignment

The temptation with a wire protocol is irresistible: describe the packet as a struct, cast the receive buffer to it, read the fields.

```c
typedef struct __attribute__((packed)) {
    uint8_t  id;
    uint32_t value;      /* at offset 1 — not 4-byte aligned */
    uint16_t crc;
} msg_t;

uint32_t read_packed(const msg_t *m) { return m->value; }
```

Whether this works depends entirely on the target, and here is what the same source produces on two Cortex-M parts with the same compiler:

<Tabs>
<TabItem value="m4" label="Cortex-M4 (Armv7-M)" default>

```armasm
read_packed:
        ldr.w   r0, [r0, #1]      @ one unaligned word load. Works.
        bx      lr
```

Armv7-M supports unaligned `LDR`/`STR` in hardware, so the compiler emits the obvious instruction and it is fast.

</TabItem>
<TabItem value="m0" label="Cortex-M0 (Armv6-M)">

```armasm
read_packed:
        ldrb    r2, [r0, #2]
        ldrb    r3, [r0, #1]
        lsls    r2, r2, #8
        orrs    r2, r3
        ldrb    r3, [r0, #3]
        ldrb    r0, [r0, #4]
        lsls    r3, r3, #16
        orrs    r3, r2
        lsls    r0, r0, #24
        orrs    r0, r3
        bx      lr
```

Armv6-M has no unaligned access at all, so the compiler synthesises the load from four byte reads and six ALU operations. Eleven instructions instead of one — correct, but a factor of ten, in a parser that may run per byte.

</TabItem>
</Tabs>

*Both: GCC 14.2.Rel1, `-Os -mthumb`, `-mcpu=cortex-m4` and `-mcpu=cortex-m0`.*

So `__attribute__((packed))` is *safe* — the compiler knows the member is unaligned and does whatever the target requires. What is not safe is the version people actually write:

```c
uint32_t value = *(uint32_t *)(buf + 1);   /* ← undefined behaviour */
```

Here the compiler has no idea the pointer is unaligned. It emits a plain aligned load, which:

- works on Cortex-M4 by luck, until someone sets `SCB->CCR.UNALIGN_TRP` to catch exactly this, at which point it is a UsageFault;
- **HardFaults immediately** on Cortex-M0/M0+, where unaligned `LDR` is not merely slow but architecturally invalid;
- can be miscompiled even on M4, because the compiler is entitled to assume the pointer is aligned and may transform the surrounding code accordingly — for example by using `LDM` or `LDRD`, which do *not* support unaligned access even on Armv7-M.

The portable idiom is `memcpy`, which every compiler recognises and lowers to whatever the target can actually do:

```c
uint32_t value;
memcpy(&value, buf + 1, sizeof value);     /* correct everywhere, free at -O1+ */
```

And the assumption you made about the layout gets written down where it can fail loudly:

```c
_Static_assert(sizeof(msg_t) == 7, "protocol says 7 bytes on the wire");
_Static_assert(offsetof(msg_t, crc) == 5, "crc must follow value immediately");
```

Without `packed` the same struct is **12 bytes** on ARM, not 7 — the compiler inserts three padding bytes before `value` (to 4-align it at offset 4) and two after `crc` (to round the struct up to a multiple of its 4-byte alignment). Sending it over a wire, writing it to flash, or comparing it with `memcmp` are all then wrong in a way no test on a single target will reveal. The `_Static_assert` costs nothing and fails at compile time on the day the layout changes.

## Bitfields are not for hardware registers

A struct of bitfields looks like the perfect description of a peripheral register:

```c
typedef struct { uint32_t a : 3; uint32_t b : 5; uint32_t c : 24; } bits_t;
void set_b(bits_t *p) { p->b = 5; }
```

Here is what GCC 14.2 actually generates for `set_b` on Cortex-M4 at `-Os`:

```armasm
set_b:
        ldrb    r3, [r0, #0]       @ ← an 8-BIT read of a 32-bit register
        movs    r2, #5
        bfi     r3, r2, #3, #5
        strb    r3, [r0, #0]       @ ← an 8-BIT write
        bx      lr
```

The compiler correctly noticed that field `b` lives entirely within the first byte, so it used a byte access. That is a perfectly legal optimisation on memory. On a peripheral it can be a disaster: a great many hardware registers are documented as 32-bit access only, and a byte write to them is ignored, or writes the wrong thing, or generates a bus fault. Nothing in the C source says "this must be one 32-bit store".

:::note[The struct above is not `volatile`, and that matters here]
A real register would be, and on ARM that changes this particular listing. The Arm EABI mandates that a `volatile` bitfield is accessed using the width of its declared container type, which GCC implements as `-fstrict-volatile-bitfields` — on by default for ARM targets. Declaring the same three fields `volatile uint32_t` and recompiling gives:

```armasm
set_vb:
        ldr     r3, [r0, #0]       @ full 32-bit read — the ARM EABI rule
        movs    r2, #5
        bfi     r3, r2, #3, #5
        str     r3, [r0, #0]       @ full 32-bit write
        bx      lr
```

*GCC 14.2.Rel1, `-Os -mcpu=cortex-m4 -mthumb`, with and without `-fno-strict-volatile-bitfields` — identical output in this case.*

So on ARM GCC with `volatile`, the access-width objection does not bite. It bites on targets or toolchains without that ABI rule, on compilers that do not implement it, and if the flag is ever turned off — and it depends on an ABI guarantee rather than on anything the C standard promises, which is a thin thing to build a register map on.

The width objection is therefore the least portable of the five, not the strongest. **Each of the four below is independently sufficient**, and all four apply even in the `volatile` ARM case above — note that the listing is still a `ldr`…`str` read-modify-write, not one atomic operation.
:::

The remaining objections:

- **Bit order within a unit is implementation-defined.** C17 §6.7.2.1¶11: whether the first declared field occupies the low-order or high-order bits is up to the implementation. GCC on ARM puts it low; another compiler may not. Your register map is then silently mirrored.
- **The allocation unit and padding are implementation-defined too** (§6.7.2.1¶11). Whether a field that would straddle a boundary is split or moved is not specified.
- **A field is not atomic.** `p->b = 5` above is a read-modify-write, with all the consequences from [Critical Sections and Atomicity](./critical-sections-and-atomicity.md).
- **Read-sensitive registers break.** A read-modify-write on a status register clears flags you never intended to touch — see [Register-Level Programming](./register-level-programming.md).

The idiom that has none of these problems is the one CMSIS device headers use throughout: a `volatile uint32_t` member and named shift/mask macros.

```c
#define USART_CR1_OVER8_Pos   (15U)
#define USART_CR1_OVER8_Msk   (0x1UL << USART_CR1_OVER8_Pos)

USART1->CR1 = (USART1->CR1 & ~USART_CR1_OVER8_Msk)
            | (1UL << USART_CR1_OVER8_Pos);      /* exactly one 32-bit store */
```

Verbose, explicit, one access of the documented width, and portable. Bitfields remain a perfectly good tool for *internal* data structures where you are packing your own state to save RAM and no hardware is watching.

## Endianness, and the only way to parse a protocol

The STM32 is little-endian. So is every Cortex-M in practice. That is precisely why endianness bugs in firmware survive so long: the code works on your target and fails against the peer, the file format, or the network — all of which are frequently big-endian.

The rule is that **the wire has an endianness and your CPU has an endianness, and the only place they may meet is in explicit code.** Not in a cast, not in a union, not in a `memcpy` of a multi-byte field.

```c
/* Correct on every machine, because it never depends on host layout. */
static uint32_t be32(const uint8_t *p)
{
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16)
         | ((uint32_t)p[2] <<  8) |  (uint32_t)p[3];
}

static void put_be32(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)(v >> 24); p[1] = (uint8_t)(v >> 16);
    p[2] = (uint8_t)(v >>  8); p[3] = (uint8_t)v;
}
```

Note the casts on the way in. Without `(uint32_t)`, `p[0]` is a `uint8_t` that gets promoted to `int`, and `p[0] << 24` shifts a value into the sign bit of a 32-bit signed `int` — undefined behaviour, and on a 16-bit `int` target it is a guaranteed zero. This is the integer-promotion trap and it turns up everywhere in byte-fiddling code; [Integers and Two's Complement](../../computer-science/bit-manipulation/integers-and-twos-complement.md) has the general rules.

Do not reach for a union to do this. Type-punning through a union is defined in C but is *reading the host's byte order*, which is exactly the dependency you are trying to remove. And do not reach for `htonl` unless you know where it came from — it is a POSIX networking function, not a C one, and the version in your vendor stack may or may not be a no-op.

At `-O2` GCC recognises the shift-and-or pattern above and compiles it to a single `REV` instruction on Armv7-M, so the portable version costs nothing. Write the portable one.

## Designated initialisers for configuration tables

Firmware is full of tables: pin maps, baud-rate tables, task lists, register initialisation sequences. Positional initialisation of these is a latent bug that detonates on an unrelated edit.

```c
/* Positional: correct today. */
static const pin_cfg_t pins[] = {
    { GPIOA, 5, MODE_OUTPUT, PULL_NONE, SPEED_LOW },
    { GPIOC, 13, MODE_INPUT, PULL_UP,   SPEED_LOW },
};
```

Insert a `drive_type` member into the middle of `pin_cfg_t` and every row silently shifts: `MODE_OUTPUT` becomes the drive type, `PULL_NONE` becomes the mode. The types are all small integers or enums, so nothing warns, and the failure is a pin configured as an input when it should drive a MOSFET.

```c
/* Designated: survives the edit, and reads as documentation. */
static const pin_cfg_t pins[] = {
    { .port = GPIOA, .pin = 5,  .mode = MODE_OUTPUT, .pull = PULL_NONE },
    { .port = GPIOC, .pin = 13, .mode = MODE_INPUT,  .pull = PULL_UP   },
};
```

Members not mentioned are zero-initialised, which is why the enums in such a table should be defined with the safe default as zero — `MODE_INPUT = 0`, `PULL_NONE = 0` — so that an omitted field fails safe rather than into an output driving a bus.

The same technique makes vector tables and command dispatch tables robust:

```c
static void (* const commands[CMD_COUNT])(const char *) = {
    [CMD_STATUS] = cmd_status,
    [CMD_RESET]  = cmd_reset,
    [CMD_DUMP]   = cmd_dump,
};
```

Adding a command to the enum can no longer renumber the others, and any slot you forget is `NULL` — which you can check for — rather than pointing at the wrong function.

And `const` on the table is not decoration: it puts the array in `.rodata`, which the linker places in flash. On a 128 KB-RAM part, moving a few kilobytes of configuration tables out of `.data` is often the single largest RAM saving available. [Memory Sections](../03-toolchain-and-build/memory-sections.md) covers where each qualifier sends your data.

:::warning[The struct that was seven bytes on the sender and twelve on the receiver]
The most expensive idiom failure is the one that spans two devices, because neither one is wrong on its own.

A sensor node and a gateway share a header file defining the message struct. The node is a Cortex-M0+ built with one vendor's compiler; the gateway is a Cortex-M4 built with another. The struct has a `uint8_t` followed by a `uint32_t`. Nobody wrote `packed`, so both compilers insert padding — but they are entitled to make different choices about how much and where, and even with identical padding, *the sender writes the struct's bytes including its uninitialised padding bytes*. Those bytes are whatever was on the stack. The CRC computed over `sizeof(msg_t)` therefore covers three bytes of garbage and fails intermittently, at a rate that depends on what the sender was doing before it built the message.

The team spends a week on the radio link. The radio is fine.

The same family of bug, with a different trigger each time:

- **A compiler upgrade changes padding or bitfield allocation**, and a firmware image can no longer read the configuration blob written to flash by its predecessor. Every device that takes the update loses its calibration.
- **`sizeof` is used as the wire length.** It is the *in-memory* size, and it includes padding. The wire length is a constant from the protocol specification, and the two agreeing is an assertion, not an assumption.
- **A field is added to the end of a persisted struct**, and old records are now short. Without a version byte as the first member, there is no way to tell.

Three habits, each about ten seconds of typing:

1. **`_Static_assert(sizeof(msg_t) == 7, "wire size")` next to every struct that crosses a boundary** — a wire, a flash sector, a shared-memory region, an API to code built separately. The check runs at compile time on every build, on both sides.
2. **Serialise field by field.** A `msg_to_bytes()` function using `put_be32` and friends is twenty lines that make layout, order and endianness explicit and immune to every compiler decision above. It is the boring answer, and it is the one that does not fail.
3. **Version the first byte of anything persisted.** Then the reader can refuse, migrate, or default — instead of interpreting the new layout with the old code.
:::

## See also

- [Register-Level Programming](./register-level-programming.md) — the shift-and-mask register idiom that this page argues against replacing with bitfields, and the read-modify-write rules for status registers.
- [Critical Sections and Atomicity](./critical-sections-and-atomicity.md) — why a bitfield assignment being a read-modify-write matters when an ISR touches the same register.
- [Memory Sections](../03-toolchain-and-build/memory-sections.md) — where `const`, `static` and initialised data actually land, and the flash-versus-RAM consequence of each.
- [Integers and Two's Complement](../../computer-science/bit-manipulation/integers-and-twos-complement.md) — integer promotion, signedness and overflow: the mechanics behind the `1U << 31` and `p[0] << 24` traps above.
- [Stack Usage and Overflow](./stack-usage-and-overflow.md) — why "pass a pointer, not a struct by value" is a stack-budget idiom as well as a performance one.

## References

- ISO/IEC — **9899:2018** (C17). §6.7.2.1¶11 for bitfields: the implementation-defined allocation order within a storage unit and the implementation-defined addressable allocation unit — the two clauses that make bitfield register maps non-portable; §6.3.1.1 for the integer promotions behind the `p[0] << 24` trap; §6.5.7 for shift behaviour, including the undefined result of shifting into the sign bit; §6.7.9 for designated initialisers and the zero-initialisation of omitted members. The freely available [N2310 working draft](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n2310.pdf) tracks the published text closely.
- Carnegie Mellon University SEI — [**CERT C Coding Standard**](https://wiki.sei.cmu.edu/confluence/display/c/SEI+CERT+C+Coding+Standard). EXP36-C (do not cast pointers to more strictly aligned types) is the rule the `*(uint32_t *)(buf + 1)` example violates; INT13-C on bitwise operators and unsigned operands; INT34-C on shifts; EXP11-C on type-punning; and the "Bit Manipulation" recommendations covering the `U` suffix idiom.
- MISRA — [***MISRA C:2012***](https://misra.org.uk/product/misra-c2012-third-edition-first-revision/), third edition, first revision. Directive 4.6 (use typedefs indicating size and signedness), Rule 6.1 and 6.2 on permitted bitfield types, Rule 8.7 and 8.8 on internal linkage and `static`, Rule 10.x on the essential type model, and Rule 15.6 on compound statements — the codified forms of most of the table above.
- Free Software Foundation — [**GCC manual, "Common Type Attributes"**](https://gcc.gnu.org/onlinedocs/gcc/Common-Type-Attributes.html) and [**"Structures, Unions, Enumerations, and Bit-Fields Implementation"**](https://gcc.gnu.org/onlinedocs/gcc/Structures-unions-enumerations-and-bit-fields-implementation.html). `packed` and `aligned`, and GCC's documented answers to every question C17 §6.7.2.1 leaves implementation-defined — which is the only reason the bitfield layout on your target is predictable at all. See also [**`-fstrict-volatile-bitfields`**](https://gcc.gnu.org/onlinedocs/gcc/Code-Gen-Options.html) in "Options for Code Generation Conventions": the flag that makes a `volatile` bitfield be accessed at the width of its declared type, enabled by default where the target ABI requires it, as the Arm EABI does.
- Arm — [**Armv7-M Architecture Reference Manual**](https://developer.arm.com/documentation/ddi0403/latest/) (DDI 0403), §A3.2 "Alignment support". Which instructions support unaligned access (`LDR`, `LDRH` and their store forms) and which never do (`LDM`, `STM`, `LDRD`, `STRD`, and all exclusive accesses); `CCR.UNALIGN_TRP` for turning permitted unaligned accesses into UsageFaults. The Armv6-M manual's corresponding section states that unaligned access is not supported at all, which is what the Cortex-M0 listing above reflects.

*Instruction listings on this page were produced with Arm GNU Toolchain 14.2.Rel1 (GCC 14.2.1) at `-Os -mthumb`, targeting `-mcpu=cortex-m4` and `-mcpu=cortex-m0`.*
