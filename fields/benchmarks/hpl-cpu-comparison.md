# Technical Analysis: Intel Container vs. Netlib `xhpl` Performance Discrepancy

### Executive Summary

When benchmarking smaller problem sizes (e.g., $N=50000$), the Intel Optimized HPL Container (`xhpl_intel64_dynamic`) demonstrates a significant performance advantage over standard Netlib `xhpl` binaries.

As problem size scales up to $N=200000$, the performance gap diminishes significantly:

* **At $N=50000$:** Intel Container is **~61.5% faster** ($3818$ vs $2365$ GFLOPS).
* **At $N=200000$:** Netlib `xhpl` catches up, narrowing the performance gap to **~5.3%** ($5616$ vs $5331$ GFLOPS).

This behavior indicates that the Intel container's advantage is **not driven by compute-bound compute limits**, but rather by **architectural overhead mitigation and algorithmic auto-tuning** that heavily favors smaller matrix sizes.

---

### Benchmark Comparison Data (94 CPU Cores, Fixed NB=384)

| Problem Size ($N$) | Container (GFLOPS) | Netlib `xhpl` (GFLOPS) | Container Advantage |
| --- | --- | --- | --- |
| **50,000** | **3,818.21** | 2,364.87 | **+61.45%** |
| **100,000** | **5,438.80** | 4,284.95 | **+26.93%** |
| **150,000** | **5,648.35** | 5,124.94 | **+10.21%** |
| **200,000** | **5,616.45** | 5,331.69 | **+5.34%** |

---

### Core Drivers of the Performance Discrepancy

#### 1. Runtime Overhead & Initialization Amortization

* **Small Problem Overhead ($N=50000$):** At smaller matrix sizes, non-compute overheads—such as process grid initialization, thread subscription/binding, and memory allocation—occupy a larger percentage of total execution time.
* **Algorithmic Complexity Crossover:** The Intel dynamic binary includes optimized runtime wrappers that streamline initial thread pinning, OpenMP binding, and memory alignment. Netlib `xhpl` suffers from raw startup and synchronization overheads, which dominate short runtime durations (e.g., 21.8s vs 35.2s).
* **Large Problem Saturation ($N \ge 150000$):** As $N$ increases to 150,000+, compute time ($O(N^3)$ complexity) completely dominates startup overhead ($O(N^2)$ / fixed overheads). The Intel container reaches performance saturation around $5600$ GFLOPS, while Netlib catches up naturally once raw floating-point operations dominate execution.

#### 2. Dynamic Input Correction & Robust Parameter Handling

* **Parameter Mismatch Tolerance:** Netlib `xhpl` strictly follows `HPL.dat` entries line-by-line. When presented with malformed or conflicting parameters (e.g., `# of NBs = 1` while providing two values like `192 256`), standard `xhpl` ignores trailing values without optimizing the execution strategy.
* **Intel Adaptive Overrides:** The dynamic Intel wrapper (`xhpl_intel64_dynamic`) inspects configuration parameters at runtime. If suboptimal or conflicting parameters are detected, the Intel library can dynamically auto-tune block sizes, process grid mappings, or BLAS call parameters under the hood to prevent hardware underutilization.

---

### Key Takeaway & Next Steps

The higher throughput seen in the Intel Container at small scale is due to **intel-native runtime dynamic tuning and reduced initialization latency**, not superior raw FLOP capability at peak workload.

> **Recommendation:** To achieve Intel-like performance on native Netlib `xhpl` at smaller problem sizes ($N=50000$), carefully tune the remaining `HPL.dat` control parameters—specifically panel factorization algorithms (`PFACT`), look-ahead depth (`MAPS`), and thread-to-core affinity settings—to bypass default synchronization overheads.