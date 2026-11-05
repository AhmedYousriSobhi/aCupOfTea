# Schedulers - Overview

How a cluster scheduler decides who runs where, with Slurm as the working example.

Forty people share a cluster. Everyone wants the GPUs now. Somebody has to decide who goes first, where the job lands and what happens when it misbehaves. That somebody is the scheduler, and these pages show how Slurm does it.

## Contents

| File | Description |
|------|-------------|
| [slurm-intro](/fields/schedulers/slurm-intro.md) | What a scheduler does and why it matters |
| [slurm-job-script-tale](/fields/schedulers/slurm-job-script-tale.md) | The story of job.sh and the snapshot Slurm takes of it |
| [slurm-slurmstepd](/fields/schedulers/slurm-slurmstepd.md) | The small daemon that actually runs your job, and why jobs survive slurmd restarts |
| [slurm-cgroups-in-practice](/fields/schedulers/slurm-cgroups-in-practice.md) | What cgroup.conf really constrains, v1 vs v2, and why sacct memory numbers are samples |
| [slurm-gpu-affinity-socket-lie](/fields/schedulers/slurm-gpu-affinity-socket-lie.md) | GPU core affinity vs Slurm socket affinity, and how to fix the topology |
| [slurm-accounting-multi-tenancy](/fields/schedulers/slurm-accounting-multi-tenancy.md) | Who stores and who enforces multi-tenant rules: slurmdbd, associations, QOS, fairshare |
| [slurm-backfill-tuning](/fields/schedulers/slurm-backfill-tuning.md) | Why a short bf_window hides long jobs, and how to tune backfill with sdiag |
| [slurm-preemption-requeue-signals](/fields/schedulers/slurm-preemption-requeue-signals.md) | Preemption modes, GraceTime, signals your training job ignores, and a requeue-safe wrapper |
| [slurm-kill-task-failed](/fields/schedulers/slurm-kill-task-failed.md) | Why jobs fail to die on uninterruptible sleep, drain the node, and how to debug it |
| [slurm-spool-dir-full](/fields/schedulers/slurm-spool-dir-full.md) | The "SlurmdSpoolDir is full" drain: the real culprit and a triage runbook |
| [slurm-pam-adopt-ssh-access](/fields/schedulers/slurm-pam-adopt-ssh-access.md) | Closing the SSH backdoor with pam_slurm_adopt |
| [slurm-reboot-order](/fields/schedulers/slurm-reboot-order.md) | Rebooting a Slurm cluster without losing jobs |
| [slurm-upgrade-order](/fields/schedulers/slurm-upgrade-order.md) | The order to upgrade Slurm daemons, the version window, and the parts that bite |
| [slurm-mixed-gpus](/fields/schedulers/slurm-mixed-gpus/README.md) | Series: mixing H100s and A100s in one Slurm job, and when it pays off |

## The route

| Start here if... | Read |
|------------------|------|
| You are new to schedulers | [slurm-intro](/fields/schedulers/slurm-intro.md), then [slurm-job-script-tale](/fields/schedulers/slurm-job-script-tale.md) |
| Jobs misbehave or nodes drain | [slurm-kill-task-failed](/fields/schedulers/slurm-kill-task-failed.md), [slurm-spool-dir-full](/fields/schedulers/slurm-spool-dir-full.md) |
| You run a multi-user cluster | [slurm-accounting-multi-tenancy](/fields/schedulers/slurm-accounting-multi-tenancy.md), [slurm-backfill-tuning](/fields/schedulers/slurm-backfill-tuning.md), [slurm-preemption-requeue-signals](/fields/schedulers/slurm-preemption-requeue-signals.md) |
| You maintain the cluster | [slurm-reboot-order](/fields/schedulers/slurm-reboot-order.md), [slurm-upgrade-order](/fields/schedulers/slurm-upgrade-order.md) |
