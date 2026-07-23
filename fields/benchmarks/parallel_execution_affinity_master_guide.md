# Parallel Execution & Affinity Master Guide
> **Objective:** Master topology-aware execution, process-to-core mapping, NUMA boundary alignment, and launcher behavior across SLURM, OpenMPI, and MPICH.

## Table of Contents
- [Parallel Execution \& Affinity Master Guide](#parallel-execution--affinity-master-guide)
  - [Table of Contents](#table-of-contents)
  - [1. Executive Mental Model](#1-executive-mental-model)
    - [The Fundamental Sizing Formulas](#the-fundamental-sizing-formulas)
  - [2. Low-Level Execution Mechanics](#2-low-level-execution-mechanics)
    - [Process vs. Thread Memory Boundaries](#process-vs-thread-memory-boundaries)
  - [3. Launcher Deep Dive: srun vs. mpirun](#3-launcher-deep-dive-srun-vs-mpirun)
    - [Feature Comparison Matrix](#feature-comparison-matrix)
    - [Interoperability Architecture](#interoperability-architecture)
    - [OpenMPI Integration Patterns](#openmpi-integration-patterns)
    - [MPICH / Intel MPI Integration Patterns](#mpich--intel-mpi-integration-patterns)
  - [4. Hardware Topology \& NUMA Architecture](#4-hardware-topology--numa-architecture)
    - [Key Rules for NUMA Performance](#key-rules-for-numa-performance)
  - [5. CPU Binding \& Affinity](#5-cpu-binding--affinity)
    - [SLURM Core Binding Strategies](#slurm-core-binding-strategies)
      - [SLURM controls binding via --cpu-bind](#slurm-controls-binding-via---cpu-bind)
      - [OpenMPI Binding Constructs (--map-by \& --bind-to)](#openmpi-binding-constructs---map-by----bind-to)
    - [OpenMP Thread Pinning Environment Variables](#openmp-thread-pinning-environment-variables)
  - [6. GPU Topology \& Multi-GPU Mapping](#6-gpu-topology--multi-gpu-mapping)
    - [Rule of Thumb](#rule-of-thumb)
    - [Wrapper Script for Explicit GPU/CPU Pinning](#wrapper-script-for-explicit-gpucpu-pinning)
  - [7. Benchmarking \& High-Sensitivity Workloads (e.g., HPL)](#7-benchmarking--high-sensitivity-workloads-eg-hpl)
    - [Disabling SLURM Binding Override for Custom Affinity Wrappers](#disabling-slurm-binding-override-for-custom-affinity-wrappers)
    - [Hardware Optimization Checklist for Benchmarking](#hardware-optimization-checklist-for-benchmarking)
  - [8. Verification \& Debugging Toolkit](#8-verification--debugging-toolkit)
    - [Command Line Topology Tools](#command-line-topology-tools)
    - [In-Situ Placement Verification](#in-situ-placement-verification)
  - [9. Master Decision Matrix \& Templates](#9-master-decision-matrix--templates)
    - [Topology Blueprint Selection](#topology-blueprint-selection)
    - [Ready-to-Use Execution TemplatesTemplate](#ready-to-use-execution-templatestemplate)
      - [A: Pure OpenMP (Single Node High Memory)Bash#!/bin/bash](#a-pure-openmp-single-node-high-memorybashbinbash)
      - [Template B: Flat MPI (Massively Parallel Scaling)Bash#!/bin/bash](#template-b-flat-mpi-massively-parallel-scalingbashbinbash)
      - [Template D: HGX Multi-GPU Scaled Node RunBash#!/bin/bash](#template-d-hgx-multi-gpu-scaled-node-runbashbinbash)

---
## 1. Executive Mental Model
To master HPC execution, isolate the four distinct abstraction layers. Performance degradation or runtime failure almost always stems from misalignments between these layers:

```
+-------------------------------------------------------------------------+
| Layer 1: SLURM (Resource Allocator)                                     |
| Maps cgroups, steps, and requested slots across nodes                   |
+-------------------------------------------------------------------------+
|
v
+-------------------------------------------------------------------------+
| Layer 2: Launcher Engine (srun vs mpirun / mpiexec)               |
| Spawns task structures, bootstraps PMI/PMIx, initializes transport      |
+-------------------------------------------------------------------------+
|
v
+-------------------------------------------------------------------------+
| Layer 3: Application Runtime (MPI Ranks + OpenMP Threads)               |
| Allocates memory spaces, spawns pthreads (OMP_NUM_THREADS)            |
+-------------------------------------------------------------------------+
|
v
+-------------------------------------------------------------------------+
| Layer 4: Linux OS Kernel & Hardware Topology (NUMA / Cores / GPUs)      |
| Enforces sched_setaffinity(), memory allocation (mbind), PCIe/NVLink    |
+-------------------------------------------------------------------------+
```

### The Fundamental Sizing Formulas

$$\text{Total Cores Allocated} = \text{Nodes} \times \text{Tasks per Node} \times \text{CPUs per Task}$$

$$\text{Total MPI Ranks} = \text{Nodes} \times \text{Tasks per Node}$$

$$\text{Active Workers per Node} = \text{Tasks per Node} \times \text{OMP\_NUM\_THREADS}$$

> [!CRITICAL]
> In high-performance computing, **1 CPU in SLURM does not equal 1 Physical Core** by default if Simultaneous Multithreading (SMT/Hyperthreading) is active. Always explicitly manage SMT.


## 2. Low-Level Execution Mechanics

### Process vs. Thread Memory Boundaries
* **MPI Rank:** An independent OS process with its own Virtual Address Space (VAS), page tables, and file descriptors. Communication requires IPC (shared memory `/dev/shm` or `vmsplice`) within a node, or network fabrics (InfiniBand/RoCE via UCX/Libfabrics) across nodes.
* **OpenMP Thread:** A POSIX thread (`pthread`) spawned inside an MPI rank's VAS. All threads share heap, global variables, and open file descriptors, but maintain independent call stacks (`OMP_STACKSIZE`).

```
+-------------------------------------------------------------------------+
| Physical Dual-Socket Node (e.g., 2x 48-Core CPUs = 96 Cores total)      |
|                                                                         |
|  +---------------------------------+   +-----------------------------+  |
|  | Socket 0 (NUMA 0,1)             |   | Socket 1 (NUMA 2,3)         |  |
|  |  +---------------------------+  |   |  +-----------------------+  |  |
|  |  | MPI Rank 0 (Process)      |  |   |  | MPI Rank 1 (Process)  |  |  |
|  |  |  - Private Heap / Memory  |  |   |  |  - Private Heap       |  |  |
|  |  |  - Thread 0 (Core 0)      |  |   |  |  - Thread 0 (Core 24) |  |  |
|  |  |  - Thread 1 (Core 1)      |  |   |  |  - Thread 1 (Core 25) |  |  |
|  |  |  - ...                    |  |   |  |  - ...                |  |  |
|  |  |  - Thread 23 (Core 23)    |  |   |  |  - Thread 23 (Core 47)|  |  |
|  |  +---------------------------+  |   |  +-----------------------+  |  |
|  +---------------------------------+   +-----------------------------+  |
|                                                                         |
| Memory Interconnect: UPI / xGMI                                         |
+-------------------------------------------------------------------------+
```

---
## 3. Launcher Deep Dive: srun vs. mpirun

### Feature Comparison Matrix

| Feature | `srun` (SLURM Native) | `mpirun` / `mpiexec` (MPI Native) |
| :--- | :--- | :--- |
| **Bootstrapping** | Direct via `slurmstepd` daemons | SSH/rsh or SLURM PMI/PMIx plugin |
| **Affinity Enforcement** | Direct cgroup / `sched_setaffinity` control | MPI runtime internal binding engine |
| **Accounting & Metrics** | Tracked natively per-task in `sacct` | Tracked as a single monolithic process |
| **Heterogeneous Jobs** | Native support via hetjob syntax | Complex command-line syntax |
| **MPI Interoperability** | Requires PMI2 or PMIx compiled into MPI | Native to specific MPI implementation |

### Interoperability Architecture

When executing MPI code, the binary relies on Process Management Interface (PMI) to exchange wireup details (e.g., InfiniBand LID/LPN, rank index, host list).
```
srun  --->  PMIx / PMI2 Plugin  --->  libpmix.so  --->  MPI_Init()
```

### OpenMPI Integration Patterns
```bash
# 1. Recommended: Native SLURM orchestration via PMIx
srun --mpi=pmix ./mpi_app

# 2. Hybrid: mpirun leveraging SLURM allocations (spawns tasks via srun internally)
mpirun --mca pml ucx --mca btl ^openib ./mpi_app
```

### MPICH / Intel MPI Integration Patterns
```bash
# 1. Intel MPI using SLURM's PMI2 interface
export I_MPI_PMI_LIBRARY=/usr/lib64/libpmi2.so
srun --mpi=pmi2 ./intel_app

# 2. Intel MPI Hydra native engine passing through SLURM environment
mpiexec -bootstrap slurm -n $SLURM_NTASKS ./intel_app
```

> [!WARNING]
> Avoid the Dual-Binding Trap: If using mpirun inside an sbatch allocation, do NOT pass aggressive CPU binding flags to both SLURM (--cpu-bind) and mpirun (--bind-to core). They can fight over bitmasks, pinning all MPI ranks to CPU Core 0.

--- 
## 4. Hardware Topology & NUMA Architecture

Modern server CPUs (AMD EPYC Zen 4/5, Intel Xeon Emerald/Granite Rapids) are built using Chiplet Architecture (NPS / NUMA Per Socket modes).

```
+--------------------------------------------------------------------------+
| NUMA Node 0                                                              |
|  +-------------------+  +-------------------+  +----------------------+  |
|  | L3 Cache Domain 0 |  | L3 Cache Domain 1 |  | Local DDR5 Controller|  |
|  | [Core 0-5]        |  | [Core 6-11]       |  | Memory Bus           |  |
|  +-------------------+  +-------------------+  +----------------------+  |
+--------------------------------------------------------------------------+
                                     ^
                                     | Inter-NUMA Bus (Latency Penalty: 1.5x - 2.5x)
                                     v
+--------------------------------------------------------------------------+
| NUMA Node 1                                                              |
|  +-------------------+  +-------------------+  +----------------------+  |
|  | L3 Cache Domain 2 |  | L3 Cache Domain 3 |  | Local DDR5 Controller|  |
|  | [Core 12-17]      |  | [Core 18-23]      |  | Memory Bus           |  |
|  +-------------------+  +-------------------+  +----------------------+  |
+--------------------------------------------------------------------------+
```

### Key Rules for NUMA Performance
1. Never allow an MPI rank or OpenMP thread pool to cross a NUMA boundary unless memory footprint strictly requires it.
2. First-Touch Memory Policy: The Linux kernel allocates physical memory pages on the NUMA domain of the CPU thread that writes to it first. Initialize data arrays using the exact same OpenMP loop structure as the computational loop.
3. Sub-NUMA Clustering (SNC / NPS4): A single physical CPU socket can present as 4 distinct NUMA nodes to the OS. Tune MPI rank counts to match the number of NUMA domains or L3 cache clusters.

## 5. CPU Binding & Affinity
### SLURM Core Binding Strategies

#### SLURM controls binding via --cpu-bind

```Bash
# Bind each MPI rank strictly to assigned physical cores
srun --cpu-bind=cores ./app

# Bind ranks to NUMA domains (ideal for OpenMP applications spanning a NUMA node)
srun --cpu-bind=sockets ./app

# Print detailed core masking at launch for verification
srun --cpu-bind=verbose,cores ./app
```

#### OpenMPI Binding Constructs (--map-by & --bind-to)

OpenMPI uses a two-stage binding paradigm: **Mapping** (assigning ranks to hardware units) and Binding (constraining execution via system calls)
```Bash
# Map ranks sequentially across NUMA nodes, bind each rank to a physical core
mpirun --map-by numa --bind-to core ./app

# Map 4 ranks per node, allocating 16 processing elements (PE) each for OpenMP
mpirun --map-by ppr:4:node:PE=16 --bind-to core ./app
```

### OpenMP Thread Pinning Environment Variables
Always explicitly define runtime behavior for OpenMP. Do not rely on compiler defaults.

```Bash
# Standard OpenMP Configuration
export OMP_NUM_THREADS=16
export OMP_PROC_BIND=spread    # Spreads threads evenly across available cores
export OMP_PLACES=cores        # Pins each thread to a physical core (ignoring hyperthreads)

# Alternative for Dense Locality
export OMP_PROC_BIND=close     # Packs threads closely to share L3 cache
```

## 6. GPU Topology & Multi-GPU Mapping
In heterogeneous clusters (e.g., NVIDIA HGX H100 / Grace Hopper), CPU-to-GPU PCIe/NVLink mapping determines throughput.
```
+---------------------------------------------------------------------+
| Dual-Socket System GPU Topology                                     |
|                                                                     |
|  [Socket 0 / NUMA 0] <== PCIe / C2C ==> [GPU 0] <--- NVLink ---> [GPU 1]
|            |                                                        |
|      UPI / xGMI Link (High Latency cross-talk penalty)              |
|            v                                                        |
|  [Socket 1 / NUMA 1] <== PCIe / C2C ==> [GPU 2] <--- NVLink ---> [GPU 3]
+---------------------------------------------------------------------+
```

### Rule of Thumb
Bind the MPI Rank controlling GPU $N$ to the exact CPU NUMA Domain local to GPU $N$'s PCIe Root Complex.1 GPU per MPI Rank Configuration

```Bash
#!/bin/bash
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:4
#SBATCH --gpu-bind=closest     # SLURM automatically maps task to closest GPU

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OMP_PLACES=cores
export OMP_PROC_BIND=spread

srun --cpu-bind=cores ./gpu_app
```

### Wrapper Script for Explicit GPU/CPU Pinning
When system topology relies on non-standard device indices or driver mappings:

```Bash
#!/bin/bash
# select_gpu.sh: Custom binding wrapper

# Calculate local rank ID inside the node
LOCAL_RANK=${SLURM_LOCALID:-${OMPI_COMM_WORLD_LOCAL_RANK}}

# Map local rank directly to GPU ID
export CUDA_VISIBLE_DEVICES=${LOCAL_RANK}

# Execute target workload
exec "$@"
```

Execution Call:
```Bash
srun --ntasks-per-node=4 --cpus-per-task=16 ./select_gpu.sh ./gpu_app
```

## 7. Benchmarking & High-Sensitivity Workloads (e.g., HPL)
Workloads like High-Performance Linpack (HPL), Quantum Chemistry, or NCCL Tests require disabling OS noise and locking hardware state.

### Disabling SLURM Binding Override for Custom Affinity Wrappers
When deploying vendor-optimized launchers (such as NVIDIA's HPL container wrappers), standard SLURM binding can conflict with internal `numactl` or `hwloc` scripts.

```Bash
# Pass --cpu-bind=none to allow full process affinity manipulation inside container
srun --cpu-bind=none --accel-bind=g ./hpl_wrapper.sh
```

### Hardware Optimization Checklist for Benchmarking
1. Disable CPU SMT / Hyperthreading via job submission:
   ```Bash
   #SBATCH --hint=nomultithread
   ```

2. Lock CPU & GPU Frequencies: Ensure nodes are configured in High-Performance mode (via IPMI/Slurm **slurm.conf** node features).
3. Set Memory Allocator: Inject jemalloc or tcmalloc to optimize concurrent thread allocations:
   ```Bash
   export LD_PRELOAD=/usr/lib64/libjemalloc.so.2
   ```

## 8. Verification & Debugging Toolkit
Never assume affinity settings are correct. Use low-overhead inspection tools to verify placement before executing production runs.

### Command Line Topology Tools
```Bash
# Display NUMA domains and processing elements
numactl --hardware

# View graphical CPU/PCIe/GPU hardware topology map
lstopo --of ascii

# Interrogate GPU-to-CPU affinity maps
nvidia-smi topo -m
```

### In-Situ Placement Verification
1. Verbose Launcher Inspection

   ```Bash
   # Check SLURM affinity masks
   srun --cpu-bind=verbose,cores hostname

   # Check OpenMPI affinity masks
   mpirun --report-bindings -np 4 ./app
   ```

2. C-Language Affinity Printing Routine: Embed this snippet into codebases to output exact runtime CPU execution IDs:

   ```C
   #define _GNU_SOURCE
   #include <sched.h>
   #include <stdio.h>
   #include <unistd.h>
   #include <mpi.h>

   void print_affinity() {
      int rank;
      MPI_Comm_rank(MPI_COMM_WORLD, &rank);
      int cpu = sched_getcpu();
      
      cpu_set_t mask;
      CPU_ZERO(&mask);
      sched_getaffinity(0, sizeof(cpu_set_t), &mask);

      printf("MPI Rank %03d | Running on CPU %03d | Mask Core Count: %d\n", 
            rank, cpu, CPU_COUNT(&mask));
   }
   ```

## 9. Master Decision Matrix & Templates

### Topology Blueprint Selection
```
                        [ Target Application Architecture ]
                                        |
                 +----------------------+----------------------+
                 |                                             |
        [ Shared Memory Only ]                      [ Distributed Memory ]
                 |                                             |
         Use OpenMP / pthreads                      Determine GPU Usage
          - Ranks: 1                                           |
          - OMP_NUM_THREADS = All Cores            +-----------+-----------+
                                                   |                       |
                                             [ Pure CPU ]            [ GPU Accelerated ]
                                                   |                       |
                                            Check NUMA Bounds        Set Ranks = GPUs
                                                   |                       |
                                           +-------+-------+       - 1 Rank per GPU
                                           |               |       - CPUs/Task = Host Cores/GPU
                                       [ Flat MPI ]   [ Hybrid ]   - Use --gpu-bind=closest
                                       (1 Rank/Core)  (MPI+OMP)
```

### Ready-to-Use Execution TemplatesTemplate 

#### A: Pure OpenMP (Single Node High Memory)Bash#!/bin/bash

```sh
#SBATCH --job-name=openmp_single
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --time=02:00:00

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OMP_PLACES=cores
export OMP_PROC_BIND=spread

srun --cpu-bind=cores ./openmp_dense_app
```

#### Template B: Flat MPI (Massively Parallel Scaling)Bash#!/bin/bash

```sh
#SBATCH --job-name=flat_mpi
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=128
#SBATCH --cpus-per-task=1
#SBATCH --time=04:00:00

export OMP_NUM_THREADS=1

srun --mpi=pmix --cpu-bind=ranks ./mpi_pure_app
Template C: Hybrid MPI + OpenMP (NUMA-Aligned)Bash#!/bin/bash
#SBATCH --job-name=hybrid_mpi_omp
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=4       # 4 Ranks per node (1 per NUMA domain)
#SBATCH --cpus-per-task=32        # 32 Cores per rank
#SBATCH --time=12:00:00

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OMP_PLACES=cores
export OMP_PROC_BIND=close        # Keeps threads within local NUMA L3 cache

srun --mpi=pmix --cpu-bind=cores ./hybrid_app
```

#### Template D: HGX Multi-GPU Scaled Node RunBash#!/bin/bash

```sh
#SBATCH --job-name=hgx_h100_cluster
#SBATCH --nodes=8
#SBATCH --ntasks-per-node=8       # 8 Ranks per node = 8 GPUs per node
#SBATCH --cpus-per-task=12        # Balanced CPU allocation per GPU
#SBATCH --gres=gpu:8
#SBATCH --gpu-bind=closest

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OMP_PLACES=cores
export OMP_PROC_BIND=spread

# UCX Infiniband Optimizations
export UCX_NET_DEVICES=mlx5_0:1,mlx5_1:1,mlx5_2:1,mlx5_3:1
export NCCL_DEBUG=INFO

srun --mpi=pmix --cpu-bind=cores ./gpu_distributed_app
```
