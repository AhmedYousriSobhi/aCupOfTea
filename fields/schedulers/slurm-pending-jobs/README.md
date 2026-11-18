
# Why Is My Job Still Pending?


The question every cluster admin answers ten times a week, and every user asks the moment their job doesn't start. This series answers it properly, for both sides of the ticket: what the reason column means, how Slurm decides who goes first, and which limits make a job wait forever without telling anyone.

Tested on Slurm **23.11.4** (Ubuntu 24.04 packages) with slurmdbd and MariaDB, and checked against the Slurm 26.11 documentation for anything that changed since.

---

## Contents

| File | Description |
| --- | --- |
| [1. Reading the Reason Column](/fields/schedulers/slurm-pending-jobs/why-is-my-job-pending.md) | What each common pending reason means, which ones fix themselves, which never will, and a small triage script |
| [2. Who Goes First](/fields/schedulers/slurm-pending-jobs/who-goes-first.md) | The multifactor priority formula, fairshare, age and QOS weights, reading `sprio` and `sshare`, and the all-zero default |
| [3. Limits That Wait Forever](/fields/schedulers/slurm-pending-jobs/limits-that-wait-forever.md) | QOS and account limits in practice, the second QOS that bypasses your cap, partition QOS, and `DenyOnLimit` |

---

## How the pages were tested

- **Lab:** a controller (`head01`) running slurmctld, slurmdbd and MariaDB 10.11, four CPU nodes (`cn001`–`cn004`, 2 CPUs each) and one GPU node (`gpu001`) with four GPUs, all Ubuntu 24.04 containers.
- **The GPUs were fake:** four device files, enough for Slurm to schedule and count them, not to run CUDA. Every GPU result on these pages is about scheduling, which is all these pages claim.
- **Every reason on these pages was produced on purpose** and its output copied from the terminal. The triage script was run against each reason, and had a bug that the pages show.

## Related pages

- [Slurm multi-tenancy](/fields/schedulers/slurm-accounting-multi-tenancy.md): who stores the limits and who enforces them. Read it first if `sacctmgr` is new to you.
- [Backfill tuning](/fields/schedulers/slurm-backfill-tuning.md): why `squeue --start` estimates drift, and how the backfill scheduler finds gaps.
- [Lab build cheatsheet](/fields/schedulers/slurm-ai-clusters/lab-build-cheatsheet.md): every step used to build this lab, as copy-paste commands.
- [Slurm for AI Clusters](/fields/schedulers/slurm-ai-clusters/README.md): the next series, on the same lab.

<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [Autopsy of a Job: Reading sacct Like a Coroner](/fields/schedulers/slurm-sacct-job-forensics.md) — How to find out what happened to a job that has gone, with sacct states, exit codes (exit:signal), requeued runs, useful fields, and the neighbors scontrol, sstat and sreport.
- [Lab Build Cheatsheet: A Slurm AI Cluster in Containers](/fields/schedulers/slurm-ai-clusters/lab-build-cheatsheet.md) — Every step used to build the Slurm lab behind the pending-jobs and AI-cluster series - node image, Slurm 23.11 with accounting, topology, PyTorch, Enroot and Pyxis, health check, Slurm 26.05, metrics.
- [Limits That Wait Forever: QOS and Account Limits in Practice](/fields/schedulers/slurm-pending-jobs/limits-that-wait-forever.md) — How Slurm QOS and account GPU limits behave on a real queue - the job that never runs, the second QOS that slips past a cap, partition QOS, DenyOnLimit, and live usage via assoc_mgr.
- [Reading the Reason Column: Why Is My Slurm Job Pending?](/fields/schedulers/slurm-pending-jobs/why-is-my-job-pending.md) — What Slurm's common pending reasons mean, which ones fix themselves and which never will, what users can fix without an admin, and a small triage script tested against each reason.
- [Schedulers: The Traffic Controller Nobody Thanks Until It Breaks](/fields/schedulers/slurm-intro.md) — What a cluster scheduler does, how it differs from the OS scheduler, the scheduler landscape, the concepts they share, and the Slurm architecture at a glance.
- [Who Goes First: Slurm's Priority Number, Taken Apart](/fields/schedulers/slurm-pending-jobs/who-goes-first.md) — How Slurm's multifactor priority is computed from age, fairshare and QOS weights, why every weight defaults to zero, how Fair Tree turns usage into a rank, and reading sprio and sshare.

</div>
