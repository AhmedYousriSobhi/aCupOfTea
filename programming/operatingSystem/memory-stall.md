# Operating Systems - Memory Stalls

# Table of Points
- [Operating Systems - Memory Stalls](#operating-systems---memory-stalls)
- [Table of Points](#table-of-points)
- [Memory Stall and Multithreading](#memory-stall-and-multithreading)
  - [Memory Stall in Single-Threaded Systems](#memory-stall-in-single-threaded-systems)
  - [Multithreaded Cores](#multithreaded-cores)
  - [Switching Threads During Memory Stalls](#switching-threads-during-memory-stalls)
    - [Example Scenario](#example-scenario)
- [CPU Stall vs Memory Stall](#cpu-stall-vs-memory-stall)

# Memory Stall and Multithreading
```
during a memory stall, a multithreaded core can switch from the stalled hardware thread to another hardware thread
```
- In Main memory, chapter 9.1.1 Basic Hardware, from Operating System concepts 10th edition reference.

## Memory Stall in Single-Threaded Systems
- In single-threaded systems, when a memory stall occurs, (i.e., the CPU must wait for data to be fetched from the main memory).
- The CPU remains idle until the required data is available.
- This waiting period significantly reduces the efficiency and overall performance of the CPU, as the cpu is stalled.

## Multithreaded Cores
- They are designed to address the inefficiencies associated with memory stalls in single-threaded systems.
- Multithreading allows a single CPU core to manage and execute multiple hardware threads concurrently.

There are different types of multithreading, including:
- ***Fine-grained multithreading***: Switches between threads at each instruction cycle.
- ***Coarse-grained multithreading***: Switches threads only when one thread encounters a long-latency event such as a memory stall.
- ***Simultaneous multithreading (SMT)***: Executes multiple threads in parallel by utilizing the core’s resources more efficiently.

## Switching Threads During Memory Stalls
When a memory stall occurs in multithreaded core, the CPU can mitigate the stall's impact by switching from the stalled thread to another thread that is ready to execute.

Here is how this works:
1. ***Detection of Memory Stall***
- The CPU detects that the current thread is stalled because it is waiting for data from memory.
- The data might be coming from the main memory or even from a slower storage medium like a hard drive.

2. ***Thread Context Switching***
- Instead of idling, the CPU saves the state (context) of the stalled thread. This context includes the current instruction, register states, and other necessary information to resume the thread later.
- The CPU then loads the state (context) of another thread that is ready to execute. This involves setting up the CPU’s registers and program counter to reflect the new thread’s state.

3. ***Execution of Another Thread***
- The CPU begins executing instructions from the new thread, effectively utilizing the CPU cycles that would otherwise be wasted during the memory stall.
- This process continues until the data required by the original thread is available.

4. ***Resumption of Stalled Thread***
- Once the memory fetch is complete and the required data is available, the CPU can switch back to the original thread.
- The state of the original thread is restored, and execution resumes from where it left off.


### Example Scenario
Consider a CPU core capable of handling two threads, Thread A and Thread B:
- Thread A is executing and encounters a memory stall while waiting for data from the main memory.
- The CPU detects the stall and switches to Thread B, which has no memory stall and can be executed immediately.
- Thread B continues executing while the memory fetch for Thread A is completed in the background.
- Once the data for Thread A is available, the CPU can switch back to Thread A and resume its execution.

# CPU Stall vs Memory Stall
Feature|	CPU Stall|	Memory Stall
|-|-|-|
Definition|	Waiting due to pipeline hazards or dependencies|	Waiting for data to be fetched from memory
Primary Cause|	- Data Hazards: Dependencies between instructions<br>- Control Hazards: Branch instructions<br>- Resource Hazards: Simultaneous resource requests	|- Cache Misses: Data not found in cache<br>- Memory Latency: Delays in accessing main memory<br>- Page Faults: Data retrieval from disk
Effects|	- Reduces instruction throughput<br>- Creates pipeline bubbles<br>- Performance degradation	|- Increases instruction latency<br>- Slows overall execution<br>- Lowers throughput
Mitigation Techniques|	- Out-of-order execution: Executes instructions out of order<br>- Branch prediction: Predicts branch outcomes<br>- Pipeline interleaving: Overlaps execution of instructions	|- Cache hierarchy: Multiple levels of cache<br>- Prefetching: Loads data into cache before needed<br>- Efficient memory management: Optimizes memory access patterns
Example Scenario|	- Waiting for the result of a previous instruction to use in the current one<br>- Waiting for a branch decision to be made<br>- Waiting for a shared resource to become available	|- Waiting for data to be loaded from main memory when it’s not found in the CPU cache<br>- Waiting for data to be fetched from disk due to a page fault
Types of Hazards|	- Data Hazards: Read-after-write, Write-after-read, Write-after-write<br>- Control Hazards: Branches, jumps<br>- Resource Hazards: Functional unit contention|	- Cache Misses: Data not in cache<br>- Memory Latency: Time to access RAM<br>- Disk Access: Time to retrieve data from disk (page faults)
Performance Impact|	- Reduced CPU efficiency<br>- Increased instruction execution time|	- Increased data access time<br>- Potential bottleneck in execution flow
Hardware/Software Techniques|	- Out-of-order execution<br>- Branch prediction<br>- Speculative execution<br>- Superscalar execution|	- Larger and more levels of cache<br>- Memory prefetching<br>- Use of faster memory technologies (e.g., DRAM vs. SRAM)<br>- Efficient paging and segmentation techniques