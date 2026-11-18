
# Ansible, for People Who Manage More Nodes Than They Can SSH Into


A story-first series for cluster admins who are comfortable with a root shell and tired of `for n in $(seq ...)` loops. Each page starts with something that went wrong, fixes it with Ansible, and goes back to the story at the end. The pages build one project, `cluster-ansible`, that manages a small Slurm cluster.

Written against **ansible-core 2.22.0** (released November 2026) on Python 3.13, with ansible-lint 26.11.0.

---

## Contents

| File | Description |
| --- | --- |
| [1. The Laptop That Ran Ansible 2.16](/fields/devops/ansible/getting-started.md) | A pinned install per project, which Python the controller and the nodes need, `ansible.cfg`, SSH host keys, and the first-run errors |
| [2. Four Nodes Said "Too Many Open Files"](/fields/devops/ansible/inventory-and-ad-hoc.md) | Inventory groups and ranges, `group_vars`, targeting patterns, ad-hoc commands, and checking a change in a fresh login |
| [3. The Playbook That Restarted slurmd Every Night](/fields/devops/ansible/idempotence-and-handlers.md) | `changed` vs `ok`, why `shell` lies, handlers, `--check --diff`, and the handler that never ran |
| [4. The GPU Node That Thought It Had 1000 MB](/fields/devops/ansible/roles-and-variables.md) | Roles, OS-specific variables, variable precedence, `hostvars` in templates, and a check that every node got the same config |
| [5. The Reboot That Killed a Week of Jobs](/fields/devops/ansible/rolling-maintenance.md) | Rolling maintenance: drain through Slurm, a canary, stop on first failure, a dry run that really is dry, and rollback |
| [6. The Munge Key in Git](/fields/devops/ansible/secrets-and-vault.md) | `ansible-vault`, rotating a leaked key, the 2.22 secret masking and where it stops, `no_log`, and a commit guard |
| [7. Cheatsheet](/fields/devops/ansible/cheatsheet.md) | Every step from the series in order, as copy-paste commands, with a quick-reference table |

---

## How the pages were tested

- **Lab:** six Ubuntu 24.04 nodes (`head01`, `cn001`–`cn004`, `gpu001`) running systemd, Slurm 23.11.4 and munge 0.5.15, in containers on a throwaway sandbox (Linux 6.18). The controller ran ansible-core 2.22.0 on Python 3.13.
- **Not run:** Rocky/RHEL steps. No Rocky image could be fetched in the sandbox, so those parts come from Red Hat and Fedora documentation and are marked on each page.
- **Lab artefacts are called out** where the container setup differed from real hardware: resource-limit caps, the boot-time check for reboots, and a Slurm scheduling quirk.
- **Failure paths too:** every check on these pages was also run against a broken input to prove it fails. Several of our own checks didn't fail at first; the pages show how we found out.

## Related pages

- [Node Health Check](/fields/system-administration/node-health-check/README.md): what to run on a node before you hand it back to Slurm (part 5).
- [VictoriaMetrics series](/fields/devops/victoriametrics/README.md): another stack you could deploy with the roles pattern from part 4.

<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [Ansible Cheatsheet: Every Step from the Series](/fields/devops/ansible/cheatsheet.md) — The Ansible series as direct steps - pinned install, ansible.cfg, inventory and host keys, ad-hoc commands, idempotent playbooks with handlers, a role, rolling maintenance, vault.
- [DevOps: Where Code Meets the Machines That Run It](/fields/devops/README.md)
- [Four Nodes Said "Too Many Open Files": Inventories and Ad-Hoc Commands](/fields/devops/ansible/inventory-and-ad-hoc.md) — Inventory groups and ranges, group_vars with overrides, targeting patterns, ad-hoc commands across the cluster, the node that was down, and checking a change in a fresh login.
- [Lab Build Cheatsheet: A Slurm AI Cluster in Containers](/fields/schedulers/slurm-ai-clusters/lab-build-cheatsheet.md) — Every step used to build the Slurm lab behind the pending-jobs and AI-cluster series - node image, Slurm 23.11 with accounting, topology, PyTorch, Enroot and Pyxis, health check, Slurm 26.05, metrics.
- [pam_slurm_adopt: Closing the Slurm SSH Backdoor](/fields/schedulers/slurm-cluster-operations/slurm-pam-adopt-ssh-access.md) — Why users can SSH into a node and escape their job's limits, and how pam_slurm_adopt closes the backdoor by admitting only users with a job there and adopting the session into its cgroup.
- [The GPU Node That Thought It Had 1000 MB: Roles and Variables](/fields/devops/ansible/roles-and-variables.md) — Turn a playbook into a role, load OS-specific variables with first_found, put site values in defaults not vars, use hostvars for per-node values in templates, and check every node got the same config.
- [The Laptop That Ran Ansible 2.16: An Install You Can Trust](/fields/devops/ansible/getting-started.md) — A pinned Ansible install per project, which Python the control machine and the nodes need, ansible.cfg, SSH host keys, and the errors you hit on the first runs.
- [The Munge Key in Git: Secrets, Vault and Rotation](/fields/devops/ansible/secrets-and-vault.md) — Keep secrets in an Ansible repo with vault, rotate a leaked munge key on every host at once, what 2.22's secret masking hides and misses, no_log, and a commit guard.
- and 2 more

</div>
