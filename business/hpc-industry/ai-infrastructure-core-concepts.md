---
id: ai-infrastructure-core-concepts
title: "Core AI Infrastructure Concepts: A Map"
sidebar_label: AI infrastructure core concepts
summary: Six concepts every AI-infrastructure engineer gets asked about, each fact-checked with a 30-second answer and a pointer to where to go deeper.
level: intermediate
type: concept
domains: [systems-and-hpc]
tags: [hpc, gpu, slurm, kubernetes, nvidia]
---

# Core AI Infrastructure Concepts: A Map

> **A hub page for interview prep and onboarding.** Six concepts come up again and again when people talk about running AI clusters. Each one is usually summarized in a sentence that's *mostly* right. This page fact-checks each summary, gives you a 30-second answer that's fully right, and points to the pages in this repo that go deep. By the end you'll know which half-truths to avoid and where to learn the whole truth.

## Table of Contents
- [Core AI Infrastructure Concepts: A Map](#core-ai-infrastructure-concepts-a-map)
  - [Table of Contents](#table-of-contents)
  - [How to use this page](#how-to-use-this-page)
  - [1. Feeding 10,000 GPUs: storage and fabric](#1-feeding-10000-gpus-storage-and-fabric)
  - [2. Slurm orchestration and multi-tenancy](#2-slurm-orchestration-and-multi-tenancy)
  - [3. Kubernetes workload isolation](#3-kubernetes-workload-isolation)
  - [4. Heterogeneous jobs and the synchronous bottleneck](#4-heterogeneous-jobs-and-the-synchronous-bottleneck)
  - [5. The roofline and the sparsity asterisk](#5-the-roofline-and-the-sparsity-asterisk)
  - [6. The job execution journey](#6-the-job-execution-journey)
  - [The thread that ties them together](#the-thread-that-ties-them-together)
    - [References](#references)

---

## How to use this page

Each section has the same four parts: the common summary, a verdict, a 30-second answer, and where to go next. Read the verdicts first: they're the difference between an answer that sounds senior and one that is.

| # | Concept | Common summary is... |
|---|---------|---------------------|
| 1 | Storage and fabric | Right, but misses the two things that actually starve GPUs |
| 2 | Slurm multi-tenancy | Half right: confuses storing limits with enforcing them |
| 3 | Kubernetes isolation | Right, but misses the toleration trap and gang scheduling |
| 4 | Heterogeneous jobs | Right |
| 5 | Sparsity on the roofline | Right |
| 6 | The job execution journey | Good skeleton, three errors: Kueue's role, step order, where CUDA comes from |

---

## 1. Feeding 10,000 GPUs: storage and fabric

**The common summary:** *Scaling to 10,000+ GPUs requires data ingestion on high-performance distributed filesystems such as Lustre or GPFS, paired with InfiniBand or RDMA networks, to prevent GPU starvation.*

**Verdict: right, but incomplete.** It's about bandwidth, while the usual killers are **metadata** (millions of small files) and **checkpoint storms**. And "InfiniBand or RDMA" mixes levels: InfiniBand is one way to do RDMA; RoCE is another.

**30-second answer:**

> "I'd use a parallel filesystem that keeps metadata out of the data path, like Lustre or Storage Scale, and feed it large sharded files, because small files are limited by metadata operations, not bandwidth. I'd size storage for checkpoint bursts, which Meta's Llama 3 paper names as a major challenge. The fabric must be RDMA, InfiniBand or RoCE, ideally with separate compute and storage networks, and GPUDirect so data skips the CPU memory hop."

**Go deeper:** [Storage and Fabric for AI Clusters](/fields/system-administration/ai-storage-and-fabric/README.md)

---

## 2. Slurm orchestration and multi-tenancy

**The common summary:** *`slurmctld` on the head node manages resources, `slurmd` agents run tasks on workers. Multi-tenant accounting, resource limits and history are managed entirely by `slurmdbd`, while `sacctmgr` is merely a client of that daemon.*

**Verdict: half right.** The daemon roles and `sacctmgr`'s role are correct. "Managed entirely by `slurmdbd`" is wrong where it matters: `slurmdbd` **stores** limits; `slurmctld` **enforces** them, and only when `AccountingStorageEnforce` is set. Set limits without it and they do nothing.

**30-second answer:**

> "`slurmctld` schedules and enforces, `slurmd` launches and contains jobs, and `slurmdbd` is the accounting database front end. Tenancy is built on associations, cluster plus account plus user plus optional partition, with Grp limits for team quotas, Max limits for job sizes, QOS for policy classes and fairshare for ordering. `sacctmgr` writes those rules through `slurmdbd`, but they're only enforced once `AccountingStorageEnforce` includes `limits`."

**Go deeper:** [Slurm multi-tenancy: who stores the rules, who enforces them](/fields/schedulers/slurm-accounting-multi-tenancy.md) and the [schedulers intro](/fields/schedulers/intro.md)

---

## 3. Kubernetes workload isolation

**The common summary:** *Kubernetes uses a service-oriented scheduling paradigm. Device plugins such as NVIDIA's expose hardware to containers. Admins isolate ML workloads from microservices with node labels, taints and tolerations.*

**Verdict: right, with two gaps.** A toleration **allows** a pod onto tainted nodes but doesn't **send** it there; dedicated nodes need a taint *and* a label with node affinity. And distributed training needs all-or-nothing (gang) scheduling, which Kubernetes historically left to add-ons like Kueue and Volcano and has only recently started building in natively.

**30-second answer:**

> "The NVIDIA device plugin advertises GPUs as the `nvidia.com/gpu` resource. I taint GPU nodes so services stay off, use `ExtendedResourceToleration` so GPU-requesting pods get the toleration automatically, and add labels with affinity for anything that must run only there, because tolerations permit but don't attract. For multi-pod training I need gang scheduling: Kueue or Volcano, or the newer native Workload and PodGroup APIs once they're stable for my version."

**Go deeper:** [Isolating GPU workloads](/fields/devops/kubernetes/isolating-gpu-workloads.md), [Fake GPUs in Kubernetes](/fields/devops/kubernetes/fake-gpus-in-kubernetes.md) and [GPU allocation vs utilization](/fields/devops/kubernetes/gpu-allocation-vs-utilization.md)

---

## 4. Heterogeneous jobs and the synchronous bottleneck

**The common summary:** *Slurm supports mixed hardware via hetjobs, but combining H100s and A100s in one distributed training run creates a synchronous bottleneck: with NCCL AllReduce, the faster hardware idles waiting for the slower.*

**Verdict: right.** Two refinements make it senior: on datasheet ratios the H100s idle about two-thirds of each compute-bound step, so 8 H100s alone can beat 8 H100s plus 8 A100s; and heterogeneous jobs shine when different hardware runs **different roles**, like a trainer on H100s with rollout workers on A100s. Watch for accidental mixing through a bare `|` in `--constraint`.

**30-second answer:**

> "Yes, Slurm can allocate mixed GPUs, with heterogeneous jobs or constraint counts. For one synchronous run it's a bad deal: every all-reduce waits for the slowest GPU, and you lose H100-only features like FP8. I mix hardware across roles, not within a role, and I give flexible users the matching-OR constraint, `[h100|a100]`, so they get either type but never both."

**Go deeper:** [Mixing GPU Types in Slurm](/fields/schedulers/slurm-mixed-gpus/README.md)

---

## 5. The roofline and the sparsity asterisk

**The common summary:** *When capacity planning with the roofline, use dense TFLOPS, not the marketed 2:4 sparsity TFLOPS. The sparsity number doubles the calculated ridge point, so teams misdiagnose compute-bound workloads as memory-bandwidth-bound.*

**Verdict: right.** On an H100, dense BF16 gives a ridge of about 295 FLOP/byte; the sparse headline gives about 590. A kernel at 400 FLOP/byte is compute-bound but looks bandwidth-bound with the wrong number. The sparse figure is only valid for models actually pruned to 2:4, and even then it helps prefill (compute-bound) far more than decode (bandwidth-bound).

**30-second answer:**

> "The ridge point is peak FLOPS over memory bandwidth, and it must use the dense number unless the model is 2:4 sparse. The datasheet's headline is with sparsity, which doubles the ridge and misfiles every workload between the two values as bandwidth-bound, so the team optimizes the wrong axis. If we do prune to 2:4, doubled math helps prefill, and decode only gains from the roughly 44% fewer weight bytes."

**Go deeper:** [Compute-bound vs memory-bandwidth-bound](/fields/generative-ai/llm-inference-performance/compute-bound-vs-memory-bound.md#the-asterisk-that-doubles-your-mistake), [2:4 sparsity](/fields/generative-ai/llm-inference-performance/structured-sparsity.md) and [sparsity vs quantization](/fields/generative-ai/llm-inference-performance/sparsity-vs-quantization.md)

---

## 6. The job execution journey

**The common summary:** *`kubectl apply` hits the API server, which authenticates, validates and stores the job in etcd; an operator like the PyTorch Operator creates launcher and worker pods plus headless Services; Kueue gang-schedules the pods and binds them to nodes; the kubelet asks the NVIDIA device plugin for free GPUs, which mounts drivers and CUDA libraries; the runtime pulls images and boots containers, and Multus adds RDMA interfaces for NCCL.*

**Verdict: a good skeleton with three real errors.** Kueue is an **admission** controller: it holds whole jobs suspended until quota fits and leaves pod placement to **kube-scheduler**, so with Kueue the operator creates no pods until admission. The **CUDA toolkit** comes from the container image; the NVIDIA Container Toolkit injects only the host's driver libraries. And the pod's network, Multus interfaces included, is set up **before** the containers start. Smaller fixes: the API server also authorizes and runs admission control, Kubeflow Trainer v2's `TrainJob` replaces `PyTorchJob`, and "launcher" pods belong to MPIJob.

**30-second answer:**

> "The API server authenticates, authorizes and runs admission, where Kueue's webhook suspends the job, then validates and stores it. Kueue admits the whole job when its quota fits, optionally checking topology. The operator, Kubeflow Trainer via JobSet, creates the pods and a headless Service. kube-scheduler filters on GPUs, taints and affinity and binds each pod. On the node, the kubelet's device manager assigns GPUs, the device plugin's Allocate says how to expose them, and the NVIDIA Container Toolkit injects driver libraries. The sandbox gets its overlay and Multus RDMA interfaces, then containers start and NCCL runs over RDMA."

**Go deeper:** [The job execution journey](/fields/devops/kubernetes/job-execution-journey.md)

---

## The thread that ties them together

Read the five verdicts again and one idea keeps showing up: **find the real bottleneck before you add capacity.**

| Concept | The tempting fix | The real bottleneck |
|---------|------------------|---------------------|
| Storage | More bandwidth | Metadata operations; checkpoint bursts |
| Slurm tenancy | Set more limits | The controller isn't enforcing them |
| Kubernetes | Add tolerations | Tolerations don't place pods; training needs gang scheduling |
| Hetjobs | Add the idle A100s | The slowest GPU sets the pace |
| Roofline | Read the headline TFLOPS | The dense number decides which wall you're hitting |
| Job journey | Restart the stuck component | Find which of the six stops the job is waiting at |

That habit, measuring which resource is actually short, is what the [GPU failure prediction](/fields/system-administration/gpu-failure-prediction/README.md) and [LLM inference performance](/fields/generative-ai/llm-inference-performance/README.md) series practice on every page.

**Takeaway:** each of these five summaries is mostly right, and the missing part is always the same: name the real bottleneck, then pick the fix that moves it.

Related: [HPC interview questions](/business/hpc-industry/hpc-interview-questions.md).

### References
Each linked page carries its own primary sources. The key ones:
- [Slurm: Resource Limits](https://slurm.schedmd.com/resource_limits.html) and [Heterogeneous Job Support](https://slurm.schedmd.com/heterogeneous_jobs.html)
- [Kubernetes: Taints and Tolerations](https://v1-34.docs.kubernetes.io/docs/concepts/configuration/taint-and-toleration) and [v1.36 workload-aware scheduling](https://kubernetes.io/blog/2026/05/13/kubernetes-v1-36-advancing-workload-aware-scheduling/)
- [Lustre wiki: Lustre Architecture for Admins](https://wiki.lustre.org/Lustre_Architecture_for_Admins)
- [NVIDIA GPUDirect Storage Overview Guide](https://docs.nvidia.com/gpudirect-storage/overview-guide/index.html)
- [Grattafiori et al., "The Llama 3 Herd of Models", arXiv:2407.21783](https://arxiv.org/abs/2407.21783)
- [Mishra et al., "Accelerating Sparse Deep Neural Networks", arXiv:2104.08378](https://arxiv.org/abs/2104.08378)
- [NVIDIA H100 Tensor Core GPU datasheet](https://www.nvidia.com/en-us/data-center/h100/)