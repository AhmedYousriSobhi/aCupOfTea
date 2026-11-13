
# Measure Twice, Reconfigure Once: Smoke-Testing a slurm.conf Change

<!-- related-block -->
<div class="reading-time">8 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [The Cluster That Worked Perfectly and Remembered Nothing: a Two-Minute Slurm Smoke Test](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md)  ·  **See also:** [Calling Dibs on Nodes: Reservations, Maintenance Windows and the Job That Fit](/fields/schedulers/slurm-cluster-operations/slurm-reservations-and-maintenance.md), [Does the Rulebook Still Work? Smoke-Testing QOS, Submit Rules and Preemption](/fields/schedulers/slurm-smoke-tests/slurm-smoke-policy.md), [Rebooting a Slurm Cluster Without Losing Your Job (Or Anyone Else's)](/fields/schedulers/slurm-cluster-operations/slurm-reboot-order.md), [The Morning After the Upgrade: Smoke Tests for the Change You Cannot Undo](/fields/schedulers/slurm-smoke-tests/slurm-smoke-after-upgrade.md), [The Receptionist Who Rewrites Your Badge: job_submit.lua](/fields/schedulers/slurm-preemption/slurm-job-submit-lua.md)

</div>


> **Part 2 of [Slurm Smoke Tests](/fields/schedulers/slurm-smoke-tests/README.md).** Everything here was run on a two-node test cluster (Slurm 23.11.4, accounting on, both `slurmd` daemons on one Ubuntu 24.04 machine), including the mistakes, which were made on purpose. Names and the story are invented. The [control-plane smoke test](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md) is the check this page runs at the end, so read it first.

## Table of Contents

- [Measure Twice, Reconfigure Once: Smoke-Testing a slurm.conf Change](#measure-twice-reconfigure-once-smoke-testing-a-slurmconf-change)
  - [Table of Contents](#table-of-contents)
  - [The partition for nodes that were not there yet](#the-partition-for-nodes-that-were-not-there-yet)
  - [What Slurm does with a bad file](#what-slurm-does-with-a-bad-file)
  - [Rung 1: look at the diff](#rung-1-look-at-the-diff)
  - [Rung 2: ask Slurm without running anything](#rung-2-ask-slurm-without-running-anything)
  - [Rung 3: a canary lane](#rung-3-a-canary-lane)
  - [Rung 4: reconfigure, then check](#rung-4-reconfigure-then-check)
  - [Version notes](#version-notes)
  - [Back to the partition for nodes that were not there yet](#back-to-the-partition-for-nodes-that-were-not-there-yet)
  - [References](#references)

---

## The partition for nodes that were not there yet

Layla is adding eight nodes next week. To save time, she writes the partition for them today, in `slurm.conf`, naming nodes that exist on the purchase order but not yet in the rack, and runs `scontrol reconfigure`. It prints an error. The cluster, she checks, is still fine: jobs are running, `squeue` answers. She decides the error is about the new nodes, which is true, and leaves it for next week.

Three weeks later the controller is restarted for an unrelated reason. It does not come back.

Nothing in Layla's story is careless in a way that feels careless at the time. The error looked non-fatal because it was. The running controller really did keep working. The problem was that the file on disk had become a time bomb, and a restart is the thing that reads the file.

---

## What Slurm does with a bad file

Four mistakes were made in `slurm.conf` on the test cluster, one at a time, each followed by `scontrol reconfigure`. The original file was restored after each.

| Mistake | What `scontrol reconfigure` did |
|---|---|
| An unknown key, `SchedulerTypo=yes` | `scontrol: error: _parse_next_key: Parsing error at unrecognized key: SchedulerTypo`, then `fatal: Unable to process configuration file`, exit status 1 |
| A bad number, `MaxJobCount=banana` | `error: MaxJobCount value (banana) is not a valid number`, then the same `fatal`, exit status 1 |
| A bad value, `State=SIDEWAYS` on a partition | `error: Bad value "SIDEWAYS" for State`, then the same `fatal`, exit status 1 |
| A partition naming a missing node, `Nodes=node9` | `slurm_reconfigure error: Unspecified error`, exit status 1 |

Look at who said what. The first three were caught by **`scontrol` itself**, which parses the file on your machine before it sends anything. The running controller never saw them. A side effect: while the file is broken, every `scontrol` command fails the same way, including `scontrol ping`.

The fourth got past the client, because the file was valid syntax. The error came back from the controller as the unhelpful "Unspecified error", and the real reason was only in the controller log:

```text
error: _find_node_record: lookup failure for node "node9"
build_part_bitmap: invalid node name node9 in partition
fatal: Invalid node names in partition ghost
```

After that failed reconfigure, `scontrol ping` still said `UP` and jobs kept running: the old process stayed in charge. Then the same file was left in place and the controller was restarted:

```text
pgrep: slurmctld NOT running
fatal: Invalid node names in partition ghost
```

**The same mistake that a reconfigure survives, a restart does not.** A failed reconfigure is a warning with a delay on it.

---

## Rung 1: look at the diff

Before touching anything, write down what is running and compare it with what will be. `scontrol show config` is the obvious tool, but on its own it is not enough. In the test it did not show a newly added partition at all, only the global settings, and its only differences after a reconfigure were two timestamps. A useful snapshot needs the partitions, nodes, reservations and accounting rules too:

The script is [`slurm-snapshot.sh`](/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-snapshot.sh), a plain file you can read on this site, [open on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-snapshot.sh) or fetch with its [raw link](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-snapshot.sh).

A change was made on the test cluster: a hidden `canary` partition added to `slurm.conf`, and a new QOS called `trial` added with a 45-second `GraceTime`. The diff:

```text
+PartitionName=canary
+   AllowGroups=ALL AllowAccounts=ALL AllowQos=ALL
+   ...
+   Nodes=node2
+   State=UP TotalCPUs=4 TotalNodes=1 SelectTypeParameters=NONE
 low|10||requeue|00:00:30|
 high_physics|1000|low|cluster|00:00:00|
 high_bio|1000|low|cluster|00:00:00|
+trial|0||cluster|00:00:45|
```

The same diff also flagged the `node2` line as changed. The cause, once the full line was read, was that `Partitions=` now listed `canary` as well. The tool did its job: it showed an effect nobody asked for in the change, which is exactly why you diff.

Keep the snapshots. When something misbehaves on Thursday, "what changed since Monday" is a `diff`.

---

## Rung 2: ask Slurm without running anything

`sbatch --test-only` validates a job and says when and where it would start, without queueing it. It is the cheapest end-to-end check that the rules still accept what users send. On the test cluster, with a valid job, it ran the whole submit path and left the queue empty:

```text
sbatch: Job 103 to start at 2026-11-13T08:07:53 using 1 processors on nodes node1 in partition gpu
```

The same flag, for jobs that should be refused, produced a different message for each cause:

| Test job | Response |
|---|---|
| No `--time`, with a [submit script](/fields/schedulers/slurm-preemption/slurm-job-submit-lua.md) that requires it | `sbatch: error: Please set --time, jobs without one are not accepted` |
| `-N5` on a two-node cluster | `allocation failure: Requested node configuration is not available` |
| A partition that does not exist | `sbatch: error: invalid partition specified: nosuch` |
| A user with no account | `allocation failure: Invalid account or account/partition combination specified` |

That makes it the right dry run for a policy change: a submit rule, a limit, a partition option. Run a handful of jobs that *should* work and a handful that *should* fail, and compare the answers with what you intended. The checks that cannot be done with it are the ones that need a real node: it does not start anything, so it proves the rules, not the machine.

There is no equivalent for the file itself on this version. The `slurmctld -h` output of 23.11 lists no option to check a configuration and exit. Do not assume newer versions are the same without reading their help.

---

## Rung 3: a canary lane

Give the change a small place to land first. The test cluster got a partition made of one node, hidden from the normal partition list:

```text
PartitionName=canary Nodes=node2 State=UP Hidden=YES MaxTime=10
```

Users do not see a hidden partition in `sinfo`, but they can still submit to it by name, and so can your smoke test:

```bash
SMOKE_PARTITION=canary ./slurm-smoke.sh
```

```text
PASS  nodes    1 node(s), none down or drained
PASS  srun     1 of 1 nodes answered
PASS  sbatch   job 107 ran and wrote its output
PASS  sacct    job 107 recorded as COMPLETED
ALL PASS
```

A canary partition has a second use: it is the place for the scheduled smoke test from [part 1](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md), so its jobs never queue behind real work and never turn into `WAIT`. For a change that needs to be tried on real nodes (a new QOS, a new limit), put the change on the canary partition first, with a small group of users, and widen it only after a day of green results.

---

## Rung 4: reconfigure, then check

By now the file has been diffed, the rules dry-run and the partition tried. The reconfigure itself was uneventful in the test. A job that was running (`sleep 300`, job 105) was still `RUNNING` on `node1` after it. The only change in `scontrol show config` was `BOOT_TIME`, which moved to the reconfigure time, one of the two lines the snapshot script drops.

After it, repeat the same three steps in the same order:

1. The [smoke test](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md), as a normal user.
2. `slurm-snapshot.sh /tmp/after` and a `diff -ru` against the one taken before.
3. A look at the controller log for new `error:` lines. The failed reconfigure above produced a `fatal:` that never reached the terminal.

Some settings need a daemon restart and not a reconfigure. The `slurm.conf` man page marks them, and this page did not test which ones.

---

## Version notes

Tests were on 23.11.4. From 26.05, a runtime error in a Lua submit script writes a stack trace to the log, which helps with a failing policy change. [Version changes 23.11 to 26.05](/fields/schedulers/slurm-cluster-operations/slurm-version-changes.md#job_submitlua) has the entry. Whether newer versions give a clearer reason than "Unspecified error" for a partition that names a missing node was not checked.

---

## Back to the partition for nodes that were not there yet

Replay Layla's afternoon with the ladder. She snapshots the cluster, adds the partition for the future nodes, and runs `scontrol reconfigure`. The error is the same. This time the rule she follows is that an error on a reconfigure is a failure, not a message. She removes the partition, reconfigures cleanly, runs the smoke test, and reads the diff. It shows nothing changed.

Next week, when the eight nodes are in the rack and defined, the partition goes in with them, on the canary lane first. Three weeks later the controller restarts for an unrelated reason and comes back in the time it takes to read the log.

**Takeaway:** syntax mistakes are stopped by `scontrol` before the controller sees them, but a semantic mistake can survive a reconfigure and kill the next restart, so treat any reconfigure error as a failure, snapshot before and after, dry-run policy with `sbatch --test-only`, try new rules on a hidden canary partition, and finish with the smoke test.

**Next:** [The Morning After the Upgrade](/fields/schedulers/slurm-smoke-tests/slurm-smoke-after-upgrade.md) applies the same discipline to the one change you cannot undo.

---

## References

- [Slurm: slurm.conf](https://slurm.schedmd.com/slurm.conf.html) (which parameters need a restart)
- [Slurm: scontrol](https://slurm.schedmd.com/scontrol.html) (`reconfigure`, `show config`, `show partition`)
- [Slurm: sbatch](https://slurm.schedmd.com/sbatch.html) (`--test-only`)
- [Slurm: Upgrade Guide](https://slurm.schedmd.com/upgrades.html) ("Always prepare and test configuration changes in a test environment before upgrading in production")
