# Concepts

## Table of Contents
- [Concepts](#concepts)
  - [Table of Contents](#table-of-contents)
  - [CPLD "Complex Programmable Logic Device"](#cpld-complex-programmable-logic-device)
  - [PCI -- and Why It's Called a "Link"?](#pci----and-why-its-called-a-link)
    - [That's why people call it a **link**](#thats-why-people-call-it-a-link)

## CPLD "Complex Programmable Logic Device"
A CPLD is a small, reconfigurable hardware chip used on motherboards or server boards to control low-level logic (e.g., power sequencing, board-level signals).

**What it actually does?**
- When you update firmware on server hardware (e.g., BMC, BIOS, and CPLD), you’re updating different layers:
    - BIOS → Boot-time firmware configuring CPU, memory, PCIe, etc.
    - BMC → Baseboard Management Controller firmware providing remote management (IPMI/Redfish, power on/off, monitoring sensors).
    - CPLD → Hardware logic that controls things like:
        - Power routing and sequencing
        - Reset logic
        - Board signals that must react faster or more deterministically than software.

> Note: CPLD code contains logic configuration like a simplified FPGA.
> 
> Note: Updating CPLD requires shutting down the target server to be updated first.

**A Useful Analogy:**
- **BOIS**: Operating System of the motherboard.
- **BMC**: Remote management supervisor.
- **CPLD**: Hardwired automation logic and traffic lights controlling signals.

## PCI -- and Why It's Called a "Link"?
PCI (Peripheral Component Interconnect) is a **communication bus standard** that defines how components inside a computer exchange data with the CPU and memory.
- Originally PCI (parallel bus): Old and slower.
- Npw PCIe (PCI Express): high-speed serial links between device.

PCIe is a high-speed point-to-point data link, not just a slot

Instead of one shared bus, PCIe establishes **point-to-point lanes**, e.g:
- x1, x4, x8, x16 lanes: Each lane is full-duplex and independent.
- Lane counts is like how many parallel lines to transfer the series data.

### That's why people call it a **link**
- It's literally a **logical data link** between two endpoints (CPU-GPU, CPU-NIC, etc).
