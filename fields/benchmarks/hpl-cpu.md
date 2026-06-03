# Benchmarks - HPL-CPU

## Table of Contents
- [Benchmarks - HPL-CPU](#benchmarks---hpl-cpu)
  - [Table of Contents](#table-of-contents)

## Understanding Theoretical HPL Performance on an Intel Xeon Platinum 8568Y+ Node

### 1. System Information

**1.1. CPU Configuration**</br>

| Parameter            | Value                      |
| -------------------- | -------------------------- |
| CPU Model            | Intel Xeon Platinum 8568Y+ |
| Architecture         | Emerald Rapids             |
| Sockets              | 2                          |
| Cores per Socket     | 48                         |
| Total Physical Cores | 96                         |
| Threads per Core     | 1                          |
| NUMA Nodes           | 4                          |
| Maximum Frequency    | 2.301 GHz                  |
| SIMD Support         | AVX, AVX2, AVX-512         |
| FMA Support          | Yes                        |

**NUMA Layout**</br>

| NUMA Node | CPUs  |
| --------- | ----- |
| Node 0    | 0-23  |
| Node 1    | 24-47 |
| Node 2    | 48-71 |
| Node 3    | 72-95 |

---

### 2. What HPL Measures

HPL (High Performance Linpack) measures floating-point performance while solving a dense system of linear equations.

Results are typically reported as:

* GFLOPS = Giga Floating Point Operations Per Second
* TFLOPS = Tera Floating Point Operations Per Second

Definitions:

| Metric | Meaning                        |
| ------ | ------------------------------ |
| Rpeak  | Theoretical peak performance   |
| Rmax   | Measured benchmark performance |

---

### 3. Important CPU Concepts

**3.1. Core:**</br>
A core is an independent compute engine inside the CPU.</br>
More cores generally means more parallel work can be performed.</br>
Example:

* 1 core → 1 worker
* 96 cores → 96 workers

**3.2. Clock Frequency:**</br>
Frequency determines how many cycles occur each second.</br>
Example: 2.301 GHz means **2.301 billion cycles per second**.

**3.3. SIMD:**</br>
SIMD stands for **Single Instruction Multiple Data**.</br>
Instead of operating on one number at a time, SIMD operates on multiple numbers simultaneously.</br>
Example:</br>

- Without SIMD:
    ```text
    a1 + b1
    ```
- With SIMD:
    ```text
    [a1 a2 a3 a4 a5 a6 a7 a8]
    +
    [b1 b2 b3 b4 b5 b6 b7 b8]
    ```

performed in a single instruction.

**3.4. AVX and AVX-512:**</br>

AVX stands for: **Advanced Vector Extensions**</br>
Intel SIMD evolution:

| Technology | Register Width |
| ---------- | -------------- |
| SSE        | 128-bit        |
| AVX        | 256-bit        |
| AVX2       | 256-bit        |
| AVX-512    | 512-bit        |

Our CPU supports AVX-512.

**What Does 512-bit Mean?**</br>
A double-precision floating-point number (FP64) occupies: **64 bits**.</br>
An AVX-512 register contains: $512 / 64 = 8$ double-precision values.</br>
Therefore one AVX-512 instruction can operate on: **8 FP64 values simultaneously**.

**3.5. FMA (Fused Multiply Add):**</br>
FMA stands for: **Fused Multiply Add**.</br>
Instead of:

```text
c = a * b
d = c + e
```

the processor performs: $d = a * b + e$ in a single instruction.</br>
Mathematically this counts as:

```text
1 multiplication
+
1 addition
=
2 FLOPs
```

---

### 4. Calculations

**4.1. FLOPs Produced by One AVX-512 FMA:**</br>
One AVX-512 register contains: 8 FP64 values.</br>
Each FMA performs:

```text
8 multiplications
+
8 additions
=
16 FLOPs
```

Therefore:

```text
1 AVX-512 FMA instruction
=
16 FP64 FLOPs
```

**4.2. Why Do We Multiply by 2 Again?**</br>
The Intel Xeon Platinum 8568Y+ core contains: **2 independent AVX-512 FMA execution units**.</br>
This information does NOT come from `lscpu`.</br>
It comes from Intel microarchitecture documentation for Sapphire Rapids / Emerald Rapids.</br>
Therefore:

```text
16 FLOPs from FMA Unit #1
+
16 FLOPs from FMA Unit #2
=
32 FLOPs/cycle/core
```

**4.3. Deriving FLOPs per Cycle per Core:**</br>
1.  **512-bit register** contains **8 FP64 values**.
2.  **FMA** produces: 8 × 2 = **16 FLOPs**
3.  **2 FMA units** produce **16 × 2 = 32 FLOPs**
4.  Final result: **32 FLOPs/cycle/core**

### 5. Theoretical Peak Performance Formula
**5.1. Formula:**</br>
The standard HPL theoretical peak formula is:

```text
Rpeak =
(Number of Cores)
×
(Frequency)
×
(FLOPs per Cycle per Core)
```

**5.2. Applying the Formula**</br>
1. Total FLOPs per Cycle: 96 cores × 32 FLOPs/cycle/core = 3072 FLOPs/cycle
2. Total FLOPs per Second: 3072 × 2.301 × 10^9 = 7.068672 × 10^12 FLOPs/sec
3. Convert to TFLOPS: 7.068672 × 10^12 = 7.07 TFLOPS
4. Therefore: Rpeak ≈ 7.07 TFLOPS

**5.3. Adjusting for Slurm Allocation:**</br>
The benchmark job saw: 94 CPUs instead of: 96 CPUs</br>
Corrected theoretical peak: 94 × 32 × 2.301 GHz = 6.92 TFLOPS

**5.4. Comparing Against Actual HPL Result:**</br>
Measured result: 5590.64 GFLOPS = 5.59 TFLOPS

**5.5. Efficiency vs Full Node Peak:**</br>

```text
Efficiency =
5.59 / 7.07
=
79.1%
```

**5.6. Efficiency vs Allocated 94-Core Peak:**</br>
Efficiency = 5.59 / 6.92 = 80.8%

**5.7. Why Actual Performance Is Lower Than Theoretical:**</br>
Theoretical calculations assume:

* Every core active
* Every cycle executes useful instructions
* Continuous dual FMA execution
* Maximum frequency maintained

Real systems experience:

* Memory stalls
* Instruction scheduling overhead
* AVX frequency reductions
* Operating system activity
* MPI/OpenMP overhead

Therefore: Rmax < Rpeak is expected.

---

### 6. AVX Frequency Caveat
The formula above uses: **2.301 GHz** which is the maximum advertised frequency.</br>
Under sustained AVX-512 workloads, CPUs often run at lower frequencies.</br>
Example:

| Sustained AVX Frequency | Theoretical Peak |
| ----------------------- | ---------------- |
| 2.30 GHz                | 7.07 TFLOPS      |
| 2.20 GHz                | 6.76 TFLOPS      |
| 2.10 GHz                | 6.45 TFLOPS      |
| 2.00 GHz                | 6.14 TFLOPS      |
| 1.90 GHz                | 5.84 TFLOPS      |

If the CPU sustained approximately 1.9–2.0 GHz during HPL, then a measured result of: **5.59 TFLOPS** corresponds to approximately: **91–96% efficiency** which indicates an excellent HPL run.

---

### 7. Quick Reference Summary

| Item                   | Value                      |
| ---------------------- | -------------------------- |
| CPU                    | Intel Xeon Platinum 8568Y+ |
| Total Cores            | 96                         |
| SIMD Width             | 512-bit                    |
| FP64 Values per Vector | 8                          |
| FLOPs per FMA          | 16                         |
| FMA Units per Core     | 2                          |
| FLOPs/Cycle/Core       | 32                         |
| Frequency Used         | 2.301 GHz                  |
| Rpeak (96 cores)       | 7.07 TFLOPS                |
| Rpeak (94 cores)       | 6.92 TFLOPS                |
| Measured HPL           | 5.59 TFLOPS                |
| Efficiency (96 cores)  | 79.1%                      |
| Efficiency (94 cores)  | 80.8%                      |

---

### 8. Key Takeaways
1. HPL theoretical peak depends primarily on:

   * Number of cores
   * SIMD width
   * Number of FMA units
   * Sustained frequency

2. AVX-512 allows one instruction to operate on eight FP64 values simultaneously.

3. FMA doubles throughput by performing a multiply and add in a single instruction.

4. The Xeon Platinum 8568Y+ can theoretically produce:

   * 32 FP64 FLOPs/cycle/core

5. A measured HPL result of 5.59 TFLOPS on this node is consistent with a well-tuned CPU-only benchmark run.
