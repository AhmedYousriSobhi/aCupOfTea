

# Kubernetes in Five Nouns, Explained Like You Just Inherited the Cluster

<!-- related-block -->
<div class="reading-time">8 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [Containers 101](/fields/libraries-frameworks-containers/101-containers.md)  ·  **Read next:** [Build a Two-Node Kubernetes Lab on Your Laptop (and Survive the DNS Pothole)](/fields/devops/kubernetes/build-a-two-node-k3s-lab.md), [Fake GPUs in Kubernetes: Learn GPU Scheduling Without Owning a GPU](/fields/devops/kubernetes/fake-gpus-in-kubernetes.md), [Broken Pods: A Rogues' Gallery (and the One Command That Catches Them All)](/fields/devops/kubernetes/broken-pods-rogues-gallery.md), [Booked Is Not Busy: GPU Allocation vs Utilization](/fields/devops/kubernetes/gpu-allocation-vs-utilization.md), [The Cluster That Passed Every Test Except the One That Mattered](/fields/devops/kubernetes/nvidia-cluster-readiness-engine.md)

</div>


Every Kubernetes story starts the same way. Someone says "just check the pods in the right namespace," and you nod confidently, like a person who knows what a pod is and which namespace is the right one. This page exists so that the nodding becomes honest.

You need exactly five nouns. Learn them and most `kubectl` output stops looking like a ransom note.

---

## The one-sentence version

**Kubernetes is a system where you declare what you want, and a crowd of small control loops keeps nagging the machines until reality matches.**

You don't say "start this container on that server." You say "I want two copies of this web server running," and Kubernetes figures out where, starts them, and replaces them when they die. Think of it as a landlord with opinions: you hand over the lease, and from then on it's the landlord's problem to keep the lights on in every flat.

The official docs say the same thing less colourfully. Controllers create Pods from a template and manage them on your behalf, which is where the auto-healing comes from.

---

## The five nouns at a glance

| Noun | What it really is | Where you'll see it |
| --- | --- | --- |
| **Node** | A machine (VM or bare metal) that runs your containers | `kubectl get nodes` |
| **Pod** | The smallest thing Kubernetes schedules: one or more containers that live and die together | `kubectl get pods` |
| **Namespace** | A folder for resources, so teams don't trip over each other's names | `kubectl get ns` |
| **Event** | A sticky note the cluster leaves when something happens | `kubectl get events` |
| **API server** | The front desk. Every request goes through it | `kubectl` itself |

Now the long version of each, with the parts the cheat sheets skip.

---

## 1. Node: the machine that does the actual work

A node is a worker machine. It has CPU, memory and, if you're lucky, GPUs. Each node runs a **kubelet**, an agent that talks to the control plane and keeps the assigned containers running.

Two details that save you an afternoon:

- **Nodes are not inside any namespace.** They belong to the whole cluster. If you run `kubectl get nodes -n team-a` and wonder why the flag did nothing, this is why. You can confirm which resource types are namespaced with `kubectl api-resources --namespaced=false`.
- **The kubelet only manages containers that Kubernetes created.** If you start a container by hand with another tool on a node, the kubelet will ignore it. It's a landlord, not a bouncer.

```bash
kubectl get nodes -o wide
kubectl describe node <node-name>      # read Conditions and Events at the bottom
```

---

## 2. Pod: the smallest unit, and not what you'd guess

A Pod is the smallest deployable unit you can create and manage in Kubernetes. Most of the time it wraps a single container, so "pod" and "container" get used as if they were the same word. They aren't. A Pod can hold several tightly coupled containers that are scheduled together, and the cluster manages the Pod, not the individual container.

The part beginners miss: **you will rarely create Pods directly.** The docs say so outright. You create a workload resource (a Deployment, a Job and so on), and its controller creates the Pods for you and replaces them when they die. Pods are disposable by design. If one disappears at 2 AM, that isn't an incident, that's the system doing its job.

```bash
kubectl get pods -A                    # every pod, every namespace
kubectl describe pod <pod> -n <ns>     # the Events at the bottom explain most mysteries
kubectl logs <pod> -n <ns> --previous  # why did the last attempt die?
```

---

## 3. Namespace: a folder, not a fortress

A namespace is a mechanism for isolating groups of resources within a single cluster. Names only have to be unique inside a namespace, so `team-a/web` and `team-b/web` can coexist happily.

What the documentation is careful to say, and what blog posts often aren't:

- Namespaces **cannot be nested**, and each resource lives in exactly one.
- They are a scope for names and a unit for **access rules and quotas**. On their own they are a soft boundary, not a security wall. Real separation comes from RBAC, ResourceQuota and network policy layered on top.
- A fresh cluster starts with a few namespaces, including `default` and `kube-system`. For production, the docs suggest not using `default`.
- The prefix `kube-` is reserved for Kubernetes system namespaces. Don't name yours `kube-anything`.

```bash
kubectl get ns
kubectl get pods -n kube-system        # the cluster's own machinery
```

---

## 4. Event: the sticky notes (with a short memory)

When something happens, such as an image failing to pull, a pod failing to schedule or a container getting killed for using too much memory, the cluster leaves an **Event**. Events come in two types, `Normal` and `Warning`, and the warnings are where you start looking when something is wrong.

The catch is that events are short-lived. The API server keeps them for **one hour by default** (the `--event-ttl` flag on `kube-apiserver`, which an administrator can change). Come back after lunch and the explanation may be gone.

```bash
kubectl get events -A --field-selector type=Warning
kubectl get events -n <ns> --sort-by=.lastTimestamp
```

Practical rule: if something broke, read the events **first**, before you restart anything. A restart can erase the clue.

---

## 5. API server: the front desk

Everything in a cluster goes through the **kube-apiserver**. It exposes the Kubernetes API and acts as the front end of the control plane. Every `kubectl` command is, underneath, an HTTP request to it. The scheduler, the controllers and the kubelets all talk to the cluster through the same front desk.

You can watch it happen. Raise kubectl's verbosity and it prints the requests:

```bash
kubectl get pods -n kube-system -v=6
# I... GET https://<server>:6443/api/v1/namespaces/kube-system/pods?limit=500 200 OK
```

The API server is designed to scale horizontally: you can run several instances and balance traffic between them. That detail matters later, when you point monitoring tools at a big cluster and find out the front desk has a queue.

---

## Two more words you'll meet within the hour

- **kubeconfig** is a YAML file that says which API server to talk to and who you are. Treat it like a house key. A kubeconfig can even tell `kubectl` to run a helper program to fetch credentials, so only use files from sources you trust.
- **RBAC** is the bouncer. It decides whether you may list nodes, or only list pods in `team-a`. "Forbidden" in `kubectl` output usually means RBAC said no, not that the cluster is broken. Check with `kubectl auth can-i list nodes`.

---

## The HPC translation table

If you come from Slurm, here is the rough mapping. It is a thinking aid, not a one-to-one match:

| Kubernetes | Closest Slurm-world idea | Where the analogy breaks |
| --- | --- | --- |
| Node | Compute node | Nodes can be added and drained constantly, and Kubernetes expects them to fail |
| kubelet | `slurmd` | The kubelet also manages container lifecycle, not just job launch |
| kube-scheduler | The scheduling half of `slurmctld` | Default Kubernetes scheduling places each Pod individually, with no fair-share or backfill |
| API server | The RPC front end of `slurmctld` | It is a REST API that every component and every tool uses |
| Pod | A job's tasks, roughly | A Pod is not a batch job. Workload resources like Jobs sit above it |
| Namespace | An account or project | A namespace has no fair-share on its own. Quotas are separate objects |

That scheduling row is why HPC sites add queueing systems on top of Kubernetes. The later pages on scale cover that.

---

## Try it in two minutes

Any cluster works, including a throwaway one:

```bash
kubectl get nodes -o wide          # who is in the cluster?
kubectl get ns                     # what folders exist?
kubectl get pods -A                # what is running, everywhere?
kubectl get events -A --field-selector type=Warning
kubectl get pods -n kube-system -v=6   # watch the front desk work
```

If those five commands make sense to you, you can already read most of the output people paste into incident channels.

---

## The one-paragraph takeaway

Kubernetes is a landlord: you describe the flat you want, and a set of control loops keeps it that way. **Nodes** are the buildings, **Pods** are the disposable tenants, **Namespaces** are the floors with their own rules and quotas, **Events** are the notes pinned to the door (taken down after about an hour), and the **API server** is the front desk everyone must go through, including the landlord. Know those five and you can follow almost any cluster conversation without nodding politely.

---

## References

Checked against the official documentation:

- [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/): control plane, kube-apiserver as the front end, kubelet scope, scale-out of the API server
- [Pods](https://kubernetes.io/docs/concepts/workloads/pods/): smallest deployable unit, rarely created directly, workload controllers
- [Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/): scope for names, no nesting, reserved `kube-` prefix, namespaced vs cluster-scoped resources
- [kube-apiserver reference](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-apiserver/): `--event-ttl`, default `1h0m0s`
- [Organizing cluster access using kubeconfig files](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/): kubeconfig structure and the trusted-source warning

The Slurm comparison table is the author's own analogy, not an official mapping.