# Operating Systems - Process - Thread Overhead

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