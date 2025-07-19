# System Administration - Virtual Machines

## Table of Contents
- [System Administration - Virtual Machines](#system-administration---virtual-machines)
  - [Table of Contents](#table-of-contents)
  - [Vagrant - Provider Libvirt](#vagrant---provider-libvirt)
    - [Steps](#steps)
  - [References](#references)

## Vagrant - Provider Libvirt
### Steps
1. Make sure your hardware supports the necessary virtualisation extensions for Kernel-based Virtual Machine (KVM). To check this, enter the following from a terminal prompt:
    ```bash
    # You will need cpu-checker package to be installed
    kvm-ok
    ```
2. Add your user to the libvirt group:
    ```bash
    # Make sure the group is created
    getent group libvirt

    # In case the group does not exist
    sudo addgroup libvirt
    
    sudo adduser $USER libvirt
    ```
3. Make sure to install the following packages
    ```bash
    sudo apt install -y libvirt-daemon-system libvirt-clients bridge-utils virt-manager libvirt-dev qemu-kvm libvirt-daemon-system
    ```
4. Install Vagrant
    - To install Vagrant, you can download the Vagrant deb package from [https://releases.hashicorp.com/vagrant/2.4.6/](https://releases.hashicorp.com/vagrant/2.4.6/)
        ```bash
        wget https://releases.hashicorp.com/vagrant/2.4.6/vagrant_2.4.6-1_amd64.deb

        sudo apt install ./vagrant_2.4.6-1_amd64.deb
        # Incase of error:
        N: Download is performed unsandboxed as root as file '/path/vagrant_2.4.6-1_amd64.deb' couldn't be accessed by user '_apt'. - pkgAcquire::Run (13: Permission denied
        ## Please run
        sudo chmod a+r /home/asobhy/Downloads/vagrant_2.4.6-1_amd64.deb
        sudo apt install ./vagrant_2.4.6-1_amd64.deb
        ```
5. Install the vagrant-libvirt plugin for Vagrant
    ```bash
    vagrant plugin install vagrant-libvirt
    ```

## References
- [Ubuntu - Libvirt Docs](https://documentation.ubuntu.com/server/how-to/virtualisation/libvirt/)
