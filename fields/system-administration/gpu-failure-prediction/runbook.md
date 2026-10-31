---
id: gpu-pred-runbook
title: "Runbook: Deploying GPU Failure Prediction End to End"
sidebar_label: "6. Runbook (deployment)"
order: 6
summary: The hands-on companion to the series - counters file, node checks, tested Prometheus rules, Alertmanager routing, a guarded Slurm drain hook and a backtest, step by step.
level: advanced
type: guide
domains: [systems-and-hpc]
tags: [gpu, nvidia, hpc, slurm]
relations:
  prerequisites: [gpu-pred-what-fails]
  related: [gpu-pred-rules, gpu-pred-alert-to-drain, gpu-pred-backtesting, nhc-auto-remediation]
---

# Runbook: Deploying GPU Failure Prediction End to End

> **The deep-technical companion to the [Predicting GPU Node Failures series](/fields/system-administration/gpu-failure-prediction/README.md).** Parts 1-5 explain the *why*: how GPU memory fails, what telemetry means, how to design rules, act safely and measure predictions. This runbook is the *how*: every config, command and script you need to deploy it on a real cluster, in order, with expected output and a rollback for each risky step. Read the concept pages first; come back here with a root shell.

## Table of Contents
- [Before you start](#before-you-start)
- [Phase 1: export the health signals](#phase-1-export-the-health-signals)
- [Phase 2: node-side checks](#phase-2-node-side-checks)
- [Phase 3: the Prometheus rules](#phase-3-the-prometheus-rules)
- [Phase 4: alert routing](#phase-4-alert-routing)
- [Phase 5: the drain hook](#phase-5-the-drain-hook)
- [Phase 6: backtesting](#phase-6-backtesting)
- [Troubleshooting](#troubleshooting)
- [Day-2 checklist](#day-2-checklist)

---

## Before you start

### What you need

| Component | Version this runbook targets | Role |
|-----------|-----------------------------|------|
| NVIDIA GPUs | Ampere or later data-center parts (A100, H100, ...) | Row remapping and bank buckets exist from Ampere on |
| dcgm-exporter | 4.8.4 (built on go-dcgm 1.4611.2) | Exports GPU telemetry on `:9400` |
| Prometheus / `promtool` | 3.15.1 | Rule evaluation and rule unit tests |
| Alertmanager / `amtool` | 0.34.2 | Routing alerts to people and to the drain hook |
| Slurm client tools | Any current release | `scontrol`, `sinfo` on the Alertmanager host |
| Python | 3.12 (standard library only) | Drain hook and backtest |

### What was tested, and what wasn't

| Item | Status |
|------|--------|
| Prometheus rules (13 rules) and 10 unit tests | **Tested** with promtool 3.15.1, including two deliberate failure paths |
| Alertmanager routing | **Tested** with `amtool check-config` and `amtool config routes test` |
| Drain hook | **Tested** in all modes against fake `scontrol`/`sinfo` scripts, plus the HTTP path |
| Backtest script | **Tested** on a hand-made fixture checked by hand |
| Xid log one-liners | **Tested** on captured kernel-log text |
| Counters file field names | **Checked** against the dcgm-exporter 4.8.4 source and go-dcgm field table |
| dcgm-exporter, `nvidia-smi`, `journalctl` on real GPUs; `scontrol` on a real cluster | **Not run** (no GPU in the test environment). From NVIDIA and SchedMD docs |

> [!IMPORTANT]
> Run every phase on **one node** first. The untested items above are standard tools used as documented, but your driver, exporter packaging and Slurm setup are the final judges.

---

## Phase 1: export the health signals

**Why:** in dcgm-exporter 4.8.4 the shipped `etc/default-counters.csv` has the ECC counters and the per-code Xid counter **commented out**, and doesn't list the remap-pending flag or the bank buckets at all. Concepts: [part 2](/fields/system-administration/gpu-failure-prediction/collecting-the-signals.md).

1. **Copy the default counters file** from the dcgm-exporter release you run (`etc/default-counters.csv` in the repo) and keep it in version control.

   ```bash
   sudo install -d /etc/dcgm-exporter
   sudo cp default-counters.csv /etc/dcgm-exporter/health-counters.csv
   ```

   Success: `grep -c ROW_REMAP_FAILURE /etc/dcgm-exporter/health-counters.csv` prints `1`.

2. **Append the health fields.** Format: `DCGM field, Prometheus type, help text`.

   ```bash
   sudo tee -a /etc/dcgm-exporter/health-counters.csv >/dev/null <<'CSV'

   # --- GPU health prediction (see gpu-failure-prediction runbook) ---
   DCGM_FI_DEV_ECC_SBE_VOL_TOTAL,     counter, Single-bit ECC errors since driver load.
   DCGM_FI_DEV_ECC_DBE_VOL_TOTAL,     counter, Double-bit ECC errors since driver load.
   DCGM_FI_DEV_ROW_REMAP_PENDING,     gauge,   1 if a row remap waits for a GPU reset.
   DCGM_FI_DEV_BANK_REMAP_AVAIL_LOW,  gauge,   Memory banks with one spare row left.
   DCGM_FI_DEV_BANK_REMAP_AVAIL_NONE, gauge,   Memory banks with no spare rows left.
   DCGM_EXP_XID_ERRORS_TOTAL,         counter, Xid errors per code since exporter start.
   CSV
   ```

   Success: `grep -c '^DCGM' /etc/dcgm-exporter/health-counters.csv` is six higher than before.

3. **Hopper only: add the NVLink error counters.**

   ```bash
   sudo tee -a /etc/dcgm-exporter/health-counters.csv >/dev/null <<'CSV'
   DCGM_FI_DEV_NVLINK_CRC_ERROR_TOTAL, counter, NVLink data-link CRC errors.
   DCGM_FI_DEV_NVLINK_REPLAY_TOTAL,    counter, NVLink data-link replay errors.
   CSV
   ```

   Pre-Hopper and Blackwell use different NVLink fields; copy the commented lines for your generation from the default file rather than guessing.

4. **Point the exporter at the file.** Flag `-f` (long form `--collectors`, env `DCGM_EXPORTER_COLLECTORS`); default listen address `:9400`.

   ```bash
   dcgm-exporter -f /etc/dcgm-exporter/health-counters.csv
   ```

   In a container or the GPU Operator, mount the file and set `DCGM_EXPORTER_COLLECTORS` to its path.

5. **Verify.**

   ```bash
   curl -s localhost:9400/metrics \
     | grep -E '^DCGM_(FI_DEV_ROW_REMAP_PENDING|FI_DEV_ECC_SBE_VOL_TOTAL|FI_DEV_BANK_REMAP_AVAIL_NONE)' | head
   ```

   Success: one line per GPU per field, with labels `gpu`, `UUID`, `pci_bus_id`, `device`, `modelName`, `hostname` (the 4.8.4 label set). `DCGM_EXP_XID_ERRORS_TOTAL` appears **only after a GPU logs an Xid**, labeled `xid`; its absence on a healthy node is normal.

> [!WARNING]
> **Pin the metric names.** In go-dcgm 1.4611.2 several remap names in the default file are deprecated aliases (for example `DCGM_FI_DEV_UNCORRECTABLE_REMAPPED_ROWS` → `DCGM_FI_DEV_ROW_REMAP_UNCORRECTABLE_TOTAL`, `DCGM_FI_DEV_ROW_REMAP_FAILURE` → `DCGM_FI_DEV_ROW_REMAP_FAILED`). The exporter names each metric after its CSV line, so renaming lines renames metrics and silently breaks Phase 3. Keep the file as written here, and keep Phase 3's tests in CI.

**Rollback:** restart the exporter without `-f` (or unset `DCGM_EXPORTER_COLLECTORS`); it falls back to its default list.

---

## Phase 2: node-side checks

**Why:** the exporter only knows what happened since it started; the kernel log is the ground truth for Xids. These checks fit a Slurm prolog or a manual triage. NVIDIA's debug guidelines recommend checking recent Xids at job start.

### Remap state with nvidia-smi

From the `nvidia-smi` docs; confirm field names on your driver with `nvidia-smi --help-query-remapped-rows`.

```bash
# Machine-readable remap state per GPU (Ampere and later)
nvidia-smi --query-remapped-rows=gpu_bus_id,remapped_rows.correctable,remapped_rows.uncorrectable,remapped_rows.pending,remapped_rows.failure --format=csv

# Human-readable, including bank availability buckets
nvidia-smi -q -d ROW_REMAPPER
```

Healthy: `pending` and `failure` read `No`/`0`, all banks in the top bucket. On a misbehaving multi-GPU node, query one GPU at a time with `-i N`.

### Xid summary for the last 24 hours

```bash
journalctl -k --since "24 hours ago" -o short-iso \
  | grep -oE 'NVRM: Xid \(PCI:[^)]*\): [0-9]+' \
  | sed -E 's/NVRM: Xid \((PCI:[^ )]*)[^)]*\): /\1 xid=/' \
  | sort | uniq -c
```

On our test log (Xid 13 on one GPU; 94, 63 and two 79s on another):

```text
      1 PCI:0000:1b:00 xid=13
      1 PCI:0000:3b:00 xid=63
      2 PCI:0000:3b:00 xid=79
      1 PCI:0000:3b:00 xid=94
```

No Xids: no output, exit 0. MIG lines (`PCI:0000:01:00 GPU-I:05`) collapse to the same shape.

### Prolog gate on fatal Xids

```bash
if journalctl -k --since "24 hours ago" -o short-iso \
     | grep -qE 'NVRM: Xid \(PCI:[^)]*\): (64|79|95),'; then
  echo "fatal Xid in the last 24h"; exit 1
fi
```

Tested: exit 1 on the log with Xid 79, exit 0 on a clean log.

### What each Xid means

Condensed from NVIDIA's GPU Debug Guidelines, Table 1:

| Xid | Meaning | Action |
|-----|---------|--------|
| 48 | Double-bit ECC error | Followed by 63/64: drain, wait, reset GPU. Otherwise field diagnostics |
| 63 | Row remap recorded | With 94: restart that app; reset/reboot when convenient |
| 64 | Row remap recording failure | Reboot immediately; if it continues, drain, triage, report |
| 74 | NVLink error | Decode the first DWORD; repeated ECC/parity bits on one link: report |
| 79 | GPU fell off the bus | Drain and report |
| 92 | High single-bit ECC rate | Field diagnostics; check RMA guidance |
| 94 | Contained ECC error | Restart the affected app; reset when convenient |
| 95 | Uncontained ECC error | MIG off: reboot immediately. MIG on: drain other instances, reset |

> [!CAUTION]
> Don't gate or drain on Xid 13 alone. NVIDIA classes it as a graphics engine exception and says to run diagnostics to separate hardware from application faults.

---

## Phase 3: the Prometheus rules

**Why:** turns Phase 1 metrics into tiered alerts, each with an `action` label that Phase 4 routes on. Concepts: [part 3](/fields/system-administration/gpu-failure-prediction/rules-that-predict.md).

### The rule file

Save as `gpu-health.rules.yml`:

```yaml
# GPU health prediction rules for dcgm-exporter 4.8.4 metrics.
# Tested with promtool 3.15.1 (see gpu-health.rules.test.yml).
# Knobs you are expected to tune from your own backtest are marked KNOB.
groups:
- name: gpu-health-recording
  interval: 1m
  rules:
  # New Xid events per GPU and Xid code in the last 10 minutes.
  # The "unless ... offset" half catches the FIRST event of a code since
  # exporter start: that series did not exist before, and increase() reads 0.
  - record: gpu:xid_new:10m
    expr: |
      increase(DCGM_EXP_XID_ERRORS_TOTAL[10m]) > 0
      or
      (DCGM_EXP_XID_ERRORS_TOTAL unless DCGM_EXP_XID_ERRORS_TOTAL offset 10m)
  - record: gpu:ecc_sbe:rate1h
    expr: rate(DCGM_FI_DEV_ECC_SBE_VOL_TOTAL[1h])
  - record: gpu:ecc_sbe:rate24h
    expr: rate(DCGM_FI_DEV_ECC_SBE_VOL_TOTAL[24h])
  - record: gpu:ecc_sbe:increase1h
    expr: increase(DCGM_FI_DEV_ECC_SBE_VOL_TOTAL[1h])
  - record: gpu:ecc_dbe:increase1h
    expr: increase(DCGM_FI_DEV_ECC_DBE_VOL_TOTAL[1h])
  # Banks with one spare row left (LOW) or none (NONE).
  - record: gpu:remap_banks_nearly_full
    expr: DCGM_FI_DEV_BANK_REMAP_AVAIL_LOW + DCGM_FI_DEV_BANK_REMAP_AVAIL_NONE

- name: gpu-health-alerts
  interval: 1m
  rules:
  # Tier 1: the GPU is already broken. Drain now, open an RMA.
  - alert: GpuRowRemapFailure
    expr: DCGM_FI_DEV_ROW_REMAP_FAILURE == 1
    for: 2m
    labels: {severity: critical, action: drain_now}
    annotations:
      summary: "Row remap failure on {{ $labels.instance }} GPU {{ $labels.gpu }}: spare rows exhausted, RMA candidate"
  - alert: GpuFatalXid
    expr: gpu:xid_new:10m{xid=~"64|79|95"}
    labels: {severity: critical, action: drain_now}
    annotations:
      summary: "Xid {{ $labels.xid }} on {{ $labels.instance }} GPU {{ $labels.gpu }}"

  # Tier 2: the GPU will fail jobs if left alone. Stop new work, reset when empty.
  - alert: GpuRowRemapPending
    expr: DCGM_FI_DEV_ROW_REMAP_PENDING == 1
    for: 15m
    labels: {severity: warning, action: drain_and_reset}
    annotations:
      summary: "Row remap pending on {{ $labels.instance }} GPU {{ $labels.gpu }}: needs a GPU reset to take effect"
  - alert: GpuUncorrectableMemoryError
    expr: gpu:ecc_dbe:increase1h > 0 or gpu:xid_new:10m{xid=~"48|94"}
    labels: {severity: warning, action: drain_and_reset}
    annotations:
      summary: "Uncorrectable memory error on {{ $labels.instance }} GPU {{ $labels.gpu }}"

  # Tier 3: early warning. Nothing is broken yet; this is the prediction.
  - alert: GpuSpareRowsNearlyExhausted
    expr: gpu:remap_banks_nearly_full > 0
    for: 1h
    labels: {severity: warning, action: plan_rma}
    annotations:
      summary: "{{ $value }} memory bank(s) with <=1 spare row on {{ $labels.instance }} GPU {{ $labels.gpu }}"
  - alert: GpuSbeRateAccelerating
    # KNOB: 3x the GPU's own 24h baseline, and at least 10 SBEs in the hour.
    expr: |
      gpu:ecc_sbe:rate1h > 3 * gpu:ecc_sbe:rate24h
      and
      gpu:ecc_sbe:increase1h >= 10
    for: 30m
    labels: {severity: info, action: watch}
    annotations:
      summary: 'Single-bit ECC rate on {{ $labels.instance }} GPU {{ $labels.gpu }} is {{ printf "%.2f" $value }}/s, over 3x its 24h baseline'

  # Silence is not health: no data means no prediction.
  - alert: GpuTelemetryMissing
    expr: up{job="dcgm-exporter"} == 0
    for: 10m
    labels: {severity: warning, action: watch}
    annotations:
      summary: "dcgm-exporter on {{ $labels.instance }} is down; GPU failure prediction is blind there"
```

> [!NOTE]
> `GpuTelemetryMissing` assumes your scrape job is named `dcgm-exporter`. Change the `job` matcher to match your `prometheus.yml`.

### The unit tests

Save as `gpu-health.rules.test.yml` next to the rules. Ten cases: the first-Xid trap, a repeat Xid, an application Xid that must stay quiet, pending and failed remaps, a double-bit error, accelerating SBEs with two GPUs that must stay quiet, nearly exhausted spares, a healthy GPU, and missing telemetry.

<details>
<summary>gpu-health.rules.test.yml (click to expand)</summary>

```yaml
# promtool test rules gpu-health.rules.test.yml
rule_files: [gpu-health.rules.yml]
evaluation_interval: 1m
tests:

# 1. The trap: the first Xid 79 since exporter start must still fire.
- name: first-ever fatal Xid fires, then resolves
  interval: 1m
  input_series:
  - series: 'DCGM_EXP_XID_ERRORS_TOTAL{instance="cn042:9400",gpu="3",UUID="GPU-0003",xid="79"}'
    values: '_x20 1x30'
  alert_rule_test:
  - eval_time: 25m
    alertname: GpuFatalXid
    exp_alerts:
    - exp_labels: {instance: "cn042:9400", gpu: "3", UUID: "GPU-0003", xid: "79", severity: critical, action: drain_now}
      exp_annotations: {summary: "Xid 79 on cn042:9400 GPU 3"}
  - eval_time: 40m
    alertname: GpuFatalXid
    exp_alerts: []

# 2. A repeat of the same Xid later fires again through increase().
- name: repeated fatal Xid fires again
  interval: 1m
  input_series:
  - series: 'DCGM_EXP_XID_ERRORS_TOTAL{instance="cn042:9400",gpu="3",UUID="GPU-0003",xid="95"}'
    values: '_x5 1x30 2x10'
  alert_rule_test:
  - eval_time: 30m
    alertname: GpuFatalXid
    exp_alerts: []
  - eval_time: 40m
    alertname: GpuFatalXid
    exp_alerts:
    - exp_labels: {instance: "cn042:9400", gpu: "3", UUID: "GPU-0003", xid: "95", severity: critical, action: drain_now}
      exp_annotations: {summary: "Xid 95 on cn042:9400 GPU 3"}

# 3. Xid 13 is usually an application fault: no hardware alert.
- name: application Xid does not page
  interval: 1m
  input_series:
  - series: 'DCGM_EXP_XID_ERRORS_TOTAL{instance="cn007:9400",gpu="0",UUID="GPU-0700",xid="13"}'
    values: '_x5 1x10 2x10'
  alert_rule_test:
  - eval_time: 20m
    alertname: GpuFatalXid
    exp_alerts: []
  - eval_time: 20m
    alertname: GpuUncorrectableMemoryError
    exp_alerts: []

# 4. Row remap pending must persist 15m before we act.
- name: pending row remap
  interval: 1m
  input_series:
  - series: 'DCGM_FI_DEV_ROW_REMAP_PENDING{instance="cn042:9400",gpu="3",UUID="GPU-0003"}'
    values: '0x10 1x30'
  alert_rule_test:
  - eval_time: 20m
    alertname: GpuRowRemapPending
    exp_alerts: []
  - eval_time: 30m
    alertname: GpuRowRemapPending
    exp_alerts:
    - exp_labels: {instance: "cn042:9400", gpu: "3", UUID: "GPU-0003", severity: warning, action: drain_and_reset}
      exp_annotations: {summary: "Row remap pending on cn042:9400 GPU 3: needs a GPU reset to take effect"}

# 5. Remap failure is latched: fires after 2m.
- name: row remap failure
  interval: 1m
  input_series:
  - series: 'DCGM_FI_DEV_ROW_REMAP_FAILURE{instance="cn042:9400",gpu="3",UUID="GPU-0003"}'
    values: '0x5 1x10'
  alert_rule_test:
  - eval_time: 9m
    alertname: GpuRowRemapFailure
    exp_alerts:
    - exp_labels: {instance: "cn042:9400", gpu: "3", UUID: "GPU-0003", severity: critical, action: drain_now}
      exp_annotations: {summary: "Row remap failure on cn042:9400 GPU 3: spare rows exhausted, RMA candidate"}

# 6. A double-bit (uncorrectable) ECC error.
- name: uncorrectable ECC
  interval: 1m
  input_series:
  - series: 'DCGM_FI_DEV_ECC_DBE_VOL_TOTAL{instance="cn042:9400",gpu="3",UUID="GPU-0003"}'
    values: '0x30 1x30'
  alert_rule_test:
  - eval_time: 45m
    alertname: GpuUncorrectableMemoryError
    exp_alerts:
    - exp_labels: {instance: "cn042:9400", gpu: "3", UUID: "GPU-0003", severity: warning, action: drain_and_reset}
      exp_annotations: {summary: "Uncorrectable memory error on cn042:9400 GPU 3"}

# 7. Prediction: SBE rate jumps from 1/min to 30/min.
- name: accelerating single-bit errors
  interval: 1m
  input_series:
  - series: 'DCGM_FI_DEV_ECC_SBE_VOL_TOTAL{instance="cn042:9400",gpu="3",UUID="GPU-0003"}'
    values: '0+1x1500 1530+30x90'
  # Steady 1/min forever: a noisy but stable GPU. Must NOT fire.
  - series: 'DCGM_FI_DEV_ECC_SBE_VOL_TOTAL{instance="cn011:9400",gpu="5",UUID="GPU-1105"}'
    values: '0+1x1600'
  # Quiet GPU that sees 5 SBEs in an hour: infinite ratio, below the floor.
  - series: 'DCGM_FI_DEV_ECC_SBE_VOL_TOTAL{instance="cn012:9400",gpu="1",UUID="GPU-1201"}'
    values: '0x1540 0+0.1x50'
  alert_rule_test:
  - eval_time: 1590m
    alertname: GpuSbeRateAccelerating
    exp_alerts:
    - exp_labels: {instance: "cn042:9400", gpu: "3", UUID: "GPU-0003", severity: info, action: watch}
      exp_annotations: {summary: "Single-bit ECC rate on cn042:9400 GPU 3 is 0.50/s, over 3x its 24h baseline"}

# 8. Spare rows nearly gone in one bank.
- name: spare rows nearly exhausted
  interval: 5m
  input_series:
  - series: 'DCGM_FI_DEV_BANK_REMAP_AVAIL_LOW{instance="cn042:9400",gpu="3",UUID="GPU-0003"}'
    values: '0x6 1x20'
  - series: 'DCGM_FI_DEV_BANK_REMAP_AVAIL_NONE{instance="cn042:9400",gpu="3",UUID="GPU-0003"}'
    values: '0x26'
  alert_rule_test:
  - eval_time: 60m
    alertname: GpuSpareRowsNearlyExhausted
    exp_alerts: []
  - eval_time: 100m
    alertname: GpuSpareRowsNearlyExhausted
    exp_alerts:
    - exp_labels: {instance: "cn042:9400", gpu: "3", UUID: "GPU-0003", severity: warning, action: plan_rma}
      exp_annotations: {summary: "1 memory bank(s) with <=1 spare row on cn042:9400 GPU 3"}

# 9. A healthy GPU: every counter flat, nothing fires.
- name: healthy GPU is quiet
  interval: 1m
  input_series:
  - series: 'DCGM_FI_DEV_ROW_REMAP_PENDING{instance="cn100:9400",gpu="0",UUID="GPU-10000"}'
    values: '0x120'
  - series: 'DCGM_FI_DEV_ROW_REMAP_FAILURE{instance="cn100:9400",gpu="0",UUID="GPU-10000"}'
    values: '0x120'
  - series: 'DCGM_FI_DEV_ECC_DBE_VOL_TOTAL{instance="cn100:9400",gpu="0",UUID="GPU-10000"}'
    values: '0x120'
  - series: 'DCGM_FI_DEV_ECC_SBE_VOL_TOTAL{instance="cn100:9400",gpu="0",UUID="GPU-10000"}'
    values: '0x120'
  - series: 'up{job="dcgm-exporter",instance="cn100:9400"}'
    values: '1x120'
  alert_rule_test:
  - {eval_time: 120m, alertname: GpuRowRemapPending, exp_alerts: []}
  - {eval_time: 120m, alertname: GpuRowRemapFailure, exp_alerts: []}
  - {eval_time: 120m, alertname: GpuUncorrectableMemoryError, exp_alerts: []}
  - {eval_time: 120m, alertname: GpuSbeRateAccelerating, exp_alerts: []}
  - {eval_time: 120m, alertname: GpuTelemetryMissing, exp_alerts: []}

# 10. Exporter down: we are blind, say so.
- name: telemetry missing
  interval: 1m
  input_series:
  - series: 'up{job="dcgm-exporter",instance="cn042:9400"}'
    values: '1x5 0x20'
  alert_rule_test:
  - eval_time: 20m
    alertname: GpuTelemetryMissing
    exp_alerts:
    - exp_labels: {job: dcgm-exporter, instance: "cn042:9400", severity: warning, action: watch}
      exp_annotations: {summary: "dcgm-exporter on cn042:9400 is down; GPU failure prediction is blind there"}
```

</details>

### Lint, test, load

1. **Lint.**

   ```bash
   promtool check rules gpu-health.rules.yml
   ```

   Expected, exit 0:

   ```text
   Checking gpu-health.rules.yml
     SUCCESS: 13 rules found
   ```

2. **Test.**

   ```bash
   promtool test rules gpu-health.rules.test.yml
   ```

   Expected, exit 0:

   ```text
     SUCCESS
   ```

3. **Prove the tests can fail.** Temporarily delete the `or (... unless ... offset 10m)` branch and rerun. Expected: exit 1 and

   ```text
     FAILED:
       name: first-ever fatal Xid fires, then resolves,
       alertname: GpuFatalXid, time: 25m,
           ...
           got:[]
   ```

   Then delete the `and gpu:ecc_sbe:increase1h >= 10` floor instead. Expected: exit 1, with an extra alert for the quiet GPU `cn012` (`... is 0.00/s, over 3x its 24h baseline`). Restore the file afterwards.

4. **Load.** Add to `prometheus.yml` and reload (`SIGHUP`, or `POST /-/reload` with `--web.enable-lifecycle`):

   ```yaml
   rule_files:
     - /etc/prometheus/rules/gpu-health.rules.yml
   ```

   Success: the rules appear on `/rules` with no evaluation errors; `gpu:remap_banks_nearly_full` returns one series per GPU.

> [!IMPORTANT]
> Put step 2 in CI for both the rules repo **and** the counters file from Phase 1. A renamed metric upstream disables rules silently; only the tests notice.

**Rollback:** remove the file from `rule_files` and reload.

### Knobs to tune later

| Knob | Starting value | Raise if | Lower if |
|------|----------------|----------|----------|
| SBE ratio vs 24h baseline | 3× | Many `watch` alerts never precede failures | Failures arrive unwarned |
| SBE noise floor | 10/hour | Quiet GPUs keep tripping it | Real degradations stay under it |
| Pending-remap `for:` | 15m | Pending flags clear on their own | Jobs die on pending GPUs within 15 min |
| Spare-rows `for:` | 1h | Rarely needed | You want earlier RMA planning |

Set them with Phase 6, not by feel.

---

## Phase 4: alert routing

**Why:** acting tiers go to the drain hook *and* to people; everything else goes to people only. Concepts: [part 4](/fields/system-administration/gpu-failure-prediction/from-alert-to-drain.md).

Save as `alertmanager.yml` (or merge into yours):

```yaml
route:
  receiver: ops-chat
  group_by: [alertname, instance]
  routes:
  - matchers: ['action=~"drain_now|drain_and_reset"']
    receiver: gpu-drain-hook
    group_wait: 30s
    repeat_interval: 1h
    continue: true          # keep matching: humans hear about every drain too
  - receiver: ops-chat      # catch-all sibling
receivers:
- name: ops-chat
  webhook_configs:
  - url: http://chat-bridge.example.internal/alert
- name: gpu-drain-hook
  webhook_configs:
  - url: http://127.0.0.1:9095/
    send_resolved: false
```

Replace the `ops-chat` URL with your real receiver (Slack, email, PagerDuty, ...).

1. **Check the config.**

   ```bash
   amtool check-config alertmanager.yml
   ```

   Expected: `Checking 'alertmanager.yml'  SUCCESS`, exit 0.

2. **Check who gets what.**

   ```bash
   amtool config routes test --config.file=alertmanager.yml action=drain_now alertname=GpuFatalXid
   amtool config routes test --config.file=alertmanager.yml action=watch alertname=GpuSbeRateAccelerating
   ```

   Expected: `gpu-drain-hook,ops-chat`, then `ops-chat`.

> [!WARNING]
> **`continue: true` alone doesn't reach the root receiver.** Our first version had only the drain route plus `continue: true`; the route test returned just `gpu-drain-hook`, because the root receiver only catches alerts that match *no* child route. The explicit catch-all sibling fixes it.

`send_resolved: false` is deliberate: a resolved alert must never un-drain a node.

---

## Phase 5: the drain hook

**Why:** turns `drain_now`/`drain_and_reset` alerts into Slurm drains, with a mode switch, a canary list and a budget.

### The script

Save as `/usr/local/sbin/gpu_drain_hook.py` on the Alertmanager host (which needs Slurm client tools and a user allowed to drain nodes):

```python
#!/usr/bin/env python3
"""Alertmanager webhook -> Slurm drain, with dry-run, canary and a drain budget."""
import json, os, subprocess, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

MODE = os.environ.get("MODE", "dryrun")             # dryrun | canary | enforce
CANARY = set(os.environ.get("CANARY_NODES", "").split(","))
BUDGET = int(os.environ.get("MAX_DRAINED", "4"))    # nodes we may hold drained at once
PREFIX = "GPUPRED:"
ACT_ON = {"drain_now", "drain_and_reset"}

def drained_by_us():
    out = subprocess.run(["sinfo", "-h", "-N", "-t", "drain", "-o", "%N|%E"],
                         capture_output=True, text=True, check=True).stdout
    return {l.split("|", 1)[0] for l in out.splitlines() if PREFIX in l}

def handle(payload):
    ours = drained_by_us()
    for a in payload.get("alerts", []):
        lab = a.get("labels", {})
        if a.get("status") != "firing" or lab.get("action") not in ACT_ON:
            continue
        node = lab.get("instance", "").split(":")[0]
        if not node or node in ours:
            continue
        reason = f'{PREFIX} {lab.get("alertname")} gpu{lab.get("gpu", "?")} {lab.get("action")}'
        cmd = ["scontrol", "update", f"NodeName={node}", "State=DRAIN", f"Reason={reason}"]
        if len(ours) >= BUDGET:
            print(f"BUDGET {len(ours)}/{BUDGET} reached, NOT draining {node}: {reason}", flush=True)
        elif MODE == "enforce" or (MODE == "canary" and node in CANARY):
            subprocess.run(cmd, check=True)
            ours.add(node)
            print(f"DRAINED {node}: {reason}", flush=True)
        else:
            print(f"WOULD DRAIN ({MODE}) {node}: {reason}", flush=True)

class Hook(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        handle(json.loads(body))
        self.send_response(200); self.end_headers()
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    if len(sys.argv) > 1:                            # offline test: drain_hook.py payload.json
        handle(json.load(open(sys.argv[1]))); sys.exit(0)
    HTTPServer(("127.0.0.1", 9095), Hook).serve_forever()
```

Design notes:

- **Listens on `127.0.0.1` only.** Anything that can POST to it can drain nodes. Put authentication in front before widening the address.
- **`instance` → node name by stripping the port** (`cn042:9400` → `cn042`). If your targets use IPs or FQDNs, map them here or relabel in Prometheus.
- **Whole-node drains.** Slurm drains nodes, not GPUs; one bad GPU idles its node until the reset.

### Run it as a service

An example systemd unit (standard systemd syntax; not run in our test environment):

```ini
[Unit]
Description=GPU failure prediction drain hook
After=network-online.target

[Service]
Environment=MODE=dryrun
Environment=MAX_DRAINED=4
Environment=CANARY_NODES=
ExecStart=/usr/bin/python3 /usr/local/sbin/gpu_drain_hook.py
Restart=on-failure
User=slurmops

[Install]
WantedBy=multi-user.target
```

Save as `/etc/systemd/system/gpu-drain-hook.service`, then `systemctl daemon-reload && systemctl enable --now gpu-drain-hook`. Logs: `journalctl -u gpu-drain-hook`. Replace `slurmops` with a user your Slurm configuration allows to drain nodes.

### Test it offline before connecting Alertmanager

Save this as `payload.json`: a fatal Xid on `cn042`, a `watch` alert on `cn011`, a pending remap on `cn017`, a *resolved* fatal Xid on `cn050`.

```json
{"alerts":[
 {"status":"firing","labels":{"alertname":"GpuFatalXid","instance":"cn042:9400","gpu":"3","xid":"79","action":"drain_now"}},
 {"status":"firing","labels":{"alertname":"GpuSbeRateAccelerating","instance":"cn011:9400","gpu":"5","action":"watch"}},
 {"status":"firing","labels":{"alertname":"GpuRowRemapPending","instance":"cn017:9400","gpu":"0","action":"drain_and_reset"}},
 {"status":"resolved","labels":{"alertname":"GpuFatalXid","instance":"cn050:9400","gpu":"1","xid":"79","action":"drain_now"}}]}
```

```bash
MODE=dryrun python3 /usr/local/sbin/gpu_drain_hook.py payload.json
```

Expected (dry run touches nothing):

```text
WOULD DRAIN (dryrun) cn042: GPUPRED: GpuFatalXid gpu3 drain_now
WOULD DRAIN (dryrun) cn017: GPUPRED: GpuRowRemapPending gpu0 drain_and_reset
```

What our tests with fake `scontrol`/`sinfo` showed in each mode:

| Mode | Output | `scontrol` calls |
|------|--------|------------------|
| `dryrun` | `WOULD DRAIN` for cn042 and cn017 | none |
| `canary`, `CANARY_NODES=cn017` | `WOULD DRAIN (canary) cn042`, `DRAINED cn017` | one |
| `enforce` | `DRAINED cn042`, `DRAINED cn017` | two |
| `enforce`, `MAX_DRAINED=2`, two `GPUPRED:` drains active | `BUDGET 2/2 reached, NOT draining ...` for both | none |

`cn011` (`watch`) and `cn050` (resolved) were ignored in every mode, and a POST of the same payload returned HTTP `200`. The real command produced:

```text
scontrol update NodeName=cn042 State=DRAIN Reason=GPUPRED: GpuFatalXid gpu3 drain_now
```

### Roll out: dry run → canary → enforce

1. **Dry run, at least a week.** `MODE=dryrun`. Each morning compare `WOULD DRAIN` lines with what actually failed. Move on when every line points at a GPU you'd have drained by hand.
2. **Canary.** `MODE=canary CANARY_NODES=cn201,cn202,cn203` (nodes you're happy to lose). Move on when canary drains carry the `GPUPRED:` reason and running jobs finished normally.
3. **Enforce, small budget.** `MODE=enforce MAX_DRAINED=4`. Size the budget to what you can lose unnoticed. Move on after a normal week with no `BUDGET` lines.
4. **Raise the budget** only when Phase 6 says the rules earn it.

> [!CAUTION]
> Alert on any `BUDGET ... reached` line from the hook's journal. It means either several GPUs are failing together (rare) or something upstream is lying (common).

### Rollback

Undo every drain the hook made (tested against fake Slurm: it resumed only the `GPUPRED:` node and left others alone):

```bash
sinfo -h -N -t drain -o '%N|%E' | awk -F'|' '/GPUPRED:/{print $1}' | sort -u \
  | xargs -r -I{} scontrol update NodeName={} State=RESUME
```

Stop new drains without undoing old ones: set `MODE=dryrun` and restart the service.

> [!WARNING]
> Don't resume a node whose GPU had a remap failure or Xid 79 just because the rollback is easy. Roll back drains you believe were wrong.

### After the drain

| Alert | Once the node is empty | Then |
|-------|------------------------|------|
| `GpuRowRemapPending`, `GpuUncorrectableMemoryError` | `nvidia-smi -r -i N` (root, no processes on that GPU) | Confirm `remapped_rows.pending` is No, run `dcgmi diag -r 2`, resume |
| `GpuFatalXid` 64, or 95 with MIG off | Reboot the node | If repeated: `nvidia-bug-report.sh`, field diagnostics, report |
| `GpuFatalXid` 79 | Collect evidence, reboot | Expect recurrence; report to the vendor |
| `GpuRowRemapFailure` | Keep it drained | Field diagnostic validates the flag for RMA |

GPU reset limits depend on the platform (NVSwitch and Fabric Manager state); check NVIDIA's reset-capabilities table before automating resets. For the fix-and-verify loop, see [NHC auto-remediation](/fields/system-administration/node-health-check/auto-remediation.md).

---

## Phase 6: backtesting

**Why:** precision, recall and lead time per rule, on your own history, decide which knobs to turn and which rules may drain. Concepts: [part 5](/fields/system-administration/gpu-failure-prediction/scoring-and-backtesting.md).

### Inputs

Two CSV files with ISO timestamps, a GPU identified by node and index:

```text
# failures.csv: one row per real hardware failure (RMA records, human drain reasons, fatal Xids)
time,node,gpu
2026-09-02T22:00:00,cn042,3

# alerts.csv: one row per alert start
time,node,gpu,alertname
2026-09-01T10:00:00,cn042,3,GpuSbeRateAccelerating
```

Alert history: Prometheus keeps firing alerts as the `ALERTS` series. Export `ALERTS{alertstate="firing"}` with the HTTP API's `query_range`, keep the first sample of each firing run, and strip the `:9400` port from `instance`. The hook's dry-run log is a second source.

### The script

Save as `backtest.py`:

```python
#!/usr/bin/env python3
"""Backtest alert rules against real failures: precision, recall, lead time."""
import csv, sys
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import median

HORIZON = timedelta(hours=float(sys.argv[3]) if len(sys.argv) > 3 else 72)

def load(path):
    with open(path) as f:
        return [dict(r, t=datetime.fromisoformat(r["time"])) for r in csv.DictReader(f)]

alerts, failures = load(sys.argv[1]), load(sys.argv[2])
fail_by_gpu = defaultdict(list)
for f in failures:
    fail_by_gpu[(f["node"], f["gpu"])].append(f["t"])

stats = defaultdict(lambda: {"fired": 0, "hit": 0, "caught": set(), "leads": []})
for a in alerts:
    s = stats[a["alertname"]]
    s["fired"] += 1
    nxt = [t for t in fail_by_gpu[(a["node"], a["gpu"])] if a["t"] <= t <= a["t"] + HORIZON]
    if nxt:
        s["hit"] += 1
        s["caught"].add((a["node"], a["gpu"], min(nxt)))
        s["leads"].append((min(nxt) - a["t"]).total_seconds() / 3600)

print(f"{len(failures)} failures, horizon {HORIZON}")
print(f"{'RULE':<30} {'FIRED':>5} {'PRECISION':>9} {'RECALL':>6} {'MEDIAN_LEAD_H':>13}")
for rule, s in sorted(stats.items()):
    prec = s["hit"] / s["fired"]
    rec = len(s["caught"]) / len(failures) if failures else 0
    lead = f'{median(s["leads"]):.1f}' if s["leads"] else "-"
    print(f"{rule:<30} {s['fired']:>5} {prec:>9.2f} {rec:>6.2f} {lead:>13}")
```

Run with the horizon in hours as the last argument:

```bash
python3 backtest.py alerts.csv failures.csv 72
```

### What a run looks like

On a hand-made fixture (four alerts, three failures; **test input, not cluster data**):

```text
3 failures, horizon 3 days, 0:00:00
RULE                           FIRED PRECISION RECALL MEDIAN_LEAD_H
GpuRowRemapPending                 1      1.00   0.33          13.0
GpuSbeRateAccelerating             2      0.50   0.33          36.0
GpuSpareRowsNearlyExhausted        1      1.00   0.33          18.0
```

With a 12-hour horizon the same inputs score 0.00 everywhere: every warning came more than 12 hours early. Always report the horizon with the numbers.

### Using the results

1. Tune knobs on **older** months, grade on the most recent months you held back.
2. Change one knob at a time; keep before/after output in the commit that changes the rule.
3. Promote a `watch` rule to a drain tier only when its precision on held-out months justifies it.
4. Rerun after every driver, firmware or exporter upgrade (drift).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `curl :9400/metrics` shows no ECC or pending metrics | Exporter still on the default counters file | Check `-f` / `DCGM_EXPORTER_COLLECTORS` points at `health-counters.csv` |
| `DCGM_EXP_XID_ERRORS_TOTAL` missing everywhere | Normal until a GPU logs an Xid | Verify with the Phase 2 log one-liner |
| `GpuFatalXid` never fires for a first Xid 79 | Naive `increase()` rule | Use the `unless ... offset` branch; run test 1 |
| All GPU alerts went quiet after an upgrade | Metric names changed in the counters file or exporter | Restore pinned names; run the rule tests |
| Drains happen but nobody is told | Routing without the catch-all sibling | Phase 4, `amtool config routes test` |
| Hook logs `BUDGET ... reached` | Correlated alerts: probably upstream, not hardware | Stop and investigate before raising the budget |
| Hook says `WOULD DRAIN` in enforce | `MODE` not set in the service environment | `systemctl show gpu-drain-hook -p Environment` |
| `scontrol` permission denied from the hook | Service user not allowed to drain | Run as a Slurm operator/admin user |
| Pending remap stays after reset | GPU still in use, or reset not supported in this topology | Confirm no processes; check NVIDIA's reset table |
| `GpuTelemetryMissing` never fires | Scrape job name isn't `dcgm-exporter` | Fix the `job` matcher |

---

## Day-2 checklist

| How often | Check |
|-----------|-------|
| Every change | `promtool test rules` and `amtool check-config` pass in CI |
| Daily (during dry run) | `WOULD DRAIN` lines vs actual failures |
| Weekly | Nodes drained with `GPUPRED:` and their outcome after reset |
| Monthly | Backtest on the latest month; review knobs |
| Every driver / exporter upgrade | Counters file still exports every field; backtest again |

**Takeaway:** deploy in order (signals, node checks, tested rules, routing, a dry-run drain hook, then backtests), and never skip the tests or the dry run, because every phase can fail silently.

Back to the concepts: [series overview](/fields/system-administration/gpu-failure-prediction/README.md).

### References
- [dcgm-exporter repository and `etc/default-counters.csv`](https://github.com/NVIDIA/dcgm-exporter)
- [go-dcgm field constants](https://github.com/NVIDIA/go-dcgm/blob/main/pkg/dcgm/const_fields.go)
- [NVIDIA GPU Memory Error Management](https://docs.nvidia.com/deploy/a100-gpu-mem-error-mgmt/index.html)
- [NVIDIA GPU Debug Guidelines: GPU Node Triage](https://docs.nvidia.com/deploy/gpu-debug-guidelines/gpu-node-triage.html)
- [NVIDIA GPU Debug Guidelines: Best Practices](https://docs.nvidia.com/deploy/gpu-debug-guidelines/best-practices.html)
- [nvidia-smi documentation](https://docs.nvidia.com/deploy/nvidia-smi/index.html)
- [Prometheus: unit testing rules](https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/)
- [Prometheus: alerting rules and the `ALERTS` series](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [Prometheus HTTP API: range queries](https://prometheus.io/docs/prometheus/latest/querying/api/#range-queries)
- [Alertmanager configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [Slurm `scontrol`](https://slurm.schedmd.com/scontrol.html) and [`sinfo`](https://slurm.schedmd.com/sinfo.html)
- [systemd.service](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)