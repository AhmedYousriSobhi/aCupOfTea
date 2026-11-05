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

Written against Ubuntu 26.04, Linux 7.0 and systemd as shipped there. The numbers shown "on my machine" were measured there. The PSI trigger, `memory.high` hang, `mlockall` limit, `oom_score_adj` and watchdog claims were also tested in a clean Ubuntu 22.04 VM (Linux 5.15, systemd 249) and the pages say where the two differ. Several levers are newer than the kernels many clusters run, and distributions backport features, so check your own kernel.

| Feature | Added in Linux | Used on page |
|---------|----------------|--------------|
| PSI (`/proc/pressure/*`) | 4.20 (some distro kernels need `psi=1`) | 2 |
| `vm.swappiness` up to 200 | 5.8 | 1 |
| `cgroup.freeze` | 5.2 | 4 |
| `cgroup.kill` | 5.14 | 4 |
| `memory.reclaim` | 5.19 | 4 |
| `RLIMIT_MEMLOCK` default 8 MiB (was 64 KiB) | 5.16 | 5 |

### What changed since Ubuntu 22.04

The pages were tested in clean VMs on Ubuntu 22.04 (Linux 5.15, systemd 249) and Ubuntu 26.04 (Linux 7.0.0-34, systemd 259.5), and the examples were written on a 26.04 machine. This is what differs. "Tested" means a command was run in the VM; "seen" means read from a machine without changing anything; "docs" means taken from release notes or kernel docs and not run.

| Area | Ubuntu 22.04 (5.15, systemd 249) | Ubuntu 26.04 (7.0, systemd 259) | Basis |
|------|----------------------------------|---------------------------------|-------|
| `memory.reclaim` | Absent | Present | Tested |
| `memory.reclaim` argument `swappiness=` | Not available | Accepted: values 0, 60 and `max` parsed, 201 and unknown keys refused with `EINVAL` | Tested. [Patch series](https://patchew.org/linux/20240103164841.2800183-1-schatzberg.dan@gmail.com/20240103164841.2800183-3-schatzberg.dan@gmail.com) |
| `memory.reclaim` write on a group holding 200 MiB of anonymous memory, no swap | n/a | Returned `EAGAIN` at once (under 1 ms) and freed nothing. Not measured where pages can be reclaimed | Tested |
| `memory.peak`, `memory.swap.peak`, `memory.swap.high`, `memory.zswap.max`, `memory.zswap.writeback`, `cgroup.pressure`, `memory.oom.group` | Not checked | Present in a new cgroup. Writing to `memory.peak` and `memory.swap.peak` is accepted (the docs say it resets them) | Tested |
| `dmem` cgroup controller (device memory) | Absent | Listed in the root `cgroup.controllers` | Tested |
| Unprivileged PSI triggers (window a multiple of 2 s) | Refused with `EPERM` for 1 s and 2 s | Works on `/proc/pressure/memory`: 2 s registered, 1 s refused with `EINVAL`. On the user's own cgroup file still `EACCES`, because that file is owned by root | Tested. [Commit d82caa27](https://lab.nexedi.cn/kirr/linux/-/commit/d82caa273565b45fcf103148950549af76c314b0) (March 2023) |
| PSI trigger repeats while the stall lasts | 14 wake-ups in 15 s | 15 wake-ups in 15 s | Tested |
| `memory.high`, no swap, nothing reclaimable | 130 MiB and 105 MiB under a 100 MiB limit both unfinished after 60 s | 130 MiB unfinished after 60 s, but 105 MiB finished in 9 s | Tested |
| Multi-gen LRU (page aging by generations) | Not in 5.15 (merged in Linux 6.1) | On: `/sys/kernel/mm/lru_gen/enabled` is `0x0007`. `Active(...)`/`Inactive(...)` still appear in `/proc/meminfo` | Tested. [Launchpad 2023629](https://bugs.launchpad.net/bugs/2023629): Ubuntu enabled it for 23.10 kernels |
| `RLIMIT_MEMLOCK` default and `mlockall` for an ordinary user | 245 MiB on the test VM, so the call succeeded | 8 MiB (`ulimit -l` is `8192`), and the call failed with `ENOMEM` | Tested |
| cgroup v1 | Supported | **Gone**: no cgroup v1 mounts in the VM. systemd 258 removed the legacy and hybrid hierarchies | Tested. [systemd NEWS, v258](https://github.com/systemd/systemd/blob/main/NEWS) |
| `systemd-oomd` | Basic | v257 adds `ManagedOOMMemoryPressureDurationSec=` per service; v259 adds `OOMKills` and `ManagedOOMKills` properties on service units; v260 (not in 26.04) adds rulesets | Docs: [systemd NEWS](https://github.com/systemd/systemd/blob/main/NEWS) |
| `oom_score_adj` lowering rule, `WatchdogSec=` with implicit `NotifyAccess=main`, a user's throwaway scope | Works as the pages say | Same | Tested |

Not reviewed: the systemd NEWS for v250 to v256, and the kernel release notes for 5.16 to 6.0 and 6.2 to 6.17. Gaps there could hide other changes.

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
