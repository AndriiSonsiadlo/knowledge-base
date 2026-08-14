---
id: installing-the-cuda-toolkit
title: Installing the CUDA Toolkit
sidebar_label: Installing CUDA
sidebar_position: 1
tags: [gpu, cuda, toolkit, setup]
---

# Installing the CUDA Toolkit

Getting `nvcc` to compile a `.cu` file and getting a program to actually run on the GPU are two different problems, and most first-time setup failures come from conflating them. Three separate pieces of software have to agree with each other — a kernel-level driver, a toolkit for building code, and a runtime linked into the binary — and version mismatches between them are the single most common reason "it compiled but won't run" happens.

## Driver, toolkit, and runtime

The three layers, in the order they get installed and the order they matter:

- **Driver.** A kernel module (`nvidia.ko` on Linux) that talks to the GPU directly. It reports the maximum CUDA version it supports, and it is backward compatible with older toolkits — a driver built for CUDA 13 will happily run a binary built with the CUDA 11 toolkit.
- **Toolkit.** `nvcc` (the compiler driver), headers, and the development libraries (cuBLAS, cuFFT, and so on). This is what you install to *build* CUDA programs; it is not required on a machine that only *runs* them.
- **Runtime.** `libcudart`, statically or dynamically linked into your binary. It's what your compiled program actually calls at execution time, and it's what has to be present — as a shared library, if you linked dynamically — on any machine that runs the binary.

The compatibility rule follows directly from that ordering: a newer driver can run a binary built against an older toolkit, but a toolkit newer than the installed driver may refuse to run — the driver has to support the CUDA version the toolkit targeted.

## Version compatibility

Check `nvidia-smi`'s reported "CUDA Version" against the toolkit version before assuming a mismatch is the problem — that field is the *maximum* CUDA version the driver supports, not the version anything is actually running. A toolkit at or below that number is expected to work; a toolkit above it is not.

:::note[Every compute-capability requirement is tied to hardware, not the toolkit]
The toolkit version controls which language features and APIs are *available to compile against*; whether a given kernel actually runs on a given GPU is a separate question governed by [Compute Capability](../02-gpu-hardware-architecture/compute-capability.md). A recent toolkit can still target an old, low-compute-capability GPU as long as you compile for the right architecture.
:::

## Installing

On Linux, the toolkit is typically installed either from a distro package repository or via NVIDIA's `.run` installer, and on Windows via the standalone installer bundled with (or separate from) the driver. Whichever route you take, install driver and toolkit from the *same* source family — see the warning below.

## WSL2

Under WSL2, the GPU driver is installed on **Windows**, not inside the Linux distribution. The distro gets a special, WSL-aware libcuda that talks through to the Windows-hosted driver via `/usr/lib/wsl/lib` — installing a normal Linux driver package inside the distro conflicts with this bridge and breaks GPU access. Install only the CUDA toolkit inside WSL2; leave driver installation to Windows.

## Containers

Container runtimes don't see the GPU by default — the host driver has to be exposed into the container. The `nvidia-container-toolkit` package configures Docker to do this, after which `docker run --gpus all ...` passes the host's GPU(s) through to the container. The container image only needs a compatible CUDA runtime/toolkit layer; it never needs its own driver, because the driver is a kernel-level component supplied by the host.

## Verifying the install

Three commands, in order of what they each confirm:

```bash
nvidia-smi                 # driver version + CUDA version the driver supports
nvcc --version             # toolkit version
/usr/local/cuda/extras/demo_suite/deviceQuery   # if installed
```

`nvidia-smi` confirms the driver is loaded and reports the device(s) it manages. `nvcc --version` confirms the toolkit that's on `PATH`. `deviceQuery`, part of the CUDA samples, actually opens the device and prints its properties — the strongest of the three checks, since the first two can succeed even if the runtime can't touch the GPU.

If a Python environment is the actual target, the fastest end-to-end check is whether a framework already on the machine sees the device at all:

```python
import torch
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))
print(torch.version.cuda)          # toolkit PyTorch was built against
```

:::warning[Don't mix a distro-packaged driver with a `.run` installer]
Installing the driver from a distro's package manager (e.g. `apt install nvidia-driver-...`) and later running NVIDIA's `.run` installer — or the reverse — leaves two driver installations partially overlapping on disk. The symptoms range from a driver that fails to load after a kernel update to `nvidia-smi` reporting a version that doesn't match what's actually loaded. Pick one installation method and uninstall fully before switching to the other.
:::

## See also

- [Your First Kernel](./your-first-kernel.md) — the first program to compile and run once the toolkit is verified.
- [The Compilation Model](./the-compilation-model.md) — what `nvcc` actually does with a `.cu` file.
- [Building CUDA with CMake](../09-tooling-profiling-and-debugging/building-cuda-with-cmake.md) — driving the same toolchain from a build system instead of the command line.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
