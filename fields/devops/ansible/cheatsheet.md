
# Ansible Cheatsheet: Every Step from the Series

<!-- related-block -->
<div class="reading-time">6 min read</div>
<!-- related-block -->
<div class="related-strip">

**See also:** [Four Nodes Said "Too Many Open Files": Inventories and Ad-Hoc Commands](/fields/devops/ansible/inventory-and-ad-hoc.md), [The GPU Node That Thought It Had 1000 MB: Roles and Variables](/fields/devops/ansible/roles-and-variables.md), [The Laptop That Ran Ansible 2.16: An Install You Can Trust](/fields/devops/ansible/getting-started.md), [The Munge Key in Git: Secrets, Vault and Rotation](/fields/devops/ansible/secrets-and-vault.md), [The Playbook That Restarted slurmd Every Night: Idempotence and Handlers](/fields/devops/ansible/idempotence-and-handlers.md), [The Reboot That Killed a Week of Jobs: Rolling Maintenance with Slurm](/fields/devops/ansible/rolling-maintenance.md)

</div>


> **Part 7 of [Ansible](/fields/devops/ansible/README.md)** The series as one list of commands, in the order you'd build the `cluster-ansible` project. Each step links to the page that explains it, shows its output, and shows how it fails.

- [Ansible Cheatsheet: Every Step from the Series](#ansible-cheatsheet-every-step-from-the-series)
  - [Before you start](#before-you-start)
  - [1. A pinned install](#1-a-pinned-install)
  - [2. ansible.cfg](#2-ansiblecfg)
  - [3. Inventory and host keys](#3-inventory-and-host-keys)
  - [4. Variables and patterns](#4-variables-and-patterns)
  - [5. Ad-hoc change, and a check that logs in fresh](#5-ad-hoc-change-and-a-check-that-logs-in-fresh)
  - [6. An idempotent playbook with handlers](#6-an-idempotent-playbook-with-handlers)
  - [7. The slurm role](#7-the-slurm-role)
  - [8. Rolling maintenance](#8-rolling-maintenance)
  - [9. Secrets with vault](#9-secrets-with-vault)
  - [Quick reference](#quick-reference)
  - [References](#references)

---

## Before you start

> [!NOTE]
> Every command here appears on one of the series pages, where it was run with **ansible-core 2.22.0** on Python 3.13 against six Ubuntu 24.04 nodes (`head01`, `cn001`–`cn004`, `gpu001`) running Slurm 23.11.4. Rocky/RHEL lines weren't run and are marked. This sheet collects the commands; it wasn't re-run from top to bottom as one script.

The nodes need: names that resolve, an `admin` user with your SSH key, passwordless `sudo`, and Python 3.9 or newer.

---

## 1. A pinned install

[Part 1, step 1](/fields/devops/ansible/getting-started.md#step-1-a-pinned-install-per-project). ansible-core 2.22 needs Python 3.13 on the controller; uv downloads it.

```bash
pip install uv
mkdir -p ~/cluster-ansible/inventory/{group_vars,host_vars} ~/cluster-ansible/{playbooks,roles,tools}
cd ~/cluster-ansible
cat > requirements.txt <<'EOF'
ansible-core==2.22.0
ansible-lint==26.11.0
EOF
uv python install 3.13
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements.txt
source .venv/bin/activate
ansible --version | head -2
ansible-lint --version
echo ".venv/" >> .gitignore
```

Expected: `ansible [core 2.22.0]` and `config file = .../cluster-ansible/ansible.cfg` (after step 2). Always `source .venv/bin/activate` first.

---

## 2. ansible.cfg

[Part 1, step 2](/fields/devops/ansible/getting-started.md#step-2-an-ansiblecfg-it-will-actually-read). In the project folder:

```ini
[defaults]
inventory = inventory/hosts.yml
remote_user = admin
roles_path = roles
collections_path = collections
interpreter_python = auto_silent
forks = 20
vault_password_file = ~/.config/cluster-ansible/vault-pass

[ssh_connection]
pipelining = True
```

(`vault_password_file` comes from [step 9](#9-secrets-with-vault); leave it out until then.) Ansible **ignores** `ansible.cfg` in a world-writable directory and then runs against nothing. `ansible --version` must show your file on the `config file =` line.

---

## 3. Inventory and host keys

[Part 1, steps 3 and 4](/fields/devops/ansible/getting-started.md#step-3-a-first-inventory). `inventory/hosts.yml`:

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

Trust host keys after comparing fingerprints, never with `host_key_checking = False`:

```bash
for n in head01 cn001 cn002 cn003 cn004 gpu001; do ssh-keyscan -t ed25519 $n 2>/dev/null; done > /tmp/scanned
ssh-keygen -lf /tmp/scanned          # compare with ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub on each node
cat /tmp/scanned >> ~/.ssh/known_hosts
ansible all -m ansible.builtin.ping; echo "exit=$?"
```

Expected: `pong` from every node, `exit=0`. Any unreachable node: exit **4**.

After you **know** a node was reinstalled:

```bash
ssh-keygen -R cn004
ssh-keyscan -t ed25519 cn004 2>/dev/null | tee -a ~/.ssh/known_hosts | ssh-keygen -lf -
ansible cn004 -m ansible.builtin.ping
```

A node with Python older than 3.9 fails with `Ansible requires Python 3.9 or newer on the target`. Fix the node, not Ansible. On Rocky/RHEL 8 (not run): `dnf install -y python3.12`, then `ansible_python_interpreter: /usr/bin/python3.12` in that group's `group_vars`.

---

## 4. Variables and patterns

[Part 2](/fields/devops/ansible/inventory-and-ad-hoc.md#variables-live-next-to-the-groups).

```bash
echo "nofile_limit: 8192" > inventory/group_vars/nodes.yml
echo "nofile_limit: 16384" > inventory/group_vars/gpu.yml
ansible-inventory --host gpu001      # the child group wins: 16384
ansible 'nodes:!cn003' --list-hosts  # aim before you fire
```

| Pattern | Means |
| --- | --- |
| `nodes` | The group |
| `nodes:!cn003` | The group minus a host |
| `compute:gpu` | Either group |
| `nodes:&gpu` | In both |
| `cn001,cn002` | A list |

A typo in an **ad-hoc** pattern warns and exits **0** (`No hosts matched`). In `ansible-playbook --limit` it exits 1. Check the host list in scripts.

---

## 5. Ad-hoc change, and a check that logs in fresh

[Part 2](/fields/devops/ansible/inventory-and-ad-hoc.md#the-change-as-one-command).

```bash
ansible nodes -b -m ansible.builtin.copy \
  -a 'dest=/etc/security/limits.d/90-nofile.conf content="* soft nofile {{ nofile_limit }}\n* hard nofile {{ nofile_limit }}\n" owner=root group=root mode=0644'
```

Checking login limits through Ansible right away shows the **old** value: it reuses each SSH connection for 60 s. `playbooks/check-nofile.yml` resets the connection first:

```yaml
- name: Check the open-files limit in a fresh login
  hosts: nodes
  gather_facts: false
  tasks:
    - name: Drop the reused SSH connection so the next task logs in again
      ansible.builtin.meta: reset_connection

    - name: Read the soft limit
      ansible.builtin.command: sh -c 'ulimit -n'
      register: nofile
      changed_when: false

    - name: Fail if it isn't what the inventory says
      ansible.builtin.assert:
        that: nofile.stdout | int == nofile_limit | int
        fail_msg: "{{ inventory_hostname }} has {{ nofile.stdout }}, expected {{ nofile_limit }}"
        quiet: true
```

```bash
ansible-playbook playbooks/check-nofile.yml; echo "exit=$?"
```

Expected: `changed=0 failed=0` on every node, `exit=0`. A node that missed the change fails with `has 1024, expected 8192`. Rerun the `copy` on just that node; on all nodes again it should say `SUCCESS`, not `CHANGED`.

---

## 6. An idempotent playbook with handlers

[Part 3](/fields/devops/ansible/idempotence-and-handlers.md#the-finished-playbook). The template, the variables and the full `playbooks/slurm-config.yml` are on that page. The parts that matter:

| Piece | Why |
| --- | --- |
| `ansible.builtin.template` instead of `shell` | Writes only when the content differs, so `changed` means changed |
| Handlers notified by the template | Restart only when the config changed |
| `force_handlers: true` on the play | A host that fails later still gets its restart; otherwise it runs the old config forever |
| `meta: flush_handlers` before the "started" tasks | A new config restarts (or first-starts) the daemon once, not start-then-restart |
| `changed_when: false` on read-only commands | Reading isn't a change |

```bash
ansible-playbook playbooks/slurm-config.yml --check --diff -l cn001   # dry run with line diffs
ansible-playbook playbooks/slurm-config.yml
ansible-playbook playbooks/slurm-config.yml                           # again: changed=0 everywhere
```

Check mode for package tasks on Ubuntu needs `python3-apt` on the node.

---

## 7. The slurm role

[Part 4](/fields/devops/ansible/roles-and-variables.md#the-finished-role).

```text
roles/slurm/
├── defaults/main.yml        choices: cluster name, controller, sizes (lowest precedence)
├── vars/Debian.yml          facts: Ubuntu package names (tested)
├── vars/RedHat.yml          facts: EPEL package names (not tested)
├── tasks/main.yml
├── handlers/main.yml
├── templates/slurm.conf.j2
└── meta/main.yml
```

Rules from that page:

- **`defaults/` for choices, `vars/` for facts.** A value in `vars/` silently beats your inventory.
- Load per-OS facts with `include_vars` + `first_found` (`<distribution>-<major>.yml`, then `<os_family>.yml`). An unsupported OS stops at the first task.
- Facts don't exist at `import_tasks` time; use `include_tasks` for paths built from facts.
- In a template loop over other hosts, read **their** values: `hostvars[node]['slurm_node_memory_mb'] | default(slurm_node_memory_mb)`. `hostvars` doesn't include role defaults, hence the `default()`.
- End the role with a `run_once` assert that every host's `slurm.conf` has the same checksum.

`playbooks/slurm.yml`:

```yaml
- name: Slurm controller and nodes
  hosts: head:nodes
  become: true
  force_handlers: true
  roles:
    - slurm
```

```bash
ansible-playbook playbooks/slurm.yml --check --diff
ansible-playbook playbooks/slurm.yml
ansible-playbook playbooks/slurm.yml        # again: changed=0
ansible-lint roles/slurm playbooks/slurm.yml
```

---

## 8. Rolling maintenance

[Part 5](/fields/devops/ansible/rolling-maintenance.md#the-playbook). The full `playbooks/rolling-maintenance.yml` is on that page: drain through Slurm, wait for `drained`, run `tasks/maintenance.yml`, reboot, check slurmd is active **and** has re-registered since the reboot (`SlurmdStartTime` changed), then resume.

| Play setting | Why |
| --- | --- |
| `serial: [1, "25%"]` | One canary, then a quarter at a time |
| `order: sorted` | A stable canary |
| `max_fail_percentage: 0` | Any failure stops the run |
| `when: not ansible_check_mode` on wait loops | Otherwise the dry run retries forever |

```bash
ansible-playbook playbooks/rolling-maintenance.yml -e maint_ticket=CHG-1047 --check --diff -l cn001   # dry run
ansible-playbook playbooks/rolling-maintenance.yml -e maint_ticket=CHG-1047                           # real run
sinfo -R                                                                                              # on the controller
```

If the canary fails, it stays drained with the ticket as the reason, and nothing else is touched. Roll back:

```bash
ansible cn001 -b -m ansible.builtin.systemd_service -a 'name=slurmd masked=false state=started'   # or revert the change
ansible head01 -b -m ansible.builtin.command -a 'scontrol update nodename=cn001 state=resume'
ansible-playbook playbooks/rolling-maintenance.yml -e maint_ticket=CHG-1047 --limit 'nodes:!cn001'  # the rest, if the change is good
```

This playbook isn't idempotent by design: rerunning it without `--limit` reboots every node again.

---

## 9. Secrets with vault

[Part 6](/fields/devops/ansible/secrets-and-vault.md#vault-in-five-minutes).

```bash
mkdir -p ~/.config/cluster-ansible
openssl rand -base64 32 > ~/.config/cluster-ansible/vault-pass
chmod 600 ~/.config/cluster-ansible/vault-pass
# add vault_password_file to ansible.cfg (step 2)

mkdir -p inventory/group_vars/head
printf 'slurmdbd_storage_pass: "Tr0ub4dor&3-not-real"\n' > inventory/group_vars/head/vault.yml
ansible-vault encrypt inventory/group_vars/head/vault.yml
ansible-vault view inventory/group_vars/head/vault.yml       # edit with: ansible-vault edit

# A new munge key, encrypted before it is ever committed
dd if=/dev/urandom of=roles/munge/files/munge.key bs=1024 count=1
ansible-vault encrypt roles/munge/files/munge.key
ansible-playbook playbooks/munge.yml                         # every host at once, never with serial
```

- A leaked secret stays in Git history: encrypting it now doesn't help. Make a **new** one.
- Rotate the munge key on all hosts in one run. Half-rotated, hosts reject each other's credentials (`unmunge: Error: Invalid credential`).
- 2.22 masks known secret values as `$REDACTED$` in output, but not values **derived** from them (`| b64encode`). Keep `no_log: true` on tasks that handle secrets.

The commit guard `tools/check-secrets.sh` is printed on [that page](/fields/devops/ansible/secrets-and-vault.md#a-guard-that-stops-the-next-one). Install it as a hook, and run it in CI too:

```bash
chmod +x tools/check-secrets.sh
ln -sf ../../tools/check-secrets.sh .git/hooks/pre-commit
tools/check-secrets.sh
```

Expected: `secrets check: ok`. A plain `*.key` or `vault.yml` prints `NOT ENCRYPTED: <file>` and blocks the commit.

---

## Quick reference

| Task | Command |
| --- | --- |
| Who would a pattern hit? | `ansible '<pattern>' --list-hosts` |
| A host's merged variables | `ansible-inventory --host <host>` |
| Ping everything | `ansible all -m ansible.builtin.ping` |
| Run as root | add `-b` |
| Dry run with diffs | `ansible-playbook <play> --check --diff` |
| Limit a run | `--limit 'nodes:!cn003'` |
| Override a variable | `-e name=value` |
| Run handlers even on failure (one run) | `--force-handlers` |
| Lint | `ansible-lint` |
| Exit codes | `0` ok, `2` a task failed, `4` a host unreachable |

**Takeaway:** pin the version per project, check `ansible.cfg` is the one in use, trust host keys deliberately, keep numbers in `group_vars`, write tasks that say what not how, restart only through handlers with `force_handlers`, roll through the cluster with a canary, and never commit a secret in plain text.

**Series index:** [Ansible](/fields/devops/ansible/README.md). The same Slurm lab is built step by step in the [Slurm lab cheatsheet](/fields/schedulers/slurm-ai-clusters/lab-build-cheatsheet.md).

---

## References

- [ansible-core installation](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) and [support matrix](https://docs.ansible.com/ansible/latest/reference_appendices/release_and_maintenance.html): Python versions.
- [Ansible configuration settings](https://docs.ansible.com/ansible/latest/reference_appendices/config.html): config file order, world-writable directories.
- [Patterns](https://docs.ansible.com/ansible/latest/inventory_guide/intro_patterns.html) and [inventory](https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html).
- [Handlers](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_handlers.html) and [variable precedence](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence).
- [Controlling playbook execution](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_strategies.html): `serial`, `max_fail_percentage`, `order`.
- [Ansible Vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html).