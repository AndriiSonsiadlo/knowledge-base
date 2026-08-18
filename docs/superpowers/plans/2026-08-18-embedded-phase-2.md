# Embedded Systems Docs — Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the 55 pages that take a reader from "I can blink an LED" to "I can build and debug a real product": peripherals and drivers, real-time behaviour, an RTOS, low-power design, and the debugging toolbox.

**Architecture:** Pure content on top of the infrastructure Phase 1 built. No new dependencies, no new components, no config changes. Five folders (05, 06, 07, 09, 11) of plain Markdown using the WaveDrom, Mermaid, `<Figure>`, and `<Tabs>` machinery already wired into the site.

**Tech Stack:** Docusaurus 3.10.2 Markdown; the `remark-wavedrom` plugin and `WaveDrom`/`Tabs` MDX components from Phase 1. Subject matter: STM32F411RE peripherals, Arm Cortex-M4 timing, FreeRTOS and Zephyr, SWD/GDB/RTT/logic analyzers.

**Spec:** `docs/superpowers/specs/2026-08-18-embedded-systems-docs-design.md` — read it before starting. This plan implements Phase 2 of three. The spec's page-by-page outline is the source of truth for every page's title and content brief; this plan does not repeat those briefs.

**Prerequisite:** Phase 1 (`docs/superpowers/plans/2026-08-18-embedded-phase-1.md`) must be complete and merged. Folders `00-overview` … `04-bare-metal-programming` and the WaveDrom pipeline must exist. Verify before starting:

```bash
find docs/embedded -name '*.md' -not -name 'readme.md' | wc -l   # expect 51
npm run test:plugins                                             # expect 8 passing
npm run build                                                    # expect exit 0
```

## Global Constraints

Copied from the spec and from the Phase 1 plan's verified baseline. Every task's requirements implicitly include this section.

- **Folders added in this phase:** `05-peripherals-and-drivers` (14 pages), `06-interrupts-timing-and-real-time` (9), `07-rtos` (13), `09-low-power-design` (7), `11-debugging-and-testing` (12). **Folders 08, 10, and 12–15 belong to Phase 3 and must not be created or linked.**
- **`_category_.json`:** 2-space indent, keys `label`, `position`, `link.type = "generated-index"`. `position` = numeric folder prefix + 1 (so `05-` is position 6, `11-` is position 12).
- **Frontmatter:** every page has `id`, `title`, `sidebar_label`, `sidebar_position`, `tags`. `tags` starts with `embedded`. Folder 07 pages add `rtos` plus the kernel slug (`freertos` or `zephyr`). `sidebar_position` starts at 1 within each folder.
- **Page shape:** mental model before mechanism (never open with code, a register table, or a definition list) → optional `:::info[Prerequisites]` → body → **at least one visual anchor** → at least one `:::warning` naming a real day-costing mistake → `## See also` (3–5 relative links) → `## References` (2–6 annotated external sources, primary first; no bare URLs).
- **Admonitions:** only `:::info`, `:::note`, `:::tip`, `:::warning`.
- **Code fences:** `c`, `cpp`, `rust`, `armasm`, `bash`, `cmake`, `makefile`, `ini`, `json`, `toml`, `diff`, `python`. Device tree, Kconfig, and linker scripts use ` ```text `.
- **WaveDrom:** at most 2–3 waveforms per page; ≤ 8 signals each; every bit-field strip is paired with a semantics table giving field meaning and reset value.
- **Images:** `static/img/embedded/<folder-slug>/<name>.png` via `<Figure src="/img/embedded/..." />` — no `/knowledge-base` prefix. Every image needs a row in `static/img/embedded/SOURCES.md` **in the same commit**. Source order: Bootlin (CC BY-SA) → Wikimedia Commons → vendor primary docs → own photographs. Never a blog or image-host copy. If no clean source exists, use Mermaid or WaveDrom — that is the correct outcome.
- **Link rule:** a page may link to folders 00–04 (Phase 1) and to folders **already written earlier in this phase**. It may **never** link to folders 08, 10, or 12–15. `onBrokenLinks: "throw"` turns a violation into a deploy failure.
- **No-duplication contract:** the spec's normative table names existing pages that own their topics. Phase 2 is the phase where this matters most — `computer-science/buses-and-io/serial-buses-i2c-spi-uart.md` owns I2C/SPI/UART basics, and `computer-science/operating-systems/{scheduling,concurrency-and-synchronization}.md` own general scheduling and concurrency theory. Link, then write only what is additional.
- **Lint gate:** `npm run lint` repo-wide **already fails** with 157 pre-existing errors in unrelated files. Do not fix them and do not gate on them. Gate on `npx biome check docs/embedded`.
- **Commits:** per CLAUDE.md — `<type>: <what>` on one line, no body unless needed, **never** a `Co-Authored-By` trailer or a "Generated with Claude Code" line.

### Hardware target

Unchanged from Phase 1: **NUCLEO-F411RE** (STM32F411RE, Cortex-M4F, 100 MHz, 512 KB flash, 128 KB SRAM). Reference documents: ST **RM0383** (MCU reference manual), ST **PM0214** (Cortex-M4 programming manual), ST **UM1724** (board), Arm *Armv7-M Architecture Reference Manual*.

### Content currency

The spec requires context7 verification for **folder 07** (FreeRTOS kernel version and task-notification API; Zephyr devicetree, Kconfig, and `west`). Do this before writing Tasks 6–8, and record the check date in the affected pages' `## References` annotations. FreeRTOS's task notification API gained the `xTaskNotifyIndexed` family, and Zephyr's build tooling moves quickly — do not write either from memory.

### Recommended model per task

| Tasks | Model | Why |
|---|---|---|
| 1–3 (peripherals), 6–8 (RTOS), 12–13 (debugging) | Opus 5 | Exact mechanism — bus error recovery, context switching, fault forensics — where fluent-but-wrong is the main risk |
| 4–5 (real-time) | Opus 5 | Scheduling analysis and WCET involve arithmetic that must be right |
| 9–10 (low power) | Sonnet 5 acceptable | Descriptive; claims check against datasheet tables |
| 11 (completion sweep) | Opus 5 | Cross-cutting consistency |

---

## File Structure

No source files change. This phase creates only content:

| Path | Contents |
|---|---|
| `docs/embedded/05-peripherals-and-drivers/` | `_category_.json` + 14 pages |
| `docs/embedded/06-interrupts-timing-and-real-time/` | `_category_.json` + 9 pages |
| `docs/embedded/07-rtos/` | `_category_.json` + 13 pages |
| `docs/embedded/09-low-power-design/` | `_category_.json` + 7 pages |
| `docs/embedded/11-debugging-and-testing/` | `_category_.json` + 12 pages |
| `static/img/embedded/SOURCES.md` | Appended rows for any figures added |
| `docs/embedded/readme.md` | Modified once, in the final task |

Folders are written in numeric order. Because folder 11 is written last, the pages in 05–09 that
naturally want to point at it record their intent in prose, and **Task 11 adds those links** once
the targets exist. The deferred links are listed explicitly in Task 11 — do not improvise them.

---

## Content task recipe

Every task below writes Markdown. There is no TDD cycle for prose; the equivalent feedback loop is
**write the page → build → check conventions → commit**. The build is not a formality:
`onBrokenLinks: "throw"` turns a mistyped relative link into a deploy failure.

For each page:

1. Read that page's row in the spec's "Page-by-page outline" — that brief is the requirement.
2. Check the spec's no-duplication table. If an existing page owns the topic, link to it with a
   correct relative path (e.g. `../../computer-science/operating-systems/scheduling.md`) and write
   only what is *additional*.
3. Write the page to the shape in Global Constraints.
4. Every concrete number — a latency, a register reset value, a sleep-mode current — cites the
   document and section it came from.

Then, once per task:

5. Run `npm run build`. Expected: exit 0.
6. Run the conventions check below, substituting the folder. Fix anything it flags.
7. Commit.

**Conventions check:**

```bash
FOLDER=docs/embedded/05-peripherals-and-drivers
for f in $FOLDER/*.md; do
  for k in id title sidebar_label sidebar_position tags; do
    grep -q "^$k:" "$f" || echo "MISSING $k: $f"
  done
  grep -q "^## See also" "$f" || echo "NO SEE ALSO: $f"
  grep -q "^## References" "$f" || echo "NO REFERENCES: $f"
  grep -q ":::warning" "$f" || echo "NO WARNING: $f"
  grep -qE '^```(mermaid|wavedrom)|<Figure|^\|' "$f" || echo "NO VISUAL ANCHOR: $f"
done
# links into folders that do not exist yet
grep -rnE '\((\.\./)*(08-|10-|1[2-5]-)' $FOLDER/*.md && echo "PHASE 3 LINK FOUND"
```

The last check protects the deploy. It must print nothing.

**Peripheral page shape** (folder 05 only) — every peripheral page follows the same order, per the
spec: what the hardware block does → the bring-up sequence (clock, reset, configure, enable) → the
registers that matter as a WaveDrom `reg` strip plus a semantics table → a worked driver → failure
modes → how to see it on a logic analyzer.

---

### Task 1: Folder 05 — Peripherals, part 1: fundamentals and timers (5 pages)

**Files:**
- Create: `docs/embedded/05-peripherals-and-drivers/_category_.json`
- Create: the first 5 pages of the spec's `05-peripherals-and-drivers` table

**Interfaces:**
- Consumes: `04-bare-metal-programming/gpio-driver-from-scratch.md` and `clock-tree-configuration.md` from Phase 1.
- Produces: `anatomy-of-a-peripheral.md`, whose bring-up sequence every later peripheral page in this folder refers back to instead of repeating.

- [ ] **Step 1: Create the category file**

```json
{
  "label": "Peripherals and Drivers",
  "position": 6,
  "link": {
    "type": "generated-index"
  }
}
```

- [ ] **Step 2: Write the five pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `anatomy-of-a-peripheral.md` | 1 | Mermaid of the universal bring-up sequence; table of the register roles every peripheral has | ST **RM0383**, RCC peripheral clock enable registers |
| `timers-and-counters.md` | 2 | WaveDrom of counter/update-event timing; worked prescaler and ARR arithmetic | ST **RM0383**, general-purpose timers chapter |
| `pwm.md` | 3 | WaveDrom of two duty cycles against the same period | ST **RM0383**, PWM mode section |
| `input-capture-and-encoders.md` | 4 | WaveDrom of quadrature A/B phase relationship | ST **RM0383**, input capture and encoder interface modes |
| `writing-a-portable-driver.md` | 14 | Mermaid of the driver/peripheral/interface layering | Elecia White, *Making Embedded Systems*, driver chapters |

`anatomy-of-a-peripheral.md` must make the point that "the peripheral does nothing" is almost
always a missing clock-enable bit in `RCC_AHB1ENR`/`RCC_APB1ENR`, and that the enable takes effect
after a short delay — reading the register back is the standard guard.

`writing-a-portable-driver.md` is written now, at position 14, because Tasks 2 and 3 apply its
structure. It must not link forward to folder 11's testing pages; describe the testable seam in
prose and let Task 11 add the link.

- [ ] **Step 3: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 4: Run the conventions check** with `FOLDER=docs/embedded/05-peripherals-and-drivers`.
- [ ] **Step 5: Commit**

```bash
git add docs/embedded/05-peripherals-and-drivers
git commit -m "docs: add peripheral fundamentals and timer pages"
```

---

### Task 2: Folder 05 — Peripherals, part 2: serial buses (3 pages)

**Files:**
- Create: `uart-in-depth.md`, `spi-in-depth.md`, `i2c-in-depth.md` in `docs/embedded/05-peripherals-and-drivers/`

**Interfaces:**
- Consumes: `anatomy-of-a-peripheral.md` and `writing-a-portable-driver.md` from Task 1.
- Produces: the bus pages that folder 08 (Phase 3) builds on for CAN, RS-485, and Ethernet.

These three are the densest WaveDrom pages in the whole section, and the ones most exposed to the
no-duplication contract: `computer-science/buses-and-io/serial-buses-i2c-spi-uart.md` **owns** the
protocol basics. Link to it, then write the register-level and failure-mode material it does not
cover.

- [ ] **Step 1: Write the three pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `uart-in-depth.md` | 5 | WaveDrom of a frame showing start bit, data bits, parity, stop bit | ST **RM0383**, USART chapter |
| `spi-in-depth.md` | 6 | WaveDrom for each of the four CPOL/CPHA modes | ST **RM0383**, SPI chapter; Motorola SPI block guide |
| `i2c-in-depth.md` | 7 | WaveDrom of start, address, ACK, data, stop; a second showing clock stretching | NXP **UM10204**, *I2C-bus specification and user manual* |

Required content that generic tutorials omit and that this section exists to provide:

- `uart-in-depth.md` — baud rate error arithmetic and why roughly 2% is the practical ceiling; the
  overrun error nobody handles; DMA reception with idle-line detection as the robust pattern.
- `spi-in-depth.md` — that every read is simultaneously a write; chip-select timing relative to
  clock edges; why the achievable clock is a wiring property, not a datasheet number.
- `i2c-in-depth.md` — the 7-bit address shift confusion (datasheets disagree on whether the
  address is pre-shifted); clock stretching; and **recovering a bus a slave has locked low by
  manually clocking SCL**, which is the fix nobody documents.

Each page links back to `../../computer-science/buses-and-io/serial-buses-i2c-spi-uart.md` for the
protocol comparison rather than restating it.

- [ ] **Step 2: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 3: Run the conventions check.**
- [ ] **Step 4: Verify the WaveDrom budget**

```bash
for f in docs/embedded/05-peripherals-and-drivers/{uart,spi,i2c}-in-depth.md; do
  echo "$f: $(grep -c '^```wavedrom' "$f")"
done
```

Expected: each ≤ 4. The spec caps waveforms at 2–3 per page; the SPI page may reach 4 because the
four CPOL/CPHA modes are the point of the page. If any page exceeds 4, split a diagram out.

- [ ] **Step 5: Commit**

```bash
git add docs/embedded/05-peripherals-and-drivers
git commit -m "docs: add uart, spi and i2c in-depth pages"
```

---

### Task 3: Folder 05 — Peripherals, part 3: data movement and storage (6 pages)

**Files:**
- Create: `adc-and-dac-drivers.md`, `dma.md`, `rtc-and-timekeeping.md`, `watchdogs.md`, `flash-and-eeprom-emulation.md`, `external-memory-and-qspi.md`

**Interfaces:**
- Consumes: Tasks 1–2.
- Produces: `dma.md`, referenced by folder 06's polling-vs-interrupt-vs-DMA decision page and folder 09's sleep pages.

- [ ] **Step 1: Write the six pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `adc-and-dac-drivers.md` | 8 | WaveDrom of sampling time then conversion; table of resolution vs effective bits | ST **RM0383**, ADC chapter; ST application note on ADC accuracy |
| `dma.md` | 9 | WaveDrom showing half-transfer and transfer-complete interrupts against a circular buffer | ST **RM0383**, DMA controller chapter |
| `rtc-and-timekeeping.md` | 10 | Mermaid of the backup domain and its power sources | ST **RM0383**, RTC chapter |
| `watchdogs.md` | 11 | Mermaid of a supervisor pattern where tasks check in | ST **RM0383**, IWDG and WWDG chapters; Jack Ganssle on watchdogs |
| `flash-and-eeprom-emulation.md` | 12 | Mermaid of a power-loss-safe record format | ST **RM0383** flash chapter; ST **AN3969** on EEPROM emulation |
| `external-memory-and-qspi.md` | 13 | Mermaid of memory-mapped XIP versus indirect mode | ST **RM0383**; the QSPI/serial-NOR vendor datasheet cited |

Required content:

- `dma.md` — the half-transfer interrupt as the double-buffer mechanism; and the cache coherency
  problem, stated accurately: **the STM32F411's Cortex-M4 has no data cache, so this bites on M7
  parts, not on this board.** Say that explicitly rather than implying the reader's board has the
  problem.
- `watchdogs.md` — why kicking from a timer ISR defeats the purpose; the supervisor pattern; and
  reading the reset reason from `RCC_CSR` after the fact.
- `flash-and-eeprom-emulation.md` — links to `../../computer-science/storage/ssd-and-nand-flash.md`
  for the physics rather than re-explaining it.

- [ ] **Step 2: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 3: Run the conventions check.** All 14 pages in folder 05 must pass.
- [ ] **Step 4: Confirm the folder is complete**

```bash
ls docs/embedded/05-peripherals-and-drivers/*.md | wc -l
```

Expected: `14`.

- [ ] **Step 5: Commit**

```bash
git add docs/embedded/05-peripherals-and-drivers
git commit -m "docs: add adc, dma, watchdog and flash pages"
```

---

### Task 4: Folder 06 — Real-Time, part 1: interrupts (5 pages)

**Files:**
- Create: `docs/embedded/06-interrupts-timing-and-real-time/_category_.json`
- Create: `interrupt-latency.md`, `interrupt-priorities-and-nesting.md`, `polling-interrupt-or-dma.md`, `deferred-work.md`, `shared-data-and-race-conditions.md`

**Interfaces:**
- Consumes: `02-processor-architecture/the-nvic.md` and `04-bare-metal-programming/{interrupt-handlers-in-c,critical-sections-and-atomicity}.md` from Phase 1; `05-peripherals-and-drivers/dma.md` from Task 3.
- Produces: `deferred-work.md`'s ring-buffer pattern, reused by folder 07's ISR-safe API page.

- [ ] **Step 1: Create the category file**

```json
{
  "label": "Interrupts, Timing and Real-Time",
  "position": 7,
  "link": {
    "type": "generated-index"
  }
}
```

- [ ] **Step 2: Write the five pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `interrupt-latency.md` | 1 | WaveDrom timeline decomposing latency into its contributors | ST **PM0214**, exception entry timing; Arm *Armv7-M ARM* |
| `interrupt-priorities-and-nesting.md` | 2 | Mermaid or WaveDrom of a higher-priority interrupt preempting a handler | ST **PM0214**, NVIC priority registers |
| `polling-interrupt-or-dma.md` | 3 | Decision table across data rate, latency, CPU cost, complexity | ST **RM0383** DMA chapter; measured figures from the board |
| `deferred-work.md` | 4 | Mermaid of the ISR-to-main handoff through a ring buffer | Memfault Interrupt blog on ISR design |
| `shared-data-and-race-conditions.md` | 5 | `<Tabs>` showing C source beside the `armasm` that makes the race visible | ISO C standard on `sig_atomic_t`; Arm *Armv7-M ARM* on exclusive access |

Required content:

- `interrupt-latency.md` — enumerate every contributor: instruction completion, stacking, vector
  fetch, **flash wait states**, higher-priority preemption, and the reader's own critical sections.
  Then show the GPIO-toggle-and-scope measurement. Note that tail-chaining removes the
  unstack/restack between back-to-back exceptions, and cite PM0214 for the cycle counts rather than
  asserting a number.
- `shared-data-and-race-conditions.md` — links to
  `../../computer-science/operating-systems/concurrency-and-synchronization.md` for the general
  theory, then shows the specific ISR-versus-`main` failure at instruction level, why `volatile` is
  not enough, and a correct single-producer/single-consumer ring buffer.

- [ ] **Step 3: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 4: Run the conventions check** with `FOLDER=docs/embedded/06-interrupts-timing-and-real-time`.
- [ ] **Step 5: Commit**

```bash
git add docs/embedded/06-interrupts-timing-and-real-time
git commit -m "docs: add interrupt latency and deferred work pages"
```

---

### Task 5: Folder 06 — Real-Time, part 2: timing analysis (4 pages)

**Files:**
- Create: `real-time-definitions.md`, `scheduling-theory.md`, `wcet.md`, `determinism-killers.md`

**Interfaces:**
- Consumes: Task 4's pages.
- Produces: `scheduling-theory.md` and `wcet.md`, which folder 07's task-design pages assume.

- [ ] **Step 1: Write the four pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `real-time-definitions.md` | 6 | Table of hard/firm/soft against consequence-of-miss, with real examples | Liu and Layland, *Scheduling Algorithms for Multiprogramming in a Hard-Real-Time Environment* (JACM 1973) |
| `scheduling-theory.md` | 7 | Worked task-set table with utilisation computed | Liu and Layland (1973); links to `../../computer-science/operating-systems/scheduling.md` |
| `wcet.md` | 8 | Mermaid or table contrasting measurement-based and static analysis | Wilhelm et al., *The Worst-Case Execution-Time Problem* (ACM TECS 2008) |
| `determinism-killers.md` | 9 | Table of each mechanism against its effect on the worst case | ST **PM0214**; ST **RM0383** flash ART accelerator section |

Required content:

- `scheduling-theory.md` — state the rate-monotonic utilisation bound as `n(2^(1/n) − 1)`,
  converging to about 0.693, and work a concrete three-task example through it. Be explicit that
  the bound is *sufficient, not necessary* — exceeding it does not prove the set is unschedulable,
  which is the misreading most write-ups invite. Link to the CS scheduling page for the general
  theory per the no-duplication table.
- `determinism-killers.md` — cover the flash ART accelerator and wait states on this specific part,
  and be accurate that the STM32F411's Cortex-M4 has **no data or instruction cache** in the M7
  sense; the variability here comes from flash latency and the ART, not from a cache.

- [ ] **Step 2: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 3: Run the conventions check.** All 9 pages must pass.
- [ ] **Step 4: Commit**

```bash
git add docs/embedded/06-interrupts-timing-and-real-time
git commit -m "docs: add real-time definitions, scheduling theory and wcet pages"
```

---

### Task 6: Folder 07 — RTOS, part 1: model and mechanics (5 pages)

**Files:**
- Create: `docs/embedded/07-rtos/_category_.json`
- Create: `why-an-rtos.md`, `the-rtos-landscape.md`, `tasks-and-scheduling.md`, `context-switching.md`, `stacks-and-heaps-in-an-rtos.md`

**Interfaces:**
- Consumes: `04-bare-metal-programming/the-superloop.md` and `stack-usage-and-overflow.md`; `02-processor-architecture/{privilege-modes-and-stacks,exceptions-and-the-vector-table}.md`; folder 06's scheduling theory.
- Produces: the task/scheduler vocabulary every later page in folder 07 uses.

**Before writing: verify FreeRTOS specifics via context7** (kernel version, API names). Record the check date in the `## References` annotations. FreeRTOS is the worked example throughout folder 07 because it is small enough to read; Zephyr gets its own page in Task 8.

- [ ] **Step 1: Create the category file**

```json
{
  "label": "Real-Time Operating Systems",
  "position": 8,
  "link": {
    "type": "generated-index"
  }
}
```

- [ ] **Step 2: Write the five pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `why-an-rtos.md` | 1 | Table of superloop failure symptoms against what an RTOS changes | *Mastering the FreeRTOS Real Time Kernel* (free official guide, freertos.org) |
| `the-rtos-landscape.md` | 2 | Table comparing FreeRTOS, Zephyr, ThreadX, RT-Thread, NuttX, RTEMS on licence, footprint, certification, ecosystem | Each project's own documentation site |
| `tasks-and-scheduling.md` | 3 | Mermaid state diagram: Running, Ready, Blocked, Suspended | freertos.org task documentation |
| `context-switching.md` | 4 | Mermaid or annotated `armasm` of the PendSV handler; diagram of the stacked frame | ST **PM0214**, PendSV and exception stacking; FreeRTOS `port.c` for Cortex-M4F |
| `stacks-and-heaps-in-an-rtos.md` | 5 | Table of `heap_1` … `heap_5` against determinism, fragmentation, and free support | freertos.org memory management documentation |

Required content:

- `context-switching.md` is the page that justifies the folder. It must explain **why PendSV is set
  to the lowest priority** — so the switch happens after all pending interrupts, never preempting a
  handler — and distinguish the hardware-stacked frame (R0–R3, R12, LR, PC, xPSR) from the
  software-stacked registers (R4–R11) the port pushes. Cover FPU context on this M4F part.
- `stacks-and-heaps-in-an-rtos.md` must connect to Phase 1's stack-overflow page and cover
  high-water-mark measurement, plus fully static allocation for a no-heap build.

- [ ] **Step 3: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 4: Run the conventions check** with `FOLDER=docs/embedded/07-rtos`.
- [ ] **Step 5: Commit**

```bash
git add docs/embedded/07-rtos
git commit -m "docs: add rtos model, scheduling and context switching pages"
```

---

### Task 7: Folder 07 — RTOS, part 2: communication and hazards (5 pages)

**Files:**
- Create: `synchronization-primitives.md`, `queues-and-message-passing.md`, `notifications-and-event-groups.md`, `software-timers-and-delays.md`, `priority-inversion-and-deadlock.md`

**Interfaces:**
- Consumes: Task 6's pages.
- Produces: the primitives vocabulary Task 8's ISR-safe API page uses.

- [ ] **Step 1: Write the five pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `synchronization-primitives.md` | 6 | Table of binary semaphore vs counting semaphore vs mutex against ownership, priority inheritance, ISR use | freertos.org semaphore and mutex documentation |
| `queues-and-message-passing.md` | 7 | Mermaid of a producer/consumer design; table of copy vs pointer semantics | freertos.org queue documentation |
| `notifications-and-event-groups.md` | 8 | Table comparing notification, queue, semaphore, and event group on RAM and speed | freertos.org task notification documentation |
| `software-timers-and-delays.md` | 9 | WaveDrom or Mermaid contrasting `vTaskDelay` drift with `vTaskDelayUntil` | freertos.org software timer documentation |
| `priority-inversion-and-deadlock.md` | 10 | Mermaid timeline of unbounded priority inversion, then the same with inheritance | Glenn Reeves, *What Really Happened on Mars* (the Mars Pathfinder account) |

Required content:

- `synchronization-primitives.md` — the distinction that matters: a mutex has an owner and supports
  priority inheritance; a binary semaphore does not and must be used for signalling, not mutual
  exclusion. Links to `../../computer-science/operating-systems/concurrency-and-synchronization.md`
  for the general theory per the no-duplication table.
- `software-timers-and-delays.md` — `vTaskDelay` schedules relative to *now*, so any preemption
  accumulates drift; `vTaskDelayUntil` schedules relative to the previous wake and does not. Also:
  never use a task delay for a hardware timing requirement.
- `priority-inversion-and-deadlock.md` — tell the Pathfinder story properly (a mutex without
  priority inheritance, a watchdog reset loop, fixed by enabling inheritance in flight), then the
  four Coffman conditions applied to firmware, with lock ordering as the practical rule.

- [ ] **Step 2: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 3: Run the conventions check.**
- [ ] **Step 4: Commit**

```bash
git add docs/embedded/07-rtos
git commit -m "docs: add rtos synchronization, queues and priority inversion pages"
```

---

### Task 8: Folder 07 — RTOS, part 3: integration (3 pages)

**Files:**
- Create: `isr-safe-apis.md`, `zephyr-in-practice.md`, `rtos-debugging-and-tracing.md`

**Interfaces:**
- Consumes: Tasks 6–7; folder 06's `deferred-work.md`.
- Produces: the complete folder 07.

**Before writing `zephyr-in-practice.md`: verify Zephyr's devicetree, Kconfig, and `west` workflow via context7.** Zephyr's tooling changes faster than any other subject in this section; record the check date.

- [ ] **Step 1: Write the three pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `isr-safe-apis.md` | 11 | Mermaid or WaveDrom of the yield-from-ISR sequence | freertos.org ISR-safe API documentation; ST **PM0214** on BASEPRI |
| `zephyr-in-practice.md` | 12 | `<Tabs>` comparing a FreeRTOS task with a Zephyr thread; Mermaid of devicetree → driver binding | docs.zephyrproject.org (devicetree, Kconfig, `west`, device driver model) |
| `rtos-debugging-and-tracing.md` | 13 | `<Figure>` of a trace view if properly sourced, else Mermaid of the trace pipeline | SEGGER SystemView documentation; Percepio Tracealyzer documentation |

Required content:

- `isr-safe-apis.md` must get the priority ceiling right: FreeRTOS on Cortex-M uses BASEPRI, and
  **only interrupts at or below `configMAX_SYSCALL_INTERRUPT_PRIORITY` may call `FromISR` APIs.**
  A higher-priority interrupt calling one is the classic cause of a hard fault that appears
  unrelated to the call. Also note that Cortex-M priority numbers are inverted — numerically lower
  means higher priority — which is where most of the confusion originates.
- `rtos-debugging-and-tracing.md` describes the tools but must **not** link to folder 11 yet;
  Task 11 adds that link.

- [ ] **Step 2: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 3: Run the conventions check.** All 13 pages must pass.
- [ ] **Step 4: Confirm the folder is complete**

```bash
ls docs/embedded/07-rtos/*.md | wc -l
```

Expected: `13`.

- [ ] **Step 5: Commit**

```bash
git add docs/embedded/07-rtos
git commit -m "docs: add isr-safe apis, zephyr and rtos tracing pages"
```

---

### Task 9: Folder 09 — Low-Power Design, part 1 (4 pages)

**Files:**
- Create: `docs/embedded/09-low-power-design/_category_.json`
- Create: `energy-budgets.md`, `sleep-modes.md`, `clock-and-peripheral-gating.md`, `wake-sources-and-event-driven-design.md`

**Interfaces:**
- Consumes: `05-peripherals-and-drivers/{dma,rtc-and-timekeeping}.md`; `04-bare-metal-programming/clock-tree-configuration.md`.
- Produces: `wake-sources-and-event-driven-design.md`, referenced by Task 10's tickless-idle page.

Folder 09 is numbered to leave a gap: `08-connectivity-and-protocols` belongs to Phase 3. Creating
`09-` without `08-` is fine — Docusaurus orders by the `position` field in `_category_.json`, and a
gap in the sequence is not an error.

- [ ] **Step 1: Create the category file**

```json
{
  "label": "Low-Power Design",
  "position": 10,
  "link": {
    "type": "generated-index"
  }
}
```

- [ ] **Step 2: Write the four pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `energy-budgets.md` | 1 | Worked table converting a battery capacity and duty cycle into a lifetime | Battery manufacturer datasheet for a named cell (e.g. a CR2032 or 18650) |
| `sleep-modes.md` | 2 | Table of Sleep, Stop, and Standby against current, wake latency, and retained state | ST **RM0383**, power control (PWR) chapter; STM32F411RE datasheet current-consumption tables |
| `clock-and-peripheral-gating.md` | 3 | Table of run-fast-then-sleep versus run-slow with the arithmetic | ST **RM0383**, RCC and PWR chapters |
| `wake-sources-and-event-driven-design.md` | 4 | WaveDrom of a wake-process-sleep cycle with current annotated | ST **RM0383**, EXTI and PWR wake-up sources |

`sleep-modes.md` must use the STM32F411RE's actual mode names and figures from its datasheet
tables, with the measurement conditions stated (they vary by voltage, temperature, and which
regulator is active — a bare microamp number without conditions is misleading).

`wake-sources-and-event-driven-design.md` carries the architectural argument that matters more than
any register setting: restructure so the default state is asleep. Cover DMA continuing while the
core sleeps, and hardware threshold detection that avoids waking at all.

- [ ] **Step 3: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 4: Run the conventions check** with `FOLDER=docs/embedded/09-low-power-design`.
- [ ] **Step 5: Commit**

```bash
git add docs/embedded/09-low-power-design
git commit -m "docs: add energy budget and sleep mode pages"
```

---

### Task 10: Folder 09 — Low-Power Design, part 2 (3 pages)

**Files:**
- Create: `tickless-idle.md`, `measuring-power.md`, `brownout-and-power-loss-safety.md`

**Interfaces:**
- Consumes: Task 9's pages; `07-rtos/tasks-and-scheduling.md`; `05-peripherals-and-drivers/flash-and-eeprom-emulation.md`.
- Produces: the complete folder 09.

- [ ] **Step 1: Write the three pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `tickless-idle.md` | 5 | WaveDrom contrasting a periodic tick with suppressed ticks | freertos.org low-power tickless idle documentation |
| `measuring-power.md` | 6 | `<Figure>` of a current trace if properly sourced, else a table of method against measurable range | Nordic Power Profiler Kit documentation; Joulescope or equivalent instrument documentation |
| `brownout-and-power-loss-safety.md` | 7 | Mermaid of the write sequence that survives interruption at any point | ST **RM0383**, brownout reset (BOR) section |

`tickless-idle.md` must explain the correctness requirement, not just the setting: on wake the
kernel has to *correct* the tick count for the time it slept, and the accuracy of that correction
bounds how long you can sleep. Links back to `07-rtos/software-timers-and-delays.md`.

`brownout-and-power-loss-safety.md` must be concrete about how much work the decoupling capacitors
actually fund — order of magnitude, with the reasoning — rather than implying a graceful shutdown
is always possible.

- [ ] **Step 2: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 3: Run the conventions check.** All 7 pages must pass.
- [ ] **Step 4: Commit**

```bash
git add docs/embedded/09-low-power-design
git commit -m "docs: add tickless idle, power measurement and brownout pages"
```

---

### Task 11: Folder 11 — Debugging and Testing, part 1: on-target debugging (6 pages)

**Files:**
- Create: `docs/embedded/11-debugging-and-testing/_category_.json`
- Create: `the-debug-toolbox.md`, `swd-jtag-and-gdb.md`, `printf-debugging-done-right.md`, `hardfault-debugging.md`, `postmortem-and-crash-dumps.md`, `logic-analyzer-workflows.md`

**Interfaces:**
- Consumes: `02-processor-architecture/{cortex-m-register-model,systick-and-core-peripherals}.md`; `03-toolchain-and-build/{elf-map-files-and-size,flashing-and-programming}.md`; `01-hardware-foundations/lab-equipment.md`.
- Produces: `hardfault-debugging.md`, the page Task 13 links back to from folders 04 and 07.

`hardfault-debugging.md` is the highest-value page in Phase 2 and the one most often written
wrongly. Get the register names and the stack-recovery procedure from PM0214, not from memory.

- [ ] **Step 1: Create the category file**

```json
{
  "label": "Debugging and Testing",
  "position": 12,
  "link": {
    "type": "generated-index"
  }
}
```

- [ ] **Step 2: Write the six pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `the-debug-toolbox.md` | 1 | Decision table mapping symptom to instrument | — (links; the page is the index for the folder) |
| `swd-jtag-and-gdb.md` | 2 | Mermaid of host → OpenOCD → probe → target; table of GDB commands worth knowing | OpenOCD user guide; GDB documentation |
| `printf-debugging-done-right.md` | 3 | Table comparing semihosting, SWO/ITM, RTT, and a DMA ring buffer on cost and intrusiveness | SEGGER RTT documentation; ST **PM0214** ITM chapter |
| `hardfault-debugging.md` | 4 | WaveDrom `reg` of CFSR with its sub-registers; Mermaid of the diagnosis procedure | ST **PM0214**, fault reporting registers; Memfault Interrupt blog series on debugging HardFaults |
| `postmortem-and-crash-dumps.md` | 5 | Mermaid of capture-to-upload flow | Memfault documentation on coredumps; ST **RM0383** `RCC_CSR` reset flags |
| `logic-analyzer-workflows.md` | 6 | `<Figure>` of a real decoded capture if properly sourced, else WaveDrom of the expected versus observed signal | sigrok/PulseView documentation; Saleae documentation |

`hardfault-debugging.md` must give a procedure a reader can follow under pressure:

1. Read `CFSR` (`UsageFault`, `BusFault`, `MemManage` sub-registers) and `HFSR`.
2. If the address is valid, read `BFAR` or `MMFAR`.
3. Determine from `EXC_RETURN` in LR whether the frame is on MSP or PSP.
4. Recover the stacked PC from that frame.
5. Map the PC to a source line via the `.map` file or `arm-none-eabi-addr2line`.

Include a fault handler worth shipping. Link to
`../02-processor-architecture/cortex-m-register-model.md` for `EXC_RETURN` and to
`../../computer-science/assembly/reading-disassembly.md` per the no-duplication table.

`printf-debugging-done-right.md` must lead with why blocking `printf` over UART changes the bug
being investigated — a timing-dependent fault often disappears when you add logging, and that is
the observation the page exists to explain.

- [ ] **Step 3: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 4: Run the conventions check** with `FOLDER=docs/embedded/11-debugging-and-testing`.
- [ ] **Step 5: Commit**

```bash
git add docs/embedded/11-debugging-and-testing
git commit -m "docs: add on-target debugging and hardfault forensics pages"
```

---

### Task 12: Folder 11 — Debugging and Testing, part 2: instrumentation and tests (6 pages)

**Files:**
- Create: `oscilloscope-for-firmware-engineers.md`, `tracing.md`, `unit-testing-firmware.md`, `mocking-hardware.md`, `static-analysis-and-sanitizers.md`, `simulation-and-emulation.md`

**Interfaces:**
- Consumes: Task 11's pages; `05-peripherals-and-drivers/writing-a-portable-driver.md`.
- Produces: the complete folder 11 and therefore all of Phase 2's content.

- [ ] **Step 1: Write the six pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `oscilloscope-for-firmware-engineers.md` | 7 | Table of symptom against what only a scope reveals | Tektronix or Keysight oscilloscope primer (vendor educational material) |
| `tracing.md` | 8 | Mermaid of DWT/ITM/ETM data paths off the chip | ST **PM0214**, DWT and ITM; Arm CoreSight documentation |
| `unit-testing-firmware.md` | 9 | Mermaid of the host-test build versus the target build sharing logic | Unity/Ceedling documentation (throwtheswitch.org); CppUTest documentation |
| `mocking-hardware.md` | 10 | `<Tabs>` showing a driver against real registers and against a fake | James Grenning, *Test-Driven Development for Embedded C* |
| `static-analysis-and-sanitizers.md` | 11 | Table of tool against defect class caught | GCC warning options documentation; cppcheck manual; clang-tidy documentation |
| `simulation-and-emulation.md` | 12 | Table comparing QEMU and Renode on fidelity and setup cost | QEMU documentation; Renode documentation (renode.readthedocs.io) |

Required content:

- `unit-testing-firmware.md` must be honest about the limit: a host test proves your logic, not
  your understanding of the hardware. Say so, and pair it with the hardware checks from Task 11.
- `mocking-hardware.md` must show the seam concretely — a driver taking a register-access interface
  rather than dereferencing a fixed address — and connect to
  `../05-peripherals-and-drivers/writing-a-portable-driver.md`, which set that structure up.
- `static-analysis-and-sanitizers.md` should note that compiler warnings are the cheapest analysis
  available and most projects leave them off; recommend a concrete flag set.

- [ ] **Step 2: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 3: Run the conventions check.** All 12 pages must pass.
- [ ] **Step 4: Commit**

```bash
git add docs/embedded/11-debugging-and-testing
git commit -m "docs: add tracing, unit testing and simulation pages"
```

---

### Task 13: Phase 2 completion sweep

**Files:**
- Modify: `docs/embedded/readme.md`
- Modify: the specific pages listed in Step 2

**Interfaces:**
- Consumes: all 55 pages from Tasks 1–12.
- Produces: a Phase 2 section with its deferred cross-links resolved, ready for Phase 3.

- [ ] **Step 1: Update the learning paths in `readme.md`**

Phase 1 left steps that land in folders 05–11 as prose. Link them now:

- **I have a board and nothing works** — the folder 11 step becomes a link to
  `11-debugging-and-testing/the-debug-toolbox.md`.
- **I'm building a product** — the 05, 07, and 09 steps become links to
  `05-peripherals-and-drivers/anatomy-of-a-peripheral.md`, `07-rtos/why-an-rtos.md`, and
  `09-low-power-design/energy-budgets.md`. The folder 14 step stays prose until Phase 3.
- **I'm moving to Linux** — the folder 11 step becomes a link; the folder 10 step stays prose.

Update the "still being written" note to say folders 08, 10, and 12–15 remain.

- [ ] **Step 2: Add the deferred backlinks**

These pages were written before their targets existed. Add one link each, in `## See also`:

| Page to modify | Link to add |
|---|---|
| `05-peripherals-and-drivers/writing-a-portable-driver.md` | `../11-debugging-and-testing/mocking-hardware.md` |
| `05-peripherals-and-drivers/uart-in-depth.md` | `../11-debugging-and-testing/logic-analyzer-workflows.md` |
| `05-peripherals-and-drivers/spi-in-depth.md` | `../11-debugging-and-testing/logic-analyzer-workflows.md` |
| `05-peripherals-and-drivers/i2c-in-depth.md` | `../11-debugging-and-testing/logic-analyzer-workflows.md` |
| `06-interrupts-timing-and-real-time/interrupt-latency.md` | `../11-debugging-and-testing/tracing.md` |
| `07-rtos/rtos-debugging-and-tracing.md` | `../11-debugging-and-testing/tracing.md` |
| `09-low-power-design/measuring-power.md` | `../11-debugging-and-testing/oscilloscope-for-firmware-engineers.md` |
| `04-bare-metal-programming/stack-usage-and-overflow.md` | `../11-debugging-and-testing/hardfault-debugging.md` |
| `04-bare-metal-programming/critical-sections-and-atomicity.md` | `../11-debugging-and-testing/hardfault-debugging.md` |

Keep each `## See also` at 3–5 bullets; if a list would exceed five, drop the weakest existing
bullet rather than growing the list.

- [ ] **Step 3: Verify the whole section against every convention**

```bash
for FOLDER in docs/embedded/0* docs/embedded/1*; do
  [ -d "$FOLDER" ] || continue
  for f in $FOLDER/*.md; do
    for k in id title sidebar_label sidebar_position tags; do
      grep -q "^$k:" "$f" || echo "MISSING $k: $f"
    done
    grep -q "^## See also" "$f" || echo "NO SEE ALSO: $f"
    grep -q "^## References" "$f" || echo "NO REFERENCES: $f"
    grep -q ":::warning" "$f" || echo "NO WARNING: $f"
    grep -qE '^```(mermaid|wavedrom)|<Figure|^\|' "$f" || echo "NO VISUAL ANCHOR: $f"
  done
done
grep -rnE '\((\.\./)*(08-|10-|1[2-5]-)' docs/embedded/ && echo "PHASE 3 LINK FOUND"
```

Expected: no output at all.

- [ ] **Step 4: Confirm the page count**

```bash
find docs/embedded -name '*.md' -not -name 'readme.md' | wc -l
```

Expected: `106` (51 from Phase 1 + 55 from this phase).

- [ ] **Step 5: Verify every image is sourced**

```bash
find static/img/embedded -type f -not -name SOURCES.md | while read -r img; do
  grep -q "$(basename "$img")" static/img/embedded/SOURCES.md || echo "UNSOURCED: $img"
done
du -sh static/img/embedded
```

Expected: no `UNSOURCED` lines; total size well under the ~1.2 MB of `static/img/gpu/`.

- [ ] **Step 6: Full verification**

```bash
npm run build
npm run typecheck
npm run test:plugins
npx biome check docs/embedded
```

Expected: build exit 0, typecheck clean, 8 tests passing, Biome clean on `docs/embedded`.
Repo-wide `npm run lint` still fails on 157 pre-existing errors in unrelated files — the documented
baseline, not a regression.

- [ ] **Step 7: Visual spot-check**

Run `npm run serve`. Confirm the sidebar shows ten folders in the right order (with the gap where
08 will go), that the SPI mode waveforms render correctly in both light and dark theme, and that
the four learning paths work. Stop the server.

- [ ] **Step 8: Commit**

```bash
git add docs/embedded
git commit -m "docs: link phase 2 learning paths and cross-references"
```

---

## Assumptions most likely to need revising after Phase 1

This plan was written before Phase 1 was executed. Re-check these before starting:

1. **WaveDrom density.** Tasks 2 and 4 lean heavily on waveforms. If Phase 1 found the rendered
   diagrams awkward at mobile width or visually heavy on the light plate, reduce the counts here.
2. **The `<Figure>` sourcing rate.** If Phase 1 found almost no cleanly-licensed embedded figures,
   drop the `<Figure>` suggestions in Tasks 11–12 to Mermaid without treating it as a loss.
3. **Task size.** Phase 1's tasks were 5–6 pages. If that proved too large in one session, split
   Tasks 3, 11, and 12 (six pages each) before starting.
4. **The board.** If the NUCLEO-F411RE was swapped during Phase 1, every RM0383 citation in this
   plan changes with it.
