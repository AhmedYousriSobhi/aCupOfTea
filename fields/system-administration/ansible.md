# System Administration - Ansible

## Table of Contents
- [System Administration - Ansible](#system-administration---ansible)
  - [Table of Contents](#table-of-contents)
  - [0- Prerequisites](#0--prerequisites)
  - [1- Installation - Steps](#1--installation---steps)
    - [1.1- Ubuntu \[Not Recommended\]](#11--ubuntu-not-recommended)
    - [1.2- Mamba - Isolated Environment](#12--mamba---isolated-environment)
    - [Note - Config File](#note---config-file)
    - [VSCode - Ansible Interpreter Configuration](#vscode---ansible-interpreter-configuration)
  - [2- Installation - Verification](#2--installation---verification)
  - [3. Getting Ready to Rock](#3-getting-ready-to-rock)
  - [Errors \& Issues](#errors--issues)
    - [1. Ping Node - Something Nasty](#1-ping-node---something-nasty)
    - [2. SyntaxError: future feature annotations is not defined](#2-syntaxerror-future-feature-annotations-is-not-defined)
    - [3. Ansible Facts - discovered\_interpreter\_python](#3-ansible-facts---discovered_interpreter_python)
    - [4. Ansible\_os\_family Dynamic Structure](#4-ansible_os_family-dynamic-structure)

## 0- Prerequisites
- Make sure Python version is 3.7 or above in the target hosts.
- Also install python3-dnf in case you're working with RedHat OS, on your host machine.
    ```bash
    sudo apt install python3-dnf
    ```

## 1- Installation - Steps
### 1.1- Ubuntu [Not Recommended]
- The following steps are for debian based systems.
1. Update the system:
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```
2. Install the software-properties-common package:
    ```bash
    sudo apt install software-properties-common -y
    ```
3. Add the official Ansible to PPA:
    ```bash
    sudo add-apt-repository --yes --update ppa:ansible/ansible
    ```
4. Install Ansible:
    ```bash
    sudo apt install ansible -y
    ```
5. Verify the installation:
    ```bash
    ansible --version
    ```

### 1.2- Mamba - Isolated Environment
1. Install Miniforge:
    ```bash
    wget -O Miniforge3.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"

    bash Miniforge3.sh -b -p "${HOME}/conda"

    source "${HOME}/conda/etc/profile.d/conda.sh"

    mamba shell init
    ```
2. Create Ansible environment:
    ```bash
    mamba create -n ansible python

    mamba activate ansible
    ```
3. Install the Ansible packages:
    ```bash
    mamba install ansible
    mamba install ansible-lint
    ```
4. Verify the installation:
    ```bash
    ansible --version

    which ansible
    # To validate that it's using the conda 
    ```

### Note - Config File
- About config file = None in ansible --version
- This is not a problem and is actually normal in a fresh setup. It just means Ansible isn’t currently using a custom configuration file (ansible.cfg) — it will fall back to its default internal settings.
- Ansible looks for ansible.cfg in this order:
    - ANSIBLE_CONFIG environment variable (if set)
    - ./ansible.cfg in the current working directory
    - ~/.ansible.cfg in your home directory
    - /etc/ansible/ansible.cfg (the global default)
- So if you don’t explicitly create one, Ansible just uses defaults. You won’t face issues, but if you want to customize behavior later (e.g., inventory path, privilege escalation, retry behavior), then creating your own config file is useful.

### VSCode - Ansible Interpreter Configuration
1. Get the path for the module ansible:
    ```bash
    # Activate the Ansible environment
    mamba activate ansible

    which ansible
    which ansible-lint
    
    # Expected output
    ${HOME}/conda/envs/ansible/bin/ansible
    ```
2. Edit the configuration settings in VScode: Files > Preferences > settings > search for ansible. Edit the following parameters:
   - Ansible Path
   - Python: Interpreter Path
   - Validation > Lint: Path with ansible-lint path.

## 2- Installation - Verification
1. Create the working directory for testing
    ```bash
    mkdir -p ~/ansible/test
    cd ~/ansible/test
    ```
2. Create a quick inventory file for testing:
    ```bash
    echo "localhost ansible_connection=local" > hosts
    ```
3. Run a simple ping-pong module:
    ```bash
    ansible -i hosts all -m ping
    ```
- Expected Output should like this:
    ```bash
    localhost | SUCCESS => {
        "changed": false,
        "ping": "pong"
    }
    ```
## 3. Getting Ready to Rock
- Create a basic Ansible folder structure:
    ```bash
    mkdir -p ~/ansible/{inventories,playbooks,roles}
    cd ~/ansible
    ```

## Errors & Issues
### 1. Ping Node - Something Nasty
- The issue happened during ssh to a node:
    ```bash
    mgmt-01 | UNREACHABLE! => {
        "changed": false,
        "msg": "Failed to connect to the host via ssh: @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\r\n@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @\r\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\r\nIT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!\r\nSomeone could be eavesdropping on you right now (man-in-the-middle attack)!\r\nIt is also possible that a host key has just been changed.\r\nThe fingerprint for the RSA key sent by the remote host is\nSHA256:4Nyl3fOKnDrBTahvLW9Kp9LZm+k+gZ1WTGC1JmNlaJg.\r\nPlease contact your system administrator.\r\nAdd correct host key in /home/ahmed-yousri/.ssh/known_hosts to get rid of this message.\r\nOffending RSA key in /home/ahmed-yousri/.ssh/known_hosts:5\r\n  remove with:\r\n  ssh-keygen -f '/home/ahmed-yousri/.ssh/known_hosts' -R '192.168.121.60'\r\nHost key for 192.168.121.60 has changed and you have requested strict checking.\r\nHost key verification failed.",
        "unreachable": true
    }
    ```
- It happens when the SSH host key of a machine has changed — likely because you destroyed and re-created the VM.

**SOLUTION**
1. Remove the outdated key by run:
    ```bash
    ssh-keygen -f ~/.ssh/known_hosts -R <NODE_IP>
    ```
2. Run again the ping test:
    ```bash
    ansible -i <INVENTORY> <NODE_HOSTNAME> -m ping
    ```
### 2. SyntaxError: future feature annotations is not defined
- The following error happened during trying to ping a node
    ```bash
    ansible -i <INVENTORY> <NODE_HOSTNAME> -m ping

    # Error Output
    An exception occurred during task execution. To see the full traceback, use -vvv. The error was: SyntaxError: future feature annotations is not defined
    ```

**EXPLANATION**
- Ansible modules use newer Python syntax — including this line:
    ```bash
    from __future__ import annotations
    ```
- CentOS VM is using Python 2.7 (the system default on CentOS 7).

**SOLUTION**
- Upgrade to higher Python version on the node:
    ```bash
    sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel wget
    cd /usr/src
    sudo wget https://www.python.org/ftp/python/3.9.18/Python-3.9.18.tgz
    sudo tar xzf Python-3.9.18.tgz
    cd Python-3.9.18
    sudo ./configure --enable-optimizations
    sudo make altinstall
    ```
- Validation: Try to import the *annotation* package:
    ```bash
    from __future__ import annotations
    ```

### 3. Ansible Facts - discovered_interpreter_python
**ISSUE**
- The error below was shown during running the following playbook:
    ```bash
    - name: Check Python interpreter
      hosts: headnode
      gather_facts: true
      tasks:
          - name: Show discovered Python interpreter
          debug:
              msg: "Using Python interpreter: {{ ansible_facts.discovered_interpreter_python }}"
    ```
- The output error:    
    ```bash
    ansible-playbook -i inventories/hosts playbooks/check_python.yml

    'task includes an option with an undefined variable.. 'dict object' has no attribute 'discovered_interpreter_python''
    ```
- This means the fact ansible_facts.discovered_interpreter_python does not exist at the point you're trying to use it.

**EXPLANATION**
- *discovered_interpreter_python* is only available if Ansible had to guess the interpreter (typically when ansible_python_interpreter is not explicitly defined in your inventory).
- But we already specified the Python interpreter in the Inventory:
    ```bash
    ansible_python_interpreter=/usr/local/bin/python3.9
    ```
- then Ansible doesn't need to "discover" the interpreter — and so the discovered_interpreter_python fact will not exist.

**SOLUTION**
- Modify the playbook to:
    ```bash
    - name: Check Python interpreter
      hosts: headnode
      gather_facts: true
      tasks:
          - name: Show discovered Python interpreter
          debug:
              msg: "Using Python interpreter: {{ ansible_python_interpreter }}"
    ```
- Use hostvars as fallback with default: If you want to print both auto-discovered and manually set interpreters in one playbook, you can do
    ```bash
    - name: Check Python interpreter
      hosts: headnode
      gather_facts: true
      tasks:
          - name: Show Python interpreter used
          debug:
              msg: >-
              Python used: {{
                  ansible_facts.discovered_interpreter_python
                  if ansible_facts.discovered_interpreter_python is defined
                  else ansible_python_interpreter
              }}
      ```

### 4. Ansible_os_family Dynamic Structure
**Objective**
- I was trying to make the playbook to be more dynamic, so based on the detected OS Family of the nodes, it will accordingly select the correct roles. For more illustration, let's check the below directory structure:
    ```yml
    playbook:
        install_x.yml
    roles:
        x:
            tasks:
                main.yml
            redhat:
                tasks:
                    main.yml
                    install_x.yml
            debian:
                tasks:
                    main.yml
                    install_x.yml
    ```

**Issue**
- I got this error:
    ```bash
    ERROR! Error when evaluating variable in dynamic parent include path: ../roles/slurm/{{ ansible_os_family | lower }}/tasks/main.yml. When using static imports, the parent dynamic include cannot utilize host facts or variables from inventory. 'ansible_os_family' is undefined
    ```
- This error occurs because ansible_os_family is a fact that's only available after gather_facts runs, but Ansible is trying to evaluate the path during the static parsing phase.

**Solution**
1. Make sure to use include_tasks instead of import_tasks.
   - Explanation: using include_tasks (dynamic) not import_tasks (static).
2. Use the absolute path for every included tasks in any roles included.
   - Explanation: When you use variables like {{ ansible_os_family | lower }} in the path, Ansible can't resolve the relative path during the static parsing phase, so it needs an absolute reference point.

**Code Snippet**
- playbook/install_x.yml
    ```yml
    # playbook/install_x.yml
    - name: Install and configure x
    hosts: cluster
    gather_facts: true
    become: true
    roles:
        - role: ../roles/x
    ```
- roles/tasks/main.yml
    ```yml
    # Dynamic Path Structure
    - name: Include OS-specific x tasks
      ansible.builtin.include_tasks: "../roles/x/{{ ansible_os_family | lower }}/tasks/main.yml"
      ```
- roles/redhat/tasks/main.yml
    ```yml
    # Dynamic Path Structure
    - name: Install x on Rocky
      ansible.builtin.include_tasks: ../roles/x/{{ ansible_os_family | lower }}/tasks/x_install.yml
    ```

**Best Practice**
- Static path with when clause is generally better, like:
    ```bash
    # Static Path Structure
    - name: Include RedHat-specific SLURM tasks
      ansible.builtin.include_tasks: ../redhat/tasks/main.yml
      when: ansible_os_family == "RedHat"

    - name: Include Debian-specific SLURM tasks
      ansible.builtin.include_tasks: ../debian/tasks/main.yml
      when: ansible_os_family == "Debian"
    ```
