---
id: nhc-writing-nhc-conf
title: Writing nhc.conf That Actually Fits Your Cluster
sidebar_label: "3. Writing nhc.conf"
order: 3
summary: The config syntax, match strings, variables and contexts, plus copy-ready starter configs for CPU, GPU and login nodes.
level: intermediate
type: guide
domains: [systems-and-hpc]
tags: [hpc, gpu]
relations:
  prerequisites: [nhc-build-and-install]
---

# Writing nhc.conf That Actually Fits Your Cluster

> **Part 3 of the [Node Health Check series](/fields/system-administration/node-health-check/README.md).** The config *is* your health policy. This is where NHC stops being a tool and starts being *your* bouncer.

## Table of Contents
- [Anatomy of a line](#anatomy-of-a-line)
- [Match strings: who runs what](#match-strings-who-runs-what)
- [Let the machine write the first draft: nhc-genconf](#let-the-machine-write-the-first-draft-nhc-genconf)
- [Variables, and the precedence trap](#variables-and-the-precedence-trap)
- [The checks you'll actually use](#the-checks-youll-actually-use)
- [Starter config: a real cluster](#starter-config-a-real-cluster)
- [Contexts: one binary, many personalities](#contexts-one-binary-many-personalities)
- [Iterate until silent](#iterate-until-silent)

---

## Anatomy of a line

```bash
# comments and blank lines are ignored
   target   ||   check_function  arg1 arg2 ...
```

- **target**: which hosts run this line (a *match string*, next section).
- **`||`**: the separator. Yes, it looks like a shell "or". It isn't one here.
- **check**: any shell command that returns success or failure. In practice, an NHC check function such as `check_fs_mount_rw`.

Lines are read top to bottom; the ones whose target matches the node's hostname are queued and executed **in order**. Order matters twice: variable assignments must come *before* the checks that use them, and by default the first failing check ends the run, so put cheap, high-signal checks first.

---

## Match strings: who runs what

NHC's "match string" syntax shows up everywhere (targets, process names, mount sources, command output), so learn it once:

| Form | Delimiters | Example | Matches |
|------|-----------|---------|---------|
| **Glob** | none | `cn*` | `cn001`, `cn-gpu7` |
| **Regex** | `/.../` | `/^gpu[0-9]{3}$/` | `gpu001`…`gpu999` |
| **Node range** | `{...}` | `{cn[001-128],gpu[01-16]}` | Slurm-style hostlists |
| **External** (1.4.2+) | your choice, e.g. `<...>` | `<gpu-nodes>` | whatever your helper command says |
| **Negated** | leading `!` | `!login*` | everything *except* login nodes |

```bash
                  * || check_fs_mount_rw -f /
          {cn[001-512]} || check_hw_cpuinfo 2 128 128
         /^gpu/ || check_nvsmi_healthmon
          !login* || check_ps_userproc_lineage log syslog
```

> [!WARNING]
> Node ranges in NHC are simpler than Slurm's. Only **one** bracketed range per name, no commas inside brackets. `{cn[001-010,015]}` is invalid; write `{cn[001-010],cn015}`.

The target is matched against `$HOSTNAME`, which NHC reads from the kernel. If your nodes report FQDNs (`cn001.cluster.local`), your globs need to account for that, or match on the short name with a regex like `/^cn0[0-9]+\./`.

---

## Let the machine write the first draft: nhc-genconf

Counting sockets and kilobytes by hand is a fine way to waste an afternoon. `nhc-genconf` (1.4.1+) scans the node with the same code NHC uses and writes `/etc/nhc/nhc.conf.auto`:

```bash
sudo nhc-genconf                 # writes /etc/nhc/nhc.conf.auto with this host's name as the target
sudo nhc-genconf -H '*' -c -     # use '*' as the target and print to stdout
```

On a heterogeneous cluster, run it everywhere and let ClusterShell group identical results, which shows you your hardware *classes* in one screen:

```bash
clush -bw @compute "/usr/sbin/nhc-genconf -H '*' -c -"
# or: pdsh -a "/usr/sbin/nhc-genconf -H '*' -c -" | dshbak -c
```

Each block of identical output is one hardware class. Turn each into a node-range target, and the odd node out (the one with 3 DIMMs short of its siblings) just introduced itself.

> [!CAUTION]
> `nhc-genconf` records what the node **has**, not what it **should have**. If you generate the config on a node with a dead DIMM, you've just declared the dead DIMM normal. Generate on a few known-good nodes per class and compare.

---

## Variables, and the precedence trap

Settings are plain shell variables, and you can set them in three places:

1. **Command line**, as trailing `VAR=value` arguments (`nhc -d MARK_OFFLINE=0`).
2. **sysconfig file**: `/etc/sysconfig/nhc` (RHEL) or `/etc/default/nhc` (Debian-ish), sourced early.
3. **The config file**, with the normal line syntax: `* || export VAR=value`.

Two traps catch nearly everyone:

**Trap 1: the config file beats the command line.** Unlike almost every other CLI tool, a value set in `nhc.conf` is *not* overridden by `VAR=value` on the command line, because of how bash initializes things. If you want a command-line override to win, only apply your site value when the variable still holds NHC's built-in default (99 for `MAX_SYS_UID`):

```bash
# Site default 999, but `nhc MAX_SYS_UID=499` on the command line still wins
* || if [[ "$MAX_SYS_UID" == "99" ]]; then export MAX_SYS_UID=999; fi
```

Why `if ... fi` and not the shorter `[[ ... ]] && ...`? Every config line is executed as a check. When the test is false, the `&&` form returns non-zero, and NHC counts that as a **failed check**. Congratulations, you just drained a healthy node with a variable assignment.

The cleaner habit: keep site-wide defaults in the sysconfig file, and keep `nhc.conf` for checks plus per-host tweaks.

**Trap 2: some variables are "early" only.** `TIMEOUT`, `CONFFILE`, `DETACHED_MODE`, `LOGFILE`, `NAME`, `HOSTNAME` and a few others **don't work from the config file**. By the time the config line runs, the watchdog is already armed or the file already open. Put them in the sysconfig file or on the command line.

A good `/etc/sysconfig/nhc`:

```bash
# /etc/sysconfig/nhc  (or /etc/default/nhc)
NHC_RM=slurm          # don't rely on auto-detection
TIMEOUT=50            # stay under Slurm's 60 s kill (see part 4)
```

---

## The checks you'll actually use

NHC ships dozens of checks. These cover 90% of real configs:

| Area | Check | Example |
|------|-------|---------|
| Filesystems | `check_fs_mount_rw` / `check_fs_mount_ro` | `check_fs_mount_rw -t nfs -s 'nas01:/export/home' -f /home` |
| | `check_fs_free`, `check_fs_used`, `check_fs_ifree` | `check_fs_free /tmp 10%` |
| CPU / memory | `check_hw_cpuinfo sockets cores threads` | `check_hw_cpuinfo 2 128 128` |
| | `check_hw_physmem min max [fudge]` | `check_hw_physmem 512GB 512GB 3%` |
| | `check_hw_mcelog` | needs `mcelog`; newer distros use `rasdaemon` instead |
| Network | `check_hw_ib rate [device]` | `check_hw_ib 400 mlx5_0` (NDR) |
| | `check_hw_eth`, `check_net_link` (1.5) | `check_net_link eno1` |
| | `check_net_ping` | `check_net_ping -W 2 -c 2 slurmctl01` |
| Processes | `check_ps_service` | `check_ps_service -u root -S sshd` |
| | `check_ps_unauth_users`, `check_ps_userproc_lineage` | catch stray user processes not started by `slurmd` |
| | `check_ps_loadavg` | `check_ps_loadavg '' 300` |
| GPUs | `check_nvsmi_healthmon`, `check_nvgpu_smi` (1.5) | wraps `nvidia-smi` |
| Anything | `check_cmd_output`, `check_cmd_status`, `check_file_contents` | turn any command into a check |

Sizes take suffixes (`kB`, `MB`, `GB`, `TB`) and the memory checks accept a **fudge factor**. Use it: the kernel never reports exactly the RAM on the invoice, and firmware updates shift it by a few MB.

> [!TIP]
> On nodes that mount NFS or Lustre, set `* || DF_FLAGS="-Tkal"` (and `DFI_FLAGS="-Tial"`) before any `check_fs_free`/`check_fs_used` lines. The `-l` makes `df` skip network filesystems, so a dead NFS server can't hang your local-disk checks. Upstream calls this *strongly recommended*.

---

## Starter config: a real cluster

A fictional but realistic cluster: 512 CPU nodes `cn001-512`, 32 GPU nodes `gpu01-32` (8 GPUs, NDR InfiniBand each), two login nodes. Adjust the numbers to your hardware; keep the structure.

```bash
#######################################################################
# /etc/nhc/nhc.conf  -- ACME cluster. Managed by Ansible, edits get overwritten.
#######################################################################

### Global settings (things allowed in the config file)
                     * || export PATH="$PATH:/opt/acme/bin"
                     * || DF_FLAGS="-Tkal"
                     * || DFI_FLAGS="-Tial"
                     * || export MAX_SYS_UID=999

### 1. Cheapest, highest-signal checks first: is the OS sane?
                     * || check_fs_mount_rw -f /
                     * || check_fs_mount_rw -t tmpfs -f /dev/shm
                     * || check_fs_free /tmp 5%
                     * || check_fs_ifree /tmp 1k
                     * || check_ps_service -u root -S sshd
                     * || check_ps_service -u munge -d munged -S munge

### 2. Shared filesystems (the #1 black-hole cause)
                     * || check_fs_mount_rw -t nfs -s 'nas01:/export/home' -f /home
              !login* || check_fs_mount_rw -t lustre -s '*@o2ib*:/scratch' -f /scratch

### 3. Hardware inventory, per class
         {cn[001-512]} || check_hw_cpuinfo 2 128 128
         {cn[001-512]} || check_hw_physmem 512GB 512GB 3%
         {gpu[01-32]}  || check_hw_cpuinfo 2 96 192
         {gpu[01-32]}  || check_hw_physmem 2TB 2TB 3%
                     * || check_hw_swap 0 0

### 4. Fabric
         {cn[001-512]} || check_hw_ib 200 mlx5_0
         {gpu[01-32]}  || check_hw_ib 400 mlx5_0
                     * || check_net_ping -W 2 -c 2 slurmctl01

### 5. GPUs
         {gpu[01-32]}  || check_nvsmi_healthmon
         {gpu[01-32]}  || check_cmd_dmesg -m '!/NVRM: Xid \(PCI:[^)]*\): (48|79|94|95|119),/' -M 'Critical GPU Xid in kernel log'

### 6. Hygiene on compute nodes only: nobody runs outside Slurm
              !login* || check_ps_unauth_users log syslog
              !login* || check_ps_userproc_lineage log syslog
```

Notes on the choices:

- **Section 1 runs first** because if `/` is read-only or `sshd` is dead, nothing else matters.
- **`check_ps_service -S`** restarts a missing daemon *and* fails the check, so the node drains now and comes back on the next clean run. That's auto-remediation in one flag; [part 7](/fields/system-administration/node-health-check/auto-remediation.md) goes deeper.
- **Swap pinned to zero** catches the node that booted the wrong image with a swap partition.
- **The Xid line** fails if the kernel log contains the listed, hardware-flavored NVIDIA Xid codes (double-bit ECC, fallen off the bus and friends). Xids stay in `dmesg` until reboot, which is what you want here: these need a reset anyway. Tune the list to your GPUs and NVIDIA's current Xid catalogue. [Part 6](/fields/system-administration/node-health-check/custom-checks.md) builds richer GPU checks.
- **The rogue-process checks only log** at first. Switch to `kill` only after you've watched the logs for a week and trust them.

---

## Contexts: one binary, many personalities

A *context* is a named configuration. The name comes from how NHC was invoked (default: `nhc`), and it decides which files load:

| Invocation | Config file | sysconfig file |
|-----------|-------------|----------------|
| `nhc` | `/etc/nhc/nhc.conf` | `/etc/sysconfig/nhc` |
| `nhc -n nhc-epilog` | `/etc/nhc/nhc-epilog.conf` | `/etc/sysconfig/nhc-epilog` |
| `nhc-deep` (a symlink to `nhc`) | `/etc/nhc/nhc-deep.conf` | `/etc/sysconfig/nhc-deep` |

A tidy layout for the "four moments" from [part 1](/fields/system-administration/node-health-check/why-node-health-check.md#four-moments-to-check-a-node):

```bash
ln -s nhc /usr/sbin/nhc-epilog     # fast post-job checks
ln -s nhc /usr/sbin/nhc-deep       # slow diagnostics, run by hand or by remediation
```

- `nhc.conf`: periodic, well under a minute.
- `nhc-epilog.conf`: a handful of seconds; "did that job leave a mess?"
- `nhc-deep.conf`: minutes are fine; DCGM level 2, memory tests, IB bandwidth.

---

## Iterate until silent

The loop that turns a draft into a production config:

```bash
# See EVERY failure at once, to the terminal, with no draining
sudo nhc -a -v -l- MARK_OFFLINE=0
# ...edit nhc.conf, repeat until it prints nothing and exits 0
echo $?
```

- `-a` runs all checks and returns the number that failed.
- `-v` prints each check (with its number, on 1.5) as it runs.
- `-l-` sends log output to the terminal instead of `/var/log/nhc.log`.

On 1.5 you can even test another node's config lines from your desk with `-m host` (masquerade): `nhc -a -v -l- -m gpu07 MARK_OFFLINE=0`. The checks still run against *this* machine's hardware, so treat it as a "which lines apply to gpu07?" tool, not a remote health check.

Each failure is either **a config bug** (your expectation is wrong; fix the line) or **a node bug** (the node is wrong; fix the node). Telling those apart across a whole fleet is what [part 5](/fields/system-administration/node-health-check/rollout-at-scale.md) is about. But first, let's plug NHC into Slurm in [part 4](/fields/system-administration/node-health-check/slurm-integration.md).

> **Takeaway:** order checks cheap-to-expensive, generate a draft with `nhc-genconf` on known-good nodes, keep "early" variables in the sysconfig file, and iterate with `nhc -a -v -l- MARK_OFFLINE=0` until it's silent.

### References
- [NHC README: Configuration, Match Strings, Contexts, Built-in Checks](https://github.com/mej/nhc#configuration)
- [Sample `nhc.conf` shipped upstream](https://github.com/mej/nhc/blob/master/nhc.conf)
- [NVIDIA Xid errors catalogue](https://docs.nvidia.com/deploy/xid-errors/index.html)
