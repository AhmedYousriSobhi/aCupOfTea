
# The Laptop That Ran Ansible 2.16: An Install You Can Trust

<!-- related-block -->
<div class="reading-time">10 min read</div>
<!-- related-block -->
<div class="related-strip">

**See also:** [Ansible Cheatsheet: Every Step from the Series](/fields/devops/ansible/cheatsheet.md)  ·  **Read next:** [Four Nodes Said "Too Many Open Files": Inventories and Ad-Hoc Commands](/fields/devops/ansible/inventory-and-ad-hoc.md)

</div>


> **Part 1 of the [Ansible series](/fields/devops/ansible/README.md).** By the end you'll have a pinned Ansible in a project folder, a config file it actually reads, every node's SSH host key checked, and a ping that answers `pong` from the whole cluster.

- [Two laptops, one playbook](#two-laptops-one-playbook)
- [Which Ansible, which Python](#which-ansible-which-python)
- [Step 1: a pinned install per project](#step-1-a-pinned-install-per-project)
- [Step 2: an ansible.cfg it will actually read](#step-2-an-ansiblecfg-it-will-actually-read)
- [Step 3: a first inventory](#step-3-a-first-inventory)
- [Step 4: first contact and host keys](#step-4-first-contact-and-host-keys)
- [When a node is reinstalled](#when-a-node-is-reinstalled)
- [When a node's Python is too old](#when-a-nodes-python-is-too-old)
- [Which Python did it pick?](#which-python-did-it-pick)
- [Your editor](#your-editor)
- [Back to the two laptops](#back-to-the-two-laptops)
- [References](#references)

---

## Two laptops, one playbook

Two admins share one Git repo of playbooks. Sara installed Ansible with `apt` two years ago. Omar ran `pip install ansible-core` last week. Same repo, same command, different results.

Sara's run works everywhere, including the old Rocky 8 nodes nobody wants to touch. Omar's fails on exactly those nodes:

```text
Ansible requires Python 3.9 or newer on the target.
```

Omar concludes his laptop is broken. It isn't. Sara is running an ansible-core that went out of support in July 2025, and Omar is running one that no longer talks to the Python those nodes ship with. Neither of them chose a version. Their package managers did.

This page fixes that: one pinned version per project, chosen on purpose, the same on every laptop.

> [!NOTE]
> Lab: ansible-core **2.22.0** on Python 3.13 (control machine), six Ubuntu 24.04 nodes with Python 3.12. Rocky/RHEL steps weren't run (no Rocky image in the sandbox); they come from Red Hat's documentation and are marked.

---

## Which Ansible, which Python

Ansible runs on your machine, the **control node**, and copies small Python programs, **modules**, to each **managed node** (target), where they run with that node's Python. So two Pythons matter, and each ansible-core release supports a range of both. From the official support matrix:

| ansible-core | Status (Nov 2026) | Control node Python | Target Python |
| --- | --- | --- | --- |
| 2.22 | Current, GA Nov 2026 | 3.13 – 3.15 | 3.9 – 3.15 |
| 2.21 | Critical fixes until Nov 2026, security until May 2027 | 3.12 – 3.14 | 3.9 – 3.14 |
| 2.20 | Security phase ended 2 Nov 2026; end of life May 2027 | 3.12 – 3.14 | 3.9 – 3.14 |
| 2.18, 2.19 | 2.18 end of life May 2026; 2.19 end of life Nov 2026 | 3.11 – 3.13 | 3.8 – 3.13 |
| 2.16 | End of life since July 2025 | 3.10 – 3.12 | 2.7, 3.6 – 3.12 |

What that means on real machines:

| What you do | What you get | Why |
| --- | --- | --- |
| `apt install ansible-core` on Ubuntu 24.04 | 2.16.3 | That's the version in Ubuntu's archive |
| `pip install ansible-core` on Python 3.12 (Ubuntu 24.04's) | 2.21.6 | pip quietly picks the newest release that supports your Python |
| `pip install ansible-core==2.22.0` on Python 3.12 | An error | 2.22.0 requires Python 3.13 |
| `pip install ansible` (the big package with collections) | 14.6.0, which pins core 2.21.6 | The community package trails ansible-core |

We ran all four in the lab. The third one says so plainly:

```text
ERROR: Ignored the following versions that require a different python version: 2.22.0 Requires-Python >=3.13
ERROR: No matching distribution found for ansible-core==2.22.0
```

And on the target side, the trap from the story: **Rocky/RHEL 8's built-in Python is 3.6** (`platform-python`, used by `dnf` itself). Every ansible-core since 2.17 refuses it. We come back to that [below](#when-a-nodes-python-is-too-old).

Rule of thumb: **pin ansible-core per project, and pick the version from your oldest node's Python, not from your laptop.**

---

## Step 1: a pinned install per project

We use **uv**, a Python package manager that can also download the Python version a project needs. That matters here: ansible-core 2.22 needs Python 3.13, and Ubuntu 24.04 ships 3.12. Install uv with any method from its docs; in the lab we used `pip install uv`.

1. Make the project and write down the versions:

```bash
mkdir -p ~/cluster-ansible/inventory/{group_vars,host_vars} ~/cluster-ansible/{playbooks,roles}
cd ~/cluster-ansible
cat > requirements.txt <<'EOF'
ansible-core==2.22.0
ansible-lint==26.11.0
EOF
```

2. Create the environment with its own Python, and install exactly those versions:

```bash
uv python install 3.13
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements.txt
source .venv/bin/activate
```

3. Check it:

```bash
ansible --version | head -2
ansible-lint --version
```

```text
ansible [core 2.22.0]
  config file = /root/cluster-ansible/ansible.cfg
ansible-lint 26.11.0 using ansible-core:2.22.0 ansible-compat:26.11.0 ruamel-yaml:0.19.1
```

Commit `requirements.txt`; add `.venv/` to `.gitignore`. Anyone who clones the repo runs the same two `uv` commands and gets the same Ansible.

> [!TIP]
> Always `source .venv/bin/activate` first. Without it, ansible-lint printed `WARNING: PATH altered to include .../.venv/bin ... This is usually a sign of broken local setup` in our lab.

If you'd rather use Mamba, as an earlier version of this page did, the same idea applies: one environment per project, with the version pinned (`mamba install ansible-core=2.22.0`). We didn't test that route this time, and conda-forge has to carry the version you pin.

---

## Step 2: an ansible.cfg it will actually read

Put the settings in the project, next to the playbooks:

```ini
[defaults]
inventory = inventory/hosts.yml
remote_user = admin
roles_path = roles
collections_path = collections
interpreter_python = auto_silent
forks = 20

[ssh_connection]
pipelining = True
```

| Setting | Why |
| --- | --- |
| `inventory` | So you never need `-i` and never run against the wrong list |
| `remote_user` | The account Ansible logs in as on every node |
| `interpreter_python = auto_silent` | Finds each node's Python without a warning per host |
| `forks = 20` | How many nodes it works on at once. The default is 5 |
| `pipelining = True` | Fewer SSH round trips per task; noticeably faster on many nodes |

Ansible uses the **first** config file it finds, in this order: the file named by `ANSIBLE_CONFIG`, `./ansible.cfg` in the current directory, `~/.ansible.cfg`, then `/etc/ansible/ansible.cfg`. That's why you run Ansible from the project folder.

Here's the trap. If the current directory is **world-writable**, Ansible ignores the `ansible.cfg` in it, because anyone could have planted it. We ran `chmod o+w .` in the project:

```text
[WARNING]: Ansible is being run in a world writable directory (/root/cluster-ansible), ignoring it as an ansible.cfg source.
[WARNING]: No inventory was parsed, only implicit localhost is available
[WARNING]: provided hosts list is empty, only localhost is available. Note that the implicit localhost does not match 'all'
```

No config, so no inventory, so a playbook against `all` runs against nothing and finishes. Shared project folders on NFS are where this bites. Check with `ansible --version`: the `config file =` line must show your file.

---

## Step 3: a first inventory

Part 2 explains inventories properly. For now, this file says which machines exist and how they're grouped:

```yaml
all:
  children:
    head:
      hosts:
        head01:
    compute:
      hosts:
        cn[001:004]:
    gpu:
      hosts:
        gpu001:
    nodes:
      children:
        compute:
        gpu:
```

Save it as `inventory/hosts.yml`. The node names must resolve (DNS or `/etc/hosts`), and the `admin` user needs your SSH key and passwordless `sudo` on every node.

---

## Step 4: first contact and host keys

```bash
ansible all -m ansible.builtin.ping
```

On a fresh setup, every node failed:

```text
cn001 | UNREACHABLE! => {
    "changed": false,
    "msg": "Task failed: Failed to connect to the host via ssh: Host key verification failed.",
    "unreachable": true
}
```

Ansible uses OpenSSH, and OpenSSH won't talk to a machine whose host key it hasn't seen. Interactive `ssh` would ask you; Ansible can't. The tempting fix is `host_key_checking = False`. Don't: that's the exact check that tells you someone is impersonating a node.

Collect the keys once, and compare them with what the nodes report about themselves:

```bash
for n in head01 cn001 cn002 cn003 cn004 gpu001; do ssh-keyscan -t ed25519 $n 2>/dev/null; done > /tmp/scanned
ssh-keygen -lf /tmp/scanned
```

```text
256 SHA256:LcF5cJgCXRUCelr3XOoLcEs60Fb9yy7fwmD728/YF3w head01 (ED25519)
256 SHA256:80kw4rx6+UTPjQmo2yqjCzANvYQlBglvLX+FdZqOgAM cn001 (ED25519)
...
```

On the node itself (through the BMC console, or your provisioning logs), `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` must print the same fingerprint. In the lab, cn001 printed `SHA256:80kw4rx6...gAM`, a match. Then trust them:

```bash
cat /tmp/scanned >> ~/.ssh/known_hosts
ansible all -m ansible.builtin.ping
```

```text
cn001 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.12"
    },
    "changed": false,
    "ping": "pong"
}
```

Success is a `pong` from every node and exit code 0. When any node is unreachable, Ansible carries on with the others and exits **4**. Scripts should check for that.

> [!NOTE]
> The `-o` (one line per host) option still works in 2.22 but prints a deprecation warning: it goes away in 2.23. Don't build scripts on it.

---

## When a node is reinstalled

You reinstall cn004. It comes back with new host keys, and the next run says:

```text
WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!
...
Host key verification failed.
```

We reproduced this by rebuilding cn004 in the lab. Everything else kept working; cn004 was `UNREACHABLE!` and the run exited 4. The fix is the same as first contact, for one node: remove the old key, scan, compare, trust.

```bash
ssh-keygen -R cn004
ssh-keyscan -t ed25519 cn004 2>/dev/null | tee -a ~/.ssh/known_hosts | ssh-keygen -lf -
ansible cn004 -m ansible.builtin.ping
```

Do it only when you *know* the node was reinstalled. If you didn't reinstall it, that warning is the one that matters.

---

## When a node's Python is too old

Back to Omar's error. In the lab we pointed one node at a Python 3.8 to reproduce it:

```bash
ansible cn003 -m ansible.builtin.ping -e ansible_python_interpreter=/opt/py38/bin/python3.8
```

```text
"msg": "Ansible requires Python 3.9 or newer on the target. Current version: 3.8.20 ..."
```

Older ansible-core versions failed differently on old Pythons; an earlier version of this page shows `SyntaxError: future feature annotations is not defined` from a CentOS 7 node with Python 2.7. Same cause: a target Python older than the release supports.

**The fix is a newer Python on the node, not an older Ansible.** For Rocky/RHEL 8, Red Hat's documentation says:

- `platform-python` (3.6) is for system tools and isn't meant for you to use. Don't remove it; `dnf` needs it.
- Newer Pythons are packages: `python3.11` (RHEL 8.8 and later) and `python3.12` (8.10 and later).

So on those nodes, install one and tell Ansible to use it, in that group's variables (`inventory/group_vars/el8.yml`, for a group called `el8`):

```bash
dnf install -y python3.12
```

```yaml
ansible_python_interpreter: /usr/bin/python3.12
```

We couldn't run this on Rocky 8 in the lab. Check the path with `ls /usr/bin/python3*` on one node first. CentOS 7 reached end of life in June 2024; the earlier advice to compile Python from source there is a workaround for a system you should be replacing.

---

## Which Python did it pick?

A small playbook to see which interpreter Ansible uses on each node. It's the fixed version of a snippet from an earlier version of this page, which had two bugs: wrong indentation, and a fact that isn't always there.

```yaml
- name: Show which Python Ansible uses on each node
  hosts: all
  gather_facts: true
  tasks:
    - name: Print the interpreter
      ansible.builtin.debug:
        msg: "{{ ansible_facts.discovered_interpreter_python | default(ansible_python_interpreter) }}"
```

`discovered_interpreter_python` only exists when Ansible had to *discover* the interpreter. If you set `ansible_python_interpreter` yourself, as for the el8 group above, it doesn't exist, and the plain version of this task fails:

```text
[ERROR]: Task failed: Finalization of task args for 'ansible.builtin.debug' failed: Error while resolving value for 'msg': object of type 'dict' has no attribute 'discovered_interpreter_python'
```

With `| default(ansible_python_interpreter)`, it printed `/usr/bin/python3.12` for discovered nodes and `/usr/bin/python3` for the one we'd set by hand. It passes `ansible-lint` on the `production` profile.

---

## Your editor

If you use VS Code with the Ansible extension, point it at the project's environment so it lints with the same versions you pinned. In the extension's settings, set the Ansible path to `.venv/bin/ansible`, the Python interpreter to `.venv/bin/python`, and the lint path to `.venv/bin/ansible-lint`. We didn't test the extension itself in the lab.

---

## Back to the two laptops

Sara and Omar delete their system Ansibles. Both clone the repo, run the two `uv` commands, and get ansible-core 2.22.0 on Python 3.13, the version written in `requirements.txt`. Their runs now behave identically, because they *are* identical.

The Rocky 8 nodes still say "requires Python 3.9". Now that's the right answer, not a laptop problem: they get `python3.12` from AppStream and one line in `group_vars/el8.yml`. The next admin who joins doesn't inherit Sara's out-of-support version or Omar's surprise. And when it's time for 2.23, upgrading is a one-line change in a reviewed commit, not something a package manager decided on a Tuesday.

**Takeaway:** pin ansible-core per project from your oldest node's Python, keep `ansible.cfg` in the project folder, and check host keys instead of switching checking off.

**Next:** [Part 2, Four Nodes Said "Too Many Open Files"](/fields/devops/ansible/inventory-and-ad-hoc.md), makes the inventory do real work.

---

## References

- [Releases and maintenance](https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html): the ansible-core support matrix with control and target Python versions and end-of-life dates.
- [ansible-core 2.22 changelog](https://github.com/ansible/ansible/blob/stable-2.22/changelogs/CHANGELOG-v2.22.rst): dropping Python 3.12 on the controller.
- [ansible-core source, `module_utils/basic.py`](https://github.com/ansible/ansible/blob/v2.22.0/lib/ansible/module_utils/basic.py): the target Python minimum (`_PY_MIN = (3, 9)`) and its error message.
- [ansible-core source, `config/manager.py`](https://github.com/ansible/ansible/blob/v2.22.0/lib/ansible/config/manager.py): config file search order and the world-writable directory check.
- [Installing Ansible](https://docs.ansible.com/projects/ansible/latest/installation_guide/intro_installation.html): `ansible` vs `ansible-core` and installation with pip.
- [Interpreter discovery](https://docs.ansible.com/projects/ansible/latest/reference_appendices/interpreter_discovery.html): how Ansible picks the target Python and the `auto_silent` setting.
- [ansible-core on PyPI](https://pypi.org/project/ansible-core/) and [ansible on PyPI](https://pypi.org/project/ansible/): `Requires-Python` and versions.
- [Ubuntu noble: ansible-core](https://packages.ubuntu.com/noble/ansible-core): the 2.16.3 package in Ubuntu 24.04.
- [Red Hat: Installing and using dynamic programming languages (RHEL 8)](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/8/html/configuring_basic_system_settings/installing-and-using-dynamic-programming-languages_configuring-basic-system-settings): `platform-python`, `python3.11`, `python3.12`.
- [uv documentation](https://docs.astral.sh/uv/): installing uv, Python versions and virtual environments.
- [ssh-keyscan(1)](https://man.openbsd.org/ssh-keyscan.1) and [ssh-keygen(1)](https://man.openbsd.org/ssh-keygen.1): collecting and fingerprinting host keys.
