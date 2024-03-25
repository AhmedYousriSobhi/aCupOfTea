# 101- Cuda

# Table of Content
- [101- Cuda](#101--cuda)
- [Table of Content](#table-of-content)
- [A good to read](#a-good-to-read)
- [What is a Thread (really)](#what-is-a-thread-really)
- [Memory Coalescing?](#memory-coalescing)
- [Code Journey from CPU to GPU](#code-journey-from-cpu-to-gpu)
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

Please refer to [memory coalescing](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/programming/operatingSystem/memoryCoalescing.md) blog to get more info explained.

# Code Journey from CPU to GPU
With the help of ChatGPT 3.5, we try to illustrate an overview of what happen when we want to run code on GPU from CPU. 

A textual representation of the flow, highlighting the key components and their interactions. Let's break it down:

>     Host CPU: The process begins with the host Central Processing Unit (CPU), which initiates GPU computation by sending commands and data to the GPU.

>     GPU Driver: The GPU driver, running on the host CPU, acts as a communication bridge between the CPU and the GPU. It manages GPU resources, loads and compiles GPU programs, and schedules GPU tasks.

>     Application Code: The application code, written by the programmer, contains GPU-accelerated tasks (e.g., CUDA or OpenCL kernels) that need to be executed on the GPU.

>     Memory Allocation: The GPU driver allocates memory space in both the host and device memory. It manages data transfers between the host and device memory as needed for GPU computations.

>  Kernel Execution: The GPU driver schedules the execution of GPU kernels (e.g., CUDA or OpenCL kernels) on the GPU. Each kernel is executed by multiple threads in parallel on the GPU cores.

>     Streaming Multiprocessors (SMs): The GPU contains multiple SMs, each consisting of CUDA cores, registers, shared memory, and other resources. The SMs execute the GPU kernels in parallel, with each SM responsible for executing one or more blocks of threads.

>     Thread Execution: Within each SM, threads execute instructions from the GPU kernels. Threads access data from global memory, shared memory, or registers as required by the kernel instructions.

>     Memory Hierarchy: The GPU memory hierarchy includes registers, shared memory, L1 cache, L2 cache, and global memory. Data is moved between these memory levels to minimize memory access latency and maximize memory bandwidth.

>     Memory Transactions: The memory controller manages memory transactions between the SMs and the memory hierarchy. It coordinates data fetching, caching, and storing operations to optimize memory access performance.

>     Data Transfer: Data is transferred between the host and device memory as needed for GPU computations. The GPU driver manages these data transfers using DMA (Direct Memory Access) techniques to minimize CPU involvement and maximize data transfer bandwidth.

>     Result Retrieval: After GPU computations are completed, the results are retrieved from the GPU memory to the host memory. The GPU driver manages this process and ensures data integrity and correctness.

>     Task Completion: Once all GPU tasks are completed, the GPU driver notifies the host CPU, indicating that GPU resources are available for additional tasks or that the GPU can enter a low-power state to conserve energy.

# References
- Nvidia presentation High-Performance Computing with CUDA and TESLA GPUs, [here](https://intranet.birmingham.ac.uk/it/teams/infrastructure/research/bear/documents/public/CUDA-2013-07-31/CUDA-Tutorial.pdf).
- High Performance Computing with CUDA, [here](https://www.nvidia.com/content/PDF/isc-2011/Bradley2.pdf).
