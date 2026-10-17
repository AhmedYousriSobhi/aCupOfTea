---
id: nvidia-cluster-readiness-engine
title: The Cluster That Passed Every Test Except the One That Mattered
sidebar_label: NVIDIA Cluster Readiness Engine
summary: "Even when traditional monitoring tools show all GPUs and networks operating normally, subtle bottlenecks—like a single slow GPU or a degraded network link—can silently drag down the performance of an"
level: intermediate
type: [concept, note]
domains: [systems-and-hpc, devops, kubernates]
tags: [kubernetes, nvidia, hpc]
relations:
  prerequisites: [kubernetes-in-five-nouns]
  related: [containers-101]
---

# The Cluster That Passed Every Test Except the One That Mattered

Every platform engineer has lived this morning. The dashboards are green, DCGM is smiling, the fabric reports no errors, and every pod is `Running`. You announce the cluster ready, someone launches a 512-GPU training job, and the job proceeds to run like a laptop on 2% battery.

Nothing is "broken." No alert fires. One GPU is a bit slow, one link only degrades when it's actually pushed, one route is quietly longer than intended. Yet a synchronous training job moves at the speed of its slowest rank, so a single shy GPU can hold hundreds of its colleagues hostage.

This page is about the tool NVIDIA built for exactly that morning: **NVIDIA Cluster Readiness Engine (NVCRE)**. It's a good page to read after [Kubernetes in Five Nouns](/fields/devops/kubernetes/kubernetes-in-five-nouns.md), because it uses a Kubernetes pattern you'll meet everywhere: you declare what you want, and a controller does the work.

---

## The one-sentence version

**NVCRE is an open source Kubernetes controller that proves a GPU cluster is ready by running real distributed workloads on it, then tells you which nodes failed and why.**

The thesis is almost insultingly simple: the best way to find out whether a cluster can run a workload is to run the workload. On Slurm that's one `srun` away. On Kubernetes there's no built-in equivalent, because the test needs GPU and RDMA resource requests, NCCL settings matched to your fabric, a big enough shared-memory volume, and every pod starting together. NVCRE packages all that up.

---

## Why "all green" isn't "ready"

Two kinds of tools watch a cluster, and they see different things.

| | Passive (telemetry) | Active (workload-driven) |
| --- | --- | --- |
| Question it answers | "Is anything obviously broken?" | "Will this cluster hold up under real load?" |
| How it works | Watches signals the cluster already emits | Generates real load and measures the result |
| Blind spot | Problems that emit nothing | It uses GPU time, so you can't run it all day |
| Example here | NVSentinel | NVCRE |

A GPU running a few percent slow with no errors and no log lines is invisible to a passive watcher, because there's nothing to watch. It only shows up when something leans on the hardware.

If this sounds familiar, it's the same lesson as the [OSU benchmarks page](/fields/benchmarks/osu.md): run different tests that exercise different layers, and let the layer that fails tell you where to dig.

---

## Readiness is a staircase, not a light switch

A cluster doesn't flip from "not ready" to "ready." The article describes four stages: **bring-up, burn-in, preproduction, production**. Each one sets a higher bar, and a node that passes a smoke test is not automatically fit for a 512-GPU run.

Most teams encode this staircase in runbooks, spreadsheets and shell scripts wrapped around hand-rolled NCCL tests. That's a second system to maintain next to everything else you're already running. NVCRE's pitch is to make the staircase a Kubernetes object instead.

---

## The architecture: three resources, one chain of custody

Everything in NVCRE is a Custom Resource, so you can inspect it with `kubectl` and manage it with GitOps. There's no separate dashboard holding secrets.

| Resource | What it is | Your relationship with it |
| --- | --- | --- |
| **Certification** | Which nodes to test and which categories to run | You write this one |
| **Workflow** | One per category; applies defaults and overrides, sets iterations, creates the job | It does the paperwork |
| **Job** | Runs the workload, watches node health, records measurements and failures | It does the sweating |

Instructions flow down, and results flow back up the same chain. The job records which nodes failed and why, the workflow reports the category result, and the certification groups everything by category. That's how a report can say `gpu-01` hit a hardware fault during the NCCL test while `gpu-02` merely missed its bandwidth target. The blame is attributed by design, not guessed afterwards.

A certification describes intent, not mechanism:

```yaml
apiVersion: nvcre.nvidia.com/v1alpha1
kind: Certification
metadata:
  name: gpu-cluster-cert
spec:
  target:
    nodeSelector:
      nvidia.com/gpu.present: "true"
  categories:
    - domain: communication
      variant: nccl-all-reduce
    - domain: training
      variant: nemotron5-8b
```

Note the `v1alpha1`. It's an early API version, so expect fields to change between releases and check the docs before copying anything into automation.

You never say how to run an all-reduce. NVCRE detects the GPU architecture and cloud platform from the target nodes, then derives GPUs per node, the NCCL environment and platform-specific networking. The built-in catalog covers three domains:

- **Communication:** five NCCL variants (all-reduce, all-gather, all-to-all, loopback, and loopback across NVSwitch)
- **Diagnostics:** the DCGM level-4 diagnostic suite
- **Training:** NeMo pretraining with Nemotron 5 at 8B and 56B parameters

---

## Pass or fail is an expression, not a vibe

NVCRE ships with **no default thresholds**. You write the criteria yourself, in Common Expression Language (CEL), evaluated against measured metrics:

```yaml
categories:
  - domain: communication
    variant: nccl-all-reduce
    options:
      thresholds:
        busBandwidthGBps: "value >= 900"
  - domain: training
    variant: nemotron5-8b
    options:
      thresholds:
        goodputRatio: "value >= 0.9"
        avgTFLOPsPerGPU: "value >= 800"
```

**Do not copy those numbers.** NVIDIA's own article calls them illustrative values for GB200 NVL72-class systems. Your threshold comes from the same place as in the OSU page: a known-good baseline for your hardware, or what your application actually needs.

The design point worth remembering is that "the job finished" and "the job hit its target" are different facts. A training run that completes at 60% of expected goodput technically succeeded and told you the cluster isn't ready. NVCRE records the second case as a `ValidationFailed` condition, separate from whether the run itself succeeded, and treats it as a failure.

---

## Scale decides what you're measuring

The same test at a different scale answers a different question. An NCCL test inside one NVLink domain measures NVLink. The same test across three racks measures the scale-out fabric. So NVCRE makes scale explicit with `testScale`:

| Mode | What it does |
| --- | --- |
| Intra-node | Tests each node on its own |
| Intra-rack | Groups nodes by topology domain (via the `nvidia.com/gpu.clique` label) |
| Full-scale | Puts every node in one big group |
| Diagnose | Adaptive fault isolation, described next |

---

## The detective: adaptive fault isolation

Here is the nightmare it solves. A 64-node all-reduce returns low bandwidth. Every node in the group is equally suspect, and the old answer was days of engineers bisecting racks by hand while the GPUs sat idle.

With `testScale: diagnose`, NVCRE does the bisecting itself. It splits a failing group, reruns the halves, and keeps going until it hits a floor size (`minGroupSize`). Groups that still fail at the floor become suspects. A `maxConcurrent` setting caps how many jobs run at once, so the detective doesn't saturate the very fabric it's measuring.

The output is a short list of suspect nodes with a reason each, instead of a shrug aimed at an entire rack. A failing report looks like this:

```
communication/nccl-all-reduce
Status:       Failed
Scale:        full-scale
Nodes/Job:    8

Failed Nodes:
  gpu-node-07  ThresholdViolation
  gpu-node-12  HardwareFailureDetected

Summary
Categories:   1/2 passed
Failed Nodes: 2
Result:       FAILED
```

---

## `WorkloadRun`: the plumbing, available separately

Underneath certification sits `WorkloadRun`, which solves a more mundane problem. Running any multi-node GPU workload on Kubernetes needs the same pile of setup every time: platform detection, framework wiring, GPU and network requests, and cleanup when a run dies halfway.

You give it an image, a framework and a node count. The framework is exactly one of:

- `torch` for distributed training through `torchrun`
- `mpi` for NCCL tests and other MPI workloads
- `exec` for an arbitrary command

NVCRE then generates the matching Kubeflow `TrainingRuntime`, injects the shared-memory volume, sets the NCCL and platform environment variables, and enables NVLink scale-up networking where the hardware supports it.

### The gang scheduling aside

This is the most transferable idea on the page. Without a gang scheduler, Kubernetes places pods independently. On a busy cluster that can deadlock: some pods land, grab their GPUs, and wait forever at the framework's rendezvous for peers that can't be scheduled. Everyone is holding a seat and nobody can start the meeting.

Setting `spec.gangScheduler` opts the workload's pods into a gang-aware scheduler such as KAI Scheduler, which holds all pods until the whole gang can be placed at once. It's all-or-nothing placement, the Kubernetes answer to a habit Slurm users take for granted. Because `WorkloadRun` is a plain CRD, other tools can call it without adopting the rest of NVCRE.

---

## Three questions, three layers

NVIDIA frames a production cluster as needing three separate answers, one per layer of its DSX OS stack:

| Question | Layer | Style |
| --- | --- | --- |
| Is it configured correctly? | **AI Cluster Runtime (AICR)** | Version-locked, validated recipes for drivers, operators and kernels; detects drift |
| Is it ready to run real work? | **NVCRE** | Active: generates load, finds failures that emit no telemetry |
| Is it healthy right now? | **NVSentinel** | Passive: watches DCGM metrics, Xid errors, logs and cloud maintenance events |

NVSentinel costs no GPU time, so it can run forever in production. NVCRE costs GPU time, so you run it before workloads land. They don't compete. One covers what emits signals, the other covers what stays quiet.

NVCRE also deliberately **does not act on what it finds**. It doesn't cordon, taint or patch node conditions, which avoids conflicting actions and half-cleaned-up state. The NVSentinel NVCRE Certification Monitor can turn a failed certification into a health event, and your NVSentinel policies can then quarantine, drain or trigger remediation. A later passing certification can clear the signal and release the taint. Find and fix stay in separate lanes.

---

## Getting started

Prerequisites on the target cluster:

- Kubernetes 1.29 or later, `kubectl` and Helm 3.x
- NVIDIA GPU Operator
- NVIDIA DRA Driver for GPUs, if you're on GB200 or GB300 NVL72 (those catalog entries create ComputeDomain resources)
- The standalone DCGM service, for the DCGM level-4 category
- A gang-aware scheduler such as KAI Scheduler, optional but recommended on busy shared clusters

Then the whole loop is four commands:

```bash
curl -fsSL https://github.com/NVIDIA/cluster-readiness-engine/releases/latest/download/installer | bash
nvcrectl setup init
nvcrectl certification run --cert-file certification.yaml --wait
nvcrectl certification report gpu-cluster-cert -n <namespace>
```

`nvcrectl setup init` installs the CRDs, the controller, Kubeflow Trainer and the default log profiles. As with any installer you pipe into `bash`, read it first on anything that matters.

---

## What it doesn't tell you (yet)

- **It's alpha-versioned (`v1alpha1`).** Treat field names as subject to change.
- **No default thresholds.** It will not tell you whether 932 GB/s is good for your fabric. You decide that.
- **Not in the lab series yet.** The two-node k3s lab in this series has no real GPUs, so nothing here was run by the author. The page summarizes NVIDIA's documentation and article.

---

## The one-paragraph takeaway

A cluster can pass every health check it owns and still fail the only test that counts, because the failures that hurt (a slightly slow GPU, a link that sulks under load) emit nothing until real work pushes on them. NVCRE's answer is almost rude in its simplicity: run the real workload before production does, measure it against thresholds you choose, and bisect automatically when the numbers are bad. Pair it with a passive watcher like NVSentinel, and readiness stops being an assumption and becomes something you can prove before the first customer job lands.

---

## References

- NVIDIA Technical Blog, [Validate GPU Cluster Readiness Before AI Workloads Land](https://developer.nvidia.com/blog/validate-gpu-cluster-readiness-before-ai-workloads-land/) (Sept 23, 2026; Dhvani Chheda and Kai Wombacher). The architecture, catalog, `testScale` modes, adaptive isolation, `WorkloadRun`, prerequisites and install commands on this page come from this article.
- [NVCRE on GitHub](https://github.com/NVIDIA/cluster-readiness-engine) and its [documentation](https://docs.nvidia.com/cluster-readiness-engine/), where the current API is defined
- [NVSentinel overview](https://docs.nvidia.com/nvsentinel/getting-started/overview/)

The comparison tables and the framing around the OSU page are the author's own.