---
sidebar_label: Kubernetes
---

# Kubernetes, for People Who Have Other Things to Do

A short series on Kubernetes, written by someone who runs GPU clusters for a living and needed a landlord-with-opinions explanation before the YAML made sense. Start at page 1 and work down. Each page stands on its own.

---

## Pages

| Page | What it covers | Time |
| --- | --- | --- |
| [Kubernetes in Five Nouns](/fields/devops/kubernetes/kubernetes-in-five-nouns.md) | Node, Pod, Namespace, Event and API server, with an HPC translation table | 5 min |

## Brewing next

These are planned and not written yet:

- Build a two-node k3s lab with Vagrant (and the DNS pothole that ate an afternoon)
- k3s vs kubeadm: which one, and when
- Fake GPUs in Kubernetes: extended resources without the hardware
- The rogues' gallery: CrashLoop, OOMKilled, ImagePull and Unschedulable pods
- RBAC and the limited viewer
- Your kubeconfig is a house key
- Polite API server monitoring
- GPU allocation vs utilization
- Kubernetes at HPC scale
- A kubectl troubleshooting cheat sheet (this one will live in `tips/`)