---
id: slurm-smoke-node-readiness
title: "Back From the Repair Shop: Is This Node Fit to Return to Service?"
order: 5
sidebar_label: Node readiness
summary: "Why idle does not mean a node is healthy, what Slurm does when hardware and slurm.conf disagree (and how config_overrides hides it), and a reservation fence for a probe job."
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
    - slurm-gpu-health-checks
    - slurm-reservations-and-maintenance
    - slurm-reboot-order
    - slurm-kill-task-failed
---

# Back From the Repair Shop: Is This Node Fit to Return to Service?

> **Part 5 of [Slurm Smoke Tests](/fields/schedulers/slurm-smoke-tests/README.md).** The commands and outputs below were run on a two-node test cluster (Slurm 23.11.4, accounting on, both `slurmd` daemons on one Ubuntu 24.04 machine, which has 2 CPUs and about 8 GB of memory). **The test cluster has no GPUs**, so nothing here was run against one, and the GPU section says so. The names and the story are invented. For the health-check program that drains a node by itself, read [When a GPU Falls Off the Bus](/fields/schedulers/slurm-ai-clusters/gpu-health-checks.md), which this page does not repeat.

## Table of Contents

- [Back From the Repair Shop: Is This Node Fit to Return to Service?](#back-from-the-repair-shop-is-this-node-fit-to-return-to-service)
  - [Table of Contents](#table-of-contents)
  - [Node 17 is idle](#node-17-is-idle)
  - [What `idle` does and does not prove](#what-idle-does-and-does-not-prove)
  - [What Slurm does by default](#what-slurm-does-by-default)
  - [Compare the hardware with the promise](#compare-the-hardware-with-the-promise)
  - [Run a probe before the users do](#run-a-probe-before-the-users-do)
  - [Let a health check do the routine part](#let-a-health-check-do-the-routine-part)
  - [And the GPUs?](#and-the-gpus)
  - [Version notes](#version-notes)
  - [Back to node 17](#back-to-node-17)
  - [References](#references)

---

## Node 17 is idle

Node 17 spends a week at the repair shop and comes back with a new motherboard. The technician resets the BIOS to defaults on the way, which turns off half the cores. Nobody remarks on this, because nobody looked.

The admin plugs it in. The cluster's `slurm.conf` was copied from a cloud template and sets `config_overrides`, a setting that makes the controller believe the file and not the hardware. `slurmd` starts, registers with the controller, and `sinfo` prints `idle`. The admin is relieved and resumes the node. For the next two days a handful of jobs that asked for 64 CPUs on node 17 run half as fast as their siblings, and one time out. The users blame the filesystem. The admin blames the users. The node is exactly as broken as it was on arrival, and Slurm has been calling it idle the whole time.

The word `idle` means that `slurmd` is running and has registered. It says nothing about whether the machine behind it is the machine the configuration describes.

---

## What `idle` does and does not prove

| What you see | What it proves | What it does not |
|---|---|---|
| `idle` in `sinfo` | `slurmd` is up and the controller heard from it | That the CPUs, memory or devices are what `slurm.conf` says |
| A passing job on the node | One task ran | That the node is *healthy*; the job may have been tiny |
| `scontrol show node` numbers | What the controller was **told** | What the node **has**, if `config_overrides` is on |

The third row is the sneaky one, and it is worth seeing happen.

---

## What Slurm does by default

On the test cluster, `slurm.conf` says each node has `CPUs=4`. The machine really has 2. With the site's usual setting, `SlurmdParameters=config_overrides`, the controller believes the file and the nodes show `idle`. Then that line was removed, the daemons restarted, and the same file with the same nodes gave:

```text
NODELIST STATE
node1 inval
node2 inval

NODELIST REASON
node[1-2] Low socket*core*thread count, Low CPUs
```

By default, Slurm compares what `slurmd` finds with what the file claims, and refuses to let a node with fewer resources than promised take jobs. That is exactly the protection node 17 would have had. `config_overrides` ("use the configuration file, ignore the hardware") is a legitimate setting, common in containers, test clusters and some cloud setups, and it turns the protection off. With it on, you do the comparison yourself.

After the file was fixed to say `CPUs=2` and the daemons were restarted, the nodes came back as `idle` and the comparison below passed.

---

## Compare the hardware with the promise

`slurmd -C` prints what the daemon detects on the machine it runs on, in the format of a `NodeName=` line. The controller's view is in `scontrol show node`. This script, run on the node itself, compares the two and checks the state:

The script is [`node-fit.sh`](/fields/schedulers/slurm-smoke-tests/smoke-scripts/node-fit.sh), a plain file you can read on this site, [open on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/node-fit.sh) or fetch with its [raw link](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/node-fit.sh).

With `config_overrides` on and the file saying `CPUs=4`, on a machine with two:

```text
FAIL  cpus    hardware 2, configured 4
PASS  memory  hardware 8022 MB, configured 1000 MB
PASS  state   IDLE
```

`sinfo` said `idle` for this node at the same moment. The `PASS` on state is the whole problem in one line. With the file corrected:

```text
PASS  cpus    hardware 2, configured 2
PASS  memory  hardware 8022 MB, configured 1000 MB
PASS  state   IDLE
```

Memory is checked in one direction only: configured must not exceed what the node has. A node configured for less than it has is wasteful but safe, and sites often leave headroom for the operating system on purpose. The script covers CPUs and memory. Sockets, cores, threads, GPUs and other generic resources need their own lines, in the same shape.

---

## Run a probe before the users do

Even a correct configuration does not prove a returning node can run a job: it may have a dead network card or an unmounted filesystem. The safest way to find out is to run a probe job on the node before anyone else can. The obvious plan fails:

```text
JobId  State    Reason
116    PENDING  ReqNodeNotAvail, UnavailableNodes:node2        (node2 drained, no reservation)
117    PENDING  ReqNodeNotAvail, UnavailableNodes:node2        (node2 drained, job inside a MAINT reservation)
```

A drained node accepts no new jobs, not even those inside a reservation. So the order matters: **fence the node first, then let it out**. A reservation that only you can use goes up while the node is still drained, and only then is the node resumed:

```bash
scontrol update NodeName=node2 State=DRAIN Reason="returning from repair"
scontrol create reservation ReservationName=probe StartTime=now Duration=10 \
    Nodes=node2 Users=tester Flags=MAINT
scontrol update NodeName=node2 State=RESUME
```

The node was idle, and yet an ordinary user's job asking for it waited:

```text
job 118: PENDING ReqNodeNotAvail, May be reserved for other job
```

A job in the reservation ran:

```bash
sbatch -w node2 --reservation=probe -t 1 --wrap='hostname; echo SLURMD_NODENAME=$SLURMD_NODENAME'
```

```text
vm
SLURMD_NODENAME=node2
```

`sacct` recorded it as `COMPLETED`. The last step is to release the fence, and the waiting job started on the node as soon as it went:

```bash
scontrol delete ReservationName=probe
```

The `Duration=10` is a safety net: if you forget the last step, the fence expires on its own after ten minutes. Make the probe job honest. A one-line `hostname` proves the node accepts jobs; a real probe should exercise what the node is for: write a file to the shared filesystem, load the software stack, run a short GPU kernel, a network ping to another node. The [reservations page](/fields/schedulers/slurm-cluster-operations/slurm-reservations-and-maintenance.md) explains what else a reservation does, including that it never kills jobs already running.

---

## Let a health check do the routine part

A probe is for the moment a node comes back. For everything after that, Slurm can run a program on every node on a timer and drain the ones that fail. The setting is `HealthCheckProgram` together with `HealthCheckInterval`, and the [GPU health-check page](/fields/schedulers/slurm-ai-clusters/gpu-health-checks.md) builds and tests one, including a bug where it overwrote the administrator's drain reason. A ready-made option is LBNL's Node Health Check (NHC). Its documentation shows it wired in with two lines:

```text
HealthCheckProgram=/usr/sbin/nhc
HealthCheckInterval=300
```

It is configured in `/etc/nhc/nhc.conf` with one check per line, for example `check_fs_mount_rw /`, `check_hw_cpuinfo 2 8 8` and `check_hw_physmem 1k 1TB`, which cover much of what `node-fit.sh` does by hand. NHC was not installed on the test cluster, so none of this was run. The `slurm.conf` it needs must match across the whole cluster, as its documentation notes.

---

## And the GPUs?

The test cluster has none, so this part is a plan and not a result. A node-fit check for a GPU node should compare the number of GPUs the machine reports (`nvidia-smi -L`) with the number configured for the node (the `Gres` line in `scontrol show node`), and the probe job should run something on each GPU, not only list them. A GPU that has "fallen off the bus" still has an entry in the configuration. The GPU health-check page has a tested version of the idea for a missing device.

---

## Version notes

Run on 23.11.4. The GPU health-check page notes that a per-GPU drain, draining one GPU instead of the whole node, comes in 26.11. The hardware comparison and the reservation fence were not run on any other version. Whether the default `inval` behaviour is the same on newer releases was not checked.

---

## Back to node 17

Replay the afternoon with the checks. The admin plugs node 17 in and runs `node-fit.sh` on it before resuming anything:

```text
FAIL  cpus    hardware 32, configured 64
PASS  memory  hardware 512000 MB, configured 500000 MB
FAIL  state   DRAIN
```

(Node 17's numbers are invented. The shape is the output above. The `state` line fails because the node is still drained, which is expected before it is resumed. The `cpus` line is the one that matters.) The failure takes seconds to find and a trip into the BIOS to fix. Then the fence goes up, the node is resumed, a probe job runs from the reservation and writes to the shared filesystem, and the fence comes down. Two days later nobody has any theories about the filesystem.

**Takeaway:** `idle` only means the daemon registered, so before a node returns to service compare what `slurmd -C` finds with what the controller was told (especially with `config_overrides`, which hides the difference), then fence the node with a reservation and run a real probe job before users can.

**Next:** [When Smoke Becomes a Fire Drill](/fields/schedulers/slurm-smoke-tests/slurm-smoke-regression-suites.md) covers the heavier tools, SchedMD's own test suite and ReFrame, and where to stop.

---

## References

- [Slurm: slurm.conf](https://slurm.schedmd.com/slurm.conf.html) (`SlurmdParameters=config_overrides`, `HealthCheckProgram`)
- [Slurm: slurmd](https://slurm.schedmd.com/slurmd.html) (`-C`)
- [Slurm: Advanced Resource Reservation Guide](https://slurm.schedmd.com/reservations.html)
- [LBNL Node Health Check user guide](https://lbnl-node-health-check.readthedocs.io/en/sphinx-docs/user_guide.html)
