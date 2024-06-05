# Operating Systems - Threads and Concurrency

Chapter 4 Threads and Concurrency, from Operating System concepts 10th edition reference

# Mystic Map
- [Operating Systems - Threads and Concurrency](#operating-systems---threads-and-concurrency)
- [Mystic Map](#mystic-map)
- [4.1. OverView](#41-overview)
  - [4.1.1. Process-Overhead](#411-process-overhead)
- [4.2. Multicore Programming](#42-multicore-programming)
  - [4.2.1. AMDAHL'S LAW](#421-amdahls-law)
- [4.4. Thread Libraries](#44-thread-libraries)
  - [4.4.1 Pthreads - Sharing-Data - Java Without Notion of Global Data!](#441-pthreads---sharing-data---java-without-notion-of-global-data)
- [4.5. Implicit-Threading](#45-implicit-threading)
- [4.6. Threading Issues](#46-threading-issues)
  - [4.6.5. Scheduler Activations](#465-scheduler-activations)
    - [Lightweight Process - LWP](#lightweight-process---lwp)

# 4.1. OverView
## 4.1.1. Process-Overhead

```
If the new process will perform the same tasks as the existing process, why incur all that overhead?

It is generally more efficient to use one process that contains multiple threads.
```
- Operating systems concepts reference. Chapter 4 - threads and concurrency.

This point is due to the significant difference in how operating systems handle processes and threads!!

Let's explain this concept..

**Process Creation Overhead**
- ***Memory Allocation***
  - Creating a new process requires the OS to allocate a seperate address space for the process. 
  - This includes copying the entire memory space of the parent process if the *fork()* system call is used.
- ***Resources Allocation***
  - Each process gets its own set of resources, such as file descriptors, memory mappings, and I/O buffers.
  - Managing these resources involves significant overhead.
- ***Context Switching***
  - Switching between processes involves saving and loading the state of the CPU registers, memory mappings, and other process-specific information, which is time-consuming.

**Thread Creation Overhead**
- ***Shared Memory Space***
  - Threads within the same process share the same address space.
  - This eliminates the need for the OS to allocate and manage separate memory spaces for each thread.
- ***Lightweight Resource Allocation***
  - Threads share resources such as file descriptors and memory reducing the overhead associated with resource allocation.
- ***Faster Context Switching***
  - Switching between threads of the same process is faster because it involves saving and loading only the thread-specific information (like the PC, registers, stack) without changing the memory mappings.

**Example: Web Server**
- ***Using Multiple Processes***: each client request is handled by creating a new process.
    ```c
    #include <stdio.h>
    #include <stdlib.h>
    #include <unistd.h>

    void handle_request() {
        // Simulate handling a request
        printf("Handling request in process %d\n", getpid());
        sleep(2);
    }

    int main() {
        while (1) {
            pid_t pid = fork();
            if (pid == 0) {
                // Child process
                handle_request();
                exit(0);
            } else if (pid > 0) {
                // Parent process
                wait(NULL); // Wait for the child process to finish
            } else {
                perror("fork");
                exit(1);
            }
        }
        return 0;
    }
    ```
- ***Using Multiple Threads***: each client request is handled by creating a new thread.
    ```c
    #include <stdio.h>
    #include <stdlib.h>
    #include <pthread.h>
    #include <unistd.h>

    void *handle_request(void *arg) {
        // Simulate handling a request
        printf("Handling request in thread %ld\n", pthread_self());
        sleep(2);
        return NULL;
    }

    int main() {
        while (1) {
            pthread_t thread;
            if (pthread_create(&thread, NULL, handle_request, NULL) != 0) {
                perror("pthread_create");
                exit(1);
            }
            pthread_detach(thread); // Detach thread to handle request independently
        }
        return 0;
    }
    ```

To sum up, Multithreading is often preferred in applications that requires handling numerous concurrent operations.

# 4.2. Multicore Programming
## 4.2.1. AMDAHL'S LAW

Amdahl's Law is a principle used to find the maximum improvement possible when only part of a system is improved. It is particularly relevant in parallel computing and is used to predict the theoretical speedup in latency of the execution of a task when the task is executed on a system with multiple processors.

**Amdahl's Law**
- The law is named after computer scientist Gene Amdahl, who formulated it. Amdahl's Law can be expressed mathematically as:
    ```
    S=1/[(1−P)+P/S]
    ```
    - Where:
        - S is the speedup of the execution of the task.
        - P is the proportion of the program that can be made parallel.
        - 1−P is the proportion of the program that remains serial.
        - N is the number of processors.

**Key Points**
1. ***Serial Portion Limits Speedup***
   - The speedup of a program is limited by the portion of the program that cannot be parallelized. Even an infinite number of processors, the maximum speedup is determined by the serial portion.
   - If a program is 90% parallelize and 10% serial, the maximum speedup, regarding of the number of processors is 10x.

2. ***Diminishing Returns***
    - As the number of processors increases, the impact of adding additional processors decreases if a significant portion of the program is serial.
    - For example, if 50% of a task is serial, the theoretical maximum speedup is 2x, no matter how many processors are used.

**Example Calculation**
- Assume we have a program where 70% of the work can be parallelized (P=0.7), and we use 4 processors (N=4):
- S ~= 2.11
- So the maximum speedup with 4 processors is approximately 2.11 times faster than the single processor execution.

**Implications of Amdahl's Law**
1. ***Optimization Focus***
        - Efforts to optimize should focus on the serial part of the program to improve overall performance effectively.
2. ***Parallelization Limits***
        - It is crucial to identify the portion of a program that can be parallelized to estimate the benefits of using multiple processors.
3. ***Scalability***
        - Amdahl's Law highlights the scalability limitations of parallel computing. As parallelization increases, the serial portion becomes the bottleneck.

# 4.4. Thread Libraries
## 4.4.1 Pthreads - Sharing-Data - Java Without Notion of Global Data!
From reference Operating System Concepts 10th edition, chapter 4.4 - thread libraries:
```
For POSIX and Windows threading, any data declared globally—that is,
declared outside of any function—are shared among all threads belonging to
the same process. Because Java has no equivalent notion of global data, access
to shared data must be explicitly arranged between threads
```

Let's first get how Java handles data sharing among threads compared to language that support global data!

**Global Data vs Shared Data in Java**
1. ***Global Data in other language***
    - In languages like C or C++, you can declare variables as global, which means they are accessible from any function of part of the program.
    - These global variables can be shared among different threads without any special arrangement.
2. ***Java's Approach***
    - Java does not support global variables in the same way. Instead, all data in java is encapsulated within classes. Variables that need to be shared among threads must be explicitly defined as field within a class.
    - To share data between threads, you need to make fields accessible to all threads that need to use them. This typically involves passing references to shared objects or using static fields within classes. 

- Because multiple threads can access shared data simultaneously, explicit synchronization is necessary to prevent race conditions and ensure data consistency. 

**Java Code Examples for Explicit Arrangement for Shared Data**
1. ***Instance variables***: define instance variables in an object and pass references to this object to all threads that need to share the data.
    ```java
    public class SharedData {
        public int counter = 0;
    }

    public class MyThread extends Thread {
        private SharedData sharedData;

        public MyThread(SharedData sharedData) {
            this.sharedData = sharedData;
        }

        public void run() {
            // Access and modify shared data
            synchronized(sharedData) {
                sharedData.counter++;
            }
        }
    }

    public class Main {
        public static void main(String[] args) {
            SharedData sharedData = new SharedData();
            Thread t1 = new MyThread(sharedData);
            Thread t2 = new MyThread(sharedData);
            t1.start();
            t2.start();
        }
    }
    ```
    - In this example, *SharedData* is an object with a shared variable *counter*. Both threads *t1* & *t2* can access and modify *counter*.
2. ***Static Variables***: define a static variable, which belong to the class rather than any particular instance.
    ```java
        public class SharedClass {
        public static int counter = 0;
    }

    public class MyThread extends Thread {
        public void run() {
            // Access and modify shared data
            synchronized(SharedClass.class) {
                SharedClass.counter++;
            }
        }
    }

    public class Main {
        public static void main(String[] args) {
            Thread t1 = new MyThread();
            Thread t2 = new MyThread();
            t1.start();
            t2.start();
        }
    }
    ```
    - *counter* is a static variable in *SharedClass*, shared by all instance of *MyThread*.
    - This code might suffer from an issue, that we need to ensure that changes to *counter* are visible to all threads immediately, this suggest adding the *volatile* keyword to *public static volatile int counter = 0;*

# 4.5. Implicit-Threading

You don't need to micromanage every task my dear king!!

**The Tale of Implicit Threading**

Imagine a bustling kingdom where the King has a monumental task: building a grand castle. The King, wise and efficient, wants to ensure the castle is built quickly without having to micromanage every worker. In this kingdom, there are two approaches to getting the job done: explicit and implicit management.

***Explicit Management (Manual Work Allocation)***

In the explicit management approach, the King personally assigns tasks to each worker. He tells each builder which stone to place, which wall to erect, and when to take a break. This requires the King to constantly supervise and allocate tasks, ensuring each worker knows exactly what to do and when. This method, while effective, takes up a lot of the King's time and energy, which could be better spent on other royal duties.

***Implicit Management (Automatic Work Allocation)***

In the implicit management approach, the King employs a wise and magical overseer named Thready. Thready's job is to oversee the workers and automatically allocate tasks based on their skills and the current needs of the project. Thready ensures that workers are always busy with the most appropriate tasks without needing constant instructions from the King. This way, the King can focus on planning the grand design of the castle rather than managing the minutiae of the construction.

**What is Implicit Threading?**

Implicit threading is like the magical overseer Thready. It refers to the technique where the responsibility of managing and distributing tasks among workers (threads) is handled by the system or library itself, rather than being explicitly coded by the programmer. This makes the task of parallel programming easier and more efficient.

**Examples of Implicit Threading**
1. ***Thread Pools***
    - Think of a thread pool as a group of workers standing by, ready to take on tasks as they come. Instead of creating and destroying threads for each new task, which is costly and time-consuming, a thread pool reuses existing threads. The King doesn’t need to hire and fire workers for each stone to be laid; Thready assigns tasks to the available workers in the pool.
2. ***OpenMP (Open Multi-Processing)***
    - OpenMP is like a set of magical spells that can be cast on portions of code to automatically parallelize them. When the King writes down the plan for building a wall, he can use these spells to tell Thready to divide the work among the workers without specifying exactly how. This makes it easier to add parallelism to the construction plans without detailed instructions.
3. ***Grand Central Dispatch (GCD)***
    - GCD is another form of implicit threading used in Apple’s ecosystem. Imagine Thready having a magical book where tasks are written down, and workers can pick them up as they become available. This system dynamically manages the tasks and distributes them among workers, optimizing for performance without the King’s constant intervention.

**Benefits of Implicit Threading**
- Efficiency: Just like how Thready efficiently manages the workers, implicit threading optimizes the use of system resources, leading to better performance and reduced overhead.
- Simplicity: The King doesn’t have to worry about the nitty-gritty details of task management. Similarly, programmers don’t need to write complex code to manage threads explicitly.
- Scalability: As the number of tasks increases, Thready can handle them smoothly without overwhelming the King. Implicit threading mechanisms can scale to handle more threads and tasks as needed.

# 4.6. Threading Issues
## 4.6.5. Scheduler Activations
### Lightweight Process - LWP
- Intermediate data structure between user thread and kernel threads.
- This data structure appears to be a Virtual processor, on which a process can schedule user thread to run. 
