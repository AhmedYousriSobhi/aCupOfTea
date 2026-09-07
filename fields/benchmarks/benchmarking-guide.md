# The HPC Benchmarking Landscape: A Field Guide

> One node. Five different questions. Five different tools. This is the map that ties `OSU`, `STREAM/BabelStream`, `HPL`, `NCCL`, and the execution/affinity layer together — plus the benchmarks that haven't come up yet but will, the moment you validate your next node.

## Table of Contents
- [The HPC Benchmarking Landscape: A Field Guide](#the-hpc-benchmarking-landscape-a-field-guide)
  - [Table of Contents](#table-of-contents)
  - [Why one benchmark is never enough](#why-one-benchmark-is-never-enough)
  - [The mental map](#the-mental-map)
  - [The core five — quick index](#the-core-five--quick-index)
  - [The benchmarks we haven't covered yet](#the-benchmarks-we-havent-covered-yet)
    - [Compute-adjacent](#compute-adjacent)
    - [Memory \& storage adjacent](#memory--storage-adjacent)
    - [Communication-adjacent](#communication-adjacent)
  - [A complete node validation walkthrough](#a-complete-node-validation-walkthrough)
  - [The diagnostic flowchart](#the-diagnostic-flowchart)
  - [The one table to screenshot](#the-one-table-to-screenshot)
  - [Further reading in this series](#further-reading-in-this-series)

---

## Why one benchmark is never enough

Every HPC node is really four separate subsystems wearing a single hostname:

```
Compute  →  how fast can it do math?
Memory   →  how fast can it feed that math?
Communication → how fast can it talk to its neighbors?
Orchestration → is the software stack even placing work correctly?
```

A single "the node feels slow" complaint could be caused by any one of these — or, more often, by a *misconfiguration between two of them* (wrong rank placement, wrong NUMA binding, wrong buffer type). Running one benchmark and declaring victory is how regressions slip through acceptance testing. Running the *right sequence* of benchmarks is how you actually localize the fault before you touch a support ticket.

---

## The mental map

```
                         HPC Node Validation
                                 │
        ┌────────────────┬──────┴──────┬────────────────────┐
        │                │             │                    │
     Compute           Memory     Communication        Orchestration
        │                │             │                    │
   ┌────┴────┐    ┌──────┴──────┐  ┌───┴────┐        (Affinity / Placement
   │         │    │             │  │        │         — the layer that makes
  HPL      HPL-GPU │        BabelStream │    │          every other number
 (CPU)              STREAM CPU  stream-gpu-test        trustworthy or garbage)
                                        │
                                ┌───────┴───────┐
                                │               │
                              MPI               NCCL
                                │               │
                              OSU          nccl-tests
                                │
                         ┌──────┴──────┐
                         │             │
                    CPU buffers   GPU buffers (CUDA-aware)
```

The single most important idea in this whole map: **compute, memory, and communication are orthogonal.** A win in one tells you nothing about the others. A GPU that aces BabelStream can still fail NCCL. A node that aces OSU over CPU buffers can still choke the moment you switch to GPU-aware MPI. Test them separately, on purpose.

---

## The core five — quick index

| # | Benchmark | One-line job | Full write-up |
|---|---|---|---|
| 1 | **OSU Micro-Benchmarks** | MPI point-to-point & collective latency/bandwidth over the network | *(see OSU deep-dive)* |
| 2 | **STREAM / BabelStream / stream-gpu-test** | Raw memory bandwidth — CPU RAM or GPU HBM, before any real compute happens | [`stream-benchmarks-blog.md`](#) |
| 3 | **HPL / HPL-GPU** | Dense linear algebra compute throughput — the TOP500 number | [`hpl-benchmarks-blog.md`](#) |
| 4 | **NCCL / nccl-tests** | GPU-native collective communication — NVLink, NVSwitch, GPUDirect RDMA | [`nccl-benchmarks-blog.md`](#) |
| 5 | **Parallel Execution & Affinity** | Not a benchmark itself — the placement/binding discipline that makes the other four *trustworthy* | [`parallel-execution-affinity-blog.md`](#) |

Plus the standalone **Intel vs. Netlib HPL comparison** — a worked example of why "same binary category, different vendor build" numbers aren't directly comparable without controlling for problem size. ([`hpl-cpu-comparison-blog.md`](#))

---

## The benchmarks we haven't covered yet

The five above get you most of the way through H200-class node validation — but the broader HPC benchmarking world is bigger. Here's what else exists, organized by the same compute/memory/communication/storage split, so you know what to reach for when OSU, HPL, STREAM, and NCCL don't answer the question in front of you.

### Compute-adjacent

| Benchmark | What it tests | When you'd reach for it |
|---|---|---|
| **HPCG** (High Performance Conjugate Gradient) | Sparse linear algebra — deliberately *memory-bandwidth-bound*, unlike HPL's compute-bound dense math | TOP500's companion list; a much more "realistic application" proxy than HPL |
| **MLPerf (Training / Inference / HPC)** | End-to-end ML workload throughput on real model architectures (BERT, ResNet, GPT-style) | Validating a GPU cluster's actual deep-learning throughput, not just raw FLOPS |
| **SPEC CPU / SPEC HPC** | General-purpose CPU throughput across a broad workload suite | Comparing CPU generations/vendors outside of pure linear algebra |
| **Graph500** | Breadth-first search / graph traversal performance | Irregular-memory-access workloads — very different stress profile than dense HPL |

### Memory & storage adjacent

| Benchmark | What it tests | When you'd reach for it |
|---|---|---|
| **Intel MLC (Memory Latency Checker)** | Fine-grained memory latency *and* bandwidth, per NUMA domain, per access pattern | Diagnosing exactly *where* in the NUMA topology a memory bottleneck lives — more granular than STREAM |
| **IOR / IOzone / mdtest** | Parallel filesystem I/O throughput and metadata performance | Validating Lustre/Weka/GPFS storage — the layer STREAM and OSU don't touch at all |
| **fio** | Block-device-level I/O benchmarking | Isolating storage hardware from the parallel filesystem layer above it |

### Communication-adjacent

| Benchmark | What it tests | When you'd reach for it |
|---|---|---|
| **GPCNeT** (Global Performance and Congestion Network Test) | Network congestion and "noisy neighbor" interference under concurrent load | Multi-tenant cluster fabrics — does one job's traffic pattern degrade another job's? |
| **iperf3 / netperf** | Raw TCP/UDP throughput, no MPI or RDMA involved | Baseline Ethernet sanity check before layering RoCE/MPI complexity on top |
| **ib_send_bw / ib_read_bw / perftest suite** | Raw InfiniBand verbs-level bandwidth and latency — below MPI entirely | Isolating "is the fabric itself fine" from "is my MPI stack configured correctly" — the layer *underneath* OSU |

> [!TIP]
> When OSU gives you a bad number, `perftest` (ib_send_bw etc.) is often your next move — it strips MPI out of the equation entirely and talks to the verbs layer directly. If `perftest` looks great but OSU looks bad, the problem is definitely in your MPI stack, not the fabric.

---

## A complete node validation walkthrough

Putting the whole map into a single run order — this is roughly the sequence I'd actually execute on a fresh H200 node before signing off on it:

```
1. Affinity sanity check
   numactl --hardware && nvidia-smi topo -m
   → confirm NUMA layout and GPU/NIC topology match what you expect

2. Memory bandwidth (before anything else touches compute or network)
   BabelStream / STREAM-CPU
   → establishes the ceiling everything downstream is competing against

3. Compute throughput
   HPL-CPU  → validate raw CPU floating-point path
   HPL-GPU  → validate GPU-dominant compute path, watch for CPU-stall-on-panel-factorization

4. Network — CPU path first
   OSU (host buffers): osu_latency, osu_bw, osu_bibw
   → isolates plain MPI-over-fabric, no GPU complexity yet

5. Network — GPU-aware path
   OSU (CUDA buffers, D D)
   → isolates whether MPI's GPU-aware/GPUDirect path is actually working

6. GPU-native communication
   nccl-tests (all_reduce_perf, -g 1, matching -np to GPU count)
   → validates NVLink/NVSwitch/GDR independent of MPI entirely

7. Storage (if the workload is I/O-heavy)
   IOR / mdtest against the target parallel filesystem

8. Only now — application-level validation
   MLPerf-style training run, or your actual production workload
```

Steps 1–6 are diagnostic. Step 8 is the number that actually matters to your users — but it's meaningless to debug directly if you skipped 1–6, because a slow training run could be caused by *any* of the five layers above it, and step 8 alone won't tell you which one.

---

## The diagnostic flowchart

When something's slow and you don't know why yet, this is the actual decision tree:

```
                    "The job is slower than expected"
                                  │
                                  ▼
              Run BabelStream / STREAM — is memory BW normal?
                       │                          │
                      NO                          YES
                       │                          │
          Memory subsystem issue          Run HPL — is compute
          (DIMM config, NUMA           throughput near theoretical peak?
           first-touch, channel                    │
           population)                    ┌────────┴────────┐
                                          NO                  YES
                                           │                  │
                              Check affinity/binding    Run OSU (CPU buffers) —
                              (Part 5 of the affinity    is host-to-host MPI
                               guide) before blaming      bandwidth/latency normal?
                               the silicon                        │
                                                          ┌────────┴────────┐
                                                         NO                  YES
                                                          │                  │
                                              Check MPI config,     Run OSU (GPU buffers)
                                              transport (UCX/OFI),  or nccl-tests —
                                              rank placement,       is GPU-to-GPU comm
                                              perftest (ib_send_bw) normal?
                                              to isolate fabric              │
                                              vs. MPI stack         ┌────────┴────────┐
                                                                   NO                  YES
                                                                    │                  │
                                                        Check GPUDirect RDMA,   The bottleneck is
                                                        nvidia-fabricmanager,   likely application-
                                                        NCCL_DEBUG=INFO logs,   level, not infra —
                                                        GPU↔NIC topology        profile the code itself
```

---

## The one table to screenshot

If you remember nothing else from this series, remember this:

| Layer | Benchmark | Bad number means... | Good number alone tells you... |
|---|---|---|---|
| **Memory** | BabelStream / STREAM | DIMM/HBM config, NUMA placement, or first-touch policy is wrong | Nothing about compute or network — they're independent |
| **Compute** | HPL / HPL-GPU | Wrong P×Q grid, bad thread affinity, wrong BLAS linkage, AVX throttling | Nothing about whether ranks can actually talk to each other |
| **MPI network** | OSU | Wrong transport, bad rank placement, GDR misconfigured, NUMA/NIC mismatch | Nothing about NCCL's independent GPU-native path |
| **GPU-native network** | NCCL / nccl-tests | Missing `nvidia_peermem`, dead `nvidia-fabricmanager`, bad GPU↔NIC topology | Nothing about your actual MPI application's communication pattern |
| **Placement/orchestration** | *(no single benchmark — verify manually)* | Every layer above will report a "fine" number for the *wrong resource*, silently invalidating the test | This is the layer that makes all four other layers' results meaningful in the first place |

---

## Further reading in this series

- **OSU Micro-Benchmarks** — MPI communication microscope: latency, bandwidth, collectives, and why RoCE/InfiniBand distinctions matter less than you'd think at the OSU layer.
- **STREAM / BabelStream / stream-gpu-test** — memory bandwidth math, `arraysize` tuning for H200-class HBM, and picking the right variant per vendor comparison.
- **HPL & HPL-GPU** — theoretical peak derivation (SIMD/AVX-512/FMA math), P×Q grid tuning, MPI rank-placement traps, and why HPL-GPU's core-count sensitivity looks nothing like HPL-CPU's.
- **Intel vs. Netlib HPL** — a worked case study in why "binary A beats binary B" claims fall apart once you plot the full problem-size curve instead of one data point.
- **NCCL** — collective primitives, Ring vs. Tree topology selection, the `-g 1` vs `-g 8` oversubscription trap, and reading `busbw` correctly.
- **Parallel Execution & Affinity** — the four-layer stack (SLURM → Launcher → Runtime → Hardware) that determines whether any of the numbers above can be trusted at all.

> **Closing thought:** none of these benchmarks tell you if your cluster is "fast." They tell you, one precisely-scoped layer at a time, exactly *where* to look when it isn't.