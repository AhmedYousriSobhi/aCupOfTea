# Operating System - Process - fork & exec

## Table of notes
- [Operating System - Process - fork \& exec](#operating-system---process---fork--exec)
  - [Table of notes](#table-of-notes)
  - [Forking a Process](#forking-a-process)
  - [Executing a New Program](#executing-a-new-program)
  - [Process Flow Explanation](#process-flow-explanation)

## Forking a Process
1. ***Forking (fork())***
    - The fork() system call is used to create a new process by duplicating the calling process. The new process is called the child process, and the original process is called the parent process.
    - When fork() is called, the operating system creates a new process with a separate address space that is a copy of the parent's address space. This includes the code, data, and heap segments, as well as file descriptors.
    - The fork() call returns twice: once in the parent process and once in the child process.
        - In the parent process, fork() returns the process ID (PID) of the child process.
        - In the child process, fork() returns 0.

    ```c
    #include <stdio.h>
    #include <unistd.h>

    int main() {
        pid_t pid = fork();

        if (pid == -1) {
            // Fork failed
            perror("fork");
            return 1;
        }

        if (pid == 0) {
            // This is the child process
            printf("This is the child process.\n");
        } else {
            // This is the parent process
            printf("This is the parent process. Child PID: %d\n", pid);
        }

        return 0;
    }
    ```

## Executing a New Program
2. ***Executing (exec())***
    - The exec() family of functions (e.g., execl(), execp(), execve()) is used to replace the current process image with a new program. This means the process keeps its PID, but its memory space (code, data, stack, and heap) is replaced by the new program's memory space.
    - After a successful exec() call, the new program starts executing, and the original code of the process is no longer present in memory. The process does not return to the code that called exec() unless exec() fails.
    ```c
    #include <stdio.h>
    #include <unistd.h>

    int main() {
        pid_t pid = fork();

        if (pid == -1) {
            // Fork failed
            perror("fork");
            return 1;
        }

        if (pid == 0) {
            // This is the child process
            printf("This is the child process. Executing new program...\n");
            execl("/bin/ls", "ls", "-l", (char *)NULL);
            // If exec() is successful, this line will not be executed
            perror("execl");
        } else {
            // This is the parent process
            printf("This is the parent process. Child PID: %d\n", pid);
        }

        return 0;
    }
    ``` 

## Process Flow Explanation
1. ***Initial Process***
   - The parent process is running, and it calls fork().
2. ***Forking***
    - The fork() system call is executed, creating a child process.
    - The child process is a copy of the parent process, with its own memory space but identical content initially.
3. ***Post-Fork***
    - Both parent and child processes continue executing from the point where fork() was called.
    - They can be distinguished by the return value of fork():
        - Parent gets the child's PID.
        - Child gets 0.
4. ***Executing New Program***
    - The child process calls an exec() function (e.g., execl()).
    - exec() replaces the child’s process memory with a new program (in this case, /bin/ls).
    - The new program starts executing immediately from its entry point.
    - The child process retains its original PID but now runs the new program.