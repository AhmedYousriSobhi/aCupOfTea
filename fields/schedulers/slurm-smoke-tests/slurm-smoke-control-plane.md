---
id: slurm-smoke-control-plane
title: "The Cluster That Worked Perfectly and Remembered Nothing: a Two-Minute Slurm Smoke Test"
order: 1
sidebar_label: Control-plane smoke test
summary: "A six-check, two-minute Slurm smoke test (MUNGE, controller, nodes, srun, sbatch, sacct) as one script with three outcomes, tested against four injected failures and a busy cluster."
level: beginner
type: guide
domains:
  - systems-and-hpc
tags:
  - slurm
  - hpc
relations:
  related:
    - slurm-smoke-config-change
    - slurm-smoke-after-upgrade
    - slurm-sacct-job-forensics
    - slurm-pending-reasons
    - slurm-job-submit-lua
---

# The Cluster That Worked Perfectly and Remembered Nothing: a Two-Minute Slurm Smoke Test

> **Part 1 of [Slurm Smoke Tests](/fields/schedulers/slurm-smoke-tests/README.md).** Every command, script and output here was run on a two-node test cluster (Slurm 23.11.4, accounting on, both `slurmd` daemons on one Ubuntu 24.04 machine), including the failures, which were injected on purpose. The node names, users and the story are invented. SchedMD does not define a "smoke test", so the checks below are a synthesis of what its [admin](https://slurm.schedmd.com/quickstart_admin.html), [troubleshooting](https://slurm.schedmd.com/troubleshoot.html) and [upgrade](https://slurm.schedmd.com/upgrades.html) guides tell you to verify, in one script.

## Table of Contents

- [The Cluster That Worked Perfectly and Remembered Nothing: a Two-Minute Slurm Smoke Test](#the-cluster-that-worked-perfectly-and-remembered-nothing-a-two-minute-slurm-smoke-test)
  - [Table of Contents](#table-of-contents)
  - [The cluster that remembered nothing](#the-cluster-that-remembered-nothing)
  - [What a smoke test is, and is not](#what-a-smoke-test-is-and-is-not)
  - [The script](#the-script)
  - [Break it on purpose](#break-it-on-purpose)
  - [When the cluster is just busy](#when-the-cluster-is-just-busy)
  - [Things that make a healthy cluster fail](#things-that-make-a-healthy-cluster-fail)
  - [Where to run it](#where-to-run-it)
  - [Version notes](#version-notes)
  - [Back to the cluster that remembered nothing](#back-to-the-cluster-that-remembered-nothing)
  - [References](#references)

---

## The cluster that remembered nothing

On Friday at five to five, Tarek restarts the Slurm controller after a small change. He runs `sinfo`, sees a tidy table with every node `idle`, and goes home.

On Monday the finance office asks why the weekend's usage report is empty. Researchers say their jobs ran fine. They did: for three days the cluster ran every job it was given and recorded none of them, because the accounting daemon had not come back with the controller. Nothing was broken in the way anybody was looking. `sinfo` was right. `squeue` was right. The only thing wrong was the part that nobody checks until someone needs the numbers.

A smoke test is the habit that would have caught it in two minutes on Friday. It is a short list of things that must all work for the cluster to be useful, run every time something changes. Its name comes from electronics: plug the board in, and if smoke comes out, stop.

---

## What a smoke test is, and is not

A smoke test answers one question: **is it basically working?** It does not measure performance, it does not test every option, and it does not replace a regression suite (that is [part 6](/fields/schedulers/slurm-smoke-tests/slurm-smoke-regression-suites.md)). It earns its place by being cheap enough to run every time and by covering every layer a job passes through.

| Layer | What it proves | The check |
|---|---|---|
| Authentication | This host can make and read a MUNGE credential | `munge -n \| unmunge` |
| Controller | `slurmctld` answers | `scontrol ping` |
| Nodes | No node is down, drained or silent | `sinfo` states |
| Launching | A task really starts on every node | `srun` across all nodes |
| Batch path | A script is accepted, scheduled, run, and writes output | `sbatch` and a wait |
| Accounting | The database recorded what ran | `sacct` for that job |

Each layer can fail while the one above it looks fine. Tarek's morning is the last row failing alone.

---

## The script

It runs as an ordinary user, not as root, because that is how real jobs arrive: through the same submit rules and the same associations. It uses the commands the Slurm guides mention, `scontrol ping` and `srun` across nodes, plus `sbatch` and `sacct`, which the upgrade guide names as the way to validate "communication with nodes and a job's ability to successfully start and finish".

The script is [`slurm-smoke.sh`](/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-smoke.sh), a plain file you can read on this site, [open on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-smoke.sh) or fetch with its [raw link](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-smoke.sh).

On the healthy test cluster it finished in one second:

```text
PASS  munge    credential encoded and decoded
PASS  ping     Slurmctld(primary) at vm is UP
PASS  nodes    2 node(s), none down or drained
PASS  srun     2 of 2 nodes answered
PASS  sbatch   job 85 ran and wrote its output
PASS  sacct    job 85 recorded as COMPLETED
ALL PASS
```

A few choices in the script matter:

- **`$SLURMD_NODENAME`, not `hostname`.** It is the name Slurm uses for the node. On the test cluster both nodes live on one machine, so `hostname` printed the same name twice and the check failed on a healthy cluster. It is also immune to fully qualified names that differ from the node name.
- **`--immediate`.** A smoke test must not sit in the queue behind real work. With `--immediate`, `srun` gives up with a clear message instead of waiting.
- **Cleanup.** The script cancels its own jobs on exit. The first version used `sbatch --wait` under `timeout`, and a timed-out run left a job pending in the queue.

---

## Break it on purpose

A check you have never seen fail is a check you do not know works. Four failures were injected, one at a time, on the test cluster. The script ran as an ordinary user with a 15-second limit per step.

| Injected failure | What the script printed | Which check caught it |
|---|---|---|
| `slurmd` on `node2` killed | `FAIL srun rc=233: srun: error: Task launch for StepId=92.0 failed on node node2: Communication connection failure` | `srun` only. The `nodes` check **passed**, because the controller had not noticed yet |
| `slurmdbd` stopped | `PASS sbatch job 101 ran and wrote its output`, then `FAIL sacct job 101 in the database: 'nothing'` | `sacct` only. Jobs kept running; `srun` alone worked too |
| `slurmctld` stopped | `FAIL ping Slurmctld(primary) at vm is DOWN`, `FAIL nodes sinfo: slurm_load_partitions: Unable to contact slurm controller (connect failure)`, `FAIL sbatch submit refused: ...` | Three checks at once |
| `node2` drained | `FAIL nodes node2 drained;` | `nodes`. The batch job still passed, because it needed only one node |

Two lessons come straight from the table. A dead `slurmd` is invisible to `sinfo` until the controller's own timeout notices it (`SlurmdTimeout`), so launching a task on every node is the only check that finds it quickly. And a stopped `slurmdbd` is Tarek's Friday: everything works except the record. Only the last row of the script sees it.

---

## When the cluster is just busy

The first version of the script treated every pending job as a failure, and a smoke test that cries wolf gets switched off. With both nodes occupied by a large job, the final script reports:

```text
PASS  munge    credential encoded and decoded
PASS  ping     Slurmctld(primary) at vm is UP
PASS  nodes    2 node(s), none down or drained
WAIT  srun     cluster is busy: Unable to allocate resources: Requested nodes are busy
WAIT  sbatch   job 91 still pending after 15s (Resources)
INCONCLUSIVE (cluster busy, nothing failed)
```

That is exit status 2, a third outcome next to pass and fail, and it means "I could not tell". It deserves its own colour on a dashboard. Two cautions from the tests:

- **A dead node can look busy.** After a killed `slurmd`, the batch job sat pending with the reason `Resources`, the same text a full cluster shows. The `FAIL` from `srun` outranked it, but a `WAIT` on its own is not proof of health.
- **A drained node reads as busy to `srun`.** In the drained run, `srun` reported "Requested nodes are busy", while the `nodes` check printed the real cause. Read the whole report, not one line.

Run on a quiet partition, or give the smoke test its own lane (a canary partition, which [part 2](/fields/schedulers/slurm-smoke-tests/slurm-smoke-config-change.md) builds), and `WAIT` becomes rare.

---

## Things that make a healthy cluster fail

Real causes of false failures, all seen during these tests:

| Symptom | Cause | Fix |
|---|---|---|
| `sbatch: error: Please set --time, jobs without one are not accepted` | A [submit script](/fields/schedulers/slurm-preemption/slurm-job-submit-lua.md) requires a time limit, and the test job had none | Give the test job `-t`. The script's `SMOKE_TIME` does this |
| Job `FAILED` with `ExitCode 0:53`, log says `Slurmd could not connect IO` | The submission directory was not writable by the user, so the output file could not be created | Run from a writable directory, or give `-o` a path that is writable. The script uses a temporary directory |
| A `WAIT` or odd result right after a restart | Probably nodes still settling after the daemons came back: a run two seconds after a restart reported `Requested nodes are busy`, and a run six seconds after did not. The cause was not isolated | Wait several seconds after a restart before the check |
| `sacct` empty for a job that finished | The database daemon is down, or accounting is not enabled on this cluster | That is exactly what check 6 is for. On a cluster without accounting, leave it out |

---

## Where to run it

- **After every change:** a restart, a reconfigure, an upgrade, a node coming back. [Part 2](/fields/schedulers/slurm-smoke-tests/slurm-smoke-config-change.md) and [part 3](/fields/schedulers/slurm-smoke-tests/slurm-smoke-after-upgrade.md) cover the two big cases.
- **On a schedule:** every few minutes from a login node, as a canary, with the result sent to your monitoring. The script's exit status is the signal. Watch the cost: each run submits a real job, so a one-minute check on a large cluster is a job per minute.
- **Not as root.** Root bypasses the rules a user meets, which is where many failures live.

---

## Version notes

Everything above ran on Slurm 23.11.4. `sacctmgr ping` appeared in 24.11 and queries the status of `slurmdbd` directly, so on newer clusters it makes a cheaper accounting check than a full job. Whether it replaces the `sacct` round trip is a judgment: it proves the daemon answers, while the `sacct` check proves a job was recorded. The [version-changes page](/fields/schedulers/slurm-cluster-operations/slurm-version-changes.md) lists what else moved.

---

## Back to the cluster that remembered nothing

Replay Friday at five to five. Tarek restarts the controller and runs the script. Munge, ping and the nodes pass. The `srun` and `sbatch` lines pass. Then the last line:

```text
FAIL  sacct    job 101 in the database: 'nothing'
```

It takes two minutes, and he has not left his desk. He starts `slurmdbd`, reruns the script, reads `ALL PASS`, and goes home. On Monday the report has three days of usage in it, not zero.

Nothing about this required cleverness. It required one more command than `sinfo`, run by someone who knew that "the table looks fine" and "the cluster works" are different statements.

**Takeaway:** a smoke test checks every layer a job passes through (MUNGE, controller, nodes, launching, batch, accounting), runs as an ordinary user after every change, and has three outcomes (pass, fail, inconclusive-because-busy), because each layer can fail while the one above it looks fine.

**Next:** [Measure Twice, Reconfigure Once](/fields/schedulers/slurm-smoke-tests/slurm-smoke-config-change.md) is what to do before you change `slurm.conf`, so the smoke test above has nothing to find.

---

## References

- [Slurm: Quick Start Administrator Guide](https://slurm.schedmd.com/quickstart_admin.html) (`-D -v`, `srun -N1 /bin/hostname`, `scontrol ping`)
- [Slurm: Troubleshooting Guide](https://slurm.schedmd.com/troubleshoot.html) (`scontrol ping`, `scontrol show node`, `scontrol show slurmd`)
- [Slurm: Upgrade Guide](https://slurm.schedmd.com/upgrades.html) (step 8, "Test key functionality")
- [Slurm: srun](https://slurm.schedmd.com/srun.html) (`--immediate`)
- [Slurm: sacct](https://slurm.schedmd.com/sacct.html)
