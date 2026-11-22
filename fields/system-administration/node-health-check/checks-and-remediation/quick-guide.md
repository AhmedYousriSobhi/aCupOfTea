---
id: nhc-checks-and-remediation-quick
title: "Write Checks, Fix Nodes and Troubleshoot NHC"
sidebar_label: "Quick guide: checks and fixes"
order: 9
summary: "Quick guide: add a custom NHC check, automate safe fixes with a guarded node doctor, and troubleshoot drains, timeouts and silent config changes."
level: advanced
type: [guide, reference]
domains: [systems-and-hpc, system-administration]
tags: [hpc, slurm, gpu]
relations:
  related: [nhc-custom-checks, nhc-auto-remediation, nhc-troubleshooting]
---

# Write Checks, Fix Nodes and Troubleshoot NHC

> **Quick guide for** parts 6 to 8: [Custom checks](/fields/system-administration/node-health-check/checks-and-remediation/custom-checks.md), [Auto-remediation](/fields/system-administration/node-health-check/checks-and-remediation/auto-remediation.md) and [Troubleshooting](/fields/system-administration/node-health-check/checks-and-remediation/troubleshooting.md). Use Part 1 to add a check, Part 2 to fix what it finds, Part 3 when a node misbehaves.

## Before you start

- Root on a test node. Every test below runs with `MARK_OFFLINE=0`, so nothing drains.
- NHC 1.5 on the nodes if you reboot from automation, and `RebootProgram` set in `slurm.conf`.
- The `ACME` and `acme_` names are examples: use your own site id.

## Part 1: add a check (part 6)

1. Try a check with no code first.

   ```bash
   * || check_cmd_status -t 3 -r 0 /usr/bin/nc -z lic01 27000
   * || check_file_contents /sys/kernel/mm/transparent_hugepage/enabled '/\[madvise\]/'
   ```

   **Expect:** the line passes silently.
   **If not:** write a module only when you need loops, per-device thresholds or cached data.

2. Write a module as `/etc/nhc/scripts/acme_gpu.nhc`.

   - The `.nhc` extension is required.
   - Name functions `check_<class>_<purpose>` and namespace globals (`ACME_GPU_...`).
   - Fail with `die 1 "clear message"` then `return 1`. Pass with `return 0`.
   - Gather once, cache in a global, bound every command with `timeout`, use full paths.

   **Expect:** the failure message becomes the `NHC:` reason in `sinfo -R`.

3. Add the lines to `nhc.conf`.

   ```bash
   {gpu[01-32]} || check_acme_gpu_count 8
   {gpu[01-32]} || check_acme_gpu_ecc 0
   ```

   **Expect:** the check runs only on the matching nodes.

4. Test the pass and the failure.

   ```bash
   bash -n /etc/nhc/scripts/acme_gpu.nhc
   nhc -l- -e 'check_acme_gpu_count 8' MARK_OFFLINE=0; echo "rc=$?"
   nhc -l- -e 'check_acme_gpu_count 9' MARK_OFFLINE=0; echo "rc=$?"
   ```

   **Expect:** rc=0 for 8, non-zero for 9 on an 8-GPU node.
   **If not:** point the command variable at a stub, for example `ACME_NVSMI=/tmp/fake-nvidia-smi`.

5. Keep slow DCGM diagnostics out of the periodic run.

   ```bash
   {gpu[01-32]} || check_acme_dcgm_diag 2 300
   ```

   **Expect:** this line lives in `/etc/nhc/nhc-deep.conf`, with `TIMEOUT=900` in `/etc/sysconfig/nhc-deep`.
   **If not:** run `dcgmi diag -r 1` on a known-bad and a known-good node and adjust the match.

## Part 2: fix nodes safely (part 7)

1. Fix in place with a check's own flag.

   ```bash
   * || check_ps_service -u root -S sshd
   * || check_ps_service -u munge -d munged -S munge
   ```

   **Expect:** this run fails and drains, the fix runs in the background, and the next run passes and resumes the node.
   **If not:** a fix that needs more than a few seconds belongs to the node doctor.

2. Run the node doctor from cron on the controller, every 10 minutes, as `/usr/local/sbin/nhc-node-doctor`.

   **Expect:** it starts in dry run (`DRY_RUN=1`) and only logs what it would do.
   **If not:** keep `MAX_ATTEMPTS=2`, `MAX_CONCURRENT=4` and the `REBOOTABLE` allowlist. Don't remove them.

3. Reboot with a plain `scontrol reboot "$node"`.

   **Expect:** the node reboots after its jobs finish, and the `NHC:` reason is kept.
   **If not:** with `ASAP` or `nextstate=`, Slurm clears the DRAIN flag and the node rejoins before verification.

4. After the retry budget is spent, drop the prefix so NHC never auto-resumes the node.

   ```bash
   scontrol update nodename="$node" reason="ESCALATED: ${reason#NHC: } (doctor gave up)"
   ```

   **Expect:** the node stays drained until a human resumes it.

5. For a deep verify after a reboot, claim the node first, then hand it back.

   ```bash
   scontrol update nodename="$node" reason="nhc-doctor: deep verify pending"
   scontrol reboot "$node"
   ssh "$node" '/usr/sbin/nhc -n nhc-deep -l-'
   scontrol update nodename="$node" reason="NHC: deep verify passed, awaiting periodic check"
   ```

   **Expect:** NHC resumes the node on its next clean periodic run.
   **If not:** on a failed deep check, set `ESCALATED: deep check failed after reboot`.

6. Send de-duplicated notifications for cron-driven contexts.

   ```bash
   */10 * * * * root /usr/sbin/nhc-wrapper -M ops@example.org -X 12h -n nhc-oob
   ```

   **Expect:** mail on a change, and a reminder every 12 hours while it persists.

## Part 3: troubleshoot (part 8)

1. Read the reason, rerun without draining, and trace when lost.

   ```bash
   sinfo -R
   tail -50 /var/log/nhc.log
   nhc -a -v -l- MARK_OFFLINE=0
   nhc -l- -e 'check_fs_mount_rw -f /scratch' MARK_OFFLINE=0
   BASH_XTRACEFD=33 33>/tmp/nhc-trace.out nhc -xdavl- MARK_OFFLINE=0
   nhc -V -V -V
   ```

   **Expect:** the failing check and the files NHC is using.
   **If not:** open an issue with the `-x` trace, your NHC version, distro and config lines.

2. Find a slow check.

   ```bash
   time nhc -a -v -l- -t 0 MARK_OFFLINE=0
   ```

   **Expect:** the slow check shows in the `-v` progress.
   **If not:** `df` on a dead NFS or Lustre mount is the usual suspect: set `DF_FLAGS="-Tkal"` and `DFI_FLAGS="-Tial"`.

3. When a node never comes back, walk this list.

   - The reason still starts with `NHC:`.
   - `HealthCheckNodeState` is not `NONDRAINED_IDLE`.
   - The node is not in `MAINT`, and the reason has no `(perm)` tag.
   - `grep -r MARK_OFFLINE /etc/nhc /etc/sysconfig/nhc /etc/default/nhc 2>/dev/null` shows no leftover `MARK_OFFLINE=0`.
   - All checks pass, so run with `-a`.

## If it fails

| What you see | Likely cause | Fix |
|---|---|---|
| A healthy node keeps draining | Wrong expectation for its class, or a memory check without a fudge | Fix the line, use `check_hw_physmem 512GB 512GB 3%` |
| Drained, reason not starting with `NHC:` | Not NHC's drain | Slurm, a prolog or epilog, or a human did it |
| Node never registers after boot | NHC fails at `slurmd` start | `journalctl -u slurmd -b \| grep -i health`, order the mount and GPU units |
| No NHC message, truncated log | Slurm killed NHC first | Lower NHC's `TIMEOUT` |
| Works by hand, fails under `slurmd` | A different `PATH` | Use full paths, test as root |
| Config change does nothing | Wrong context file, early-only variable, or a module without `.nhc` | Check `nhc -V -V -V`, move the variable to the sysconfig file |
| Exit 127 or 126 | Command not found, or not executable | Full path or `PATH`, `chmod +x` |
| `Unsupported RM detected` | NHC can't tell the resource manager | Set `NHC_RM=slurm` in `/etc/sysconfig/nhc` |

## Roll back

- Keep `DRY_RUN=1` on the node doctor until its log looks right.
- Set `MARK_OFFLINE=0` to stop NHC draining while you investigate.

**Don't:** reset error counters to make a check pass, kill user processes on nodes running jobs, or reboot during a cluster-wide event.

**Why it works:** [Custom checks](/fields/system-administration/node-health-check/checks-and-remediation/custom-checks.md), [Auto-remediation](/fields/system-administration/node-health-check/checks-and-remediation/auto-remediation.md) and [Troubleshooting](/fields/system-administration/node-health-check/checks-and-remediation/troubleshooting.md).
