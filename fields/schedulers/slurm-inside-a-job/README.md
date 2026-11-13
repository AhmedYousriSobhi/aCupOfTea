---
summary: A four-part series that follows one Slurm job from the submitted script to the daemon that runs it, the cgroup limits around it and the GPU topology under it.
sidebar_label: Inside a Slurm Job
sidebar_group: Inside a Slurm Job
---

# Inside a Slurm Job

You type `sbatch job.sh` and walk away. This series follows what happens next on the node: what Slurm froze from your script, which small daemon starts your processes, what actually fences them in, and how they land on the hardware.

Read the parts in order. Each one answers a question the one before it leaves open.

---

## Contents

| File | Description |
| --- | --- |
| [1. The Tale of a Job Script](/fields/schedulers/slurm-inside-a-job/slurm-job-script-tale.md) | Why editing a script after `sbatch` changes nothing, where the frozen copy lives, and what stays live |
| [2. slurmstepd](/fields/schedulers/slurm-inside-a-job/slurm-slurmstepd.md) | The small daemon that actually runs your job, and why jobs survive `slurmd` restarts |
| [3. cgroups in Practice](/fields/schedulers/slurm-inside-a-job/slurm-cgroups-in-practice.md) | What `cgroup.conf` really constrains, v1 vs v2, and why `sacct` memory numbers are samples |
| [4. GPU Affinity vs Socket Affinity](/fields/schedulers/slurm-inside-a-job/slurm-gpu-affinity-socket-lie.md) | GPU core affinity vs Slurm socket affinity, and how to fix the topology |

---

## Related pages

- [Schedulers: the traffic controller](/fields/schedulers/slurm-intro.md): read first if Slurm is new to you.
- [Cluster operations](/fields/schedulers/slurm-cluster-operations/README.md): what to do when a job on a node refuses to die or a spool directory fills.
- [Dying politely: preemption and signals](/fields/schedulers/slurm-preemption/README.md): what Slurm sends to the processes this series describes.
- [Slurm for AI clusters](/fields/schedulers/slurm-ai-clusters/README.md): topology-aware placement and distributed training on top of these ideas.
