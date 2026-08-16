---
id: peer-to-peer-and-nvlink
title: Peer-to-Peer Access and NVLink
sidebar_label: Peer-to-Peer & NVLink
sidebar_position: 2
tags: [gpu, cuda, multi-gpu, nvlink]
---

# Peer-to-Peer Access and NVLink

Two GPUs in the same box can talk to each other directly, or every byte between them can detour through host memory — the difference is entirely a matter of whether peer access has been enabled, and it has real bandwidth consequences either way. This page covers the API for checking, enabling, and using that direct path; the bandwidths themselves live on [Interconnects: PCIe and NVLink](../02-gpu-hardware-architecture/interconnects-pcie-and-nvlink.md).

## What P2P gives you

Peer-to-peer (P2P) access lets one GPU's kernel read or write another GPU's memory directly, and lets `cudaMemcpy`-family calls move data GPU-to-GPU without staging through a host buffer. Whether it's available at all depends on the physical link between the two devices — NVLink (with or without an NVSwitch), a shared PCIe switch, or nothing usable at all if the pair only reaches each other over `SYS` — and CUDA won't attempt it silently; the application has to ask.

## Enabling it

```cpp showLineNumbers
int canAccess = 0;
CUDA_CHECK(cudaDeviceCanAccessPeer(&canAccess, 0, 1));
if (canAccess) {
    CUDA_CHECK(cudaSetDevice(0));
    CUDA_CHECK(cudaDeviceEnablePeerAccess(1, 0));   // 0 accesses 1's memory
    CUDA_CHECK(cudaMemcpyPeerAsync(d1, 1, d0, 0, bytes, stream));
}
```

`cudaDeviceCanAccessPeer(&canAccess, 0, 1)` asks whether device 0 can access device 1's memory — the check is directional, so a full mesh across `N` devices needs it queried both ways for every pair. `cudaDeviceEnablePeerAccess(1, 0)` is called with device 0 current and grants *that* device access to device 1 (the second argument is a reserved flags parameter, always `0`); it has to be called once per direction and once per device pair, not globally.

## Direct copies and direct access

Two different things are enabled by the same peer-access setup, and conflating them leads to bad decisions:

- `cudaMemcpyPeerAsync` / `cudaMemcpyPeer` is a **copy** — an explicit, bulk transfer from one device's buffer to another's, and it's the right tool whenever the transfer volume is large or the access pattern is regular.
- Peer **access** lets a kernel running on device 0 dereference a pointer into device 1's memory directly, as if it were a regular pointer, without an explicit copy at all. It's convenient — no separate transfer step, no intermediate buffer — but every single access crosses the interconnect at that access's own latency and granularity, with none of the batching a bulk copy gets. It only makes sense for low-volume, irregular access patterns; using it as a substitute for a bulk copy of a large regular region is much slower than just copying.

## Discovering topology

```bash
nvidia-smi topo -m
```

```text
        GPU0    GPU1    GPU2    GPU3    CPU Affinity   NUMA Affinity
GPU0     X      NV18    PIX     SYS     0-31           0
GPU1    NV18     X      SYS     SYS     0-31           0
GPU2    PIX     SYS      X      NV18    32-63          1
GPU3    SYS     SYS     NV18     X      32-63          1
```

- **`NV#`** (e.g. `NV18`) — NVLink-connected, with the number naming the aggregate link count for that generation; the fast path, and the pairing to prefer for anything bandwidth-sensitive.
- **`PIX`** — connected through at most one PCIe bridge/switch, no NVLink; slower than NVLink but still a single local hop.
- **`PXB`** — connected through multiple PCIe bridges without crossing a host bridge; one step down from `PIX`.
- **`NODE`** — connected within the same NUMA node but crossing a host bridge, not just a PCIe switch.
- **`SYS`** — the connection crosses the host's CPU-to-CPU interconnect between NUMA sockets; the slowest path shown, and one to actively avoid placing communication-heavy pairs on.

Placement follows directly from this table: put the two halves of a tightly-coupled pair (a tensor-parallel shard split across two devices, for instance) on an `NV#` pair, not a `SYS` pair, and confirm it with this command before assuming the topology matches expectations.

:::warning[A false `cudaDeviceCanAccessPeer` fails silently, not loudly]
P2P over PCIe can be blocked by the chipset or by IOMMU settings even when the devices are physically on the same bus, and there's no error raised for it — `cudaDeviceCanAccessPeer` just returns false. Code that doesn't check the return value and instead always calls `cudaMemcpyPeerAsync` still works in that case; CUDA routes the copy through host memory instead, at a large and easy-to-miss cost. Always branch on the check rather than assuming P2P is available because the devices look adjacent.
:::

## Bandwidth expectations

Achieved bandwidth between two devices depends entirely on which link connects them, and the numbers for each interconnect generation are covered in [Interconnects: PCIe and NVLink](../02-gpu-hardware-architecture/interconnects-pcie-and-nvlink.md) rather than repeated here — an `NV#` pair on current NVLink generations delivers roughly an order of magnitude more bandwidth than a `PIX` or `SYS` pair falling back to PCIe, which is why the topology check above should come before, not after, a multi-GPU decomposition is designed.

## See also

- [Collectives with NCCL](./collectives-with-nccl.md) — the algorithms built on top of this direct-transfer path when more than two devices are involved.
- [GPUDirect and RDMA](./gpudirect-and-rdma.md) — extending the same "skip the host" idea to storage and network devices.
- [Interconnects: PCIe and NVLink](../02-gpu-hardware-architecture/interconnects-pcie-and-nvlink.md) — the bandwidth figures per link generation.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
