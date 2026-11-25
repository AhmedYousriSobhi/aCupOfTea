
<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/fields/">Fields</a> / <a href="#/fields/system-administration/">System Administration</a> / <a href="#/fields/system-administration/node-health-check/">Node Health Check</a> / <a href="#/fields/system-administration/node-health-check/gpu-temperature/">GPU Temperature</a></nav>

# Add GPU Temperature Rules to a Health Check

<!-- related-block -->
<div class="reading-time">Advanced · Guide · 4 min read · Updated 23 Nov 2026</div>
<!-- related-block -->
<div class="tag-chips"><a class="chip" href="#/.docs/generated/explore/tags/gpu">gpu</a> <a class="chip" href="#/.docs/generated/explore/tags/hpc">hpc</a> <a class="chip" href="#/.docs/generated/explore/tags/nvidia">nvidia</a> <a class="chip" href="#/.docs/generated/explore/tags/slurm">slurm</a></div>


> **Quick guide for** [The Ceiling Rule](/fields/system-administration/node-health-check/gpu-temperature/gpu-temperature-ceiling.md) and [The Idle Timer](/fields/system-administration/node-health-check/gpu-temperature/gpu-temperature-idle-timer.md). Do the ceiling first, then the idle timer. You will end with one rule that drains above a ceiling and never drains on a failed read, and a second that drains only after a warm idle GPU stays warm for a window.

## Before you start

- A health-check script you can edit, and a test node.
- `dcgmi` installed and the [DCGM](/references/glossary?id=dcgm "Data Center GPU Manager") host engine running.
- Your GPU's limits: `nvidia-smi -q -d TEMPERATURE`.
- For the idle timer: `scontrol` on the node, an ssh key loaded for the scan, and your nodes in `nodelist.yml` (a `nodes:` list, one `- name` per line).

## Part 1: the ceiling rule

1. Read all GPUs once.

   ```bash
   dcgmi dmon -e 150,203,252 -c 1
   ```

   **Expect:** one row per GPU, for example `GPU 0     38     0     12` (temperature, utilization, memory).
   **If not:** list the fields your version knows with `dcgmi dmon -l`.

2. Choose a ceiling below your GPU's slowdown limit and set it once.

   ```bash
   GPU_TEMP_CEILING=87      # example value: take yours from the nvidia-smi output in Before you start
   ```

   **Expect:** one variable the rule reads.

3. Wrap the call in `timeout`, skip headers and `N/A`, and keep the rows.

   **Expect:** `GPU_TEMPS` holds one `index, temp, util, mem` line per GPU.
   **If not:** if `dcgmi` failed or `GPU_TEMPS` is empty, print a warning and return. Do not drain.

4. Flag and fail the check for any GPU above the ceiling.

   ```bash
   msg="GPU_TEMP_CRITICAL: GPU-$idx at ${temp}C (ceiling ${GPU_TEMP_CEILING}C)"
   ```

   **Expect:** a syslog line like `nhc: GPU_TEMP_CRITICAL node=gpu-node-12 GPU-3 at 89C (ceiling 87C)` and a drain at the end of the run.
   **If not:** check that the flag line reaches syslog and your alerts.

## Part 2: the idle timer

1. Set the parameters (example values: choose yours from your fleet).

   ```bash
   GPU_IDLE_TEMP_MAX=45
   GPU_IDLE_WINDOW_MIN=10
   GPU_IDLE_MEM_MAX_MIB=1024
   GPU_TEMP_STATE_DIR="/var/tmp/nhc_gpu_temp"
   ```

   **Expect:** four variables at the top of the temperature block.

2. Gate on the node state.

   ```bash
   scontrol show node $(hostname -s) | grep -E 'State=|GresUsed|AllocTRES'
   ```

   **Expect:** apply the idle rule only when `State=` starts with `IDLE` and does not contain `COMPLETING`.
   **If not:** on `MIXED` or `ALLOCATED`, apply the ceiling only and clear the idle timers.

3. Treat a GPU as idle only if utilization is 0% and memory in use is at most `GPU_IDLE_MEM_MAX_MIB`.

   **Expect:** anything else clears that GPU's timer.

4. On first sight above `GPU_IDLE_TEMP_MAX`, record the time and warn only.

   **Expect:** `/var/tmp/nhc_gpu_temp/gpu<N>.hot_since` exists, and no drain yet.

5. Drain only if the GPU is still idle and hot after the window.

   **Expect:** `GPU_TEMP_IDLE_HIGH: GPU-<n> idle above 45C for <m>m` and a drain at the end of the run.
   **If not:** discard the timer when the node leaves IDLE, utilization rises, memory is in use, the GPU cools, or the recorded time is before the last boot or in the future.

6. Before enforcing, scan the fleet read-only.

   ```bash
   eval "$(ssh-agent -s)"; ssh-add
   ./gpu_temp_scan.sh nodelist.yml
   ```

   **Expect:** a summary with scanned, unreachable and flagged counts, and `all_gpus.csv` and `flagged.csv`.
   **If not:** unreachable and no-data nodes are unknown, not fine.

## If it fails

| What you see | Likely cause | Fix |
|---|---|---|
| Every node drains at once | A failed read was treated as hot | Warn and skip on a failed read |
| No temperature rows | `dcgmi` or the DCGM host engine is down | Start the host engine, then re-run Part 1 step 1 |
| Drain never happens | Ceiling above what your GPUs reach | Lower it, below the slowdown limit |
| A node with a live job is flagged idle | Idle was defined by utilization alone | Gate on node state and memory in use |
| Idle timer never starts | Node not `IDLE`, or GPU not idle | Check `State=` and memory in use |
| Hot GPUs on `MIXED` nodes are missed | The idle rule skips them by design | Only the ceiling covers them |

## Roll out and roll back

- Start with the flag line only and watch syslog for a few days, then let the check drain.
- Test on a node with the DCGM host engine stopped: it must warn and not drain.
- For the idle timer: scan first, then run the check with draining off, then enforce.
- A drained node needs a manual resume, and running jobs are not killed.
- Roll back the idle timer: restore the previous script and remove `/var/tmp/nhc_gpu_temp/`.

**Don't:** drain because a reading failed, and don't define idle by utilization alone.

**Why it works:** [The Ceiling Rule](/fields/system-administration/node-health-check/gpu-temperature/gpu-temperature-ceiling.md) and [The Idle Timer](/fields/system-administration/node-health-check/gpu-temperature/gpu-temperature-idle-timer.md).

<!-- related-block -->
<div class="see-also">

**See also**

- [GPU Temperature in a Health Check: The Ceiling Rule](/fields/system-administration/node-health-check/gpu-temperature/gpu-temperature-ceiling.md) — Add a GPU over-temperature ceiling to a health-check script: read temperature with one dcgmi call, drain without killing jobs, fail safe when the sensor can't be read, and pick the number.
- [GPU Temperature in a Health Check: The Idle Timer](/fields/system-administration/node-health-check/gpu-temperature/gpu-temperature-idle-timer.md) — Catch GPUs that run warm while doing nothing: a warn-then-drain timer, why 0% utilization alone is not idle, using the Slurm node state, and a read-only fleet scan before you enforce.

</div>
<!-- related-block -->
<div class="mentioned-in">

**Mentioned in**

- [GPU Temperature in a Health Check: The Ceiling Rule](/fields/system-administration/node-health-check/gpu-temperature/gpu-temperature-ceiling.md) — Add a GPU over-temperature ceiling to a health-check script: read temperature with one dcgmi call, drain without killing jobs, fail safe when the sensor can't be read, and pick the number.
- [GPU Temperature in a Health Check: The Idle Timer](/fields/system-administration/node-health-check/gpu-temperature/gpu-temperature-idle-timer.md) — Catch GPUs that run warm while doing nothing: a warn-then-drain timer, why 0% utilization alone is not idle, using the Slurm node state, and a read-only fleet scan before you enforce.

</div>
