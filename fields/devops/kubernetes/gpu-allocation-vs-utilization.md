---
id: gpu-allocation-vs-utilization
sidebar_label: GPU Allocation vs Utilization
order: 5
summary: "The scheduler knows who has booked the GPUs, not whether they’re busy, so use kubectl for the first question and DCGM-style telemetry for the second."
level: intermediate
type: [concept, guide]
domains: [systems-and-hpc, devops, kubernates]
tags: [kubernetes, hpc, dev]
relations:
  prerequisites: [build-a-two-node-k3s-lab, kubernetes-in-five-nouns]
  related: [containers-101]
---

# Booked Is Not Busy: GPU Allocation vs Utilization

Picture a restaurant with four tables. Four parties have reservations. Three of them haven't shown up, and one has ordered a glass of water and is now reading a book. The dashboard at the door says **100% booked**. The kitchen says **it's the quietest night of the year**. Both are telling the truth, and if you only look at one of them you'll make the wrong decision.

That's the difference between GPU **allocation** and GPU **utilization**, and mixing them up is one of the most expensive misunderstandings on a shared cluster.

---

## The one-sentence version

**Allocation is how many GPUs the scheduler has promised to pods; utilization is how hard the hardware is actually working, and Kubernetes natively tracks only the first.**

---

## Allocation: what the scheduler has promised

A pod that wants GPUs asks for them under `limits`, as the [fake GPU page](/fields/devops/kubernetes/fake-gpus-in-kubernetes.md) covered. The scheduler counts those requests against what each node advertises as allocatable. By default, a GPU is handed out whole, so a pod that asks for four GPUs holds four GPUs from the moment it's placed until it finishes, whether or not it ever touches them.

That makes allocation the right answer to the question every user asks first:

> "Why won't my job start?"

Because somebody else is *holding* the GPUs, whether or not they're using them. A pod that requests four GPUs and then sleeps blocks four GPUs from everyone else.

You can see allocation without installing anything:

```bash
kubectl describe node <gpu-node>        # "Allocated resources" table at the bottom
kubectl get pods -A -o custom-columns=NS:.metadata.namespace,POD:.metadata.name,NODE:.spec.nodeName,GPU:.spec.containers[*].resources.limits.nvidia\.com/gpu
```

The second command lists every pod with the GPU count it asked for and the node it landed on. Add those up per node and compare with the node's allocatable figure, and you have the allocation picture.

---

## Utilization: what the hardware is doing

Utilization asks a different question:

> "Is anyone actually using the GPUs they're holding?"

Kubernetes has no idea. Its scheduler deals in whole-number counters; it never looks at what the silicon is doing. The answer comes from the device itself: utilization, memory use, power, temperature and error counters. On a single machine that's `nvidia-smi`. Across a cluster, the usual stack is NVIDIA's **DCGM Exporter** (per-GPU hardware metrics, run as a DaemonSet on the GPU nodes), **kube-state-metrics** (the state of Kubernetes objects), **Prometheus** to store the numbers, and **Grafana** to draw them. NVIDIA publishes guidance on assembling exactly that for GPU usage visibility across clusters.

This is why the two views are complementary instead of redundant:

| | Allocation | Utilization |
| --- | --- | --- |
| Question | "Who is holding the GPUs?" | "Who is actually using them?" |
| Source | The scheduler and the Kubernetes API | The hardware, via DCGM and friends |
| Needs extra tooling? | No, plain `kubectl` | Yes, an exporter plus a metrics stack |
| Good for | Debugging a pending job, capacity planning | Finding waste, justifying hardware, spotting a slow GPU |
| Blind spot | A held GPU may be idle | A GPU can look idle to a metric but still be reserved |

---

## Four situations, and which view answers them

| What's happening | Allocation says | Utilization says | Reading |
| --- | --- | --- | --- |
| Job won't start, cluster looks "full" | 8/8 allocated | Maybe 10% busy | Hoarding. Someone holds GPUs they aren't using |
| Job won't start, but GPUs are free in total | 6/8 allocated | Low | Fragmentation. Free GPUs are spread across nodes, none with enough for a 4-GPU job |
| Everything's allocated and busy | 8/8 allocated | ~95% | Healthy, and a good reason to buy more |
| Training is slow, nothing looks wrong | Allocated as expected | One GPU behind its peers | Utilization (or an active test) is the only view that can see it |

The last row is the story from the [Cluster Readiness Engine page](/fields/devops/kubernetes/nvidia-cluster-readiness-engine.md): a quietly slow GPU doesn't show up in allocation, and passive telemetry may not flag it either. The point of putting all three views side by side is that each one catches what the others miss.

---

## Why GPUs make this worse than CPUs

Two reasons.

**GPUs are coarse.** CPU capacity is divided into small, fungible slices (millicores). A GPU, by default, is allocated as a whole unit. That's why fragmentation is a real thing: two nodes with two free GPUs each can't run a four-GPU job that needs them together on one node. Sharing a GPU is possible, through hardware partitioning (MIG) or time-slicing set up in NVIDIA's software, but it's an explicit configuration with trade-offs, not a free default.

**Distributed jobs need everyone at once.** A 512-GPU training job isn't useful with 400 GPUs. Without gang scheduling, a half-placed job can hold GPUs while it waits for the rest, which is the single biggest waste on shared clusters: lots of allocation, zero useful work. The [Cluster Readiness Engine page](/fields/devops/kubernetes/nvidia-cluster-readiness-engine.md) covers gang scheduling and why it exists.

---

## For Slurm people

You already know both views, under different names. `squeue` and `scontrol show node` tell you what's allocated; `nvidia-smi` and your accounting data tell you what was used. A job that requested 8 GPUs and used 1 is a familiar sight. The Kubernetes version differs in one habit: because pods are meant to be disposable and the scheduler never looks at hardware activity, nothing in the default setup nudges anyone to release an idle allocation. Reclaiming them is a policy choice (quotas, queues, timeouts), not something Kubernetes does for you.

---

## What to do with this

- **Debugging a pending job:** look at allocation first. It's free and answers "who's holding them?" in one command.
- **Judging efficiency:** look at utilization over time, in Grafana, not a one-time snapshot.
- **Never present one as the other.** "The cluster is 100% utilized" and "the cluster is 100% allocated" are different sentences, and a team that conflates them will either buy hardware it doesn't need or leave real waste untouched.
- **Label your dashboards.** Say "allocated" or "utilized" on the chart itself. It prevents the argument before it starts.

---

## The one-paragraph takeaway

Allocation is the reservation book; utilization is the kitchen. Kubernetes keeps the reservation book, so `kubectl` can tell you who is holding which GPUs and why your job is `Pending`. It does not watch the kitchen, so finding idle or underperforming GPUs needs DCGM-style telemetry and a metrics stack. Use allocation to unblock people today, utilization to fix waste over time, and an active test when neither explains why the job is slow.

---

## References

- [Schedule GPUs](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/): GPUs are specified under `limits`, and the request/limit rules
- NVIDIA Technical Blog, [Get Real-Time Visibility into GPU Usage Across Kubernetes Clusters](https://developer.nvidia.com/blog/get-real-time-visibility-into-gpu-usage-across-kubernetes-clusters/): the DCGM Exporter, kube-state-metrics, Prometheus and Grafana stack. I listed this link as a related article from NVIDIA's cluster-readiness post and have not read its full text for this page, so check it for current setup details.
- NVIDIA Technical Blog, [Validate GPU Cluster Readiness Before AI Workloads Land](https://developer.nvidia.com/blog/validate-gpu-cluster-readiness-before-ai-workloads-land/): active vs passive validation and gang scheduling

The restaurant analogy, the four-situations table and the Slurm comparison are the author's own framing, not official terminology. The statements about MIG and time-slicing summarize NVIDIA's documentation, not the Kubernetes pages above.