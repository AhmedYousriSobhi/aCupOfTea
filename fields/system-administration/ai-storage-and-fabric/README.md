
# Storage and Fabric for AI Clusters - Overview

> A two-part series on the least glamorous way to waste a GPU: making it wait for data. By the end you'll know how parallel filesystems and RDMA fabrics keep 10,000 GPUs fed, and how to tell when they don't.

## Table of Contents
- [Storage and Fabric for AI Clusters - Overview](#storage-and-fabric-for-ai-clusters---overview)
  - [Table of Contents](#table-of-contents)
  - [The claim, and what's missing from it](#the-claim-and-whats-missing-from-it)
  - [The route](#the-route)
  - [Contents](#contents)
  - [Related reading in this repo](#related-reading-in-this-repo)

---

## The claim, and what's missing from it

A common summary of AI infrastructure says: *scaling to 10,000+ GPUs needs data ingestion built on high-performance distributed filesystems such as Lustre or GPFS, paired with InfiniBand or RDMA networks, to prevent GPU starvation.*

True, and incomplete in three useful ways:

- **Bandwidth isn't the usual bottleneck; metadata is.** Millions of small files starve GPUs on storage with petabytes free. ([Part 1](/fields/system-administration/ai-storage-and-fabric/parallel-filesystems-for-ai.md))
- **Checkpoints, not datasets, set the peak.** Meta's Llama 3 paper names bursty checkpoint writes as a major storage challenge. ([Part 1](/fields/system-administration/ai-storage-and-fabric/parallel-filesystems-for-ai.md#the-checkpoint-storm))
- **"InfiniBand or RDMA" is not either/or.** InfiniBand is one way to run RDMA; RoCE is another, and Llama 3 405B trained on RoCE. And the last hop into GPU memory needs GPUDirect. ([Part 2](/fields/system-administration/ai-storage-and-fabric/rdma-infiniband-gpudirect.md))

---

## The route

| # | Page | The question it answers |
|---|------|-------------------------|
| 1 | [Parallel filesystems](/fields/system-administration/ai-storage-and-fabric/parallel-filesystems-for-ai.md) | Why can GPUs starve on storage with petabytes free and bandwidth to spare? |
| 2 | [RDMA, InfiniBand and GPUDirect](/fields/system-administration/ai-storage-and-fabric/rdma-infiniband-gpudirect.md) | Why does a 400 Gb/s network still leave GPUs waiting, and how do you take the CPU out of the way? |

## Contents

| File | Description |
|------|-------------|
| [parallel-filesystems-for-ai](/fields/system-administration/ai-storage-and-fabric/parallel-filesystems-for-ai.md) | Lustre architecture, striping, the small-file trap, checkpoint storms |
| [rdma-infiniband-gpudirect](/fields/system-administration/ai-storage-and-fabric/rdma-infiniband-gpudirect.md) | Two fabrics, RDMA, InfiniBand vs RoCE, GPUDirect RDMA and Storage |

## Related reading in this repo

- [NCCL](/fields/benchmarks/nccl.md) and [OSU](/fields/benchmarks/osu.md) benchmarks: measuring the compute fabric.
- [Node Health Check series](/fields/system-administration/node-health-check/README.md): catching a node whose storage mount or link has gone bad.
- [Predicting GPU Node Failures](/fields/system-administration/gpu-failure-prediction/README.md): why checkpoint frequency matters at scale.