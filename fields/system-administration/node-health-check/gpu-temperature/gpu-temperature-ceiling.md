---
id: nhc-gpu-temperature-ceiling
title: "GPU Temperature in a Health Check: The Ceiling Rule"
sidebar_label: "12. GPU heat: the ceiling"
order: 12
summary: "Add a GPU over-temperature ceiling to a health-check script: read temperature with one dcgmi call, drain without killing jobs, fail safe when the sensor can't be read, and pick the number."
level: advanced
type: [guide, concept]
domains: [systems-and-hpc, system-administration]
tags: [hpc, gpu, nvidia, slurm]
relations:
  prerequisites: [nhc-custom-checks]
  related: [nhc-rollout-at-scale, nhc-slurm-integration]
---

# GPU Temperature in a Health Check: The Ceiling Rule

> **Part 12 of the [Node Health Check series](/fields/system-administration/node-health-check/README.md).** Dana, Sam and `gpu-node-12` are invented, and 87 °C is an example value. Commands and field IDs come from NVIDIA's DCGM documentation. The check is a site-style bash health script, the kind many clusters run next to or instead of stock NHC checks, not an upstream NHC module. The author tested this code and it works; the output samples on the page are synthetic.

Around 04:10, a GPU on `gpu-node-12` will cross a temperature nobody ever wrote down. Nothing will page anyone, because nothing is looking. Dana will fix that by making the health check shout whenever it can't read a number, and that will be a much louder mistake.

**By the end of this page you will be able to:**

- Read GPU temperature, utilization and memory in one `dcgmi dmon` call.
- Write a ceiling rule that drains a node without killing its jobs.
- Make the check fail safe, so an unreadable sensor never drains a node.
- Choose a ceiling from the GPU's own limits and roll it out alert-first.

---

## The job that got slower and never failed

It's 04:10. A training job on `gpu-node-12` has been running for days, and its step time has crept up by a little each hour. No error, no crash, no alert.

By morning Sam from the hardware team finds a failed fan tray. One GPU had been running hotter than anything else in the rack for hours.

Dana, who inherited the cluster's health checks on Monday, takes the action item: the health check should have noticed. It already counts GPUs and reads their health. It has never once looked at temperature.

The obvious plan is a few lines: read the temperature, compare, drain.

---

## Three ways to get a ceiling wrong

**Attempt 1: use `nvidia-smi`.** The script already calls it elsewhere, so Dana adds one more call.

**Attempt 2: pick 80.** It feels hot, and nobody objects.

**Attempt 3: be safe.** If the temperature can't be read, treat the GPU as too hot and drain the node. Better safe than sorry. Dana's cursor is on "Save" when Sam replies in the review:

> **Sam:** If the DCGM host engine restarts across the fleet, every node fails to read at the same moment. Every node drains at once.

Dana deletes the line.

Three attempts, one lesson: the ceiling itself is simple. Everything around it (where the number comes from, how it's chosen, and what happens when it's missing) is where the page is.

---

## What the check reads

One call returns all three values the temperature rules need:

```bash
dcgmi dmon -e 150,203,252 -c 1
```

| Field | Meaning | Current name (DCGM docs) |
|---|---|---|
| 150 | GPU temperature (°C) | `DCGM_FI_DEV_GPU_TEMP_CELSIUS` |
| 203 | GPU utilization (%) | `DCGM_FI_DEV_GPU_UTIL_RATIO` |
| 252 | GPU memory in use (MiB) | `DCGM_FI_DEV_FB_USED` |

- `-e` takes a comma-separated list of field IDs, and `-c 1` exits after one sample.
- With no entity given, `dcgmi dmon` monitors all supported GPUs.
- The IDs are stable, but names have changed between DCGM releases. `dcgmi dmon -l` lists the fields your installed version knows.

Each GPU comes back as a row, for example `GPU 0     38     0     12`, with the columns in the order of `-e`.

### Why dcgmi and not nvidia-smi

Both read the same sensor, as far as the author knows. The trade-off is the failure mode, and that is the author's experience, not NVIDIA's documentation.

- `nvidia-smi` can hang on a bad GPU.
- `dcgmi` depends on the DCGM host engine being up.

Wrap either in `timeout`. A health check that can hang is a health check that needs a health check.

### One reading per run

The script reads once per run and keeps the parsed rows for later rules. The excerpt below is the core of it. The helper names (`record_error`, `TIMEOUT_DURATION`) belong to the surrounding site script.

```bash
raw=$(timeout -k 5 ${TIMEOUT_DURATION}s dcgmi dmon -e 150,203,252 -c 1 2>&1)
ret=$?

GPU_TEMPS=""
while read -r _ idx temp util mem _; do
    [[ "$idx" =~ ^[0-9]+$ ]] || continue          # skip header lines
    temp="${temp%%.*}"; util="${util%%.*}"; mem="${mem%%.*}"
    [[ "$temp" =~ ^[0-9]+$ ]] || continue          # skip N/A readings
    GPU_TEMPS+="${idx}, ${temp}, ${util}, ${mem}"$'\n'
done < <(echo "$raw" | grep -E '^[[:space:]]*GPU[[:space:]]+[0-9]+')
```

---

## What a ceiling does, and what it must not do

The rule is one comparison per GPU, busy or idle:

```bash
if (( temp > GPU_TEMP_CEILING )); then
    msg="GPU_TEMP_CRITICAL: GPU-$idx at ${temp}C (ceiling ${GPU_TEMP_CEILING}C)"
    flag_gpu_temp "GPU_TEMP_CRITICAL" "crit" "$msg"   # one line to syslog via logger
    record_error "14_check_gpu_temp_ceiling" "$msg"   # the drain happens at the end of the run
fi
```

![A GPU temperature line rises over time and crosses a dashed ceiling; at the crossing the node drains with the reason GPU_TEMP_CRITICAL and running jobs keep running.](images/temp-ceiling.svg)

*One crossing, one drain. Running jobs are not touched.*

- **The node drains at once.** Any GPU above the ceiling drains the node, whatever the node's state. The reason text starts with `GPU_TEMP_CRITICAL`, so alerts can match on it.
- **Running jobs are not killed.** A drained node accepts no new jobs, and jobs already running continue (see the `sinfo` and `scontrol` docs for the DRAINING and DRAINED states).
- **It needs a manual resume.** The drain does not clear itself when the GPU cools.
- **A node already drained for another reason** only gets the event logged.

> [!WARNING]
> Never drain because a reading failed. If `dcgmi` can't be read, print a warning and skip the temperature checks for that run.

```bash
if [[ $ret -ne 0 || -z "$GPU_TEMPS" ]]; then
    echo "  WARNING: could not read GPU temperatures (dcgmi said: $(echo "$raw" | head -1)). Temperature checks skipped."
    GPU_TEMPS=""
    return
fi
```

A real DCGM or GPU failure is caught by the other checks (GPU count, GPU health), so this check has no reason to drain on its own. It fails safe, and it fails quietly.

---

## Where the number comes from

Dana's 80 came from a feeling. The right place to start is the GPU itself:

```bash
nvidia-smi -q -d TEMPERATURE
```

It prints the current temperature along with limits such as the slowdown and shutdown temperatures. Fields differ by GPU model, and forum threads disagree on what each one means, so read the output of your own GPU and the NVIDIA documentation, not a blog (this one included).

- **Pick the ceiling below the slowdown threshold, with margin.** That is the author's reading, not a documented rule.
- **87 °C in this page is an example value.** Take yours from your GPU's limits and your fleet's real readings.
- **The variable is `GPU_TEMP_CEILING`.** Every rule on this page reads it, so changing it is one line.

---

## The night it happens again

Three weeks later, a fan tray fails on `gpu-node-12` again. The health check reads the temperature once per run. On the run that finds a GPU above the ceiling, the log shows:

```text
nhc: GPU_TEMP_CRITICAL node=gpu-node-12 GPU-3 at 89C (ceiling 87C)
```

The node drains in that same run and stops taking new jobs. The jobs already running keep going, and Sam swaps the fan tray in the morning, not at 04:10.

Dana's other checks stay quiet. When DCGM restarts across the fleet a week later, every node prints a warning and none of them drains. Nobody notices, which is how a health check is supposed to feel.

The ceiling protects against a GPU that is hot while it works. What about a GPU that is hot while it does nothing?

---

## Before this reaches every node

Ship it the way the series teaches: [dry run, canary, enforce](/fields/system-administration/node-health-check/getting-started/rollout-at-scale.md). Practical steps for this check:

| Question | Where to look | Why it matters |
|---|---|---|
| What are healthy readings in your fleet? | A few `dcgmi dmon -e 150,203,252 -c 1` samples across busy and idle nodes | Your ceiling should sit well above them |
| What is the GPU's own limit? | `nvidia-smi -q -d TEMPERATURE` | The ceiling goes below it, with margin |
| Does the flag line reach your alerts? | `logger` output in syslog, matched on `GPU_TEMP_CRITICAL` | A drain nobody sees is a silent outage |
| What happens when `dcgmi` is down? | A test node with the DCGM host engine stopped | Prove it warns and does not drain |

A suggestion of the author's: start with the flag line only and watch syslog for a few days before letting the check drain.

**Next:** a GPU at 50 °C is fine under load and suspicious when it has nothing to do. How do you tell an idle GPU from a busy one that happens to read 0%? See [the idle timer](/fields/system-administration/node-health-check/gpu-temperature/gpu-temperature-idle-timer.md). **Just the steps:** [quick guide](/fields/system-administration/node-health-check/gpu-temperature/quick-guide.md).

---

## 📜 The Scroll (keep this)

```text
Read:       dcgmi dmon -e 150,203,252 -c 1   (150 temp C, 203 util %, 252 memory MiB)
Rule:       any GPU above GPU_TEMP_CEILING -> drain the node at once
Reason:     GPU_TEMP_CRITICAL: GPU-<n> at <t>C (ceiling <c>C)
Running:    jobs already running are not killed; resume is manual
Fail safe:  dcgmi unreadable -> warn and skip, never drain
Pick:       ceiling below the GPU's slowdown limit, from nvidia-smi -q -d TEMPERATURE
```

## References

- [NVIDIA DCGM: `dcgmi dmon` reference](https://docs.nvidia.com/datacenter/dcgm/latest/reference/command-line-reference/dcgmi/dcgmi-dmon.html)
- [NVIDIA DCGM: field identifiers](https://docs.nvidia.com/datacenter/dcgm/latest/reference/field-identifiers.html)
- [nvidia-smi manual page](https://man.archlinux.org/man/nvidia-smi.1.en) (a copy of NVIDIA's man page)
- [NVIDIA developer forum: nvidia-smi target and maximum operating temperature](https://forums.developer.nvidia.com/t/nvidia-smi-gpu-target-temperature-maximum-operating-temperature/229325)
- [nvidia-smi documentation (NVIDIA)](https://docs.nvidia.com/deploy/nvidia-smi/index.html)
- [NVIDIA NVSentinel: GPU thermal margin runbook](https://docs.nvidia.com/nvsentinel/runbooks/gpu-thermal-margin.md)
- [NVIDIA developer forum: GPU T.Limit and shutdown T.Limit explained by NVIDIA staff](https://forums.developer.nvidia.com/t/nvidia-smi-gpu-t-limit-gpu-shutdown-t-limit-temp/292006)
- [Slurm: `sinfo` (node states DRAINING and DRAINED)](https://slurm.schedmd.com/sinfo.html)
- [CoreWeave: drain and undrain nodes (running workloads are not killed)](https://docs.coreweave.com/products/sunk/manage_sunk/drain-and-undrain-nodes)
- [GNU coreutils: `timeout` (`-k`, exit status 124 and 137)](https://www.gnu.org/s/coreutils/manual/html_node/timeout-invocation.html)
- [Slurm: `scontrol`](https://slurm.schedmd.com/scontrol.html)
- [Upstream NHC (LBNL)](https://github.com/mej/nhc)
