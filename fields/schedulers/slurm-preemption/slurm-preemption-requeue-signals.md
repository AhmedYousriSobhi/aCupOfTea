---
id: slurm-preemption-requeue-signals
title: "Dying Politely: Preemption, Requeue and the Signals Your Training Job Ignores"
order: 1
sidebar_label: Preemption, requeue and signals
summary: How Slurm preemption modes differ, what GraceTime and --signal send and to whom, why a bash trap never fires while the trainer runs, and a requeue-safe checkpoint wrapper that cannot loop.
level: intermediate
type: guide
domains:
  - systems-and-hpc
tags:
  - slurm
  - hpc
  - gpu
relations:
  related:
    - slurm-kill-task-failed
    - slurm-upgrade-order
    - slurm-accounting-multi-tenancy
    - slurm-qos-preemption-setup
    - slurm-signals-cheatsheet
    - slurm-job-submit-lua
---

# Dying Politely: Preemption, Requeue and the Signals Your Training Job Ignores

> **Part of the [schedulers](/fields/schedulers/slurm-intro.md) directory.** Preemption behavior comes from SchedMD's Preemption guide for Slurm 26.05. Signal details come from site documentation and the `sbatch` options as described there. Where a paragraph says **Tested**, the behavior was measured on a two-node test cluster running Slurm 23.11.4, so it can differ from the 26.05 guide and from your version. The wrapper script is still a sketch and was not run as a whole, so test it with a short job before trusting a week-long run to it. The [signals cheat sheet](/fields/schedulers/slurm-preemption/slurm-signals-cheatsheet.md) holds the measured timelines.

## Table of Contents

- [Dying Politely: Preemption, Requeue and the Signals Your Training Job Ignores](#dying-politely-preemption-requeue-and-the-signals-your-training-job-ignores)
  - [Table of Contents](#table-of-contents)
  - [The week-long run that wasn't](#the-week-long-run-that-wasnt)
  - [Four ways to be evicted](#four-ways-to-be-evicted)
  - [GraceTime: the polite notice (and its twist)](#gracetime-the-polite-notice-and-its-twist)
  - [--signal: the other notice](#--signal-the-other-notice)
  - [Why your trap never fires](#why-your-trap-never-fires)
  - [A requeue-safe wrapper](#a-requeue-safe-wrapper)
  - [Requeue without the infinite loop](#requeue-without-the-infinite-loop)
  - [Preemption fine print](#preemption-fine-print)
  - [Setting it up](#setting-it-up)
  - [Version notes](#version-notes)
  - [Cheat sheet](#cheat-sheet)
  - [Back to the week-long run](#back-to-the-week-long-run)
  - [References](#references)

* * *

## The week-long run that wasn't

A researcher submits a training job to a low-priority partition on Friday. It runs happily until Sunday, when someone from a better-funded group submits a job that needs those nodes. Slurm requeues the researcher's job. The training script, which saves a checkpoint every six hours, restarts from the beginning of the script. The latest checkpoint is five hours old, and the script never looks for it.

Nobody did anything wrong in the dramatic sense. Everybody just assumed that "requeue" meant "resume". It means "start the script again". What happens next is up to your script.

* * *

## Four ways to be evicted

`PreemptMode` decides what happens to a job that gets pushed off its resources. The Preemption guide lists the modes:

| Mode | What happens to the victim | Fine print |
|---|---|---|
| `CANCEL` | Cancelled | Simple and final |
| `REQUEUE` | Requeued, or cancelled if it cannot be | The job needs `--requeue`, or the cluster-wide `JobRequeue=1`. Without either, it is **cancelled** |
| `SUSPEND` | Paused in memory, resumed later by the gang scheduler | Always needs the `GANG` option. Memory stays occupied |
| `OFF` | Nothing, preemption is disabled | The default |

`PreemptType` decides *who* may preempt whom: `preempt/partition_prio` compares partition `PriorityTier` values, and `preempt/qos` uses rules stored in the accounting database. `PreemptMode` can then be set per partition or per QOS, so one cluster can requeue one queue and suspend another.

**Tested:** a victim with `JobRequeue=0` and no `--requeue` ended as `PREEMPTED` and vanished from the queue; the same eviction with the job requeueable left a second run waiting. Two more details from the same tests: `PreemptType=preempt/none` is the off switch, but it must be paired with `PreemptMode=OFF`, because `preempt/none` with `PreemptMode=REQUEUE` is refused and the controller will not start. And `PreemptMode` accepted a `WITHIN` modifier (shown as `WITHIN,REQUEUE`), though what it does was not tested. The commands to set all of this up are in [the QOS preemption setup page](/fields/schedulers/slurm-preemption/slurm-qos-preemption-setup.md).

> [!WARNING]
> Suspend and GPUs make an awkward couple. The GRES guide says that when a job is suspended, its generic resources **do not become available to other jobs**. A suspended job keeps its GPUs allocated, so suspending is a poor way to free GPUs for a preemptor. Requeue or cancel is the way to actually release them.

* * *

## GraceTime: the polite notice (and its twist)

`GraceTime` (per partition or QOS) gives a victim some time to react. Defaults and semantics, per the guide:

- The default is **0**, meaning no delay.
- When a job is selected for preemption, its end time becomes now plus `GraceTime`, or stays as it was if that is already sooner. A job whose time limit would expire first gets only what is left of it.
- The job is **immediately** sent `SIGCONT` and `SIGTERM`.
- When the new end time arrives, it gets the sequence again: `SIGCONT`, `SIGTERM`, then `SIGKILL`.

Read that again: the job receives `SIGTERM` **twice**. Once when preemption starts, and once when the grace period ends. A handler that checkpoints and then exits will be fine. A handler that does something irreversible on every `SIGTERM` will do it twice, so make yours idempotent.

> [!WARNING]
> **Tested: "the job" here means the job's `srun` steps.** With `GraceTime=30`, a step started with `srun` got `SIGTERM` and `SIGCONT` about a second after the preemptor was submitted. The **batch shell** heard nothing at that moment, and was told only when the grace period ended. A command in your script that is not behind `srun` is a child of the batch shell, so it misses the early warning too. Section [A requeue-safe wrapper](#a-requeue-safe-wrapper) runs the trainer exactly that way, so read its note before relying on `SIGTERM`.

A few more things worth knowing:

- **The end of the window is noticed late.** On the test cluster a 30-second grace period was noticed at about 33, 41 and 55 seconds, and a 60-second one at 64 and 83. A job that ignores `SIGTERM` then gets `KillWait` (30 seconds there) before `SIGKILL`, and only after that does the preemptor start. Budget the checkpoint accordingly.

- **A job that exits early still counts as preempted.** If the job leaves before `GraceTime` runs out, Slurm handles it according to `PreemptMode`, regardless of *why* it exited. It cannot tell a clean checkpoint exit from an unrelated crash that happened to land in the window.
- **`GraceTime` is not used with `SUSPEND`.** There is a separate `suspend_grace_time` for that.

* * *

## --signal: the other notice

`GraceTime` is set by the admin and only matters when a job is preempted. `--signal` is set by the user and fires when the job is within N seconds of its **end time**. Because preemption moves the end time to "now plus `GraceTime`", you might expect it to fire at preemption too, if `GraceTime` is shorter than the lead time you asked for. One university guide describes it that way.

**Tested: it does not, unless the admin asks for it.** With `GraceTime=60` and `--signal=B:USR1@300`, the batch shell received no `USR1` at preemption and heard only the final `SIGTERM`. With `PreemptParameters=send_user_signal` set in `slurm.conf`, the same job received `USR1` about a second after the preemptor was submitted. That parameter is what turns `--signal` into a real preemption warning, and it is an admin setting. Format:

```bash
#SBATCH --signal=B:USR1@300
```

| Part | Meaning |
|---|---|
| `B:` | Send only to the batch shell (the script itself). Without it, the signal goes to the job steps instead, not to the batch script |
| `USR1` | The signal. A user-defined one is a good choice, because `srun` passes it through |
| `@300` | Send it 300 seconds before the limit. With no number, the default is 60 |

The important footnote: because of how Slurm handles events, the signal can arrive **up to 60 seconds earlier** than requested. Treat the lead time as a minimum, not an appointment. **Tested:** on a 2-minute job, `--signal=B:USR1@90` arrived at 68 seconds, 52 seconds before the end instead of 90, and the time limit itself was enforced about 26 seconds late. The controller works on a periodic tick, so the lead time is approximate in both directions, and the safe plan is a checkpoint that fits the smaller window.

How this fits with the other clock, `KillWait`: on a cancel or a time limit, the sequence is `SIGTERM`, then a `KillWait` pause (30 seconds on the sites I read), then `SIGKILL`. If your checkpoint takes longer than that, `--signal` is how you buy more time. Site documentation puts it well: a checkpoint plus final sync has to fit inside whichever window you actually have.

* * *

## Why your trap never fires

Here is the bug that eats weekends. You write:

```bash
#SBATCH --signal=B:USR1@300
trap 'echo caught it; ./save_checkpoint.sh' USR1
python train.py        # runs for 11 hours
```

and the trap does not run until `train.py` finishes. That is how bash works: a trap handler runs after the current foreground command completes. If the foreground command is the thing that runs for hours, the signal sits waiting while `SIGKILL` approaches.

The cure is to run the long command in the background and `wait` for it. `wait` is interruptible by trapped signals, so the handler can run at once. This is also the structure that university cluster guides use in their checkpoint wrappers.

The trainer must cooperate too. A signal handler in Python should set a flag, not write a 20 GB checkpoint from inside the handler. The training loop checks the flag at a safe step boundary, saves, and exits.

* * *

## A requeue-safe wrapper

A sketch that combines everything above. It asks the trainer to checkpoint on `USR1`, waits for it, then requeues the job itself.

```bash
#!/bin/bash
#SBATCH --job-name=trainer
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00
#SBATCH --requeue                 # allow requeue after preemption or failure
#SBATCH --open-mode=append        # default is truncate: requeue would erase old logs
#SBATCH --signal=B:USR1@300       # warn the batch shell ~5+ min before the limit

MAX_RESTARTS=10
child=""

on_usr1() {
    echo "[$(date)] USR1: asking trainer to checkpoint and exit"
    kill -USR1 "$child" 2>/dev/null
    wait "$child"                  # let it finish writing
    if [ "${SLURM_RESTART_COUNT:-0}" -lt "$MAX_RESTARTS" ]; then
        echo "[$(date)] requeueing (restart #${SLURM_RESTART_COUNT:-0})"
        scontrol requeue "$SLURM_JOB_ID"
    else
        echo "[$(date)] restart limit reached, not requeueing"
    fi
    exit 0
}
trap on_usr1 USR1

# the trainer itself must resume from the newest checkpoint if one exists
python train.py --resume-latest &
child=$!
wait "$child"
exit $?
```

What each piece is for:

| Piece | Why |
|---|---|
| `--requeue` | Without it, a `REQUEUE` preemption becomes a cancel |
| `--open-mode=append` | Slurm's default is `truncate`, so a requeued run erases the log of the earlier run |
| `&` plus `wait` | Lets the trap run immediately |
| `SLURM_RESTART_COUNT` | Slurm sets it whenever a job restarts, and it is unset on the first run. Use it to cap restarts and to tell a fresh start from a resume |
| `--resume-latest` | The part that makes a requeue a resume. Slurm will not do this for you |

> [!NOTE]
> The wrapper handles `USR1`. A preemption with `GraceTime` delivers `SIGTERM` to the job instead, and you may want a second trap for it that calls the same function. Remember the double `SIGTERM` described earlier.

> [!WARNING]
> **Tested: this wrapper does not receive the early `SIGTERM`.** It starts the trainer with `python train.py &`, which is a child of the batch shell and not a step, and the early `GraceTime` signal went only to `srun` steps. Two ways to close the gap: start the trainer with `srun python train.py &` so it hears the early `SIGTERM` itself, or have the admin set `PreemptParameters=send_user_signal` so the `USR1` from `--signal` reaches the batch shell at preemption. In both cases the final `SIGTERM` at the end of the grace period still arrives, so keep the trap for it. The [signals cheat sheet](/fields/schedulers/slurm-preemption/slurm-signals-cheatsheet.md#which-design-to-choose) lays out the choice.

* * *

## Requeue without the infinite loop

Self-requeueing scripts have an old failure mode: a job that crashes in ten seconds requeues itself, crashes again, and keeps going until an administrator notices. Site documentation recommends two guards, which the wrapper above only partly implements:

- **Cap the restarts** with `SLURM_RESTART_COUNT`, as shown.
- **Require a minimum runtime** before a requeue is allowed. If the job has been alive for less than, say, a minute, it died of something that a restart will not fix, so do not requeue.

`SLURM_JOB_START_TIME` is available for the second check. Also note that a requeued job goes back to pending and may show a short begin-time hold before it starts again; one site's guide describes that as Slurm avoiding thrash.

* * *

## Preemption fine print

For the administrators, a handful of details from the guide that are easy to miss:

- **Backfill reserves whole nodes.** If a job preempts during a backfill pass, the whole nodes of the preempted jobs are reserved for the preemptor, even when it asked for less. One preemptor can therefore evict more than it needed to.
- **`PreemptExemptTime`** sets a minimum runtime before a job may be preempted, honored for `REQUEUE` and `CANCEL`.
- **Exclusivity blocks preemption.** `--exclusive=user` and `--exclusive=mcs` stop a job from preempting or being preempted by other users' jobs. The guide suggests using a job-submit plugin to disable those options if you rely on preemption. **Tested:** a [Lua submit script](/fields/schedulers/slurm-preemption/slurm-job-submit-lua.md#recipe-4-defuse-user-exclusive-jobs) can do exactly that, by turning `--exclusive=user` (`job_desc.shared == 2`) into plain `--exclusive`. Plain `--exclusive` did not block preemption in the tests.
- **Heterogeneous jobs** are preempted only if all components are eligible, and one component's mode (`SUSPEND` beats `REQUEUE` beats `CANCEL`) sets the mode for all.
- **Licenses are not freed by suspend.** Reclaiming them needs `REQUEUE` or `CANCEL` plus `PreemptParameters=reclaim_licenses`.
- **Plugin changes need a restart.** Changing `PriorityTier` or `OverSubscribe` only needs `scontrol reconfig`; changing preemption plugin settings needs a full restart of the daemons.

* * *

## Setting it up

Everything above assumes preemption is switched on, and it is off by default. The short version for QOS-based requeue (the full walkthrough, with a drill that proves it works, is on [its own page](/fields/schedulers/slurm-preemption/slurm-qos-preemption-setup.md)):

```text
# slurm.conf
PreemptType=preempt/qos
PreemptMode=REQUEUE
AccountingStorageEnforce=associations,qos
PreemptParameters=send_user_signal      # optional: makes --signal fire at preemption
```

```bash
sacctmgr -i add qos low
sacctmgr -i modify qos low set PreemptMode=requeue GraceTime=120 PreemptExemptTime=00:30:00
sacctmgr -i add qos high_bio
sacctmgr -i modify qos high_bio set Preempt=low
```

`Preempt=` goes on the preemptor and `PreemptMode`, `GraceTime` and `PreemptExemptTime` go on the victim. Changing `PreemptType` needs a `slurmctld` restart. If you want jobs to land in `low` or `high_<account>` without users typing the full name, a [Lua submit script](/fields/schedulers/slurm-preemption/slurm-job-submit-lua.md) does the routing.

* * *

## Version notes

The signal measurements on this page were taken on 23.11.4. Between 23.11 and 26.05 the changelogs record these preemption changes:

- **24.05:** a job signalled during `GraceTime` is assumed to have been preempted, for `PreemptMode=CANCEL` and `REQUEUE`.
- **25.05:** a new `PRIORITY` preemption option, and deleting a QOS removes it from other QOSes' preempt lists.
- **26.05:** `PreemptExemptTime` also applies to `suspend,gang` under `preempt/partition_prio`.

No changelog entry mentions the `GraceTime` signal targets or `send_user_signal`, so rerun the probe on your version. The full list is on [Version changes 23.11 to 26.05](/fields/schedulers/slurm-cluster-operations/slurm-version-changes.md#preemption).

* * *

## Cheat sheet

```
Preempt, then:    CANCEL (dead) | REQUEUE (needs --requeue) | SUSPEND (GPUs stay held)
GraceTime:        SIGCONT+SIGTERM now, SIGCONT+SIGTERM+SIGKILL at the new end time
                  -> two SIGTERMs; make the handler idempotent
                  -> tested (23.11.4): the early signal reaches srun STEPS, not the batch shell
                  -> tested: the end of the window is noticed 3 to 25 s late, then KillWait
--signal=B:USR1@N:  to the batch shell only, N seconds before the limit, up to 60 s early
                  -> at preemption only with PreemptParameters=send_user_signal (tested)
bash trap:        runs only after the foreground command ends -> background it and `wait`
Requeue =         start the script again, not resume. Your script must find the checkpoint
Logs:             --open-mode=append, or the second run erases the first
Loops:            cap with SLURM_RESTART_COUNT, require a minimum runtime
```

Preemption is not a failure of the cluster. It is a contract, and the job's side of it is a script that can be killed at any moment and still make progress.

* * *

## Back to the week-long run

Replay the Friday submission with this page open. The researcher's job runs under a preemptible QOS, and the admin has switched on `send_user_signal`. Her wrapper starts the trainer with `srun`, so it hears `SIGTERM` itself, and `--signal=B:USR1@300` warns the batch shell as well. Both handlers do the same small thing: set a flag, save at the next step boundary, exit.

On Sunday the better-funded group's job arrives. A second later the trainer is told to wrap up, and within a minute it has written a checkpoint and left. Slurm, seeing the job exit inside the grace period, treats it as preempted and puts it back in the queue (the changelog says that rule was added in 24.05 for `CANCEL` and `REQUEUE`, and a clean exit inside the window was not tested on 23.11). When a node frees up, the script runs again, finds the checkpoint, and carries on. The latest checkpoint is a minute old, not five hours.

Nobody was dramatic. "Requeue" still meant "start the script again", but this time the script knew where it had stopped.

**Takeaway:** requeue means "start the script again", so the job must catch its warning (steps hear `GraceTime`'s `SIGTERM`, the batch shell hears `--signal=B:` only with `send_user_signal`), save at a safe boundary, and find its own checkpoint on restart.

**Next:** [The Guest List](/fields/schedulers/slurm-preemption/slurm-qos-preemption-setup.md) shows how to switch preemption on and prove it works with a drill.

* * *

## References

- [Slurm: Preemption](https://slurm.schedmd.com/preempt.html)
- [Slurm: Generic Resource (GRES) Scheduling](https://slurm.schedmd.com/gres.html) (suspended jobs keep their GRES)
- [Slurm: sbatch](https://slurm.schedmd.com/sbatch.html) (`--signal`, `--requeue`, `--open-mode`)
- [CoreWeave SUNK: handling Slurm signals](https://docs.coreweave.com/products/sunk/run_workloads/handle-slurm-signals.md)
- [CoreWeave SUNK: checkpoint and restart](https://docs.coreweave.com/products/sunk/run_workloads/checkpoint-and-restart.md)
- [LRZ: handling jobs running into TIMEOUT](https://doku.lrz.de/spaces/UniARZHPCKB/pages/392035505/Handling+Jobs+running+into+TIMEOUT)
- [University of Chicago DSI: batch jobs and the checkpoint contract](https://cluster-policy.ds.uchicago.edu/using-the-cluster/batch-jobs/)