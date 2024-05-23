# Operating Systems - AMDAHL'S LAW

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