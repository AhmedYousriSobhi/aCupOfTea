---
id: nhc-slurm-integration
title: Plugging NHC into Slurm (and Friends)
sidebar_label: "4. Slurm integration"
order: 4
summary: The three slurm.conf lines, which node states to check, timeouts that don't fight each other, prolog and epilog patterns, reboots, plus PBS and cron.
level: intermediate
type: guide
domains: [systems-and-hpc]
tags: [hpc, slurm]
relations:
  prerequisites: [nhc-writing-nhc-conf]
---

# Plugging NHC into Slurm (and Friends)

> **Part 4 of the [Node Health Check series](/fields/system-administration/node-health-check/README.md).** NHC knows how to judge a node. Now we give it a schedule, a timeout that won't get it killed mid-sentence, and the right to drain.

## Table of Contents
- [The three lines](#the-three-lines)
- [Which nodes should get checked? HealthCheckNodeState](#which-nodes-should-get-checked-healthchecknodestate)
- [Timeouts: make sure the bouncer isn't shot mid-sentence](#timeouts-make-sure-the-bouncer-isnt-shot-mid-sentence)
- [Life of a failure, end to end](#life-of-a-failure-end-to-end)
- [Draining etiquette for humans](#draining-etiquette-for-humans)
- [Boot and reboot: the sneaky part](#boot-and-reboot-the-sneaky-part)
- [Prolog and Epilog: checks at job boundaries](#prolog-and-epilog-checks-at-job-boundaries)
- [Not on Slurm? PBS, Grid Engine, cron, Kubernetes](#not-on-slurm-pbs-grid-engine-cron-kubernetes)

---

## The three lines

Add to `slurm.conf` on **every** node and the controller (Slurm expects the file identical everywhere, even though only `slurmd` runs the program):

```ini
HealthCheckProgram=/usr/sbin/nhc
HealthCheckInterval=300
HealthCheckNodeState=ANY,CYCLE
```

Then tell NHC which resource manager it's talking to, in `/etc/sysconfig/nhc` (or `/etc/default/nhc`):

```bash
NHC_RM=slurm
```

NHC can auto-detect Slurm, but pinning it removes one variable from every future debugging session. Apply the Slurm side with `scontrol reconfigure` (or restart `slurmctld` and the `slurmd`s), and confirm:

```bash
scontrol show config | grep -i healthcheck
```

What each line does:

| Setting | Meaning | Advice |
|---------|---------|--------|
| `HealthCheckProgram` | Absolute path, run as **root** by `slurmd` | Point at `nhc` directly, or at a tiny wrapper if you need flags |
| `HealthCheckInterval` | Seconds between runs. **Default 0 = never** | 300 is the classic value. Go to 3600 if users report jitter |
| `HealthCheckNodeState` | Which node states get checked (next section) | `ANY,CYCLE` is a sane default |

Want to pass flags? Use a wrapper, because `HealthCheckProgram` takes a path, not a command line:

```bash
#!/bin/bash
# /etc/slurm/nhc-wrapper.sh
exec /usr/sbin/nhc -c /etc/nhc/nhc.conf "$@"
```

---

## Which nodes should get checked? HealthCheckNodeState

| Value | Runs on | Typical use |
|-------|---------|-------------|
| `ANY` (default) | Every node, busy or not | Catch problems even under running jobs |
| `IDLE` | Idle nodes (drained-and-idle included) | Jitter-sensitive sites |
| `NONDRAINED_IDLE` (23.02+) | Idle nodes that are **not** drained | See the warning below |
| `ALLOC` / `MIXED` | Fully / partially allocated nodes | Rare on their own; combine with others |
| `CYCLE` | Combine with the above: spreads runs across the interval instead of all at once | Big clusters, shared filesystems |
| `START_ONLY` | Only when `slurmd` starts | Boot-time validation only |
| `REBOOT_ONLY` | Only when `slurmd` reports back after a reboot | Post-reboot validation only |

`START_ONLY` and `REBOOT_ONLY` can't be combined with anything else.

> [!WARNING]
> **`NONDRAINED_IDLE` breaks NHC's auto-resume.** NHC brings a node back by passing a later check, but this state means drained nodes are never checked again. Every NHC drain becomes a manual resume. That can be exactly what you want (human eyes on every failure) but choose it on purpose.

Why `CYCLE`? Without it, all 2,000 nodes run NHC in the same second. If your checks touch NFS or Lustre (stat a file, `df` a mount), that's a synchronized thundering herd against your metadata server every five minutes. `CYCLE` staggers them.

---

## Timeouts: make sure the bouncer isn't shot mid-sentence

There are two clocks, and they need to agree:

| Clock | Default | Who sets it |
|-------|---------|-------------|
| NHC watchdog `TIMEOUT` | **30 s** | `/etc/sysconfig/nhc` or `-t` |
| Slurm kills the program | **60 s** (`HealthCheckTimeout` on recent Slurm, max 65535) | `slurm.conf` |

Rule: **NHC's timeout must be shorter than Slurm's.** When NHC's watchdog fires, NHC reports a clean "timed out" failure and drains with a reason. When Slurm's fires first, NHC just dies silently, nothing gets drained, and you learn nothing.

What if your checks genuinely need minutes (GPU stress, bandwidth tests)? Don't stretch the periodic timeout. Pick one:

1. **Move them** to a deep context run from cron or by your remediation loop ([part 7](/fields/system-administration/node-health-check/auto-remediation.md)).
2. **Detached mode** (`DETACHED_MODE=1` in sysconfig): NHC forks, returns *the previous run's* result immediately, and runs the checks in the background. `slurmd` never blocks. The catch: a fresh failure is only acted on at the **next** run, so a job can land on a node that broke five minutes ago.

> [!NOTE]
> On your Slurm version, `man slurm.conf` is the truth: older releases have a fixed 60-second kill and no `HealthCheckTimeout` knob.

---

## Life of a failure, end to end

Let's break `cn042` on purpose (on a test node, please):

```bash
# on cn042
umount -l /scratch
```

Within one `HealthCheckInterval`, `slurmd` runs NHC, `check_fs_mount_rw` fails, and the offline helper runs the equivalent of:

```bash
scontrol update NodeName=cn042 State=DRAIN Reason="NHC: check_fs_mount:  /scratch not mounted"
```

From the controller (the exact wording depends on the check and NHC version):

```text
$ sinfo -R -n cn042
REASON                                       USER  TIMESTAMP            NODELIST
NHC: check_fs_mount:  /scratch not mounted   root  2026-10-28T10:05:12  cn042
```

Running jobs keep running (the node is DRAINING, then DRAINED). No new jobs land. Now fix it:

```bash
mount /scratch
```

Next run, every check passes, the online helper sees a reason starting with `NHC:`, and resumes the node. Zero humans paged. That's the whole point.

---

## Draining etiquette for humans

Because of the `NHC:` handshake from [part 1](/fields/system-administration/node-health-check/why-node-health-check.md#the-nhc-handshake):

```bash
# ✅ Good: a reason that isn't NHC's. NHC will never resume this node.
scontrol update nodename=cn042 state=drain reason="ahmed: BIOS update, ticket 4711"

# ❌ Bad: no reason. NHC won't touch it, and in six weeks nobody remembers why.
scontrol update nodename=cn042 state=drain

# 🧠 Pro move: claim an NHC-drained node to stop it auto-resuming while you dig
scontrol update nodename=cn042 reason="ahmed: investigating flaky lustre"
```

Two more NHC 1.5 behaviors worth knowing:

- Nodes in Slurm's **`MAINT`** state are never resumed by NHC (Slurm rejects that transition anyway).
- Run with `-p` and NHC marks failures as **permanent**: the reason gets a `(perm)` tag and NHC won't resume it, ever. Good for hardware classes where any failure means an RMA.

---

## Boot and reboot: the sneaky part

`slurmd` runs the health check **when it starts, before it registers with the controller**. A failing check at boot means the node doesn't register as healthy. That's great when the check is right and baffling when your config is wrong (see [troubleshooting](/fields/system-administration/node-health-check/troubleshooting.md)).

Reboots via `scontrol reboot` used to be a mess: Slurm clears the DRAIN flag when a node comes back from an `ASAP` reboot, which could wipe out what the health check had decided. NHC 1.5 merged a set of fixes for this ([PR #115](https://github.com/mej/nhc/pull/115) by Trey Dockendorf). After a plain `scontrol reboot`, the helper keeps the node drained until NHC itself onlines it, and it no longer fights the `Reboot ASAP` reason. If you reboot nodes from automation, **run 1.5**.

---

## Prolog and Epilog: checks at job boundaries

The periodic check has a blind spot: the five minutes between runs. Job boundaries close it.

**Epilog: "did that job break the node?"** Jobs leave `/tmp` full, orphan processes behind, or trigger GPU errors. A short epilog check catches it before the next job lands:

```bash
#!/bin/bash
# /etc/slurm/epilog.d/50-nhc.sh  (slurm.conf: Epilog=/etc/slurm/epilog.d/*)
# NHC drains with a clear "NHC:" reason on failure. We exit 0 on purpose,
# so Slurm doesn't ALSO drain the node with a vaguer "Epilog error" reason.
/usr/sbin/nhc -n nhc-epilog -t 20 || true
exit 0
```

**Prolog: "is it safe to start?"** Here you *want* a non-zero exit. When a prolog fails, Slurm drains the node and requeues the job instead of letting it die:

```bash
#!/bin/bash
# /etc/slurm/prolog.d/50-nhc.sh
exec /usr/sbin/nhc -n nhc-prolog -t 15
```

> [!CAUTION]
> Every second in the prolog/epilog is a second added to **every** job. A 30-second epilog on a cluster doing 100,000 short jobs a day burns 830 node-hours of idle time. Keep these contexts tiny: mounts, GPU count, a `dmesg` Xid grep, done.

---

## Not on Slurm? PBS, Grid Engine, cron, Kubernetes

**PBS / TORQUE** (`mom_priv/config` on each MOM):

```text
$node_check_script /usr/sbin/nhc
$node_check_interval 5,jobstart,jobend
$down_on_error 1
```

That runs every 5 MOM intervals plus at job start and end. For NHC to offline nodes with notes, the nodes need operator rights: `qmgr -c "set server operators += root@*"`. The `NHC:` note rule works the same as in Slurm.

**Grid Engine family**: follow Dave Love's [SGE NHC recipe](https://arc.liv.ac.uk/SGE/howto/nhc-recipe.html), which upstream points to.

**LSF**: supported ("sorta", in upstream's own words) via `badmin hclose`/`hopen`.

**Plain cron**, for servers with no scheduler (storage nodes, login nodes), use `nhc-wrapper`. It de-duplicates results, so you get one e-mail when a problem appears, one when it clears, and a reminder while it persists:

```bash
# /etc/cron.d/nhc
*/5 * * * * root /usr/sbin/nhc-wrapper -M ops@example.org -X 12h -n nhc-oob
```

**Kubernetes**: NHC 1.5 ships `check_kube*` checks, and Azure documents a pattern that runs AzNHC in an init container and **taints** the node (`NoExecute`) on failure, the k8s equivalent of a drain.

Next up: getting this onto hundreds of nodes without draining all of them on the first run, in [part 5](/fields/system-administration/node-health-check/rollout-at-scale.md).

> **Takeaway:** three `slurm.conf` lines plus `NHC_RM=slurm`; keep NHC's timeout under Slurm's; use `CYCLE` on big clusters; never drain without a reason; run 1.5 if you reboot nodes from automation.

### References
- [`slurm.conf`: HealthCheckProgram / Interval / NodeState / Timeout](https://slurm.schedmd.com/slurm.conf.html#OPT_HealthCheckProgram)
- [NHC README: Slurm, TORQUE, Grid Engine integration, periodic execution, detached mode](https://github.com/mej/nhc#implementation)
- [NHC 1.5 release notes (Slurm reboot handling, MAINT, `-p`)](https://github.com/mej/nhc/releases/tag/1.5)
- [Slurm: Prolog and Epilog guide](https://slurm.schedmd.com/prolog_epilog.html)
- [Azure: Pre-job health checks on AKS](https://techcommunity.microsoft.com/blog/azurehighperformancecomputingblog/pre-job-health-checks-on-aks-a-guide-to-stable-ai-workloads/4195962)
