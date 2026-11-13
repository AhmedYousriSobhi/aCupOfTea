---
id: slurm-version-changes
title: "The Changelog Nobody Reads: What Moved Between Slurm 23.11 and 26.05"
order: 4
sidebar_label: Version changes 23.11 to 26.05
summary: A per-topic tour of what changed in Slurm between 23.11 and 26.05 for preemption, job_submit/lua, reservations, signals, accounting and cgroups, with the security-fix timeline and upgrade paths.
level: intermediate
type: reference
domains:
  - systems-and-hpc
tags:
  - slurm
  - hpc
relations:
  related:
    - slurm-upgrade-order
    - slurm-preemption-requeue-signals
    - slurm-qos-preemption-setup
    - slurm-job-submit-lua
    - slurm-signals-cheatsheet
    - slurm-reservations-and-maintenance
    - slurm-sacct-job-forensics
    - slurm-cgroups-in-practice
---

# The Changelog Nobody Reads: What Moved Between Slurm 23.11 and 26.05

> **Part of the [schedulers](/fields/schedulers/slurm-intro.md) directory.** This page was assembled from SchedMD's changelogs and release notes, read through a web fetch and summarized, so it quotes short lines and names the version each one belongs to. Nothing here was run: the tested pages in this directory ran on Slurm 23.11.4, and the [sources and coverage](#sources-and-coverage) section says exactly what was and was not read. For a real upgrade, read the official notes for every version you cross.

## Table of Contents

- [The Changelog Nobody Reads: What Moved Between Slurm 23.11 and 26.05](#the-changelog-nobody-reads-what-moved-between-slurm-2311-and-2605)
  - [Table of Contents](#table-of-contents)
  - [The config that survived three upgrades](#the-config-that-survived-three-upgrades)
  - [Sources and coverage](#sources-and-coverage)
  - [The security timeline](#the-security-timeline)
  - [Preemption](#preemption)
  - [job_submit/lua](#job_submitlua)
  - [Reservations](#reservations)
  - [Signals and killing jobs](#signals-and-killing-jobs)
  - [Accounting, sacct and sacctmgr](#accounting-sacct-and-sacctmgr)
  - [cgroups](#cgroups)
  - [Upgrade paths](#upgrade-paths)
  - [What the tested pages need re-checking](#what-the-tested-pages-need-re-checking)
  - [Back to the config that survived three upgrades](#back-to-the-config-that-survived-three-upgrades)
  - [References](#references)

## The config that survived three upgrades

A site has a `slurm.conf` that was written in 2023. It has been copied to every new cluster since, with the care people give to a recipe from a grandmother: nobody remembers why each line is there, and nobody dares remove one. This autumn the admin plans to move from 23.11 to 26.05, because the old version stopped getting fixes, and checks the plan by reading the one page everybody reads: the install guide.

Nobody reads the changelog. It is long, written by developers, and mostly about things that do not apply to you. The few lines that do apply are scattered across five releases: a default that changed, an option that was renamed, a path that now has a different name. Each is harmless to know in advance and annoying to discover on a Monday.

This page is those lines, collected by topic.

---

## Sources and coverage

| Version | What was read | Limits |
|---|---|---|
| 24.05 | The changelog | Read in full for the topics below |
| 24.11 | Release notes | Not the full changelog |
| 25.05 | The changelog | Read in full for the topics below |
| 25.11 | Release notes | Not the changelog, so bug fixes are missing |
| 26.05 | The changelog | Read in full for the topics below |
| 26.11 | Release notes from the development branch | Not a stable release for the purposes of this page. Check whether it has been released before relying on it |

A topic with no entry for a version means nothing turned up in what was read, not that nothing changed.

---

## The security timeline

Security fixes did not wait for 26.05. They arrived as point releases on the branches that were supported at the time:

| Fix | Where it appears | What it was |
|---|---|---|
| CVE-2024-42511 | 24.05.2, with matching releases on 23.11 and 23.02 | Access control around network and IMEX channel resources in the HPE Slingshot and NVIDIA IMEX switch plugins |
| CVE-2024-48936 | 24.05.4 | A stepmgr flaw that could let an attacker execute processes |
| CVE-2025-43904 | 24.05.8, 24.11.5, 23.11.11, 25.05.0 | A coordinator could add a user with elevated privileges |
| Eight CVEs, including CVE-2026-65107 to 65109, 65138 to 65140, 65165 and 65168 | 26.05.4, 25.11.8, 25.05.9 | `sbcast` credential checks, a `slurmstepd` stack overflow, OCI cleanup deleting files outside its directory, a malformed-RPC heap over-read, unsafe cluster names reaching accounting queries, and an operator editing Administrator accounts |

Two things follow. First, 23.11 did receive security releases, up to at least 23.11.11 for the privilege issue above. A cluster still on 23.11.4, like the test cluster behind these pages, is missing even those. Second, the 2026 batch was released for 26.05, 25.11 and 25.05. The announcement does not say whether 23.11 or 24.x are affected. It lists those three branches as fixed, so an older branch is not going to receive them, whether or not it is affected. Whichever version you run, take the latest point release of a supported branch.

---

## Preemption

| Version | Change |
|---|---|
| 24.05 | "For PreemptMode=CANCEL and PreemptMode=REQUEUE assume that job signalled for GraceTime was preempted." A job that is signalled during `GraceTime` and then leaves is recorded as preempted |
| 24.05.4 | A fix for QOS preemptability being lost after clearing a preempt list with `preempt=''` |
| 25.05 | A new `PRIORITY` preemption option so that a preemptor can preempt only when its priority is higher than the victim's. Deleting a QOS now removes it from the other QOSes' preempt lists |
| 25.05.1, 25.05.5 | `preempt/partition_prio` no longer lets a partition's `PreemptMode` default to `PRIORITY`. A fatal error when `min_exempt_priority` was not the last `PreemptParameters` option was fixed |
| 26.05 | `PreemptExemptTime` now also applies to `PreemptMode=suspend,gang` under `preempt/partition_prio`. Partitions can be created or updated dynamically with `PreemptMode=Priority`. A segfault with QOS `SUSPEND` on an `OverSubscribe=YES` partition was fixed in 26.05.3 |

What this means for the [preemption pages](/fields/schedulers/slurm-preemption/slurm-qos-preemption-setup.md): the 24.05 line affects how a victim that exits cleanly during `GraceTime` shows up in `sacct`. On 23.11 that was not tested here. The `GraceTime` signal behavior itself (the early `SIGTERM` reaching steps and not the batch shell) was measured on 23.11.4 only, and none of the changelogs read mention it, so it needs a rerun on the version you use.

---

## job_submit/lua

| Version | Change |
|---|---|
| 24.05.2 | `curr_dependency` is exposed in `job_submit.lua` and `jobcomp.lua` |
| 24.11 | `job_desc` gains `assoc_qos`, and there is a `slurm.get_qos_priority()` function. `burst_buffer/lua` loses `slurm.job_info_to_string()` |
| 25.05.3 | A controller crash was fixed when a script read `job_desc.assoc_qos` for an association that does not exist |
| 26.05 | A Lua stack trace is logged on runtime errors in `slurm_job_submit()` and `slurm_job_modify()`. `core_spec` and `thread_spec` are exposed in `job_desc` |
| 26.05 | In partition definitions `Exclusive=[NO\|NODE\|USER\|TOPO]` replaces `ExclusiveUser` and `ExclusiveTopo` |

The [Lua page](/fields/schedulers/slurm-preemption/slurm-job-submit-lua.md) says a broken script is hard to debug. From 26.05 a runtime error leaves a stack trace in the log, which makes the failure-mode table there easier to use. The `assoc_qos` field in 24.11 is a candidate for a stronger version of Recipe 1: the script could check which QOS the user's association really allows before routing to `high_<account>`. That idea was not tested.

---

## Reservations

| Version | Change |
|---|---|
| 24.05 | `USER_DELETE` lets users with access to a reservation delete it. In 24.05.4 nodes in reservations with the Maintenance or Overlap flags are considered when new reservations are created |
| 25.05 | `FORCE_START` lets recurring reservations start in the past. Empty reservations can no longer be created with `ANY_NODES`. Typed GRES reservations work without also listing the untyped GRES. `sacct` gets a `ReqReservation` field |
| 25.11 | New reservation access controls, `AllowQOS` and `AllowPartition` |
| 26.05 | "Do not allocate maintenance nodes to new reservations." `FLEX` plus `MAGNETIC` reservations can pick up jobs that extend past the end (26.05.2) |

The [maintenance page](/fields/schedulers/slurm-cluster-operations/slurm-reservations-and-maintenance.md) was tested on 23.11.4. The maintenance-flag behavior in 24.05.4 and 26.05 is about picking nodes for a second reservation, which that page did not exercise. The `ReqReservation` field is useful for the `sacct` question "did this job ask for a reservation?".

---

## Signals and killing jobs

| Version | Change |
|---|---|
| 24.05 | The default for `UnkillableStepTimeout` became 60 seconds, and an error is logged when it is less than five times `MessageTimeout` |
| 25.05 | "Sigkill user processes atomically by using cgroup.kill interface" |
| 26.05 | "KillWait will be honored when the task does not end with the TERM signal." `srun --ignore-signals` stops specified signals being forwarded to tasks. After a task returns a non-zero code, `SIGCONT`, `SIGTERM` and `SIGKILL` go to the remaining tasks. Job cancellation is no longer delayed while `slurmstepd` is launching a task (26.05.2) |

The [signals cheat sheet](/fields/schedulers/slurm-preemption/slurm-signals-cheatsheet.md) measured the `KillWait` and `SIGKILL` timing on 23.11.4 with a task that ignored `SIGTERM`. The 26.05 `KillWait` line is exactly about that case, so those timings are the first thing to rerun with the probe. The [kill-task-failed page](/fields/schedulers/slurm-cluster-operations/slurm-kill-task-failed.md) is also affected by the `UnkillableStepTimeout` default.

---

## Accounting, sacct and sacctmgr

| Version | Change |
|---|---|
| 24.05 | Output, error and input paths are stored in the database and shown by accounting tools |
| 24.11 | `sacctmgr ping` checks `slurmdbd`. `sreport` gets `AccountUtilizationByQOS` |
| 25.05 | `sacct` can show `TimeLimit` and `TimelimitRaw` for steps, and `SegmentSize` |
| 25.11 | Administrators can change a job's `AllocTRES` retroactively through `sacctmgr`. `slurmdbd.conf` gets `DisableArchiveCommands` |
| 26.05 | `sacct --json` and `--yaml` print `submit_line` for steps and a `.jobs[].sluid` field. A fix in 26.05.4 for corrupted earlier accounting records (a bumped requeue counter and a missing start time) |
| 26.11 (development) | "Record the name, not the UID, of the user that cancelled a job or set a node reason." |

The last row matters for the [sacct page](/fields/schedulers/slurm-sacct-job-forensics.md): on 23.11.4 a cancelled job showed `CANCELLED by 30033`, a numeric user ID. If the 26.11 change ships as described, the same record would carry a name. The `-D` view of a requeued job is also the one the 26.05.4 fix is about.

---

## cgroups

| Version | Change |
|---|---|
| 24.05 | `CgroupPlugin=disabled`, `SystemdTimeout=` in `cgroup.conf`, `RestrictedCoresPerGPU`, and a requirement of dbus 1.11.16 or newer for cgroup v2 |
| 25.05 | "cgroup/v1 started its deprecation process", with a recommendation to move to v2. `EnableExtraControllers` is added to `cgroup.conf` |
| 25.11 | `slurmd` can be launched in a cgroup slice other than `system.slice` |
| 26.05 | cgroup v2 paths are built from the SLUID instead of the numeric job ID. 26.05.2 adds an option to use the job ID again, and the default stays SLUID |

The [cgroups page](/fields/schedulers/slurm-inside-a-job/slurm-cgroups-in-practice.md) already covers the 26.05 path change. The 25.05 deprecation is the one to plan around, because a cluster on cgroup v1 will want to be on v2 before a later release removes v1. No removal was found in the notes read here.

---

## Upgrade paths

| Target | Can be upgraded directly from | Notes |
|---|---|---|
| 24.11 | 23.02, 23.11, 24.05 | All SPANK plugins must be recompiled. Update `slurmdbd` first |
| 25.11 | 25.05, 24.11, 24.05 | |
| 26.11 (development) | 26.05, 25.11, 25.05 | Database schema changes may make the `slurmdbd` upgrade slower than usual |
| 26.05 | Not checked | The 26.05 upgrade rules were not among the pages read |

So a jump from 23.11 to 26.05 cannot be done in a single step under the rules found: 23.11 reaches 24.11 directly, and the hops after that need to be checked against each release's own notes. The [upgrade order page](/fields/schedulers/slurm-cluster-operations/slurm-upgrade-order.md) covers the order of daemons for each hop.

---

## What the tested pages need re-checking

| Claim in these pages (measured on 23.11.4) | Why it may differ later | How to check |
|---|---|---|
| The early `GraceTime` `SIGTERM` goes to `srun` steps, not the batch shell | Not mentioned in the changelogs read, so unknown | The `probe.sh` in the signals page |
| `--signal` fires at preemption only with `send_user_signal` | Same | The same probe |
| A process that ignores `SIGTERM` is killed `KillWait` seconds later | 26.05 changed `KillWait` handling for tasks that do not end with `TERM` | The same probe, `GraceTime` at 0 |
| A victim that exits cleanly during `GraceTime` | 24.05 treats it as preempted under `CANCEL` and `REQUEUE` | A drill from the [setup page](/fields/schedulers/slurm-preemption/slurm-qos-preemption-setup.md), then `sacct -X -D` |
| `CANCELLED by <uid>` in `sacct` | 26.11 notes say a name is recorded instead | `sacct -X -P -o JobID,State%30` after a `scancel` |
| Rollback needs `PreemptType=preempt/none` and `PreemptMode=OFF` | Not checked on other versions | A test controller before a real change |

---

## Back to the config that survived three upgrades

Replay the plan with this page open. The admin reads the changelog entries for each hop, and ends up with a short list instead of a surprise. The cgroup v1 deprecation goes on the calendar. The `UnkillableStepTimeout` default is noted, because the old value would be changed under them. The tested pages' claims get a Friday afternoon rerun on a test controller, with the probe from the signals page, and the three that differ are written down.

None of it is dramatic. The upgrade happens on a Saturday, the config line nobody remembered is still there and still harmless, and Monday is dull in the way upgrades should be.

**Takeaway:** security fixes came as point releases on supported branches, so the goal is the latest point release of a supported version, not a particular major one, and the changes worth knowing are small and scattered (GraceTime and KillWait handling, `Exclusive=`, cgroup v1 deprecation, SLUID paths), so read each hop's notes before you cross it.

**Next:** [the upgrade order page](/fields/schedulers/slurm-cluster-operations/slurm-upgrade-order.md) covers which daemons to upgrade first on each hop.

---

## References

- [Slurm 24.05 changelog](https://github.com/SchedMD/slurm/blob/master/CHANGELOG/slurm-24.05.md)
- [Slurm 25.05 changelog](https://github.com/SchedMD/slurm/blob/master/CHANGELOG/slurm-25.05.md)
- [Slurm 26.05 changelog](https://github.com/SchedMD/slurm/blob/slurm-26.05/CHANGELOG/slurm-26.05.md)
- [Release notes for Slurm 25.11 and 26.11 (development), mirror](https://third-party-mirror.googlesource.com/SchedMD/slurm/+/refs/heads/master/RELEASE_NOTES.md)
- [Slurm versions 26.05.4, 25.11.8 and 25.05.9 announcement](https://lists.schedmd.com/mailman3/hyperkitty/list/slurm-users@lists.schedmd.com/thread/3YAYJNR6YFN6NLR3S5GVOI6BOTMEZUG5/)
- [Slurm versions 24.11.5, 24.05.8 and 23.11.11 announcement (CVE-2025-43904)](https://groups.google.com/g/slurm-users/c/ynRBya4AiLo)
- [Slurm versions 24.05.2, 23.11.9 and 23.02.8 announcement (switch plugins security fix)](https://lists.schedmd.com/mailman3/hyperkitty/list/slurm-announce@lists.schedmd.com/message/26WSTB5KF6UL52A52KDI3AR4LZKRAFMR/)
