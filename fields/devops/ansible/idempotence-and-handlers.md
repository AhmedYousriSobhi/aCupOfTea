
# The Playbook That Restarted slurmd Every Night: Idempotence and Handlers

<!-- related-block -->
<div class="reading-time">8 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [Four Nodes Said "Too Many Open Files": Inventories and Ad-Hoc Commands](/fields/devops/ansible/inventory-and-ad-hoc.md)  ·  **See also:** [Ansible Cheatsheet: Every Step from the Series](/fields/devops/ansible/cheatsheet.md)  ·  **Read next:** [The GPU Node That Thought It Had 1000 MB: Roles and Variables](/fields/devops/ansible/roles-and-variables.md)

</div>


> **Part 3 of the [Ansible series](/fields/devops/ansible/README.md).** [Part 2](/fields/devops/ansible/inventory-and-ad-hoc.md) made one-off changes with ad-hoc commands. This page writes a playbook that deploys `slurm.conf` to the whole cluster, restarts daemons only when the file really changed, previews changes before making them, and survives a failure halfway through.

- [Changed, every night](#changed-every-night)
- [Idempotent: say what, not how](#idempotent-say-what-not-how)
- [The version that started it all](#the-version-that-started-it-all)
- [A template and two handlers](#a-template-and-two-handlers)
- [Preview with --check --diff](#preview-with---check---diff)
- [The handler that never ran](#the-handler-that-never-ran)
- [Started, then restarted](#started-then-restarted)
- [The finished playbook](#the-finished-playbook)
- [Back to the nightly run](#back-to-the-nightly-run)
- [References](#references)

---

## Changed, every night

A cron job runs the Slurm playbook every night "to keep things in line". Every morning the summary says the same thing: `changed=2` on every node. Everyone learns to ignore it.

Then someone edits `slurm.conf` by hand on one node to test something and forgets to undo it. The nightly run fixes the file, which is good. But the report says `changed=2` on that node, the same as on every other node, every other night. Nobody notices that this time it meant something. Meanwhile every node's slurmd has been restarted every night for a year, and once a month that restart lands during a burst of job launches.

A run that always says "changed" tells you nothing. This page makes "changed" mean something again.

> [!NOTE]
> Lab: ansible-core **2.22.0**, Slurm **23.11.4** from Ubuntu 24.04's packages, with systemd running on every node. Two Slurm settings in the template below (`SlurmUser=slurm`, `MpiDefault=none`) were added after the lab's first run failed without them; they match Ubuntu's packaging.

---

## Idempotent: say what, not how

A task is **idempotent** when running it twice leaves the system the same as running it once, and the second run reports **ok** instead of **changed**. Ansible's modules are built for this: you describe the end state ("this file has this content", "this service is running"), and the module checks before it acts.

Every task ends in one of these states:

| State | Means | What you should feel |
| --- | --- | --- |
| `ok` | Already right, nothing done | Nothing. That's the goal |
| `changed` | It was wrong, now it's right | Look: something drifted, or you shipped a change |
| `skipped` | A condition said "not here" | Nothing |
| `failed` | Couldn't make it right | Act |

Rule of thumb: **a clean second run should be all `ok`.** If it isn't, the playbook is lying to you.

---

## The version that started it all

This is the playbook from the story, in miniature:

```yaml
- name: The way it started
  hosts: nodes
  become: true
  tasks:
    - name: Write slurm.conf
      ansible.builtin.shell: cat /tmp/slurm.conf.new > /etc/slurm/slurm.conf
    - name: Restart slurmd
      ansible.builtin.command: systemctl restart slurmd
```

`shell` and `command` just run what you give them. Ansible can't know whether that changed anything, so it always says `changed`. We ran it twice:

```text
cn001 : ok=3    changed=2    unreachable=0    failed=0
cn001 : ok=3    changed=2    unreachable=0    failed=0
```

Two runs, two restarts, identical reports. And in check mode (next section) both tasks are simply `skipped`: you can't preview anything. `ansible-lint` flags all of it:

```text
no-changed-when: Commands should not change things if nothing needs doing.
command-instead-of-module: systemctl used in place of systemd module
no-changed-when: Commands should not change things if nothing needs doing.
```

`shell` and `command` aren't banned. Use them for things no module does, and tell Ansible when they change something (`changed_when:`), as part 2's check did with `changed_when: false`.

---

## A template and two handlers

Two ideas fix this.

A **template** is a file with placeholders, filled in per host from variables. The `ansible.builtin.template` module renders it, compares the result with the file on the node, and writes only if they differ. Save as `playbooks/templates/slurm.conf.j2`:

```jinja
# Managed by Ansible (playbooks/slurm-config.yml). Local edits will be overwritten.
ClusterName={{ slurm_cluster_name }}
SlurmctldHost={{ slurm_controller }}
SlurmUser=slurm
AuthType=auth/munge
ProctrackType=proctrack/linuxproc
TaskPlugin=task/none
MpiDefault=none
SelectType=select/cons_tres
ReturnToService=2
StateSaveLocation=/var/lib/slurm/slurmctld
SlurmdSpoolDir=/var/lib/slurm/slurmd
SlurmctldLogFile=/var/log/slurm/slurmctld.log
SlurmdLogFile=/var/log/slurm/slurmd.log

{% for node in groups['nodes'] | sort %}
NodeName={{ node }} CPUs={{ slurm_node_cpus }} RealMemory={{ slurm_node_memory_mb }} State=UNKNOWN
{% endfor %}
PartitionName=batch Nodes={{ groups['nodes'] | sort | join(',') }} Default=YES MaxTime=INFINITE State=UP
```

The node list comes from the inventory: add a host to `compute`, and it appears in every node's `slurm.conf` on the next run. The values go in `inventory/group_vars/all.yml`:

```yaml
slurm_cluster_name: acot
slurm_controller: head01
slurm_node_cpus: 1
slurm_node_memory_mb: 1000
```

(The lab's containers have one CPU and plenty of memory. Use your hardware's real numbers; `slurmd -C` on a node prints them.)

A **handler** is a task that runs only when another task **notifies** it, and only if that task reported `changed`. Handlers run once, at the end of the play, however many tasks notified them. So "restart slurmd" becomes a handler, notified by the template task. Same file, no change, no restart.

The full playbook is [further down](#the-finished-playbook). First, what it does.

On the second run, every host reported `changed=0` and no handler ran. That's the whole point:

```text
cn001 : ok=4    changed=0    unreachable=0    failed=0    skipped=1
head01 : ok=4    changed=0    unreachable=0    failed=0    skipped=1
```

When we really changed something (adding `SlurmUser=slurm` to the template), only then did the handlers run:

```text
+SlurmUser=slurm
RUNNING HANDLER [Restart slurmctld] ********************************************
RUNNING HANDLER [Restart slurmd] ***********************************************
```

---

## Preview with --check --diff

**Check mode** (`--check`) runs the playbook without changing anything: modules that support it report what they *would* do. **Diff mode** (`--diff`) shows the line-level change for files. Together, they're the dry run you show a colleague before the real one.

We changed `slurm_node_memory_mb` from 950 to 1000 and asked:

```bash
ansible-playbook playbooks/slurm-config.yml --check --diff -l cn001
```

```text
--- before: /etc/slurm/slurm.conf
+++ after: /root/.ansible/tmp/.../slurm.conf.j2
-NodeName=cn001 CPUs=1 RealMemory=950 State=UNKNOWN
+NodeName=cn001 CPUs=1 RealMemory=1000 State=UNKNOWN
changed: [cn001]
RUNNING HANDLER [Restart slurmctld] ********************************************
RUNNING HANDLER [Restart slurmd] ***********************************************
changed: [cn001]
```

You see the exact line, and that slurmd *would* restart. The file's checksum was the same before and after: nothing was written.

> [!TIP]
> On Ubuntu, check mode for package tasks needs `python3-apt` on the node. A minimal image without it failed with `python3-apt must be installed to use check mode`. Normal runs install it automatically; check mode can't, because that would be a change.

---

## The handler that never ran

Here's the trap that bites good playbooks. Handlers run at the **end** of the play. If a host fails anywhere after the notifying task, that host's handlers don't run.

We reproduced it: changed a value, and added a task after the template that fails on cn002, standing in for a full `/var`, a typo, anything.

```text
fatal: [cn002]: FAILED! => {"changed": false, "msg": "simulated failure"}
cn001 : ok=5    changed=2    unreachable=0    failed=0
cn002 : ok=3    changed=1    unreachable=0    failed=1
```

cn002 got the new `slurm.conf` (`changed=1`), but its slurmd kept running with the old one. We compared slurmd's start time with the file's modification time:

```text
cn001 slurmd restarted after config change
cn002 STALE: slurmd older than slurm.conf
```

Then we removed the failure and ran again. cn002 said `changed=0`, because the file was already correct. **No change, no notification, no restart, ever.** cn002 stayed stale until someone restarted it by hand.

The fix is one line at the play level:

```yaml
  force_handlers: true
```

With it, Ansible runs the notified handlers for a host even when that host failed. Same failure on cn002, this time:

```text
fatal: [cn002]: FAILED! => {"changed": false, "msg": "simulated failure"}
RUNNING HANDLER [Restart slurmd] ***********************************************
changed: [cn002]
```

```text
cn002 slurmd restarted after config change
```

The run still fails, as it should, but no daemon is left running on a config that's no longer on disk. (`--force-handlers` on the command line does the same for one run.)

---

## Started, then restarted

One more subtle one, found in the controller's log on the very first deploy. The playbook had two tasks in this order: "make sure slurmctld is started", then (at the end of the play) the "restart slurmctld" handler. On a fresh node that means:

```text
[...T13:45:15.824] Running as primary controller                         <- the "started" task
[...T13:45:17.895] Terminate signal (SIGINT or SIGTERM) received         <- the handler, 2 s later
[...T13:45:17.914] slurmctld version 23.11.4 started on cluster acot
```

Started, then immediately restarted, because the config was new. Harmless here, wasteful on a real controller, and confusing when you read the log.

`meta: flush_handlers` runs any pending handlers *right there*, instead of at the end. Put it between the template and the "started" tasks: a changed config restarts (or first-starts) the daemon, and the "started" task finds it already running. We reinstalled cn004 and counted daemon starts in its log on the first deploy:

| Order | slurmd starts on first deploy |
| --- | --- |
| started task, then handler at end of play | 2 |
| template, `flush_handlers`, then started task | 1 |

---

## The finished playbook

Save as `playbooks/slurm-config.yml`:

```yaml
- name: Deploy slurm.conf everywhere and restart only what changed
  hosts: head:nodes
  become: true
  force_handlers: true
  tasks:
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
        src: templates/slurm.conf.j2
        dest: /etc/slurm/slurm.conf
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

  handlers:
    - name: Restart slurmctld
      ansible.builtin.systemd_service:
        name: slurmctld
        state: restarted
      when: inventory_hostname in groups['head']

    - name: Restart slurmd
      ansible.builtin.systemd_service:
        name: slurmd
        state: restarted
      when: inventory_hostname in groups['nodes']
```

```bash
ansible-playbook playbooks/slurm-config.yml
ansible-playbook playbooks/slurm-config.yml   # again: should be changed=0 everywhere
```

On the lab cluster: `sinfo` showed all five nodes `idle`, a batch job ran on the node we asked for, the second run was all `changed=0`, and `ansible-lint` passed on the `production` profile.

> [!NOTE]
> This template writes the same `CPUs` and `RealMemory` for every node. That's fine while every node is the same. Part 4 gives the GPU node its own value and finds the bug hiding in that loop.

---

## Back to the nightly run

The cron job runs the new playbook. Most mornings the summary is `changed=0` everywhere and no daemon restarted overnight. The burst-of-launches incident stops, because nothing restarts unless something changed.

Then comes the morning someone hand-edited `slurm.conf` on one node. The summary shows `changed=2` on exactly one host. It stands out like a red light on a quiet panel. The template put the file back, the handler restarted that one slurmd, and `--diff` in the log shows exactly which line drifted. If anything had failed halfway, `force_handlers` would still have restarted the daemon, so no node is left running a config that isn't on its disk.

**Takeaway:** describe end states with modules, restart through handlers, preview with `--check --diff`, and set `force_handlers` so a failure can't leave a daemon on a stale config.

**Next:** [Part 4, The GPU Node That Thought It Had 1000 MB](/fields/devops/ansible/roles-and-variables.md), turns this playbook into a reusable role.

---

## References

- [Intro to playbooks](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_intro.html): desired state and idempotency.
- [Handlers: running operations on change](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_handlers.html): notification, `meta: flush_handlers`, and handlers after failures.
- [Error handling in playbooks](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_error_handling.html): `force_handlers`, `changed_when`.
- [Validating tasks: check mode and diff mode](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_checkmode.html): `--check`, `--diff` and module support.
- [ansible.builtin.template](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/template_module.html), [ansible.builtin.systemd_service](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/systemd_service_module.html), [ansible.builtin.command](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/command_module.html): the modules used.
- [ansible-lint rules](https://docs.ansible.com/projects/lint/rules/): `no-changed-when`, `command-instead-of-module`.
- [slurm.conf(5)](https://slurm.schedmd.com/slurm.conf.html): `SlurmUser`, `MpiDefault`, `ReturnToService`, node and partition definitions.
- [slurmd(8)](https://slurm.schedmd.com/slurmd.html): `slurmd -C` prints a node's real hardware for `slurm.conf`.
