
# Calling Dibs on Nodes: Reservations, Maintenance Windows and the Job That Fit

<!-- related-block -->
<div class="reading-time">8 min read</div>
<!-- related-block -->
<div class="related-strip">

**See also:** [Back From the Repair Shop: Is This Node Fit to Return to Service?](/fields/schedulers/slurm-smoke-tests/slurm-smoke-node-readiness.md), [Backfill Tuning: The Planner That Can Only See One Day Ahead](/fields/schedulers/slurm-backfill-tuning.md), [Measure Twice, Reconfigure Once: Smoke-Testing a slurm.conf Change](/fields/schedulers/slurm-smoke-tests/slurm-smoke-config-change.md), [Reading the Reason Column: Why Is My Slurm Job Pending?](/fields/schedulers/slurm-pending-jobs/why-is-my-job-pending.md), [Rebooting a Slurm Cluster Without Losing Your Job (Or Anyone Else's)](/fields/schedulers/slurm-cluster-operations/slurm-reboot-order.md), [SlurmdSpoolDir Is Full: The Drain That Is Not About the Spool Directory](/fields/schedulers/slurm-cluster-operations/slurm-spool-dir-full.md), [The Changelog Nobody Reads: What Moved Between Slurm 23.11 and 26.05](/fields/schedulers/slurm-cluster-operations/slurm-version-changes.md), [The Receptionist Who Rewrites Your Badge: job_submit.lua](/fields/schedulers/slurm-preemption/slurm-job-submit-lua.md)

</div>


> **Part of the [schedulers](/fields/schedulers/slurm-intro.md) directory.** Every command and output here was run on a two-node test cluster (Slurm 23.11.4, accounting on, both `slurmd` daemons on one Ubuntu 24.04 machine). The names, dates and the story are invented. Reservation flags have many options, so this page covers the maintenance and "hold it for me" cases and points to the man page for the rest.

## Table of Contents

- [Calling Dibs on Nodes: Reservations, Maintenance Windows and the Job That Fit](#calling-dibs-on-nodes-reservations-maintenance-windows-and-the-job-that-fit)
  - [Table of Contents](#table-of-contents)
  - [Firmware Saturday](#firmware-saturday)
  - [Three ways to clear a node](#three-ways-to-clear-a-node)
  - [Creating the reservation](#creating-the-reservation)
  - [The job that fits, and the job that does not](#the-job-that-fits-and-the-job-that-does-not)
  - [When the window opens](#when-the-window-opens)
  - [Reservations for people, not just for maintenance](#reservations-for-people-not-just-for-maintenance)
  - [Things that go wrong](#things-that-go-wrong)
  - [Version notes](#version-notes)
  - [Back to Firmware Saturday](#back-to-firmware-saturday)
  - [References](#references)

---

## Firmware Saturday

The vendor has released a firmware update for the compute nodes, and the admin has booked Saturday at six in the morning for it. On Wednesday, the admin has a problem: the nodes are full of jobs that were never told about Saturday, and some of them have a time limit of three days.

There are the usual three answers. Drain the nodes now, and the cluster sits half empty for days, which makes everyone who wanted those nodes loudly unhappy. Send an email, which will be read by exactly the people who did not need it. Or kill whatever is running at five fifty-nine on Saturday and take the angry messages on Monday.

There is a fourth answer, and it makes the cluster tidy itself. Tell the scheduler on Wednesday that the nodes are *already taken* from Saturday six o'clock. From that moment the scheduler plans around the window, and only starts jobs that will be finished before it opens.

---

## Three ways to clear a node

| Way | What it does | The catch |
|---|---|---|
| Drain the nodes (`scontrol update State=DRAIN`) | No new jobs, now. Running ones finish | The nodes sit idle from the moment the last job ends, however long before the maintenance that is |
| Reserve the nodes ahead of time | Jobs that fit before the window start as normal. Longer ones wait | Needs honest time limits. Jobs without `--time` never fit |
| Reboot on demand (`scontrol reboot ASAP`) | Drains, reboots and returns each node for you | Fine for a reboot; the [reboot order page](/fields/schedulers/slurm-cluster-operations/slurm-reboot-order.md) covers when it is not enough |

A reservation is the only one of the three that uses the idle time before the window. The scheduler knows when the window opens, so it keeps filling the nodes with jobs that will end in time. This is the same trick [backfill](/fields/schedulers/slurm-backfill-tuning.md) plays with a reserved start for a big job: the short jobs slip into the gap.

---

## Creating the reservation

On the test cluster, a one-hour maintenance window on `node2` that opens in ten minutes:

```bash
scontrol create reservation ReservationName=maint \
    StartTime=now+10minutes Duration=60 Nodes=node2 \
    Flags=MAINT,IGNORE_JOBS Users=root
```

```text
Reservation created: maint
```

| Field | Meaning |
|---|---|
| `StartTime` | When the window opens. A timestamp, or `now+10minutes` |
| `Duration` | Length of the window in **minutes** (`60` came back as `01:00:00`) |
| `Nodes` | Which nodes. `NodeCnt=` or `PartitionName=` are alternatives |
| `Users`, `Accounts` | Who may use the reserved nodes during the window. A maintenance window usually lists only root, or the admins |
| `Flags=MAINT` | Marks it as maintenance. It shows up in `scontrol show reservation` and in the node's state while the window is open |
| `Flags=IGNORE_JOBS` | Create the reservation even though jobs are running on the nodes right now. It does not kill them |

Look at what you made:

```bash
scontrol show reservation maint
sinfo -T
```

```text
ReservationName=maint StartTime=2026-11-12T23:03:01 EndTime=2026-11-13T00:03:01 Duration=01:00:00
 Nodes=node2 NodeCnt=1 CoreCnt=4 Features=(null) PartitionName=(null) Flags=MAINT,IGNORE_JOBS,SPEC_NODES
 TRES=cpu=4
 Users=root Groups=(null) Accounts=(null) Licenses=(null) State=INACTIVE BurstBuffer=(null) Watts=n/a

RESV_NAME     STATE           START_TIME             END_TIME     DURATION  NODELIST
maint      INACTIVE  2026-11-12T23:03:01  2026-11-13T00:03:01     01:00:00  node2
```

`State=INACTIVE` means the window has not opened yet. The reservation is a promise, and the scheduler already plans around it.

---

## The job that fits, and the job that does not

Two jobs asked for `node2` while the window was ten minutes away. One wanted five minutes; the other wanted thirty:

```text
JobID  Time limit  State    Reason
39       5:00     RUNNING  None
40      30:00     PENDING  ReqNodeNotAvail, May be reserved for other job
```

The five-minute job started at once, because it would be finished long before the window opens. The thirty-minute job waits, because it would still be running when the window opened. Neither was refused. The scheduler just did the arithmetic.

That arithmetic uses the **time limit**, not how long the job really takes. A job with no `--time` inherits the partition's `MaxTime`, which is usually days, and it can never fit a window. This is the reason the [Lua submit script](/fields/schedulers/slurm-preemption/slurm-job-submit-lua.md#recipe-2-demand-a-time-limit) insists on `--time`, and why the [backfill page](/fields/schedulers/slurm-backfill-tuning.md) keeps asking whether the limits are honest.

> [!NOTE]
> The reason text does not say "maintenance". The pending reason in the test was `ReqNodeNotAvail, May be reserved for other job`, both before the window opened and while it was open. It is the same generic message you see for any reservation. When a user asks why their job waits, look at the reservation, not the reason: `sinfo -T` and `scontrol show reservation` give the real answer. The [pending reasons page](/fields/schedulers/slurm-pending-jobs/why-is-my-job-pending.md) covers the codes.

---

## When the window opens

At the start time the reservation becomes `ACTIVE`, and the node's own state shows it:

```bash
sinfo -N -o "%N %T"
scontrol show node node2 | grep -oE 'State=[A-Z+]+'
```

```text
node2 maint
State=IDLE+MAINTENANCE+RESERVED
```

If jobs were still running on the node when the window opened, the state reads `MIXED+MAINTENANCE+RESERVED` instead. The test confirmed that **a running job is not killed when the window opens**. It kept running on `node2` and the reservation simply blocked every *new* job. A new one-minute job submitted during the window waited with the same `ReqNodeNotAvail` reason.

That detail matters for planning. The reservation protects the window from *new* work. It does nothing about work that overlaps the start, so the quality of your maintenance window depends on the time limits of the jobs that were already running when you booked it. Check them (`squeue -w node2 -o "%i %u %L"`) and decide, for each, whether it will end in time or needs a conversation.

When the work is done, release the nodes. Either let the reservation expire at its end time, or delete it early:

```bash
scontrol delete ReservationName=maint
sinfo -N -o "%N %T"
```

```text
node1 idle
node2 idle
```

The nodes went back to `idle` straight away. The order for a real maintenance (reserve, wait, reboot, resume, delete) fits with the [reboot order page](/fields/schedulers/slurm-cluster-operations/slurm-reboot-order.md).

---

## Reservations for people, not just for maintenance

The same command holds nodes for a person, which is useful for a demo, a class, or a deadline run. On the test cluster, a reservation for one user on `node1`, starting now:

```bash
scontrol create reservation ReservationName=demo StartTime=now \
    Duration=10 Nodes=node1 Users=tester
```

The user then asks for it explicitly:

```bash
sbatch --reservation=demo -w node1 job.sh
```

Both jobs below were submitted by the reservation's user, and the difference was just `--reservation`:

```text
JobID  State    Reason
41     PENDING  ReqNodeNotAvail, May be reserved for other job     (no --reservation)
42     RUNNING  None                                                (--reservation=demo)
```

The node was held for the demo even against its own user, until the job said which reservation it was using. Other users are kept off it too, since that is what the `Users` list is for (a second user was not tested).

---

## Things that go wrong

| Symptom | Cause | Check |
|---|---|---|
| The window opens and the node is still full | Jobs that were already running overlap it. IGNORE_JOBS lets you create the reservation, not kill them | `squeue -w <node> -o "%i %u %L"` before the window |
| Nothing ever starts on the reserved nodes, even for the right user | The job did not name the reservation | `--reservation=<name>`, and the user must be in `Users` or `Accounts` |
| The short jobs do not slip in before the window | They have no `--time`, so they inherit the partition `MaxTime` | A required `--time`, from the [submit script](/fields/schedulers/slurm-preemption/slurm-job-submit-lua.md) |
| A user cannot tell why their job waits | The reason text does not mention the reservation | `sinfo -T` |
| The reservation is gone after a controller problem | Reservations are saved in the controller's state directory | Back up `StateSaveLocation`, as the [spool directory page](/fields/schedulers/slurm-cluster-operations/slurm-spool-dir-full.md) notes |

---

## Version notes

Tested on 23.11.4. Later versions add the `USER_DELETE` flag (24.05), `FORCE_START` for recurring reservations and a `ReqReservation` field in `sacct` (25.05), `AllowQOS` and `AllowPartition` access controls (25.11), and in 26.05 "Do not allocate maintenance nodes to new reservations". [Version changes 23.11 to 26.05](/fields/schedulers/slurm-cluster-operations/slurm-version-changes.md#reservations) has the list.

---

## Back to Firmware Saturday

Replay Wednesday with the reservation. The admin creates `maint` for Saturday at six, then looks at what is running on the nodes and finds two jobs with limits that run into the weekend. Two short emails go to two people instead of an announcement to everyone.

From Wednesday to Saturday the scheduler does the rest. Short jobs keep arriving and keep running, because they fit before the window. Long jobs wait in the queue instead of arriving at six o'clock on Saturday morning and being killed. At five fifty-nine the nodes are nearly empty, with no drain and no idle days beforehand.

**Takeaway:** a reservation tells the scheduler about the window in advance, so jobs that fit run first and jobs that do not wait, it blocks only new work, so check the running jobs' time limits before it opens, and when a user asks why their job waits, look at `sinfo -T`, not at the reason text.

**Next:** [Autopsy of a Job](/fields/schedulers/slurm-sacct-job-forensics.md) shows how to read what happened to a job after it has gone.

---

## References

- [Slurm: Advanced Resource Reservation Guide](https://slurm.schedmd.com/reservations.html)
- [Slurm: scontrol](https://slurm.schedmd.com/scontrol.html) (`create reservation`, `update`, `delete`, `reboot`)
- [Slurm: sinfo](https://slurm.schedmd.com/sinfo.html) (`-T`)
