# Operating Systems - Operating Systems Introduction

Chapter 1 Operating Systems Introduction, from Operating System concepts 10th edition reference

> An Operating system is a described as 'a fill in the blank!'

The phrase "An operating system is 'fill in the blanks'" typically means that the definition or description of an operating system can be tailored to highlight specific functions, features, or aspects that are most relevant to the context in which it is being discussed. In other words, an operating system (OS) can be described in various ways depending on what aspects one wants to emphasize

# Mystic Map
- [Operating Systems - Operating Systems Introduction](#operating-systems---operating-systems-introduction)
- [Mystic Map](#mystic-map)
- [1.1. What Operating Systems Do](#11-what-operating-systems-do)
  - [1.1.3. Defining Operating System](#113-defining-operating-system)
- [1.2. Computer-System Organization](#12-computer-system-organization)
  - [1.2.1.1. Interrupt Vector Table](#1211-interrupt-vector-table)
  - [1.2.2. Storage Structure](#122-storage-structure)
- [1.3. Computer-System Architecture](#13-computer-system-architecture)
  - [1.3.2. Multiprocessor Systems](#132-multiprocessor-systems)
- [1.4. Operating-System Operations](#14-operating-system-operations)
  - [1.4.1. Multiprogramming and Multitasking](#141-multiprogramming-and-multitasking)
  - [1.4.3. Timer](#143-timer)
- [1.5. Resource Management](#15-resource-management)
  - [1.5.2. Memory Management](#152-memory-management)
  - [1.5.6. I/O System Management](#156-io-system-management)

# 1.1. What Operating Systems Do
## 1.1.3. Defining Operating System
> Operating system is a resource allocator and control program making efficient use of HW and managing execution of user programs.

> the operating system includes the always-
running kernel, middleware frameworks that ease application development
and provide features, and system programs that aid in managing the system
while it is running.

# 1.2. Computer-System Organization
## 1.2.1.1. Interrupt Vector Table
***Why to have an interrupt vector table?***
- Interrupts must be handled quickly, as they occur very frequently; That's why a table of pointers to interrupt routines can used instead to provide the necessary speed.
- The interrupt routines is called indirectly thought the table, with no intermediate routine needed.

***Why to have a table?***
- To reduce the need for a single interrupt handler to search all possible sources of interrupts to determine which one needs service.

***In practical, computers have more devices than they have address elements in the interrupt vector.***
- So this problem was solved using ***interrupt chaining***, in which each element in the interrupt vector points to the head of a list of interrupt handlers.
- So each element in the vector table points to a specific group type iof interrupts "interrupt handler responsible for a specific type of interrupts".
- When an interrupt is raised, the handlers on the corresponding list are called one by one, until one is found that can service the request.
- This structure is a compromise between the overhead of a huge interrupt table and the inefficiency of dispatching to a single interrupt handler.

Handling the interrupt priority level in important to enable the most urgent work to be done first, modern computers use a system of interrupt priorities; Because interrupts are used so heavily for time-sensitive processing, efficient interrupt handling is required for good system performance. 

***Let's describe what is it looks***
- The table of pointers is stored in low memory, the first hundred or so locations.
- This array, or interrupt vector, of addresses is then indexed by a unique number, given with the interrupt request, to provide address of the interrupt service routine for the interrupting device.

***How would it be in case there is no interrupt vector table?***
1. Single Interrupt Handler for All Devices
   - Without an interrupt vector table, the system would likely have a single interrupt handler responsible for all possible interrupts.
   - This single handler would need to identify the source of the interrupt to determine the appropriate action.
2. Identifying the Interrupt Source
    - Upon receiving an interrupt, the handler would start by checking each possible device to determine which one generated the interrupt.
    - This could involve polling each device in sequence, querying its status registers to see if it has raised an interrupt.
3. Handling the Interrupt
    - Once the source device is identified, the handler would execute the corresponding interrupt service routine (ISR) to address the interrupt.
    - After handling the interrupt, the system would return to its normal operation.

***Challenges of not having interrupt vector table***
  - Increased latency.
  - Inefficiency.
  - Scalability issues.
  - Complexity in ISR Management.

## 1.2.2. Storage Structure
- Was here stopped

# 1.3. Computer-System Architecture
## 1.3.2. Multiprocessor Systems
***Two types***
- Asymmetric multiprocessing (AMP)ّ
  - It will have a one main ***Master*** processor, which decide which jobs to be done by the ***salve*** processors.
  - Each processor is assigned to a specific task. A master processor controls the system; the other processors either look to the master for instruction or have predefined tasks. 
  - This scheme defines a master-slave relationship.
  - The master processor schedules and allocates work to the slave processors.
- Symmetric Multiprocessing (SMP)
  - All processors are peers, they perform all tasks, including the operating-system functions and user processes.

# 1.4. Operating-System Operations
## 1.4.1. Multiprogramming and Multitasking
***Multiprogramming*** needed for efficiency
- single job cannot keep CPU and I/O devices busy at all times.
- Multiprogramming organizes jobs (code and data) so CPU always has
one to execute.
- A subset of total jobs in system is kept in memory.
- One job selected and run via job scheduling.
- When it has to wait (for io e.g), OS switches to another job.

***Timesharing (multitasking)*** is logical extension in which CPU switches
job so frequently that users can interact with each job while it is running,
creating Interactive computing.
- Response time should be < 1 sec.
- Each user has at least one program executing in memory -> Process.
- if several jobs ready to run at the same time -> CPU scheduling.
- If processes don't fit in memory, swapping moves them in and out to run
- Virtual memory allows execution of processes not completely in memory.

## 1.4.3. Timer
***Timer is used to control the execution of the process***!
- make sure that each process does not exceed its allowed time limit and does not enter a void loop, by setting a counter to some value according to some privileged instructions.
- each clock cycle, timer starts to decrement the value of the counter till the counter reaches zero.
- Then an interrupt is issues to the operating system, executing an os code, to check if that process exceeds its resources or not, and can give it extra time or not.

# 1.5. Resource Management
## 1.5.2. Memory Management
process address space, set its start and assign it to a register called ***base register***, detect the process size and assign it to a register called ***limit register***.

## 1.5.6. I/O System Management
***I/O subsystem responsible for***
- Memory management of I/O including buffering (storing data temporarily while it is being transferred).
- Caching (storing parts of data in faster storage for performance).
- Spooling (the overlapping of output of one job with input of other jobs)



