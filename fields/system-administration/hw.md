# System Administration - Hardware

## Table of Contents
- [System Administration - Hardware](#system-administration---hardware)
  - [Table of Contents](#table-of-contents)
  - [Audio in HDMI](#audio-in-hdmi)

## Audio in HDMI
- To resolve the issue for HDMI audio in Ubuntu OS:
    ```bash
    vi /lib/udev/rules.d/71-nvidia.rules 

    # Comment this line: 
    ACTION==“add”, SUBSYSTEM==“pci”, ATTR{vendor}==“0x10de”, ATTR{class}==“0x040300”, TEST==“power/control”, ATTR{power/control}=“auto”
    ```
