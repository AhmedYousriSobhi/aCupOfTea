# Benchmarks - NCCL

This document summarizes key concepts, interpretations, and practical guidance derived from NCCL AllReduce benchmarking on an 8×H200 NVLink system.

## Table of Contents
- [Benchmarks - NCCL](#benchmarks---nccl)
  - [Table of Contents](#table-of-contents)
  - [Motivation](#motivation)
  - [1. What is NCCL?](#1-what-is-nccl)
  - [2. The Core Primitives (The "Collectives")](#2-the-core-primitives-the-collectives)
  - [3. NCCL Execution Topologies: Rings Vs Tree](#3-nccl-execution-topologies-rings-vs-tree)
  - [4. Advanced Hardware Interconnect Protocols](#4-advanced-hardware-interconnect-protocols)
  - [5. Essential Telemetry Environment Variables for Engineering](#5-essential-telemetry-environment-variables-for-engineering)
  - [6. Common Structural Failures an HPC Engineer Must Triage](#6-common-structural-failures-an-hpc-engineer-must-triage)
  - [@hat would be different between: `mpirun -np 8 all_readuce - g 1` Vs. `mpirun -np 8 all_readuce - g 8`](#hat-would-be-different-between-mpirun--np-8-all_readuce---g-1-vs-mpirun--np-8-all_readuce---g-8)
  - [2. NCCL AllReduce Basics](#2-nccl-allreduce-basics)
  - [2. In-place vs Out-of-place](#2-in-place-vs-out-of-place)
  - [3. Important NCCL Metrics](#3-important-nccl-metrics)
  - [4. BusBW vs NVLink (critical concept)](#4-busbw-vs-nvlink-critical-concept)
  - [5. Example for benchmark result interpretation](#5-example-for-benchmark-result-interpretation)
  - [6. Message size sweep behavior](#6-message-size-sweep-behavior)
  - [7. Critical Flag Definitions:](#7-critical-flag-definitions)
  - [11. Performance interpretation (H200 NVLink)](#11-performance-interpretation-h200-nvlink)

---
## Motivation
For a High-Performance Computing (HPC) Performance Engineer, mastering NCCL (NVIDIA Collective Communications Library) is one of the most critical skills for scaling Deep Learning (LLMs, Mixture of Experts) and distributed AI workloads. When handling massive models across clusters of H100/H200 or Blackwell GPUs, performance bottlenecks almost always shift from pure compute (TFLOPS) to communication fabric.

---
## 1. What is NCCL? 
NCCL (pronounced "Nickel") is a stand-alone library of standard collective communication primitives topology-aware and highly optimized for NVIDIA GPUs.

In traditional scientific HPC, workloads rely on MPI (Message Passing Interface) running on the host CPU. However, MPI forces data to hop through host memory (RAM) and CPU sockets. NCCL is essentially "MPI for GPUs," written to bypass the CPU entirely wherever possible. It automatically detects the system's hardware topology and utilizes the fastest available path:

- Inside a Node: Direct GPU-to-GPU memory copies over high-speed physical NVLink lines and NVSwitches.
- Across Nodes: Cross-chassis communication using GPUDirect RDMA (Remote Direct Memory Access) over InfiniBand (or RoCE) network fabrics, pushing data straight from one GPU's memory pool into another node's GPU memory without stepping into the host system.

Following Github repositories: [NVIDIA/nccl.git](https://github.com/NVIDIA/nccl.git) and [NVIDIA/nccl-tests.git](https://github.com/NVIDIA/nccl-tests.git)

---

## 2. The Core Primitives (The "Collectives")

To know how the data moves during these collective operations, as different deep learning training phases rely on different primitives.

|Primitive|Description|Use Case|
|-|-|-|
AllReduce| Every GPU contributes an array of data, the data is combined (usually via summation), and the exact final global result is distributed back to all GPUs.|Deep Learning Use Case: Standard Data Parallelism (DDP). All GPUs compute independent gradients during the backward pass and must average them before the next optimization step.
AllGather| Every GPU starts with a small piece of data and sends it to all other GPUs, resulting in every GPU holding a combined, ordered array of everyone's pieces.|Deep Learning Use Case: Fully Sharded Data Parallelism (FSDP) or DeepSpeed ZeRO-3. When a specific layer is computed, weights sharded across GPUs are gathered in real-time.
ReduceScatter| The reverse of AllGather. Every GPU starts with a large array, the arrays are summed/reduced, and the resulting block is scattered so each GPU gets an equal slice of the final reduced array|Deep Learning Use Case: FSDP/ZeRO backward passes, where gradients are averaged and immediately partitioned across devices to minimize memory footprints.
All-to-All (AllToAll)| A personalized matrix transpose where every GPU sends unique, separate blocks of data to every other individual GPU.|Deep Learning Use Case: Mixture of Experts (MoE) models. Tokens must be dynamically routed to different specialized GPU "Experts" spread across the cluster fabric.

---
## 3. NCCL Execution Topologies: Rings Vs Tree

NCCL does not just blindly broadcast messages; it structures communication using logical graphs depending on message size and hardware scale:

||Ring Topology|Tree Topology
|-|-|-|
How it works|NCCL builds a logical, unidirectional ring traversing all GPUs.</br> Each device only sends data to its downstream neighbor and receives data from its upstream neighbor|NCCL constructs a logical double-binary tree structure across the nodes.
When it's used|Large messages.</br> Rings excel at maximizing total bandwidth capacity because they saturate all physical links simultaneously.</br> However, they suffer from high latency because a message must traverse N−1 hops around the ring.|Small messages.</br> Trees significantly minimize latency because the total hop count scales logarithmically (log2​N) rather than linearly.</br> It allows synchronization parameters and small gradient chunks to resolve rapidly.

---

## 4. Advanced Hardware Interconnect Protocols
To push your validation tests into optimal territory, you must understand the underlying acceleration features built into the hardware fabric:

|Protocols|Description|
|-|-|
|GPUDirect RDMA (GDR)|Without GDR, an inter-node message follows a costly path: GPU 0 VRAM → PCIe Switch → CPU RAM → InfiniBand NIC → Wire.</br> With GPUDirect RDMA enabled, the network card directly reads from the GPU’s high-bandwidth memory over the local PCIe switch line, cutting latency drastically and freeing CPU cycles.
Sharp (Scalable Hierarchical Aggregation and Reduction Protocol)|Traditionally, when performing an AllReduce, the GPUs themselves must use their streaming multiprocessors (SMs) to calculate the arithmetic math reductions (like summing up gradients).</br>InfiniBand SHARP: Collects and sums data packet-by-packet inside the ASICs of the physical InfiniBand switches as the data flies across the network wires.</br>NVLink SHARP (NVLS): On Hopper/Blackwell nodes, math reduction engines are built directly into the physical NVSwitches inside the chassis. The GPUs drop their arrays into the switch, the NVSwitch processes the addition in flight, and it returns the result. This completely unburdens the GPU compute cores and saves massive interconnect bandwidth.

---

## 5. Essential Telemetry Environment Variables for Engineering

As a performance engineer, you should never run NCCL blindly. You must interrogate its behavior by exporting environment variables before launching your training scripts or [nccl-tests](https://github.com/NVIDIA/nccl-tests.git):

|Env Variable|Purpose|
|-|-|
`export NCCL_DEBUG=INFO`|The absolute most important flag.</br> It forces NCCL to output detailed runtime initialization logs to stdout.</br> It will explicitly tell you whether it is using NVLink, PCIe, or InfiniBand, how many rings/trees it built, and what network interfaces it bound to.
`export NCCL_DEBUG_SUBSYS=INIT,COLL,ENV,NET`|Narrows down verbose tracing into initialization, collective algorithms selected, environmental changes, and networking interface negotiation.
`export NCCL_NET_GDR_LEVEL=5`|Forces NCCL's aggressiveness in using GPUDirect RDMA. Level 5 (SYS) tells NCCL to route GDR even if traffic must bridge host CPU sockets.</br> Level 3 (PIX) limits GDR to devices behind the exact same local PCIe switch tray.
`export NCCL_IB_DISABLE=0 and export NCCL_IB_HCA=mlx5_0,mlx5_1...`|Ensures InfiniBand is explicitly forced on and binds the specific host channel adapter (HCA) network interfaces that correspond perfectly to your local NUMA/GPU affinity profiles.

---

## 6. Common Structural Failures an HPC Engineer Must Triage

When running performance validation benchmarks like all_reduce_perf, deviations from target reference baselines indicate distinct environmental bottlenecks:

**| Symptom: High inter-node latency or low multi-node bandwidth**:</br>
Check: Run lsmod | grep nvidia_peermem.</br> 
If this specific kernel module isn't loaded into the Linux OS, GPUDirect RDMA fails globally, forcing NCCL to fallback to copying buffers through host CPU memory.

**| Symptom: Intra-node bandwidth is cut exactly in half (~220 GB/s instead of ~450 GB/s on Hopper)**:</br>
Check: The NVIDIA Fabric Manager system service (nvidia-fabricmanager) is likely down, misconfigured, or has a mismatched version relative to the base kernel driver.</br> 
Without Fabric Manager, the NVSwitches cannot construct unified non-blocking memory fabrics, crashing performance down to legacy ring boundaries.

**| Symptom: Erratic performance scaling across large node jobs**:</br>
Check: CPU core affinity masking. If your MPI/Slurm launcher spawns the NCCL rank processes without strict NUMA bindings matching the physical GPU placement layout, cross-socket context switching will bottleneck memory access paths.</br> 
Ensure workers are bound precisely to the CPU cores local to their respective GPU socket.

---
## @hat would be different between: `mpirun -np 8 all_readuce - g 1` Vs. `mpirun -np 8 all_readuce - g 8`

When launching the NCCL benchmark via mpirun, the difference between these two commands lies entirely in how many independent OS processes (MPI ranks) are created versus how many GPUs each individual process is told to manage. In short, the first command (-g 1) sets up a standard, production-like distributed environment, while the second command (-g 8) accidentally creates an oversubscribed, broken execution layout.</br>
Here is the exact architectural breakdown of what happens under the hood for an 8-GPU node:</br>

**1- `mpirun -np 8 ./all_reduce_perf -g 1` (The Correct, Standard Production Layout)**
- What it means: MPI spawns 8 separate OS processes (ranks). Each individual process is explicitly instructed to control exactly 1 GPU (-g 1).
- Under the Hood: * MPI launches Rank 0 through Rank 7.
    - Each rank binds to its local CPU core, initialises a single CUDA context, and takes ownership of exactly one physical GPU (e.g., Rank 0 handles cuda:0, Rank 1 handles cuda:1, etc.).
    - When the collective starts, NCCL initialises a communication ring/tree across these 8 separate processes.
- Performance & Validation Use Case: This is the industry-standard way to benchmark NCCL. It perfectly mimics how real distributed deep learning frameworks (like PyTorch DDP, Megatron-LM, or DeepSpeed) execute workloads. Each GPU operates independently with its own dedicated host process memory space, utilizing the full bandwidth of your NVLink mesh fabric.

**2- `mpirun -np 8 ./all_reduce_perf -g 8` (The Oversubscribed, Incorrect Layout)**
- What it means: MPI spawns 8 separate OS processes (ranks). However, each of those 8 processes is instructed to target and run an internal 8-GPU test (-g 8).
- Under the Hood: * MPI launches Rank 0 through Rank 7.
    - Rank 0 starts up and allocates memory across all 8 GPUs on the node.
    - Concurrently, Rank 1 starts up and also attempts to allocate memory across the exact same 8 GPUs.
    - This happens for all 8 ranks. You end up with 8 separate processes blindly competing for the same physical hardware resources on the node.
- Result & Behavior:
    - OOM (Out Of Memory): Because the max payload size scales up to gigabytes (e.g., -e 16G), multiplying that allocation 8 times across 8 competing ranks will instantly exhaust your HBM3e VRAM pool, throwing a cudaErrorMemoryAllocation or Out of memory crash.
    - Severe Resource Contention: If the payload is small enough not to crash, the 8 ranks will fight violently over the GPU copy engines, hardware contexts, and CPU scheduling queues.
    - Incorrect Matrix Tracking: NCCL will attempt to build an inner collective loop of 8 devices inside an outer loop of 8 MPI ranks, resulting in an aggregated, invalid test cluster size of 64 logical ranks mapped onto only 8 physical devices.

**| Summary Rule of Thumb**</br>
When writing automation scripts or executing validations on a modern HGX/DGX baseboard, remember this mathematical invariant for nccl-tests:
Total Physical GPUs Utilized=MPI Ranks (-np)×GPUs per Rank (-g)

- To test an 8-GPU node using the standard multi-process design:
    ```bash
    mpirun -np 8 ./all_reduce_perf -g 1
    ```
- Alternatively, if you ever want to run a single-process multi-GPU test (where one single master OS process spawns multiple internal threads to control all devices without relying heavily on MPI orchestration):
    ```Bash
    mpirun -np 1 ./all_reduce_perf -g 8
    ```
---

## 2. NCCL AllReduce Basics

**| What the test does**:</br>
`all_reduce_perf` benchmarks collective communication across GPUs.

Each GPU:
- allocates a buffer of size **S**
- participates in AllReduce operation
- repeats the operation multiple times

**| Key rule (very important)**:</br>
NCCL message size is **per GPU (per rank)**, not total system size.

So:</br>

| Setting | Meaning |
|----------|--------|
| `-b 1G -g 8` | 1 GiB per GPU × 8 GPUs = 8 GiB total |
| `-b 8G -g 8` | 8 GiB per GPU × 8 GPUs = 64 GiB total |


## 2. In-place vs Out-of-place

**| Out-of-place**
- input buffer ≠ output buffer
- safer, slightly more memory usage

**| In-place**
- input buffer == output buffer
- saves memory
- may slightly change kernel behavior

Example:</br>
```
Out-of-place: sendbuf → recvbuf
In-place: buf → buf (overwritten)
```

## 3. Important NCCL Metrics

| Metric | Meaning |
|--------|--------|
| time (us) | latency per operation |
| algbw | algorithm bandwidth |
| busbw | effective fabric bandwidth |

**| Recommendation**:</br>
- Use **BusBW** for system comparison.

## 4. BusBW vs NVLink (critical concept)

- NVLink 4.0 is hardware peak bandwidth (~900 GB/s per GPU bidirectional)
- NCCL BusBW is **derived collective performance**, not raw link speed.

Typical HGX H100/H200 8-GPU result: ~450–500 GB/s BusBW

## 5. Example for benchmark result interpretation

**| Observed peak**:</br>

| Metric | Value |
|--------|------:|
| Peak BusBW | 481.88 GB/s |
| Avg BusBW | 335.26 GB/s |
| GPUs | 8 × H200 |
| NCCL version | 2.18.5 |

**| Behavior**

- Performance saturates at ~1–2 GiB
- Stable plateau from 1G → 16G
- No errors (`#wrong = 0`)

## 6. Message size sweep behavior

Command: `-b 1M -e 16G -f 2`</br>
Generate: `1M → 2M → 4M → ... → 16G`</br>

## 7. Critical Flag Definitions:

|Option|Definition|
|-|-|
-b 1M| Starting message payload size (Minimum Bytes).
-e 16G| Ceiling message payload size (Maximum Bytes).
-f 2| Step factor multiplier used to advance through sizes.
-g 8| Total count of active, participating GPU devices locally.
-w 5| Number of initial unmeasured warmup loops to stabilize memory addresses.
-i 50| Number of measurement iterations per buffer step to ensure statistical variance control.

Example: `-n 100` Means</br>
- 100 repetitions per message size
- improves statistical stability
- does NOT increase data size

**| Total operations formula:**</br>
total_calls = message_sizes × iterations

## 11. Performance interpretation (H200 NVLink)

**| Observed plateau**:

| Size | BusBW |
|------|------:|
| 1G | ~466 GB/s |
| 2G | ~472 GB/s |
| 4G | ~477 GB/s |
| 8G | ~479 GB/s |
| 16G | ~482 GB/s |

**| Insight**:
- system saturates quickly
- large sizes mainly validate stability, not peak speed