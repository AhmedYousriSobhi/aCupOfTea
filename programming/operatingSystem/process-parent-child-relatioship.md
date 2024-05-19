# Operating System: Parent - child relationship

## Table of notes
- [Operating System: Parent - child relationship](#operating-system-parent---child-relationship)
  - [Table of notes](#table-of-notes)
  - [Zombie \& Orphan Diagram-flow](#zombie--orphan-diagram-flow)
  - [Zombie Processes](#zombie-processes)
  - [Orphan Processes](#orphan-processes)
  - [Key Differences](#key-differences)
  - [Why do child not die when parent dies?](#why-do-child-not-die-when-parent-dies)

## Zombie & Orphan Diagram-flow

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
                init adaption to the orhpan
                send wait() to terminate the orphan process entity.
                        
```

## Zombie Processes
1. *Definition* 
   - A zombie process is a process that has completed execution but still has an entry in the process table. This entry is maintained so the parent process can read the exit status of the child process using system calls like wait() or waitpid().
   - The process is "dead" in terms of execution but "alive" in terms of having an entry in the process table, hence the term "zombie".
2. **Creation of Zombie Processes**
   - When a child process terminates, it sends a SIGCHLD signal to its parent process. The parent is expected to call wait() to read the child's exit status.
   - If the parent process does not call wait(), the child process remains in the zombie state.
3. Code Example
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

## Orphan Processes
1. **Definition**
   - An orphan process is a process whose parent has terminated before it. When a process becomes an orphan, it is adopted by the *init* process (PID 1 in Unix-like systems), which becomes its new parent.
2. *Handling of Orphan Processes*
   - The init process periodically performs a wait() call to clean up orphaned processes, ensuring that they do not remain in the process table as zombies.
3. *Difference from Zombie Processes*
   - A zombie is a terminated process that has not yet been waited on by its parent.
   - An orphan is a live process whose parent has terminated.
   - If an orphan process terminates, init will call wait() on it, preventing it from becoming a zombie.
4. *Code example*
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

## Key Differences
- *Zombie Process*
  - Has terminated but remains in the process table until the parent calls wait().
  - Exists because the parent has not yet retrieved the child's exit status.
- *Orphan Process*
  - Is still running but its parent has terminated.
  - Adopted by init, which will call wait() when the orphan terminates, preventing it from becoming a zombie.

## Why do child not die when parent dies?
```
CAUSE:The reason that child processes do not die when their parent is killed is that the standard UNIX function fork() was not designed to behave in that way.  When a child process is created, the parent process calls the fork() function.  The fork() function returns 0 in the child and the process ID of the created child in the parent on success, -1 on failure.

It is the programmers responsibility to write the parent process in such a way to watch it's children, this is called a malice parent. It is a good programming technique to have the parent process monitor it's children behavior and wait on some sort of signal from the child. The wait() function is used to do this. It should be the child's responsibility to exit properly when finished.
```
- resource: [https://support.hpe.com/hpesc/public/docDisplay?docId=ns100.0.14972193.3027917en_us&docLocale=en_US](https://support.hpe.com/hpesc/public/docDisplay?docId=ns100.0.14972193.3027917en_us&docLocale=en_US)
