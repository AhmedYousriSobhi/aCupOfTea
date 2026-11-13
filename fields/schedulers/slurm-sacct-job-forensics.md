---
id: slurm-sacct-job-forensics
title: "Autopsy of a Job: Reading sacct Like a Coroner"
order: 4
sidebar_label: Job forensics with sacct
summary: How to find out what happened to a job that has gone, with sacct states, exit codes (exit:signal), requeued runs, useful fields, and the neighbors scontrol, sstat and sreport.
level: beginner
type: guide
domains:
  - systems-and-hpc
tags:
  - slurm
  - hpc
relations:
  related:
    - slurm-pending-reasons
    - slurm-preemption-requeue-signals
    - slurm-qos-preemption-setup
    - slurm-cgroups-in-practice
    - slurm-accounting-multi-tenancy
---

# Autopsy of a Job: Reading sacct Like a Coroner

> **Part of the [schedulers](/fields/schedulers/slurm-intro.md) directory.** The outputs below were produced on a two-node test cluster (Slurm 23.11.4, accounting on, both `slurmd` daemons on one Ubuntu 24.04 machine), with jobs created to die in each way. Job numbers and users are invented. `sacct` needs the accounting database, so on a cluster without `slurmdbd` it has nothing to read.

## Table of Contents

- [Autopsy of a Job: Reading sacct Like a Coroner](#autopsy-of-a-job-reading-sacct-like-a-coroner)
  - [Table of Contents](#table-of-contents)
  - [The job that vanished](#the-job-that-vanished)
  - [First, find the body](#first-find-the-body)
  - [Reading the verdict](#reading-the-verdict)
  - [Dying of old age](#dying-of-old-age)
  - [The job that was evicted](#the-job-that-was-evicted)
  - [The fields worth knowing](#the-fields-worth-knowing)
  - [The neighbors on the shelf](#the-neighbors-on-the-shelf)
  - [Four questions for the coroner](#four-questions-for-the-coroner)
  - [Version notes](#version-notes)
  - [Back to the vanished job](#back-to-the-vanished-job)
  - [References](#references)

---

## The job that vanished

A student writes to the admin: "my job disappeared". It is not in `squeue`. The output file is half written. There is no error message anywhere. The student is not sure it ever finished, never mind how it ended.

The admin could grep logs on three machines. Or run one command, because Slurm keeps a record of every job's life and death, and the coroner's tool for reading it is `sacct`. It answers four questions: did the job finish, was it killed, who did it, and was it even the job's fault?

---

## First, find the body

```bash
sacct -j 44,45,46,47
```

```text
JobID           JobName  Partition    Account  AllocCPUS      State ExitCode
------------ ---------- ---------- ---------- ---------- ---------- --------
44                 wrap        gpu    physics          1  COMPLETED      0:0
44.batch          batch               physics          1  COMPLETED      0:0
45                 wrap        gpu    physics          1     FAILED      3:0
45.batch          batch               physics          1     FAILED      3:0
46                 wrap        gpu    physics          1     FAILED      0:9
46.batch          batch               physics          1  CANCELLED      0:9
47                 wrap        gpu    physics          1 CANCELLED+      0:0
47.batch          batch               physics          1  CANCELLED     0:15
```

Each job has a main line, and below it a line per **step**: `.batch` is your script, `.0`, `.1` are the `srun` steps. The main line is the verdict. The step lines are the evidence.

Four options do most of the work:

| Option | What it does |
|---|---|
| `-j <ids>` | Pick the jobs |
| `-X` | Show only the main line per job, with no step lines |
| `-o JobID,State,ExitCode,...` | Choose the columns |
| `-P` | Plain pipe-separated output, with nothing truncated, which is what you want for pasting |

By default `sacct` looks at jobs from today. For an older job, give a start date with `-S 2026-11-01`. Without it, an older job simply does not appear, which is a good way to convince yourself a job never existed.

---

## Reading the verdict

The `State` says how the job ended. `ExitCode` is two numbers, **exit code : signal**. The first is what the script returned. The second is the signal that stopped it, if any.

```bash
sacct -X -j 44,45,46,47 -o JobID,State,ExitCode,Elapsed -P
```

```text
JobID|State|ExitCode|Elapsed
44|COMPLETED|0:0|00:00:02
45|FAILED|3:0|00:00:00
46|FAILED|0:9|00:00:00
47|CANCELLED by 30033|0:0|00:00:11
```

| Job | What the test did | Verdict | How to read it |
|---|---|---|---|
| 44 | `sleep 2` | `COMPLETED 0:0` | The ordinary, happy ending |
| 45 | `exit 3` | `FAILED 3:0` | The script itself returned 3. The bug is in the script |
| 46 | `kill -9 $$` | `FAILED 0:9` | Exit code 0, **signal 9**: something killed it with `SIGKILL`. The out-of-memory killer and an admin's `kill -9` look the same here |
| 47 | `scancel` by a user | `CANCELLED by 30033` | A person, and `30033` is their user ID. Not the job's fault |

The signal half is the coroner's best friend. `0:9` is `SIGKILL` and `0:15` is `SIGTERM`. Notice job 47's step line in the earlier table: `.batch` shows `0:15`, because `scancel` sends `SIGTERM` first, and the job line shows `0:0` because nothing failed. Different lines of the same record tell different parts of the story.

(In the narrow default table the state is cut to `CANCELLED+`. The `+` means "there is more": widen it with `-o State%20`, or use `-P`, and the "by 30033" appears.)

---

## Dying of old age

A job that runs into its time limit is killed by Slurm, and the record says so:

```text
JobID|State|Timelimit|Elapsed|ExitCode
23|TIMEOUT|00:02:00|00:02:26|0:9
```

`TIMEOUT` is unambiguous. The `Elapsed` is longer than the `Timelimit` here, by 26 seconds, because Slurm checks limits on a periodic tick and then waits `KillWait` for the job to exit after `SIGTERM`. The [signals cheat sheet](/fields/schedulers/slurm-preemption/slurm-signals-cheatsheet.md#everything-arrives-late-and-sometimes-early) has the timings. In that test the job ignored `SIGTERM` on purpose, which is why the signal in `ExitCode` is `9`.

---

## The job that was evicted

Under [QOS preemption](/fields/schedulers/slurm-preemption/slurm-qos-preemption-setup.md), the verdict is `PREEMPTED`. What happens next depends on whether the job could be requeued, and `sacct` shows both endings.

A victim that could **not** be requeued is simply gone:

```text
JobID|QOS|State
35|low|PREEMPTED
36|high_physics|COMPLETED
```

A victim that was requeued has two lives. A plain `sacct` shows only the latest one. Add **`-D`** (`--duplicates`) to see every run:

```bash
sacct -X -D -j 55,56 -o JobID,QOS%12,State%12 -P
```

```text
JobID|QOS|State
55|low|PREEMPTED
56|high_physics|COMPLETED
55|low|RUNNING
```

Job 55 appears twice: first run `PREEMPTED`, second run `RUNNING`. Without `-D`, a requeued job showed only its latest run in the test (checked on a similar job, where the plain line read `CANCELLED` and `-D` revealed the earlier `PREEMPTED`). While the job is still alive, `scontrol show job 55 | grep Restarts` gives the count (`Restarts=1`).

So "my job restarted from the beginning and I lost a day" is answered by `-D`: yes, it was evicted at that time by that QOS. That is a question for the [preemption page](/fields/schedulers/slurm-preemption/slurm-preemption-requeue-signals.md), not for the filesystem.

---

## The fields worth knowing

`sacct --helpformat` lists the columns. A few that earn their place:

| Column | Tells you |
|---|---|
| `Submit`, `Eligible`, `Start`, `End`, `Elapsed` | The timeline: how long it waited, how long it ran |
| `Timelimit` and `Elapsed` | Whether it died of old age, and how close it came |
| `QOS`, `Partition`, `Account` | Under which policy and charge it ran |
| `NodeList` | Where it ran, which matters when a node turns out to be sick |
| `Reason` | Why a job that was not running was waiting |
| `Reservation` | Which reservation it used, if any |
| `SubmitLine`, `WorkDir`, `Comment` | What was typed, and from where |
| `ReqTRES`, `AllocTRES` | What was asked for, and what was given |
| `MaxRSS` | Peak memory of the steps. **Empty unless the cluster gathers it** (`JobAcctGatherType`); the [cgroups page](/fields/schedulers/slurm-inside-a-job/slurm-cgroups-in-practice.md) explains why those numbers are samples |

(`Restart` is not a column. The test cluster refused it. Use `-D` and `scontrol show job`.)

---

## The neighbors on the shelf

| Tool | For | Remember |
|---|---|---|
| `scontrol show job <id>` | Details of a job that is queued, running, or finished only moments ago | Slurm forgets finished jobs from memory after a while. After that, only `sacct` remembers |
| `sacct` | The record of any job, after the fact | Needs `slurmdbd`; defaults to today |
| `sstat -j <id>` | A **running** job's live usage | Needs a usage-gathering plugin |
| `sreport` | Totals per account or user over time | A summary, not one job |
| `seff <id>` | A one-line efficiency summary | A contributed script, not part of every install: it was not on the test cluster |

---

## Four questions for the coroner

When a job is missing, ask in this order:

1. **Was it a person?** `CANCELLED by <uid>`. Not a bug, maybe a misunderstanding.
2. **Was it the clock?** `TIMEOUT`, and `Elapsed` at the `Timelimit`. Ask for more time or save checkpoints.
3. **Was it the code?** `FAILED` with a non-zero exit code, or a signal in the second number. Read the script's own output.
4. **Was it the cluster?** `PREEMPTED`, and also other states you will meet such as `NODE_FAIL` and `OUT_OF_MEMORY`, which this page did not reproduce. Then it is not the job's fault, and the admin should look at the node or the QOS.

---

## Version notes

Outputs are from 23.11.4. Later versions add the job's output, error and input paths to accounting (24.05), `ReqReservation` and step `TimeLimit` columns (25.05), and in 26.05 `sluid` and step `submit_line` in `--json` and `--yaml`, with a 26.05.4 fix for corrupted earlier requeue records. The notes for the development 26.11 say the name, not the UID, of whoever cancelled a job is recorded, so the `CANCELLED by 30033` form above may change. [Version changes 23.11 to 26.05](/fields/schedulers/slurm-cluster-operations/slurm-version-changes.md#accounting-sacct-and-sacctmgr) has the list.

---

## Back to the vanished job

Replay the student's email. The admin runs `sacct -X -D -j <id> -o JobID,State,ExitCode,Elapsed,Timelimit,NodeList -P`, and reads one line: `TIMEOUT`, `Elapsed` equal to the `Timelimit`, on the third node of the rack. Nothing disappeared. The job was allowed twelve hours, used twelve hours, and was ended on time.

The reply takes one minute: "your job hit its time limit; it needed longer, or it needed to save progress". No logs on three machines, no theory about the filesystem. The record had been in the database all along.

**Takeaway:** `sacct` keeps the cause of death for every job, so read `State` and the two-part `ExitCode` (exit code : signal), add `-D` to see every life of a requeued job, and ask four questions: a person, the clock, the code, or the cluster.

**Next:** the opposite problem, a job that has not started yet, is covered by [Why Is My Job Still Pending?](/fields/schedulers/slurm-pending-jobs/README.md).

---

## References

- [Slurm: sacct](https://slurm.schedmd.com/sacct.html) (job states, `--duplicates`, format fields)
- [Slurm: sstat](https://slurm.schedmd.com/sstat.html)
- [Slurm: sreport](https://slurm.schedmd.com/sreport.html)
- [Slurm: scontrol](https://slurm.schedmd.com/scontrol.html) (`show job`)
