# Operating System - Memory 

In Main memory, chapter 9 Memory, from Operating System concepts 10th edition reference,

# Table of notes
- [Operating System - Memory](#operating-system---memory)
- [Table of notes](#table-of-notes)
- [9.1.1 - Basic Hardware](#911---basic-hardware)
  - [CPU General-Purpose Storage](#cpu-general-purpose-storage)
  - [Machine Instructions](#machine-instructions)
  - [CPU Stall](#cpu-stall)
  - [Example Scenario](#example-scenario)
- [9.1.2 - Address Binding](#912---address-binding)
  - [Overview](#overview)
  - [Stages of Address Binding](#stages-of-address-binding)
  - [Address Space](#address-space)
  - [Dynamic Address Binding](#dynamic-address-binding)
  - [Example Scenario](#example-scenario-1)
  - [Benefits and Challenges](#benefits-and-challenges)
- [9.1.4 - Dynamic Loading](#914---dynamic-loading)
  - [Dynamic Loading](#dynamic-loading)
  - [How It Works!](#how-it-works)
  - [Use-case](#use-case)
  - [Programmer Responsibility, not OS](#programmer-responsibility-not-os)
- [9.1.5 - Dynamic Linking and Shared Libraries](#915---dynamic-linking-and-shared-libraries)
  - [Motivation](#motivation)
  - [Static Linking vs Dynamic Linking](#static-linking-vs-dynamic-linking)
  - [How It Works!](#how-it-works-1)
  - [Advantages](#advantages)
  - [OS Help is Required](#os-help-is-required)

# 9.1.1 - Basic Hardware
## CPU General-Purpose Storage
**The only general-purpose storage that The CPU can access are two!**
1. Main memory
2. Registers build into each processing core.
- They serve as general-purpose storage as they can hold any type of data or instructions needed for processing.

## Machine Instructions
**"There are machine instructions that take memory addresses as arguments, but none that take disk addresses."**
- Machine instructions can directly reference memory addresses. This means the CPU can fetch, decode, and execute instructions that involves reading from or writing to specific locations in the main memory.
- Also machine instructions cannot directly reference disk addresses, so they can't read from or write to disk storage; instead they must work with the data that has been loaded into memory.

## CPU Stall
Registers could be access on one cycle, unlike main memory accessed in many cycles via a transaction on the memory bus.

Here comes the Operating System to pause the CPU's execution momentarily, to load the required data from disk into memory, then resume the execution; This is called ***CPU Stall***.

The remedy is to add fast memory between the CPU and main memory, which is ***cache memory***, which build on the CPU chip, without the control of operating-system.
- This will speed up the memory-access.
- During a memory stall, a multithreaded core can switch from the stalled hardware thread to another hardware thread.

## Example Scenario
Imagine a scenario where a program is running on a computer. Here's how the process works in line with the paragraph:
1. Program Execution: The CPU needs to execute a program that is stored on the disk.
2. Loading into Memory: The program and any necessary data are loaded from the disk into the main memory.
3. CPU Operation: The CPU fetches instructions from the main memory, decodes them, and executes them. It also uses data from the main memory during this process.
4. Data Not in Memory: If the CPU needs data that is not currently in the main memory (perhaps it is still on the disk), the operating system will pause the CPU's execution momentarily, load the required data into memory, and then resume execution.

# 9.1.2 - Address Binding

In Main memory, chapter 9.1.2 Address Binding, from Operating System concepts 10th edition reference,

Address Binding is a concept in OS, particularly in the context of memory management.

## Overview
Address binding refers to the process of mapping a program's logical address to physical addresses in the memory. 

## Stages of Address Binding
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
   - The addresses are bound dynamically using hardware support (e.g., Memory Management unit or MMU).

![multi-step processing of a user program](https://i.postimg.cc/V6PLbQj7/Screenshot-from-2024-05-26-21-22-40.png)

## Address Space
- ***Logical address space***: the set of addresses generated by the CPU during execution.
- ***Physical address space***: the set of addresses seen by the memory unit (RAM).
- The logical address is translated to a physical address by the address binding process. This translation can be static (compile/load time) or dynamic (execution time).

## Dynamic Address Binding

Dynamic binding involves:
- ***Base register***: holds the starting physical address of the process.
- ***Limit register***: specifies the range of logical addresses.

When a logical address is generated by the CPU, it's checked against the limit register to ensure it is within bounds. If it's valid, the address is added to the base register to form the physical address.

## Example Scenario

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

## Benefits and Challenges
- Compile-Time Binding: Simple but inflexible, as it requires the program to always load at the same location.
- Load-Time Binding: More flexible but requires relocation each time the program is loaded.
- Execution-Time Binding: Highly flexible, supports dynamic memory allocation and virtual memory, but requires sophisticated hardware support.

# 9.1.4 - Dynamic Loading
A program is limited to the size of physical memory, as the entire program and all data of a process must be loaded in the physical memory for the process to execute.

How to utilize the memory space more?

## Dynamic Loading
- With dynamic loading, a routine is not loaded until it is called.
- So routine is loaded only when it is needed.

## How It Works!
- All routines are kept on disk in a relocatable load format.
- The main program is loaded into memory and is executed.
- When a routine needs to call another routine, the calling routine first checks to see whether the other routine has been loaded. 
- If it has not, the relocatable linking loader is called to load the desired routine into memory and to update the program’s address tables to reflect this change. 
- Then control is passed to the newly loaded routine.

## Use-case
- When large amount or code are needed to handle infrequently occurring cases, such as error routines.
- In such case, the total program size is large, but the portion that used (hence loaded) may be much smaller.

## Programmer Responsibility, not OS
- Dynamic loading does not require special support from the operating system. 
- It is the responsibility of the users to design their programs to take advantage of such a method. 
Operating systems may help the programmer, however, by providing library routines to implement dynamic loading.

# 9.1.5 - Dynamic Linking and Shared Libraries
In this part, it's discussed the concept of ***DLL - Dynamic Linked libraries***, ***which are *system libraries* that are linked to user programs when the programs are run***.

## Motivation
A programmer found that, his program has a huge size of program's executable image, and also consume main memory which is a waste of memory resources.

Investigating, he found that the program includes a copy of its language library(or at least the routines referenced by the program) in the executable image.

This was due to ***Static Linking***, where the language libraries are actually combined by the loader into the binaries of the program image.

Thinking about a solution, why wouldn't system libraries be shared and also linked to the program during program running stage?!

## Static Linking vs Dynamic Linking
- ***Static Linking***: in which system libraries are treated like any other object module, and are combined by the loader into the binary program image.
- ***Dynamic Linking***: is similar to dynamic loading, though, linking, rather than loading, is postponed until execution time.

## How It Works!
- When a program references a routine, that is in a dynamic library. 
- The loader locates the DLL, then loads it into memory if necessary.
- It then adjusts addresses that reference functions in the dynamic library to the location in memory where the DLL is stored.

## Advantages
- DLL libraries can be shared among multiple processes, so that only one instance of DLL in main memory.
    - That's the reason, DLL are also known as ***shared libraries***.
    - Mainly used in Windows, and Linux systems.

- Dynamically linked libraries can be extended to library updates (such as bug fixes).
  - A library may be replaced by a new version, and all programs that reference the library will automatically use the new version.
  - Without dynamic linking, all programs would need to be relinked to gain access to new library.
  - This has a benefit that, it could be different version of the same library, each version information is included in both the program and the library. each version is loaded into the memory, and each program uses its version information to decide which copy of the library to use.

## OS Help is Required
Unlike dynamic loading, dynamic linking and shared libraries generally require help from the operating system. If the processes in memory are protected from one another, then the operating system is the only entity that can check to see whether the needed routine is in another process’s memory space or that can allow multiple processes to access the same memory addresses.

This concept, as well as how DLLs can be shared by multiple processes, are elaborated in paging in Section 9.3.4.