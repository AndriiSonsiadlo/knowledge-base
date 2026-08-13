---
id: the-accelerator-landscape
title: The Accelerator Landscape
sidebar_label: Accelerator Landscape
sidebar_position: 3
tags: [gpu, overview, npu, vendors]
---

# The Accelerator Landscape

Once you accept that some of your work belongs on a throughput engine, you have to pick one, and the market offers far more options than "NVIDIA or not". There are discrete GPUs on a PCIe slot, GPUs integrated into the same die as the CPU, phone-class GPUs paired with NPUs, datacenter training and inference ASICs reachable only through a compiler, and FPGAs where you describe the datapath yourself. They differ enormously in peak throughput — and that difference is almost never what decides the outcome.

The thesis of this page, and of the portability material later in the section, is blunt: **choosing hardware is mostly choosing a software stack, and stack maturity varies far more than peak FLOPS.** Two accelerators within 20% of each other on paper can be a factor of five apart in delivered performance, and ten times apart in engineering effort, because one has a decade of tuned libraries, a working profiler, and every framework upstreaming kernels for it, and the other has a compiler that silently falls back when it meets an operator it doesn't implement. Read every row of the table below as a statement about tooling first and silicon second.

## Discrete GPUs

The PCIe-attached (or NVLink-attached) discrete GPU is the default for anything compute-heavy, and it is where the section's CUDA material applies directly.

NVIDIA's datacenter line runs Hopper (H100, H200) into Blackwell (B200, and the GB200 CPU+GPU packages), with HBM capacities and bandwidths that have grown roughly one generation-step each cycle — an H100 SXM carries 80 GB of HBM3 at ~3.35 TB/s, an H200 141 GB of HBM3e at ~4.8 TB/s, a B200 192 GB of HBM3e at roughly 8 TB/s. The consumer line (Ada RTX 40-series, Blackwell RTX 50-series) shares the programming model and most of the compute capability surface, but with GDDR instead of HBM — an RTX 4090 pairs ~83 TFLOPS FP32 with only ~1 TB/s of GDDR6X — and with FP64 throughput cut deliberately. For development and for bandwidth-light workloads a consumer card is entirely adequate; for FP64 or for anything HBM-bound it is not.

AMD's Instinct line (MI300X and successors, CDNA architecture) is the credible datacenter alternative, competitive on memory capacity and bandwidth — MI300X ships 192 GB of HBM3 at ~5.3 TB/s, more than a contemporary H100 — and programmed through HIP, which is close enough to CUDA that mechanical translation usually works. Intel's Data Center GPU line and its Arc consumer parts round out the discrete field, programmed through oneAPI/SYCL and Level Zero.

## Integrated and mobile

Integrated GPUs share the CPU's physical memory, which changes the arithmetic completely: there is no PCIe transfer to amortise, so workloads that would never be worth offloading on a discrete card become viable. The tradeoff is bandwidth — an integrated part is limited to system DRAM, on the order of 100–500 GB/s on a wide LPDDR5X design, against multiple TB/s of HBM.

Apple silicon is the fullest expression of this: a unified memory architecture where CPU, GPU, and the Neural Engine address the same pool with no copies, programmed through Metal compute shaders, with Metal Performance Shaders and MLX layered on top for common primitives. Mobile SoCs from Qualcomm, Arm's partners, and MediaTek pair a modest GPU (Adreno, Mali/Immortalis) with a much more efficient NPU (Hexagon, Ethos), and on those parts the interesting compute mostly goes to the NPU rather than the GPU. NVIDIA's Jetson modules sit oddly in between — a genuine CUDA-capable GPU sharing memory with an Arm CPU, plus a fixed-function deep learning accelerator — which makes them the one embedded target where the rest of this section transfers unchanged.

## Datacenter inference and training ASICs

Above and beside the GPUs sit chips built for one job. Google's TPUs are the longest-running example: systolic-array matrix engines with large on-chip memory, reachable only through XLA, which means you program them by writing JAX or PyTorch-XLA and letting the compiler handle everything below. That is a real constraint — there is no equivalent of writing a hand-tuned kernel — and also the source of their appeal, because a graph that compiles cleanly needs no kernel engineering at all. AWS Inferentia and Trainium, Intel's Gaudi line, and a long tail of startup silicon follow the same pattern: a compiler-first stack where your leverage is at the graph level.

The failure mode across this whole category is uniform. Performance is excellent on the model architectures the vendor optimised for and unpredictable elsewhere, because a single unsupported operator can force a partition boundary or a host round trip. Evaluating one of these chips means compiling *your* model and reading the partition report, not reading a TOPS number.

## FPGAs

An FPGA is not an accelerator with a fixed architecture; it is a fabric on which you build one. That buys two things a GPU cannot offer: arbitrary bit widths (a 5-bit accumulator if that is what your algorithm wants) and deterministic, deeply-pipelined latency with no scheduler in the way. It costs you development time measured in a different unit — even with high-level synthesis, where you write C++ and the tool infers a datapath, an FPGA design cycle is dominated by hours-long place-and-route runs.

The practical niches are real but narrow: low-latency financial and network packet processing, signal processing chains with unusual precision requirements, and prototyping of ASIC dataflows. For dense floating-point throughput an FPGA loses to a GPU decisively, and it has for years. Both AMD (Vitis HLS, on the former Xilinx parts) and Intel/Altera (oneAPI FPGA flow) now offer C++-level entry points, which narrows the effort gap without closing it.

## The software stack each one implies

| Vendor | Hardware | Primary stack | Portable option |
|---|---|---|---|
| NVIDIA | GeForce, RTX/Quadro, Datacenter (Hopper, Blackwell), Jetson | CUDA C++, cuBLAS/cuDNN/CUTLASS, Nsight tooling | Source-portable to AMD via HIP (`hipify`); OpenCL, SYCL, OpenMP offload |
| AMD | Instinct (CDNA), Radeon (RDNA) | ROCm with HIP, rocBLAS/MIOpen | HIP itself is the portability layer; also SYCL and OpenMP offload |
| Intel | Data Center GPU Max, Arc, Gaudi | oneAPI (SYCL/DPC++) over Level Zero; OpenVINO for inference | SYCL is vendor-neutral by design; OpenCL |
| Apple | M-series GPU, Neural Engine | Metal compute shaders, Metal Performance Shaders, MLX | Core ML for inference; WebGPU in-browser; no CUDA path |
| Qualcomm | Adreno GPU, Hexagon NPU | Hexagon SDK, QNN / AI Engine Direct | ONNX Runtime with the QNN execution provider; TFLite delegates |
| Google | TPU v5/v6 and successors | XLA, reached through JAX or PyTorch-XLA | XLA is the only path — portability is at the framework level |
| Arm | Mali/Immortalis GPU, Ethos-U NPU | Ethos-U driver stack, CMSIS-NN | TensorFlow Lite / LiteRT Micro, ONNX Runtime |
| FPGA vendors (AMD, Altera) | Versal, Agilex and similar | Vitis HLS; Intel/Altera oneAPI FPGA flow | SYCL through the oneAPI FPGA flow; OpenCL on older toolchains |

Reading down the "portable option" column tells you where the leverage is. CUDA is the only column entry that is both a primary stack and, through HIP's near-mechanical translation, a viable source of portable code — which is why so much of the ecosystem is written in it first and ported afterwards. SYCL is the most genuinely vendor-neutral option and correspondingly the one where you most often give up the last factor of two. ONNX Runtime and TFLite occupy a different layer entirely: they do not port your kernels, they port your *model*, and they are the right abstraction whenever your workload is inference on a fixed graph. The full decision procedure lives in [Choosing a Portability Layer](../11-portable-and-vendor-neutral/choosing-a-portability-layer.md).

:::note[This table dates quickly]
The vendor and model names above reflect the landscape as of 2026 and will be partly wrong within a year — parts are renamed, stacks are merged or abandoned, and today's most promising startup silicon may not ship. The durable content is the *shape* of the tradeoff: a mature single-vendor stack buys delivered performance and tooling at the cost of lock-in; a portable stack buys optionality at the cost of some peak and a lot of library coverage; a compiler-only accelerator removes kernel work entirely and replaces it with the risk that your graph does not compile well. Those three positions have been stable for fifteen years and will outlast every model number here.
:::

## See also

- [CPU vs GPU vs NPU](./cpu-vs-gpu-vs-npu.md) — the architectural differences that put each of these vendors where they are.
- [Choosing a Portability Layer](../11-portable-and-vendor-neutral/choosing-a-portability-layer.md) — how to actually decide between HIP, SYCL, OpenCL, and staying on CUDA.
- [Edge NPUs](../12-npu-and-inference-accelerators/edge-npus.md) — the mobile and embedded end of the table in detail.
- [GPU & Accelerators](../readme.md) — the section index and its three learning paths.
