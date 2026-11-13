---
summary: A six-part series on running AI training on Slurm - topology-aware placement, launching distributed PyTorch, containers with Pyxis and Enroot, GPU health checks, metrics, and a lab cheatsheet.
sidebar_label: Slurm for AI Clusters
sidebar_group: Slurm for AI Clusters
---

# Slurm for AI Clusters

A GPU cluster is a Slurm cluster with expensive opinions. A training job wants its nodes close together on the network, every rank started with the right environment, the same container on every node, GPUs that are actually there, and someone watching the numbers. Slurm can do all of that, but very little of it is on by default.

Each page opens with a failure we reproduced in a lab, then fixes it.

---

## Contents

| File | Description |
| --- | --- |
| [1. Keep the Job on One Switch](/fields/schedulers/slurm-ai-clusters/topology-aware-placement.md) | `topology/tree` and `topology/block`, `--switches`, the 25.05 `topology.yaml`, and what each does to a 2-node job |
| [2. Launching Distributed Training](/fields/schedulers/slurm-ai-clusters/launching-distributed-training.md) | The batch script runs on one node; `srun` with rank variables vs `torchrun`, and the double-launch trap |
| [3. Containers with Pyxis and Enroot](/fields/schedulers/slurm-ai-clusters/containers-with-pyxis.md) | `--container-image` on `srun`, read-only images, mounts, named containers, and the node that silently ran outside the container |
| [4. GPU Health Checks](/fields/schedulers/slurm-ai-clusters/gpu-health-checks.md) | Draining a node when a GPU disappears, without overwriting the admin's reason, and the 26.11 per-GPU drain |
| [5. Metrics into VictoriaMetrics](/fields/schedulers/slurm-ai-clusters/metrics-openmetrics.md) | The 25.11+ OpenMetrics endpoints, the idle CPUs nobody could use, units that change in 26.11, and a tested alert |
| [6. Lab Build Cheatsheet](/fields/schedulers/slurm-ai-clusters/lab-build-cheatsheet.md) | Every step used to build the lab for both Slurm series, in order, as copy-paste commands |

---

## How the pages were tested

- **Main lab:** Slurm **23.11.4** from the Ubuntu 24.04 packages, with slurmdbd and MariaDB 10.11. A controller (`head01`), four CPU nodes (`cn001`–`cn004`, 2 CPUs each) and one GPU node (`gpu001`), all systemd containers on one Docker network.
- **Newer Slurm:** **26.05.6** built from source on three more containers (`s26a`–`s26c`), for `topology.yaml` and the OpenMetrics endpoints, which 23.11 doesn't have. Slurm **26.11** was at rc1 when this was written; its features are documented from the 26.11 source tree's man pages and release notes, not tested.
- **No real GPUs.** `gpu001` has four fake device files, enough for Slurm to schedule, count and health-check them, not to run CUDA. Distributed training was tested with PyTorch **2.15.0** on CPUs with the Gloo backend; the launch mechanics are the same for NCCL on GPUs, the performance is not.
- **Containers:** Enroot built from the **v4.2.1** tag and Pyxis **v0.24.0**, from source. The lab could not reach a container registry, so images were squashfs files built locally.
- **Metrics:** VictoriaMetrics **v1.156.0**, from the [VictoriaMetrics series](/fields/devops/victoriametrics/README.md).

## Related pages

- [Why Is My Job Still Pending?](/fields/schedulers/slurm-pending-jobs/README.md): reason codes, priority and limits, on the same lab.
- [GPU affinity and the socket lie](/fields/schedulers/slurm-inside-a-job/slurm-gpu-affinity-socket-lie.md): which CPUs a GPU job gets.
- [Mixed GPUs](/fields/schedulers/slurm-mixed-gpus/README.md): H100s and A100s in one job.
- [Preemption, requeue and signals](/fields/schedulers/slurm-preemption/slurm-preemption-requeue-signals.md): keeping a long training run alive.
