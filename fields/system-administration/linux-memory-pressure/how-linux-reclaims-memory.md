
# How Linux Reclaims Memory: Cache, Swap and the Two Kinds of Stall

<!-- related-block -->
<div class="reading-time">9 min read</div>
<!-- related-block -->
<div class="related-strip">

**See also:** [The Server That Looked Full: Free vs Available Memory, Cache, and What Is Really Used](/fields/system-administration/linux-memory-pressure/linux-memory-free-vs-available.md)  ·  **Read next:** [Pressure Stall Information: Measuring Time Lost, Not Bytes Left](/fields/system-administration/linux-memory-pressure/memory-pressure-psi.md), [The OOM Killer: Who Gets Thrown Overboard, and Why So Late](/fields/system-administration/linux-memory-pressure/the-oom-killer.md), [cgroup v2 Memory Control: The Levers Between Doing Nothing and Killing](/fields/system-administration/linux-memory-pressure/cgroup-v2-memory-control.md), [Memory Locking: Keeping a Rescuer in RAM with mlockall](/fields/system-administration/linux-memory-pressure/memory-locking-mlockall.md)

</div>


> **Part 1 of the [Linux Memory Pressure series](/fields/system-administration/linux-memory-pressure/README.md).** A Linux machine with almost no free memory is usually healthy, and a machine with plenty of free memory can still be in trouble. By the end of this page you'll know why, you'll be able to read `/proc/meminfo` without panic, and you'll know the exact moment a program starts to stall.

## Table of Contents
- [How Linux Reclaims Memory: Cache, Swap and the Two Kinds of Stall](#how-linux-reclaims-memory-cache-swap-and-the-two-kinds-of-stall)
  - [Table of Contents](#table-of-contents)
  - [The library with no empty desks](#the-library-with-no-empty-desks)
  - [Three kinds of page](#three-kinds-of-page)
  - [Try it before you scroll](#try-it-before-you-scroll)
  - [Free is not available](#free-is-not-available)
  - [Who does the clearing: kswapd and direct reclaim](#who-does-the-clearing-kswapd-and-direct-reclaim)
  - [The knobs: swappiness, zram and zswap](#the-knobs-swappiness-zram-and-zswap)
  - [Thrashing: when the clearing never ends](#thrashing-when-the-clearing-never-ends)
  - [See it on your own machine](#see-it-on-your-own-machine)
  - [References](#references)

---

## The library with no empty desks

A university library has a reading room with a fixed number of desks. Every desk holds something a student is working on right now. The rest of the collection lives in the basement stacks, which are slow to reach.

A good librarian doesn't keep desks empty. An empty desk is wasted. She fills spare desks with books people *might* want again soon, because fetching from the basement costs ten minutes. When a student walks in and needs a desk, she clears one in seconds by sending the least-recently-touched book back down.

Walk in at 3 p.m. and every desk is covered. Is the library overloaded? Not necessarily. Most of those desks hold books that can be swept away at no cost the moment someone needs the space.

| Library | Linux machine |
|---------|---------------|
| Reading-room desks | RAM, in 4 KiB pages |
| The basement stacks | Disk (files, swap) |
| Spare desks used as a shelf of "might want again" books | The **page cache** |
| The librarian clearing a desk | Page **reclaim** |
| The student who can't sit down until a desk is cleared | A program waiting on an allocation |

Everything on this page is about how the librarian decides what to clear, and what happens when she can't keep up.

---

## Three kinds of page

Not every page is equally cheap to take back. This is the fact that everything else follows from.

| Kind of page | Library version | What reclaim has to do | Cost |
|--------------|-----------------|------------------------|------|
| **Clean file page** | A library book: the original is in the stacks | Just drop it. Re-read it from the file if it is needed again | Free now, a disk read later |
| **Dirty file page** | A book someone wrote notes in | Write the changes back to the file first, then drop it | One disk write |
| **Anonymous page** | Your own handwritten notes: no original exists | Needs somewhere to go: **swap**. With no swap, these pages **cannot** be reclaimed | A disk write now, a read later |

*Anonymous* means "not backed by a file": a program's heap, its stack, memory from `malloc`. That's the memory programs own.

The kernel sorts pages onto four lists in `/proc/meminfo`: `Active(file)`, `Inactive(file)`, `Active(anon)` and `Inactive(anon)`. A page moves from active to inactive when it hasn't been touched for a while, and the inactive ends are where reclaim eats first. (Kernels with **multi-gen LRU**, on by default on Ubuntu 26.04, age pages through several generations instead. The four `/proc/meminfo` counters are still there, so the picture here still reads correctly. Check `/sys/kernel/mm/lru_gen/enabled`.) This is the "least recently used" rule from the [memory-locking page](/fields/system-administration/linux-memory-pressure/memory-locking-mlockall.md), made concrete.

One consequence is worth saying out loud. **A machine with no swap isn't safer, it just has fewer pages it is allowed to reclaim.** All the anonymous memory is pinned by the lack of a place to put it, and only the file cache is left to squeeze.

---

## Try it before you scroll

☕ Grab a pen. A 16 GiB server reports this:

```
MemFree:      300 MB
Cached:       11 GB
Swap used:    0
```

Is the server in trouble?

Got your answer? Scroll on.

Answer: **no**. 11 GB of the "used" memory is cache, mostly clean file pages the librarian can send back to the stacks in an instant. The 300 MB figure only says the desks are being used well. The number that matters is the next section's.

One catch: `Cached` also counts **shared memory** (`tmpfs`, `/dev/shm`, MPI shared segments), which is swap-backed like anonymous memory. With no swap those pages can't be dropped. Check the `Shmem` line in `/proc/meminfo` before you call all of `Cached` free.

---

## Free is not available

`MemFree` is memory nobody is using at all. On a healthy, busy machine it is small *on purpose*, because the kernel spends the spare on cache.

The number you want is `MemAvailable`: the kernel's estimate of how much it could hand to a new program **without swapping**, which is free memory plus the part of the cache it can drop, minus a safety margin.

On the machine I wrote this page on (Ubuntu 26.04, Linux 7.0, 14.8 GiB of RAM):

| Field | Value | Meaning |
|-------|-------|---------|
| `MemTotal` | 14.8 GiB | The desks |
| `MemFree` | 1.3 GiB | Empty desks |
| `Cached` | 4.3 GiB | Books kept on desks, mostly droppable |
| `MemAvailable` | 5.4 GiB | What a new student could get without anyone being sent to swap |

`free` says 1.3, `MemAvailable` says 5.4. A script alerting on `MemFree` would have paged someone for nothing. A script alerting on `MemAvailable` is much closer to right, and PSI in the [next page](/fields/system-administration/linux-memory-pressure/memory-pressure-psi.md) is closer still.

---

## Who does the clearing: kswapd and direct reclaim

The librarian doesn't wait for a student to ask. She has two modes, and the difference between them is the most important idea on this page.

The kernel tracks three **watermarks** on free memory: *high*, *low* and *min*. Think of them as three lines painted on the wall of the reading room.

| Free memory is... | What happens | Who waits |
|-------------------|--------------|-----------|
| Above *high* | Nothing. Everything is calm | Nobody |
| Below *low* | A background thread, **`kswapd`**, wakes up and reclaims pages | **Nobody.** It runs beside the programs |
| Below *min* | The program asking for memory has to **reclaim pages itself**, before its allocation can finish. This is **direct reclaim** | **The program** |

```mermaid
flowchart LR
    A["Free memory<br/>above high"] --> B["Below low:<br/>kswapd wakes<br/>in the background"]
    B --> C["Below min:<br/>direct reclaim"]
    C --> D["Your program<br/>stalls inside malloc"]
```

While `kswapd` keeps up, memory pressure is invisible. When programs allocate faster than it can clear, free memory sinks to *min*, and now **the program that wanted one page is made to do the clearing before it gets it**. That wait is a stall: no CPU used, nothing wrong with the code, just a thread queued behind disk writes.

This is exactly the trap behind the mlock page: allocating under pressure can block, which is why a rescuer must do its allocating before the trouble starts.

The kernel counts both. On the same machine:

| Counter in `/proc/vmstat` | Value | Reading |
|--------------------------|-------|---------|
| `pgscan_kswapd` | 5.39 million | Pages scanned by the background thread |
| `pgscan_direct` | 122 thousand | Pages scanned by stalled programs themselves |
| `allocstall_*` | about 1,000 in total | Times a program had to enter direct reclaim |

Roughly two scanned pages in a hundred were done by a program that was made to wait. A healthy machine has a small `pgscan_direct`. When that line starts climbing fast, the stalls have begun.

---

## The knobs: swappiness, zram and zswap

Three settings change how the librarian behaves. People often misread the first.

**`vm.swappiness`** (default 60) is the balance between reclaiming **file pages** and **anonymous pages**. It is *not* "start swapping when memory is 60% full". Higher values make the kernel more willing to push anonymous pages to swap rather than shrink the cache. At 0 it strongly prefers dropping cache first. The range is 0 to 200 since Linux 5.8 (0 to 100 before).

**zram** is a swap device that lives in RAM and **compresses** what is put into it. Swapping out a page costs a bit of CPU instead of a disk write, which is why zram-backed swap hurts far less. It is common on laptops and some servers.

**zswap** is a compressed *cache in front of a real swap device*. Pages are compressed into a RAM pool first, and only pushed to disk when that pool fills.

| | Where evicted pages go | Cost to bring one back |
|-|------------------------|------------------------|
| Disk swap | A swap file or partition | Microseconds (SSD) to milliseconds (disk), worse when the disk is busy |
| zram | A compressed block in RAM | A decompression: far faster than disk |
| zswap | Compressed RAM, spilling to disk when full | Fast while the pool lasts |

None of these remove the stall. They make each swapped-in page cheaper, so the stall is shorter.

---

## Thrashing: when the clearing never ends

One more word, because it names the worst case.

If the pages programs are *actively using* (their **working set**) don't fit in RAM, reclaim evicts a page, the program touches it a moment later, and it has to be read straight back in. The kernel counts these in `workingset_refault_*`. The machine spends its time swapping the same pages in and out while no program makes progress. This is **thrashing**, and it feels like the machine froze, though nothing has crashed.

Thrashing is also why the kernel's OOM killer, which only fires when it truly cannot find a page, can take **minutes** to act on a machine that is unusable long before. That gap is the subject of the [OOM-killer page](/fields/system-administration/linux-memory-pressure/the-oom-killer.md), and it is why something has to notice trouble earlier.

---

## See it on your own machine

```bash
free -h                                           # the quick view; read the "available" column
grep -E "MemTotal|MemFree|MemAvailable|^Cached|^Active|^Inactive|SwapTotal|SwapFree" /proc/meminfo
sysctl vm.swappiness vm.min_free_kbytes           # the knob and the "min" watermark source
grep -E "^(pgscan_kswapd|pgscan_direct|allocstall)" /proc/vmstat
vmstat 1                                          # watch si/so (swap in/out per second) live
```

Run the `/proc/vmstat` line twice, a minute apart, during busy work, and subtract. A growing `pgscan_direct` is the number that says programs are paying for the clearing themselves.

**Takeaway:** the kernel keeps RAM full on purpose and takes it back as needed; a background thread does it quietly until free memory hits the minimum line, and from then on *your program* does the clearing and stalls. Watch `MemAvailable` and `pgscan_direct`, not `MemFree`.

So the machine is spending its time clearing desks. How do you notice that it's happening *before* anything breaks? That's [part 2](/fields/system-administration/linux-memory-pressure/memory-pressure-psi.md).

## References
- [Linux kernel docs: Concepts overview (page cache, anonymous memory, reclaim)](https://www.kernel.org/doc/html/latest/admin-guide/mm/concepts.html)
- [Linux kernel docs: /proc/sys/vm (swappiness, min_free_kbytes, watermark_scale_factor)](https://www.kernel.org/doc/html/latest/admin-guide/sysctl/vm.html)
- [Linux kernel docs: zram](https://www.kernel.org/doc/html/latest/admin-guide/blockdev/zram.html) and [zswap](https://www.kernel.org/doc/html/latest/admin-guide/mm/zswap.html)
- [proc(5): /proc/meminfo and /proc/vmstat](https://man7.org/linux/man-pages/man5/proc.5.html)
