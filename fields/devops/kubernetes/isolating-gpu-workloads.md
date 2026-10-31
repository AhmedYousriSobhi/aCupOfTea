---
id: isolating-gpu-workloads
sidebar_label: Isolating GPU Workloads
order: 7
summary: How the NVIDIA device plugin exposes GPUs to pods, why taints alone don't dedicate GPU nodes, and why distributed training needs all-or-nothing scheduling.
level: intermediate
type: concept
domains: [systems-and-hpc, devops]
tags: [kubernetes, nvidia, gpu, hpc]
relations:
  prerequisites: [fake-gpus-in-kubernetes, gpu-allocation-vs-utilization]
  related: [slurm-accounting-multi-tenancy]
---

# Isolating GPU Workloads: Taints, Labels and the Device Plugin

> **Page 7 of the [Kubernetes series](/fields/devops/kubernetes/README.md).** [Page 3](/fields/devops/kubernetes/fake-gpus-in-kubernetes.md) faked GPUs with a hand-patched counter. This page is the real thing: how a device plugin advertises GPUs, how to keep web services off your GPU nodes and GPU jobs on them, and why a 64-GPU training job needs a kind of scheduling Kubernetes was never built for. By the end you'll be able to design GPU isolation on a shared cluster and explain where Kubernetes still differs from Slurm.

## Table of Contents
- [Isolating GPU Workloads: Taints, Labels and the Device Plugin](#isolating-gpu-workloads-taints-labels-and-the-device-plugin)
  - [Table of Contents](#table-of-contents)
  - [The logging agent that ate a GPU node](#the-logging-agent-that-ate-a-gpu-node)
  - [Concept 1: the device plugin is a translator](#concept-1-the-device-plugin-is-a-translator)
  - [Concept 2: labels attract, taints repel](#concept-2-labels-attract-taints-repel)
  - [The trap: a toleration is a permission, not a destination](#the-trap-a-toleration-is-a-permission-not-a-destination)
  - [Try it before you scroll](#try-it-before-you-scroll)
  - [Concept 3: training jobs need all-or-nothing](#concept-3-training-jobs-need-all-or-nothing)
  - [Slurm and Kubernetes, side by side](#slurm-and-kubernetes-side-by-side)
    - [References](#references)

---

## The logging agent that ate a GPU node

A company runs one Kubernetes cluster for everything: the website, internal tools, and a pool of 8-GPU H100 nodes for model training.

Monday morning, a 32-GPU training job sits `Pending`. Four GPU nodes exist. Every one has 8 free GPUs. So why won't it schedule?

Because the scheduler doesn't only count GPUs. It also counts CPU and memory. Over the weekend, a dozen web pods, a log shipper and a batch report job drifted onto the GPU nodes, because those nodes had the most free CPU and RAM in the cluster. Each GPU node now has its GPUs free and its memory full. The training pods don't fit anywhere.

Nobody did anything wrong. Kubernetes did exactly what it was built to do: pack services onto whatever capacity is free. It just had no idea those nodes were special.

This page is about telling it.

---

## Concept 1: the device plugin is a translator

Kubernetes doesn't know what a GPU is. As page 3 showed, it only knows **extended resources**: named counters on nodes, like `nvidia.com/gpu: 8`.

A **device plugin** is the translator between real hardware and those counters. NVIDIA's runs as a DaemonSet, one pod on every GPU node, and does three things:

1. **Discovers** the GPUs on its node.
2. **Advertises** them to the kubelet, which publishes `nvidia.com/gpu` in the node's capacity.
3. **Hands them out**: when a pod that asked for GPUs lands on the node, the plugin tells the kubelet which specific devices to expose to that container.

Pods ask for GPUs in `limits`, as page 3 covered:

```yaml
resources:
  limits:
    nvidia.com/gpu: 8
```

In production, the plugin rarely comes alone. NVIDIA's **GPU Operator** installs the whole stack as Kubernetes components: the driver, the container toolkit, the device plugin, **GPU Feature Discovery** (which labels nodes with facts like the GPU model), and the DCGM exporter for metrics. One install, every GPU node configured the same way.

What a GPU request does **not** do: it says nothing about which *kind* of node or who else may land there. A pod asking for 8 GPUs can only go where 8 are free. But a pod asking for **zero** GPUs can go anywhere, GPU nodes included. That's the logging agent's loophole.

---

## Concept 2: labels attract, taints repel

Kubernetes has two opposite tools for placement, and the official docs put the contrast neatly: **node affinity attracts pods to nodes; taints let a node repel pods.**

| Tool | Lives on | Effect | Analogy |
|------|----------|--------|---------|
| **Label** + `nodeSelector` / node affinity | Label on node, selector on pod | "This pod should go **only** to nodes like these" | A pod's destination address |
| **Taint** | Node | "Keep **every** pod away unless it tolerates me" | A "staff only" sign on a door |
| **Toleration** | Pod | "I'm allowed past that sign" | A staff badge |

A taint has a key, a value and an **effect**:

| Effect | Meaning |
|--------|---------|
| `NoSchedule` | New pods without a matching toleration won't be placed here |
| `PreferNoSchedule` | The scheduler tries to avoid placing them here |
| `NoExecute` | Also evicts already-running pods that don't tolerate it |

The docs list GPU nodes as a textbook case: in a cluster where a small subset of nodes have special hardware, taint those nodes so pods that don't need the hardware stay off, leaving room for pods that do.

```bash
kubectl taint nodes gpu-h100-01 nvidia.com/gpu=present:NoSchedule
```

Now the web pods and the log shipper bounce off the GPU nodes. Monday's problem is solved.

There's even a built-in shortcut. The docs recommend representing special hardware as an extended resource, tainting those nodes with the extended resource's name, and enabling the **`ExtendedResourceToleration`** admission controller. Then any pod that requests `nvidia.com/gpu` automatically gets the matching toleration. GPU users don't have to remember anything.

> [!TIP]
> Some system DaemonSets, like the device plugin itself, the GPU Operator's components and node monitoring agents, must run on GPU nodes. Give those pods the toleration deliberately; the taint will block them too.

---

## The trap: a toleration is a permission, not a destination

Here's where most GPU isolation designs go wrong. The docs say it in one line: tolerations **allow, but do not require**, pods to schedule onto nodes with matching taints.

A toleration is a staff badge. It lets you into the staff area. It doesn't make you go there.

So picture a data-preprocessing pod: CPU-heavy, no GPUs, but it belongs to the ML team, so someone gave it the GPU toleration "so it can run next to the training job." The scheduler is now free to put it on a GPU node *or* any ordinary node. Worse, if it lands on a GPU node, it's eating CPU and memory that training pods need, recreating Monday's problem from the inside.

The docs' recipe for **dedicated nodes** uses both tools together:

1. **Taint** the GPU nodes, so outsiders stay off.
2. **Label** the same nodes (for example `node-pool=gpu-training`).
3. Give the pods that belong there **a toleration *and* a node affinity or `nodeSelector`** for that label, so they go there and only there.

| You want | Taint on node | Toleration on pod | Affinity on pod |
|----------|:---:|:---:|:---:|
| Keep outsiders off GPU nodes | Yes | - | - |
| Let GPU pods onto GPU nodes | Yes | Yes | - |
| Keep a team's pods **only** on their nodes | Yes | Yes | **Yes** |

The rule of thumb: **taints guard the door; labels give directions.** You almost always need both.

---

## Try it before you scroll

☕ Three pods on a cluster where GPU nodes are tainted `nvidia.com/gpu=present:NoSchedule` and labeled `node-pool=gpu`. Where can each one land?

1. A web server with no tolerations and no selectors.
2. A training pod requesting 8 GPUs, with the toleration (added automatically by `ExtendedResourceToleration`).
3. A CPU-only preprocessing pod with the toleration but no node selector.

Answers: (1) only non-GPU nodes: the taint repels it; (2) only GPU nodes, but because it asked for GPUs, not because of the toleration; (3) **anywhere**, GPU nodes included, which is probably not what anyone intended. Add `nodeSelector: {node-pool: gpu}` if it should be there, or remove the toleration if it shouldn't.

---

## Concept 3: training jobs need all-or-nothing

Isolation gets the right pods onto the right nodes. Distributed training needs one more thing: **all of its pods at once.**

A 32-GPU job is four pods of 8 GPUs, and it can't take a single training step until all four are running. The traditional kube-scheduler placed pods **one at a time**. Two jobs that each need four pods, on a cluster with room for four, could each grab two pods and wait forever for the rest, both holding GPUs and neither running. That's a scheduling deadlock, and it's why the batch world invented **gang scheduling**: place all of a group's pods, or none.

For years, the answer on Kubernetes was an add-on: **Kueue** (job queueing and admission) or **Volcano** (a batch scheduler), among others. That's changing. Kubernetes 1.35 added a Workload API with an initial alpha implementation of gang scheduling; the Kubernetes project's 1.36 post describes a redesigned Workload and PodGroup API (`scheduling.k8s.io/v1alpha2`) and a dedicated PodGroup scheduling cycle in kube-scheduler. Release coverage of 1.37 reports these APIs moving to beta.

> [!IMPORTANT]
> These APIs changed incompatibly between alpha versions: per the 1.36 announcement, `v1alpha2` completely replaced `v1alpha1`. Check your cluster's version and feature gates before relying on native gang scheduling, and keep Kueue or Volcano until it's stable for you.

This is the clearest place where Kubernetes's roots show. It grew up placing long-running services that each work alone. Batch schedulers like Slurm grew up placing jobs that need many nodes at the same moment.

---

## Slurm and Kubernetes, side by side

| Concern | Slurm | Kubernetes |
|---------|-------|------------|
| Design center | Batch jobs that start, run, finish | Long-running services, kept at a desired state |
| GPU discovery | GRES, configured in `gres.conf` or autodetected via NVML | Device plugin advertising `nvidia.com/gpu` |
| Keeping workloads apart | Partitions, features, accounts and QOS | Taints, tolerations, labels, affinity, namespaces |
| All-or-nothing multi-node start | Built in: a job gets all its nodes or waits | Add-ons (Kueue, Volcano); native gang scheduling arriving in recent releases |
| Tenant quotas and fairness | Associations, Grp/Max limits, fairshare ([see the Slurm page](/fields/schedulers/slurm-accounting-multi-tenancy.md)) | ResourceQuota per namespace; Kueue adds queues, quotas and borrowing |
| Mixed GPU types | Typed GRES, constraints, heterogeneous jobs ([see the series](/fields/schedulers/slurm-mixed-gpus/README.md)) | Node labels such as GPU Feature Discovery's GPU model label, plus affinity |

Neither is "better." A common pattern at large AI organizations is both: Slurm for big training runs, Kubernetes for inference services and tooling, sometimes on the same hardware pool.

**Takeaway:** the device plugin turns GPUs into counters, taints keep outsiders off GPU nodes, labels and affinity send the right pods there, and distributed training still needs all-or-nothing scheduling that Kubernetes is only now building in.

Isolation decides where pods *may* go. To follow one training job through every component, from `kubectl apply` to its first all-reduce, continue to [page 8, the job execution journey](/fields/devops/kubernetes/job-execution-journey.md).

### References
- [Kubernetes: Taints and Tolerations (dedicated nodes, special hardware, `ExtendedResourceToleration`)](https://v1-34.docs.kubernetes.io/docs/concepts/configuration/taint-and-toleration)
- [Kubernetes: Schedule GPUs](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)
- [Kubernetes: Device Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)
- [Kubernetes blog: "Kubernetes v1.36: Advancing Workload-Aware Scheduling"](https://kubernetes.io/blog/2026/05/13/kubernetes-v1-36-advancing-workload-aware-scheduling/)
- [NVIDIA GPU Operator documentation](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/index.html)
- [NVIDIA k8s-device-plugin (includes GPU Feature Discovery)](https://github.com/NVIDIA/k8s-device-plugin)