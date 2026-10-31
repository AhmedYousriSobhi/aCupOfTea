---
id: gpu-pred-collecting-signals
title: "Reading the GPU's Vital Signs"
sidebar_label: "2. Reading the vital signs"
order: 2
summary: The telemetry concepts behind GPU failure prediction - counters, gauges and events, volatile versus persistent, in-band versus out-of-band - and the ways each one misleads.
level: intermediate
type: concept
domains: [systems-and-hpc]
tags: [gpu, nvidia, hpc]
relations:
  prerequisites: [gpu-pred-what-fails]
---

# Reading the GPU's Vital Signs

> **Part 2 of the [Predicting GPU Node Failures series](/fields/system-administration/gpu-failure-prediction/README.md).** [Part 1](/fields/system-administration/gpu-failure-prediction/what-fails-and-what-warns.md) described the error ladder. This page is about how the ladder reaches you: what kind of number each signal is, where it comes from, and how it can mislead you. By the end you'll be able to look at any GPU dashboard and say what it can and can't tell you.

## Table of Contents
- [Reading the GPU's Vital Signs](#reading-the-gpus-vital-signs)
  - [Table of Contents](#table-of-contents)
  - [A doctor's analogy](#a-doctors-analogy)
  - [Concept 1: three shapes of signal](#concept-1-three-shapes-of-signal)
  - [Concept 2: volatile versus persistent](#concept-2-volatile-versus-persistent)
  - [Concept 3: where the numbers come from](#concept-3-where-the-numbers-come-from)
  - [Concept 4: the cost of looking](#concept-4-the-cost-of-looking)
  - [The ladder, as telemetry](#the-ladder-as-telemetry)
  - [Five ways the numbers lie](#five-ways-the-numbers-lie)
  - [Silence is not health](#silence-is-not-health)
    - [References](#references)

---

## A doctor's analogy

A doctor uses three kinds of information. A **chart** of measurements taken regularly (blood pressure every visit). An **alarm** that goes off when something happens (a heart monitor beeping). And the **patient's history**, written down at the time.

GPU monitoring has the same three:

| Doctor | GPU | Example |
|--------|-----|---------|
| Chart | Metrics scraped every 15-60 s | ECC counters, remap counts |
| Alarm | Events | Xid messages from the driver |
| History | Logs | The kernel log, where every Xid is written |

Most monitoring mistakes come from treating one kind as if it were another: reading an alarm off a chart, or trusting a chart that started yesterday as if it were the full history.

---

## Concept 1: three shapes of signal

Every number in GPU telemetry has one of three shapes. Knowing the shape tells you how to read it.

| Shape | What it is | Example | How to read it | Classic mistake |
|-------|-----------|---------|----------------|-----------------|
| **Counter** | Only goes up (until it resets) | Single-bit ECC errors so far | Look at its *rate* or *increase*, not its value | Alerting on "errors > 100" on a GPU that's three years old |
| **Gauge** | Goes up and down; describes *now* | Remap pending (0 or 1), temperature | Read the value directly | Expecting it to remember the past |
| **Event** | Something happened at a moment | Xid 79 | Count it, or keep the log | Sampling it like a gauge and missing it |

A good example of shape confusion is in NVIDIA's dcgm-exporter. Its default configuration exports a field described as *"Value of the last XID error encountered."* That's an **event squeezed into a gauge**. If a GPU logs Xid 79 and then Xid 13 between two scrapes, the dashboard only ever sees 13. The exporter also offers a proper per-code **counter** of Xid events (`DCGM_EXP_XID_ERRORS_TOTAL`). Using the counter instead of the gauge is the difference between seeing the failure and not seeing it.

> [!TIP]
> When you meet a new metric, ask first: counter, gauge or event? It decides every query and alert you'll write on it.

---

## Concept 2: volatile versus persistent

GPU error counters come in two lifetimes, and dcgm-exporter exposes both for ECC:

- **Volatile** counts start from zero when the driver loads. They tell you about *this session*. A reboot or driver reload wipes them.
- **Aggregate** (persistent) counts are stored on the GPU and survive reboots. They tell you about *this GPU's life*.

Row-remap counts are a third kind: NVIDIA notes that the remapped-row numbers are the entries recorded in the GPU's **InfoROM** (a small non-volatile store on the board), not the rows remapped in hardware so far. A recorded remap can still be pending.

Each lifetime answers a different question:

| Question | Use |
|----------|-----|
| "Is something happening on this GPU *right now*?" | The rate of a volatile counter |
| "Has this GPU been in trouble before?" | Aggregate counts and recorded remaps |
| "How much repair budget is left?" | The bank buckets from [part 1](/fields/system-administration/gpu-failure-prediction/what-fails-and-what-warns.md#concept-3-banks-rows-and-spare-rows) |

A GPU that was moved from another node, or reset last night, can look brand new on volatile counters and tired on persistent ones. Both are true.

---

## Concept 3: where the numbers come from

NVIDIA describes two paths for reading GPU health, and they fail differently.

- **In-band**: software on the node asks the driver. Tools: NVML, `nvidia-smi`, DCGM and the DCGM exporter, plus the kernel log. Rich and detailed, but it depends on the driver and the OS being alive.
- **Out-of-band**: the board's management controller reads the GPU over a side channel (NVIDIA calls the interface SMBPBI), usually reached through the server's BMC. It exposes the essentials, including remap counts and the pending and failure flags, and works even when the OS has hung.

When a GPU falls off the bus, in-band tools on that node can't reach the GPU, or can't reach anything. Out-of-band telemetry is how you still learn what happened. For prediction, in-band is enough most of the time. For the post-mortem, you'll want both.

There's also a matter of **scope**. dcgm-exporter only knows what happened since it started: its Xid counter begins at zero with the process. The kernel log is written by the driver regardless of whether any exporter is running. That makes the log the closest thing to ground truth for Xid events, and it's why NVIDIA's own triage guidance starts from log messages.

---

## Concept 4: the cost of looking

Every check has a price: time, load on the GPU, and sometimes disruption to the job running on it. That gives a simple rule of thumb:

> **The more often a check runs, the cheaper it must be.**

| How often | What fits | Example |
|-----------|-----------|---------|
| Every scrape (seconds) | Reading counters the driver already keeps | ECC, remaps, Xid counts |
| Every job (prolog/epilog) | Quick queries and short tests | `nvidia-smi` queries, recent Xids in the log, a short DCGM diagnostic |
| On a drained node | Deep tests that stress the GPU | NVIDIA's long DCGM diagnostic, about 30 minutes |
| Before an RMA | The authoritative test | NVIDIA's field diagnostic |

NVIDIA's debug guidelines make the same split: they recommend checks at the start or end of jobs (recent Xid errors, a short `dcgmi diag -r 2`), and the long diagnostic for fully stressing a system. Prediction lives in the first row. Everything below it is what prediction tells you to *do*.

---

## The ladder, as telemetry

Here's each rung from part 1 with the signal that shows it, as exposed by dcgm-exporter and `nvidia-smi`.

| Rung | Signal | Shape | How you'd read it |
|------|--------|-------|-------------------|
| Correctable errors | Single-bit ECC count | Counter | Rate, compared with this GPU's own past |
| Row remapped | Correctable / uncorrectable remapped rows; Xid 63 | Counter, event | Did it go up recently? |
| Spares running out | Banks in the "Low" and "None" buckets | Gauge | Above zero means a bank is nearly out of repairs |
| Uncorrectable error | Double-bit ECC count; Xid 48, 94 | Counter, event | Any increase matters |
| Remap pending | Pending flag | Gauge | 1 means a reset is owed |
| Remap failure | Failure flag; Xid 64 | Gauge, event | 1 means RMA candidate, latched |
| Uncontained / off the bus | Xid 95, 79 | Event | Any occurrence |

To see the remap state of a GPU by hand, `nvidia-smi` has a dedicated view. These field names are from its documentation; confirm them with `nvidia-smi --help-query-remapped-rows` on your driver.

```bash
nvidia-smi --query-remapped-rows=gpu_bus_id,remapped_rows.pending,remapped_rows.failure --format=csv
```

> [!WARNING]
> **The defaults don't show the ladder.** In dcgm-exporter 4.8.4, the shipped counter list has the ECC counters and the per-code Xid counter commented out. The remap counts and failure flag are on; the pending flag and bank buckets are not listed at all. A stock install mostly shows temperatures and utilization. Check what yours exports before trusting any GPU-health dashboard built on it.

---

## Five ways the numbers lie

| What you see | What's really happening | Concept |
|--------------|------------------------|---------|
| A GPU logged Xid 79 but the dashboard shows only Xid 13 | The "last Xid" gauge was overwritten between scrapes | Event read as a gauge |
| ECC errors dropped to zero overnight | The driver reloaded and volatile counters reset | Volatile lifetime |
| A GPU with a long error history looks clean | It was reset or moved; you're reading volatile counts | Volatile vs persistent |
| An idle GPU has a perfect record | Errors are mostly found when memory is used | Detection depends on use (part 1) |
| Xid history vanished after maintenance | The exporter restarted and its counter started over | Scope: exporter vs log |

One more, which deserves its own name because it bites rules in [part 3](/fields/system-administration/gpu-failure-prediction/rules-that-predict.md): **counters that are born on their first event.** The per-code Xid counter has no series for Xid 79 until the first Xid 79 happens. A rule that asks "did this counter increase?" can't see an increase from *nothing* to 1, so it misses exactly the first fatal event.

> [!WARNING]
> **Metric names change.** In the go-dcgm library behind dcgm-exporter 4.8.4, several remap field names in the default list are marked deprecated in favor of new ones. The exporter names each metric after the line in its config, so "modernizing" the config renames the metrics and every alert built on the old names silently stops matching.

---

## Silence is not health

The most dangerous dashboard is the one with no data on it. An exporter that crashed, a node whose scrape target was removed, a GPU that fell off the bus and took the exporter's view with it: all of them produce *no errors*. No errors looks exactly like a healthy GPU.

So a GPU monitoring design always needs a second question next to "is anything wrong?": **"are we still able to see?"** Missing telemetry is itself an alert. Part 3 builds it in.

**Takeaway:** know each signal's shape (counter, gauge, event), its lifetime (volatile, persistent) and its source (exporter, log, out-of-band), because every misleading GPU dashboard gets one of those three wrong.

Next: [part 3, from signals to decisions](/fields/system-administration/gpu-failure-prediction/rules-that-predict.md).

### References
- [NVIDIA GPU Memory Error Management: User Visible Statistics (in-band, out-of-band, InfoROM, buckets)](https://docs.nvidia.com/deploy/a100-gpu-mem-error-mgmt/user-visible-statistics.html)
- [NVIDIA GPU Debug Guidelines: Best Practices (metrics, prolog and epilog checks)](https://docs.nvidia.com/deploy/gpu-debug-guidelines/best-practices.html)
- [NVIDIA GPU Debug Guidelines: GPU Node Triage (DCGM diagnostics, field diagnostics)](https://docs.nvidia.com/deploy/gpu-debug-guidelines/gpu-node-triage.html)
- [dcgm-exporter `etc/default-counters.csv`](https://github.com/NVIDIA/dcgm-exporter/blob/main/etc/default-counters.csv)
- [go-dcgm field constants](https://github.com/NVIDIA/go-dcgm/blob/main/pkg/dcgm/const_fields.go)
- [nvidia-smi documentation](https://docs.nvidia.com/deploy/nvidia-smi/index.html)
- [Prometheus: metric types](https://prometheus.io/docs/concepts/metric_types/)