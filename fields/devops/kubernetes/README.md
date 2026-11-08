---
summary: A fourteen-page Kubernetes series for HPC people, from core concepts and a two-node lab to GPU scheduling and a job's journey, with a list of planned pages.
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
| 9 | [Draining a GPU Node With a Three-Day Run on It](/fields/devops/kubernetes/draining-a-gpu-node.md) | Cordon vs drain, the SIGTERM-to-SIGKILL clock, PodDisruptionBudgets and a runbook that keeps the checkpoint | 10 min |
| 10 | [The Pod Killed With Memory to Spare](/fields/devops/kubernetes/oomkilled-with-memory-to-spare.md) | OOMKilled on a node with free RAM: cgroup limits, working set, /dev/shm, QoS and spikes dashboards miss | 11 min |
| 11 | [k3s vs kubeadm: Furnished Flat or Empty Unit?](/fields/devops/kubernetes/k3s-vs-kubeadm.md) | What each installs, how upgrades and HA differ, and which to pick for a lab or a GPU cluster | 9 min |
| 12 | [Your kubeconfig Is a House Key](/fields/devops/kubernetes/your-kubeconfig-is-a-house-key.md) | What a kubeconfig holds, how kubectl picks one, why certificates cannot be revoked, and short-lived keys | 7 min |
| 13 | [RBAC: The Error Message Writes the Rule for You](/fields/devops/kubernetes/rbac-and-the-limited-viewer.md) | Reading a Forbidden error as a rule, a read-only user in two commands, RBAC guardrails, and revoking at the binding | 8 min |
| 14 | [Polite API Server Monitoring: Leave Your Number](/fields/devops/kubernetes/polite-api-server-monitoring.md) | Polling vs watching measured on a lab, what a list costs, the shared priority lane, and five habits | 10 min |
 
## Brewing next
 
These are planned and not written yet:
 
- Kubernetes at HPC scale
- A kubectl troubleshooting cheat sheet (this one will live in `tips/`)