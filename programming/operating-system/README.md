# Operating System - Overview

> Operating system concepts relevant for developers and data scientists. By the end you'll have a feel for what happens underneath your code: memory, CPU cores, and the hardware itself.

You write `x = np.zeros(1000)` and move on. Underneath, the operating system finds memory, makes sure nobody can read what the last program left there, and decides which CPU core runs your process. You don't need to build an OS to benefit. Knowing the basics tells you why code is slow and where to look.

---

## The route

| Page | The question it answers |
|---|---|
| [computer-architectures-technologies](/programming/operating-system/computer-architectures-technologies.md) | What are instruction sets and processors, and how do they compare? |
| [memory-coalescing](/programming/operating-system/memory-coalescing.md) | Why does it matter how GPU threads read memory? |
| [memory-empty-zero-filling](/programming/operating-system/memory-empty-zero-filling.md) | Why is fresh memory filled with zeros? |
| [process-cpu-affinity](/programming/operating-system/process-cpu-affinity.md) | How do you control which CPU a process runs on? |

---

## Who this is for

Developers and data scientists who are curious about the machine under their code, and want to optimize performance and resource use.

---

## Contents

| File | Description |
|------|-------------|
| [computer-architectures-technologies](/programming/operating-system/computer-architectures-technologies.md) | Computer architectures and technologies |
| [memory-coalescing](/programming/operating-system/memory-coalescing.md) | Memory coalescing techniques |
| [memory-empty-zero-filling](/programming/operating-system/memory-empty-zero-filling.md) | Memory zero-filling concepts |
| [process-cpu-affinity](/programming/operating-system/process-cpu-affinity.md) | CPU affinity for process scheduling |

Understanding OS fundamentals helps optimize code performance and resource utilization.
