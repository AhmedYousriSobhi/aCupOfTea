
<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/references/">References</a></nav>

# Glossary

<!-- related-block -->
<div class="reading-time">Reference · 3 min read · Updated 23 Nov 2026</div>


The acronyms that come up again and again in these pages, in one sentence each. On the site, the first use of each term on a page links here, and hovering it shows its meaning. Where a page explains the term properly, the entry points to it.

## CPU

**Central Processing Unit.** The general-purpose processor that runs the operating system and hands work to accelerators such as a GPU.

## CUDA

**Compute Unified Device Architecture.** NVIDIA's platform and programming model for running general-purpose code on its GPUs. Read more: [CUDA 101](/fields/libraries-frameworks-containers/101-cuda.md).

## DCGM

**Data Center GPU Manager.** NVIDIA's tooling to monitor and diagnose GPUs in a data centre. Read more: [Custom checks for NHC](/fields/system-administration/node-health-check/checks-and-remediation/custom-checks.md).

## ECC

**Error-Correcting Code** memory. Memory that detects and corrects flipped bits; GPUs report corrected and uncorrected error counts, which health checks watch. Read more: [GPU failure prediction runbook](/fields/system-administration/gpu-failure-prediction/runbook.md).

## GPU

**Graphics Processing Unit.** A processor built to run thousands of small calculations at once, which is why it trains neural networks and runs HPC codes.

## GRES

**Generic RESource.** Slurm's way of describing things other than CPUs and memory, such as GPUs, that a job can ask for. Read more: [Four ways to mix GPUs](/fields/schedulers/slurm-mixed-gpus/four-ways-to-mix-gpus.md).

## HBM

**High Bandwidth Memory.** Stacked memory placed right next to a GPU, giving far more bandwidth than ordinary server memory. Read more: [Compute-bound vs memory-bound](/fields/generative-ai/llm-inference-performance/compute-bound-vs-memory-bound.md).

## HPC

**High-Performance Computing.** Using many machines together, usually through a scheduler such as Slurm, to solve problems one computer cannot. Read more: [HPC 101](/business/hpc-industry/101-hpc.md).

## MIG

**Multi-Instance GPU.** An NVIDIA feature that splits one GPU into several isolated slices. Read more: [The socket lie in GPU affinity](/fields/schedulers/slurm-inside-a-job/slurm-gpu-affinity-socket-lie.md).

## MPI

**Message Passing Interface.** The standard way for processes (ranks), on one machine or many, to exchange messages; Open MPI is a common implementation. Read more: [OpenMP and Open MPI](/fields/system-administration/openmp-and-open-mpi/README.md).

## NCCL

**NVIDIA Collective Communications Library**, said "nickel". The library GPUs use for collective operations such as all-reduce. Read more: [NCCL](/fields/benchmarks/nccl.md).

## NHC

**Node Health Check.** A script that runs on a cluster node, tests it, and tells the scheduler to take the node out of service when a check fails. Read more: [Node Health Check](/fields/system-administration/node-health-check/README.md).

## NUMA

**Non-Uniform Memory Access.** A design where memory is attached to particular CPU sockets, so reaching near memory is faster than reaching far memory. Read more: [Parallel execution and affinity](/fields/benchmarks/parallel-execution-affinity-master-guide.md).

## OOM

**Out Of Memory.** The moment a machine or container has no memory left; Linux then kills a process, the OOM killer. Read more: [The OOM killer](/fields/system-administration/linux-memory-pressure/the-oom-killer.md).

## QoS

**Quality of Service.** In Slurm, a named set of limits and priorities attached to jobs ([Limits that wait forever](/fields/schedulers/slurm-pending-jobs/limits-that-wait-forever.md)). In Kubernetes, a pod's class (Guaranteed, Burstable or BestEffort), which decides who is killed first when memory runs out ([OOMKilled with memory to spare](/fields/devops/kubernetes/oomkilled-with-memory-to-spare.md)).

## RDMA

**Remote Direct Memory Access.** Lets one machine's network card read or write another machine's memory directly, without involving its CPU. Read more: [RDMA, InfiniBand and GPUDirect](/fields/system-administration/ai-storage-and-fabric/rdma-infiniband-gpudirect.md).

## SSH

**Secure Shell.** The encrypted protocol for logging in to a remote machine and running commands on it.

## VM

**Virtual Machine.** A computer emulated in software, running its own operating system on top of a host.
