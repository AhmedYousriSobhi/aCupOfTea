---
id: slurm-cluster-operations-quick
title: Run Slurm Cluster Operations Without Losing Jobs
order: 8
sidebar_label: "Quick guide: cluster operations"
summary: Copy-paste steps for a drained node, a maintenance reservation, a reboot, an upgrade and SSH access, each with the expected output.
level: intermediate
type: [guide, reference]
domains: [systems-and-hpc, schedulers]
tags: [slurm, hpc, quick]
relations:
  related: [slurm-spool-dir-full, slurm-kill-task-failed, slurm-reservations-and-maintenance, slurm-reboot-order, slurm-upgrade-order, slurm-pam-adopt-ssh-access]
---

# Run Slurm Cluster Operations Without Losing Jobs

> **Quick guide for** the [Cluster operations series](/fields/schedulers/slurm-cluster-operations/README.md).
> Use it at the terminal when a node is drained or a maintenance window is coming. You end with a node back in service, or a window that did not kill a job.

## Before you start

- Root on the controller and the nodes, plus OOB/BMC/IPMI console access to every server.
- A hidden root-only partition and a small test job for after the work.
- Backups, taken before any upgrade: `StateSaveLocation`, the config directory and the accounting database.

---

## Part 1: A node drained with "SlurmdSpoolDir is full"

1. Confirm the reason.

   ```bash
   sinfo -R
   scontrol show node <node> | grep -iE 'reason|state'
   ```

   **Expect:** reason `SlurmdSpoolDir is full`.
   **If not:** go to Part 2.

2. Find the full filesystem.

   ```bash
   df -h /var/spool/slurmd /tmp /var/tmp /var/log
   df -i /var/spool/slurmd
   ```

   **Expect:** one filesystem full, or `df -i` full (inodes).
   **If not:** step 3.

3. Find the culprit.

   ```bash
   du -sh /tmp /var/tmp /var/log /home 2>/dev/null
   lsof +L1
   ```

   **Expect:** a huge directory, or a deleted-but-open file (`df` full, `du` small).
   **If not:** read the logs from the time in the reason.

4. Free the temp files, then resume.

   ```bash
   df -h /var/spool/slurmd
   scontrol update NodeName=<node> State=RESUME
   sinfo -n <node>
   ```

   **Expect:** the node is idle and a job starts and finishes.
   **If not:** it drains again within the hour, so something still fills the disk.

**Don't:** `rm` inside `SlurmdSpoolDir`. It holds scripts and sockets of running jobs.

---

## Part 2: A node drained with "Kill task failed"

1. Read the reason and the timers.

   ```bash
   sinfo -R
   scontrol show config | grep -Ei 'killwait|unkillable'
   ```

   **Expect:** reason `Kill task failed`.
   **If not:** check whether your epilog returned non-zero.

2. Look for processes the kernel will not release.

   ```bash
   ps -eo pid,user,stat,wchan:32,cmd | awk '$3 ~ /^D/'
   ```

   **Expect:** no process in `D` state.
   **If not:** fix the filesystem path, or reboot the node (Part 4).

3. Resume only when the node is clean.

   ```bash
   scontrol update NodeName=<node> State=RESUME
   ```

   **Expect:** the node leaves the drain.
   **If not:** a node stays drained until a human resumes it.

4. Keep the evidence next time: set `UnkillableStepProgram=/etc/slurm/unkillable.sh` in `slurm.conf`.

**Don't:** raise `UnkillableStepTimeout` as the fix. It only delays the drain.

---

## Part 3: A maintenance window that does not kill jobs

1. Create the reservation.

   ```bash
   scontrol create reservation ReservationName=maint \
       StartTime=now+10minutes Duration=60 Nodes=node2 \
       Flags=MAINT,IGNORE_JOBS Users=root
   ```

   **Expect:** `Reservation created: maint`.
   **If not:** read the error, then check the node name.

2. Check it.

   ```bash
   scontrol show reservation maint
   sinfo -T
   ```

   **Expect:** `State=INACTIVE` until the window opens.
   **If not:** the reservation was not saved, so recreate it.

3. Check what is running on the nodes.

   ```bash
   squeue -w node2 -o "%i %u %L"
   ```

   **Expect:** every time limit ends before the window.
   **If not:** talk to that user. Running jobs are not killed when the window opens.

4. When the work is done, release the nodes.

   ```bash
   scontrol delete ReservationName=maint
   sinfo -N -o "%N %T"
   ```

   **Expect:** nodes show `idle`.
   **If not:** check the reservation again with `sinfo -T`.

**Reserve for a person:** `sbatch --reservation=demo -w node1 job.sh`.

**Don't:** expect jobs without `--time` to fit, because they inherit the partition `MaxTime`.

---

## Part 4: Reboot

**Compute nodes only** (needs `RebootProgram` in `slurm.conf`):

```bash
scontrol reboot ASAP nextstate=RESUME reason="kernel CHG-2001" cn[001-400]
```

**Expect:** `sinfo -R` shows `reboot^` or `draining@`, then the node resumes.
**If not:** set `nextstate=RESUME` explicitly.

**Control plane too** (this order, one step each):

1. Create a `MAINT` reservation after the running jobs end.
2. Put `/etc/nologin` on the front-end nodes.
3. Check `State=DOWN` on the partitions in `slurm.conf`.
4. Stop and disable `slurmctld`, then `slurmdbd`.
5. Back up the SQL database. Stop and disable MariaDB/MySQL.
6. Reboot the Slurm and DB servers.
7. Start DB, then `slurmdbd`, then `slurmctld`. **Expect:** partitions still `DOWN`.
8. Reboot the front-ends, re-apply `/etc/nologin`, check InfiniBand, mounts and Slurm access, then remove `/etc/nologin`.
9. Reboot the compute nodes and set the state to `idle`.
10. Set the hidden partition `UP` and run the test job. **Expect:** it runs clean.
11. Set the real partitions `State=UP`.

**Don't:** trust "it booted". Kernel changes can break IB drivers.

---

## Part 5: Upgrade

1. Check the hop. From 24.11 on, a release accepts the previous three. **Expect:** your version is in the target's list.
   **If not:** go through an intermediate version and verify it first.

2. Back up.

   ```bash
   scontrol show config | grep StateSaveLocation
   mysqldump --databases slurm_acct_db > backup.sql
   ```

   **Expect:** a state directory path, the config directory (usually `/etc/slurm/`) and a dump file.
   **If not:** stop. Do not continue without all three.

3. `slurmdbd` first. Stop it (`sacctmgr shutdown` or `systemctl stop slurmdbd`) and wait until it is fully down. Upgrade its packages, then run the first start by hand:

   ```bash
   sudo -u slurm slurmdbd -D
   ```

   **Expect:** `sacct` and `sacctmgr` return data after the conversion (Ctrl+C when it finishes).
   **If not:** read the log. Do not start it through systemd on the first run.

4. `slurmctld`, then `slurmd`. Raise `SlurmdTimeout` and `SlurmctldTimeout`, run `scontrol reconfig`, stop `slurmctld`, back up `StateSaveLocation`, upgrade, start `slurmd` then `slurmctld`. **Expect:** a job starts and finishes.
   **If not:** keep the timeouts raised and read the logs.
   Then put the timeouts back and run `scontrol reconfig` again.

5. Clients and plugins.

   ```bash
   sinfo --json=v0.0.41 | my_site_script
   ldd /path/to/binary | grep slurm
   ```

   **Expect:** pinned JSON output, and no versioned `libslurm.so`.
   **If not:** recompile.

**Don't:** call it finished until the jobs from before the upgrade have drained.
**Roll back:** there is no undo once a daemon has started. Restore `StateSaveLocation`, the config directory and the database.

---

## Part 6: SSH only for users with a job

1. In `slurm.conf`: `task/cgroup` and `PrologFlags=contain`.
2. In `/etc/ssh/sshd_config`: `UsePAM yes`.
3. In the `sshd` PAM file: `account required pam_slurm_adopt.so`.
4. Switch off `pam_systemd`:

   ```bash
   sed -i 's/^session\toptional\tpam_systemd.so/#&/' /etc/pam.d/common-session
   ```

5. Keep a door for admins:

   ```bash
   groupadd -f hpcadmins
   usermod -aG hpcadmins admin
   printf '+:(hpcadmins):ALL\n-:ALL:ALL\n' >> /etc/security/access.conf
   ```

   Then use these PAM lines:

   ```text
   account    sufficient    pam_access.so
   account    required      pam_slurm_adopt.so action_adopt_failure=deny action_generic_failure=deny
   ```

   **Expect:** a user with a job lands in `job_2/step_extern`. A user without one gets `Access denied by pam_slurm_adopt`.
   **If not:** see the table below.

**Don't:** log out of root before a second session proves the change. A PAM mistake locks everyone out.

---

## Tips and tricks

- Email yourself the `Reason` of every newly drained node from a cron job, so a 3 a.m. drain becomes a 9 a.m. one.
- Put the ticket in `reason=` when you reboot. It is what `sinfo -R` shows.
- Alert early: a node health check on free space, run through `HealthCheckProgram`, turns a surprise drain into a warning.
- Give each job its own temp directory with the `namespace/tmpfs` plugin (`PrologFlags=Contain` and a `job_container.conf`). Before 25.11 it is `job_container/tmpfs`.
- Set `TmpFS=/scratch` if that is where jobs write. Jobs can then ask for space with `--tmp`.
- Before an upgrade, purge old accounting records. A smaller database means a shorter dump and schema update.
- For a self-built Slurm, install each version in its own directory and point a symlink at the active one.

## Warnings

> [!WARNING]
> There is no undo once any Slurm daemon has started after an upgrade. Back up `StateSaveLocation`, the config directory and the database first.

- A running job is not killed when a maintenance window opens. Check its time limit before the window.
- A routine system update can pull in the EPEL Slurm package. Add `exclude=slurm*` to the `[epel]` section.
- Do not start `slurmdbd` through systemd the first time after an upgrade. If the conversion outlasts the unit's start timeout, systemd kills it halfway, which can lose data.
- Put `SlurmdTimeout` and `SlurmctldTimeout` back after the upgrade, or a dead node takes far too long to notice.
- `/etc/nologin` is wiped when a front-end boots. Re-apply it.
- Mass cancels can drain nodes in batches when they all hit the same stalled mount.

## If it fails

| What you see | Likely cause | Fix |
|---|---|---|
| Drained, `df` full, `du` small | Deleted file held open | `lsof +L1` |
| Drained after a job, `slurmd` log shows an epilog error | The epilog returned non-zero | Fix the epilog, then resume |
| Short jobs do not run before the window | No `--time` | Require `--time` |
| User asks why a job waits during maintenance | Reason text does not mention the reservation | `sinfo -T` |
| `slurmdbd` died halfway through an upgrade | First start went through systemd | Run `sudo -u slurm slurmdbd -D` by hand |
| SSH session lands in `session-15.scope` | `pam_systemd` still on | Comment it out in `common-session` |

**Why it works:** [spool dir](/fields/schedulers/slurm-cluster-operations/slurm-spool-dir-full.md), [kill task failed](/fields/schedulers/slurm-cluster-operations/slurm-kill-task-failed.md), [reservations](/fields/schedulers/slurm-cluster-operations/slurm-reservations-and-maintenance.md), [reboot order](/fields/schedulers/slurm-cluster-operations/slurm-reboot-order.md), [upgrade order](/fields/schedulers/slurm-cluster-operations/slurm-upgrade-order.md), [SSH access](/fields/schedulers/slurm-cluster-operations/slurm-pam-adopt-ssh-access.md). Next: [smoke tests](/fields/schedulers/slurm-smoke-tests/README.md).
