---
id: interconnects-pcie-and-nvlink
title: "Interconnects: PCIe and NVLink"
sidebar_label: PCIe & NVLink
sidebar_position: 10
tags: [gpu, hardware, nvlink, pcie]
---

# Interconnects: PCIe and NVLink

Everything so far in this section covers bandwidth *inside* a single GPU — SM to L2, L2 to HBM. The moment a workload needs data on another device, whether that's the host CPU or a second GPU, a completely different and usually much slower link is in the critical path. Which link is available, and at what bandwidth, is not a software choice — it's a property of the physical topology of the machine, and designing a multi-GPU strategy without first knowing that topology is a common source of disappointing scaling.

## PCIe

PCI Express is the default link between a GPU and the host, and — absent NVLink — between GPUs as well. Its bandwidth doubles roughly every generation, and per-direction bandwidth for a x16 slot (the width GPUs use) is what actually matters for host-to-device transfers:

| Link | Generation | Per-direction bandwidth | Typical use |
| --- | --- | --- | --- |
| PCIe Gen3 x16 | Gen3 | ~15.75 GB/s | Host↔device on older systems (Kepler/Pascal/Volta era) |
| PCIe Gen4 x16 | Gen4 | ~31.5 GB/s | Host↔device, typical Ampere-era system |
| PCIe Gen5 x16 | Gen5 | ~63 GB/s | Host↔device, typical Hopper/Blackwell-era system |
| NVLink 3 | NVLink3 (A100) | ~300 GB/s (12 links) | A100 GPU-to-GPU |
| NVLink 4 | NVLink4 (H100) | ~450 GB/s (18 links) | H100 GPU-to-GPU |
| NVLink 5 | NVLink5 (B200/GB200) | ~900 GB/s (18 links) | Blackwell GPU-to-GPU |

Even at PCIe Gen5, per-direction host-device bandwidth (~63 GB/s) is roughly 50x lower than the H100's on-die HBM3 bandwidth from [Device Memory and Bandwidth](./device-memory-and-bandwidth.md) — which is why staging data across PCIe is treated as expensive relative to anything happening inside a single GPU.

## NVLink and NVSwitch

NVLink is NVIDIA's proprietary GPU-to-GPU (and, on some platforms, GPU-to-CPU) interconnect, offering both far higher bandwidth and lower latency than PCIe for the same link count, plus direct peer-to-peer memory access without routing through host memory. Each NVLink generation ships a fixed number of individual links per GPU (the table above's "12 links" / "18 links"), and the aggregate figure is what NVLink-connected GPUs actually achieve to each other. In systems with more than a handful of GPUs, **NVSwitch** sits between the GPUs' NVLink ports and lets every GPU reach every other GPU at full NVLink bandwidth simultaneously — without it, a GPU's fixed link budget would have to be divided across however many peers it talks to directly.

## Topology decides strategy

Two GPUs connected by NVLink through an NVSwitch and two GPUs that only share a PCIe root complex are, for practical multi-GPU decomposition purposes, different pieces of hardware, even if both pairs are nominally "GPUs in the same box." A halo-exchange or all-reduce pattern that assumes NVLink-class bandwidth between every pair of GPUs will bottleneck hard on a system where some of those pairs only have PCIe between them, or worse, only reach each other by routing through the host over `SYS` links (see below). [Peer-to-Peer Access and NVLink](../10-multi-gpu-and-scaling/peer-to-peer-and-nvlink.md) and [GPUDirect and RDMA](../10-multi-gpu-and-scaling/gpudirect-and-rdma.md) cover the APIs for actually using whichever link is present; this page is about knowing which one you have before writing that code.

## Discovering your topology

`nvidia-smi topo -m` prints a matrix of how every GPU (and NIC) pair on the machine is connected:

```bash
nvidia-smi topo -m
```

A representative 4-GPU system might report:

```text
        GPU0    GPU1    GPU2    GPU3    CPU Affinity   NUMA Affinity
GPU0     X      NV18    PIX     SYS     0-31           0
GPU1    NV18     X      SYS     SYS     0-31           0
GPU2    PIX     SYS      X      NV18    32-63          1
GPU3    SYS     SYS     NV18     X      32-63          1
```

- **`NV18`** — connected via NVLink presenting the full 18-link aggregate bandwidth for that generation (as if the pair were directly wired, typically because an NVSwitch routes all of both GPUs' links between them). GPU0↔GPU1 and GPU2↔GPU3 above have this — the fast path.
- **`PIX`** — connected through at most a single PCIe bridge/switch, no NVLink involved. Slower than NVLink but still a single local hop; GPU0↔GPU2 above.
- **`SYS`** — the connection has to cross the host's CPU-to-CPU interconnect (e.g. between NUMA sockets), traversing PCIe on both sides plus the socket link in between. This is the slowest path shown here, and it's what appears whenever two GPUs have neither an NVLink connection nor a shared local PCIe root complex — GPU0↔GPU3, GPU1↔GPU2, and GPU1↔GPU3 above.

A design that assumes uniform GPU-to-GPU bandwidth on a system whose topology looks like this will badly misjudge the cost of communication between, say, GPU1 and GPU3.

:::tip[Measure P2P bandwidth before designing the decomposition]
Don't infer bandwidth from the topology matrix alone — measure actual peer-to-peer bandwidth and latency between the specific GPU pairs a workload will use (CUDA's `p2pBandwidthLatencyTest` sample, or a direct copy-and-time, both work). Real achieved P2P bandwidth is what should drive a multi-GPU decomposition, not the nominal link-generation number. See [Peer-to-Peer Access and NVLink](../10-multi-gpu-and-scaling/peer-to-peer-and-nvlink.md) for the APIs.
:::

## See also

- [Device Memory and Bandwidth](./device-memory-and-bandwidth.md) — the on-die HBM bandwidth this page's PCIe/NVLink figures are dwarfed by.
- [Peer-to-Peer Access and NVLink](../10-multi-gpu-and-scaling/peer-to-peer-and-nvlink.md) — the APIs for using whichever link this page's topology check finds.
- [GPUDirect and RDMA](../10-multi-gpu-and-scaling/gpudirect-and-rdma.md) — bypassing host memory entirely for GPU-to-GPU and GPU-to-NIC transfers.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
