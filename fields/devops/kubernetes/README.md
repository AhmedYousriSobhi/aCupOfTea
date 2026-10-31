---
sidebar_label: Kubernetes
sidebar_group: Kubernetes
---

# Kubernetes, for People Who Have Other Things to Do
 
A short series on Kubernetes, written by someone who runs GPU clusters for a living and needed a landlord-with-opinions explanation before the YAML made sense. Start at page 1 and work down. Each page stands on its own, and later pages link back to earlier ones when they lean on them.
 
---
 
## Pages
 
| # | Page | What it covers | Time |
| --- | --- | --- | --- |
| 1 | [Kubernetes in Five Nouns](/fields/devops/kubernetes/kubernetes-in-five-nouns.md) | Node, Pod, Namespace, Event and API server, with an HPC translation table | 5 min |
| 2 | [Build a Two-Node k3s Lab](/fields/devops/kubernetes/build-a-two-node-k3s-lab.md) | Vagrant, libvirt and k3s on a laptop, plus the DNS and network potholes | 10 min |
| 3 | [Fake GPUs in Kubernetes](/fields/devops/kubernetes/fake-gpus-in-kubernetes.md) | Extended resources: learn GPU scheduling without owning a GPU | 5 min |
| 4 | [Broken Pods, the Rogues' Gallery](/fields/devops/kubernetes/broken-pods-rogues-gallery.md) | CrashLoop, OOMKilled, ImagePull and Pending pods, and how to read each one | 7 min |
| 5 | [GPU Allocation vs Utilization](/fields/devops/kubernetes/gpu-allocation-vs-utilization.md) | Booked is not busy: what the scheduler knows and what it doesn't | 6 min |
| 6 | [NVIDIA Cluster Readiness Engine](/fields/devops/kubernetes/nvidia-cluster-readiness-engine.md) | Proving a GPU cluster is ready by running real workloads on it | 8 min |
| 7 | [Isolating GPU Workloads](/fields/devops/kubernetes/isolating-gpu-workloads.md) | Device plugins, taints vs labels, the toleration trap, and gang scheduling | 9 min |
| 8 | [The Job Execution Journey](/fields/devops/kubernetes/job-execution-journey.md) | From `kubectl apply` to the first NCCL all-reduce: six stops, in the right order | 12 min |
 
## Brewing next
 
These are planned and not written yet:
 
- k3s vs kubeadm: which one, and when
- RBAC and the limited viewer
- Your kubeconfig is a house key
- Polite API server monitoring
- Kubernetes at HPC scale
- A kubectl troubleshooting cheat sheet (this one will live in `tips/`)