---
id: slurm-reboot-order
sidebar_label: Rebooting a Slurm Cluster
order: 12
level: intermediate
type: [concept, experiment]
domains: [systems-and-hpc, system-design]
summary: "The step-by-step order for rebooting a Slurm cluster: drain, lock access, control plane first, then front-end and compute nodes, and reopen in a controlled way."
tags: [slurm, hpc]
relations:
  related: [slurm-upgrade-order, slurm-spool-dir-full]
---
# Rebooting a Slurm Cluster Without Losing Your Job (Or Anyone Else's)

> **Part of the `schedulers/` series.** Sourced and expanded from a [classic r/HPC thread](https://www.reddit.com/r/HPC/comments/ipij91/slurm_reboot_order/) that every cluster admin eventually rediscovers the hard way. The full-outage sequence is for when the control plane needs rebooting too; if only compute nodes do, [Slurm can do it for you](#when-only-the-compute-nodes-need-a-reboot) without an outage.

## Table of Contents
- [Rebooting a Slurm Cluster Without Losing Your Job (Or Anyone Else's)](#rebooting-a-slurm-cluster-without-losing-your-job-or-anyone-elses)
  - [Table of Contents](#table-of-contents)
  - [The question every new admin eventually asks](#the-question-every-new-admin-eventually-asks)
  - [Before you touch anything: five things to have ready](#before-you-touch-anything-five-things-to-have-ready)
  - [The full reboot sequence](#the-full-reboot-sequence)
    - [Phase 0 — Scheduling](#phase-0--scheduling)
    - [Phase 1 — Locking down access](#phase-1--locking-down-access)
    - [Phase 2 — Control plane first](#phase-2--control-plane-first)
    - [Phase 3 — Front-end nodes](#phase-3--front-end-nodes)
    - [Phase 4 — Compute nodes](#phase-4--compute-nodes)
    - [Phase 5 — Controlled reopening](#phase-5--controlled-reopening)
  - [The order, visualized](#the-order-visualized)
  - [Why this order and not another](#why-this-order-and-not-another)
  - [When only the compute nodes need a reboot](#when-only-the-compute-nodes-need-a-reboot)
  - [The honest caveat](#the-honest-caveat)
  - [References](#references)

---

## The question every new admin eventually asks

> *"What's the actual order for restarting the nodes? At what point do I drain the compute nodes? Should `slurmdbd`, `slurmd`, and `slurmctld` stay auto-enabled across a reboot? Do I just `shutdown -r now` a node, or stop the daemons first with `scontrol shutdown`? And where does a maintenance reservation fit into all of this?"*

This is a rite of passage — everyone runs into it the first time they need to patch a Slurm cluster without a) losing queued jobs, b) corrupting the accounting database, or c) getting paged at 2 AM because a node came back up in a weird state and started eating jobs it shouldn't have. Below is the order that actually works, assuming **you are not upgrading Slurm itself** — just patching/rebooting the underlying OS.

---

## Before you touch anything: five things to have ready

Skipping this section is how a 2-hour maintenance window turns into a 14-hour incident.

- [ ] **Estimate the work and the time it'll take.** Vague estimates turn into angry Slack threads from users mid-maintenance.
- [ ] **Prepare a small test job.** A tiny `xhpl` instance is perfect — cheap to run, and immediately tells you if compute nodes are actually healthy post-reboot.
- [ ] **Create a hidden Slurm partition reserved for you (root only).** You want somewhere to test job submission *before* opening the floodgates back to real users.
- [ ] **Have a node-health-check mechanism ready** — [NHC (Node Health Check)](https://github.com/mej/nhc) or equivalent, so bad nodes get flagged automatically instead of silently eating jobs.
- [ ] **Confirm you have root credentials and OOB/BMC/IPMI console access to every server.** Losing thousands of core-hours because a node hung at GRUB and you couldn't remember how to reach its console is a genuinely common, genuinely avoidable failure mode.

> [!TIP]
> If you have a test/lab system, dry-run the entire upgrade path there before day D. There is no substitute for having already seen the failure once.

---

## The full reboot sequence

### Phase 0 — Scheduling

1. **Estimate when currently running jobs will finish**, and schedule your maintenance start time safely after that. Pick your weekday carefully:
   > [!WARNING]
   > **Avoid Thursdays and Fridays.** Users can't submit new jobs during the blackout, the system sits under-utilized over the weekend, and if something breaks Friday night, nobody's around to help you fix it.
2. **Create a reservation with the `MAINT` flag**, starting at your chosen time — with a safe overlap buffer built in, because maintenance windows always run long.
3. **Wait for day D, time T.** If you have a test/lab system, use the waiting period to dry-run the upgrade path there.

### Phase 1 — Locking down access

4. **Place `/etc/nologin` on the front-end/login nodes** to block non-root users from doing anything unexpected while you work. *(Make sure your own root login still works before you do this.)*
5. **Confirm `State=DOWN` is set on partitions in `slurm.conf`** — this is your safety net against a badly-restarted `slurmd`/node grabbing and executing jobs before you're ready.

### Phase 2 — Control plane first

6. **Stop and disable `slurmctld`, then `slurmdbd`** — controller before database daemon, in that order.
7. **Take a consistent backup of the Slurm SQL database.** This is your one clean window to do it — everything is quiesced, nothing is writing to it mid-backup. Future-you will be extremely grateful you didn't skip this step.
8. **Stop and disable MariaDB/MySQL.**
9. **Reboot the Slurm and DB servers** and perform whatever underlying OS maintenance you actually came here to do.
10. **Bring services back up in order: DB → `slurmdbd` → `slurmctld`.** Check the logs carefully — confirm services started cleanly *and* that partitions are genuinely showing `DOWN` (not silently back up and accepting work).

### Phase 3 — Front-end nodes

11. **Reboot the front-end/login servers now** that the control plane is confirmed healthy. Re-apply `/etc/nologin` here too — it gets wiped during the boot process, so it won't persist automatically.
12. **Verify InfiniBand, filesystem mounts, and Slurm client connectivity** on the front-ends. Kernel version changes are a classic way to break third-party kernel modules (IB drivers especially) — don't assume "it booted" means "it works." Once confirmed healthy, remove `/etc/nologin` and let users back onto the front-ends. Partitions are still `DOWN`, so they can queue jobs — nothing will actually execute yet.

### Phase 4 — Compute nodes

13. **Reboot the compute nodes.** If they're already empty (which they should be, per your Phase 0 scheduling), there's no real need to fuss with drain state first.
14. **Clear the "unexpectedly rebooted" flag** by setting node state to `idle`, and let your node health check mechanism (NHC or equivalent) do its job of flagging anything unhealthy.

### Phase 5 — Controlled reopening

15. **Flip your hidden root-only partition to `UP`** and submit your test job (that small `xhpl` instance from your prep checklist) there first.
16. **If the test job runs clean — open the real partitions.** `State=UP`, and you're done.

---

## The order, visualized

```
 Phase 0: Schedule           Phase 1: Lock down          Phase 2: Control plane
 ┌───────────────────┐      ┌─────────────────────┐     ┌──────────────────────┐
 │ Estimate end time  │      │ /etc/nologin on      │     │ Stop slurmctld        │
 │ of running jobs    │─────►│ front-ends            │────►│ Stop slurmdbd         │
 │ Create MAINT        │      │ Set State=DOWN on     │     │ Backup SQL DB ★       │
 │ reservation         │      │ partitions            │     │ Stop MariaDB/MySQL    │
 └───────────────────┘      └─────────────────────┘     │ Reboot Slurm/DB hosts │
                                                          │ Start: DB→slurmdbd→   │
                                                          │        slurmctld      │
                                                          └──────────────────────┘
                                                                     │
          ┌──────────────────────────────────────────────────────────┘
          ▼
 Phase 3: Front-ends              Phase 4: Compute nodes         Phase 5: Reopen
 ┌────────────────────────┐      ┌───────────────────────┐     ┌───────────────────┐
 │ Reboot front-ends        │      │ Reboot compute nodes   │     │ Hidden partition→UP │
 │ Re-apply /etc/nologin     │─────►│ Set state=idle          │────►│ Run test job         │
 │ Verify IB / FS / Slurm    │      │ Let NHC flag bad nodes  │     │ If clean: partitions │
 │ Remove /etc/nologin        │      │                         │     │ → UP. Done.           │
 └────────────────────────┘      └───────────────────────┘     └───────────────────┘
```

★ = the one irreversible step in the whole sequence — get your DB backup *before* touching MariaDB/MySQL, not after.

---

## Why this order and not another

The sequence isn't arbitrary — it follows a simple dependency chain:

```
Database  →  slurmdbd  →  slurmctld  →  front-ends  →  compute nodes
(source of  (needs DB   (needs        (need a        (need a
 truth)      to start)   slurmdbd)     controller      controller
                                        to talk to)     accepting
                                                         work — but
                                                         kept DOWN
                                                         until you
                                                         say so)
```

Bring anything up out of order — say, compute nodes before the controller is confirmed healthy — and you risk exactly the failure mode this whole checklist exists to prevent: a node rejoining the pool in a bad state and silently swallowing jobs before you've verified anything.

---

## When only the compute nodes need a reboot

Most reboots aren't whole-cluster events. A kernel or driver update on the compute nodes doesn't need the controller, the database or the login nodes to go anywhere. For that, Slurm has a rolling reboot built in:

```bash
scontrol reboot ASAP nextstate=RESUME reason="kernel CHG-2001" cn[001-400]
```

| Piece | What it does |
| --- | --- |
| `reboot` | Runs `RebootProgram` from `slurm.conf` on each node when it's idle. Nothing happens without `RebootProgram` set |
| `ASAP` | Drains each node right away, so no new jobs land there; running jobs finish normally first |
| `nextstate=RESUME` | Clears the drain and the reason once the node has rebooted and slurmd registered again. `nextstate=DOWN` leaves it down for you to check. With `ASAP` and no `nextstate`, newer man pages (26.11) say it defaults to `UNDRAIN`; the 23.11 page doesn't say, so set it explicitly |
| `reason=` | What `sinfo -R` shows while it's out. Put the ticket there |

We ran it on two lab nodes (Slurm 23.11.4, `RebootProgram=/usr/sbin/reboot`): cn001 was idle, cn002 had a 40-second job.

```text
NODELIST STATE    REASON
cn001    reboot^  kernel CHG-2001 : reboot issued
cn002    draining@ kernel CHG-2001
```

cn001 went straight to reboot (`^` = reboot issued). cn002 drained (`@` = reboot pending) and waited; its job finished `COMPLETED 0:0`, and only then did the node reboot. No job was killed, and nobody ran a loop.

The last step didn't complete in our lab, and the reason is worth knowing. Both containers did reboot, but stayed in `reboot^` until we resumed them by hand. The controller only accepts a reboot once the node reports a **boot time later than the reboot request** (`waiting_for_node_boot()` in `node_mgr.c`), and containers report their host's boot time, so it never moves. On real hardware the boot time changes and the node returns on its own. The same check is what catches a node that *didn't* reboot: after `ResumeTimeout` it's marked `DOWN` instead of quietly resuming.

When to use which:

| Situation | Use |
| --- | --- |
| Compute nodes only: kernel, driver, firmware | `scontrol reboot ASAP nextstate=RESUME`, maybe a few racks at a time |
| You need a canary and a health check before resume | A rolling playbook, like [Rolling maintenance](/fields/devops/ansible/rolling-maintenance.md) in the Ansible series |
| Controller, database or login nodes too | The full sequence on this page |

`nextstate=RESUME` puts the node back as soon as slurmd registers, but not blindly: the man page says slurmd runs `HealthCheckProgram` once after the reboot, *before* it registers. If that's [NHC](/fields/system-administration/node-health-check/README.md), a node that comes back without its mounts or GPUs is drained instead of resumed.

---

## The honest caveat

This exact sequence scales down cleanly to a handful of nodes and a weekend maintenance window. On genuinely large systems, expect the process to stretch, and expect pressure from whoever's paying the bills — **every hour of downtime on a large cluster can cost thousands of euros**, and that pressure is real regardless of how careful you're being. Two things help more than anything else at that scale: a longer prep list than you think you need, and enough colleagues in the loop that the to-do list isn't resting on one person's memory at 3 AM.

**Takeaway:** for a whole-cluster outage, go database → slurmdbd → slurmctld → front-ends → compute with partitions held `DOWN`; for compute-only reboots, let `scontrol reboot ASAP nextstate=RESUME` drain and return each node for you.

---

## References

- [scontrol(1): reboot](https://slurm.schedmd.com/scontrol.html#OPT_reboot): `ASAP`, `nextstate`, `reason`.
- [slurm.conf(5): RebootProgram](https://slurm.schedmd.com/slurm.conf.html#OPT_RebootProgram), [ResumeTimeout](https://slurm.schedmd.com/slurm.conf.html#OPT_ResumeTimeout), [ReturnToService](https://slurm.schedmd.com/slurm.conf.html#OPT_ReturnToService).
- [sinfo(1): node state codes](https://slurm.schedmd.com/sinfo.html#SECTION_NODE-STATE-CODES): `@` reboot pending, `^` reboot issued.
- [Slurm reservations](https://slurm.schedmd.com/reservations.html): the `MAINT` flag.
- [Slurm source, `node_mgr.c`](https://github.com/SchedMD/slurm/blob/slurm-23-11-4-1/src/slurmctld/node_mgr.c): `waiting_for_node_boot()`, the boot-time check.
- [r/HPC: Slurm reboot order](https://www.reddit.com/r/HPC/comments/ipij91/slurm_reboot_order/): the thread this page grew from.