# Embedded Systems Docs — Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the section with the 68 pages that cover shipping a real product: connectivity and industrial protocols, embedded Linux, functional safety, security, the firmware lifecycle, and languages beyond C.

**Architecture:** Pure content on top of Phase 1's infrastructure. No new dependencies, no new components, no config changes. Six folders (08, 10, 12, 13, 14, 15) of plain Markdown. On completion the section is 174 topic pages plus `readme.md`, matching the spec exactly.

**Tech Stack:** Docusaurus 3.10.2 Markdown; the `remark-wavedrom` plugin and `WaveDrom`/`Tabs` MDX components from Phase 1. Subject matter: CAN/Modbus/BLE/Ethernet, the Linux kernel and Yocto, IEC 61508 and its derivatives, Arm TrustZone-M and PSA, MCUboot and OTA, embedded C++ and Rust.

**Spec:** `docs/superpowers/specs/2026-08-18-embedded-systems-docs-design.md` — read it before starting. This plan implements Phase 3 of three. The spec's page-by-page outline is the source of truth for every page's title and content brief; this plan does not repeat those briefs.

**Prerequisite:** Phases 1 and 2 complete and merged. Verify before starting:

```bash
find docs/embedded -name '*.md' -not -name 'readme.md' | wc -l   # expect 106
npm run build                                                    # expect exit 0
```

## Global Constraints

Copied from the spec and from the Phase 1 plan's verified baseline. Every task's requirements implicitly include this section.

- **Folders added in this phase:** `08-connectivity-and-protocols` (12 pages), `10-embedded-linux` (14), `12-safety-and-reliability` (12), `13-security` (10), `14-firmware-lifecycle` (9), `15-languages-and-practice` (11). These are the last six; nothing is deferred past this phase.
- **`_category_.json`:** 2-space indent, keys `label`, `position`, `link.type = "generated-index"`. `position` = numeric folder prefix + 1 (so `08-` is position 9, `15-` is position 16).
- **Frontmatter:** every page has `id`, `title`, `sidebar_label`, `sidebar_position`, `tags`. `tags` starts with `embedded`. Folder 10 pages add `linux`; folder 12 adds `safety`; folder 13 adds `security`; folder 15 Rust pages add `rust`. `sidebar_position` starts at 1 within each folder.
- **Page shape:** mental model before mechanism → optional `:::info[Prerequisites]` → body → **at least one visual anchor** → at least one `:::warning` naming a real day-costing mistake → `## See also` (3–5 relative links) → `## References` (2–6 annotated external sources, primary first; no bare URLs).
- **Admonitions:** only `:::info`, `:::note`, `:::tip`, `:::warning`.
- **Code fences:** `c`, `cpp`, `rust`, `armasm`, `bash`, `cmake`, `makefile`, `ini`, `json`, `toml`, `diff`, `python`. **Device tree, Kconfig, and linker scripts use ` ```text `** — there is no Prism grammar for them, and ` ```c ` mis-highlights device tree. Folder 10 uses ` ```text ` heavily for exactly this reason.
- **WaveDrom:** at most 2–3 waveforms per page; ≤ 8 signals each; every bit-field strip paired with a semantics table. Folders 12–15 will use few or none — that is expected, and a comparison table is a valid visual anchor.
- **Images:** `static/img/embedded/<folder-slug>/<name>.png` via `<Figure src="/img/embedded/..." />` — no `/knowledge-base` prefix. Every image needs a row in `static/img/embedded/SOURCES.md` **in the same commit**. Source order: **Bootlin (CC BY-SA) → Wikimedia Commons → vendor primary docs → own photographs.** Folder 10 is where Bootlin matters most: their embedded Linux and kernel training slides are CC BY-SA and are the best license-clean figure source in the whole section. Attribute the licence in the caption.
- **Link rule:** by the end of this phase all folders exist, so any internal link is legal — but within a task, a page may only link to folders already written. Folders are written in numeric order; deferred links are resolved in Task 14, which lists them explicitly.
- **No-duplication contract:** the spec's normative table is binding. Folder 08 must not re-explain OSI layering, TCP, UDP, or TLS — `computer-science/computer-networks/*` and `computer-science/protocols/tls-and-encryption-basics.md` own those. Folder 10 must not re-explain virtual memory, processes, or IPC — `computer-science/memory-hierarchy/virtual-memory-and-paging.md` and `computer-science/operating-systems/*` own those. Folder 15 must not re-explain C++ language features — `programming/cpp/**` owns those. Link, then write only what is additional.
- **Lint gate:** `npm run lint` repo-wide **already fails** with 157 pre-existing errors in unrelated files. Do not fix them, do not gate on them. Gate on `npx biome check docs/embedded`.
- **Commits:** per CLAUDE.md — `<type>: <what>` on one line, no body unless needed, **never** a `Co-Authored-By` trailer or a "Generated with Claude Code" line.

### Hardware target

Unchanged: **NUCLEO-F411RE** (STM32F411RE, Cortex-M4F). ST **RM0383**, ST **PM0214**, ST **UM1724**.

**Two places the reference board does not apply, and pages must say so plainly:**

- **Folder 10 (embedded Linux)** needs an MMU and therefore a Cortex-A class part. Pages should be written against a generic ARM Linux target and name a concrete example board where one helps (a Raspberry Pi or BeagleBone is the widely-available choice). Do not imply the F411 can run Linux.
- **`13-security/trustzone-for-cortex-m.md`** describes an **Armv8-M** feature (Cortex-M23/M33/M55). The Cortex-M4 on the reference board **does not have TrustZone**. State this in the page rather than leaving a reader trying to enable it on their board.

### Content currency

The spec requires context7 verification for folders 10, 13, and 15. Do this immediately before writing the affected pages and record the check date in their `## References` annotations:

| Folder | Verify via context7 |
|---|---|
| 10 | Linux kernel driver APIs, U-Boot, current Yocto release names |
| 13 | Mbed TLS / PSA Crypto API, TrustZone-M tooling |
| 15 | `embedded-hal` 1.0 traits, RTIC 2.x, Embassy |

**`embedded-hal` reached 1.0 and its trait set changed from the 0.2 series that most tutorials still show.** Folder 15 must document the 1.0 traits. This is the single most likely place for this section to ship outdated content.

### Safety-standard accuracy guardrail (folder 12)

IEC 61508, ISO 26262, DO-178C, and IEC 62304 are **paywalled documents**. Every page in folder 12 explains the standard's structure, intent, and day-to-day engineering consequences, cites parts and clause numbers so a reader with access can navigate, and states that the standard is a purchase. Pages must **not** purport to reproduce normative text, and must not be written so a reader could mistake the page for the standard. **Every page in folder 12 carries a `:::note` saying this.** Task 6 Step 2 defines the wording once so it is consistent across all twelve pages.

### Recommended model per task

| Tasks | Model | Why |
|---|---|---|
| 1–5 (connectivity, Linux) | Opus 5 | Protocol mechanics and kernel APIs where wrong detail is invisible to a beginner |
| 6–7 (safety) | Opus 5 | Content about paywalled standards; accuracy and the guardrail both matter |
| 8–9 (security) | Opus 5 | Security advice that is subtly wrong is worse than none |
| 10–11 (lifecycle) | Sonnet 5 acceptable | Process and practice; claims are checkable |
| 12–13 (languages) | Opus 5 | Rust ecosystem detail moves fast and `embedded-hal` 1.0 is easy to get wrong |
| 14 (final sweep) | Opus 5 | Whole-section consistency across 174 pages |

---

## File Structure

No source files change. This phase creates only content:

| Path | Contents |
|---|---|
| `docs/embedded/08-connectivity-and-protocols/` | `_category_.json` + 12 pages |
| `docs/embedded/10-embedded-linux/` | `_category_.json` + 14 pages |
| `docs/embedded/12-safety-and-reliability/` | `_category_.json` + 12 pages |
| `docs/embedded/13-security/` | `_category_.json` + 10 pages |
| `docs/embedded/14-firmware-lifecycle/` | `_category_.json` + 9 pages |
| `docs/embedded/15-languages-and-practice/` | `_category_.json` + 11 pages |
| `static/img/embedded/SOURCES.md` | Appended rows for any figures added |
| `docs/embedded/readme.md` | Modified once, in Task 14 |

---

## Content task recipe

Every task below writes Markdown. There is no TDD cycle for prose; the loop is **write the page →
build → check conventions → commit**. `onBrokenLinks: "throw"` turns a mistyped relative link into
a deploy failure.

For each page:

1. Read that page's row in the spec's "Page-by-page outline" — that brief is the requirement.
2. Check the spec's no-duplication table and link rather than re-explain.
3. Write the page to the shape in Global Constraints.
4. Every concrete number cites the document and section it came from.

Then, once per task:

5. Run `npm run build`. Expected: exit 0.
6. Run the conventions check, substituting the folder. Fix anything flagged.
7. Commit.

**Conventions check:**

```bash
FOLDER=docs/embedded/08-connectivity-and-protocols
for f in $FOLDER/*.md; do
  for k in id title sidebar_label sidebar_position tags; do
    grep -q "^$k:" "$f" || echo "MISSING $k: $f"
  done
  grep -q "^## See also" "$f" || echo "NO SEE ALSO: $f"
  grep -q "^## References" "$f" || echo "NO REFERENCES: $f"
  grep -q ":::warning" "$f" || echo "NO WARNING: $f"
  grep -qE '^```(mermaid|wavedrom)|<Figure|^\|' "$f" || echo "NO VISUAL ANCHOR: $f"
done
```

---

### Task 1: Folder 08 — Connectivity, part 1: wired and industrial (6 pages)

**Files:**
- Create: `docs/embedded/08-connectivity-and-protocols/_category_.json`
- Create: `choosing-a-bus-or-link.md`, `can-and-can-fd.md`, `canopen-and-j1939.md`, `modbus.md`, `rs485-and-industrial-serial.md`, `ethernet-on-mcu.md`

**Interfaces:**
- Consumes: `05-peripherals-and-drivers/{uart,spi,i2c}-in-depth.md` and `dma.md` from Phase 2.
- Produces: `can-and-can-fd.md`, referenced by folder 12's automotive material.

- [ ] **Step 1: Create the category file**

```json
{
  "label": "Connectivity and Protocols",
  "position": 9,
  "link": {
    "type": "generated-index"
  }
}
```

- [ ] **Step 2: Write the six pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `choosing-a-bus-or-link.md` | 1 | Decision matrix over distance, nodes, rate, noise, power, certification | — (links; this is the folder's index page) |
| `can-and-can-fd.md` | 2 | WaveDrom of two nodes arbitrating, showing the dominant bit winning | Bosch *CAN Specification 2.0*; ISO 11898-1 |
| `canopen-and-j1939.md` | 3 | Mermaid of the object dictionary and PDO/SDO relationship | CiA 301 (CAN in Automation); SAE J1939 standards family |
| `modbus.md` | 4 | Table of the four register spaces and the function codes that reach them | Modbus Organization, *MODBUS Application Protocol Specification V1.1b3* |
| `rs485-and-industrial-serial.md` | 5 | WaveDrom of driver-enable turnaround around a transmission | TIA/EIA-485-A; transceiver vendor application notes |
| `ethernet-on-mcu.md` | 6 | Mermaid of MAC/PHY/RMII and the descriptor ring | IEEE 802.3; lwIP documentation |

Required content that generic write-ups omit:

- `can-and-can-fd.md` — arbitration is **non-destructive**: the lower identifier wins and the loser
  backs off without corrupting the frame. Cover bit timing and sample-point calculation, the error
  counters, and bus-off recovery. This is the page where a WaveDrom diagram earns its place.
- `modbus.md` — the addressing off-by-one (documentation numbers registers from 1, the wire numbers
  them from 0) that has confused engineers for forty years, and RTU's inter-frame timing rule.
- `rs485-and-industrial-serial.md` — the firmware-visible problem is driver-enable turnaround: release
  too early and you truncate your own last byte, too late and you collide with the reply.
- `ethernet-on-mcu.md` — note that the STM32F411 has **no Ethernet MAC**; this page is written
  against parts that do (STM32F4x7 and similar). Say so rather than implying the reference board works.

- [ ] **Step 3: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 4: Run the conventions check** with `FOLDER=docs/embedded/08-connectivity-and-protocols`.
- [ ] **Step 5: Commit**

```bash
git add docs/embedded/08-connectivity-and-protocols
git commit -m "docs: add can, modbus and industrial serial pages"
```

---

### Task 2: Folder 08 — Connectivity, part 2: networking and radios (6 pages)

**Files:**
- Create: `tcp-ip-on-constrained-devices.md`, `mqtt-and-coap.md`, `bluetooth-low-energy.md`, `wifi-on-mcu.md`, `lpwan.md`, `usb-device-on-mcu.md`

**Interfaces:**
- Consumes: Task 1's pages; `09-low-power-design/energy-budgets.md` from Phase 2.
- Produces: the complete folder 08.

Every page here is governed by the no-duplication contract: `computer-science/computer-networks/*`
owns OSI, TCP, UDP, and routing; `computer-science/buses-and-io/usb.md` owns the USB bus itself.
Link to them and write only the constrained-device material.

- [ ] **Step 1: Write the six pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `tcp-ip-on-constrained-devices.md` | 7 | Table of lwIP's raw, netconn, and socket APIs against thread-safety and RAM | lwIP documentation (savannah.nongnu.org/projects/lwip) |
| `mqtt-and-coap.md` | 8 | Mermaid of publish/subscribe versus request/response | OASIS *MQTT Version 5.0*; RFC 7252 (CoAP) |
| `bluetooth-low-energy.md` | 9 | Mermaid of the GATT service/characteristic tree; table of connection interval against latency and current | Bluetooth SIG *Core Specification*; Nordic DevAcademy |
| `wifi-on-mcu.md` | 10 | Table of integrated radio versus host-plus-module | IEEE 802.11; ESP-IDF documentation as the worked example |
| `lpwan.md` | 11 | Table of LoRaWAN, NB-IoT, and LTE-M against range, rate, power, and operator dependency | LoRa Alliance *LoRaWAN Specification*; 3GPP NB-IoT documentation |
| `usb-device-on-mcu.md` | 12 | Mermaid of enumeration, step by step | USB-IF *USB 2.0 Specification*; ST **RM0383** USB OTG FS chapter |

Required content:

- `bluetooth-low-energy.md` — the framing that makes BLE click: it is a data model (GATT) as much as
  a radio, and connection interval is the single dial trading latency against battery life. Give
  real numbers with their source.
- `mqtt-and-coap.md` — what each QoS level actually costs in round trips and stored state; last-will
  messages; reconnection on a flaky link.
- `usb-device-on-mcu.md` — enumeration failures are the common problem; show how to debug one, and
  which classes (CDC, HID, MSC) need no host driver.

- [ ] **Step 2: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 3: Run the conventions check.** All 12 pages must pass.
- [ ] **Step 4: Confirm the folder is complete**

```bash
ls docs/embedded/08-connectivity-and-protocols/*.md | wc -l
```

Expected: `12`.

- [ ] **Step 5: Commit**

```bash
git add docs/embedded/08-connectivity-and-protocols
git commit -m "docs: add tcp-ip, mqtt, ble and usb device pages"
```

---

### Task 3: Folder 10 — Embedded Linux, part 1: boot and configuration (5 pages)

**Files:**
- Create: `docs/embedded/10-embedded-linux/_category_.json`
- Create: `when-you-need-linux.md`, `the-boot-chain.md`, `u-boot.md`, `device-tree.md`, `kernel-configuration-and-build.md`

**Interfaces:**
- Consumes: `00-overview/bare-metal-vs-rtos-vs-linux.md` and `02-processor-architecture/arm-cortex-m-profiles.md` from Phase 1.
- Produces: `device-tree.md`, which Tasks 4 and 5 both depend on.

**Verify kernel, U-Boot, and Yocto specifics via context7 before writing.** Record check dates.

**Write against a generic ARM Linux target**, naming a Raspberry Pi or BeagleBone where a concrete
example helps. The reference NUCLEO board cannot run Linux; do not imply otherwise.

**Bootlin's training slides are CC BY-SA** and are the preferred figure source for this entire
folder. If you add one, attribute the licence in the caption and add the `SOURCES.md` row in the
same commit.

- [ ] **Step 1: Create the category file**

```json
{
  "label": "Embedded Linux",
  "position": 11,
  "link": {
    "type": "generated-index"
  }
}
```

- [ ] **Step 2: Write the five pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `when-you-need-linux.md` | 1 | Decision table: MMU, networking, filesystems, display, third-party software, team size | Bootlin *Embedded Linux system development* training materials (CC BY-SA) |
| `the-boot-chain.md` | 2 | Mermaid of BootROM → SPL → U-Boot → kernel → init, annotated with where each stage lives | Bootlin training materials; docs.u-boot.org |
| `u-boot.md` | 3 | Table of the environment variables and commands that matter, with a worked `bootcmd` | docs.u-boot.org |
| `device-tree.md` | 4 | Annotated ` ```text ` `.dts` excerpt; Mermaid of `compatible` string → driver binding | devicetree.org *Devicetree Specification*; docs.kernel.org devicetree bindings |
| `kernel-configuration-and-build.md` | 5 | Table of `ARCH`/`CROSS_COMPILE`/image-target combinations | docs.kernel.org kbuild documentation |

Required content:

- `when-you-need-linux.md` — the threshold is the **MMU**, and the costs are boot time,
  determinism, BOM, and a maintenance obligation measured in years. Links to
  `../../computer-science/memory-hierarchy/virtual-memory-and-paging.md` per the no-duplication
  table rather than re-explaining paging.
- `device-tree.md` — lead with *why it exists*: describing hardware that cannot be discovered, so
  one kernel binary serves many boards. Cover `.dts` versus `.dtsi` versus overlays, and reading
  `/sys/firmware/devicetree` on a running system.
- All device tree and Kconfig listings use ` ```text `, never ` ```c `.

- [ ] **Step 3: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 4: Run the conventions check** with `FOLDER=docs/embedded/10-embedded-linux`.
- [ ] **Step 5: Commit**

```bash
git add docs/embedded/10-embedded-linux static/img/embedded
git commit -m "docs: add linux boot chain, u-boot and device tree pages"
```

---

### Task 4: Folder 10 — Embedded Linux, part 2: drivers (5 pages)

**Files:**
- Create: `kernel-modules.md`, `character-drivers.md`, `kernel-driver-frameworks.md`, `userspace-hardware-access.md`, `root-filesystems-and-init.md`

**Interfaces:**
- Consumes: Task 3's `device-tree.md`.
- Produces: `userspace-hardware-access.md`, referenced by Task 5's boot-time page.

- [ ] **Step 1: Write the five pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `kernel-modules.md` | 6 | Mermaid of build → `insmod` → `probe` → `rmmod` lifecycle | docs.kernel.org kbuild; Bootlin kernel training (CC BY-SA) |
| `character-drivers.md` | 7 | Table of `file_operations` members against the syscall each serves | *Linux Device Drivers, Third Edition* (free online, dated but still the clearest introduction); docs.kernel.org |
| `kernel-driver-frameworks.md` | 8 | Mermaid of devicetree node → platform driver `probe` → subsystem registration | docs.kernel.org driver-api; Bootlin kernel training |
| `userspace-hardware-access.md` | 9 | Decision table: sysfs, libgpiod, spidev, i2c-dev, UIO, `/dev/mem` | libgpiod documentation; docs.kernel.org gpio and spi userspace APIs |
| `root-filesystems-and-init.md` | 10 | Mermaid of a minimal rootfs layout; table of init options | BusyBox documentation; systemd documentation |

Required content:

- `character-drivers.md` — `copy_to_user`/`copy_from_user` are mandatory; dereferencing a userspace
  pointer directly is a bug even when it appears to work. Cover `ioctl` and that its numbering
  becomes an ABI you must not break.
- `kernel-driver-frameworks.md` — the payoff framing: writing to a subsystem (IIO, gpiod, spi) gives
  you userspace interfaces for free, and that is why it beats a bespoke char driver.
- `userspace-hardware-access.md` — the old sysfs GPIO interface (`/sys/class/gpio`) is **deprecated**
  in favour of the character-device interface and `libgpiod`; a lot of published material still
  teaches the deprecated one. Say so explicitly.
- `root-filesystems-and-init.md` — read-only rootfs with a writable overlay as the right default for
  a shipped device.
- Links to `../../computer-science/operating-systems/{processes-and-threads,memory-management}.md`
  per the no-duplication table.

- [ ] **Step 2: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 3: Run the conventions check.**
- [ ] **Step 4: Commit**

```bash
git add docs/embedded/10-embedded-linux static/img/embedded
git commit -m "docs: add kernel modules, char drivers and userspace access pages"
```

---

### Task 5: Folder 10 — Embedded Linux, part 3: build systems and real-time (4 pages)

**Files:**
- Create: `yocto.md`, `buildroot.md`, `realtime-linux.md`, `boot-time-optimization.md`

**Interfaces:**
- Consumes: Tasks 3–4.
- Produces: the complete folder 10.

- [ ] **Step 1: Write the four pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `yocto.md` | 11 | Mermaid of layers → recipes → BitBake → image and SDK | docs.yoctoproject.org |
| `buildroot.md` | 12 | Table comparing Buildroot and Yocto on build time, learning curve, and package management | buildroot.org documentation |
| `realtime-linux.md` | 13 | Table of preemption models; `cyclictest` output excerpt with latency figures | Linux Foundation real-time wiki; docs.kernel.org on preemption |
| `boot-time-optimization.md` | 14 | Mermaid of the boot timeline with each stage's cost | Bootlin boot-time optimization training (CC BY-SA); `systemd-analyze` documentation |

Required content:

- `yocto.md` — be honest about the build times and disk usage nobody warns about, and frame
  reproducibility as the reason the complexity is worth accepting.
- `realtime-linux.md` — state what PREEMPT_RT actually changes and give realistic latency
  expectations with the measurement conditions. Do not present Linux as a substitute for an MCU on
  hard-deadline work; link back to `../06-interrupts-timing-and-real-time/real-time-definitions.md`.

- [ ] **Step 2: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 3: Run the conventions check.** All 14 pages must pass.
- [ ] **Step 4: Confirm the folder is complete**

```bash
ls docs/embedded/10-embedded-linux/*.md | wc -l
```

Expected: `14`.

- [ ] **Step 5: Commit**

```bash
git add docs/embedded/10-embedded-linux static/img/embedded
git commit -m "docs: add yocto, buildroot and realtime linux pages"
```

---

### Task 6: Folder 12 — Safety, part 1: the standards (6 pages)

**Files:**
- Create: `docs/embedded/12-safety-and-reliability/_category_.json`
- Create: `why-functional-safety.md`, `iec-61508.md`, `iso-26262.md`, `do-178c.md`, `iec-62304-and-medical.md`, `misra-c.md`

**Interfaces:**
- Consumes: `08-connectivity-and-protocols/can-and-can-fd.md` (automotive context).
- Produces: the standards vocabulary Task 7's practice pages use.

- [ ] **Step 1: Create the category file**

```json
{
  "label": "Safety and Reliability",
  "position": 13,
  "link": {
    "type": "generated-index"
  }
}
```

- [ ] **Step 2: Add the guardrail note to every page in this folder**

Use this exact wording on all twelve pages in folders 12 (Tasks 6 and 7), placed immediately after
the opening prose:

```md
:::note[This page is not the standard]
The standard itself is a paywalled purchase. This page explains its structure, intent, and what
complying with it changes about day-to-day engineering, and cites parts and clauses so you can
navigate the document if you have access. It does not reproduce normative text, and it is not a
substitute for reading the standard or for a competent assessor.
:::
```

- [ ] **Step 3: Write the six pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `why-functional-safety.md` | 1 | Mermaid of hazard → risk → tolerable risk → requirement | IEC 61508-1, scope and definitions |
| `iec-61508.md` | 2 | Table of SIL 1–4 against target failure measures for low and high demand modes | IEC 61508 parts 1–3 (IEC, purchase) |
| `iso-26262.md` | 3 | Table of the severity/exposure/controllability grid producing ASIL A–D and QM | ISO 26262 parts 3, 6, and 9 (ISO, purchase) |
| `do-178c.md` | 4 | Table of DAL A–E against objectives and independence | RTCA DO-178C (RTCA, purchase) |
| `iec-62304-and-medical.md` | 5 | Table of software safety classes A, B, C against required processes | IEC 62304; ISO 14971 for the risk-management relationship |
| `misra-c.md` | 6 | Table of rule categories (mandatory, required, advisory) and directives versus rules | MISRA C:2012 and its amendments (MISRA, purchase) |

Required content:

- `iso-26262.md` — ASIL is **derived** from severity, exposure, and controllability, not chosen;
  cover ASIL decomposition and freedom from interference.
- `do-178c.md` — MC/DC is the structural coverage criterion that makes DAL A expensive; explain what
  it demands beyond branch coverage.
- `misra-c.md` — be even-handed: some rules prevent real defects, some are dogma, and the deviation
  process is a documentation burden teams underestimate. That honesty is why this page is worth
  reading over a rule listing.

- [ ] **Step 4: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 5: Verify the guardrail note is present**

```bash
grep -L "This page is not the standard" docs/embedded/12-safety-and-reliability/*.md
```

Expected: no output.

- [ ] **Step 6: Run the conventions check** with `FOLDER=docs/embedded/12-safety-and-reliability`.
- [ ] **Step 7: Commit**

```bash
git add docs/embedded/12-safety-and-reliability
git commit -m "docs: add functional safety standards pages"
```

---

### Task 7: Folder 12 — Safety, part 2: practice (6 pages)

**Files:**
- Create: `coding-standards-for-safety.md`, `defensive-programming.md`, `fault-detection-and-recovery.md`, `watchdog-strategies-for-safety.md`, `requirements-and-traceability.md`, `verification-and-certification.md`

**Interfaces:**
- Consumes: Task 6's pages; `05-peripherals-and-drivers/watchdogs.md` and `11-debugging-and-testing/static-analysis-and-sanitizers.md` from Phase 2.
- Produces: the complete folder 12.

- [ ] **Step 1: Write the six pages**, each carrying the same `:::note[This page is not the standard]` block defined in Task 6 Step 2.

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `coding-standards-for-safety.md` | 7 | Table comparing MISRA C, CERT C, Barr, and the Power of Ten on focus and enforcement | SEI CERT C Coding Standard (wiki.sei.cmu.edu); Barr Group Embedded C Coding Standard; Holzmann, *The Power of Ten* |
| `defensive-programming.md` | 8 | Mermaid of a state machine with an explicit safe state | IEC 61508-3 software design requirements |
| `fault-detection-and-recovery.md` | 9 | Table of self-test against the fault class it detects and its runtime cost | IEC 61508-2 diagnostic coverage; Arm/ST self-test library documentation |
| `watchdog-strategies-for-safety.md` | 10 | Mermaid of a supervisor requiring every task to check in before the kick | ST **RM0383** WWDG chapter; Jack Ganssle on watchdogs |
| `requirements-and-traceability.md` | 11 | Mermaid of bidirectional traceability requirement ↔ design ↔ code ↔ test | DO-178C traceability objectives; IEC 61508-3 |
| `verification-and-certification.md` | 12 | Table of the evidence package by artefact and who produces it | RTCA DO-178C; IEC 61508-1 assessment requirements |

Required content:

- `defensive-programming.md` — the honest treatment of assertions: what an assertion should do in a
  production safety build is a real decision with no universal answer. Present the trade-off rather
  than a rule.
- `watchdog-strategies-for-safety.md` — extends the Phase 2 watchdog page; explain why an internal
  watchdog may not be sufficient evidence for a safety argument and when an external IC is required.
- `verification-and-certification.md` — timeline and cost realities, and which practices are worth
  adopting even when you are not certifying anything.

- [ ] **Step 2: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 3: Verify the guardrail note** across all twelve pages:

```bash
grep -L "This page is not the standard" docs/embedded/12-safety-and-reliability/*.md
```

Expected: no output.

- [ ] **Step 4: Run the conventions check.** All 12 pages must pass.
- [ ] **Step 5: Commit**

```bash
git add docs/embedded/12-safety-and-reliability
git commit -m "docs: add safety practice, traceability and certification pages"
```

---

### Task 8: Folder 13 — Security, part 1: foundations and hardware (5 pages)

**Files:**
- Create: `docs/embedded/13-security/_category_.json`
- Create: `embedded-threat-model.md`, `secure-boot.md`, `crypto-accelerators-and-key-storage.md`, `secure-elements-and-tpms.md`, `trustzone-for-cortex-m.md`

**Interfaces:**
- Consumes: `03-toolchain-and-build/flashing-and-programming.md`; `05-peripherals-and-drivers/flash-and-eeprom-emulation.md`.
- Produces: `secure-boot.md`, which Task 9's anti-rollback page and Task 10's bootloader page both build on.

**Verify PSA Crypto API and TrustZone-M tooling via context7 before writing.** Record check dates.

- [ ] **Step 1: Create the category file**

```json
{
  "label": "Embedded Security",
  "position": 14,
  "link": {
    "type": "generated-index"
  }
}
```

- [ ] **Step 2: Write the five pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `embedded-threat-model.md` | 1 | Table of asset against attacker capability given physical access | Arm PSA Certified threat models and security analyses |
| `secure-boot.md` | 2 | Mermaid of the chain of trust from immutable ROM through each stage | Arm PSA Certified *Trusted Boot and Firmware Update* specification; MCUboot documentation |
| `crypto-accelerators-and-key-storage.md` | 3 | Table of TRNG, AES, and hash engines against what each removes from software | Arm PSA Crypto API specification; ST **RM0383** RNG chapter |
| `secure-elements-and-tpms.md` | 4 | Mermaid of the host/secure-element trust boundary | TCG TPM 2.0 Library Specification; secure element vendor documentation |
| `trustzone-for-cortex-m.md` | 5 | Mermaid of secure/non-secure worlds with NSC veneers | Arm *Armv8-M Security Extensions* documentation; Arm TrustZone for Cortex-M guidance |

Required content:

- `embedded-threat-model.md` is the framing page for the whole folder: physical access inverts the
  assumptions server security rests on. The attacker owns the device, can desolder the flash, and
  has unlimited time.
- **`trustzone-for-cortex-m.md` must open by stating that TrustZone-M is an Armv8-M feature
  (Cortex-M23/M33/M55) and that the Cortex-M4 on the reference board does not have it.** A reader
  trying to enable it on their NUCLEO-F411RE will waste a day otherwise. Link to
  `../02-processor-architecture/arm-cortex-m-profiles.md`.
- `crypto-accelerators-and-key-storage.md` — the key property worth understanding is a key the
  hardware can *use* but firmware cannot *read*. Cover OTP and fuses, and be clear that a software
  PRNG is not a substitute for a TRNG.

- [ ] **Step 3: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 4: Run the conventions check** with `FOLDER=docs/embedded/13-security`.
- [ ] **Step 5: Commit**

```bash
git add docs/embedded/13-security
git commit -m "docs: add threat model, secure boot and trustzone pages"
```

---

### Task 9: Folder 13 — Security, part 2: protecting a deployed device (5 pages)

**Files:**
- Create: `firmware-encryption-and-anti-rollback.md`, `debug-port-lockdown.md`, `side-channel-and-fault-injection.md`, `secure-communication-on-mcu.md`, `vulnerability-management-and-sbom.md`

**Interfaces:**
- Consumes: Task 8's pages.
- Produces: the complete folder 13; `vulnerability-management-and-sbom.md` is referenced by Task 11's long-term maintenance page.

**Verify Mbed TLS specifics via context7 before writing `secure-communication-on-mcu.md`.**

- [ ] **Step 1: Write the five pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `firmware-encryption-and-anti-rollback.md` | 6 | Table separating confidentiality, integrity, and authenticity and what each mechanism provides | MCUboot documentation; Arm PSA firmware update specification |
| `debug-port-lockdown.md` | 7 | Table of ST readout protection levels against what each blocks and what it costs you | ST **RM0383**, option bytes and readout protection |
| `side-channel-and-fault-injection.md` | 8 | Mermaid or table of attack class against countermeasure | Kocher et al., *Differential Power Analysis* (CRYPTO '99); published glitching research |
| `secure-communication-on-mcu.md` | 9 | Table of TLS/DTLS footprint against cipher suite and features enabled | Mbed TLS documentation (mbed-tls.readthedocs.io); RFC 8446 (TLS 1.3) |
| `vulnerability-management-and-sbom.md` | 10 | Mermaid of the SBOM → CVE monitoring → patch → OTA loop | EU Cyber Resilience Act; CycloneDX and SPDX specifications |

Required content:

- `debug-port-lockdown.md` must be clear-eyed: readout protection has historically been bypassed by
  published attacks, and a locked device is also a device you cannot diagnose in the field. Present
  both costs. Do not describe bypass techniques beyond naming that the class exists — the page's
  purpose is defensive decision-making.
- `secure-communication-on-mcu.md` — the certificate validation problem on a device with **no RTC**:
  you cannot check `notBefore`/`notAfter` without trustworthy time. Cover PSK as the pragmatic
  alternative. Links to `../../computer-science/protocols/tls-and-encryption-basics.md` per the
  no-duplication table rather than re-explaining TLS.
- `side-channel-and-fault-injection.md` is **awareness level**: name the attack classes, give
  constant-time comparison and redundant checks as baseline countermeasures, and say plainly when a
  threat model requires specialist help.

- [ ] **Step 2: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 3: Run the conventions check.** All 10 pages must pass.
- [ ] **Step 4: Commit**

```bash
git add docs/embedded/13-security
git commit -m "docs: add firmware encryption, debug lockdown and sbom pages"
```

---

### Task 10: Folder 14 — Firmware Lifecycle, part 1: build and ship (5 pages)

**Files:**
- Create: `docs/embedded/14-firmware-lifecycle/_category_.json`
- Create: `versioning-and-reproducible-builds.md`, `bootloaders.md`, `ota-and-firmware-updates.md`, `device-provisioning.md`, `production-programming-and-test.md`

**Interfaces:**
- Consumes: `03-toolchain-and-build/{startup-code,the-linker-script,flashing-and-programming}.md`; `13-security/secure-boot.md`.
- Produces: `bootloaders.md` and `ota-and-firmware-updates.md`, referenced by Task 11.

- [ ] **Step 1: Create the category file**

```json
{
  "label": "Firmware Lifecycle",
  "position": 15,
  "link": {
    "type": "generated-index"
  }
}
```

- [ ] **Step 2: Write the five pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `versioning-and-reproducible-builds.md` | 1 | Mermaid or table of what must be pinned for a byte-identical rebuild | reproducible-builds.org; Arm GNU Toolchain release notes |
| `bootloaders.md` | 2 | Mermaid of validate → relocate vector table → jump; memory layout diagram | MCUboot documentation; ST **AN2606** on the system bootloader |
| `ota-and-firmware-updates.md` | 3 | Mermaid of A/B slots with confirm and rollback | MCUboot documentation; Arm PSA firmware update specification |
| `device-provisioning.md` | 4 | Mermaid of the manufacturing-line provisioning flow | Arm PSA Certified provisioning guidance |
| `production-programming-and-test.md` | 5 | Table of programming method against volume and cost | ST **UM1724**; gang programmer vendor documentation |

Required content:

- `bootloaders.md` — the jump-to-application sequence is the part people get wrong: set the vector
  table offset (`VTOR`), set the main stack pointer from the application's vector table, then jump.
  Peripherals and interrupts the bootloader enabled must be disabled first, or the application
  inherits state it did not configure. Cover staying small enough never to need updating.
- `ota-and-firmware-updates.md` — atomic activation and automatic rollback on failure to confirm.
  Say plainly that the update path needs more testing than the application, because a bad update is
  the one bug you cannot fix remotely.

- [ ] **Step 3: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 4: Run the conventions check** with `FOLDER=docs/embedded/14-firmware-lifecycle`.
- [ ] **Step 5: Commit**

```bash
git add docs/embedded/14-firmware-lifecycle
git commit -m "docs: add bootloader, ota and provisioning pages"
```

---

### Task 11: Folder 14 — Firmware Lifecycle, part 2: operate and maintain (4 pages)

**Files:**
- Create: `configuration-and-calibration-storage.md`, `fleet-telemetry-and-diagnostics.md`, `ci-cd-for-firmware.md`, `long-term-maintenance.md`

**Interfaces:**
- Consumes: Task 10's pages; `11-debugging-and-testing/postmortem-and-crash-dumps.md`, `11-debugging-and-testing/unit-testing-firmware.md`, and `11-debugging-and-testing/simulation-and-emulation.md`; `13-security/vulnerability-management-and-sbom.md`.
- Produces: the complete folder 14.

- [ ] **Step 1: Write the four pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `configuration-and-calibration-storage.md` | 6 | Mermaid of schema versioning and migration on upgrade | ST **AN3969** EEPROM emulation; general record-format practice |
| `fleet-telemetry-and-diagnostics.md` | 7 | Table of metric against its bandwidth and power cost | Memfault documentation on device observability |
| `ci-cd-for-firmware.md` | 8 | Mermaid of the pipeline: build matrix → host tests → static analysis → size gate → sign → HIL → staged release | GitHub Actions documentation; the repo's own `.github/workflows/deploy.yml` as a local example |
| `long-term-maintenance.md` | 9 | Table of obsolescence risk against mitigation | Component obsolescence guidance from distributors; reproducible-builds.org |

Required content:

- `ci-cd-for-firmware.md` — the firmware-specific gates that general CI advice omits: flash and RAM
  size regression checks, worst-case stack budget, and artifact signing before anything reaches a
  device. Links back to `../11-debugging-and-testing/unit-testing-firmware.md` and
  `../11-debugging-and-testing/simulation-and-emulation.md`.
- `long-term-maintenance.md` — keeping a decade-old toolchain runnable (containerise it), security
  patching for products out of production, and planning end-of-life honestly.

- [ ] **Step 2: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 3: Run the conventions check.** All 9 pages must pass.
- [ ] **Step 4: Commit**

```bash
git add docs/embedded/14-firmware-lifecycle
git commit -m "docs: add telemetry, ci-cd and long-term maintenance pages"
```

---

### Task 12: Folder 15 — Languages, part 1: C++, and Rust foundations (6 pages)

**Files:**
- Create: `docs/embedded/15-languages-and-practice/_category_.json`
- Create: `freestanding-c-and-standards.md`, `cpp-on-microcontrollers.md`, `cpp-patterns-for-firmware.md`, `rust-embedded-overview.md`, `rust-pacs-hals-and-bsps.md`, `rust-concurrency-rtic-and-embassy.md`

**Interfaces:**
- Consumes: `03-toolchain-and-build/{startup-code,c-libraries-for-embedded}.md`; `04-bare-metal-programming/embedded-c-idioms.md`.
- Produces: the Rust layering vocabulary Task 13's interop page uses.

**Verify `embedded-hal` 1.0 traits, RTIC 2.x, and Embassy via context7 before writing the Rust pages.** This is the highest staleness risk in the section — `embedded-hal` 1.0 changed the trait set from the 0.2 series that most published tutorials still show. Record check dates in `## References`.

The no-duplication contract binds hard here: `programming/cpp/**` owns C++ language features. These
pages cover only what is *different* on a microcontroller.

- [ ] **Step 1: Create the category file**

```json
{
  "label": "Languages and Practice",
  "position": 16,
  "link": {
    "type": "generated-index"
  }
}
```

- [ ] **Step 2: Write the six pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `freestanding-c-and-standards.md` | 1 | Table of what a freestanding implementation must provide versus a hosted one | ISO/IEC 9899 (C standard), freestanding execution environment clause |
| `cpp-on-microcontrollers.md` | 2 | Table of each C++ feature against its flash, RAM, and determinism cost | Arm GNU Toolchain C++ documentation; the existing `programming/cpp/` section |
| `cpp-patterns-for-firmware.md` | 3 | `<Tabs>` comparing a C register access with a `constexpr` typed C++ equivalent | Odin Holmes / Kris Jusiak embedded C++ talks; ISO C++ committee guidance on freestanding |
| `rust-embedded-overview.md` | 4 | Table of what ownership prevents against the C bug class it corresponds to | *The Embedded Rust Book* (docs.rust-embedded.org) |
| `rust-pacs-hals-and-bsps.md` | 5 | Mermaid of SVD → `svd2rust` → PAC → HAL → BSP layering | `svd2rust` documentation; `embedded-hal` 1.0 documentation on docs.rs |
| `rust-concurrency-rtic-and-embassy.md` | 6 | `<Tabs>` comparing the same task in RTIC and in Embassy | rtic.rs documentation; embassy.dev documentation |

Required content:

- `cpp-on-microcontrollers.md` — the specific costs: exceptions and RTTI (usually disabled, and
  why), vtable overhead, template code bloat, the **static initialisation order problem**, and
  replacing global `operator new`. Links to `../../programming/cpp/` rather than teaching C++.
- `rust-pacs-hals-and-bsps.md` — the layering is the whole mental model, and `embedded-hal` 1.0
  traits are the portability contract. Show a driver generic over those traits.
- `rust-concurrency-rtic-and-embassy.md` — RTIC schedules at compile time and locks resources by
  priority ceiling; Embassy is an async executor where `await` maps onto interrupts. Give the
  criteria for choosing between them and a traditional RTOS, linking to `../07-rtos/why-an-rtos.md`.

- [ ] **Step 3: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 4: Run the conventions check** with `FOLDER=docs/embedded/15-languages-and-practice`.
- [ ] **Step 5: Commit**

```bash
git add docs/embedded/15-languages-and-practice
git commit -m "docs: add embedded c++ and rust foundation pages"
```

---

### Task 13: Folder 15 — Languages, part 2: interop, ML, and architecture (5 pages)

**Files:**
- Create: `rust-and-c-interop.md`, `micropython-and-scripting.md`, `ml-on-microcontrollers.md`, `firmware-architecture-and-layering.md`, `porting-to-a-new-chip.md`

**Interfaces:**
- Consumes: Task 12's pages; `05-peripherals-and-drivers/writing-a-portable-driver.md`; `03-toolchain-and-build/the-linker-script.md`.
- Produces: the complete folder 15 and therefore all 174 pages.

- [ ] **Step 1: Write the five pages**

| File | `sidebar_position` | Required visual anchor | Primary reference to cite |
|---|---|---|---|
| `rust-and-c-interop.md` | 7 | Mermaid of the mixed-language build producing one image | `bindgen` and `cbindgen` documentation; *The Embedded Rust Book* interop chapter |
| `micropython-and-scripting.md` | 8 | Table of interpreter cost against the cases where it still wins | docs.micropython.org |
| `ml-on-microcontrollers.md` | 9 | Table of model size and arena RAM against what fits on this class of part | TensorFlow Lite for Microcontrollers documentation; CMSIS-NN documentation |
| `firmware-architecture-and-layering.md` | 10 | Mermaid of the layering with the hardware boundary marked | Elecia White, *Making Embedded Systems*; Robert Martin on dependency direction |
| `porting-to-a-new-chip.md` | 11 | Mermaid or table of the porting procedure in dependency order | — (synthesises the section; cite the reference manuals of both parts in a worked comparison) |

Required content:

- `ml-on-microcontrollers.md` — links to
  `../../gpu-computing/12-npu-and-inference-accelerators/quantization-for-accelerators.md` for
  quantization theory per the no-duplication table, and to that folder's edge-NPU pages. The page's
  own contribution is the arena allocator and RAM ceiling, operator support gaps, latency budgeting,
  and the honest question of whether a threshold or a filter would do the job instead.
- `porting-to-a-new-chip.md` is the section's capstone: inventory hardware dependencies, map
  peripheral differences, rebuild clock and memory configuration, port linker script and startup,
  bring peripherals up in dependency order. It should demonstrate what the layering from the
  previous page actually saves.

- [ ] **Step 2: Build.** Run `npm run build`. Expected: exit 0.
- [ ] **Step 3: Run the conventions check.** All 11 pages must pass.
- [ ] **Step 4: Confirm the folder is complete**

```bash
ls docs/embedded/15-languages-and-practice/*.md | wc -l
```

Expected: `11`.

- [ ] **Step 5: Commit**

```bash
git add docs/embedded/15-languages-and-practice
git commit -m "docs: add rust interop, tinyml and firmware architecture pages"
```

---

### Task 14: Final sweep — the complete section

**Files:**
- Modify: `docs/embedded/readme.md`
- Modify: the specific pages listed in Step 2

**Interfaces:**
- Consumes: all 174 pages.
- Produces: the finished section, matching the spec exactly.

- [ ] **Step 1: Complete the learning paths in `readme.md`**

Every path target now exists. Link all of them and **remove the "still being written" note**:

- **Day one** → `00-overview/what-embedded-means.md` → `01-hardware-foundations/what-hardware-to-buy.md` → `04-bare-metal-programming/your-first-bare-metal-blink.md` → 02 → 03.
- **I have a board and nothing works** → 01 → 03 → 04 → `11-debugging-and-testing/the-debug-toolbox.md`.
- **I'm building a product** → 04 → `05-peripherals-and-drivers/anatomy-of-a-peripheral.md` → `07-rtos/why-an-rtos.md` → `09-low-power-design/energy-budgets.md` → `14-firmware-lifecycle/ota-and-firmware-updates.md`.
- **I'm moving to Linux** → 02 → `10-embedded-linux/when-you-need-linux.md` → `11-debugging-and-testing/the-debug-toolbox.md`.

Confirm the curated master reference list is present and complete per the spec's "External references" section.

- [ ] **Step 2: Add the deferred backlinks**

These pages were written before their targets existed. Add one link each, in `## See also`:

| Page to modify | Link to add |
|---|---|
| `05-peripherals-and-drivers/uart-in-depth.md` | `../08-connectivity-and-protocols/rs485-and-industrial-serial.md` |
| `05-peripherals-and-drivers/flash-and-eeprom-emulation.md` | `../14-firmware-lifecycle/configuration-and-calibration-storage.md` |
| `05-peripherals-and-drivers/watchdogs.md` | `../12-safety-and-reliability/watchdog-strategies-for-safety.md` |
| `07-rtos/why-an-rtos.md` | `../15-languages-and-practice/rust-concurrency-rtic-and-embassy.md` |
| `11-debugging-and-testing/unit-testing-firmware.md` | `../14-firmware-lifecycle/ci-cd-for-firmware.md` |
| `03-toolchain-and-build/flashing-and-programming.md` | `../13-security/debug-port-lockdown.md` |
| `04-bare-metal-programming/embedded-c-idioms.md` | `../12-safety-and-reliability/misra-c.md` |
| `02-processor-architecture/arm-cortex-m-profiles.md` | `../13-security/trustzone-for-cortex-m.md` |
| `00-overview/glossary.md` | link every previously-unlinked term to its home page |

Keep each `## See also` at 3–5 bullets; drop the weakest existing bullet rather than growing a list
past five.

- [ ] **Step 3: Verify the whole section**

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
```

Expected: no output.

- [ ] **Step 4: Confirm the final page count**

```bash
find docs/embedded -name '*.md' -not -name 'readme.md' | wc -l
for d in docs/embedded/*/; do echo "$(ls "$d"*.md 2>/dev/null | wc -l) $d"; done
```

Expected total: `174`. Per folder: 6, 11, 11, 11, 12, 14, 9, 13, 12, 7, 14, 12, 12, 10, 9, 11.

- [ ] **Step 5: Confirm no device tree is mislabelled as C**

```bash
grep -rn '^```c$' docs/embedded/10-embedded-linux/ | head
```

Review each hit: device tree, Kconfig, and linker-script listings must use ` ```text `. Actual C
source in kernel-module and char-driver pages correctly uses ` ```c `.

- [ ] **Step 6: Verify every image is sourced and the section is not bloated**

```bash
find static/img/embedded -type f -not -name SOURCES.md | while read -r img; do
  grep -q "$(basename "$img")" static/img/embedded/SOURCES.md || echo "UNSOURCED: $img"
done
du -sh static/img/embedded static/img/gpu
```

Expected: no `UNSOURCED` lines; `static/img/embedded` in the same order of magnitude as
`static/img/gpu` (~1.2 MB).

- [ ] **Step 7: Full verification**

```bash
npm run build
npm run typecheck
npm run test:plugins
npx biome check docs/embedded
```

Expected: build exit 0, typecheck clean, 8 tests passing, Biome clean on `docs/embedded`.
Repo-wide `npm run lint` still fails on 157 pre-existing errors in unrelated files — the documented
baseline, not a regression.

- [ ] **Step 8: Visual spot-check**

Run `npm run serve`. Confirm all sixteen folders appear in order, the four learning paths work end
to end, WaveDrom diagrams render in both themes, and the search box finds pages from folders 12–15.
Stop the server.

- [ ] **Step 9: Commit**

```bash
git add docs/embedded
git commit -m "docs: complete embedded systems section"
```

---

## Assumptions most likely to need revising after Phases 1 and 2

This plan was written before either earlier phase was executed. Re-check before starting:

1. **`embedded-hal` 1.0.** Task 12's Rust pages are the section's biggest staleness risk. Verify via
   context7 at write time, not from this plan.
2. **Bootlin figure availability.** Folder 10's figure strategy assumes Bootlin's CC BY-SA slides
   remain available and relevant. If not, Mermaid is the correct fallback, not a vendor PDF screenshot.
3. **Task size.** Tasks 1, 2, 6, 7, and 12 are six pages each. If Phase 1 and 2 showed six pages is
   too much for one session, split them before starting.
4. **The deferred backlink table in Task 14** assumes the exact filenames in Phases 1 and 2 shipped
   as planned. Verify each path resolves before editing; the build will catch any that do not.
5. **The board.** Every RM0383 and PM0214 citation assumes the NUCLEO-F411RE chosen in Phase 1.
