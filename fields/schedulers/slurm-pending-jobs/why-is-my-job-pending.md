
# Reading the Reason Column: Why Is My Slurm Job Pending?

<!-- related-block -->
<div class="reading-time">7 min read</div>
<!-- related-block -->
<div class="related-strip">

**See also:** [Autopsy of a Job: Reading sacct Like a Coroner](/fields/schedulers/slurm-sacct-job-forensics.md), [Backfill Tuning: The Planner That Can Only See One Day Ahead](/fields/schedulers/slurm-backfill-tuning.md), [Calling Dibs on Nodes: Reservations, Maintenance Windows and the Job That Fit](/fields/schedulers/slurm-cluster-operations/slurm-reservations-and-maintenance.md), [Lab Build Cheatsheet: A Slurm AI Cluster in Containers](/fields/schedulers/slurm-ai-clusters/lab-build-cheatsheet.md), [Slurm Multi-Tenancy: Who Stores the Rules, Who Enforces Them](/fields/schedulers/slurm-accounting-multi-tenancy.md), [The Cluster That Worked Perfectly and Remembered Nothing: a Two-Minute Slurm Smoke Test](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md)  ·  **Read next:** [Who Goes First: Slurm's Priority Number, Taken Apart](/fields/schedulers/slurm-pending-jobs/who-goes-first.md), [Limits That Wait Forever: QOS and Account Limits in Practice](/fields/schedulers/slurm-pending-jobs/limits-that-wait-forever.md)

</div>


> **Part 1 of [Why Is My Job Still Pending?](/fields/schedulers/slurm-pending-jobs/README.md)** By the end you'll read any pending job's reason in one look, know whether it will ever start, and have a script that tells users what to try before they open a ticket.

- [Two days in the queue](#two-days-in-the-queue)
- [Where the reason lives](#where-the-reason-lives)
- [Only one job says Resources](#only-one-job-says-resources)
- [The common reasons, produced on purpose](#the-common-reasons-produced-on-purpose)
- [Rejected before it ever queues](#rejected-before-it-ever-queues)
- [What users can fix themselves](#what-users-can-fix-themselves)
- [A triage script, and the bug we found in it](#a-triage-script-and-the-bug-we-found-in-it)
- [Back to the two days](#back-to-the-two-days)
- [References](#references)

---

## Two days in the queue

A PhD student submits a training job on Monday morning and checks on Wednesday. Still `PD`. They've watched other people's jobs start and finish around theirs. They open a ticket: "the scheduler is broken, my job isn't starting".

The admin runs one command and sees `PartitionTimeLimit`. The student asked for three days on a partition whose limit is two. The job was never going to start, and Slurm said so from the first second, in a column nobody read.

Most pending jobs are fine; they're just waiting. A few will wait forever. The reason column tells you which, if you know how to read it.

> [!NOTE]
> Lab: Slurm **23.11.4** with slurmdbd, four CPU nodes in partition `cpu` (2 CPUs each, 2-day `MaxTime`) and one node in partition `gpu`. Every reason below was produced on purpose and copied from the terminal. Reason names come from `squeue(1)`, section JOB REASON CODES.

---

## Where the reason lives

Slurm records one **reason** for every pending job: its best single explanation of why that job isn't running *right now*. Three ways to see it:

```bash
squeue -u $USER -t PD -o "%.8i %.12j %.8Q %.24r"     # id, name, priority, reason
scontrol show job <jobid> | grep -o 'Reason=[^ ]*'
squeue --start -j <jobid>                              # estimated start, if Slurm has one
```

The default `squeue` output puts the reason in the last column, in brackets, as `NODELIST(REASON)`. Easy to miss when you're looking for a node list.

---

## Only one job says Resources

We filled the `cpu` partition, then submitted more jobs. This is the most misread line on any cluster:

```text
JOBID   USER        NAME PRIORITY                   REASON
   21  carol   carol-job    10000                Resources
   13    bob     bob-job     6000                 Priority
   12  alice  wants-2cpu     2000                 Priority
```

| Reason | Means |
| --- | --- |
| `Resources` | This job is **first in line** for the partition. It's waiting for nodes to free up |
| `Priority` | One or more jobs with higher priority are ahead of it in the same partition |

Only the top job in a partition shows `Resources`. Everyone behind it shows `Priority`, even when they'd fit the moment something frees up. So `Priority` doesn't mean "your priority is low"; it means "you're not first". (Alice submitted before bob and carol, and still sits behind both. That's fairshare, and it's [part 2](/fields/schedulers/slurm-pending-jobs/who-goes-first.md).)

Smaller jobs behind the queue can still start early, through the backfill scheduler, if they fit in a gap without delaying the top job. See [backfill tuning](/fields/schedulers/slurm-backfill-tuning.md).

---

## The common reasons, produced on purpose

Here's every reason we produced, with the command that caused it, whether it fixes itself, and who can fix it:

| Reason | How we caused it | Starts by itself? | Fix |
| --- | --- | --- | --- |
| `Resources` | Partition full | Yes | Wait. `squeue --start` gives an estimate |
| `Priority` | Behind other jobs | Yes | Wait. [Part 2](/fields/schedulers/slurm-pending-jobs/who-goes-first.md) explains the order |
| `Dependency` | `--dependency=afterok:12`, job 12 still pending | Yes, when 12 succeeds | Wait |
| `DependencyNeverSatisfied` | `afterok` on a job that exited 3 | **Never** | `scancel` it and resubmit |
| `BeginTime` | `--begin=now+2hours` | Yes, at that time | Nothing, or `scontrol update jobid=<id> starttime=now` |
| `JobHeldUser` | `sbatch -H` | **Never** | `scontrol release <id>` |
| `ReqNodeNotAvail, Unavail` | `-w cn004` while cn004 was drained | Only when the node returns | Drop the `-w`, or ask why it's drained: `sinfo -R` |
| `PartitionTimeLimit` | `-t 3-00:00:00` on a 2-day partition | **Never** | Lower the time limit |
| `QOSMaxGRESPerUser` | More GPUs than the QOS allows per user | Depends; see [part 3](/fields/schedulers/slurm-pending-jobs/limits-that-wait-forever.md) | Wait for your other jobs, or ask less |
| `AssocGrpGRES` | The account's GPU limit was reached | When the account's other jobs end | Wait, or talk to your group |

The three marked **Never** are the ones that generate tickets. Nothing about the cluster will change their fate. `PartitionTimeLimit` is the sneakiest: by default Slurm accepts the job and lets it wait. (`EnforcePartLimits` in `slurm.conf` makes it reject such jobs at submission instead.)

`JobHeldUser` showed priority `0` in our lab. A held job isn't considered at all.

---

## Rejected before it ever queues

Some mistakes never get as far as a reason. `sbatch` refuses them and prints why. From the same lab:

| What we asked | What `sbatch` said |
| --- | --- |
| `--mem=64G` on nodes with 3 GB configured | `Memory specification can not be satisfied` / `Requested node configuration is not available` |
| `-A chem` by a user who isn't in that account | `Invalid account or account/partition combination specified` |
| `--dependency=afternotok:999999` (no such job) | `Job dependency problem` |

These are the good failures: immediate, specific, and impossible to miss.

---

## What users can fix themselves

Several fixes don't need an admin. A user can update their own pending job, as long as the change makes it *smaller* or *later*:

```bash
scontrol update jobid=14 timelimit=1-00:00:00   # 3 days -> 1 day: allowed
scontrol release 18                              # their own hold: allowed
```

Both ran as the job's owner in the lab, exit 0, and both jobs moved to `Priority`. Asking for *more* is refused:

```text
$ scontrol update jobid=12 timelimit=3-00:00:00
Access/permission denied for job 12
```

Only an operator or admin can raise a limit. That's on purpose: otherwise a user could submit a short job to get backfilled, then extend it.

---

## A triage script, and the bug we found in it

Most of the tickets above have the same answer, so put the answer next to the question. This script takes a job ID, reads the reason, and prints what to try. Save it as `/usr/local/bin/whypending` on login nodes:

```bash
#!/usr/bin/env bash
# whypending JOBID - explain why a pending Slurm job is waiting, and what to try.
set -euo pipefail
job=${1:?usage: whypending JOBID}
line=$(squeue -h -j "$job" -o "%T|%P|%Q|%r") || exit 1
IFS='|' read -r state part prio reason <<<"$line"
if [ "$state" != "PENDING" ]; then echo "job $job is $state, not pending"; exit 0; fi
# Ahead = higher priority, or equal priority and submitted earlier (lower job ID).
ahead=$(squeue -h -t PD -p "$part" -o "%Q %i" | awk -v p="$prio" -v j="$job" '$1 > p || ($1 == p && $2 < j)' | wc -l)
echo "job $job: pending in partition $part, priority $prio, reason: $reason"
case "$reason" in
  Resources)                echo "First in line for $part. Waiting for nodes to free up. Estimate: squeue --start -j $job" ;;
  Priority)                 echo "$ahead pending job(s) in $part are ahead of it. Breakdown: sprio -j $job" ;;
  Dependency)               echo "Waiting for another job to finish: scontrol show job $job | grep -o 'Dependency=[^ ]*'" ;;
  DependencyNeverSatisfied) echo "The job it depends on ended the wrong way. This job will never start: scancel $job" ;;
  ReqNodeNotAvail*)         echo "A node it needs is down, drained or reserved. Check: sinfo -R" ;;
  PartitionTimeLimit)       echo "Time limit is above the partition's MaxTime. Lower it: scontrol update jobid=$job timelimit=<shorter>" ;;
  BeginTime)                echo "Asked not to start before a set time: scontrol show job $job | grep -o 'StartTime=[^ ]*'" ;;
  JobHeld*)                 echo "Held. Release it: scontrol release $job" ;;
  QOS*)                     echo "A QOS limit. See it: sacctmgr show qos format=name,maxtrespu,grptres,maxwall" ;;
  Assoc*)                   echo "An account or user limit. See it: sacctmgr show assoc where user=$(squeue -h -j "$job" -o %u) format=account,user,grptres,maxtres" ;;
  *)                        echo "Look this reason up in squeue(1), section JOB REASON CODES." ;;
esac
```

We ran it against every reason above. A few of the answers:

```text
job 55: pending in partition cpu, priority 2000, reason: DependencyNeverSatisfied
The job it depends on ended the wrong way. This job will never start: scancel 55

job 56: pending in partition cpu, priority 2000, reason: PartitionTimeLimit
Time limit is above the partition's MaxTime. Lower it: scontrol update jobid=56 timelimit=<shorter>

job 59: pending in partition gpu, priority 2000, reason: AssocGrpGRES
An account or user limit. See it: sacctmgr show assoc where user=alice format=account,user,grptres,maxtres
```

An unknown job ID prints Slurm's own `Invalid job id specified` and exits 1.

The bug: the first version counted only jobs with **higher** priority as "ahead". Two jobs from the same user had the same priority (2000), and the second one was told:

```text
0 pending job(s) in cpu have higher priority. Breakdown: sprio -j 60
```

True, and useless: it was second in line. Slurm breaks priority ties by submission order, so the count now includes equal-priority jobs with a lower job ID. Retested: the first job said `First in line`, the second `1 pending job(s) in cpu are ahead of it`.

> [!TIP]
> The script uses only `squeue`, so any user can run it on their own jobs. It doesn't need accounting access.

---

## Back to the two days

Run Monday again with this page on the wiki. The student submits, sees `PD`, runs `whypending`, and reads: "Time limit is above the partition's MaxTime. Lower it." One `scontrol update` later, the job is `Priority`, then `Resources`, and it's running before lunch. No ticket, two days saved.

And when the reason *is* `Priority`, the script says how many jobs are ahead and points at `sprio`. That's the right question for part 2: not "is the scheduler broken" but "why are those jobs ahead of mine".

**Takeaway:** `Resources` means first in line and `Priority` means not first; check for the three reasons that never clear (`DependencyNeverSatisfied`, held jobs, `PartitionTimeLimit`) before waiting any longer.

**Next:** [Part 2, Who Goes First](/fields/schedulers/slurm-pending-jobs/who-goes-first.md), opens up the priority number.

---

## References

- [squeue(1)](https://slurm.schedmd.com/squeue.html): output format codes (`%r`, `%Q`), `--start`, and the JOB REASON CODES section.
- [Slurm: Resource Limits](https://slurm.schedmd.com/resource_limits.html): the limit-related reasons and how they're enforced.
- [scontrol(1)](https://slurm.schedmd.com/scontrol.html): `update jobid=... timelimit=`, `release`, and what users may change.
- [sbatch(1)](https://slurm.schedmd.com/sbatch.html): `--dependency`, `--begin`, `-H`, `-w`.
- [slurm.conf(5): EnforcePartLimits](https://slurm.schedmd.com/slurm.conf.html#OPT_EnforcePartLimits): rejecting jobs that exceed partition limits at submission.
- [Backfill tuning](/fields/schedulers/slurm-backfill-tuning.md): how jobs behind the queue can still start early.
