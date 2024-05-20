# Operating Systems - The init Process

## Table of notes
- [Operating Systems - The init Process](#operating-systems---the-init-process)
  - [Table of notes](#table-of-notes)
  - [Note - The init process](#note---the-init-process)
  - [Modern Init Systems](#modern-init-systems)

## Note - The init process
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

## Modern Init Systems
In modern Unix-like systems, the traditional init has been replaced or supplemented by more advanced init systems, such as:
1. ***Systemd***
        - A modern init system and system manager that provides aggressive parallelization capabilities, on-demand starting of daemons, and dependency-based service control logic.
        - It uses unit files to define services and targets (analogous to runlevels).
2. ***Upstart***
        - An event-based init system designed to start services asynchronously and to respond to events (e.g., hardware availability, file system mounting).
        - Developed by Canonical for Ubuntu.
3. ***OpenRC***
        - A dependency-based init system used by Gentoo Linux, which works with the traditional init and provides advanced service management features.