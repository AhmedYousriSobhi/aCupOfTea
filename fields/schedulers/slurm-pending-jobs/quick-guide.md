---
id: slurm-pending-jobs-quick
title: Find Out Why a Slurm Job Is Pending
order: 4
sidebar_label: "Quick guide: pending jobs"
summary: Read the reason column, tell waiting from never-starting, see the priority breakdown and roll out a QOS limit safely.
level: beginner
type: [guide, reference]
domains: [systems-and-hpc, schedulers]
tags: [slurm, hpc, quick]
relations:
  related: [slurm-pending-reasons, slurm-priority-multifactor, slurm-qos-limits]
---

# Find Out Why a Slurm Job Is Pending

> **Quick guide for** the [Why is my job still pending series](/fields/schedulers/slurm-pending-jobs/README.md).
> Use it when a user asks why a job has not started. You end knowing whether to wait, fix the job, or change a limit.

## Before you start

- A job ID, and `squeue`, `sprio`, `sshare` and `sacctmgr` on your path.
- Admin rights for `sacctmgr`. A user can lower a time limit or release their own hold, but cannot raise a limit.

---

## Steps

1. Read the reason.

   ```bash
   squeue -u $USER -t PD -o "%.8i %.12j %.8Q %.24r"
   scontrol show job <jobid> | grep -o 'Reason=[^ ]*'
   squeue --start -j <jobid>
   ```

   **Expect:** a reason such as `Resources` or `Priority`.
   **If not:** the job is not pending, so check its state.

2. Decide: wait or act. Use the table below.
   **Expect:** `Resources` means first in line, `Priority` means someone is ahead.
   **If not:** look up the reason in `squeue(1)`, section JOB REASON CODES.

3. If it is `Priority`, see why.

   ```bash
   sprio -o "%.6i %.6u %.9Y %.6A %.9F %.6Q"
   sshare -a -o account,user,rawshares,rawusage,effectvusage,fairshare
   ```

   **Expect:** priority split into age, fairshare and QOS columns.
   **If not:** every weight defaults to 0, so a column of zeros means the factor is off.

4. If it is a limit (`QOS...` or `Assoc...`), read the live numbers.

   ```bash
   scontrol show assoc_mgr flags=qos qos=gpu-normal
   scontrol show assoc_mgr flags=assoc accounts=physics
   ```

   **Expect:** current use against the limit, such as `gres/gpu=2(2)`.
   **If not:** the limit is on the account, not the QOS.

---

## Wait or act

| Reason | Starts by itself? | Fix |
|---|---|---|
| `Resources`, `Priority` | Yes | Wait. `squeue --start` gives an estimate |
| `Dependency` | Yes, when the other job succeeds | Wait |
| `DependencyNeverSatisfied` | **Never** | `scancel` it and resubmit |
| `JobHeldUser` | **Never** | `scontrol release <id>` |
| `PartitionTimeLimit` | **Never** | Lower the time limit: `scontrol update jobid=<id> timelimit=<shorter>` |
| `BeginTime` | At that time | Nothing, or `scontrol update jobid=<id> starttime=now` |
| `ReqNodeNotAvail, Unavail` | When the node returns | Drop `-w`, or `sinfo -R` |
| `QOSMaxGRESPerUser`, `AssocGrpGRES` | When other jobs end | Wait, or ask for less |

---

## Add a limit without surprises

1. Dry run: count who would be over it today with `squeue -o "%u %b" -t R`.
2. Announce the limit and the date.
3. Put the cap on a partition QOS and add `DenyOnLimit`.

   ```bash
   sacctmgr -i add qos gpu-normal MaxTRESPerUser=gres/gpu=2
   sacctmgr -i modify qos gpu-normal set flags=DenyOnLimit
   ```

   **Expect:** a job that could never run is refused with `Job violates accounting/QOS policy`.
   **If not:** the cap is on a QOS the job does not use.

**Don't:** put a cap on a QOS only. It binds only jobs running under that QOS.
**Roll back:** `sacctmgr modify ... set MaxTRESPerUser=gres/gpu=-1` clears the limit for the next scheduling pass.

---

## Make an urgent lane

```bash
sacctmgr -i add qos urgent Priority=100
sacctmgr -i modify user carol set qos+=urgent
sbatch -q urgent ...
```

**Expect:** the job's `QOS` column in `sprio` is non-zero.
**If not:** the QOS weight is 0.

## Tips and tricks

- Ask for the estimate first: `squeue --start -j <jobid>`.
- Every priority weight defaults to 0, so turn on only the factors you want, with fairshare largest by a clear margin if groups must share fairly.
- Users can lower their own time limit and release their own hold.
- A small triage script (`whypending JOBID`) can print the reason, the number of jobs ahead and what to try.
- `-1` clears a limit.

## Warnings

> [!WARNING]
> A limit on a QOS binds only jobs running under that QOS. A second QOS bypasses your cap, so put caps on a partition QOS.

- `DependencyNeverSatisfied`, `JobHeldUser` and `PartitionTimeLimit` never start by themselves.
- Running jobs are not killed when you add a limit.

## If it fails

| What you see | Likely cause | Fix |
|---|---|---|
| `Memory specification can not be satisfied` at submit | Asked for more than the nodes have | Lower `--mem` |
| `Invalid account or account/partition combination specified` | User is not in that account | Use their own account |
| `Job dependency problem` | The dependency job does not exist | Fix the `--dependency` ID |
| `Access/permission denied for job 12` | A user tried to raise a time limit | Only an admin can |

**Why it works:** [reading the reason column](/fields/schedulers/slurm-pending-jobs/why-is-my-job-pending.md), [who goes first](/fields/schedulers/slurm-pending-jobs/who-goes-first.md), [limits that wait forever](/fields/schedulers/slurm-pending-jobs/limits-that-wait-forever.md). Next: [read what happened to a finished job](/fields/schedulers/slurm-sacct-job-forensics.md).
