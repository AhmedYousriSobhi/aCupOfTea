
# NHC Troubleshooting: Symptom First

<!-- related-block -->
<div class="reading-time">8 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [Plugging NHC into Slurm (and Friends)](/fields/system-administration/node-health-check/slurm-integration.md)  ·  **See also:** [NHC Cheat Sheet](/fields/system-administration/node-health-check/cheat-sheet.md)

</div>


> **Part 8 of the [Node Health Check series](/fields/system-administration/node-health-check/README.md).** Find your symptom, follow the steps. Bookmark this one; future you at 2 AM will be grateful.

## Table of Contents
- [The debugging toolkit](#the-debugging-toolkit)
- [1. A healthy node keeps getting drained](#1-a-healthy-node-keeps-getting-drained)
- [2. The problem is fixed but the node never comes back](#2-the-problem-is-fixed-but-the-node-never-comes-back)
- [3. Node is drained, but not by NHC](#3-node-is-drained-but-not-by-nhc)
- [4. After boot, the node never registers with Slurm](#4-after-boot-the-node-never-registers-with-slurm)
- [5. NHC times out, or gets killed silently](#5-nhc-times-out-or-gets-killed-silently)
- [6. Works when I run it, fails under slurmd](#6-works-when-i-run-it-fails-under-slurmd)
- [7. My config change does nothing](#7-my-config-change-does-nothing)
- [8. Weird errors: 126, 127, "no checks", "Unsupported RM"](#8-weird-errors-126-127-no-checks-unsupported-rm)
- [9. Build and install problems](#9-build-and-install-problems)
- [Still stuck?](#still-stuck)

---

## The debugging toolkit

Memorize these five; they solve most problems.

```bash
# What did NHC say, and when?
sinfo -R                                  # drain reasons across the cluster
tail -50 /var/log/nhc.log                 # on the node

# Rerun like slurmd would, but see everything and drain nothing (as root on the node)
nhc -a -v -l- MARK_OFFLINE=0

# Test a single check line in isolation
nhc -l- -e 'check_fs_mount_rw -f /scratch' MARK_OFFLINE=0

# Full bash trace into a file you can read (or attach to a GitHub issue)
BASH_XTRACEFD=33 33>/tmp/nhc-trace.out nhc -xdavl- MARK_OFFLINE=0

# Which files and paths is this NHC actually using? (1.5)
nhc -V -V -V
```

---

## 1. A healthy node keeps getting drained

**Look at the reason first.** `sinfo -R -n <node>` usually names the check. Then rerun with `-a -v -l- MARK_OFFLINE=0` on the node.

| Likely cause | Tell-tale | Fix |
|-------------|-----------|-----|
| Expectation is wrong for this hardware class | Same failure on all nodes of a class | Fix the config line or its target ([part 3](/fields/system-administration/node-health-check/writing-nhc-conf.md)) |
| Memory check without fudge factor | `check_hw_physmem` complaining by a few hundred MB | Add a fudge: `check_hw_physmem 512GB 512GB 3%` |
| Threshold checks during busy hours | `check_ps_loadavg`, `check_fs_free` fail only by day | Raise thresholds, or move them to a non-draining context |
| Flaky network check | `check_net_ping` fails randomly | More packets and a longer wait (`-c 3 -W 3`); check the target isn't overloaded |
| Target matches more hosts than intended | Login nodes failing compute checks | Test with `nhc -m login01 -a -v -l- MARK_OFFLINE=0` (1.5) to see which lines apply |
| Hostname format mismatch | Checks for `cn*` not running, or running for the wrong nodes | Compare `cat /proc/sys/kernel/hostname` with your targets (FQDN vs short name) |

---

## 2. The problem is fixed but the node never comes back

NHC resumes a node only when **all** of these are true. Walk the list:

1. **The reason still starts with `NHC:`.** If someone (or a script) edited it, NHC no longer owns the node. `sinfo -R -n <node>`. Fix: resume it yourself, or set the reason back to an `NHC:` one.
2. **NHC actually runs on drained nodes.** `HealthCheckNodeState=NONDRAINED_IDLE` never checks drained nodes, so they never get resumed. `scontrol show config | grep -i healthcheck`.
3. **The node isn't in `MAINT`.** NHC 1.5 doesn't resume nodes in maintenance state; Slurm rejects that transition anyway.
4. **It wasn't a permanent failure.** A `(perm)` tag in the reason means NHC ran with `-p`. Humans only.
5. **`MARK_OFFLINE` isn't 0.** Left over from a canary or a dry run? It disables onlining too. `grep -r MARK_OFFLINE /etc/nhc /etc/sysconfig/nhc /etc/default/nhc 2>/dev/null`.
6. **All checks pass now**, not just the one you fixed. With default settings NHC stops at the first failure, so a second, hidden problem keeps it drained. Run with `-a`.
7. **The online helper can talk to Slurm.** Look in `nhc.log` for helper output; `scontrol` must work from the node as root.

---

## 3. Node is drained, but not by NHC

If the reason doesn't start with `NHC:`, NHC didn't do it, and NHC won't undo it. Common culprits:

| Reason | Who did it |
|--------|-----------|
| `Kill task failed` | `slurmd` couldn't kill a job step (often processes stuck in D state on a dead filesystem) |
| `Epilog error` / `Prolog error` | Your prolog/epilog exited non-zero |
| `Not responding` / `NO NETWORK ADDRESS` | Controller lost contact with `slurmd` |
| `Low RealMemory` / `Low socket*core*thread count` | Node registered with less hardware than `slurm.conf` says |
| `Reboot ASAP` | Someone ran `scontrol reboot ASAP` |
| Empty | A human, being mysterious |

Fun fact: `Kill task failed` and an NHC `check_fs_mount` failure often show up together. Same root cause (dead storage), two different detectors.

---

## 4. After boot, the node never registers with Slurm

`slurmd` runs the health check **at startup, before registering**. If NHC fails, the node stays out of the pool.

```bash
# on the node
systemctl status slurmd
journalctl -u slurmd -b | grep -i health
nhc -a -v -l- MARK_OFFLINE=0          # what's actually failing at boot?
```

Typical boot-time-only failures:

- **Mounts not ready yet.** NFS/Lustre mount after `slurmd` starts. Order your units (`After=remote-fs.target` in a `slurmd` drop-in) instead of loosening the check.
- **GPU driver not initialized.** Persistence daemon or fabric manager not started yet. Same fix: unit ordering.
- **Image drift.** The node booted an image whose hardware or software differs from what the config expects.

> [!TIP]
> Need the node up *now* while you fix the config? Temporarily run with a known-good config, `nhc -c /etc/nhc/nhc.conf.minimal`, via the `HealthCheckProgram` wrapper, rather than removing health checks cluster-wide.

---

## 5. NHC times out, or gets killed silently

Two clocks again ([part 4](/fields/system-administration/node-health-check/slurm-integration.md#timeouts-make-sure-the-bouncer-isnt-shot-mid-sentence)):

- **NHC's watchdog fired** (default 30 s): you'll see a timeout failure in `nhc.log` and a drain reason saying so. Something in your checks was slow.
- **Slurm killed NHC** (60 s, or `HealthCheckTimeout`): no NHC message at all, just a truncated log. Your `TIMEOUT` is higher than Slurm's. Lower it.

Find the slow check:

```bash
time nhc -a -v -l- -t 0 MARK_OFFLINE=0     # -t 0 disables the watchdog; -v shows progress
```

The usual suspect: **`df` hanging on a dead NFS or Lustre mount** inside `check_fs_free`/`check_fs_used`/`check_fs_inodes`. Fixes, in order of preference:

1. `* || DF_FLAGS="-Tkal"` and `* || DFI_FLAGS="-Tial"` so `df` skips network filesystems when you only check local ones.
2. Check network filesystems with `check_fs_mount*` (reads `/proc/mounts`, doesn't touch the server) instead of space checks.
3. `DETACHED_MODE=1` so `slurmd` never blocks (accepting that failures are reported one run late).

Other slow spots: `nvidia-smi` on a wedged GPU (wrap it in `timeout`), `dmidecode` on some BMCs, DNS lookups in `check_net_ping` (use IPs or `/etc/hosts`).

**Two NHCs at once?** NHC 1.5 keeps a per-context PID file, so a second run won't pile on top of a hung one. On older versions, overlapping runs are possible when checks run longer than the interval.

---

## 6. Works when I run it, fails under slurmd

Your shell and `slurmd`'s environment are not the same:

| Difference | Symptom | Fix |
|-----------|---------|-----|
| `PATH` (NHC sets `/sbin:/usr/sbin:/bin:/usr/bin`) | "command not found", exit 127 | Full paths in checks, or `* \|\| export PATH="$PATH:/opt/x/bin"` at the top of the config |
| Environment modules / `LD_LIBRARY_PATH` | Vendor tools fail to load libraries | Call tools through a wrapper script that sets their environment |
| Ran as a user vs root | Permission errors on `dmesg`, `/dev/*` | `slurmd` runs it as root; test as root too |
| `sudo` closing file descriptors | Your trace redirect (`33>`) is empty | Use a real root shell for tracing |

---

## 7. My config change does nothing

- **Wrong file for the context.** `nhc -n foo` reads `/etc/nhc/foo.conf`, not `nhc.conf`. Check what's loaded with `nhc -V -V -V` (1.5) and `-v` output.
- **Early-only variable set in the config.** `TIMEOUT`, `DETACHED_MODE`, `LOGFILE`, `CONFFILE`, `NAME`... go in the sysconfig file or on the command line ([part 3](/fields/system-administration/node-health-check/writing-nhc-conf.md#variables-and-the-precedence-trap)).
- **Config beats command line.** `nhc FOO=1` loses to `FOO=0` in the config.
- **Custom module not loading.** It must end in `.nhc` and live in `/etc/nhc/scripts/` (or `$INCDIR`). `bash -n` it for syntax errors.
- **Variable set after it's used.** Lines execute in order; assignments must come before the checks that need them.
- **Old copy on the node.** Your config management didn't run. `md5sum /etc/nhc/nhc.conf` across the fleet with `clush -b`.

---

## 8. Weird errors: 126, 127, "no checks", "Unsupported RM"

| Message / code | Meaning | Fix |
|---------------|---------|-----|
| Exit **127** | Command not found | Full path or `PATH` (see #6). 1.5 explicitly points this out |
| Exit **126** | Found but not executable | `chmod +x`, check `noexec` mounts |
| Warning: check list is **empty** (1.5) | No line's target matched this hostname | Compare targets with the real hostname; test with `-m` |
| `Unsupported RM detected` from a helper | NHC couldn't tell which resource manager to talk to | Set `NHC_RM=slurm` in `/etc/sysconfig/nhc` |
| `check_file_stat` options behave differently after upgrade | 1.5 breaking change: `-M`/`-m` now test the file *type*; permission bits moved to `-P`/`-p` | Update those lines when moving to 1.5 |

---

## 9. Build and install problems

- **`./configure: No such file or directory`**: you downloaded GitHub's auto-generated "Source code" archive. Use the `lbnl-nhc-<ver>.tar.xz` release asset, or run `./autogen.sh` first ([part 2](/fields/system-administration/node-health-check/build-and-install.md#before-you-start-the-one-trap-everyone-falls-into)).
- **`make test` fails**: something about your platform breaks an assumption (bash version, `/proc` layout). That's a real bug report: post the output.
- **Helpers not found**: the `--libexecdir` you built with doesn't match where NHC looks. Compare `nhc -V -V -V` with the files on disk, or set `HELPERDIR` in the sysconfig file.

---

## Still stuck?

- Search and open issues at [github.com/mej/nhc/issues](https://github.com/mej/nhc/issues). Attach the `-x` trace file from the toolkit above, your NHC version, distro, and the relevant config lines.
- The NHC users' mailing list (`nhc@lbl.gov`) and the Slurm users' list both have years of searchable answers.

> **Takeaway:** read the reason, rerun with `-a -v -l- MARK_OFFLINE=0`, trace with `-x` when lost. Most problems are one of: wrong expectation, ownership (`NHC:` prefix), timeouts, `df` on dead NFS, or environment differences under `slurmd`.

### References
- [NHC README: Testing, Command-Line Invocation, Configuration Variables](https://github.com/mej/nhc#testing)
- [NHC 1.5 release notes: exit codes 126/127, empty check list warning, PID file, `check_file_stat` change](https://github.com/mej/nhc/releases/tag/1.5)
- [`slurm.conf`: HealthCheckProgram behavior at slurmd startup](https://slurm.schedmd.com/slurm.conf.html#OPT_HealthCheckProgram)
