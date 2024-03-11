# 101- Cuda

# Table of Content
- [101- Cuda](#101--cuda)
- [Table of Content](#table-of-content)
- [A good to read](#a-good-to-read)
- [What is a Thread (really)](#what-is-a-thread-really)
- [Memory Coalescing?](#memory-coalescing)
- [References](#references)

# A good to read
- [The supercomputing blog](http://supercomputingblog.com/cuda-tutorials/) for Cuda tutorial.

# What is a Thread (really)
According to a question in [Stackoverflow regarding what is a thread really](https://stackoverflow.com/a/5201906)!!, the auther pwnall illustrate the following:
- Thread is an execution context, where the process is a bunch of resources associated with a computation; so process can have one or many threads.
- As said, the thread is an execution context, which is all the information a CPU needs to execute a stream of instructions.
- The CPU knows each execution needs to be done by its thread, so if the cpu needs to continue work on it, it will continue its thread.
- It's an illusion by the CPU, that it's doing multiple computations at the same time.
- It does that by spending a bit of time on each computation. It can do that because it has an execution context for each computation

Following up the next answer from Ben Voigt, from [stackoverflow](https://stackoverflow.com/a/5201879), who tries to describe what is really a thread:
- A thread is an independent set of values for the processor registers {instruction pointer: program counter that controls what exectures in what order, Stack pointer: points to area of memory for each thread or else they'll interfere with.}
- Threads are the software unit affected by control flow (functions call, loops, goto), because these instructions operate on the instruction pointer, and that belongs to a particular thread.
- The value of instruction pointer, and the instruction stored at that location is sufficient to determine a new value for the instruction pointer.
- The sequence of values that IP tales on, forms a path of execution weaving throught the program code, giving rise to the name 'thread'.

# Memory Coalescing?
Memory coalescing is a technique used in parallel computing, particularly in GPU programming, to improve memory access efficiency.

In GPU architectures, memory access typically occurs in groups called "warps" or "threads", which are small groups of parallel execution units. When these threads access memory, they often do so in a non-contiguous manner, meaning they may request data from different memory locations.

Memory coalescing aims to optimize memory access patterns by organizing memory requests from adjacent threads into larger, contiguous memory transactions. By doing so, memory coalescing reduces the number of memory transactions required to fulfill memory requests, which can significantly improve memory access performance and bandwidth utilization.

For example, suppose multiple threads in a warp need to access consecutive elements of an array. Instead of accessing these elements individually, memory coalescing allows the GPU to fetch them in a single transaction, minimizing the overhead associated with memory accesses.

# References
- Nvidia presentation High-Performance Computing with CUDA and TESLA GPUs, [here](https://intranet.birmingham.ac.uk/it/teams/infrastructure/research/bear/documents/public/CUDA-2013-07-31/CUDA-Tutorial.pdf).
- High Performance Computing with CUDA, [here](https://www.nvidia.com/content/PDF/isc-2011/Bradley2.pdf).
