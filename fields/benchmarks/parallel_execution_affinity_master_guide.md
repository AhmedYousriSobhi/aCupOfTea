# Parallel Execution & Affinity: The Layer Cake Nobody Draws Correctly

> **Objective:** master topology-aware execution, process-to-core mapping, NUMA boundary alignment, and launcher behavior across SLURM, OpenMPI, and MPICH — because 90% of "mysterious" HPC performance problems are actually a misalignment between these layers, not a hardware fault.

## Table of Contents
- [1. The mental model](#1-the-mental-model)
- [2. Process vs. thread — know your boundaries](#2-process-vs-thread--know-your-boundaries)
- [3. `srun` vs. `mpirun`: pick a lane](#3-srun-vs-mpirun-pick-a-lane)
- [4. NUMA architecture, in one picture](#4-numa-architecture-in-one-picture)
- [5. CPU binding & affinity syntax](#5-cpu-binding--affinity-syntax)
- [6. GPU topology & multi-GPU mapping](#6-gpu-topology--multi-gpu-mapping)
- [7. Benchmarking-grade tuning (HPL, NCCL, etc.)](#7-benchmarking-grade-tuning-hpl-nccl-etc)
- [8. Verify, don't assume](#8-verify-dont-assume)
- [9. Decision matrix & copy-paste templates](#9-decision-matrix--copy-paste-templates)

---

## 1. The mental model

Every "why is my job slow / crashing / underutilizing the node" question traces back to one of four layers. Performance problems are almost always a **misalignment between adjacent layers**, not a broken layer in isolation:

```
┌───────────────────────────────────────────────────────────────────────┐
│ Layer 1 — SLURM (Resource Allocator)                                  │
│ Maps cgroups, steps, and requested slots across nodes                 │
└───────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Layer 2 — Launcher Engine (srun vs. mpirun / mpiexec)                 │
│ Spawns task structures, bootstraps PMI/PMIx, initializes transport    │
└───────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Layer 3 — Application Runtime (MPI Ranks + OpenMP Threads)            │
│ Allocates memory, spawns pthreads per OMP_NUM_THREADS                 │
└───────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Layer 4 — Linux Kernel & Hardware Topology (NUMA / Cores / GPUs)      │
│ Enforces sched_setaffinity(), mbind(), PCIe/NVLink routing            │
└───────────────────────────────────────────────────────────────────────┘
```

### The three formulas that decide everything

$$\text{Total Cores Allocated} = \text{Nodes} \times \text{Tasks per Node} \times \text{CPUs per Task}$$

$$\text{Total MPI Ranks} = \text{Nodes} \times \text{Tasks per Node}$$

$$\text{Active Workers per Node} = \text{Tasks per Node} \times \text{OMP\_NUM\_THREADS}$$

> [!CAUTION]
> **1 SLURM "CPU" ≠ 1 physical core**, if Simultaneous Multithreading (SMT/Hyperthreading) is active. Always explicitly manage SMT — never assume.

---

## 2. Process vs. thread — know your boundaries

- **MPI Rank** = an independent OS process with its own virtual address space, page tables, and file descriptors. Talks to other ranks via shared memory (`/dev/shm`, `vmsplice`) within a node, or network fabrics (InfiniBand/RoCE via UCX/libfabric) across nodes.
- **OpenMP Thread** = a `pthread` living *inside* an MPI rank's address space. All threads in a rank share heap, globals, and file descriptors — but each keeps its own call stack (`OMP_STACKSIZE`).

```
┌─────────────────────────────────────────────────────────────────────┐
│ Physical Dual-Socket Node (e.g., 2× 48-Core CPUs = 96 Cores total)   │
│                                                                       │
│  ┌───────────────────────────┐   ┌───────────────────────────┐      │
│  │ Socket 0 (NUMA 0,1)       │   │ Socket 1 (NUMA 2,3)        │      │
│  │  ┌─────────────────────┐  │   │  ┌─────────────────────┐   │      │
│  │  │ MPI Rank 0 (Process) │  │   │  │ MPI Rank 1 (Process) │  │      │
│  │  │  Private Heap        │  │   │  │  Private Heap        │  │      │
│  │  │  Thread 0 → Core 0    │  │   │  │  Thread 0 → Core 24   │  │      │
│  │  │  Thread 1 → Core 1    │  │   │  │  Thread 1 → Core 25   │  │      │
│  │  │  ...                  │  │   │  │  ...                  │  │      │
│  │  │  Thread 23 → Core 23  │  │   │  │  Thread 23 → Core 47  │  │      │
│  │  └─────────────────────┘  │   │  └─────────────────────┘   │      │
│  └───────────────────────────┘   └───────────────────────────┘      │
│                    Memory Interconnect: UPI / xGMI                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. `srun` vs. `mpirun`: pick a lane

| Feature | `srun` (SLURM-native) | `mpirun` / `mpiexec` (MPI-native) |
|---|---|---|
| **Bootstrapping** | Direct via `slurmstepd` daemons | SSH/rsh, or SLURM's PMI/PMIx plugin |
| **Affinity enforcement** | Direct cgroup / `sched_setaffinity` control | MPI runtime's internal binding engine |
| **Accounting** | Native per-task tracking in `sacct` | Tracked as one monolithic process |
| **Heterogeneous jobs** | Native `hetjob` syntax | Complex command-line workarounds |
| **MPI interoperability** | Needs PMI2/PMIx compiled into MPI | Native to the specific MPI implementation |

**How they talk to MPI under the hood:**

```
srun → PMIx/PMI2 Plugin → libpmix.so → MPI_Init()
```

**OpenMPI patterns:**

```bash
# Recommended: native SLURM orchestration via PMIx
srun --mpi=pmix ./mpi_app

# Hybrid: mpirun leveraging a SLURM allocation
mpirun --mca pml ucx --mca btl ^openib ./mpi_app
```

**MPICH / Intel MPI patterns:**

```bash
# Intel MPI over SLURM's PMI2
export I_MPI_PMI_LIBRARY=/usr/lib64/libpmi2.so
srun --mpi=pmi2 ./intel_app

# Intel MPI Hydra engine, passed through SLURM's environment
mpiexec -bootstrap slurm -n $SLURM_NTASKS ./intel_app
```

> [!WARNING]
> **The Dual-Binding Trap.** If you use `mpirun` inside an `sbatch` allocation, do **not** pass aggressive binding flags to both SLURM (`--cpu-bind`) *and* `mpirun` (`--bind-to core`) at once. They can fight over bitmasks — the classic failure mode is every single MPI rank silently getting pinned to CPU core 0.

---

## 4. NUMA architecture, in one picture

Modern chiplet-based CPUs (AMD EPYC Zen 4/5, Intel Xeon Emerald/Granite Rapids) present multiple NUMA nodes per physical socket:

```
┌────────────────────────────────────────────────────────────────────┐
│ NUMA Node 0                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────────┐     │
│  │ L3 Cache Dom. 0 │  │ L3 Cache Dom. 1 │  │ Local DDR5        │     │
│  │ [Core 0-5]      │  │ [Core 6-11]     │  │ Memory Controller │     │
│  └────────────────┘  └────────────────┘  └───────────────────┘     │
└────────────────────────────────────────────────────────────────────┘
                                 ▲
                    Inter-NUMA Bus (1.5×–2.5× latency penalty)
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│ NUMA Node 1                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────────┐     │
│  │ L3 Cache Dom. 2 │  │ L3 Cache Dom. 3 │  │ Local DDR5        │     │
│  │ [Core 12-17]    │  │ [Core 18-23]    │  │ Memory Controller │     │
│  └────────────────┘  └────────────────┘  └───────────────────┘     │
└────────────────────────────────────────────────────────────────────┘
```

### The three rules that actually matter

1. **Never let an MPI rank or OpenMP thread pool cross a NUMA boundary** unless memory footprint genuinely forces it. Crossing costs you that 1.5–2.5× latency penalty on every access.
2. **First-touch memory policy** — Linux allocates a physical page on the NUMA domain of whichever CPU thread *writes to it first*. Initialize arrays using the exact same loop structure (same thread-to-index mapping) you'll use for the real computation, or you'll "first-touch" your data onto the wrong domain.
3. **Sub-NUMA Clustering (SNC/NPS4)** — a single physical socket can present as up to 4 separate NUMA nodes to the OS. Tune your MPI rank count to match the actual NUMA domain count, not the socket count.

---

## 5. CPU binding & affinity syntax

### SLURM (`--cpu-bind`)

```bash
# Bind each MPI rank strictly to assigned physical cores
srun --cpu-bind=cores ./app

# Bind ranks to NUMA domains (good for OpenMP apps spanning a NUMA node)
srun --cpu-bind=sockets ./app

# Print the actual core mask at launch — always do this once per new config
srun --cpu-bind=verbose,cores ./app
```

### OpenMPI (`--map-by` & `--bind-to`)

OpenMPI splits binding into two stages: **Mapping** (assign ranks to hardware units) and **Binding** (enforce it via syscalls).

```bash
# Map ranks sequentially across NUMA nodes, bind each to a physical core
mpirun --map-by numa --bind-to core ./app

# Map 4 ranks per node, 16 processing elements (PE) each, for OpenMP threads
mpirun --map-by ppr:4:node:PE=16 --bind-to core ./app
```

### OpenMP thread pinning — never trust the compiler defaults

```bash
# Standard configuration
export OMP_NUM_THREADS=16
export OMP_PROC_BIND=spread    # spread threads across available cores
export OMP_PLACES=cores        # pin each thread to a physical core (skip hyperthreads)

# Alternative — dense locality (share L3 cache)
export OMP_PROC_BIND=close     # pack threads tightly
```

---

## 6. GPU topology & multi-GPU mapping

On heterogeneous clusters (HGX H100/H200, Grace Hopper), CPU-to-GPU PCIe/NVLink mapping directly determines throughput:

```
┌──────────────────────────────────────────────────────────────────────┐
│ Dual-Socket System GPU Topology                                      │
│                                                                        │
│ [Socket 0/NUMA 0] ⇄ PCIe/C2C ⇄ [GPU 0] ⇄ NVLink ⇄ [GPU 1]             │
│           │                                                           │
│    UPI/xGMI Link (high-latency cross-talk penalty)                    │
│           ▼                                                           │
│ [Socket 1/NUMA 1] ⇄ PCIe/C2C ⇄ [GPU 2] ⇄ NVLink ⇄ [GPU 3]             │
└──────────────────────────────────────────────────────────────────────┘
```

### Rule of thumb

**Bind the MPI rank controlling GPU N to the exact CPU NUMA domain local to GPU N's PCIe root complex.**

```bash
#!/bin/bash
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:4
#SBATCH --gpu-bind=closest     # SLURM auto-maps each task to its nearest GPU

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OMP_PLACES=cores
export OMP_PROC_BIND=spread

srun --cpu-bind=cores ./gpu_app
```

### When SLURM's auto-mapping isn't enough — explicit wrapper script

For non-standard device indices or driver mappings:

```bash
#!/bin/bash
# select_gpu.sh — custom binding wrapper

LOCAL_RANK=${SLURM_LOCALID:-${OMPI_COMM_WORLD_LOCAL_RANK}}

# Map local rank directly to a GPU ID
export CUDA_VISIBLE_DEVICES=${LOCAL_RANK}

exec "$@"
```

```bash
srun --ntasks-per-node=4 --cpus-per-task=16 ./select_gpu.sh ./gpu_app
```

---

## 7. Benchmarking-grade tuning (HPL, NCCL, etc.)

Latency-sensitive workloads — HPL, quantum chemistry, NCCL tests — need OS noise disabled and hardware state locked down.

### Let vendor wrappers control their own affinity

Vendor-optimized launchers (like NVIDIA's HPL container wrapper) often run their own internal `numactl`/`hwloc` logic. Standard SLURM binding can fight with it:

```bash
# Pass --cpu-bind=none so the container's own affinity script has full control
srun --cpu-bind=none --accel-bind=g ./hpl_wrapper.sh
```

### Hardware optimization checklist

- [ ] **Disable SMT/Hyperthreading** at submission time: `#SBATCH --hint=nomultithread`
- [ ] **Lock CPU & GPU frequencies** — confirm nodes run in High-Performance mode (via IPMI or Slurm node features)
- [ ] **Swap in a faster allocator** for concurrent thread allocation:
  ```bash
  export LD_PRELOAD=/usr/lib64/libjemalloc.so.2
  ```

---

## 8. Verify, don't assume

Never trust that a binding flag "worked." Check it every time before a production run.

### Topology inspection tools

```bash
numactl --hardware          # NUMA domains and processing elements
lstopo --of ascii           # full CPU/PCIe/GPU topology map
nvidia-smi topo -m          # GPU-to-CPU affinity matrix
```

### In-situ placement verification

```bash
# SLURM affinity masks
srun --cpu-bind=verbose,cores hostname

# OpenMPI affinity masks
mpirun --report-bindings -np 4 ./app
```

For code-level verification, embed this directly in your application:

```c
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

---

## 9. Decision matrix & copy-paste templates

### Which topology blueprint do I even need?

```
                     [ Target Application Architecture ]
                                     │
              ┌──────────────────────┴──────────────────────┐
              │                                              │
    [ Shared Memory Only ]                         [ Distributed Memory ]
              │                                              │
      Use OpenMP/pthreads                          Determine GPU usage
       Ranks = 1                                             │
       OMP_NUM_THREADS = all cores          ┌──────────────────┴──────────────────┐
                                             │                                     │
                                       [ Pure CPU ]                     [ GPU Accelerated ]
                                             │                                     │
                                     Check NUMA bounds                   Set Ranks = GPUs
                                             │                            1 Rank per GPU
                                   ┌─────────┴─────────┐        CPUs/Task = Host Cores/GPU
                                   │                   │        Use --gpu-bind=closest
                             [ Flat MPI ]         [ Hybrid ]
                             (1 Rank/Core)        (MPI+OMP)
```

### Template A — Pure OpenMP (single node, high memory)

```bash
#!/bin/bash
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

### Template B — Flat MPI (massively parallel scaling)

```bash
#!/bin/bash
#SBATCH --job-name=flat_mpi
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=128
#SBATCH --cpus-per-task=1
#SBATCH --time=04:00:00

export OMP_NUM_THREADS=1

srun --mpi=pmix --cpu-bind=ranks ./mpi_pure_app
```

### Template C — Hybrid MPI + OpenMP (NUMA-aligned)

```bash
#!/bin/bash
#SBATCH --job-name=hybrid_mpi_omp
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=4       # 4 ranks per node = 1 per NUMA domain
#SBATCH --cpus-per-task=32        # 32 cores per rank
#SBATCH --time=12:00:00

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OMP_PLACES=cores
export OMP_PROC_BIND=close        # keep threads within local NUMA L3 cache

srun --mpi=pmix --cpu-bind=cores ./hybrid_app
```

### Template D — HGX multi-GPU scaled node run

```bash
#!/bin/bash
#SBATCH --job-name=hgx_h100_cluster
#SBATCH --nodes=8
#SBATCH --ntasks-per-node=8       # 8 ranks per node = 8 GPUs per node
#SBATCH --cpus-per-task=12        # balanced CPU allocation per GPU
#SBATCH --gres=gpu:8
#SBATCH --gpu-bind=closest

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OMP_PLACES=cores
export OMP_PROC_BIND=spread

# UCX InfiniBand optimizations
export UCX_NET_DEVICES=mlx5_0:1,mlx5_1:1,mlx5_2:1,mlx5_3:1
export NCCL_DEBUG=INFO

srun --mpi=pmix --cpu-bind=cores ./gpu_distributed_app
```

---

**Bottom line:** every one of these templates is really the same four-layer stack (SLURM → Launcher → Runtime → Hardware) configured to *agree with itself*. Whenever a job underperforms, walk the stack top to bottom before blaming the network or the silicon — the answer is usually a mismatch between two adjacent layers, not a fault in either one alone.