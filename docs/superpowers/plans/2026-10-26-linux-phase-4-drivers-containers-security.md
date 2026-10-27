# Linux & Kernel Section — Phase 4 (Drivers, Containers, Security) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold and write folders `14`–`16` of `docs/linux/`. That is 37 pages: device drivers and hardware, containers and virtualization, and the security model. Also write the four `computer-science/` backfill pages those folders declare as prerequisites (hardware virtualization, PCIe in depth, DMA and the IOMMU, isolation theory) and the backlinks into them. Turn every prose-only forward mention of folders 14–16 in folders 00–13 into a real link. Finish at a green `npm run build` with `npm run check:linux -- --written` passing for folders 00–16.

**Architecture:** No new site machinery. Phase 4 uses the Phase 1a–3 toolchain unchanged: the manifest-driven scaffolder, the knowledge-graph build gate, `<PrereqBlock>` injection, and the registered MDX components. The work comes in four kinds:
- one mechanical task that extends `tools/linux-docs-manifest.json` and regenerates the tree;
- two CS backfill tasks;
- sixteen writing tasks against fixed per-page briefs;
- a closing set of aggregation tasks: forward-link resolution, figures, glossary, misconceptions index and roadmap, and the review.

This phase contains two **build-it-yourself labs**: `14/lab-a-character-driver` and `15/building-a-container-from-scratch`. The spec requires both to be **run in the QEMU lab before the pages around them are finalised**. Their tasks therefore run the lab first and write the page from what actually happened.

**Tech Stack:** Docusaurus 3.10.2, React 19, Mermaid (via `@docusaurus/theme-mermaid`), WaveDrom (`src/plugins/remark-wavedrom.js`), Biome 2.5.7, Node 22 (`node --test`), `docusaurus-plugin-image-zoom`, and context7 MCP for currency checks.

**Spec:** `docs/superpowers/specs/2026-08-28-linux-kernel-docs-design.md`. This plan implements:
- its "Phase 4 ordering" section;
- the folder 14/15/16 outlines;
- backfill rows 5, 9, 11 and 18.

**Predecessor plans:** `2026-08-28-linux-phase-1a-infrastructure.md`, `2026-08-29-linux-phase-1b-foundations.md`, `2026-09-04-linux-phase-2-core-kernel.md` and `2026-09-14-linux-phase-3-storage-and-networking.md`. All have been executed and merged to `master`.

**Base branch:** `linux-phase-4-drivers-containers-security`, cut from `master` at `c8dc471`. Following the branch-per-phase convention, squash-merge it when the phase is done and delete it after the merge.

---

## Global Constraints

- **Pinned kernel is `v6.18`** (`customFields.linuxKernelVersion`). Every source citation goes through `<Src file="..." symbol="..." />`. Never hand-write an `elixir.bootlin.com` URL, and never cite a line number.
- **Never invent a symbol, struct field, path, sysctl, config option, ioctl, or interface file.** Before a page is committed, check every symbol at `https://elixir.bootlin.com/linux/v6.18/ident/<symbol>` and every path at `/source/<path>`. Every symbol in this plan is an informed starting point, **not** a verified fact. This phase's code moved recently:
  - `class_create` lost its `owner` argument;
  - `platform_driver.remove` returns `void` (the `remove_new` transition is finished);
  - `pci_alloc_irq_vectors` replaced `pci_enable_msix`;
  - `DEFINE_SIMPLE_DEV_PM_OPS` and `pm_ptr()` replaced the `SIMPLE_DEV_PM_OPS` idiom;
  - `dma_alloc_noncoherent` and `dma_alloc_pages` arrived, and swiotlb gained dynamic pools;
  - cgroup v2 gained `memory.peak` writes, `memory.zswap.*`, and `cpu.max.burst`;
  - seccomp user notification gained `SECCOMP_ADDFD_FLAG_SEND`;
  - LSM syscalls arrived (`lsm_get_self_attr`, `lsm_set_self_attr`, `lsm_list_modules`);
  - Landlock gained network and scoping rules;
  - IPE was merged as a new LSM.

  Where a symbol has moved, cite what v6.18 actually has. Mention the old name only when the page's subject is the change itself or when a reader will meet the old name in tutorials. Name the latter explicitly as outdated.
- **Every doc under `docs/linux/` must carry a `prerequisites` front-matter key.** The scaffolder writes it. Do not remove it.
- **`onBrokenLinks: "throw"`.** Folders **17–19 are not scaffolded**, so no page may link into them. Observability, `ftrace` depth, sanitizers, eBPF and contributing are named in prose with no link. The exception is folder 01's existing `ftrace`/`gdb` material, which can be linked. Links backwards into 00–13 and sideways within 14–16 are free, because Task 1 scaffolds all three folders before any is written.
- **Relative doc links only**, e.g. `../14-device-drivers-and-hardware/the-dma-api.md`. Never `/docs/linux/...`.
- **`## What actually happens` is conditional.** Only pages marked **[WAH]** carry it.
- **Every finished topic page ends with `<KernelFacts />` and carries `## References`** with 2–6 annotated entries. `tools/check-linux-docs.mjs` enforces both.
- **Every page carries at least one visual anchor**, and its caption says what it shows.
- **Visual vocabulary is fixed** (spec):
  - Mermaid `flowchart` for code paths and layering;
  - `stateDiagram-v2` for state machines (runtime-PM states, device bind states, SELinux enforcing modes);
  - `sequenceDiagram` for interactions over time (probe, DMA ownership handoff, suspend/resume, the KVM run loop);
  - WaveDrom `reg` for bit-field layouts (the PCI command register, `CLONE_NEW*` flags, the capability sets, a seccomp return value);
  - `<Tabs>` for genuine alternatives (DT vs ACPI, cgroup v1 vs v2, SELinux vs AppArmor);
  - tables for comparison.
- **Struct-heavy pages get a struct-*shape* diagram, not a struct dump.** This applies to `struct device`, `struct pci_dev`, `struct cred`, `struct kvm_run` and `struct nsproxy`.
- **Fence languages:**
  - kernel and user C → ` ```c `
  - `dmesg`, `lspci`, `/proc`/`/sys` dumps, AVC denials, `ausearch` output, Kconfig, devicetree source, udev rules, SELinux/AppArmor policy source, OCI `config.json` excerpts → ` ```text `, or ` ```json ` for the OCI JSON
  - `.config` fragments → ` ```ini `
  - shell → ` ```bash `

  No new Prism language is added. A devicetree, udev or AppArmor fence is ` ```text `.
- **Five admonitions only.** `:::danger` is reserved for irreversible damage. A `<Lab>` carrying a `:::danger` may not have `host="any-linux"`. In this phase that means:
  - loading an unsigned module with lockdown or module signing enforced;
  - relabeling a filesystem for SELinux;
  - binding a real device to `vfio-pci`.
- **Name the architecture on every arch-specific claim.** Folder 14 owns three of the spec's structural **arm64 contrast `:::note`s**. They are required, and the review checks them:
  - `platform-devices-and-description` (device tree as the arm64 norm — carried by its `<Tabs>`);
  - `mmio-and-port-io` (no port I/O on arm64, and how arm64 `readl`/`writel` order against DMA);
  - `the-dma-api` (non-coherent DMA on many arm64 SoCs makes the `dma_sync_*` calls real cache maintenance rather than no-ops).

  Folders 15 and 16 own none. Do not invent one to fill a quota.
- **Folder 16 is defensive throughout (spec).** No page contains working exploit code, a proof-of-concept, or a step-by-step exploitation procedure. Attack classes are described by shape, consequence, recognition and mitigation. This has a separate review check in Task 24.
- **Casts.** The spec marks `<Cast>` on `14/lab-a-character-driver`. Per the Phase 3 precedent, **no casts are recorded in this phase**. The lab ships its session as annotated ` ```text ` blocks, and the cast library is recorded in one Phase 5 session.
- **Figures in `docs/linux/` are not licence-gated**. They still need a `static/img/linux/SOURCES.md` row and a `<Figure source= href= />` credit. **Figures in `docs/computer-science/` keep normal licence discipline**: a `static/img/cs/SOURCES.md` row with `file | source | author | licence` and `license=` on `<Figure>`.
- **context7 verification is mandatory** (spec table). The check date goes into the page's `## References` annotation:
  - **14:** current driver-model APIs and DMA API function names;
  - **15:** cgroup v2 controller files and their semantics, runc/containerd and the OCI runtime spec, the Docker CLI;
  - **16:** seccomp, SELinux and AppArmor policy tooling.

  Where context7 has no entry, cite `docs.kernel.org` or the man page and say so.
- **No-duplication contract (spec, normative).**
  - `computer-science/buses-and-io/*` (including backfill 9 and 11) owns PCIe and DMA/IOMMU *hardware*. Folder 14 owns the driver's use of them.
  - `computer-science/cpu-architecture/hardware-virtualization` owns VT-x/AMD-V, VM entry/exit and EPT/NPT. `15/kvm-and-hardware-virtualization` owns `/dev/kvm` and the run loop.
  - `computer-science/operating-systems/virtualization-and-isolation` owns isolation *theory*. Folder 15 owns Linux's mechanism.
  - `11/mounts-and-mount-namespaces` and `11/overlayfs` own mount propagation and overlay mechanics. `13/network-namespaces-and-virtual-devices` and `13/connection-tracking-and-nat` own veth, bridge and NAT. Folder 15 links to them and adds only the container angle.
  - `06/credentials-and-identity` owns the process-side view of UIDs. `16/credentials-in-the-kernel` goes deeper and does not repeat it.
  - `07/cgroup-cpu-control` owns `cpu.weight`/`cpu.max` and CFS bandwidth. `15/cgroup-controllers-in-practice` links to it for `cpu` rather than re-deriving it.
- **`## Misconceptions` entries are mirrored** into `00-overview/misconceptions-index.md` (Task 23).
- **Biome:** run the lint gate raw — `rtk run 'npm run lint'`.
- **Commit messages:** `<type>: <what>` on one line. **Never** a `Co-Authored-By` trailer or a "Generated with Claude Code" line. `CLAUDE.md` and the user's memory override any tool default.

## Review Focus

These are the failure modes that are most likely to reach a reader and that no build gate catches, most likely first. Each has a check in its owning task.

1. **A lab's code that only compiles against a 5.x-era API.** Driver tutorials online overwhelmingly use the old forms: `class_create(THIS_MODULE, …)`, `int (*remove)()`, and `pci_enable_msix`. Tasks 7 and 13 require the code on the page to be byte-identical to the code that ran against the v6.18 lab kernel.
2. **A container lab that silently works only as root on the author's distro.** Ubuntu 24.04+ restricts unprivileged user namespaces through AppArmor (`kernel.apparmor_restrict_unprivileged_userns`). Tasks 11 and 13 state the restriction and the exact error a reader sees, and their labs run in the Debian VM, where the behaviour is measured.
3. **A security page that drifts into an exploitation procedure.** Task 19 Step 4 and Task 24 grep and read for it.
4. **`--privileged` or `CAP_SYS_ADMIN` described as "a bit more access".** Task 13's `capabilities-in-containers` and Task 16's `capabilities` must each state the root-equivalence plainly, with the mechanism (for example, mounting, BPF, or module loading).
5. **A lab that leaves host state changed.** This covers a loaded module, a cgroup, a veth/bridge/nftables table, an SELinux mode, and an enabled audit rule. Every lab ends with a cleanup block, and Task 24 checks each one.

---

## File Structure

**Modified (machinery)**

| File | Change |
|---|---|
| `tools/linux-docs-manifest.json` | Three new folder objects (`14`–`16`, 37 pages) and four new `external` entries. Nothing existing is edited. |

**Created by the scaffolder in Task 1 — never by hand**

| Path | Count |
|---|---|
| `docs/linux/14-device-drivers-and-hardware/` + `_category_.json` | 13 pages |
| `docs/linux/15-containers-and-virtualization/` + `_category_.json` | 12 pages |
| `docs/linux/16-security/` + `_category_.json` | 12 pages |
| `docs/computer-science/cpu-architecture/hardware-virtualization.md` | backfill 5 |
| `docs/computer-science/buses-and-io/pcie-in-depth.md` | backfill 9 |
| `docs/computer-science/buses-and-io/dma-and-iommu.md` | backfill 11 |
| `docs/computer-science/operating-systems/virtualization-and-isolation.md` | backfill 18 |

**Created by hand (lab sources, kept in the repo so the page and the code cannot drift)**

| Path | Purpose |
|---|---|
| `static/code/linux/chardrv/chardrv.c`, `Makefile`, `test_chardrv.c` | The Task 7 module and its user-space exerciser; the page embeds them verbatim and links to the files. |
| `static/code/linux/minicontainer/minicontainer.c`, `setup-rootfs.sh`, `Makefile` | The Task 13 container; same rule. |

`static/` serves these files as downloads. `static/code/` is new: Phase 3's `lab-a-minimal-filesystem` embedded its module inline and shipped no file, so there is no existing convention to follow.

**Modified (existing CS pages — small, additive backlinks only)**

| File | Edit |
|---|---|
| `docs/computer-science/cpu-architecture/intro.md` | New bullet for backfill 5. |
| `docs/computer-science/cpu-architecture/privilege-levels-and-protection.md` | `## Related Pages`: backfill 5 (root/non-root mode is a new privilege axis). |
| `docs/computer-science/buses-and-io/intro.md` | Two new bullets for backfill 9 and 11. |
| `docs/computer-science/buses-and-io/system-interconnects.md` | `## Related Pages`: backfill 9 (the spec names this page as the one that mentions PCIe without the enumeration model). |
| `docs/computer-science/buses-and-io/io-and-interrupts.md` | `## Related Pages`: backfill 11 and `linux/device-drivers-and-hardware/interrupts-in-drivers`. |
| `docs/computer-science/buses-and-io/interrupt-controllers.md` | `## Related Pages`: backfill 9 (MSI/MSI-X is a PCIe write). |
| `docs/computer-science/memory-hierarchy/tlb-and-address-translation-hardware.md` | `## Related Pages`: backfill 5 (EPT/NPT as a two-dimensional walk) and backfill 11 (the IOMMU as a TLB for devices). |
| `docs/computer-science/operating-systems/intro.md` | New bullet for backfill 18. |
| `docs/computer-science/operating-systems/os-structure-monolithic-microkernel-hybrid.md` | `## Related Pages`: backfill 18. |
| `docs/computer-science/operating-systems/processes-and-threads.md` | `## Related Pages`: `linux/containers-and-virtualization/what-a-container-actually-is`. |

**Modified (existing section pages — forward links now resolvable, Task 20)**

The Step 1 grep in Task 20 is the authority. Planning located these:
- `00-overview/roadmap.md`
- `03-boot-and-init/systemd-the-model.md`
- `03-boot-and-init/systemd-in-practice-and-boot-debugging.md`
- `06-processes-and-threads/threads-are-tasks.md`
- `06-processes-and-threads/credentials-and-identity.md`
- `07-scheduling/cgroup-cpu-control.md`
- `08-memory-management/vmalloc-and-choosing-an-allocator.md`
- `11-vfs-and-filesystems/overlayfs.md`
- `12-block-layer-and-storage/nvme-in-the-kernel.md`
- `02-guided-traces/the-life-of-a-container.md` (namespaces, cgroups, capabilities and seccomp — deliberately left unlinked in Phase 3)

**Modified (section overview pages)**
- `00-overview/glossary.md`
- `00-overview/misconceptions-index.md`
- `00-overview/roadmap.md`
- `00-overview/what-this-section-covers.md`
- `static/img/linux/SOURCES.md`
- `static/img/cs/SOURCES.md`
- `CLAUDE.md`

**Untouched, deliberately:** everything under `src/`, `tools/scaffold-linux-docs.mjs`, `tools/check-linux-docs.mjs`, `scripts/*.test.mjs`, `docusaurus.config.js` and `sidebars.js`. If a task seems to need a component change, stop. That means the page is fighting the conventions.

---

## Doc-id reference

| Short form | Real doc id prefix |
|---|---|
| `00/…` … `13/…` | as in the Phase 3 plan (`linux/overview/…` through `linux/networking-stack/…`) |
| `01/…` | `linux/lab-and-toolchain/…` |
| `03/…` | `linux/boot-and-init/…` |
| `14/…` | `linux/device-drivers-and-hardware/…` |
| `15/…` | `linux/containers-and-virtualization/…` |
| `16/…` | `linux/security/…` |
| `cs:…` | `computer-science/…` |

Relative *links* keep the numeric prefix, because they are file paths: `../16-security/seccomp.md`. CS backfill pages go in `prerequisites` where the Linux page genuinely depends on them.

## Page brief format

The format is unchanged from Phase 3. Each page gets:
- **Opens with**
- **Sections**
- **Anchor**
- **KernelFacts** (`structure`, `path`, `observe`, `trap`)
- **References** — leads only; open every URL before citing it.

Markers:
- `[WAH]` — the page carries `## What actually happens`.
- `[Lab host=…]` — a `<Lab>` with **measured** expected output and an "if it fails" line.
- `[Misc]` — the page carries `## Misconceptions`.
- `[arm64]` — the page carries a required arm64 contrast `:::note`.

**QEMU environments are folder 01's, never new ones:**
- **Initramfs labs** (module loading, the character driver, driver debugging) use `01/booting-your-kernel-in-qemu`, with the module built against the lab kernel's build tree from `01/building-a-kernel`.
- **Labs needing systemd, cgroup delegation, package-installed tools, or a writable root** (containers, cgroups, SELinux, AppArmor, `lspci`, audit) use the Debian VM from `01/a-full-system-vm-and-wsl2`.

---

## Task 1: Extend the manifest and scaffold folders 14–16

**Files:**
- Modify: `tools/linux-docs-manifest.json`
- Create (by running the scaffolder): 37 stub pages, 3 `_category_.json` files, 4 CS backfill stubs

**Interfaces:**
- Consumes: the manifest schema (`folders[]` with `dir`, `label`, `position`, `description`, `roadmapLink`, `pages[]`; page objects with `file`, `id`, `title`, `sidebar_label`, `sidebar_position`, `tags`, `prerequisites`, optional `related`, `summary`; `external[]` with `path`, `id`, `title`, `sidebar_label`, `sidebar_position`, `tags`, `summary`).
- Produces: every doc id later tasks link to. **No later task starts until the build is green.**

- [ ] **Step 0: Confirm the base**

Run: `ls docs/linux && node -e "const m=require('./tools/linux-docs-manifest.json'); console.log(m.folders.length, m.folders.reduce((n,f)=>n+f.pages.length,0), m.external.length)"`
Expected: folders `00`–`13` plus `readme.md`, and `14 158 14`.

- [ ] **Step 1: Append three folder objects**, each with `"roadmapLink": "../00-overview/roadmap.md"`:

| dir | label | position | description |
|---|---|---|---|
| `14-device-drivers-and-hardware` | Device Drivers | 15 | How the kernel finds hardware and binds code to it: the device model, platform and PCI devices, MMIO, the DMA API, interrupts in drivers, character devices, the interfaces drivers expose, firmware and hotplug, power management, and debugging a driver. |
| `15-containers-and-virtualization` | Containers and Virtualization | 16 | There is no container object in the kernel: namespaces, cgroup v2, capabilities, and a root filesystem assembled by user space — built by hand, then compared with what runc does. Plus KVM and virtio, the kernel as a hypervisor. |
| `16-security` | The Security Model | 17 | Every layer between "may this process do that?" and the answer: permission bits, credentials, capabilities, the LSM framework, SELinux and AppArmor, seccomp, keyrings, integrity, kernel hardening, the recurring vulnerability classes, and auditing. Defensive throughout. |

Tags: `14` → `["linux", "kernel", "drivers"]`, `15` → `["linux", "kernel", "containers"]`, `16` → `["linux", "kernel", "security"]`.

- [ ] **Step 2: Folder 14's thirteen pages** (`sidebar_position` = row number; short-form prerequisites)

| # | file / id | title | sidebar_label | prerequisites | summary |
|---|---|---|---|---|---|
| 1 | `the-linux-device-model` | The Linux Device Model | The device model | `04/kobjects-sysfs-and-the-object-model`, `04/modules-in-practice` | Buses, devices, drivers and classes, the matching that binds them, probe and remove as the driver lifecycle, and `/sys` as the model made visible. |
| 2 | `platform-devices-and-description` | Platform Devices, Device Tree, and ACPI | Platform devices | `14/the-linux-device-model` | Hardware that cannot be enumerated must be described: device tree on arm64 and embedded, ACPI on x86-64, platform devices over both. |
| 3 | `pci-and-pcie-drivers` | PCI and PCIe Drivers | PCI drivers | `14/the-linux-device-model`, `cs:buses-and-io/pcie-in-depth` | The ID table, config space, BARs, `pci_enable_device` and `pci_iomap`, bus mastering, and `lspci -vvv` read against a driver. |
| 4 | `mmio-and-port-io` | MMIO, `ioremap`, and Accessors | MMIO and accessors | `14/pci-and-pcie-drivers`, `09/memory-ordering-and-barriers` | Why a driver never dereferences a device pointer: `ioremap`, `readl`/`writel` and their ordering, `__iomem`, relaxed accessors, and port I/O. |
| 5 | `the-dma-api` | The DMA API | The DMA API | `14/mmio-and-port-io`, `cs:buses-and-io/dma-and-iommu`, `08/the-page-allocator` | Device addresses versus physical versus virtual, coherent and streaming mappings, ownership handoff, bounce buffers, and the IOMMU. |
| 6 | `interrupts-in-drivers` | Interrupts in a Driver | Driver interrupts | `14/pci-and-pcie-drivers`, `10/threaded-irqs` | Requesting a line, MSI and MSI-X vectors, the shared-line contract, threaded handlers, and per-queue interrupts. |
| 7 | `character-devices` | Character Devices | Character devices | `14/the-linux-device-model`, `11/the-four-objects` | `cdev`, device numbers, `file_operations`, the misc-device shortcut, and how `/dev` nodes appear. |
| 8 | `lab-a-character-driver` | Lab: Write a Character Driver | Lab: a char driver | `14/character-devices`, `05/copying-data-across-the-boundary`, `01/booting-your-kernel-in-qemu` | A complete out-of-tree misc driver with `read`, `write` and `ioctl`, loaded in the QEMU lab, exercised from C, traced, and unloaded cleanly. |
| 9 | `talking-to-user-space` | Talking to User Space | User-space interfaces | `14/character-devices` | `ioctl`, sysfs, debugfs, netlink, `read`/`poll`, `mmap`, and uio/vfio — and how to choose between them. |
| 10 | `block-and-network-driver-shapes` | Block and Network Driver Shapes | Block and net drivers | `14/the-linux-device-model`, `12/blk-mq`, `13/the-receive-path` | How a blk-mq `queue_rq` driver and a `net_device_ops`-plus-NAPI driver differ from a character driver — enough to read either. |
| 11 | `firmware-udev-and-hotplug` | Firmware, udev, and Hotplug | Firmware and udev | `14/the-linux-device-model` | `request_firmware`, uevents, udev rules and device naming, and the coldplug/hotplug distinction. |
| 12 | `power-management` | Power Management | Power management | `14/the-linux-device-model`, `14/interrupts-in-drivers` | System suspend states and callbacks, runtime PM and autosuspend, wakeup sources, and diagnosing a machine that will not sleep. |
| 13 | `debugging-drivers` | Debugging Drivers | Debugging drivers | `14/lab-a-character-driver`, `04/memory-safety-in-kernel-c` | Dynamic debug, `ftrace` scoped to a module, a probe that never fires, debugfs, reading an oops back to a driver line, and the five common driver bugs. |

Extra `related`:
- Page 1: `["linux/vfs-and-filesystems/procfs-sysfs-debugfs-configfs", "linux/kernel-architecture-and-idioms/reference-counting-and-lifetime"]`
- Page 3: `["computer-science/buses-and-io/system-interconnects"]`
- Page 5: `["linux/memory-management/vmalloc-and-choosing-an-allocator"]`
- Page 6: `["linux/interrupts-time-and-deferred-work/interrupt-affinity-and-balancing", "computer-science/buses-and-io/interrupt-controllers"]`
- Page 10: `["linux/block-layer-and-storage/nvme-in-the-kernel"]`
- Page 11: `["linux/boot-and-init/initramfs-and-early-userspace"]`
- Page 13: `["linux/lab-and-toolchain/debugging-the-kernel-with-gdb"]`

- [ ] **Step 3: Folder 15's twelve pages**

| # | file / id | title | sidebar_label | prerequisites | summary |
|---|---|---|---|---|---|
| 1 | `what-a-container-actually-is` | What a Container Actually Is | What a container is | `06/threads-are-tasks`, `cs:operating-systems/virtualization-and-isolation` | There is no container object: a process with namespaces, a cgroup, a root filesystem, a capability set and a seccomp filter, assembled by user space. |
| 2 | `namespaces-overview` | Namespaces | Namespaces | `15/what-a-container-actually-is`, `06/task-struct-the-anatomy-of-a-task` | All eight namespaces, what each virtualises, `clone`/`unshare`/`setns`, and `/proc/PID/ns` as the handle. |
| 3 | `mount-and-pid-namespaces` | Mount and PID Namespaces | Mount and PID ns | `15/namespaces-overview`, `11/mounts-and-mount-namespaces`, `06/exit-zombies-and-orphans` | Propagation from the container angle, nested PID numbering, and why a container's PID 1 must reap orphans. |
| 4 | `user-namespaces` | User Namespaces | User namespaces | `15/namespaces-overview`, `06/credentials-and-identity` | UID/GID maps, root inside versus root outside, namespaced capabilities, rootless containers, and the attack-surface trade-off. |
| 5 | `cgroup-v2-architecture` | cgroup v2 | cgroup v2 | `15/what-a-container-actually-is`, `11/procfs-sysfs-debugfs-configfs` | The unified hierarchy, the no-internal-process rule, controller enablement, delegation, and systemd as the hierarchy's owner. |
| 6 | `cgroup-controllers-in-practice` | cgroup Controllers in Practice | cgroup controllers | `15/cgroup-v2-architecture`, `07/cgroup-cpu-control`, `08/reclaim-lru-and-kswapd` | `cpu`, `memory`, `io`, `pids` and `cpuset` — the files that matter, `memory.high` versus `memory.max`, and PSI. |
| 7 | `capabilities-in-containers` | Capabilities and Container Privilege | Container privilege | `15/user-namespaces`, `16/capabilities` | The default drop set, what `--privileged` turns off, `no_new_privs`, and the capabilities that are root in practice. |
| 8 | `building-a-container-from-scratch` | Lab: Build a Container from Scratch | Lab: a container | `15/mount-and-pid-namespaces`, `15/user-namespaces`, `15/cgroup-v2-architecture`, `13/network-namespaces-and-virtual-devices` | About 150 lines of C and shell: namespaces, `pivot_root`, `/proc`, a cgroup limit, dropped capabilities, a seccomp filter, a veth pair, then `exec`. |
| 9 | `images-layers-and-oci` | Images, Layers, and the OCI Runtime | Images and OCI | `15/building-a-container-from-scratch`, `11/overlayfs` | Layers as overlayfs lowerdirs, the OCI image and runtime specs, what runc does with a bundle, and where containerd, Docker and Podman sit. |
| 10 | `container-networking` | Container Networking | Container networking | `15/namespaces-overview`, `13/network-namespaces-and-virtual-devices`, `13/connection-tracking-and-nat` | Bridge-and-NAT built by hand, port publishing, CNI in one section, and why cross-host traffic needs an overlay. |
| 11 | `kvm-and-hardware-virtualization` | KVM | KVM | `cs:cpu-architecture/hardware-virtualization`, `15/what-a-container-actually-is`, `14/talking-to-user-space` | The kernel as a hypervisor: `/dev/kvm`, VM and vCPU file descriptors, the run loop, VM exits, EPT/NPT, and where QEMU fits. |
| 12 | `virtio-and-paravirtualization` | virtio and Paravirtual Devices | virtio | `15/kvm-and-hardware-virtualization`, `14/the-dma-api` | Why emulated hardware is slow, virtqueues, virtio-net/blk/fs, and vhost moving the datapath into the kernel. |

Extra `related`:
- Page 1: `["linux/guided-traces/the-life-of-a-container", "computer-science/operating-systems/virtualization-and-isolation"]`
- Page 7: `["linux/security/seccomp"]`
- Page 8: `["linux/security/seccomp"]`
- Page 12: `["linux/lab-and-toolchain/booting-your-kernel-in-qemu"]`

**Cycle check before writing it:** `15/capabilities-in-containers` → `16/capabilities` is a cross-folder edge. Confirm that no folder-16 page lists a folder-15 page in `prerequisites` (Step 4's table does not), so no cycle is possible.

- [ ] **Step 4: Folder 16's twelve pages**

| # | file / id | title | sidebar_label | prerequisites | summary |
|---|---|---|---|---|---|
| 1 | `the-unix-permission-model` | The UNIX Permission Model | Permissions | `11/the-four-objects`, `06/credentials-and-identity` | Mode bits and the check order, what `x` on a directory controls, setuid/setgid/sticky, umask, and POSIX ACLs. |
| 2 | `credentials-in-the-kernel` | Credentials in the Kernel | Credentials | `16/the-unix-permission-model`, `09/rcu-in-practice` | `struct cred` in detail, real/effective/saved/filesystem IDs, privilege-drop mistakes, and RCU credential replacement. |
| 3 | `capabilities` | Capabilities | Capabilities | `16/credentials-in-the-kernel` | Root split into about forty pieces: the five sets and their transition rules, file capabilities, and which capabilities are root-equivalent. |
| 4 | `the-lsm-framework` | The LSM Framework | LSM framework | `16/capabilities` | Hooks at every security decision, restrict-only, stacking, and how a policy decision reaches a hook. |
| 5 | `selinux` | SELinux | SELinux | `16/the-lsm-framework` | Type enforcement, contexts and labels, policy and booleans, modes, and reading an AVC denial to a fix. |
| 6 | `apparmor` | AppArmor | AppArmor | `16/the-lsm-framework` | Path-based profiles, profile syntax, complain versus enforce, and an honest comparison with SELinux. |
| 7 | `seccomp` | seccomp and Syscall Filtering | seccomp | `16/capabilities`, `05/the-syscall-table-and-dispatch` | Strict mode, seccomp-BPF and the architecture check, `no_new_privs`, user notification, and runtime default profiles. |
| 8 | `keyrings` | Keyrings | Keyrings | `16/credentials-in-the-kernel` | Kernel-managed secrets: key types, the keyring hierarchy and search order, and dm-crypt, NFS and module signing as users. |
| 9 | `integrity-and-signing` | Integrity: IMA, EVM, and Module Signing | Integrity | `16/keyrings`, `03/secure-boot-and-signed-kernels` | Measurement versus appraisal, IMA policy, EVM, module signature enforcement, and the chain to Secure Boot. |
| 10 | `kernel-hardening` | Kernel Hardening | Hardening | `16/the-lsm-framework`, `08/page-tables-and-the-walk` | KASLR, SMEP/SMAP, KPTI, stack protector, `FORTIFY_SOURCE`, lockdown, and the dmesg/kptr restrictions — what each defeats and costs. |
| 11 | `vulnerability-classes` | Vulnerability Classes in the Kernel | Vulnerability classes | `16/kernel-hardening`, `04/memory-safety-in-kernel-c`, `05/copying-data-across-the-boundary` | Use-after-free, refcount overflow, user-pointer TOCTOU, size-arithmetic overflow, stack disclosure, and transient execution — for recognition and defence. |
| 12 | `auditing-and-security-observability` | Auditing and Security Observability | Auditing | `16/the-lsm-framework` | The audit subsystem, rules and records, `ausearch`, LSM audit output, and BPF-LSM — what to log and what it costs. |

Extra `related`:
- Page 2: `["linux/processes-and-threads/credentials-and-identity"]`
- Page 3: `["linux/containers-and-virtualization/capabilities-in-containers"]`
- Page 7: `["linux/containers-and-virtualization/building-a-container-from-scratch", "linux/syscalls-and-the-boundary/tracing-and-intercepting-syscalls"]`
- Page 10: `["computer-science/cpu-architecture/privilege-levels-and-protection", "linux/memory-management/tlb-and-address-space-switching"]`
- Page 11: `["linux/kernel-architecture-and-idioms/reference-counting-and-lifetime"]`

`related` edges into folder 15 are fine. `buildGraph.js` cycle-checks only `prerequisites`, and its own error message suggests demoting an edge to `related` to break a loop.

- [ ] **Step 5: Four CS backfill entries in `manifest.external`.** Re-check each folder's positions first (planning saw `cpu-architecture/` 1–10, `buses-and-io/` 1–6, `operating-systems/` 1–7). If a position collides, take the next free integer.

| path | id | title | sidebar_label | position | tags | summary |
|---|---|---|---|---|---|---|
| `docs/computer-science/cpu-architecture/hardware-virtualization.md` | `hardware-virtualization` | Hardware Virtualization | Hardware virtualization | 11 | `["computer-science", "cpu-architecture", "virtualization"]` | Why x86 was not classically virtualizable, VT-x/AMD-V root and non-root modes, VM entry and exit, EPT/NPT, and why an exit is expensive. |
| `docs/computer-science/buses-and-io/pcie-in-depth.md` | `pcie-in-depth` | PCIe in Depth | PCIe in depth | 7 | `["computer-science", "buses-and-io", "pcie"]` | The PCIe link and topology, configuration space, BARs, enumeration, and MSI/MSI-X as memory writes. |
| `docs/computer-science/buses-and-io/dma-and-iommu.md` | `dma-and-iommu` | DMA and the IOMMU | DMA and IOMMU | 8 | `["computer-science", "buses-and-io", "dma"]` | Bus-master DMA, scatter-gather, cache coherency with devices, and the IOMMU as address translation and isolation for devices. |
| `docs/computer-science/operating-systems/virtualization-and-isolation.md` | `virtualization-and-isolation` | Virtualization and Isolation | Isolation | 8 | `["computer-science", "operating-systems", "isolation"]` | VMs, containers and sandboxes as isolation theory: what each shares, where each boundary is enforced, and how wide the attack surface is. |

- [ ] **Step 6: Validate.** Run the Step 0 `node -e` command. Expected: `17 195 18`.

- [ ] **Step 7: Scaffold.** Run: `npm run scaffold:linux`. Expected: `scaffold: 41 file(s) created, 172 left alone, 17 category file(s) written`. If any existing page is reported as created, stop and restore it from git.

- [ ] **Step 8: Confirm nothing was clobbered**

```bash
git status --short docs/linux docs/computer-science
git diff --stat -- docs/linux docs/computer-science
```

Expected: only new untracked files, and an empty `diff --stat`.

- [ ] **Step 9: Gates**

```bash
npm run check:linux
npm run test:graph
npm run build
```

Expected: `check-linux-docs: OK — 159 written page(s), 37 stub(s)`, passing graph tests, and a green build. A failure is almost always a prerequisite id typo, such as a leftover `NN-` or an unexpanded `cs:`.

- [ ] **Step 10: Eyeball.** Run `npm run start`. Check that seventeen folders appear in order and that the new index pages carry their descriptions. Check that `15/kvm-and-hardware-virtualization`'s `<PrereqBlock>` shows a `CS`-badged chip. Then stop the server.

- [ ] **Step 11: Commit**

```bash
git add tools/linux-docs-manifest.json docs/linux docs/computer-science
git commit -m "docs: scaffold linux folders 14-16 and the phase 4 CS backfill stubs"
```

---
## Task 2: CS backfill 9 and 11 — PCIe in depth, and DMA and the IOMMU — with buses-and-io backlinks

**Files:**
- Modify (stub → written):
  - `docs/computer-science/buses-and-io/pcie-in-depth.md`
  - `docs/computer-science/buses-and-io/dma-and-iommu.md`
- Modify (backlinks):
  - `docs/computer-science/buses-and-io/intro.md`
  - `docs/computer-science/buses-and-io/system-interconnects.md`
  - `docs/computer-science/buses-and-io/io-and-interrupts.md`
  - `docs/computer-science/buses-and-io/interrupt-controllers.md`
  - `docs/computer-science/memory-hierarchy/tlb-and-address-translation-hardware.md` (the backfill-11 row only; Task 3 adds backfill 5)

**Interfaces:**
- Produces:
  - `computer-science/buses-and-io/pcie-in-depth` — a prerequisite of `14/pci-and-pcie-drivers`;
  - `computer-science/buses-and-io/dma-and-iommu` — a prerequisite of `14/the-dma-api`.

  **The spec says both gate folder 14.** No folder-14 writing task starts until this task is committed.

These are `computer-science/` pages. They carry no `prerequisites` key, no `<KernelFacts>`, no `<Src>`, and **no Linux API**: `pci_*`, `dma_map_*` and `iommu_*` belong to folder 14. They follow the structure of the **backfill pages already in this folder**, not the older topic pages. Open `buses-and-io/interrupt-controllers.md` (a Phase 2 backfill) and match it:
- an H1 and a lead;
- topic `##` sections;
- `## Comparison`;
- `## Where this goes next` (which is where the Linux link goes);
- `## References`.

Delete the `:::info[Not yet written]` block.

### `pcie-in-depth.md` — PCIe in Depth

- **Lead:** PCIe looks like a bus to software and is a packet-switched network in hardware. Software still sees PCI's model from 1992: a tree of functions, each with a configuration space that says what it is and which address windows it wants. The links underneath became serial, point-to-point and packetised. The rest of the page explains how that compatibility trick works and what an OS has to do at boot to make a device usable.
- **Sections:**
  - `## From a shared bus to point-to-point links` — lanes, link widths (x1–x16), generations as per-lane rate, and the transaction/data-link/physical layering as TLPs. Give one paragraph and a table of generations with per-lane throughput. Take the figures from PCI-SIG's published specifications summary.
  - `## Topology: root complex, switches, endpoints` — bus/device/function addressing (BDF), bridges creating secondary buses, and the tree as software sees it.
  - `## Configuration space` — 256 bytes of legacy space plus 4 KiB of extended space, reached through ECAM (memory-mapped configuration). Cover the header fields that matter: vendor/device ID, class code, command/status, header type, the BARs, and the capability list as a linked list of structures.
  - `## BARs and resource assignment` — the write-all-ones-and-read-back sizing trick, memory versus I/O BARs, 64-bit and prefetchable flags, and firmware or the OS assigning addresses.
  - `## Enumeration` — the depth-first walk that assigns bus numbers and discovers functions; hotplug as enumeration that happens later.
  - `## MSI and MSI-X: interrupts as memory writes` — an interrupt is a posted write to an address the interrupt controller decodes. Contrast MSI (up to 32 vectors, contiguous) with MSI-X (up to 2048, a table in a BAR). Link to `./interrupt-controllers.md`, which already owns the controller side; do not repeat it.
  - `## Comparison` — a table of legacy PCI, PCI-X and PCIe on signalling, topology, interrupts and config access.
  - `## Where this goes next` — `../../linux/14-device-drivers-and-hardware/pci-and-pcie-drivers.md`.
- **Anchor:** a WaveDrom `reg` for the type-0 configuration header's first 16 bytes (vendor ID, device ID, command, status, revision, class code, cache line, latency, header type, BIST), plus a Mermaid `flowchart TB` topology (CPU → root complex → switch → endpoints, with BDFs labelled).
- **References:**
  - The PCI-SIG specifications page, for the generation table only (the specifications themselves are paywalled — say so);
  - *PCI Express System Architecture* (Budruk, Anderson, Shanley; MindShare) — the standard long-form text; note that it predates Gen 4+;
  - the OSDev wiki "PCI" and "PCI Express" pages — the configuration mechanism with register tables;
  - `https://docs.kernel.org/PCI/pci.html` — appropriate as a "see it used" pointer, annotated as such.

### `dma-and-iommu.md` — DMA and the IOMMU

- **Lead:** a device that can write to memory by itself is fast and dangerous. It is fast because the CPU stops copying bytes, and dangerous because the device writes to whatever address it is given. That address is not a virtual address the CPU would recognise and may not even be a physical one. This page covers the hardware side of that trade: how bus-master DMA works, why caches make it subtle, and how an IOMMU puts a page table in front of every device.
- **Sections:**
  - `## Programmed I/O versus bus-master DMA` — the CPU moving every byte versus the device mastering the bus, and a descriptor ring as the usual interface (state that ring formats are device-specific).
  - `## Scatter-gather` — physically discontiguous buffers described as a list, and why that matters when memory is fragmented.
  - `## Three kinds of address` — CPU virtual, CPU physical, and bus/device (IOVA). Before IOMMUs, device address equalled physical address on most x86 systems. Address-width limits (32-bit devices) forced bounce buffers.
  - `## Caches and DMA` — the coherency problem. A device writes RAM while a stale line sits in the CPU cache, or the CPU's dirty line has not reached RAM when the device reads. Coherent interconnects snoop and solve it in hardware (typical on x86-64). Non-coherent systems (many arm64 SoCs) need explicit clean/invalidate operations around every transfer. Name the architecture on each claim. Link to `../memory-hierarchy/cache-coherence-and-mesi.md`.
  - `## The IOMMU: a page table for devices` — device-originated addresses translated through per-device or per-domain tables, with IOTLBs and their invalidation cost. Name Intel VT-d, AMD-Vi and the Arm SMMU. Cover the two jobs: **translation** (contiguous IOVA over scattered pages, and removing the 32-bit limit) and **isolation** (a device can only reach what is mapped for it, which is the DMA-attack defence and the basis of device passthrough to VMs).
  - `## The cost` — mapping and unmapping on every I/O, IOTLB misses, and the strict versus deferred (batched) invalidation trade-off as a general concept.
  - `## Comparison` — a table: no IOMMU / IOMMU in passthrough / IOMMU translating × isolation, bounce buffers needed, and per-I/O cost.
  - `## Where this goes next` — `../../linux/14-device-drivers-and-hardware/the-dma-api.md`.
- **Anchor:** a Mermaid `sequenceDiagram` of one streaming DMA receive on a non-coherent system:
  1. CPU invalidates the buffer's cache lines;
  2. CPU hands the device the IOVA;
  3. device writes through the IOMMU;
  4. the IOMMU translates and checks;
  5. the device raises an interrupt;
  6. the CPU reads the buffer.

  Plus a `flowchart LR` contrasting a device's path to RAM with and without an IOMMU.
- **References:**
  - Intel *Virtualization Technology for Directed I/O* architecture specification (public PDF) — the DMA remapping chapter;
  - the Arm SMMU architecture overview from Arm's developer site;
  - Markuze, Morrison & Tsafrir, "True IOMMU Protection from DMA Attacks" (ASPLOS 2016) — why per-I/O mapping still leaves windows;
  - *Operating Systems: Three Easy Pieces*, the I/O devices chapter — the PIO-versus-DMA basics.

- [ ] **Step 1: Read `interrupt-controllers.md` and `atomic-operations-in-hardware.md`** for this folder's backfill template and voice.
- [ ] **Step 2: Write `pcie-in-depth.md`** to the brief. Check the config-header offsets against the OSDev table before drawing the WaveDrom strip.
- [ ] **Step 3: Write `dma-and-iommu.md`** to the brief.
- [ ] **Step 4: Backlinks.**
  - In `buses-and-io/intro.md`, add one bullet per page in the existing list style.
  - In `system-interconnects.md`, `io-and-interrupts.md` and `interrupt-controllers.md`, add one line each in their closing link section (`## Related Pages` or `## Where this goes next`, whichever the page uses), as listed in File Structure.
  - In `tlb-and-address-translation-hardware.md`, add the backfill-11 line ("the IOMMU is a TLB for devices").
- [ ] **Step 5: Confirm no Linux API leaked in.** Run: `rtk run "grep -n -E 'pci_|dma_map|iommu_|dma_alloc|<Src' docs/computer-science/buses-and-io/pcie-in-depth.md docs/computer-science/buses-and-io/dma-and-iommu.md"`. Expected: no output.
- [ ] **Step 6: Build and commit**

```bash
npm run build
git add docs/computer-science
git commit -m "docs: write CS backfill pages on PCIe and on DMA and the IOMMU"
```

---

## Task 3: CS backfill 5 and 18 — hardware virtualization, and isolation theory — with backlinks

**Files:**
- Modify (stub → written):
  - `docs/computer-science/cpu-architecture/hardware-virtualization.md`
  - `docs/computer-science/operating-systems/virtualization-and-isolation.md`
- Modify (backlinks):
  - `cpu-architecture/intro.md`
  - `cpu-architecture/privilege-levels-and-protection.md`
  - `memory-hierarchy/tlb-and-address-translation-hardware.md` (the backfill-5 line)
  - `operating-systems/intro.md`
  - `operating-systems/os-structure-monolithic-microkernel-hybrid.md`
  - `operating-systems/processes-and-threads.md`

**Interfaces:**
- Produces:
  - `computer-science/cpu-architecture/hardware-virtualization` — a prerequisite of `15/kvm-and-hardware-virtualization`;
  - `computer-science/operating-systems/virtualization-and-isolation` — a prerequisite of `15/what-a-container-actually-is`.

The template rule is the same as Task 2: match the Phase 1–2 backfill pages in each folder (`privilege-levels-and-protection.md`, `os-structure-monolithic-microkernel-hybrid.md`). No Linux mechanism: no KVM ioctls, no namespaces by name beyond one "Linux implements this as…" sentence in `## Where this goes next`.

### `hardware-virtualization.md` — Hardware Virtualization

- **Lead:** a virtual machine is a guest kernel that believes it owns privileged hardware. Running one fast means letting it run directly on the CPU most of the time, and catching it the moment it does something only the real owner may do. Popek and Goldberg stated in 1974 when that is possible. x86 failed their test for thirty years, and VT-x and AMD-V are the hardware fix.
- **Sections:**
  - `## Trap-and-emulate, and the Popek–Goldberg condition` — sensitive versus privileged instructions, and the classic x86 counterexamples (`POPF` silently dropping the interrupt flag in ring 3, `SGDT`). Then the pre-hardware workarounds in one paragraph each: binary translation (VMware) and paravirtualization (Xen).
  - `## A new axis: root and non-root mode` — VMX root/non-root (Intel) and host/guest (AMD SVM) as orthogonal to rings, so a guest kernel runs in ring 0 non-root. Link back to `./privilege-levels-and-protection.md`.
  - `## VM entry and VM exit` — the VMCS (Intel) and VMCB (AMD) as the saved state of both worlds. Exits are configured per cause: I/O, `CPUID`, control-register writes, external interrupts, EPT violations. `VMLAUNCH`/`VMRESUME` and `VMRUN`.
  - `## Why an exit is expensive` — a full world switch of state, plus the handler's work. Give the cost as an order-of-magnitude range from a cited source rather than a single number. Exits dominate virtualization overhead, which is why later hardware features exist mainly to avoid them: posted interrupts, APICv/AVIC.
  - `## Memory: shadow page tables and EPT/NPT` — the guest's virtual→guest-physical tables composed with the host's guest-physical→host-physical tables, giving the two-dimensional walk. The worst case is up to 24 memory references for a 4-level/4-level walk (derive it on the page: (4+1)×(4+1)−1), and that is why TLBs and page-walk caches matter more under virtualization. Link to `../memory-hierarchy/tlb-and-address-translation-hardware.md`.
  - `## I/O: emulated, paravirtual, passthrough` — three answers, with the IOMMU as the enabler of passthrough. Link to `../buses-and-io/dma-and-iommu.md`.
  - `## arm64's model, briefly` — EL2 as a dedicated hypervisor exception level, and VHE letting a host kernel run at EL2. One section, since the contrast is structural.
  - `## Where this goes next` — `../../linux/15-containers-and-virtualization/kvm-and-hardware-virtualization.md`.
- **Anchor:** a Mermaid `stateDiagram-v2` (host root mode ↔ guest non-root mode, with VM entry and exits labelled by cause), plus a table of exit causes × typical frequency class × what the hypervisor must do.
- **References:**
  - Popek & Goldberg, "Formal Requirements for Virtualizable Third Generation Architectures" (CACM 1974);
  - Adams & Agesen, "A Comparison of Software and Hardware Techniques for x86 Virtualization" (ASPLOS 2006) — the honest early numbers;
  - the Intel SDM vol. 3C, VMX chapters;
  - Bhargava et al., "Accelerating Two-Dimensional Page Walks for Virtualized Systems" (ASPLOS 2008) — the 2D-walk cost.

### `virtualization-and-isolation.md` — Virtualization and Isolation

- **Lead:** "isolated" is not one property. A VM, a container and a sandbox each draw a boundary in a different place. The useful questions are: what do the two sides still share? Who enforces the boundary? How much code sits on the trusted side of it? This page owns that theory, and the Linux folders own the mechanisms.
- **Sections:**
  - `## Three boundaries` — machine-level (hypervisor: separate kernels, shared hardware), OS-level (containers: one kernel, partitioned *views* of its resources), and process/language-level (sandboxes: a restricted interface to one kernel, as in seccomp-style filtering, capability systems and WebAssembly).
  - `## What is shared, and why it matters` — the shared kernel is the container's defining weakness: a kernel bug is a container escape. The shared CPU is everyone's: microarchitectural side channels cross every boundary on this page.
  - `## Attack surface as a measurable quantity` — the size of the interface the untrusted side can reach: a few dozen hypercalls/VM-exit kinds versus ~350 syscalls versus a filtered subset of them. Interface size is not the same as bug count, so present it as an argument, not a proof.
  - `## Resource isolation versus security isolation` — quotas and fair share (performance isolation) versus confidentiality and integrity. A cgroup is the first; a namespace contributes to neither on its own.
  - `## The hybrid answers` — microVMs (Firecracker), sandboxed kernels (gVisor), and Kata Containers: each moves the container boundary toward the VM boundary. Describe what each puts on the trusted side; no benchmarks.
  - `## Comparison` — a table of VM / container / gVisor-style / microVM / seccomp sandbox × shared component, enforcement point, startup cost class, density class, and escape requires.
  - `## Where this goes next` — `../../linux/15-containers-and-virtualization/what-a-container-actually-is.md` and `../../linux/15-containers-and-virtualization/kvm-and-hardware-virtualization.md`.
- **Anchor:** a Mermaid `flowchart TB` with three stacked columns (VM, container, sandbox), each showing hardware → [hypervisor] → kernel(s) → workload, with the trust boundary drawn as a dashed subgraph edge.
- **References:**
  - Agache et al., "Firecracker: Lightweight Virtualization for Serverless Applications" (NSDI 2020);
  - the gVisor architecture guide (gvisor.dev);
  - Saltzer & Schroeder, "The Protection of Information in Computer Systems" (1975) — least privilege and economy of mechanism, the vocabulary this page uses;
  - *Operating Systems: Three Easy Pieces*, the virtualization appendix on VMMs.

- [ ] **Step 1: Read `privilege-levels-and-protection.md` and `os-structure-monolithic-microkernel-hybrid.md`** for the folders' backfill template.
- [ ] **Step 2: Write `hardware-virtualization.md`.** Derive the 24-reference figure on the page; do not merely assert it.
- [ ] **Step 3: Write `virtualization-and-isolation.md`.**
- [ ] **Step 4: Backlinks**, as listed in File Structure, in each page's existing closing-link style.
- [ ] **Step 5: Leak check.** Run: `rtk run "grep -n -E 'KVM_|/dev/kvm|unshare|CLONE_NEW|<Src' docs/computer-science/cpu-architecture/hardware-virtualization.md docs/computer-science/operating-systems/virtualization-and-isolation.md"`. Expected: no output.
- [ ] **Step 6: Build and commit**

```bash
npm run build
git add docs/computer-science
git commit -m "docs: write CS backfill pages on hardware virtualization and isolation"
```

---
## Writing-task procedure (applies to Tasks 4–19)

Each writing task lists its pages' briefs and then runs these steps. They are written once here instead of repeated in every task.

- [ ] **Write each page to its brief**, in the listed order. Delete the `:::info[Not yet written]` block and keep the scaffolded front matter.
- [ ] **Run every `<Lab>` and every `## What actually happens` session in the named environment before writing it up.** Paste real output, trimmed with `…` but never edited. Record the kernel version (`uname -r`) that produced it in a comment next to the block.
- [ ] **context7 check** where the task names one. Resolve the library id, query it, and add "(checked against <source> via context7, YYYY-MM-DD)" to the relevant `## References` annotation. If context7 has no entry, say so and cite `docs.kernel.org` or the man page.
- [ ] **Verify every symbol, field, path, config option, ioctl and interface file** on the pages at `https://elixir.bootlin.com/linux/v6.18/ident/<symbol>` or `/source/<path>`. The task's verification list is the minimum.
- [ ] **Gates:** `npm run check:linux && npm run build`. Expected: zero findings and a green build.
- [ ] **Commit** with the task's commit message: `git add docs/linux/<folder> && git commit -m "<message>"`.

---

## Task 4: Folder 14 — the device model, and platform devices

**Interfaces:**
- Consumes: `04/kobjects-sysfs-and-the-object-model`, which already owns kobjects, ksets and refcounted lifetime. This page **uses** that material and never re-explains it.
- Produces: `14/the-linux-device-model` — the spec says it is **written first**. It is the vocabulary of every later folder-14 page: bus, device, driver, class, bind, probe.

### `the-linux-device-model.md` — The Linux Device Model **[WAH]** **[Misc]**

- **Opens with:** a driver never goes looking for its hardware. The kernel keeps two lists per bus, devices that exist and drivers that are loaded, and whenever either list changes it tries to pair them. When a pair matches, the driver's `probe` runs. Everything else in this folder happens inside a `probe` or is undone in a `remove`.
- **Sections:**
  - `## Four objects` — `bus_type`, `device`, `device_driver` and `class`, each in one paragraph, plus how they embed `kobject` (link to folder 04).
  - `## Matching and binding` — `bus_type.match`, ID tables (`of_device_id`, `acpi_device_id`, `pci_device_id`), and `driver_override`. Binding from either side: a device registered, or a driver loaded.
  - `## probe and remove` — the lifecycle contract. `devm_*` resources are released automatically in reverse order (link to `../08-memory-management/vmalloc-and-choosing-an-allocator.md`, which names `devm_*` and promises this folder owns it). Show the error-path benefit with a short ` ```c ` probe sketch.
  - `## Deferred probe` — `-EPROBE_DEFER` when a supplier (clock, regulator, GPIO) is not ready, the retry on every successful bind, `dev_err_probe`, fw_devlink, and `/sys/kernel/debug/devices_deferred`.
  - `## /sys as the model made visible` — `/sys/bus/*/devices`, `/sys/bus/*/drivers`, `/sys/class`, `/sys/devices` as the real hierarchy (everything else is symlinks), and manual `bind`/`unbind`.
  - `## What actually happens` **[WAH]** — on the Debian VM, `echo` a virtio device's BDF to its driver's `unbind` then `bind`, and show the `dmesg` lines and the `/sys` symlinks disappearing and reappearing. Use a virtio device that is **not** the root disk — the virtio-net or the RNG device. Put the cleanup (rebind) inside the same block.
  - `## Misconceptions` — (1) "Drivers scan for their hardware." (2) "Loading a module means its device is in use." It may bind nothing. (3) "`-EPROBE_DEFER` in the log is an error." It is a retry.
- **Anchor:** a `sequenceDiagram` — device registered → `bus_add_device` → `bus_probe_device` → `driver_match_device` → `really_probe` → `drv->probe` → `-EPROBE_DEFER` → deferred list → supplier binds → retry → success → uevent `bind`. Plus a `stateDiagram-v2` of a device's bind states.
- **KernelFacts:**
  - structure: `[["struct device", "include/linux/device.h"], ["struct bus_type", "include/linux/device/bus.h"]]`
  - path: `"device_add() → bus_probe_device() → __device_attach() → driver_match_device() → really_probe() → drv->probe()"`
  - observe: `ls -l /sys/bus/pci/devices/*/driver`
  - trap: "A failed `probe` leaves the device present but unbound, silently, unless the driver logs. `devices_deferred` and `unbound` devices in `/sys` are the first place to look when hardware 'is not detected'."
- **References:** `https://docs.kernel.org/driver-api/driver-model/` (overview, binding, devres) — context7 check; `<Src file="drivers/base/dd.c" symbol="really_probe" />`; *Linux Device Drivers* 3rd ed. ch. 14, annotated as 2.6-era (the concepts hold, the API names do not); the LWN article on fw_devlink.
- **Verify:** `bus_type`, `device_driver`, `really_probe`, `__device_attach`, `driver_match_device`, `dev_err_probe`, `devm_kzalloc`, `driver_override`, `deferred_probe_pending_list`, `fw_devlink`, and the debugfs `devices_deferred` path.

### `platform-devices-and-description.md` — Platform Devices, Device Tree, and ACPI **[arm64]**

- **Opens with:** PCI and USB devices announce themselves. A UART at a fixed address on an SoC does not. Something has to tell the kernel it is there, at which address and on which interrupt: device tree on arm64 and most embedded systems, ACPI tables on x86-64 servers and laptops. Platform devices are the driver-side abstraction that hides which of the two did the telling.
- **Sections:** `## Enumerable versus described hardware`; `## Device tree` (nodes, `compatible`, `reg`, `interrupts`, phandles, and the DTB passed by the bootloader; **link `docs/embedded` device-tree material for depth** — find the real path with `ls docs/embedded/*/`, and if no embedded device-tree page exists yet, name it in prose); `## ACPI` (DSDT/SSDT, `_HID`, `_CRS`, AML as executable firmware, and `/sys/firmware/acpi/tables`); `## The platform bus`; `## One driver, both descriptions` (the `device_property_read_*` unified property API, and `of_match_table` plus `acpi_match_table` on one driver); `## Choosing and reading`.
- **Anchor:** `<Tabs>` with **Device tree** and **ACPI** tabs. Each shows the description of the same imaginary UART (a ` ```text ` DTS node versus an ASL `Device()` excerpt), and a shared table below maps `reg`↔`_CRS`, `compatible`↔`_HID`, and `interrupts`↔`_CRS Interrupt`. This `<Tabs>` *is* the page's arm64 contrast. Add a one-paragraph `:::note[arm64]` saying arm64 servers commonly boot with ACPI (SBSA/SBBR) while arm64 embedded boards use DT.
- **KernelFacts:** structure `[["struct platform_driver", "include/linux/platform_device.h"], ["struct of_device_id", "include/linux/mod_devicetable.h"]]`; path `"platform_driver_register() → driver_register() → platform_match() → of_driver_match_device() | acpi_driver_match_device() → probe()"`; observe `ls /sys/bus/platform/devices; ls /proc/device-tree 2>/dev/null || ls /sys/firmware/acpi/tables`; trap: "A `compatible` string that differs from the DT by one character never matches and produces no error. The device simply stays unbound."
- **References:** `https://docs.kernel.org/devicetree/usage-model.html`; `https://docs.kernel.org/firmware-guide/acpi/enumeration.html`; the devicetree specification (devicetree.org); `<Src file="drivers/base/platform.c" symbol="platform_match" />`.
- **Verify:** `platform_driver`, `platform_match`, `of_driver_match_device`, `acpi_driver_match_device`, `device_property_read_u32`, `platform_get_resource`, `devm_platform_ioremap_resource`, and that `.remove` returns `void` in v6.18.

**Task-specific steps** (in addition to the procedure):
- context7: the driver-model API (`docs.kernel.org/driver-api`).
- Commit: `docs: write the linux device model and platform devices pages`.

---

## Task 5: Folder 14 — PCI drivers, and MMIO

**Interfaces:** Consumes Task 2's `pcie-in-depth` (config space, BARs, MSI). **Never re-explain them.** Produces `14/pci-and-pcie-drivers` and `14/mmio-and-port-io`, which Tasks 6, 8 and 15 build on.

### `pci-and-pcie-drivers.md` — PCI and PCIe Drivers **[Lab host=qemu]**

- **Opens with:** by the time a PCI driver's `probe` runs, firmware and the PCI core have already done the hard part. The device was enumerated, its BARs were sized and assigned, and its config space is cached in a `struct pci_dev`. A PCI driver's job is narrower than it looks: claim the device, turn on what it needs, map the BARs, and set up interrupts and DMA.
- **Sections:** `## The ID table and MODULE_DEVICE_TABLE` (and how modalias autoloading follows from it); `## struct pci_dev, in shape`; `## The probe sequence` (`pcim_enable_device`/`pci_enable_device`, `pci_request_regions`, `pci_iomap` or `pcim_iomap_regions`, `pci_set_master`, `dma_set_mask_and_coherent`, IRQ vectors — each step forward-linked to the page that owns it); `## Reading lspci -vvv against the code`; `## Managed versus unmanaged` (the `pcim_*` family).
- **Lab:** in the Debian VM, `lspci -vvv -s <virtio-net BDF>` and `lspci -k`, then find `virtio_pci_probe` in the source and match each step to a `lspci` line: BAR regions, MSI-X capability with its vector count, and "Kernel driver in use". Expected output is measured. If it fails: no `lspci` means `apt install pciutils`.
- **Anchor:** a WaveDrom `reg` for the PCI Command register (I/O space, memory space, bus master, …, INTx disable), annotated with which kernel call sets each bit; plus the probe sequence as a `flowchart TD`.
- **KernelFacts:** structure `[["struct pci_dev", "include/linux/pci.h"], ["struct pci_driver", "include/linux/pci.h"]]`; path `"pci_register_driver() → pci_bus_match() → pci_device_probe() → local_pci_probe() → drv->probe()"`; observe `lspci -k -nn`; trap: "Forgetting `pci_set_master()` produces a device that accepts commands and never completes DMA. No error is logged and no fault is raised."
- **References:** `https://docs.kernel.org/PCI/pci.html` (context7); `<Src file="drivers/virtio/virtio_pci_common.c" symbol="virtio_pci_probe" />`; `man 8 lspci`; LDD3 ch. 12, annotated as dated.
- **Verify:** `pci_device_id`, `PCI_DEVICE`, `MODULE_DEVICE_TABLE`, `pcim_enable_device`, `pci_request_regions`, `pcim_iomap_regions` (it may be deprecated in favour of `pcim_iomap_region` at v6.18 — check, and cite what is current), `pci_set_master`, `local_pci_probe`, `virtio_pci_probe`.

### `mmio-and-port-io.md` — MMIO, `ioremap`, and Accessors **[WAH]** **[arm64]** **[Misc]**

- **Opens with:** device registers sit at physical addresses, and the CPU reaches them with ordinary loads and stores. That makes the mistake easy: a plain pointer dereference compiles, works on the author's machine, and is still wrong. The compiler may merge, reorder or elide the access, the CPU may reorder it against DMA, and the mapping may be cacheable. Accessors exist to make those three guarantees explicit.
- **Sections:** `## ioremap and why the mapping is special` (uncached/device memory types, `ioremap` versus `ioremap_wc`, and `devm_ioremap_resource`); `## __iomem and sparse` (the address-space annotation and what `make C=1` catches); `## readl/writel and their guarantees` (little-endian, no tearing, ordering against each other and against prior normal memory writes for DMA); `## Relaxed accessors and explicit barriers` (`readl_relaxed`, `wmb` versus `dma_wmb`, and when relaxed is safe; link `../09-concurrency-and-locking/memory-ordering-and-barriers.md`); `## Posted writes and the read-back` (a PCI write may not have landed when `writel` returns, so drivers read back to flush); `## Port I/O, an x86 legacy` (`inb`/`outb` and `ioport_map`); `:::note[arm64]` — no port I/O instructions exist, so PCI I/O BARs are emulated through an MMIO window, and arm64's `writel` includes a barrier before the store (`__iowmb`) while `writel_relaxed` omits it.
- **WAH:** disassemble `writel` versus `writel_relaxed` on x86-64 from the lab kernel (`objdump -d` on a tiny module that calls both), and show they compile to the same `mov` there. Then show from the v6.18 arm64 `io.h` source (`<Src>`) that they differ. Name both architectures.
- **Misconceptions:** (1) "`volatile` is enough." (2) "`writel` returning means the device saw it." (3) "Relaxed accessors are a micro-optimisation with no correctness impact."
- **Anchor:** a `sequenceDiagram` — CPU fills a DMA descriptor in RAM → `wmb()`/`writel` ordering point → doorbell write posted → read-back flush → device fetches the descriptor. Plus a table of accessors × ordering × byte order × typical use.
- **KernelFacts:** structure `[["readl/writel (generic)", "include/asm-generic/io.h"], ["ioremap", "arch/x86/mm/ioremap.c"]]`; path `"devm_ioremap_resource() → ioremap() → page tables with _PAGE_CACHE_MODE_UC_MINUS → readl(addr)"`; observe `cat /proc/iomem | head -40`; trap: "Code that dereferences an `__iomem` pointer directly may pass every test on x86-64 and fail on arm64. `make C=1` reports it before a user does."
- **References:** `https://docs.kernel.org/driver-api/device-io.html`; `Documentation/memory-barriers.txt` "Kernel I/O barrier effects"; `<Src file="arch/arm64/include/asm/io.h" symbol="__iowmb" />`; `https://docs.kernel.org/dev-tools/sparse.html`.
- **Verify:** `ioremap`, `ioremap_wc`, `devm_ioremap_resource`, `__iomem`, `readl_relaxed`, `dma_wmb`, `__iowmb`, `ioport_map`, and the x86 cache-mode constant named in `path`.

**Task-specific:** context7: driver-model and PCI API. Commit: `docs: write the PCI driver and MMIO accessor pages`.

---

## Task 6: Folder 14 — the DMA API, and interrupts in drivers

**Interfaces:** Consumes Task 2's `dma-and-iommu` and folder 10 (threaded IRQs, affinity). Produces `14/the-dma-api` (a prerequisite of `15/virtio-and-paravirtualization`) and `14/interrupts-in-drivers` (a prerequisite of `14/power-management`).

### `the-dma-api.md` — The DMA API **[arm64]** **[Misc]**

- **Opens with:** a driver hands a device an address and then must not touch the buffer until the device gives it back. The DMA API makes both halves explicit. It turns a kernel buffer into a `dma_addr_t` the device can use, whether or not an IOMMU or a bounce buffer stands in between, and it marks the moments ownership changes hands. Most DMA bugs are a CPU touching a buffer the device currently owns.
- **Sections:** `## dma_addr_t is not a physical address`; `## Masks: dma_set_mask_and_coherent`; `## Coherent allocations` (`dma_alloc_coherent`, for descriptor rings); `## Streaming mappings` (`dma_map_single`, `dma_map_sg`, `dma_map_page`, direction, and `dma_mapping_error`); `## Ownership and sync` (`dma_sync_single_for_cpu`/`_for_device`); `## Bounce buffers and swiotlb`; `## The IOMMU underneath` (the DMA API unchanged with or without it; `iommu.strict`; passthrough); `## Debugging` (`CONFIG_DMA_API_DEBUG`); `:::note[arm64]` — on non-coherent arm64 SoCs, `dma_sync_*` and map/unmap perform real cache clean/invalidate (`arch_sync_dma_for_device`). On coherent x86-64 they are close to free, which is why a missing sync often ships unnoticed until the driver runs on arm64.
- **Misconceptions:** (1) "`virt_to_phys` gives the address to program into the device." (2) "Coherent memory is always the better choice." (3) "Without an IOMMU, the DMA API is just bookkeeping."
- **Anchor:** a `sequenceDiagram` of a streaming receive: `dma_map_single(DMA_FROM_DEVICE)` → device owns → DMA → IRQ → `dma_unmap_single` / `sync_for_cpu` → CPU owns, with the "do not touch" interval shaded via a `rect`. Plus a table of coherent versus streaming × lifetime, cache behaviour, typical use and cost.
- **KernelFacts:** structure `[["struct dma_map_ops", "include/linux/dma-map-ops.h"], ["dma_addr_t", "include/linux/types.h"]]`; path `"dma_map_single() → dma_map_page_attrs() → dma_direct_map_page() | iommu_dma_map_page() → swiotlb_map() if needed"`; observe `dmesg | grep -i -E 'iommu|swiotlb|DMAR'`; trap: "Reading a receive buffer before `dma_unmap`/`sync_for_cpu` works on x86-64 and returns stale data on a non-coherent arm64 board. `CONFIG_DMA_API_DEBUG` catches several of the ownership mistakes; it cannot catch all of them."
- **References:** `https://docs.kernel.org/core-api/dma-api.html` and `dma-api-howto.html` (context7, DMA function names); `<Src file="kernel/dma/mapping.c" symbol="dma_map_page_attrs" />`; `https://docs.kernel.org/core-api/swiotlb.html`; LWN on dynamic swiotlb.
- **Verify:** every function named above, plus `dma_direct_map_page`, `iommu_dma_map_page`, `swiotlb_map`, `arch_sync_dma_for_device`, `CONFIG_DMA_API_DEBUG`, and the `iommu.strict` parameter.

### `interrupts-in-drivers.md` — Interrupts in a Driver **[Misc]**

- **Opens with:** folder 10 explained how an interrupt reaches the kernel. A driver sees the other end: it asks for vectors, installs a handler that must decide quickly whether the interrupt was its own, and pushes everything slow into a thread. Multi-queue devices make this concrete, with one vector per queue, each steered to the CPU that will consume the data.
- **Sections:** `## request_irq and devm_request_threaded_irq`; `## The shared-line contract` (`IRQF_SHARED`, and returning `IRQ_NONE` honestly so the spurious-IRQ detector works); `## MSI and MSI-X vectors` (`pci_alloc_irq_vectors` with `PCI_IRQ_MSIX | PCI_IRQ_MSI | PCI_IRQ_INTX`, `pci_irq_vector`; link the CS backfill); `## Top half and thread` (`IRQ_WAKE_THREAD` and `IRQF_ONESHOT`; link `../10-interrupts-time-and-deferred-work/threaded-irqs.md`); `## Per-queue vectors and affinity` (`PCI_IRQ_AFFINITY` and managed affinity; link the affinity page); `## Masking, disable_irq, and teardown order`.
- **Misconceptions:** (1) "Returning `IRQ_HANDLED` always is harmless." (2) "`disable_irq` from inside the handler is fine." It deadlocks, and `disable_irq_nosync` is the in-handler form.
- **Anchor:** a `sequenceDiagram` — device MSI-X write → hardirq handler (reads status, acks, returns `IRQ_WAKE_THREAD`) → irq thread (processes) → re-enable. Plus a table of `/proc/interrupts` columns explained against a real MSI-X device on the Debian VM.
- **KernelFacts:** structure `[["irqreturn_t", "include/linux/irqreturn.h"], ["pci_alloc_irq_vectors", "include/linux/pci.h"]]`; path `"pci_alloc_irq_vectors() → __pci_enable_msix_range() → request_threaded_irq(pci_irq_vector(pdev, i), …)"`; observe `grep -E 'virtio|nvme' /proc/interrupts`; trap: "On a shared line, a handler that claims every interrupt hides a stuck device. One that claims none gets the line disabled with 'nobody cared'."
- **References:** `https://docs.kernel.org/PCI/msi-howto.html`; `https://docs.kernel.org/core-api/genericirq.html`; `<Src file="kernel/irq/manage.c" symbol="request_threaded_irq" />`.
- **Verify:** `pci_alloc_irq_vectors`, `PCI_IRQ_INTX` (renamed from `PCI_IRQ_LEGACY` — confirm at v6.18), `PCI_IRQ_AFFINITY`, `pci_irq_vector`, `IRQ_WAKE_THREAD`, `IRQF_ONESHOT`, `disable_irq_nosync`, `__pci_enable_msix_range`, `note_interrupt`.

**Task-specific:** context7: DMA API function names. Commit: `docs: write the DMA API and driver interrupt pages`.

---

## Task 7: Folder 14 — character devices, and Lab: a character driver

**Run the lab first** (spec Phase 4 step 4). Steps 1–4 below produce working code; the two pages are written from it.

**Files:**
- Create: `static/code/linux/chardrv/chardrv.c`, `static/code/linux/chardrv/Makefile`, `static/code/linux/chardrv/test_chardrv.c`
- Modify: `docs/linux/14-device-drivers-and-hardware/character-devices.md`, `docs/linux/14-device-drivers-and-hardware/lab-a-character-driver.md`

**Interfaces:**
- Consumes: `01/building-a-kernel` (the build tree), `01/booting-your-kernel-in-qemu` (the initramfs VM), and `04/modules-in-practice`.
- Produces: the module that `14/debugging-drivers` (Task 9) reuses as its debugging subject. **Its file names and its misc device name `chardrv` are fixed here.**

**Module behaviour (the spec of the code):**
- It registers a misc device `/dev/chardrv`, minor `MISC_DYNAMIC_MINOR`.
- It holds a single 4 KiB kernel buffer protected by a `mutex`.
- `write` copies into the buffer at `*ppos`, bounded by the buffer size; past the end it returns `-ENOSPC`.
- `read` copies out from `*ppos` up to the current length; at the end it returns 0.
- `llseek` uses `default_llseek` or `fixed_size_llseek`, whichever v6.18 provides.
- It has two ioctls, defined with `_IO`/`_IOR` on magic `'c'`: `CHARDRV_CLEAR` (`_IO('c', 1)`) and `CHARDRV_GET_LEN` (`_IOR('c', 2, __u32)`). An unknown command returns `-ENOTTY`.
- It uses `copy_to_user`/`copy_from_user`/`put_user` with their return values checked.
- `module_misc_device()` replaces explicit init/exit if v6.18 has it; otherwise use `misc_register`/`misc_deregister`.
- `MODULE_LICENSE("GPL")` and `MODULE_DESCRIPTION`.

- [ ] **Step 1: Write the three files.**
  - `test_chardrv.c` writes `"hello"`, seeks to 0, reads it back, calls `CHARDRV_GET_LEN` (expects 5), calls `CHARDRV_CLEAR`, calls `CHARDRV_GET_LEN` (expects 0), calls an invalid ioctl (expects `ENOTTY`), and prints `PASS` or the first failing check.
  - The `Makefile` builds with `make -C $(KDIR) M=$(PWD) modules`, with `KDIR` defaulting to the folder-01 build tree path.
- [ ] **Step 2: Build against the lab kernel.** Run `make KDIR=<folder-01 build tree>`. Expected: `chardrv.ko` with **zero warnings**. Then run `make C=1` (sparse). Expected: no sparse warnings.
- [ ] **Step 3: Run it in the initramfs VM.** Add `chardrv.ko` and a statically linked `test_chardrv` (`gcc -static`) to the folder-01 initramfs, boot it, and run `insmod chardrv.ko`, `ls -l /dev/chardrv`, `./test_chardrv`, a `function_graph` trace of `chardrv_*` functions via tracefs, and `rmmod chardrv`. Expected: `PASS` and a clean `rmmod` with no `dmesg` warnings. Save the full console transcript to the scratchpad.

  If the initramfs has no devtmpfs mount for `/dev/chardrv`, fix the init script per folder 01 and note the fix on the page.
- [ ] **Step 4: Break it on purpose, then restore.** Remove the `mutex_unlock` on one error path, rebuild with `CONFIG_PROVE_LOCKING` if the lab kernel has it, and capture the lockdep splat for the debugging page. If lockdep is not configured, skip this step and say so in Task 9.

### `character-devices.md` — Character Devices

- **Opens with:** a character device is the simplest complete driver shape. It is a device number pointing at a `file_operations` table, so `open`, `read`, `write` and `ioctl` on a `/dev` node land in driver functions. Everything from folder 11's `struct file` applies unchanged; the only new part is how a device number finds its table.
- **Sections:** `## Device numbers` (`dev_t`, major/minor, `alloc_chrdev_region`, `/proc/devices`); `## struct cdev and cdev_add`; `## file_operations for a device` (which members matter, and `private_data` per open); `## The misc-device shortcut` (one major, dynamic minors, and why most small drivers should use it); `## Where /dev nodes come from` (devtmpfs creates them, udev names and permissions them; forward link `./firmware-udev-and-hotplug.md`); `## Classes` (`class_create` — **v6.18 signature, no owner argument**).
- **Anchor:** a `flowchart LR`: `open("/dev/chardrv")` → path lookup → inode with `i_rdev` → `chrdev_open` → `kobj_lookup` / cdev map → driver `file_operations` → `filp->f_op` replaced. Plus a table: cdev versus misc × major allocation, boilerplate, and when to use.
- **KernelFacts:** structure `[["struct cdev", "include/linux/cdev.h"], ["struct miscdevice", "include/linux/miscdevice.h"]]`; path `"open() → do_dentry_open() → chrdev_open() → cdev->ops->open()"`; observe `cat /proc/devices; ls -l /dev/null /dev/kmsg`; trap: "Calling `cdev_add` before the device is ready makes it live immediately. User space can `open()` it on the very next instruction, before the rest of `probe` has run."
- **References:** LDD3 ch. 3, annotated as dated; `<Src file="fs/char_dev.c" symbol="chrdev_open" />`; `https://docs.kernel.org/driver-api/misc_devices.html` if it exists at v6.18 (otherwise `<Src file="include/linux/miscdevice.h" />`); `man 4 mem` for a classic example.

### `lab-a-character-driver.md` — Lab: Write a Character Driver **[Lab host=qemu]**

- **Opens with:** this lab builds a complete, correct, if useless, driver. It is a 4 KiB scratch buffer behind `/dev/chardrv` with `read`, `write`, `seek` and two ioctls. The module is small enough to read in one sitting and complete enough to show every boundary from earlier folders: `copy_*_user`, a mutex, `file_operations`, the misc device, and module load and unload.
- **Sections:** `## What you will build`; `## The code` (embed `chardrv.c` verbatim in ` ```c `, with numbered call-outs in prose; link the downloadable file); `## Building against your kernel`; `## Loading and exercising it` (the measured transcript from Step 3); `## Watching it with ftrace` (the measured `function_graph` excerpt; link `../01-lab-and-toolchain/debugging-the-kernel-with-gdb.md` for the debugger route); `## Unloading cleanly`; `## Things to try` (add `poll`, add a sysfs attribute — forward link `./talking-to-user-space.md`); and the `ioctl` number encoding.
- **Anchor:** a WaveDrom `reg` of the 32-bit ioctl number (nr 8 bits, type 8, size 14, dir 2), filled in for `CHARDRV_GET_LEN`, plus a `sequenceDiagram` of `test_chardrv` → syscalls → `chardrv_write`/`read`/`ioctl`.
- **KernelFacts:** structure `[["struct file_operations", "include/linux/fs.h"], ["_IOR", "include/uapi/asm-generic/ioctl.h"]]`; path `"ioctl(fd, CHARDRV_GET_LEN, &n) → do_vfs_ioctl() → vfs_ioctl() → filp->f_op->unlocked_ioctl() → chardrv_ioctl()"`; observe `ls -l /dev/chardrv && cat /sys/class/misc/chardrv/dev`; trap: "Returning `-EINVAL` for an unknown ioctl breaks tools that probe with `ENOTTY` (the documented 'not a tty/not supported' answer). Unknown command is `-ENOTTY`."
- **Lab block:** `host="qemu"`, measured output, "if it fails: `Invalid module format` means the module was built against a different kernel than the one booted; rebuild with `KDIR` pointing at the tree that produced the booted `bzImage`."
- **References:** `https://docs.kernel.org/kbuild/modules.html`; `https://docs.kernel.org/driver-api/ioctl.html`; `<Src file="include/uapi/asm-generic/ioctl.h" />`.
- **No `<Cast>`** in this phase (Global Constraints); the transcript block is what Phase 5 records.

- [ ] **Step 5: Write `character-devices.md`**, then `lab-a-character-driver.md`. The `## The code` block must be byte-identical to `chardrv.c`; confirm with a diff of the fenced block against the file.
- [ ] **Step 6:** Writing-task procedure (context7: driver-model API; verify `misc_register`, `module_misc_device`, `MISC_DYNAMIC_MINOR`, `class_create`, `alloc_chrdev_region`, `cdev_add`, `chrdev_open`, `do_dentry_open`, `vfs_ioctl`, `fixed_size_llseek`, `default_llseek`).
- [ ] **Step 7: Lint and commit**

```bash
rtk run 'npm run lint'
git add static/code/linux/chardrv docs/linux/14-device-drivers-and-hardware
git commit -m "docs: write the character device page and the character driver lab"
```

---

## Task 8: Folder 14 — talking to user space, block/net driver shapes, and firmware/udev

### `talking-to-user-space.md` — Talking to User Space **[WAH]** **[Misc]**

- **Opens with:** most new drivers get the interface wrong rather than the hardware. The hardware is fixed and the interface is forever: once user space depends on it, it is ABI. This page is a decision guide. It lists what each mechanism is for, what it costs to change later, and which one the kernel community will accept.
- **Sections:** one `##` each for `ioctl` (versioning, `_IOW`/`_IOR` sizes, `compat_ioctl`, and no pointers inside structs), sysfs attributes (one value per file, `DEVICE_ATTR_RW`, attribute groups registered with the device, and the `Documentation/ABI` requirement), debugfs (no ABI, may be absent, never for production tooling), netlink and generic netlink (structured, multicast, extensible), `read`/`poll` event streams, `mmap` of device memory (`remap_pfn_range`, `vm_iomap_memory`), and uio/vfio (user-space drivers, and vfio as the IOMMU-safe one); then `## Choosing` (the decision table).
- **WAH:** pick one real device on the Debian VM and show all three of its faces: `udevadm info -a` on its sysfs attributes, a debugfs directory for it if one exists, and its `ioctl`s in `strace` of the tool that drives it (`ethtool -i eth0` uses the `SIOCETHTOOL` ioctl or ethtool netlink — show which v6.18 plus the VM's `ethtool` actually use).
- **Misconceptions:** (1) "debugfs is fine for a tool, since it is always mounted." (2) "One sysfs file can return a table." (3) "`ioctl` is deprecated."
- **Anchor:** the decision table: need × mechanism × ABI weight × example in-tree user. Plus a `flowchart TD` decision tree.
- **KernelFacts:** structure `[["struct device_attribute", "include/linux/device.h"], ["struct genl_family", "include/net/genetlink.h"]]`; path `"write(/sys/.../attr) → kernfs_fop_write_iter() → sysfs_kf_write() → dev_attr_store() → driver's _store()"`; observe `udevadm info -a -n /dev/vda | head -30`; trap: "A sysfs attribute added without a `Documentation/ABI` entry still becomes ABI the day a script reads it. Removing it later is a user-visible regression."
- **References:** `https://docs.kernel.org/filesystems/sysfs.html`; `https://docs.kernel.org/driver-api/ioctl.html`; `https://docs.kernel.org/userspace-api/netlink/intro.html`; `https://docs.kernel.org/driver-api/vfio.html`.

### `block-and-network-driver-shapes.md` — Block and Network Driver Shapes

- **Opens with:** a character driver handles one call at a time on behalf of one file. Block and network drivers handle queues. The core hands a block driver `struct request`s through blk-mq, and hands a network driver `sk_buff`s through `ndo_start_xmit` while expecting NAPI polling on receive. Recognising the shape makes either kind of driver readable.
- **Sections:** `## The block shape` (`blk_mq_tag_set`, `blk_mq_ops.queue_rq`, `blk_mq_alloc_disk` with `queue_limits` at v6.18, completion via `blk_mq_end_request`; link folder 12's blk-mq and NVMe pages; walk `drivers/block/null_blk` briefly); `## The network shape` (`net_device`, `net_device_ops`, `ndo_open`/`ndo_stop`/`ndo_start_xmit`, NAPI `poll` with its budget, and `netif_napi_add`; link `13/the-receive-path`; walk `drivers/net/veth.c` or `virtio_net` briefly); `## Side by side`.
- **Anchor:** a three-column table — char / block / net × unit of work, entry point, completion, flow control, and a canonical small in-tree example. Plus two small `flowchart LR` diagrams.
- **KernelFacts:** structure `[["struct blk_mq_ops", "include/linux/blk-mq.h"], ["struct net_device_ops", "include/linux/netdevice.h"]]`; path `"blk-mq: __blk_mq_issue_directly() → ops->queue_rq() ‖ net: dev_hard_start_xmit() → ndo_start_xmit()"`; observe `ls /sys/block/*/mq; ethtool -l eth0`; trap: "`ndo_start_xmit` must not sleep, and it must stop the queue (`netif_stop_queue`) before the ring is full. Returning `NETDEV_TX_BUSY` routinely is a bug, not flow control."
- **References:** `https://docs.kernel.org/block/blk-mq.html`; `https://docs.kernel.org/networking/netdevices.html`; `https://docs.kernel.org/networking/napi.html`; `<Src file="drivers/block/null_blk/main.c" symbol="null_queue_rq" />`.

### `firmware-udev-and-hotplug.md` — Firmware, udev, and Hotplug **[WAH]**

- **Opens with:** two things happen outside the kernel every time a device appears. Many devices are inert until a firmware blob is loaded into them, and the kernel asks for that blob by name. User space also has to create a usable, stably named `/dev` entry and apply permissions. Both run through the same channel: a uevent from the device model to udev.
- **Sections:** `## request_firmware` (search paths under `/lib/firmware`, the initramfs requirement for early devices, compressed firmware, and `firmware_class.path`); `## Uevents` (`kobject_uevent`, the netlink multicast, and the environment variables); `## udev rules and naming` (rule matching, `udevadm test`, and predictable network interface names — `enp0s3` decoded); `## Coldplug versus hotplug` (`udevadm trigger` replaying boot-time devices); `## Modalias autoloading` (closes the loop with the ID-table page).
- **WAH:** `udevadm monitor --kernel --udev --property` while hot-adding a virtio disk to the running Debian VM via the QEMU monitor (`device_add`) and removing it. Show the paired KERNEL/UDEV events. Cleanup: `device_del`.
- **Anchor:** a `sequenceDiagram` — device appears → `kobject_uevent(KOBJ_ADD)` → netlink → `systemd-udevd` → rules → `/dev` symlink/permissions → `modprobe` via modalias → driver `probe` → `request_firmware` → file read → device started.
- **KernelFacts:** structure `[["struct firmware", "include/linux/firmware.h"], ["kobject_uevent_env", "lib/kobject_uevent.c"]]`; path `"device_add() → kobject_uevent(KOBJ_ADD) → netlink broadcast → udevd rules → modprobe $MODALIAS"`; observe `udevadm monitor --kernel --property`; trap: "A driver built into the kernel that calls `request_firmware` before the root filesystem is mounted finds nothing unless the firmware is in the initramfs. The symptom is a device that works only when built as a module."
- **References:** `https://docs.kernel.org/driver-api/firmware/index.html`; `man 7 udev`; `https://systemd.io/PREDICTABLE_INTERFACE_NAMES/`; `<Src file="drivers/base/firmware_loader/main.c" symbol="request_firmware" />`.

**Task-specific:** context7: driver-model API, plus systemd/udev for the rules syntax. Verify `DEVICE_ATTR_RW`, `remap_pfn_range`, `vm_iomap_memory`, `kernfs_fop_write_iter`, `sysfs_kf_write`, `dev_attr_store`, `blk_mq_alloc_disk`, `null_queue_rq`, `netif_napi_add`, `ndo_start_xmit`, `dev_hard_start_xmit`, `__blk_mq_issue_directly`, `request_firmware`, `kobject_uevent_env`, and the `firmware_class.path` parameter. Commit: `docs: write the user-space interface, driver shapes, and firmware/udev pages`.

---

## Task 9: Folder 14 — power management, and debugging drivers

### `power-management.md` — Power Management **[WAH]** **[Misc]**

- **Opens with:** power management is two separate systems that share callbacks. **System sleep** stops the whole machine in an ordered sequence and must bring every device back. **Runtime PM** idles individual devices while the system runs, gated by reference counts. A laptop that will not sleep is almost always one driver failing a step in the first, or one held reference in the second.
- **Sections:** `## System sleep states` (s2idle, S3/deep, hibernate, and `/sys/power/mem_sleep`); `## The callback sequence` (prepare → suspend → suspend_late → suspend_noirq, then the reverse on resume; `dev_pm_ops` and `DEFINE_SIMPLE_DEV_PM_OPS`/`pm_sleep_ptr` at v6.18; freezing tasks first); `## Runtime PM` (`pm_runtime_get_sync`/`put`, usage counts, autosuspend delay, and `/sys/devices/.../power/runtime_status`); `## Wakeup sources`; `## Diagnosing a machine that will not sleep` (`pm_debug_messages`, `/sys/power/pm_test`, `/sys/kernel/debug/wakeup_sources`, `/sys/power/suspend_stats`, `analyze_suspend`/`sleepgraph`).
- **WAH:** in the Debian VM, `echo freezers > /sys/power/pm_test` then `echo freeze > /sys/power/state`, which runs the freeze phase without actually sleeping, with `pm_debug_messages` on. Show the dmesg sequence. Cleanup: `echo none > /sys/power/pm_test`. Also show `runtime_status` for a few devices.
- **Misconceptions:** (1) "Suspend and runtime PM are the same thing at different scales." (2) "`pm_runtime_get` means the device is powered when it returns." That is `_sync`/`resume_and_get`. (3) "S3 is always available." Many modern laptops offer only s2idle.
- **Anchor:** a `stateDiagram-v2` of runtime PM (active ↔ suspending → suspended → resuming → active, with usage-count guards), plus a `sequenceDiagram` of the system suspend phases across three devices.
- **KernelFacts:** structure `[["struct dev_pm_ops", "include/linux/pm.h"], ["struct dev_pm_info", "include/linux/pm.h"]]`; path `"echo mem > /sys/power/state → pm_suspend() → suspend_devices_and_enter() → dpm_suspend_start() → dpm_suspend_end()"`; observe `cat /sys/power/mem_sleep /sys/power/suspend_stats/fail`; trap: "A driver that resumes fine in testing can still fail after hibernate: hibernate restores memory from an image, while the hardware was fully powered off. `restore` is not `resume`."
- **References:** `https://docs.kernel.org/driver-api/pm/devices.html`; `https://docs.kernel.org/power/runtime_pm.html`; `https://docs.kernel.org/admin-guide/pm/sleep-states.html`; the `pm-graph`/sleepgraph project.

### `debugging-drivers.md` — Debugging Drivers **[Lab host=qemu]** **[Misc]**

- **Opens with:** driver bugs are hard to see because the driver runs in places a debugger dislikes: interrupt context, `probe` at boot, and paths that only run when hardware misbehaves. The toolkit is to make the driver talk (dynamic debug), watch its functions without editing it (`ftrace`), check that it bound at all, and read an oops back to a source line. This page applies each tool to the lab's `chardrv` module.
- **Sections:** `## Dynamic debug` (`pr_debug`/`dev_dbg`, `dyndbg="+p"` on module load, and `/proc/dynamic_debug/control`); `## ftrace scoped to a module` (`set_ftrace_filter ':mod:chardrv'`, `function_graph`; folder 17 owns `ftrace` in depth, so name it in prose without a link); `## A probe that never fires` (a checklist: the module loaded? the ID table matches? `driver_override`? `devices_deferred`? the device present in `/sys/bus`?); `## debugfs for your driver`; `## From oops to source line` (`scripts/decode_stacktrace.sh`, `faddr2line`; folder 17 owns oops reading in depth, so name it); `## Five driver bugs` — a table drawn from folder 04's memory-safety catalogue: use-after-free after `remove`, sleeping in atomic context, missing `dma_unmap`/ownership violation, unbalanced runtime-PM counts, and a `devm` resource released while an IRQ can still fire. Each has its symptom and the tool that finds it.
- **Lab:** load `chardrv` with `dyndbg=+p` and show the `pr_debug` lines; run the module filter `function_graph`; then the Task 7 Step 4 lockdep splat (or the note that it was skipped), decoded with `decode_stacktrace.sh` to the exact line. If it fails: no `pr_debug` output means `CONFIG_DYNAMIC_DEBUG` is off in the lab config — enable it per `01/building-a-kernel`.
- **Misconceptions:** (1) "`printk` debugging is primitive." (2) "If `probe` failed, there would be an error in `dmesg`."
- **Anchor:** the five-bugs table, plus a `flowchart TD` for "the probe never fires".
- **KernelFacts:** structure `[["struct _ddebug", "include/linux/dynamic_debug.h"], ["decode_stacktrace.sh", "scripts/decode_stacktrace.sh"]]`; path `"pr_debug() → DYNAMIC_DEBUG_BRANCH(descriptor) → __dynamic_pr_debug() → printk"`; observe `grep chardrv /proc/dynamic_debug/control`; trap: "`devm_request_irq` frees the IRQ *after* `remove` returns. If `remove` freed the memory the handler uses, a late interrupt is a use-after-free."
- **References:** `https://docs.kernel.org/admin-guide/dynamic-debug-howto.html`; `https://docs.kernel.org/trace/ftrace.html`; `https://docs.kernel.org/admin-guide/bug-hunting.html`; `<Src file="scripts/decode_stacktrace.sh" />`.

**Task-specific:** context7: driver-model and PM APIs. Verify `dev_pm_ops`, `DEFINE_SIMPLE_DEV_PM_OPS`, `pm_sleep_ptr`, `pm_runtime_resume_and_get`, `pm_suspend`, `suspend_devices_and_enter`, `dpm_suspend_start`, `__dynamic_pr_debug`, `DYNAMIC_DEBUG_BRANCH`, the `pm_test` values, and the `:mod:` filter syntax. Run the lab in the initramfs VM first. Commit: `docs: write the power management and driver debugging pages`.

---
## Task 10: Folder 15 — what a container actually is, and namespaces

**Interfaces:**
- Consumes: Task 3's `virtualization-and-isolation` (the theory).
- Produces: `15/what-a-container-actually-is`. The spec puts it **second in the phase** after the device model, and it is the framing of every folder-15 page. It names the five ingredients — namespaces, cgroup, root filesystem, capabilities, seccomp — and every later page is one of them.

### `what-a-container-actually-is.md` — What a Container Actually Is **[WAH]** **[Misc]**

- **Opens with:** search the kernel source for a container struct and you will not find one. A container is an ordinary process, or a tree of them. User space has given it five things: namespaces that change what it can see, a cgroup that limits what it can use, a different root filesystem, a reduced set of capabilities, and a seccomp filter on its syscalls. Docker, Podman and Kubernetes are different ways of assembling the same five parts.
- **Sections:** `## The five ingredients` (one paragraph each, linking the page that owns each); `## What the kernel sees` (a `task_struct` with an `nsproxy`, a `css_set`, and a `cred` — nothing more); `## What is still shared` (the kernel itself, the clock in most cases, the page cache, kernel memory accounting caveats, and `/proc/sys` partially; link the CS isolation page); `## Containers versus VMs, in one table`; `## What actually happens`; `## Misconceptions`.
- **WAH:** on the Debian VM, start a container with `podman run -d --rm docker.io/library/alpine sleep 600`. If neither podman nor docker is installed, install podman, and say which one was used. From the **host**, find the process (`ps -o pid,cmd`), then show:
  - `ls -l /proc/<pid>/ns` beside `/proc/self/ns` (different inode numbers);
  - `cat /proc/<pid>/cgroup`;
  - `grep Cap /proc/<pid>/status` decoded with `capsh --decode`;
  - `grep Seccomp /proc/<pid>/status`;
  - `ls -l /proc/<pid>/root/`.

  All five ingredients are visible from outside on one ordinary process. Cleanup: `podman stop`.
- **Misconceptions:** (1) "A container is a lightweight VM." (2) "Containers are a kernel feature." (3) "Processes in a container are invisible to the host."
- **Anchor:** a `flowchart LR` with one `task_struct` in the middle and five arrows to `nsproxy` (→ 8 namespaces), `css_set` (→ cgroup), `fs_struct.root` (→ rootfs), `cred` (→ capability sets), and `seccomp.filter`. Caption: "A container, as the kernel stores it: one task and five pointers."
- **KernelFacts:** structure `[["struct nsproxy", "include/linux/nsproxy.h"], ["struct css_set", "include/linux/cgroup-defs.h"]]`; path `"runtime: clone3(CLONE_NEW*) → cgroup write → pivot_root() → capset() → seccomp(SET_MODE_FILTER) → execve()"`; observe `ls -l /proc/<pid>/ns; cat /proc/<pid>/cgroup`; trap: "Everything in the container shares the host kernel. A kernel vulnerability reachable through an allowed syscall is a container escape, whatever the namespaces say."
- **References:** `man 7 namespaces`, `man 7 cgroups`; Jérôme Petazzoni's or Liz Rice's "containers from scratch" talk (choose whichever is reachable, and annotate it as a video); the OCI runtime spec (context7, OCI); `<Src file="include/linux/nsproxy.h" symbol="nsproxy" />`.

### `namespaces-overview.md` — Namespaces **[Lab host=qemu]**

- **Opens with:** a namespace wraps one kind of global resource so that a group of processes gets its own copy: hostname, PID numbers, mount table, network stack, and so on. There are eight kinds. Each is created the same way (a `CLONE_NEW*` flag), joined the same way (`setns` on a file descriptor), and inspected the same way (`/proc/PID/ns`).
- **Sections:** `## The eight namespaces` (a table: namespace × flag × what it isolates × kernel version introduced × owning page — mount and network link to folders 11 and 13); `## Creating: clone, clone3, unshare`; `## Joining: setns and nsenter` (including pidfd-based `setns` of several namespaces at once); `## /proc/PID/ns as the handle` (inode identity, bind-mounting to keep a namespace alive, and `ip netns` as exactly that); `## Ownership: every namespace has a user namespace` (forward link `./user-namespaces.md`); `## Lifetime`.
- **Lab:** on the Debian VM, `sudo unshare --uts --pid --fork --mount-proc bash`, then `hostname lab` and `ps aux` inside versus outside. Then `lsns` before and after. Then `nsenter -t <pid> -u hostname` from outside. Measured output. Cleanup: exit the shell. If it fails: `unshare: unshare failed: Operation not permitted` without `sudo` is expected — user namespaces come on the next page.
- **Anchor:** a WaveDrom `reg` of the `CLONE_NEW*` bits within the 64-bit clone flags word, at their real bit positions from `include/uapi/linux/sched.h`. **Read the positions from the header**; `CLONE_NEWTIME` lives in the low byte, which surprises people.
- **KernelFacts:** structure `[["struct nsproxy", "include/linux/nsproxy.h"], ["struct ns_common", "include/linux/ns_common.h"]]`; path `"unshare(CLONE_NEWUTS) → ksys_unshare() → unshare_nsproxy_namespaces() → create_new_namespaces() → switch_task_namespaces()"`; observe `lsns; ls -l /proc/self/ns`; trap: "`unshare(CLONE_NEWPID)` does not move the caller. Only its *next child* becomes PID 1 in the new namespace, which is why `unshare --pid` needs `--fork`."
- **References:** `man 7 namespaces`, `man 2 unshare`, `man 2 setns`; Kerrisk's LWN series "Namespaces in operation" (2013, annotated as older than time and cgroup namespaces); `<Src file="kernel/nsproxy.c" symbol="create_new_namespaces" />`.

**Task-specific:** context7: OCI runtime spec / runc (for the WAH's runtime) and the Docker/Podman CLI. Verify `nsproxy`, `css_set`, `ns_common`, `ksys_unshare`, `unshare_nsproxy_namespaces`, `create_new_namespaces`, `switch_task_namespaces`, the eight flag values, and `clone3`. Commit: `docs: write what a container actually is and the namespaces overview`.

---

## Task 11: Folder 15 — mount and PID namespaces, and user namespaces

### `mount-and-pid-namespaces.md` — Mount and PID Namespaces **[WAH]** **[Misc]**

- **Opens with:** two namespaces cause most of the surprises. The mount namespace copies the mount table, but mounts can still propagate between copies unless the container runtime says otherwise. The PID namespace gives a container its own PID 1, and PID 1 has duties ordinary processes do not: it must reap orphans and it ignores signals it has not asked for. Containers rediscovered both problems the hard way.
- **Sections:** `## Mount namespaces from the container side` (copy-on-unshare; propagation recap **by link** to `../11-vfs-and-filesystems/mounts-and-mount-namespaces.md` — do not re-teach shared/slave/private; why runtimes make `/` `rprivate` or `rslave` first); `## pivot_root versus chroot` (why `chroot` is escapable and `pivot_root` plus unmounting the old root is not); `## PID namespaces nest` (a process has a PID in every ancestor namespace, `NSpid` in `/proc/PID/status`); `## PID 1's duties` (orphan reaping — link `../06-processes-and-threads/exit-zombies-and-orphans.md`; signal default-ignore for PID 1; the namespace dies when PID 1 dies); `## The zombie problem, and tini` (`--init`, `PR_SET_CHILD_SUBREAPER`); `## What actually happens`.
- **WAH:** inside `unshare --pid --fork --mount-proc`, run a shell as PID 1 that starts a background child, which double-forks an orphan that exits. Show the zombie accumulating under a non-reaping PID 1 (`sh -c 'exec sleep 1000'` as PID 1 in a test) versus being reaped by a shell that waits. Show `NSpid` for the same process from inside and outside. Cleanup: exit.
- **Misconceptions:** (1) "`chroot` is a security boundary." (2) "`kill -9 1` inside a container kills it." The kernel protects the namespace's init from signals it has no handler for, except from an ancestor namespace. (3) "Zombies in containers are a Docker bug."
- **Anchor:** a `flowchart TB` of nested PID namespaces showing one process with PIDs 1 (child ns), 4231 (parent ns), and the host's number, plus a `sequenceDiagram` of orphan → reparent to the namespace's PID 1 → `wait()` or zombie.
- **KernelFacts:** structure `[["struct pid_namespace", "include/linux/pid_namespace.h"], ["struct upid", "include/linux/pid.h"]]`; path `"exit of PID 1 → zap_pid_ns_processes() → SIGKILL to every task in the namespace"`; observe `grep NSpid /proc/self/status`; trap: "A container whose entrypoint is a script that does not `exec` its main process has a shell as PID 1. `docker stop` sends SIGTERM to the shell, the shell ignores it, and the container is SIGKILLed after the timeout."
- **References:** `man 7 pid_namespaces`, `man 7 mount_namespaces`, `man 2 pivot_root`; the tini README; `<Src file="kernel/pid_namespace.c" symbol="zap_pid_ns_processes" />`.

### `user-namespaces.md` — User Namespaces **[Misc]**

- **Opens with:** a user namespace lets an unprivileged user be root, but only over things that namespace owns. Inside it, UID 0 maps to the user's own UID outside, and capabilities apply only to resources owned by that namespace. This is what makes rootless containers possible. It is also why several distributions restrict it: it exposes large parts of the kernel, previously reachable only by real root, to every user.
- **Sections:** `## UID and GID maps` (`/proc/PID/uid_map` format, the write-once rule, `setgroups` deny, and `newuidmap` plus `/etc/subuid` for ranges); `## Root inside is not root outside` (the capability check is `ns_capable(ns, CAP_X)` against the resource's owning namespace; a file owned by host root stays unwritable); `## Namespaced capabilities`; `## Rootless containers` (mapping ranges, the networking limitations — slirp4netns/pasta — and the storage caveats: fuse-overlayfs historically, native overlayfs in user namespaces since 5.11); `## The attack-surface trade-off` (unprivileged users can now reach code paths gated on `CAP_NET_ADMIN`/`CAP_SYS_ADMIN` in their own namespace; many kernel CVEs were reachable only this way; `kernel.unprivileged_userns_clone` (Debian patch) and Ubuntu's AppArmor restriction `kernel.apparmor_restrict_unprivileged_userns`. **State exactly which is upstream and which is a distribution patch**).
- **Review Focus #2 lives here:** state the Ubuntu 24.04+ restriction, the exact error a reader sees (`unshare: write failed /proc/self/uid_map: Operation not permitted`, or whatever the measured message is), and how to check the sysctl. Run `unshare --user --map-root-user id` on the Debian VM and record the measured output. Do not claim behaviour on Ubuntu that was not observed; phrase it as "Ubuntu documents…" and cite the Ubuntu source.
- **Misconceptions:** (1) "Rootless containers are as isolated as rootful ones, just safer." Safer against host-root compromise, but with more kernel surface exposed to the user. (2) "Root inside a user namespace can load modules." (3) "The UID map can be changed later."
- **Anchor:** a two-column mapping diagram (Mermaid `flowchart LR`): inside UIDs 0–65535 → outside 100000–165535, with uid 0 ↔ the user's own uid. Plus a WaveDrom-free table of the three `uid_map` fields.
- **KernelFacts:** structure `[["struct user_namespace", "include/linux/user_namespace.h"], ["struct uid_gid_map", "include/linux/user_namespace.h"]]`; path `"write(/proc/PID/uid_map) → proc_uid_map_write() → map_write() → new_idmap_permitted()"`; observe `cat /proc/self/uid_map; unshare --user --map-root-user cat /proc/self/uid_map`; trap: "`ns_capable()` and `capable()` are different checks. A driver or filesystem that uses the namespaced form where it should use the global one hands real privilege to any unprivileged user."
- **References:** `man 7 user_namespaces`, `man 1 newuidmap`; the Ubuntu blog or security notice on the unprivileged-userns restriction (dated); Kerrisk LWN "Namespaces in operation, part 5"; `<Src file="kernel/user_namespace.c" symbol="map_write" />`.

**Task-specific:** context7: Docker/Podman CLI for rootless. Verify `pid_namespace`, `upid`, `zap_pid_ns_processes`, `PR_SET_CHILD_SUBREAPER`, `user_namespace`, `uid_gid_map`, `proc_uid_map_write`, `map_write`, `new_idmap_permitted`, `ns_capable`, and both sysctl names (and whether each exists upstream at v6.18). Commit: `docs: write the mount, PID, and user namespace pages`.

---

## Task 12: Folder 15 — cgroup v2, and cgroup controllers in practice

### `cgroup-v2-architecture.md` — cgroup v2 **[WAH]** **[Misc]**

- **Opens with:** a cgroup is a node in one tree that every process belongs to, and controllers hang resource rules on the nodes. cgroup v1 had a separate tree per controller, which made "this service's CPU and memory" ambiguous. v2 has a single tree with a few strict rules, and on a modern distribution systemd owns it.
- **Sections:** `## v1 versus v2` — `<Tabs>` with **cgroup v1** and **cgroup v2** tabs: mount layout, one tree versus many, and the thread-granularity differences; `## The interface files` (`cgroup.procs`, `cgroup.controllers`, `cgroup.subtree_control`, `cgroup.events`, `cgroup.type`); `## The no-internal-process rule`; `## Enabling controllers down the tree`; `## Delegation` (what an unprivileged delegate may do, and the `nsdelegate` mount option); `## systemd owns the tree` (slices, scopes and services, `Delegate=yes`, and why writing to `/sys/fs/cgroup` behind systemd's back gets undone); `## The cgroup namespace`.
- **WAH:** on the Debian VM, `systemd-run --user --scope -p MemoryMax=50M bash`, or the system equivalent. Find it with `systemd-cgls` and `cat /proc/self/cgroup`, then read its `memory.max` directly in `/sys/fs/cgroup/...`. Cleanup: exit.
- **Misconceptions:** (1) "Docker manages cgroups." On systemd hosts it asks systemd. (2) "A process can be in a parent and a child cgroup at once." (3) "cgroup v1 is gone." It still exists in hybrid setups. State v6.18's state and what Debian ships.
- **Anchor:** the `<Tabs>`, plus a `flowchart TB` tree: root → `system.slice` / `user.slice` / `machine.slice` → services, with `subtree_control` annotated per level.
- **KernelFacts:** structure `[["struct cgroup", "include/linux/cgroup-defs.h"], ["struct cgroup_subsys", "include/linux/cgroup-defs.h"]]`; path `"echo PID > cgroup.procs → cgroup_procs_write() → cgroup_attach_task() → css_set migration → each controller's attach()"`; observe `cat /proc/self/cgroup; systemd-cgls --no-pager | head -30`; trap: "Writing `+memory` to a cgroup's `subtree_control` fails with `EBUSY` if that cgroup still has processes of its own. That is the no-internal-process rule enforcing itself."
- **References:** `https://docs.kernel.org/admin-guide/cgroup-v2.html` (context7: cgroup v2 controller files and semantics); `man 7 cgroups`; `https://systemd.io/CGROUP_DELEGATION/`; `<Src file="kernel/cgroup/cgroup.c" symbol="cgroup_attach_task" />`.

### `cgroup-controllers-in-practice.md` — cgroup Controllers in Practice **[Lab host=qemu]** **[Misc]**

- **Opens with:** five controllers carry most real workloads: `cpu`, `memory`, `io`, `pids` and `cpuset`. Each has one or two interface files that matter and a handful that confuse. The most useful signal of all, pressure stall information, is not a controller but a file in every cgroup.
- **Sections:** `## cpu` (**by link** to `../07-scheduling/cgroup-cpu-control.md` for `cpu.weight`/`cpu.max`; add only `cpu.max.burst` and `cpu.stat` throttling counters); `## memory` (`memory.max` as a hard limit with OOM, `memory.high` as throttling with reclaim, `memory.low`/`min`, `memory.events`, `memory.stat`, `memory.peak`, and `memory.swap.max`; link `08/reclaim-lru-and-kswapd` and `08/the-oom-killer`); `## io` (`io.max` as a hard throttle versus `io.latency` as a target versus `io.weight`, and why `io.latency` protects better; link folder 12); `## pids` (fork-bomb protection, `pids.max`); `## cpuset` (pinning, and memory nodes); `## PSI` (`*.pressure` `some`/`full` and `avg10`, and why it beats utilisation as an overload signal; triggers via `poll`).
- **Lab:** on the Debian VM, `systemd-run --scope -p MemoryHigh=64M -p MemoryMax=128M stress-ng --vm 1 --vm-bytes 200M --timeout 20s` (or a Python allocator if `stress-ng` is absent — say which). Watch `memory.events` (`high`, `max`, `oom_kill` counts) and `memory.pressure` during the run. Then repeat with only `MemoryMax`. Record both measured runs. If it fails: `stress-ng` missing → `apt install stress-ng`.
- **Misconceptions:** (1) "`memory.high` is a soft limit that can be exceeded freely." (2) "High CPU utilisation means the cgroup is overloaded." Read `cpu.pressure`. (3) "`io.max` is the right tool for protecting a latency-sensitive service."
- **Anchor:** a table of controller × the 2–3 files that matter × what each enforces × what happens at the limit. Plus a `flowchart LR` for memory: usage crosses `high` → throttle and reclaim; crosses `max` → reclaim, then OOM in the cgroup.
- **KernelFacts:** structure `[["struct mem_cgroup", "include/linux/memcontrol.h"], ["struct psi_group", "include/linux/psi_types.h"]]`; path `"charge on page fault → try_charge_memcg() → over memory.high: mem_cgroup_handle_over_high() on return to user | over memory.max: reclaim → mem_cgroup_out_of_memory()"`; observe `cat /sys/fs/cgroup/system.slice/memory.pressure`; trap: "A cgroup at its `memory.max` with page cache to reclaim is not out of memory. It is slow. The OOM kill comes only after reclaim fails, so a sluggish service with no OOM in the logs is often exactly this."
- **References:** `https://docs.kernel.org/admin-guide/cgroup-v2.html` (context7); `https://docs.kernel.org/accounting/psi.html`; Facebook/Meta's "PSI" and "oomd" write-ups; `man 5 systemd.resource-control`.

**Task-specific:** context7: cgroup v2 controller files (mandatory). Verify every interface file named against the v6.18 `cgroup-v2.rst`, and verify `cgroup_attach_task`, `cgroup_procs_write`, `try_charge_memcg`, `mem_cgroup_handle_over_high`, `mem_cgroup_out_of_memory`, and `psi_group`. Commit: `docs: write the cgroup v2 architecture and controllers pages`.

---

## Task 13: Folder 15 — capabilities in containers, and Lab: build a container from scratch

**Run the lab first** (spec Phase 4 step 4). Steps 1–4 build and run `minicontainer`; both pages are written from what it needed.

**Files:**
- Create: `static/code/linux/minicontainer/minicontainer.c`, `setup-rootfs.sh`, `Makefile`
- Modify: `docs/linux/15-containers-and-virtualization/capabilities-in-containers.md`, `docs/linux/15-containers-and-virtualization/building-a-container-from-scratch.md`

**Interfaces:**
- Consumes: Tasks 10–12. `16/capabilities` and `16/seccomp` are still stubs at this point, which is fine for the build. Link them, but explain only the container angle here, because folder 16 owns the model.
- Produces: `minicontainer`, which `15/container-networking` (Task 14) extends with a bridge and NAT, and `16/seccomp` (Task 18) references as a worked example.

**Program behaviour (the spec of the code):** `minicontainer <rootfs> <cmd> [args…]`, run as root on the Debian VM, does the following, in order, each step checked and failing loudly with `perror`:
1. Creates a cgroup `/sys/fs/cgroup/minicontainer-<pid>` and writes `memory.max = 64M` and `pids.max = 64`. On a systemd host, use a systemd-delegated subtree if writing directly is undone; record what was needed.
2. `clone()` with `CLONE_NEWNS|CLONE_NEWPID|CLONE_NEWUTS|CLONE_NEWIPC|CLONE_NEWNET|SIGCHLD`. The parent moves the child's PID into the cgroup and creates a veth pair (`ip link add` via `system()` is acceptable on the page — say it is, and that a real runtime uses netlink). It moves one end into the child's netns, assigns `10.200.0.1/24` and `10.200.0.2/24`, and signals the child through a pipe.
3. In the child: wait on the pipe; `sethostname("minicontainer")`; `mount(NULL, "/", NULL, MS_REC|MS_PRIVATE, NULL)`; bind-mount the rootfs onto itself; `pivot_root` into it; `umount2(old, MNT_DETACH)`; mount `proc` on `/proc`.
4. Drop capabilities. Clear the bounding set except a docker-like default (`CAP_CHOWN`, `CAP_DAC_OVERRIDE`, `CAP_FOWNER`, `CAP_FSETID`, `CAP_KILL`, `CAP_SETGID`, `CAP_SETUID`, `CAP_SETPCAP`, `CAP_NET_BIND_SERVICE`, `CAP_NET_RAW`, `CAP_SYS_CHROOT`, `CAP_MKNOD`, `CAP_AUDIT_WRITE`, `CAP_SETFCAP` — **check Docker's current default list via context7 and use that**) via `prctl(PR_CAPBSET_DROP)`, then `capset`. Use raw syscalls and no libcap, so the page has no extra dependency, or libcap if raw `capset` proves unreadable. Decide once and say why.
5. `prctl(PR_SET_NO_NEW_PRIVS, 1)`, then install a seccomp-BPF filter that checks `AUDIT_ARCH_X86_64` first and returns `SECCOMP_RET_ERRNO|EPERM` for `keyctl`, `add_key`, `request_key`, `unshare`, `mount`, `umount2`, `ptrace`, `kexec_load`, `init_module`, `finit_module` and `bpf`, allowing everything else. This is a small denylist for teaching; the page says real runtimes ship an allowlist.
6. `execvp(cmd)`.

`setup-rootfs.sh` downloads the Alpine minirootfs tarball for x86_64 (its URL is pinned in the script with the version, and the SHA-256 is checked) into `./rootfs`. Downloaded archives are untrusted: extract into a new empty directory.

- [ ] **Step 1: Write the three files.** Aim for about 150 lines of C (spec) — under 250 is acceptable if correctness needs it. Report the real count.
- [ ] **Step 2: Build and run on the Debian VM.** `./setup-rootfs.sh && make && sudo ./minicontainer ./rootfs /bin/sh`. Inside, run and record: `hostname`; `ps` (only PIDs 1 and 2); `cat /proc/self/status | grep -E 'Cap|Seccomp|NoNewPrivs'`; `ip addr`; `ping -c1 10.200.0.1`; `mount -t tmpfs x /mnt` (expect `EPERM` from seccomp); a memory hog (`head -c 200M /dev/zero | tail` or similar) killed by the cgroup. Outside: `cat /sys/fs/cgroup/minicontainer-*/memory.events`. Save the full transcript.
- [ ] **Step 3: Write the cleanup** — the cgroup `rmdir` and the veth deletion. The veth disappears with the netns, but say so. Confirm that the host state after cleanup matches the state before: `ip link`, `ls /sys/fs/cgroup | grep minicontainer`.
- [ ] **Step 4: Record what the lab required that the plan did not foresee** (systemd interaction, a missing `/dev`, `pivot_root`'s `EINVAL` conditions) in a scratch list. Those items become `:::note`s on the lab page — spec step 4: "what the lab turns out to require reshapes the pages around it."

### `capabilities-in-containers.md` — Capabilities and Container Privilege **[WAH]** **[Misc]**

- **Opens with:** a container started by root runs as root, so what stops it doing everything root can? Mostly the capability set. Runtimes drop about two-thirds of root's capabilities by default. `--privileged` puts them all back and turns off the other guards too. This page shows what the default keeps, what `--privileged` actually disables, and which capabilities are root by another name.
- **Sections:** `## The default set` (a table from Docker's current default and runc's; context7); `## What --privileged turns off` (all capabilities, no seccomp, no AppArmor/SELinux confinement, all devices, and writable `/sys` and `/proc` paths — **list from the runtime's documentation, not memory**); `## no_new_privs` (why setuid binaries inside cannot regain dropped capabilities, and its interaction with seccomp); `## Capabilities that are root` (`CAP_SYS_ADMIN` — mount, namespaces, BPF historically, and a long tail; `CAP_SYS_MODULE` — loading kernel code; `CAP_BPF`/`CAP_PERFMON`; `CAP_SYS_PTRACE`; `CAP_DAC_READ_SEARCH`'s `open_by_handle_at` history. **Describe the mechanism by which each is root-equivalent in one sentence, with no procedure.** This is Review Focus #4); `## Rootless changes the question` (link `./user-namespaces.md`).
- **WAH:** run `podman run --rm alpine grep Cap /proc/self/status` and then the same with `--privileged`, decoding both with `capsh --decode`. Add `grep Seccomp` for both. Measured.
- **Misconceptions:** (1) "`--privileged` just grants extra capabilities." (2) "Dropping `CAP_SYS_ADMIN` is enough." (3) "Capabilities inside a user namespace are real capabilities."
- **Anchor:** a WaveDrom `reg` of the 64-bit effective set, with the default container set highlighted (bit positions from `include/uapi/linux/capability.h`), plus a table: flag/setting × what it disables.
- **KernelFacts:** structure `[["kernel_cap_t", "include/linux/capability.h"], ["struct cred (cap_* fields)", "include/linux/cred.h"]]`; path `"execve() → bprm_creds_from_file() → cap_bprm_creds_from_file() → new effective = f(permitted, bounding, file caps, no_new_privs)"`; observe `grep Cap /proc/self/status | capsh --decode=$(awk '/CapEff/{print $2}' /proc/self/status)`; trap: "A container granted `CAP_SYS_ADMIN` 'just to mount something' has been granted most of root. Grant the narrowest capability or mount from outside."
- **References:** `man 7 capabilities`; Docker's "Runtime privilege and Linux capabilities" docs (context7: Docker CLI); runc's default spec (`runc spec` output, measured); `<Src file="security/commoncap.c" symbol="cap_bprm_creds_from_file" />`.

### `building-a-container-from-scratch.md` — Lab: Build a Container from Scratch **[Lab host=qemu]**

- **Opens with:** every earlier page in this folder described one ingredient. This lab assembles all of them in about 150 lines of C, in the same order a real runtime does, and ends with a shell that `ps`, `hostname`, `ip` and `mount` all agree is inside a container. Nothing here is a toy version of the mechanism; it *is* the mechanism, without the robustness.
- **Sections:** `## What you will build` (the six steps as a list, each linked to its owning page); `## Prepare a root filesystem` (`setup-rootfs.sh`, embedded); `## The code` (`minicontainer.c` embedded verbatim, then walked step by step in `###` subsections matching the six steps); `## Run it` (the measured Step 2 transcript, annotated); `## What runc does that this does not` (user namespaces, cgroup via systemd, an allowlist seccomp profile, `/dev` setup, masked `/proc` paths, rlimits, hooks — the bridge to `./images-layers-and-oci.md`); `## Clean up`; and the Step 4 notes as `:::note`s.
- **Lab block:** `host="qemu"` (Debian VM). It needs root, so it carries a `:::warning` saying it changes host network and cgroup state until cleanup — **not** `:::danger`, since nothing is lost. If it fails: `pivot_root: Invalid argument` means the new root is not a mount point or `/` is shared; the code's bind-mount and `MS_PRIVATE` steps exist for exactly this.
- **Anchor:** a `sequenceDiagram` — parent / child / kernel across the six steps, with the pipe synchronisation point where the parent finishes cgroup and veth setup before the child proceeds.
- **KernelFacts:** structure `[["struct nsproxy", "include/linux/nsproxy.h"], ["struct seccomp_filter", "kernel/seccomp.c"]]`; path `"clone(CLONE_NEW*) → [parent: cgroup.procs, veth] → pivot_root() → capset() → prctl(NO_NEW_PRIVS) → seccomp(SET_MODE_FILTER) → execvp()"`; observe `sudo ./minicontainer ./rootfs /bin/sh -c 'grep -E "Cap|Seccomp" /proc/self/status'`; trap: "Order matters. Install the seccomp filter after `pivot_root` and the mounts, because the filter denies `mount`, and drop capabilities before `exec`, because a capability dropped after `exec` was never dropped for the new program's first instructions."
- **References:** `man 2 clone`, `man 2 pivot_root`, `man 2 seccomp`; Liz Rice, *Container Security* (O'Reilly, 2020), ch. 4; the runc `libcontainer` init (`nsexec.c`/`init_linux.go`) on GitHub as "the production version of this lab".

- [ ] **Step 5: Write `capabilities-in-containers.md`, then the lab page.** The embedded code must be byte-identical to the files.
- [ ] **Step 6:** Writing-task procedure (context7: Docker CLI default capabilities, runc/OCI runtime spec; verify `kernel_cap_t`, `cap_bprm_creds_from_file`, `bprm_creds_from_file`, `PR_CAPBSET_DROP`, `PR_SET_NO_NEW_PRIVS`, `SECCOMP_RET_ERRNO`, `AUDIT_ARCH_X86_64`, `seccomp_filter`, and every capability bit position).
- [ ] **Step 7: Lint and commit**

```bash
rtk run 'npm run lint'
git add static/code/linux/minicontainer docs/linux/15-containers-and-virtualization
git commit -m "docs: write the container privilege page and the build-a-container lab"
```

---

## Task 14: Folder 15 — images and OCI, and container networking

### `images-layers-and-oci.md` — Images, Layers, and the OCI Runtime

- **Opens with:** the lab built a container from one extracted tarball. A real image is a stack of tarballs plus a JSON config, and it is unpacked into overlayfs lower directories so a hundred containers can share them. The OCI specifications standardise both halves: what an image is, and what a runtime must do with a bundle. runc is the reference runtime, and everything above it is image management.
- **Sections:** `## An image is layers plus config` (manifest, config, layer digests, and content addressing); `## Layers as overlayfs lowerdirs` (**by link** to `../11-vfs-and-filesystems/overlayfs.md`; show a real `mount | grep overlay` from the VM with its `lowerdir=` stack); `## The OCI runtime spec` (bundle = `config.json` + rootfs; show a ` ```json ` excerpt of `runc spec` output: `process`, `root`, `mounts`, `linux.namespaces`, `linux.resources`, `linux.seccomp`, mapped to the lab's steps); `## What runc does with a bundle` (create/start/state/delete and the `runc init` re-exec trick); `## The stack above` (containerd and shims, CRI, Docker, Podman's daemonless model, crun/youki as alternative runtimes).
- **Anchor:** a `flowchart TB` — docker/podman CLI → containerd/conmon → shim → runc → kernel (namespaces, cgroups, overlayfs, seccomp), with each arrow labelled by what crosses it. Plus a table: OCI `config.json` field → kernel mechanism → owning page.
- **KernelFacts:** structure `[["struct ovl_fs", "fs/overlayfs/ovl_entry.h"], ["clone3 args", "include/uapi/linux/sched.h"]]`; path `"runc create → runc init (re-exec, nsexec) → namespaces + cgroup → waits on exec.fifo → runc start → execve(process.args)"`; observe `mount -t overlay | head -3`; trap: "Deleting files in a later layer does not shrink the image. The bytes stay in the lower layer and a whiteout hides them. Secrets added then removed in a Dockerfile are still in the image."
- **References:** the OCI image spec and runtime spec on GitHub (context7: OCI); `man 8 runc` / runc README; containerd architecture docs; Docker storage-driver docs on overlay2.

### `container-networking.md` — Container Networking **[Lab host=qemu]**

- **Opens with:** a container's default network is a private network namespace with one end of a veth pair, a bridge on the host, and a masquerade rule. Folder 13 built every one of those pieces. This page assembles them the way Docker's default bridge does, adds port publishing as a DNAT rule, and explains why traffic between hosts needs something more.
- **Sections:** `## The default model` (netns + veth + bridge + masquerade; **links**, not re-teaching, to `13/network-namespaces-and-virtual-devices` and `13/connection-tracking-and-nat`); `## Built by hand` (the lab); `## Port publishing is DNAT`; `## CNI in one section` (plugin model, `bridge`, `host-local` IPAM, and the plugin chain); `## Across hosts: why an overlay` (VXLAN encapsulation, routed alternatives, and where Kubernetes CNIs differ); `## Rootless networking` (slirp4netns/pasta, briefly).
- **Lab:** on the Debian VM, two namespaces `c1` and `c2`, a bridge `br-lab` at `10.201.0.1/24`, veths, `ip_forward`, and an nftables table `lab` with a masquerade rule and a DNAT rule publishing `c1:8080` on host port 18080 (`python3 -m http.server` in `c1`). Measured: `ip netns exec c2 ping 10.201.0.2`, `curl` from the host to `localhost:18080`, and `conntrack -L` showing the DNAT entry. **Cleanup block** deletes the namespaces, the bridge and `table inet lab`, and restores `ip_forward` to its prior value (save it first). If it fails: nothing reaches the outside → check the masquerade's `oifname` matches the VM's uplink.
- **Anchor:** a `flowchart LR` of the whole packet path for a published port: client → host eth0 → prerouting DNAT → bridge → veth → c1, and return via conntrack un-NAT.
- **KernelFacts:** structure `[["struct veth_priv", "drivers/net/veth.c"], ["struct net_bridge", "net/bridge/br_private.h"]]`; path `"host:18080 → nf_nat_ipv4_pre_routing (DNAT) → br_handle_frame → veth_xmit → c1 netns → socket"`; observe `nft list table inet lab; bridge link`; trap: "With `br_netfilter` loaded, bridged traffic also traverses iptables/nftables `FORWARD`. Container traffic can then be dropped by a host firewall rule that appears to have nothing to do with bridges."
- **References:** the CNI specification (GitHub containernetworking/cni); Docker's bridge networking docs (context7: Docker CLI); `man 8 ip-netns`; `https://docs.kernel.org/networking/vxlan.html`.

**Task-specific:** context7: OCI runtime spec / runc, Docker CLI, plus nftables syntax (re-checked from Phase 3). Verify `ovl_fs`, `veth_priv`, `net_bridge`, `br_handle_frame`, `veth_xmit`, the nf_nat hook function name at v6.18, and the `br_netfilter` sysctl names. Commit: `docs: write the OCI images and container networking pages`.

---

## Task 15: Folder 15 — KVM, and virtio

### `kvm-and-hardware-virtualization.md` — KVM **[WAH]** **[Misc]**

- **Opens with:** KVM turns the kernel into a hypervisor with very little new machinery. A VM is a process, each virtual CPU is a thread, guest memory is ordinary process memory, and the whole interface is ioctls on file descriptors from `/dev/kvm`. The hardware support from the CS backfill page does the hard part. KVM's job is the loop around `VMRUN`/`VMRESUME`, and QEMU's job is everything the loop hands back to user space.
- **Sections:** `## The file-descriptor hierarchy` (`/dev/kvm` → `KVM_CREATE_VM` → VM fd → `KVM_CREATE_VCPU` → vCPU fd, and the mmap'd `kvm_run`); `## Guest memory is process memory` (`KVM_SET_USER_MEMORY_REGION`, EPT/NPT built from the host's page tables; link the CS backfill); `## The run loop` (`KVM_RUN` → enter guest → exit → handled in kernel or returned to user space with `exit_reason`); `## VM exits and where they are handled` (a table: exit reason × handled in KVM or QEMU × typical cause); `## Where QEMU fits` (device emulation, the machine model, and `-accel kvm` versus TCG; link folder 01's QEMU invocation); `## What actually happens`.
- **WAH:** a ~100-line C program (embedded, run on the Debian VM with nested virtualization, or on the host if the VM lacks `/dev/kvm` — say which) that creates a VM, maps one page of guest memory containing a handful of real-mode instructions that `out` a byte to port `0x3f8` and `hlt`, runs it, and prints `KVM_EXIT_IO` with the byte and then `KVM_EXIT_HLT`. This is the canonical minimal KVM example. **Credit the LWN "Using the KVM API" article it follows.** Also show `perf kvm stat` or `/sys/kernel/debug/kvm` exit counts for a running QEMU guest if available.
- **Misconceptions:** (1) "KVM is a type-2 hypervisor because it runs inside Linux." State the honest answer: the taxonomy fits poorly. (2) "QEMU is slow emulation." With KVM it runs only device models. (3) "Every guest instruction is trapped."
- **Anchor:** a `sequenceDiagram` — QEMU vCPU thread → `ioctl(KVM_RUN)` → KVM → VM entry → guest runs → VM exit (I/O) → KVM decides: in-kernel handling → re-enter, or return `KVM_EXIT_IO` → QEMU emulates → `KVM_RUN` again. Plus a struct-shape diagram of `struct kvm_run` (the dozen fields that matter).
- **KernelFacts:** structure `[["struct kvm_run", "include/uapi/linux/kvm.h"], ["struct kvm_vcpu", "include/linux/kvm_host.h"]]`; path `"ioctl(vcpu_fd, KVM_RUN) → kvm_vcpu_ioctl() → kvm_arch_vcpu_ioctl_run() → vcpu_run() → vmx_vcpu_run() | svm_vcpu_run() → exit handler"`; observe `ls -l /dev/kvm; grep -c -E 'vmx|svm' /proc/cpuinfo`; trap: "Nested virtualization (KVM inside a VM) works, but every L2 exit costs several L1 exits. Benchmarks taken inside a cloud VM's nested guest say little about bare-metal KVM."
- **References:** `https://docs.kernel.org/virt/kvm/api.html`; LWN "Using the KVM API" (2015, annotated); `<Src file="virt/kvm/kvm_main.c" symbol="kvm_vcpu_ioctl" />`; the QEMU docs on accelerators.

### `virtio-and-paravirtualization.md` — virtio and Paravirtual Devices

- **Opens with:** emulating a real network card means trapping every register access the guest driver makes, and real drivers make many. virtio drops the pretence. The guest knows it is virtualized, and guest and host share rings of buffer descriptors in guest memory, so a whole batch of I/O costs one notification. vhost goes further and moves the host side of the ring into the host kernel, so packets never visit QEMU at all.
- **Sections:** `## Why emulation is slow` (exit count per packet with an emulated e1000 versus virtio — a cited figure or a measured `perf kvm stat` comparison, not a guess); `## Virtqueues` (descriptor table, available ring, used ring, notifications and their suppression; the packed-ring variant in one paragraph; the virtqueue is DMA, which is why the DMA API applies — link `14/the-dma-api`); `## The device family` (net, blk, scsi, fs/virtiofs, gpu, vsock, balloon, rng — a table); `## Transports` (virtio-pci, virtio-mmio); `## vhost: the datapath in the kernel` (vhost-net, ioeventfd/irqfd, and vhost-user to a user-space switch); `## Back to folder 01` (decode each virtio flag in folder 01's QEMU command line; link it).
- **Anchor:** a `flowchart LR` of a virtio-net transmit with and without vhost (guest driver → avail ring → kick (ioeventfd) → QEMU or vhost-net thread → tap → host stack), plus a table of the virtqueue's three parts × who writes × who reads.
- **KernelFacts:** structure `[["struct vring_desc", "include/uapi/linux/virtio_ring.h"], ["struct virtqueue", "include/linux/virtio.h"]]`; path `"guest: virtqueue_add_outbuf() → virtqueue_kick() → MMIO/PIO notify → (vhost) ioeventfd → handle_tx() → tap"`; observe `lspci -nn | grep -i virtio; ls /sys/bus/virtio/devices`; trap: "virtio devices bind to the `virtio` bus, not directly to PCI. `lspci -k` shows `virtio-pci`, and the real driver (`virtio_net`, `virtio_blk`) is one level down in `/sys/bus/virtio`."
- **References:** the OASIS virtio specification (current version — check it); `https://docs.kernel.org/driver-api/virtio/virtio.html`; Rusty Russell, "virtio: Towards a De-Facto Standard For Virtual I/O Devices" (2008); `<Src file="drivers/virtio/virtio_ring.c" symbol="virtqueue_add_outbuf" />`.

**Task-specific:** run the KVM WAH program before writing the page; if no environment has `/dev/kvm`, mark the WAH as source-reading only and say so. Verify `KVM_CREATE_VM`, `KVM_SET_USER_MEMORY_REGION` (and whether `_2` is the current form), `kvm_vcpu_ioctl`, `kvm_arch_vcpu_ioctl_run`, `vcpu_run`, `vmx_vcpu_run`, `svm_vcpu_run`, `vring_desc`, `virtqueue_add_outbuf`, `virtqueue_kick`, and `handle_tx` in `drivers/vhost/net.c`. Commit: `docs: write the KVM and virtio pages`.

---
## Task 16: Folder 16 — permissions, credentials in the kernel, and capabilities

**Interfaces:**
- Consumes: `06/credentials-and-identity`, which owns the process-side view. `16/credentials-in-the-kernel` goes deeper and **links to it rather than repeating it**. Read it first and list what it already says.
- Produces: `16/capabilities`, a prerequisite of `15/capabilities-in-containers`. That page was written in Task 13, so check that it still agrees with this one and fix whichever is wrong.

### `the-unix-permission-model.md` — The UNIX Permission Model **[WAH]** **[Misc]**

- **Opens with:** the classic model is twelve bits and a fixed check order, and most permission surprises come from not knowing that order. The kernel finds the *first* class that matches (owner, then group, then other) and uses only that class's bits, even if a later class would allow more. Directories reuse the same bits with different meanings. Everything later in this folder layers on top of this check rather than replacing it.
- **Sections:** `## Mode bits and the check order` (owner → group → other, first match wins, and root's `CAP_DAC_OVERRIDE` bypass with its exception for execute); `## Directories` (`r` lists names, `w` creates/deletes/renames entries, `x` traverses; `x` without `r` and `r` without `x`); `## setuid, setgid, sticky` (setgid on directories for group inheritance, sticky on `/tmp`); `## umask`; `## POSIX ACLs` (the mask entry, `getfacl`/`setfacl`, and how the mask caps named entries); `## What actually happens`.
- **WAH:** demonstrate first-match-wins: a file mode `0407` owned by the user, where the owner is denied though "other" is allowed. Show `ls -l`, the `EACCES`, and `strace -e openat`. Then a directory with `r` but no `x` (`ls` lists names with `?` attributes). All of it runs in a temp dir, and the cleanup is `rm -rf`.
- **Misconceptions:** (1) "Owner gets the union of the owner, group and other bits." (2) "Deleting a file needs write permission on the file." It needs write permission on the directory. (3) "Root can execute any file." Only if some execute bit is set.
- **Anchor:** a WaveDrom `reg` of the 16-bit `st_mode` (file type 4 bits, setuid/setgid/sticky, rwx×3), plus a `flowchart TD` of `generic_permission`'s order: owner? → group or ACL? → other → capability override.
- **KernelFacts:** structure `[["struct inode (i_mode, i_uid, i_gid)", "include/linux/fs.h"], ["struct posix_acl", "include/linux/posix_acl.h"]]`; path `"may_open() → inode_permission() → generic_permission() → acl_permission_check() → capable_wrt_inode_uidgid()"`; observe `stat -c '%A %a %U %G %n' /tmp /usr/bin/passwd`; trap: "`chmod 777` on a directory without the sticky bit lets anyone delete anyone's files in it. `/tmp` is `1777` for this reason."
- **References:** `man 7 inode` (mode bits), `man 5 acl`; `<Src file="fs/namei.c" symbol="generic_permission" />`; APUE (Stevens & Rago) ch. 4.

### `credentials-in-the-kernel.md` — Credentials in the Kernel **[Misc]**

- **Opens with:** every permission check reads one structure, the task's `struct cred`, and the kernel never modifies one in place. Changing identity means building a new `cred` and swapping the pointer, so code holding the old one under RCU keeps a consistent view. Real, effective, saved and filesystem IDs all live there, with a capability set and a security label. The classic privilege-drop bugs are all about which of those IDs a call actually changed.
- **Sections:** `## struct cred, in shape` (struct-shape diagram: the ID fields, the capability sets, `user_ns`, `security`, `group_info`, and the `cred` versus `real_cred` pair on `task_struct`); `## Four IDs and why each exists` (**link** `06/credentials-and-identity` for the basics; this section covers only fsuid's NFS origin and the saved ID's purpose); `## Transitions` (`setuid` versus `seteuid` versus `setresuid` semantics depending on privilege, and a table of the classic mistakes: dropping effective but not saved, dropping UID before groups, and not checking the return value); `## Copy, modify, commit` (`prepare_creds` → modify → `commit_creds`, and `override_creds` for temporary borrowing); `## RCU and credentials` (readers via `current_cred()`/`rcu_dereference`, and `get_cred` to keep one; link `09/rcu-in-practice`).
- **Misconceptions:** (1) "`setuid(getuid())` always drops privilege permanently." (2) "A task has one credential." (3) "Credentials can be edited in place under a lock."
- **Anchor:** a struct-shape `classDiagram` of `cred`, plus a `sequenceDiagram` of `prepare_creds` → modify → `commit_creds` with an RCU reader on the old copy.
- **KernelFacts:** structure `[["struct cred", "include/linux/cred.h"], ["struct group_info", "include/linux/cred.h"]]`; path `"setresuid() → __sys_setresuid() → prepare_creds() → modify uid/euid/suid/fsuid → commit_creds() → rcu_assign_pointer(task->cred)"`; observe `grep -E '^(Uid|Gid|Groups)' /proc/self/status`; trap: "A setuid-root program that calls `seteuid(user)` has *not* dropped privilege. The saved UID is still 0 and any later code can `seteuid(0)` back. Permanent drops need `setresuid` with all three set."
- **References:** `https://docs.kernel.org/security/credentials.html`; `man 2 setresuid`; Chen, Wagner & Dean, "Setuid Demystified" (USENIX Security 2002); `<Src file="kernel/cred.c" symbol="commit_creds" />`.

### `capabilities.md` — Capabilities **[WAH]** **[Misc]**

- **Opens with:** capabilities split root's single all-powerful check into about forty named privileges, so a program that needs to bind port 80 does not also get to load kernel modules. The idea is sound. The execution has five per-thread sets with transition rules on `execve`, and several capabilities that are as good as root in practice. This page covers both honestly.
- **Sections:** `## The five sets` (permitted, effective, inheritable, bounding, ambient — one paragraph each); `## What happens at execve` (the transformation rules as a table, derived from `man 7 capabilities`; file capabilities in `security.capability` xattrs; setuid-root's special casing); `## File capabilities replace setuid` (`setcap cap_net_bind_service+ep`, and `ping` as the classic example — and that many distros now use the `ping_group_range` sysctl instead; check Debian); `## Ambient capabilities`; `## Securebits`; `## The honest assessment` (a table of the root-equivalent capabilities with one-sentence mechanism each — consistent with `15/capabilities-in-containers`, linked; **no procedures**. This is Review Focus #4).
- **WAH:** in a temp dir on the Debian VM, copy `python3` (or a small C program that binds port 80), try to bind 80 as a user (`EACCES`), `setcap cap_net_bind_service+ep` on the copy, and bind succeeds. Show `getcap` and `/proc/<pid>/status` Cap lines. Cleanup: delete the copy.
- **Misconceptions:** (1) "`CAP_NET_BIND_SERVICE`-style fine-grained capabilities make root unnecessary everywhere." (2) "Inheritable means children inherit it." (3) "Removing a capability from the effective set is permanent."
- **Anchor:** a `flowchart LR` of the execve transformation: P(old), I(old), bounding, ambient, file F(p), F(i), F(e) → P(new), E(new), I(new), A(new), labelled with the formulas from the man page.
- **KernelFacts:** structure `[["kernel_cap_t", "include/linux/capability.h"], ["struct cpu_vfs_cap_data", "include/linux/capability.h"]]`; path `"execve() → bprm_creds_from_file() → security_bprm_creds_from_file() → cap_bprm_creds_from_file() → get_file_caps()"`; observe `getcap -r /usr/bin /usr/sbin 2>/dev/null`; trap: "Copying a binary drops its file capabilities, because the xattr does not follow `cp`. A packaging step that copies binaries silently turns `setcap`'d tools into ones that fail with `EPERM`."
- **References:** `man 7 capabilities` (the authority for the transformation rules); `<Src file="security/commoncap.c" symbol="cap_bprm_creds_from_file" />`; grsecurity's "False Boundaries and Arbitrary Code Execution" post (on root-equivalent capabilities; annotate its age); `man 8 setcap`.

**Task-specific:** context7: none mandated for these three. Verify `generic_permission`, `acl_permission_check`, `capable_wrt_inode_uidgid`, `inode_permission`, `prepare_creds`, `commit_creds`, `override_creds`, `__sys_setresuid`, `cpu_vfs_cap_data`, `get_file_caps`, `security_bprm_creds_from_file`, and the capability count at v6.18 (`CAP_LAST_CAP`). Commit: `docs: write the permission model, kernel credentials, and capabilities pages`.

---

## Task 17: Folder 16 — the LSM framework, SELinux, and AppArmor

### `the-lsm-framework.md` — The LSM Framework

- **Opens with:** after the permission bits and capabilities say yes, the kernel asks one more question at almost every security-relevant point: does any loaded security module object? The Linux Security Module framework is that set of hooks. A module can only add restrictions, never grant what the base checks refused, and several modules can now be stacked.
- **Sections:** `## Hooks at every decision` (`security_file_open`, `security_bprm_check`, `security_socket_connect`, … — a table of hook family × example hook × call site); `## Restrict only` (why `return 0` from every module is "no objection" and the DAC check already happened); `## Security blobs` (per-object `security` pointers, and blob-size accounting for stacking); `## Stacking and ordering` (`lsm=` boot parameter, `CONFIG_LSM`, major versus minor modules, and the current exclusivity limits); `## The modules today` (a table: capability, Yama, SELinux, AppArmor, Smack, TOMOYO, Landlock, Lockdown, LoadPin, SafeSetID, BPF, IPE — one line each, and which are "exclusive"); `## LSM syscalls` (`lsm_list_modules` etc. — verify at v6.18).
- **Anchor:** a `flowchart TD` — `open()` → DAC check → capability check → `security_file_open()` → for each LSM in order → any non-zero denies → open proceeds. Plus the modules table.
- **KernelFacts:** structure `[["struct security_hook_list", "include/linux/lsm_hooks.h"], ["struct lsm_info", "include/linux/lsm_hooks.h"]]`; path `"do_dentry_open() → security_file_open() → call_int_hook(file_open, file) → each LSM's hook"`; observe `cat /sys/kernel/security/lsm`; trap: "An LSM denial and a DAC denial both return `EACCES`/`EPERM`. If the permission bits look correct and access still fails, check the LSM audit log before the file modes."
- **References:** `https://docs.kernel.org/security/lsm.html`; `https://docs.kernel.org/admin-guide/LSM/index.html`; Wright et al., "Linux Security Modules: General Security Support for the Linux Kernel" (USENIX Security 2002); `<Src file="security/security.c" symbol="security_file_open" />`.

### `selinux.md` — SELinux **[WAH]** **[Lab host=qemu]** **[Misc]**

- **Opens with:** SELinux labels every process and every object, then checks every access against a policy written in terms of those labels, not paths or users. A web server process of type `httpd_t` may read files of type `httpd_sys_content_t` because a rule says so, and nothing else. The everyday skill is not writing policy. It is reading a denial and deciding which of three fixes it calls for.
- **Sections:** `## Type enforcement` (subject type, object type, class, permission, and allow rules); `## Contexts` (`user:role:type:level`, `ls -Z`, `ps -Z`, and that type is what matters day to day); `## Policy, modules, and booleans`; `## Enforcing, permissive, disabled` — `stateDiagram-v2`, with permissive domains as a per-type escape hatch; `## Reading an AVC denial` (every field of a real AVC line explained); `## Three fixes` (relabel with `restorecon`/`semanage fcontext`, set a boolean, write a local module with `audit2allow`, and why `audit2allow` blindly is the wrong default); `## What actually happens`.
- **Lab and WAH:** Debian ships AppArmor by default, so this lab needs SELinux enabled on the Debian VM. **Before writing anything, establish feasibility:**
  - install `selinux-basics selinux-policy-default auditd`;
  - run `selinux-activate`;
  - reboot (the relabel is slow).

  Then serve a file from a non-standard directory with a confined daemon, capture the AVC, and fix it with `semanage fcontext` + `restorecon`. **This lab changes the VM's LSM and relabels its filesystem**, so it carries a `:::danger` stating that: not on a host, only on a disposable VM, and that reverting means `selinux-deactivate` plus a reboot. Snapshot the VM first.

  If SELinux on Debian proves unworkable in reasonable time, use a Fedora cloud image under the same folder-01 QEMU invocation. Record the switch and the reason in the page's lab note.
- **Misconceptions:** (1) "The fix for an AVC denial is `setenforce 0`." (2) "SELinux is about users." It is about types. (3) "`audit2allow` output is safe to load."
- **Anchor:** the `stateDiagram-v2` of modes, plus a WaveDrom-free annotated AVC line as a table (field × meaning × where to look).
- **KernelFacts:** structure `[["struct avc_node", "security/selinux/avc.c"], ["struct task_security_struct", "security/selinux/include/objsec.h"]]`; path `"security_file_open() → selinux_file_open() → file_path_has_perm() → avc_has_perm() → avc cache hit | security_compute_av()"`; observe `ausearch -m avc -ts recent`; trap: "Files moved with `mv` keep their old label, while files created by `cp` get the destination's. A file moved into a web root is denied while an identical copied file works."
- **References:** the SELinux Notebook (SELinuxProject on GitHub); Red Hat's "Using SELinux" guide (context7: SELinux tooling); `man 8 audit2allow`, `man 8 semanage-fcontext`; `<Src file="security/selinux/avc.c" symbol="avc_has_perm" />`.

### `apparmor.md` — AppArmor

- **Opens with:** AppArmor confines programs by path. A profile for `/usr/sbin/nginx` lists the files, capabilities and network access that program may use, and anything not listed is denied. It is easier to read and write than SELinux policy and less expressive. The question is which trade-off fits.
- **Sections:** `## Profiles by path` (attachment by executable path, and the profile language: file rules with permissions, `capability`, `network`, includes and abstractions); `## Complain versus enforce` (`aa-complain`, `aa-enforce`, `aa-logprof`); `## Reading a denial` (`apparmor="DENIED"` audit lines); `## Containers` (`docker-default`, and Ubuntu's userns restriction as an AppArmor feature — link `15/user-namespaces`); `## SELinux versus AppArmor` — `<Tabs>` with **SELinux** and **AppArmor** tabs, each the same policy intent ("nginx may read /srv/www") expressed in that system; then a comparison table: model, label storage, rename/hardlink behaviour, expressiveness, tooling, and default distros.
- **Anchor:** the `<Tabs>` plus the comparison table.
- **KernelFacts:** structure `[["struct aa_profile", "security/apparmor/include/policy.h"], ["struct aa_label", "security/apparmor/include/label.h"]]`; path `"security_file_open() → apparmor_file_open() → aa_path_perm() → profile DFA match"`; observe `aa-status`; trap: "Path-based rules follow the name, not the object. A hard link or bind mount at a different path can be governed by different rules than the original."
- **References:** `https://docs.kernel.org/admin-guide/LSM/apparmor.html`; the AppArmor wiki profile-language reference (context7: AppArmor tooling); `man 7 apparmor`; Ubuntu Server docs on AppArmor.

**Task-specific:** context7: SELinux and AppArmor tooling (mandatory). Verify `security_hook_list`, `lsm_info`, `call_int_hook`, `security_file_open`, `selinux_file_open`, `file_path_has_perm`, `avc_has_perm`, `security_compute_av`, `task_security_struct`, `aa_profile`, `aa_label`, `apparmor_file_open`, `aa_path_perm`, and the LSM syscalls. Commit: `docs: write the LSM framework, SELinux, and AppArmor pages`.

---

## Task 18: Folder 16 — seccomp, keyrings, and integrity

### `seccomp.md` — seccomp and Syscall Filtering **[Lab host=qemu]** **[Misc]**

- **Opens with:** seccomp shrinks the kernel a process can reach. A small classic-BPF program runs on every system call, sees the syscall number, the architecture and the raw arguments, and returns allow, deny with an errno, kill, trap, or "ask a supervisor". Every container runtime installs one. The details that matter are the ones people get wrong: check the architecture first, and filter pointers by number only, never by what they point to.
- **Sections:** `## Strict mode`; `## Filter mode` (`struct seccomp_data`, the return actions and their precedence, and `SECCOMP_FILTER_FLAG_TSYNC`); `## Check the architecture first` (why: the x32 and i386 syscall numbers differ, and a filter that skips the check can be bypassed by the other ABI — **describe the class, not a procedure**); `## Arguments are values, not memory` (TOCTOU on pointer arguments, and why seccomp cannot filter paths); `## no_new_privs`; `## User notification` (`SECCOMP_RET_USER_NOTIF`, the listener fd, `SECCOMP_IOCTL_NOTIF_ADDFD`, and supervised syscalls); `## Runtime default profiles` (Docker's allowlist, how it is generated, and `--security-opt seccomp=`).
- **Lab:** a small C program that installs a filter denying `uname` with `EPERM` (arch check included), shown with `strace` before and after, and `grep Seccomp /proc/self/status`. Then point at `15/building-a-container-from-scratch`'s filter as the larger example. Measured output. If it fails: `EACCES` from `prctl(PR_SET_SECCOMP)` means `no_new_privs` was not set and the process lacks `CAP_SYS_ADMIN`.
- **Misconceptions:** (1) "seccomp can block access to a file path." (2) "A denylist is as good as an allowlist." (3) "seccomp filters are eBPF." They are classic BPF.
- **Anchor:** a WaveDrom `reg` of the 32-bit filter return value (`SECCOMP_RET_ACTION_FULL` high bits, `SECCOMP_RET_DATA` low 16), with the actions listed by value. Plus a table of actions × precedence × effect.
- **KernelFacts:** structure `[["struct seccomp_data", "include/uapi/linux/seccomp.h"], ["struct seccomp_filter", "kernel/seccomp.c"]]`; path `"syscall entry → syscall_trace_enter() → __secure_computing() → seccomp_run_filters() → action"`; observe `grep Seccomp /proc/self/status; grep Seccomp /proc/1/status`; trap: "A filter written for x86-64 numbers that does not first check `arch == AUDIT_ARCH_X86_64` can be sidestepped through another syscall ABI on the same machine."
- **References:** `https://docs.kernel.org/userspace-api/seccomp_filter.html` (context7: seccomp tooling — libseccomp); `man 2 seccomp`, `man 2 seccomp_unotify`; Docker's seccomp profile docs; `<Src file="kernel/seccomp.c" symbol="__secure_computing" />`.

### `keyrings.md` — Keyrings

- **Opens with:** the kernel keeps secrets for user space and for itself: disk-encryption keys, Kerberos tickets, and the public keys that verify modules. The key retention service stores them as typed, permissioned objects in keyrings attached to threads, processes, sessions and users. That way a secret can be used by the kernel without ever being handed back to user space.
- **Sections:** `## Keys and key types` (`user`, `logon`, `keyring`, `asymmetric`, `encrypted`, `trusted`); `## The keyring hierarchy and search order` (thread → process → session → user, plus persistent keyrings); `## Permissions on keys`; `## The tools` (`keyctl show`, `add`, `request`); `## Who uses them` (dm-crypt/LUKS via `logon` keys, NFS/Kerberos via `request-key`, and module signing via `.builtin_trusted_keys`/`.secondary_trusted_keys`/`.machine`; forward link `./integrity-and-signing.md`); `## Containers and keyrings` (why runtimes block `keyctl` — keyrings are not namespaced — linking `15/building-a-container-from-scratch`'s filter).
- **Anchor:** a `flowchart TB` of the keyring hierarchy and search order, plus a key-types table.
- **KernelFacts:** structure `[["struct key", "include/linux/key.h"], ["struct key_type", "include/linux/key-type.h"]]`; path `"request_key() → request_key_and_link() → search_process_keyrings_rcu() → (miss) call_sbin_request_key() → /sbin/request-key"`; observe `keyctl show @s; cat /proc/keys | head`; trap: "Keyrings are not namespaced by container. A key in a user's keyring is reachable from any container running as that UID unless `keyctl` is blocked."
- **References:** `https://docs.kernel.org/security/keys/core.html`; `man 7 keyrings`, `man 1 keyctl`; `<Src file="security/keys/request_key.c" symbol="request_key_and_link" />`.

### `integrity-and-signing.md` — Integrity: IMA, EVM, and Module Signing

- **Opens with:** Secure Boot proves the kernel that booted was signed. Integrity subsystems extend that proof past boot. Module signing refuses unsigned kernel code. IMA measures, and optionally appraises, every file executed or read under a policy. EVM protects the extended attributes IMA's verdicts are stored in. Together they answer whether the system is still running what it was supposed to run.
- **Sections:** `## Module signing` (`CONFIG_MODULE_SIG`, `module.sig_enforce`, the trusted keyrings, signing at build time, and DKMS/MOK on distros; link `03/secure-boot-and-signed-kernels`); `## IMA measurement` (the measurement list, extending a TPM PCR, `/sys/kernel/security/ima/ascii_runtime_measurements`, and remote attestation); `## IMA appraisal` (`security.ima` hashes or signatures, and enforce versus fix modes); `## The IMA policy language` (a few annotated rules: `measure func=BPRM_CHECK`, `appraise …`); `## EVM`; `## Lockdown's role` (briefly; link `./kernel-hardening.md`); `## How it chains` (firmware → shim → GRUB → kernel → modules → files).
- **Anchor:** a `flowchart LR` chain of trust from UEFI to an executed file, with which mechanism verifies each arrow. Plus a measure-versus-appraise table.
- **KernelFacts:** structure `[["struct ima_rule_entry", "security/integrity/ima/ima_policy.c"], ["struct module_signature", "include/linux/module_signature.h"]]`; path `"finit_module() → load_module() → module_sig_check() → verify_pkcs7_signature() against .builtin_trusted_keys"`; observe `cat /proc/sys/kernel/modules_disabled; dmesg | grep -i -E 'module verification|ima'`; trap: "Measurement without appraisal changes nothing locally. A tampered file still runs, and only a remote verifier reading the log notices."
- **Lab note:** **no lab**. Loading an unsigned module under enforcement is the spec's `:::danger` case only if it is demonstrated; this page describes it and does not demonstrate it. Keep `host` badges out.
- **References:** `https://docs.kernel.org/admin-guide/module-signing.html`; the IMA/EVM documentation at `https://ima-doc.readthedocs.io` (check it is current); `https://docs.kernel.org/security/IMA-templates.html`; `<Src file="kernel/module/signing.c" symbol="module_sig_check" />`.

**Task-specific:** context7: seccomp tooling (libseccomp). Verify `seccomp_data`, `__secure_computing`, `seccomp_run_filters`, `SECCOMP_RET_USER_NOTIF`, `SECCOMP_IOCTL_NOTIF_ADDFD`, `SECCOMP_FILTER_FLAG_TSYNC`, `key`, `key_type`, `request_key_and_link`, `search_process_keyrings_rcu`, `call_sbin_request_key`, `ima_rule_entry`, `module_signature`, `module_sig_check`, `verify_pkcs7_signature`, and the `.machine` keyring's existence at v6.18. Commit: `docs: write the seccomp, keyrings, and integrity pages`.

---

## Task 19: Folder 16 — kernel hardening, vulnerability classes, and auditing

### `kernel-hardening.md` — Kernel Hardening **[WAH]** **[Misc]**

- **Opens with:** hardening assumes the kernel has bugs and makes each one less useful to an attacker. KASLR hides where code is. SMEP and SMAP stop the kernel executing or touching user memory by accident. KPTI unmaps the kernel from user page tables. Stack protectors, fortified string functions and lockdown close specific routes. Each defeats a particular step and has a measurable cost, and this page states both for each.
- **Sections:** one `##` per mitigation family (KASLR and its limits; SMEP/SMAP and the `stac`/`clac` window around `copy_*_user` — link `05/copying-data-across-the-boundary`; KPTI and PCID — link `08/tlb-and-address-space-switching`; stack protector and shadow stacks/CET; `CONFIG_FORTIFY_SOURCE`; slab hardening: `slab_nomerge`, freelist hardening, `init_on_alloc`/`init_on_free`, and `RANDOM_KMALLOC_CACHES`; lockdown; information restrictions: `kptr_restrict`, `dmesg_restrict`, `perf_event_paranoid`, and `unprivileged_bpf_disabled`); `## The cost table`; `## What actually happens`.
- **Cost table:** mitigation × what it defeats × cost class × how to check it. **Costs are cited from a source (kernel docs, LWN, a paper) or stated as "workload-dependent"**; never an invented percentage.
- **WAH:** on the lab kernel, show `/sys/devices/system/cpu/vulnerabilities/*`, `grep -o -E 'smep|smap|pti|pcid' /proc/cpuinfo | sort -u`, `cat /proc/sys/kernel/kptr_restrict`, `head -3 /proc/kallsyms` as a user (zeros) versus root, and `cat /sys/kernel/security/lockdown`. Measured.
- **Misconceptions:** (1) "KASLR stops exploitation." It raises the bar and is defeated by any pointer leak. (2) "`mitigations=off` is a free speedup." (3) "Hardening options are all on by default."
- **Anchor:** the cost table, plus a `flowchart LR` of a generic attack chain (bug → info leak → control → privilege) with each mitigation drawn at the step it blocks. This is generic and contains no specific exploit.
- **KernelFacts:** structure `[["struct kernel_param (lockdown=)", "security/lockdown/lockdown.c"], ["cpu_vulnerabilities sysfs", "drivers/base/cpu.c"]]`; path `"user access in kernel: copy_from_user() → __uaccess_begin() (stac) → access → __uaccess_end() (clac)"`; observe `grep . /sys/devices/system/cpu/vulnerabilities/*`; trap: "`/sys/devices/system/cpu/vulnerabilities` reports what the kernel *believes* about the CPU and its microcode. Outdated microcode shows up as 'Vulnerable' even with every software mitigation enabled."
- **References:** `https://docs.kernel.org/security/self-protection.html`; `https://docs.kernel.org/admin-guide/hw-vuln/index.html`; the Kernel Self Protection Project recommended settings (kspp.github.io); `<Src file="arch/x86/include/asm/uaccess.h" symbol="__uaccess_begin" />`.

### `vulnerability-classes.md` — Vulnerability Classes in the Kernel **[Misc]**

- **Opens with:** kernel vulnerabilities come in a small number of recurring shapes, and recognising the shape in a diff or a crash report is most of the defence. This page describes each class by its shape, its consequence, how it shows up in testing, and what the kernel does to prevent or contain it. It is written for people reviewing and fixing code. **It contains no exploitation technique.**
- **Sections:** one `##` per class, each with the same four `###`s — *Shape*, *Consequence*, *How it is found*, *Mitigation*:
  - use-after-free (link `04/reference-counting-and-lifetime`; KASAN);
  - refcount overflow (`refcount_t` saturation);
  - TOCTOU on user memory, the double fetch (link `05/copying-data-across-the-boundary`);
  - integer overflow in size arithmetic (`struct_size`, `check_mul_overflow`, `array_size`);
  - uninitialised memory disclosure (`init_on_alloc`, `INIT_STACK_ALL_ZERO`, KMSAN);
  - transient execution (Spectre v1/v2, Meltdown, MDS, Retbleed — what each leaks, and `array_index_nospec`, retpolines/IBRS, KPTI, `VERW`, as a table).

  Folder 17 owns the sanitizers in depth: name KASAN/KMSAN/UBSAN/KCSAN in prose without linking. Close with `## Where to read real reports` (the kernel CVE process and `linux-cve-announce`; LWN).

  **Each code example is a short *buggy pattern and its fix* in ` ```c `, as a review exercise** — no payloads, no exploitation steps.
- **Misconceptions:** (1) "Most kernel CVEs need local root to exploit." (2) "Rust in the kernel removes these classes." It removes some, in Rust code only. State honestly which. (3) "A crash is not a vulnerability."
- **Anchor:** a table of class × shape in one line × primary detector × primary mitigation, plus the transient-execution sub-table.
- **KernelFacts:** structure `[["refcount_t", "include/linux/refcount.h"], ["struct_size()", "include/linux/overflow.h"]]`; path `"get_user(len, &uarg->len) twice → double fetch; fix: copy_from_user() once into a kernel struct, validate, use the copy"`; observe `ls /sys/devices/system/cpu/vulnerabilities/`; trap: "Reading a user-space value twice — once to check, once to use — is a bug even when both reads are in adjacent lines. Another thread can change it in between."
- **References:** `https://docs.kernel.org/process/cve.html`; `https://docs.kernel.org/process/deprecated.html` (open-coded arithmetic and similar); `https://docs.kernel.org/admin-guide/hw-vuln/index.html`; Jann Horn's or Project Zero's defensive write-ups, chosen for root-cause analysis and annotated as such. **Exclude any reference that is primarily an exploit walkthrough.**

### `auditing-and-security-observability.md` — Auditing and Security Observability

- **Opens with:** prevention fails eventually, and then the question is what was recorded. The audit subsystem is the kernel's tamper-resistant record of security-relevant events: syscalls matching rules, LSM decisions, logins and policy changes, delivered to `auditd` over netlink. BPF-LSM is the newer, programmable way to watch, or act, at the same hook points.
- **Sections:** `## The audit subsystem` (records, events, and the netlink path to `auditd`); `## Rules` (syscall rules with filters, file watches, `auditctl -l`, persistent rules in `/etc/audit/rules.d`); `## Reading records` (`ausearch`, `aureport`, and one multi-record event — SYSCALL + PATH + PROCTITLE — annotated); `## Where LSM output goes` (AVC and `apparmor=` records; link the two LSM pages); `## BPF-LSM` (programs attached to LSM hooks, what it enables for tools like Tetragon/Falco, `CONFIG_BPF_LSM` and `lsm=…,bpf`; eBPF itself is folder 18's, so name it in prose); `## What to log and what it costs` (per-syscall rules on hot syscalls, backlog limits and `audit_backlog_limit`, lost events, and the `-a never,task` trick in default configs).
- **Anchor:** a `flowchart LR` — syscall exit → `audit_filter_syscall` → record build → `kauditd` → netlink → `auditd` → log/dispatcher, plus a table of an annotated event's fields.
- **KernelFacts:** structure `[["struct audit_context", "kernel/audit.h"], ["struct audit_buffer", "kernel/audit.c"]]`; path `"syscall exit → __audit_syscall_exit() → audit_filter_syscall() → audit_log_exit() → kauditd_thread → netlink unicast to auditd"`; observe `auditctl -s; auditctl -l`; trap: "When the audit backlog fills, the kernel either drops records or, with `-f 2`, panics. A security-mandated 'panic on audit failure' setting turns a log-volume spike into an outage."
- **References:** `man 8 auditctl`, `man 8 ausearch`, `man 7 audit.rules`; the Linux Audit project on GitHub; `https://docs.kernel.org/bpf/prog_lsm.html`; `<Src file="kernel/auditsc.c" symbol="__audit_syscall_exit" />`.

- [ ] **Step 1: Write the three pages**, running the hardening WAH on the lab kernel first.
- [ ] **Step 2: Writing-task procedure** (context7: none mandated beyond auditd man pages. Verify `__uaccess_begin`, `array_index_nospec`, `struct_size`, `check_mul_overflow`, `refcount_t`, `init_on_alloc`, `INIT_STACK_ALL_ZERO`, `RANDOM_KMALLOC_CACHES`, `audit_context`, `audit_filter_syscall`, `__audit_syscall_exit`, `audit_log_exit`, `kauditd_thread`, `CONFIG_BPF_LSM`).
- [ ] **Step 3: Optional audit lab.** If there is time, add a small file-watch rule on the Debian VM and an `ausearch` of it to the auditing page, with `auditctl -D` cleanup. The spec does not mark this page **[Lab]**, so this is optional.
- [ ] **Step 4: The defensive-content check for folder 16** (spec Phase 4 step 6, Review Focus #3). Run `rtk run "grep -n -i -E 'exploit|payload|shellcode|ROP|gadget|spray|privesc|proof.of.concept|PoC' docs/linux/16-security/*.md"` and read every hit in context. Each hit must be a description of a class or a mitigation, never an instruction. Then re-read `vulnerability-classes.md` and `kernel-hardening.md` end to end with one question: could a reader follow this page as a procedure to attack a system? Any yes is rewritten before commit.
- [ ] **Step 5: Gates and commit**

```bash
npm run check:linux && npm run build
git add docs/linux/16-security
git commit -m "docs: write the hardening, vulnerability classes, and auditing pages"
```

---
## Task 20: Turn prose-only forward references in folders 00–13 into links

**Rules (unchanged from Phase 3 Task 21):**
- Add links; do not rewrite pages.
- Link only into folders 14–16. Observability, eBPF and contributing (17–19) stay prose.
- Link the first meaningful mention per page.
- Use relative paths with numeric prefixes.

- [ ] **Step 1: Find candidates**

```bash
rtk run "grep -rn -i -E 'folder 1[4-6]|not yet written|named here (only )?in prose|in prose only|in prose rather than|later folder|security folder|containers material|driver|devm_|IOMMU|namespace|cgroup|capabilit|seccomp|SELinux|AppArmor|LSM|KVM|virtio|udev|firmware' docs/linux/0* docs/linux/1[0-3]-*"
```

For each hit, decide: (a) a forward reference into 14–16 → link it; (b) a 17–19 topic → leave it; (c) already linked or incidental → leave it.

- [ ] **Step 2: Apply the known fixes.** These were located during planning; confirm each still reads as quoted before editing.

| File | Current text (abridged) | Link to |
|---|---|---|
| `08/vmalloc-and-choosing-an-allocator.md` | "Folder 14 develops this point properly when it covers DMA and IOMMUs"; "Folder 14 owns this properly — driver code meets `devm_*` constantly" | `../14-device-drivers-and-hardware/the-dma-api.md`; `../14-device-drivers-and-hardware/the-linux-device-model.md` (its `probe and remove` section) |
| `00/roadmap.md` | "A real character driver is built in folder 14." | `../14-device-drivers-and-hardware/lab-a-character-driver.md` |
| `11/overlayfs.md` | "Container image layers … (named here in prose only — the containers material…)" | `../15-containers-and-virtualization/images-layers-and-oci.md` |
| `03/systemd-the-model.md` | "…placed in its own cgroup for tracking — folder 15 covers how that…" | `../15-containers-and-virtualization/cgroup-v2-architecture.md` |
| `03/systemd-in-practice-and-boot-debugging.md` | "Folder 15 covers cgroups themselves" | `../15-containers-and-virtualization/cgroup-v2-architecture.md` |
| `07/cgroup-cpu-control.md` | "Folder 15 owns cgroup v2 as a whole" | `../15-containers-and-virtualization/cgroup-v2-architecture.md` |
| `06/threads-are-tasks.md` | "…folder 15's subject, not this page's, and this page does not link ahead to unwritten pages." | `../15-containers-and-virtualization/namespaces-overview.md`; delete the "does not link ahead" clause |
| `06/credentials-and-identity.md` | "belong to the security folder later in this section (folder 16) and are only named here"; "folder 16 is where it is…" | `../16-security/capabilities.md`; `../16-security/the-lsm-framework.md` (or `credentials-in-the-kernel.md`, whichever the sentence is about) |
| `12/nvme-in-the-kernel.md` | "…belongs to a later folder, named here only in prose" | Read the sentence. If it is about DMA or PCI → folder 14; if about observability → leave it |
| `02/the-life-of-a-container.md` | namespaces, cgroups, capabilities and seccomp mentions — deliberately unlinked in Phase 3 | `15/namespaces-overview`, `15/cgroup-v2-architecture`, `16/capabilities`, `16/seccomp`; add a pointer to `15/what-a-container-actually-is` near the top |
| `10/how-an-interrupt-reaches-the-kernel.md`, `10/the-irq-subsystem.md` | any "drivers" forward mention found in Step 1 | `../14-device-drivers-and-hardware/interrupts-in-drivers.md` |
| `04/kobjects-sysfs-and-the-object-model.md` | any device-model forward mention found in Step 1 | `../14-device-drivers-and-hardware/the-linux-device-model.md` |
| `13/network-namespaces-and-virtual-devices.md`, `13/connection-tracking-and-nat.md` | container-networking prose mentions | `../15-containers-and-virtualization/container-networking.md` |

- [ ] **Step 3: Apply any further fixes Step 1 found.**
- [ ] **Step 4: Nothing links into 17–19, and everything resolves**

```bash
rtk run "grep -rn -E '\.\./1[7-9]-' docs/linux docs/computer-science"
npm run build
```

Expected: no grep output, and a green build.

- [ ] **Step 5: Re-run the wording grep** (`not yet written|in prose only|named here (only )?in prose|folder 1[4-6]`). Every remaining hit must refer to folders 17–19 or not be a forward reference at all.
- [ ] **Step 6: Lint and commit**

```bash
rtk run 'npm run lint'
git add docs/linux
git commit -m "docs: link folders 00-13 forward into the driver, container, and security pages"
```

---

## Task 21: Figures and `SOURCES.md` rows for the phase

**Interfaces:** Consumes the written pages. Produces the phase's figure set, **batched deliberately** so downloads and provenance rows happen once.

The spec names no canonical figure for folders 14–16 (unlike Phase 3's storage-stack and netfilter diagrams). Every page already has a Mermaid, WaveDrom or table anchor. Figures here are additions only where a real image beats a diagram (CLAUDE.md: figures are preferred where a real one carries more information). The candidates are below; for each, decide **keep** or **decline**, and state the decline in the commit message so a later phase does not re-litigate it.

| Candidate | Page | Source to try | Notes |
|---|---|---|---|
| PCIe topology or config-space figure | `cs:buses-and-io/pcie-in-depth` | Wikimedia Commons (search "PCI Express") | **CS page: licence required.** |
| IOMMU / DMA remapping figure | `cs:buses-and-io/dma-and-iommu` | Wikimedia Commons "MMU and IOMMU" | **CS page: licence required.** |
| Linux device model / sysfs hierarchy | `14/the-linux-device-model` | kernel docs figures, if any exist at v6.18 | Linux page: no licence gate; still needs a `SOURCES.md` row. |
| virtio architecture | `15/virtio-and-paravirtualization` | the OASIS spec or a docs.kernel.org figure | |
| cgroup v2 hierarchy | `15/cgroup-v2-architecture` | | Probably decline — the Mermaid tree is clearer. |

- [ ] **Step 1: Confirm the directory conventions.** Linux figures go in `static/img/linux/<folder-slug-without-prefix>/`, and CS figures in `static/img/cs/<section>/`. Reference both as `/img/...` with no `/knowledge-base` prefix.
- [ ] **Step 2: For each candidate,** open the file page, confirm author and licence (CS) or publisher (Linux), and download into a new empty directory first (untrusted). Check it with `file`, then move it into place. If an SVG renders badly, use the source's own PNG rendering at ≤ 1400 px and note that.
- [ ] **Step 3: Add the `SOURCES.md` rows,** matching each file's existing columns exactly. The Linux file uses `file | source_url | publisher | retrieved | notes`; the CS file uses `file | source | author | licence`. The notes must say if the image is a crop, an extracted frame, or a downscale.
- [ ] **Step 4: Place each figure** with a full `<Figure>`: `src`, a descriptive `alt`, a caption saying what it shows, and `source`/`href`, plus `license=` on CS pages.
- [ ] **Step 5: Size budget.** Run `du -sh static/img/linux static/img/cs`. No new file may exceed ~1 MB.
- [ ] **Step 6: No orphans.** Run `npm run build`. Then cross-check `grep -rho '/img/linux/[^"]*' docs/linux | sort -u` and the CS equivalent against `SOURCES.md` and `ls -R` in both directions.
- [ ] **Step 7: Commit:** `docs: add phase 4 figures and SOURCES rows`, listing the declined candidates in the commit body. If every candidate is declined, there is nothing to commit. Record the declines in the Task 24 report instead.

---

## Task 22: Extend the glossary

- [ ] **Step 1: Read `00-overview/glossary.md`** and match its format exactly: an alphabetised list, a bolded term, an em dash, one or two sentences, and one link to the **owning** page. No per-letter headings. Extend existing entries (for example **Namespace**, **cgroup**, **Capability** if they exist) with the new owner link rather than duplicating them.
- [ ] **Step 2: Extract terms from the written pages.** The list below is a starting point; a term the owning page does not define does not get an entry.
  - **14:** bus type, device, driver, class, probe, bind/unbind, deferred probe, `devm_*`/devres, fw_devlink, platform device, device tree, `compatible`, ACPI, `_HID`, ID table, modalias, `pci_dev`, BAR (driver side), bus mastering, `__iomem`, `ioremap`, relaxed accessor, posted write, `dma_addr_t`, DMA mask, coherent mapping, streaming mapping, swiotlb/bounce buffer, MSI-X vector (driver side), `IRQ_NONE`, `cdev`, misc device, major/minor, ioctl number, sysfs attribute, `Documentation/ABI`, debugfs, netlink (driver side), vfio, uio, `queue_rq`, `ndo_start_xmit`, uevent, udev rule, predictable interface name, coldplug, `request_firmware`, s2idle, runtime PM, autosuspend, wakeup source, dynamic debug.
  - **15:** container, `nsproxy`, namespace (each of the eight), `unshare`, `setns`, `pivot_root`, mount propagation (container side → link 11), PID 1 / subreaper, `NSpid`, UID map, rootless container, `ns_capable`, cgroup v2, unified hierarchy, no-internal-process rule, `subtree_control`, delegation, slice/scope, `memory.high`, `memory.max`, `io.latency`, `pids.max`, PSI, `--privileged`, `no_new_privs`, OCI image, OCI runtime spec, bundle, runc, containerd, shim, CNI, port publishing, KVM, `kvm_run`, VM exit (Linux side), virtio, virtqueue, vhost.
  - **16:** mode bits, sticky bit, umask, POSIX ACL, `struct cred`, fsuid, saved set-user-ID, capability sets (each), file capability, ambient set, securebits, LSM, LSM hook, LSM stacking, type enforcement, security context, AVC, boolean, permissive mode, AppArmor profile, complain mode, seccomp, seccomp-BPF, user notification, keyring, key type, IMA, EVM, measurement versus appraisal, module signing, lockdown, KASLR, SMEP, SMAP, KPTI, stack protector, `FORTIFY_SOURCE`, double fetch, refcount saturation, transient execution, audit rule, `auditd`, BPF-LSM.
  - **Owned by the CS backfill pages** — link *there*: Popek–Goldberg, VMX root/non-root, VMCS, EPT/NPT, two-dimensional page walk, PCIe link/lane, TLP, BDF, configuration space, ECAM, BAR sizing, MSI/MSI-X (hardware), bus-master DMA, scatter-gather, IOVA, IOMMU, IOTLB, attack surface, performance versus security isolation, microVM.
- [ ] **Step 3: Enforce the one-owner rule.** Every entry links to exactly one page, and that page must genuinely introduce the term.
- [ ] **Step 4: Update the opening paragraph** to say the glossary covers folders 00–16.
- [ ] **Step 5: Verify order and links.** Run `rtk run "grep -o '^\*\*[^*]*\*\*' docs/linux/00-overview/glossary.md"` and scan for ordering mistakes; then run `npm run build`.
- [ ] **Step 6: Commit:** `docs: extend the glossary for folders 14-16`.

---

## Task 23: Extend the misconceptions index, the roadmap, and the folder ladder

- [ ] **Step 1: Collect entries mechanically.** Run: `rtk run "grep -rn -A 12 '^## Misconceptions' docs/linux/14-* docs/linux/15-* docs/linux/16-*"`. The plan marks 21 pages **[Misc]** (seven per folder), but the grep is the authority.
- [ ] **Step 2: Append three groups** after `## 13 — The Networking Stack`, in the index's existing format: `## 14 — Device Drivers`, `## 15 — Containers and Virtualization`, `## 16 — The Security Model`. Where a belief already appears under `## 02` (for example in `the-life-of-a-container`), keep that entry and add the new one in the new page's wording.
- [ ] **Step 3: Count both directions** — entries found and entries added must match. State both counts in the commit message.
- [ ] **Step 4: `roadmap.md`.** Keep `<LearningPath>` usage as is.
  - **"I want to write a module"** — replace the closing "A real character driver is built in folder 14." (linked by Task 20) with appended steps: `14/the-linux-device-model`, `14/character-devices`, `14/lab-a-character-driver`, `14/debugging-drivers`.
  - **New: "I want to write a driver"** (the spec's path) — one sentence saying it assumes "I want to write a module" and the interrupts folder. Steps: `cs:buses-and-io/pcie-in-depth`, `14/the-linux-device-model`, `14/platform-devices-and-description`, `14/pci-and-pcie-drivers`, `14/mmio-and-port-io`, `cs:buses-and-io/dma-and-iommu`, `14/the-dma-api`, `14/interrupts-in-drivers`, `14/character-devices`, `14/lab-a-character-driver`, `14/talking-to-user-space`, `14/power-management`, `14/debugging-drivers`.
  - **New: "I want to work on containers"** (the spec's path) — one sentence naming its outside prerequisites (`13/network-namespaces-and-virtual-devices`, `11/overlayfs`). Steps: `cs:operating-systems/virtualization-and-isolation`, `15/what-a-container-actually-is`, `15/namespaces-overview`, `15/mount-and-pid-namespaces`, `15/user-namespaces`, `15/cgroup-v2-architecture`, `15/cgroup-controllers-in-practice`, `16/capabilities`, `15/capabilities-in-containers`, `16/seccomp`, `15/building-a-container-from-scratch`, `15/images-layers-and-oci`, `15/container-networking`.
  - **New: "I want to understand Linux security"** — steps: `16/the-unix-permission-model`, `16/credentials-in-the-kernel`, `16/capabilities`, `16/the-lsm-framework`, `16/selinux`, `16/apparmor`, `16/seccomp`, `16/kernel-hardening`, `16/vulnerability-classes`, `16/auditing-and-security-observability`.
  - **`## Where the rest is`:** folders 17 through 19 remain specified and not yet scaffolded (observability, eBPF, contributing).
  - Step labels are in sentence case, matching the existing paths. CS steps use `../../computer-science/...` paths.
- [ ] **Step 5: Folder ladder** in `what-this-section-covers.md`: rows `14`–`16` get the written-status wording that rows `11`–`13` use. The "14 through 19" sentence becomes "17 through 19". Make one table edit and one or two sentence edits only.
- [ ] **Step 6: Build and commit:** `npm run build`, then `docs: extend the misconceptions index, roadmap, and folder ladder for folders 14-16`.

---

## Task 24: Phase review, `CLAUDE.md`, and the written gate

- [ ] **Step 1: Written gate.** Run `npm run check:linux -- --written`. Expected: `check-linux-docs: OK — 196 written page(s), 0 stub(s)`. Any stub is a page this plan missed; write it rather than adjusting the gate.
- [ ] **Step 2: Full gates**

```bash
npm run build
npm run typecheck
npm run test:graph
npm run test:kernel-source
rtk run 'npm run lint'
```

Expected: all green.

- [ ] **Step 3: Review pass** over all 41 pages (37 Linux + 4 CS), the two lab source directories, and the Task 20 edits. Record findings, fix them, and re-run Step 2.
  - Every topic page has a visual anchor with a caption that says what it shows; 2–6 annotated references with no bare URLs; and a closing `<KernelFacts>` whose `trap` is a real trap. **Every URL has been opened.**
  - **Every symbol, field, path, ioctl, sysctl and interface file has been checked against v6.18.** This is a per-page audit, not a spot check. The driver API and cgroup files are where drift hides.
  - **The three required arm64 notes exist:** `14/platform-devices-and-description` (`<Tabs>` + note), `14/mmio-and-port-io`, and `14/the-dma-api`. None was invented in 15 or 16. Check with `rtk run "grep -rln ':::note\[arm64' docs/linux/1[4-6]-*"`.
  - `## What actually happens` appears only on the **[WAH]** pages: 14 → device-model, mmio, talking-to-user-space, firmware-udev, power-management; 15 → what-a-container, mount-and-pid, cgroup-v2, capabilities-in-containers, kvm; 16 → permission-model, capabilities, selinux, kernel-hardening. Run `rtk run "grep -rln '^## What actually happens' docs/linux/1[4-6]-*"` and compare.
  - Every `<Lab>` has a host badge, measured output, an "if it fails" line, and **a cleanup block that restores host state** (Review Focus #5): the chardrv `rmmod`; the cgroup `rmdir`; the netns/bridge/`table inet lab` deletion with `ip_forward` restored; `pm_test` reset; `device_del`; the SELinux VM snapshot note.
  - The `:::danger` labs (`16/selinux`) are not `host="any-linux"`.
  - **Lab code is byte-identical to the files in `static/code/linux/`** (Review Focus #1). Diff each fenced block against its file.
  - **Folder 16 defensive check re-run** (Task 19 Step 4) over the whole folder, plus `15/capabilities-in-containers` and `15/user-namespaces`.
  - **The root-equivalence of `CAP_SYS_ADMIN` and `--privileged` is stated plainly** on both `15/capabilities-in-containers` and `16/capabilities`, and the two pages agree (Review Focus #4).
  - context7 checks are done and dated: driver-model and DMA (14); cgroup v2, OCI/runc and Docker CLI (15); seccomp, SELinux and AppArmor (16).
  - No page links into 17–19: `rtk run "grep -rn -E '\.\./1[7-9]-' docs/linux docs/computer-science"` prints nothing.
  - **No-duplication spot checks:** `14/pci-and-pcie-drivers` against `cs:pcie-in-depth`; `14/the-dma-api` against `cs:dma-and-iommu`; `15/kvm-and-hardware-virtualization` against `cs:hardware-virtualization`; `15/what-a-container-actually-is` against `cs:virtualization-and-isolation`; `15/mount-and-pid-namespaces` against `11/mounts-and-mount-namespaces`; `15/container-networking` against `13/network-namespaces-and-virtual-devices`; `16/credentials-in-the-kernel` against `06/credentials-and-identity`; `15/cgroup-controllers-in-practice` against `07/cgroup-cpu-control`.
  - Every CS backfill page follows its folder's backfill template, and every backlink from Tasks 2–3 is present.
  - The `SOURCES.md` files have no orphans in either direction.
- [ ] **Step 4: Walk the learning paths.** For the three new paths and the extended module path, check that every folder-14–16 prerequisite of every page on the path appears earlier in that path, and that outside prerequisites are named in the path's introducing sentence.
- [ ] **Step 5: Production build by eye.** Run `npm run build && npm run serve`, then check:
  - the three new folders appear in order with their index descriptions;
  - `15/kvm-and-hardware-virtualization`'s `<PrereqBlock>` shows a `CS` chip;
  - the WaveDrom strips render (PCI command register, ioctl number, `CLONE_NEW*`, capability set, `st_mode`, seccomp return value);
  - the `stateDiagram`s render (bind states, runtime PM, SELinux modes, host/guest in CS);
  - the `<Tabs>` switch on platform-devices, cgroup-v2 and apparmor;
  - a `<Lab>` badge shows;
  - the lab source downloads resolve under `/knowledge-base/code/linux/...`;
  - the new roadmap paths click through.
- [ ] **Step 6: Update `CLAUDE.md`** — one surgical edit to the Linux phase-status sentence: Phase 4 wrote folders `14`–`16` (37 pages) and CS backfill 5/9/11/18 (hardware virtualization, PCIe, DMA/IOMMU, isolation theory), bringing the section to **196 written pages**; folders `17`–`19` remain spec-only; and `npm run check:linux -- --written` now covers 00–16. If Task 7/13 created `static/code/linux/`, add one sentence saying lab sources live there and that pages embed them verbatim.
- [ ] **Step 7: Commit:** `docs: update CLAUDE.md for phase 4 completion`.
- [ ] **Step 8: Final verification.** Run `npm run check:linux -- --written && npm run build && rtk run 'npm run lint' && git status`. Expected: all green and a clean tree. Report:
  - the page count;
  - the gates run;
  - the context7 checks and their dates;
  - the figures kept and declined;
  - the forward references converted;
  - the lab-driven page changes (Task 13 Step 4);
  - everything the review found and fixed.

---

## Self-review notes

**Spec coverage** — every item in "Phase 4 ordering" has a task:

| Spec item | Tasks |
|---|---|
| 1. Scaffold 14–16; green build | 1 |
| 2. CS backfill 5, 9, 11, 18 plus backlinks; 9 and 11 gate folder 14 | 2 (9, 11 — ordered before any folder-14 task), 3 (5, 18) |
| 3. Folders 14 → 15 → 16; `the-linux-device-model` first, `what-a-container-actually-is` second | 4–9, 10–15, 16–19; Task 4 opens with the device model, and Task 10 is the first folder-15 task |
| 4. The two build-it-yourself labs run in QEMU before their surrounding pages are finalised | Task 7 Steps 1–4 and Task 13 Steps 1–4 run first; Task 13 Step 4 feeds lab findings back into the pages |
| 5. context7 for driver-model/DMA (14), cgroup v2 and OCI/runc (15), seccomp/SELinux/AppArmor (16) | Tasks 4–9, 10–15, 17–18 "Task-specific" lines; audited in Task 24 |
| 6. Figures and labs pass, then review; folder 16 has no exploit code or procedures | Task 21; Task 19 Step 4; Task 24 |

Page counts match the spec: 13 + 12 + 12 = 37 Linux pages, plus 4 CS pages. Every spec **[WAH]** and **[Lab]** marker is carried over.

**Deliberate deviations, stated rather than hidden:**
- **No `<Cast>` on `14/lab-a-character-driver`.** It ships an annotated transcript, and the cast is recorded in Phase 5 with the rest, per the Phase 3 precedent.
- **Lab sources live in the repo** (`static/code/linux/`), so the page and the code that ran cannot drift. The spec does not say where lab code lives; this is the smallest mechanism that enforces the spec's "measured, not predicted" rule. Phase 3 had none (it embedded its module inline only).
- **`16/integrity-and-signing` has no lab**, although it is the natural home of the `:::danger` unsigned-module case. Demonstrating it means disabling enforcement on a VM, which teaches little the prose does not. The spec does not mark the page **[Lab]**.
- **The SELinux lab may run on Fedora** instead of the Debian VM if Debian's SELinux setup is impractical. It uses the same QEMU invocation, and the switch is recorded on the page.
- **`15/capabilities-in-containers` is written before `16/capabilities`** because the spec orders folders 14 → 15 → 16. Task 16 reconciles the two pages.
- **Three learning paths are added** ("write a driver" and "work on containers" are the spec's; "understand Linux security" follows the Phase 3 per-folder precedent).

**Known risks:**
- **Driver API drift** is the largest risk to the labs: `class_create`, void `remove`, `PCI_IRQ_INTX`, `pcim_iomap_regions`, and the PM macros. Every lab is built against the v6.18 lab kernel with zero warnings.
- **Distribution behaviour around user namespaces** (Ubuntu's AppArmor restriction, Debian's historic sysctl) is widely misreported. The page states only what was measured or what the distribution documents, dated.
- **Nested virtualization** may be unavailable in the lab VM, which blocks the KVM WAH. Task 15 allows a source-reading fallback and says so on the page.
- **Folder 16's tone.** Exploit detail creeps in through "for example" sentences and references. Task 19 Step 4 and Task 24 check for it twice.
