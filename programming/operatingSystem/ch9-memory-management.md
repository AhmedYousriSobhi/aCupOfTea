# Operating System - Memory Management

In Main memory, chapter 9 Memory Management, from Operating System concepts 10th edition reference,

# Table of notes
- [Operating System - Memory Management](#operating-system---memory-management)
- [Table of notes](#table-of-notes)
- [9.1. Background](#91-background)
  - [9.1.1. Basic Hardware](#911-basic-hardware)
    - [CPU General-Purpose Storage](#cpu-general-purpose-storage)
    - [Machine Instructions](#machine-instructions)
    - [CPU Stall](#cpu-stall)
      - [Example Scenario](#example-scenario)
    - [Memory Stall \& Multithreading](#memory-stall--multithreading)
      - [Memory Stall in Single-Threaded Systems](#memory-stall-in-single-threaded-systems)
      - [Multithreaded Cores](#multithreaded-cores)
      - [Switching Threads During Memory Stalls](#switching-threads-during-memory-stalls)
    - [Example Scenario](#example-scenario-1)
      - [CPU Stall vs Memory Stall](#cpu-stall-vs-memory-stall)
  - [9.1.2. Address Binding](#912-address-binding)
    - [Overview](#overview)
    - [Stages of Address Binding](#stages-of-address-binding)
    - [Address Space](#address-space)
    - [Dynamic Address Binding](#dynamic-address-binding)
    - [Example Scenario](#example-scenario-2)
    - [Benefits and Challenges](#benefits-and-challenges)
  - [9.1.4-Memory-Dynamic Loading](#914-memory-dynamic-loading)
    - [Dynamic Loading](#dynamic-loading)
    - [How It Works!](#how-it-works)
    - [Use-case](#use-case)
    - [Programmer Responsibility, not OS](#programmer-responsibility-not-os)
  - [9.1.5. Dynamic Linking and Shared Libraries](#915-dynamic-linking-and-shared-libraries)
    - [Motivation](#motivation)
    - [Static Linking vs Dynamic Linking](#static-linking-vs-dynamic-linking)
    - [How It Works!](#how-it-works-1)
    - [DLL Advantages](#dll-advantages)
    - [OS Help is Required](#os-help-is-required)
- [9.2. Contiguous Memory Allocation](#92-contiguous-memory-allocation)
  - [9.2.2. Memory Allocation](#922-memory-allocation)
- [9.3. Paging](#93-paging)
  - [9.3.2 Hardware Support](#932-hardware-support)
    - [9.3.2.1. Translation Look-Aside Buffer](#9321-translation-look-aside-buffer)
      - [How The TLB Works](#how-the-tlb-works)
      - [TLB Structure](#tlb-structure)
      - [Detailed Structure](#detailed-structure)
      - [Example Page Table Entry (PTE)](#example-page-table-entry-pte)
      - [TLB Operations](#tlb-operations)
      - [Benefits of the TLB](#benefits-of-the-tlb)
      - [Challenges with TLBs](#challenges-with-tlbs)
- [9.4. Structure of the Page Table](#94-structure-of-the-page-table)
  - [Problem of Straight-Forward Approach](#problem-of-straight-forward-approach)

# 9.1. Background
## 9.1.1. Basic Hardware
### CPU General-Purpose Storage
**The only general-purpose storage that The CPU can access are two!**
1. Main memory
2. Registers build into each processing core.
- They serve as general-purpose storage as they can hold any type of data or instructions needed for processing.

### Machine Instructions
**"There are machine instructions that take memory addresses as arguments, but none that take disk addresses."**
- Machine instructions can directly reference memory addresses. This means the CPU can fetch, decode, and execute instructions that involves reading from or writing to specific locations in the main memory.
- Also machine instructions cannot directly reference disk addresses, so they can't read from or write to disk storage; instead they must work with the data that has been loaded into memory.

### CPU Stall
Registers could be access on one cycle, unlike main memory accessed in many cycles via a transaction on the memory bus.

Here comes the Operating System to pause the CPU's execution momentarily, to load the required data from disk into memory, then resume the execution; This is called ***CPU Stall***.

The remedy is to add fast memory between the CPU and main memory, which is ***cache memory***, which build on the CPU chip, without the control of operating-system.
- This will speed up the memory-access.
- During a memory stall, a multithreaded core can switch from the stalled hardware thread to another hardware thread.

#### Example Scenario
Imagine a scenario where a program is running on a computer. Here's how the process works in line with the paragraph:
1. Program Execution: The CPU needs to execute a program that is stored on the disk.
2. Loading into Memory: The program and any necessary data are loaded from the disk into the main memory.
3. CPU Operation: The CPU fetches instructions from the main memory, decodes them, and executes them. It also uses data from the main memory during this process.
4. Data Not in Memory: If the CPU needs data that is not currently in the main memory (perhaps it is still on the disk), the operating system will pause the CPU's execution momentarily, load the required data into memory, and then resume execution.

### Memory Stall & Multithreading
```
during a memory stall, a multithreaded core can switch from the stalled hardware thread to another hardware thread
```
- In Main memory, chapter 9.1.1 Basic Hardware, from Operating System concepts 10th edition reference.

#### Memory Stall in Single-Threaded Systems
- In single-threaded systems, when a memory stall occurs, (i.e., the CPU must wait for data to be fetched from the main memory).
- The CPU remains idle until the required data is available.
- This waiting period significantly reduces the efficiency and overall performance of the CPU, as the cpu is stalled.

#### Multithreaded Cores
- They are designed to address the inefficiencies associated with memory stalls in single-threaded systems.
- Multithreading allows a single CPU core to manage and execute multiple hardware threads concurrently.

There are different types of multithreading, including:
- ***Fine-grained multithreading***: Switches between threads at each instruction cycle.
- ***Coarse-grained multithreading***: Switches threads only when one thread encounters a long-latency event such as a memory stall.
- ***Simultaneous multithreading (SMT)***: Executes multiple threads in parallel by utilizing the core’s resources more efficiently.

#### Switching Threads During Memory Stalls
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

#### CPU Stall vs Memory Stall
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

## 9.1.2. Address Binding
In Main memory, chapter 9.1.2 Address Binding, from Operating System concepts 10th edition reference,

Address Binding is a concept in OS, particularly in the context of memory management.

### Overview
Address binding refers to the process of mapping a program's logical address to physical addresses in the memory. 

### Stages of Address Binding
1. ***Compile Time***
   - if the memory location of a process is known at compile time, *absolute code* is generated.
   - The logical and physical addresses are fixed, which means the process must always be loaded at the same location.
   - If the starting location changes, then it'll be necessary to recompile the code again.
   - E.g, embedded systems often uses compile-time binding because they have fixed memory layouts.
2. ***Load Time***
    - If the memory location is not known at compile time, the compiler generate *relocatable code*.
    - The final binding occurs when the program is loaded into memory.
    - If the starting address changes, the code must be reloaded and relocated.
3. ***Execution Time***
   - The most flexible binding occurs at execution time, allowing processes to move in the memory.
   - This is used in systems that support virtual memory.
   - The addresses are bound dynamically using ***hardware support*** (e.g., Memory Management unit or MMU).

![multi-step processing of a user program](https://i.postimg.cc/V6PLbQj7/Screenshot-from-2024-05-26-21-22-40.png)

### Address Space
- ***Logical address space***: the set of addresses generated by the CPU during execution.
- ***Physical address space***: the set of addresses seen by the memory unit (RAM).
- The logical address is translated to a physical address by the address binding process. This translation can be static (compile/load time) or dynamic (execution time).

### Dynamic Address Binding

Dynamic binding involves:
- ***Base register***: holds the starting physical address of the process.
- ***Limit register***: specifies the range of logical addresses.

When a logical address is generated by the CPU, it's checked against the limit register to ensure it is within bounds. If it's valid, the address is added to the base register to form the physical address.

### Example Scenario

Imagine a program that needs to be executed. Here’s how address binding might occur at different stages:

- ***Compile Time***:
   - The compiler generates addresses assuming the program will start at a specific memory location (e.g., address 1000).
   - If it’s loaded at address 1000, no further binding is needed.

- ***Load Time***:
   - The program is compiled with relocatable addresses.
   - When the loader places the program in memory at address 2000, it adjusts the addresses accordingly.

- ***Execution Time***:
   - The program is loaded into memory, and the base register is set to 3000.
   - If the program generates a logical address 40, the MMU translates this to the physical address 3040 using the base register.

### Benefits and Challenges
- Compile-Time Binding: Simple but inflexible, as it requires the program to always load at the same location.
- Load-Time Binding: More flexible but requires relocation each time the program is loaded.
- Execution-Time Binding: Highly flexible, supports dynamic memory allocation and virtual memory, but requires sophisticated hardware support.

## 9.1.4-Memory-Dynamic Loading
A program is limited to the size of physical memory, as the entire program and all data of a process must be loaded in the physical memory for the process to execute.

How to utilize the memory space more?

### Dynamic Loading
- With dynamic loading, a routine is not loaded until it is called.
- So routine is loaded only when it is needed.

### How It Works!
- All routines are kept on disk in a relocatable load format.
- The main program is loaded into memory and is executed.
- When a routine needs to call another routine, the calling routine first checks to see whether the other routine has been loaded. 
- If it has not, the relocatable linking loader is called to load the desired routine into memory and to update the program’s address tables to reflect this change. 
- Then control is passed to the newly loaded routine.

### Use-case
- When large amount or code are needed to handle infrequently occurring cases, such as error routines.
- In such case, the total program size is large, but the portion that used (hence loaded) may be much smaller.

### Programmer Responsibility, not OS
- Dynamic loading does not require special support from the operating system. 
- It is the responsibility of the users to design their programs to take advantage of such a method. 
Operating systems may help the programmer, however, by providing library routines to implement dynamic loading.

## 9.1.5. Dynamic Linking and Shared Libraries
In this part, it's discussed the concept of ***DLL - Dynamic Linked libraries***, ***which are *system libraries* that are linked to user programs when the programs are run***.

### Motivation
A programmer found that, his program has a huge size of program's executable image, and also consume main memory which is a waste of memory resources.

Investigating, he found that the program includes a copy of its language library(or at least the routines referenced by the program) in the executable image.

This was due to ***Static Linking***, where the language libraries are actually combined by the loader into the binaries of the program image.

Thinking about a solution, why wouldn't system libraries be shared and also linked to the program during program running stage?!

### Static Linking vs Dynamic Linking
- ***Static Linking***: in which system libraries are treated like any other object module, and are combined by the loader into the binary program image.
- ***Dynamic Linking***: is similar to dynamic loading, though, linking, rather than loading, is postponed until execution time. Small piece of code, stub, used to locate the appropriate memory-resident library routine.

### How It Works!
- When a program references a routine, that is in a dynamic library. 
- The loader locates the DLL, then loads it into memory if necessary.
- It then adjusts addresses that reference functions in the dynamic library to the location in memory where the DLL is stored.

### DLL Advantages
- DLL libraries can be shared among multiple processes, so that only one instance of DLL in main memory.
    - That's the reason, DLL are also known as ***shared libraries***.
    - Mainly used in Windows, and Linux systems.

- Dynamically linked libraries can be extended to library updates (such as bug fixes).
  - A library may be replaced by a new version, and all programs that reference the library will automatically use the new version.
  - Without dynamic linking, all programs would need to be relinked to gain access to new library.
  - This has a benefit that, it could be different version of the same library, each version information is included in both the program and the library. each version is loaded into the memory, and each program uses its version information to decide which copy of the library to use.

### OS Help is Required
Unlike dynamic loading, dynamic linking and shared libraries generally require help from the operating system. If the processes in memory are protected from one another, then the operating system is the only entity that can check to see whether the needed routine is in another process’s memory space or that can allow multiple processes to access the same memory addresses.

This concept, as well as how DLLs can be shared by multiple processes, are elaborated in paging in Section 9.3.4.


# 9.2. Contiguous Memory Allocation
## 9.2.2. Memory Allocation
There are two type of allocation in memory:
- Contiguous Allocation: where the whole process must be loaded into the memory.
- Non-Contiguous Allocation: dividing the process into parts in the memory, so the process is loaded into different parts in the memory.
  - Segmentation: Non-equal parts; the process is divided into parts according to the user view of the process. So each segment has different length.
  - Paging: Equal parts.

# 9.3. Paging
## 9.3.2 Hardware Support
### 9.3.2.1. Translation Look-Aside Buffer
Yes storing the page table in main memory can yield in faster context switches, but it may also results in slower memory access times.

The Purpose of the TLB, is designed to speed up this translation by caching recent address translations.

#### How The TLB Works
1. Virtual to Physical Address Translation:
    - When a program needs to access a memory location, it uses a virtual address.
    - The MMU translates this virtual address into a physical address using the page table.

2. Role of the TLB:
    - The TLB caches a small number of recent virtual-to-physical address translations.
    - When a virtual address translation is needed, the MMU first checks the TLB.
    - If the translation is found in the TLB (a TLB hit), the physical address is returned quickly without accessing the page table.
    - If the translation is not in the TLB (a TLB miss), the MMU must perform the translation using the page table, and the result is then cached in the TLB for future use.
      - Note: some entries can be *wired down* for permanent fast access.

![Paging Hardware with TLB](https://i.postimg.cc/fLX6kyJ5/Screenshot-from-2024-06-07-10-26-20.png)

#### TLB Structure
1. Page Number (Virtual Page Number - VPN): This part of the entry represents a portion of the virtual address. 
   - In virtual memory systems, the virtual address is divided into two parts: the page number and the offset within that page. The page number is used to identify the virtual page being accessed.
2. Frame Number (Physical Frame Number - PFN): This part of the entry corresponds to the physical address. Specifically, it is the base address of the physical memory frame that maps to the virtual page. Similar to the virtual address, the physical address is divided into a frame number and an offset within that frame.

#### Detailed Structure
The structure of a TLB entry can be more elaborated as follows:
1. Tag (Page Number): This is the virtual page number (VPN) part of the virtual address that is being translated.
2. Data (Frame Number): This is the physical frame number (PFN) part of the physical address that the virtual page maps to.
3. Additional Information (optional):
    - Access Permissions: Information about the permissions associated with the page, such as read, write, and execute permissions.
    - Valid Bit: A bit that indicates whether the TLB entry is valid and can be used.
    - Dirty Bit: A bit that indicates if the page has been modified.
    - Accessed Bit: A bit that indicates if the page has been accessed recently.
    - Reference Count: A count of how many times the page has been accessed.

#### Example Page Table Entry (PTE)

Here is an example layout of a 32-bit PTE:

Bits|	Field|	Description|
|-|-|-|
0|	Valid Bit|	Indicates if the entry is valid
1-11|	Access Permissions|	Read, write, execute permissions
12|	Present Bit|	Indicates if the page is in physical memory
13|	Dirty Bit|	Indicates if the page has been modified
14|	Accessed Bit|	Indicates if the page has been accessed
15-31|	Physical Frame Number|	Base address of the physical frame

#### TLB Operations
1. TLB Hit:
    - The virtual address is found in the TLB.
    - The physical address is quickly retrieved from the TLB.
2. TLB Miss:
    - The virtual address is not in the TLB.
    - The MMU performs a page table lookup to find the physical address.
    - The new translation is stored in the TLB, possibly replacing an older entry.

#### Benefits of the TLB
- Speed: TLBs significantly reduce the time required for address translation by avoiding frequent accesses to the slower page table in memory.
- Efficiency: By caching translations, TLBs reduce the overall memory access time, improving the performance of the CPU and the system as a whole.

#### Challenges with TLBs
- Capacity: TLBs have a limited number of entries and may not always hold the necessary translations, leading to TLB misses.
- Coherency: Maintaining TLB coherency in multi-core systems can be complex, as changes to page tables must be reflected in all TLBs.
- Replacement Policies: Deciding which entry to replace on a TLB miss (e.g., Least Recently Used (LRU), Random) impacts performance

# 9.4. Structure of the Page Table
## Problem of Straight-Forward Approach
Memory structures for paging can get huge using straight-forward methods!!

Let's break down the problem with example:
1. 32-bit Logical Address Space:
  - Modern computers often use a 32-bit addressing scheme, meaning the logical (virtual) addresses are 32 bits long.
  - This results in a total addressable space of 2^32 bytes (4 GB).

2. Page Size of 4 KB:
  - Pages are the fixed-size blocks of memory that the virtual address space is divided into.
  - A page size of 4 KB means each page is 2^12 bytes (4096 bytes).

3. Number of Page Table Entries:
  - To calculate the number of entries in the page table, divide the total addressable space by the page size.
  - 2^32 / 2^12 ​=2^20
  - So, there are 2^20 (1 million) pages in a 32-bit address space with a 4 KB page size.

4. Size of Each Page Table Entry (PTE):
  - Assume each PTE is 4 bytes (which is common, though it can vary).

5. Total Size of the Page Table:
  - Multiply the number of entries by the size of each entry.
  - 2^20 entries × 4 bytes/entry = 2^22 bytes
  - 2^22 bytes=4 MB

So each process would need a 4MB of physical memory just to store its page table.

***Issues with Straightforward Page Tables***
- Large Memory Requirement: For each process, the page table alone consumes 4 MB of memory. If you have multiple processes, this requirement scales linearly, leading to a significant amount of memory dedicated solely to page tables.
- Contiguous Allocation: Allocating 4 MB of contiguous physical memory for each process’s page table can be problematic, especially when there are many processes or when the system is fragmented.

***Possible Solutions***
- Hierarchical Paging.
- Hashed Page Tables.
- Inverted Page Tables.