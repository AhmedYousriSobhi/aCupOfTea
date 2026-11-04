---
id: linux-mem-rescuer-checklist
order: 6
title: "Making a Rescuer Survive: CPU, Protection and a Checklist"
sidebar_label: "6. The rescuer checklist"
summary: Beyond memory locking, what keeps an emergency program running under load - real-time priority, an OOM shield, restart and watchdog - and one checklist that ties all six pages together.
level: intermediate
type: guide
domains: [systems-and-hpc]
relations:
  prerequisites: [linux-mem-mlockall, linux-mem-cgroup-v2]
  related: [linux-mem-psi, linux-mem-oom-killer]
---

# Making a Rescuer Survive: CPU, Protection and a Checklist

> **Part 6 of the [Linux Memory Pressure series](/fields/system-administration/linux-memory-pressure/README.md).** Pinning a program in RAM stops one kind of stall. A machine in trouble has others: the program can be starved of CPU, killed by the OOM killer, or simply hung. This page covers the rest of what a rescuer needs, then gives one checklist for the whole series.

## Table of Contents
- [Making a Rescuer Survive: CPU, Protection and a Checklist](#making-a-rescuer-survive-cpu-protection-and-a-checklist)
  - [Table of Contents](#table-of-contents)
  - [The ambulance that is stuck in traffic](#the-ambulance-that-is-stuck-in-traffic)
  - [Gap 1: CPU time](#gap-1-cpu-time)
  - [Gap 2: being killed](#gap-2-being-killed)
  - [Gap 3: hanging, and who watches the watcher](#gap-3-hanging-and-who-watches-the-watcher)
  - [Try it before you scroll](#try-it-before-you-scroll)
  - [The whole unit file](#the-whole-unit-file)
  - [The checklist](#the-checklist)
  - [Other uses of locked memory](#other-uses-of-locked-memory)
    - [References](#references)

---

## The ambulance that is stuck in traffic

A city gives its ambulance a reserved garage so it is never towed (that's [memory locking](/fields/system-administration/linux-memory-pressure/memory-locking-mlockall.md)), and keys always in the ignition (pre-allocation). On the day of the big traffic jam it is parked, intact, in its garage, and cannot get out. Three more things were needed:

| Gap | What goes wrong | The ambulance equivalent |
|-----|-----------------|--------------------------|
| **CPU** | The machine is so busy the rescuer isn't scheduled | Stuck in the jam: needs lights and siren, the right to jump the queue |
| **Being killed** | The OOM killer picks it as the heaviest crate | Someone impounds it for taking up space |
| **Hanging** | It's alive but stuck, and nobody notices | The driver fell asleep at the wheel; no dispatcher is checking |

---

## Gap 1: CPU time

Under memory pressure the machine is busy: reclaim threads, a thrashing workload, a disk queue. A rescuer in RAM still has to be *given the CPU*.

Linux has **real-time scheduling classes**, `SCHED_FIFO` and `SCHED_RR`, which always beat ordinary processes. A real-time task runs the moment it is ready, and keeps the CPU until it blocks.

```bash
chrt -f 50 ./rescuer          # run with SCHED_FIFO, priority 50
chrt -p <pid>                 # show a running process's policy and priority
```

In a systemd unit: `CPUSchedulingPolicy=fifo` and `CPUSchedulingPriority=50`.

The cost: this is a power that can freeze a machine. A real-time program that loops without blocking would starve everything, including the programs it was meant to rescue, which is why the kernel limits it:

- A normal user needs `CAP_SYS_NICE` or an `RLIMIT_RTPRIO` allowance to ask for it, so it is **privileged**, just like the memory lock.
- Real-time tasks get at most **95% of each second** by default (`sched_rt_runtime_us` is 950000 of 1000000 µs on my machine), leaving 5% for everyone else. That reserve is the safety net against a runaway.

Rule of thumb: a rescuer should do a small amount of work and then **block** (wait on a PSI trigger or a timer). It uses real-time priority for *latency*, not for throughput.

A softer version: a negative nice value (`Nice=-10`) and a higher IO class (`IOSchedulingClass=realtime`, which usually needs privilege too).

---

## Gap 2: being killed

Even locked and prioritized, the rescuer is a process. When the kernel is out of memory, it is scored like any other ([part 3](/fields/system-administration/linux-memory-pressure/the-oom-killer.md)). The shield is `OOMScoreAdjust=-900`.

Why `-900` and not `-1000`? Because `-1000` makes the process **exempt from the OOM killer entirely**. If the rescuer itself ever leaks, the kernel has no way to remove it, and the machine can wedge. `-900` makes it a victim of last resort: almost any other process dies first, but a real bug in the rescuer is still correctable.

One more shield sits in the cgroup. Giving the rescuer's service a **`MemoryLow=`** (or `memory.low`) tells reclaim to take memory from other groups first when the machine is short. It's a cousin of the lock for pages that are *not* worth pinning individually.

---

## Gap 3: hanging, and who watches the watcher

A rescuer that crashes is bad. One that is alive but stuck is worse, because nothing restarts it.

Two systemd settings handle this:

- `Restart=always` brings it back after a crash or a kill.
- `WatchdogSec=30` makes the service send an "I'm alive" message (via `sd_notify`) at least that often. If it goes quiet, systemd treats it as hung and restarts it.

This turns the rescuer's own failure into a short gap instead of a silent one. The `sd_notify` call must itself be allocation-free, so the same rule from [part 5](/fields/system-administration/linux-memory-pressure/memory-locking-mlockall.md) applies: open the notification socket at startup.

---

## Try it before you scroll

☕ Grab a pen. A rescuer has `mlockall` and `OOMScoreAdjust=-900`. During a memory spike it still reacts three seconds late. Name two things that could still be wrong.

Got yours? Scroll on.

Answers: (1) It isn't getting **CPU** quickly. It is a normal-priority process competing with a busy machine. (2) Its **action** allocates. If acting means starting a subprocess like `docker stop`, the child process needs new memory and can stall in direct reclaim, even though the parent is locked. A third: its **trigger** is slow. Polling once every few seconds is itself a three-second delay, which a PSI trigger would remove.

---

## The whole unit file

Putting every gap together, a privileged rescuer's unit might look like this:

```ini
[Unit]
Description=Memory-pressure rescuer

[Service]
ExecStart=/usr/local/bin/rescuer
Restart=always
WatchdogSec=30

# part 5: never swapped out
LimitMEMLOCK=infinity

# part 3: shield from the kernel OOM killer, but not exempt
OOMScoreAdjust=-900

# gap 1: get the CPU when it matters
CPUSchedulingPolicy=fifo
CPUSchedulingPriority=50

# keep its group's memory when others are reclaimed
MemoryLow=64M
```

Every line here needs privilege, which is the reason an unprivileged rescuer is "best effort" and a root service is "the real thing".

---

## The checklist

One row per page of the series.

| # | Question | What to do | Page |
|---|----------|------------|------|
| 1 | Am I looking at the right number? | Alert on `MemAvailable` and `pgscan_direct`, never `MemFree` | [How Linux reclaims memory](/fields/system-administration/linux-memory-pressure/how-linux-reclaims-memory.md) |
| 2 | How will I know pressure is coming? | Read PSI (`some` early, `full` late), or use a PSI trigger to wake up | [Memory pressure (PSI)](/fields/system-administration/linux-memory-pressure/memory-pressure-psi.md) |
| 3 | What happens if I'm too late? | Know the kernel OOM victim rule; shield what matters with `oom_score_adj` | [The OOM killer](/fields/system-administration/linux-memory-pressure/the-oom-killer.md) |
| 4 | What can I do, gentlest first? | `memory.high`, then `memory.reclaim`, then `cgroup.freeze`, then `cgroup.kill`, chosen per group by priority | [cgroup v2 memory control](/fields/system-administration/linux-memory-pressure/cgroup-v2-memory-control.md) |
| 5 | Will I be fast when it happens? | `mlockall`, plus pre-open handles and pre-touch buffers before the lock | [Memory locking (mlockall)](/fields/system-administration/linux-memory-pressure/memory-locking-mlockall.md) |
| 6 | Will I get CPU, survive and be noticed if I hang? | Real-time priority, `-900` OOM adjust, `Restart=` and `WatchdogSec=` | This page |

And the one rule that holds them all: **everything the rescuer needs under pressure must be acquired before the pressure.** Memory, file handles, sockets, buffers, the decision about whom to act on. If any step opens, allocates or looks something up during the crisis, the crisis can delay it.

The unprivileged fallback is a sensible product decision, not a failure: try each privileged step, log the ones that fail, and keep running with what worked.

---

## Other uses of locked memory

Locking isn't only for rescuers. The same call shows up wherever *the kernel moving a page* would be a problem:

- **Secrets.** Keys and passwords are locked so they never reach a swap file. Newer kernels also offer `memfd_secret`, memory even the kernel cannot read directly.
- **Latency-critical programs.** Audio, trading and packet-processing code lock memory so a page fault never interrupts a deadline. Often paired with huge pages and real-time priority, the same recipe as above.
- **Hardware access.** Devices that read memory directly (RDMA, GPU transfers) need pages that cannot move, which is why this series is related to [the GPU storage and fabric pages](/fields/system-administration/ai-storage-and-fabric/README.md).

**Takeaway:** a rescuer that is only locked in RAM can still be starved of CPU, killed by the OOM killer or hang unnoticed; give it real-time priority, a `-900` OOM shield and a watchdog, and acquire every resource it will need before the pressure begins.

### References
- [sched(7): real-time scheduling policies](https://man7.org/linux/man-pages/man7/sched.7.html) and [chrt(1)](https://man7.org/linux/man-pages/man1/chrt.1.html)
- [systemd.service(5): Restart, WatchdogSec](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html) and [sd_notify(3)](https://www.freedesktop.org/software/systemd/man/latest/sd_notify.html)
- [systemd.exec(5): CPUSchedulingPolicy, OOMScoreAdjust, LimitMEMLOCK](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html)
- [memfd_secret(2)](https://man7.org/linux/man-pages/man2/memfd_secret.2.html)
