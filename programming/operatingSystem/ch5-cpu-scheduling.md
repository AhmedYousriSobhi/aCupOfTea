# Operating Systems - CPU Scheduling

Chapter 5 CPU Scheduling, from Operating System concepts 10th edition reference

# Mystic Map
- [Operating Systems - CPU Scheduling](#operating-systems---cpu-scheduling)
- [Mystic Map](#mystic-map)
- [5.1. Basic Concepts](#51-basic-concepts)
  - [5.1.3. Preemptive and Nonpreemptive Scheduling](#513-preemptive-and-nonpreemptive-scheduling)

# 5.1. Basic Concepts
## 5.1.3. Preemptive and Nonpreemptive Scheduling
Preemptive scheduling means that the scheduler (like an OS kernel) can interrupt the running tasks at any time, schedule something else and resume them later.

Non-preemptive scheduling requires the tasks to cooperate by yielding control back to the scheduler in reasonable intervals (even when they are not done with their work yet).

