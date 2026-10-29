---
id: nhc-cheat-sheet
title: NHC Cheat Sheet
sidebar_label: "11. Cheat sheet"
order: 11
summary: Every NHC command, option, variable, config pattern and Slurm knob from the series on one page.
level: intermediate
type: reference
domains: [systems-and-hpc]
tags: [hpc, slurm]
relations:
  related: [nhc-troubleshooting, nhc-writing-nhc-conf]
---

# NHC Cheat Sheet

> **Part 11 of the [Node Health Check series](/fields/system-administration/node-health-check/README.md).** The whole series in one sip. Each section links back to the page that explains it.

## Everyday commands

| Task | Command |
|------|---------|
| Run like the scheduler does | `nhc` |
| See every failure, to the terminal, never drain | `nhc -a -v -l- MARK_OFFLINE=0` |
| Test one check | `nhc -l- -e 'check_fs_mount_rw -f /' MARK_OFFLINE=0` |
| Debug output, no watchdog | `nhc -d -t 0 -l- MARK_OFFLINE=0` |
| Full trace to a file | `BASH_XTRACEFD=33 33>/tmp/nhc.trace nhc -xdavl- MARK_OFFLINE=0` |
| Use another config / context | `nhc -c /path/x.conf` · `nhc -n nhc-deep` |
| Pretend to be another host (1.5) | `nhc -m gpu07 -a -v -l- MARK_OFFLINE=0` |
| Version and paths (1.5) | `nhc -V -V -V` |
| Generate a starter config | `nhc-genconf -H '*' -c -` |
| Fleet-wide dry run | `clush -bw @compute "nhc -a -l- MARK_OFFLINE=0"` |
| Cron with de-duplicated mail | `nhc-wrapper -M ops@x.org -X 12h -n nhc-oob` |

Rule: **flags first, `VAR=value` last.** Details: [part 2](/fields/system-administration/node-health-check/build-and-install.md#smoke-test), [part 3](/fields/system-administration/node-health-check/writing-nhc-conf.md#iterate-until-silent).

## Command-line options

| Flag | Variable | Meaning |
|------|----------|---------|
| `-a` | `NHC_CHECK_ALL=1` | Run all checks; exit code = number of failures |
| `-c file` | `CONFFILE` | Config file (default `/etc/nhc/$NAME.conf`) |
| `-D dir` | `CONFDIR` | Config directory (default `/etc/nhc`) |
| `-d` | `DEBUG=1` | Debug output |
| `-e 'check'` | `EVAL_LINE` | Run one check and exit |
| `-f` | `NHC_CHECK_FORKED=1` | Each check in its own process (experimental) |
| `-j` | `NHC_FMT_JSON=1` | JSON syslog messages (1.5) |
| `-l spec` | `LOGFILE` | Log target; `-` = stdout |
| `-m host` | `NHC_HOST` | Use this hostname (1.5) |
| `-n name` | `NAME` | Context name |
| `-p` | `NHC_FAIL_PERM=1` | Failures are permanent: never auto-resumed (1.5) |
| `-q` | `SILENT=1` | No logging |
| `-r rm` | `NHC_RM` | Resource manager: `slurm`, `pbs`, `sge`, `lsf`, `none` (1.5) |
| `-t secs` | `TIMEOUT` | Watchdog (default 30, `0` = off) |
| `-v` | `VERBOSE=1` | Show each check as it runs |
| `-V` | | Version info; repeat for more (1.5) |
| `-x` | | bash trace (`set -x`) |

## Important variables

| Variable | Default | Where to set | Notes |
|----------|---------|--------------|-------|
| `NHC_RM` | auto | sysconfig | Pin to `slurm` |
| `TIMEOUT` | 30 | sysconfig / `-t` | Must be below Slurm's 60 s |
| `MARK_OFFLINE` | 1 | anywhere | `0` = log only, never drain or resume |
| `DETACHED_MODE` | 0 | sysconfig | Return last result, check in background |
| `DF_FLAGS` / `DFI_FLAGS` | `-Tka` / `-Tia` | config | Add `l` to skip network filesystems |
| `MAX_SYS_UID` | 99 | config | UIDs at or below are "system" for process checks |
| `NHC_AUTH_USERS` | `root nobody` | config | Allowed to run arbitrary processes |
| `HOSTNAME` | kernel hostname | sysconfig | `HOSTNAME="$HOSTNAME_S"` if the RM uses short names |
| `LOGFILE` | `>>/var/log/nhc.log` | sysconfig / `-l` | |

"Early" variables (sysconfig or command line only): `CONFDIR`, `CONFFILE`, `DETACHED_MODE`, `HELPERDIR`, `HOSTNAME`, `INCDIR`, `LOGFILE`, `NAME`, `TIMEOUT`. Remember: the **config file beats the command line**. See [part 3](/fields/system-administration/node-health-check/writing-nhc-conf.md#variables-and-the-precedence-trap).

## Config syntax

```bash
# target              || check
*                     || check_fs_mount_rw -f /
cn*                   || ...        # glob
/^gpu[0-9]+$/         || ...        # regex
{cn[001-128],gpu01}   || ...        # node range (one bracket per name)
!login*               || ...        # negation
*                     || export PATH="$PATH:/opt/x/bin"            # variable
*                     || if [[ $X == default ]]; then X=new; fi    # never use bare && here
```

## Checks by purpose

| Purpose | Checks |
|---------|--------|
| Mounts | `check_fs_mount`, `check_fs_mount_rw`, `check_fs_mount_ro` (`-t type -s source -o opts -f mountpoint`, fix with `-r` / `-e`) |
| Space / inodes | `check_fs_free`, `check_fs_used`, `check_fs_size`, `check_fs_ifree`, `check_fs_iused`, `check_fs_inodes` |
| CPU / memory | `check_hw_cpuinfo S C T`, `check_hw_physmem min max [fudge]`, `check_hw_mem`, `check_hw_swap`, `check_hw_*_free`, `check_hw_mcelog` |
| Network | `check_hw_ib rate [dev]`, `check_hw_eth dev`, `check_net_link dev` (1.5), `check_net_ping`, `check_net_socket` |
| Processes | `check_ps_service` (`-S/-r/-c/-s/-k/-e/-E`), `check_ps_unauth_users`, `check_ps_userproc_lineage`, `check_ps_loadavg`, `check_ps_cpu/mem/physmem/time` |
| GPUs | `check_nvsmi_healthmon`, `check_nvgpu_smi` (1.5), `check_cmd_dmesg` for Xids |
| Firmware | `check_dmi_data_match` |
| Generic | `check_cmd_output`, `check_cmd_status`, `check_file_contents`, `check_file_stat`, `check_file_test` |
| Kubernetes | `check_kube`, `check_kube_etcd_*` (1.5) |

Most process and mount checks accept `-0` (non-fatal: log, don't drain).

## Slurm side

```ini
# slurm.conf (identical on all nodes)
HealthCheckProgram=/usr/sbin/nhc
HealthCheckInterval=300
HealthCheckNodeState=ANY,CYCLE
```

| `HealthCheckNodeState` | Runs on |
|-----|---------|
| `ANY` | all nodes (default) |
| `IDLE`, `ALLOC`, `MIXED` | nodes in that state |
| `NONDRAINED_IDLE` | idle, not drained: **disables NHC auto-resume** |
| `CYCLE` | spread runs across the interval (combine with the above) |
| `START_ONLY` / `REBOOT_ONLY` | only at slurmd start / after reboot (exclusive) |

| Task | Command |
|------|---------|
| Drain reasons | `sinfo -R` |
| NHC-drained nodes only | `sinfo -h -N -R -o '%N\|%E' \| grep '\|NHC'` |
| Drain for maintenance (NHC won't resume) | `scontrol update nodename=X state=drain reason="you: why"` |
| Take ownership of an NHC drain | `scontrol update nodename=X reason="you: investigating"` |
| Hand a node back to NHC | `scontrol update nodename=X reason="NHC: handed back"` |
| Reboot a node NHC drained, keep it drained | `scontrol reboot X` (avoid `ASAP` / `nextstate=`, which clear DRAIN) |
| Health check config in effect | `scontrol show config \| grep -i healthcheck` |

Details: [part 4](/fields/system-administration/node-health-check/slurm-integration.md), [part 7](/fields/system-administration/node-health-check/auto-remediation.md).

## Files and paths

| Path | Purpose |
|------|---------|
| `/usr/sbin/nhc`, `nhc-genconf`, `nhc-wrapper` | Programs |
| `/etc/nhc/<context>.conf` | Config per context |
| `/etc/nhc/scripts/*.nhc` | Check modules (`.nhc` required) |
| `/etc/sysconfig/<context>` or `/etc/default/<context>` | Early settings |
| `/usr/libexec/nhc/node-mark-{offline,online}` | RM helpers |
| `/var/log/nhc.log` | Run log |
| `/var/run/nhc/` | Detached results, PID file (1.5) |

## The rules, in eight lines

1. A fast-failing node is a black hole; NHC is the bouncer.
2. `NHC:`-prefixed reasons are NHC's; everything else is a human's.
3. Cheap checks, often. Expensive checks, rarely and elsewhere.
4. NHC's timeout below Slurm's.
5. Dry run, canary, enforce, behind a circuit breaker.
6. Every custom check: namespaced, cached, timed out, proven to fail.
7. Automate cheap fixes; budget retries; escalate by dropping the `NHC:` prefix.
8. Read the reason, rerun with `-a -v -l- MARK_OFFLINE=0`.

### References
- [LBNL NHC on GitHub](https://github.com/mej/nhc) · [1.5 release notes](https://github.com/mej/nhc/releases/tag/1.5)
- [`slurm.conf` man page](https://slurm.schedmd.com/slurm.conf.html) · [`scontrol` man page](https://slurm.schedmd.com/scontrol.html)
