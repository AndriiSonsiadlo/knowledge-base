---
id: clusters-and-schedulers
title: GPU Clusters and Schedulers
sidebar_label: Clusters & Schedulers
sidebar_position: 6
tags: [gpu, cuda, multi-gpu, slurm]
---

# GPU Clusters and Schedulers

A GPU on a shared cluster isn't just requested and used the way a local one is — a scheduler decides which physical devices a job gets, renumbers them from the job's point of view, and (on Kubernetes) treats them as an indivisible resource unless something extra is configured. Getting any of this wrong tends to look like a correctness bug — a job silently touching the wrong device, or "no GPUs available" on a node that clearly has some — rather than an obvious scheduling error.

## Requesting GPUs

Both major schedulers in use for GPU workloads — Slurm (HPC-style clusters) and Kubernetes (cloud-native clusters) — treat a GPU as a resource to request explicitly, not something a job gets by default. The request mechanism differs, but the underlying effect is the same: the scheduler picks physical devices, and the job sees only what it was given.

## Slurm

`sbatch` requests GPUs with `--gres=gpu:4` (generic resource syntax) or the more specific `--gpus-per-node=4`, and Slurm sets `CUDA_VISIBLE_DEVICES` for the job itself, scoped to whichever physical GPUs it allocated. A job that also sets `CUDA_VISIBLE_DEVICES` in its own script usually breaks itself — it's overriding a value Slurm already computed correctly, often narrowing it to a subset of what was actually granted or pointing at device indices that don't exist in the job's cgroup.

```bash showLineNumbers title="train.sbatch"
#!/bin/bash
#SBATCH --job-name=multi-gpu-train
#SBATCH --nodes=1
#SBATCH --gpus-per-node=4
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=8

srun torchrun --nproc_per_node=4 train.py
```

`--ntasks-per-node=4` matches one Slurm task to each of the four requested GPUs, and `srun` launches all four under Slurm's process management — `torchrun` then handles the rank assignment within that.

## Kubernetes

Kubernetes exposes a GPU as the extended resource `nvidia.com/gpu`, requested in a pod's resource limits:

```json
{
  "apiVersion": "v1",
  "kind": "Pod",
  "spec": {
    "containers": [
      {
        "name": "train",
        "image": "my-training-image:latest",
        "resources": {
          "limits": {
            "nvidia.com/gpu": 2
          }
        }
      }
    ]
  }
}
```

This only works with the NVIDIA device plugin for Kubernetes installed on the cluster — it's what advertises `nvidia.com/gpu` as a schedulable resource in the first place and binds requested GPUs to the container. Without extra configuration, GPUs are allocated whole: a pod requesting `1` gets exclusive use of one physical GPU, and there's no way to request "half a GPU" through the resource model alone. Fractional allocation needs MPS, MIG, or time-slicing configured on top — see Sharing policies below.

## `CUDA_VISIBLE_DEVICES`

`CUDA_VISIBLE_DEVICES` doesn't filter which devices a process can see in the abstract — it **renumbers** them from that process's perspective. Setting `CUDA_VISIBLE_DEVICES=2,3` makes physical GPU 2 appear as device 0 and physical GPU 3 appear as device 1 inside that process; device indices used anywhere else in the program (`cudaSetDevice(0)`, for instance) now refer to physical GPU 2, not physical GPU 0. This is exactly the mechanism both Slurm and the Kubernetes device plugin use to hand a job only the GPUs it was allocated, without the job's code needing to know or care which physical GPUs those are.

:::warning[Renumbering makes logs ambiguous across jobs]
"Device 0" in one job's logs and "device 0" in another job's logs on the same node can be two entirely different physical GPUs, because each job's `CUDA_VISIBLE_DEVICES` renumbers independently. When device identity matters for debugging — correlating a hardware fault or a specific GPU's behavior across jobs — log the device UUID from `cudaDeviceProp` (or `nvidia-smi -L`) rather than the process-local index; the UUID is the one identifier that doesn't get remapped.
:::

## Containers

The NVIDIA Container Toolkit is what makes `docker run --gpus all` (or the Kubernetes device plugin's equivalent) work: it injects the host's GPU devices and driver libraries into the container at startup. The split that matters is which side owns which piece — the **driver** comes from the host (it must match the kernel module loaded on the host machine) while the **CUDA toolkit and libraries** come from the image. A container built against a newer CUDA toolkit than the host driver supports will fail or silently downgrade features; the driver is never something the container ships itself.

## Sharing policies

Whether a scheduler can pack more than one job onto a single GPU — and how isolated those jobs are from each other when it does — is governed by the same time-slicing, MPS, and MIG mechanisms described in [MPS and MIG](../06-cuda-runtime-and-apis/mps-and-mig.md); this page doesn't restate them. What's specific to a cluster context is that the scheduler has to be told about whichever mechanism is in use — Kubernetes needs MIG instances exposed as their own distinct resource types, for instance — rather than the mechanism working transparently underneath a plain `nvidia.com/gpu: 1` request.

## See also

- [Multi-GPU Basics](./multi-gpu-basics.md) — the process-per-device model these schedulers exist to launch and coordinate.
- [MPS and MIG](../06-cuda-runtime-and-apis/mps-and-mig.md) — the sharing and partitioning mechanisms a scheduler allocates on top of.
- [Device Management](../06-cuda-runtime-and-apis/device-management.md) — the per-process device state `CUDA_VISIBLE_DEVICES` renumbers.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
