# Benchmarks - Overview

> HPC benchmarks: what each tool measures, how to run it, and how to read the numbers. Start with the field guide, which ties the others together.

Someone hands you a node and says "how fast is it?". Fast at what? Arithmetic, memory, the network, GPU-to-GPU traffic? Each benchmark answers one of those questions, and none answers all of them.

## Contents

| File | Description |
|------|-------------|
| [benchmarking-guide](/fields/benchmarks/benchmarking-guide.md) | The map: five questions about one node, five tools |
| [hpl](/fields/benchmarks/hpl.md) | HPL and the TOP500, and what a GFLOPS number means |
| [hpl-cpu-comparison](/fields/benchmarks/hpl-cpu-comparison.md) | Intel's HPL binary against Netlib |
| [nccl](/fields/benchmarks/nccl.md) | NCCL collective communication between GPUs |
| [osu](/fields/benchmarks/osu.md) | OSU micro-benchmarks for MPI latency and bandwidth |
| [parallel-execution-affinity-master-guide](/fields/benchmarks/parallel-execution-affinity-master-guide.md) | Ranks, threads, cores and affinity, layer by layer |
| [stream](/fields/benchmarks/stream.md) | STREAM and BabelStream memory bandwidth |

## The route

| Page | The question it answers |
|------|-------------------------|
| [benchmarking-guide](/fields/benchmarks/benchmarking-guide.md) | Which of five tools answers which of five questions about one node? |
| [hpl](/fields/benchmarks/hpl.md) | What does a GFLOPS number mean, and what is the TOP500? |
| [hpl-cpu-comparison](/fields/benchmarks/hpl-cpu-comparison.md) | How does Intel's HPL binary compare with Netlib? |
| [stream](/fields/benchmarks/stream.md) | How much memory bandwidth do I have? |
| [osu](/fields/benchmarks/osu.md) | What are my MPI latency and bandwidth? |
| [nccl](/fields/benchmarks/nccl.md) | How fast do GPUs talk to each other? |
| [parallel-execution-affinity-master-guide](/fields/benchmarks/parallel-execution-affinity-master-guide.md) | How do ranks, threads, cores and affinity fit together? |
