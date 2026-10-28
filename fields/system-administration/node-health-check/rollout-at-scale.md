---
id: nhc-rollout-at-scale
title: Rolling NHC Out to a Fleet Without Draining Everything
sidebar_label: "5. Rolling out to a fleet"
order: 5
summary: A dry-run, canary, enforce plan for deploying NHC or a new nhc.conf to hundreds of nodes, with a circuit breaker for bad pushes.
level: intermediate
type: guide
domains: [systems-and-hpc]
tags: [hpc, slurm]
relations:
  prerequisites: [nhc-slurm-integration]
---

# Rolling NHC Out to a Fleet Without Draining Everything

> **Part 5 of the [Node Health Check series](/fields/system-administration/node-health-check/README.md).** A config typo in `nhc.conf` is the fastest way to take a 2,000-node cluster to zero. Here's how to make that impossible, or at least boring.

## Table of Contents
- [The failure mode we're designing against](#the-failure-mode-were-designing-against)
- [Phase 0: inventory](#phase-0-inventory)
- [Phase 1: dry run, fleet-wide](#phase-1-dry-run-fleet-wide)
- [Phase 2: triage, config bug or node bug?](#phase-2-triage-config-bug-or-node-bug)
- [Phase 3: canary, enforcing on a few nodes](#phase-3-canary-enforcing-on-a-few-nodes)
- [Phase 4: enforce everywhere, with a circuit breaker](#phase-4-enforce-everywhere-with-a-circuit-breaker)
- [Day two: logs, metrics and config changes](#day-two-logs-metrics-and-config-changes)
- [Jitter: the "NHC slowed my job" conversation](#jitter-the-nhc-slowed-my-job-conversation)

---

## The failure mode we're designing against

You push a config with `check_hw_physmem 512GB 512GB` and no fudge factor. The kernel on every node reports 503 GB. Within five minutes, every node in the partition is `drain` with `NHC: check_hw_physmem: ...`. Running jobs finish; nothing new starts. Your queue grows; your phone rings.

Health checks are a **fleet-wide kill switch** you hand to a config file. Treat changes to that file like production deployments, because they are.

The plan below works for the first NHC rollout and for every config change after it.

---

## Phase 0: inventory

Know your hardware classes before writing expectations about them:

```bash
clush -bw @compute "/usr/sbin/nhc-genconf -H '*' -c -"
```

`clush -b` folds identical output together, so each block is one hardware class with its node list. Three blocks where you expected one? You just found the nodes with a missing DIMM or a BIOS that disabled hyperthreading. Write the config from the *majority* of each class ([part 3](/fields/system-administration/node-health-check/writing-nhc-conf.md)).

---

## Phase 1: dry run, fleet-wide

Install the package and config everywhere, but **don't** set `HealthCheckProgram` yet. Run NHC by hand, in check-all mode, with draining disabled:

```bash
clush -bw @compute "/usr/sbin/nhc -a -l- MARK_OFFLINE=0" 2>&1 | tee nhc-dryrun.txt
```

- `-a` reports **every** failure, not just the first.
- `-l-` prints to stdout so `clush` can collect it.
- `MARK_OFFLINE=0` guarantees nothing gets drained.

Healthy nodes print nothing. With `-b`, failing nodes collapse into groups by identical message, so 2,000 nodes of output become a dozen readable blocks.

> [!TIP]
> Run the dry run **twice**, at different times of day. Checks like `check_ps_loadavg` and `check_fs_free` behave very differently at 3 AM and during the 10 AM job storm.

---

## Phase 2: triage, config bug or node bug?

For each block of failures, ask one question:

| If the failure is on... | It's probably... | Do this |
|-------------------------|------------------|---------|
| All (or most) nodes of a class | A **config bug**: your expectation is wrong | Fix the line: add a fudge factor, correct the count, fix the target |
| A handful of nodes | A **node bug**: those nodes really are different | Fix the nodes, or drain them yourself *with a human reason* |
| Random nodes, changing each run | A **flaky check** | Make it more robust (retries, tolerance) or drop it |

Iterate until the dry run is quiet except for nodes that are *really* broken and that you've consciously drained.

---

## Phase 3: canary, enforcing on a few nodes

`slurm.conf` must be identical on all nodes, so you can't enable `HealthCheckProgram` on just 16 of them. Instead, enable it everywhere and do the canary **inside `nhc.conf`**, since lines run in order and later assignments win:

```bash
# top of /etc/nhc/nhc.conf during the canary
                 * || export MARK_OFFLINE=0
      {cn[001-016]} || export MARK_OFFLINE=1
```

Now every node runs every check and logs failures, but only `cn001-016` can actually drain. Leave it a few days. Watch `/var/log/nhc.log` across the fleet and `sinfo -R` on the canaries.

Then widen: `{cn[001-128]}`, then delete both lines.

---

## Phase 4: enforce everywhere, with a circuit breaker

Even with a perfect rollout, a future change will eventually go wrong. Add a **circuit breaker**: something outside NHC that notices when "too many" nodes are NHC-drained, and screams.

```bash
#!/bin/bash
# /usr/local/sbin/nhc-circuit-breaker  -- run every few minutes on the controller
# Alerts if more than MAX_PCT of nodes are drained by NHC.
MAX_PCT=${MAX_PCT:-5}

total=$(sinfo -h -N -o '%N' | sort -u | wc -l)
nhc_drained=$(sinfo -h -N -R -o '%N|%E' | awk -F'|' '$2 ~ /^NHC/ {print $1}' | sort -u | wc -l)
(( total > 0 )) || exit 0
pct=$(( 100 * nhc_drained / total ))

if (( pct >= MAX_PCT )); then
    msg="NHC drained ${nhc_drained}/${total} nodes (${pct}%). Possible bad nhc.conf push."
    logger -t nhc-circuit-breaker -p user.crit "$msg"
    # page a human: replace with your webhook / Alertmanager / mail
    echo "$msg" | mail -s "[CRIT] NHC circuit breaker" ops@example.org
fi
```

What should happen when it trips? At minimum, a page. Bolder sites also flip a kill switch: push `* || export MARK_OFFLINE=0` to the top of `nhc.conf` cluster-wide, so NHC keeps logging but stops draining until a human looks.

> [!WARNING]
> Don't make the breaker auto-resume nodes. If 30% of your nodes really did lose Lustre, resuming them recreates 600 black holes at once. Stop *new* drains; let a human decide about existing ones.

---

## Day two: logs, metrics and config changes

**Config lives in Git.** Every change gets a pull request and a one-line "why". When a node drains on Tuesday, `git log -p nhc.conf` tells you whether Monday's change did it.

**Every config change replays phases 1 to 3 in miniature:** dry run the new file on the fleet without installing it (process substitution works for `-c` in 1.5), then canary.

```bash
# copy candidate.conf to the nodes first (clush --copy), then:
clush -bw @compute "/usr/sbin/nhc -a -l- -c /tmp/candidate.conf MARK_OFFLINE=0"
```

**Logs.** `/var/log/nhc.log` on each node (logrotate snippet included), failures also to syslog. NHC 1.5 can format syslog messages as **JSON** (`-j`, or `NHC_FMT_JSON=1`), which your log pipeline (Loki, Elastic, Splunk) will parse without regex sorcery.

**Metrics worth graphing:**

- Count of nodes with an `NHC:` reason, over time (the circuit breaker's number).
- Top 10 NHC failure messages this week. The top one is your next hardware conversation or config fix.
- Time from NHC drain to resume. Long tails mean manual work you could automate ([part 7](/fields/system-administration/node-health-check/auto-remediation.md)).

A crude exporter is ten lines: `sinfo -h -N -R -o '%E'` piped into a textfile for node_exporter's textfile collector.

---

## Jitter: the "NHC slowed my job" conversation

Sooner or later, someone running a tightly coupled MPI code will ask whether NHC is stealing their cycles. Upstream designed NHC to keep "OS jitter" minimal (bash builtins, few forks) and reports no significant jitter in practice, including on very sensitive systems. If it *is* a concern on your cluster, upstream's own suggestions:

1. Raise `HealthCheckInterval` from 300 to 3600 seconds.
2. Use `HealthCheckNodeState=IDLE` (or `NONDRAINED_IDLE`, knowing [the trade-off](/fields/system-administration/node-health-check/slurm-integration.md#which-nodes-should-get-checked-healthchecknodestate)) so busy nodes aren't checked.
3. Have heavier checks skip or slim down when a job is running on the node, and rely on the epilog to cover job boundaries.

Measure before and after with the user's actual code. Feelings are not a benchmark.

> **Takeaway:** dry run with `-a -l- MARK_OFFLINE=0` across the fleet, triage config bugs vs node bugs, canary with `MARK_OFFLINE` inside `nhc.conf`, then enforce behind a circuit breaker. Every config change after that repeats the cycle.

### References
- [NHC README: Testing, Periodic Execution and the jitter note](https://github.com/mej/nhc#testing)
- [NHC 1.5 release notes (JSON syslog, PID file, config from pipes)](https://github.com/mej/nhc/releases/tag/1.5)
- [ClusterShell documentation](https://clustershell.readthedocs.io/)
