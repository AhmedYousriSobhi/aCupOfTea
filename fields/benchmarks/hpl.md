# Benchmarks - HPL

## Table of Contents
- [Benchmarks - HPL](#benchmarks---hpl)
  - [Table of Contents](#table-of-contents)
  - [HPL Benchmark Concept](#hpl-benchmark-concept)
    - [1. What HPL Measures](#1-what-hpl-measures)
    - [. What is MKL DGEMM?](#-what-is-mkl-dgemm)
    - [2. Understanding the Difference Between P and Q](#2-understanding-the-difference-between-p-and-q)
    - [3. MPI Guide](#3-mpi-guide)
      - [Debug](#debug)
      - [Question: Which BLAS library is linked into your HPL?](#question-which-blas-library-is-linked-into-your-hpl)
  - [HPL-CPU: Understanding Theoretical HPL Performance on an Intel Xeon Platinum 8568Y+ Node](#hpl-cpu-understanding-theoretical-hpl-performance-on-an-intel-xeon-platinum-8568y-node)
    - [1. System Information](#1-system-information)
    - [2. Important CPU Concepts](#2-important-cpu-concepts)
    - [3. Calculations](#3-calculations)
    - [4. Theoretical Peak Performance Formula](#4-theoretical-peak-performance-formula)
    - [5. AVX Frequency Caveat](#5-avx-frequency-caveat)
    - [6. Quick Reference Summary](#6-quick-reference-summary)
    - [7. Key Takeaways](#7-key-takeaways)
  - [HPL-GPU](#hpl-gpu)
    - [1. How CPU core count affects HPL-GPU performance](#1-how-cpu-core-count-affects-hpl-gpu-performance)



## HPL Benchmark Concept

### 1. What HPL Measures

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

### . What is MKL DGEMM?
`DGEMM` = Double-Precision General Matrix Multiply: $C=\alpha A.B+\beta C$ ; it's the core kernel inside HPL (this is where ~95% of time is spent)</br>
It is the core kernel inside HPL (this is where ~95–99% of time is spent).</br>
MKL DGEMM means Intel's optimized implementation from Intel oneAPI Math Kernel Library (MKL).</br>

It is responsible for:
- Multithreaded matrix multiplication
- Cache blocking
- SIMD vectorization (AVX2/AVX-512 depending on CPU)
- NUMA-aware memory access (partially)

In **HPL**:
- MPI handles distribution of matrix blocks
- MKL DGEMM does the heavy compute inside each rank

So HPL performance is basically: **MPI decomposition × MKL DGEMM efficiency**

---

### 2. Understanding the Difference Between P and Q

In the High-Performance Linpack (HPL) benchmark, the total number of MPI processes (or GPUs) is organized into a 2D Cartesian grid denoted as P×Q, where:
- P represents the number of process rows.
- Q represents the number of process columns.

The matrix is sliced into small blocks (NB) and distributed across this grid using a block-cyclic distribution method. The algorithm alternates between two main phases, and how you balance P and Q dictates how communication bottlenecks form.
1. Column Operations (Factorization) → Governed by P: To solve the linear system, HPL must perform LU factorization on a vertical slice of the matrix (a block column).
    - This operation requires heavy, synchronous communication among all processes residing in the same grid column.
    - Because these messages are relatively small but happen frequently, this phase is highly sensitive to network latency.
    - If P is large (e.g., P=4,Q=2): More processes are forced to synchronize and communicate within each column. This increases latency overhead and stalls the GPUs while they wait for data handshakes.

2. Row Operations (Broadcast & Update) → Governed by Q: Once a column is factorized, it must be broadcast horizontally across the process row so that all other processes can update their remaining portions of the matrix using dense matrix multiplication (GEMM).
   - This phase is highly data-parallel and is bound by computational bandwidth and raw floating-point speed.
   - HPL uses a lookahead algorithm, which means while one column row is broadcasting and updating, the next column factorization is already starting. This hides the row broadcast time behind matrix computation.
   - If Q is large (e.g., P=2,Q=4): You have fewer processes stalling during column factorization (P=2), and you have more process breadth (Q=4) to parallelize the heavy matrix update calculations.

**Summary: Why P<Q (P=2,Q=4) is preferred**</br>
As a hard rule of thumb in HPC engineering, you should almost always configure P≤Q (and ideally, P should be as small as practically possible while keeping the grid roughly square).
- Setting P>Q (P=4,Q=2): Exposes your benchmark to severe column-factorization latency. It will almost always result in lower GFLOPS scores because the GPUs spend too much time synchronizing.
- Setting P<Q (P=2,Q=4): Minimizes column synchronization overhead while giving the lookahead pipeline more row processes to effectively stream and overlap matrix updates. Your script's selection of P=2, Q=4 for the 8-GPU run is the mathematically superior choice.

---

### 3. MPI Guide
Many HPL guides recommend `1 MPI rank per NUMA domain`, but this advice assume `OpemMP threads > 1`.

Index|Case Example|Code|Illustration
|-|-|-|-|
1|23 Cores allocated per Task</br>4 Tasks</br>4 MPI ranks</br>Each Rank uses 1 thread.</br>Each rank is pinned to a single core</br>Per Rank: 1 core x 4 ranks = 4 active cores|#SBATCH --cpus-per-task=23</br>#SBATCH --ntasks=4</br>export OMP_NUM_THREADS=1</br>mpirun --report-bindings \\</br>-np 4 \\</br>--bind-to core \\</br>--map-by ppr:1:numa \\</br>./xhpl|This utilize only 4 out of 92 (4 tasks * 23 core per task) CPU allocated.</br>This utilized only 4/92 ~ 4% of available cores.
2||mpirun \\</br>-np 4 \\</br>--map-by ppr:1:numa:PE=23 \\</br>--bind-to core \\</br>./xhpl||

#### Debug
1. To check is the test is running:</br>
    ```bash
    # Thread Level Visibility
    ps -eLo pid,tid,psr,comm | grep xhpl
    ```
2. To tell what is the actual binding:
    ```bash
    mpirun \
    --report-bindings \
    -np 4 \
    --bind-to core \
    --map-by ppr:1:numa \
    hostname
    ```
3. Confirm if Slurm is doing the right thing!
    ```bash
    srun -n 4 --cpu-bind=verbose bash -c 'echo Rank=$SLURM_PROCID; taskset -cp $$'

    # Expected output
    cpu-bind=MASK - gpu209-06, task  0  0 [3585787]: mask 0x1fffff9 set
    cpu-bind=MASK - gpu209-06, task  1  1 [3585788]: mask 0x33ffffe000000 set
    cpu-bind=MASK - gpu209-06, task  2  2 [3585789]: mask 0x1fffffc000000000000 set
    cpu-bind=MASK - gpu209-06, task  3  3 [3585790]: mask 0xfffffe000000000000000000 set

    Rank=1
    Rank=3
    Rank=2
    Rank=0
    pid 3585787's current affinity list: 0,3-24
    pid 3585788's current affinity list: 25-45,48,49
    pid 3585789's current affinity list: 50-72
    pid 3585790's current affinity list: 73-95
    ```
4. To confirm on which the HPL binaries is built over:
    ```bash
    strings ./xhpl_intel64_dynamic | egrep -i "dgemm|blas|mkl|openblas|blis|aocl|amd"
    ```

Below was from running Case example #1 !
<details>
  <summary>Output Example</summary>
    ps -eLo pid,tid,psr,comm | grep xhpl</br>
    3521137 3521137   0 xhpl</br>
    3521137 3521145   0 xhpl</br>
    3521137 3521147   0 xhpl</br>
    3521137 3521161   3 xhpl</br>
    3521137 3521162   0 xhpl</br>
    3521137 3521163  95 xhpl</br>
    3521137 3521164  94 xhpl</br>
    3521137 3521165   4 xhpl</br>
    3521137 3521166  93 xhpl</br>
    3521137 3521167  92 xhpl</br>
    3521137 3521168  91 xhpl</br>
    3521137 3521169   8 xhpl</br>
    3521137 3521170   9 xhpl</br>
    3521137 3521171  10 xhpl</br>
    3521137 3521172  11 xhpl</br>
    3521137 3521173  12 xhpl</br>
    3521137 3521174  13 xhpl</br>
    3521137 3521175  14 xhpl</br>
    3521137 3521176  15 xhpl</br>
    3521137 3521177  16 xhpl</br>
    3521137 3521178  17 xhpl</br>
    3521137 3521179  18 xhpl</br>
    3521137 3521180  19 xhpl</br>
    3521137 3521181  20 xhpl</br>
    3521137 3521182  21 xhpl</br>
    3521137 3521183  22 xhpl</br>
    3521137 3521184  23 xhpl</br>
    3521137 3521185  24 xhpl</br>
    3521137 3521186  25 xhpl</br>
    3521137 3521187  26 xhpl</br>
    3521137 3521188  27 xhpl</br>
    3521137 3521189  28 xhpl</br>
    3521137 3521190  29 xhpl</br>
    3521137 3521191  30 xhpl</br>
    3521137 3521192  31 xhpl</br>
    3521137 3521193  32 xhpl</br>
    3521137 3521194  33 xhpl</br>
    3521137 3521195  34 xhpl</br>
    3521137 3521196  35 xhpl</br>
    3521137 3521197  36 xhpl</br>
    3521137 3521198  37 xhpl</br>
    3521137 3521199   5 xhpl</br>
    3521137 3521200  38 xhpl</br>
    3521137 3521201  39 xhpl</br>
    3521137 3521202  40 xhpl</br>
    3521137 3521203  41 xhpl</br>
    3521137 3521204  42 xhpl</br>
    3521137 3521205  43 xhpl</br>
    3521137 3521206  44 xhpl</br>
    3521137 3521207  45 xhpl</br>
    3521137 3521208   0 xhpl</br>
    3521137 3521209   0 xhpl</br>
    3521137 3521210  48 xhpl</br>
    3521137 3521211  49 xhpl</br>
    3521137 3521212  50 xhpl</br>
    3521137 3521213  51 xhpl</br>
    3521137 3521214  52 xhpl</br>
    3521137 3521215  53 xhpl</br>
    3521137 3521216  54 xhpl</br>
    3521137 3521217  55 xhpl</br>
    3521137 3521218  56 xhpl</br>
    3521137 3521219  57 xhpl</br>
    3521137 3521220   6 xhpl</br>
    3521137 3521221  58 xhpl</br>
    3521137 3521222  59 xhpl</br>
    3521137 3521223  60 xhpl</br>
    3521137 3521224  61 xhpl</br>
    3521137 3521225  62 xhpl</br>
    3521137 3521226  63 xhpl</br>
    3521137 3521227  64 xhpl</br>
    3521137 3521228  65 xhpl</br>
    3521137 3521229  66 xhpl</br>
    3521137 3521230  67 xhpl</br>
    3521137 3521231  68 xhpl</br>
    3521137 3521232  69 xhpl</br>
    3521137 3521233  70 xhpl</br>
    3521137 3521234  71 xhpl</br>
    3521137 3521235  72 xhpl</br>
    3521137 3521236  73 xhpl</br>
    3521137 3521237  74 xhpl</br>
    3521137 3521238  75 xhpl</br>
    3521137 3521239  76 xhpl</br>
    3521137 3521240  77 xhpl</br>
    3521137 3521241  78 xhpl</br>
    3521137 3521242  79 xhpl</br>
    3521137 3521243  80 xhpl</br>
    3521137 3521244  81 xhpl</br>
    3521137 3521245  82 xhpl</br>
    3521137 3521246   7 xhpl</br>
    3521137 3521247  83 xhpl</br>
    3521137 3521248  84 xhpl</br>
    3521137 3521249  85 xhpl</br>
    3521137 3521250  86 xhpl</br>
    3521137 3521251  87 xhpl</br>
    3521137 3521252  88 xhpl</br>
    3521137 3521253  89 xhpl</br>
    3521137 3521254  90 xhpl</br>
    3521137 3521537   0 xhpl</br>
    3521138 3521138   0 xhpl</br>
    3521138 3521141  24 xhpl</br>
    3521138 3521142  24 xhpl</br>
    3521138 3521349   0 xhpl</br>
    3521138 3521350   3 xhpl</br>
    3521138 3521351  69 xhpl</br>
    3521138 3521352  71 xhpl</br>
    3521138 3521353   6 xhpl</br>
    3521138 3521354   7 xhpl</br>
    3521138 3521355   8 xhpl</br>
    3521138 3521356   9 xhpl</br>
    3521138 3521357  10 xhpl</br>
    3521138 3521358  11 xhpl</br>
    3521138 3521359  12 xhpl</br>
    3521138 3521360  13 xhpl</br>
    3521138 3521361  14 xhpl</br>
    3521138 3521362  15 xhpl</br>
    3521138 3521363  16 xhpl</br>
    3521138 3521364  17 xhpl</br>
    3521138 3521365  18 xhpl</br>
    3521138 3521366  19 xhpl</br>
    3521138 3521367  20 xhpl</br>
    3521138 3521368  21 xhpl</br>
    3521138 3521369  22 xhpl</br>
    3521138 3521370  23 xhpl</br>
    3521138 3521371  24 xhpl</br>
    3521138 3521372  25 xhpl</br>
    3521138 3521373   4 xhpl</br>
    3521138 3521374  26 xhpl</br>
    3521138 3521375  27 xhpl</br>
    3521138 3521376  28 xhpl</br>
    3521138 3521377  29 xhpl</br>
    3521138 3521378  30 xhpl</br>
    3521138 3521379  31 xhpl</br>
    3521138 3521380  32 xhpl</br>
    3521138 3521381  33 xhpl</br>
    3521138 3521382  34 xhpl</br>
    3521138 3521383  35 xhpl</br>
    3521138 3521384  36 xhpl</br>
    3521138 3521385  37 xhpl</br>
    3521138 3521386  38 xhpl</br>
    3521138 3521387  39 xhpl</br>
    3521138 3521388  40 xhpl</br>
    3521138 3521389  41 xhpl</br>
    3521138 3521390  42 xhpl</br>
    3521138 3521391  43 xhpl</br>
    3521138 3521392  44 xhpl</br>
    3521138 3521393  45 xhpl</br>
    3521138 3521394   0 xhpl</br>
    3521138 3521395   0 xhpl</br>
    3521138 3521396   5 xhpl</br>
    3521138 3521397  48 xhpl</br>
    3521138 3521398  49 xhpl</br>
    3521138 3521399  50 xhpl</br>
    3521138 3521400  51 xhpl</br>
    3521138 3521401  52 xhpl</br>
    3521138 3521402  53 xhpl</br>
    3521138 3521403  54 xhpl</br>
    3521138 3521404  55 xhpl</br>
    3521138 3521405  56 xhpl</br>
    3521138 3521406  57 xhpl</br>
    3521138 3521407  58 xhpl</br>
    3521138 3521408  59 xhpl</br>
    3521138 3521409  60 xhpl</br>
    3521138 3521410  61 xhpl</br>
    3521138 3521411  62 xhpl</br>
    3521138 3521412  63 xhpl</br>
    3521138 3521413  64 xhpl</br>
    3521138 3521414  65 xhpl</br>
    3521138 3521415  66 xhpl</br>
    3521138 3521416  67 xhpl</br>
    3521138 3521417  68 xhpl</br>
    3521138 3521418  70 xhpl</br>
    3521138 3521419  72 xhpl</br>
    3521138 3521420  73 xhpl</br>
    3521138 3521421  74 xhpl</br>
    3521138 3521422  75 xhpl</br>
    3521138 3521423  76 xhpl</br>
    3521138 3521424  77 xhpl</br>
    3521138 3521425  78 xhpl</br>
    3521138 3521426  79 xhpl</br>
    3521138 3521427  80 xhpl</br>
    3521138 3521428  81 xhpl</br>
    3521138 3521429  82 xhpl</br>
    3521138 3521430  83 xhpl</br>
    3521138 3521431  84 xhpl</br>
    3521138 3521432  85 xhpl</br>
    3521138 3521433  86 xhpl</br>
    3521138 3521434  87 xhpl</br>
    3521138 3521435  88 xhpl</br>
    3521138 3521436  89 xhpl</br>
    3521138 3521437  90 xhpl</br>
    3521138 3521438  91 xhpl</br>
    3521138 3521439  92 xhpl</br>
    3521138 3521440  93 xhpl</br>
    3521138 3521441  94 xhpl</br>
    3521138 3521442  95 xhpl</br>
    3521138 3521539   0 xhpl</br>
    3521139 3521139   0 xhpl</br>
    3521139 3521143  48 xhpl</br>
    3521139 3521144  48 xhpl</br>
    3521139 3521255   0 xhpl</br>
    3521139 3521256   3 xhpl</br>
    3521139 3521257  15 xhpl</br>
    3521139 3521258  38 xhpl</br>
    3521139 3521259  82 xhpl</br>
    3521139 3521260   7 xhpl</br>
    3521139 3521261   8 xhpl</br>
    3521139 3521262   9 xhpl</br>
    3521139 3521263  10 xhpl</br>
    3521139 3521264  11 xhpl</br>
    3521139 3521265  12 xhpl</br>
    3521139 3521266  13 xhpl</br>
    3521139 3521267  14 xhpl</br>
    3521139 3521268   4 xhpl</br>
    3521139 3521269  16 xhpl</br>
    3521139 3521270  17 xhpl</br>
    3521139 3521271  18 xhpl</br>
    3521139 3521272  19 xhpl</br>
    3521139 3521273  20 xhpl</br>
    3521139 3521274  21 xhpl</br>
    3521139 3521275  22 xhpl</br>
    3521139 3521276  23 xhpl</br>
    3521139 3521277  24 xhpl</br>
    3521139 3521278  25 xhpl</br>
    3521139 3521279  26 xhpl</br>
    3521139 3521280  27 xhpl</br>
    3521139 3521281  28 xhpl</br>
    3521139 3521282  29 xhpl</br>
    3521139 3521283  30 xhpl</br>
    3521139 3521284  31 xhpl</br>
    3521139 3521285  32 xhpl</br>
    3521139 3521286  33 xhpl</br>
    3521139 3521287  34 xhpl</br>
    3521139 3521288  35 xhpl</br>
    3521139 3521289  36 xhpl</br>
    3521139 3521290  37 xhpl</br>
    3521139 3521291   5 xhpl</br>
    3521139 3521292  39 xhpl</br>
    3521139 3521293  40 xhpl</br>
    3521139 3521294  41 xhpl</br>
    3521139 3521295  42 xhpl</br>
    3521139 3521296  43 xhpl</br>
    3521139 3521297  44 xhpl</br>
    3521139 3521298  45 xhpl</br>
    3521139 3521299   0 xhpl</br>
    3521139 3521300   0 xhpl</br>
    3521139 3521301  48 xhpl</br>
    3521139 3521302  49 xhpl</br>
    3521139 3521303  50 xhpl</br>
    3521139 3521304  51 xhpl</br>
    3521139 3521305  52 xhpl</br>
    3521139 3521306  53 xhpl</br>
    3521139 3521307  54 xhpl</br>
    3521139 3521308  55 xhpl</br>
    3521139 3521309  56 xhpl</br>
    3521139 3521310  57 xhpl</br>
    3521139 3521311  58 xhpl</br>
    3521139 3521312  59 xhpl</br>
    3521139 3521313  60 xhpl</br>
    3521139 3521314  61 xhpl</br>
    3521139 3521315  62 xhpl</br>
    3521139 3521316  63 xhpl</br>
    3521139 3521317  64 xhpl</br>
    3521139 3521318  65 xhpl</br>
    3521139 3521319  66 xhpl</br>
    3521139 3521320  67 xhpl</br>
    3521139 3521321  68 xhpl</br>
    3521139 3521322  69 xhpl</br>
    3521139 3521323  70 xhpl</br>
    3521139 3521324  71 xhpl</br>
    3521139 3521325  72 xhpl</br>
    3521139 3521326  73 xhpl</br>
    3521139 3521327  74 xhpl</br>
    3521139 3521328  75 xhpl</br>
    3521139 3521329  76 xhpl</br>
    3521139 3521330  77 xhpl</br>
    3521139 3521331  78 xhpl</br>
    3521139 3521332  79 xhpl</br>
    3521139 3521333  80 xhpl</br>
    3521139 3521334  81 xhpl</br>
    3521139 3521335   6 xhpl</br>
    3521139 3521336  83 xhpl</br>
    3521139 3521337  84 xhpl</br>
    3521139 3521338  85 xhpl</br>
    3521139 3521339  86 xhpl</br>
    3521139 3521340  87 xhpl</br>
    3521139 3521341  88 xhpl</br>
    3521139 3521342  89 xhpl</br>
    3521139 3521343  90 xhpl</br>
    3521139 3521344  91 xhpl</br>
    3521139 3521345  92 xhpl</br>
    3521139 3521346  93 xhpl</br>
    3521139 3521347  94 xhpl</br>
    3521139 3521348  95 xhpl</br>
    3521139 3521538   0 xhpl</br>
    3521140 3521140   0 xhpl</br>
    3521140 3521146  72 xhpl</br>
    3521140 3521148  72 xhpl</br>
    3521140 3521443   0 xhpl</br>
    3521140 3521444   3 xhpl</br>
    3521140 3521445  71 xhpl</br>
    3521140 3521446  72 xhpl</br>
    3521140 3521447  73 xhpl</br>
    3521140 3521448   7 xhpl</br>
    3521140 3521449  83 xhpl</br>
    3521140 3521450  91 xhpl</br>
    3521140 3521451  10 xhpl</br>
    3521140 3521452  11 xhpl</br>
    3521140 3521453  12 xhpl</br>
    3521140 3521454  13 xhpl</br>
    3521140 3521455  14 xhpl</br>
    3521140 3521456   4 xhpl</br>
    3521140 3521457  15 xhpl</br>
    3521140 3521458  16 xhpl</br>
    3521140 3521459  17 xhpl</br>
    3521140 3521460  18 xhpl</br>
    3521140 3521461  19 xhpl</br>
    3521140 3521462  20 xhpl</br>
    3521140 3521463  21 xhpl</br>
    3521140 3521464  22 xhpl</br>
    3521140 3521465  23 xhpl</br>
    3521140 3521466  24 xhpl</br>
    3521140 3521467  25 xhpl</br>
    3521140 3521468  26 xhpl</br>
    3521140 3521469  27 xhpl</br>
    3521140 3521470  28 xhpl</br>
    3521140 3521471  29 xhpl</br>
    3521140 3521472  30 xhpl</br>
    3521140 3521473  31 xhpl</br>
    3521140 3521474  32 xhpl</br>
    3521140 3521475  33 xhpl</br>
    3521140 3521476  34 xhpl</br>
    3521140 3521477   5 xhpl</br>
    3521140 3521478  35 xhpl</br>
    3521140 3521479  36 xhpl</br>
    3521140 3521480  37 xhpl</br>
    3521140 3521481  38 xhpl</br>
    3521140 3521482  39 xhpl</br>
    3521140 3521483  40 xhpl</br>
    3521140 3521484  41 xhpl</br>
    3521140 3521485  42 xhpl</br>
    3521140 3521486  43 xhpl</br>
    3521140 3521487  44 xhpl</br>
    3521140 3521488  45 xhpl</br>
    3521140 3521489   0 xhpl</br>
    3521140 3521490   0 xhpl</br>
    3521140 3521491  48 xhpl</br>
    3521140 3521492  49 xhpl</br>
    3521140 3521493  50 xhpl</br>
    3521140 3521494  51 xhpl</br>
    3521140 3521495  52 xhpl</br>
    3521140 3521496  53 xhpl</br>
    3521140 3521497  54 xhpl</br>
    3521140 3521498  55 xhpl</br>
    3521140 3521499  56 xhpl</br>
    3521140 3521500  57 xhpl</br>
    3521140 3521501  58 xhpl</br>
    3521140 3521502  59 xhpl</br>
    3521140 3521503  60 xhpl</br>
    3521140 3521504  61 xhpl</br>
    3521140 3521505  62 xhpl</br>
    3521140 3521506  63 xhpl</br>
    3521140 3521507  64 xhpl</br>
    3521140 3521508  65 xhpl</br>
    3521140 3521509  66 xhpl</br>
    3521140 3521510  67 xhpl</br>
    3521140 3521511  68 xhpl</br>
    3521140 3521512  69 xhpl</br>
    3521140 3521513  70 xhpl</br>
    3521140 3521514   6 xhpl</br>
    3521140 3521515  74 xhpl</br>
    3521140 3521516  75 xhpl</br>
    3521140 3521517  76 xhpl</br>
    3521140 3521518  77 xhpl</br>
    3521140 3521519  78 xhpl</br>
    3521140 3521520  79 xhpl</br>
    3521140 3521521  80 xhpl</br>
    3521140 3521522  81 xhpl</br>
    3521140 3521523  82 xhpl</br>
    3521140 3521524   8 xhpl</br>
    3521140 3521525  84 xhpl</br>
    3521140 3521526  85 xhpl</br>
    3521140 3521527  86 xhpl</br>
    3521140 3521528  87 xhpl</br>
    3521140 3521529  88 xhpl</br>
    3521140 3521530  89 xhpl</br>
    3521140 3521531  90 xhpl</br>
    3521140 3521532   9 xhpl</br>
    3521140 3521533  92 xhpl</br>
    3521140 3521534  93 xhpl</br>
    3521140 3521535  94 xhpl</br>
    3521140 3521536  95 xhpl</br>
    3521140 3521540   0 xhpl</br>
</details>


#### Question: Which BLAS library is linked into your HPL?
This is a tricky one to ask, because some vendor HPL builds internally spawn threaded `MKL DGEMM` kernels even when `OMP_NUM_THREADS=1`, while other do not. This determines whether it's using 4 cores or all allocated 92 cores.

```bash
# Check which BLAS library is linked.
ldd ./xhpl | egrep "mkl|openblas|blis"
```

---

## HPL-CPU: Understanding Theoretical HPL Performance on an Intel Xeon Platinum 8568Y+ Node

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

### 2. Important CPU Concepts

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

### 3. Calculations

**3.1. FLOPs Produced by One AVX-512 FMA:**</br>
One AVX-512 register contains: 8 FP64 values.</br>
Each FMA performs: 8 multiplications + 8 additions = 16 FLOPs

Therefore: 1 AVX-512 FMA instruction = 16 FP64 FLOPs


**3.2. Why Do We Multiply by 2 Again?**</br>
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

**3.3. Deriving FLOPs per Cycle per Core:**</br>
1.  **512-bit register** contains **8 FP64 values**.
2.  **FMA** produces: 8 × 2 = **16 FLOPs**
3.  **2 FMA units** produce **16 × 2 = 32 FLOPs**
4.  Final result: **32 FLOPs/cycle/core**

### 4. Theoretical Peak Performance Formula
**4.1. Formula:**</br>
The standard HPL theoretical peak formula is:

```text
Rpeak =
(Number of Cores)
×
(Frequency)
×
(FLOPs per Cycle per Core)
```

**4.2. Applying the Formula**</br>
1. Total FLOPs per Cycle: 96 cores × 32 FLOPs/cycle/core = 3072 FLOPs/cycle
2. Total FLOPs per Second: 3072 × 2.301 × 10^9 = 7.068672 × 10^12 FLOPs/sec
3. Convert to TFLOPS: 7.068672 × 10^12 = 7.07 TFLOPS
4. Therefore: Rpeak ≈ 7.07 TFLOPS

**4.3. Adjusting for Slurm Allocation:**</br>
The benchmark job saw: 94 CPUs instead of: 96 CPUs</br>
Corrected theoretical peak: 94 × 32 × 2.301 GHz = 6.92 TFLOPS

**4.4. Comparing Against Actual HPL Result:**</br>
Measured result: 5590.64 GFLOPS = 5.59 TFLOPS

**4.5. Efficiency vs Full Node Peak:**</br>

```text
Efficiency =
5.59 / 7.07
=
79.1%
```

**4.6. Efficiency vs Allocated 94-Core Peak:**</br>
Efficiency = 5.59 / 6.92 = 80.8%

**4.7. Why Actual Performance Is Lower Than Theoretical:**</br>
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

### 5. AVX Frequency Caveat
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

### 6. Quick Reference Summary

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

### 7. Key Takeaways
1. HPL theoretical peak depends primarily on:
   - Number of cores
   - SIMD width
   - Number of FMA units
   - Sustained frequency
2. AVX-512 allows one instruction to operate on eight FP64 values simultaneously.
3. FMA doubles throughput by performing a multiply and add in a single instruction.
4. The Xeon Platinum 8568Y+ can theoretically produce: 32 FP64 FLOPs/cycle/core
5. A measured HPL result of 5.59 TFLOPS on this node is consistent with a well-tuned CPU-only benchmark run.

---

## HPL-GPU

### 1. How CPU core count affects HPL-GPU performance
This is a different story than CPU-only HPL, because in the GPU variant, the GPU does essentially all of the DGEMM trailing-matrix-update FLOPs — that's >95% of the compute. The CPU's role shrinks down to three things:

1. Panel factorization — the LU decomposition of the current panel is done on the host CPU (via threaded BLAS), while the GPU works on the previous panel's trailing update. NVIDIA's hpl.sh pipelines this ("lookahead") so panel factorization on the CPU overlaps with GPU compute — it's not purely serial.
2. Data staging/PCIe-NVLink transfer prep — packing/unpacking buffers before handing them to the GPU.
3. MPI communication and progress threads — broadcasting panels between ranks.

Because of that overlap, HPL-GPU is much less core-hungry than CPU HPL. The practical effect of core count:

- Too few cores → panel factorization can't keep pace with the GPU's trailing-matrix update, so the GPU starts stalling waiting for the next panel. This shows up as lower GPU utilization, not a clean linear slowdown.
- Enough cores → panel factorization finishes comfortably inside the lookahead window, GPU stays fed, and adding more cores beyond that point gives diminishing to zero returns since the GPU, not the CPU, is the bound resource.
- Where that "enough" threshold sits depends on problem size (N) and block size (NB) — larger N per rank means a bigger panel to factor each step, needing more host threads to hide it under the same GPU compute window.
