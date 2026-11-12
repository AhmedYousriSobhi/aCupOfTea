---
id: ansible-rolling
title: "The Reboot That Killed a Week of Jobs: Rolling Maintenance with Slurm"
sidebar_label: "5. Rolling maintenance"
order: 5
summary: Change busy compute nodes safely - drain through Slurm, wait for jobs, one canary first, stop on the first failure, check the node really came back, a dry run that is really dry, and rollback.
level: advanced
type: [concept, guide]
domains: [devops, systems-and-hpc]
tags: [ansible, slurm]
relations:
  prerequisites: [ansible-roles]
  related: [nhc-build-and-install]
---

# The Reboot That Killed a Week of Jobs: Rolling Maintenance with Slurm

> **Part 5 of the [Ansible series](/fields/devops/ansible/README.md).** [Part 4](/fields/devops/ansible/roles-and-variables.md) built a role that configures Slurm. This page changes nodes that are busy *running* jobs: drain each node, wait for its jobs to finish, do the work, prove it came back healthy, return it to service. One canary first, and a full stop at the first failure.

- [All at once, at 14:00](#all-at-once-at-1400)
- [The mental model: drain, change, prove, resume](#the-mental-model-drain-change-prove-resume)
- [The playbook](#the-playbook)
- [What each piece buys you](#what-each-piece-buys-you)
- [Step 1: dry run](#step-1-dry-run)
- [The dry run that hung](#the-dry-run-that-hung)
- [Step 2: canary, then the rest](#step-2-canary-then-the-rest)
- [When the canary comes back broken](#when-the-canary-comes-back-broken)
- [Rollback](#rollback)
- [How we caught our own weak health check](#how-we-caught-our-own-weak-health-check)
- [Back to 14:00](#back-to-1400)
- [References](#references)

---

## All at once, at 14:00

A driver update has to go out, and it needs a reboot. The playbook is ready and tested on a spare node. At 14:00 someone runs it against `compute`. Without `serial`, Ansible runs each task on every host before moving to the next (5 hosts in parallel by default, 20 with part 1's `forks`), with no idea that a node has jobs on it. Batch after batch, nodes reboot under running jobs. Some jobs had been running for six days.

Worse, the new driver has a problem on one hardware revision. Those nodes come back without their GPUs, and Slurm hands them new jobs immediately. Those fail too.

Every piece worked as written. Nobody wrote "wait for the jobs" or "stop if it goes wrong".

> [!NOTE]
> Lab: ansible-core **2.22.0**, Slurm 23.11.4 on five Ubuntu 24.04 nodes in containers. Two lab differences, both disclosed where they matter: reboots needed one extra setting because containers share the host's boot ID, and the lab's Slurm (no accounting database) logged "invalid account" for new jobs; the backfill scheduler still started them within its 30-second cycle.

---

## The mental model: drain, change, prove, resume

Four ideas, each a few lines of YAML:

| Idea | Slurm or Ansible feature | Meaning |
| --- | --- | --- |
| **Drain** | `scontrol update state=drain` | No *new* jobs land on the node; running jobs finish normally |
| **Batches** | `serial:` | Work on a few nodes at a time; the rest keep running jobs |
| **Canary** | `serial: [1, ...]` | The first batch is a single node. If it goes wrong, one node is affected |
| **Stop on failure** | `max_fail_percentage: 0` | Any failure in a batch stops the whole run before the next batch |

The Slurm commands run on the controller, not on the node being changed. That's **`delegate_to`**: "run this task on another host, on behalf of this one".

Rule of thumb: **a node is out of service from the moment you drain it until you've proven it healthy, not until the reboot finishes.**

---

## The playbook

Save as `playbooks/rolling-maintenance.yml`:

```yaml
- name: Rolling maintenance, one canary node first, then a quarter at a time
  hosts: nodes
  become: true
  serial:
    - 1
    - "25%"
  order: sorted
  max_fail_percentage: 0
  vars:
    maint_reason: "ansible maintenance {{ maint_ticket | default('no-ticket') }}"
  tasks:
    - name: Drain the node in Slurm
      ansible.builtin.command: >-
        scontrol update nodename={{ inventory_hostname }}
        state=drain reason="{{ maint_reason }}"
      delegate_to: "{{ slurm_controller }}"
      changed_when: true

    - name: Wait for its running jobs to finish
      ansible.builtin.command: sinfo --noheader --nodes={{ inventory_hostname }} --format=%T
      delegate_to: "{{ slurm_controller }}"
      register: node_state
      until: node_state.stdout == 'drained'
      retries: "{{ drain_wait_retries | default(360) }}"
      delay: 10
      changed_when: false
      when: not ansible_check_mode

    - name: Do the maintenance
      ansible.builtin.include_tasks: tasks/maintenance.yml

    - name: Remember when slurmd last registered, to compare after the reboot
      ansible.builtin.command: scontrol show node {{ inventory_hostname }} --oneliner
      delegate_to: "{{ slurm_controller }}"
      register: before_reboot
      changed_when: false
      when: not ansible_check_mode

    - name: Reboot
      ansible.builtin.reboot:
        reboot_timeout: 900

    - name: Read slurmd's state after the reboot
      ansible.builtin.systemd_service:
        name: slurmd
      register: slurmd_unit

    - name: Fail unless slurmd is running
      ansible.builtin.assert:
        that: slurmd_unit.status.ActiveState == 'active'
        fail_msg: "slurmd is {{ slurmd_unit.status.ActiveState }} on {{ inventory_hostname }}"
        quiet: true

    - name: Wait until slurmd has registered again since the reboot
      ansible.builtin.command: scontrol show node {{ inventory_hostname }} --oneliner
      delegate_to: "{{ slurm_controller }}"
      register: node_back
      until: >-
        (node_back.stdout | regex_search('SlurmdStartTime=\\S+'))
        != (before_reboot.stdout | regex_search('SlurmdStartTime=\\S+'))
        and 'NOT_RESPONDING' not in node_back.stdout
      retries: 30
      delay: 10
      changed_when: false
      when: not ansible_check_mode

    - name: Return the node to service
      ansible.builtin.command: >-
        scontrol update nodename={{ inventory_hostname }} state=resume
      delegate_to: "{{ slurm_controller }}"
      changed_when: true
```

The actual change lives in its own file, `playbooks/tasks/maintenance.yml`, so this playbook never changes. In the lab it just records what was done:

```yaml
# The actual change goes here: a driver, a kernel, firmware, a config that needs a reboot.
- name: Record what was done and when
  ansible.builtin.copy:
    dest: /etc/cluster-maintenance
    content: "{{ maint_reason }}\n"
    owner: root
    group: root
    mode: "0644"
```

> [!NOTE]
> In the lab, the playbook ran with one extra play setting: `module_defaults` giving `ansible.builtin.reboot` a `boot_time_command` of `stat -c %Z /proc/1`. Containers share the host's boot ID, so the default check never saw a new boot and timed out after the container had restarted fine. Real nodes don't need it; the default is right for them.

---

## What each piece buys you

| Line | Without it |
| --- | --- |
| `serial: [1, "25%"]` | Every node at once (well, 20 at a time) |
| `order: sorted` | The canary is whichever host the inventory lists first. Sorting keeps it stable when someone reorders the inventory |
| `max_fail_percentage: 0` | By default the run stops only when *every* host in a batch fails. A canary batch of one stops either way, but in a batch of 100, 99 failures wouldn't. The percentage must be *exceeded*, so 0 means "any failure stops the run" |
| Drain, then wait for `drained` | `draining` means jobs are still running. Only `drained` means the node is empty |
| `drain_wait_retries` default 360 × 10 s | One hour per node. Raise it for long jobs, or use `-e drain_wait_retries=...` |
| Reason with a ticket number | `sinfo -R` tells everyone why the node is out, and who to ask |
| Health checks before resume | A broken node goes back into service and eats jobs |

Batch sizes from percentages are rounded down, with a minimum of one host (`pct_to_int` in ansible-core's source). On our five nodes, 25% is one node per batch; on 400 nodes it's 100. Pick a percentage that leaves enough of the cluster running.

Don't trust `--list-hosts` to tell you who the canary will be. In the lab it listed the hosts in a different order every time (`gpu001` first, once), while real runs always started with cn001. It shows *which* hosts, not in what order.

---

## Step 1: dry run

```bash
ansible-playbook playbooks/rolling-maintenance.yml -e maint_ticket=CHG-1047 --check --diff -l cn001
```

```text
-ansible maintenance CHG-1043
+ansible maintenance CHG-1047
cn001 : ok=6    changed=2    unreachable=0    failed=0    skipped=5
```

You see the change the maintenance would make, and that a reboot would happen. Nothing actually happened: in the lab, the node wasn't drained, wasn't rebooted (PID 1's start time was the same before and after), and the file still had the old ticket.

---

## The dry run that hung

The first version of this playbook didn't have the `when: not ansible_check_mode` lines, and its dry run never finished. We killed it after five minutes. With the retries turned down to two, it showed what was going on:

```text
TASK [Drain the node in Slurm]
skipping: [cn001]
TASK [Wait for its running jobs to finish]
FAILED - RETRYING: [cn001 -> head01]: Wait for its running jobs to finish (1 retries left).
FAILED - RETRYING: [cn001 -> head01]: Wait for its running jobs to finish (0 retries left).
```

In check mode, `command` doesn't run: the task returns `"Command would have run if not in check mode"` and an empty output. An empty output never equals `drained`, so `until` retried, 360 times, ten seconds apart. The drain was skipped too, so even a real `sinfo` couldn't have said `drained`.

Wait loops only mean something in a real run, so they're skipped in check mode. Same for the "remember when slurmd registered" task, which only feeds a wait loop.

---

## Step 2: canary, then the rest

Before the real run in the lab, we put a 45-second job on cn001 and another on cn002:

```text
JOBID NAME        STATE   NODELIST
4     long-cn001  RUNNING cn001
5     long-cn002  RUNNING cn002
```

```bash
ansible-playbook playbooks/rolling-maintenance.yml -e maint_ticket=CHG-1042
```

The controller's log tells the story better than Ansible's output:

```text
14:00:45 sched/backfill: _start_job: Started JobId=4 in batch on cn001
14:00:49 update_node: node cn001 reason set to: ansible maintenance CHG-1042
14:00:49 update_node: node cn001 state set to DRAINING
14:01:30 _job_complete: JobId=4 WEXITSTATUS 0
14:01:46 update_node: node cn001 state set to IDLE
```

cn001 was drained at 14:00:49 with its job still running. Ansible waited (five retries in its log) until the job **finished on its own** at 14:01:30 with exit 0. Then it did the change, rebooted, proved the node was back, and resumed it at 14:01:46. cn002's job had finished by the time its turn came. The run ended with exit 0, `failed=0` on every node, the change on all five, and `sinfo` showing all five idle.

---

## When the canary comes back broken

The story's second problem: a node that comes back wrong. We stood in for the bad driver by masking slurmd on cn001, so it wouldn't start after the reboot, and ran the playbook again:

```text
fatal: [cn001]: FAILED! => {"assertion": "slurmd_unit.status.ActiveState == 'active'", ... "msg": "slurmd is inactive on cn001"}
NO MORE HOSTS LEFT *************************************************************
cn001 : ok=8    changed=3    unreachable=0    failed=1
```

Exit 2. The run stopped after the canary. Look at what that left behind:

```text
REASON               USER      TIMESTAMP           NODELIST
ansible maintenance  root      2026-11-11T14:24:42 cn001
```

| Node | State |
| --- | --- |
| cn001 | Drained, with the ticket as the reason. No jobs will land on it |
| cn002, cn003, cn004, gpu001 | Untouched: no drain, no change, no reboot, still running jobs |

That's the point of a canary: the failure cost one node, and that node is parked safely.

---

## Rollback

There's no magic undo for a driver. Rollback means two things: fix or revert the node, and return it to service only once it's healthy. In the lab:

1. Fix the canary (here, unmask and start slurmd; in real life, roll back the package or the change in `maintenance.yml`):

```bash
ansible cn001 -b -m ansible.builtin.systemd_service -a 'name=slurmd masked=false state=started'
```

2. Return it to service, by hand, deliberately:

```bash
ansible head01 -b -m ansible.builtin.command -a 'scontrol update nodename=cn001 state=resume'
```

`sinfo` showed `cn001 idle`.

3. Then either stop there (the change is bad), or continue with the nodes that haven't had it yet:

```bash
ansible-playbook playbooks/rolling-maintenance.yml -e maint_ticket=CHG-1043 --limit 'nodes:!cn001'
```

That finished with exit 0 on the remaining four, all five idle, and the change recorded on every node.

> [!CAUTION]
> Rerunning without `--limit` drains and reboots *every* node again, including the ones that are done. This playbook is an operation, not a desired state: it isn't idempotent, by design.

---

## How we caught our own weak health check

Our first version had a different last check: "wait until `sinfo` says the node is `drained`" (drained and responding). It passed. But right after resume, `sinfo` showed cn002 as `idle*`; the asterisk means "not responding". The controller's log explained it:

```text
14:21:31 update_node: node cn002 state set to DRAINED
14:21:36 update_node: node cn002 state set to IDLE        <- our resume
14:21:37 Node cn002 now responding                         <- slurmd re-registering
```

The container rebooted in seconds, faster than the controller noticed it had gone. So `drained` was the controller's *old* opinion, and our check proved nothing. On real hardware the reboot takes minutes, but the same race exists: the controller only marks a node not responding after missed contacts.

The fix is the version above. Record `SlurmdStartTime` before the reboot, and wait until it has changed, meaning slurmd has started and registered since the reboot. On the next real run, cn003's slurmd started at 14:22:15 and the check saw the new time. To prove it fails when it should, we ran the record-and-wait pair on cn004 *without* a reboot: `SlurmdStartTime` never changed, and it failed after its retries, exit 2.

A one-second `idle*` right after resume still showed up once in the lab. It cleared on its own at the controller's next contact.

> [!TIP]
> For a real health check before resume, run [Node Health Check](/fields/system-administration/node-health-check/README.md) on the node as one more task. Checking that GPUs, mounts and InfiniBand came back is exactly what it's for.

---

## Back to 14:00

Run the story again with this playbook. At 14:00 the canary drains. It has a six-day job on it, so the playbook waits, and the job finishes on its own that evening. The node reboots onto the new driver, and it's one of the bad hardware revisions: no GPUs. slurmd doesn't come up healthy, the assertion fails, the run stops. One node is drained with `CHG-1042` as the reason; the rest of the cluster never noticed.

Next morning the admin reads `sinfo -R`, rolls the driver back on that one node, resumes it, and excludes that hardware revision from the change with a `--limit`. Then the rest goes through, one batch at a time, each node empty before it reboots. Nobody's six-day job was killed, and no job ever landed on a node without its GPUs.

**Takeaway:** for busy nodes, drain through Slurm, canary first, stop on the first failure, prove the node re-registered before resuming, and make sure your dry run is really dry.

**Next:** [Part 6, The Munge Key in Git](/fields/devops/ansible/secrets-and-vault.md), handles the secrets these playbooks need.

---

## References

- [Controlling playbook execution: strategies and more](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_strategies.html): `serial` with lists and percentages, `order`, rolling updates.
- [Error handling in playbooks](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_error_handling.html): `max_fail_percentage` (must be exceeded, not equaled), `any_errors_fatal`.
- [Controlling where tasks run: delegation](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_delegation.html): `delegate_to`.
- [Retrying a task until a condition is met](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_loops.html#retrying-a-task-until-a-condition-is-met): `until`, `retries`, `delay`.
- [Validating tasks: check mode and diff mode](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_checkmode.html): `ansible_check_mode` and how modules behave in check mode.
- [ansible.builtin.reboot](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/reboot_module.html): `reboot_timeout`, `boot_time_command`.
- [scontrol(1)](https://slurm.schedmd.com/scontrol.html): `update state=drain|resume`, `show node`, `SlurmdStartTime`.
- [sinfo(1)](https://slurm.schedmd.com/sinfo.html): node states (`draining`, `drained`, `*` for not responding) and `-R`.
- [Node Health Check](/fields/system-administration/node-health-check/README.md): health checks to run before returning a node to service.
