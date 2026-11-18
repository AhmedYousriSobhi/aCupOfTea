
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

<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [Containers on Slurm with Pyxis and Enroot](/fields/schedulers/slurm-ai-clusters/containers-with-pyxis.md) — Running Slurm job steps in containers with Pyxis and Enroot - the node that silently ran outside the container, read-only images, mounts, node-local paths, named containers, and the PyTorch env hook.
- [Keep the Job on One Switch: Topology-Aware Placement in Slurm](/fields/schedulers/slurm-ai-clusters/topology-aware-placement.md) — How Slurm places multi-node jobs with and without a topology plugin - topology/tree, --switches, topology/block that refuses to straddle, the 25.05 topology.yaml, and a fatal block config.
- [Lab Build Cheatsheet: A Slurm AI Cluster in Containers](/fields/schedulers/slurm-ai-clusters/lab-build-cheatsheet.md) — Every step used to build the Slurm lab behind the pending-jobs and AI-cluster series - node image, Slurm 23.11 with accounting, topology, PyTorch, Enroot and Pyxis, health check, Slurm 26.05, metrics.
- [Launching Distributed Training on Slurm: srun, torchrun, and the Rank Contract](/fields/schedulers/slurm-ai-clusters/launching-distributed-training.md) — Why a 2-node training job can run on one node, the environment PyTorch needs from Slurm, launching with srun or torchrun, and the double-launch trap - tested with PyTorch 2.15 on Slurm 23.11.
- [Schedulers: The Traffic Controller Nobody Thanks Until It Breaks](/fields/schedulers/slurm-intro.md) — What a cluster scheduler does, how it differs from the OS scheduler, the scheduler landscape, the concepts they share, and the Slurm architecture at a glance.
- [Slurm Metrics Without an Exporter: OpenMetrics into VictoriaMetrics](/fields/schedulers/slurm-ai-clusters/metrics-openmetrics.md) — Slurm 25.11+ serves OpenMetrics from slurmctld - scraping it into VictoriaMetrics, idle CPUs fixed by DefMemPerCPU, MiB in _bytes metrics until 26.11, open access, and a tested alert.
- [When a GPU Falls Off the Bus: Health Checks That Drain the Node](/fields/schedulers/slurm-ai-clusters/gpu-health-checks.md) — A tested Slurm HealthCheckProgram that drains a node when a GPU disappears, the bug where it overwrote the admin's drain reason, what slurmd does on restart, and the per-GPU drain coming in 26.11.

</div>
