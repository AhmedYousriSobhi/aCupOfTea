---
id: openmp-mpi-threads-and-ranks
title: "Cooks and Kitchens: Threads, Ranks and the One Mental Model"
order: 3
sidebar_label: "3. Threads and ranks"
summary: Run one tiny program of each kind and watch the difference - OpenMP threads sharing one memory (and a data race), MPI ranks with separate memory (and a reduction) - on a real 4-core machine.
level: beginner
type: concept
domains: [systems-and-hpc, software-engineering]
tags: [openmp, mpi, hpc]
relations:
  prerequisites: [openmp-open-mpi-name-mixup]
---

# Cooks and Kitchens: Threads, Ranks and the One Mental Model

> Part 3 of 6. By the end you'll know what a **thread** and a **rank** are, you'll have seen both run, and you'll understand the one bug each style invites.

## Contents

- [The mental model in two sentences](#the-mental-model-in-two-sentences)
- [OpenMP: one process, many threads](#openmp-one-process-many-threads)
- [The bug OpenMP invites: a data race](#the-bug-openmp-invites-a-data-race)
- [MPI: many processes, many ranks](#mpi-many-processes-many-ranks)
- [The bug MPI invites: not enough slots, and waiting forever](#the-bug-mpi-invites-not-enough-slots-and-waiting-forever)
- [Side by side](#side-by-side)

---

## The mental model in two sentences

An OpenMP program is **one process** that, at marked spots, splits into a team of **threads** which all see the same memory, then joins back into one. An MPI program is **a team of separate processes**, called **ranks**, started together, each with its own private memory, which cooperate only by sending messages.

Everything else in both worlds is detail on top of that.

> [!NOTE]
> Written against Ubuntu 26.04.1 (Linux 7.0), gcc 15.2.0 and Open MPI 5.0.10, run in a throwaway 4-CPU VM. Output order and exact numbers will differ on your machine. That is the point of parallel code: nothing promises the order.

---

## OpenMP: one process, many threads

```c
#include <omp.h>
#include <stdio.h>
int main(void) {
    #pragma omp parallel
    {
        #pragma omp critical
        printf("hello from thread %d of %d\n", omp_get_thread_num(), omp_get_num_threads());
    }
    return 0;
}
```

`#pragma omp parallel` is the whole trick: the next block runs once **per thread**. `critical` lets only one thread print at a time so lines don't get mixed up.

```bash
gcc -O2 -Wall -fopenmp omp_hello.c -o omp_hello
OMP_NUM_THREADS=4 ./omp_hello
```

```text
hello from thread 0 of 4
hello from thread 2 of 4
hello from thread 3 of 4
hello from thread 1 of 4
```

Two knobs to remember:

- **`-fopenmp`** tells gcc to honour the pragmas. Other compilers have their own spelling.
- **`OMP_NUM_THREADS`** sets the team size. Unset, it printed 4 lines on this 4-CPU VM, but the standard leaves the default to the implementation, so set it yourself.

> [!WARNING]
> Forget `-fopenmp` and the pragmas are **silently ignored**. A program with only pragmas builds clean (gcc warns only with `-Wall`) and runs on one thread. I tested a four-thread `printf` region: with the flag it printed 4 lines, without it, 1. If your OpenMP program is mysteriously slow, check the flag first.

---

## The bug OpenMP invites: a data race

Threads share memory, so two threads can touch the same variable at once. Count to 100 million with four threads, the wrong way and the right way:

```c
long racy = 0, safe = 0;
#pragma omp parallel for
for (long i = 0; i < N; i++) racy += 1;           /* all threads write one variable */
#pragma omp parallel for reduction(+:safe)
for (long i = 0; i < N; i++) safe += 1;           /* each thread keeps its own copy, summed at the end */
```

Three runs, four threads, expected 100000000 every time (the program prints the three lines `expected`, `racy`, `reduction`; condensed here):

```text
racy      75000000      reduction 100000000
racy     100000000      reduction 100000000
racy      75000000      reduction 100000000
```

The racy total was wrong in two runs out of three, and right in the third by luck. I did not dig into why it landed on those exact numbers. The lesson stands: **a race gives wrong answers that change from run to run**, so a pass proves nothing. `reduction(+:var)` is the standard fix for "everyone adds to one total".

---

## MPI: many processes, many ranks

```c
#include <mpi.h>
#include <stdio.h>
int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, size, len; char host[MPI_MAX_PROCESSOR_NAME];
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Get_processor_name(host, &len);
    int sum = 0;
    MPI_Reduce(&rank, &sum, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
    printf("rank %d of %d on %s\n", rank, size, host);
    if (rank == 0) printf("sum of ranks = %d\n", sum);
    MPI_Finalize();
    return 0;
}
```

- `MPI_COMM_WORLD` is "everyone who was started together".
- `MPI_Get_processor_name` just reports which machine the rank runs on (here the VM is called `twins`).
- `rank` is your number in that group (0 to size-1); `size` is how many there are.
- `MPI_Reduce` is a **collective**: every rank calls it, and rank 0 receives the sum of everyone's value.

```bash
mpicc -O2 -Wall mpi_hello.c -o mpi_hello
mpirun -np 4 ./mpi_hello
```

```text
rank 3 of 4 on twins
rank 2 of 4 on twins
rank 1 of 4 on twins
rank 0 of 4 on twins
sum of ranks = 6
```

0 + 1 + 2 + 3 = 6. Four separate processes each held one number in private memory, and the library moved them together. No rank could simply read another's `rank` variable. That is the "separate kitchens" rule.

---

## The bug MPI invites: not enough slots, and waiting forever

Ask for more ranks than the machine has slots and Open MPI refuses to start (exit code 1):

```bash
mpirun -np 8 ./mpi_hello     # on a 4-CPU VM: refused
mpirun --oversubscribe -np 8 ./mpi_hello    # allowed, exit 0
```

`--oversubscribe` means "yes, I know there are only 4 slots". Use it for testing, not for speed.

> [!WARNING]
> On this Ubuntu 26.04 install, the refusal message is hidden behind `Sorry!  You were supposed to get help about: prte-rmaps-base:alloc-error` plus "couldn't open the help file". The packages looked for the help text under `/usr/lib/x86_64-linux-gnu/prrte3/share/prte/`, and I found one such file only under `/usr/share/doc/libprrte-dev/`. On such a system, `alloc-error` means "not enough slots". The same missing file also breaks `mpirun --version`; `ompi_info --version` works.

The other classic MPI bug I did not run here, because it hangs by design: a **deadlock**, where two ranks each wait for a message the other has not sent. It is the mirror of the data race: instead of a wrong answer, you get no answer.

---

## Side by side

| | OpenMP threads | MPI ranks |
|---|----------------|-----------|
| What runs in parallel | Threads inside one process | Separate processes |
| Memory | Shared | Private to each rank |
| How they cooperate | By reading and writing shared variables | By calling library functions to send and receive |
| How you start it | `./prog` (set `OMP_NUM_THREADS`) | `mpirun -np N ./prog` |
| How you build it | `gcc -fopenmp` | `mpicc` (a gcc wrapper) |
| Reach | One machine | One machine or many |
| Signature bug | Data race: wrong, changing answers | Deadlock or too few slots: no answer |

**Takeaway:** a thread shares memory and needs care about who writes what; a rank owns its memory and needs messages to cooperate.

Next: [Spotting OpenMP and MPI code](/fields/system-administration/openmp-and-open-mpi/spotting-openmp-and-mpi-code.md), part 4: what to look for the moment you open someone's source or job script.

---

## References

- [OpenMP API specification: parallel construct, reduction clause, OMP_NUM_THREADS](https://www.openmp.org/specifications/)
- [MPI standard (MPI Forum): MPI_Init, communicators, MPI_Reduce](https://www.mpi-forum.org/docs/)
- [Open MPI mpirun manual (v5.0.x)](https://docs.open-mpi.org/en/v5.0.x/man-openmpi/man1/mpirun.1.html): slots and `--oversubscribe`
- Every output block on this page: run on Ubuntu 26.04.1, Linux 7.0, gcc 15.2.0, Open MPI 5.0.10, 4 vCPUs.
