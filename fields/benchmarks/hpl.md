# HPL: The Benchmark That Built the TOP500 (and Why Your GFLOPS Number Lies a Little)

> HPL is the benchmark everyone's heard of and almost nobody fully understands. This is the deep dive — from "what is DGEMM" to "why is my node only getting 80% of theoretical peak" — written the way I actually think about it when a job finishes and the number on screen doesn't match what I expected.

## Table of Contents
- [HPL: The Benchmark That Built the TOP500 (and Why Your GFLOPS Number Lies a Little)](#hpl-the-benchmark-that-built-the-top500-and-why-your-gflops-number-lies-a-little)
  - [Table of Contents](#table-of-contents)
  - [Part 1 — What HPL Actually Measures](#part-1--what-hpl-actually-measures)
    - [The core kernel: DGEMM](#the-core-kernel-dgemm)
    - [P × Q: the grid shape that decides your fate](#p--q-the-grid-shape-that-decides-your-fate)
    - [MPI rank placement: the mistake almost everyone makes](#mpi-rank-placement-the-mistake-almost-everyone-makes)
    - [Debugging checklist](#debugging-checklist)
  - [Part 2 — Calculating Theoretical Peak (HPL-CPU)](#part-2--calculating-theoretical-peak-hpl-cpu)
    - [The building blocks: SIMD, AVX-512, FMA](#the-building-blocks-simd-avx-512-fma)
    - [Doing the math](#doing-the-math)
    - [The AVX frequency trap](#the-avx-frequency-trap)
    - [Quick reference](#quick-reference)
  - [Part 3 — HPL-GPU: A Completely Different Animal](#part-3--hpl-gpu-a-completely-different-animal)

---

## Part 1 — What HPL Actually Measures

**HPL (High-Performance Linpack)** measures raw floating-point throughput by solving a dense system of linear equations — the same workload that's produced the TOP500 list for three decades. Two numbers you'll always see:

| Metric | Meaning |
|---|---|
| **Rpeak** | Theoretical peak performance — what the silicon *could* do on paper |
| **Rmax**  | What HPL actually measured — what the silicon *did* do |

Everything below is really just an exercise in explaining the gap between those two numbers.

### The core kernel: DGEMM

`DGEMM` = **D**ouble-precision **GE**neral **M**atrix **M**ultiply:

$$C = \alpha \cdot A \cdot B + \beta \cdot C$$

This one operation eats **95–99% of HPL's total runtime**. Everything else — MPI, orchestration, I/O — is rounding error by comparison. When people say "MKL DGEMM," they mean Intel's hand-optimized implementation from oneAPI MKL, handling:

- Multithreaded matrix multiplication
- Cache blocking
- SIMD vectorization (AVX2/AVX-512, depending on CPU)
- Partial NUMA-aware memory access

The mental model that actually matters:

```
HPL performance  ≈  MPI decomposition efficiency  ×  MKL DGEMM efficiency
```

MPI slices and distributes the matrix. MKL does the heavy lifting inside each rank. Get either one wrong and your GFLOPS number suffers — which is exactly why P×Q and rank placement (next two sections) matter so much.

### P × Q: the grid shape that decides your fate

HPL arranges your MPI processes (or GPUs) into a 2D grid: **P rows × Q columns**. The matrix is chopped into `NB`-sized blocks and distributed block-cyclically across that grid. Two phases alternate, and P vs Q governs which bottleneck you hit:

| Phase | Governed by | What happens | Sensitivity |
|---|---|---|---|
| **Column ops** (factorization) | `P` | LU factorization on a vertical matrix slice — needs synchronous communication among *all* ranks in that column | High latency sensitivity — small, frequent messages |
| **Row ops** (broadcast + update) | `Q` | Factorized column broadcasts horizontally; other ranks update their portion via GEMM | Bandwidth/compute bound, largely hidden by look-ahead pipelining |

> [!TIP]
> **Rule of thumb: keep P ≤ Q, and keep P as small as practically possible.**
>
> - `P=4, Q=2` → too many ranks stall waiting on column-factorization handshakes → GPUs/CPUs idle, GFLOPS drop.
> - `P=2, Q=4` → minimal column-sync overhead, and the wider row dimension gives the look-ahead pipeline more parallel breadth to hide broadcast time behind computation.
>
> For an 8-GPU run, `P=2, Q=4` isn't just *a* valid choice — it's close to mathematically optimal.

### MPI rank placement: the mistake almost everyone makes

Most HPL guides say "1 MPI rank per NUMA domain" — but that advice **silently assumes `OMP_NUM_THREADS > 1`**. Get the flags wrong and you can burn a node down to single-digit core utilization without a single error message.

<details>
<summary><b>❌ The trap: 4 ranks that look correct but use ~4% of your cores</b></summary>

```bash
#SBATCH --cpus-per-task=23
#SBATCH --ntasks=4
export OMP_NUM_THREADS=1

mpirun --report-bindings \
  -np 4 \
  --bind-to core \
  --map-by ppr:1:numa \
  ./xhpl
```

This allocates 23 cores × 4 tasks = 92 cores to the job — but with `OMP_NUM_THREADS=1` and each rank pinned to a single core, **only 4 out of 92 allocated cores ever do work.** That's ~4% utilization, and it will silently produce a low GFLOPS number with zero errors.
</details>

<details>
<summary><b>✅ The fix: let each rank actually spread across its NUMA domain</b></summary>

```bash
mpirun \
  -np 4 \
  --map-by ppr:1:numa:PE=23 \
  --bind-to core \
  ./xhpl
```

`PE=23` tells OpenMPI each rank owns **23 Processing Elements**, so all 92 cores are actually claimed by the 4 ranks.
</details>

### Debugging checklist

Run these *before* you trust a GFLOPS number:

```bash
# 1. Is the job even alive? (thread-level visibility)
ps -eLo pid,tid,psr,comm | grep xhpl

# 2. What binding did MPI actually apply?
mpirun --report-bindings -np 4 --bind-to core --map-by ppr:1:numa hostname

# 3. Is Slurm doing what you think it's doing?
srun -n 4 --cpu-bind=verbose bash -c 'echo Rank=$SLURM_PROCID; taskset -cp $$'
```

Expected shape of output for step 3 (masks will differ per node/topology):

```text
cpu-bind=MASK - gpu209-06, task  0  0 [3585787]: mask 0x1fffff9 set
cpu-bind=MASK - gpu209-06, task  1  1 [3585788]: mask 0x33ffffe000000 set
...
pid 3585787's current affinity list: 0,3-24
pid 3585788's current affinity list: 25-45,48,49
```

<details>
<summary>📄 Real example: full <code>ps -eLo</code> thread dump from Case #1 (heavily truncated)</summary>

```text
3521137 3521137   0 xhpl      ← main rank thread, core 0
3521137 3521163  95 xhpl      ← worker thread pinned to core 95
3521137 3521164  94 xhpl      ← worker thread pinned to core 94
...
(dozens more lines, one per OS thread, each pinned to a distinct core)
...
3521140 3521540   0 xhpl      ← last thread of last rank
```

The pattern to look for: each rank should spread its worker threads across a *distinct, non-overlapping* block of cores. If you see multiple ranks' threads piling onto the same core numbers, your binding is broken.
</details>

**One more question worth asking every time:** *which BLAS is actually linked into this binary?* Some vendor HPL builds spawn internally-threaded MKL DGEMM kernels even when `OMP_NUM_THREADS=1` — silently using far more cores than your environment variables suggest.

```bash
ldd ./xhpl | egrep "mkl|openblas|blis"
```

---

## Part 2 — Calculating Theoretical Peak (HPL-CPU)

Worked example: **Intel Xeon Platinum 8568Y+ (Emerald Rapids)**, 2 sockets × 48 cores = 96 total cores, 4 NUMA nodes, max frequency 2.301 GHz, AVX-512 capable.

| NUMA Node | CPUs |
|---|---|
| 0 | 0–23 |
| 1 | 24–47 |
| 2 | 48–71 |
| 3 | 72–95 |

### The building blocks: SIMD, AVX-512, FMA

**SIMD** (Single Instruction, Multiple Data) means one instruction operates on many numbers at once instead of one:

```text
Without SIMD:   a1 + b1
With SIMD:      [a1 a2 a3 a4 a5 a6 a7 a8] + [b1 b2 b3 b4 b5 b6 b7 b8]   ← one instruction
```

**AVX-512** means a 512-bit register. Since FP64 = 64 bits:

$$\frac{512}{64} = 8 \text{ double-precision values per register}$$

**FMA (Fused Multiply-Add)** collapses `c = a*b; d = c+e` into a single instruction: `d = a*b + e`. Mathematically that's **1 multiply + 1 add = 2 FLOPs**, done in one shot.

### Doing the math

**Step 1 — FLOPs per FMA instruction:**

$$8 \text{ FP64 values} \times 2 \text{ FLOPs (mul+add)} = 16 \text{ FLOPs per FMA}$$

**Step 2 — Why multiply by 2 again:** the 8568Y+ core has **2 independent AVX-512 FMA execution units** (this comes from Intel's Emerald Rapids microarchitecture docs, not from `lscpu`):

$$16 \text{ (unit 1)} + 16 \text{ (unit 2)} = 32 \text{ FLOPs/cycle/core}$$

**Step 3 — Theoretical peak formula:**

$$R_{peak} = (\text{Cores}) \times (\text{Frequency}) \times (\text{FLOPs/cycle/core})$$

Plugging in numbers:

```text
96 cores × 32 FLOPs/cycle          = 3,072 FLOPs/cycle
3,072 × 2.301 × 10⁹ cycles/sec     = 7.068672 × 10¹² FLOPs/sec
                                    = 7.07 TFLOPS  (Rpeak, full 96-core node)
```

**Step 4 — Adjust for what Slurm actually gave you.** If the job only saw 94 cores (2 reserved elsewhere, e.g. for Weka FS):

$$94 \times 32 \times 2.301\ \text{GHz} = 6.92\ \text{TFLOPS}$$

**Step 5 — Compare to what you actually measured.** Say HPL reported `5,590.64 GFLOPS = 5.59 TFLOPS`:

$$\text{Efficiency vs. 96-core peak} = \frac{5.59}{7.07} = 79.1\%$$

$$\text{Efficiency vs. 94-core allocated peak} = \frac{5.59}{6.92} = 80.8\%$$

That gap (≈20%) isn't a red flag by itself — it's expected. Real systems lose ground to memory stalls, instruction scheduling overhead, AVX frequency throttling, OS jitter, and MPI/OpenMP overhead. `Rmax < Rpeak` is the rule, not the exception.

### The AVX frequency trap

The formula above assumed the CPU sustains its **maximum advertised frequency (2.301 GHz)** — but sustained AVX-512 workloads routinely throttle lower under real thermal/power conditions:

| Sustained AVX Frequency | Theoretical Peak |
|---:|---:|
| 2.30 GHz | 7.07 TFLOPS |
| 2.20 GHz | 6.76 TFLOPS |
| 2.10 GHz | 6.45 TFLOPS |
| 2.00 GHz | 6.14 TFLOPS |
| 1.90 GHz | 5.84 TFLOPS |

> [!IMPORTANT]
> This is why "efficiency" numbers can be misleading in either direction. If this CPU actually sustained ~1.9–2.0 GHz under AVX-512 load (which is common), that same 5.59 TFLOPS result reflects **91–96% efficiency**, not 79–81%. Always know which denominator you're using before declaring a run "bad."

### Quick reference

| Item | Value |
|---|---|
| CPU | Intel Xeon Platinum 8568Y+ |
| Total Cores | 96 |
| SIMD Width | 512-bit |
| FP64 per vector | 8 |
| FLOPs per FMA | 16 |
| FMA units/core | 2 |
| FLOPs/cycle/core | 32 |
| Frequency used | 2.301 GHz |
| Rpeak (96 cores) | 7.07 TFLOPS |
| Rpeak (94 cores) | 6.92 TFLOPS |
| Measured HPL | 5.59 TFLOPS |
| Efficiency (96c) | 79.1% |
| Efficiency (94c) | 80.8% |

**Key takeaways:**
1. Peak depends on core count × SIMD width × FMA units × sustained frequency — nothing else.
2. AVX-512 processes 8 FP64 values per instruction.
3. FMA doubles throughput by fusing multiply + add.
4. This CPU's ceiling: 32 FP64 FLOPs/cycle/core.
5. 5.59 TFLOPS on this node is a solid, well-tuned CPU-only result — context (sustained frequency) determines whether it's "good" or "great."

---

## Part 3 — HPL-GPU: A Completely Different Animal

Everything above was CPU-bound HPL. **HPL-GPU flips the script entirely** — the GPU now does >95% of the DGEMM trailing-matrix-update FLOPs, and the CPU's job shrinks down to three supporting roles:

1. **Panel factorization** — the LU decomposition of the *current* panel runs on the host CPU (threaded BLAS) while the GPU chews on the *previous* panel's trailing update. NVIDIA's `hpl.sh` pipelines this via look-ahead, so it's overlapped, not serial.
2. **Data staging** — packing/unpacking buffers before handing them to the GPU across PCIe/NVLink.
3. **MPI communication** — broadcasting panels between ranks.

Because of that overlap, HPL-GPU is **far less core-hungry** than CPU-only HPL. Core count matters, but in a threshold way, not a linear way:

```
Too few cores    →  panel factorization can't keep pace with GPU trailing update
                 →  GPU stalls waiting on the CPU  →  shows up as low GPU utilization,
                     not a clean linear slowdown

Enough cores     →  factorization comfortably finishes inside the look-ahead window
                 →  GPU stays fed  →  adding *more* cores past this point gives
                     diminishing-to-zero returns, because the GPU is now the bound resource
```

Where exactly that "enough" threshold sits isn't fixed — it depends on problem size (`N`) and block size (`NB`). A bigger `N` per rank means a bigger panel to factor at each step, which needs more host threads to hide the work under the same GPU compute window.

**The practical implication:** don't blindly throw more CPU cores at an HPL-GPU job expecting linear gains the way you would with HPL-CPU. Find the threshold where the GPU stops stalling, and stop there — anything beyond is wasted allocation you could give to another job.