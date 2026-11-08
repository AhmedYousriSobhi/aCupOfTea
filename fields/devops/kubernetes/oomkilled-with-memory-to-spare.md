---
id: oomkilled-with-memory-to-spare
title: "The Pod Killed With Memory to Spare"
order: 10
sidebar_label: OOMKilled with memory to spare
summary: "Why a training pod is OOMKilled on a node with memory free: three killers, per-container limits, working set, /dev/shm, QoS and a spike no dashboard caught."
level: intermediate
type: concept
domains:
  - devops
  - systems-and-hpc
tags:
  - kubernetes
  - gpu
relations:
  related:
    - draining-a-gpu-node
    - linux-memory-free-vs-available
    - slurm-cgroups-in-practice
---

# The Pod Killed With Memory to Spare

> **Part of the [Kubernetes](/fields/devops/kubernetes/README.md) directory.** The story is invented. The explanations come from Kubernetes-focused write-ups on OOMKilled and memory metrics, the cAdvisor definition of working set, Zero to JupyterHub's notes on shared memory, and Kubernetes design documents on QoS, all listed at the end. Nothing here was run on a live cluster for this page. Memory accounting differs between cgroup v1 and v2 and between kernel versions, so treat the file names in the debugging section as a starting point and check them on your own nodes.

## Table of Contents

- [The Pod Killed With Memory to Spare](#the-pod-killed-with-memory-to-spare)
  - [Table of Contents](#table-of-contents)
  - [Prologue: the dashboard that said everything was fine](#prologue-the-dashboard-that-said-everything-was-fine)
  - [Three killers, three crime scenes](#three-killers-three-crime-scenes)
  - [Requests, limits, and the one that kills](#requests-limits-and-the-one-that-kills)
  - [Which memory number?](#which-memory-number)
  - [The shared-memory trap](#the-shared-memory-trap)
  - [Who dies first on a crowded node](#who-dies-first-on-a-crowded-node)
  - [The spike between two scrapes](#the-spike-between-two-scrapes)
  - [Debugging runbook](#debugging-runbook)
  - [The Slurm and Linux mirror](#the-slurm-and-linux-mirror)
  - [Cheat sheet](#cheat-sheet)
  - [References](#references)

* * *

## Prologue: the dashboard that said everything was fine

At 02:14 a training pod restarts. Karim, the engineer on call in this invented story, opens the dashboards the next morning and sees nothing wrong:

- The node has tens of gigabytes of memory free.
- The pod's memory graph peaks at about 11Gi, below its 16Gi limit.
- `kubectl top pod` shows a modest number, because the pod has just restarted.

And yet `kubectl describe pod` says it plainly:

```
Last State:     Terminated
  Reason:       OOMKilled
  Exit Code:    137
```

The pod was killed for lack of memory on a machine with plenty of it. Karim's first thought is that Kubernetes is broken. It is not. Three things combined to produce that morning, and none of them show up on the node's free-memory graph.

* * *

## Three killers, three crime scenes

When memory runs short on a Kubernetes node, three different mechanisms can kill something. They look alike in a hurry and they have different causes.

| | **Container OOM (cgroup limit)** | **Node OOM (kernel, global)** | **Kubelet eviction** |
|---|---|---|---|
| Trigger | The container's cgroup reaches its **memory limit** and the kernel cannot reclaim enough | The whole node exhausts memory before the kubelet reacts | `memory.available` on the node crosses an eviction threshold |
| Who acts | The Linux kernel | The Linux kernel | The kubelet |
| What you see | `Reason: OOMKilled`, exit code **137** | Kernel log lines about killing a process, often several pods affected | Pod status `Evicted`, with a message about the node being low on memory |
| What happens next | The container restarts in place under its `restartPolicy` | Whatever the kernel picked dies | The pod is removed and rescheduled elsewhere |
| Needs the node to be short of memory? | **No** | Yes | Yes |

The first column is Karim's. A container-level OOM fires on the **container's own cgroup limit**, so it can happen on a node with plenty of free RAM. Exit code 137 is 128 + 9: SIGKILL, with no chance to catch it or write a checkpoint. (Page [Draining a GPU Node](/fields/devops/kubernetes/draining-a-gpu-node.md) covers the polite way to die. This is the other way.)

Tell them apart quickly:

```bash
kubectl describe pod <pod> | grep -A4 'Last State'      # OOMKilled / 137 -> container limit
kubectl get pod <pod> -o jsonpath='{.status.reason}{"\n"}{.status.message}{"\n"}'   # Evicted -> kubelet
# on the node:
dmesg -T | grep -iE 'memory cgroup out of memory|out of memory: killed'
```

The first kernel message form names a memory cgroup, which is the container-level kill. The second is the global one.

* * *

## Requests, limits, and the one that kills

Every container can declare two numbers for memory, and they do different jobs:

| Field | Who reads it | Effect |
|---|---|---|
| `requests.memory` | The scheduler, and the kubelet when ranking pods | Decides where the pod fits. Feeds the QoS class and the pod's `oom_score_adj` |
| `limits.memory` | The kernel, through the container's cgroup | A **hard cap**. Hit it and the kernel reclaims what it can, then kills |

CPU and memory differ in a way that matters here. CPU is compressible: a container over its CPU limit is throttled. Memory is not: a container over its memory limit is killed, because there is nothing to slow down.

So "memory to spare" on the node means nothing to a container sitting at its own limit. The question is never how much the node has. It is how much **this cgroup** has used against **this cgroup's** limit.

* * *

## Which memory number?

There are several numbers for "how much memory is this container using", and they disagree on purpose. This is the same family of numbers as the [free vs available page](/fields/system-administration/linux-memory-pressure/linux-memory-free-vs-available.md), one level down, inside a cgroup.

| Metric | What it counts |
|---|---|
| `container_memory_rss` | Anonymous memory the processes hold (heap, stacks) |
| `container_memory_usage_bytes` | Everything charged to the cgroup, **including page cache** |
| `container_memory_working_set_bytes` | **Usage minus inactive file cache.** Anonymous memory, shared memory and the file pages recently used |
| `kubectl top` | The working set, via the metrics pipeline (one source I read says usage, so check on your version) |

cAdvisor defines the working set as usage minus the inactive file pages. On cgroup v1 that is `total_inactive_file` from `memory.stat`, and on cgroup v2 it is `inactive_file`. It is the number to watch, because the inactive file cache is what the kernel gives up first.

What the kernel actually does when a cgroup nears its limit: it **reclaims first**. Inactive page cache goes before anything is killed, so a container full of cache is not in danger by that alone. A kill happens when the memory that cannot be reclaimed fills the limit. That means:

- **Anonymous memory** (heap, tensors, buffers) cannot be dropped without swap.
- **Shared memory and tmpfs** cannot be dropped either. They are counted in cache-like numbers but have nowhere to go. This is exactly the `shared` column in `free`.
- **Dirty page cache** must be written to disk before it can be reclaimed, so a burst of writes can create pressure even though it is "just cache" (my reading of how reclaim works, not a claim from the sources).

And one more number that does not belong to any container: the kubelet's node-level `memory.available` is computed from cgroup accounting, capacity minus the working set, not from what `free` reports.

* * *

## The shared-memory trap

Back to Karim's pod. The training job uses a PyTorch `DataLoader` with eight worker processes. The workers hand batches to the main process through **shared memory**, which lives in `/dev/shm`, a tmpfs.

Two facts collide:

1. **The default `/dev/shm` in a container is 64MB.** That is the Docker default, and Kubernetes pods get the same. DataLoader workers that outgrow it crash with "Unexpected bus error... insufficient shared memory", a message that has launched many forum threads.
2. **The usual fix spends your memory limit.** The standard answer is to mount an `emptyDir` with `medium: Memory` at `/dev/shm`. Zero to JupyterHub's documentation says it plainly: shared memory usage counts toward the pod's memory limit, and when the limit is exceeded the pod is evicted or killed.

So the fix for one failure becomes the cause of the next. The shared memory is real RAM that the cgroup is charged for, and it cannot be reclaimed like page cache. Karim's workers had been filling `/dev/shm` with prefetched batches. Together with the main process's tensors, they crossed 16Gi, in a burst that no dashboard captured (more on that below).

A pod spec that makes the budget explicit:

```yaml
spec:
  containers:
  - name: trainer
    image: registry.example/trainer:1.0
    resources:
      requests: {cpu: "8", memory: 24Gi}
      limits:   {cpu: "8", memory: 24Gi}   # requests == limits for every resource -> Guaranteed QoS
    volumeMounts:
    - {name: dshm, mountPath: /dev/shm}
  volumes:
  - name: dshm
    emptyDir:
      medium: Memory
      sizeLimit: 8Gi          # a ceiling, so shm cannot eat the whole limit
```

An illustrative budget for the 24Gi limit above (invented numbers, to show the shape): up to 8Gi for shared memory, about 10Gi for the main process's anonymous memory, and the rest as headroom for kernel overhead and the active cache. If those do not add up to the limit with room to spare, the pod is a candidate for the same 02:14.

* * *

## Who dies first on a crowded node

Kubernetes derives a **QoS class** for each pod from its requests and limits. You do not set it directly:

| Class | Rule | `oom_score_adj` (kubelet sets it) |
|---|---|---|
| **Guaranteed** | Every container has CPU and memory requests equal to limits | Very low: -997 in recent versions (older design documents say -998) |
| **Burstable** | At least one request or limit, but not Guaranteed | Between 2 and 999, lower the larger the memory request |
| **BestEffort** | No requests or limits at all | 1000 |

The Burstable value follows a formula, `1000 - 1000 × memoryRequest / nodeAllocatableMemory`, clamped to that range. When the **kernel** has to choose a victim during a node-level OOM, a high `oom_score_adj` makes a process more likely to die, so Guaranteed pods are nearly the last victims and BestEffort pods the first. You can check the actual value: `cat /proc/<pid>/oom_score_adj` on the node, or `/proc/1/oom_score_adj` inside the container.

Two cautions:

- **The kubelet's eviction order is not just QoS.** For memory pressure it ranks pods by whether they exceed their requests, then by pod priority, then by how far over they are. A Burstable pod that stays under its request is in a safe spot, and one that blows past it is not, regardless of class.
- **Guaranteed has a cost.** It requires CPU requests equal to limits too, so the pod is throttled at its CPU limit, and if you use the kubelet's static CPU manager policy, integer CPU counts. For long training runs, the trade is usually worth it. For everything else, it is a decision.

* * *

## The spike between two scrapes

Karim's graph peaked at 11Gi and the limit is 16Gi. How can both be true?

Because the graph is a **sample**. Prometheus scrapes cAdvisor every so often (15 to 60 seconds is typical), and a burst that fills memory, triggers the OOM kill and ends the container between two scrapes never appears. The restarted container then shows low numbers, and `kubectl top` only shows the present.

It is the same lesson as `MaxRSS` in [the Slurm cgroups page](/fields/schedulers/slurm-cgroups-in-practice.md): accounting numbers are periodic samples, and the kernel's own counters are the truth. Where to find them:

| Source | What it tells you |
|---|---|
| `kubectl describe pod` → Last State | That an OOM kill happened, and when |
| `kube_pod_container_status_last_terminated_reason{reason="OOMKilled"}` in Prometheus | Counts OOM terminations, so you can alert on them |
| `memory.events` in the container's cgroup | An `oom_kill` counter that records the kills |
| `memory.peak` in the cgroup (cgroup v2, newer kernels) | The highest usage seen, which no scrape needs to catch |
| `memory.stat` | Splits the usage into anonymous, file, shared and kernel parts |

The cgroup files are only reachable while the container exists, so read them from inside a container that is still alive and heading toward trouble.

* * *

## Debugging runbook

```bash
# 1. Which killer was it?
kubectl describe pod <pod> | grep -B1 -A6 'Last State'

# 2. What did the pod ask for, and what QoS did it get?
kubectl get pod <pod> -o jsonpath='{.spec.containers[*].resources}{"\n"}{.status.qosClass}{"\n"}'

# 3. Live numbers (working set, per container)
kubectl top pod <pod> --containers

# 4. Inside the container: the cgroup's own view (cgroup v2 layout)
kubectl exec <pod> -- sh -c 'cd /sys/fs/cgroup && for f in memory.max memory.current memory.peak memory.events; do echo "== $f"; cat $f; done; grep -E "^(anon|file|shmem|inactive_file|active_file) " memory.stat'
kubectl exec <pod> -- df -h /dev/shm

# 5. On the node: the kernel's account of the kill
dmesg -T | grep -iE 'memory cgroup out of memory|out of memory: killed'
```

Reading step 4: if `anon + shmem` sits close to `memory.max`, the container is genuinely full of memory it cannot give back. If `file` is large and `shmem` is small, the cache is probably not the problem. If `memory.events` shows `oom_kill` greater than zero, the kernel has already acted, whatever the dashboard says.

Fix patterns, roughly in order of preference:

1. **Find what actually grew.** Anonymous memory, shared memory and kernel memory each have a different cure.
2. **Bound the shared memory.** Set `sizeLimit` on the `/dev/shm` volume and cap the number of DataLoader workers and their prefetch depth.
3. **Size the limit from the working-set peak**, not the average. One rule of thumb in the sources is 1.5 to 2 times the observed peak. Treat that as a starting point.
4. **Make the run survive a kill.** Checkpoint regularly to a PersistentVolumeClaim, as in the [draining page](/fields/devops/kubernetes/draining-a-gpu-node.md), because SIGKILL gives no warning to write one at the last moment.

* * *

## The Slurm and Linux mirror

| This page | Elsewhere in the repo |
|---|---|
| The container's memory cgroup limit | Slurm's `ConstrainRAMSpace`, with the same kernel OOM killer behind it |
| Container OOM kills one process or container, the pod restarts it | Slurm's cgroup kill leaves the step running unless `OOMKillStep` is set, as described on the [cgroups page](/fields/schedulers/slurm-cgroups-in-practice.md) |
| `container_memory_working_set_bytes` | The "available" idea from the [free vs available story](/fields/system-administration/linux-memory-pressure/linux-memory-free-vs-available.md), at container scale |
| `/dev/shm` and `emptyDir: Memory` counting toward the limit | The `shared` column in `free`: tmpfs counted as cache but not reclaimable |
| A scrape interval hiding a spike | Slurm `MaxRSS` sampled every 30 seconds |
| Kubelet eviction at `memory.available` thresholds | No direct Slurm equivalent. Slurm jobs have no node-pressure eviction, and the kernel decides |

* * *

## Cheat sheet

```
OOMKilled / 137   = the kernel killed the container at ITS cgroup limit; node free RAM is irrelevant
Evicted           = the kubelet removed the pod because the NODE was short (memory.available)
limit             = hard cap (memory is not compressible); request = scheduling + QoS + oom_score_adj
working set       = usage - inactive_file  (what to watch); usage includes reclaimable cache
cannot reclaim    = anon memory, /dev/shm, emptyDir: Memory, (dirty cache must be written first)
/dev/shm          = 64MB default; the fix (emptyDir Memory) spends the pod's memory limit -> add sizeLimit
QoS               = Guaranteed (requests == limits) dies last; BestEffort first; eviction also ranks by overage
truth             = memory.events (oom_kill), memory.peak, memory.stat; dashboards are samples
```

The node had memory to spare. The container did not, and the container is the one the kernel counts.

* * *

## References

- [OOMKilled: Kubernetes out of memory errors explained (cgroup limit, reclaim before kill, working set)](https://jorijn.com/en/knowledge-base/kubernetes/troubleshooting/oomkilled-kubernetes-out-of-memory/)
- [Kubernetes pod eviction: node pressure, disk pressure and Evicted status (memory.available from cgroup accounting)](https://jorijn.com/en/knowledge-base/kubernetes/troubleshooting/kubernetes-pod-eviction-node-pressure/)
- [OOMKilled and exit code 137 (cast.ai)](https://cast.ai/blog/oomkilled-exit-code-137/)
- [Kubernetes OOMKilled: exit code 137 explained (container limit, not node memory)](https://www.guance.com/learn/articles/kubernetes-oomkilled)
- [Kubernetes memory metrics: working set and cache (Baeldung)](https://www.baeldung.com/ops/kubernetes-container-memory-metrics)
- [Memory working set vs memory RSS in Kubernetes (cAdvisor definition)](https://mohamedmsaeed.medium.com/memory-working-set-vs-memory-rss-in-kubernetes-which-one-you-should-monitor-8ef77bf0acee)
- [Demystifying OOM killer in Kubernetes (cache definition on cgroup v1 vs v2)](https://medium.com/cloud-native-daily/title-demystifying-oom-killer-in-kubernetes-tracking-down-memory-issues-b5a4973fbd56)
- [Zero to JupyterHub: customizing user resources (shared memory counts toward the limit)](https://z2jh.jupyter.org/en/1.x/jupyterhub/customizing/user-resources.html)
- [Raising shared memory limit of a Kubernetes container (PyTorch DataLoader bus error)](https://medium.com/dive-into-ml-ai/raising-shared-memory-limit-of-a-kubernetes-container-62aae0468a33)
- [Priorities, preemption and QoS: making sure your critical pods survive saturation (oom_score_adj and eviction ranking)](https://dev.to/florient_4262fab5463a691/priorities-preemption-and-qos-making-sure-your-critical-pods-survive-saturation-18ni)
- [Kubernetes design proposal: Resource Quality of Service (OOM score configuration)](https://github.com/kubernetes/design-proposals-archive/blob/8da1442ea29adccea40693357d04727127e045ed/node/resource-qos.md)