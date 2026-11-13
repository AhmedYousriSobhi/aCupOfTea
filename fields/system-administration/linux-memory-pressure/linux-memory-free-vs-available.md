---
id: linux-memory-free-vs-available
title: "The Server That Looked Full: Free vs Available Memory, Cache, and What Is Really Used"
order: 1
sidebar_label: "Prelude: free vs available"
summary: One real free -h snapshot explained - why free is the wrong number, what buff/cache and shared hold, why the columns sum above total, and how to find what is really used.
level: beginner
type: concept
domains:
  - systems-and-hpc
relations:
  related:
    - linux-mem-reclaim
    - linux-mem-psi
    - slurm-cgroups-in-practice
---

# The Server That Looked Full: Free vs Available Memory, Cache, and What Is Really Used

> **Facts in this page come from the `free` man pages, `proc_meminfo(5)` and the kernel commit that added `MemAvailable`.** The scenario is invented. The numbers are a real `free -h` snapshot, and a few derived figures depend on one assumption that is flagged where it appears. Verify with the commands in each section, on your own machine.

## Table of Contents

- [The snapshot](#the-snapshot)
- [The cast of columns](#the-cast-of-columns)
- [The puzzle: the columns do not add up](#the-puzzle-the-columns-do-not-add-up)
- [Free memory is a feature, not a symptom](#free-memory-is-a-feature-not-a-symptom)
- [What cache really is](#what-cache-really-is)
- [What is really used](#what-is-really-used)
- [The swap clue](#the-swap-clue)
- [The detective kit](#the-detective-kit)
- [Verdict on ps331](#verdict-on-ps331)
- [Which number to alert on](#which-number-to-alert-on)
- [Cheat sheet](#cheat-sheet)
- [References](#references)

* * *

## The snapshot

An engineer, invented for this story, has a terminal open on a host called `ps331`, running `free -h` every two seconds. At 17:13 on a Thursday it shows this:

```
Every 2.0s: free -h                                  ps331: Thu Nov  5 17:13:47 2026

               total        used        free      shared  buff/cache   available
Mem:            14Gi       9.7Gi       789Mi       1.3Gi       5.9Gi       5.2Gi
Swap:          2.0Gi       1.2Gi       780Mi
```

The engineer's first reaction is the one most of us have: **789Mi free out of 14Gi. This machine is nearly out of memory, and it is already swapping.**

Is it? The answer depends on which of six numbers you read, and the one that jumps out, `free`, is the least useful of them.

* * *

## The cast of columns

`free` just parses `/proc/meminfo`. The man page defines each column:

| Column | Meaning | `/proc/meminfo` field |
|---|---|---|
| `total` | Usable RAM (and swap on the Swap line) | `MemTotal`, `SwapTotal` |
| `used` | **Used or unavailable memory, calculated as total − available** (newer versions) | derived |
| `free` | Memory not used for anything at all | `MemFree`, `SwapFree` |
| `shared` | Memory used mostly by tmpfs | `Shmem` |
| `buff/cache` | Buffers plus page cache plus reclaimable slab | `Buffers` + `Cached` + `SReclaimable` |
| `available` | An estimate of how much memory can be allocated to start new applications **without swapping** | `MemAvailable` |

A version note that matters for this story: older `free` man pages (2016 and 2018 copies) define `used` as total − free − buffers − cache. The newer man page (the copy I read is dated 2023-05) defines it as total − **available**. If your `used` seems to disagree with a mental sum, check which procps-ng you have with `free -V`.

* * *

## The puzzle: the columns do not add up

Add the three obvious ones from the snapshot:

```
used + free + buff/cache = 9.7 + 0.77 + 5.9 = 16.4 Gi        (789Mi is about 0.77Gi)
total                    = 14 Gi
```

The three columns that look like a partition of memory add up to **more than the total**. That is not a bug, and it is the first clue about how `free` works now.

With the older definition, `used + free + buff/cache` equals `total` by construction. With the newer one, `used` is `total − available`, and `available` excludes part of the cache, so some memory is counted in `used` **and** in `buff/cache`. The overlap is exactly `free + buff/cache − available`:

```
0.77 + 5.9 − 5.2 = 1.47 Gi of memory counted twice
```

One loose end: `used + available = 9.7 + 5.2 = 14.9`, so the real total is close to 14.9Gi, while the header says 14Gi. I believe `free -h` truncates rather than rounds, which would explain it, and the figures below use 14.9. Check on your own machine with `free -m`, which has no rounding games.

Here is the whole machine on one picture (numbers in Gi, derived from the snapshot, so treat the small ones as approximate):

```
RAM ≈ 14.9 Gi
|----------------------- used 9.7 -----------------------|--------- available 5.2 ---------|
| 8.2 not cache at all   | ~1.5 "cache" that cannot be   |  free 0.77  | ~4.4 cache that    |
| (processes, kernel)    | handed back (shared + margin) |             | can be handed back |
                         |<--------------- buff/cache 5.9 ----------------------------------->|
```

So there are two different questions with two different answers: how much is **not cache** (8.2Gi), and how much is **not available** (9.7Gi). The difference between them is the part of "cache" that cannot actually be given back.

* * *

## Free memory is a feature, not a symptom

Why is `free` so small? Because the kernel is doing its job. RAM that holds nothing is wasted, so Linux fills spare memory with cached copies of files it has read recently. Next time a program asks for that file, the answer comes from RAM instead of disk.

A hotel is a good picture:

| Hotel | Memory |
|---|---|
| Empty rooms | `free` |
| Guests who agreed to check out the moment someone arrives | Clean page cache and reclaimable slab |
| Guests who cannot leave without being moved to a warehouse (swap) | Anonymous memory, `shared`/tmpfs |
| "Rooms I could realistically give a new arrival tonight" | `available` |

A hotel manager who panics because few rooms are *empty* is reading the wrong board. The one that matters is how many rooms could be freed without a fight. The kernel's own author of the `MemAvailable` field made the same point: programs that used `MemFree` as the measure of free memory, or simply added `MemFree` and cache, kept getting it wrong, so he added an estimate calculated from `MemFree`, the reclaimable slab, the size of the file LRU lists and the low watermarks in each zone.

* * *

## What cache really is

`buff/cache` is three different things stirred together:

| Part | What it holds | Can it be dropped? |
|---|---|---|
| **Page cache** | Contents of files read or written recently | Clean pages: yes, instantly. Dirty pages must be written out first (watch `Dirty` and `Writeback` in `/proc/meminfo`) |
| **Buffers** | Block-device metadata | Mostly yes |
| **Reclaimable slab** | Kernel caches such as directory entries and inodes | Yes, but the man page notes not all of it will be, because some items are in use |

And then there is the guest in the wrong room: **tmpfs and shared memory are counted inside `Cached`**, the same pool as page cache. The `Shmem` field is the total memory used by shared memory and tmpfs, and it appears in `buff/cache`. But tmpfs pages are not a cache of anything on disk. If you delete them, the data is gone, and the kernel can only move them to swap. So they are not reclaimable the way ordinary cache is.

That is exactly why `available` does not count them. A forum experiment makes it concrete: creating several 1GB files in a tmpfs reduced `MemAvailable` by 1GB each time, because the "file LRU lists" the kernel adds up do not include shared memory.

Now the snapshot makes sense. Of the 5.9Gi in `buff/cache`, roughly 1.5Gi is not counted as available. The `shared` column says 1.3Gi of that is tmpfs or shared memory. The remaining ~0.2Gi is, as I read the kernel code, the safety margin: the estimate leaves the low watermarks untouched and keeps at least some page cache in place, because the system needs some page cache to function well. That ~0.2 figure is my arithmetic, not a measured value.

* * *

## What is really used

"Used" is the hardest column to name, so break it into what is really in it. In the snapshot (using the 14.9Gi assumption):

```
total − free − buff/cache = 14.9 − 0.77 − 5.9 ≈ 8.2 Gi    memory that is not cache at all
+ cache that cannot be given back                ≈ 1.5 Gi    (shared/tmpfs ≈ 1.3 + kernel margin)
= used (as free -h reports it now)               ≈ 9.7 Gi
```

The 8.2Gi is where the actual consumers live:

| Consumer | `/proc/meminfo` field |
|---|---|
| Process heaps and stacks | `AnonPages` |
| Shared memory and tmpfs | `Shmem` |
| Kernel memory that cannot be reclaimed | `SUnreclaim`, `PageTables`, `KernelStack` |
| File pages processes have mapped | `Mapped` |

You can read them all at once:

```bash
awk '/^(MemTotal|MemFree|MemAvailable|Buffers|Cached|SReclaimable|SUnreclaim|AnonPages|Shmem|Mapped|PageTables|KernelStack|Dirty|Writeback|SwapTotal|SwapFree|SwapCached):/ \
     { printf "%-14s %8.2f GiB\n", $1, $2/1048576 }' /proc/meminfo
```

If `AnonPages` plus `Shmem` explains most of "used", you have a process problem, and `ps` can name the culprit. If `SUnreclaim` is large, you have a kernel-side problem, and `slabtop` is the next stop.

* * *

## The swap clue

The snapshot also shows 1.2Gi of the 2.0Gi swap in use. Does that mean the machine is thrashing?

Not by itself. Swap **used** is a stock, not a flow. The kernel may have pushed pages that no one has touched in a long time out to swap to make room for something more useful, such as cache. Those pages can sit there for days at no cost. What hurts is swap **traffic**, pages moving in and out right now. Measure the flow:

```bash
vmstat 1 5          # columns si (swapped in) and so (swapped out): sustained non-zero = trouble
cat /proc/pressure/memory    # PSI: 'some' and 'full' stall percentages (needs a kernel with PSI enabled)
```

A swap number that **grows over time** while `available` shrinks is the real warning sign. One snapshot cannot tell you which of those you are looking at, and that is worth remembering for the verdict below.

* * *

## The detective kit

```bash
free -m                                  # exact numbers, no rounding surprises
free -V                                  # which definition of 'used' you have
grep -E 'MemAvailable|Shmem|SwapCached' /proc/meminfo
df -h /dev/shm /run /tmp                 # tmpfs mounts: who is filling Shmem?
ps -eo pid,user,rss,comm --sort=-rss | head     # biggest resident processes
slabtop -o | head -15                    # kernel slab consumers (usually needs root)
vmstat 1 5                               # swap traffic and memory flow
cat /proc/pressure/memory                # are tasks actually stalling for memory?
dmesg -T | grep -i 'out of memory\|oom'  # has the OOM killer already acted?
```

Two traps:

- **`RSS` double counts shared pages.** Summing `ps` RSS across processes overstates usage when processes share libraries or memory. Tools that report proportional set size (PSS), such as `smem`, split shared pages fairly.
- **Dropping caches is a demonstration, not a fix.** Writing to `/proc/sys/vm/drop_caches` empties the cache and makes `free` look healthy. It also makes every file read slow again until the cache warms up. Use it to prove a point on a test box, not to "solve" memory on a production one.

* * *

## Verdict on ps331

From one snapshot, with the caveats above:

| Number | Reading |
|---|---|
| `free` 789Mi | Meaningless on its own. The kernel is using spare RAM for cache, as designed |
| `available` 5.2Gi | About 35% of total memory can be handed to new work without swapping. That is decent headroom |
| `shared` 1.3Gi | Worth a look. Check `df -h /dev/shm /tmp /run`. This memory is not reclaimable |
| `swap used` 1.2Gi | Unknown without a second look. Run `vmstat 1` and see whether `si`/`so` are zero |
| `used` 9.7Gi | Mostly real: about 8.2Gi of non-cache memory plus ~1.5Gi of stuck cache. The `awk` command above says who |

The engineer's panic was premature. The question to ask is not "why is free so low", but **"is `available` falling over time, and is swap traffic non-zero?"** A `watch -n2 free -h` window is good for exactly that, if you read the `available` and `Swap used` columns instead of `free`.

* * *

## Which number to alert on

| Signal | Alert on it? |
|---|---|
| `free` low | No. Healthy systems run with little free memory |
| `buff/cache` large | No. It is mostly the kernel being useful |
| `available` low **and falling** | Yes |
| Swap in/out rate sustained above zero (`vmstat` `si`/`so`) | Yes |
| Memory pressure (PSI `some`/`full`) rising | Yes. It measures stalls, not usage |
| OOM-kill messages in the kernel log | Yes, and by then you are late |

A footnote for cluster people: on a Slurm node, jobs live inside cgroups, and in cgroup v2 a job's `memory.current` includes its page cache. That is reclaimable under the job's limit, so a high number is not automatically a job about to be killed. The [cgroups page](/fields/schedulers/slurm-inside-a-job/slurm-cgroups-in-practice.md) explains what actually gets enforced, and `memory.stat` splits a cgroup's usage into anonymous, file and shared parts the same way this page splits the host's.

* * *

## Cheat sheet

```
free       empty RAM. Low is normal; do not alert on it
buff/cache page cache + buffers + reclaimable slab, PLUS shared/tmpfs that cannot be dropped
available  free + the cache the kernel can really give back (estimate; shmem excluded)
used       newer free: total - available  ->  overlaps buff/cache, so columns can sum > total
shared     tmpfs + shared memory (Shmem): counted in cache, NOT reclaimable
swap used  a stock, not a flow. Look at vmstat si/so and PSI for the flow
really used = AnonPages + Shmem + SUnreclaim + PageTables + KernelStack (+ mapped files in use)
```

Free memory is the number that scares you. Available memory is the number that tells you the truth. And neither one tells you who is using the room.

* * *

**Takeaway:** Read `available`, not `free`, and watch whether it falls and whether swap is moving.

Next: [How Linux reclaims memory](/fields/system-administration/linux-memory-pressure/how-linux-reclaims-memory.md), part 1: why the kernel keeps free memory near zero, and when a program really stalls.

* * *

## References

- [free(1) man page, 2023 procps-ng (`used` = total − available)](https://mankier.com/1/free)
- [free(1) man page, 2016 procps-ng (`used` = total − free − buffers − cache; column definitions)](https://www.unix.com/man_page/v7/1/free)
- [free(1) man page, 2018 copy (`available` description)](https://man.he.net/man1/free)
- [Linux kernel commit 34e431b0: add MemAvailable to /proc/meminfo](https://coral.googlesource.com/linux-mtk/+/34e431b0ae398fc54ea69ff85ec700722c9da773%5E%21)
- [Rik van Riel's RFC patch: provide estimated available memory](https://lkml.iu.edu/hypermail/linux/kernel/1311.0/03096.html)
- [Unix StackExchange: is cached memory de facto free (tmpfs and MemAvailable experiment)](https://backiee.wasmer.app/https_unix_stackexchange_com/questions/499649/is-cached-memory-de-facto-free)
- [Unix StackExchange: MemAvailable higher than expected (the estimate in practice)](https://wiki.neonvagabond.xyz/content/unix.stackexchange.com_en_all_2024-05/questions/500400/memavailable-higher-than-expected)
- [Detailed explanation of /proc/meminfo fields (Shmem and Cached)](https://git.ipr.univ-rennes.fr/cellinfo/linuxram/src/branch/main/linuxram.md)
