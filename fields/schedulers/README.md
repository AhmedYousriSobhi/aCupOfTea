# Schedulers - Overview

How a cluster scheduler decides who runs where, with Slurm as the working example.

Forty people share a cluster. Everyone wants the GPUs now. Somebody has to decide who goes first, where the job lands and what happens when it misbehaves. That somebody is the scheduler, and these pages show how Slurm does it.

## Contents

| File | Description |
|------|-------------|
| [slurm-intro](/fields/schedulers/slurm-intro.md) | What a scheduler does and why it matters |
| [slurm-accounting-multi-tenancy](/fields/schedulers/slurm-accounting-multi-tenancy.md) | Who stores and who enforces multi-tenant rules: slurmdbd, associations, QOS, fairshare |
| [slurm-backfill-tuning](/fields/schedulers/slurm-backfill-tuning.md) | Why a short bf_window hides long jobs, and how to tune backfill with sdiag |
| [slurm-sacct-job-forensics](/fields/schedulers/slurm-sacct-job-forensics.md) | Reading sacct to find out how a job ended: states, exit codes, requeued runs |
| [slurm-inside-a-job](/fields/schedulers/slurm-inside-a-job/README.md) | Series: one job from script to node - the frozen script, slurmstepd, cgroups and GPU affinity |
| [slurm-preemption](/fields/schedulers/slurm-preemption/README.md) | Series: preemption, requeue, QOS setup, job_submit.lua and every signal Slurm sends |
| [slurm-cluster-operations](/fields/schedulers/slurm-cluster-operations/README.md) | Series: reservations, reboots, upgrades, version changes, SSH access and drain runbooks |
| [slurm-mixed-gpus](/fields/schedulers/slurm-mixed-gpus/README.md) | Series: mixing H100s and A100s in one Slurm job, and when it pays off |
| [slurm-pending-jobs](/fields/schedulers/slurm-pending-jobs/README.md) | Series: why is my job still pending - reason codes, multifactor priority, and QOS limits that wait forever |
| [slurm-ai-clusters](/fields/schedulers/slurm-ai-clusters/README.md) | Series: Slurm for AI clusters - topology, distributed training, containers, GPU health checks, metrics, and a lab cheatsheet |

## The route

| Start here if... | Read |
|------------------|------|
| You are new to schedulers | [slurm-intro](/fields/schedulers/slurm-intro.md), then [Inside a Slurm job](/fields/schedulers/slurm-inside-a-job/README.md) |
| Jobs misbehave or nodes drain | [slurm-kill-task-failed](/fields/schedulers/slurm-cluster-operations/slurm-kill-task-failed.md), [slurm-spool-dir-full](/fields/schedulers/slurm-cluster-operations/slurm-spool-dir-full.md) |
| You run a multi-user cluster | [slurm-accounting-multi-tenancy](/fields/schedulers/slurm-accounting-multi-tenancy.md), [slurm-backfill-tuning](/fields/schedulers/slurm-backfill-tuning.md), [Preemption and signals](/fields/schedulers/slurm-preemption/README.md) |
| Users ask why their job isn't running, or where it went | [slurm-pending-jobs](/fields/schedulers/slurm-pending-jobs/README.md), [slurm-sacct-job-forensics](/fields/schedulers/slurm-sacct-job-forensics.md) |
| You maintain the cluster | [Cluster operations](/fields/schedulers/slurm-cluster-operations/README.md) |
| You run GPU training jobs | [slurm-signals-cheatsheet](/fields/schedulers/slurm-preemption/slurm-signals-cheatsheet.md), [slurm-ai-clusters](/fields/schedulers/slurm-ai-clusters/README.md), [slurm-gpu-affinity-socket-lie](/fields/schedulers/slurm-inside-a-job/slurm-gpu-affinity-socket-lie.md) |
| You want to build a lab to try all this | [lab build cheatsheet](/fields/schedulers/slurm-ai-clusters/lab-build-cheatsheet.md) |
