---
id: mps-and-mig
title: MPS and MIG
sidebar_label: MPS & MIG
sidebar_position: 9
tags: [gpu, cuda, runtime, sharing]
---

# MPS and MIG

A single GPU is often shared by more processes than it has obvious ways to divide itself among. The default sharing mechanism, time-slicing, works but wastes capacity on small kernels; two other mechanisms exist to do better, and they solve different problems. Multi-Process Service (MPS) lets independent processes' kernels run concurrently instead of merely taking turns; Multi-Instance GPU (MIG) physically partitions the hardware so processes don't share anything at all. Choosing between them means understanding what each one isolates and what it doesn't.

## One GPU, many processes

Without any of these mechanisms, every process that submits work to a GPU competes for the same set of hardware queues, and the GPU's default answer is to time-slice between them.

| | Time-slicing | MPS | MIG |
|---|---|---|---|
| Isolation | None — one bad process can stall others | Context-level, not memory-level | Real — physically separate hardware |
| Memory partitioning | None, shared address space per context | None, shared address space via one server context | Yes, fixed memory slice per instance |
| Error containment | Faulting process's context is torn down | None — one client's illegal access can take the whole server down | Yes, a fault in one instance doesn't affect others |
| Concurrency mechanism | Alternating time slices, no true overlap | Concurrent execution via one shared server context | Independent hardware, genuinely parallel |
| Supported hardware | All CUDA GPUs | All CUDA GPUs (Volta+ for the client-submission model used today) | A100-class and newer datacenter GPUs |
| Typical use | Default, unconfigured multi-tenant use | Many small, low-occupancy processes (e.g. MPI ranks) | Hard multi-tenant isolation, e.g. separate customers/jobs |

## Time-slicing (the default)

With no sharing mechanism configured, each process gets its own CUDA context, and the GPU switches between contexts' work in time slices — one context's kernels run for a while, then the GPU switches to the next context's queued work. Nothing overlaps: two processes' kernels never execute concurrently under pure time-slicing, they alternate. For workloads where each process already keeps the GPU busy, that's not a large loss; for many processes each submitting small, low-occupancy kernels, the GPU spends much of its time context-switching and under-occupied rather than computing.

## Multi-Process Service

MPS changes the concurrency mechanism, not the isolation model: client processes funnel their work through one shared MPS server context instead of each holding its own, and because the server sees all of it as one context's work, kernels from different clients can be scheduled onto the GPU concurrently rather than time-sliced. That's why MPS helps specifically with many small, low-occupancy kernels — the kind of workload MPI-style multi-process jobs produce — where concurrent execution lets kernels from different clients fill SMs that a single client's kernel leaves idle. A process that's already saturating the GPU on its own gains nothing from MPS, because there's no spare capacity for another client's kernels to run into.

```bash
# start the MPS control daemon
nvidia-cuda-mps-control -d

# stop it
echo quit | nvidia-cuda-mps-control
```

## Multi-Instance GPU

MIG takes the opposite approach: instead of sharing one context more cleverly, it physically divides the GPU. SMs, L2 cache slices, and memory controllers are partitioned into separate instances, each behaving like a smaller, independent GPU with its own fixed memory allocation. Because the partition is in hardware, not in a shared driver context, MIG gives real fault isolation and real performance isolation — one instance's workload cannot starve or crash another's.

```bash
nvidia-smi mig -cgi 9,9 -C
```

Each created instance gets its own device UUID, which is what selects it for a given process:

```bash
CUDA_VISIBLE_DEVICES=MIG-<instance-uuid> ./my_app
```

:::note[MIG needs A100-class hardware or newer]
MIG requires datacenter GPUs from the Ampere generation onward (A100 and later) with the hardware partitioning support built in. MPS has no such restriction — it works on any CUDA-capable GPU.
:::

## Choosing between them

:::warning[MPS gives no memory-error containment]
Because MPS clients share one server context, one client's illegal memory access can crash the MPS server itself, taking down every other client sharing it — there is no hardware boundary between them the way there is with MIG. MPS is a throughput optimization for cooperating, trusted processes, not an isolation mechanism. Use MIG instead whenever the workloads involved are untrusted, unrelated, or need a fault in one to be guaranteed not to affect the others.
:::

Time-slicing needs no configuration and is the right default when isolation and concurrency don't matter enough to justify setting up either alternative. MPS is the answer when the goal is throughput for many small, cooperating, trusted processes on hardware that may not support MIG. MIG is the answer when the goal is isolation between workloads that shouldn't be able to affect each other, on hardware that supports it.

## See also

- [Device Management](./device-management.md) — the device and context model that time-slicing, MPS, and MIG each modify differently.
- [Clusters and Schedulers](../10-multi-gpu-and-scaling/clusters-and-schedulers.md) — how a scheduler allocates MIG instances or MPS-shared GPUs across jobs.
- [Streams and Concurrency](./streams-and-concurrency.md) — the single-process concurrency model these mechanisms extend across processes.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
