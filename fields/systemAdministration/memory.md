# System Administration - Memory

## Table of Contents
- [System Administration - Memory](#system-administration---memory)
  - [Table of Contents](#table-of-contents)
  - [1- Memory Issues in Linux Application](#1--memory-issues-in-linux-application)
    - [1.1- Segmentation Faults (segfaults)](#11--segmentation-faults-segfaults)
    - [1.2- Memory Leaks](#12--memory-leaks)
    - [1.3- Buffer Overflow](#13--buffer-overflow)
  - [2- Memory Debugging Tools](#2--memory-debugging-tools)
    - [2.1- What is Static Analysis?](#21--what-is-static-analysis)
    - [2.2- Static Analysis Tools (Clang Analyzer)](#22--static-analysis-tools-clang-analyzer)

## 1- Memory Issues in Linux Application
- Common memory issue:
    1. Segmentation faults (segfaults).
    2. Memory leaks.
    3. Buffer overflow.
    4. Use after free (dangling pointer dereference).

### 1.1- Segmentation Faults (segfaults)
- Causes Can happen when a program tries to access : 
  - A non-existing virtual memory segment.
  - An existing virtual memory segment in a different way as defined by its attribute.
  - Execute data in non-executable segment.
  - Write data in read only segment.

- As a consequence; the kernel delivers the *SIGSEGV* signal to the offending process, and it usually results in the termination of the process.
- Code example:
    ```c
    int *example_ptr = NULL;

    *example_ptr = 5; // Trying to store 5 in invalid memory location.
    ```

### 1.2- Memory Leaks
- Memory leaks is a condition that occurs when a program fails to release memory that is no longer needed.
- memory leaks gradually consume available memory resources over time causing performance degradation and eventual program crashes.
- Common causes:
    - Not deallocating dynamically allocated memory.
    - Losing references to memory blocks.
    - Failing to release resources properly.
- Code example:
    ```c
    int main() {
        // Allocate memory for an integer array
        int *arr = (int *)malloc(5 * sizeof(int));
        // Initialize the array
        for (int i = 0; i<5; i++){
            arr[i] = i;
        }
        // No explicit free() call to deallocate the memory.
        return 0;
    }
    ```

### 1.3- Buffer Overflow
- Buffer overflow is a type of software vulnerability that occurs when a program writes more data to a buffer (a temporary storage area) than it can hold, causing the excess data to overflow into adjacent memory locations.
- Two common types of buffer overflows are [*Stack-based*, *heap-based*], depending on where the buffer is located in memory.
- It can lead to memory corruption, program crashes, or unauthorized access to a system, making it a significant security risk.

- Code Example:
    ```c
    // Create an integer array with a size of 5 elements
    int buffer[5];

    // Writing to the 6th location of buffer will result in a buffer overflow.
    buffer[5] = 15;

    // Print the content of buffer[5]
    print("Buffer[%d]: %d\n", 5, buffer[5])
    ```

## 2- Memory Debugging Tools
### 2.1- What is Static Analysis?
- Static analysis is a method of debugging by examining source code before a program is run. 
- This is especially useful in system-level programming (like C/C++ under Linux) where memory management is manual and prone to errors.

### 2.2- Static Analysis Tools (Clang Analyzer)
- A tool built into the Clang/LLVM compiler suite.
- It analyzes C, C++, and Objective-C programs.
- It focuses on finding bugs without running the code, which makes it very helpful in early development and CI/CD pipelines.