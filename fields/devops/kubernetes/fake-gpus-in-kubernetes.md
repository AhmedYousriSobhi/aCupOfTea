
<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/devops/">DevOps: Where Code Meets the Machines That Run It</a> / <a href="#/fields/devops/kubernetes/">Kubernetes, for People Who Have Other Things to Do</a></nav>

# Fake GPUs in Kubernetes: Learn GPU Scheduling Without Owning a GPU

<!-- related-block -->
<div class="reading-time">Intermediate · Concept · 6 min read · Updated 17 Nov 2026</div>
<!-- related-block -->
<div class="tag-chips"><a class="chip" href="#/.docs/generated/explore/tags/devops">devops</a> <a class="chip" href="#/.docs/generated/explore/tags/hpc">hpc</a> <a class="chip" href="#/.docs/generated/explore/tags/kubernetes">kubernetes</a> <a class="chip" href="#/.docs/generated/explore/tags/nvidia">nvidia</a></div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [Build a Two-Node Kubernetes Lab on Your Laptop (and Survive the DNS Pothole)](/fields/devops/kubernetes/build-a-two-node-k3s-lab.md), [Kubernetes in Five Nouns, Explained Like You Just Inherited the Cluster](/fields/devops/kubernetes/kubernetes-in-five-nouns.md)  ·  **Read next:** [Isolating GPU Workloads: Taints, Labels and the Device Plugin](/fields/devops/kubernetes/isolating-gpu-workloads.md)

</div>


Real GPUs are expensive, shared, and always booked by someone else. Fake GPUs are free, always available, and will never melt a rack. If what you want to learn is how Kubernetes *schedules* GPU workloads (who gets them, who waits, who sits `Pending` forever), you don't need hardware. You need one command and a slightly dishonest node.

This page builds on the [two-node lab](/fields/devops/kubernetes/build-a-two-node-k3s-lab.md). The trick it teaches is also the cleanest way to understand what a real GPU device plugin actually does.

---

## The one-sentence version

**Kubernetes doesn't know what a GPU is; it only knows named counters on nodes called extended resources, so you can add a counter called `nvidia.com/gpu` to a node by hand and the scheduler will treat it exactly like the real thing.**

That's not a hack around the system. It's the documented mechanism. The official docs say extended resources let cluster administrators advertise node-level resources that Kubernetes would otherwise not know about, and that they're opaque to Kubernetes: it knows only that a node has a certain number of them.

---

## How the real thing works (so the fake makes sense)

On a real cluster, a **device plugin** runs on each GPU node. It discovers the hardware and advertises it, so the cluster exposes a schedulable resource such as `nvidia.com/gpu` or `amd.com/gpu`. Kubernetes has stable support for managing AMD and NVIDIA GPUs this way.

Your pod then asks for GPUs in its container spec. The rules from the official GPU scheduling docs:

- GPUs are only supposed to be specified in the **`limits`** section.
- You can give a GPU limit with no request, because Kubernetes uses the limit as the request.
- If you give both, they must be equal.
- You cannot give a GPU request without a limit.

By default, a GPU is handed out whole. Two pods don't quietly split one device. (Sharing exists, through NVIDIA's [MIG](/references/glossary?id=mig "Multi-Instance GPU") partitioning and time-slicing, but you configure it deliberately. It is not the default.)

So there are two halves: someone has to **advertise** the counter, and someone has to **request** it. The device plugin does the first on real hardware. In the lab, you do it with a patch.

---

## Step 1: advertise four GPUs that don't exist

```bash
kubectl patch node k8s-worker --subresource=status --type=json -p '[
  {"op":"add","path":"/status/capacity/nvidia.com~1gpu","value":"4"},
  {"op":"add","path":"/status/allocatable/nvidia.com~1gpu","value":"4"}]'
```

Unpacking the parts:

| Piece | Why it's there |
| --- | --- |
| `--subresource=status` | Extended resources live in the node's **status**, so the patch has to target the status subresource, the same `/status` endpoint the official docs use |
| `/status/capacity/...` | What the node says it physically has |
| `/status/allocatable/...` | What's left over for pods to use. The scheduler places pods against this figure, so the lab sets it too |
| `nvidia.com~1gpu` | The resource name `nvidia.com/gpu`, with the slash escaped as `~1`, which is how JSON Patch spells a slash inside a path segment. Yes, really |
| `"4"` | Extended resources must be whole numbers. No half GPUs |

Resource names should carry a domain prefix you control or that matches the real convention. The `kubernetes.io` prefix is reserved, which is why the fake uses the same `nvidia.com/gpu` name the real device plugin would.

Check that it took:

```bash
kubectl describe node k8s-worker | grep -A8 -E 'Capacity|Allocatable'
kubectl get node k8s-worker -o jsonpath='{.status.allocatable}'
```

You should see `nvidia.com/gpu: 4` alongside [CPU](/references/glossary?id=cpu "Central Processing Unit") and memory.

---

## Step 2: request them

Here's a pod that wants two GPUs. The container is a do-nothing `pause` image, because the GPU is imaginary and we only care about the accounting:

```bash
kubectl create ns team-a
kubectl -n team-a run gpu-train --image=rancher/mirrored-pause:3.6 \
  --overrides='{"spec":{"containers":[{"name":"c","image":"rancher/mirrored-pause:3.6","resources":{"limits":{"nvidia.com/gpu":"2"}}}]}}'
```

It schedules and runs, and the node now has two GPUs spoken for. Now ask for more than exist:

```bash
kubectl create ns team-b
kubectl -n team-b run gpu-waiting --image=rancher/mirrored-pause:3.6 \
  --overrides='{"spec":{"containers":[{"name":"c","image":"rancher/mirrored-pause:3.6","resources":{"limits":{"nvidia.com/gpu":"8"}}}]}}'
```

That pod can never fit: the only node with GPUs has four. It will sit in `Pending`, and `kubectl describe pod gpu-waiting -n team-b` will show a scheduling event explaining that no node has enough of the resource. That event is the single most useful thing to learn to read on a GPU cluster, and the [rogues' gallery page](/fields/devops/kubernetes/broken-pods-rogues-gallery.md) goes deeper.

---

## What's real, and what isn't

| Real | Fake |
| --- | --- |
| The scheduler's arithmetic: capacity, allocatable, who requested what | There is no device. `nvidia-smi` won't exist |
| `Pending` pods that can't fit, and the events that say why | No driver, no CUDA, no device plugin |
| Quotas, namespaces and monitoring tools that read these fields | No isolation between "GPU users", because there's nothing to isolate |

That second column is the point of the exercise and its limit. The fake teaches **allocation** (what the cluster has promised to whom), which is half the story. The other half is **utilization** (what the hardware is actually doing), and for that you need real GPUs and real telemetry. The [next-but-one page](/fields/devops/kubernetes/gpu-allocation-vs-utilization.md) is about exactly that gap.

---

## Cleaning up

The patch is removable the same way the official docs show: a JSON Patch `remove` on the same path.

```bash
kubectl patch node k8s-worker --subresource=status --type=json -p '[
  {"op":"remove","path":"/status/capacity/nvidia.com~1gpu"}]'
```

Delete the fake pods first if you want a tidy cluster. And if the node object is ever deleted and re-created (for example, you destroy and re-join the worker), the counters go with it, so patch again.

---

## A warning about mixing fake and real

Don't run this trick on a cluster that also has a real device plugin advertising the same resource name. The two would disagree about reality, and the scheduler would believe whichever spoke last. The lab is isolated on purpose. Tools that expect real GPUs, such as NVIDIA's [Cluster Readiness Engine](/fields/devops/kubernetes/nvidia-cluster-readiness-engine.md), launch real [NCCL](/references/glossary?id=nccl "NVIDIA Collective Communications Library") workloads and need actual hardware; a fake counter will pass the scheduler and then fail when a container tries to use a device that isn't there.

---

## The one-paragraph takeaway

A GPU, to the Kubernetes scheduler, is a whole-number counter on a node that pods ask for under `limits`. A device plugin maintains that counter on real hardware, and a single `kubectl patch` can maintain it in a lab, which makes the scheduler's behaviour completely observable for free: pods that fit, pods that wait, and the events that explain which is which. Just remember what the fake can't do. It can promise a GPU, but it can't run anything on one.

---

## References

- [Advertise Extended Resources for a Node](https://kubernetes.io/docs/tasks/administer-cluster/extended-resource-node/): patching `/status`, JSON Patch `~1` escaping, integer amounts, opaque resources, removal
- [Schedule GPUs](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/): device plugins, GPUs specified under `limits`, request and limit rules, node labels for mixed GPU types

The lab fixtures (`gpu-train`, `gpu-waiting`) come from the author's own lab. The remark about sharing through MIG and time-slicing summarizes NVIDIA's documentation and isn't covered by the Kubernetes pages above.

<!-- related-block -->
<div class="see-also">

**See also**

- [Containers 101](/fields/libraries-frameworks-containers/101-containers.md) — Containers from the ground up: what happens at boot, kernel and user space, virtual machines, then namespaces, cgroups and Linux containers.

</div>
<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [Booked Is Not Busy: GPU Allocation vs Utilization](/fields/devops/kubernetes/gpu-allocation-vs-utilization.md) — The scheduler knows who has booked the GPUs, not whether they’re busy, so use kubectl for the first question and DCGM-style telemetry for the second.
- [Broken Pods: A Rogues' Gallery (and the One Command That Catches Them All)](/fields/devops/kubernetes/broken-pods-rogues-gallery.md) — How to recognise CrashLoop, OOMKilled, ImagePull and Pending pods by reading status, events and previous logs.
- [Core AI Infrastructure Concepts: A Map](/business/hpc-industry/ai-infrastructure-core-concepts.md) — Six concepts every AI-infrastructure engineer gets asked about, each fact-checked with a 30-second answer and a pointer to where to go deeper.
- [Isolating GPU Workloads: Taints, Labels and the Device Plugin](/fields/devops/kubernetes/isolating-gpu-workloads.md) — How the NVIDIA device plugin exposes GPUs to pods, why taints alone don't dedicate GPU nodes, and why distributed training needs all-or-nothing scheduling.
- [Kubernetes, for People Who Have Other Things to Do](/fields/devops/kubernetes/README.md)

</div>
