---
id: slurm-signals-cheatsheet
title: "Who Gets Told What: Every Signal Slurm Sends, and Who Actually Hears It"
order: 16
sidebar_label: Signals cheat sheet
summary: Which signals Slurm sends at preemption, GraceTime, --signal, time limits and scancel, whether the batch shell or the srun steps receive them, and how late they really arrive.
level: intermediate
type: reference
domains:
  - systems-and-hpc
tags:
  - slurm
  - hpc
relations:
  related:
    - slurm-preemption-requeue-signals
    - slurm-kill-task-failed
    - slurm-slurmstepd
    - slurm-qos-preemption-setup
---

# Who Gets Told What: Every Signal Slurm Sends, and Who Actually Hears It

> **Part of the [schedulers](/fields/schedulers/slurm-intro.md) directory.** The timings below were measured on a two-node test cluster (Slurm 23.11.4, `KillWait=30`, accounting on, both `slurmd` daemons on one Ubuntu 24.04 machine), with a probe script that logged every signal it received and ignored `SIGTERM` on purpose, so the kill deadline could be seen. Each number is one run, so read them as a shape and not as a specification. Another Slurm version may behave differently, and the [preemption page](/fields/schedulers/slurm-preemption-requeue-signals.md) quotes the newer 26.05 guide. Run the probe in [Measure it yourself](#measure-it-yourself) on your own cluster.

## Table of Contents

- [Who Gets Told What: Every Signal Slurm Sends, and Who Actually Hears It](#who-gets-told-what-every-signal-slurm-sends-and-who-actually-hears-it)
  - [Table of Contents](#table-of-contents)
  - [The message that went to the wrong address](#the-message-that-went-to-the-wrong-address)
  - [Two kinds of listeners](#two-kinds-of-listeners)
  - [Who sends what, and to whom](#who-sends-what-and-to-whom)
  - [The timelines](#the-timelines)
  - [Everything arrives late (and sometimes early)](#everything-arrives-late-and-sometimes-early)
  - [Which design to choose](#which-design-to-choose)
  - [Measure it yourself](#measure-it-yourself)
  - [Cheat sheet](#cheat-sheet)
  - [Version notes](#version-notes)
  - [Back to Ana's Saturday night](#back-to-anas-saturday-night)
  - [References](#references)

---

## The message that went to the wrong address

Ana has done everything the [preemption page](/fields/schedulers/slurm-preemption-requeue-signals.md) asked. Her batch script traps `SIGTERM`, runs the trainer in the background, and waits. Her admin has set a two-minute `GraceTime` on the cluster. On Saturday night her job is preempted, and she reads the log on Sunday expecting a calm "caught signal, checkpoint saved".

The log says nothing at all until the very last second, when everything dies at once. The checkpoint is a day old.

The signal was sent. It simply went to a different address. A Slurm job has two kinds of listeners, and the early warning was addressed to the one Ana was not.

---

## Two kinds of listeners

| Listener | What it is | Example |
|---|---|---|
| **The batch shell** | The `bash` process running your `sbatch` script | The wrapper with the `trap` |
| **The steps** | Anything launched with `srun` inside the job | `srun python train.py` |

The difference is easy to miss, because a command in your script that is *not* behind `srun` is not a step at all. It is a child of the batch shell:

```bash
python train.py          # child of the batch shell: not a step
srun python train.py     # a job step: a different listener
```

Almost every signal in this page is addressed to one listener or the other. That is the whole mystery.

---

## Who sends what, and to whom

| Event | Signal | Batch shell | srun steps |
|---|---|---|---|
| Preemption begins, `GraceTime` > 0 | `SIGCONT` + `SIGTERM` | **No** (measured) | Yes, about 1 s later |
| Preemption begins, `GraceTime` = 0 | `SIGCONT` + `SIGTERM` | Yes | Yes |
| End of grace, time limit, or `scancel` of the job | `SIGCONT` + `SIGTERM`, then after `KillWait`, `SIGKILL` | Yes | Yes |
| `--signal=B:USR1@N` near the time limit | `USR1` | Yes | No |
| `--signal=USR1@N` (no `B:`) near the time limit | `USR1` | No | Yes |
| Preemption begins with `PreemptParameters=send_user_signal` and a `--signal` | The `--signal` signal, at once | Yes if `B:` | Yes if no `B:` |
| `scancel -s USR1 <job>` | `USR1` | No | Yes |
| `scancel -s USR1 --batch <job>` | `USR1` | Yes | No |

Measured on the test cluster: the preemption rows, the kill sequence, `--signal=B:` (both near the time limit and with `send_user_signal`) and the two `scancel` rows. Not measured: the `--signal` row without `B:` and the step half of the `send_user_signal` row, which follow the `sbatch` documentation, where a signal without `B:` goes to the job steps rather than the batch script. `scancel --full` is described in its man page as signalling the batch script and its children. In one test, a `SIGCONT` sent with it was reported only by the batch shell, so test it before relying on it.

---

## The timelines

Each timeline starts when the preempting job is submitted (`t = 0`). The victim's probe logged the signals, and ignored `SIGTERM`, so it had to be killed.

**GraceTime = 0.** There is no grace period, but a job that ignores `SIGTERM` still gets `KillWait` before `SIGKILL`:

```text
t =  0.6 s   batch shell:  SIGCONT, SIGTERM
t =  0.6 s   srun step:    SIGTERM (twice), SIGCONT
t = 33.7 s   preemptor starts (the victim had to be killed: ignored SIGTERM + KillWait 30 s)
```

**GraceTime = 30, trainer under `srun`.** The step is warned at the start, everybody is told at the end:

```text
t =  0.9 s   srun step:    SIGTERM, SIGCONT            <- the early warning
t = 54.9 s   batch shell:  SIGCONT, SIGTERM            <- end of grace, noticed late
t = 54.9 s   srun step:    SIGTERM (twice more), SIGCONT
t = 87.5 s   preemptor starts (ignored SIGTERM + KillWait)
```

**GraceTime = 30, trainer in the batch shell only.** No early warning exists for it:

```text
t =  0      (nothing)
t = 41.3 s   batch shell:  SIGCONT, SIGTERM            <- the only message
t = 71.2 s   preemptor starts
```

**GraceTime = 60 with `--signal=B:USR1@300`, without and with `PreemptParameters=send_user_signal`:**

```text
without:  t =  0      (nothing)
          t = 64.0 s   batch shell: SIGCONT, SIGTERM
with:     t =  1.0 s   batch shell: USR1, SIGCONT     <- prompt warning
          t = 83.0 s   batch shell: SIGCONT, SIGTERM
```

Without `send_user_signal`, the `USR1` never fired at preemption, even though the grace period (60 s) was shorter than the 300 s lead time asked for. The idea that `--signal` might fire at preemption anyway, because preemption moves the job's end time closer, did not hold in this version.

---

## Everything arrives late (and sometimes early)

Slurm checks time limits and grace windows on a periodic tick in the controller, not on a stopwatch:

| What | Asked for | Observed |
|---|---|---|
| End of a 30 s grace window | 30 s | noticed at 41 s and at 55 s (two runs); at about 33 s in an earlier run |
| End of a 60 s grace window | 60 s | noticed at 64 s and at 83 s (two runs) |
| `--signal=B:USR1@90` on a 120 s job | 90 s before the end | arrived at 68 s: **52 s** before the end |
| The 120 s time limit itself | 120 s | `TERM` at 146 s; `sacct` showed `TIMEOUT` and `Elapsed 00:02:26` |
| `SIGKILL` after `SIGTERM` | `KillWait` = 30 s | the preemptor started 30 s after the second `SIGTERM` |

Two lessons. The lead time in `--signal` is a target, not a promise: the `sbatch` documentation says the signal can come up to 60 seconds early, and in this test it came about 38 seconds late. And the grace window is `GraceTime` plus a few to 25 extra seconds on this cluster, so size your checkpoint with room on both sides.

A job that exits quickly on the first `SIGTERM` makes all of this moot: the preemptor starts as soon as the victim is gone.

---

## Which design to choose

| Where does the trainer run? | Early warning you get | What to do |
|---|---|---|
| `srun python train.py` (a step) | `SIGTERM` + `SIGCONT` about 1 s after preemption begins, if `GraceTime` > 0 | Let the trainer handle `SIGTERM`: set a flag, checkpoint at a safe boundary, exit |
| `python train.py &` in the batch script | None from `GraceTime` | Set `PreemptParameters=send_user_signal` and `#SBATCH --signal=B:USR1@N`, and trap `USR1` in the script. Otherwise you hear only at the end of the window |
| Anywhere | Always the final `SIGTERM` | Trap `TERM` too. It arrives more than once for steps, so make the handler idempotent |

Whichever you pick, do not write the checkpoint inside the signal handler. Set a flag, return, and let the training loop save at a step boundary.

---

## Measure it yourself

Because versions differ, thirty minutes with a probe beats a week of guessing. A job script that logs every signal with a timestamp:

```bash
#!/bin/bash
# probe.sh: logs the signals it receives, then carries on
for s in TERM CONT USR1 USR2; do
    trap "echo \"BATCH_GOT_$s \$(date +%s.%N)\"" $s
done
echo "BATCH_START $(date +%s.%N)"
while true; do sleep 1; done
```

Submit it as the victim (`--exclusive`, requeueable, on a node you can spare), land a preemptor on the same node, and subtract the preemptor's submit time from each logged time. For the step case, put the same traps in a second script and start it with `srun script.sh &` followed by `wait`. Repeat with `GraceTime` at 0 and at 30, with and without `--signal` and `send_user_signal`. The same probe tells you what your version does.

---

## Cheat sheet

```text
Two listeners:    batch shell (your script)   vs   steps (things behind srun)
Early SIGTERM:    GraceTime > 0 -> to srun STEPS at once, NOT to the batch shell (23.11.4)
End of grace:     SIGCONT+SIGTERM to everyone; then KillWait -> SIGKILL
Batch shell warn: --signal=B:USR1@N  +  PreemptParameters=send_user_signal (else only at the end)
Timing:           ticks, not stopwatches; grace +3..+25 s, --signal can be late (52 s, not 90 s)
scancel -s SIG:   steps by default; --batch for the shell
Handler rules:    set a flag, never save inside the handler, make it idempotent
Don't guess:      run probe.sh with your GraceTime and your version
```

Signals are letters with an address on them. Half of the debugging is checking whether the address was the shell or the step.

---

## Version notes

Every timing above is from 23.11.4. The changelogs add: a default `UnkillableStepTimeout` of 60 s (24.05); `SIGKILL` through the `cgroup.kill` interface (25.05); and in 26.05 "KillWait will be honored when the task does not end with the TERM signal", `srun --ignore-signals`, and no delay in cancelling a job while `slurmstepd` is launching a task. The `KillWait` line concerns exactly the case measured here, so rerun the probe first. [Version changes 23.11 to 26.05](/fields/schedulers/slurm-version-changes.md#signals-and-killing-jobs) has the list.

---

## Back to Ana's Saturday night

With this page in hand, Ana changes one line: the wrapper starts the trainer with `srun`, so the trainer is a step and receives the early `SIGTERM` itself. Her admin also sets `PreemptParameters=send_user_signal`, and she adds `--signal=B:USR1@120`, so the batch shell is warned too. Both handlers do the same thing: set a flag, checkpoint at the next step boundary, exit.

Next Saturday the job is preempted again. This time the log has a calm line about a caught signal, a checkpoint that is two minutes old, and a requeue. The message had not been lost on the way to her; it had just been addressed to a step.

**Takeaway:** a job has two listeners, the batch shell and the `srun` steps; the early `GraceTime` warning goes to the steps, the `--signal=B:` warning goes to the shell (and only at preemption with `send_user_signal`), and every timing is a tick, so budget for lateness.

**Next:** back to [Dying Politely](/fields/schedulers/slurm-preemption-requeue-signals.md) for the checkpoint-and-requeue wrapper that these signals feed.

---

## References

- [Slurm: Preemption](https://slurm.schedmd.com/preempt.html) (`GraceTime`, signals at preemption)
- [Slurm: sbatch](https://slurm.schedmd.com/sbatch.html) (`--signal`, `B:`)
- [Slurm: scancel](https://slurm.schedmd.com/scancel.html) (`--signal`, `--batch`, `--full`)
- [Slurm: slurm.conf](https://slurm.schedmd.com/slurm.conf.html) (`KillWait`, `PreemptParameters`)
