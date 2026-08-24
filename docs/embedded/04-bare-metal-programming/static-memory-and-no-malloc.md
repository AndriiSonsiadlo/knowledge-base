---
id: static-memory-and-no-malloc
title: Static Memory and Why malloc Is Banned
sidebar_label: Static Memory, No malloc
sidebar_position: 10
tags: [embedded, bare-metal, memory, malloc, heap, fragmentation, pools, misra]
---

# Static Memory and Why `malloc` Is Banned

Most embedded coding standards ban dynamic allocation after startup, and most engineers meet the rule before they meet the reason. Stated as a rule it sounds like superstition — `malloc` works, it is in the standard library, the vendor examples call it. Stated as a consequence it is obvious: **a device that runs for three years without restarting cannot use a memory strategy whose correctness depends on restarting.**

The mental model: on a desktop, allocation failure is rare, recoverable, and bounded by a process lifetime that ends in hours. On an MCU there is no virtual memory, no overcommit, no OOM killer, no swap, and no restart. You have one flat SRAM — 128 KB on an STM32F411RE — shared by globals, the stack, and whatever heap you carve out, and a program that must not fail once in a hundred million allocations. Dynamic allocation does not make that impossible, but it makes it *unanalysable*, and unanalysable is the thing safety standards actually object to.

:::info[Prerequisites]
[Memory Sections](../03-toolchain-and-build/memory-sections.md) covers `.data`, `.bss`, and where the heap and stack come from in the linker script. [ELF, Map Files and Size](../03-toolchain-and-build/elf-map-files-and-size.md) is how you find out what your static allocation actually costs. [C Libraries for Embedded](../03-toolchain-and-build/c-libraries-for-embedded.md) covers newlib-nano's allocator and the `_sbrk` stub that stands behind it.
:::

## The four objections

They are separate problems and they need separate answers. Conflating them is why the discussion usually goes badly.

| Objection | What actually happens | Does a fixed-size pool fix it? |
|---|---|---|
| **Fragmentation** | Free memory exists but not contiguously; a 200-byte request fails with 4 KB free | **Yes** — same-size blocks cannot fragment |
| **Non-deterministic timing** | `malloc` walks a free list; the walk length depends on history, so worst case is unbounded | **Yes** — pop from a free list head is O(1) |
| **Silent failure** | `malloc` returns `NULL`, nobody checks, next write is to address 0, which on a Cortex-M is *valid flash* and does nothing | Partly — the pool can still be empty, but the failure is local and countable |
| **Unanalysable footprint** | You cannot state, from the source, the peak RAM the program will use | **Yes** — the pool's size is a number in the linker map |

## Fragmentation in a process that never restarts

Fragmentation is the objection people find least convincing, because on a desktop it is genuinely rare. Here is why it is not rare here: a long-lived embedded program performs the *same* allocation pattern millions of times, so an unlucky interleaving does not have to be likely — it only has to be possible, and then it is certain.

An 8 KB heap, four points in time, every `free` correctly paired with its `malloc`:

```text
                 0K    1K    2K    3K    4K    5K    6K    7K    8K
                 |-----|-----|-----|-----|-----|-----|-----|-----|

t0  fresh        [ A   ][ B: 3K            ][ C   ][ D: 2K   ][ - ]
                                                                free: 1K   largest hole: 1K

t1  free B, D    [ A   ][ ~~~~~ hole 3K ~~~][ C   ][~ hole 2K~][ - ]
                                                                free: 6K   largest hole: 3K

t2  alloc E(1K)  [ A   ][ E   ][~ hole 2K ~][ C   ][ F: 2K   ][ - ]
    alloc F(2K)                                                 free: 3K   largest hole: 2K

t3  malloc(2.5K) [ A   ][ E   ][~ hole 2K ~][ C   ][ F: 2K   ][ - ]
                        ^^^^ FAILS: 3 KB is free, but no hole is 2.5 KB
```

Nothing leaked. Every `free` matched a `malloc`. The total free memory is more than the request. The allocation fails anyway, because the free memory is in the wrong *shape* — and the shape is a function of the entire allocation history of the device since it was powered on, which is not something you can put in a test.

This is why "we tested it for a week and it was fine" is not evidence. The failure mode is a rare interleaving compounded over months, and the field is the only place with enough samples to find it.

There is a second, sharper version on an MCU: **the heap and the stack grow toward each other in the same SRAM.** The usual bare-metal linker script puts `.bss` at the bottom, the heap above it growing up, and the stack at the top growing down, with nothing between them. A successful `malloc` that returns memory the stack is about to need is not detected by anything. The heap wins the race, the stack overwrites the allocation, and the corruption appears in an object the allocator handed out perfectly correctly. The next page is about that collision from the stack's side.

## The failure that is not reported

```c
uint8_t *buf = malloc(len);
memcpy(buf, src, len);        /* nobody checked. */
```

On a hosted system this segfaults, loudly, at the exact line. On a Cortex-M, address `0x0000_0000` is the start of flash (or the boot alias). Writing there does nothing at all — it is not writable, there is no MMU to object, and by default there is no fault. `memcpy` "succeeds", `buf` reads back as whatever was in flash, and the program continues with plausible-looking garbage. The symptom appears somewhere else entirely, minutes later.

Two things make this worse than it sounds:

- **Nobody checks `malloc`.** In host code the check is often skipped because failure means the machine is doomed anyway. That reasoning is imported wholesale into firmware, where failure is both likely and locally recoverable.
- **Newlib's `_sbrk` is usually a stub you wrote.** The default `_sbrk` in a bare-metal project either always succeeds — never bounds-checking against the stack — or is the `--specs=nosys.specs` version that returns an error. Which one you got is determined by a linker flag most people set by copying a Makefile. [C Libraries for Embedded](../03-toolchain-and-build/c-libraries-for-embedded.md) has the details.

The MPU turns this specific class into an immediate, diagnosable fault: a no-access region over the first page makes a null write a MemManage fault at the offending instruction. See [The MPU](../02-processor-architecture/the-mpu.md).

## What to do instead

### Static allocation, which is most of the answer

The overwhelming majority of embedded allocations are for objects whose maximum count is known at compile time. Write the maximum down and allocate it once:

```c
/* Not: struct sensor *s = malloc(sizeof *s); */
#define MAX_SENSORS 8
static sensor_t sensors[MAX_SENSORS];
static uint8_t  sensor_count;
```

This is not a workaround. It is strictly more informative than the dynamic version: the peak footprint is now in the map file, the bound is stated in the source where a reviewer can argue with it, and there is no allocation to fail. If `MAX_SENSORS` is genuinely unbounded, the program has a requirements problem that dynamic allocation would have hidden rather than solved.

### A fixed-size block pool

When objects come and go at runtime — network packets, log records, command objects — a pool gives you the lifetime flexibility of `malloc` with none of the four objections. All blocks are the same size, so a free block always fits a request, so fragmentation is definitionally impossible.

```c
#define POOL_BLOCKS 16
#define POOL_BLOCK_SIZE 128

typedef struct block { struct block *next; } block_t;

static uint8_t   pool_mem[POOL_BLOCKS][POOL_BLOCK_SIZE] __attribute__((aligned(8)));
static block_t  *free_list;
static uint8_t   in_use, high_water;    /* diagnostics are not optional */

void pool_init(void)
{
    free_list = NULL;
    for (size_t i = 0; i < POOL_BLOCKS; i++) {
        block_t *b = (block_t *)pool_mem[i];
        b->next   = free_list;           /* the free list lives in the free blocks */
        free_list = b;
    }
}

void *pool_alloc(void)                   /* O(1), always */
{
    uint32_t s = critical_enter();
    block_t *b = free_list;
    if (b != NULL) {
        free_list = b->next;
        if (++in_use > high_water) { high_water = in_use; }
    }
    critical_exit(s);
    return b;                            /* NULL means the pool is empty — check it */
}

void pool_free(void *p)
{
    if (p == NULL) { return; }
    uint32_t s = critical_enter();
    ((block_t *)p)->next = free_list;
    free_list = p;
    in_use--;
    critical_exit(s);
}
```

Forty lines, and every objection is answered. Note the details that matter more than the algorithm:

- **The free list is stored *inside* the free blocks.** Zero metadata overhead; a free block is not doing anything else with its first four bytes.
- **`high_water` is the whole point.** A pool without a high-water mark tells you nothing about whether 16 was the right number. Report it in your log or over the debug interface, run the device through its worst case, and read it. If it reaches 16, the pool is too small and you were one event away from an allocation failure in the field. If it peaks at 3, you are wasting 1.6 KB.
- **The critical section is required.** If any ISR calls `pool_alloc`, the free-list pop is a read-modify-write on shared state. See [Critical Sections and Atomicity](./critical-sections-and-atomicity.md).
- **`aligned(8)`** because a block may be cast to a struct containing a `double` or a `uint64_t`, and unaligned access to those is a fault or a performance cliff.

Several pools of different block sizes (32 / 128 / 512) covers almost everything a general allocator would, at the cost of rounding up. Rounding up is a known, bounded, computable waste — which is precisely the property `malloc` cannot offer.

### An arena, when nothing is ever freed individually

For a parse, a request, or a frame of work: bump a pointer to allocate, reset the pointer to free everything at once.

```c
static uint8_t  arena[2048];
static size_t   arena_used;

void *arena_alloc(size_t n)
{
    n = (n + 7u) & ~(size_t)7u;                      /* align up to 8 */
    if (arena_used + n > sizeof arena) { return NULL; }
    void *p = &arena[arena_used];
    arena_used += n;
    return p;
}

void arena_reset(void) { arena_used = 0; }           /* frees everything, O(1) */
```

Allocation is three instructions. There is no free list, no fragmentation, and no per-object lifetime to get wrong. The constraint — everything in the arena dies at the same moment — sounds severe and turns out to fit an enormous number of embedded workloads, because most embedded work is a cycle that ends.

### Ring buffers for streams

For data that flows — UART bytes, ADC samples, log lines — a fixed ring buffer is the right structure, not a queue of allocated nodes. One producer, one consumer, power-of-two size so the index wrap is a mask, and a documented policy for what happens when it is full (drop the oldest, drop the newest, or set an overrun flag). *Choosing* that policy is the design work; an allocator would have let you avoid choosing until it failed at 3 a.m.

## Where `malloc` is legitimately fine

The rule is not "never link an allocator". The defensible version, and the one most standards actually write down, is **no allocation after initialisation**:

- **Allocate at startup, never free.** A driver stack that allocates its buffers once during `init()` and holds them forever cannot fragment — there is exactly one allocation phase and no interleaving. This is how a lot of third-party middleware is legitimately used. Some teams go further and deliberately let `_sbrk` fail after `main` has started, which converts a violation into an immediate, obvious bug.
- **Third-party code you cannot modify.** A TCP/IP stack, a filesystem, or a TLS library may require an allocator. Give it a *dedicated* pool or heap region sized from measurement, so that its failure is contained and its footprint is a number in the map.
- **On a Linux-class device.** Different machine, different rules — an MMU, a restartable process, and an OOM killer change the analysis entirely.

MISRA C:2012 states this as Rule 21.3 ("the memory allocation and deallocation functions of `<stdlib.h>` shall not be used"), and it is a *required* rule with a documented deviation process — which is the standard admitting that the answer is sometimes "yes, with justification", not "never". The justification is what the process is for.

:::warning[The device that runs for six weeks and then stops responding]
The archetypal dynamic-memory bug in firmware has three properties that together make it exceptionally expensive: it takes weeks to appear, it appears only in the field, and the crash is nowhere near the cause.

A logging subsystem allocates a record per event and frees it after the record is written. It is correct — no leak, every `malloc` has a `free`. Over six weeks the allocation sizes vary with message length, the heap fragments, and one day a 512-byte request fails while 3 KB is free. `malloc` returns `NULL`, the unchecked `memcpy` writes to address 0, which on a Cortex-M is flash and silently does nothing. The record is garbage. Two hours later a *different* subsystem's allocation succeeds but lands in a block adjacent to a heap header that an earlier overrun corrupted, and the allocator's free-list walk follows a bad pointer and hangs inside `malloc` with interrupts enabled and the watchdog un-refreshed. The device resets. It comes back up, works perfectly, and does it again in six weeks.

What the field report says is "random reboots". What the developer sees on the bench is nothing at all, for as long as they are willing to wait.

The three habits that make this not happen:

- **`grep -rn 'malloc\|calloc\|realloc\|strdup\|new ' src/`** as a CI step, allowed only in an explicit allowlist of files. A rule nobody enforces is a rule that decays.
- **If you must have a heap, instrument it.** Newlib's `mallinfo()` gives you `arena`, `uordblks` and `fordblks`; log the largest free block, not just the total. A shrinking largest-free-block over days *is* fragmentation, visible weeks before it becomes a failure.
- **Set the heap size to zero in the linker script if you do not intend to have one.** Then a stray `malloc` fails immediately, at the first call, on the bench, on the day someone adds it — instead of six weeks after shipping. This is the highest-value fifteen seconds in this entire page.
:::

## See also

- [Stack Usage and Overflow](./stack-usage-and-overflow.md) — the other consumer of the same SRAM, and the collision the heap makes possible.
- [Memory Sections](../03-toolchain-and-build/memory-sections.md) — `.data`, `.bss`, the heap and stack regions, and how the linker script assigns them.
- [ELF, Map Files and Size](../03-toolchain-and-build/elf-map-files-and-size.md) — reading the actual cost of every static array you just declared.
- [Critical Sections and Atomicity](./critical-sections-and-atomicity.md) — protecting the pool free list when an ISR allocates from it.
- [The MPU](../02-processor-architecture/the-mpu.md) — making a null-pointer write fault instead of silently doing nothing.

## References

- MISRA — [***MISRA C:2012***, *Guidelines for the Use of the C Language in Critical Systems*](https://misra.org.uk/product/misra-c2012-third-edition-first-revision/), third edition, first revision (2019). **Rule 21.3** prohibits `malloc`, `calloc`, `realloc` and `free`; the rationale section is the concise statement of the fragmentation and determinism arguments above, and Directive 4.12 ("dynamic memory allocation shall not be used") gives the broader design-level version. Both are *required* rules, subject to the documented deviation process.
- Jack Ganssle — [**"Dynamic Memory Allocation"** and the *Embedded Muse* archive](http://www.ganssle.com/tem-back.htm). Ganssle's long-running argument against heaps in firmware, including field data on fragmentation-induced failures and the "allocate at init, never free" compromise. See also his [**"Firmware Standard"**](http://www.ganssle.com/fsm.htm), which codifies the rule for a working team.
- Free Software Foundation / Red Hat — [**Newlib documentation, "Memory Allocation"**](https://sourceware.org/newlib/libc.html#Stdlib). `malloc`, `_sbrk` and `mallinfo`; the `arena`, `uordblks` and `fordblks` fields used for the fragmentation instrumentation above, and newlib-nano's smaller allocator variant.
- Carnegie Mellon University SEI — [**CERT C Coding Standard, MEM sections**](https://wiki.sei.cmu.edu/confluence/display/c/Rule+08.+Memory+Management+%28MEM%29). MEM32-C on checking the return of memory-allocation functions, MEM34-C on freeing only dynamically allocated memory, and MEM35-C on allocating sufficient memory — the failure modes the unchecked-`NULL` section describes.
- STMicroelectronics — [**RM0383**, *STM32F411xC/E reference manual*](https://www.st.com/resource/en/reference_manual/rm0383-stm32f411xce-advanced-armbased-32bit-mcus-stmicroelectronics.pdf), Rev 4. §2.3 for the memory map: 128 KB of SRAM starting at `0x2000 0000`, and the flash aliased at `0x0000 0000` that makes a null write silently harmless.
