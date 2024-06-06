# Operating Systems - Synchronization Tools

Chapter 6 Synchronization Tools, from Operating System concepts 10th edition reference

# Mystic Map
- [Operating Systems - Synchronization Tools](#operating-systems---synchronization-tools)
- [Mystic Map](#mystic-map)
- [6.1. Background](#61-background)
- [6.2. The Critical-Section Problem](#62-the-critical-section-problem)
  - [Storyline](#storyline)

# 6.1. Background
***Race Condition***
- The situation where several processes access - and manipulate shared data concurrently. The final value of the shared data depends upon which finished last.
- To guard against the race condition above, we need to ensure that only one process at a time can be manipulating the variable count. To make such a guarantee, we require that the processes be ***synchronized*** in some way.

# 6.2. The Critical-Section Problem
***Critical Section Problem***
- In concurrent programming, the critical section problem arises when multiple processes or threads need to access shared resources, such as memory or files, concurrently. The goal is to ensure that only one process can enter its critical section at a time, thereby preventing race conditions and ensuring data consistency.

Could be solved using:
- Hardware instruction solution.
- Software solution: {Semaphore, Monitor}.

6.6. Semaphores
In operating systems (OS), a semaphore is a synchronization primitive used to control access to a common resource by multiple processes or threads. 

It helps prevent race conditions and ensures safe concurrent access to shared resources. 

There are two main types of semaphores: counting semaphores and binary semaphores.

**Types of Semaphores**

***Counting Semaphore***
- Value: Can range over an unrestricted domain.
- Use Case: Useful for managing a resource with multiple instances, such as a pool of database connections or a limited number of identical printers.
- Operations:
    - P (wait, decrement): Decreases the semaphore's value. If the value becomes negative, the process executing the P operation is blocked until the value is greater than or equal to zero.
    - V (signal, increment): Increases the semaphore's value. If there are any blocked processes, one of them is unblocked.

***Binary Semaphore (Mutex)***
- Value: Can only be 0 or 1.
- Use Case: Typically used to manage access to a single resource or a critical section, ensuring mutual exclusion.
- Operations:
    - P (wait, lock): If the semaphore's value is 1, it is set to 0, allowing the process to enter the critical section. If the value is 0, the process is blocked until the value becomes 1.
    - V (signal, unlock): Sets the semaphore's value to 1, releasing the lock and potentially unblocking a waiting process.

## Storyline
Imagine a bustling medieval kingdom where many skilled artisans work in a grand castle, creating beautiful tapestries, forging weapons, and preparing grand feasts for the royal family. However, there is a critical problem: the castle has only one magnificent loom that can weave the finest cloth, one powerful forge that can create the strongest swords, and one grand kitchen for cooking the royal feasts. These resources must be shared among many artisans, blacksmiths, and cooks, but they must never be used by more than one person at a time to ensure the highest quality of work.

**The Concept of Semaphores**

In this medieval setting, let's introduce the concept of semaphores as magical scrolls, given by the wise royal advisor, to manage access to these precious resources. These scrolls help the artisans coordinate and avoid conflicts, much like how semaphores work in modern operating systems.

**Types of Semaphores**

1. ***Counting Semaphore***
    - Analogy: Imagine there are multiple anvils in the forge, but only a certain number are available at any given time.
    - Scroll Function: The counting scroll keeps track of how many anvils are free. If an artisan wants to use an anvil, they must check the scroll. If the scroll shows that anvils are available, they can proceed. If not, they must wait until an anvil is freed.
2. ***Binary Semaphore (Mutex)***
    - Analogy: The loom is a single-use resource; only one weaver can use it at a time.
    - Scroll Function: The binary scroll (mutex) ensures that only one weaver can use the loom. If the loom is in use, the scroll prevents any other weaver from accessing it until it is free again.

**How It Works**

***The Loom (Binary Semaphore)***
1. Waiting to Weave (P operation):
    - Weaver A approaches the loom. They must first consult the binary scroll.
    - If the scroll says the loom is free (scroll = 1), Weaver A sets the scroll to indicate the loom is now in use (scroll = 0) and starts weaving.
    - If the scroll says the loom is occupied (scroll = 0), Weaver A must wait until it becomes free.

2. Finished Weaving (V operation):
    - After completing the work, Weaver A sets the scroll to indicate the loom is free (scroll = 1), allowing other weavers to use it.

***The Forge (Counting Semaphore)***
1. Waiting to Forge (P operation):
    - Blacksmith B wants to use an anvil. They consult the counting scroll, which shows the number of free anvils.
    - If an anvil is available (scroll > 0), Blacksmith B decrements the scroll (scroll--) and starts working.
    - If no anvils are free (scroll = 0), Blacksmith B waits until an anvil becomes available.

2. Finished Forging (V operation):
    - After finishing, Blacksmith B increments the scroll (scroll++), indicating that one more anvil is now available.