---
id: linux-memory-pressure-overview
title: Linux Memory Pressure - Overview
sidebar_label: Overview
summary: A six-part series on what Linux does when RAM runs short - reclaim, PSI, the OOM killer, cgroup levers, memory locking - and how to build a rescuer that still works at the worst moment.
level: intermediate
type: concept
domains: [systems-and-hpc]
---

# Linux Memory Pressure - Overview

> A six-part series on the moment a Linux machine runs short of memory, and on the program whose job is to act then. By the end you'll read `/proc/meminfo` and PSI without panic, predict which process the OOM killer picks, know every cgroup lever from throttle to kill, and be able to explain why a rescuer must lock its own memory in RAM.

## The route

| # | Page | The question it answers |
|---|------|-------------------------|
| 1 | [How Linux reclaims memory](/fields/system-administration/linux-memory-pressure/how-linux-reclaims-memory.md) | Why is free memory near zero normal, and when does a program actually stall? |
| 2 | [Memory pressure (PSI)](/fields/system-administration/linux-memory-pressure/memory-pressure-psi.md) | How do you measure trouble in time lost, not bytes left? |
| 3 | [The OOM killer](/fields/system-administration/linux-memory-pressure/the-oom-killer.md) | Who gets killed, why so late, and how do you shield or sacrifice a process? |
| 4 | [cgroup v2 memory control](/fields/system-administration/linux-memory-pressure/cgroup-v2-memory-control.md) | What can you do about it, gentlest step first? |
| 5 | [Memory locking (mlockall)](/fields/system-administration/linux-memory-pressure/memory-locking-mlockall.md) | How does the rescuer avoid being swapped out when it is needed most? |
| 6 | [The rescuer checklist](/fields/system-administration/linux-memory-pressure/rescuer-checklist.md) | What else keeps it alive, and what is the whole checklist? |

Each page ends with the question the next one answers. The series follows one story: **see the pressure (1, 2), know what happens if you're late (3), pull the levers (4), and stay alive while you do it (5, 6)**.

## Versions

Written against Ubuntu 26.04, Linux 7.0 and systemd as shipped there. The numbers shown "on my machine" were measured there. Several levers are newer than the kernels many clusters run, and distributions backport features, so check your own kernel.

| Feature | Added in Linux | Used on page |
|---------|----------------|--------------|
| PSI (`/proc/pressure/*`) | 4.20 (some distro kernels need `psi=1`) | 2 |
| `vm.swappiness` up to 200 | 5.8 | 1 |
| `cgroup.freeze` | 5.2 | 4 |
| `cgroup.kill` | 5.14 | 4 |
| `memory.reclaim` | 5.19 | 4 |
| `RLIMIT_MEMLOCK` default 8 MiB (was 64 KiB) | 5.16 | 5 |

Kernel versions here come from the kernel release history and man pages, except the memory-locking default, which is from getrlimit(2).

## Who this is for

Anyone running Linux machines under load: sysadmins and HPC engineers who have been paged for "the node froze", and developers writing a watchdog, a job killer or an autoscaler. You need to be comfortable with a shell and know what a process is. Everything else is explained with a story first.

## Contents

| File | Description |
|------|-------------|
| [how-linux-reclaims-memory](/fields/system-administration/linux-memory-pressure/how-linux-reclaims-memory.md) | Page cache, swap, kswapd and direct reclaim |
| [memory-pressure-psi](/fields/system-administration/linux-memory-pressure/memory-pressure-psi.md) | Pressure Stall Information and PSI triggers |
| [the-oom-killer](/fields/system-administration/linux-memory-pressure/the-oom-killer.md) | Victim scoring, oom_score_adj and why the kernel is late |
| [cgroup-v2-memory-control](/fields/system-administration/linux-memory-pressure/cgroup-v2-memory-control.md) | memory.min/low/high/max, reclaim, freeze, kill |
| [memory-locking-mlockall](/fields/system-administration/linux-memory-pressure/memory-locking-mlockall.md) | Pinning a rescuer in RAM, and the 8 MiB limit |
| [rescuer-checklist](/fields/system-administration/linux-memory-pressure/rescuer-checklist.md) | Real-time priority, OOM shield, watchdog, and the checklist |

## Related reading in this repo

- [System administration: memory](/fields/system-administration/memory.md): memory bugs in applications (segfaults, leaks, buffer overflows).
- [Node health check](/fields/system-administration/node-health-check/README.md): detecting and draining unhealthy cluster nodes.
