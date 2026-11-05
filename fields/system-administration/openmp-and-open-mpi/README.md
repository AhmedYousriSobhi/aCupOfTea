---
id: openmp-and-open-mpi-overview
title: OpenMP and Open MPI - Overview
sidebar_label: Overview
summary: A six-part series that untangles OpenMP, MPI and Open MPI - what each one is, where they came from, how to read their code on sight and how to combine them.
level: beginner
type: concept
domains: [systems-and-hpc, software-engineering]
---

# OpenMP and Open MPI - Overview

> A six-part series for anyone whose brain blue-screens when two names differ by one space. By the end you'll know what each name means, why they exist, how to spot their code in a glance, and how the two meet in one job.

## The route

| # | Page | The question it answers |
|---|------|-------------------------|
| 1 | [Not twins, not even cousins](/fields/system-administration/openmp-and-open-mpi/the-name-mixup.md) | Are OpenMP and Open MPI twins? What is MPI, then? |
| 2 | [Where they came from](/fields/system-administration/openmp-and-open-mpi/where-they-came-from.md) | Why do two parallel standards exist, and who wrote each? |
| 3 | [Threads and ranks](/fields/system-administration/openmp-and-open-mpi/threads-and-ranks.md) | What does each style look like when it runs, and what bug does each invite? |
| 4 | [Spotting the code](/fields/system-administration/openmp-and-open-mpi/spotting-openmp-and-mpi-code.md) | How do I tell OpenMP, MPI or both from the source, the build and the job script? |
| 5 | [Hybrid and the binding trap](/fields/system-administration/openmp-and-open-mpi/hybrid-and-the-binding-trap.md) | Why does mixing them silently halve my speed, and how do I fix it? |
| 6 | [Where they're going](/fields/system-administration/openmp-and-open-mpi/where-they-are-going.md) | What did OpenMP 6.0 and MPI 5.0 add, and what never changes? |

Each page ends with the question the next one answers. The story: **name the things (1, 2), see them run (3), recognize them anywhere (4), combine them safely (5), and know what is stable (6)**.

## Versions

Run on Ubuntu 26.04.1 (Linux 7.0), gcc 15.2.0 and Open MPI 5.0.10 in a throwaway 4-CPU VM, destroyed afterwards. Ubuntu 22.04 and Open MPI 4.x were not tested; where a page leans on older behaviour it says so. The history and version facts come from the OpenMP and MPI Forum sites linked at the end of each page.

## Contents

| File | Description |
|------|-------------|
| [the-name-mixup](/fields/system-administration/openmp-and-open-mpi/the-name-mixup.md) | Not twins, not even cousins: what OpenMP, MPI and Open MPI each are |
| [where-they-came-from](/fields/system-administration/openmp-and-open-mpi/where-they-came-from.md) | The 1990s story behind both standards and Open MPI's ancestors |
| [threads-and-ranks](/fields/system-administration/openmp-and-open-mpi/threads-and-ranks.md) | Threads vs ranks with tested hello programs, a data race and a reduction |
| [spotting-openmp-and-mpi-code](/fields/system-administration/openmp-and-open-mpi/spotting-openmp-and-mpi-code.md) | Recognizing OpenMP, MPI or hybrid in source, builds and job scripts |
| [hybrid-and-the-binding-trap](/fields/system-administration/openmp-and-open-mpi/hybrid-and-the-binding-trap.md) | Hybrid MPI+OpenMP and the default binding that halves your speed |
| [where-they-are-going](/fields/system-administration/openmp-and-open-mpi/where-they-are-going.md) | OpenMP 6.0, MPI 5.0 and Open MPI today, and what stays stable |
