---
id: gpudirect-and-rdma
title: GPUDirect and RDMA
sidebar_label: GPUDirect & RDMA
sidebar_position: 5
tags: [gpu, cuda, multi-gpu, rdma]
---

# GPUDirect and RDMA

Every transfer that has to bounce through a staging buffer in host memory pays for it twice — once copying into the buffer, once out — and that cost shows up whenever a GPU needs to talk to something other than another GPU on the same NVLink fabric: a network card, an NVMe drive, storage over the network. GPUDirect is NVIDIA's umbrella name for the mechanisms that let those other devices address GPU memory directly instead.

## Bypassing the host

GPUDirect P2P, GPUDirect RDMA, and GPUDirect Storage are three variants of the same idea: remove the bounce through host memory, saving both bandwidth (no duplicate copy) and latency (no round trip through the CPU). Each needs kernel and driver support for the same underlying reason — a third-party device (a NIC, an NVMe controller) has to be able to address GPU memory directly, and that's not something PCIe gives a device for free; the driver has to expose GPU memory in a form the third-party device's DMA engine can target.

## GPUDirect P2P

Covered on [Peer-to-Peer Access and NVLink](./peer-to-peer-and-nvlink.md) — this is the GPU-to-GPU case, where the "third-party device" is simply another GPU on the same node.

## GPUDirect RDMA

GPUDirect RDMA extends the same idea to the network: an InfiniBand or RoCE NIC DMAs data straight into or out of GPU memory, with no host-memory staging buffer in the path at all. This is what makes NCCL's inter-node path fast — without it, every cross-node collective would pay a GPU-to-host copy and a host-to-NIC copy (and the reverse on receive) on top of the network transfer itself. It requires the `nvidia-peermem` kernel module (or DMA-BUF on newer driver/NIC stacks) to be loaded and the NIC and GPU to sit close enough in the PCIe topology for the DMA path to work at all.

Multi-rail configurations — more than one NIC per GPU — exist precisely because a single NIC's bandwidth can be lower than what NVLink delivers intra-node; matching NIC count and placement to GPU count is a topology decision the same way NVLink pairing is, not something that fixes itself once RDMA is enabled.

## GPUDirect Storage

GPUDirect Storage applies the same bypass to NVMe: data moves from an NVMe drive straight into GPU memory without a host-memory bounce, through the `cuFile` API.

```cpp showLineNumbers
CUfileHandle_t fh;
CUfileDescr_t desc = {};
desc.handle.fd = fd;               // POSIX fd of the opened file
desc.type = CU_FILE_HANDLE_TYPE_OPAQUE_FD;
cuFileHandleRegister(&fh, &desc);
cuFileBufRegister(d_buf, size, 0); // register the GPU destination buffer
cuFileRead(fh, d_buf, size, file_offset, 0);
```

The win is largest for workloads bottlenecked on getting data *to* the GPU rather than on compute — data-loading-bound inference pipelines and analytics over large datasets, where the CPU-side staging copy that GPUDirect Storage removes was otherwise sitting directly in the critical path.

`cuFileHandleRegister` associates a `CUfileHandle_t` with an already-open POSIX file descriptor; `cuFileBufRegister` pins the destination GPU buffer so the NVMe controller's DMA engine can target it directly; `cuFileRead` then performs the transfer. The registration calls are one-time setup cost per file and buffer — the actual reads that follow are what get to skip the host bounce.

## When the network becomes the bottleneck

| Path | Without GPUDirect | With GPUDirect |
|---|---|---|
| GPU ↔ GPU (same node) | GPU → host → GPU (2 hops) | GPU → GPU (1 hop) |
| GPU ↔ NIC (inter-node) | GPU → host → NIC → network (3 hops) | GPU → NIC → network (2 hops) |
| GPU ↔ NVMe | GPU → host page cache → GPU (2 hops, plus the storage read itself) | GPU → NVMe (1 hop, plus the storage read itself) |

Once the extra host hop is removed, whatever's left — network fabric bandwidth for RDMA, drive throughput for Storage — becomes the actual ceiling, and that's the point at which topology (how many NICs per GPU, how they're wired) starts mattering as much as the GPUDirect path itself.

:::warning[GPUDirect falls back silently when unavailable]
GPUDirect RDMA and Storage both need specific hardware, driver, and topology support — the right kernel module loaded, the NIC or NVMe controller close enough to the GPU in the PCIe tree, compatible firmware. When that support isn't there, the stack doesn't error out; it silently falls back to a staged copy through host memory, and the only symptom is worse-than-expected bandwidth. Verify the fast path is actually active with `NCCL_DEBUG=INFO` for the RDMA case, or the `cuFile` diagnostics (`gds_stats`, `cufile.log`) for storage — don't assume it from the hardware being nominally present.
:::

## See also

- [Peer-to-Peer Access and NVLink](./peer-to-peer-and-nvlink.md) — the intra-node case of the same host-bypass idea.
- [GPU Clusters and Schedulers](./clusters-and-schedulers.md) — the multi-node topology GPUDirect RDMA depends on.
- [Interconnects: PCIe and NVLink](../02-gpu-hardware-architecture/interconnects-pcie-and-nvlink.md) — the link bandwidths that set the ceiling GPUDirect lets a transfer actually reach.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
