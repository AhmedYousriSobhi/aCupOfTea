# Schedulers - Overview

How a cluster scheduler decides who runs where, with Slurm as the working example.

Forty people share a cluster. Everyone wants the GPUs now. Somebody has to decide who goes first, where the job lands and what happens when it misbehaves. That somebody is the scheduler, and these pages show how Slurm does it.

## Contents

| File | Description |
|------|-------------|
| [slurm-intro](/fields/schedulers/slurm-intro.md) | What a scheduler does and why it matters |
| [slurm-job-script-tale](/fields/schedulers/slurm-inside-a-job/slurm-job-script-tale.md) | The story of job.sh and the snapshot Slurm takes of it |
| [slurm-slurmstepd](/fields/schedulers/slurm-inside-a-job/slurm-slurmstepd.md) | The small daemon that actually runs your job, and why jobs survive slurmd restarts |
| [slurm-cgroups-in-practice](/fields/schedulers/slurm-inside-a-job/slurm-cgroups-in-practice.md) | What cgroup.conf really constrains, v1 vs v2, and why sacct memory numbers are samples |
| [slurm-gpu-affinity-socket-lie](/fields/schedulers/slurm-inside-a-job/slurm-gpu-affinity-socket-lie.md) | GPU core affinity vs Slurm socket affinity, and how to fix the topology |
| [slurm-accounting-multi-tenancy](/fields/schedulers/slurm-accounting-multi-tenancy.md) | Who stores and who enforces multi-tenant rules: slurmdbd, associations, QOS, fairshare |
| [slurm-backfill-tuning](/fields/schedulers/slurm-backfill-tuning.md) | Why a short bf_window hides long jobs, and how to tune backfill with sdiag |
| [slurm-preemption-requeue-signals](/fields/schedulers/slurm-preemption/slurm-preemption-requeue-signals.md) | Preemption modes, GraceTime, signals your training job ignores, and a requeue-safe wrapper |
| [slurm-qos-preemption-setup](/fields/schedulers/slurm-preemption/slurm-qos-preemption-setup.md) | Setting up QOS preemption with requeue, step by step, with a drill that proves it works |
| [slurm-job-submit-lua](/fields/schedulers/slurm-preemption/slurm-job-submit-lua.md) | The job_submit.lua plugin: routing jobs to the right QOS, requiring time limits, and how it fails |
| [slurm-signals-cheatsheet](/fields/schedulers/slurm-preemption/slurm-signals-cheatsheet.md) | Every signal Slurm sends, whether the batch shell or the srun steps hear it, and how late it arrives |
| [slurm-reservations-and-maintenance](/fields/schedulers/slurm-cluster-operations/slurm-reservations-and-maintenance.md) | Reserving nodes for maintenance or people, and what happens to jobs that fit or overlap |
| [slurm-sacct-job-forensics](/fields/schedulers/slurm-sacct-job-forensics.md) | Reading sacct to find out how a job ended: states, exit codes, requeued runs |
| [slurm-version-changes](/fields/schedulers/slurm-cluster-operations/slurm-version-changes.md) | What changed between Slurm 23.11 and 26.05 for preemption, Lua, reservations, signals, accounting and cgroups, plus the security timeline |
| [slurm-kill-task-failed](/fields/schedulers/slurm-cluster-operations/slurm-kill-task-failed.md) | Why jobs fail to die on uninterruptible sleep, drain the node, and how to debug it |
| [slurm-spool-dir-full](/fields/schedulers/slurm-cluster-operations/slurm-spool-dir-full.md) | The "SlurmdSpoolDir is full" drain: the real culprit and a triage runbook |
| [slurm-pam-adopt-ssh-access](/fields/schedulers/slurm-cluster-operations/slurm-pam-adopt-ssh-access.md) | Closing the SSH backdoor with pam_slurm_adopt |
| [slurm-reboot-order](/fields/schedulers/slurm-cluster-operations/slurm-reboot-order.md) | Rebooting a Slurm cluster without losing jobs |
| [slurm-upgrade-order](/fields/schedulers/slurm-cluster-operations/slurm-upgrade-order.md) | The order to upgrade Slurm daemons, the version window, and the parts that bite |
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
