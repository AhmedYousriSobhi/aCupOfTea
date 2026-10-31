
# Predicting GPU Node Failures - Overview

<!-- related-block -->
<div class="related-strip">

**See also:** [Auto-Remediation: From Detected to Fixed, Safely](/fields/system-administration/node-health-check/auto-remediation.md)

</div>


> A five-part series on the "AIOps" half of a classic AI-infrastructure interview question: how do you see a GPU dying *before* it takes a training run down with it? It's about understanding, not tooling: by the end you'll be able to reason about GPU failures, judge any monitoring setup, and defend your design in a review or an interview.

## Table of Contents
- [Predicting GPU Node Failures - Overview](#predicting-gpu-node-failures---overview)
  - [Table of Contents](#table-of-contents)
  - [The question this series answers](#the-question-this-series-answers)
  - [The five ideas, one per page](#the-five-ideas-one-per-page)
  - [Who this is for](#who-this-is-for)
  - [What the series assumes](#what-the-series-assumes)
  - [Contents](#contents)
  - [Related reading in this repo](#related-reading-in-this-repo)

---

## The question this series answers

> *"How do you define and measure operational excellence and performance in an AI research cluster?"*

A strong answer has two halves. The first is the hardware "golden signals": GPU utilization, memory bandwidth, NVLink and InfiniBand traffic, thermal throttling, collected with tools like the NVIDIA DCGM exporter. That half tells you how well the cluster *performs*.

The second half is what separates a senior answer: **use the GPU's own error telemetry to predict which node will fail, and get it out of the way before it crashes a critical run.** That half tells you how well the cluster *survives*. This series is about the second half.

A 60-second version you can say in an interview:

> "GPU memory rarely dies in one step. It climbs a ladder: corrected errors, then rows swapped for spares, then spares running out, then uncorrectable errors. Each rung is visible in telemetry. I react instantly to the rungs NVIDIA documents as fatal, treat the trends as early warnings, and measure every warning by precision and lead time against real failures. I only move to a learned model once I have enough labeled failures to prove it beats simple rules."

---

## The five ideas, one per page

| # | Page | The idea you'll take away |
|---|------|---------------------------|
| 1 | [How GPU memory fails](/fields/system-administration/gpu-failure-prediction/what-fails-and-what-warns.md) | Errors are mostly hard faults that repeat and cluster, which is exactly what makes them predictable |
| 2 | [Reading the GPU's vital signs](/fields/system-administration/gpu-failure-prediction/collecting-the-signals.md) | Counters, gauges and events lie in different ways; know which one you're looking at |
| 3 | [From signals to decisions](/fields/system-administration/gpu-failure-prediction/rules-that-predict.md) | State, event and trend rules; baselines beat fixed thresholds; tiers map to actions |
| 4 | [Acting without making it worse](/fields/system-administration/gpu-failure-prediction/from-alert-to-drain.md) | Automate only reversible steps, and cap the blast radius of your own automation |
| 5 | [Is the prediction any good?](/fields/system-administration/gpu-failure-prediction/scoring-and-backtesting.md) | Base rates, precision, recall and lead time, and when a model is worth it |

Read them in order the first time. Page 5 is the one to reread before any design review.

> [!TIP]
> **Deploying it?** The [runbook](/fields/system-administration/gpu-failure-prediction/runbook.md) is the deep-technical companion: the counters file, node checks, tested Prometheus rules and unit tests, Alertmanager routing, a guarded Slurm drain hook and a backtest script, step by step with expected output and rollbacks.

---

## Who this is for

HPC and AI platform engineers who run NVIDIA data-center GPUs (A100, H100 or newer), usually under Slurm or Kubernetes, and who are tired of hearing about a bad GPU from a user whose job just died. You don't need a statistics background; page 5 builds what it needs.

---

## What the series assumes

| Topic | Assumed | Explained here |
|-------|---------|----------------|
| Prometheus-style metrics | You've seen a dashboard | Counter vs gauge vs event, and why it matters |
| Slurm | You know what draining a node means | Why drain is the right first action |
| GPU hardware | You know what HBM is | ECC, banks, rows, spares, containment |
| Statistics | None | Base rates, precision, recall, lead time, overfitting |

Facts come from NVIDIA documentation and published field studies (Meta's Llama 3 paper, Google's DRAM study, NCSA's Delta GPU study), cited on each page. Where a page gives an opinion rather than a fact, it says so.

## Contents

| File | Description |
|------|-------------|
| [what-fails-and-what-warns](/fields/system-administration/gpu-failure-prediction/what-fails-and-what-warns.md) | How ECC, row remapping and containment work, and the error ladder |
| [collecting-the-signals](/fields/system-administration/gpu-failure-prediction/collecting-the-signals.md) | Telemetry concepts: counters, gauges, events, in-band and out-of-band |
| [rules-that-predict](/fields/system-administration/gpu-failure-prediction/rules-that-predict.md) | Designing failure rules: state, event, trend, tiers and traps |
| [from-alert-to-drain](/fields/system-administration/gpu-failure-prediction/from-alert-to-drain.md) | Safe automation: reversibility, budgets, rollout and rollback |
| [scoring-and-backtesting](/fields/system-administration/gpu-failure-prediction/scoring-and-backtesting.md) | Measuring predictions and choosing between rules and models |
| [runbook](/fields/system-administration/gpu-failure-prediction/runbook.md) | Deep-technical deployment runbook: configs, tested rules, drain hook, backtest |

## Related reading in this repo

- [Node Health Check series](/fields/system-administration/node-health-check/README.md): the reactive side. NHC catches a node that is already broken; this series tries to get there first.
- [Auto-remediation with NHC](/fields/system-administration/node-health-check/auto-remediation.md): what happens after a predictive drain.
- [The cluster that passed every test except the one that mattered](/fields/devops/kubernetes/nvidia-cluster-readiness-engine.md): failures that per-GPU counters can't see.