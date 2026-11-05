---
id: openmp-mpi-where-they-are-going
title: "Where They're Going: OpenMP 6, MPI 5 and Open MPI Today"
order: 6
sidebar_label: "6. Where they're going"
summary: The version trail from the 1990s to OpenMP 6.0 and MPI 5.0 - GPUs and tasks on one side, a standard ABI on the other - and why the core ideas you learned will not expire.
level: beginner
type: concept
domains: [systems-and-hpc, software-engineering]
tags: [openmp, mpi, hpc]
relations:
  prerequisites: [openmp-mpi-where-they-came-from]
---

# Where They're Going: OpenMP 6, MPI 5 and Open MPI Today

> Part 6 of 6. By the end you'll know what the latest version of each one added, how to read a version number, and what is safe to learn once and keep.

## Contents

- [The version trail](#the-version-trail)
- [OpenMP: from loops to devices to tasks](#openmp-from-loops-to-devices-to-tasks)
- [MPI: from messages to one binary interface](#mpi-from-messages-to-one-binary-interface)
- [Open MPI today](#open-mpi-today)
- [What won't change](#what-wont-change)
- [Your pocket summary of the series](#your-pocket-summary-of-the-series)

---

## The version trail

Dates from the official lists, [OpenMP](https://www.openmp.org/specifications/) and [MPI](https://www.mpi-forum.org/docs/):

| Year | OpenMP | MPI |
|------|--------|-----|
| 1997 | Fortran 1.0 (October) | MPI 2.0 (July) |
| 1998 | C/C++ 1.0 | |
| 2005 | 2.5 (C/C++ and Fortran in one document) | |
| 2008 | 3.0 (May) | 2.1 (September) |
| 2009 | | 2.2 |
| 2011 | 3.1 | |
| 2012 | | 3.0 (September) |
| 2013 | 4.0 (July) | |
| 2015 | 4.5 | 3.1 (June) |
| 2018 | 5.0 | |
| 2020-21 | 5.1 (2020), 5.2 (2021) | 4.0 (June 2021) |
| 2023 | | 4.1 (November) |
| 2024-25 | **6.0 (November 2024)** | **5.0 (June 5, 2025)** |

Reading the numbers: a bump in the **first** number is a larger step (new capabilities); a bump in the second is usually a consolidation and fixes. Neither standard throws old programs away lightly: the MPI standard states that "any valid MPI-4.1 program is a valid MPI-5.0 program".

---

## OpenMP: from loops to devices to tasks

- **1.0 to 3.x:** loops and sections split among threads, the picture from part 3.
- **4.0 (July 2013):** the biggest widening. Per the [4.0 release announcement](https://www.openmp.org/press-release/openmp-4-0-api-released/): support for **accelerator devices** (this is the `#pragma omp target` you meet in GPU-offloading code), **SIMD** constructs to vectorize loops, **task dependencies**, **thread affinity**, user-defined reductions and cancellation.
- **6.0 (November 14, 2024):** per the [announcement](https://www.openmp.org/home-news/openmp-arb-releases-openmp-6-0-for-easier-programming/): easier task programming, finer control over memory allocation, loop transformations such as fusion, reversal and interchange, support for recent C, C++ and Fortran standards, and **removal of features deprecated in 5.0, 5.1 and 5.2**. The openmp.org blog says first implementations of 6.0 features are in the Intel and GCC compilers.
- **6.1:** a public comment draft dated July 2026 is on the specifications page. It is a draft, not a release.

The direction: from "make my loop parallel" to "describe the work, the data and the device, and let the compiler map it".

> [!NOTE]
> A spec version is not a compiler version. What your cluster's compiler supports is a separate question: check its documentation before relying on a new directive.

---

## MPI: from messages to one binary interface

- **1.x (1994-95):** the core of part 3: ranks, communicators, send and receive, collectives.
- **2.0 (1997):** an extension of 1.x, per the Open MPI FAQ ("mostly added to and extended MPI-1.0").
- **4.0 (June 2021):** per the MPI-4.1 document, the largest changes are **large-count** versions of many routines (counts no longer limited to an `int`), **persistent collectives**, **partitioned communication**, and a new way to initialize MPI called **sessions**.
- **5.0 (June 5, 2025):** the headline is a **standard ABI** (Application Binary Interface). Until now, a program compiled against one MPI implementation had to be recompiled for another, because details such as the layout of handle types differed. The ABI chapter fixes those details so one compiled program can run with different implementations. It exists "in parallel with existing implementation ABIs", so nothing existing breaks. At ISC25, MPICH was described as having implemented it already, and Open MPI's work as in progress.

The direction: the same rank-and-message model, with larger data, better overlap of communication and computation, and less pain moving binaries between systems.

---

## Open MPI today

Per the [downloads page](https://www.open-mpi.org/software/ompi/) (retrieved as of this series' writing):

| Series | Status |
|--------|--------|
| v6.0 | Upcoming, no date listed |
| v5.0 | Current, stable; latest 5.0.11 (September 16, 2026) |
| v4.1 | Still supported |
| v4.0 and older | Retired |

The [about page](https://www.open-mpi.org/about/) says Open MPI offers full MPI-3.1 conformance with many MPI-4.0 elements. The series I tested, 5.0.10, is the Ubuntu 26.04 package. On that install, `mpirun` ships with the PMIx and PRRTE packages, which is why some help text lived in `libprrte-dev` (part 3).

> [!NOTE]
> Behaviour I describe for binding and launching is from 5.0.x. Open MPI 4.1 is still supported but has different internals. I did not test it for this series, so check its manual before assuming the same flags and messages.

---

## What won't change

You can learn these once and keep them for the rest of your career:

| Idea | Why it lasts |
|------|--------------|
| Shared memory vs separate memory | It is the hardware split that started both standards (part 2) |
| Threads need care about who writes what; ranks need messages | The two signature bugs, race and deadlock, are the same in every version |
| `parallel`, `for`, `reduction` / `Init`, `rank`, `Send`, `Reduce` | The vocabulary has been stable since the 1990s |
| Binding decides where work runs | Newer hardware makes it matter more, not less |

New versions add vocabulary on top. They do not replace the vocabulary you now have.

---

## Your pocket summary of the series

| Part | One line |
|------|----------|
| 1 | OpenMP = threads, MPI = messages, Open MPI = one implementation of MPI |
| 2 | Two tribes in the 1990s: MPI (1992-94) and OpenMP (1997) solved the same headache from opposite sides |
| 3 | One kitchen with many cooks vs many kitchens passing notes; race vs deadlock |
| 4 | `omp.h`, `#pragma omp`, `-fopenmp` vs `mpi.h`, `MPI_`, `mpirun`; both together is hybrid |
| 5 | Check "rank may use N cpus": the default can pin each rank to one core |
| 6 | OpenMP 6.0 and MPI 5.0 are the current versions; the core ideas are stable |

**Takeaway:** the names are confusing, but the ideas are two: share memory between threads, or send messages between processes. Everything else is detail on top.

---

## References

- [OpenMP specifications: release dates and the 6.1 draft](https://www.openmp.org/specifications/)
- [OpenMP 4.0 release announcement (July 26, 2013)](https://www.openmp.org/press-release/openmp-4-0-api-released/)
- [OpenMP ARB releases OpenMP 6.0 (November 2024)](https://www.openmp.org/home-news/openmp-arb-releases-openmp-6-0-for-easier-programming/)
- [OpenMP 6.0 blog: first implementations](https://www.openmp.org/blog/openmp-6/)
- [MPI Forum: standard versions and dates](https://www.mpi-forum.org/docs/)
- [MPI-5.0 standard: background, ABI chapter](https://www.mpi-forum.org/docs/mpi-5.0/mpi50-report/node20.htm)
- [MPI-4.1 standard: summary of the MPI-4.0 additions](https://mpi-forum.org/docs/mpi-4.1/mpi41-report/node17.htm)
- [MPI 5.0 voted in (MPI Forum mailing list)](https://lists.mpi-forum.org/pipermail/mpi-forum/2025-June/007905.html)
- [Open MPI downloads: release series](https://www.open-mpi.org/software/ompi/)
- [About Open MPI](https://www.open-mpi.org/about/)
