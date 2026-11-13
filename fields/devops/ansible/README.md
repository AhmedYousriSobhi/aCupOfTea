
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