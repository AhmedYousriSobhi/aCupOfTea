# Operating Systems - Virtual Memory

Chapter 10 Virtual Memory, from Operating System concepts 10th edition reference

# Mystic Map
- [Operating Systems - Virtual Memory](#operating-systems---virtual-memory)
- [Mystic Map](#mystic-map)
- [10.4. Page Replacement](#104-page-replacement)
  - [10.4.2. FIFI Page Replacement](#1042-fifi-page-replacement)
    - [Belady's Anomaly](#beladys-anomaly)

# 10.4. Page Replacement
## 10.4.2. FIFI Page Replacement
### Belady's Anomaly
Belady's anomaly is a phenomenon in computer science, specifically in the context of page replacement algorithms used in virtual memory systems. It describes a counterintuitive situation where increasing the number of page frames (memory) allocated to a process can actually result in an increase in the number of page faults, rather than the expected decrease. This anomaly is most famously associated with the FIFO (First-In-First-Out) page replacement algorithm.

Under FIFO, pages are replaced in the order they were brought into memory, and adding more frames does not necessarily reduce the number of page faults because it does not consider the frequency or recency of page accesses.

From the reference:
```
for some page-replacement algorithms, the page-fault rate may increase as the number of allocated frames increases. 
We would expect that giving more memory to a process would improve its performance. 
In some early research, investigators noticed that this assumption was not always true. 
Belady’s anomaly was discovered as a result.
```
![Page-fault curve for FIFO](https://i.postimg.cc/3Jh8NF98/Screenshot-from-2024-06-07-21-22-26.png)
