---
id: slurm-smoke-after-upgrade
title: "The Morning After the Upgrade: Smoke Tests for the Change You Cannot Undo"
order: 3
sidebar_label: After an upgrade
summary: "What to check around a Slurm upgrade: a backup proven by restoring it, versions on every node, a before/after snapshot, the control-plane smoke test, and why downgrading is not supported."
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
    - slurm-smoke-config-change
    - slurm-upgrade-order
    - slurm-version-changes
    - slurm-reboot-order
---

# The Morning After the Upgrade: Smoke Tests for the Change You Cannot Undo

> **Part 3 of [Slurm Smoke Tests](/fields/schedulers/slurm-smoke-tests/README.md).** The commands and outputs below were run on a two-node test cluster (Slurm 23.11.4, accounting on, both `slurmd` daemons on one Ubuntu 24.04 machine). **No Slurm upgrade was performed**: there was only one version installed. What was tested is everything that surrounds one, namely the backup, the version reports, the snapshot and the restarts. The upgrade procedure itself is quoted from the [Slurm upgrade guide](https://slurm.schedmd.com/upgrades.html). The names and the story are invented. The order in which to upgrade the daemons is on the [upgrade order page](/fields/schedulers/slurm-cluster-operations/slurm-upgrade-order.md).

## Table of Contents

- [The Morning After the Upgrade: Smoke Tests for the Change You Cannot Undo](#the-morning-after-the-upgrade-smoke-tests-for-the-change-you-cannot-undo)
  - [Table of Contents](#table-of-contents)
  - [The undo button that isn't](#the-undo-button-that-isnt)
  - [What the guide says to test](#what-the-guide-says-to-test)
  - [Rung 1: a backup you have restored](#rung-1-a-backup-you-have-restored)
  - [Rung 2: take the snapshot](#rung-2-take-the-snapshot)
  - [Rung 3: after the daemons are back](#rung-3-after-the-daemons-are-back)
  - [Do jobs survive the restart?](#do-jobs-survive-the-restart)
  - [Version notes](#version-notes)
  - [Back to the undo button that isn't](#back-to-the-undo-button-that-isnt)
  - [References](#references)

---

## The undo button that isn't

Samira starts the upgrade at ten on Saturday night. The plan is the usual one: stop the accounting daemon, upgrade it, start it and let it convert its database, then the controller, then the nodes. By half past eleven the daemons are all running and she runs her smoke test. Everything passes except the last line. Jobs run, and the database has recorded none of them.

Now she has a decision with a clock on it. She can fix forward, reading logs at midnight with an unknown number of causes. Or she can go back. The Slurm upgrade guide has a blunt sentence about going back: "Reverting an upgrade (or downgrading) is **not supported** once any of the Slurm daemons have been started." The only way back is the backup, and the backup, the guide adds, loses "anything that happened after the backups were created."

Samira has a nightly database dump. She has never tried to restore it. At half past eleven on a Saturday, that is a poor time to find out whether it works.

---

## What the guide says to test

The upgrade guide lists nine steps, and one of them is a smoke test with a different name:

| Step | The guide's wording | Where it is covered |
|---|---|---|
| 1 | Prepare cluster for the upgrade (release notes, configuration changes, downtime) | [Version changes](/fields/schedulers/slurm-cluster-operations/slurm-version-changes.md) |
| 2 | Create backups | [Rung 1 below](#rung-1-a-backup-you-have-restored) |
| 3 | Upgrade `slurmdbd`, then validate accounting | [Rung 3](#rung-3-after-the-daemons-are-back) |
| 4 to 7 | Upgrade `slurmctld`, `slurmd`, login nodes, customised plugins | [Upgrade order](/fields/schedulers/slurm-cluster-operations/slurm-upgrade-order.md) |
| 8 | **Test key functionality** | The [control-plane smoke test](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md), plus [Rung 3](#rung-3-after-the-daemons-are-back) |
| 9 | Archive backup data, once the upgrade is confirmed | After a few good days, not the same night |

Two sentences from the guide frame everything: "Always prepare and test configuration changes in a test environment before upgrading in production", and "Sites are encouraged to actively run pre-release versions on test machines before each major release." A smoke test on production tells you whether tonight went well. A smoke test on a test cluster tells you whether tonight is a good idea.

---

## Rung 1: a backup you have restored

A backup that has never been restored is a hope. The check is small: dump the accounting database, restore the dump into a scratch database, and compare the row counts of the tables that matter. This script does it and cleans up after itself:

The script is [`slurm-db-backup-check.sh`](/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-db-backup-check.sh), a plain file you can read on this site, [open on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-db-backup-check.sh) or fetch with its [raw link](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-db-backup-check.sh).

On the test cluster:

```text
dump: 237712 bytes
PASS  smoke_job_table          live=284 restored=284
PASS  smoke_assoc_table        live=6 restored=6
BACKUP RESTORES
```

The tables are named after the cluster, here `smoke`, which is why the script looks them up instead of hard-coding them. Two limits are worth saying out loud. This ran while `slurmdbd` was up, using a transaction-consistent dump, which is fine for a rehearsal. The guide's own procedure takes the real dump with `slurmdbd` stopped, and the script's header says so. And matching row counts show the dump is complete, not that every row is right. It catches the failures that matter, an empty, truncated or unreadable dump, which are the ones nobody finds until they need it.

A second backup comes with the first: the controller's state directory (`StateSaveLocation`), which holds the queue and reservations. The [spool directory page](/fields/schedulers/slurm-cluster-operations/slurm-spool-dir-full.md) covers where that lives.

---

## Rung 2: take the snapshot

Save what the cluster looks like before, so the morning after has something to compare with. The `slurm-snapshot.sh` script from [part 2](/fields/schedulers/slurm-smoke-tests/slurm-smoke-config-change.md#rung-1-look-at-the-diff) records the running configuration, partitions, nodes, reservations, QOS and associations as plain text:

```bash
./slurm-snapshot.sh /root/before-upgrade
```

After the upgrade, run it again into another directory and `diff -ru` the two. Expect differences: the version on every node, and probably a few new default parameters in `config.txt`. What should not differ is the list of partitions, the QOS and association rules, and the reservations. If one does, it is either a consequence the release notes warned about or something to investigate before the users find it.

---

## Rung 3: after the daemons are back

Each of these takes seconds:

| Check | Command | What it should show |
|---|---|---|
| Version of every daemon | `slurmctld -V`, `slurmdbd -V`, `slurmd -V`, `sinfo -V` | The target version. On the test cluster all four read `slurm-wlm 23.11.4` |
| Version of every node, as the controller sees it | `scontrol show node -o \| grep -o 'NodeName=[^ ]*\|Version=[^ ]*' \| paste - -` | One line per node with the same version |
| The control plane | [`slurm-smoke.sh`](/fields/schedulers/slurm-smoke-tests/slurm-smoke-control-plane.md), as an ordinary user | `ALL PASS` |
| Accounting answers | `sacctmgr ping` (24.11 and newer), and `sacct` for an old job | The old job is still readable, and the last smoke job is recorded |
| The state matches before | `diff -ru` of the two snapshots | Only the expected differences |
| Custom plugins and SPANK | Submit a job that uses each one | They load. The 24.11 release notes say all SPANK plugins must be recompiled when upgrading from an earlier version |

The per-node line on the test cluster:

```text
NodeName=node1	Version=23.11.4
NodeName=node2	Version=23.11.4
```

A node that was missed shows its old version here, which is the cheapest way to find the one `slurmd` that did not restart. A version mismatch is the first thing the [troubleshooting guide](https://slurm.schedmd.com/troubleshoot.html) suggests ruling out, with `sinfo -V` or `rpm -qa | grep slurm`.

`sacctmgr ping` does not exist on 23.11. On the test cluster it answered `invalid keyword: ping`. It was added in 24.11, so the script from part 1 still uses `sacct`, which works on every version.

---

## Do jobs survive the restart?

The upgrade guide has you stop and start every daemon, with users' jobs running through it. Whether they survive is something to know before the real night. On the test cluster, a 300-second job was started on `node1`. Then `slurmdbd`, `slurmctld` and the `slurmd` on `node1` were all stopped, and everything restarted:

```text
job 109: RUNNING node1
all three stopped; restarting
job 109 after restarts: RUNNING node1
```

The job was still running, and a smoke test straight after passed. That is one job, with default settings and a process tracker that does not use cgroups, so it is evidence, not a guarantee. A rehearsal on a test cluster with your real configuration, long-running jobs and a node restart is worth more than this table.

---

## Version notes

Nothing on this page was run across two versions, so there are no measured differences. From the release notes read for the [version changes page](/fields/schedulers/slurm-cluster-operations/slurm-version-changes.md): 24.11 can be upgraded directly from 23.02, 23.11 or 24.05, and the notes say to update `slurmdbd` first; 25.11 from 25.05, 24.11 or 24.05. The upgrade path for 26.05 was not checked. A jump from 23.11 to 26.05 is therefore several upgrades, and each one deserves its own backup and its own run of this page.

---

## Back to the undo button that isn't

Replay Saturday with a rehearsed Friday. On Friday afternoon Samira ran the backup check and saw `BACKUP RESTORES`, with the same row counts on both sides. She saved a snapshot. She stopped `slurmdbd`, took the real dump, and started.

At half past eleven the smoke test fails on the last line, as before. This time the decision takes five minutes and not an hour. She has a dump she knows can be restored, a snapshot to compare against, and a clear question: is this a quick fix? She reads the accounting daemon's log, finds the cause, fixes it, and reruns the script. `ALL PASS`. She did not need the restore, and she knew exactly what it would have cost.

**Takeaway:** a Slurm upgrade cannot be rolled back once a daemon has started, so the real smoke test happens before it (a backup you have restored, a saved snapshot, a rehearsal on a test cluster) and after it (versions on every node, the control-plane smoke test, accounting, and a diff of the snapshots).

**Next:** [Does the Rulebook Still Work?](/fields/schedulers/slurm-smoke-tests/slurm-smoke-policy.md) tests the layer an upgrade is most likely to change quietly: QOS, submit rules and preemption.

---

## References

- [Slurm: Upgrade Guide](https://slurm.schedmd.com/upgrades.html) (the nine steps, "Test key functionality", no downgrade)
- [Slurm: Troubleshooting Guide](https://slurm.schedmd.com/troubleshoot.html) (`sinfo -V`, version compatibility)
- [Slurm: Quick Start Administrator Guide](https://slurm.schedmd.com/quickstart_admin.html)
- [Slurm 24.11 release notes, mirror](https://third-party-mirror.googlesource.com/SchedMD/slurm/+/refs/heads/master/RELEASE_NOTES.md) (`sacctmgr ping`, upgrade paths, SPANK recompile)
