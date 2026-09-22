# Why Does Intel's HPL Binary Beat Netlib by 60% — Then Suddenly Not?

> **The setup:** same 94-core node, same fixed block size (NB=384), two different `xhpl` binaries — Intel's optimized container vs. plain-vanilla Netlib. At small problem sizes Intel crushes it. At large problem sizes... it basically doesn't matter. Here's why.

## Table of Contents
- [Why Does Intel's HPL Binary Beat Netlib by 60% — Then Suddenly Not?](#why-does-intels-hpl-binary-beat-netlib-by-60--then-suddenly-not)
  - [Table of Contents](#table-of-contents)
  - [The headline numbers](#the-headline-numbers)
  - [The full curve](#the-full-curve)
  - [So what's actually causing this?](#so-whats-actually-causing-this)
    - [1. Overhead vs. compute — a race that only matters early](#1-overhead-vs-compute--a-race-that-only-matters-early)
    - [2. Intel plays defense against a bad HPL.dat](#2-intel-plays-defense-against-a-bad-hpldat)
  - [The takeaway](#the-takeaway)
  - [What to actually do about it](#what-to-actually-do-about-it)

---

## The headline numbers

At the smallest problem size tested, the Intel container wasn't just a little ahead — it lapped Netlib:

| Metric | Result |
|---|---|
| **N = 50,000** | Intel: `3,818.21` GFLOPS vs. Netlib: `2,364.87` GFLOPS → **+61.5%** |
| **N = 200,000** | Intel: `5,616.45` GFLOPS vs. Netlib: `5,331.69` GFLOPS → **+5.3%** |

Same CPUs. Same core count. Same NB. That's not a hardware story — that's a **software/runtime story**, and it disappears almost entirely once the problem gets big enough.

## The full curve

| Problem Size (N) | Intel Container (GFLOPS) | Netlib `xhpl` (GFLOPS) | Advantage |
|---:|---:|---:|---:|
| 50,000  | **3,818.21** | 2,364.87 | 🟢 +61.45% |
| 100,000 | **5,438.80** | 4,284.95 | 🟢 +26.93% |
| 150,000 | **5,648.35** | 5,124.94 | 🟡 +10.21% |
| 200,000 | **5,616.45** | 5,331.69 | ⚪ +5.34% |

Notice the shape: Intel plateaus almost immediately (~5,600–5,650 GFLOPS from N=100k onward), while Netlib keeps climbing and closing the gap. That convergence pattern is the clue.

---

## So what's actually causing this?

### 1. Overhead vs. compute — a race that only matters early

HPL's runtime is roughly: **fixed startup overhead + O(N³) compute time.** At small N, that fixed overhead — process-grid init, thread pinning, OpenMP binding, memory allocation — eats a *huge* percentage of total runtime. At large N, raw floating-point work dwarfs it completely.

```
Runtime(N) ≈ startup_overhead + compute(N³)

Small N  →  overhead dominates  →  the "faster startup" binary wins big
Large N  →  compute dominates   →  both binaries converge toward the same ceiling
```

Concretely: at N=50,000 the runs finished in **21.8s (Intel) vs. 35.2s (Netlib)** — a gap that's mostly attributable to Intel's streamlined thread pinning, OpenMP binding, and memory-alignment wrappers doing their job *before the real math even starts*. Once N crosses ~150,000, compute time swamps that startup cost and Netlib naturally catches up as raw GEMM throughput takes over.

### 2. Intel plays defense against a bad HPL.dat

This is the subtler one. Netlib's `xhpl` is a **literalist** — it parses `HPL.dat` exactly as written. Feed it a malformed or conflicting entry (say, `# of NBs = 1` but two values `192 256` on the line), and it just... ignores the extras. No optimization, no correction, no warning.

Intel's `xhpl_intel64_dynamic`, by contrast, is an **adaptive runtime**. It inspects the parsed config and, if it spots something suboptimal, can silently auto-tune block sizes, process-grid mappings, or BLAS call parameters underneath you — actively working around a bad config file to avoid leaving hardware on the table.

> [!NOTE]
> This means Intel's "advantage" at small N is partly *runtime intelligence covering for tuning you didn't do*, not raw compute superiority. That's important context when comparing the two.

---

## The takeaway

```
Intel's edge at small N  =  faster startup/init  +  auto-correction of a suboptimal HPL.dat
Intel's edge at large N  ≈  basically gone, because compute dominates for both binaries
```

**Neither binary has more raw FLOP capability than the other at peak workload.** The gap you see at small problem sizes is architectural overhead mitigation and algorithmic auto-tuning — not silicon.

## What to actually do about it

If you're stuck on Netlib and want Intel-like numbers at smaller N, don't just accept the gap — go tune it yourself:

- [ ] Tune `PFACT` (panel factorization algorithm) in `HPL.dat`
- [ ] Tune `MAPS` / look-ahead depth to reduce synchronization stalls
- [ ] Explicitly set thread-to-core affinity instead of relying on defaults
- [ ] Double-check your `NB`, process grid (`P×Q`), and `# of NBs` entries are internally consistent — don't rely on any binary to save you from a sloppy config

And more broadly: **never compare two HPL binaries at a single problem size.** Run the full curve. A 61% gap at N=50,000 and a 5% gap at N=200,000 tell two completely different stories about the same hardware.