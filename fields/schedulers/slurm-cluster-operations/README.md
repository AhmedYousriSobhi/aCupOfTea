
# Slurm Cluster Operations

The admin shelf. The first four pages are about planned work: blocking nodes, rebooting, upgrading and knowing what changed between versions. The last three are about access and about nodes that drain for reasons that look unrelated to the real cause.

Pages 1 to 4 are best read in order before a maintenance window. Pages 5 to 7 stand alone.

---

## Contents

| File | Description |
| --- | --- |
| [1. Calling Dibs on Nodes](/fields/schedulers/slurm-cluster-operations/slurm-reservations-and-maintenance.md) | Reserving nodes for maintenance or people, and what happens to jobs that fit or overlap |
| [2. Rebooting a Slurm Cluster](/fields/schedulers/slurm-cluster-operations/slurm-reboot-order.md) | Rebooting a cluster without losing jobs: drain, lock access, control plane first |
| [3. Upgrading Slurm](/fields/schedulers/slurm-cluster-operations/slurm-upgrade-order.md) | The order to upgrade daemons, the version window, and the parts that bite |
| [4. The Changelog Nobody Reads](/fields/schedulers/slurm-cluster-operations/slurm-version-changes.md) | What changed between Slurm 23.11 and 26.05, plus the security timeline |
| [5. The SSH Backdoor](/fields/schedulers/slurm-cluster-operations/slurm-pam-adopt-ssh-access.md) | Closing SSH access that escapes job limits with `pam_slurm_adopt` |
| [6. Kill Task Failed](/fields/schedulers/slurm-cluster-operations/slurm-kill-task-failed.md) | Why jobs fail to die on uninterruptible sleep, drain the node, and how to debug it |
| [7. SlurmdSpoolDir Is Full](/fields/schedulers/slurm-cluster-operations/slurm-spool-dir-full.md) | The "SlurmdSpoolDir is full" drain: the real culprit and a triage runbook |

---

## Related pages

- [Schedulers: the traffic controller](/fields/schedulers/slurm-intro.md): the starting point for the whole Slurm set.
- [Inside a Slurm job](/fields/schedulers/slurm-inside-a-job/README.md): the `slurmstepd` and cgroup background behind pages 5 to 7.
- [Backfill tuning](/fields/schedulers/slurm-backfill-tuning.md): why reservations change start-time estimates.
- [Node health check](/fields/system-administration/node-health-check/README.md): automated checks that drain bad nodes.
