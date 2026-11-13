
# Four Nodes Said "Too Many Open Files": Inventories and Ad-Hoc Commands

<!-- related-block -->
<div class="reading-time">8 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [The Laptop That Ran Ansible 2.16: An Install You Can Trust](/fields/devops/ansible/getting-started.md)  ·  **See also:** [Ansible Cheatsheet: Every Step from the Series](/fields/devops/ansible/cheatsheet.md)  ·  **Read next:** [The Playbook That Restarted slurmd Every Night: Idempotence and Handlers](/fields/devops/ansible/idempotence-and-handlers.md)

</div>


> **Part 2 of the [Ansible series](/fields/devops/ansible/README.md).** [Part 1](/fields/devops/ansible/getting-started.md) got a pinned Ansible talking to every node. By the end of this page you'll describe the cluster in an inventory, change one setting on exactly the right nodes, catch the one that missed it, and prove the change in a fresh login.

- [The loop that skipped a node](#the-loop-that-skipped-a-node)
- [An inventory is a map with groups](#an-inventory-is-a-map-with-groups)
- [Variables live next to the groups](#variables-live-next-to-the-groups)
- [Aim before you fire](#aim-before-you-fire)
- [The change, as one command](#the-change-as-one-command)
- [The trap: checking through a reused connection](#the-trap-checking-through-a-reused-connection)
- [A check you can rerun](#a-check-you-can-rerun)
- [Catching up the node that was down](#catching-up-the-node-that-was-down)
- [What ad-hoc commands are not for](#what-ad-hoc-commands-are-not-for)
- [Back to the loop](#back-to-the-loop)
- [References](#references)

---

## The loop that skipped a node

A user's data-loading job dies with `OSError: [Errno 24] Too many open files`. The fix is well known: raise the open-files limit on the compute nodes. Someone does it the quick way:

```bash
for n in $(seq -w 1 400); do ssh cn$n 'echo "* soft nofile 8192" | sudo tee -a /etc/security/limits.d/90-nofile.conf'; done
```

It scrolls past, mostly fine. Three weeks later the same error comes back, but only for jobs that land on four particular nodes. Those nodes were down for repair that afternoon. The loop printed `ssh: connect to host ... No route to host` four times among four hundred lines, and nobody read them. Two other nodes now have the line twice, from when someone reran the loop "to be safe".

This page does the same change so that a missed node can't hide.

> [!NOTE]
> Lab: ansible-core **2.22.0**, Ubuntu 24.04 nodes with the usual default soft limit of 1024 open files. The lab container capped the hard limit at 20000, so we used values below that. The per-limit numbers here are examples, not recommendations.

---

## An inventory is a map with groups

An **inventory** lists your machines and puts them in **groups**. You'll use the groups everywhere: to choose where a task runs, and to attach settings. This is the lab's `inventory/hosts.yml`:

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

Three things to notice:

- `cn[001:004]` is a **range**: cn001 to cn004. A real cluster writes `cn[001:400]` and gets 400 hosts.
- `nodes` has no hosts of its own. Its **children** are other groups, so `nodes` means "every machine that runs jobs".
- Groups describe roles, not hardware racks. Add `rack07` if you need it; a host can be in many groups.

See what Ansible understood:

```bash
ansible-inventory --graph
```

```text
@all:
  |--@ungrouped:
  |--@head:
  |  |--head01
  |--@compute:
  |  |--cn001
  ...
  |--@nodes:
  |  |--@compute:
  |  |  |--cn001
  ...
  |  |--@gpu:
  |  |  |--gpu001
```

> [!WARNING]
> Ranges don't guess your padding. `cn[1:4]` expands to `cn1 cn2 cn3 cn4`, not `cn001`. We checked: `ansible -i unpadded.yml all --list-hosts` printed `cn1 cn2 cn3 cn4`. If your names have leading zeros, so does the range.

---

## Variables live next to the groups

Values that differ between groups go in `inventory/group_vars/<group>.yml`. Ansible loads them automatically for every host in that group.

```bash
echo "nofile_limit: 8192" > inventory/group_vars/nodes.yml
echo "nofile_limit: 16384" > inventory/group_vars/gpu.yml
```

gpu001 is in both `nodes` and `gpu`. The more specific group wins: a child group overrides its parent. Check before you rely on it:

```bash
ansible-inventory --host gpu001
ansible-inventory --host cn001
```

```text
{
    "nofile_limit": 16384
}
{
    "nofile_limit": 8192
}
```

Rule of thumb: **if you're about to type a number into a command, it probably belongs in `group_vars`.**

---

## Aim before you fire

A **pattern** picks hosts. Before any change, ask Ansible who it would touch with `--list-hosts`:

| Pattern | Means | In the lab |
| --- | --- | --- |
| `nodes` | The group | cn001–cn004, gpu001 |
| `nodes:!cn003` | The group, minus a host | cn001, cn002, cn004, gpu001 |
| `compute:gpu` | Either group | cn001–cn004, gpu001 |
| `nodes:&gpu` | In both groups | gpu001 |
| `cn001,cn002` | A list | cn001, cn002 |

```bash
ansible 'nodes:!cn003' --list-hosts
```

```text
  hosts (4):
    cn001
    cn002
    cn004
    gpu001
```

Now the trap. Mistype a group name in an **ad-hoc** command and Ansible warns, does nothing, and **exits 0**:

```bash
ansible compte -m ansible.builtin.ping; echo "exit=$?"
```

```text
[WARNING]: Could not match supplied host pattern, ignoring: compte
[WARNING]: No hosts matched, nothing to do
exit=0
```

A wrapper script would call that a success. The same typo in a **playbook's** `--limit` is treated properly: `--limit cn0003` failed with `no hosts to target` and exit 1. When you script ad-hoc commands, check the host list first.

---

## The change, as one command

An **ad-hoc command** runs one module on a set of hosts from the command line. No playbook file. Here's the whole change:

```bash
ansible nodes -b -m ansible.builtin.copy \
  -a 'dest=/etc/security/limits.d/90-nofile.conf content="* soft nofile {{ nofile_limit }}\n* hard nofile {{ nofile_limit }}\n" owner=root group=root mode=0644'
```

| Piece | Meaning |
| --- | --- |
| `nodes` | The pattern: where |
| `-b` | **Become** root with sudo on the node |
| `-m ansible.builtin.copy` | The module: write a file with exactly this content |
| `{{ nofile_limit }}` | Filled in per host from `group_vars`: 8192 on compute, 16384 on gpu001 |

Two differences from the `for` loop already. `copy` *sets* the file's content instead of appending to it, so running it twice gives the same file, not two lines. And Ansible reports every host. In the lab we ran it with cn003 switched off:

```text
cn001 | CHANGED => {
cn002 | CHANGED => {
cn003 | UNREACHABLE! => {
cn004 | CHANGED => {
gpu001 | CHANGED => {
```

Exit code 4. cn003 can't hide among the others.

---

## The trap: checking through a reused connection

You want to see the new limit, so you ask the nodes straight away:

```bash
ansible nodes -m ansible.builtin.command -a 'sh -c "ulimit -n"'
```

Every node said `1024`, the **old** value. At the same moment, a plain new SSH login to cn001 already showed the new one. We waited 65 seconds and asked through Ansible again: now every node showed its new value too.

Here's why. The limit is applied by PAM when you **log in**, and Ansible doesn't log in for every command. By default it keeps each SSH connection open for 60 seconds (`ControlPersist=60s` in its default `ssh_args`) and reuses it. Within that minute you're asking an old session.

So the change worked; the check was lying. This one cost us a confused ten minutes in the lab, and it'll do the same to anyone verifying limits, group memberships or anything else that's set at login.

---

## A check you can rerun

Turn the check into a small playbook that resets the connection, so it always reads a fresh login, and that compares the result with the inventory instead of with your eyes. Save it as `playbooks/check-nofile.yml`:

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

`changed_when: false` tells Ansible that reading a value changes nothing, so it doesn't report a change. Part 3 is about why that matters.

```bash
ansible-playbook playbooks/check-nofile.yml; echo "exit=$?"
```

With cn003 back up but still missing the change, the check named it and exited 2:

```text
fatal: [cn003]: FAILED! => {... "msg": "cn003 has 1024, expected 8192"}
cn001 : ok=2    changed=0    unreachable=0    failed=0
cn003 : ok=1    changed=0    unreachable=0    failed=1
```

Before we lowered the GPU value under the lab's cap, the same check also caught gpu001 holding a value the inventory didn't expect. It fails when it should. It passes `ansible-lint` on the `production` profile.

---

## Catching up the node that was down

Run the same change on just the node that missed it:

```bash
ansible cn003 -b -m ansible.builtin.copy \
  -a 'dest=/etc/security/limits.d/90-nofile.conf content="* soft nofile {{ nofile_limit }}\n* hard nofile {{ nofile_limit }}\n" owner=root group=root mode=0644'
```

`cn003 | CHANGED`. Then the important test: run it on **all** nodes again. Every host answered `SUCCESS`, not `CHANGED`. Nothing to do, so nothing done. And the check:

```text
cn001 : ok=2    changed=0    unreachable=0    failed=0
cn002 : ok=2    changed=0    unreachable=0    failed=0
cn003 : ok=2    changed=0    unreachable=0    failed=0
cn004 : ok=2    changed=0    unreachable=0    failed=0
gpu001 : ok=2    changed=0    unreachable=0    failed=0
exit=0
```

> [!IMPORTANT]
> A login limit doesn't reach processes that are already running, and Slurm jobs don't log in through PAM on the node. By default Slurm copies the limits from where the job was **submitted** (`PropagateResourceLimits` in `slurm.conf`), and slurmd's own limit caps what a job can have. So set the limit on the login nodes too, and restart slurmd after raising its limit. See the Slurm documentation in the references; we didn't test the Slurm side in this lab.

---

## What ad-hoc commands are not for

Ad-hoc is for questions and one-off fixes: "what's the kernel version everywhere?", "restart this daemon on these three nodes". It's not for changes you want to keep. Nobody can review a command in your shell history, and nobody will rerun it on the node you add next month. Once a change matters, it goes into a playbook in Git. That's part 3.

---

## Back to the loop

Same request, same 400 nodes, this inventory. The change is one command with the value in `group_vars`, so GPU nodes get theirs without a second loop. Four nodes are down; the output says `UNREACHABLE!` four times, the run exits 4, and that's impossible to scroll past in a script. Nobody reruns anything "to be safe", because rerunning changes nothing.

When the four nodes come back, `check-nofile.yml` names them. One `--limit` run catches them up, and the check passes on all 400. Three weeks later there's no mystery error, because the check would have failed first. It's a five-second job to put it in the node health checks.

**Takeaway:** describe the cluster once in an inventory, keep values in `group_vars`, aim with `--list-hosts`, and verify with a check that logs in fresh and compares against the inventory.

**Next:** [Part 3, The Playbook That Restarted slurmd Every Night](/fields/devops/ansible/idempotence-and-handlers.md), turns one-off commands into playbooks you can trust to rerun.

---

## References

- [How to build your inventory](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_inventory.html): YAML inventories, ranges, child groups, `group_vars` and how group variables merge.
- [Patterns: targeting hosts and groups](https://docs.ansible.com/projects/ansible/latest/inventory_guide/intro_patterns.html): `:`, `!`, `&` and `--limit`.
- [Introduction to ad hoc commands](https://docs.ansible.com/projects/ansible/latest/command_guide/intro_adhoc.html): running modules from the command line, `-b`.
- [ansible.builtin.copy](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/copy_module.html), [ansible.builtin.assert](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/assert_module.html), [ansible.builtin.meta](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/meta_module.html): the modules used here, including `reset_connection`.
- [ansible.builtin.ssh connection](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/ssh_connection.html): the default `ssh_args` with `ControlPersist=60s`.
- [limits.conf(5)](https://man7.org/linux/man-pages/man5/limits.conf.5.html) and [pam_limits(8)](https://man7.org/linux/man-pages/man8/pam_limits.8.html): when login limits apply.
- [slurm.conf: PropagateResourceLimits](https://slurm.schedmd.com/slurm.conf.html#OPT_PropagateResourceLimits): how Slurm passes limits from the submit host to jobs.
