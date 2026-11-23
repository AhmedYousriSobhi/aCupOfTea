---
id: nhc-getting-started-quick
title: "Install, Configure and Roll Out NHC"
sidebar_label: "Quick guide: getting started"
order: 6
summary: "Quick guide: install NHC, draft and test its config, wire it into Slurm with a safe timeout, and roll it out with a dry run, a canary and a circuit breaker."
level: intermediate
type: [guide, reference]
domains: [systems-and-hpc, system-administration]
tags: [hpc, slurm]
relations:
  related: [nhc-build-and-install, nhc-writing-nhc-conf, nhc-slurm-integration, nhc-rollout-at-scale]
---

# Install, Configure and Roll Out NHC

> **Quick guide for** parts 2 to 5: [Build and install](/fields/system-administration/node-health-check/getting-started/build-and-install.md), [Writing nhc.conf](/fields/system-administration/node-health-check/getting-started/writing-nhc-conf.md), [Slurm integration](/fields/system-administration/node-health-check/getting-started/slurm-integration.md) and [Rolling out to a fleet](/fields/system-administration/node-health-check/getting-started/rollout-at-scale.md). Work through the four parts in order. You will end with NHC installed, configured, wired into Slurm, and rolled out behind a canary and a circuit breaker.

## Before you start

- Root on a test node, and `slurm.conf` access.
- `bash` 4.3 or newer, the usual coreutils and `make`.
- `clush` (ClusterShell) for the fleet steps.

## Part 1: install (part 2)

1. On RHEL-family nodes, install the release RPM.

   ```bash
   dnf install -y https://github.com/mej/nhc/releases/download/<version>/lbnl-nhc-<version>-<release>.el9.noarch.rpm
   rpm -q lbnl-nhc
   nhc -V
   ```

   **Expect:** `rpm -q` prints the package and `nhc -V` the version.
   **If not:** no RPM for your EL version? `rpmbuild --rebuild lbnl-nhc-<version>-<release>.src.rpm`.

2. On any other distro, use the release tarball.

   ```bash
   VER=1.5
   curl -LO https://github.com/mej/nhc/releases/download/${VER}/lbnl-nhc-${VER}.tar.xz
   tar xf lbnl-nhc-${VER}.tar.xz
   cd lbnl-nhc-${VER}
   ./configure --prefix=/usr --sysconfdir=/etc --libexecdir=/usr/libexec
   make test
   sudo make install
   ```

   **Expect:** every module reports `ok N/N`, ending with an "All N tests passed" line.
   **If not:** `bash: ./configure: No such file or directory` means you downloaded GitHub's auto-archive. Get the `lbnl-nhc-<version>.tar.xz` asset, or use a Git checkout and run `./autogen.sh` first.

3. Smoke test, without touching the scheduler.

   ```bash
   sudo nhc -e 'check_fs_mount_rw -f /' && echo "root fs is rw, NHC works"
   sudo nhc -d -v -t 0 -l- MARK_OFFLINE=0
   ```

   **Expect:** the first prints the message. The second may complain, because the stock config is generic.
   **If not:** put options first and `VAR=value` pairs last.

## Part 2: configure (part 3)

1. Generate a draft on a known-good node.

   ```bash
   sudo nhc-genconf
   ```

   **Expect:** `/etc/nhc/nhc.conf.auto` with this host's name as the target.
   **If not:** on a heterogeneous cluster run `clush -bw @compute "/usr/sbin/nhc-genconf -H '*' -c -"` and read each identical block as one hardware class.

2. Write each line as `target || check`, cheapest and highest-signal checks first.

   ```bash
   * || check_fs_mount_rw -f /
   {gpu[01-32]} || check_hw_cpuinfo 2 96 192
   !login* || check_ps_userproc_lineage log syslog
   ```

   **Expect:** a glob, `/regex/`, `{node[range]}` or `!negated` target on every line.
   **If not:** only one bracketed range per name, no commas inside brackets: write `{cn[001-010],cn015}`.

3. Put early settings in `/etc/sysconfig/nhc` (or `/etc/default/nhc`), not in the config.

   ```bash
   NHC_RM=slurm
   TIMEOUT=50
   ```

   **Expect:** both values take effect.
   **If not:** `TIMEOUT`, `CONFFILE`, `DETACHED_MODE`, `LOGFILE`, `NAME` and `HOSTNAME` don't work from the config file.

4. Iterate until silent.

   ```bash
   sudo nhc -a -v -l- MARK_OFFLINE=0
   echo $?
   ```

   **Expect:** no output and exit 0.
   **If not:** each failure is a config bug (fix the line) or a node bug (fix the node).

## Part 3: wire it into Slurm (part 4)

1. Add three lines to `slurm.conf` on every node and the controller.

   ```ini
   HealthCheckProgram=/usr/sbin/nhc
   HealthCheckInterval=300
   HealthCheckNodeState=ANY,CYCLE
   ```

   **Expect:** after `scontrol reconfigure`, `scontrol show config | grep -i healthcheck` shows all three.
   **If not:** the default `HealthCheckInterval` is 0, which means never.

2. Keep NHC's timeout under Slurm's. NHC's `TIMEOUT` defaults to 30 s and Slurm kills the program at 60 s.

   **Expect:** a clean "timed out" failure and a drain with a reason.
   **If not:** NHC dies silently and nothing drains. Move minute-long checks to a deep context, or use `DETACHED_MODE=1`.

3. Prove the loop on a test node.

   ```bash
   umount -l /scratch
   sinfo -R -n cn042
   mount /scratch
   ```

   **Expect:** a reason starting with `NHC:` while broken, and a resume at the next clean run.
   **If not:** check `/var/log/nhc.log`.

4. Drain by hand only with your own reason.

   ```bash
   scontrol update nodename=cn042 state=drain reason="ahmed: BIOS update, ticket 4711"
   ```

   **Expect:** NHC never resumes it.
   **If not:** a drain without a reason is not touched by NHC either, and nobody remembers why.

## Part 4: roll out (part 5)

1. Inventory the hardware classes.

   ```bash
   clush -bw @compute "/usr/sbin/nhc-genconf -H '*' -c -"
   ```

   **Expect:** one block per class.

2. Dry run fleet-wide, twice, at different times of day.

   ```bash
   clush -bw @compute "/usr/sbin/nhc -a -l- MARK_OFFLINE=0" 2>&1 | tee nhc-dryrun.txt
   ```

   **Expect:** healthy nodes print nothing, failures group by message.
   **If not:** a failure on most nodes of a class is a config bug, on a handful a node bug, on random nodes a flaky check.

3. Canary inside `nhc.conf`, then widen to `{cn[001-128]}`, then delete both lines.

   ```bash
                    * || export MARK_OFFLINE=0
         {cn[001-016]} || export MARK_OFFLINE=1
   ```

   **Expect:** only `cn001-016` can drain.

4. Add a circuit breaker on the controller, run every few minutes (`/usr/local/sbin/nhc-circuit-breaker`, `MAX_PCT=5`).

   **Expect:** an alert when NHC has drained `MAX_PCT` percent of nodes or more.
   **If not:** as a kill switch, push `* || export MARK_OFFLINE=0` to the top of `nhc.conf`.

5. Dry run every later change on the fleet before installing it.

   ```bash
   clush -bw @compute "/usr/sbin/nhc -a -l- -c /tmp/candidate.conf MARK_OFFLINE=0"
   ```

   **Expect:** the same quiet output as step 2.

## If it fails

| What you see | Likely cause | Fix |
|---|---|---|
| `bash: ./configure: No such file or directory` | GitHub auto-archive | Use the `.tar.xz` asset or `./autogen.sh` |
| A healthy node drains after a variable line | `[[ ... ]] && ...` returned non-zero and counted as a failed check | Use `if ... fi` |
| A command-line override is ignored | The config file beats the command line | Apply your value only while the variable holds NHC's default |
| NHC dies silently, nothing drains | Slurm's timeout fired first | Make NHC's `TIMEOUT` shorter |
| Every node drains after a push | e.g. `check_hw_physmem 512GB 512GB` with no fudge factor | Add a fudge such as `3%`, push the kill switch |
| Drained nodes never resume | `HealthCheckNodeState=NONDRAINED_IDLE` | Choose it on purpose, or use another state |

## Roll back

- Set `MARK_OFFLINE=0` in `nhc.conf` so NHC keeps logging and stops draining.
- Keep `nhc.conf` and custom `.nhc` modules in Git, so `git log -p nhc.conf` shows which change did it.

**Don't:** use GitHub's "Source code" archives, drain without a reason, or let the circuit breaker auto-resume nodes.

**Why it works:** [Build and install](/fields/system-administration/node-health-check/getting-started/build-and-install.md), [Writing nhc.conf](/fields/system-administration/node-health-check/getting-started/writing-nhc-conf.md), [Slurm integration](/fields/system-administration/node-health-check/getting-started/slurm-integration.md) and [Rolling out to a fleet](/fields/system-administration/node-health-check/getting-started/rollout-at-scale.md).
