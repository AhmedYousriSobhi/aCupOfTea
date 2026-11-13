---
id: slurm-backfill-tuning
title: "Backfill Tuning: The Planner That Can Only See One Day Ahead"
order: 3
sidebar_label: Backfill tuning
summary: Slurm backfill relies on accurate time limits. A 1-day bf_window hides 7-day jobs, causing squeue drift. Use sdiag to tune bf_window, bf_resolution, bf_max_job_test, and bf_max_time.
level: advanced
type: guide
domains:
  - systems-and-hpc
tags:
  - slurm
  - hpc
relations:
  related:
    - slurm-accounting-multi-tenancy
    - slurm-preemption-requeue-signals
---

# Backfill Tuning: The Planner That Can Only See One Day Ahead

> **Part of the [schedulers](/fields/schedulers/slurm-intro.md) directory.** The intro explains what backfill is. This page is about the knobs, the failure modes, and the one counter screen (`sdiag`) that tells you whether either matters. Defaults and option descriptions come from SchedMD's Scheduling Configuration Guide for Slurm 26.05 and the `sdiag` man page. Tuning advice and logs come from SchedMD support tickets and the slurm-users list. Nothing here was run on a live cluster, the invented scenario is just that, and the `sdiag` sample uses made-up numbers.

## Table of Contents

- [Backfill Tuning: The Planner That Can Only See One Day Ahead](#backfill-tuning-the-planner-that-can-only-see-one-day-ahead)
  - [Table of Contents](#table-of-contents)
  - [The planner with a one-day calendar](#the-planner-with-a-one-day-calendar)
  - [Two schedulers, several clocks](#two-schedulers-several-clocks)
  - [How backfill actually thinks](#how-backfill-actually-thinks)
  - [The window and the resolution](#the-window-and-the-resolution)
  - [Backfill is only as honest as your time limits](#backfill-is-only-as-honest-as-your-time-limits)
  - [Why squeue --start drifts](#why-squeue---start-drifts)
  - [Depth and the time budget](#depth-and-the-time-budget)
  - [Per-user limits and job arrays](#per-user-limits-and-job-arrays)
    - [What bf\_max\_job\_user does](#what-bf_max_job_user-does)
    - [Reading the 12345\_\[1-1000\] lines](#reading-the-12345_1-1000-lines)
    - [How arrays meet the scheduler](#how-arrays-meet-the-scheduler)
    - [So what about 1000 tasks and bf\_max\_job\_user=50?](#so-what-about-1000-tasks-and-bf_max_job_user50)
  - [Reading sdiag](#reading-sdiag)
  - [A tuning recipe: one knob at a time](#a-tuning-recipe-one-knob-at-a-time)
  - [When you need to watch it think](#when-you-need-to-watch-it-think)
  - [Cheat sheet](#cheat-sheet)
  - [References](#references)

* * *

## The planner with a one-day calendar

An invented but common story. A cluster allows jobs of up to 7 days. A user submits a 64-node job with a 6-day time limit. It is the highest-priority job in the queue, and it waits. And waits. Meanwhile hundreds of small jobs start, run and finish around it. The big job's reason is `Priority` or `Resources`, and `squeue --start` shows nothing useful.

Nothing is broken. The backfill scheduler plans resources into the future so that small jobs cannot steal what a big job is waiting for. But it only plans as far ahead as `bf_window`, and `bf_window` defaults to **1440 minutes, one day**. A job that needs a slot that only opens beyond that horizon never gets protected, so the small jobs keep filling the gaps in front of it.

SchedMD states the rule in one sentence, in both the guide and the `slurm.conf` man page: a `bf_window` at least as long as the highest allowed time limit is generally advisable to prevent job starvation. One support ticket shows it in real life: a site with a 1-day window suspected exactly this when its larger MPI jobs would not schedule, and the SchedMD engineer's reply was to set `bf_window` to the maximum time limit allowed on the cluster, 7 days, and raise `bf_resolution` to 10 minutes:

```
SchedulerParameters=bf_window=10080,bf_resolution=600
```

The rest of this page is why that works, what it costs, and how to know whether your cluster needs it.

* * *

## Two schedulers, several clocks

Slurm has two scheduling mechanisms, and people often mix them up when they read tuning advice.

| Mechanism | When it runs | How far it looks | Key knobs (default) |
|---|---|---|---|
| **Event-triggered** | At job submission, job completion and config changes | A quick attempt at the top of the queue | `default_queue_depth` (100 jobs) |
| **Main loop** | Every `sched_interval` | All jobs, limited by `partition_job_depth` | `sched_interval` (60 s), `partition_job_depth` (0, no limit) |
| **Backfill** | Every `bf_interval` | Pending jobs in priority order, planned into the future | `bf_interval` (30 s), `bf_window` (1440 min), `bf_resolution` (60 s), `bf_max_job_test` (100) |

The first two follow a strict rule. Jobs are evaluated in priority order, and **once any job in a partition is left pending, no other jobs in that partition are scheduled**, so lower-priority jobs cannot take the resources of the waiting one. Without backfill, that rule alone gives you head-of-line blocking and, in SchedMD's words, significantly lower utilization.

Backfill is the clever part. It lets lower-priority jobs start now if doing so does not delay the expected start of any higher-priority job. That promise depends on two things: how far ahead it can see, and how well it can guess when running jobs will end.

* * *

## How backfill actually thinks

From the guide, in order:

1. It considers every running job and works out when each will end.
2. It walks the pending jobs in priority order and works out when and where each could start, taking preemption, gang scheduling, GRES and memory into account.
3. If a job can start now without hurting the expected start of any higher-priority job, it starts.
4. Otherwise, the resources it will need are **reserved for its expected execution time**, and its expected start time is recorded. The nodes involved show up in a `Planned` state.

Three consequences deserve their own lines:

- **"Any higher priority job" is stricter than it sounds.** Backfill does not protect only the job at the head of the queue. It builds a plan for as many pending jobs as it manages to test, which is why `bf_max_job_test` matters so much (see below).
- **Backfill reserves whole nodes**, even for jobs that do not need whole nodes. The guide says this is for performance. On a cluster full of small jobs, reservations can look much bigger than the jobs behind them.
- **A job submitted to several partitions appears once per partition** in the list backfill walks, and may reserve resources in each, though it only starts in the reservation with the earliest start. That multiplies its cost in the backfill's work queue. The option `bf_one_resv_per_job` limits it to one reservation per job, at the price of no longer guaranteeing the earliest-partition start.

* * *

## The window and the resolution

`bf_window` is how many **minutes** into the future backfill plans. `bf_resolution` is the **granularity in seconds** of that plan. The guide's tuning advice ties them together: if you raise the window, raise the resolution too, to limit the amount of data backfill has to manage.

The arithmetic shows why. Here is a back-of-envelope count of time slots in the plan, which is my own illustration of the trade-off and not a figure from the docs:

| `bf_window` | `bf_resolution` | Slots in the plan |
|---|---|---|
| 1,440 min (default, 1 day) | 60 s (default) | 1,440 |
| 10,080 min (7 days) | 60 s | 10,080 |
| 10,080 min (7 days) | 600 s | 1,008 |

Going from a 1-day to a 7-day window at the default resolution makes the plan seven times larger, which means more work in every cycle and, per the man page, "more overhead and less responsiveness". Coarsening the resolution to 10 minutes gives you the week of vision for roughly the cost of the original day. The price is imprecision: start times are planned on a coarser grid. The docs say larger resolutions suit sites where time limits are imprecise anyway, or where a small delay in starting jobs is an acceptable trade for higher utilization.

Practical rules:

- **Set the window from your longest `MaxTime`** across all partitions, converted to minutes. A 7-day `MaxTime` is 10,080.
- **The window has hard limits.** The man page gives a minimum of 1 and a maximum of 43,200 minutes (30 days).
- **Unlimited time limits break the plan.** On the list, a user whose jobs had no `--time` and no partition limit was told that if the resulting runtime is more than 28 days, the scheduler does not reserve slots for those jobs. A job that cannot fit inside the window cannot be planned.
- **Re-check the window when `MaxTime` changes.** Raising a partition's limit to 14 days without touching `bf_window` quietly recreates the starvation problem.

> [!NOTE]
> The precise mechanism by which a job beyond the window loses its protection is not spelled out in the guide. What the docs and the ticket establish is the rule (window at least as long as the longest time limit) and the symptom (large jobs not starting). The explanation above is the standard reading of those two facts.

* * *

## Backfill is only as honest as your time limits

Backfill plans from the **time limits** of running jobs, not from how long they will really run. The guide says it plainly: because the expected start time of pending jobs depends on the expected completion time of running jobs, reasonably accurate time limits are important for backfill to work well, and backfill is difficult without reasonable time limit estimates.

Think of it as a reservation system at a restaurant where every party books a table "until closing". The host cannot promise anyone a table. A few lines in `slurm.conf` give you some control over that:

| Setting | What it does |
|---|---|
| `DefaultTime` (per partition) | The time limit given to jobs that do not specify one |
| `MaxTime` (per partition) | The ceiling on time limits |
| `OverTimeLimit` | Grace beyond the limit before a job is killed (system-wide) |

If `DefaultTime` is not set, a job without `--time` inherits the partition `MaxTime`, so a cluster with a 7-day maximum and no default quietly turns every careless submission into a 7-day reservation. On the list, a site new to Slurm asked whether a job-submit plugin that requires `--time` is the way out. That is a reasonable policy lever, and a short `DefaultTime` is a gentler one.

**Measure the gap.** A rough script that compares what users asked for with what they used, per user. It is a sketch and untested, so run it on a small date range first:

```bash
# ratio of used time to requested time for completed jobs, per user
sacct -X -s CD -S 2026-10-01 -E now -n -P -o User,ElapsedRaw,TimelimitRaw \
 | awk -F'|' '$3+0 > 0 { used[$1]+=$2/60; asked[$1]+=$3; n[$1]++ }
   END { for (u in used) printf "%-12s jobs=%-6d used/asked=%.2f\n", u, n[u], used[u]/asked[u] }' \
 | sort -t= -k3 -n
```

A ratio near 1.0 means honest limits. A ratio of 0.1 means that user is booking ten times the table they use. Reports like this are better used for a friendly conversation than for punishment, since users have good reasons to pad (a job killed at the limit loses all its work), and the [preemption page](/fields/schedulers/slurm-preemption/slurm-preemption-requeue-signals.md) covers making jobs safe to shorten.

* * *

## Why squeue --start drifts

`squeue --start` shows the expected start time that backfill assigned. It is a **forecast**, and like any forecast it changes when its inputs change. Reasons for drift, with the evidence for each:

| Cause | Direction | Source |
|---|---|---|
| A running job finishes **earlier** than its time limit | Start moves earlier | The guide: expected start depends on expected completion of running jobs |
| A **higher-priority** job arrives and is planned ahead of yours | Start moves later | Follows from backfill planning in priority order |
| Fairshare usage decays or accumulates, reordering the queue | Either | Follows from priority-ordered planning |
| Nodes drain, reservations appear | Later | Resources the plan counted on are gone |
| The job is **not in the plan at all** this cycle | Shows `N/A` or "now" | See below |
| The cycle is cut short by `bf_max_time` or `bf_max_job_test` before reaching the job | Stale or missing | See [Depth and the time budget](#depth-and-the-time-budget) |

The "not in the plan" row has a well-documented oddity. In a SchedMD ticket from a large site, a pending job's `START_TIME` flipped between `N/A` and a time one second from now, every ten seconds, while nodes sat idle. The controller log said "StartTime set but no backfill reservation created". The engineer's suspicion was `bf_min_age_reserve`, set to 6 hours at that site: jobs younger than that get no backfill reservation, so their start time is placeholder noise. They suggested trying the default of 0 and finding the smallest value that fit. The case was closed as timed out without a confirmed root cause, and the reporter observed jobs starting before the age threshold, so treat that one as a lead rather than a rule.

A cheap check when a start time looks odd:

```bash
scontrol show job <jobid> | grep -E 'StartTime|SchedNodeList|LastSchedEval|Scheduler|Reason'
```

`LastSchedEval` says when a scheduler last evaluated the job, and `Scheduler=Backfill:*` (as it appeared in the ticket) says who. A `LastSchedEval` that is minutes old on a busy cluster suggests backfill is not reaching that job.

> [!TIP]
> Treat `squeue --start` as a hint, never a promise. Users who plan around it will be disappointed in both directions.

* * *

## Depth and the time budget

The window decides how far ahead backfill looks. These settings decide **how many jobs** it looks at and **how long it is allowed to think**.

| Setting | Default | Plain English |
|---|---|---|
| `bf_max_job_test` | **100** | Jobs considered per cycle. Past this depth, jobs are not tested at all |
| `bf_max_time` | = `bf_interval` (30 s) | Wall-clock limit for one cycle, sleeping included |
| `bf_interval` | 30 s | Pause between cycles |
| `bf_continue` | off | Keep going after the periodic lock release |
| `bf_yield_interval` | 2,000,000 µs | How often backfill gives the locks back |
| `bf_yield_sleep` | 500,000 µs | How long it stays out |
| `bf_max_job_user` | 0 (no limit) | Jobs per user that may start per cycle |
| `bf_max_job_part` | 0 (no limit) | Jobs per partition that may start per cycle |
| `bf_max_job_start` | 0 (no limit) | Jobs that may start per cycle |

The default `bf_max_job_test` of 100 is worth pausing on. On a cluster with thousands of pending jobs, the backfill scheduler by default never reaches the 101st job in priority order, so lower-priority work deep in the queue is invisible to it. A SchedMD engineer's suggestion on one ticket was `bf_max_job_test=500`, alongside `bf_window=480` matching an 8-hour maximum limit and `bf_resolution=300`. A very large site in another ticket runs `bf_max_job_test=25000` with several per-user and per-partition caps. Both are examples of what some sites do, not recommendations.

**Why `bf_continue` matters.** Backfill is a long-running operation holding locks that job submissions need, so it releases the locks every `bf_yield_interval` (2 seconds by default) for `bf_yield_sleep`. The guide describes `bf_continue` as continuing backfill "after periodically releasing locks", and says doing so ignores newly submitted jobs. Without it, a lock release can cut a long cycle short, so on a deep queue backfill may never get far down the list. The trade the guide names: more jobs considered, but newly submitted jobs may be scheduled later.

**Why per-user limits matter.** A single user who submits thousands of separate jobs (for example with a shell loop around `sbatch`) can fill the depth budget with their own jobs. `bf_max_job_user` and `bf_max_job_part` cap how much of each cycle one user or partition can consume. Job arrays behave differently, and the next section covers both.

* * *

## Per-user limits and job arrays

### What bf_max_job_user does

The `slurm.conf` man page describes `bf_max_job_user` as the maximum number of jobs per user that backfill will **attempt to start**, counted across all partitions. Its stated purpose is to stop a user from flooding the backfill queue with jobs that cannot start and that keep other users' jobs from starting. The man page compares it to the MAXIJOB limit in Maui, says it applies only to `sched/backfill`, and advises setting `bf_max_job_test` to a value **much higher** than `bf_max_job_user`.

Take `bf_max_job_user=50` and a user with 100 separate pending jobs:

| Question | Answer |
|---|---|
| How many of that user's jobs does one backfill cycle attempt? | At most 50, in priority order. The other 50 are skipped for that cycle |
| Are the other 50 rejected? | No. They stay pending and move into the top 50 on later cycles as earlier ones start or finish |
| Is this a cap on queue size or running jobs? | No. Those are association limits such as `MaxSubmitJobs` and `MaxJobs` |
| Do the skipped jobs get a backfill reservation? | Not in that cycle, so they are unprotected and their `squeue --start` may show `N/A` |
| Does it save backfill much work? | Less than you might expect. A SchedMD reply on ticket 2762 says skipped jobs are still briefly looked at and still count against `bf_max_job_test` and `bf_max_job_part` |
| Do blocked jobs count? | Yes. On the same ticket, each job tested counts toward the limit, even when a QOS or TRES limit then stops it. Fifty stuck jobs at the head of a user's queue can shadow runnable jobs behind them |
| Does it stop the main scheduler from starting those jobs? | No. The limit applies only to the backfill scheduler |

### Reading the 12345_[1-1000] lines

If you have not met job arrays, the squeue output looks odd at first. An array is many similar jobs submitted as one:

```bash
#SBATCH --array=1-1000          # tasks 1 to 1000
#SBATCH --array=1-1000%50       # same, but at most 50 running at once
#SBATCH --array=0-100:10        # 0,10,20,...,100
#SBATCH --array=1,5,10-12       # an explicit list
```

Each task gets an index in `SLURM_ARRAY_TASK_ID` and shares `SLURM_ARRAY_JOB_ID`. In output file names, `%A` is the array job ID and `%a` the task index. The largest index is `MaxArraySize - 1`, and the default `MaxArraySize` is 1001, so indices run 0 to 1000 on a default configuration.

The official guide says `squeue` reports all the pending tasks of one record on **one line**, with the task IDs written as a range. A sketch of what you see (job IDs and names invented, layout from the guide):

```
$ squeue
JOBID            PARTITION  NAME  USER   ST  TIME  NODES  NODELIST(REASON)
12345_[8-1000]   normal     sim   alice  PD  0:00  1      (Resources)
12345_5          normal     sim   alice  R   0:42  1      node041
12345_6          normal     sim   alice  R   0:42  1      node042
12345_7          normal     sim   alice  R   0:41  1      node043
```

| You see | It means |
|---|---|
| `12345_[8-1000]` with `PD` | One line standing for all pending tasks, 8 to 1000 |
| `12345_7` with `R` | Task 7 has started and now has a record of its own |
| `12345_[20,23-24]` | A pending set that is not contiguous (this form appears in a real ticket) |
| `12345_[1-1000%50]` | The same, with a limit of 50 running at once (my recollection of the notation, so check it on your version) |

Useful commands:

```bash
squeue -r                    # one array task per line (SQUEUE_ARRAY does the same)
squeue -j 12345_7            # one task
scancel 12345_7              # cancel one task
scancel 12345_[1-50]         # cancel a range of tasks
scontrol show job 12345      # ArrayJobId / ArrayTaskId fields
```

### How arrays meet the scheduler

- **Records are created progressively.** The guide says job records for the tasks are created as the array runs, not all up front. A pending array normally costs one record, and `sdiag` counts it as one job until tasks start, are requeued or are individually modified.
- **The main scheduler walks an array one task at a time.** Once a task of an array is left pending, no other tasks of that array are considered, which is why arrays tend to start in a steady trickle.
- **Backfill reservations for arrays have their own knob.** `bf_max_job_array_resv` limits how many tasks of one array get resources reserved. I have not confirmed its default, and the sites in the tickets I read set it to values like 2 and 20.
- **`MaxJobCount` still counts every task.** The man page says each task of an array counts as one job even though it has no separate record until modified or started. A few large arrays can reach the limit, which is why site admins pair arrays with `MaxSubmitJobs` and `MaxJobs`.

### So what about 1000 tasks and bf_max_job_user=50?

I could not find a source that says exactly how `bf_max_job_user` counts the tasks of a pending array, so this part is inference. Because a pending array is normally one record, it most likely uses one of the 50 slots, and running tasks are not "attempts to start". If so, the limit rarely bites an array. It bites the user who submits 1000 separate jobs in a loop, which creates 1000 records. That is the practical argument for steering users toward arrays with a `%N` throttle.

A quick way to settle it on your own cluster:

```bash
# as a test user, with a short time limit
sbatch --array=1-100 --time=00:05:00 --wrap='sleep 60'           # one array
for i in $(seq 100); do sbatch --time=00:05:00 --wrap='sleep 60'; done   # 100 jobs
scontrol setdebugflags +Backfill
# read slurmctld.log, then compare how many of each get "_dump_job_test" lines per cycle
scontrol setdebugflags -Backfill
```

* * *

## Reading sdiag

`sdiag` is the stethoscope. It reports what `slurmctld` has been doing since the counters were last reset, which by default happens at midnight UTC. (`sdiag -r` resets them by hand, as root.) The backfill block is the part this page cares about. Below is an **illustrative** layout using field names from the man page, with invented numbers:

```
Backfilling stats
  Total backfilled jobs (since last slurm start): 1843021
  Total backfilled jobs (since last stats cycle start): 5120
  Total cycles: 2760
  Last cycle: 3811000          (microseconds)
  Max cycle: 29870000
  Mean cycle: 4620000
  Last depth cycle: 100
  Last depth cycle (try sched): 100
  Depth Mean: 100
  Depth Mean (try sched): 100
  Last queue length: 4120
  Queue length mean: 3980
  Last table size: 1744
  Mean table size: 1650
```

How to read it. These are heuristics built from the field definitions, not official thresholds:

| What you see | What it suggests |
|---|---|
| **Depth Mean (try sched)** equals `bf_max_job_test` | Backfill is hitting its depth cap every cycle |
| **Last queue length** much bigger than depth | Most of the queue is never tested. The man page counts a job once per partition it requested |
| **Max cycle** close to `bf_max_time` in µs (30 s is 30,000,000) | Cycles are being cut off by the time budget |
| **Mean cycle** close to or above `bf_interval` | Backfill is barely finishing before the next one is due |
| **Mean table size** growing after you raise `bf_window` | The plan is bigger, so each cycle costs more. The man page says larger counts increase backfill time |
| **Total backfilled jobs** small next to **Jobs started** | Backfill is contributing little, which may be fine on a quiet cluster |

Two details from the man page that stop misreadings:

- **"Last cycle" and "Max cycle" count execution time only**, with the sleeping time during lock releases removed. A cycle that took 30 seconds on the clock may show less.
- **"Depth" and "Depth (try sched)" are different.** The first counts every job examined, even ones that cannot start because of dependencies or limits. The second counts only jobs that had a chance to start. The second is the one that makes backfill heavy.

The same output also reports main-scheduler cycles and RPC counts per user, which is where you look when someone's `watch squeue` loop is the actual problem.

* * *

## A tuning recipe: one knob at a time

Backfill parameters interact, so change one thing, wait a representative period, and look at `sdiag` again.

1. **Baseline.** Save `sdiag` output and the current line:
   ```bash
   sdiag > sdiag.before
   scontrol show config | grep SchedulerParameters
   ```
2. **Fix the window first.** It is the one with a rule. Set `bf_window` to your longest `MaxTime` in minutes, and raise `bf_resolution` with it:
   ```
   SchedulerParameters=bf_window=10080,bf_resolution=600
   ```
   Keep the existing options in the line. Replacing the whole value drops anything not repeated.
3. **Check depth.** If **Depth Mean (try sched)** sits at `bf_max_job_test` and the queue is longer, raise it in steps (for example 100, then 300, then 500) and watch **Mean cycle** and **Max cycle**.
4. **Give it room to think.** If cycles are cut off, look at `bf_max_time`, and consider `bf_continue`. If submissions feel slow, shorten the yield interval, as the docs suggest for high-throughput sites.
5. **Stop one user eating the depth.** Add `bf_max_job_user` and, if needed, `bf_max_job_part`.
6. **Re-measure.** After at least a day, compare against the baseline. Remember the counters reset at midnight UTC.

Apply changes and confirm them:

```bash
scontrol reconfigure
scontrol show config | grep SchedulerParameters
```

One ticket from 2019 told the user to restart `slurmctld` and then reconfigure; a recent site guide says `scontrol reconfigure` is enough for `SlurmctldParameters`. Check what your version does on a test controller before touching production.

* * *

## When you need to watch it think

If a job refuses to start and the numbers do not explain why, turn on backfill logging for a short time, then switch it off:

```bash
scontrol setdebugflags +Backfill,BackfillMap
# ... wait a few cycles, read slurmctld.log ...
scontrol setdebugflags -Backfill,-BackfillMap
```

The ticket above also asked for `debug3` and the `Priority` and `Accrue` flags for the same short window, and for the log level to go back to normal right after. Lines worth knowing from that ticket:

| Log line | Meaning |
|---|---|
| `_dump_job_test: Test JobId=...` | Backfill is evaluating that job this cycle |
| `... has a prio_reserve of ...` | The `bf_min_prio_reserve` threshold is in play for that job |
| `StartTime set but no backfill reservation created` | The job got a start time without a reservation (see the drift section) |
| `_start_job: Started JobId=...` | Backfill started the job |

These logs are large. Capture a ten-minute window, filter by the job ID, and put the log level back.

* * *

## Cheat sheet

```
Window     bf_window (min) >= longest MaxTime; default 1440; range 1..43200
Resolution raise it when you raise the window (10080 / 600 is a documented example)
Depth      bf_max_job_test default 100  -> deep queues are invisible by default
Budget     bf_max_time defaults to bf_interval (30 s); bf_continue keeps going after lock release
Per user   bf_max_job_user = jobs per user ATTEMPTED per cycle (not a queue cap); keep bf_max_job_test far above it
Arrays     12345_[8-1000] = one pending record; running tasks get 12345_7; squeue -r expands them
Honesty    backfill plans from time limits: set DefaultTime, measure Elapsed vs Timelimit
Forecast   squeue --start is an estimate; flickers/N-A can mean "no reservation this cycle"
Evidence   sdiag: Max cycle vs bf_max_time, Depth Mean (try sched) vs bf_max_job_test,
           Last queue length vs depth, Mean table size vs window/resolution
Method     one knob, one day, then sdiag again
```

Backfill is a planner with two inputs it cannot fix itself: a horizon, and the truthfulness of the people booking the tables. The horizon is one line of configuration. The truthfulness is a long-term project.

* * *

## References

- [Slurm: Scheduling Configuration Guide](https://slurm.schedmd.com/sched_config.html)
- [Slurm: sdiag man page](https://www.mankier.com/1/sdiag), and the [Debian 13 copy with the full field list](https://dokk.org/manpages/debian/13/slurm-client/sdiag.1.en)
- [SchedMD ticket 7207: backfill for HPC cluster (1-day window, set to 7 days)](https://support.schedmd.com/show_bug.cgi?id=7207)
- [SchedMD ticket 6688: tuning suggestions for bf_* and max_rpc_cnt](https://support.schedmd.com/show_bug.cgi?id=6688)
- [SchedMD ticket 14608: start time constantly pushed, bf_min_age_reserve](https://support.schedmd.com/show_bug.cgi?id=14608)
- [SchedMD ticket 2762: what bf_max_job_user limits](https://support.schedmd.com/show_bug.cgi?id=2762)
- [slurm-users: bf_max_job_user and bf_max_job_user_part man page text (2020)](https://lists.schedmd.com/pipermail/slurm-users/2020-March/005049.html)
- [Slurm: Job Array Support (squeue display, task records, MaxArraySize)](https://third-party-mirror.googlesource.com/SchedMD/slurm/+/HEAD/doc/html/job_array.shtml)
- [SchedMD SUG 2014: scheduling tutorial slides (array scheduling rule)](https://Slurm.schedmd.com/SUG14/sched_tutorial.pdf)
- [UL HPC: job arrays and MaxArraySize](https://hpc-docs.uni.lu/jobs/arrays/)
- [Niflheim: Slurm configuration (MaxJobCount and job arrays)](https://niflheim-system.readthedocs.io/en/latest/Slurm_configuration.html)
- [slurm-users: large memory jobs stuck pending, bf_window and --time (2025)](https://lists.schedmd.com/mailman3/hyperkitty/list/slurm-users@lists.schedmd.com/thread/CXS4DPV2KGQC7C2UAJBWC3H5AJSW6BGV/)
- [Niflheim: Slurm job scheduler configuration](https://niflheim-system.readthedocs.io/en/latest/Slurm_scheduler.html)