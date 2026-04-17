# Operating System - CPU Affinity

This terminology came up in front of me during my work with benchmark tests, from its name it describes that it is related to managing the CPU processes of certain degree, and again it gets me back to why we should learn the foundation of Operating System (OS). This topic is related to performance tuning in OS.

In the coming up sections, I will try to explain what I learned and needed about it.

# Table of Notes
- [Operating System - CPU Affinity](#operating-system---cpu-affinity)
- [Table of Notes](#table-of-notes)
- [CPU Affinity](#cpu-affinity)
- [Why?!](#why)
  - [Useful for Various Reasons!](#useful-for-various-reasons)
  - [What is the challenges in Multitasking Systems?](#what-is-the-challenges-in-multitasking-systems)
- [How to Set CPU Affinity?!](#how-to-set-cpu-affinity)
  - [Typical Affinity Setups](#typical-affinity-setups)
  - [How to Set?](#how-to-set)
- [Resources](#resources)

# CPU Affinity
The capability of assign a process or a thread to certain CPU cores.

On the normal default scenario, the OS' scheduler decides which core to use for each process, and of course it's depending on factors like:
- load balancing
- priority
- resources available

So the ability to override this decision by setting the CPU affinity of a process, either manually or programmatically, this is what's called ****CPU Affinity****; this means restriction or preferring certain cores for a process, or assign different cores to different processes.

# Why?!
There are lots of overhead that we might be interested to reduce, so we can improve the performance!! 

Ones of the biggest overhead a process faces, are the ****context switching, Cache Misses, Memory Access latency, & Synchronization****.

So we are interested in ****The Locality of Data and Instructions**** where every data and instructions are now local wrt to the process and CPU it works on, so there is no overhead, resulting in a higher cache hit rate and memory bandwidth.

## Useful for Various Reasons!
Here are a list of Reasons what are the benefits of CPU affinity?
|Reason|Details|
-|-|
Performance Optimization|Assigning specific threads or processes to dedicated CPU cores can improve performance by reducing contention of shared resources and minimizing cache trashing.
Resource Utilization|Used to isolate tasks from others.
Hardware Utilization|Maximize hardware utilization and system throughput.

## What is the challenges in Multitasking Systems?
|Challenge|Problem|CPU Affinity Solution|
|-|-|-|
CPU Contention|In multitasking environments, multiple processes or threads compete for CPU resources, leading to CPU contention. This contention can result in inefficient CPU utilization and degraded performance for individual tasks.|CPU affinity allows specific processes or threads to be bound to particular dedicated CPU cores, without contention from other tasks.
Cache Effects|Modern CPUs have multiple levels of cache memory, which are shared among CPU cores. When tasks are switched between cores, it can lead to cache **thrashing**, where cache contents are frequently invalidated, causing cache misses and degraded.
NUMA effects|In NUMA systems, memory access latency varies depending on the distance between CPU cores and memory banks. Tasks accessing memory that is local to their assigned CPU cores have lower latency compared to accessing remote memory.|CPU affinity can be used to schedule tasks on CPU cores that are closer to the memory banks containing the data they need. This will helps reduce memory access latency and improve overall system performance in NUMA architectures.
Thread migration overhead|When tasks are migrated between CPU cores frequently, it incurs overhead due to context switching and cache invalidation. This overhead can degrade system performance, especially for latency-sensitive applications.|CPU affinity minimizes thread migration overhead by keeping tasks bound to specific CPU cores. 

# How to Set CPU Affinity?!
In RHEL, Affinity is represented by a bit mask, where each bit in the mask represents a CPU core, so {1: the thread or interrupt runs on that core, 0: the thread or interrupt in excluded from running on the core}. The default value for an affinity bit mask is all ones, meaning the thread or interrupt can run on any core in the system.
- Note child processes inherit the CPU affinities of their parents.

## Typical Affinity Setups
There are several setups to achieve maximum possible performance using CPU affinity:
1. We can use a single CPU core dedicated to specific type of processes, for example, we can set a single CPU core for all system processes, and setting the remaining CPU cores for the applications to run on.
2. Configure a thread application and specific kernel thread to work on the same CPU.
3. Pairing the producer-consumer threads on each CPU?!
   - A producer & consumer are two classes of threads, where producers are responsible for insert data into the buffer, where consumers are responsible for remote it from the buffer.
   - So Utilizing CPU affinity to setup the producers and consumers to work on the same CPU core, will optimize performance by reducing cache misses and improving cache locality, as the threads share the same CPU cache and can communicate more efficiently.

## How to Set?
A typical good practice is to estimate the correct number of CPUs cores required for certain application/process, then isolates these cores.

This could be achieved using several methods like:
- Tuna tool, please refer to [docs](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/performance_tuning_guide/chap-tuna).
- Shell scripts to modify bit mask, like *taskset*command.

Please refer to RHEL chapter 8 [docs](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux_for_real_time/8/html/optimizing_rhel_8_for_real_time_for_low_latency_operation/assembly_setting-cpu-affinity-on-rhel-for-real-time_optimizing-rhel8-for-real-time-for-low-latency-operation#proc_tuning-processor-affinity-using-the-taskset-command_assembly_setting-cpu-affinity-on-rhel-for-real-time) for better info related to how to set CPU affinity.

# Resources
- What are the advantages and disadvantages of using CPU affinity and pinning for process scheduling?, Linkedin System Monitoring, [https://www.linkedin.com/advice/1/what-advantages-disadvantages-using-cpu-affinity](https://www.linkedin.com/advice/1/what-advantages-disadvantages-using-cpu-affinity)
- Chapter 8. Setting CPU affinity on RHEL, Red Hat Customer Portal, [https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux_for_real_time/8/html/optimizing_rhel_8_for_real_time_for_low_latency_operation/assembly_setting-cpu-affinity-on-rhel-for-real-time_optimizing-rhel8-for-real-time-for-low-latency-operation](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux_for_real_time/8/html/optimizing_rhel_8_for_real_time_for_low_latency_operation/assembly_setting-cpu-affinity-on-rhel-for-real-time_optimizing-rhel8-for-real-time-for-low-latency-operation)
- Chapter 4. Tuna, Red Hat Customer Portal, [https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/performance_tuning_guide/chap-tuna](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/performance_tuning_guide/chap-tuna)