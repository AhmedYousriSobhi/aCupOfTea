# Operating Systems - Processes

Chapter 3 Processes, from Operating System concepts 10th edition reference

# Mystic Map
- [Operating Systems - Processes](#operating-systems---processes)
- [Mystic Map](#mystic-map)
- [3.2. Process Scheduling](#32-process-scheduling)
  - [3.2.2. The-init-Process](#322-the-init-process)
    - [Note - The init process](#note---the-init-process)
    - [Modern Init Systems](#modern-init-systems)
  - [3.2.2. Parent-child-relationship](#322-parent-child-relationship)
    - [Zombie \& Orphan Diagram-flow](#zombie--orphan-diagram-flow)
    - [Zombie Processes](#zombie-processes)
    - [Orphan Processes](#orphan-processes)
    - [Key Differences](#key-differences)
    - [Why do child not die when parent dies?](#why-do-child-not-die-when-parent-dies)
    - [Resource](#resource)
- [3.3. Operation on Processes](#33-operation-on-processes)
  - [3.3.1. fork-\&-exec](#331-fork--exec)
    - [Forking a Process](#forking-a-process)
    - [Executing a New Program](#executing-a-new-program)
    - [Process Flow Explanation](#process-flow-explanation)

# 3.2. Process Scheduling
## 3.2.2. The-init-Process
### Note - The init process
In Unix and Unix-like operating systems, it is the first process that the kernel starts during the booting of the system, and remains running until the system is shut down.

1. ***Process ID***
   - The init process always has a process ID (PID) of 1. This unique identifier signifies its special role in the system.
2. ***Booting***
   - When the Unix kernel finishes initializing and setting up the system's hardware and memory, it starts the init process.
   - The kernel execute the init program, which is located in */sbin/init*, */etc/init*, or other locations depending on the Unix variant.
3. ***System Initialization***
   - The init process reads its configuration file, typically '/etc/inittab' in the traditional Unix systems, to determine how the system should be initialized.
   - It performs a series of tasks, such as setting the system's hostname, initializing the system logs, and configuring the network.
4. ***Running Services***
   - init is responsible for starting and managing system services and daemons. These include essential services like network services, login prompts (getty), and scheduled tasks (cron).
   - It runs scripts found in directories like /etc/rc.d, /etc/init.d, or /etc/systemd/system (depending on the init system) to start services in a specified sequence.
5. ***Managing Runlevels***
    - Traditional init systems use runlevels to define the state of the machine and the set of services that should be running. Common runlevels include:
        - 0: Halt (shuts down the system)
        - 1: Single-user mode (maintenance mode)
        - 2-5: Multi-user modes with various levels of service
        - 6: Reboot
    - The init process can switch between runlevels based on system needs or user commands.
6. ***Parent of Orphaned Processes***
    - If a process's parent terminates before the child, the child becomes an orphan. The init process adopts orphaned processes, ensuring they are properly managed and cleaned up when they terminate.

### Modern Init Systems
In modern Unix-like systems, the traditional init has been replaced or supplemented by more advanced init systems, such as:
1. ***Systemd***
        - A modern init system and system manager that provides aggressive parallelization capabilities, on-demand starting of daemons, and dependency-based service control logic.
        - It uses unit files to define services and targets (analogous to runlevels).
2. ***Upstart***
        - An event-based init system designed to start services asynchronously and to respond to events (e.g., hardware availability, file system mounting).
        - Developed by Canonical for Ubuntu.
3. ***OpenRC***
        - A dependency-based init system used by Gentoo Linux, which works with the traditional init and provides advanced service management features.

## 3.2.2. Parent-child-relationship
### Zombie & Orphan Diagram-flow

```
process -> forking -> Child
                        |
    |                 execution
    execute             |

    |            |      
    |        termination
                |  
    |          Zombie    ---> if the parent did not response to the child signal (either parent terminated or busy) 
                |        --> the process will be zombie forever.                                      
                |
                send SIGCHILd
                |
                parent response to the signal 
                using wait()
                |
                zombie terminated successfully


process -> forking -> Child
                        |
    |                 execution
    execute             |

    |                   |      
termination
                        |  
                      orphan                                        
                        |
                termination? where is the parent?
                        |
                init adaption to the orphan
                send wait() to terminate the orphan process entity.
                        
```
- A family problem, as you are a father:
  - If you neglect your child, then it will become zombie.
  - If you left the house, then your child will become orphan.

### Zombie Processes
1. ***Definition*** 
   - A zombie process is a process that has completed execution but still has an entry in the process table. This entry is maintained so the parent process can read the exit status of the child process using system calls like wait() or waitpid().
   - The process is "dead" in terms of execution but "alive" in terms of having an entry in the process table, hence the term "zombie".
2. ***Creation of Zombie Processes***
   - When a child process terminates, it sends a SIGCHLD signal to its parent process. The parent is expected to call wait() to read the child's exit status.
   - If the parent process does not call wait(), the child process remains in the zombie state.
3. ***Code Example***
    ```c
    #include <sys/types.h>
    #include <unistd.h>
    #include <stdio.h>
    #include <stdlib.h>

    int main() {
        pid_t pid = fork();

        if (pid > 0) {
            // Parent process
            sleep(10); // Sleep to allow child to enter zombie state
        } else if (pid == 0) {
            // Child process
            printf("Child process terminating\n");
            exit(0); // Child exits, becomes zombie until parent calls wait()
        } else {
            perror("fork");
            exit(EXIT_FAILURE);
        }

        return 0;
    }
    ```
    - The child process will terminate and become a zombie until the parent process calls wait() or exits.

### Orphan Processes
1. ***Definition***
   - An orphan process is a process whose parent has terminated before it. When a process becomes an orphan, it is adopted by the *init* process (PID 1 in Unix-like systems), which becomes its new parent.
2. ***Handling of Orphan Processes***
   - The init process periodically performs a wait() call to clean up orphaned processes, ensuring that they do not remain in the process table as zombies.
3. ***Difference from Zombie Processes***
   - A zombie is a terminated process that has not yet been waited on by its parent.
   - An orphan is a live process whose parent has terminated.
   - If an orphan process terminates, init will call wait() on it, preventing it from becoming a zombie.
4. ***Code example***
    ```c
    #include <sys/types.h>
    #include <unistd.h>
    #include <stdio.h>
    #include <stdlib.h>

    int main() {
        pid_t pid = fork();

        if (pid > 0) {
            // Parent process
            printf("Parent process terminating\n");
            exit(0); // Parent exits
        } else if (pid == 0) {
            // Child process
            sleep(10); // Sleep to ensure parent terminates first
            printf("Child process terminating\n");
            exit(0);
        } else {
            perror("fork");
            exit(EXIT_FAILURE);
        }

        return 0;
    }
    ```
        - The child process becomes an orphan when the parent terminates, the child process is then adopted by 'init'.

### Key Differences
- ***Zombie Process***
  - Has terminated but remains in the process table until the parent calls wait().
  - Exists because the parent has not yet retrieved the child's exit status.
  - If no parent waiting (did not invoke wait()) process is a zombie. 
- ***Orphan Process***
  - Is still running but its parent has terminated.
  - Adopted by init, which will call wait() when the orphan terminates, preventing it from becoming a zombie.
  - If parent terminated without invoking wait(), process is an orphan.

### Why do child not die when parent dies?
```
CAUSE:The reason that child processes do not die when their parent is killed is that the standard UNIX function fork() was not designed to behave in that way.  
When a child process is created, the parent process calls the fork() function.
The fork() function returns 0 in the child and the process ID of the created child in the parent on success, -1 on failure.

It is the programmers responsibility to write the parent process in such a way to watch it's children, this is called a malice parent.
It is a good programming technique to have the parent process monitor it's children behavior and wait on some sort of signal from the child. The wait() function is used to do this.
It should be the child's responsibility to exit properly when finished.
```
### Resource
- hpe-Explain why a child process will not automatically die when the parent process is killed or terminates.[https://support.hpe.com/hpesc/public/docDisplay?docId=ns100.0.14972193.3027917en_us&docLocale=en_US](https://support.hpe.com/hpesc/public/docDisplay?docId=ns100.0.14972193.3027917en_us&docLocale=en_US)

# 3.3. Operation on Processes
## 3.3.1. fork-&-exec
### Forking a Process
1. ***Forking (fork())***
    - The fork() system call is used to create a new process by duplicating the calling process. The new process is called the child process, and the original process is called the parent process.
    - When fork() is called, the operating system creates a new process with a separate address space that is a copy of the parent's address space. This includes the code, data, and heap segments, as well as file descriptors.
        ![process fork](https://i.postimg.cc/65qFtZ4C/Whats-App-Image-2024-06-05-at-20-46-47.jpg)
        - Note in thread fork: only stack is duplicated.
            ![thread fork](https://i.postimg.cc/ZnG8GXy7/Whats-App-Image-2024-06-05-at-20-46-57.jpg)
        - Note: in modern OS, they use COW "Copy on Write", so they create reference to the memory instead of duplication, and only the copy happens when we want to write on the memory.
    - The fork() call returns twice: once in the parent process and once in the child process.
        - In the parent process, fork() returns the process ID (PID) of the child process.
        - In the child process, fork() returns 0.

    - Code Example
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

### Executing a New Program
2. ***Executing (exec())***
    - The exec() family of functions (e.g., execl(), execp(), execve()) is used to replace the current process image with a new program. This means the process keeps its PID, but its memory space (code, data, stack, and heap) is replaced by the new program's memory space.
    - After a successful exec() call, the new program starts executing, and the original code of the process is no longer present in memory. The process does not return to the code that called exec() unless exec() fails.
    - Code Example
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

### Process Flow Explanation
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