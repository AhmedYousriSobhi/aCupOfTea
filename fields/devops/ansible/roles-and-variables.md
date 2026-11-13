
# The GPU Node That Thought It Had 1000 MB: Roles and Variables

<!-- related-block -->
<div class="reading-time">8 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [The Playbook That Restarted slurmd Every Night: Idempotence and Handlers](/fields/devops/ansible/idempotence-and-handlers.md)  ·  **See also:** [Ansible Cheatsheet: Every Step from the Series](/fields/devops/ansible/cheatsheet.md)  ·  **Read next:** [The Reboot That Killed a Week of Jobs: Rolling Maintenance with Slurm](/fields/devops/ansible/rolling-maintenance.md), [The Munge Key in Git: Secrets, Vault and Rotation](/fields/devops/ansible/secrets-and-vault.md)

</div>


> **Part 4 of the [Ansible series](/fields/devops/ansible/README.md).** [Part 3](/fields/devops/ansible/idempotence-and-handlers.md) built a playbook that deploys `slurm.conf` safely. This page turns it into a **role** that works on Ubuntu and Rocky, takes per-group values from the inventory, and proves every node ended up with the same file.

- [Big jobs that never start](#big-jobs-that-never-start)
- [What a role is](#what-a-role-is)
- [The OS-family maze, done right](#the-os-family-maze-done-right)
- [defaults or vars? The precedence trap](#defaults-or-vars-the-precedence-trap)
- [Whose value is it?](#whose-value-is-it)
- [Prove every node got the same file](#prove-every-node-got-the-same-file)
- [The finished role](#the-finished-role)
- [Back to the big jobs](#back-to-the-big-jobs)
- [References](#references)

---

## Big jobs that never start

A new GPU node arrives with far more memory than the compute nodes. The admin does it by the book from part 2: one line in `group_vars/gpu.yml` with the bigger memory size, run the Slurm playbook, all green.

A week later, users complain that jobs asking for lots of memory sit in the queue forever. The scheduler is sure the GPU node is a small one. `slurm.conf` on gpu001 says the big number. `slurm.conf` on the controller says the small one. And the controller's log has been saying it for a week:

```text
error: Node gpu001 appears to have a different slurm.conf than the slurmctld.  This could cause issues with communication and functionality.
```

Nothing failed, and every task was green. The template did exactly what it was told. This page is about telling it the right thing.

> [!NOTE]
> Lab: ansible-core **2.22.0**, Ubuntu 24.04 nodes, Slurm 23.11.4. The memory numbers are lab-sized (1000 and 4000 MB). The Rocky/RHEL variables file wasn't run; there was no Rocky image in the sandbox.

---

## What a role is

A **role** is a folder with a fixed layout that bundles tasks, handlers, templates and variables, so a playbook can say "this host gets Slurm" in one line. Ansible finds each piece by its folder name:

| Folder | Holds | Loaded |
| --- | --- | --- |
| `tasks/main.yml` | The steps | Always |
| `handlers/main.yml` | Restarts and reloads | When notified |
| `templates/` | `.j2` files for the `template` module | By name, no path needed |
| `defaults/main.yml` | Settings a site may change | Always, **lowest** precedence |
| `vars/` | Facts about the OS or the software, not choices | `vars/main.yml` always, **high** precedence; other files when you load them |
| `meta/main.yml` | Author, supported platforms, dependencies | By tools and Galaxy |

With part 1's `roles_path = roles` in `ansible.cfg`, the role lives in `roles/slurm/`, and the playbook shrinks to this (`playbooks/slurm.yml`):

```yaml
- name: Slurm controller and nodes
  hosts: head:nodes
  become: true
  force_handlers: true
  roles:
    - slurm
```

---

## The OS-family maze, done right

Ubuntu and Rocky package Slurm under different names. An earlier version of the [Ansible page](/fields/devops/ansible/getting-started.md) tried to pick OS-specific *task files* by building a path from a fact, and hit this. We reproduced it on 2.22:

```yaml
- name: Include OS-specific tasks
  ansible.builtin.import_tasks: "../{{ ansible_os_family | lower }}/tasks/main.yml"
```

```text
[ERROR]: Error when evaluating variable in import path '../{{ ansible_os_family | lower }}/tasks/main.yml': 'ansible_os_family' is undefined
```

`import_tasks` is **static**: Ansible reads it when it loads the playbook, before it has talked to any host, so no facts exist yet. `include_tasks` is **dynamic**: it's resolved when the task runs, after facts are gathered. Switching to `include_tasks` fixed it, and the relative path worked as is. The earlier advice to make the path absolute isn't needed on 2.22.

But usually you don't need different *tasks*, only different *names*. Same steps, different package names. So keep one set of tasks and load the OS-specific values:

```yaml
- name: Load the variables for this OS
  ansible.builtin.include_vars: "{{ lookup('ansible.builtin.first_found', params) }}"
  vars:
    params:
      files:
        - "{{ ansible_facts['distribution'] }}-{{ ansible_facts['distribution_major_version'] }}.yml"
        - "{{ ansible_facts['os_family'] }}.yml"
      paths:
        - vars
```

**`first_found`** takes the first file that exists: `Ubuntu-24.yml` if you ever need one for a specific release, otherwise `Debian.yml` (Ubuntu's OS family) or `RedHat.yml` (Rocky's). `roles/slurm/vars/Debian.yml`:

```yaml
# Facts about the OS packaging, not site choices. Tested on Ubuntu 24.04.
slurm_controller_packages: [slurmctld]
slurm_node_packages: [slurmd]
slurm_config_dir: /etc/slurm
```

`roles/slurm/vars/RedHat.yml`, with the EPEL package names:

```yaml
# EPEL package names. Not tested in the lab (no Rocky image available).
slurm_controller_packages: [slurm-slurmctld]
slurm_node_packages: [slurm-slurmd]
slurm_config_dir: /etc/slurm
```

And the failure path. We hid `Debian.yml` to stand in for an OS the role doesn't support. The run stopped at the first task, before touching anything, with exit 2:

```text
The lookup plugin 'ansible.builtin.first_found' failed: No file was found when using first_found.
```

That's what you want from an unsupported OS: a clear stop, not a half-configured node.

---

## defaults or vars? The precedence trap

Ansible has more than twenty places a variable can come from, and an order that decides which wins. You need two facts from that list:

| Where | Beats inventory `group_vars`? |
| --- | --- |
| Role `defaults/main.yml` | No. It's the lowest of all |
| Inventory `group_vars` and `host_vars` | n/a |
| Role `vars/main.yml`, and `include_vars` files | **Yes** |

So a value in the role's `vars/` silently beats your inventory. We tested it: the inventory says `slurm_cluster_name: acot`. We put `slurm_cluster_name: cluster` in `roles/slurm/vars/main.yml` and dry-ran:

```text
-ClusterName=acot
+ClusterName=cluster
```

The inventory lost, with no warning. Moved to `defaults/main.yml`, the inventory won again and the dry run showed no change.

Rule of thumb: **`defaults/` is for choices, `vars/` is for facts.** Cluster name, memory sizes, the controller's name: choices, so `defaults/`. Package names on Ubuntu: facts, so `vars/Debian.yml`. `roles/slurm/defaults/main.yml`:

```yaml
# Anything a site may want to change lives here: lowest precedence, so inventory wins.
slurm_cluster_name: cluster
slurm_controller: "{{ groups['head'] | first }}"
slurm_partition: batch
slurm_node_cpus: 1
slurm_node_memory_mb: 1000
```

---

## Whose value is it?

Now the bug from the story. Part 3's template had this loop:

```jinja
{% for node in groups['nodes'] | sort %}
NodeName={{ node }} CPUs={{ slurm_node_cpus }} RealMemory={{ slurm_node_memory_mb }} State=UNKNOWN
{% endfor %}
```

A template is rendered **once per host, with that host's variables.** Inside the loop, `slurm_node_memory_mb` isn't the memory of `node`; it's the memory of the host the file is being written for. We gave the GPU group its own size:

```yaml
# inventory/group_vars/gpu.yml
nofile_limit: 16384
slurm_node_memory_mb: 4000
```

and looked at two nodes' copies of the file:

```text
--- slurm.conf on cn001:
NodeName=cn001 CPUs=1 RealMemory=1000 State=UNKNOWN
NodeName=gpu001 CPUs=1 RealMemory=1000 State=UNKNOWN
--- slurm.conf on gpu001:
NodeName=cn001 CPUs=1 RealMemory=4000 State=UNKNOWN
NodeName=gpu001 CPUs=1 RealMemory=4000 State=UNKNOWN
```

Every node wrote every line with *its own* number. The controller (not a GPU node) believes gpu001 is small, so big jobs never go there. Slurm noticed the mismatch and logged the error from the story.

The fix: inside a loop over other hosts, read **their** variables through `hostvars[node]`:

```jinja
NodeName={{ node }} CPUs={{ hostvars[node]['slurm_node_cpus'] | default(slurm_node_cpus) }} RealMemory={{ hostvars[node]['slurm_node_memory_mb'] | default(slurm_node_memory_mb) }} State=UNKNOWN
```

Why the `| default(...)`? `hostvars` holds inventory variables and facts, **not** role defaults. When we removed `slurm_node_cpus` from the inventory to rely on the role's default, the plain `hostvars[node]['slurm_node_cpus']` failed:

```text
[ERROR]: Task failed: object of type 'HostVarsVars' has no attribute 'slurm_node_cpus'
```

The `default()` falls back to the role default when the inventory doesn't set one. After the fix, every copy agreed: `NodeName=gpu001 CPUs=1 RealMemory=4000` on both cn001 and gpu001.

A side effect worth knowing: because `hostvars` doesn't see role variables at all, the precedence trap above can't reach values read this way. It still reaches every plain `{{ variable }}`, like `ClusterName`.

---

## Prove every node got the same file

`slurm.conf` must be identical everywhere. Slurm warns when it isn't, but only in a log. So make the role check it and fail the run instead. These two tasks go at the end of `tasks/main.yml`:

```yaml
- name: Read the checksum of slurm.conf
  ansible.builtin.stat:
    path: "{{ slurm_config_dir }}/slurm.conf"
    checksum_algorithm: sha256
  register: slurm_conf_stat

- name: Fail unless every host has the same slurm.conf
  ansible.builtin.assert:
    that: >-
      ansible_play_hosts
      | map('extract', hostvars, ['slurm_conf_stat', 'stat', 'checksum'])
      | unique | length == 1
    fail_msg: "slurm.conf differs between hosts. Check that per-node values use hostvars[node]."
    quiet: true
  run_once: true
```

Each host records its file's checksum; one host (`run_once`) collects all of them and asserts there's exactly one distinct value. We proved it fails when it should: with the buggy template and the GPU override, the run stopped with exit 2 at this task. With the fixed template it passed, exit 0.

> [!TIP]
> Run the role with `--limit` and this check compares only the hosts in that run. It catches a bad template, not an old file on a host you left out.

---

## The finished role

```text
roles/slurm/
├── defaults/main.yml      choices (shown above)
├── handlers/main.yml      the two restart handlers from part 3
├── meta/main.yml          platforms and minimum Ansible version
├── tasks/main.yml         below
├── templates/slurm.conf.j2  part 3's template, with the hostvars fix
└── vars/
    ├── Debian.yml         facts for Ubuntu (tested)
    └── RedHat.yml         facts for Rocky/RHEL (not tested)
```

`roles/slurm/tasks/main.yml`, between the `include_vars` task at the top and the two check tasks at the bottom (both shown above):

```yaml
- name: Install the controller packages
  ansible.builtin.package:
    name: "{{ slurm_controller_packages }}"
    state: present
  when: inventory_hostname in groups['head']

- name: Install the node packages
  ansible.builtin.package:
    name: "{{ slurm_node_packages }}"
    state: present
  when: inventory_hostname in groups['nodes']

- name: Make sure Slurm's directories exist
  ansible.builtin.file:
    path: "{{ item }}"
    state: directory
    owner: slurm
    group: slurm
    mode: "0755"
  loop:
    - /var/lib/slurm
    - /var/log/slurm

- name: Install slurm.conf
  ansible.builtin.template:
    src: slurm.conf.j2
    dest: "{{ slurm_config_dir }}/slurm.conf"
    owner: root
    group: root
    mode: "0644"
  notify:
    - Restart slurmctld
    - Restart slurmd

- name: Restart now if the config changed, before the start tasks below
  ansible.builtin.meta: flush_handlers

- name: Run slurmctld on the controller
  ansible.builtin.systemd_service:
    name: slurmctld
    state: started
    enabled: true
  when: inventory_hostname in groups['head']

- name: Run slurmd on compute and GPU nodes
  ansible.builtin.systemd_service:
    name: slurmd
    state: started
    enabled: true
  when: inventory_hostname in groups['nodes']
```

`handlers/main.yml` holds part 3's two handlers unchanged, and `templates/slurm.conf.j2` is part 3's template with two edits: the header says `(role slurm)`, and the `NodeName` line is the `hostvars` version above. `PartitionName` uses `{{ slurm_partition }}` instead of a fixed `batch`.

```bash
ansible-playbook playbooks/slurm.yml --check --diff   # see what the role would change
ansible-playbook playbooks/slurm.yml
ansible-playbook playbooks/slurm.yml                  # again: changed=0 everywhere
ansible-lint roles/slurm playbooks/slurm.yml
```

On the lab cluster, the role's first dry run against part 3's deployment showed one difference: the header comment. The real run, the rerun with `changed=0` on all six hosts, and `ansible-lint` on the `production` profile all passed.

---

## Back to the big jobs

Run the story again with the finished role. The GPU node's size goes into `group_vars/gpu.yml` exactly as before. This time the controller renders gpu001's line from gpu001's own variables. Every copy of `slurm.conf` says the GPU node is the big one, the checksum check passes on every host, and big jobs land on the GPU node the moment it's idle.

Had the template still been wrong, the run would have stopped red at "Fail unless every host has the same slurm.conf" the first day, instead of a week of green runs and a log nobody read. And when the Rocky nodes join, they need one tested `vars/RedHat.yml`, not a second playbook.

**Takeaway:** in a role, put choices in `defaults/` and facts in `vars/`, read other hosts' values through `hostvars[node]` with a default, and make the role prove every node got the same config.

**Next:** [Part 5, The Reboot That Killed a Week of Jobs](/fields/devops/ansible/rolling-maintenance.md), changes nodes that are busy running jobs.

---

## References

- [Roles](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_reuse_roles.html): role layout, `defaults` vs `vars`, `roles_path`, `meta/main.yml`.
- [Re-using Ansible artifacts](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_reuse.html): `import_tasks` (static) vs `include_tasks` (dynamic).
- [Using variables: variable precedence](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence): the full precedence list.
- [Special variables](https://docs.ansible.com/projects/ansible/latest/reference_appendices/special_variables.html): `hostvars`, `groups`, `ansible_play_hosts`.
- [ansible.builtin.first_found lookup](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/first_found_lookup.html) and [ansible.builtin.include_vars](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/include_vars_module.html): loading OS-specific variables.
- [ansible.builtin.stat](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/stat_module.html), [ansible.builtin.assert](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/assert_module.html), [ansible.builtin.package](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/package_module.html): modules used.
- [Fedora/EPEL: slurm-slurmctld](https://packages.fedoraproject.org/pkgs/slurm/slurm-slurmctld) and [slurm-slurmd](https://packages.fedoraproject.org/pkgs/slurm/slurm-slurmd): package names for Rocky/RHEL.
- [Ubuntu noble: slurmctld](https://packages.ubuntu.com/noble/slurmctld): Ubuntu's package names.
- [slurm.conf(5)](https://slurm.schedmd.com/slurm.conf.html): every node and the controller must share the same file.
