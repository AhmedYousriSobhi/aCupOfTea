---
id: linux-mem-oom-killer
order: 3
title: "The OOM Killer: Who Gets Thrown Overboard, and Why So Late"
sidebar_label: "3. The OOM killer"
summary: How the kernel decides when it is out of memory and whom to kill, how oom_score_adj shields or sacrifices a process, and why userspace killers like systemd-oomd act earlier than the kernel.
level: intermediate
type: concept
domains: [systems-and-hpc]
relations:
  prerequisites: [linux-mem-reclaim]
  related: [linux-mem-psi, linux-mem-cgroup-v2]
---

# The OOM Killer: Who Gets Thrown Overboard, and Why So Late

> **Part 3 of the [Linux Memory Pressure series](/fields/system-administration/linux-memory-pressure/README.md).** When reclaim can't free another page, the kernel kills a process. It will tell you which one in `dmesg`, but never why that one, and rarely early enough. By the end you'll be able to predict the victim, protect or sacrifice a process on purpose, and explain why the kernel is the *last* line of defence, not the first.

## Table of Contents
- [The OOM Killer: Who Gets Thrown Overboard, and Why So Late](#the-oom-killer-who-gets-thrown-overboard-and-why-so-late)
  - [Table of Contents](#table-of-contents)
  - [The overloaded ship](#the-overloaded-ship)
  - [When the kernel decides it is out of memory](#when-the-kernel-decides-it-is-out-of-memory)
  - [How the victim is chosen](#how-the-victim-is-chosen)
  - [Try it before you scroll](#try-it-before-you-scroll)
  - [Shielding and sacrificing: oom_score_adj](#shielding-and-sacrificing-oom_score_adj)
  - [A smaller ship: OOM inside a cgroup](#a-smaller-ship-oom-inside-a-cgroup)
  - [Why the kernel is late, and who acts earlier](#why-the-kernel-is-late-and-who-acts-earlier)
  - [Read the crime scene](#read-the-crime-scene)
  - [References](#references)

---

## The overloaded ship

A cargo ship is caught in a storm, riding too low. The captain will not throw cargo overboard while the ship is merely heavy. She waits until water is coming over the deck and nothing else can be done. Then she picks the crate that frees the most weight and sends it into the sea.

Two things about this are true of the Linux OOM killer too:

1. It is a **last resort**. It only fires after everything else, including all the reclaim from the previous pages, has failed.
2. It picks the **heaviest crate**, with a way for the crates to wear labels like "medical supplies: do not throw".

| Ship | Linux machine |
|------|---------------|
| Water over the deck | An allocation that reclaim cannot satisfy |
| The captain | The kernel's OOM killer |
| A crate | A process |
| Weight of the crate | Memory the process holds (RSS plus swap and page tables) |
| The label on the crate | `oom_score_adj` |

---

## When the kernel decides it is out of memory

It does not trigger on "memory is low". It triggers on a **failure**:

1. A program asks for a page.
2. There isn't one, so the kernel tries direct reclaim ([part 1](/fields/system-administration/linux-memory-pressure/how-linux-reclaims-memory.md)), and compaction, repeating several times.
3. Still nothing. Only now it calls the OOM killer.

Because of memory **overcommit** (`vm.overcommit_memory`, default 0), a program's `malloc` almost always *succeeds*: the kernel promises memory without handing over real pages until each page is first touched. The bill arrives at touch time, which is why a program can crash with an OOM kill in the middle of an ordinary loop, long after the allocation call that "worked".

---

## How the victim is chosen

For every candidate process the kernel computes a **badness** score. The base is how much real memory it holds:

$$\text{points} = \text{RSS} + \text{swap used} + \text{page-table pages}$$

and that is scaled to a number from 0 to 1000 by the share of the machine's memory it represents. A process holding half of all RAM scores about 500. Then the label is added:

$$\text{oom\_score} = \frac{\text{points} \times 1000}{\text{total pages}} + \text{oom\_score\_adj}$$

"Total pages" is the memory the process is *allowed* to use: RAM plus swap on the whole machine, or the cgroup's limit inside a cgroup (so the same process scores higher in a small cgroup). The proc(5) man pages describe it as an estimate of memory and swap use relative to allowed memory.

The process with the **highest** score is killed. Its memory is released quickly by a helper (the *OOM reaper*), so the system recovers without waiting for the victim to finish exiting.

Notes that explain real surprises:

- It's the **biggest**, not the **guilty**. A small leaky service filled the machine, but a large database holding more RAM scores higher and gets killed instead.
- Memory is counted *per process*. Ten workers at 1 GiB each score lower than one process at 8 GiB, even though together they use more.
- You can read any process's current score in `/proc/<pid>/oom_score`.

---

## Try it before you scroll

☕ Grab a pen. On a 16 GiB machine that has run out of memory:

| Process | RSS | `oom_score_adj` |
|---------|-----|-----------------|
| A: database | 8 GiB | 0 |
| B: a rescue daemon | 0.05 GiB | -900 |
| C: a build job | 5 GiB | 0 |
| D: a browser | 3 GiB | +500 |

Which process is killed first?

Got your answer? Scroll on.

Answer: the **browser (D)**. The scores are roughly A: 500, B: -897, C: 312, D: about 690 (3 GiB is 188 on its own, plus 500). Even though it is the smallest of the big three, its label of +500 pushes it to the top. The rescue daemon, at -900, is nearly untouchable. Labels, not just size, decide.

---

## Shielding and sacrificing: oom_score_adj

`oom_score_adj` is a number from **-1000 to +1000** written to `/proc/<pid>/oom_score_adj`.

| Value | Effect |
|-------|--------|
| `-1000` | **Never kill.** The process is exempt (its badness score is always 0). Use sparingly: if it leaks, the kernel has nothing else left to sacrifice |
| `-900` | Very strongly protected, but not exempt. The usual choice for something that must survive |
| `0` | Default: judged on size alone |
| `+500` to `+1000` | Prefer to kill this first. Good for disposable batch work |

The rule that matters for permissions: **an ordinary user can raise the value of their own processes**. Lowering it below the value the process started with, which is what shields it, needs `CAP_SYS_RESOURCE`, which in practice means root. (This rule is from the kernel source, `fs/proc/base.c`, not from the man pages, which don't spell it out.) This is the same shape as `RLIMIT_MEMLOCK` from [part 5](/fields/system-administration/linux-memory-pressure/memory-locking-mlockall.md): protection from the machine's limits is rationed to privileged code.

In systemd you don't write the file yourself:

```ini
[Service]
OOMScoreAdjust=-900          # shield this service
# OOMScoreAdjust=500         # or: sacrifice it first
```

Locking a program in RAM (part 5) keeps it from being *slow* under pressure. A low `oom_score_adj` keeps it from being *killed*. A rescuer needs both, and they are separate settings.

---

## A smaller ship: OOM inside a cgroup

A cgroup with a hard `memory.max` has its own, smaller ship. When the group tries to go past its cap and reclaim inside it fails, the kernel runs an OOM kill **within that cgroup only**, and the rest of the machine is untouched. The kernel's log says so: `Memory cgroup out of memory`, and in the constraint line `CONSTRAINT_MEMCG`.

Two files in the group show what happened:

| File | What it tells you |
|------|-------------------|
| `memory.events` | Counters: how often `max` was hit, how many times `oom` fired, how many processes were killed (`oom_kill`) |
| `memory.oom.group` | If set to `1`, an OOM kill takes down **the whole group** together, instead of one process. Right for a container that is useless once any part dies |

This is why a container is "OOM-killed" with the host looking healthy: its ship was small, and it sank on its own. The files are covered in [part 4](/fields/system-administration/linux-memory-pressure/cgroup-v2-memory-control.md).

---

## Why the kernel is late, and who acts earlier

The kernel OOM killer only runs when reclaim *fails outright*. But recall thrashing from part 1: a machine can spend minutes swapping the same pages in and out, where every allocation technically **succeeds**, slowly. The OOM killer never fires, and the machine is unusable. People then power-cycle it, which is worse than a kill.

That gap, from "unusable" to "kernel notices", is why userspace killers exist. They watch pressure ([part 2](/fields/system-administration/linux-memory-pressure/memory-pressure-psi.md)) and act early, on purpose, and on a chosen victim:

| | Kernel OOM killer | Userspace killer (systemd-oomd, earlyoom, your own rescuer) |
|-|-------------------|--------------------------------------------------------------|
| Trigger | An allocation failed after reclaim | Pressure stays high, or available memory is low |
| Timing | Last resort, can be minutes late | Early, while the machine still works |
| Victim | Biggest score | Chosen by policy: a whole cgroup, a low-priority job |
| Gentler options | None, it kills | Can throttle, freeze or pause first |
| Needs memory to act? | It's the kernel | **Yes**, which is the reason for memory locking |

Note the last row. The userspace killer is the program whose pages could have been swapped out. It is the tow truck from [part 5](/fields/system-administration/linux-memory-pressure/memory-locking-mlockall.md).

systemd adds a policy setting: `OOMPolicy=` decides what happens to a *service* when one of its processes is OOM-killed (`stop` the whole service, `kill` it, or `continue`), and `ManagedOOMMemoryPressure=kill` opts a cgroup into `systemd-oomd`.

---

## Read the crime scene

When something was killed, the kernel writes a report. Read it with:

```bash
journalctl -k | grep -i -E "out of memory|oom-kill|killed process"
dmesg -T | grep -i -E "out of memory|oom-kill|killed process"
```

You'll see lines like `Out of memory: Killed process 1234 (python) ... anon-rss: ...`, a table of every process's memory at that moment, and the constraint (`CONSTRAINT_NONE` for the whole machine, `CONSTRAINT_MEMCG` for a cgroup).

To see how exposed a process is right now:

```bash
cat /proc/<pid>/oom_score          # its current badness
cat /proc/<pid>/oom_score_adj      # its label
cat /sys/fs/cgroup/<group>/memory.events    # oom, oom_kill counts for a cgroup
```

**Takeaway:** the kernel kills only after reclaim has failed, picks the process holding the most memory adjusted by `oom_score_adj`, and often acts long after the machine became unusable; so shield what must survive with a low `oom_score_adj`, and use a userspace killer on pressure for the early, gentler action.

The kernel's tool is a blunt kill. The cgroup files give you gentler levers, such as throttling, asking a group to give memory back, freezing it. That's [part 4](/fields/system-administration/linux-memory-pressure/cgroup-v2-memory-control.md).

## References
- [Linux kernel docs: Out of memory management](https://www.kernel.org/doc/html/latest/admin-guide/mm/concepts.html#oom-killer)
- [proc(5): oom_score, oom_score_adj](https://man7.org/linux/man-pages/man5/proc.5.html)
- [Linux kernel docs: Control Group v2, memory.events and memory.oom.group](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html#memory)
- [systemd.exec(5): OOMScoreAdjust](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html) and [systemd.service(5): OOMPolicy](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
