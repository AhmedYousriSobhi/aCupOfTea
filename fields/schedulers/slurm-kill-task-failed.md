---
id: slurm-kill-task-failed
title: "Kill Task Failed: A Murder Mystery With No Body (and One Drained Node)"
order: 9
sidebar_label: Kill task failed
summary: Slurm job death (SIGTERM, KillWait, SIGKILL) fails on uninterruptible sleep, draining nodes. Raising timeouts rarely helps. Debug these with UnkillableStepProgram.
level: intermediate
type: concept
domains:
  - systems-and-hpc
tags:
  - slurm
  - hpc
relations:
  related:
    - slurm-cgroups-in-practice
    - slurm-accounting-multi-tenancy
---

# Kill Task Failed: A Murder Mystery With No Body (and One Drained Node)

> **Part of the [schedulers](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-intro.md) directory.** Option names and the kill sequence come from the Slurm documentation and from support tickets and mailing-list threads where SchedMD staff and site admins describe the behavior. Nothing here was run on a live cluster for this page. Scenarios are invented for illustration.

## Table of Contents

- [Kill Task Failed: A Murder Mystery With No Body (and One Drained Node)](#kill-task-failed-a-murder-mystery-with-no-body-and-one-drained-node)
  - [Table of Contents](#table-of-contents)
  - [The call comes in at 3 a.m.](#the-call-comes-in-at-3-am)
  - [How a job is supposed to die](#how-a-job-is-supposed-to-die)
  - [Suspect 1: the process that cannot hear you](#suspect-1-the-process-that-cannot-hear-you)
  - [Suspect 2: the epilog with a temper](#suspect-2-the-epilog-with-a-temper)
  - [Why raising the timeout is mostly a delay](#why-raising-the-timeout-is-mostly-a-delay)
  - [The detective kit](#the-detective-kit)
  - [Releasing the node](#releasing-the-node)
  - [Case closed: the short version](#case-closed-the-short-version)
  - [References](#references)

* * *

## The call comes in at 3 a.m.

You run `sinfo -R` and find a node that has been quietly drained overnight:

```
REASON               USER      TIMESTAMP           NODELIST
Kill task failed     root      2026-11-04T03:12:09 gpu-node-17
```

The job is gone. The queue moved on. `slurmctld` has nothing to say, because from its point of view nothing went wrong in the controller. The node has simply declared that it can no longer be trusted, and Slurm took it at its word.

Where did the job go? That is the mystery. The honest answer is that it may not have gone anywhere. One of its processes might still be on that node, alive, deaf and dangerous.

* * *

## How a job is supposed to die

Cancelling a job, hitting a time limit, or being preempted all end in the same sequence. SchedMD staff describe it in a support ticket, and the pieces line up like this:

```mermaid
flowchart LR
    A["Cancel, time limit<br/>or preemption"] --> B["SIGCONT + SIGTERM<br/>'please wrap up'"]
    B --> C{"Wait KillWait<br/>(30 s on the sites I read)"}
    C --> D["SIGKILL<br/>'no, really'"]
    D --> E{"Wait UnkillableStepTimeout"}
    E -->|processes gone| F["Job ends, node carries on"]
    E -->|something survived| G["Step terminated:<br/>node set to DRAIN<br/>'Kill task failed'"]
```

Two timers, two different questions:

| Timer | Question it answers | Seen in practice |
|---|---|---|
| `KillWait` | How long do we wait between the polite request and `SIGKILL`? | 30 seconds on the clusters in the threads I read |
| `UnkillableStepTimeout` | After `SIGKILL`, how long before we decide a process is unkillable? | 60 seconds in older threads; one site on 25.05 shows 300 |

Defaults have moved between versions and many sites change them, so ask your own cluster:

```bash
scontrol show config | grep -Ei 'killwait|unkillable'
```

The `slurmstepd` log line you are looking for says the step was terminated "due to job not ending with signals". That is the node reporting, in a slightly Victorian tone, that it sent the signals and nothing happened.

* * *

## Suspect 1: the process that cannot hear you

`SIGKILL` cannot be caught, blocked or ignored. It can, however, be *postponed*. A process in uninterruptible sleep (state `D` in `ps`) is waiting for the kernel to finish something, usually I/O, and the kernel will not deliver a fatal signal until that wait ends.

The usual accomplice is a network or parallel filesystem having a bad night. Admins in the mailing-list threads blame laggy storage again and again, and one thread adds a useful detail: the I/O may complete *after* Slurm drained the node, leaving a perfectly clean machine wearing a drain flag.

One support ticket even includes the kernel's own confession in the node log, a line saying a task had been blocked for more than 362 seconds. That kind of message in `dmesg` or the journal is your best evidence that the suspect was stuck in a system call.

A few things this implies:

- **It is rarely the job's fault.** A user cancelling a healthy job on a sick filesystem is enough.
- **Mass cancels amplify it.** One thread describes a workflow tool that stops a run by cancelling many jobs at once, and nodes drain in batches, presumably because they all hit the same stalled mount at the same moment.
- **Not every case is storage.** One admin in the threads reports the same drain on a site with no Lustre at all. Treat "storage" as the leading suspect, not the only one.

> [!NOTE]
> Slurm's own reasoning, as one list reply puts it, is a heuristic: if a process could not be killed, something is wrong with the node, so keep new jobs away until a human looks.

* * *

## Suspect 2: the epilog with a temper

There is a second way to get a drained node after a job ends, and it looks similar from the outside. Slurm's Prolog and Epilog guide says that if the **Epilog exits with a non-zero code, the node is set to DRAIN**. A site epilog that checks for leftover GPU processes, full scratch space or stale mounts will drain a node the moment its check fails, which is its job.

So when you see a drained node after a job, check which story it is:

| Clue | Likely cause |
|---|---|
| Reason says "Kill task failed" | A step process survived `SIGKILL` for `UnkillableStepTimeout` seconds |
| `slurmd` log shows the epilog finishing with an error | Your epilog returned non-zero |
| `dmesg` shows hung-task warnings | The kernel was already unhappy before Slurm noticed |

The epilog also runs **outside** the job's cgroup, which matters if your check looks at device numbers. [The cgroups page](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-cgroups-in-practice.md) and the [GPU affinity page](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-gpu-affinity-socket-lie.md) explain how the same GPU can have different numbers inside and outside.

* * *

## Why raising the timeout is mostly a delay

The obvious fix is to raise `UnkillableStepTimeout`. SchedMD's own troubleshooting guide suggests it for nodes stuck in COMPLETING, so it is a legitimate tool. But admins report the limits of it:

- One admin who tried it says it mostly prolonged the time before the failure.
- A site with the timeout at 180 seconds still reports drains several times a day.
- Another thread has a user cancelling a job at 120 seconds and still getting a drained node.

The reasoning is simple. If the storage is down for ten minutes, a three-minute timeout drains the node and a nine-minute timeout does too, just later. A longer timeout helps only when the stall is shorter than the new value.

Also, the drained node does not undrain itself. A list reply is explicit that even when the job finally terminates, the node is **not** resumed. Somebody has to do that.

* * *

## The detective kit

`UnkillableStepProgram` runs a script of your choosing when a step is unkillable. Admins in the threads recommend it as a debugging tool, and it is the best thing you can do for your future self, because it captures the scene while the body is still warm.

A sketch of what such a script might gather. This is a suggestion, not a Slurm-provided script, so test it before relying on it:

```bash
#!/bin/bash
# UnkillableStepProgram sketch: record evidence, change nothing.
OUT=/var/log/slurm/unkillable.$(hostname).$(date +%s)
{
  echo "== job info =="; env | grep -E '^SLURM_' | sort
  echo "== processes in D state =="
  ps -eo pid,ppid,user,stat,wchan:32,etime,cmd | awk '$4 ~ /^D/'
  echo "== kernel hung-task messages =="
  dmesg -T | grep -i 'blocked for more than' | tail -20
  echo "== mounts that might be unhappy =="
  mount | grep -E 'nfs|lustre|beegfs|gpfs'
} > "$OUT" 2>&1
```

Set it in `slurm.conf`:

```
UnkillableStepProgram=/etc/slurm/unkillable.sh
```

Two more habits from the threads: check core-file locations around the timestamp in the reason, and keep a cron job that emails you the `Reason` of every newly drained node, so the 3 a.m. discovery becomes a 9 a.m. one.

* * *

## Releasing the node

First make sure the culprit is really gone. If it is, return the node to service:

```bash
# is anything still in D state?
ps -eo pid,user,stat,wchan:32,cmd | awk '$3 ~ /^D/'

# the node looks clean; put it back
scontrol update NodeName=gpu-node-17 State=RESUME
```

If processes are still stuck, resuming just feeds the next job to the same problem. At that point the options are fixing the filesystem path, rebooting the node (see the [reboot order page](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-reboot-order.md)), or both.

* * *

## Case closed: the short version

```
cancel -> SIGTERM -> [KillWait] -> SIGKILL -> [UnkillableStepTimeout] -> DRAIN
                                      ^
            a process in D state cannot receive it until the kernel lets go

Longer timeouts delay the verdict. They do not fix the storage.
UnkillableStepProgram is how you find out who the victim was.
A drained node stays drained until a human says otherwise.
```

The culprit is nearly always not the job, not Slurm, but a kernel call waiting on something that is not answering.

* * *

## References

- [SchedMD ticket 14265: job not ending with signals (KillWait and UnkillableStepTimeout)](https://support.schedmd.com/show_bug.cgi?id=14265)
- [SchedMD ticket 11103: unkillable step and the hung-task kernel message](https://support.schedmd.com/show_bug.cgi?id=11103)
- [SchedMD ticket 22425: how to update UnkillableStepTimeout](https://support.schedmd.com/show_bug.cgi?id=22425)
- [slurm-users: nodes going into drain because of "Kill task failed" (2020)](https://lists.schedmd.com/pipermail/slurm-users/2020-July/005820.html)
- [slurm-users: Kill task failed, UnkillableStepTimeout=120 (2020)](https://lists.schedmd.com/pipermail/slurm-users/2020-November/006433.html)
- [slurm-users: the I/O may complete after the drain (2025)](https://lists.schedmd.com/mailman3/hyperkitty/list/slurm-users@lists.schedmd.com/message/34FZZN2LUJL26TMZR5PJDB3LWFICP56G/)
- [Slurm: Prolog and Epilog Guide](https://slurm.schedmd.com/prolog_epilog.html) (epilog failure drains the node, as quoted in the 2020 thread)