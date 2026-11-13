---
id: oomkilled-with-memory-to-spare
title: "The Pod Killed With Memory to Spare"
order: 10
sidebar_label: OOMKilled with memory to spare
summary: "Why a training pod is OOMKilled on a node with memory free: three killers, per-container limits, working set, /dev/shm, QoS and a spike no dashboard caught."
level: intermediate
type: [concept, guide]
domains:
  - devops
  - systems-and-hpc
tags:
  - kubernetes
  - gpu
relations:
  prerequisites:
    - broken-pods-rogues-gallery
  related:
    - draining-a-gpu-node
    - linux-memory-free-vs-available
    - slurm-cgroups-in-practice
---

# The Pod Killed With Memory to Spare

> **Page 10 of the [Kubernetes series](/fields/devops/kubernetes/README.md).** A training pod dies with `OOMKilled` while every dashboard says the node has gigabytes free. By the end you'll know which of three different killers struck, why the number you were watching could not show it, and how a harmless-looking `/dev/shm` fix spends your memory budget. Written against Kubernetes 1.31 and later and cgroup v2. The story is invented; **nothing here was run on a live cluster**. Claims trace to the docs in the references, and the places I could not confirm a fact are marked on the page.

## Table of Contents

[The dashboard](#the-dashboard-that-said-everything-was-fine) · [Three killers](#three-killers-three-crime-scenes) · [The unit](#the-storage-unit-has-its-own-size) · [Which number](#which-memory-number) · [The freezer](#the-freezer-you-plugged-in) · [Who goes first](#who-gets-cleared-out-first) · [The photo](#the-photo-every-thirty-seconds) · [Runbook](#debugging-runbook) · [Slurm mirror](#the-slurm-and-linux-mirror) · [Back to Karim](#back-to-karim)

* * *

## The dashboard that said everything was fine

At 02:14 a training pod restarts. Karim, the engineer on call in this story, looks at the dashboards the next morning and finds nothing wrong:

- The node has tens of gigabytes of memory free.
- The pod's memory graph peaks around 11Gi, under its 16Gi limit.
- `kubectl top pod` shows a modest number, because the pod has just restarted.

And yet:

```text
Last State:     Terminated
  Reason:       OOMKilled
  Exit Code:    137
```

Picture the node as a warehouse, half empty. Each container rents a **storage unit** with a fixed size. Karim is staring at the warehouse floor plan. The unit that overflowed is not on it.

Three different things can clear out a unit, and they look alike at 02:14. Which one came for Karim?

* * *

## Three killers, three crime scenes

| | **Container OOM** | **Node OOM** | **Kubelet eviction** |
|---|---|---|---|
| Who | The kernel, at the container's cgroup limit | The kernel, when the whole node runs out before the kubelet reacts | The kubelet, when node `memory.available` crosses a threshold |
| Picture | The lock-cutter clears **one unit** that is over its size | A fire marshal clears whoever scores worst in a full warehouse | The manager empties whole units when the warehouse nears full |
| You see | `OOMKilled`, exit code **137** | Kernel log lines, possibly several pods hit | Pod phase `Failed`, status `Evicted` |
| Next | The kubelet may restart the container per its `restartPolicy` | Same as the first | The pod is not restarted in place: it is `Failed`, and its controller makes a new one |
| Needs a short node? | **No** | Yes | Yes |

The Kubernetes docs back the first column: memory limits are applied by the kubelet and container runtime and "ultimately enforced by the kernel" through cgroups, and `kubectl describe pod` shows `Reason: OOMKilled` with exit code 137 for a container that went over its limit. Exit code 137 is 128 + 9, a SIGKILL: no chance to catch it, no chance to write a checkpoint. ([Draining a GPU Node](/fields/devops/kubernetes/draining-a-gpu-node.md) covers the polite way to die. This is the other way.)

☕ **Try it before you scroll.** The node has 200Gi free and the pod's limit is 16Gi. Can the pod be OOMKilled? *(Hint: whose size matters to a storage unit?)*

Yes, and that is Karim's column. So what exactly is the unit's size, and who reads it?

* * *

## The storage unit has its own size

| Field | Read by | Effect |
|---|---|---|
| `requests.memory` | The scheduler, and the kubelet when it ranks pods | Decides where the pod fits. The kubelet reserves at least the request for the container |
| `limits.memory` | The kernel, through the container's cgroup | The size of the unit |

CPU and memory differ here. A container near its CPU limit is **throttled**. A container over its memory limit may be **killed**, because there is nothing to slow down.

The docs add an honest nuance: memory limits are enforced *reactively*. Terminations "only happen when the kernel detects memory pressure", so a container can run over its limit for a while and not be killed yet. The kernel doc for `memory.max` says the same from the other side: the OOM killer runs "if a cgroup's memory usage reaches this limit and can't be reduced". Two words in that sentence matter: *reaches*, and *can't be reduced*. What can be reduced?

* * *

## Which memory number?

Inside the unit, some things can be thrown out and some cannot. Packing peanuts (inactive file cache) go first. Furniture (anonymous memory) stays.

| Number | Source | What it counts |
|---|---|---|
| `container_memory_usage_bytes` | cAdvisor | "all memory regardless of when it was accessed" |
| `container_memory_working_set_bytes` | cAdvisor | The working set |
| `container_memory_rss` | cAdvisor | RSS |
| `memory.stat`: `anon`, `file`, `shmem` | Kernel cgroup v2 doc | Anonymous mappings; filesystem cache **including tmpfs and shared memory**; the swap-backed part of that cache |

The node-pressure page gives the rule the kubelet itself uses: `memory.available` is node capacity minus the node's working set, read from cgroupfs rather than `free -m`, and the kubelet excludes `inactive_file` because it assumes that memory is reclaimable under pressure.

Read the `memory.stat` row twice. The kernel counts tmpfs and shared memory inside `file`, the same bucket as cache, yet that memory has nowhere to go when pressure comes. That is the `shared` column of `free` one level down (see [free vs available](/fields/system-administration/linux-memory-pressure/linux-memory-free-vs-available.md)). So where does Karim's unit hide such memory?

* * *

## The freezer you plugged in

Karim's job uses data-loader worker processes that hand batches to the main process through shared memory, which in a container lives in `/dev/shm`, a tmpfs. Multiprocessing data loaders typically work this way; I could not retrieve the PyTorch page to cite it, so treat that as general knowledge, not a checked claim.

Two facts then collide:

1. **`/dev/shm` is small by default in a container.** It is commonly reported as 64MB. The Docker CLI reference I checked says only "Size of /dev/shm", with no default, so check `df -h /dev/shm` on your runtime. Workers that outgrow it fail, which sends people looking for a fix.
2. **The usual fix spends your limit.** Mount an `emptyDir` with `medium: Memory` at `/dev/shm`. The docs say the kubelet "tracks `tmpfs` emptyDir volumes as container memory use, rather than as local ephemeral storage". Without a `sizeLimit`, the volume "may consume up to that pod's memory limit".

The docs warn about the part that bites: files on a memory-backed volume are managed by the application, and "Neither Kubernetes nor the OS may automatically delete files from a volume, so memory used by those files can not be reclaimed when the system or the pod are under memory pressure." You plugged a freezer into your storage unit, and it counts as furniture.

A spec that makes the budget explicit (the `emptyDir` fields follow the docs; the numbers are invented):

```yaml
spec:
  containers:
  - name: trainer
    image: registry.example/trainer:1.0
    resources:
      requests: {cpu: "8", memory: 24Gi}
      limits:   {cpu: "8", memory: 24Gi}   # requests == limits, CPU and memory -> Guaranteed
    volumeMounts:
    - {name: dshm, mountPath: /dev/shm}
  volumes:
  - name: dshm
    emptyDir:
      medium: Memory
      sizeLimit: 8Gi          # a ceiling, so the freezer cannot fill the unit
```

Budget the 24Gi like a floor plan: up to 8Gi for the freezer, the main process's anonymous memory, and headroom for kernel memory and active cache. If those leave no room, the pod is a candidate for another 02:14. But what if the warehouse itself fills up? Who goes first?

* * *

## Who gets cleared out first

Two different rules apply, and the docs keep them apart.

**The kubelet's eviction** ranks pods by whether usage exceeds requests, then by Pod Priority, then by how far over they are. The docs state that the kubelet "does not use the pod's QoS class to determine the eviction order", though QoS lets you estimate the likely order. The default hard threshold is `memory.available<100Mi` on Linux. For hard thresholds the kubelet does not respect PodDisruptionBudgets or `terminationGracePeriodSeconds`, so this is not the polite death of the [draining page](/fields/devops/kubernetes/draining-a-gpu-node.md).

**The kernel's OOM killer** acts if the node runs out before the kubelet reclaims. The kubelet sets `oom_score_adj` per container from the QoS class:

| QoS class | Rule | `oom_score_adj` |
|---|---|---|
| **Guaranteed** | Every container has CPU and memory requests equal to limits | -997 |
| **Burstable** | Not Guaranteed, but some request or limit set | min(max(2, 1000 − 1000 × memoryRequestBytes / machineMemoryCapacityBytes), 999) |
| **BestEffort** | No requests or limits | 1000 |

The kernel scores each container by the share of node memory it uses, adds `oom_score_adj`, and kills the highest. In the docs' words, containers in low-QoS pods that use a lot of memory relative to their requests are killed first.

One more detail explains the second killer: the kubelet polls cAdvisor on an interval, and "if memory usage increases within that window rapidly, the kubelet may not observe `MemoryPressure` fast enough, and the OOM killer will still be invoked". The docs suggest `kernelMemcgNotification` for immediate notification, or `kubeReserved` and `systemReserved` as a workaround.

Karim's pod was Guaranteed, so a node-level kill was unlikely. That leaves the lock-cutter. But if the kill is so loud, why did no graph see it?

* * *

## The photo every thirty seconds

The graph is a **sample**. A monitoring system takes a photo of the unit every so often. A burst that fills the unit, triggers the kill and ends the container between two photos is in none of them, and the restarted container looks calm. `kubectl top` only shows the present.

The kernel keeps its own books. Where to look:

| Source | What it tells you |
|---|---|
| `kubectl describe pod`, Last State | That a kill happened, and when |
| `kube_pod_container_status_last_terminated_reason{reason="OOMKilled"}` | A kube-state-metrics gauge you can alert on (documented as EXPERIMENTAL) |
| `memory.events` | `oom_kill`: processes in the cgroup killed by any kind of OOM killer; `max`: times usage was about to exceed the limit; `oom`: times allocation was about to fail |
| `memory.peak` | The highest usage recorded since the cgroup was created or the counter was reset: no photo needed |
| `memory.stat` | The split into `anon`, `file`, `shmem` and the rest |

The cgroup files exist only while the container does, so read them in a container that is still alive and heading for trouble.

* * *

## Debugging runbook

Commands follow the docs above; the cgroup path assumes cgroup v2 as seen from inside the container, so check it on your nodes.

```bash
# 1. Which killer was it?
kubectl describe pod <pod> | grep -B1 -A6 'Last State'
kubectl get pod <pod> -o jsonpath='{.status.phase}{" "}{.status.reason}{"\n"}'   # Failed Evicted -> kubelet

# 2. What did the pod ask for, and what QoS did it get?
kubectl get pod <pod> -o jsonpath='{.spec.containers[*].resources}{"\n"}{.status.qosClass}{"\n"}'

# 3. Live working set, per container
kubectl top pod <pod> --containers

# 4. The cgroup's own books (inside the container, cgroup v2)
kubectl exec <pod> -- sh -c 'cd /sys/fs/cgroup && for f in memory.max memory.current memory.peak memory.events; do echo "== $f"; cat $f; done; grep -E "^(anon|file|shmem) " memory.stat'
kubectl exec <pod> -- df -h /dev/shm

# 5. On the node: the kernel's account (wording varies by kernel version)
dmesg -T | grep -iE 'out of memory|oom'
```

Reading step 4: if `anon` plus `shmem` sits near `memory.max`, the unit is full of things that cannot leave. If `memory.events` shows `oom_kill` above zero, the kernel has already acted, whatever the dashboard says.

Fixes, roughly in order:

1. **Find what actually grew.** Anonymous, shared and kernel memory have different cures.
2. **Bound the freezer.** Set `sizeLimit` on the memory `emptyDir` and cap worker count and prefetch depth.
3. **Size the limit from the working-set peak**, not the average, and leave headroom. The docs' advice, if the app behaves as expected, is a higher limit and possibly a higher request.
4. **Make the run survive a kill.** Checkpoint regularly to a PersistentVolumeClaim: SIGKILL gives no warning to write one at the last moment.

* * *

## The Slurm and Linux mirror

| This page | Elsewhere in the repo |
|---|---|
| The container's memory limit | Slurm's `ConstrainRAMSpace`, with the same kernel OOM killer behind it ([cgroups page](/fields/schedulers/slurm-inside-a-job/slurm-cgroups-in-practice.md)) |
| Kernel kills one container, the kubelet may restart it | With Slurm, `OOMKillStep` makes the whole step die instead (same page) |
| Working set vs usage | "Available" vs "free" at container scale ([free vs available](/fields/system-administration/linux-memory-pressure/linux-memory-free-vs-available.md)) |
| `/dev/shm` and memory `emptyDir` in the limit | The `shared` column in `free` |
| A scrape hiding a spike | `MaxRSS`, polled every 30 s by default |
| Kubelet eviction at `memory.available` | No Slurm equivalent: the kernel decides |

* * *

## Back to Karim

At 02:14 the unit, not the warehouse, was full. The worker processes had been filling a memory-backed `/dev/shm` with prefetched batches, the volume had no `sizeLimit`, and the freezer counted against the 16Gi limit alongside the main process's tensors. The kernel cut the lock. The 11Gi on the graph was a photo taken before the break-in.

**Takeaway:** the node having memory to spare is irrelevant to a container at its own limit; watch the working set against the container's limit, bound anything memory-backed, and trust `memory.events` over a dashboard.

**Challenge:** a pod shows `Evicted` instead of `OOMKilled`. Which killer was it, who decided, and did its `terminationGracePeriodSeconds` apply? If you can answer all three, the [Rogues' Gallery](/fields/devops/kubernetes/broken-pods-rogues-gallery.md) is easier the second time.

* * *

## References

- [Resource management for pods and containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/): limit enforcement, `OOMKilled`, memory-backed `emptyDir`.
- [Node-pressure eviction](https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/): `memory.available`, thresholds, eviction order, `oom_score_adj`, known issues.
- [Pod Quality of Service classes](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/): Guaranteed, Burstable, BestEffort.
- [Assign memory resources to containers](https://kubernetes.io/docs/tasks/configure-pod-container/assign-memory-resource/): exceeding a limit and restart.
- [Control Group v2 (kernel docs)](https://docs.kernel.org/admin-guide/cgroup-v2.html): `memory.max`, `memory.peak`, `memory.events`, `memory.stat`.
- [cAdvisor Prometheus metrics](https://github.com/google/cadvisor/blob/master/docs/storage/prometheus.md) and [kube-state-metrics pod metrics](https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/workload/pod-metrics.md): metric names and descriptions.
- [docker container run](https://docs.docker.com/reference/cli/docker/container/run/): `--shm-size` (no default stated).
