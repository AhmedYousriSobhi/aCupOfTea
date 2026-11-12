---
id: slurm-qos-preemption-setup
title: "The Guest List: Setting Up QOS Preemption Without Starting a War"
order: 14
sidebar_label: QOS preemption setup
summary: A step-by-step setup of QOS-based requeue preemption (slurm.conf, sacctmgr, who may use what), a drill that proves it works, and the quiet ways it goes wrong.
level: intermediate
type: guide
domains:
  - systems-and-hpc
tags:
  - slurm
  - hpc
relations:
  prerequisites:
    - slurm-accounting-multi-tenancy
  related:
    - slurm-preemption-requeue-signals
    - slurm-job-submit-lua
    - slurm-signals-cheatsheet
    - slurm-qos-limits
---

# The Guest List: Setting Up QOS Preemption Without Starting a War

> **Part of the [schedulers](/fields/schedulers/slurm-intro.md) directory.** The [preemption page](/fields/schedulers/slurm-preemption-requeue-signals.md) explains what preemption *is*. This page is the other half: the commands that switch it on. Everything here was run on a two-node test cluster (Slurm 23.11.4, accounting on, both `slurmd` daemons on one Ubuntu 24.04 machine) and then adapted to read well. The names are invented. Your site's defaults, and your Slurm version, may differ, so run the drill in step 4 before you trust it.

## Table of Contents

- [The Guest List: Setting Up QOS Preemption Without Starting a War](#the-guest-list-setting-up-qos-preemption-without-starting-a-war)
  - [Table of Contents](#table-of-contents)
  - [The Thursday before the deadline](#the-thursday-before-the-deadline)
  - [Three dials, one cluster](#three-dials-one-cluster)
  - [Step 1: switch preemption on](#step-1-switch-preemption-on)
  - [Step 2: define the two tiers](#step-2-define-the-two-tiers)
  - [Step 3: let people use the tiers](#step-3-let-people-use-the-tiers)
  - [Partition priority instead?](#partition-priority-instead)
  - [Step 4: prove it with a drill](#step-4-prove-it-with-a-drill)
  - [Five ways this goes quietly wrong](#five-ways-this-goes-quietly-wrong)
  - [Rolling it out, and back](#rolling-it-out-and-back)
  - [Version notes](#version-notes)
  - [Back to the Thursday](#back-to-the-thursday)
  - [References](#references)

---

## The Thursday before the deadline

It is Thursday evening. The bio lab has a paper due Monday, and Priya needs eight GPUs for a final run. All the GPUs are busy. Most of them are held by a hyperparameter sweep that a student in another time zone started three days ago, and that, honestly, could stop and restart tomorrow without anyone noticing.

The admin has three options. Message the student and wait for a reply that arrives Saturday. Cancel the sweep and lose the student's trust forever. Or have set things up beforehand, so the scheduler can ask the sweep to step aside, politely, and put it back in line afterwards.

The third option takes four small steps. None of them is hard, but each has one sentence of fine print, and the fine print is the whole page.

---

## Three dials, one cluster

Preemption by QOS is not one setting. It is three settings living in three places, and they have to agree:

| Dial | Lives in | Says |
|---|---|---|
| Preemption on, and how | `slurm.conf` | "Use QOS rules; victims are requeued" |
| The tiers themselves | The accounting database (`sacctmgr`) | "`low` exists; `high_bio` may evict `low`" |
| Who may use which tier | Associations (`sacctmgr`) | "Users in account `bio` may submit to `high_bio`" |

A fourth, optional piece decides which tier a job *lands in* when the user doesn't say. That is either a default QOS on the association or the [Lua submit script](/fields/schedulers/slurm-job-submit-lua.md). Neither is preemption itself: they only put a label on the job.

---

## Step 1: switch preemption on

Preemption is **off by default** (`PreemptMode=OFF`). In `slurm.conf`:

```text
PreemptType=preempt/qos
PreemptMode=REQUEUE
AccountingStorageEnforce=associations,qos
```

`PreemptType` picks the rulebook. It takes **one** value, so QOS rules and partition-priority rules are alternatives, not layers. `PreemptMode` is the cluster-wide fate of a victim, and each QOS can override it.

Check what the controller actually loaded:

```bash
scontrol show config | grep -E '^Preempt|^AccountingStorageEnforce|^JobRequeue|^KillWait'
```

```text
PreemptType             = preempt/qos
PreemptMode             = REQUEUE
KillWait                = 30 sec
```

> [!WARNING]
> Changing `PreemptType` needs a restart of `slurmctld`; `scontrol reconfigure` is not enough. A restart does not touch running jobs, but submissions fail for a few seconds while the daemon is down, so pick a quiet moment.

`AccountingStorageEnforce` needs `qos` in it, or Slurm does not hold users to the QOS they are allowed. That is the same switch described in [the accounting page](/fields/schedulers/slurm-accounting-multi-tenancy.md#turning-it-on-safely).

---

## Step 2: define the two tiers

One victim tier, and one high tier per account that is allowed to evict:

```bash
# the tier that gets evicted
sacctmgr -i add qos low Priority=10
sacctmgr -i modify qos low set PreemptMode=requeue GraceTime=120 PreemptExemptTime=00:30:00

# one high tier per account, each allowed to evict "low"
for acct in physics bio; do
    sacctmgr -i add qos "high_${acct}" Priority=1000
    sacctmgr -i modify qos "high_${acct}" set Preempt=low
done

sacctmgr show qos format=Name%14,Priority,Preempt%14,PreemptMode,GraceTime,PreemptExemptTime
```

```text
          Name   Priority        Preempt PreemptMode  GraceTime   PreemptExemptTime
-------------- ---------- -------------- ----------- ---------- -------------------
        normal          0                    cluster   00:00:00
           low         10                    requeue   00:02:00            00:30:00
  high_physics       1000            low     cluster   00:00:00
      high_bio       1000            low     cluster   00:00:00
```

`cluster` in the `PreemptMode` column means "use the cluster-wide mode from `slurm.conf`". Only `low` overrides it.

The settings sit on opposite sides, and mixing them up is the commonest mistake:

| Setting | Goes on | Meaning |
|---|---|---|
| `Preempt=low` | the **preemptor** (`high_bio`) | "I may evict these QOSs" |
| `PreemptMode`, `GraceTime`, `PreemptExemptTime` | the **victim** (`low`) | "this is what happens to me, and when" |

`Priority` helps order the queue, but under `preempt/qos` it is the `Preempt=` list that decides who may evict whom. A high-`Priority` QOS with no `Preempt=` evicts nobody.

`PreemptExemptTime` is a minimum runtime before a job may be evicted. It is a good idea in production (nobody wants a job evicted a minute after it starts) and a trap in a drill, where it makes nothing happen for half an hour. Set it to `00:00:00` while testing.

---

## Step 3: let people use the tiers

A QOS nobody may submit to is a very tidy decoration. Add both tiers to each account, with `+=` so existing QOSs are kept:

```bash
for acct in physics bio; do
    sacctmgr -i modify account name="$acct" set qos+=low,"high_${acct}"
done
sacctmgr show assoc format=Account%12,User%12,DefaultQOS,QOS%30
```

Now the question from the beginning: which tier does a job get when the user types nothing? Two answers, and both work:

| Way | How | Good for |
|---|---|---|
| Default QOS on the association | `sacctmgr modify user alice set DefaultQOS=low` | Plain defaults, nothing to maintain |
| Submit script | [`job_submit.lua`](/fields/schedulers/slurm-job-submit-lua.md) | Rewriting what the user typed, e.g. `--qos=high` into `high_<account>` |

In the test cluster, a job submitted with no `--qos` by a user whose `DefaultQOS` was `low` came out as `low`, with the submit script doing nothing. If "everyone types `--qos=high_bio` themselves" is acceptable, you can stop here and skip Lua entirely.

---

## Partition priority instead?

The same idea works with `PreemptType=preempt/partition_prio`: a job in a partition with a higher `PriorityTier` may evict jobs in a lower-tier partition that share its nodes. Choose by how your cluster is already organized:

| Choose | When |
|---|---|
| `preempt/qos` | Policy follows groups, projects or users; you want several tiers in one partition |
| `preempt/partition_prio` | The cluster is already split into queues such as `high` and `low`, over the same nodes |

You cannot mix them. Pick one, and remember that changing it is a controller restart.

---

## Step 4: prove it with a drill

Do this on a quiet node, as a normal user in a real account. Give `low` drill-sized settings first, `PreemptExemptTime=00:00:00` and a short `GraceTime`, and put the real values back afterwards:

```bash
sacctmgr -i modify qos low set GraceTime=30 PreemptExemptTime=00:00:00
```

Then two jobs on one node, `--exclusive` so they cannot share it:

```bash
# 1. the victim: low QOS, requeueable, appends to its log
L=$(sbatch --parsable -A physics --qos=low -w node1 --exclusive --requeue \
      --open-mode=append -o low.out --wrap='sleep 600')

# 2. wait until it is RUNNING, then land the preemptor on the same node
H=$(sbatch --parsable -A physics --qos=high_physics -w node1 --exclusive --wrap='sleep 5')

# 3. once the high job is COMPLETED (about a minute or two): what happened?
sacct -X -D -j $L,$H -o JobID,QOS%12,State%12 -P
scontrol show job $L | grep -oE 'Requeue=[0-9]+ Restarts=[0-9]+'
```

```text
JobID|QOS|State
55|low|PREEMPTED
56|high_physics|COMPLETED
55|low|RUNNING
Requeue=1 Restarts=1
```

Read the output like a detective. Job `55` appears twice because `-D` shows every run of a requeued job: first run `PREEMPTED`, second run `RUNNING` again. `Restarts=1` is the proof of a requeue, as opposed to a cancel. And the preemptor ran, which is the point.

After the high job finishes, the victim starts again on its own. A script that does not look for its own checkpoint will start from the top, which is why the [preemption page](/fields/schedulers/slurm-preemption-requeue-signals.md) spends so long on resuming.

> [!NOTE]
> The drill's victim used `sleep`, which dies on the first `SIGTERM`, so the preemptor started as soon as the victim was told. A real training job that ignores `SIGTERM` gets `KillWait` (30 seconds here) on top of the grace time before `SIGKILL`. The [signals cheat sheet](/fields/schedulers/slurm-signals-cheatsheet.md) has the measured timings.

---

## Five ways this goes quietly wrong

| Symptom | Cause | What to check |
|---|---|---|
| The victim is **gone**, not requeued. `sacct` shows `PREEMPTED` and no second run | It was not requeueable: `JobRequeue=0` and no `--requeue` | `scontrol show job <id>` shows `Requeue=0`. Set `JobRequeue=1`, or make the [submit script](/fields/schedulers/slurm-job-submit-lua.md#recipe-3-make-the-victims-requeueable) set it |
| Nothing is ever evicted | `Preempt=` is missing on the high QOS, or on the wrong side | `sacctmgr show qos format=Name,Preempt` |
| Nothing is evicted for the first half hour | `PreemptExemptTime` is longer than the job has run | The exempt time on the victim QOS |
| `Invalid qos specification` on submit | The user's association does not include that QOS | `sacctmgr show assoc user=<name> format=Account,QOS%30` |
| A high job still waits behind a low one | The low job asked for `--exclusive=user` or `--exclusive=mcs`, which block cross-user preemption | Plain `--exclusive` was fine in the test; see the [preemption page](/fields/schedulers/slurm-preemption-requeue-signals.md#preemption-fine-print) |

Two more are worth a sentence each. Jobs that were already running or pending before you switched this on keep their old QOS and are not preemptible until they finish, and that is a feature. And `PreemptMode=SUSPEND` keeps a suspended job's GPUs allocated, so for GPU clusters requeue is the mode that actually frees anything.

---

## Rolling it out, and back

The safe order is the order of the steps, because each one is invisible until the next:

1. Create the QOSs and grant them to accounts (steps 2 and 3). Nothing changes yet.
2. Set the `slurm.conf` lines (step 1). If `PreemptType` changed, restart `slurmctld` in a quiet moment.
3. Run the drill (step 4) on one node.
4. Only then tell users the `low` tier exists.

To roll back, set **both** `PreemptType=preempt/none` and `PreemptMode=OFF`, and restart `slurmctld`. Together is the point: in the test, `preempt/none` with `PreemptMode=REQUEUE` was refused with "PreemptType and PreemptMode values incompatible", and the controller would not start. With both set, it started and a high-QOS job simply waited (`Resources`) instead of evicting anything. The QOSs can stay in the database. Unused QOSs cost nothing.

---

## Version notes

The drill output on this page came from Slurm 23.11.4. Since then: 24.05 treats a job that was signalled during `GraceTime` as preempted for `CANCEL` and `REQUEUE`; 25.05 adds a `PRIORITY` option and removes a deleted QOS from other QOSes' preempt lists; 26.05 applies `PreemptExemptTime` to `suspend,gang` under `preempt/partition_prio`. Rerun the drill after any upgrade. [Version changes 23.11 to 26.05](/fields/schedulers/slurm-version-changes.md#preemption) has the list.

---

## Back to the Thursday

Replay the evening with this page applied. Priya submits with `--qos=high`, which becomes `high_bio` on the way in. The scheduler looks at the nodes, finds the sweep running under `low`, sends it a polite signal and, once the grace time is up, puts it back in the queue. The sweep's own script, which saves a checkpoint every hour, picks up where it left off the moment a node is free.

The student wakes up in the morning to a log with one extra line and a job that is still running. Nobody sent a message. Nobody cancelled anything. Priya's run finished on Friday afternoon.

**Takeaway:** preemption by QOS is three settings that must agree (`slurm.conf`, the QOS rules, and who may use them), `Preempt=` goes on the preemptor and `GraceTime` on the victim, and only a drill with `Restarts=1` proves it works.

**Next:** [The Receptionist Who Rewrites Your Badge](/fields/schedulers/slurm-job-submit-lua.md) shows how a submit script routes jobs into these tiers automatically.

---

## References

- [Slurm: Preemption](https://slurm.schedmd.com/preempt.html)
- [Slurm: Quality of Service (QOS)](https://slurm.schedmd.com/qos.html)
- [Slurm: sacctmgr](https://slurm.schedmd.com/sacctmgr.html)
- [Slurm: slurm.conf](https://slurm.schedmd.com/slurm.conf.html) (`PreemptType`, `PreemptMode`, `JobRequeue`, `KillWait`)
