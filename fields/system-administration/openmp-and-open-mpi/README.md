
# OpenMP and Open MPI - Overview

> An eight-part series for anyone whose brain blue-screens when two names differ by one space. By the end you'll know what each name means, why they exist, how to spot their code at a glance, and how the two end up in the same job script, arguing over the same CPU, and who starts them on Slurm and Kubernetes.

The cast, so you can keep score: **OpenMP** is one kitchen with several chefs sharing a counter. **MPI** is the rulebook for kitchens that pass notes through a delivery window. **Open MPI** is one courier company that follows that rulebook. Nobody here is a twin. Several of them are, however, very good at stepping on each other's toes.

## The route

| # | Page | The question it answers |
|---|------|-------------------------|
| 1 | [Not twins, not even cousins](/fields/system-administration/openmp-and-open-mpi/the-name-mixup.md) | Are OpenMP and Open MPI twins? What is MPI, then? |
| 2 | [Where they came from](/fields/system-administration/openmp-and-open-mpi/where-they-came-from.md) | Why do two parallel standards exist, and who wrote each? |
| 3 | [Threads and ranks](/fields/system-administration/openmp-and-open-mpi/threads-and-ranks.md) | What does each style look like when it runs, and what bug does each invite? |
| 4 | [Spotting the code](/fields/system-administration/openmp-and-open-mpi/spotting-openmp-and-mpi-code.md) | How do I tell OpenMP, MPI or both from the source, the build and the job script? |
| 5 | [Hybrid and the binding trap](/fields/system-administration/openmp-and-open-mpi/hybrid-and-the-binding-trap.md) | Why does mixing them silently halve my speed, and how do I fix it? |
| 6 | [Where they're going](/fields/system-administration/openmp-and-open-mpi/where-they-are-going.md) | What did OpenMP 6.0 and MPI 5.0 add, and what never changes? |
| 7 | [Under Slurm](/fields/system-administration/openmp-and-open-mpi/mpi-and-openmp-under-slurm.md) | Who starts the ranks on a cluster, and which job-script lines decide the binding trap? |
| 8 | [On Kubernetes](/fields/system-administration/openmp-and-open-mpi/mpi-and-openmp-on-kubernetes.md) | How does an MPIJob give mpirun its address book, and which three numbers must agree? |

Each page ends with the question the next one answers. The story: **name the things (1, 2), see them run (3), recognize them anywhere (4), combine them safely (5), know what is stable (6), and run it on Slurm (7) and Kubernetes (8)**.

## Versions

Parts 1 to 6 ran on Ubuntu 26.04.1 (Linux 7.0), gcc 15.2.0 and Open MPI 5.0.10 in a throwaway 4-CPU VM, destroyed afterwards. Ubuntu 22.04 and Open MPI 4.x were not tested; where a page leans on older behaviour it says so. Parts 7 and 8 were **not run**: they are written from the Slurm, Kubernetes, MPI Operator and Open MPI documentation (Slurm 26.05 docs, MPI Operator v2beta1) and say so on the page. The history and version facts come from the OpenMP and MPI Forum sites linked at the end of each page.

## Contents

| File | Description |
|------|-------------|
| [the-name-mixup](/fields/system-administration/openmp-and-open-mpi/the-name-mixup.md) | Not twins, not even cousins: what OpenMP, MPI and Open MPI each are |
| [where-they-came-from](/fields/system-administration/openmp-and-open-mpi/where-they-came-from.md) | The 1990s story behind both standards and Open MPI's ancestors |
| [threads-and-ranks](/fields/system-administration/openmp-and-open-mpi/threads-and-ranks.md) | Threads vs ranks with tested hello programs, a data race and a reduction |
| [spotting-openmp-and-mpi-code](/fields/system-administration/openmp-and-open-mpi/spotting-openmp-and-mpi-code.md) | Recognizing OpenMP, MPI or hybrid in source, builds and job scripts |
| [hybrid-and-the-binding-trap](/fields/system-administration/openmp-and-open-mpi/hybrid-and-the-binding-trap.md) | Hybrid MPI+OpenMP and the default binding that halves your speed |
| [where-they-are-going](/fields/system-administration/openmp-and-open-mpi/where-they-are-going.md) | OpenMP 6.0, MPI 5.0 and Open MPI today, and what stays stable |
| [mpi-and-openmp-under-slurm](/fields/system-administration/openmp-and-open-mpi/mpi-and-openmp-under-slurm.md) | How Slurm launches ranks, PMIx as the address book, ntasks and cpus-per-task |
| [mpi-and-openmp-on-kubernetes](/fields/system-administration/openmp-and-open-mpi/mpi-and-openmp-on-kubernetes.md) | The MPI Operator: launcher, workers, headless Service, SSH and CPU numbers |
