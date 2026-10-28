---
id: nhc-custom-checks
title: Writing Your Own NHC Checks
sidebar_label: "6. Custom checks"
order: 6
summary: Build a site .nhc module the way upstream does, with cached data, clear failure messages, fast bash, and practical GPU checks.
level: advanced
type: guide
domains: [systems-and-hpc]
tags: [hpc, gpu, nvidia]
relations:
  prerequisites: [nhc-writing-nhc-conf]
---

# Writing Your Own NHC Checks

> **Part 6 of the [Node Health Check series](/fields/system-administration/node-health-check/README.md).** The built-in checks cover the classics. Your cluster has its own weirdness: a licence daemon, a GPU generation with its own failure modes, a burst buffer. Time to teach the bouncer some new rules.

## Table of Contents
- [First, do you even need a module?](#first-do-you-even-need-a-module)
- [The rules of the house](#the-rules-of-the-house)
- [Skeleton: a module in five parts](#skeleton-a-module-in-five-parts)
- [Real example: GPU count and ECC errors](#real-example-gpu-count-and-ecc-errors)
- [Real example: wrapping DCGM](#real-example-wrapping-dcgm)
- [Testing your check](#testing-your-check)
- [Writing bash like NHC does](#writing-bash-like-nhc-does)
- [Sharing upstream](#sharing-upstream)

---

## First, do you even need a module?

Often no. `check_cmd_output`, `check_cmd_status` and `check_file_contents` turn almost any command or file into a check with no code at all:

```bash
# A licence server port must answer
   * || check_cmd_status -t 3 -r 0 /usr/bin/nc -z lic01 27000

# SELinux must be off on compute (selinuxenabled returns 1 when disabled)
   * || check_cmd_status -t 1 -r 1 selinuxenabled

# Transparent hugepages must be "madvise"
   * || check_file_contents /sys/kernel/mm/transparent_hugepage/enabled '/\[madvise\]/'

# CPU governor must be performance, with a human-friendly failure message
   * || check_cmd_output -t 5 -m '!/powersave/' -M 'CPU governor is not performance' -e 'cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'
```

`check_cmd_output` passes when every positive `-m` match is found and no negated one is. Each `-M` gives the matching `-m` a readable failure message, and `-C name` makes the failure show up under a name of your choice. In 1.5 it also gained conditionals (`-c`), so you can compare numbers from the output, not just match text.

Write a module when you need **logic**: loops over devices, thresholds per device, cached data shared between several checks.

---

## The rules of the house

From upstream's guidelines, plus what bites people in practice:

1. **File:** `/etc/nhc/scripts/<siteid>_<class>.nhc`, for example `acme_gpu.nhc`. The **`.nhc` extension is required**; other files are ignored (so `*.rpmnew` leftovers don't get loaded).
2. **Function names:** `check_<class>_<purpose>`, like `check_gpu_count`. Helpers: `nhc_<class>_gather_data`.
3. **Namespace your globals:** `ACME_GPU_...`, never `DATA` or `COUNT`. Every module shares one bash process.
4. **Fail with `die`:** `die 1 "clear message"` then `return 1`. The message becomes the `NHC:` reason in `sinfo -R`, so make it say *what* and *where*: `"GPU 3 (0000:3b:00.0): 12 uncorrected ECC errors"` beats `"gpu bad"`.
5. **Pass with `return 0`.** Silence is success.
6. **Cache expensive data** in a gather function, so three checks don't run `nvidia-smi` three times.
7. **Bound every external command** with a timeout. A wedged GPU can hang `nvidia-smi` forever; NHC's watchdog will eventually kill the *whole run*, with a much less useful message than yours.
8. **Use full paths or extend `PATH`.** NHC runs with `PATH=/sbin:/usr/sbin:/bin:/usr/bin`, not your login shell's.

---

## Skeleton: a module in five parts

```bash
# NHC -- ACME checks for <thing>
#
# Your Name <you@example.org>, 2026-10-28
# License: BSD-3 (same as NHC) unless stated otherwise

# 1. Globals with safe defaults (namespaced!)
declare -a ACME_THING_DATA=( )
declare    ACME_THING_GATHERED=0

# 2. Gather once, cache in globals
function nhc_acme_thing_gather_data() {
    local IFS=$'\n'
    ACME_THING_DATA=( $(timeout 10 /usr/bin/thing-status 2>/dev/null) )
    ACME_THING_GATHERED=1
}

# 3. The check
function check_acme_thing_ok() {
    (( ACME_THING_GATHERED )) || nhc_acme_thing_gather_data

    if (( ${#ACME_THING_DATA[@]} == 0 )); then
        die 1 "${FUNCNAME[0]}:  thing-status returned no data"
        return 1
    fi
    return 0
}
```

Parts 4 and 5 live elsewhere: the line in `nhc.conf` (`* || check_acme_thing_ok`) and a test run (below).

---

## Real example: GPU count and ECC errors

The most common GPU failure modes in production are boringly physical: a GPU **falls off the bus** (count drops from 8 to 7) or **memory errors** pile up. Here's a module that catches both from one `nvidia-smi` call.

```bash
# /etc/nhc/scripts/acme_gpu.nhc
# NHC -- ACME GPU checks (count, uncorrected ECC)

declare -a ACME_GPU_ROWS=( )
declare    ACME_GPU_GATHERED=0
declare    ACME_GPU_RC=0
declare    ACME_NVSMI="${ACME_NVSMI:-/usr/bin/nvidia-smi}"

function nhc_acme_gpu_gather_data() {
    local IFS=$'\n'
    ACME_GPU_ROWS=( $(timeout 20 "$ACME_NVSMI" \
        --query-gpu=index,pci.bus_id,ecc.errors.uncorrected.volatile.total \
        --format=csv,noheader,nounits 2>/dev/null) )
    ACME_GPU_RC=$?          # status of the command substitution
    ACME_GPU_GATHERED=1
}

# check_acme_gpu_count <expected>
function check_acme_gpu_count() {
    local EXPECTED="$1"
    (( ACME_GPU_GATHERED )) || nhc_acme_gpu_gather_data

    if (( ACME_GPU_RC != 0 )); then
        die 1 "${FUNCNAME[0]}:  nvidia-smi failed or timed out (rc=$ACME_GPU_RC)"
        return 1
    fi
    if (( ${#ACME_GPU_ROWS[@]} != EXPECTED )); then
        die 1 "${FUNCNAME[0]}:  found ${#ACME_GPU_ROWS[@]} GPUs, expected $EXPECTED"
        return 1
    fi
    return 0
}

# check_acme_gpu_ecc [max_uncorrected]   (default 0)
function check_acme_gpu_ecc() {
    local MAX="${1:-0}" ROW IDX BUS ECC
    (( ACME_GPU_GATHERED )) || nhc_acme_gpu_gather_data

    for ROW in "${ACME_GPU_ROWS[@]}"; do
        IFS=',' read -r IDX BUS ECC <<< "$ROW"
        IDX="${IDX// /}" BUS="${BUS// /}" ECC="${ECC// /}"
        [[ "$ECC" == *N/A* || -z "$ECC" ]] && continue      # ECC disabled/unsupported
        if (( ECC > MAX )); then
            die 1 "${FUNCNAME[0]}:  GPU $IDX ($BUS) has $ECC uncorrected ECC errors (max $MAX)"
            return 1
        fi
    done
    return 0
}
```

And in `nhc.conf`:

```bash
   {gpu[01-32]} || check_acme_gpu_count 8
   {gpu[01-32]} || check_acme_gpu_ecc 0
```

Design notes:

- **One gather, two checks.** The second check reuses the cached rows.
- **Fails loudly when `nvidia-smi` itself fails.** A driver that can't talk to the GPUs is a failure, not "zero GPUs, zero errors, all good".
- **Volatile vs aggregate counters.** Volatile counters reset with the driver; aggregate ones persist. Which one to alert on, and at what threshold, depends on your GPU generation's error-recovery features (row remapping and friends). Read NVIDIA's guidance for your hardware and adjust the field name.
- **Field names change between driver versions.** Check `nvidia-smi --help-query-gpu` on your nodes before trusting this verbatim.

Pair it with the `dmesg` Xid one-liner from [part 3](/fields/system-administration/node-health-check/writing-nhc-conf.md#starter-config-a-real-cluster), and you have count, memory errors and kernel-reported faults covered in milliseconds.

---

## Real example: wrapping DCGM

NVIDIA's **DCGM** offers two very different kinds of checks, and they belong in different places:

| DCGM feature | Cost | Where it belongs |
|--------------|------|------------------|
| **Background health** (`dcgmi health -c` after watches are set with `dcgmi health -s`) | Cheap, non-invasive | Periodic NHC run |
| **Active diagnostics** (`dcgmi diag -r 1/2/3/4`) | Level 1 takes seconds, level 2 about two minutes, level 3 about fifteen, level 4 longer; levels 2+ **load the GPUs** | Never periodic. Deep context, after a drain, or burn-in |

NVIDIA's own guidance maps the levels to jobs: level 1 as a readiness check, level 2 after failures, levels 3-4 for administrators doing a post-mortem.

A check that runs the quick diagnostic and fails on any failing test:

```bash
# acme_dcgm.nhc
function check_acme_dcgm_diag() {
    local LEVEL="${1:-1}" TMO="${2:-60}"
    check_cmd_output -C "${FUNCNAME[0]}" -t "$TMO" -r 0 \
        -m '!/Fail/' -M "dcgmi diag -r $LEVEL reported a failing test" \
        -e "dcgmi diag -r $LEVEL"
}
```

Because it reuses `check_cmd_output`, it inherits the timeout, the exit-code check and the matching for free. Wire it into the deep context, not the periodic one:

```bash
# /etc/nhc/nhc-deep.conf
   {gpu[01-32]} || check_acme_dcgm_diag 2 300
```

The deep context needs a watchdog longer than its slowest check, so give it its own early settings, for example `TIMEOUT=900` in `/etc/sysconfig/nhc-deep`. The periodic context keeps its short timeout.

> [!IMPORTANT]
> DCGM's output format and exit codes evolve between releases, and newer releases can emit JSON (`-j`). Run `dcgmi diag -r 1` on a known-bad and a known-good node, confirm what "fail" looks like on your version, and adjust the match. NHC 1.5 also ships GPU checks of its own (`lanl_nvgpu.nhc` for nvidia-smi, `csc_nvidia_smi.nhc`), so read those first; they may already do what you need.

---

## Testing your check

```bash
# as root on a test node. MARK_OFFLINE=0 everywhere: testing must never drain.

# 1. Syntax: does the module even parse?
bash -n /etc/nhc/scripts/acme_gpu.nhc

# 2. Run just this check, no config file involved
nhc -l- -e 'check_acme_gpu_count 8' MARK_OFFLINE=0; echo "rc=$?"

# 3. Same, with debug output, and the bash trace in a separate file
BASH_XTRACEFD=33 33>/tmp/nhc-trace.out nhc -d -v -x -l- -e 'check_acme_gpu_ecc 0' MARK_OFFLINE=0

# 4. Prove it FAILS when it should: expect 9 GPUs on an 8-GPU node
nhc -l- -e 'check_acme_gpu_count 9' MARK_OFFLINE=0; echo "rc=$?"   # should be non-zero
```

Remember the ordering rule from [part 2](/fields/system-administration/node-health-check/build-and-install.md#smoke-test): flags first, `VAR=value` pairs last. Also run these as a real root shell rather than through `sudo`, which closes extra file descriptors like the `33` used for the trace.

Step 4 is the one people skip. A check that has never failed in testing is a check you don't know works.

> [!TIP]
> To fake a failure without breaking hardware, point the command variable at a stub: `ACME_NVSMI=/tmp/fake-nvidia-smi` (a script that prints 7 rows or a non-zero ECC count). This is why the module reads `ACME_NVSMI` instead of hardcoding the path.

---

## Writing bash like NHC does

NHC is fast because it avoids forking subprocesses. Your checks run on every node every few minutes, so the same habits pay off:

| Instead of | Write | Why |
|-----------|-------|-----|
| `X=$(cat /proc/loadavg)` | `read -a X < /proc/loadavg` | `read` is a builtin: no fork |
| `HOST=$(hostname)` | `read HOST < /proc/sys/kernel/hostname` | Same, and NHC already sets `$HOSTNAME` |
| `cmd \| grep foo` | `[[ "$LINE" == *foo* ]]` or `[[ "$LINE" =~ regex ]]` | Matching in-process |
| `echo "$S" \| sed 's/^ *//'` | `${S#"${S%%[! ]*}"}` | Parameter expansion |
| `awk -F: '{print $1}' /etc/passwd` | `while IFS=: read -r U _; do ...; done < /etc/passwd` | One process instead of two |
| Three checks each calling the tool | One gather function + cached array | The tool runs once |

For matching, call NHC's own `mcheck "$string" "$match_string"` so your check accepts globs, `/regex/`, `{ranges}` and `!negation` just like the built-ins.

---

## Sharing upstream

Wrote something others would want (a check for a common NIC, filesystem or GPU)? Upstream welcomes pull requests. Include the header comment, keep the naming convention, and add unit tests under `test/` like the existing modules. Several of the GPU and Kubernetes checks in 1.5 started life as exactly that kind of site module (LANL, CSC).

Next: turning "detected" into "fixed" without turning your cluster into a reboot loop, in [part 7](/fields/system-administration/node-health-check/auto-remediation.md).

> **Takeaway:** try `check_cmd_output` first; write a module when you need logic. Namespace globals, cache expensive data, bound every command with a timeout, write failure messages a human can act on, and prove each check fails when it should.

### References
- [NHC README: Customization, Writing Checks, Tips and Best Practices](https://github.com/mej/nhc#customization)
- [NHC `check_cmd_output` documentation](https://github.com/mej/nhc#check_cmd_output)
- [NVIDIA DCGM diagnostics: run levels](https://docs.nvidia.com/datacenter/dcgm/latest/user-guide/dcgm-diagnostics.html)
- [`dcgmi diag` command reference](https://docs.nvidia.com/datacenter/dcgm/latest/reference/command-line-reference/dcgmi/dcgmi-diag.html)
