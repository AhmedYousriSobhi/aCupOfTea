# Parallel Programming - Overview

> Techniques for concurrent and parallel execution in Python and other languages. By the end you'll know which flavor of "doing many things at once" to reach for.

One worker is slow. Ten workers could be faster, if they can split the job and talk to each other. That's parallel programming. The ways to do it range from threads and processes on one machine to many machines passing messages, and GPUs.

---

## The route

| Page | The question it answers |
|---|---|
| [mpi](/programming/parallel-programming/mpi.md) | How do separate processes, even on separate machines, send each other messages? |

---

## Who this is for

Anyone whose job is too big or too slow for a single process.

---

## Contents

| File | Description |
|------|-------------|
| [mpi](/programming/parallel-programming/mpi.md) | Message Passing Interface for distributed computing |

So far this folder holds the MPI references. Multithreading, multiprocessing and GPU parallelism are not written yet.
