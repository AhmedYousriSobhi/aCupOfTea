---
id: slurm-smoke-policy
title: "Does the Rulebook Still Work? Smoke-Testing QOS, Submit Rules and Preemption"
order: 4
sidebar_label: Policy and preemption
summary: "A two-stage smoke test for QOS, submit rules and preemption: routing and refusals with no resources, then a real eviction and requeue, with a full script and its output."
level: intermediate
type: guide
domains:
  - systems-and-hpc
tags:
  - slurm
  - hpc
relations:
  prerequisites:
    - slurm-smoke-control-plane
  related:
    - slurm-qos-preemption-setup
    - slurm-job-submit-lua
    - slurm-preemption-requeue-signals
    - slurm-signals-cheatsheet
    - slurm-smoke-config-change
---

# Does the Rulebook Still Work? Smoke-Testing QOS, Submit Rules and Preemption

> **Part 4 of [Slurm Smoke Tests](/fields/schedulers/slurm-smoke-tests/README.md).** The script and every output below were run on a two-node test cluster (Slurm 23.11.4, accounting on, QOS preemption with requeue, a `job_submit.lua` that routes and refuses jobs, both `slurmd` daemons on one Ubuntu 24.04 machine). The accounts, users and the story are invented. The policy under test is the one built in [The Guest List](/fields/schedulers/slurm-preemption/slurm-qos-preemption-setup.md) and [The Receptionist Who Rewrites Your Badge](/fields/schedulers/slurm-preemption/slurm-job-submit-lua.md). Read the [control-plane smoke test](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md) first.

## Table of Contents

- [Does the Rulebook Still Work? Smoke-Testing QOS, Submit Rules and Preemption](#does-the-rulebook-still-work-smoke-testing-qos-submit-rules-and-preemption)
  - [Table of Contents](#table-of-contents)
  - [The monitor that was refused](#the-monitor-that-was-refused)
  - [Why policy needs its own test](#why-policy-needs-its-own-test)
  - [The script](#the-script)
  - [What each check proves](#what-each-check-proves)
  - [Things the drill showed](#things-the-drill-showed)
  - [When to run it](#when-to-run-it)
  - [Version notes](#version-notes)
  - [Back to the monitor that was refused](#back-to-the-monitor-that-was-refused)
  - [References](#references)

---

## The monitor that was refused

On Wednesday, Omar adds a rule to the submit script: every job must say how long it will run. It is a good rule. The backfill scheduler works better with honest time limits, and the nodes stop filling with week-long jobs nobody meant.

For two days nothing seems different. Then a researcher asks why the cluster's "is it up?" page has shown green since Wednesday morning. The page is fed by a cron job that submits a one-minute test job every five minutes. Since Wednesday, every one of those submissions has been refused with "Please set --time". The cron script printed the error into a mail spool nobody reads, and the last good result stayed on the page.

The monitor was the first casualty of the new rule, and nothing noticed, because the monitor was the thing that was supposed to notice. A smoke test for policy has two jobs: check that the rules do what they should, and be a user who is subject to them.

---

## Why policy needs its own test

QOS tiers, account limits, a Lua submit script and preemption settings are all rules, and rules change quietly. Someone edits a QOS on Tuesday. A Lua file is replaced on Wednesday. An upgrade changes a default. None of that touches the control plane, so [the six-check smoke test](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md) stays green while the policy is wrong.

The test has two stages. The first uses no resources at all: held jobs and a dry run. The second stages a real eviction, because "the rule says high beats low" and "a high job really evicted a low one and the low one came back" are different statements.

---

## The script

It runs as an ordinary user who belongs to the test account and may use the low QOS and the high QOS for that account. It picks an idle node on its own, cancels everything it submitted on exit, and exits non-zero on any failure.

The script is [`slurm-policy-smoke.sh`](/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-policy-smoke.sh), a plain file you can read on this site, [open on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-policy-smoke.sh) or fetch with its [raw link](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-policy-smoke.sh).

Its result on the test cluster:

```text
== Stage 1: routing and rules (no resources used)
  PASS  no --qos becomes low
  PASS  --qos=high becomes high_physics
  PASS  a job without --time is refused
== Stage 2: a high job evicts a low job on node node1
  PASS  low job 114 running (qos low)
  PASS  high job 115 got the node (qos high_physics)
  PASS  low job was requeued (Restarts=1)
  PASS  low job restarted once the high job finished
  log:
    START restart=0 08:09:43
    slurmstepd-node1: error: *** JOB 114 ON node1 CANCELLED AT 2026-11-13T08:10:37 DUE TO PREEMPTION ***
    START restart=1 08:13:08
== 7 passed, 0 failed
```

The whole run took three minutes and twenty-six seconds, nearly all of it in stage 2. The log tells the story in three lines: the low job started, was cancelled "due to preemption" about 50 seconds after the high job arrived (`GraceTime` was 30 seconds, plus the controller's own tick), and started again with `restart=1`. The same job had been put back in the queue.

---

## What each check proves

| Check | If it fails, then |
|---|---|
| `no --qos becomes low` | The submit script is not loaded, is broken, or the default routing changed. Users are now landing in the wrong tier |
| `--qos=high becomes high_<account>` | Routing for the preemptor broke. High jobs will be refused, or will run without preempting anything |
| `a job without --time is refused` | The time-limit rule is off. (The test passes when the job is *refused*) |
| `high job got the node` | The preemptor never started: `PreemptType`, `PreemptMode` or the QOS `Preempt=` list is wrong |
| `low job was requeued` | The victim was cancelled, not requeued: the QOS victim mode, `JobRequeue` or `--requeue` is wrong |
| `low job restarted` | The requeued job never came back: it is stuck pending, or held |

Two more things the script cannot see. It does not look at the *signals* the victim received, because that depends on whether the job is a batch shell or an `srun` step, and the timings are the subject of the [signals cheat sheet](/fields/schedulers/slurm-preemption/slurm-signals-cheatsheet.md). And it does not test that a real job's checkpoint is valid: it can prove a job was evicted and restarted, not that it resumed correctly. That needs a drill with your own workload.

---

## Things the drill showed

- **The victim restarted late.** The preempted job was put back in the queue at once, but it did not start again until 08:13:08, about two and a half minutes after it was cancelled, long after the high job's 15 seconds were done. The cause was not investigated, and the script's `WAIT` of 150 seconds was only just enough. If you test with a tight limit, a correct policy can look like a failure.
- **A test job without `--time` is refused.** That is Omar's story, and it happened on the test cluster: the first version of the [part 1 script](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md) failed with `Please set --time, jobs without one are not accepted` until it was given `-t`. An earlier version of this drill, read against the same rule, would be refused the same way (it was not rerun). The version above passes `-t` everywhere.
- **Where the eviction lands.** The script pins both jobs to one idle node with `--exclusive`, so the high job should only evict the low job the script itself started a moment earlier. It would still be better to run it on a canary partition (see [part 2](/fields/schedulers/slurm-smoke-tests/slurm-smoke-config-change.md#rung-3-a-canary-lane)), where a real user's low job can never be the victim.
- **A user with no account was not tested here.** The routing check should also be run by hand for a user with no default account: asking for `--qos=high` should produce a clear refusal.

---

## When to run it

Run stage 1 whenever anything near the rules changes: a QOS edit, a new Lua file, a reconfigure, an upgrade. It costs nothing. Run stage 2 after any change to `PreemptType`, `PreemptMode`, QOS preemption lists or the submit script's routing, and after an upgrade. It evicts a real job, so do not put stage 2 on a schedule against production nodes.

---

## Version notes

Run on 23.11.4. For the preemption settings this page exercises, the changelogs read for the [version changes page](/fields/schedulers/slurm-cluster-operations/slurm-version-changes.md#preemption) record: 24.05 treats a job signalled during `GraceTime` as preempted under `CANCEL` and `REQUEUE`; 25.05 adds a `PRIORITY` preemption option; 26.05 applies `PreemptExemptTime` to `suspend,gang` under `preempt/partition_prio`. None of those were tried. Run the drill after an upgrade before trusting any of them.

---

## Back to the monitor that was refused

Replay Wednesday with the drill. Omar edits the submit script, and before he leaves he runs stage 1:

```text
  PASS  no --qos becomes low
  PASS  --qos=high becomes high_physics
  PASS  a job without --time is refused
```

The third line passes, which is what he wanted. Then the cron monitor, which is itself a user, runs the [control-plane test](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md) and the script prints `FAIL sbatch submit refused: Please set --time`, in red, on the status page. Omar changes the monitor to pass `-t 2` and the page goes green within five minutes. The researcher never asks why the page has been green since Wednesday.

**Takeaway:** policy is code that changes quietly, so test it as a user in two stages (routing and refusals with no resources, then a real eviction and requeue), make your own monitoring subject to the same rules, and run the drill after any change to QOS, preemption settings, the submit script or the version.

**Next:** [Back From the Repair Shop](/fields/schedulers/slurm-smoke-tests/slurm-smoke-node-readiness.md) moves from the rules to the hardware: how to tell that a node is really fit to go back into service.

---

## References

- [Slurm: Preemption](https://slurm.schedmd.com/preempt.html)
- [Slurm: Quality of Service (QOS)](https://slurm.schedmd.com/qos.html)
- [Slurm: job_submit plugin](https://slurm.schedmd.com/job_submit_plugins.html)
- [Slurm: sbatch](https://slurm.schedmd.com/sbatch.html) (`--test-only`, `--requeue`, `--hold`)
